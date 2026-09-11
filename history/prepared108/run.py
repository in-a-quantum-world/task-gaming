"""One dedicated continuation slot with operational-only public receipts."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pilot"))
import run as preserved
from common import now, save, sha256
from contract import CONDITION, read

RAW = ROOT / "research/data/raw/history"
EVIDENCE = ROOT / "research/evidence/history" / CONDITION
CONTRACT_PATH = ROOT / "history/prepared108" / f"{CONDITION}.json"
CONTRACT = read(CONTRACT_PATH)
IMAGE = CONTRACT["image_id"]
CONFIG = ROOT / "history/prepared108/SOURCE108_CONFIG.yaml"
CHECKPOINT = Path(CONTRACT["checkpoint"])


def common_git():
    path = Path(preserved.output(["git", "rev-parse", "--git-common-dir"]))
    return path if path.is_absolute() else ROOT / path


def ledger_path():
    return common_git() / f"history-continuation-{CONDITION}.json"


def implementation_hashes():
    paths = sorted((ROOT / "history/prepared108").glob("*.py"))
    paths += [CONTRACT_PATH, ROOT / "history/prepared108/README.md"]
    return {str(p.relative_to(ROOT)): sha256(p) for p in paths}


def verify_source():
    preserved.require_frozen(
        ROOT / "SOURCE_PILOT_CONFIG.yaml", IMAGE)
    if sha256(CONFIG) != CONTRACT["config_sha256"]:
        raise ValueError("Source config differs")
    source = Path(CONTRACT["source_run"])
    manifest = source / "artifact_sha256.json"
    if sha256(manifest) != CONTRACT["source_manifest_sha256"]:
        raise ValueError("Original source manifest differs")
    for name, value in read(manifest).items():
        if sha256(source / name) != value:
            raise ValueError("Original source artifact hash mismatch")
    for name, value in CONTRACT["checkpoint_sha256"].items():
        if sha256(CHECKPOINT / name) != value:
            raise ValueError("Original checkpoint differs")
    for name, record in CONTRACT["source_ledger_states"].items():
        if sha256(common_git() / name) != record["sha256"]:
            raise ValueError("Prior source ledger changed")
    if preserved.output(["docker", "image", "inspect", IMAGE,
                         "--format", "{{.Id}}"] ) != IMAGE:
        raise ValueError("Pinned image unavailable")


def validate_condition(condition, count):
    if condition != CONDITION or count != 1:
        raise ValueError("Only the prepared 108 step-32 identifier is valid")


def allocate_paid(metadata, raw=RAW):
    raw.mkdir(parents=True, exist_ok=True)
    with (common_git() / "history-continuation.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        directory = raw / CONDITION
        if directory.exists():
            raise ValueError("Condition directory already exists")
        allocation = {
            "condition_id": CONDITION, "allocated_at": now(),
            "checkpoint": str(CHECKPOINT), "slot_consumed": True,
            "policy": "One sample. All allocated failures consume the slot.",
            "contract_sha256": sha256(CONTRACT_PATH), **metadata,
        }
        save(ledger_path(), allocation)
        directory.mkdir(mode=0o700)
        save(directory / "allocation.json", allocation)
    return directory


def prepare_directory(mode, metadata):
    if mode == "paid":
        directory = allocate_paid(metadata)
    else:
        directory = ROOT / "research/data/raw/history-validation" / (
            f"{mode}-{uuid.uuid4().hex}")
        directory.mkdir(parents=True, mode=0o700)
        save(directory / "allocation.json", {
            "mode": mode, "paid_slot_consumed": False})
    save(directory / "run.json", {
        **metadata, "mode": mode, "synthetic": mode != "paid",
        "condition_id": CONDITION, "start": now(),
    })
    shutil.copytree(ROOT / "history/prepared108", directory / "history_implementation",
                    ignore=shutil.ignore_patterns("__pycache__"))
    save(directory / "SEALED_UNTIL_CONDITION_FREEZE", {
        "condition_id": CONDITION, "opened_for_behavior": False,
        "release_requires": CONTRACT["quarantine_until"],
        "prohibited": ["transcript rendering", "behavior grading",
                       "outcome inspection", "additional paid samples"],
    })
    return directory


def seal_directories(directory):
    # The inherited launcher already hashes and chmods regular files to 0400.
    for path in sorted(directory.rglob("*"), key=lambda p: -len(p.parts)):
        if path.is_dir() and not path.is_symlink():
            path.chmod(0o500)
    directory.chmod(0o500)


def integrity_receipt(directory, code, mode):
    manifest = read(directory / "artifact_sha256.json")
    matches = all(sha256(directory / p) == value
                  for p, value in manifest.items())
    required = ["data/state.json", "data/messages.json",
                "final_workspace.tar.gz", "SEALED_UNTIL_CONDITION_FREEZE"]
    present = all((directory / name).is_file() for name in required)
    comparison_path = directory / "data/restore_comparison.json"
    gate_path = directory / "data/pre_invocation_manifest.json"
    category = None
    if code == 124:
        category = "wall_timeout"
    elif code != 0:
        category = "provider_or_infrastructure_failure"
    if not matches or not present:
        category = "artifact_preservation_failure"
    receipt = {
        "time": now(), "condition_id": CONDITION, "mode": mode,
        "slot_consumed": mode == "paid", "raw_path": str(directory),
        "artifacts_sealed": matches and present,
        "raw_manifest_sha256": sha256(directory / "artifact_sha256.json"),
        "restore_gate_record_present": comparison_path.is_file(),
        "pre_invocation_manifest_present": gate_path.is_file(),
        "failure_category": category,
        "scientific_outcome_opened_or_analyzed": False,
        "release_requires": CONTRACT["quarantine_until"],
    }
    destination = EVIDENCE / (
        "operational-receipt.json" if mode == "paid"
        else f"{directory.name}.json")
    save(destination, receipt)
    return receipt


def launch(mode):
    raise PermissionError(
        "108 path is prepared only; execution is not authorized")
    directory = None
    original_popen = subprocess.Popen
    original_allocate = preserved.allocate

    def allocate(unused_mode, metadata):
        nonlocal directory
        directory = prepare_directory(mode, metadata)
        return directory

    def popen(command, *args, **kwargs):
        if (isinstance(command, list)
                and "/opt/pilot/bootstrap.py" in command):
            command = list(command)
            command[-1] = "/root/history/bootstrap.py"
            for index, value in enumerate(command):
                if isinstance(value, str) and value.endswith(
                        ":/opt/checkpoint:ro"):
                    command[index] = value.replace(
                        ":/opt/checkpoint:ro", ":/root/history-checkpoint:ro")
            extra = [
                "-v", f"{directory / 'history_implementation'}:"
                "/root/history:ro",
                "-v", f"{directory / 'allocation.json'}:"
                "/root/history-allocation.json:ro",
                "-e", f"HISTORY_MODE={mode}",
            ]
            if mode != "paid":
                extra += ["--network", "none"]
            command[command.index(IMAGE):command.index(IMAGE)] = extra
            save(directory / "actual_command.json", command)
        return original_popen(command, *args, **kwargs)

    preserved.allocate = allocate
    subprocess.Popen = popen
    try:
        # Reuse the source launcher's network, timeout, capture, and recovery.
        directory, code = preserved.launch("source", CONFIG, IMAGE, CHECKPOINT)
    finally:
        preserved.allocate = original_allocate
        subprocess.Popen = original_popen
    seal_directories(directory)
    verify_source()
    receipt = integrity_receipt(directory, code, mode)
    print(json.dumps(receipt, indent=2))
    return receipt


def main():
    raise PermissionError(
        "108 path is prepared only; execution is not authorized")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("restore-check", "offline-wire",
                                          "paid"))
    parser.add_argument("--condition", default=CONDITION)
    parser.add_argument("--count", type=int, default=1)
    args = parser.parse_args()
    os.umask(0o077)
    validate_condition(args.condition, args.count)
    verify_source()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if args.mode == "paid":
        if ledger_path().exists() or (RAW / CONDITION).exists():
            raise ValueError("Prepared 108 continuation slot is already consumed")
        frozen = read(ROOT / "history/prepared108/frozen.json")
        if implementation_hashes() != frozen["implementation_sha256"]:
            raise ValueError("Continuation implementation freeze differs")
        for path, expected in frozen["gate_sha256"].items():
            if sha256(ROOT / path) != expected:
                raise ValueError("Continuation gate evidence changed")
        if not frozen["all_gates_passed"]:
            raise ValueError("Continuation gates not passed")
        from dotenv import dotenv_values
        key = dotenv_values(ROOT / ".env").get("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("Approved local provider credential absent")
        os.environ["OPENROUTER_API_KEY"] = key
    else:
        os.environ["OPENROUTER_API_KEY"] = "offline-history-sentinel"
    try:
        result = launch(args.mode)
    except BaseException as error:
        # Do not print exceptions that could include quarantined runtime data.
        if args.mode != "paid" or not ledger_path().exists():
            raise
        directory = RAW / CONDITION
        if directory.exists() and not (
                directory / "artifact_sha256.json").exists():
            save(directory / "host_failure.json", {
                "time": now(), "failure_type": type(error).__name__})
            preserved.seal(directory)
            seal_directories(directory)
        receipt_path = EVIDENCE / "operational-receipt.json"
        if not receipt_path.exists():
            save(receipt_path, {
                "time": now(), "condition_id": CONDITION,
                "slot_consumed": True, "raw_path": str(directory),
                "failure_category": "host_infrastructure_failure",
                "scientific_outcome_opened_or_analyzed": False,
                "release_requires": CONTRACT["quarantine_until"],
            })
        print("Allocated sample stopped: host infrastructure failure. "
              "No replacement; outcome remains quarantined.")
        raise SystemExit(1) from None
    raise SystemExit(0 if result["failure_category"] is None else 1)


if __name__ == "__main__":
    main()
