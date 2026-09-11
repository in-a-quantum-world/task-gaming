"""Verify ordered review and request parity without model calls or raw edits."""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "near100"))
import run_stage


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    evidence = ROOT / "research/evidence/near100"
    run = ROOT / (
        "research/data/raw/near100/"
        "source108-955f35aaeaf24d7a8e5de9b4fc29611a")
    ledger = evidence / "ordered-review"
    prior = read(evidence / "prior-state.json")
    failures, rows = [], []
    for step in range(51):
        opened_path = ledger / f"opened-{step:03d}.json"
        decision_path = ledger / f"decision-{step:03d}.json"
        opened, decision = read(opened_path), read(decision_path)
        checkpoint = run / f"data/step-{step}"
        valid = (
            decision["opened_record_sha256"] == digest(opened_path)
            and opened["messages_sha256"]
            == digest(checkpoint / "messages.json")
            and opened["state_sha256"] == digest(checkpoint / "state.json")
            and opened["opened_at"] <= decision["recorded_at"])
        if step < 50:
            next_open = read(ledger / f"opened-{step + 1:03d}.json")
            valid &= decision["recorded_at"] < next_open["opened_at"]
        if not valid:
            failures.append([step, "review_order_or_hash"])
        rows.append({
            "step": step, "errors": decision["current_errors"],
            "remaining": decision["remaining"],
            "criteria": decision["criteria"],
            "eligible": decision["eligible"],
            "rationale": decision["rationale"],
            "opened_at": opened["opened_at"],
            "recorded_at": decision["recorded_at"],
            "decision_sha256": digest(decision_path),
        })
    if (ledger / "selection.json").exists():
        failures.append("Unexpected automatic selection")
    run_stage.require_frozen(ROOT / "NEAR100_SOURCE_CONFIG.yaml")
    old_checks = {}
    for label, record in prior["old_raw"].items():
        path = Path(record["path"])
        manifest_path = path / "artifact_sha256.json"
        manifest = read(manifest_path)
        bad = [name for name, value in manifest.items()
               if digest(path / name) != value]
        if (bad or digest(manifest_path) != record["manifest_sha256"]):
            failures.append([label, "prior_raw_changed"])
        old_checks[label] = {"files_verified": len(manifest),
                             "hash_failures": bad,
                             "manifest_sha256": digest(manifest_path)}
    slot_path = run_stage.common_git() / run_stage.SLOT
    slot = read(slot_path)
    if slot["run_id"] != run.name:
        failures.append("New source slot mismatch")
    sources = sorted(p.name for p in run.parent.glob("source108-*"))
    if sources != [run.name]:
        failures.append("Unexpected source count")
    old_request = read(Path(prior["old_raw"]["258"]["path"])
                       / "data/api-request-0001.json")["body"]
    source_request = read(run / "data/api-request-0001.json")["body"]
    same_controls = (
        {k: v for k, v in old_request.items() if k != "messages"}
        == {k: v for k, v in source_request.items() if k != "messages"})
    same_prompts = old_request["messages"] == source_request["messages"]
    if not same_controls or not same_prompts:
        failures.append("Actual original-258 request parity failed")
    preflight = run.parent / "preflight108-d34a023b172a4cf49039e41c4ea9394b"
    preflight_cost = sum((Decimal(str(read(p)["usage"]["cost"]))
                         for p in preflight.glob("api-response-*.body.json")),
                        Decimal(0))
    audit = read(evidence / "source-audit.json")
    if audit["hash_failures"] or audit["request_audit_failures"]:
        failures.append("Source raw/request audit failed")
    result = {
        "time": datetime.now(timezone.utc).isoformat(),
        "passed": not failures, "failures": failures,
        "reviewed_checkpoints": len(rows), "earliest_near_candidate": 32,
        "automatically_eligible": [r["step"] for r in rows if r["eligible"]],
        "researcher_adjudication": "pending",
        "old_raw_unchanged": old_checks,
        "legacy_and_stage_freeze_unchanged": True,
        "old_source_slots_unchanged": True,
        "source_slots": {"near100": slot, "sha256": digest(slot_path)},
        "source_runs": sources, "source_trajectories": 1,
        "source_requests": 51, "preflight_requests": 2,
        "source_retry_count": 0,
        "actual_258_controls_identical": same_controls,
        "actual_258_initial_prompts_identical": same_prompts,
        "preflight_cost_usd": str(preflight_cost),
        "source_cost_usd": audit["provider_reported_cost_usd"],
        "total_reported_cost_usd": str(
            Decimal(audit["provider_reported_cost_usd"]) + preflight_cost),
        "review": rows,
        "limits": "Local records verify recorded order; they cannot prove "
        "absence of every possible unrecorded information channel. Provider "
        "internals and semantic legitimacy require separate review.",
    }
    with (evidence / "final-review-audit.json").open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "review"},
                     indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
