"""Typed messages shared by the download service and presentation layer."""

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class DownloadStatus(str, Enum):
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    PLAYLIST = "playlist"


@dataclass(frozen=True)
class DownloadRequest:
    url: str
    output_folder: str
    mode: str = "mp3"
    quality: str = "320"
    video_quality: str = "best"
    is_playlist: bool = False
    filename_template: str = "%(title)s"
    clip_start: str = ""
    clip_end: str = ""
    sponsorblock_cats: tuple[str, ...] | None = None
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is not None:
            object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class ProgressUpdate:
    status: DownloadStatus
    mode: str
    filename: str = ""
    percent: float = 0.0
    speed: str = ""
    eta: str = ""
    current: int = 0
    total: int = 0
    title: str = ""


@dataclass(frozen=True)
class DownloadResult:
    count: int
    title: str
    succeeded: int
    failed: int = 0
