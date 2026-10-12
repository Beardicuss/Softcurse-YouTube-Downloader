"""
thumbnail.py - Softcurse // Thumbnail & Video Info Fetcher
Fetches YouTube video/playlist info + thumbnail asynchronously.
"""
import threading
import urllib.request
import io
import os
from urllib.parse import urlparse
from typing import Callable

# Pillow is optional — thumbnail display degrades gracefully
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def check_pil():
    return PIL_AVAILABLE


def install_pil(log_callback: Callable = None):
    import subprocess, sys
    def log(m):
        if log_callback: log_callback(m)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "Pillow"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        log("Pillow installed. Restart to enable thumbnails.")
        return True
    except Exception as e:
        log(f"Pillow install failed: {e}")
        return False


def fetch_info_and_thumb(
    url: str,
    on_info: Callable,   # called with dict: title, duration, type, count, thumb_url
    on_thumb: Callable,  # called with ImageTk.PhotoImage (or None)
    on_error: Callable,  # called with str
    thumb_size: tuple = (160, 90),
    max_thumb_bytes: int = 5 * 1024 * 1024,
):
    """Fetch video info and thumbnail asynchronously."""
    def worker():
        try:
            import yt_dlp
        except ImportError:
            on_error("yt-dlp not installed")
            return

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if info is None:
                on_error("Could not fetch info")
                return

            is_playlist = info.get("_type") == "playlist"

            if is_playlist:
                entries = [e for e in info.get("entries", []) if e]
                thumb_url = info.get("thumbnail") or (
                    entries[0].get("thumbnail") if entries else None
                )
                result = {
                    "type": "playlist",
                    "title": info.get("title", "Unknown Playlist"),
                    "count": len(entries),
                    "thumb_url": thumb_url,
                    "duration": None,
                    "channel": info.get("uploader", ""),
                }
            else:
                thumb_url = info.get("thumbnail")
                duration = info.get("duration", 0)
                mins, secs = divmod(int(duration or 0), 60)
                hrs, mins = divmod(mins, 60)
                dur_str = (f"{hrs}:{mins:02d}:{secs:02d}" if hrs
                           else f"{mins}:{secs:02d}")
                result = {
                    "type": "video",
                    "title": info.get("title", "Unknown"),
                    "duration": dur_str,
                    "count": 1,
                    "thumb_url": thumb_url,
                    "channel": info.get("uploader", ""),
                    "view_count": info.get("view_count", 0),
                    "upload_date": info.get("upload_date", ""),
                }

            on_info(result)

            # Fetch thumbnail image
            if thumb_url and PIL_AVAILABLE:
                try:
                    parsed_thumb = urlparse(thumb_url)
                    if parsed_thumb.scheme not in {"http", "https"}:
                        raise ValueError("Unsupported thumbnail URL")
                    req = urllib.request.Request(
                        thumb_url,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        declared_size = resp.headers.get("Content-Length")
                        if declared_size and int(declared_size) > max_thumb_bytes:
                            raise ValueError("Thumbnail is too large")
                        data = resp.read(max_thumb_bytes + 1)
                    if len(data) > max_thumb_bytes:
                        raise ValueError("Thumbnail is too large")
                    img = Image.open(io.BytesIO(data))
                    img = img.convert("RGB")
                    img.thumbnail(thumb_size, Image.LANCZOS)
                    # Add cyan border
                    bordered = Image.new("RGB",
                        (img.width + 4, img.height + 4), (0, 255, 255))
                    bordered.paste(img, (2, 2))
                    photo = ImageTk.PhotoImage(bordered)
                    on_thumb(photo)
                except Exception:
                    on_thumb(None)
            else:
                on_thumb(None)

        except Exception as e:
            on_error(str(e))

    threading.Thread(target=worker, daemon=True).start()
