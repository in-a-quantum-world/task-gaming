"""Instrument the patched upstream loop without changing its step logic."""

import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

sys.path.insert(0, "/opt")

from agent_interp_envs import checkpoint, tool_calling
from agent_interp_envs.config import load_config
from agent_interp_envs.providers import create_provider
from agent_interp_envs.providers.mock_provider import MockProvider
import run_step as step_module
from score import score_precommit_hook
import states

from common import now, redact, save
from telemetry import instrument
from workspace import (
    WORKSPACE, archive_workspace, capture_checkpoint, compare_external,
    external_inventory, restore_archive, validator,
)


OUTPUT = Path("/opt/output")
CONFIG_PATH = Path(sys.argv[1])
CONFIG = load_config(CONFIG_PATH)
CONTEXT = {"step": -1, "invocations": 0, "provider": None, "state": None}
spec = importlib.util.spec_from_file_location("pilot_agent", "/opt/agent.py")
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)
original_dump = agent.dump
original_step = agent.run_step
original_restore = agent.restore
original_command = step_module.run_command


def provider_factory(**kwargs):
    if kwargs["provider"] == "mock":
        provider = MockProvider(
            model=kwargs["model"], messages=kwargs["messages"],
            tools=kwargs["tools"], mock_script=CONFIG["pilot"]["script"])
    else:
        provider = create_provider(**kwargs)
    CONTEXT["provider"] = provider
    instrument(provider, OUTPUT, CONTEXT)
    runtime = {
        "provider": kwargs["provider"], "model": provider.model,
        "constructor_kwargs": {k: v for k, v in kwargs.items()
                               if k != "messages"},
        "request_kwargs": getattr(provider, "kwargs", {}),
        "tools": kwargs["tools"], "agent_cwd": "/agent",
        "agent_environment": tool_calling._agent_env(),
        "image_id": os.environ["PILOT_IMAGE_ID"],
        "command_timeout_seconds": 30,
    }
    if hasattr(provider, "client"):
        runtime["sdk_max_retries"] = provider.client.max_retries
        runtime["sdk_timeout"] = str(provider.client.timeout)
        runtime["base_url"] = str(provider.client.base_url)
    save(OUTPUT / "runtime.json", runtime)
    if not Path("/opt/checkpoint").exists():
        initial = OUTPUT / "initial"
        initial.mkdir()
        save(initial / "state.json", states.CodingAgentState().to_dict())
        save(initial / "messages.json", provider.messages)
        archive_workspace(initial)
        capture_checkpoint(initial, CONFIG_PATH, OUTPUT / "runtime.json")
    return provider


def execute(command, *args, **kwargs):
    result = original_command(command, *args, **kwargs)
    CONTEXT.setdefault("executions", []).append({
        "command": command, "returncode": result[0],
        "output": redact(result[1]),
    })
    return result


def run_step(provider, state, config):
    CONTEXT.update(step=state.step, state=state, executions=[],
                   native_message=None)
    return original_step(provider, state, config)


def dump(state, provider, destination):
    original_dump(state, provider, destination)
    archive_workspace(destination)
    result = capture_checkpoint(destination, CONFIG_PATH,
                                OUTPUT / "runtime.json")
    save(destination / "upstream_score.json", score_precommit_hook(
        state.commands, WORKSPACE))
    save(destination / "actions.json", {
        "native_message": CONTEXT.get("native_message"),
        "executions": CONTEXT.get("executions", []),
        "synthetic": CONFIG["agent"]["provider"] == "mock",
    })
    inventory_path = destination / "original_inventory.json"
    reference = json.loads(inventory_path.read_text())
    if reference["files"] != result["files"] or result["probe_mutations"]:
        raise RuntimeError("Original workspace changed during capture")
    if external_inventory()["live_agent_processes"]:
        raise RuntimeError("Live agent processes prevent a stable checkpoint")


def restore(config, source):
    state, provider = original_restore(config, source)
    CONTEXT.update(state=state, step=state.step)
    before, _, _ = validator.inventory(WORKSPACE)
    expected = json.loads((source / "original_inventory.json").read_text())
    save(OUTPUT / "upstream_restore_check.json", {
        "matches_original": before == expected["files"],
        "changed_paths": sorted(k for k in before.keys()
                                | expected["files"].keys()
                                if before.get(k) != expected["files"].get(k)),
    })
    restore_archive(source)
    destination = OUTPUT / "restored"
    destination.mkdir()
    save(destination / "state.json", state.to_dict())
    save(destination / "messages.json", provider.messages)
    archive_workspace(destination)
    actual = capture_checkpoint(destination, CONFIG_PATH,
                                OUTPUT / "runtime.json")
    original = json.loads((source / "validation.json").read_text())
    comparison = validator.compare(original, actual)
    original_external = json.loads((source / "external.json").read_text())
    restored_external = json.loads((destination / "external.json").read_text())
    comparison["external_inventory_equal"] = compare_external(
        original_external, restored_external)
    save(OUTPUT / "restore_comparison.json", comparison)
    if (comparison["verdict"] != "equal_on_recorded_fields"
            or not comparison["mtimes_equal"]
            or not comparison["external_inventory_equal"]):
        raise RuntimeError("Restore does not match ORIGINAL checkpoint")
    # This stage permits technical restores only, with zero decisions.
    raise SystemExit(0)


def main():
    agent.create_provider = provider_factory
    checkpoint.create_provider = provider_factory
    agent.dump = dump
    agent.run_step = run_step
    agent.restore = restore
    step_module.run_command = execute
    reason = "runtime_failure"
    started = now()
    try:
        agent.main()
        state = CONTEXT["state"]
        reason = ("text_only_or_done" if state.task_completed else "cap_hit")
    except SystemExit as error:
        if Path("/opt/checkpoint").exists() and error.code == 0:
            reason = "restore_only"
        else:
            raise
    except BaseException as error:
        save(OUTPUT / "error.json", {
            "type": type(error).__name__, "message": redact(str(error)),
            "traceback": redact(traceback.format_exc()),
        })
        raise
    finally:
        provider, state = CONTEXT["provider"], CONTEXT["state"]
        save(OUTPUT / "termination.json", {
            "start": started, "end": now(), "reason": reason,
            "provider_invocations": CONTEXT["invocations"],
            "next_step": state.step if state else None,
            "synthetic": CONFIG["agent"]["provider"] == "mock",
        })
        if provider is not None:
            save(OUTPUT / "messages.json", provider.messages)
        if state is not None:
            save(OUTPUT / "state.json", state.to_dict())


if __name__ == "__main__":
    main()
