"""Presentation-friendly states derived from engine errors."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorPresentation:
    category: str
    summary: str
    action: str


def present_error(message: str) -> ErrorPresentation:
    lowered = message.lower()
    if "ffmpeg" in lowered:
        return ErrorPresentation("DEPENDENCY", "FFmpeg is unavailable", "Install FFmpeg, then retry")
    if "yt-dlp not installed" in lowered:
        return ErrorPresentation("DEPENDENCY", "The download engine is unavailable", "Install yt-dlp, then restart")
    if "unsupported" in lowered or "invalid" in lowered or "valid http" in lowered:
        return ErrorPresentation("INPUT", message, "Review the URL and selected options")
    if "private" in lowered or "sign in" in lowered or "login" in lowered:
        return ErrorPresentation("ACCESS", "This media requires authorization", "Use media you can access")
    if "network" in lowered or "timed out" in lowered or "connection" in lowered:
        return ErrorPresentation("NETWORK", "The network request failed", "Check the connection and retry")
    return ErrorPresentation("DOWNLOAD", message, "Review the log and retry")

