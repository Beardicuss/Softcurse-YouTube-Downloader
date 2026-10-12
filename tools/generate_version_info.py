"""Generate PyInstaller Windows version resources from the canonical VERSION file."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "VERSION"


def read_version() -> str:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("VERSION must use MAJOR.MINOR.PATCH")
    return version


def render(version: str) -> str:
    parts = tuple(int(part) for part in version.split(".")) + (0,)
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={parts}, prodvers={parts}, mask=0x3f, flags=0x0,
    OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'Softcurse'),
    StringStruct('FileDescription', 'Softcurse Media Downloader'),
    StringStruct('FileVersion', '{version}'),
    StringStruct('InternalName', 'Softcurse_Media_Downloader'),
    StringStruct('OriginalFilename', 'Softcurse_Media_Downloader.exe'),
    StringStruct('ProductName', 'Softcurse Media Downloader'),
    StringStruct('ProductVersion', '{version}')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)\n"""


def main() -> int:
    destination = ROOT / "build" / "version_info.txt"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render(read_version()), encoding="utf-8")
    print(destination)
    return 0


if __name__ == "__main__":
    sys.exit(main())
