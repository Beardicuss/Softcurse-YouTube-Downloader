"""Canonical application identity and resource lookup."""

import os
import sys

APP_NAME = "Softcurse Media Downloader"

def resource_path(*parts: str) -> str:
    """Resolve a packaged or source-tree resource without using the working directory."""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, *parts)


def _read_version() -> str:
    path = resource_path("VERSION")
    try:
        with open(path, encoding="utf-8") as file:
            return file.read().strip()
    except OSError:
        return "0.0.0"


APP_VERSION = _read_version()
APP_TITLE = f"Softcurse // Media Downloader v{APP_VERSION}"


def icon_path() -> str | None:
    candidates = [
        resource_path("assets", "yt.ico"),
        resource_path("yt.ico"),
    ]
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(os.path.dirname(sys.executable), "yt.ico"))
    return next((path for path in candidates if os.path.isfile(path)), None)
