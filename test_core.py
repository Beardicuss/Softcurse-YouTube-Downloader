import json
import os
import tempfile
import tomllib
import unittest
from unittest import mock

import config
import downloader
import history
import sponsorblock
import storage
from app_info import APP_VERSION, icon_path, resource_path
from download_models import DownloadRequest, DownloadStatus, ProgressUpdate
from download_queue import DownloadQueue, QueueStatus
from preview_controller import PreviewRequestCoordinator
from player import AudioPlayer
from ux_state import present_error
from dependency_status import DependencyStatus, required_ready
from update_checker import UpdateInfo, check_for_update


class TimeParsingTests(unittest.TestCase):
    def test_normalizes_minute_and_hour_timestamps(self):
        self.assertEqual(downloader._parse_time("2:05"), "00:02:05")
        self.assertEqual(downloader._parse_time("1:02:03"), "01:02:03")

    def test_rejects_non_numeric_timestamp(self):
        self.assertEqual(downloader._parse_time("not-a-time"), "")

    def test_converts_supported_timestamp_shapes_to_seconds(self):
        self.assertEqual(downloader._time_to_secs("01:02:03"), 3723)
        self.assertEqual(downloader._time_to_secs("02:03"), 123)
        self.assertEqual(downloader._time_to_secs("4.5"), 4.5)

    def test_request_validation_rejects_invalid_format_and_clip(self):
        with self.assertRaisesRegex(ValueError, "Unsupported output format"):
            downloader.validate_request(
                "https://example.com/media", ".", "avi", "320", "best", "", ""
            )
        with self.assertRaisesRegex(ValueError, "later than"):
            downloader.validate_request(
                "https://example.com/media", ".", "mp3", "320", "best", "2:00", "1:00"
            )

    def test_request_validation_rejects_out_of_range_timestamp_parts(self):
        with self.assertRaisesRegex(ValueError, "seconds must be below 60"):
            downloader.validate_request(
                "https://example.com/media", ".", "mp3", "320", "best", "1:60", ""
            )


class AudioPlayerTests(unittest.TestCase):
    def test_stop_keeps_loaded_track_available_for_replay(self):
        mixer = mock.Mock()
        player = AudioPlayer()
        player._mixer = mixer
        player._loaded = True

        player.stop()
        player.play()

        self.assertTrue(player._loaded)
        mixer.music.stop.assert_called_once_with()
        mixer.music.play.assert_called_once_with()


class SponsorBlockTests(unittest.TestCase):
    def test_extracts_common_youtube_video_ids(self):
        video_id = "abcdefghijk"
        self.assertEqual(
            sponsorblock._extract_video_id(f"https://youtu.be/{video_id}?si=123"),
            video_id,
        )

    def test_extracts_shorts_and_rejects_lookalike_domains(self):
        video_id = "abcdefghijk"
        self.assertEqual(
            sponsorblock._extract_video_id(f"https://youtube.com/shorts/{video_id}"),
            video_id,
        )
        self.assertIsNone(
            sponsorblock._extract_video_id(f"https://youtube.com.example/shorts/{video_id}")
        )
        self.assertEqual(
            sponsorblock._extract_video_id(
                f"https://www.youtube.com/watch?v={video_id}&list=example"
            ),
            video_id,
        )

    def test_builds_keep_ranges_around_sorted_skip_segments(self):
        segments = [
            {"start": 20, "end": 30},
            {"start": 5, "end": 10},
        ]
        self.assertEqual(
            sponsorblock.segments_to_keep_ranges(segments, total_duration=40),
            [(0.0, 5), (10, 20), (30, 40)],
        )

    def test_overlapping_skip_segments_do_not_create_negative_ranges(self):
        segments = [
            {"start": 5, "end": 15},
            {"start": 10, "end": 20},
        ]
        self.assertEqual(
            sponsorblock.segments_to_keep_ranges(segments, total_duration=25),
            [(0.0, 5), (20, 25)],
        )

    def test_invalid_and_out_of_bounds_segments_are_normalized(self):
        segments = [
            {"start": -10, "end": 5},
            {"start": 8, "end": 6},
            {"start": "bad", "end": 9},
            {"start": 15, "end": 40},
        ]
        self.assertEqual(
            sponsorblock.segments_to_keep_ranges(segments, total_duration=20),
            [(5.0, 15.0)],
        )


class ConfigPersistenceTests(unittest.TestCase):
    def test_round_trip_preserves_values_and_supplies_new_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "config.json")
            legacy_path = os.path.join(temp_dir, "legacy.json")
            with mock.patch.object(config, "CONFIG_FILE", path), \
                    mock.patch.object(config, "LEGACY_CONFIG_FILE", legacy_path):
                saved = {"quality": "128", "crt_effects": False}
                config.save_config(saved)
                loaded = config.load_config()

        self.assertEqual(loaded["quality"], "128")
        self.assertFalse(loaded["crt_effects"])
        self.assertIn("output_folder", loaded)

    def test_malformed_config_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "config.json")
            with open(path, "w", encoding="utf-8") as file:
                file.write("{broken")
            legacy_path = os.path.join(temp_dir, "legacy.json")
            with mock.patch.object(config, "CONFIG_FILE", path), \
                    mock.patch.object(config, "LEGACY_CONFIG_FILE", legacy_path):
                loaded = config.load_config()

        self.assertEqual(loaded, config.DEFAULT_CONFIG)

    def test_legacy_config_is_migrated_without_deleting_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "new", "config.json")
            legacy_path = os.path.join(temp_dir, "legacy.json")
            with open(legacy_path, "w", encoding="utf-8") as file:
                json.dump({"quality": "192"}, file)
            with mock.patch.object(config, "CONFIG_FILE", path), \
                    mock.patch.object(config, "LEGACY_CONFIG_FILE", legacy_path):
                loaded = config.load_config()

            self.assertEqual(loaded["quality"], "192")
            self.assertTrue(os.path.exists(path))
            self.assertTrue(os.path.exists(legacy_path))

    def test_invalid_config_types_and_choices_fall_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "config.json")
            with open(path, "w", encoding="utf-8") as file:
                json.dump({"quality": "999", "crt_effects": "yes", "sb_categories": [1]}, file)
            with mock.patch.object(config, "CONFIG_FILE", path), \
                    mock.patch.object(config, "LEGACY_CONFIG_FILE", os.path.join(temp_dir, "legacy")):
                loaded = config.load_config()

        self.assertEqual(loaded["quality"], config.DEFAULT_CONFIG["quality"])
        self.assertEqual(loaded["crt_effects"], config.DEFAULT_CONFIG["crt_effects"])
        self.assertEqual(loaded["sb_categories"], config.DEFAULT_CONFIG["sb_categories"])


class HistoryPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.history_path = os.path.join(self.temp_dir.name, "history.json")
        self.path_patch = mock.patch.object(history, "HISTORY_FILE", self.history_path)
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)
        self.legacy_patch = mock.patch.object(
            history, "LEGACY_HISTORY_FILE", os.path.join(self.temp_dir.name, "legacy.json")
        )
        self.legacy_patch.start()
        self.addCleanup(self.legacy_patch.stop)

    def test_add_load_and_delete_entry(self):
        history.add_entry("Example", "https://example.com", "mp3", self.temp_dir.name)
        entries = history.load_history()

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "Example")
        self.assertEqual(entries[0]["status"], "success")

        history.delete_entry(entries[0]["id"])
        self.assertEqual(history.load_history(), [])

    def test_history_is_capped_to_configured_limit(self):
        records = [{"id": number} for number in range(5)]
        with mock.patch.object(history, "MAX_ENTRIES", 3):
            history._save_raw(records)

        with open(self.history_path, encoding="utf-8") as file:
            persisted = json.load(file)
        self.assertEqual([entry["id"] for entry in persisted], [2, 3, 4])

    def test_history_filter_searches_user_visible_fields(self):
        entries = [
            {"title": "Ambient Mix", "mode": "mp3", "status": "success", "folder": "Music"},
            {"title": "Tutorial", "mode": "mp4", "status": "failed", "folder": "Videos"},
        ]
        self.assertEqual(history.filter_history(entries, "ambient"), [entries[0]])
        self.assertEqual(history.filter_history(entries, "FAILED"), [entries[1]])
        self.assertEqual(history.filter_history(entries, ""), entries)


class AtomicStorageTests(unittest.TestCase):
    def test_atomic_json_write_replaces_existing_document(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "nested", "data.json")
            storage.atomic_write_json(path, {"version": 1})
            storage.atomic_write_json(path, {"version": 2})
            with open(path, encoding="utf-8") as file:
                self.assertEqual(json.load(file), {"version": 2})
            leftovers = [name for name in os.listdir(os.path.dirname(path)) if name.endswith(".tmp")]
            self.assertEqual(leftovers, [])


class ArchitectureFoundationTests(unittest.TestCase):
    def test_source_resource_resolution_does_not_depend_on_working_directory(self):
        expected = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "yt.ico"))
        self.assertEqual(os.path.abspath(resource_path("assets", "yt.ico")), expected)
        self.assertEqual(os.path.abspath(icon_path()), expected)

    def test_download_progress_messages_are_typed_and_immutable(self):
        update = ProgressUpdate(
            status=DownloadStatus.DOWNLOADING,
            mode="mp3",
            percent=50,
        )
        self.assertEqual(update.status, DownloadStatus.DOWNLOADING)
        self.assertEqual(update.percent, 50)
        with self.assertRaises(AttributeError):
            update.percent = 75

    def test_download_requests_snapshot_mutable_user_metadata(self):
        metadata = {"artist": "Example"}
        request = DownloadRequest(
            url="https://example.com/media",
            output_folder=".",
            metadata=metadata,
        )
        metadata["artist"] = "Changed"
        self.assertEqual(request.metadata["artist"], "Example")

    def test_application_version_uses_semantic_version_shape(self):
        self.assertRegex(APP_VERSION, r"^\d+\.\d+\.\d+$")
        with open("VERSION", encoding="utf-8") as file:
            self.assertEqual(APP_VERSION, file.read().strip())
        with open("pyproject.toml", "rb") as file:
            self.assertEqual(APP_VERSION, tomllib.load(file)["project"]["version"])

    def test_preview_coordinator_rejects_stale_and_duplicate_requests(self):
        coordinator = PreviewRequestCoordinator()
        self.assertTrue(coordinator.begin("https://example.com/first"))
        self.assertFalse(coordinator.begin("https://example.com/first"))
        self.assertTrue(coordinator.begin("https://example.com/second"))
        self.assertFalse(coordinator.is_current("https://example.com/first"))
        self.assertTrue(coordinator.is_current("https://example.com/second"))

    def test_errors_are_presented_with_actionable_categories(self):
        dependency = present_error("ffmpeg not found")
        self.assertEqual(dependency.category, "DEPENDENCY")
        self.assertIn("Install", dependency.action)
        invalid = present_error("Invalid clip start")
        self.assertEqual(invalid.category, "INPUT")

    def test_readiness_requires_only_required_components(self):
        statuses = (
            DependencyStatus("required", True, True, "core"),
            DependencyStatus("optional", False, False, "extra"),
        )
        self.assertTrue(required_ready(statuses))
        self.assertFalse(required_ready((
            DependencyStatus("required", False, True, "core"),
        )))

    def test_update_comparison_and_bounded_release_response(self):
        self.assertTrue(UpdateInfo("1.0.0", "1.1.0", "https://github.com/example").available)
        self.assertFalse(UpdateInfo("1.1.0", "1.1.0", "https://github.com/example").available)

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, size):
                return json.dumps({
                    "tag_name": "v1.2.0",
                    "html_url": "https://github.com/Beardicuss/Softcurse-YouTube-Downloader/releases/tag/v1.2.0",
                }).encode()

        with mock.patch("urllib.request.urlopen", return_value=FakeResponse()):
            info = check_for_update("1.0.0")
        self.assertTrue(info.available)
        self.assertEqual(info.latest_version, "1.2.0")


class DownloadQueueTests(unittest.TestCase):
    def test_queue_deduplicates_and_runs_items_in_order(self):
        queue = DownloadQueue()
        added = queue.add_urls([
            "https://example.com/one",
            "https://example.com/one",
            "not-a-url",
            "https://example.com/two",
        ])
        self.assertEqual(len(added), 2)

        first = queue.next_pending()
        self.assertEqual(first.url, "https://example.com/one")
        self.assertIsNone(queue.next_pending())
        queue.finish(first.id, QueueStatus.COMPLETE)

        second = queue.next_pending()
        self.assertEqual(second.url, "https://example.com/two")
        queue.finish(second.id, QueueStatus.FAILED, "test failure")
        self.assertEqual([item.status for item in queue.items], [
            QueueStatus.COMPLETE, QueueStatus.FAILED,
        ])

    def test_only_pending_items_can_be_removed(self):
        queue = DownloadQueue()
        first, second = queue.add_urls([
            "https://example.com/one", "https://example.com/two",
        ])
        queue.next_pending()
        self.assertFalse(queue.remove_pending(first.id))
        self.assertTrue(queue.remove_pending(second.id))


if __name__ == "__main__":
    unittest.main()
