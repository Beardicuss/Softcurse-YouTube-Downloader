"""
downloader.py - Softcurse // Download Engine v1.0
Modes: MP3, FLAC, WAV, MP4
Features: SponsorBlock, clip/trim, filename templates, playlists, metadata injection
"""
import os, sys, subprocess, threading
from typing import Callable, List, Tuple


def get_ffmpeg_path():
    bases = [os.path.dirname(os.path.abspath(__file__))]
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        bases.append(exe_dir)
        bases.append(os.path.abspath(os.path.join(exe_dir, '..')))
        
    for base in bases:
        for sub in ["ffmpeg", "{ffmpeg}", ""]:
            c = os.path.join(base, sub, "ffmpeg.exe")
            if os.path.exists(c):
                return c
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        if r.returncode == 0:
            return "ffmpeg"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def check_ytdlp():
    try:
        import yt_dlp; return True
    except ImportError:
        return False


def install_ytdlp(log_callback: Callable = None):
    def log(m):
        if log_callback: log_callback(m)
    log("Installing yt-dlp...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "yt-dlp", "--upgrade"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("yt-dlp installed!"); return True
    except subprocess.CalledProcessError as e:
        log(f"Failed: {e}"); return False


def update_ytdlp(log_callback: Callable = None):
    """Update yt-dlp to latest version."""
    def log(m):
        if log_callback: log_callback(m)
    log("Updating yt-dlp...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "yt-dlp", "--upgrade", "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("✅ yt-dlp updated!"); return True
    except Exception as e:
        log(f"❌ Update failed: {e}"); return False


def _parse_time(t: str) -> str:
    t = t.strip()
    if not t: return ""
    parts = t.split(":")
    try:
        [int(p) for p in parts]
    except ValueError:
        return ""
    if len(parts) == 2:
        return f"00:{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    if len(parts) == 3:
        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
    return t


def _time_to_secs(t: str) -> float:
    parts = t.strip().split(":")
    try:
        p = [float(x) for x in parts]
        if len(p) == 3: return p[0]*3600 + p[1]*60 + p[2]
        if len(p) == 2: return p[0]*60 + p[1]
        return p[0]
    except Exception:
        return 0.0


# ── Audio mode configs ────────────────────────────────────────────────────────
AUDIO_MODES = {
    "mp3":  {"codec": "mp3",  "ext": "mp3",  "thumb": True},
    "flac": {"codec": "flac", "ext": "flac", "thumb": False},
    "wav":  {"codec": "wav",  "ext": "wav",  "thumb": False},
}


class Downloader:
    def __init__(self):
        self._cancel_flag = False

    def cancel(self):
        self._cancel_flag = True

    def download(
        self,
        url: str,
        output_folder: str,
        mode: str = "mp3",            # "mp3","flac","wav","mp4"
        quality: str = "320",         # kbps for mp3
        video_quality: str = "best",
        is_playlist: bool = False,
        filename_template: str = "%(title)s",
        clip_start: str = "",
        clip_end: str = "",
        sponsorblock_cats: List[str] = None,  # None = disabled
        metadata: dict = None,                # pre-set tags to embed
        on_progress: Callable = None,
        on_log: Callable = None,
        on_complete: Callable = None,
        on_error: Callable = None,
    ):
        self._cancel_flag = False
        thread = threading.Thread(
            target=self._worker,
            args=(url, output_folder, mode, quality, video_quality,
                  is_playlist, filename_template, clip_start, clip_end,
                  sponsorblock_cats, metadata,
                  on_progress, on_log, on_complete, on_error),
            daemon=True)
        thread.start()
        return thread

    def _worker(
        self, url, output_folder, mode, quality, video_quality,
        is_playlist, filename_template, clip_start, clip_end,
        sponsorblock_cats, metadata,
        on_progress, on_log, on_complete, on_error
    ):
        def log(m):
            if on_log: on_log(m)
        def prog(d):
            if on_progress: on_progress(d)

        class YtdlpLogger:
            """Forward yt-dlp diagnostics to the UI instead of hiding failures."""
            def debug(self, message):
                # yt-dlp sends informational messages through debug(). Keep the
                # UI readable while preserving warnings and errors below.
                if message.startswith("[debug]"):
                    return
                log(message)

            def warning(self, message):
                log(f"⚠️  {message}")

            def error(self, message):
                log(f"❌ {message}")

        try:
            import yt_dlp
        except ImportError:
            if on_error: on_error("yt-dlp not installed. Run: pip install yt-dlp")
            return

        ffmpeg = get_ffmpeg_path()
        if not ffmpeg:
            if on_error:
                on_error("ffmpeg not found!\nInstall: winget install ffmpeg\n"
                         "Or place ffmpeg.exe in ./ffmpeg/")
            return

        os.makedirs(output_folder, exist_ok=True)

        # ── SponsorBlock pre-fetch ────────────────────────────────────────────
        sb_ranges = None
        if sponsorblock_cats and mode != "mp4":
            try:
                from sponsorblock import fetch_segments, segments_to_keep_ranges, format_segments_summary
                log("🔍 Querying SponsorBlock...")
                segs, vid_id = fetch_segments(url, categories=sponsorblock_cats)
                if segs:
                    log(format_segments_summary(segs))
                    sb_ranges = segments_to_keep_ranges(segs)
                else:
                    log("ℹ️  No SponsorBlock segments found — downloading full video")
            except Exception as e:
                log(f"⚠️  SponsorBlock error: {e} — downloading full video")

        # ── Clip / Trim ───────────────────────────────────────────────────────
        t_start    = _parse_time(clip_start)
        t_end      = _parse_time(clip_end)
        using_clip = bool(t_start or t_end)
        if using_clip:
            log(f"✂️  Clip: {t_start or 'start'} → {t_end or 'end'}")

        # ── Format selection ──────────────────────────────────────────────────
        if mode in AUDIO_MODES:
            cfg  = AUDIO_MODES[mode]
            fmt  = "bestaudio/best"
            pp = [
                {"key": "FFmpegExtractAudio",
                 "preferredcodec": cfg["codec"],
                 "preferredquality": quality if mode == "mp3" else "0"},
                {"key": "FFmpegMetadata", "add_metadata": True},
            ]
            if cfg["thumb"]:
                pp.append({"key": "EmbedThumbnail"})
            write_thumb = cfg["thumb"]
            merge_fmt   = None
        else:
            # mp4
            if video_quality == "best":
                fmt = "bestvideo+bestaudio/best"
            else:
                h   = video_quality
                fmt = (f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best")
            pp = [
                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
                {"key": "FFmpegMetadata", "add_metadata": True},
            ]
            write_thumb = False
            merge_fmt   = "mp4"

        tmpl   = (filename_template or "%(title)s").strip()
        outtmpl = os.path.join(output_folder, tmpl + ".%(ext)s")

        def ydl_hook(d):
            if self._cancel_flag:
                raise Exception("Download cancelled by user.")
            status   = d.get("status", "")
            filename = os.path.basename(d.get("filename", ""))
            if status == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                speed = d.get("speed", 0) or 0
                eta   = d.get("eta",   0) or 0
                pct   = (downloaded / total * 100) if total > 0 else 0
                prog({
                    "status": "downloading", "filename": filename,
                    "percent": pct,
                    "speed": f"{speed/1024:.1f} KB/s" if speed else "-- KB/s",
                    "eta":   f"{eta}s" if eta else "--",
                    "mode":  mode,
                })
            elif status == "finished":
                labels = {"mp3":"Converting→MP3","flac":"Converting→FLAC",
                          "wav":"Converting→WAV","mp4":"Merging video"}
                log(f"✅ {labels.get(mode,'Processing')}: {filename}")
                prog({"status":"converting","filename":filename,"percent":100,"mode":mode})
            elif status == "error":
                log(f"❌ Error: {filename}")

        ffmpeg_dir = os.path.dirname(ffmpeg) if ffmpeg != "ffmpeg" else None
        ydl_opts = {
            "format":        fmt,
            "outtmpl":       outtmpl,
            "postprocessors": pp,
            "progress_hooks": [ydl_hook],
            "quiet":         True,
            "no_warnings":   False,
            "logger":        YtdlpLogger(),
            "writethumbnail": write_thumb,
            "noplaylist":    not is_playlist,
            # Never report success when extraction, download, or conversion
            # failed. With ignoreerrors=True yt-dlp could leave only the
            # thumbnail behind and return control as though the media existed.
            "ignoreerrors":  False,
        }
        if ffmpeg_dir:
            ydl_opts["ffmpeg_location"] = ffmpeg_dir
        if merge_fmt:
            ydl_opts["merge_output_format"] = merge_fmt

        # ── Download ranges (SponsorBlock or Clip, mutually exclusive) ────────
        if sb_ranges and not using_clip:
            ydl_opts["download_ranges"] = yt_dlp.utils.download_range_func(
                None, sb_ranges)
            ydl_opts["force_keyframes_at_cuts"] = True
        elif using_clip:
            s0 = _time_to_secs(t_start) if t_start else 0
            e0 = _time_to_secs(t_end)   if t_end   else float("inf")
            ydl_opts["download_ranges"] = yt_dlp.utils.download_range_func(
                None, [(s0, e0)])
            ydl_opts["force_keyframes_at_cuts"] = True

        # ── Run download ──────────────────────────────────────────────────────
        downloaded_files = []

        try:
            log("🔍 Fetching info...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    if on_error: on_error("Could not fetch info. Check the URL.")
                    return

                if info.get("_type") == "playlist":
                    entries = [e for e in info.get("entries", []) if e]
                    total   = len(entries)
                    log(f"📂 Playlist: '{info.get('title')}' — {total} items")
                    for i, entry in enumerate(entries):
                        if self._cancel_flag:
                            log("⛔ Cancelled."); break
                        title = entry.get("title", f"Item {i+1}")
                        log(f"⬇️  [{i+1}/{total}] {title}")
                        prog({"status":"playlist","current":i+1,
                              "total":total,"title":title,"percent":0})
                        try:
                            entry_url = entry.get("webpage_url") or entry.get("url")
                            if not entry_url:
                                raise RuntimeError("Playlist entry has no downloadable URL")
                            result = ydl.download([entry_url])
                            if result:
                                raise RuntimeError(f"yt-dlp returned error code {result}")
                        except Exception as e:
                            log(f"⚠️  Skipped: {title} ({e})")
                    if not self._cancel_flag:
                        ext_l = mode.upper()
                        log(f"🎉 Playlist done! {total} {ext_l} files saved.")
                        # Write metadata to folder after download
                        if metadata and any(metadata.values()):
                            self._write_folder_tags(output_folder, metadata, log)
                        if on_complete: on_complete(total, info.get("title","Playlist"))
                else:
                    title = info.get("title","Unknown")
                    log(f"⬇️  [{mode.upper()}] {title}")
                    result = ydl.download([url])
                    if result:
                        raise RuntimeError(f"yt-dlp returned error code {result}")
                    log(f"🎉 Done! Saved to: {output_folder}")
                    # Write metadata to the file
                    if metadata and any(metadata.values()):
                        self._write_folder_tags(output_folder, metadata, log)
                    if on_complete: on_complete(1, title)

        except Exception as e:
            if "cancelled" in str(e).lower():
                log("⛔ Download cancelled.")
            else:
                if on_error: on_error(str(e))

    def _write_folder_tags(self, folder: str, tags: dict, log: Callable):
        try:
            from metadata_editor import write_tags_to_folder
            count, errors = write_tags_to_folder(folder, tags)
            if count:
                log(f"🏷️  Tags written to {count} file(s)")
            for e in errors:
                log(f"⚠️  Tag error: {e}")
        except Exception as e:
            log(f"⚠️  Could not write tags: {e}")
