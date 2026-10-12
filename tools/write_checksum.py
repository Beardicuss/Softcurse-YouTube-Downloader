"""Write a sha256sum-compatible checksum file for a release artifact."""

import hashlib
from pathlib import Path
import sys


def write_checksum(path: Path) -> Path:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checksum_path = Path(f"{path}.sha256")
    checksum_path.write_text(f"{digest} *{path.name}\n", encoding="ascii")
    return checksum_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: write_checksum.py <artifact>")
    write_checksum(Path(sys.argv[1]))
