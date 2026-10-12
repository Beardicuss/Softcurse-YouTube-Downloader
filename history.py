"""
history.py - Softcurse // Download History Manager
Persists download records to ~/.softcurse_history.json
"""
import json
import logging
import os
import time
from typing import List, Dict

from storage import app_data_dir, atomic_write_json, preserve_corrupt_file

LOGGER = logging.getLogger(__name__)
LEGACY_HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".softcurse_history.json")
HISTORY_FILE = os.path.join(app_data_dir(), "history.json")
MAX_ENTRIES = 500


def _migrate_legacy_history():
    if os.path.exists(HISTORY_FILE) or not os.path.exists(LEGACY_HISTORY_FILE):
        return
    try:
        with open(LEGACY_HISTORY_FILE, "r", encoding="utf-8") as file:
            legacy = json.load(file)
        if not isinstance(legacy, list):
            raise ValueError("legacy history is not a list")
        atomic_write_json(HISTORY_FILE, legacy[-MAX_ENTRIES:])
        LOGGER.info("Migrated legacy history to %s", HISTORY_FILE)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        LOGGER.warning("Could not migrate legacy history: %s", error)


def _load_raw() -> List[Dict]:
    _migrate_legacy_history()
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, list):
            raise ValueError("history root must be a list")
        return [entry for entry in loaded if isinstance(entry, dict)]
    except (OSError, ValueError, json.JSONDecodeError) as error:
        backup = preserve_corrupt_file(HISTORY_FILE)
        LOGGER.warning("Malformed history ignored (%s); preserved at %s", error, backup)
        return []


def _save_raw(entries: List[Dict]):
    try:
        atomic_write_json(HISTORY_FILE, entries[-MAX_ENTRIES:])
    except OSError as error:
        LOGGER.error("History save failed: %s", error)


def add_entry(title: str, url: str, mode: str, output_folder: str,
              count: int = 1, status: str = "success"):
    entries = _load_raw()
    entries.append({
        "id": int(time.time() * 1000),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "title": title,
        "url": url,
        "mode": mode,          # "mp3" or "mp4"
        "folder": output_folder,
        "count": count,
        "status": status,      # "success" or "failed"
    })
    _save_raw(entries)


def add_failed_entry(url: str, mode: str, output_folder: str, error: str = ""):
    entries = _load_raw()
    entries.append({
        "id": int(time.time() * 1000),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "title": url[:80],
        "url": url,
        "mode": mode,
        "folder": output_folder,
        "count": 0,
        "status": "failed",
        "error": error[:200],
    })
    _save_raw(entries)


def load_history() -> List[Dict]:
    return list(reversed(_load_raw()))  # newest first


def filter_history(entries, query: str):
    query = query.strip().lower()
    if not query:
        return list(entries)
    keys = ("title", "url", "mode", "status", "folder")
    return [
        entry for entry in entries
        if query in " ".join(str(entry.get(key, "")) for key in keys).lower()
    ]


def clear_history():
    _save_raw([])


def delete_entry(entry_id: int):
    entries = _load_raw()
    entries = [e for e in entries if e.get("id") != entry_id]
    _save_raw(entries)
