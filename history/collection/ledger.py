"""Exclusive per-sample allocations with no replacement or ledger reset."""

from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path

from schedule import EXISTING


def write_exclusive(path, value):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def allocate(common_git, raw, row, schedule, freeze_sha256):
    sample = row["sample_id"]
    if sample == EXISTING or row["order"] == 0:
        raise PermissionError("The historical A_FULL slot is already consumed")
    common_git.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    with (common_git / "history-collection.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for prior in schedule["samples"][1:row["order"]]:
            path = common_git / f"history-collected-{prior['sample_id']}.json"
            if not path.is_file():
                raise ValueError("Earlier scheduled allocation is unfinished")
            receipt = json.loads(path.read_text())
            if (receipt["slot_consumed"] is not True
                    or receipt["freeze_sha256"] != freeze_sha256):
                raise ValueError("Prior operational receipt differs")
        destination = raw / sample
        if destination.exists():
            raise FileExistsError("Raw destination already exists")
        allocation = {
            "sample_id": sample, "slot_consumed": True,
            "allocated_at": datetime.now(timezone.utc).isoformat(),
            "freeze_sha256": freeze_sha256, "schedule_row": row,
            "policy": "All allocated failures consume the slot; no retry.",
        }
        write_exclusive(common_git / f"history-collection-{sample}.json",
                        allocation)
        destination.mkdir(mode=0o700)
        write_exclusive(destination / "allocation.json", allocation)
    return destination
