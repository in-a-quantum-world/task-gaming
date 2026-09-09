"""Produce conservative observation tables; do not infer causal labels."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "prototype_results"
FIELDS = [
    "run_id", "baseline_run_id", "condition", "checkpoint", "model",
    "provider", "reasoning_effort", "generation_settings", "max_steps",
    "remaining_steps_at_checkpoint", "history_token_count", "workspace_hash",
    "unresolved_error_count", "shortcut_known", "legitimate_options_known",
    "workaround_attempted", "workaround_succeeded", "honest_repair",
    "abandonment", "commit_succeeded", "final_outcome",
    "steps_after_checkpoint", "scorer_result", "termination_reason", "notes",
    "synthetic", "start", "end", "config_sha256", "image_id",
    "prohibited_action_attempted", "prohibited_action_succeeded",
    "unresolved_errors_remained", "legitimate_repair_steps",
    "steps_until_first_workaround", "task_success_constraint_satisfied",
    "provider_invocations", "http_requests", "runtime_error",
    "interpretation", "history_utf8_bytes", "checkpoint_restore_equivalent",
    "final_workspace_hash", "checkpoint_unresolved_error_count",
]


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def summarize(directory):
    record = read(directory / "run.json")
    config = read(directory / "config.json")
    data = directory / "data"
    termination = read(data / "termination.json", {})
    ending = read(directory / "exit.json", {})
    restore = read(data / "restore_check.json", {})
    checkpoints = sorted(data.glob("step-*"),
                         key=lambda path: int(path.name.split("-")[1]))
    last = checkpoints[-1] if checkpoints else data
    diagnostics = read(last / "diagnostics.json", {})
    workspace = read(last / "workspace.json", {})
    if not workspace:
        workspace = read(data / "restore_workspace.json", {})
    starting_workspace = read(data / "restore_workspace.json", {})
    if not starting_workspace:
        starting_workspace = read(data / "initial_workspace.json", {})
    checkpoint_diagnostics = {}
    if record["checkpoint"]:
        checkpoint_diagnostics = read(Path(record["checkpoint"]) /
                                      "diagnostics.json", {})
    initial = read(data / "initial_diagnostics.json", {})
    before = initial.get("git_head", {}).get("stdout")
    after = diagnostics.get("git_head", {}).get("stdout")
    messages_path = data / "initial_messages.json"
    history_bytes = (messages_path.stat().st_size
                     if messages_path.exists() else None)
    unresolved = diagnostics.get("unresolved_error_count")
    synthetic = record["synthetic"]
    row = dict.fromkeys(FIELDS)
    row.update({
        "run_id": record["run_id"],
        "baseline_run_id": record["baseline_run_id"],
        "condition": record.get("history_condition") or record["condition"],
        "checkpoint": record["checkpoint"],
        "model": config["agent"]["model"],
        "provider": config["agent"]["provider"],
        "reasoning_effort": config["agent"].get("reasoning_effort"),
        "generation_settings": {
            "temperature": config["agent"].get("temperature"),
            "top_p": config["agent"].get("top_p"),
            "max_tokens": "omitted; provider default",
        },
        "max_steps": config["agent"]["max_steps"],
        "remaining_steps_at_checkpoint": restore.get("remaining_steps"),
        "workspace_hash": starting_workspace.get("sha256"),
        "final_workspace_hash": workspace.get("sha256"),
        "checkpoint_unresolved_error_count": checkpoint_diagnostics.get(
            "unresolved_error_count"),
        "unresolved_error_count": unresolved,
        "commit_succeeded": before != after if before and after else None,
        "final_outcome": "OTHER / AMBIGUOUS",
        "steps_after_checkpoint": termination.get("provider_invocations"),
        "scorer_result": read(data / "scorer.json"),
        "termination_reason": termination.get("reason", "runtime_error"),
        "notes": ("Scripted fixture; not behavioral evidence. " if synthetic
                  else "Manual observable labels await review. ")
        + "Null means unknown or not measured; it never means false.",
        "synthetic": synthetic, "start": record["start"],
        "end": ending.get("end"), "config_sha256": record["config_sha256"],
        "image_id": record["image_id"],
        "unresolved_errors_remained": (unresolved > 0
                                       if unresolved is not None else None),
        "provider_invocations": termination.get("provider_invocations"),
        "http_requests": termination.get("http_requests"),
        "runtime_error": read(data / "error.json"),
        "history_utf8_bytes": history_bytes,
        "checkpoint_restore_equivalent": restore.get("equivalent"),
    })
    annotation = read(RESULTS / "processed" / "annotations" /
                      (record["run_id"] + ".json"), {})
    allowed = set(FIELDS) - {"run_id", "provider", "model", "synthetic"}
    if not set(annotation).issubset(allowed):
        raise ValueError("Annotation contains an unrecognized field.")
    row.update(annotation)
    return row


def main():
    rows = [summarize(path.parent) for path in sorted(
        (RESULTS / "raw").glob("*/run.json"))]
    processed = RESULTS / "processed"
    with (processed / "runs.jsonl").open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    with (processed / "runs.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value) if isinstance(
                value, (dict, list)) else value for key, value in row.items()})
    # This file contains only real-model observations, including failed runs.
    with (processed / "model_runs.jsonl").open("w") as handle:
        for row in rows:
            if not row["synthetic"]:
                handle.write(json.dumps(row) + "\n")
    print(f"Saved {len(rows)} technical/empirical records.")


if __name__ == "__main__":
    main()
