"""Prospective full-history request gates; no behavior interpretation."""

import hashlib
import json
from pathlib import Path

CONDITION = "RESTORE_108_STEP32"


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    body = json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def validate_history(messages, contract):
    if digest(messages) != contract["complete_history_value_sha256"]:
        raise ValueError("Full original history differs")
    if messages[-2:] != contract["final_assistant_tool_pair"]:
        raise ValueError("Final assistant/tool pair differs")
    for index, role in enumerate(("system", "user")):
        text_hash = hashlib.sha256(messages[index]["content"].encode())
        if (messages[index]["role"] != role or text_hash.hexdigest()
                != contract[f"{role}_prompt_sha256"]):
            raise ValueError("Original prompt differs")


def validate_state(state, contract):
    if (state["step"] != contract["checkpoint_step"]
            or state["task_completed"]
            or contract["max_steps"] - state["step"] - 1
            != contract["remaining_decisions"]):
        raise ValueError("Original checkpoint budget/state differs")


def validate_request(body, contract, first):
    controls = {k: v for k, v in body.items() if k != "messages"}
    if controls != contract["actual_source_api_controls"]:
        raise ValueError("Request settings differ from the real source")
    if first:
        validate_history(body["messages"], contract)


def full_restore_check(original, actual, comparison, messages, state,
                       contract):
    validate_history(messages, contract)
    validate_state(state, contract)
    if (comparison["verdict"] != "equal_on_recorded_fields"
            or not comparison["history_equal"]
            or not comparison["mtimes_equal"]
            or not comparison["external_inventory_equal"]
            or actual["mypy"]["reference"]["errors_hash"]
            != contract["diagnostic_sha256"]
            or actual["mypy"]["reference"]["error_count"]
            != contract["diagnostic_count"]
            or actual["runtime"] != original["runtime"]):
        raise ValueError("Actual original restore gate failed")
