import sys
import tempfile
import os
import threading
import types
import unittest
from unittest import mock

import downloader
from download_models import DownloadResult


class _FakeYoutubeDL:
    download_result = 0

    def __init__(self, options):
        self.options = options

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def extract_info(self, url, download=False):
        return {"title": "Test media", "webpage_url": url}

    def download(self, urls):
        return self.download_result


class DownloaderResultTests(unittest.TestCase):
    def _run_worker(self, result):
        fake_class = type("FakeYoutubeDL", (_FakeYoutubeDL,), {"download_result": result})
        fake_module = types.SimpleNamespace(YoutubeDL=fake_class)
        completed = []
        errors = []

        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}), \
                mock.patch.object(downloader, "get_ffmpeg_path", return_value="ffmpeg"):
            downloader.Downloader()._worker(
                "https://example.com/media", tempfile.gettempdir(), "mp3", "128", "best",
                False, "%(title)s", "", "", None, None,
                None, None, lambda *args: completed.append(args), errors.append,
            )
        return completed, errors

    def test_nonzero_ytdlp_result_is_reported_as_error(self):
        completed, errors = self._run_worker(1)
        self.assertEqual(completed, [])
        self.assertEqual(errors, ["yt-dlp returned error code 1"])

    def test_zero_ytdlp_result_completes(self):
        completed, errors = self._run_worker(0)
        self.assertEqual(errors, [])
        self.assertEqual(
            completed,
            [(DownloadResult(count=1, title="Test media", succeeded=1),)],
        )


class PlaylistResultTests(unittest.TestCase):
    def _run_playlist(self, results):
        class FakePlaylistYDL(_FakeYoutubeDL):
            remaining_results = list(results)

            def extract_info(self, url, download=False):
                return {
                    "_type": "playlist",
                    "title": "Test playlist",
                    "entries": [
                        {"title": f"Item {index}", "webpage_url": f"https://example.com/{index}"}
                        for index in range(1, len(results) + 1)
                    ],
                }

            def download(self, urls):
                return self.remaining_results.pop(0)

        fake_module = types.SimpleNamespace(YoutubeDL=FakePlaylistYDL)
        completed = []
        errors = []
        logs = []
        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}), \
                mock.patch.object(downloader, "get_ffmpeg_path", return_value="ffmpeg"):
            downloader.Downloader()._worker(
                "https://example.com/playlist", tempfile.gettempdir(), "mp3", "128", "best",
                True, "%(title)s", "", "", None, None,
                None, logs.append, lambda *args: completed.append(args), errors.append,
            )
        return completed, errors, logs

    def test_partial_playlist_reports_only_successful_items(self):
        completed, errors, logs = self._run_playlist([0, 1, 0])
        self.assertEqual(errors, [])
        self.assertEqual(
            completed,
            [(DownloadResult(count=2, title="Test playlist", succeeded=2, failed=1),)],
        )
        self.assertTrue(any("2 saved, 1 failed" in message for message in logs))

    def test_all_failed_playlist_reports_error(self):
        completed, errors, _ = self._run_playlist([1, 1])
        self.assertEqual(completed, [])
        self.assertEqual(errors, ["Playlist failed: 2 item(s) could not be downloaded"])


class CancellationAndMetadataTests(unittest.TestCase):
    def test_cancelled_playlist_calls_cancel_callback_not_completion(self):
        cancel_event = threading.Event()
        cancel_event.set()
        fake_module = types.SimpleNamespace(YoutubeDL=_FakeYoutubeDL)
        completed = []
        cancelled = []
        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}), \
                mock.patch.object(downloader, "get_ffmpeg_path", return_value="ffmpeg"):
            downloader.Downloader()._worker(
                "https://example.com/media", tempfile.gettempdir(), "mp3", "128", "best",
                False, "%(title)s", "", "", None, None,
                None, None, lambda *args: completed.append(args), None,
                cancel_event, lambda: cancelled.append(True),
            )
        self.assertEqual(completed, [])
        self.assertEqual(cancelled, [True])

    def test_metadata_writer_touches_only_explicit_existing_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            downloaded = os.path.join(temp_dir, "downloaded.mp3")
            unrelated = os.path.join(temp_dir, "unrelated.mp3")
            for path in (downloaded, unrelated):
                with open(path, "wb") as file:
                    file.write(b"test")

            with mock.patch("metadata_editor.write_tags", return_value="") as write_tags:
                downloader.Downloader()._write_file_tags(
                    {downloaded}, {"artist": "Test"}, lambda message: None
                )

            write_tags.assert_called_once_with(downloaded, {"artist": "Test"})
            self.assertNotEqual(write_tags.call_args.args[0], unrelated)


if __name__ == "__main__":
    unittest.main()
