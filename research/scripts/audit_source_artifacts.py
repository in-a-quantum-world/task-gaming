"""Audit saved source artifacts after ordered checkpoint review is complete."""

import argparse
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(run, ledger):
    data = run / "data"
    steps = sorted(data.glob("step-*"),
                   key=lambda path: int(path.name.split("-")[1]))
    for index in range(len(steps)):
        if not (ledger / f"decision-{index:03d}.json").exists():
            raise ValueError("Complete ordered prefix review first")
    manifest = read(run / "artifact_sha256.json")
    failed_hashes = [name for name, value in manifest.items()
                     if digest(run / name) != value]
    requests = sorted(data.glob("api-request-*.json"))
    first = read(requests[0])["body"]
    controls = {key: value for key, value in first.items()
                if key != "messages"}
    failures = []
    costs, rows, raw_messages = [], [], []
    for index, request_path in enumerate(requests):
        number = index + 1
        request = read(request_path)
        body = request["body"]
        actual = {key: value for key, value in body.items()
                  if key != "messages"}
        response = read(data / f"api-response-{number:04d}.body.json")
        metadata = read(data / f"api-response-{number:04d}.json")
        raw = read(data / f"api-assistant-{number:04d}.json")
        raw_messages.append(raw)
        native = read(data / f"step-{index}/actions.json")["native_message"]
        history = read(data / f"step-{index}/messages.json")
        assistant = history[2 + 2 * index]
        if actual != controls:
            failures.append([index, "controlled_request_fields_changed"])
        if response["model"] != "moonshotai/kimi-k2-thinking":
            failures.append([index, "wrong_model"])
        if response["provider"] != "Novita":
            failures.append([index, "wrong_provider"])
        if raw != response["choices"][0]["message"]:
            failures.append([index, "raw_assistant_changed"])
        if metadata["status_code"] != 200:
            failures.append([index, "non_200_response"])
        for key, value in raw.items():
            if native.get(key) != value or assistant.get(key) != value:
                failures.append([index, "history_or_native_changed", key])
        for prior in range(index):
            replay = body["messages"][2 + 2 * prior]
            for key, value in raw_messages[prior].items():
                if replay.get(key) != value:
                    failures.append([index, "replay_changed", prior, key])
        usage = response["usage"]
        costs.append(Decimal(str(usage["cost"])))
        rows.append({
            "step": index, "request_id": response["id"],
            "created": response["created"],
            "elapsed_seconds": metadata["elapsed_seconds"],
            "finish_reason": response["choices"][0]["finish_reason"],
            "usage": usage,
        })
    decisions = [read(ledger / f"decision-{i:03d}.json")
                 for i in range(len(steps))]
    order_failures = []
    for index, decision in enumerate(decisions[:-1]):
        next_opened = read(ledger / f"opened-{index + 1:03d}.json")
        if decision["recorded_at"] >= next_opened["opened_at"]:
            order_failures.append(index)
    termination = read(data / "termination.json")
    elapsed = (datetime.fromisoformat(termination["end"])
               - datetime.fromisoformat(termination["start"])).total_seconds()
    last = read(steps[-1] / "validation.json")
    checkpoints = []
    for index, path in enumerate(steps):
        validation = read(path / "validation.json")
        checkpoints.append({
            "step": index, "criteria": decisions[index]["criteria"],
            "eligible": decisions[index]["eligible"],
            "errors": validation["mypy"]["reference"]["error_count"],
            "remaining": validation["steps_remaining"],
            "rationale": decisions[index]["rationale"],
        })
    return {
        "run": str(run.resolve()), "manifest_files": len(manifest),
        "hash_failures": failed_hashes, "request_audit_failures": failures,
        "review_order_failures": order_failures,
        "raw_request_count": len(requests), "saved_steps": len(steps),
        "controlled_fields": controls,
        "raw_assistant_fields_preserved_and_replayed": not failures,
        "sdk_added_alias_fields": ["reasoning_content"],
        "server_use_of_replayed_reasoning": "not_observable",
        "provider_reported_cost_usd": str(sum(costs, Decimal(0))),
        "prompt_tokens": sum(r["usage"]["prompt_tokens"] for r in rows),
        "completion_tokens": sum(r["usage"]["completion_tokens"] for r in rows),
        "reasoning_tokens": sum(r["usage"]["completion_tokens_details"]
                                ["reasoning_tokens"] for r in rows),
        "source_loop_seconds": elapsed,
        "termination": termination, "exit": read(run / "exit.json"),
        "final_head": last["git"]["head"]["stdout"].strip(),
        "final_git_status": last["git"]["status"]["stdout"],
        "upstream_final_score": read(steps[-1] / "upstream_score.json"),
        "eligible_steps": [d["step"] for d in decisions if d["eligible"]],
        "earliest_near_candidate": next((d["step"] for d in decisions
                                         if d.get("earliest_near_candidate")),
                                        None),
        "checkpoints": checkpoints, "requests": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(args.run, args.ledger)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    args.output.chmod(0o400)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("requests", "checkpoints")}, indent=2))


if __name__ == "__main__":
    main()
