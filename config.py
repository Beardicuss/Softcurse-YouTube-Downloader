"""
config.py - Softcurse // Settings persistence v4
"""
import json, os

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".softcurse_config.json")

DEFAULT_CONFIG = {
    "output_folder":       os.path.join(os.path.expanduser("~"), "Music"),
    "mp4_output_folder":   os.path.join(os.path.expanduser("~"), "Videos"),
    "quality":             "320",
    "video_quality":       "best",
    "audio_format":        "mp3",     # mp3 / flac / wav
    "last_url":            "",
    "filename_template":   "%(title)s",
    "minimize_to_tray":    False,
    "notify_on_complete":  True,
    "crt_effects":         True,
    "sponsorblock":        False,
    "sb_categories":       ["sponsor","intro","outro","selfpromo","interaction"],
    "theme":               "softcurse",
}

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Config] Save failed: {e}")
