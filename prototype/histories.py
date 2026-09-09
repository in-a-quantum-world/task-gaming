"""Build explicit history variants without edits to source checkpoints."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil


CONDITIONS = ("A_FULL", "B_FAILURE_FACT", "C_STATE_ONLY")


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checkpoint_hashes(directory):
    return {str(path.relative_to(directory)): file_hash(path)
            for path in sorted(directory.rglob("*")) if path.is_file()
            and path.name not in {"messages.json", "history_provenance.json"}}


def verify_bundle(directory):
    """Reject edits to prepared histories or workspace artifacts."""
    provenance = json.loads(
        (directory / "history_provenance.json").read_text())
    source = Path(provenance["source_checkpoint"])
    if file_hash(directory / "messages.json") != provenance["messages_sha256"]:
        raise ValueError("Prepared history changed after its record.")
    if checkpoint_hashes(directory) != provenance["artifact_hashes"]:
        raise ValueError("Prepared workspace artifacts changed.")
    if checkpoint_hashes(source) != provenance["artifact_hashes"]:
        raise ValueError("The source checkpoint changed.")
    if file_hash(source / "messages.json") != provenance[
            "source_messages_sha256"]:
        raise ValueError("The source history changed.")
    return provenance


def final_exchange(messages):
    """Keep the last tool exchange intact, including call IDs and roles."""
    if messages[-1]["role"] != "tool":
        raise ValueError("Choose a checkpoint after a tool observation.")
    start = len(messages) - 1
    while messages[start]["role"] == "tool":
        start -= 1
    if messages[start]["role"] != "assistant":
        raise ValueError("The final observation has no assistant tool call.")
    calls = {call["id"] for call in messages[start].get("tool_calls", [])}
    results = {message["tool_call_id"] for message in messages[start + 1:]}
    if calls != results:
        raise ValueError("The final tool exchange has unmatched IDs.")
    return messages[start:]


def build(source, facts_path, destination):
    """Copy each checkpoint and replace only its message history."""
    messages = json.loads((source / "messages.json").read_text())
    facts = json.loads(facts_path.read_text())
    if facts["source_messages_sha256"] != file_hash(source / "messages.json"):
        raise ValueError("Facts belong to another message history.")
    if [message["role"] for message in messages[:2]] != ["system", "user"]:
        raise ValueError("Only this task's initial system/user layout works.")
    last = final_exchange(messages)
    for item in facts["items"]:
        if not item["text"].strip() or "\n" in item["text"]:
            raise ValueError("Each information item must be one sentence.")
        if not item["present_in_A"] or not item["evidence_message_indices"]:
            raise ValueError("Summary sentences need evidence in A.")
        for index in item["evidence_message_indices"]:
            if not 0 <= index < len(messages):
                raise ValueError("An evidence index is outside A.")
    original_hashes = checkpoint_hashes(source)
    destination.mkdir(parents=True, exist_ok=False)
    metrics = {}
    for condition in CONDITIONS:
        target = destination / condition
        shutil.copytree(source, target)
        if condition != "A_FULL":
            sentences = [item["text"] for item in facts["items"]
                         if item[condition]]
            summary = {"role": "assistant", "content": "\n".join(sentences)}
            replaced = messages[:2] + [summary] + last
            (target / "messages.json").write_text(
                json.dumps(replaced, indent=2) + "\n")
        else:
            replaced = messages
        if checkpoint_hashes(target) != original_hashes:
            raise ValueError("History edit changed checkpoint artifacts.")
        body = (target / "messages.json").read_bytes()
        metrics[condition] = {
            "messages": len(replaced), "utf8_bytes": len(body),
            "history_token_count": None,
            "token_count_note": "No exact provider tokenizer was available.",
            "rough_bytes_div_4": len(body) / 4,
            "roles": [message["role"] for message in replaced],
            "latest_exchange_equal": final_exchange(replaced) == last,
            "checkpoint_artifacts_equal": True,
        }
        (target / "history_provenance.json").write_text(json.dumps({
            "condition": condition, "source_checkpoint": str(source),
            "source_messages_sha256": file_hash(source / "messages.json"),
            "messages_sha256": file_hash(target / "messages.json"),
            "artifact_hashes": original_hashes,
            "facts_sha256": file_hash(facts_path),
            "synthetic": facts["synthetic"],
        }, indent=2) + "\n")
    shutil.copy2(facts_path, destination / "information_items.json")
    (destination / "history_metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n")
    rows = [
        "# History information matrix", "",
        "EXPLORATORY ONLY — GENERATED BEFORE FINAL PREREGISTRATION", "",
        "Every B/C summary sentence appears below.", "",
        "The original system prompt and task prompt remain verbatim.",
        "The final assistant/tool exchange remains verbatim in each arm.",
        "Each sentence cites zero-based A message indices in the facts file.",
        "The summary uses the assistant role; its authorship is artificial.",
        "", "| INFORMATION ITEM | PRESENT IN A? | PRESENT IN B? | "
        "PRESENT IN C? | WHY INCLUDED/EXCLUDED | POSSIBLE CONFOUND |",
        "|---|---|---|---|---|---|",
    ]
    for item in facts["items"]:
        cells = [item["id"] + ": " + item["text"],
                 "Yes; indices " + str(item["evidence_message_indices"]),
                 "Yes" if item["B_FAILURE_FACT"] else "No",
                 "Yes" if item["C_STATE_ONLY"] else "No",
                 item["why"], item["possible_confound"]]
        rows.append("| " + " | ".join(cell.replace("|", "\\|")
                                    for cell in cells) + " |")
    rows += ["", "Omission register:", ""]
    rows += ["- " + note for note in facts["omissions"]]
    (destination / "history_information_matrix.md").write_text(
        "\n".join(rows) + "\n")
    (destination / "researcher_review.json").write_text(json.dumps({
        "checkpoint_scientifically_usable": False,
        "history_information_review_complete": False,
        "reason": "Synthetic fixture; no model checkpoint exists.",
    }, indent=2) + "\n")
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--facts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.checkpoint.resolve(), args.facts.resolve(),
                           args.output.resolve()), indent=2))


if __name__ == "__main__":
    main()
