"""Exercise the actual runtime functions with synthetic in-memory state."""

import ast
import copy
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import contract


def function(name, namespace):
    path = Path(__file__).parent / "loop.py"
    module = ast.parse(path.read_text())
    node = next(node for node in module.body
                if isinstance(node, ast.FunctionDef) and node.name == name)
    code = ast.Module(body=[node], type_ignores=[])
    exec(compile(code, str(path), "exec"), namespace)
    return namespace[name]


def exercise(test, source, original, state):
    messages = copy.deepcopy(original)
    messages.insert(2, {"role": "assistant", "content": "SYNTHETIC SUMMARY"})
    runtime = {
        "source_contract": source, "condition_id": "B_EFFORT_HISTORY",
        "sample_id": "SYNTHETIC-RUNTIME", "condition_file_sha256": "fixture",
        "history_value_sha256": contract.digest(messages),
    }
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp)
        provider = SimpleNamespace(client=SimpleNamespace(
            _client=SimpleNamespace(event_hooks={"request": []})))
        context = {"step": source["first_continuation_step"]}
        constructor = []

        def create(**kwargs):
            constructor.append(kwargs)
            return provider

        namespace = {
            "original_factory": create, "MODE": "paid",
            "CONTRACT": runtime, "SOURCE": source, "json": json,
            "validate_request": contract.validate_request,
            "preserved": SimpleNamespace(OUTPUT=output, CONTEXT=context),
        }
        factory = function("factory", namespace)
        test.assertIs(factory(model="fixture", temperature=1.0), provider)
        test.assertEqual(constructor,
                         [{"model": "fixture", "temperature": 1.0}])
        guard = provider.client._client.event_hooks["request"][0]
        body = {**source["actual_source_api_controls"], "messages": messages}
        request = SimpleNamespace(content=json.dumps(body).encode())
        with test.assertRaises(ValueError):
            guard(request)
        (output / "pre_invocation_manifest.json").write_text("{}")
        guard(request)
        context["step"] = 100
        with test.assertRaises(ValueError):
            guard(request)
    actual = {"runtime": {"fixture": True}, "mypy": {"reference": {
        "errors_hash": source["diagnostic_sha256"],
        "error_count": source["diagnostic_count"]}}}
    for gate_passes in (True, False):
        provider = SimpleNamespace(messages=copy.deepcopy(original))
        state_object = SimpleNamespace(to_dict=lambda: state)
        comparison = {"verdict": "equal_on_recorded_fields",
                      "history_equal": gate_passes, "mtimes_equal": True,
                      "external_inventory_equal": True}
        output = Path("/synthetic-output")
        checkpoint = Path("/synthetic-checkpoint")
        records = {
            output / "restored/validation.json": actual,
            checkpoint / "validation.json": actual,
            output / "restore_comparison.json": comparison,
            checkpoint / "state.json": state,
            Path("/root/history/condition.messages.json"): messages,
            Path("/root/history-allocation.json"): {"synthetic": True},
        }
        saved = {}

        def original_restore(config, source):
            raise SystemExit(0)

        namespace = {
            "Path": Path, "MODE": "restore-check", "SOURCE": source,
            "CONTRACT": runtime, "original_restore": original_restore,
            "read": lambda path: records[Path(path)],
            "sha256": lambda path: "fixture", "now": lambda: "fixture",
            "save": lambda path, value: saved.update({str(path): value}),
            "digest": contract.digest,
            "validate_history": contract.validate_history,
            "validate_original_restore": contract.validate_original_restore,
            "preserved": SimpleNamespace(
                OUTPUT=output, CONTEXT={"state": state_object,
                                        "provider": provider},
                original_command=lambda command: (0, "")),
        }
        restore = function("restore", namespace)
        if gate_passes:
            with test.assertRaises(SystemExit):
                restore({}, checkpoint)
            test.assertEqual(provider.messages, messages)
            manifest = next(iter(saved.values()))
            test.assertEqual(manifest["remaining_decisions"],
                             source["remaining_decisions"])
        else:
            with test.assertRaises(ValueError):
                restore({}, checkpoint)
            test.assertEqual(provider.messages, original)
            test.assertEqual(saved, {})
