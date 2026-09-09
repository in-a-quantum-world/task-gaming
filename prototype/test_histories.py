"""Verify the artifact controls that protect history-only comparisons."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from histories import build, final_exchange, verify_bundle


class HistoryArtifactTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        messages = [
            {"role": "system", "content": "Task constraint."},
            {"role": "user", "content": "Repair the errors."},
            {"role": "assistant", "tool_calls": [{
                "id": "call-1", "type": "function", "function": {
                    "name": "execute_command", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "call-1",
             "content": "Found 258 errors."},
        ]
        history = self.source / "messages.json"
        history.write_text(json.dumps(messages))
        (self.source / "state.json").write_text('{"step": 4}')
        (self.source / "workspace.tar.gz").write_bytes(b"opaque fixture")
        self.facts = self.root / "facts.json"
        self.facts.write_text(json.dumps({
            "synthetic": True, "source_messages_sha256": hashlib.sha256(
                history.read_bytes()).hexdigest(),
            "items": [{
                "id": "errors", "text": "There are 258 errors.",
                "present_in_A": True, "evidence_message_indices": [3],
                "B_FAILURE_FACT": True, "C_STATE_ONLY": True,
                "why": "Retain current errors.",
                "possible_confound": "Changes emphasis.",
            }], "omissions": [],
        }))

    def test_history_changes_preserve_workspace_and_observation(self):
        destination = self.root / "prepared"
        original = (self.source / "messages.json").read_bytes()
        build(self.source, self.facts, destination)
        self.assertEqual(original, (destination / "A_FULL" /
                                    "messages.json").read_bytes())
        self.assertEqual(original, (self.source / "messages.json").read_bytes())
        for condition in ("A_FULL", "B_FAILURE_FACT", "C_STATE_ONLY"):
            variant = destination / condition
            verify_bundle(variant)
            final = final_exchange(json.loads(
                (variant / "messages.json").read_text()))
            self.assertEqual(final, final_exchange(json.loads(original)))

    def test_altered_workspace_is_rejected(self):
        destination = self.root / "prepared"
        build(self.source, self.facts, destination)
        variant = destination / "B_FAILURE_FACT"
        (variant / "state.json").write_text('{"step": 0}')
        with self.assertRaisesRegex(ValueError, "artifacts changed"):
            verify_bundle(variant)

    def test_altered_history_is_rejected(self):
        destination = self.root / "prepared"
        build(self.source, self.facts, destination)
        variant = destination / "C_STATE_ONLY"
        (variant / "messages.json").write_text("[]")
        with self.assertRaisesRegex(ValueError, "history changed"):
            verify_bundle(variant)

    def test_missing_tool_call_and_missing_evidence_are_rejected(self):
        with self.assertRaises(ValueError):
            final_exchange([{"role": "user", "content": "Observation"}])
        facts = json.loads(self.facts.read_text())
        facts["items"][0]["evidence_message_indices"] = []
        self.facts.write_text(json.dumps(facts))
        with self.assertRaisesRegex(ValueError, "evidence"):
            build(self.source, self.facts, self.root / "prepared")


if __name__ == "__main__":
    unittest.main()
