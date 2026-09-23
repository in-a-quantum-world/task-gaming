"""Private, exclusive artifacts and content hashes."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    path.chmod(0o600)


def seal(directory):
    """Hash artifacts and remove ordinary write permission."""
    directory = Path(directory)
    hashes = {str(p.relative_to(directory)): sha256(p)
              for p in sorted(directory.rglob("*"))
              if p.is_file() and not p.is_symlink()}
    save(directory / "artifact_sha256.json", hashes)
    for path in directory.rglob("*"):
        if path.is_file() and not path.is_symlink():
            path.chmod(0o400)


def redact(text):
    """Remove configured secret values from telemetry."""
    for name, value in os.environ.items():
        if value and any(part in name for part in (
                "API_KEY", "TOKEN", "SECRET", "PASSWORD")):
            text = text.replace(value, "[REDACTED]")
    return text
