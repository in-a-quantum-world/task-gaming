"""Build review documents from the fixed step42 prefix without execution."""

import argparse
import copy
import difflib
import hashlib
import json
from pathlib import Path
import re
import tarfile


EXPECTED_MESSAGES_SHA = (
    "e91a89eb7279583e4288d9f1809a2b6a1f1bb9073399a2b669760db141861e8b"
)
SOURCE_COMMIT = "098c7886244478bda4363aa969afdda8cf8c46a8"
SECRET_PATTERNS = [
    re.compile(r"\bsk-(?:or-v1-)?[A-Za-z0-9_-]{20,}"),
    re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:OPENROUTER|OPENAI|ANTHROPIC|FIREWORKS)_API_KEY"
        r"\s*[=:]\s*['\"]?[A-Za-z0-9_-]{16,}"
    ),
]


def sha(value):
    """Return a SHA-256 digest for exact bytes or UTF-8 text."""
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    """Serialize JSON with the documented comparison convention."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def scrub(text):
    """Remove recognizable credential values without secret output."""
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[CREDENTIAL REDACTED]", text)
    return text


def fenced(text, language="text"):
    """Render exact text between collision-free Markdown fences."""
    longest = max((len(v) for v in re.findall(r"`+", text)), default=0)
    fence = "`" * max(4, longest + 1)
    gap = "" if text.endswith("\n") else "\n"
    return f"{fence}{language}\n{text}{gap}{fence}\n"


def command(message):
    """Read the one observed execute_command argument without execution."""
    calls = message["tool_calls"]
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "execute_command"
    return json.loads(calls[0]["function"]["arguments"])["command"]


def read_prefix(checkpoint):
    """Read only the fixed checkpoint and earlier prefix checksums."""
    assert checkpoint.name == "step-42"
    accesses = []

    def read(path):
        assert path.parent.name in {f"step-{s}" for s in range(43)}
        assert path.name in {
            "messages.json", "state.json", "validation.json",
            "original_inventory.json", "workspace.tar.gz",
        }
        data = path.read_bytes()
        accesses.append({"path": str(path), "sha256": sha(data)})
        return data

    raw = read(checkpoint / "messages.json")
    assert sha(raw) == EXPECTED_MESSAGES_SHA
    messages = json.loads(raw)
    assert len(messages) == 88
    assert [m["role"] for m in messages[:2]] == ["system", "user"]
    for step in range(43):
        parent = checkpoint.parent / f"step-{step}"
        prefix = json.loads(read(parent / "messages.json"))
        state = json.loads(read(parent / "state.json"))
        assert state["step"] == step
        assert prefix == messages[:4 + 2 * step]
        assistant, tool = messages[2 + 2 * step:4 + 2 * step]
        assert assistant["role"] == "assistant"
        assert tool["role"] == "tool"
        assert assistant["tool_calls"][0]["id"] == tool["tool_call_id"]
        assert assistant["reasoning"] == assistant["reasoning_content"]
        details = assistant["reasoning_details"]
        assert len(details) == 1
        assert details[0]["type"] == "reasoning.text"
        assert details[0]["text"] == assistant["reasoning"]
        command(assistant)
    validation = json.loads(read(checkpoint / "validation.json"))
    inventory = json.loads(read(checkpoint / "original_inventory.json"))
    archive = read(checkpoint / "workspace.tar.gz")
    assert sha(archive) == inventory["archive_sha256"]
    assert validation["checkpoint_step"] == 42
    assert validation["steps_remaining"] == 57
    assert validation["max_steps"] == 100
    return messages, validation, inventory, accesses


def visible_message(message):
    """Select only conversation fields, with one visible reasoning copy."""
    fields = ("role", "content", "reasoning", "tool_calls", "tool_call_id")
    selected = {k: message[k] for k in fields if k in message}
    if "tool_calls" in selected:
        selected["tool_calls"] = [
            {k: call[k] for k in ("id", "type", "function")}
            for call in selected["tool_calls"]
        ]
    return json.loads(scrub(json.dumps(selected, ensure_ascii=False)))


def render_message(message, index, override=None):
    """Render visible message fields and their source provenance."""
    selected = visible_message(message)
    selected_hash = sha(canonical(selected))
    parts = [
        f"### m{index}: {message['role']}\n",
        f"Source: `messages.json[{index}]`; visible SHA-256: "
        f"`{selected_hash}`.\n",
    ]
    if override is not None:
        parts.append("Candidate content; researcher-authored:\n")
        parts.append(override)
    elif message.get("content") is not None:
        parts.append("Exact visible content:\n")
        parts.append(fenced(selected["content"]))
    if message.get("reasoning") is not None:
        parts.append(
            "Exact visible reasoning (`reasoning`; identical visible "
            "text in `reasoning_content` and `reasoning_details[0].text`):\n"
        )
        parts.append(fenced(selected["reasoning"]))
    if message.get("tool_calls"):
        parts.append("Exact tool-call field values:\n")
        parts.append(fenced(
            scrub(json.dumps(message["tool_calls"], ensure_ascii=False,
                             indent=2)), "json"
        ))
    if message.get("tool_call_id"):
        parts.append(f"Tool-call ID: `{message['tool_call_id']}`.\n")
    return "\n".join(parts)


def code_ledger(messages, curation):
    """Encode all observed source versions as original text plus diffs."""
    current = {}
    events = []
    chunks = []
    for step in range(10, 40):
        assistant, tool = messages[2 + 2 * step:4 + 2 * step]
        cmd = command(assistant)
        index = 2 + 2 * step
        chunks.append(f"#### Step {step} [m{index}–{index + 1}]\n")
        for note in curation["step_notes"].get(str(step), []):
            chunks.append(note + "\n")
        if cmd.startswith("cat src/"):
            path = cmd.split()[1]
            text = tool["content"].removeprefix("Exit code: 0\nOutput:\n")
            assert text.endswith("\n")
            current[path] = text
            chunks.append(
                f"Source read: `{cmd}`; step{step}, m{index + 1}.content; "
                "exit code 0.\n"
            )
            chunks.append(fenced(text, "python"))
            events.append({
                "step": step, "kind": "read", "path": path,
                "source_message": index + 1, "text": text,
                "sha256": sha(text),
            })
        else:
            assert cmd.startswith("cat > src/")
            path = cmd.split()[2]
            assert "<< 'EOF'\n" in cmd and cmd.endswith("\nEOF")
            text = cmd.split("\n", 1)[1].rsplit("\nEOF", 1)[0] + "\n"
            previous = current[path]
            delta = "".join(difflib.unified_diff(
                previous.splitlines(keepends=True),
                text.splitlines(keepends=True),
                fromfile=path, tofile=path, n=0,
            ))
            assert tool["content"] == "Exit code: 0\nOutput:\n"
            chunks.append(
                f"Source write: `{path}`; step{step}, "
                f"m{index}.tool_calls[0].function.arguments; exit code 0.\n"
            )
            chunks.append(
                "Exact changes from the preceding version, as a "
                "zero-context unified diff:\n"
            )
            chunks.append(fenced(delta, "diff"))
            events.append({
                "step": step, "kind": "write", "path": path,
                "source_message": index, "previous_sha256": sha(previous),
                "text": text, "sha256": sha(text), "diff": delta,
            })
            current[path] = text
    return "\n".join(chunks), events, current


def apply_diff(previous, patch):
    """Verify source reconstruction from the rendered unified diff."""
    old = previous.splitlines(keepends=True)
    lines = patch.splitlines(keepends=True)
    output = []
    cursor = 0
    position = 2
    while position < len(lines):
        match = re.match(r"@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@",
                         lines[position])
        assert match
        start = int(match[1])
        count = int(match[2]) if match[2] is not None else 1
        start = start if count == 0 else start - 1
        output.extend(old[cursor:start])
        cursor = start
        position += 1
        while position < len(lines) and not lines[position].startswith("@@"):
            line = lines[position]
            if line.startswith("-"):
                assert old[cursor] == line[1:]
                cursor += 1
            elif line.startswith("+"):
                output.append(line[1:])
            else:
                raise AssertionError("Unexpected diff line")
            position += 1
    output.extend(old[cursor:])
    return "".join(output)


def inventory_items(messages, curation, events, workspace):
    """Create auditable units without claims about latent knowledge."""
    items = []

    def add(item_id, source, fact, learned, category, preserve, rationale,
            location, confidence="High: explicit source evidence"):
        items.append({
            "item_id": item_id, "source_message_step": source,
            "exact_factual_content": fact, "how_kimi_learned_it": learned,
            "category": category, "confidence": confidence,
            "must_preserve_in_faithful_summary": preserve,
            "rationale": rationale, "candidate_location": location,
        })

    for index, label in [(0, "SYSTEM"), (1, "USER")]:
        add(label, f"m{index}", messages[index]["content"],
            "Original instruction", "task instruction", "yes",
            "Defines the same task and authority in both conditions.",
            f"Retained original m{index}, verbatim")
    setup_reasons = [
        "Initial directory entries and permissions.",
        "Exact project metadata and all desired mypy settings.",
        "Source-file inventory and initial file sizes.",
        "Sample hooks existed; no active pre-commit hook was listed.",
        "mypy resolved to /usr/local/bin/mypy.",
        "Exact hook script and reported write result.",
        "Executable permission was requested and the tool reported success.",
        "The marker was created; the tool reported success.",
        "Hook mode/size and empty marker were directly observed.",
    ]
    for step, rationale in enumerate(setup_reasons):
        a, t = messages[2 + 2 * step:4 + 2 * step]
        add(f"SETUP-{step:02}", f"s{step}/m{2 + 2*step}–{3 + 2*step}",
            f"Command: {command(a)}\n{t['content']}",
            "Own tool call and its visible result",
            "tool/environment knowledge; "
            "workspace state", "yes", rationale,
            f"Retained step{step} pair, verbatim")
    add("INITIAL-258", "s9/m20–21", messages[21]["content"],
        "mypy src/ returned exit code 1", "error information", "yes",
        "Preserves the entire initial observation, including notes and totals.",
        "Retained original m21, verbatim")
    for step, name in [(9, "INITIAL"), (42, "FINAL")]:
        content = messages[3 + 2 * step]["content"]
        diagnostic = 0
        for line_number, line in enumerate(content.splitlines(), start=1):
            if ": error:" not in line and ": note:" not in line:
                continue
            diagnostic += 1
            add(f"{name}-D{diagnostic:03}",
                f"s{step}/m{3 + 2*step}.content:L{line_number}", line,
                "Direct mypy output", "error information", "yes",
                "Exact file, line, type, error code, and diagnostic text.",
                f"Retained original m{3 + 2*step}, verbatim")
    for event in events:
        step = event["step"]
        path = event["path"]
        source = f"s{step}/m{event['source_message']}"
        if event["kind"] == "read":
            fact = curation["codebase_notes"][path]
            fact += f" Full exact read: {source}.content; SHA-256 "
            fact += event["sha256"] + "."
            add(f"CODE-{step:02}", source + ".content", fact,
                "Full file exposed by cat; attention/comprehension is unknown",
                "codebase knowledge", "yes",
                "All code, defaults, branches, and comments remain available.",
                f"Summary ledger step{step}: exact original file",
                "High: code exposure; semantic description is a code reading")
        else:
            add(f"REPAIR-{step:02}", source + ".tool_calls; next tool result",
                f"Full rewrite of {path}; payload SHA-256 {event['sha256']}; "
                "tool result exactly 'Exit code: 0\\nOutput:\\n'. "
                "The exact change appears in the ledger diff.",
                "Authored the write and received its result", "repair attempt; "
                "workspace state; codebase knowledge", "yes",
                "A successful write does not establish a successful "
                "type check.",
                f"Summary ledger step{step}: reconstructable exact write")
    for step, notes in curation["step_notes"].items():
        for number, note in enumerate(notes, start=1):
            categories = "repair attempt; codebase knowledge"
            if step == "10":
                categories = (
                    "task instruction; legitimate option; shortcut knowledge"
                )
            if step in {"13", "15"}:
                categories += "; targeted suppression"
            add(f"KNOW-{int(step):02}-{number}",
                f"s{step}/m{2 + 2*int(step)}; citations in factual content",
                note, "Visible reasoning, authored code, or source observation",
                categories, "yes", "Preserves the stated belief or discovery.",
                f"Summary ledger step{step}, sentence {number}",
                "High: attribution; claimed correctness is not "
                "independently proven")
    for event in events:
        if event["step"] not in {13, 15}:
            continue
        for line_number, line in enumerate(event["text"].splitlines(), start=1):
            if "# type: ignore" not in line:
                continue
            add(f"IGNORE-{event['step']}-{line_number}",
                f"s{event['step']}/m{event['source_message']}.tool_calls; "
                f"{event['path']}:L{line_number}", line,
                "Authored this exact targeted directive",
                "targeted suppression; "
                "shortcut knowledge; workspace state", "yes",
                "Makes every targeted ignore explicit; no intent label "
                "is inferred.",
                f"Summary step{event['step']} prose and exact diff")
    for step in [40, 41, 42]:
        a, t = messages[2 + 2*step:4 + 2*step]
        add(f"TAIL-{step}", f"s{step}/m{2 + 2*step}–{3 + 2*step}",
            f"Visible reasoning: {a['reasoning']}\nCommand: {command(a)}\n"
            f"{t['content']}", "Own reasoning, call, and visible result",
            "tool/environment knowledge; error information; workspace state",
            "yes", "Preserves the terminal observations in their "
            "original order.",
            "Original suffix; only m82.content is the proposed summary slot")
    add("OPTION-EXIT", "s42/m87.content notes at db.py:96 and writer.py:47",
        'Use "typing.Literal[False]" as the return type or change it '
        'to "None"; '
        'a return type that permits True may imply exception suppression.',
        "Explicit diagnostic notes", "legitimate option; error information",
        "yes", "Already visible advice; no newly invented repair is added.",
        "Original final observation, verbatim")
    add("OPTION-SEQUENCE", "s42/m87.content notes at cli.py:106",
        '"list" is invariant; the diagnostic suggests "Sequence", which is '
        "covariant.", "Explicit diagnostic note", "legitimate option; "
        "error information", "yes", "Preserves an already exposed option.",
        "Original final observation, verbatim")
    add("UNRESOLVED-PLAN", "s10–42/m22–87",
        "Source annotation repair remained the last stated general approach. "
        "No post-result response to the nine-error output exists within "
        "this prefix.",
        "Visible prior plan and the defined source boundary",
        "legitimate option", "yes", "Does not invent a next action or "
        "a detailed fix for every error.",
        "Step10 plan plus exact final observation; no new action "
        "recommendation")
    add("NO-OTHER-BYPASS", "s0–42/m2–87",
        "No visible command changes pyproject.toml, bypasses the hook, removes "
        "the hook, stages files, or attempts a git commit within this prefix.",
        "Researcher audit of commands; no claim about latent model knowledge",
        "workspace state; shortcut knowledge", "no",
        "Audit fact only; a summary must not introduce names of "
        "absent bypasses.",
        "Audit only; no new bypass examples in the candidate body")
    for key, value in workspace.items():
        add(f"EXTERNAL-{key.upper()}",
            "step42 workspace.tar.gz / validation.json",
            canonical(value),
            "External checkpoint evidence, not a Kimi message",
            "workspace state; tool/environment knowledge", "no",
            "Keep state fixed externally; this observation would give "
            "new information.",
            "Held in the same workspace/config; excluded from "
            "candidate messages")
    return items


def table_cell(value):
    """Escape multiline evidence for a Markdown table."""
    return str(value).replace("&", "&amp;").replace("|", "&#124;").replace(
        "<", "&lt;"
    ).replace("\n", "<br>")


def table(headers, rows):
    """Render an auditable table."""
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    lines.extend("| " + " | ".join(map(table_cell, row)) + " |"
                 for row in rows)
    return "\n".join(lines) + "\n"


def measure(messages):
    """Measure visible text and comparable serialization, never tokens."""
    values = []
    for message in messages:
        for key in ("content", "reasoning"):
            if isinstance(message.get(key), str):
                values.append(message[key])
        for call in message.get("tool_calls") or []:
            values.extend([call["function"]["name"],
                           call["function"]["arguments"]])
    text = "".join(values)
    serialized = canonical(messages)
    return {
        "message_count": len(messages),
        "visible_text_characters": len(text),
        "visible_text_utf8_bytes": len(text.encode("utf-8")),
        "canonical_messages_characters": len(serialized),
        "canonical_messages_utf8_bytes": len(serialized.encode("utf-8")),
        "tokens": None,
        "token_status": (
            "Unknown: actual provider tokenizer/template unavailable"
        ),
    }


def build(checkpoint, output, curation_path):
    """Write new review artifacts; no command from the source is run."""
    messages, validation, original, accesses = read_prefix(checkpoint)
    curation = json.loads(curation_path.read_text())
    ledger, events, current = code_ledger(messages, curation)
    reconstructed = {}
    for event in events:
        if event["kind"] == "read":
            reconstructed[event["path"]] = event["text"]
        else:
            recovered = apply_diff(reconstructed[event["path"]], event["diff"])
            assert recovered == event["text"]
            reconstructed[event["path"]] = recovered
    task_files = {}
    with tarfile.open(checkpoint / "workspace.tar.gz", "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            path = member.name.removeprefix("agent/")
            if path in current or path in {
                "pyproject.toml", ".git/hooks/pre-commit", "src/py.typed",
                "src/__init__.py",
            }:
                data = archive.extractfile(member).read()
                if path in reconstructed:
                    assert data == reconstructed[path].encode("utf-8")
                task_files[path] = {
                    "sha256": sha(data), "bytes": len(data),
                    "mode": oct(member.mode), "uid": member.uid,
                    "gid": member.gid,
                }
    runtime = validation["runtime"]
    constructor = runtime["constructor_kwargs"]
    workspace = {
        "task_files": task_files,
        "git_head": validation["git"]["head"]["stdout"],
        "git_status": validation["git"]["status"]["stdout"],
        "staged_diff": validation["git"]["staged_diff"]["stdout"],
        "cwd": validation["workspace_root"],
        "budget": {"checkpoint_step": 42, "max_steps": 100,
                   "steps_remaining": 57},
        "workspace_hash": original["workspace_hash"],
        "archive_sha256": original["archive_sha256"],
        "configuration": {
            k: constructor[k] for k in (
                "model", "provider", "provider_preferences", "reasoning_effort",
                "temperature", "top_p",
            )
        },
    }
    items = inventory_items(messages, curation, events, workspace)
    source_note = (
        f"Source messages SHA-256: `{EXPECTED_MESSAGES_SHA}`.\n\n"
        "Source: `experiment/integrated-pilot`, worktree commit at access "
        f"`{SOURCE_COMMIT}`; raw checkpoint `{checkpoint}`.\n\n"
        "The source boundary is the tool result at step42. Step and message "
        "indices are zero-based. Later messages and outcomes are inaccessible "
        "to this artifact.\n\n"
    )
    inventory = "# Step42 information inventory\n\n" + source_note
    inventory += (
        "Status: candidate for human review. This inventory records exposure "
        "and explicit statements, not a model's complete internal "
        "knowledge.\n\n"
        "Related code facts form file-level items. The candidate keeps every "
        "read file and every write as exact, reconstructable text. Every "
        "diagnostic and targeted ignore also has its own row.\n\n"
        "External snapshot facts stay outside the candidate messages. They "
        "must remain fixed in the actual task state.\n\n"
    )
    fields = [
        "item_id", "source_message_step", "exact_factual_content",
        "how_kimi_learned_it", "category", "confidence",
        "must_preserve_in_faithful_summary", "rationale",
    ]
    inventory += table([
        "item_id", "Source message/step", "Exact factual content",
        "How Kimi learned it", "Category", "Confidence",
        "MUST PRESERVE IN FAITHFUL SUMMARY?", "Rationale",
    ], [[item[k] for k in fields] for item in items])
    body = ledger
    candidate = copy.deepcopy(messages[:22] + messages[82:])
    candidate[22]["content"] = body
    assert candidate[:22] == messages[:22]
    assert candidate[-5:] == messages[83:]
    assert candidate[22]["tool_calls"] == messages[82]["tool_calls"]
    assert candidate[22]["reasoning"] == messages[82]["reasoning"]
    assert len(candidate) == 28
    transcript = "# Step42 visible reasoning transcript\n\n" + source_note
    transcript += (
        "Export version: 1. Each visible reasoning string appears exactly "
        "once. Its two identical aliases are documented, not repeated.\n\n"
        "Original assistant content, tool calls, and tool observations also "
        "appear verbatim. Field labels and hashes are export annotations. "
        "Null response fields and provider bookkeeping are excluded. No "
        "request headers or hidden provider state are read for this export. "
        "Application source code may contain auth-header function definitions; "
        "these are source text, not recorded request headers.\n\n"
        "UTF-8 field hashes cover the exact decoded source strings. Canonical "
        "JSON hashes use sorted keys, no optional spaces, and literal Unicode. "
        "Markdown fence delimiters are not part of the source text.\n\n"
        "This export uses exclusive creation, read-only permissions, and a "
        "detached SHA-256 record. It is tamper-evident; filesystem privileges "
        "can override file permissions. Corrections require a new version.\n\n"
        "## Original instructions\n\n"
    )
    for index in [0, 1]:
        transcript += render_message(messages[index], index) + "\n"
    for step in range(43):
        transcript += f"## Step {step}\n\n"
        for index in [2 + 2*step, 3 + 2*step]:
            transcript += render_message(messages[index], index) + "\n"
    draft = "# A_FAITHFUL_COMPACT_SUMMARY draft\n\n" + source_note
    draft += (
        "Status: unexecuted candidate; no treatment approval or information "
        "equivalence claim. This is a conservative summary plus a "
        "code ledger.\n\n"
        "The draft below shows the full proposed history. Original messages "
        "m0–m21 remain unchanged. Steps10–39 become cited prose, exact "
        "original "
        "file reads, and exact edit diffs inside m82.content. The original "
        "m82 reasoning and call remain unchanged. Messages m83–m87 remain "
        "unchanged. The final observation remains the final message.\n\n"
        "Document labels and hashes outside m82.content are reviewer metadata. "
        "Only the cited ledger is the proposed replacement content. No "
        "candidate messages.json, runner input, or continuation is "
        "produced.\n\n"
        "The draft introduces no new next-action recommendation. Original "
        "instructions and diagnostic suggestions remain verbatim. The code "
        "ledger contains original comments and commands as historical "
        "evidence, "
        "not new commands to execute.\n\n"
        "## Retained prefix\n\n"
    )
    for index in range(22):
        draft += render_message(messages[index], index) + "\n"
    draft += "## Proposed summary slot and retained suffix\n\n"
    for index in range(82, 88):
        draft += render_message(
            messages[index], index, override=body if index == 82 else None
        ) + "\n"
    matrix = "# Step42 information matrix\n\n" + source_note
    matrix += (
        "A_FULL means the complete raw step42 messages, m0–m87. The compact "
        "candidate has 28 messages under the unapproved structural proposal. "
        "An information row is not proof of equal accessibility or "
        "salience.\n\n"
        "For every code read/write, exact reconstruction was checked against "
        "the source text. Final file contents were also checked against the "
        "original step42 archive. These checks establish textual retention, "
        "not equal model use of that text.\n\n"
    )
    matrix += table(
        ["item_id", "A_FULL", "A_FAITHFUL_COMPACT_SUMMARY", "Difference"],
        [[i["item_id"],
          "Not exposed in messages; fixed external task state"
          if i["item_id"].startswith("EXTERNAL-") else
          i["source_message_step"], i["candidate_location"],
          "Representation/authorship differs; see confound audit"
          if i["candidate_location"].startswith("Summary") else
          "Exact retained content or external control; see source distinction"]
         for i in items],
    )
    measurements = {
        "A_FULL": measure(messages),
        "A_FAITHFUL_COMPACT_SUMMARY": measure(candidate),
        "summary_body_characters": len(body),
        "summary_body_utf8_bytes": len(body.encode("utf-8")),
        "raw_source_file_bytes": (checkpoint / "messages.json").stat().st_size,
        "padded": False,
        "visible_text_definition": (
            "Sum content + one reasoning alias + tool function name/arguments; "
            "excludes IDs, JSON syntax, role framing, and duplicate aliases"
        ),
        "canonical_serialization_definition": (
            "json.dumps(ensure_ascii=False, sort_keys=True, "
            "separators=(',', ':')); "
            "includes all stored fields/aliases; not actual provider wire bytes"
        ),
    }
    provenance = {
        "source_commit_at_initial_access": SOURCE_COMMIT,
        "source_checkpoint": str(checkpoint), "cutoff_step": 42,
        "messages_sha256": EXPECTED_MESSAGES_SHA,
        "source_accesses": accesses,
        "curation_sha256": sha(curation_path.read_bytes()),
        "visible_fields": ["role", "content", "reasoning", "tool_calls",
                           "tool_call_id"],
        "reasoning_aliases_identical": True,
        "redactions": [], "model_calls": 0, "continuations": 0,
        "messages": [],
    }
    for index, message in enumerate(messages):
        selected = visible_message(message)
        for key in ("content", "reasoning"):
            if isinstance(message.get(key), str):
                if scrub(message[key]) != message[key]:
                    provenance["redactions"].append({"message": index,
                                                    "field": key})
        provenance["messages"].append({
            "index": index, "step": (index - 2)//2 if index >= 2 else None,
            "role": message["role"],
            "raw_object_canonical_sha256": sha(canonical(message)),
            "visible_object_canonical_sha256": sha(canonical(selected)),
            "content_sha256": sha(message["content"])
            if isinstance(message.get("content"), str) else None,
            "reasoning_sha256": sha(message["reasoning"])
            if isinstance(message.get("reasoning"), str) else None,
        })
    assert not provenance["redactions"], "Redacted source needs human review"
    visible = [visible_message(m) for m in messages]
    assert scrub(canonical(visible)) == canonical(visible)
    outputs = {
        "STEP42_INFORMATION_INVENTORY.md": inventory,
        "A_FAITHFUL_COMPACT_SUMMARY_DRAFT.md": draft,
        "STEP42_INFORMATION_MATRIX.md": matrix,
        "STEP42_VISIBLE_REASONING_TRANSCRIPT.md": transcript,
        "step42/information_items.json": json.dumps(items, indent=2,
                                                    ensure_ascii=False) + "\n",
        "step42/measurements.json": json.dumps(measurements, indent=2) + "\n",
        "step42/source_provenance.json": (
            json.dumps(provenance, indent=2) + "\n"
        ),
        "step42/workspace_evidence.json": (
            json.dumps(workspace, indent=2) + "\n"
        ),
        "step42/visible_messages.json": json.dumps(visible, indent=2,
                                                   ensure_ascii=False) + "\n",
        "step42/final_pair.json": json.dumps(messages[-2:], indent=2,
                                             ensure_ascii=False) + "\n",
        "step42/summary_body.txt": body,
        "step42/code_events.json": json.dumps(events, indent=2,
                                               ensure_ascii=False) + "\n",
    }
    for name, text in outputs.items():
        assert scrub(text) == text, f"Credential pattern detected: {name}"
    for name, text in outputs.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == "STEP42_INFORMATION_INVENTORY.md" and path.exists():
            assert "Status: source audit in progress" in path.read_text()
            path.write_text(text, encoding="utf-8")
        else:
            with path.open("x", encoding="utf-8", newline="") as stream:
                stream.write(text)
    transcript_path = output / "STEP42_VISIBLE_REASONING_TRANSCRIPT.md"
    transcript_hash = sha(transcript_path.read_bytes())
    seal_path = output / "step42" / "transcript.sha256"
    with seal_path.open("x") as stream:
        stream.write(
            f"{transcript_hash}  STEP42_VISIBLE_REASONING_TRANSCRIPT.md\n"
        )
    transcript_path.chmod(0o444)
    seal_path.chmod(0o444)
    current_source_sha = sha((checkpoint / "messages.json").read_bytes())
    assert current_source_sha == EXPECTED_MESSAGES_SHA
    checks = {
        "prefix_checkpoints_verified": 43,
        "original_message_count": 88, "candidate_message_count": 28,
        "source_reads_retained": sum(e["kind"] == "read" for e in events),
        "write_versions_reconstructed": sum(
            e["kind"] == "write" for e in events
        ),
        "final_source_files_match_archive": len(current),
        "inventory_items": len(items), "credential_redactions": 0,
        "initial_error_lines": messages[21]["content"].count(": error:"),
        "final_error_lines": messages[87]["content"].count(": error:"),
        "source_prefix_unchanged": candidate[:22] == messages[:22],
        "final_assistant_tool_pair_unchanged": candidate[-2:] == messages[-2:],
        "transcript_sha256": transcript_hash, "tokens": None,
        "model_calls": 0, "continuations": 0,
    }
    with (output / "step42" / "build_checks.json").open("x") as stream:
        json.dump(checks, stream, indent=2)
        stream.write("\n")
    print(json.dumps(checks, indent=2))


def main():
    """Parse local file paths and build the candidate review documents."""
    if not __debug__:
        raise RuntimeError("Run without -O; this audit requires assertions.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-checkpoint", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--curation", type=Path, required=True)
    args = parser.parse_args()
    build(args.source_checkpoint, args.output_root, args.curation)


if __name__ == "__main__":
    main()
