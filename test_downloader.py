import sys
import tempfile
import types
import unittest
from unittest import mock

import downloader


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
        self.assertEqual(completed, [(1, "Test media")])


if __name__ == "__main__":
    unittest.main()
