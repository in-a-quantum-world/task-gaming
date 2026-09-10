"""Audit raw request controls, visible field replay, and preserved checkpoints."""

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(run):
    data = run / "data"
    manifest = read(run / "artifact_sha256.json")
    hash_failures = [name for name, value in manifest.items()
                     if digest(run / name) != value]
    requests = sorted(data.glob("api-request-*.json"))
    controls, raw_messages, rows, failures = None, [], [], []
    for path in requests:
        number = int(path.stem.split("-")[-1])
        request = read(path)
        step = request["step"]
        body = request["body"]
        actual = {key: value for key, value in body.items()
                  if key != "messages"}
        if controls is None:
            controls = actual
        elif actual != controls:
            failures.append([step, "request_controls_changed"])
        replay = [m for m in body["messages"]
                  if m.get("role") == "assistant"]
        for prior, original in enumerate(raw_messages):
            if prior >= len(replay) or any(
                    replay[prior].get(k) != v for k, v in original.items()):
                failures.append([step, "visible_replay_changed", prior])
        response_path = data / f"api-response-{number:04d}.body.json"
        if not response_path.exists():
            rows.append({"step": step, "request_number": number,
                         "response": "absent; inspect error.json"})
            continue
        response = read(response_path)
        metadata = read(data / f"api-response-{number:04d}.json")
        row = {"step": step, "request_number": number,
               "status_code": metadata["status_code"],
               "elapsed_seconds": metadata["elapsed_seconds"],
               "request_id": response.get("id"),
               "model": response.get("model"),
               "provider": response.get("provider"),
               "usage": response.get("usage"),
               "finish_reasons": [c.get("finish_reason") for c in
                                  response.get("choices", [])]}
        rows.append(row)
        if not response.get("choices"):
            continue
        if response.get("model") != "moonshotai/kimi-k2-thinking":
            failures.append([step, "wrong_model"])
        if response.get("provider") != "Novita":
            failures.append([step, "wrong_provider"])
        raw = read(data / f"api-assistant-{number:04d}.json")
        if raw != response["choices"][0]["message"]:
            failures.append([step, "raw_assistant_changed"])
        raw_messages.append(raw)
        checkpoint = data / f"step-{step}"
        if not (checkpoint / "actions.json").exists():
            row["checkpoint"] = "absent; response remains preserved"
            continue
        native = read(checkpoint / "actions.json")["native_message"]
        history = [m for m in read(checkpoint / "messages.json")
                   if m.get("role") == "assistant"]
        if not history or any(native.get(k) != v or history[-1].get(k) != v
                              for k, v in raw.items()):
            failures.append([step, "native_or_history_changed"])
    checkpoints = []
    for path in sorted(data.glob("step-*"),
                       key=lambda p: int(p.name.split("-")[1])):
        val = read(path / "validation.json")
        checkpoints.append({
            "step": val["checkpoint_step"], "remaining": val["steps_remaining"],
            "active_errors": val["mypy"]["active"]["error_count"],
            "strict_errors": val["mypy"]["reference"]["error_count"],
            "strict_diagnostics_sha256": val["mypy"]["reference"]["errors_hash"],
            "head": val["git"]["head"]["stdout"].strip(),
            "git_status": val["git"]["status"]["stdout"],
            "workspace_hash": val["workspace_hash"],
        })
    usage = [r["usage"] for r in rows if r.get("usage")]
    return {
        "run": str(run.resolve()), "manifest_files": len(manifest),
        "hash_failures": hash_failures, "request_audit_failures": failures,
        "raw_request_count": len(requests), "saved_steps": len(checkpoints),
        "controlled_fields": controls,
        "provider_reported_cost_usd": str(sum(
            (Decimal(str(u.get("cost", 0))) for u in usage), Decimal(0))),
        "prompt_tokens": sum(u.get("prompt_tokens", 0) for u in usage),
        "completion_tokens": sum(u.get("completion_tokens", 0) for u in usage),
        "termination": read(data / "termination.json")
        if (data / "termination.json").exists() else None,
        "exit": read(run / "exit.json"), "requests": rows,
        "checkpoints": checkpoints,
        "limits": "Server use of visible reasoning is not observable. "
        "No history-experiment checkpoint is selected by this audit.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(args.run)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items()
                      if k not in {"requests", "checkpoints", "controlled_fields"}},
                     indent=2))


if __name__ == "__main__":
    main()
