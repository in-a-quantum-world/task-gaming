"""Exercise a complete synthetic freeze and reject stale bindings."""

import copy
from pathlib import Path

import contract
import freeze


def exercise(test, root, candidate, sources, write):
    frozen_schedule = copy.deepcopy(candidate)
    frozen_schedule["status"] = "FROZEN"
    frozen_schedule["execution_authorized"] = True
    for row in frozen_schedule["samples"][1:]:
        row["status"] = "frozen_pending"
    schedule_path = root / "frozen-schedule.json"
    write(schedule_path, frozen_schedule)
    source_hashes = {key: contract.sha(root / spec[0])
                     for key, spec in contract.SOURCE_FILES.items()}
    legacy = {}
    for name in ("history/frozen.json", "pilot/frozen.json"):
        write(root / name, {"synthetic_legacy_fixture": True})
        legacy[name] = contract.sha(root / name)
    documents = {}
    for name in ("preregistration", "analysis_plan", "primary_rubric",
                 "local_suppression_rubric", "researcher_authorization"):
        path = root / f"{name}.json"
        write(path, {"synthetic_document": name})
        documents[name] = {"path": str(path), "sha256": contract.sha(path)}
    gate_sets = {}
    for row in frozen_schedule["samples"]:
        key = f"{row['checkpoint']}/{row['condition_id']}"
        if key in gate_sets:
            continue
        gates = {"restore": []}
        for kind, suffix in (("restore", "1"), ("restore", "2"),
                             ("wire", "1")):
            path = root / "gates" / key / f"{kind}{suffix}.json"
            write(path, {
                "kind": kind, "passed": True, "real_model_calls": 0,
                "checkpoint": row["checkpoint"],
                "condition_file_sha256": row["condition_file_sha256"],
                "source_contract_sha256": source_hashes[row["checkpoint"]],
                "implementation_sha256": freeze.implementation_hashes(root),
                "config_sha256": row["config_sha256"],
                "remaining_decisions": sources[row["checkpoint"]][
                    "remaining_decisions"],
                "image_id": "synthetic-image",
                "raw_synthetic_directory": str(path.parent / suffix),
            })
            spec = {"path": str(path), "sha256": contract.sha(path)}
            if kind == "restore":
                gates[kind].append(spec)
            else:
                gates[kind] = spec
        gate_sets[key] = gates
    plan = {
        "status": "FROZEN", "researcher_authorized_collection": True,
        "researcher": "SYNTHETIC FIXTURE", "approved_at_utc": "FIXTURE",
        "legacy_freeze_sha256": legacy,
        "implementation_sha256": freeze.implementation_hashes(root),
        "source_contract_sha256": source_hashes, "documents": documents,
        "release_policy": "after_collection_and_explicit_release",
        "schedule_path": str(schedule_path),
        "schedule_sha256": contract.sha(schedule_path), "gates": gate_sets,
    }
    plan_path = root / "freeze.json"
    write(plan_path, plan)
    first = frozen_schedule["samples"][1]["sample_id"]
    result = freeze.verify_frozen(root, plan_path, first)
    test.assertEqual(result[2]["sample_id"], first)
    test.assertEqual(result[3]["remaining_decisions"],
                     sources[result[2]["checkpoint"]]["remaining_decisions"])
    with test.assertRaises(PermissionError):
        freeze.verify_frozen(root, plan_path, frozen_schedule["samples"][0][
            "sample_id"])
    for key in gate_sets:
        changed = copy.deepcopy(plan)
        changed["gates"][key]["restore"] = [gate_sets[key]["restore"][0]] * 2
        write(plan_path, changed)
        with test.assertRaises(ValueError):
            freeze.verify_frozen(root, plan_path, first)
    changed = copy.deepcopy(plan)
    del changed["gates"][next(iter(gate_sets))]
    write(plan_path, changed)
    with test.assertRaises(KeyError):
        freeze.verify_frozen(root, plan_path, first)
    write(plan_path, plan)
    last = frozen_schedule["samples"][-1]
    path = Path(last["condition_file"])
    original = path.read_bytes()
    path.chmod(0o600)
    path.write_bytes(original + b" ")
    with test.assertRaises(ValueError):
        freeze.verify_frozen(root, plan_path, first)
    path.write_bytes(original)
    path.chmod(0o400)
