"""
downloader.py - Softcurse // Download Engine v1.0
Modes: MP3, FLAC, WAV, MP4
Features: SponsorBlock, clip/trim, filename templates, playlists, metadata injection
"""
import os, sys, subprocess, threading
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

from download_models import DownloadRequest, DownloadResult, DownloadStatus, ProgressUpdate


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


VALID_MODES = {"mp3", "flac", "wav", "mp4"}
VALID_AUDIO_QUALITIES = {"128", "192", "256", "320"}
VALID_VIDEO_QUALITIES = {"best", "1080", "720", "480", "360"}


def _validated_time(value: str, label: str) -> float | None:
    """Validate a user timestamp and return seconds, or None when omitted."""
    value = value.strip()
    if not value:
        return None
    parts = value.split(":")
    if len(parts) not in (1, 2, 3):
        raise ValueError(f"Invalid {label}: use SS, MM:SS, or HH:MM:SS")
    try:
        numbers = [float(part) for part in parts]
    except ValueError as exc:
        raise ValueError(f"Invalid {label}: use numbers only") from exc
    if any(number < 0 for number in numbers):
        raise ValueError(f"Invalid {label}: time cannot be negative")
    if len(numbers) >= 2 and numbers[-1] >= 60:
        raise ValueError(f"Invalid {label}: seconds must be below 60")
    if len(numbers) == 3 and numbers[-2] >= 60:
        raise ValueError(f"Invalid {label}: minutes must be below 60")
    if len(numbers) == 3:
        return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
    if len(numbers) == 2:
        return numbers[0] * 60 + numbers[1]
    return numbers[0]


def validate_request(url, output_folder, mode, quality, video_quality, clip_start, clip_end):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Enter a valid HTTP or HTTPS media URL")
    if not output_folder or not output_folder.strip():
        raise ValueError("Choose an output folder")
    if mode not in VALID_MODES:
        raise ValueError(f"Unsupported output format: {mode}")
    if mode == "mp3" and quality not in VALID_AUDIO_QUALITIES:
        raise ValueError(f"Unsupported MP3 quality: {quality}")
    if mode == "mp4" and video_quality not in VALID_VIDEO_QUALITIES:
        raise ValueError(f"Unsupported video quality: {video_quality}")
    start = _validated_time(clip_start, "clip start")
    end = _validated_time(clip_end, "clip end")
    if start is not None and end is not None and end <= start:
        raise ValueError("Clip end must be later than clip start")
    return start, end


# ── Audio mode configs ────────────────────────────────────────────────────────
AUDIO_MODES = {
    "mp3":  {"codec": "mp3",  "ext": "mp3",  "thumb": True},
    "flac": {"codec": "flac", "ext": "flac", "thumb": False},
    "wav":  {"codec": "wav",  "ext": "wav",  "thumb": False},
}


@dataclass
class DownloadJob:
    cancel_event: threading.Event
    thread: threading.Thread | None = None


class Downloader:
    def __init__(self):
        self._lock = threading.Lock()
        self._active_job = None

    def cancel(self):
        with self._lock:
            job = self._active_job
        if job:
            job.cancel_event.set()

    def download(
        self,
        request: DownloadRequest,
        on_progress: Callable = None,
        on_log: Callable = None,
        on_complete: Callable = None,
        on_error: Callable = None,
        on_cancel: Callable = None,
    ):
        job = DownloadJob(threading.Event())

        def run_job():
            try:
                self._worker(
                    request.url, request.output_folder, request.mode,
                    request.quality, request.video_quality,
                    request.is_playlist, request.filename_template,
                    request.clip_start, request.clip_end,
                    list(request.sponsorblock_cats) if request.sponsorblock_cats else None,
                    request.metadata,
                    on_progress, on_log, on_complete, on_error,
                    job.cancel_event, on_cancel,
                )
            finally:
                with self._lock:
                    if self._active_job is job:
                        self._active_job = None

        thread = threading.Thread(
            target=run_job,
            daemon=True)
        job.thread = thread
        with self._lock:
            if self._active_job and self._active_job.thread.is_alive():
                raise RuntimeError("A download is already running")
            self._active_job = job
        thread.start()
        return job

    def _worker(
        self, url, output_folder, mode, quality, video_quality,
        is_playlist, filename_template, clip_start, clip_end,
        sponsorblock_cats, metadata,
        on_progress, on_log, on_complete, on_error,
        cancel_event=None, on_cancel=None,
    ):
        cancel_event = cancel_event or threading.Event()

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
            clip_start_seconds, clip_end_seconds = validate_request(
                url, output_folder, mode, quality, video_quality, clip_start, clip_end
            )
        except ValueError as error:
            if on_error:
                on_error(str(error))
            return

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
        t_start = _parse_time(clip_start)
        t_end = _parse_time(clip_end)
        using_clip = clip_start_seconds is not None or clip_end_seconds is not None
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
            if cancel_event.is_set():
                raise Exception("Download cancelled by user.")
            status   = d.get("status", "")
            filename = os.path.basename(d.get("filename", ""))
            if status == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                speed = d.get("speed", 0) or 0
                eta   = d.get("eta",   0) or 0
                pct   = (downloaded / total * 100) if total > 0 else 0
                prog(ProgressUpdate(
                    status=DownloadStatus.DOWNLOADING,
                    filename=filename,
                    percent=pct,
                    speed=f"{speed/1024:.1f} KB/s" if speed else "-- KB/s",
                    eta=f"{eta}s" if eta else "--",
                    mode=mode,
                ))
            elif status == "finished":
                labels = {"mp3":"Converting→MP3","flac":"Converting→FLAC",
                          "wav":"Converting→WAV","mp4":"Merging video"}
                log(f"✅ {labels.get(mode,'Processing')}: {filename}")
                prog(ProgressUpdate(
                    status=DownloadStatus.CONVERTING,
                    filename=filename,
                    percent=100,
                    mode=mode,
                ))
            elif status == "error":
                log(f"❌ Error: {filename}")

        ffmpeg_dir = os.path.dirname(ffmpeg) if ffmpeg != "ffmpeg" else None
        downloaded_files = set()

        def postprocessor_hook(data):
            if cancel_event.is_set():
                raise Exception("Download cancelled by user.")
            if data.get("status") != "finished":
                return
            info = data.get("info_dict") or {}
            filepath = info.get("filepath") or data.get("filename")
            if filepath:
                downloaded_files.add(os.path.abspath(filepath))

        ydl_opts = {
            "format":        fmt,
            "outtmpl":       outtmpl,
            "postprocessors": pp,
            "progress_hooks": [ydl_hook],
            "postprocessor_hooks": [postprocessor_hook],
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
            s0 = clip_start_seconds if clip_start_seconds is not None else 0
            e0 = clip_end_seconds if clip_end_seconds is not None else float("inf")
            ydl_opts["download_ranges"] = yt_dlp.utils.download_range_func(
                None, [(s0, e0)])
            ydl_opts["force_keyframes_at_cuts"] = True

        # ── Run download ──────────────────────────────────────────────────────
        try:
            if cancel_event.is_set():
                if on_cancel: on_cancel()
                return
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
                    succeeded = 0
                    failed = 0
                    for i, entry in enumerate(entries):
                        if cancel_event.is_set():
                            log("⛔ Cancelled."); break
                        title = entry.get("title", f"Item {i+1}")
                        log(f"⬇️  [{i+1}/{total}] {title}")
                        prog(ProgressUpdate(
                            status=DownloadStatus.PLAYLIST,
                            current=i + 1,
                            total=total,
                            title=title,
                            mode=mode,
                        ))
                        try:
                            entry_url = entry.get("webpage_url") or entry.get("url")
                            if not entry_url:
                                raise RuntimeError("Playlist entry has no downloadable URL")
                            result = ydl.download([entry_url])
                            if result:
                                raise RuntimeError(f"yt-dlp returned error code {result}")
                            succeeded += 1
                        except Exception as e:
                            if cancel_event.is_set():
                                break
                            failed += 1
                            log(f"⚠️  Skipped: {title} ({e})")
                    if cancel_event.is_set():
                        if on_cancel: on_cancel()
                    elif succeeded == 0:
                        if on_error: on_error(f"Playlist failed: {failed} item(s) could not be downloaded")
                    else:
                        ext_l = mode.upper()
                        if failed:
                            log(f"⚠️  Playlist partially complete: {succeeded} saved, {failed} failed")
                        else:
                            log(f"🎉 Playlist done! {succeeded} {ext_l} files saved.")
                        if metadata and any(metadata.values()):
                            self._write_file_tags(downloaded_files, metadata, log)
                        if on_complete:
                            on_complete(DownloadResult(
                                count=succeeded,
                                title=info.get("title", "Playlist"),
                                succeeded=succeeded,
                                failed=failed,
                            ))
                else:
                    title = info.get("title","Unknown")
                    log(f"⬇️  [{mode.upper()}] {title}")
                    result = ydl.download([url])
                    if result:
                        raise RuntimeError(f"yt-dlp returned error code {result}")
                    log(f"🎉 Done! Saved to: {output_folder}")
                    if metadata and any(metadata.values()):
                        self._write_file_tags(downloaded_files, metadata, log)
                    if on_complete:
                        on_complete(DownloadResult(count=1, title=title, succeeded=1))

        except Exception as e:
            if "cancelled" in str(e).lower():
                log("⛔ Download cancelled.")
                if on_cancel: on_cancel()
            else:
                if on_error: on_error(str(e))

    def _write_file_tags(self, paths, tags: dict, log: Callable):
        try:
            from metadata_editor import write_tags
            existing_paths = [path for path in paths if os.path.isfile(path)]
            if not existing_paths:
                log("⚠️  Could not identify the downloaded file; metadata was not applied")
                return
            count = 0
            errors = []
            for path in existing_paths:
                error = write_tags(path, tags)
                if error:
                    errors.append(f"{os.path.basename(path)}: {error}")
                else:
                    count += 1
            if count:
                log(f"🏷️  Tags written to {count} file(s)")
            for e in errors:
                log(f"⚠️  Tag error: {e}")
        except Exception as e:
            log(f"⚠️  Could not write tags: {e}")
