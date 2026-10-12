"""Shared, recoverable JSON persistence helpers."""

import json
import logging
import os
import tempfile
import time

LOGGER = logging.getLogger(__name__)
APP_DIR_NAME = "Softcurse Media Downloader"


def app_data_dir() -> str:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".softcurse")
    return os.path.join(base, APP_DIR_NAME)


def atomic_write_json(path: str, value) -> None:
    """Write JSON beside its destination and atomically replace the old file."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    descriptor, temp_path = tempfile.mkstemp(prefix=".softcurse-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(value, file, indent=2, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, path)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise


def preserve_corrupt_file(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    backup = f"{path}.corrupt-{time.strftime('%Y%m%d-%H%M%S')}"
    try:
        os.replace(path, backup)
        return backup
    except OSError as error:
        LOGGER.warning("Could not preserve malformed data file %s: %s", path, error)
        return None

