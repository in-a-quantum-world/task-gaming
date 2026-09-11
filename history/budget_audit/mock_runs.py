"""Exercise pinned loop and native step code with deterministic mock calls."""

import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import itertools
import json
from pathlib import Path
import socket
import sys
from types import SimpleNamespace
from unittest import mock

sys.path[:0] = ["/opt", "/opt/pilot"]
from agent_interp_envs import checkpoint
from agent_interp_envs.providers.mock_provider import MockProvider
import states
import run_step


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(root, saved_step, agent_text, label):
    destination = root / label
    destination.mkdir()
    module = SimpleNamespace(__name__="budget_agent_fixture")
    namespace = module.__dict__
    exec(compile(agent_text, "/opt/agent.py", "exec"), namespace)
    state = states.CodingAgentState(step=saved_step, variant="precommit_hook")
    config = json.loads(Path("/repo/SOURCE_PILOT_CONFIG.yaml").read_text())
    # This is a synthetic cursor, never a restore of a real checkpoint.
    config["task"]["target_errors"] = 258 if saved_step == 42 else 108
    initial = [{"role": "system", "content": "offline budget fixture"},
               {"role": "user", "content": "emit scripted native calls"}]
    provider = MockProvider(
        model="deterministic-budget-fixture", messages=copy.deepcopy(initial),
        tools=namespace["get_tools"](config),
        mock_script=[f"budget-probe-{i}" for i in range(120)])
    invocations, saved, commands = [], [], []
    original_invoke = provider.invoke

    def invoke():
        invocations.append(state.step)
        return original_invoke()

    def execute(command, *args, **kwargs):
        commands.append({"step": state.step, "command": command})
        return 0, "deterministic offline tool result\n"

    def dump(current, current_provider, unused):
        saved.append(current.step)
        checkpoint.dump(current, current_provider,
                        destination / f"step-{current.step}", snapshot=None)

    provider.invoke = invoke
    ids = itertools.count()
    namespace.update(
        load_config=lambda *args: config,
        restore=lambda *args: (state, provider),
        Path=lambda *args: SimpleNamespace(exists=lambda: True),
        dump=dump, print_step_header=lambda *args: None,
        print_final_results=lambda *args: None)
    with mock.patch.object(run_step, "run_command", side_effect=execute), \
         mock.patch("uuid.uuid4", side_effect=lambda:
                    SimpleNamespace(hex=f"{next(ids):032x}")), \
         mock.patch.object(socket.socket, "connect",
                           side_effect=AssertionError("Network forbidden")), \
         contextlib.redirect_stdout(io.StringIO()):
        namespace["main"]()
    return {
        "fixture": label, "synthetic_saved_step": saved_step,
        "invoked_steps": invocations, "saved_steps": saved,
        "mock_provider_calls": len(invocations),
        "native_tool_results": sum(m["role"] == "tool"
                                   for m in provider.messages),
        "script_commands_left": len(provider._script),
        "final_cursor": state.step,
        "ended_by_mock_script_exhaustion": not provider._script,
        "real_checkpoint_restored": False,
        "real_provider_requests": 0,
        "shell_execution": "deterministic recorder; no shell subprocess",
        "commands": commands,
    }


def check_expected(result, saved_step):
    expected = list(range(saved_step + 1, 100))
    assert result["invoked_steps"] == expected
    assert result["saved_steps"] == expected
    assert result["mock_provider_calls"] == 99 - saved_step
    assert result["native_tool_results"] == 99 - saved_step
    assert result["final_cursor"] == 100
    assert result["script_commands_left"] > 0
    assert 100 not in result["invoked_steps"]


def guard_case(loop_path, contract_path, output, first_step):
    """Test actual factory/transport guard AST without restoring a checkpoint."""
    contract_module = loop_path.parent / "contract.py"
    spec = importlib.util.spec_from_file_location("guard_contract",
                                                   contract_module)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contract = json.loads(contract_path.read_text())
    output.mkdir()
    client = SimpleNamespace(event_hooks={"request": []})
    provider = SimpleNamespace(client=SimpleNamespace(_client=client))
    context = {"step": first_step}
    namespace = {
        "original_factory": lambda **kwargs: provider,
        "MODE": "paid", "CONTRACT": contract, "json": json,
        "preserved": SimpleNamespace(OUTPUT=output, CONTEXT=context),
        "validate_request": module.validate_request,
    }
    tree = ast.parse(loop_path.read_text())
    factory = next(n for n in tree.body
                   if isinstance(n, ast.FunctionDef) and n.name == "factory")
    exec(compile(ast.Module(body=[factory], type_ignores=[]),
                 str(loop_path), "exec"), namespace)
    namespace["factory"]()
    guard = client.event_hooks["request"][0]
    body = {**contract["actual_source_api_controls"], "messages": []}
    request = SimpleNamespace(content=json.dumps(body).encode())
    try:
        guard(request)
    except ValueError:
        pass
    else:
        raise AssertionError("Missing pre-invocation manifest was accepted")
    (output / "pre_invocation_manifest.json").write_text("{}")
    # First-history equality is tested separately; suppress it here solely to
    # isolate the actual guard's decision-bound check without real histories.
    namespace["validate_request"] = lambda *args: None
    for step in (first_step, 99):
        context["step"] = step
        guard(request)
    rejected = []
    for step in (first_step - 1, 100, 101):
        context["step"] = step
        try:
            guard(request)
        except ValueError:
            rejected.append(step)
    assert rejected == [first_step - 1, 100, 101]
    return {"first_accepted": first_step, "last_accepted": 99,
            "rejected_steps": rejected,
            "missing_manifest_rejected": True,
            "real_checkpoint_restored": False,
            "provider_created": False, "transport_called": False,
            "guard_source_sha256": digest(loop_path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    text = Path("/opt/agent.py").read_text()
    results, mutations, guards = [], [], []
    for variant, step in ((258, 42), (108, 32)):
        result = run_case(args.output, step, text, f"{variant}-cap")
        check_expected(result, step)
        results.append(result)
        assert text.count("while state.step < max_steps:") == 1
        changed = text.replace("while state.step < max_steps:",
                               "while state.step <= max_steps:")
        mutant = run_case(args.output, step, changed, f"{variant}-mutant")
        try:
            check_expected(mutant, step)
        except AssertionError:
            caught = True
        else:
            caught = False
        assert caught and mutant["invoked_steps"][-1] == 100
        mutations.append({"variant": variant,
                          "deliberate_in_memory_mutation": "< changed to <=",
                          "extra_mock_decision": 100,
                          "regression_test_rejects_mutant": caught})
    guards.append(guard_case(
        Path("/repo/history/loop.py"),
        Path("/repo/history/A_FULL_258_STEP42_RUN1.json"),
        args.output / "guard258", 43))
    guards.append(guard_case(
        Path("/repo/history/prepared108/loop.py"),
        Path("/repo/history/prepared108/RESTORE_108_STEP32.json"),
        args.output / "guard108", 33))
    receipt = {
        "passed": True, "deterministic_mock_runs": results,
        "mutation_checks": mutations, "transport_guard_checks": guards,
        "agent_py_sha256": digest(Path("/opt/agent.py")),
        "run_step_py_sha256": digest(Path("/opt/run_step.py")),
        "mock_provider_module": MockProvider.__module__,
        "network": "Docker --network none plus socket-connect rejection",
        "scope": "Budget and guard audit with synthetic cursors, not an "
        "invocation of either real restoration/continuation path.",
    }
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps({"passed": True, "258": [43, 99, 57],
                      "108": [33, 99, 67], "decision100_rejected": True,
                      "mutations_detected": 2, "real_model_requests": 0}))


if __name__ == "__main__":
    main()
