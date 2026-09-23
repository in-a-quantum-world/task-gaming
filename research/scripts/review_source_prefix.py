"""Open source checkpoints in order and preserve each prior review decision."""

import argparse
import difflib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pilot"))
from common import now, save, sha256
from grade import grade_transition, read_workspace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("inspect", "record"))
    parser.add_argument("run", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("step", type=int)
    parser.add_argument("--decision", type=Path)
    args = parser.parse_args()
    args.ledger.mkdir(parents=True, exist_ok=True)
    for step in range(args.step):
        if not (args.ledger / f"decision-{step:03d}.json").exists():
            raise ValueError("Record every prior prefix before opening this one")
    checkpoint = args.run / "data" / f"step-{args.step}"
    previous = (args.run / "data" / f"step-{args.step - 1}"
                if args.step else args.run / "data/initial")
    opened = args.ledger / f"opened-{args.step:03d}.json"
    if args.operation == "record":
        if not opened.exists() or not args.decision:
            raise ValueError("Inspect the prefix and supply a decision first")
        decision = json.loads(args.decision.read_text())
        if decision["step"] != args.step:
            raise ValueError("Decision step mismatch")
        if set(decision["criteria"]) != set("abcdefg"):
            raise ValueError("Record all seven eligibility criteria")
        decision.update(recorded_at=now(), opened_record_sha256=sha256(opened))
        eligible = all(value is True for value in decision["criteria"].values())
        decision["eligible"] = eligible
        decision["question"] = "Does this prefix satisfy the frozen rule?"
        decision["previous_belief"] = (
            "Earlier prefixes were recorded before this prefix was opened")
        decision["evidence"] = str(checkpoint.resolve())
        decision["decision"] = "eligible" if eligible else "rejected"
        decision["why"] = decision["rationale"]
        decision["what_could_make_this_wrong"] = decision.get(
            "uncertainty", "Human interpretation of source-edit legitimacy")
        path = args.ledger / f"decision-{args.step:03d}.json"
        save(path, decision)
        path.chmod(0o400)
        selection = args.ledger / "selection.json"
        if eligible and not selection.exists():
            save(selection, {"step": args.step, "recorded_at": now(),
                             "decision_sha256": sha256(path),
                             "later_checkpoint_behavior_not_opened": True})
            selection.chmod(0o400)
        print(json.dumps(decision))
        return
    if not opened.exists():
        save(opened, {"step": args.step, "opened_at": now(),
                      "checkpoint": str(checkpoint.resolve()),
                      "messages_sha256": sha256(checkpoint / "messages.json"),
                      "state_sha256": sha256(checkpoint / "state.json")})
        opened.chmod(0o400)
    state = json.loads((checkpoint / "state.json").read_text())
    validation = json.loads((checkpoint / "validation.json").read_text())
    actions = json.loads((checkpoint / "actions.json").read_text())
    displayed_actions = dict(actions)
    native = actions.get("native_message") or {}
    displayed_actions["native_message"] = {
        key: value for key, value in native.items()
        if key not in ("reasoning_content", "reasoning_details")}
    if not native.get("reasoning"):
        displayed_actions["native_message"]["reasoning_details"] = native.get(
            "reasoning_details")
    before, after = read_workspace(previous), read_workspace(checkpoint)
    diffs = {}
    for name in sorted(before.keys() | after.keys()):
        if not (name.startswith("src/") or name in (
                "pyproject.toml", ".git/hooks/pre-commit", ".git/config")):
            continue
        if before.get(name) != after.get(name):
            diffs[name] = "".join(difflib.unified_diff(
                before.get(name, b"").decode(errors="replace").splitlines(True),
                after.get(name, b"").decode(errors="replace").splitlines(True),
                fromfile="previous/" + name, tofile="current/" + name))
    print(json.dumps({
        "step": args.step, "remaining": validation["steps_remaining"],
        "task_completed": state["task_completed"],
        "reference_errors": validation["mypy"]["reference"]["error_count"],
        "active_errors": validation["mypy"]["active"]["error_count"],
        "validation_issues": validation["issues"],
        "actions": displayed_actions, "source_and_policy_diffs": diffs,
        "prefix_transition_grade": grade_transition(previous, checkpoint),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
