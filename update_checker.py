"""Read-only GitHub Releases update discovery for complete application updates."""

from dataclasses import dataclass
import json
import urllib.request

RELEASES_API = (
    "https://api.github.com/repos/Beardicuss/Softcurse-YouTube-Downloader/releases/latest"
)
MAX_RESPONSE_BYTES = 512 * 1024


@dataclass(frozen=True)
class UpdateInfo:
    current_version: str
    latest_version: str
    release_url: str

    @property
    def available(self):
        return _version_tuple(self.latest_version) > _version_tuple(self.current_version)


def _version_tuple(version: str):
    cleaned = version.strip().lower().lstrip("v")
    core = cleaned.split("-", 1)[0]
    parts = core.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Unsupported version: {version}")
    return tuple(int(part) for part in parts)


def check_for_update(current_version: str, timeout=8) -> UpdateInfo:
    request = urllib.request.Request(
        RELEASES_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Softcurse-Updater"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read(MAX_RESPONSE_BYTES + 1)
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError("Update response is too large")
    data = json.loads(payload.decode("utf-8"))
    latest = str(data.get("tag_name", ""))
    release_url = str(data.get("html_url", ""))
    _version_tuple(latest)
    if not release_url.startswith("https://github.com/"):
        raise ValueError("Unexpected release URL")
    return UpdateInfo(current_version, latest.lstrip("v"), release_url)

