"""Preserve the original restore before an approved history substitution."""

import contextlib
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, "/opt/pilot")
from common import now, save, sha256
from contract import (digest, read, validate_history,
                      validate_original_restore, validate_request)

spec = importlib.util.spec_from_file_location("preserved_loop",
                                               "/opt/pilot/loop.py")
preserved = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preserved)
original_restore = preserved.restore
original_factory = preserved.provider_factory
CONTRACT = read("/root/history/condition.json")
SOURCE = CONTRACT["source_contract"]
MODE = os.environ["HISTORY_MODE"]


def factory(**kwargs):
    provider = original_factory(**kwargs)
    first = True

    def wire_guard(request):
        nonlocal first
        if not (preserved.OUTPUT / "pre_invocation_manifest.json").is_file():
            raise ValueError("Provider request before validated manifest")
        validate_request(json.loads(request.content), CONTRACT, first,
                         preserved.CONTEXT["step"])
        first = False

    provider.client._client.event_hooks["request"].insert(0, wire_guard)
    if MODE == "offline-wire":
        import httpx2 as httpx

        def respond(request):
            return httpx.Response(200, json={
                "id": "offline-collection-gate", "created": 0,
                "object": "chat.completion",
                "model": SOURCE["actual_source_api_controls"]["model"],
                "provider": "Novita", "choices": [{
                    "index": 0, "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "OFFLINE",
                                "reasoning": "fixture only\n",
                                "reasoning_details": [{
                                    "type": "reasoning.text",
                                    "text": "fixture only\n"}]}}]})

        provider.client._client._transport = httpx.MockTransport(respond)
        provider.client._client._mounts.clear()
    return provider


def restore(config, source):
    try:
        original_restore(config, source)
    except SystemExit as error:
        if error.code != 0:
            raise
    else:
        raise RuntimeError("Unexpected original restore control flow")
    state = preserved.CONTEXT["state"]
    provider = preserved.CONTEXT["provider"]
    actual = read(preserved.OUTPUT / "restored/validation.json")
    original = read(source / "validation.json")
    comparison = read(preserved.OUTPUT / "restore_comparison.json")
    if state.to_dict() != read(source / "state.json"):
        raise ValueError("Restored state values differ from original")
    validate_original_restore(original, actual, comparison, provider.messages,
                              state.to_dict(), SOURCE)
    payload = Path("/root/history/condition.messages.json")
    if sha256(payload) != CONTRACT["condition_file_sha256"]:
        raise ValueError("Approved condition file changed inside container")
    messages = read(payload)
    validate_history(messages, SOURCE, CONTRACT["condition_id"],
                     CONTRACT["history_value_sha256"])
    if messages[:2] != provider.messages[:2]:
        raise ValueError("Exact original prompt objects differ")
    # Only the approved history changes after original workspace validation.
    provider.messages = messages
    private_paths = ["/root/history/condition.json", str(payload),
                     "/root/history-allocation.json",
                     "/opt/checkpoint/messages.json",
                     "/opt/output/runtime.json"]
    command = " && ".join(f"test ! -r {path}" for path in private_paths)
    code, _ = preserved.original_command(command)
    if code != 0:
        raise ValueError("Model shell can read private study artifacts")
    manifest = {
        "time": now(), "sample_id": CONTRACT["sample_id"],
        "contract": CONTRACT, "validation": comparison,
        "original_history_value_sha256":
        SOURCE["complete_history_value_sha256"],
        "condition_history_value_sha256": digest(provider.messages),
        "original_validation_sha256": sha256(source / "validation.json"),
        "restored_validation_sha256": sha256(
            preserved.OUTPUT / "restored/validation.json"),
        "actual_runtime": actual["runtime"],
        "continuation_ledger_state": read("/root/history-allocation.json"),
        "remaining_decisions": SOURCE["remaining_decisions"],
        "next_step": SOURCE["first_continuation_step"],
        "provider_invocations_before_manifest": 0,
        "model_cannot_read_study_artifacts": True,
        "private_path_probes": private_paths, "mode": MODE,
    }
    save(preserved.OUTPUT / "pre_invocation_manifest.json", manifest)
    if MODE == "restore-check":
        raise SystemExit(0)
    if MODE not in ("paid", "offline-wire"):
        raise ValueError("Unknown continuation mode")
    return state, provider


def dump(state, provider, destination):
    preserved.original_dump(state, provider, destination)
    preserved.archive_workspace(destination)
    result = preserved.capture_checkpoint(
        destination, preserved.CONFIG_PATH, preserved.OUTPUT / "runtime.json")
    save(destination / "actions.json", {
        "native_message": preserved.CONTEXT.get("native_message"),
        "executions": preserved.CONTEXT.get("executions", []),
        "synthetic": MODE != "paid",
    })
    reference = read(destination / "original_inventory.json")
    if reference["files"] != result["files"] or result["probe_mutations"]:
        raise RuntimeError("Original workspace changed during capture")
    if preserved.external_inventory()["live_agent_processes"]:
        raise RuntimeError("Live agent process prevents stable capture")


if __name__ == "__main__":
    preserved.provider_factory = factory
    preserved.restore = restore
    preserved.dump = dump
    with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), \
            contextlib.redirect_stderr(sink):
        preserved.main()
