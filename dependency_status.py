"""Read-only runtime readiness checks used by startup and Settings."""

from dataclasses import dataclass

from downloader import check_ytdlp, get_ffmpeg_path
from metadata_editor import check_mutagen
from player import check_pygame
from thumbnail import check_pil
from tray import check_tray_deps


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    available: bool
    required: bool
    purpose: str


def collect_dependency_status():
    tray = check_tray_deps()
    return (
        DependencyStatus("yt-dlp", check_ytdlp(), True, "media extraction"),
        DependencyStatus("FFmpeg", bool(get_ffmpeg_path()), True, "conversion and merging"),
        DependencyStatus("Pillow", check_pil(), False, "thumbnail previews"),
        DependencyStatus("mutagen", check_mutagen(), False, "metadata editing"),
        DependencyStatus("pygame", check_pygame(), False, "audio player"),
        DependencyStatus(
            "pystray + plyer",
            tray["pystray"] and tray["plyer"],
            False,
            "tray and notifications",
        ),
    )


def required_ready(statuses) -> bool:
    return all(status.available for status in statuses if status.required)

