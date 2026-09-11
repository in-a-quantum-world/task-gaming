"""Prepared serial collection adapter; every invocation remains locked."""

import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import sys
import uuid

from contract import SOURCE_FILES, read, sha
from freeze import (implementation_hashes, save_new, source_contracts,
                    verify_frozen)
from ledger import allocate, write_exclusive
from schedule import validate as validate_schedule

ROOT = Path(__file__).resolve().parents[2]
EXECUTION_ENABLED = False


def require_execution_enabled():
    if not EXECUTION_ENABLED:
        raise PermissionError("Collection and 108 restoration remain locked")


def candidate_inputs(root, schedule_path, sample_id):
    """Validate an externally reviewed candidate for future offline gates."""
    from contract import digest, load_condition
    schedule = read(schedule_path)
    sources = source_contracts(root)
    validate_schedule(schedule, {
        key: source["config_sha256"] for key, source in sources.items()})
    if (schedule["status"] != "REVIEW_CANDIDATE_NOT_AUTHORIZED"
            or schedule["execution_authorized"]):
        raise ValueError("Offline gate requires a review candidate")
    row = next(row for row in schedule["samples"]
               if row["sample_id"] == sample_id)
    source = sources[row["checkpoint"]]
    messages = load_condition(*(Path(row[field]) for field in (
        "condition_file", "condition_manifest", "review_file")), row, source)
    if digest(messages) != row["history_value_sha256"]:
        raise ValueError("Candidate history value hash differs")
    return None, schedule, row, source, messages


def legacy_runner(root):
    """Load the unchanged v1 host launcher with its own contract module."""
    previous = sys.modules.get("contract")
    previous_run = sys.modules.get("run")
    spec = importlib.util.spec_from_file_location(
        "contract", root / "history/contract.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules["contract"] = module
    try:
        sys.path.insert(0, str(root / "pilot"))
        spec = importlib.util.spec_from_file_location(
            "preserved_source_host", root / "pilot/run.py")
        source_host = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(source_host)
        sys.modules["run"] = source_host
        spec = importlib.util.spec_from_file_location(
            "legacy_history_host", root / "history/run.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
    finally:
        if previous is None:
            del sys.modules["contract"]
        else:
            sys.modules["contract"] = previous
        if previous_run is None:
            del sys.modules["run"]
        else:
            sys.modules["run"] = previous_run
    return runner


def launch(mode, manifest_path, sample_id, root=ROOT):
    require_execution_enabled()
    if mode not in ("paid", "restore-check", "offline-wire"):
        raise ValueError("Unknown collection mode")
    inputs = (verify_frozen(root, manifest_path, sample_id) if mode == "paid"
              else candidate_inputs(root, manifest_path, sample_id))
    freeze, schedule, row, source, messages = inputs
    runner = legacy_runner(root)
    runner.CONDITION = sample_id
    runner.CONTRACT = {**source, "quarantine_until": [
        "planned collection complete", "all condition/rubric/analysis freezes",
        "explicit researcher outcome release"]}
    runner.CONFIG = root / SOURCE_FILES[row["checkpoint"]][1]
    runner.CHECKPOINT = Path(source["checkpoint"])
    runner.IMAGE = source["image_id"]
    runner.EVIDENCE = root / "research/evidence/history/collection" / sample_id
    runner.RAW = root / "research/data/raw/history"
    runner.EVIDENCE.mkdir(parents=True, exist_ok=True)
    manifest_hash = sha(manifest_path)

    def verify_source():
        runner.preserved.require_frozen(root / "SOURCE_PILOT_CONFIG.yaml",
                                        source["image_id"])
        for name, expected in read(root / "history/frozen.json")[
                "implementation_sha256"].items():
            if sha(root / name) != expected:
                raise ValueError("Original A_FULL code changed")
        for name, expected in source["checkpoint_sha256"].items():
            if sha(runner.CHECKPOINT / name) != expected:
                raise ValueError("Original checkpoint changed")
        for name, record in source["source_ledger_states"].items():
            if sha(runner.common_git() / name) != record["sha256"]:
                raise ValueError("Prior source ledger changed")
        actual = runner.preserved.output([
            "docker", "image", "inspect", source["image_id"],
            "--format", "{{.Id}}"])
        if actual != source["image_id"]:
            raise ValueError("Pinned image unavailable")

    def prepare_directory(unused_mode, metadata):
        if mode == "paid":
            # Recheck file bytes immediately before exclusive allocation.
            verify_frozen(root, manifest_path, sample_id)
            directory = allocate(runner.common_git(), runner.RAW, row,
                                 schedule, manifest_hash)
        else:
            directory = root / "research/data/raw/history-validation" / (
                f"collection-{mode}-{uuid.uuid4().hex}")
            directory.mkdir(parents=True, mode=0o700)
            save_new(directory / "allocation.json", {
                "mode": mode, "paid_slot_consumed": False})
        save_new(directory / "run.json", {
            **metadata, "mode": mode, "sample_id": sample_id,
            "manifest_sha256": manifest_hash, "synthetic": mode != "paid"})
        implementation = directory / "history_implementation"
        shutil.copytree(root / "history/collection", implementation,
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(root / "history/bootstrap.py",
                        implementation / "bootstrap.py")
        for field, filename in (("condition_file", "condition.messages.json"),
                                ("condition_manifest", "prototype.json"),
                                ("review_file", "review.json")):
            shutil.copyfile(row[field], implementation / filename)
        if sha(implementation / "condition.messages.json") != row[
                "condition_file_sha256"]:
            raise ValueError("Condition changed during private copy")
        save_new(implementation / "condition.json", {
            **row, "source_contract": source,
            "schedule_manifest_sha256": manifest_hash,
            "collection_implementation_sha256": implementation_hashes(root)})
        save_new(directory / "SEALED_UNTIL_CONDITION_FREEZE", {
            "sample_id": sample_id, "opened_for_behavior": False,
            "release_requires": runner.CONTRACT["quarantine_until"]})
        save_new(directory / "SEALED_UNTIL_COLLECTION_COMPLETE", {
            "release_requires": runner.CONTRACT["quarantine_until"],
            "no_automatic_release": True})
        return directory

    runner.prepare_directory = prepare_directory
    runner.verify_source = verify_source
    verify_source()
    if mode == "paid":
        from dotenv import dotenv_values
        key = dotenv_values(root / ".env").get("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("Approved local provider credential absent")
        os.environ["OPENROUTER_API_KEY"] = key
    else:
        os.environ["OPENROUTER_API_KEY"] = "offline-collection-sentinel"
    try:
        receipt = runner.launch(mode)
    except BaseException as error:
        if mode != "paid":
            raise
        allocation = runner.common_git() / (
            f"history-collection-{sample_id}.json")
        if not allocation.exists():
            raise
        directory = runner.RAW / sample_id
        if (directory.exists()
                and not (directory / "artifact_sha256.json").exists()):
            save_new(directory / "host_failure.json", {
                "failure_type": type(error).__name__})
            runner.preserved.seal(directory)
            runner.seal_directories(directory)
        receipt = {"slot_consumed": True, "sample_id": sample_id,
                   "failure_category": "host_infrastructure_failure",
                   "scientific_outcome_opened_or_analyzed": False}
    if mode == "paid":
        write_exclusive(runner.common_git() / (
            f"history-collected-{sample_id}.json"), {
                "sample_id": sample_id, "slot_consumed": True,
                "freeze_sha256": manifest_hash,
                "operational_receipt": receipt})
    elif receipt["failure_category"] is None:
        from gates import record_offline_gate
        record_offline_gate(root, Path(receipt["raw_path"]), row, source,
                            mode, runner.EVIDENCE)
    return receipt


def main():
    require_execution_enabled()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("paid", "restore-check",
                                          "offline-wire"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--sample", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    receipt = launch(args.mode, args.manifest, args.sample)
    if receipt["failure_category"] is not None:
        raise SystemExit("Operational failure; slot retained; no replacement")


if __name__ == "__main__":
    main()
