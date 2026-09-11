"""Offline contracts, allocation, and exact remaining-budget regressions."""

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "history"))
from contract import (CONDITION, full_restore_check, read, validate_history,
                      validate_request, validate_state)

spec = importlib.util.spec_from_file_location("history_runner",
                                               ROOT / "history/run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
C = runner.CONTRACT
MESSAGES = read(Path(C["checkpoint"]) / "messages.json")


class HistoryTest(unittest.TestCase):

    def test_original_history_and_every_mutation_rejected(self):
        validate_history(MESSAGES, C)
        for index in (0, 1, 10, len(MESSAGES) - 2, len(MESSAGES) - 1):
            changed = copy.deepcopy(MESSAGES)
            changed[index]["content"] = "changed"
            with self.assertRaises(ValueError):
                validate_history(changed, C)
        with self.assertRaises(ValueError):
            validate_history(MESSAGES + [{"role": "user", "content": "go"}], C)
        with self.assertRaises(ValueError):
            validate_history(MESSAGES[:2] + MESSAGES[-2:], C)

    def test_all_wire_controls_and_first_history_are_exact(self):
        body = {**copy.deepcopy(C["actual_source_api_controls"]),
                "messages": copy.deepcopy(MESSAGES)}
        validate_request(body, C, first=True)
        for key in C["actual_source_api_controls"]:
            changed = copy.deepcopy(body)
            changed[key] = None
            with self.assertRaises(ValueError):
                validate_request(changed, C, first=False)
        body["seed"] = 0
        with self.assertRaises(ValueError):
            validate_request(body, C, first=True)

    def test_original_state_and_failure_gates(self):
        source = read(Path(C["checkpoint"]) / "validation.json")
        state = read(Path(C["checkpoint"]) / "state.json")
        comparison = {"verdict": "equal_on_recorded_fields",
                      "history_equal": True, "mtimes_equal": True,
                      "external_inventory_equal": True}
        full_restore_check(source, source, comparison, MESSAGES, state, C)
        for key in ("history_equal", "mtimes_equal",
                    "external_inventory_equal"):
            changed = {**comparison, key: False}
            with self.assertRaises(ValueError):
                full_restore_check(source, source, changed, MESSAGES, state, C)
        for changed in ({**state, "step": 43},
                        {**state, "task_completed": True}):
            with self.assertRaises(ValueError):
                validate_state(changed, C)

    def test_one_dedicated_slot_no_other_condition(self):
        runner.validate_condition(CONDITION, 1)
        for condition, count in ((CONDITION, 2), (CONDITION, 0),
                                 ("A_COMPACT", 1), ("108_STEP32", 1)):
            with self.assertRaises(ValueError):
                runner.validate_condition(condition, count)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old = root / "integrated-pilot-source-slot.json"
            old.write_text("unchanged consumed source")
            with mock.patch.object(runner, "common_git", return_value=root):
                runner.allocate_paid({}, root / "raw1")
                with self.assertRaises(FileExistsError):
                    runner.allocate_paid({}, root / "raw2")
            self.assertEqual(old.read_text(), "unchanged consumed source")

    def test_upstream_continuation_runs_steps_43_through_99_only(self):
        env = ROOT / "upstream/agent-interp-envs/environments/precommit_hook"
        sys.path.insert(0, str(env))
        spec = importlib.util.spec_from_file_location("budget_agent",
                                                       env / "agent.py")
        agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent)
        config = read(ROOT / "SOURCE_PILOT_CONFIG.yaml")
        state = mock.Mock(step=42, task_completed=False)
        visited = []
        with mock.patch.object(agent, "load_config", return_value=config), \
             mock.patch.object(agent, "Path") as path, \
             mock.patch.object(agent, "restore",
                               return_value=(state, mock.Mock())), \
             mock.patch.object(agent, "run_step", side_effect=lambda *args:
                               visited.append(state.step) or False), \
             mock.patch.object(agent, "dump"), \
             mock.patch.object(agent, "print_step_header"), \
             mock.patch.object(agent, "print_final_results"):
            path.return_value.exists.return_value = True
            agent.main()
        self.assertEqual(visited, list(range(43, 100)))
        self.assertEqual(len(visited), 57)
        self.assertEqual(state.step, 100)


if __name__ == "__main__":
    unittest.main()
