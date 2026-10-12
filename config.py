"""
config.py - Softcurse // Settings persistence v1.0
"""
import json
import logging
import os

from storage import app_data_dir, atomic_write_json, preserve_corrupt_file

LOGGER = logging.getLogger(__name__)
CONFIG_VERSION = 1
LEGACY_CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".softcurse_config.json")
CONFIG_FILE = os.path.join(app_data_dir(), "config.json")

DEFAULT_CONFIG = {
    "schema_version":      CONFIG_VERSION,
    "output_folder":       os.path.join(os.path.expanduser("~"), "Music"),
    "mp4_output_folder":   os.path.join(os.path.expanduser("~"), "Videos"),
    "quality":             "320",
    "video_quality":       "best",
    "audio_format":        "mp3",     # mp3 / flac / wav
    "last_url":            "",
    "filename_template":   "%(title)s",
    "minimize_to_tray":    False,
    "notify_on_complete":  True,
    "first_run_complete":  False,
    "crt_effects":         True,
    "reduced_motion":      False,
    "sponsorblock":        False,
    "sb_categories":       ["sponsor","intro","outro","selfpromo","interaction"],
}


def _normalize_config(value: dict) -> dict:
    normalized = DEFAULT_CONFIG.copy()
    for key, default in DEFAULT_CONFIG.items():
        if key == "schema_version" or key not in value:
            continue
        candidate = value[key]
        if isinstance(default, bool):
            if isinstance(candidate, bool):
                normalized[key] = candidate
        elif isinstance(default, str):
            if isinstance(candidate, str):
                normalized[key] = candidate
        elif isinstance(default, list):
            if isinstance(candidate, list) and all(isinstance(item, str) for item in candidate):
                normalized[key] = candidate
    if normalized["audio_format"] not in {"mp3", "flac", "wav"}:
        normalized["audio_format"] = DEFAULT_CONFIG["audio_format"]
    if normalized["quality"] not in {"128", "192", "256", "320"}:
        normalized["quality"] = DEFAULT_CONFIG["quality"]
    if normalized["video_quality"] not in {"best", "1080", "720", "480", "360"}:
        normalized["video_quality"] = DEFAULT_CONFIG["video_quality"]
    return normalized


def _migrate_legacy_config():
    if os.path.exists(CONFIG_FILE) or not os.path.exists(LEGACY_CONFIG_FILE):
        return
    try:
        with open(LEGACY_CONFIG_FILE, "r", encoding="utf-8") as file:
            legacy = json.load(file)
        if not isinstance(legacy, dict):
            raise ValueError("legacy configuration is not an object")
        atomic_write_json(CONFIG_FILE, _normalize_config(legacy))
        LOGGER.info("Migrated legacy configuration to %s", CONFIG_FILE)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        LOGGER.warning("Could not migrate legacy configuration: %s", error)

def load_config() -> dict:
    _migrate_legacy_config()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if not isinstance(loaded, dict):
                raise ValueError("configuration root must be an object")
            return _normalize_config(loaded)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            backup = preserve_corrupt_file(CONFIG_FILE)
            LOGGER.warning("Malformed configuration ignored (%s); preserved at %s", error, backup)
    return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    try:
        atomic_write_json(CONFIG_FILE, _normalize_config(config))
    except OSError as error:
        LOGGER.error("Configuration save failed: %s", error)
