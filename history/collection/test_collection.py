"""Synthetic contract, schedule, ledger, and quarantine regressions."""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import blind
import blind_inputs
import contract
import freeze
import gates
import ledger
import run as collection_run
import schedule


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2))


def fixture(root, checkpoint="258_step42"):
    filename, config, step, budget = contract.SOURCE_FILES[checkpoint]
    source_path = root / "synthetic-source" / checkpoint
    messages = [
        {"role": "system", "content": "SYNTHETIC SYSTEM"},
        {"role": "user", "content": "SYNTHETIC TASK"},
        {"role": "assistant", "content": None,
         "reasoning": "SYNTHETIC VISIBLE REASONING",
         "reasoning_details": [{"text": "EXACT FIXTURE FIELD"}],
         "tool_calls": [{"id": "fixture-call", "type": "function",
                         "function": {"name": "execute_command",
                                      "arguments":
                                      '{"command":"mypy src/"}'}}]},
        {"role": "tool", "tool_call_id": "fixture-call",
         "content": "SYNTHETIC ERRORS"},
    ]
    state = {"step": step, "task_completed": False}
    write(source_path / "messages.json", messages)
    write(source_path / "state.json", state)
    (source_path / "workspace.tar.gz").write_bytes(b"synthetic archive bytes")
    write(root / config, {"fixture": checkpoint})
    source = {
        "checkpoint": str(source_path), "checkpoint_step": step,
        "first_continuation_step": step + 1, "remaining_decisions": budget,
        "max_steps": 100, "diagnostic_count": 9 if step == 42 else 6,
        "diagnostic_sha256": "e" * 64, "image_id": "synthetic-image",
        "config_sha256": contract.sha(root / config),
        "complete_history_value_sha256": contract.digest(messages),
        "final_assistant_tool_pair": messages[-2:],
        "actual_source_api_controls": {
            "model": "SYNTHETIC-NO-PROVIDER", "temperature": 1.0,
            "top_p": 1.0, "max_tokens": 16384,
            "reasoning": {"enabled": True, "exclude": False},
            "provider": {"only": ["novita/bf16"],
                         "allow_fallbacks": False, "require_parameters": True},
            "tools": [{"type": "function", "function": {
                "name": "execute_command"}}],
        },
        "checkpoint_sha256": {name: contract.sha(source_path / name)
                              for name in ("messages.json", "state.json",
                                           "workspace.tar.gz")},
    }
    for index, role in enumerate(("system", "user")):
        source[f"{role}_prompt_sha256"] = hashlib.sha256(
            messages[index]["content"].encode()).hexdigest()
    write(root / filename, source)
    return source, messages, state


class ScheduleTests(unittest.TestCase):

    def setUp(self):
        self.hashes = {"258_step42": "a" * 64, "108_step32": "b" * 64}

    def test_reproducible_exact_counts_and_no_reallocation(self):
        draft = schedule.generate(self.hashes)
        self.assertEqual(draft, schedule.generate(self.hashes))
        schedule.validate(draft, self.hashes)
        rows = draft["samples"]
        self.assertEqual(len(rows), 32)
        self.assertEqual(len({row["sample_id"] for row in rows}), 32)
        self.assertEqual(rows[0]["sample_id"], schedule.EXISTING)
        self.assertFalse(rows[0]["randomized"])
        self.assertEqual([row["order"] for row in rows], list(range(32)))
        counts = Counter((row["checkpoint"], row["condition_id"])
                         for row in rows)
        for checkpoint, conditions in schedule.COUNTS.items():
            for condition, expected in conditions.items():
                self.assertEqual(counts[checkpoint, condition], expected)

    def test_each_block_is_balanced_within_checkpoint(self):
        rows = schedule.generate(self.hashes)["samples"][1:]
        for block in range(1, 5):
            for checkpoint, expected in (("258_step42", 2), ("108_step32", 1)):
                counts = Counter(row["condition_id"] for row in rows
                                 if row["checkpoint"] == checkpoint
                                 and row["block"] == block)
                self.assertEqual(counts["B_EFFORT_HISTORY"], expected)
                self.assertEqual(counts["C_CURRENT_STATE"], expected)

    def test_order_or_design_change_rejected(self):
        draft = schedule.generate(self.hashes)
        for key, value in (("order", 100), ("replicate", 9),
                           ("config_sha256", "wrong")):
            changed = copy.deepcopy(draft)
            changed["samples"][1][key] = value
            with self.assertRaises(ValueError):
                schedule.validate(changed, self.hashes)
        draft["samples"].append(draft["samples"][-1])
        with self.assertRaises(ValueError):
            schedule.validate(draft, self.hashes)


class ContractTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source, self.messages, self.state = fixture(self.root)

    def test_exact_pair_and_reasoning_fields_unchanged(self):
        original_hash = contract.digest(self.messages)
        contract.validate_history(self.messages, self.source, "A_FULL",
                                  original_hash)
        for index, field in ((0, "content"), (1, "content"),
                             (2, "reasoning"), (2, "reasoning_details"),
                             (3, "content")):
            changed = copy.deepcopy(self.messages)
            changed[index][field] = "CHANGED"
            with self.assertRaises(ValueError):
                contract.validate_history(changed, self.source, "A_FULL",
                                          original_hash)

    def test_broken_roles_and_native_pairs_rejected(self):
        cases = [self.messages[:-1], self.messages + [{"role": "user"}],
                 self.messages[:2] + self.messages[-1:]]
        changed = copy.deepcopy(self.messages)
        changed[-1]["tool_call_id"] = "wrong"
        cases.append(changed)
        for messages in cases:
            with self.assertRaises((ValueError, KeyError)):
                contract.validate_roles(messages)

    def test_both_budgets_and_every_request_control(self):
        for checkpoint in contract.SOURCE_FILES:
            source, messages, state = fixture(self.root, checkpoint)
            contract.validate_state(state, source)
            from runtime_fixture_checks import exercise
            exercise(self, source, messages, state)
            runtime = {"source_contract": source, "condition_id": "A_FULL",
                       "history_value_sha256": contract.digest(messages)}
            body = {**source["actual_source_api_controls"],
                    "messages": messages}
            for step in range(source["first_continuation_step"], 100):
                contract.validate_request(body, runtime, True, step)
            for step in (source["checkpoint_step"], 100, 101):
                with self.assertRaises(ValueError):
                    contract.validate_request(body, runtime, True, step)
            for key in source["actual_source_api_controls"]:
                changed = {**body, key: None}
                with self.assertRaises(ValueError):
                    contract.validate_request(changed, runtime, False, 99)
            with self.assertRaises(ValueError):
                contract.validate_request({**body, "seed": 1}, runtime,
                                          False, 99)

    def test_original_restore_failures_prevent_substitution(self):
        actual = {"mypy": {"reference": {
            "errors_hash": self.source["diagnostic_sha256"], "error_count": 9}},
                  "runtime": {"fixture": True}}
        comparison = {"verdict": "equal_on_recorded_fields",
                      "history_equal": True, "mtimes_equal": True,
                      "external_inventory_equal": True}
        contract.validate_original_restore(actual, actual, comparison,
                                           self.messages, self.state,
                                           self.source)
        for key in ("history_equal", "mtimes_equal",
                    "external_inventory_equal"):
            with self.assertRaises(ValueError):
                contract.validate_original_restore(
                    actual, actual, {**comparison, key: False}, self.messages,
                    self.state, self.source)

    def test_reviewed_bytes_staged_without_rewrite_then_mutation_rejected(self):
        sources = {"258_step42": self.source}
        sources["108_step32"], _, _ = fixture(self.root, "108_step32")
        draft = schedule.generate({key: value["config_sha256"]
                                   for key, value in sources.items()})
        write(self.root / "draft.json", draft)
        approvals = {}
        for checkpoint, conditions in schedule.COUNTS.items():
            source = sources[checkpoint]
            original_path = Path(source["checkpoint"]) / "messages.json"
            original = contract.read(original_path)
            for condition in conditions:
                directory = self.root / "exports" / checkpoint / condition
                messages = copy.deepcopy(original)
                if condition != "A_FULL":
                    messages.insert(2, {"role": "assistant",
                                        "content": "SYNTHETIC UNIT SUMMARY"})
                write(directory / "messages.json", messages)
                payload_hash = contract.sha(directory / "messages.json")
                metadata = {
                    "condition": condition, "status": "reviewed_dry_run",
                    "text_reviewed": True, "payload_sha256": payload_hash,
                    "source_checkpoint": {
                        "step": source["checkpoint_step"],
                        "remaining_decision_budget":
                        source["remaining_decisions"],
                        "raw_sha256": source["checkpoint_sha256"]},
                }
                write(directory / "manifest.json", metadata)
                review = {
                    "status": "approved", "reviewer": "SYNTHETIC REVIEWER",
                    "reviewed_at_utc": "SYNTHETIC TIME",
                    "final_text_and_roles_approved": True,
                    "checkpoint": checkpoint, "condition_id": condition,
                    "payload_sha256": payload_hash,
                    "manifest_sha256":
                    contract.sha(directory / "manifest.json"),
                }
                write(directory / "review.json", review)
                approvals[f"{checkpoint}/{condition}"] = {
                    "condition_file": str(directory / "messages.json"),
                    "condition_manifest": str(directory / "manifest.json"),
                    "review_file": str(directory / "review.json"),
                    "condition_file_sha256": payload_hash,
                    "condition_manifest_sha256":
                    review["manifest_sha256"],
                    "review_sha256": contract.sha(directory / "review.json"),
                }
        write(self.root / "approvals.json", approvals)
        output = self.root / "candidate"
        freeze.stage_inputs(self.root, self.root / "draft.json",
                            self.root / "approvals.json", output)
        candidate = contract.read(output / "schedule.candidate.json")
        self.assertFalse(candidate["execution_authorized"])
        from frozen_fixture_checks import exercise
        exercise(self, self.root, candidate, sources, write)
        row = candidate["samples"][1]
        source = sources[row["checkpoint"]]
        payload = Path(row["condition_file"])
        before = payload.read_bytes()
        paths = [Path(row[field]) for field in
                 ("condition_file", "condition_manifest", "review_file")]
        contract.load_condition(*paths, row, source)
        self.assertEqual(before, payload.read_bytes())
        payload.chmod(0o600)
        payload.write_bytes(before + b" ")
        with self.assertRaises(ValueError):
            contract.load_condition(*paths, row, source)


class LedgerAndQuarantineTests(unittest.TestCase):

    def test_duplicate_concurrent_allocation_has_one_winner(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            draft = schedule.generate({"258_step42": "a", "108_step32": "b"})
            row = draft["samples"][1]

            def allocate(index):
                try:
                    ledger.allocate(root / "git", root / f"raw{index}", row,
                                    draft, "frozen-fixture")
                    return "allocated"
                except FileExistsError:
                    return "blocked"

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(allocate, (1, 2)))
            self.assertCountEqual(results, ["allocated", "blocked"])
            with self.assertRaises(PermissionError):
                ledger.allocate(root / "git", root / "raw3",
                                draft["samples"][0], draft, "frozen-fixture")
            with self.assertRaises(ValueError):
                ledger.allocate(root / "git", root / "raw4",
                                draft["samples"][2], draft, "frozen-fixture")

    def test_all_execution_and_release_locks_precede_file_access(self):
        with mock.patch.object(Path, "read_text", side_effect=AssertionError):
            for mode in ("paid", "restore-check", "offline-wire"):
                with self.assertRaises(PermissionError):
                    collection_run.launch(mode, Path("do-not-open"), "sample")
            with self.assertRaises(PermissionError):
                blind.export_packets(Path("do-not-open"), Path("no-output"),
                                     {}, "hash", b"fixture-key")
            with self.assertRaises(PermissionError):
                blind_inputs.normalize_run(Path("do-not-open"), {}, {}, "hash")
            with self.assertRaises(PermissionError):
                gates.record_offline_gate(None, None, None, None, "paid", None)

    def test_packet_strips_labels_and_reasoning_but_keeps_native_evidence(self):
        step = {
            "condition": "SECRET CONDITION", "checkpoint": "SECRET CHECKPOINT",
            "native_message": {
                "role": "assistant", "reasoning": "SECRET REASONING",
                "reasoning_details": [{"text": "SECRET DETAILS"}],
                "content": "SECRET ASSISTANT TEXT",
                "tool_calls": [{"id": "SECRET ID", "function": {
                    "name": "execute_command",
                    "arguments": '{"command":"git status"}'}}]},
            "executions": [{"command": "git status", "returncode": 0,
                            "output": "EXACT TOOL OUTPUT"}],
            "verified_state": {"mypy": {}, "git": {},
                               "workspace_changes": [],
                               "verification_status": "fixture"},
        }
        packet = blind.primary_packet([step], "blind-fixture")
        body = json.dumps(packet)
        self.assertNotIn("SECRET", body)
        self.assertIn("git status", body)
        self.assertIn("EXACT TOOL OUTPUT", body)
        self.assertEqual(packet["primary_label"], "UNADJUDICATED")
        self.assertEqual(packet["events"][0]["relative_decision"], 1)

    def test_draft_freeze_cannot_authorize_even_with_false_execution_flag(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "freeze.json"
            write(path, {"status": "DRAFT",
                         "researcher_authorized_collection": False})
            with self.assertRaises(PermissionError):
                freeze.verify_frozen(Path(temp), path, "future-sample")


if __name__ == "__main__":
    unittest.main(verbosity=2)
