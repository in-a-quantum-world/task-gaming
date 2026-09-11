"""Validate immutable external histories and both checkpoint contracts."""

import hashlib
import json
from pathlib import Path

SOURCE_FILES = {
    "258_step42": ("history/A_FULL_258_STEP42_RUN1.json",
                   "SOURCE_PILOT_CONFIG.yaml", 42, 57),
    "108_step32": ("history/prepared108/RESTORE_108_STEP32.json",
                   "history/prepared108/SOURCE108_CONFIG.yaml", 32, 67),
}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    data = json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def validate_state(state, source):
    if (state["step"] != source["checkpoint_step"]
            or state["task_completed"] or source["max_steps"] != 100
            or 99 - state["step"] != source["remaining_decisions"]):
        raise ValueError("Source state or remaining budget differs")


def validate_roles(messages):
    if not isinstance(messages, list) or len(messages) < 4:
        raise ValueError("Expected a complete native message array")
    if [m.get("role") for m in messages[:2]] != ["system", "user"]:
        raise ValueError("Original system/user roles required")
    pending = None
    seen = set()
    for message in messages[2:]:
        role = message.get("role")
        if role == "assistant" and pending is None:
            calls = message.get("tool_calls") or []
            if not calls:
                if not isinstance(message.get("content"), str):
                    raise ValueError("Assistant summary must contain text")
                continue
            if len(calls) != 1:
                raise ValueError("Source tool schema permits one call")
            call = calls[0]
            function = call["function"]
            arguments = json.loads(function["arguments"])
            if (call["type"] != "function"
                    or function["name"] != "execute_command"
                    or set(arguments) != {"command"}
                    or not isinstance(arguments["command"], str)):
                raise ValueError("Native tool schema differs")
            pending = call["id"]
            if not isinstance(pending, str) or not pending or pending in seen:
                raise ValueError("Duplicate or invalid native tool ID")
            seen.add(pending)
        elif role == "tool" and pending is not None:
            if message.get("tool_call_id") != pending:
                raise ValueError("Native call/result IDs differ")
            if not isinstance(message.get("content"), str):
                raise ValueError("Tool result must be text")
            pending = None
        else:
            raise ValueError("Unexpected role or missing native result")
    if pending is not None or messages[-1]["role"] != "tool":
        raise ValueError("Checkpoint must end after the final tool result")


def validate_history(messages, source, condition, expected_digest):
    validate_roles(messages)
    if digest(messages) != expected_digest:
        raise ValueError("Approved history value hash differs")
    if messages[-2:] != source["final_assistant_tool_pair"]:
        raise ValueError("Exact original final assistant/tool pair differs")
    for index, role in enumerate(("system", "user")):
        value = hashlib.sha256(messages[index]["content"].encode())
        if value.hexdigest() != source[f"{role}_prompt_sha256"]:
            raise ValueError("Original prompt content differs")
    if (condition == "A_FULL" and digest(messages)
            != source["complete_history_value_sha256"]):
        raise ValueError("A_FULL must contain the complete original history")


def load_condition(payload, manifest_path, review_path, entry, source):
    """Read exact external bytes; never synthesize or rewrite wording."""
    checks = [(payload, "condition_file_sha256"),
              (manifest_path, "condition_manifest_sha256"),
              (review_path, "review_sha256")]
    for path, key in checks:
        if sha(path) != entry[key]:
            raise ValueError("Condition differs from frozen schedule")
    metadata, review = read(manifest_path), read(review_path)
    if (metadata["status"] != "reviewed_dry_run"
            or metadata["text_reviewed"] is not True
            or metadata["payload_sha256"] != entry["condition_file_sha256"]
            or metadata["condition"] != entry["condition_id"]):
        raise ValueError("Prototype export is unreviewed or mismatched")
    if (review["status"] != "approved" or not review["reviewer"]
            or not review["reviewed_at_utc"]
            or review["final_text_and_roles_approved"] is not True
            or review["checkpoint"] != entry["checkpoint"]
            or review["condition_id"] != entry["condition_id"]
            or review["payload_sha256"] != entry["condition_file_sha256"]
            or review["manifest_sha256"]
            != entry["condition_manifest_sha256"]):
        raise ValueError("Final researcher text/role approval absent or stale")
    lock = metadata["source_checkpoint"]
    if (lock["step"] != source["checkpoint_step"]
            or lock["remaining_decision_budget"]
            != source["remaining_decisions"]):
        raise ValueError("Prototype checkpoint budget differs")
    for name in ("messages.json", "state.json", "workspace.tar.gz"):
        if lock["raw_sha256"][name] != source["checkpoint_sha256"][name]:
            raise ValueError("Prototype source checkpoint hashes differ")
    messages = read(payload)
    original = read(Path(source["checkpoint"]) / "messages.json")
    if messages[:2] != original[:2]:
        raise ValueError("Original prompt objects differ")
    if (entry["condition_id"] == "A_FULL" and sha(payload)
            != source["checkpoint_sha256"]["messages.json"]):
        raise ValueError("A_FULL original file bytes differ")
    validate_history(messages, source, entry["condition_id"], digest(messages))
    return messages


def validate_original_restore(original, actual, comparison, messages, state,
                              source):
    validate_state(state, source)
    validate_history(messages, source, "A_FULL",
                     source["complete_history_value_sha256"])
    if (comparison["verdict"] != "equal_on_recorded_fields"
            or not comparison["history_equal"]
            or not comparison["mtimes_equal"]
            or not comparison["external_inventory_equal"]
            or actual["mypy"]["reference"]["errors_hash"]
            != source["diagnostic_sha256"]
            or actual["mypy"]["reference"]["error_count"]
            != source["diagnostic_count"]
            or actual["runtime"] != original["runtime"]):
        raise ValueError("Restore differs from actual ORIGINAL checkpoint")


def validate_request(body, contract, first, step):
    source = contract["source_contract"]
    if not source["first_continuation_step"] <= step < source["max_steps"]:
        raise ValueError("Decision outside remaining budget")
    controls = {key: value for key, value in body.items() if key != "messages"}
    if controls != source["actual_source_api_controls"]:
        raise ValueError("Exact source request controls differ")
    if first:
        validate_history(body["messages"], source, contract["condition_id"],
                         contract["history_value_sha256"])
