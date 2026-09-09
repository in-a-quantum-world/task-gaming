"""Offline tests for false-equivalence failure modes."""

import copy
import os
from pathlib import Path
import tempfile
import unittest

import validate_state_equivalence as validator


def record() -> dict:
    """Return a complete synthetic record for comparator tests."""
    mypy = {
        "valid": True, "error_count": 258, "returncode": 1,
        "config_sha256": "config", "errors_hash": "errors",
    }
    return {
        "version": 1, "workspace_root": "/agent", "files": {},
        "workspace_hash": validator.digest({}), "git": {"head": "one"},
        "extra_roots": {}, "config_hash": "config", "state_hash": "state",
        "checkpoint_step": 5, "max_steps": 30, "steps_remaining": 24,
        "system_prompt_hash": "system", "user_prompt_hash": "user",
        "latest_observation_hash": "observation", "latest_call_hash": "call",
        "history_hash": "history", "history_message_roles": [],
        "mtimes_ns": {}, "mypy": {"active": mypy, "reference": mypy},
        "runtime": {
            "model": "mock", "provider": "mock", "request_kwargs": {},
            "tools": [], "agent_cwd": "/agent", "agent_environment": {},
            "image_id": "image", "command_timeout_seconds": 30,
        },
        "mypy_version": "1.20.2", "issues": [],
    }


class EquivalenceTests(unittest.TestCase):
    def test_identical_complete_records_match(self):
        result = validator.compare(record(), record())
        self.assertEqual(result["verdict"], "equal_on_recorded_fields")

    def test_history_text_can_differ_without_a_task_state_difference(self):
        right = record()
        right["history_hash"] = "rewritten-history"
        result = validator.compare(record(), right)
        self.assertEqual(result["verdict"], "equal_on_recorded_fields")
        self.assertFalse(result["history_equal"])

    def test_task_invariants_cannot_differ(self):
        for key in ["config_hash", "state_hash", "steps_remaining", "git",
                    "system_prompt_hash", "user_prompt_hash",
                    "latest_observation_hash", "latest_call_hash", "runtime"]:
            with self.subTest(key=key):
                right = record()
                right[key] = None
                self.assertEqual(
                    validator.compare(record(), right)["verdict"], "different",
                )

    def test_two_failed_mypy_checks_do_not_match(self):
        left = record()
        left["mypy"]["active"]["valid"] = False
        result = validator.compare(left, copy.deepcopy(left))
        self.assertEqual(result["verdict"], "inconclusive")

    def test_missing_runtime_is_inconclusive(self):
        left = record()
        left["runtime"] = None
        result = validator.compare(left, copy.deepcopy(left))
        self.assertEqual(result["verdict"], "inconclusive")

    def test_null_runtime_fields_are_inconclusive(self):
        left = record()
        left["runtime"]["image_id"] = None
        result = validator.compare(left, copy.deepcopy(left))
        self.assertEqual(result["verdict"], "inconclusive")

    def test_inconsistent_budget_is_inconclusive(self):
        left = record()
        left["steps_remaining"] = 30
        result = validator.compare(left, copy.deepcopy(left))
        self.assertEqual(result["verdict"], "inconclusive")

    def test_inconsistent_file_hash_cannot_match(self):
        left = record()
        left["files"]["hidden-generated-file"] = {"kind": "file"}
        result = validator.compare(left, copy.deepcopy(left))
        self.assertEqual(result["verdict"], "inconclusive")

    def test_hook_permission_change_is_a_difference(self):
        left, right = record(), record()
        left["files"] = {".git/hooks/pre-commit": {"mode": 0o755}}
        right["files"] = {".git/hooks/pre-commit": {"mode": 0o644}}
        for item in [left, right]:
            item["workspace_hash"] = validator.digest(item["files"])
        result = validator.compare(left, right)
        self.assertEqual(result["verdict"], "different")
        self.assertIn(".git/hooks/pre-commit", result["changed_files"])

    def test_same_size_same_mtime_edit_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.py"
            source.write_text("value = 1\n")
            before_stat = source.stat()
            before, _, _ = validator.inventory(root)
            source.write_text("value = 2\n")
            os.utime(source, ns=(before_stat.st_atime_ns,
                                 before_stat.st_mtime_ns))
            after, _, _ = validator.inventory(root)
            self.assertNotEqual(
                validator.digest(before), validator.digest(after),
            )

    def test_directory_symlink_is_recorded_without_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "cycle").symlink_to(root, target_is_directory=True)
            entries, _, issues = validator.inventory(root)
            self.assertEqual(entries["cycle"]["kind"], "symlink")
            self.assertEqual(set(entries), {".", "cycle"})
            self.assertEqual(issues, [])

    def test_orphan_tool_result_is_rejected(self):
        messages = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
            {"role": "tool", "tool_call_id": "missing", "content": "error"},
        ]
        self.assertTrue(validator.validate_messages(messages))

    def test_valid_tool_pair_is_accepted(self):
        messages = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
            {"role": "assistant", "tool_calls": [{"id": "one"}]},
            {"role": "tool", "tool_call_id": "one", "content": "error"},
        ]
        self.assertEqual(validator.validate_messages(messages), [])


if __name__ == "__main__":
    unittest.main()
