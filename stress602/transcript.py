"""Render exact visible provider text and native actions from immutable runs."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re


def read(path):
    return json.loads(path.read_text())


def visible_reasoning(message):
    parts = []
    for key in ("reasoning", "reasoning_content"):
        if isinstance(message.get(key), str):
            parts.append((key, message[key]))
    for index, detail in enumerate(message.get("reasoning_details") or []):
        if isinstance(detail.get("text"), str):
            parts.append((f"reasoning_details[{index}].text", detail["text"]))
    return parts


def fenced(value, secrets, language="text"):
    for secret in secrets:
        if secret and secret in value:
            raise ValueError("Credential found; do not publish unchanged text")
    longest = max((len(s) for s in re.findall(r"`+", value)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{value}" + (
        "" if value.endswith("\n") else "\n") + f"{fence}\n"


def render(run, label, secrets):
    data = run / "data"
    steps = sorted(data.glob("step-*"),
                   key=lambda path: int(path.name.split("-")[1]))
    previous = read(data / "initial/messages.json")
    lines = [f"# Human-readable {label} Kimi trajectory", "",
             "This is a transcript, not a scientific behavior classification.",
             "All visible provider text below is verbatim. Repeated reasoning",
             "fields are shown separately because the provider returned both.",
             "Code-block delimiter newlines are display formatting only.",
             "Credentials and unrelated transport/account metadata are excluded.",
             "", f"Immutable raw root (local): `{run.resolve()}`.",
             "Per-step paths below resolve under that root. Raw files remain",
             "unchanged. The run's `artifact_sha256.json` pins every artifact.",
             ""]
    counts = {"steps": 0, "reasoning_fields": 0, "native_calls": 0,
              "tool_results": 0, "text_redactions": 0}
    for path in steps:
        step = int(path.name.split("-")[1])
        raw_path = data / f"api-assistant-{step + 1:04d}.json"
        message = read(raw_path)
        actions = read(path / "actions.json")
        history = read(path / "messages.json")
        if history[:len(previous)] != previous:
            raise ValueError("History prefix changed; transcript needs review")
        new_messages = history[len(previous):]
        previous = history
        validation = read(path / "validation.json")
        counts["steps"] += 1
        lines.extend([f"## STEP {step}", "",
                      f"Raw checkpoint: `data/step-{step}/`.",
                      f"Raw provider message: `{raw_path.relative_to(run)}`.",
                      "", "### VISIBLE KIMI REASONING", ""])
        parts = visible_reasoning(message)
        if not parts:
            lines.append("No visible reasoning text returned.")
        for field, value in parts:
            counts["reasoning_fields"] += 1
            lines.extend([f"Provider field: `{field}`.", "",
                          fenced(value, secrets)])
        lines.extend(["### ASSISTANT RESPONSE", ""])
        if message.get("content") is None:
            lines.append("Provider content: null.")
        else:
            lines.append(fenced(message["content"], secrets))
        lines.extend(["", "### NATIVE TOOL CALL", ""])
        calls = message.get("tool_calls") or []
        if not calls:
            lines.append("No native tool call returned.")
        for call in calls:
            counts["native_calls"] += 1
            function = call["function"]
            lines.extend([f"Tool: `{function['name']}`; ID: `{call['id']}`.",
                          "", "Exact returned arguments:", "",
                          fenced(function["arguments"], secrets, "json")])
            try:
                command = json.loads(function["arguments"])["command"]
            except (KeyError, TypeError, ValueError):
                command = None
            if isinstance(command, str):
                lines.extend(["Exact command text (decoded JSON string):", "",
                              fenced(command, secrets, "bash")])
        lines.extend(["### TOOL RESULT", ""])
        results = [m for m in new_messages if m.get("role") == "tool"]
        if not results:
            lines.append("No tool-result message at this decision.")
        for result in results:
            counts["tool_results"] += 1
            lines.extend([f"Tool call ID: `{result.get('tool_call_id')}`.", "",
                          fenced(result.get("content") or "", secrets)])
        for index, execution in enumerate(actions.get("executions", [])):
            lines.append(f"Execution {index}: exit code "
                         f"`{execution['returncode']}`.")
        lines.extend(["", "### MYPY ERROR COUNT AFTER STEP", "",
                      f"Active configuration: "
                      f"**{validation['mypy']['active']['error_count']}**. "
                      f"Pristine strict configuration: "
                      f"**{validation['mypy']['reference']['error_count']}**.",
                      "Harness measurement; it was not necessarily shown to "
                      "Kimi. Any model-visible check is in the tool result.", ""])
    # A response can arrive before a checkpoint fails. Preserve its visible text.
    saved_numbers = {int(p.name.split("-")[1]) + 1 for p in steps}
    for raw_path in sorted(data.glob("api-assistant-*.json")):
        number = int(raw_path.stem.split("-")[-1])
        if number in saved_numbers:
            continue
        message = read(raw_path)
        lines.extend([f"## UNSAVED DECISION {number - 1}", "",
                      f"Raw provider message: `{raw_path.relative_to(run)}`.",
                      "No complete checkpoint exists for this response.", "",
                      "### VISIBLE KIMI REASONING", ""])
        for field, value in visible_reasoning(message):
            counts["reasoning_fields"] += 1
            lines.extend([f"Provider field: `{field}`.", "",
                          fenced(value, secrets)])
        lines.extend(["### ASSISTANT RESPONSE", "",
                      fenced(message.get("content") or "", secrets),
                      "### NATIVE TOOL CALL", ""])
        for call in message.get("tool_calls") or []:
            counts["native_calls"] += 1
            lines.extend([f"Tool: `{call['function']['name']}`; "
                          f"ID: `{call['id']}`.", "",
                          fenced(call["function"]["arguments"], secrets,
                                 "json")])
        lines.extend(["### TOOL RESULT", "",
                      "No checkpointed result; inspect preserved partial files.",
                      "", "### MYPY ERROR COUNT AFTER STEP", "",
                      "Not measured in a complete checkpoint.", ""])
    # Preserve incomplete final requests as an explicit appendix if needed.
    if (data / "error.json").exists():
        lines.extend(["## Recorded run failure", "",
                      "The raw `data/error.json` preserves the infrastructure "
                      "failure. Completed decisions above remain intact.", ""])
    return "\n".join(lines), counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("label", choices=("258", "602"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    secrets = [value for key, value in os.environ.items() if value and any(
        token in key for token in ("API_KEY", "TOKEN", "SECRET", "PASSWORD"))]
    document, counts = render(args.run, args.label, secrets)
    with args.output.open("x") as stream:
        stream.write(document)
    receipt = {"run": str(args.run.resolve()), "output": str(args.output),
               "sha256": hashlib.sha256(document.encode()).hexdigest(),
               "raw_manifest_sha256": hashlib.sha256(
                   (args.run / "artifact_sha256.json").read_bytes()).hexdigest(),
               **counts}
    with args.receipt.open("x") as stream:
        json.dump(receipt, stream, indent=2)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
