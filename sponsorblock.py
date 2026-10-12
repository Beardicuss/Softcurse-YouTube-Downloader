"""
sponsorblock.py - Softcurse // SponsorBlock Integration
Fetches sponsor segments from the SponsorBlock API and passes
them to yt-dlp's download_ranges so ffmpeg cuts them out.
API docs: https://wiki.sponsor.ajay.app/w/API_Docs
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import hashlib
import logging
import math
import re
from typing import List, Tuple, Optional
from urllib.parse import parse_qs, urlparse

SPONSORBLOCK_API = "https://sponsor.ajay.app/api"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
LOGGER = logging.getLogger(__name__)

# Category labels for UI display
CATEGORY_LABELS = {
    "sponsor":          "💰 Sponsor",
    "intro":            "🎬 Intro",
    "outro":            "🔚 Outro",
    "selfpromo":        "📣 Self-Promo",
    "interaction":      "👍 Interaction Reminder",
    "preview":          "👁 Preview",
    "music_offtopic":   "🎵 Non-Music Section",
    "filler":           "💬 Filler/Tangent",
    "poi_highlight":    "⭐ Highlight",
}

DEFAULT_CATEGORIES = ["sponsor", "intro", "outro", "selfpromo", "interaction"]


def _extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from a URL."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    video_id = None
    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            parts = parsed.path.strip("/").split("/")
            video_id = parts[1] if len(parts) > 1 else None
    if video_id and re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return video_id
    return None


def _hash_video_id(video_id: str) -> str:
    """SHA-256 hash prefix (first 4 chars) for privacy-preserving API lookup."""
    return hashlib.sha256(video_id.encode()).hexdigest()[:4]


def fetch_segments(
    url: str,
    categories: List[str] = None,
    timeout: int = 8,
) -> Tuple[List[dict], str]:
    """
    Fetch SponsorBlock segments for a YouTube URL.
    Returns (segments_list, video_id).
    Each segment: {"start": float, "end": float, "category": str, "uuid": str}
    Returns ([], "") on failure or no segments.
    """
    if categories is None:
        categories = DEFAULT_CATEGORIES

    video_id = _extract_video_id(url)
    if not video_id:
        return [], ""

    # Use the hashed endpoint for privacy
    hash_prefix = _hash_video_id(video_id)
    cats_param  = urllib.parse.quote(json.dumps(categories))
    api_url = f"{SPONSORBLOCK_API}/skipSegments/{hash_prefix}?categories={cats_param}"

    try:
        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": "SoftcurseDownloader/4.0",
                "Accept": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            declared_size = resp.headers.get("Content-Length")
            if declared_size and int(declared_size) > MAX_RESPONSE_BYTES:
                raise ValueError("SponsorBlock response is too large")
            payload = resp.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise ValueError("SponsorBlock response is too large")
        data = json.loads(payload.decode())
        if not isinstance(data, list):
            raise ValueError("Unexpected SponsorBlock response")

        # API returns a list of video entries matching the hash prefix
        # Find ours by videoID
        segments = []
        for entry in data:
            if entry.get("videoID") == video_id:
                for seg in entry.get("segments", []):
                    start, end = seg.get("segment", [0, 0])
                    segments.append({
                        "start":    float(start),
                        "end":      float(end),
                        "category": seg.get("category", "sponsor"),
                        "uuid":     seg.get("UUID", ""),
                    })
                break
        return segments, video_id

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return [], video_id   # No segments found — normal
        LOGGER.warning("SponsorBlock HTTP error %s", e.code)
        return [], video_id
    except (OSError, ValueError, json.JSONDecodeError) as error:
        LOGGER.warning("SponsorBlock request failed: %s", error)
        return [], video_id


def segments_to_keep_ranges(
    segments: List[dict],
    total_duration: float = None,
) -> List[Tuple[float, float]]:
    """
    Convert a list of skip segments into a list of (start, end) ranges
    to KEEP — i.e. the inverse of the skip segments.
    These are passed to yt-dlp's download_ranges.
    """
    if not segments:
        return [(0, float("inf"))]

    end_time = total_duration if total_duration is not None else float("inf")
    if end_time < 0 or math.isnan(end_time):
        raise ValueError("total duration must be a non-negative number")
    candidates = []
    for segment in segments:
        try:
            start = max(0.0, float(segment["start"]))
            end = min(end_time, float(segment["end"]))
        except (KeyError, TypeError, ValueError):
            continue
        if not math.isfinite(start) or math.isnan(end) or end <= start:
            continue
        candidates.append((start, end))

    normalized = []
    for start, end in sorted(candidates):
        if normalized and start <= normalized[-1][1]:
            normalized[-1] = (normalized[-1][0], max(normalized[-1][1], end))
        else:
            normalized.append((start, end))

    keep = []
    cursor = 0.0

    for start, end in normalized:
        if start > cursor:
            keep.append((cursor, start))
        cursor = max(cursor, end)

    if cursor < end_time:
        keep.append((cursor, end_time))

    return keep if keep else [(0, float("inf"))]


def format_segments_summary(segments: List[dict]) -> str:
    """Human-readable summary of what will be skipped."""
    if not segments:
        return "No SponsorBlock segments found."
    lines = [f"✂️  SponsorBlock — {len(segments)} segment(s) to skip:"]
    for seg in segments:
        label = CATEGORY_LABELS.get(seg["category"], seg["category"])
        duration = seg["end"] - seg["start"]
        start_str = _secs_to_ts(seg["start"])
        end_str   = _secs_to_ts(seg["end"])
        lines.append(f"   {label}  {start_str} → {end_str}  ({duration:.1f}s)")
    return "\n".join(lines)


def _secs_to_ts(secs: float) -> str:
    secs = int(secs)
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
