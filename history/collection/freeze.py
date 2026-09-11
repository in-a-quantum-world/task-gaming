"""Offline input staging and fail-closed collection freeze validation."""

import argparse
import json
from pathlib import Path

from contract import (SOURCE_FILES, digest, load_condition, read, sha)
from schedule import EXISTING, validate as validate_schedule


def save_new(path, value):
    path = Path(path)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    path.chmod(0o400)


def source_contracts(root):
    sources = {}
    for key, (filename, config, step, budget) in SOURCE_FILES.items():
        source = read(root / filename)
        if (source["checkpoint_step"] != step
                or source["remaining_decisions"] != budget
                or source["first_continuation_step"] != step + 1
                or source["max_steps"] != 100
                or sha(root / config) != source["config_sha256"]):
            raise ValueError("Source contract/config differs")
        sources[key] = source
    controls = [source["actual_source_api_controls"]
                for source in sources.values()]
    if controls[0] != controls[1]:
        raise ValueError("Source API controls differ across checkpoints")
    return sources


def implementation_hashes(root):
    paths = sorted((root / "history/collection").glob("*.py"))
    return {str(path.relative_to(root)): sha(path) for path in paths}


def stage_inputs(root, draft_path, approvals_path, destination):
    """Copy reviewed external bytes into an exclusive, non-runnable bundle."""
    sources = source_contracts(root)
    schedule = read(draft_path)
    hashes = {key: value["config_sha256"] for key, value in sources.items()}
    validate_schedule(schedule, hashes)
    if schedule["status"] != "DRAFT" or schedule["execution_authorized"]:
        raise ValueError("Input must be a non-authoritative draft")
    approvals = read(approvals_path)
    validated = {}
    for row in schedule["samples"]:
        key = f"{row['checkpoint']}/{row['condition_id']}"
        if key in validated:
            continue
        spec = approvals[key]
        entry = {**row, **{name: spec[name] for name in (
            "condition_file_sha256", "condition_manifest_sha256",
            "review_sha256")}}
        paths = [Path(spec[name]).resolve() for name in
                 ("condition_file", "condition_manifest", "review_file")]
        messages = load_condition(*paths, entry, sources[row["checkpoint"]])
        validated[key] = (entry, paths, digest(messages))
    destination.mkdir(parents=True, exist_ok=False)
    for row in schedule["samples"]:
        key = f"{row['checkpoint']}/{row['condition_id']}"
        entry, paths, value_hash = validated[key]
        storage = destination / "conditions" / key
        if not storage.exists():
            storage.mkdir(parents=True)
            for path, name in zip(paths, ("messages.json", "manifest.json",
                                          "review.json")):
                with (storage / name).open("xb") as stream:
                    stream.write(path.read_bytes())
                (storage / name).chmod(0o400)
        for field in ("condition_file_sha256", "condition_manifest_sha256",
                      "review_sha256"):
            row[field] = entry[field]
        for field, name in zip(("condition_file", "condition_manifest",
                                "review_file"),
                               ("messages.json", "manifest.json",
                                "review.json")):
            row[field] = str((storage / name).resolve())
        row["history_value_sha256"] = value_hash
        load_condition(*(Path(row[field]) for field in (
            "condition_file", "condition_manifest", "review_file")),
            row, sources[row["checkpoint"]])
    schedule["status"] = "REVIEW_CANDIDATE_NOT_AUTHORIZED"
    save_new(destination / "schedule.candidate.json", schedule)
    save_new(destination / "provenance.json", {
        "draft_sha256": sha(draft_path),
        "approvals_index_sha256": sha(approvals_path),
        "implementation_sha256": implementation_hashes(root),
        "paid_calls": 0, "execution_authorized": False,
    })


def verify_frozen(root, freeze_path, sample_id):
    """Return approved inputs only when all independent freezes agree."""
    freeze = read(freeze_path)
    if (freeze["status"] != "FROZEN"
            or freeze["researcher_authorized_collection"] is not True
            or not freeze["researcher"] or not freeze["approved_at_utc"]):
        raise PermissionError("Researcher collection authorization is absent")
    if sample_id == EXISTING:
        raise PermissionError("Existing sealed A_FULL can never be rerun")
    sources = source_contracts(root)
    for filename in ("history/frozen.json", "pilot/frozen.json"):
        if sha(root / filename) != freeze["legacy_freeze_sha256"][filename]:
            raise ValueError("Legacy freeze changed")
    if implementation_hashes(root) != freeze["implementation_sha256"]:
        raise ValueError("Collection implementation changed")
    for key, source in sources.items():
        filename = SOURCE_FILES[key][0]
        if sha(root / filename) != freeze["source_contract_sha256"][key]:
            raise ValueError("Checkpoint contract changed")
        for name, expected in source["checkpoint_sha256"].items():
            if sha(Path(source["checkpoint"]) / name) != expected:
                raise ValueError("Original checkpoint artifact changed")
    required = {"preregistration", "analysis_plan", "primary_rubric",
                "local_suppression_rubric", "researcher_authorization"}
    if set(freeze["documents"]) != required:
        raise ValueError("Required freeze document absent")
    for spec in freeze["documents"].values():
        if sha(spec["path"]) != spec["sha256"]:
            raise ValueError("Frozen study document changed")
    if freeze["release_policy"] != "after_collection_and_explicit_release":
        raise ValueError("Collection-wide quarantine policy required")
    schedule = read(freeze["schedule_path"])
    if sha(freeze["schedule_path"]) != freeze["schedule_sha256"]:
        raise ValueError("Frozen schedule bytes changed")
    validate_schedule(schedule, {
        key: value["config_sha256"] for key, value in sources.items()})
    if schedule["status"] != "FROZEN" or not schedule["execution_authorized"]:
        raise PermissionError("Schedule is not execution-authoritative")
    matches = [row for row in schedule["samples"]
               if row["sample_id"] == sample_id]
    if len(matches) != 1:
        raise ValueError("Sample is absent or duplicated")
    row = matches[0]
    if row["status"] != "frozen_pending" or row["order"] == 0:
        raise ValueError("Sample is not a future frozen slot")
    checked = {}
    for item in schedule["samples"][1:]:
        if item["status"] != "frozen_pending":
            raise ValueError("Future schedule status differs")
        key = (item["checkpoint"], item["condition_id"])
        if key not in checked:
            checked[key] = validate_bound_condition(
                item, sources[item["checkpoint"]], freeze)
    if schedule["samples"][0]["status"] != "already_allocated_sealed":
        raise ValueError("Historical sealed sample status differs")
    source = sources[row["checkpoint"]]
    messages = checked[row["checkpoint"], row["condition_id"]]
    return freeze, schedule, row, source, messages


def validate_bound_condition(row, source, freeze):
    messages = load_condition(*(Path(row[field]) for field in (
        "condition_file", "condition_manifest", "review_file")), row, source)
    if digest(messages) != row["history_value_sha256"]:
        raise ValueError("Frozen message value hash differs")
    gate_key = f"{row['checkpoint']}/{row['condition_id']}"
    restore_gates = freeze["gates"][gate_key]["restore"]
    if (len(restore_gates) != 2 or len({spec["sha256"]
                                     for spec in restore_gates}) != 2):
        raise ValueError("Two distinct original-restore receipts required")
    gate_specs = [("restore", spec) for spec in restore_gates]
    gate_specs.append(("wire", freeze["gates"][gate_key]["wire"]))
    restore_directories = set()
    for kind, spec in gate_specs:
        if sha(spec["path"]) != spec["sha256"]:
            raise ValueError("Gate evidence changed")
        gate = read(spec["path"])
        if kind == "restore":
            restore_directories.add(gate["raw_synthetic_directory"])
        if (gate["kind"] != kind or gate["passed"] is not True
                or gate["real_model_calls"] != 0
                or gate["checkpoint"] != row["checkpoint"]
                or gate["condition_file_sha256"]
                != row["condition_file_sha256"]
                or gate["source_contract_sha256"]
                != freeze["source_contract_sha256"][row["checkpoint"]]
                or gate["implementation_sha256"]
                != freeze["implementation_sha256"]
                or gate["config_sha256"] != row["config_sha256"]
                or gate["remaining_decisions"] != source["remaining_decisions"]
                or gate["image_id"] != source["image_id"]):
            raise ValueError("Restore/wire gate absent, stale, or mismatched")
    if len(restore_directories) != 2:
        raise ValueError("Restore receipts refer to the same reconstruction")
    return messages



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--approvals-index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    stage_inputs(args.root, args.draft, args.approvals_index, args.output)
    print("Review candidate saved; execution remains unauthorized.")


if __name__ == "__main__":
    main()
