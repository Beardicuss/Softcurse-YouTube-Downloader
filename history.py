"""
history.py - Softcurse // Download History Manager
Persists download records to ~/.softcurse_history.json
"""
import json
import os
import time
from typing import List, Dict

HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".softcurse_history.json")
MAX_ENTRIES = 500


def _load_raw() -> List[Dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_raw(entries: List[Dict]):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(entries[-MAX_ENTRIES:], f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[History] Save failed: {e}")


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


def clear_history():
    _save_raw([])


def delete_entry(entry_id: int):
    entries = _load_raw()
    entries = [e for e in entries if e.get("id") != entry_id]
    _save_raw(entries)
