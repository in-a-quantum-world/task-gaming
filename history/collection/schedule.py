"""Create the draft order without any provider or raw-outcome access."""

import argparse
from collections import Counter
import json
from pathlib import Path
import random

SEED = 20260911
EXISTING = "A_FULL_258_STEP42_RUN1"
COUNTS = {
    "258_step42": {"A_FULL": 4, "A_FAITHFUL_COMPACT": 4,
                   "B_EFFORT_HISTORY": 8, "C_CURRENT_STATE": 8},
    "108_step32": {"B_EFFORT_HISTORY": 4, "C_CURRENT_STATE": 4},
}


def generate(config_hashes, seed=SEED):
    """Return four blocks, with checkpoint strata intact in each block."""
    rng = random.Random(seed)
    replicate = Counter({("258_step42", "A_FULL"): 1})
    rows = [{
        "sample_id": EXISTING, "condition_id": "A_FULL",
        "checkpoint": "258_step42", "replicate": 1, "order": 0,
        "block": None, "seed": None, "randomized": False,
        "status": "already_allocated_sealed", "condition_file_sha256": None,
        "condition_manifest_sha256": None, "review_sha256": None,
        "config_sha256": config_hashes["258_step42"],
        "counts_toward_planned_total": True,
    }]
    for block in range(1, 5):
        primary = ["B_EFFORT_HISTORY", "C_CURRENT_STATE"] * 2
        primary += ["A_FAITHFUL_COMPACT"]
        if block != 1:
            primary += ["A_FULL"]
        strata = [("258_step42", primary),
                  ("108_step32", ["B_EFFORT_HISTORY", "C_CURRENT_STATE"])]
        rng.shuffle(strata)
        for checkpoint, conditions in strata:
            rng.shuffle(conditions)
            for condition in conditions:
                replicate[checkpoint, condition] += 1
                number = replicate[checkpoint, condition]
                variant, step = checkpoint.split("_step")
                rows.append({
                    "sample_id": f"{condition}_{variant}_STEP{step}_RUN"
                    f"{number}", "condition_id": condition,
                    "checkpoint": checkpoint, "replicate": number,
                    "order": len(rows), "block": block, "seed": seed,
                    "randomized": True, "status": "draft_not_authorized",
                    "condition_file_sha256": None,
                    "condition_manifest_sha256": None,
                    "review_sha256": None,
                    "config_sha256": config_hashes[checkpoint],
                    "counts_toward_planned_total": True,
                })
    return {
        "schema": "history-collection-schedule-v1", "status": "DRAFT",
        "execution_authorized": False, "seed": seed,
        "prng": "Python random.Random MT19937; shuffle; seed version 2",
        "planned_total": 32, "already_allocated": 1, "future_slots": 31,
        "planned_counts": COUNTS, "samples": rows,
        "policy": "Four blocks; 258 B/C balanced 2:2 per block; 108 B/C "
        "balanced 1:1. Existing A_FULL is a historical sample, not randomized. "
        "Block 1 omits that future A_FULL slot. "
        "Do not regenerate after freeze.",
    }


def validate(schedule, config_hashes):
    expected = generate(config_hashes, schedule["seed"])
    for key in ("schema", "planned_total", "already_allocated",
                "future_slots", "planned_counts", "prng", "policy"):
        if schedule[key] != expected[key]:
            raise ValueError("Schedule design differs")
    if len(schedule["samples"]) != 32:
        raise ValueError("Schedule must contain the existing plus 31 slots")
    fields = ("sample_id", "condition_id", "checkpoint", "replicate",
              "order", "block", "seed", "randomized", "config_sha256",
              "counts_toward_planned_total")
    for actual, planned in zip(schedule["samples"], expected["samples"]):
        if any(actual[key] != planned[key] for key in fields):
            raise ValueError("Schedule order or allocation differs")
    bindings = {}
    if schedule["status"] == "FROZEN":
        for row in schedule["samples"]:
            key = (row["checkpoint"], row["condition_id"])
            bound = tuple(row[name] for name in (
                "condition_file_sha256", "condition_manifest_sha256",
                "review_sha256", "history_value_sha256"))
            if any(not isinstance(value, str) or len(value) != 64
                   for value in bound):
                raise ValueError("Frozen condition hashes are incomplete")
            if key in bindings and bindings[key] != bound:
                raise ValueError("Replicates use different condition files")
            bindings[key] = bound


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = {"258_step42": "history/A_FULL_258_STEP42_RUN1.json",
             "108_step32": "history/prepared108/RESTORE_108_STEP32.json"}
    hashes = {key: json.loads((args.root / path).read_text())["config_sha256"]
              for key, path in files.items()}
    schedule = generate(hashes)
    validate(schedule, hashes)
    with args.output.open("x") as stream:
        json.dump(schedule, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
