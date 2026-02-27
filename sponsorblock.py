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
from typing import List, Tuple, Optional

SPONSORBLOCK_API = "https://sponsor.ajay.app/api"

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
    if "youtu.be/" in url:
        vid = url.split("youtu.be/")[-1].split("?")[0].strip()
        return vid if len(vid) == 11 else None
    for param in ["v=", "video_id="]:
        if param in url:
            vid = url.split(param)[-1].split("&")[0].strip()
            return vid if vid else None
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
            data = json.loads(resp.read().decode())

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
        return [], video_id
    except Exception:
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

    # Sort by start time
    segs = sorted(segments, key=lambda s: s["start"])

    end_time = total_duration if total_duration else float("inf")
    keep = []
    cursor = 0.0

    for seg in segs:
        s, e = seg["start"], seg["end"]
        if s > cursor:
            keep.append((cursor, s))
        cursor = max(cursor, e)

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
