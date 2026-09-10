"""Verify the step42 review artifacts without model or source-code execution."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile


def digest(data):
    """Return the hash of exact bytes."""
    return hashlib.sha256(data).hexdigest()


def code_block(section, language):
    """Read the single labeled fenced block from a review section."""
    match = re.search(
        r"^(`{4,})" + re.escape(language) + r"\n(.*?)^\1\n",
        section, flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    return match[2]


def sections(text, expression):
    """Index distinct review sections by numeric source index."""
    headings = list(re.finditer(expression, text, flags=re.MULTILINE))
    output = {}
    for position, heading in enumerate(headings):
        end = headings[position + 1].start() if position + 1 < len(
            headings
        ) else len(text)
        output[int(heading[1])] = text[heading.end():end]
    return output


def verify_transcript(root, messages, provenance):
    """Check all displayed fields against the raw source, independently."""
    path = root / "STEP42_VISIBLE_REASONING_TRANSCRIPT.md"
    transcript = path.read_text()
    expected_hash = (root / "step42/transcript.sha256").read_text().split()[0]
    assert digest(path.read_bytes()) == expected_hash
    assert path.stat().st_mode & 0o222 == 0
    steps = re.findall(r"^## Step (\d+)$", transcript, re.MULTILINE)
    assert list(map(int, steps)) == list(range(43))
    displayed = sections(transcript, r"^### m(\d+): [a-z]+\n")
    assert list(displayed) == list(range(88))
    for index, message in enumerate(messages):
        section = displayed[index]
        for key, label in [
            ("content", "Exact visible content:"),
            ("reasoning", "Exact visible reasoning ("),
        ]:
            value = message.get(key)
            if value is None:
                continue
            actual = code_block(section.split(label, 1)[1], "text")
            expected = value if value.endswith("\n") else value + "\n"
            assert actual == expected, (index, key)
            field_hash = provenance["messages"][index][key + "_sha256"]
            assert digest(value.encode("utf-8")) == field_hash
        if message.get("tool_calls"):
            assert json.loads(code_block(section, "json")) == message[
                "tool_calls"
            ]
        if message.get("tool_call_id"):
            assert f"`{message['tool_call_id']}`" in section
    return expected_hash


def verify_code_ledger(root, messages, checkpoint):
    """Apply rendered diffs with GNU patch, never the source commands."""
    body = (root / "step42/summary_body.txt").read_text()
    ledger = sections(body, r"^#### Step (\d+) \[m\d+–\d+\]\n")
    assert list(ledger) == list(range(10, 40))
    known = set()
    writes = 0
    with tempfile.TemporaryDirectory(prefix="step42-passive-check-") as tmp:
        temporary = Path(tmp)
        for step in range(10, 40):
            message = messages[2 + 2*step]
            command = json.loads(
                message["tool_calls"][0]["function"]["arguments"]
            )["command"]
            if command.startswith("cat src/"):
                name = command.split()[1]
                original = messages[3 + 2*step]["content"].split(
                    "Output:\n", 1
                )[1]
                assert code_block(ledger[step], "python") == original
                destination = temporary / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(original)
                known.add(name)
            else:
                assert command.startswith("cat > src/")
                name = command.split()[2]
                expected = command.split("\n", 1)[1].rsplit(
                    "\nEOF", 1
                )[0] + "\n"
                patch = code_block(ledger[step], "diff")
                result = subprocess.run(
                    ["/usr/bin/patch", "--batch", "--silent", "--fuzz=0",
                     "-p0", "-d", tmp],
                    input=patch, text=True, capture_output=True, timeout=5,
                    env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
                    check=False,
                )
                assert result.returncode == 0, (step, result.stderr)
                assert (temporary / name).read_text() == expected
                writes += 1
        with tarfile.open(checkpoint / "workspace.tar.gz", "r:gz") as tar:
            for name in known:
                archived = tar.extractfile("agent/" + name).read()
                assert (temporary / name).read_bytes() == archived
    assert len(known) == 14 and writes == 16
    return body


def verify_workspace(root, messages, checkpoint):
    """Verify task-file records and the known hook/config/marker contents."""
    workspace_path = root / "step42/workspace_evidence.json"
    workspace = json.loads(workspace_path.read_text())
    with tarfile.open(checkpoint / "workspace.tar.gz", "r:gz") as tar:
        for name, record in workspace["task_files"].items():
            member = tar.getmember("agent/" + name)
            content = tar.extractfile(member).read()
            assert digest(content) == record["sha256"]
            assert len(content) == record["bytes"]
            assert oct(member.mode) == record["mode"]
        original_config = messages[5]["content"].split("Output:\n", 1)[1]
        assert tar.extractfile("agent/pyproject.toml").read().decode() == (
            original_config
        )
        hook_command = json.loads(
            messages[12]["tool_calls"][0]["function"]["arguments"]
        )["command"]
        hook = hook_command.split("\n", 1)[1].rsplit("\nEOF", 1)[0] + "\n"
        hook_member = tar.getmember("agent/.git/hooks/pre-commit")
        assert tar.extractfile(hook_member).read().decode() == hook
        assert hook_member.mode == 0o700
        assert tar.extractfile("agent/src/py.typed").read() == b""
        assert tar.extractfile("agent/src/__init__.py").read() == b""
    assert workspace["budget"] == {
        "checkpoint_step": 42, "max_steps": 100, "steps_remaining": 57,
    }


def verify_draft(root, messages, body):
    """Check the displayed candidate, including all unchanged messages."""
    draft = (root / "A_FAITHFUL_COMPACT_SUMMARY_DRAFT.md").read_text()
    displayed = sections(draft, r"^### m(\d+): [a-z]+\n")
    assert list(displayed) == list(range(22)) + list(range(82, 88))
    assert body in displayed[82]
    for index, section in displayed.items():
        original = messages[index]
        for key, label in [("content", "Exact visible content:"),
                           ("reasoning", "Exact visible reasoning (")]:
            text = original.get(key)
            if text is None:
                continue
            expected = text if text.endswith("\n") else text + "\n"
            assert code_block(section.split(label, 1)[1], "text") == expected
        if original.get("tool_calls"):
            assert json.loads(code_block(section, "json")) == original[
                "tool_calls"
            ]
        if original.get("tool_call_id"):
            assert f"`{original['tool_call_id']}`" in section


def verify(root):
    """Validate the artifact package and return a concise report."""
    provenance_path = root / "step42/source_provenance.json"
    provenance = json.loads(provenance_path.read_text())
    checkpoint = Path(provenance["source_checkpoint"])
    assert checkpoint.name == "step-42" and provenance["cutoff_step"] == 42
    source = (checkpoint / "messages.json").read_bytes()
    assert digest(source) == provenance["messages_sha256"]
    messages = json.loads(source)
    for access in provenance["source_accesses"]:
        path = Path(access["path"])
        assert path.parent.parent == checkpoint.parent
        assert re.fullmatch(r"step-(?:[0-9]|[1-3][0-9]|4[0-2])",
                            path.parent.name)
        assert path.name in {
            "messages.json", "state.json", "validation.json",
            "original_inventory.json", "workspace.tar.gz",
        }
        assert digest(path.read_bytes()) == access["sha256"]
    transcript_hash = verify_transcript(root, messages, provenance)
    body = verify_code_ledger(root, messages, checkpoint)
    verify_workspace(root, messages, checkpoint)
    verify_draft(root, messages, body)
    curation_path = root / "step42/curation.json"
    assert digest(curation_path.read_bytes()) == provenance["curation_sha256"]
    curation = json.loads(curation_path.read_text())
    for step, notes in curation["step_notes"].items():
        assert 10 <= int(step) <= 39
        for note in notes:
            assert note in body
            assert re.search(r"\[.*s\d+/m\d+.*\]$", note)
            assert all(int(n) <= 87 for n in re.findall(r"\bm(\d+)", note))
    candidate = copy.deepcopy(messages[:22] + messages[82:])
    candidate[22]["content"] = body
    assert candidate[-2:] == json.loads(
        (root / "step42/final_pair.json").read_text()
    ) == messages[-2:]
    assert candidate[:22] == messages[:22]
    assert candidate[-5:] == messages[83:]
    expected_roles = ["system", "user"] + ["assistant", "tool"] * 13
    assert [m["role"] for m in candidate] == expected_roles
    for index in range(2, len(candidate), 2):
        assert candidate[index]["tool_calls"][0]["id"] == candidate[
            index + 1
        ]["tool_call_id"]
    measures = json.loads((root / "step42/measurements.json").read_text())
    for name, history in [("A_FULL", messages),
                          ("A_FAITHFUL_COMPACT_SUMMARY", candidate)]:
        parts = []
        for message in history:
            parts.extend(message[k] for k in ["content", "reasoning"]
                         if isinstance(message.get(k), str))
            for call in message.get("tool_calls") or []:
                parts.extend(call["function"][k] for k in ["name", "arguments"])
        text = "".join(parts)
        assert len(text) == measures[name]["visible_text_characters"]
        assert len(text.encode()) == measures[name]["visible_text_utf8_bytes"]
        assert measures[name]["tokens"] is None
    items = json.loads((root / "step42/information_items.json").read_text())
    assert len(items) == len({item["item_id"] for item in items})
    assert sum(i["item_id"].startswith("IGNORE-") for i in items) == 8
    assert messages[21]["content"].count(": error:") == 258
    assert messages[87]["content"].count(": error:") == 9
    for filename in ["STEP42_INFORMATION_INVENTORY.md",
                     "STEP42_INFORMATION_MATRIX.md"]:
        document = (root / filename).read_text()
        for item in items:
            assert f"| {item['item_id']} |" in document
    assert not provenance["redactions"]
    return {
        "status": "PASS", "inventory_items": len(items),
        "raw_prefix_checkpoints": 43, "transcript_messages_verified": 88,
        "draft_messages_verified": 28,
        "visible_reasoning_messages_verified": 43,
        "rendered_write_diffs_verified_with_gnu_patch": 16,
        "final_source_files_equal_original_archive": 14,
        "targeted_ignores_retained": 8, "final_pair_equal_raw_source": True,
        "source_bytes_unchanged": True, "transcript_sha256": transcript_hash,
        "token_counts": "unknown", "model_calls": 0, "continuations": 0,
    }


def main():
    """Read local artifacts and optionally write a new verification report."""
    if not __debug__:
        raise RuntimeError("Run without -O; this audit requires assertions.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root", type=Path, default=Path("research"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = verify(args.research_root)
    text = json.dumps(report, indent=2) + "\n"
    if args.report:
        with args.report.open("x") as stream:
            stream.write(text)
    print(text, end="")


if __name__ == "__main__":
    main()
