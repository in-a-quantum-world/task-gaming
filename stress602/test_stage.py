"""Offline separation, count, configuration, and exact transcript checks."""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_stage
from transcript import fenced, visible_reasoning


class StageTest(unittest.TestCase):

    def test_only_source_variant_changes(self):
        original = json.loads((run_stage.ROOT / "SOURCE_PILOT_CONFIG.yaml")
                              .read_text())
        actual = json.loads((run_stage.ROOT / "STRESS_602_CONFIG.yaml")
                            .read_text())
        self.assertEqual(actual["task"]["target_errors"], 602)
        actual["task"]["target_errors"] = 258
        self.assertEqual(actual, original)

    def test_source_guards_reject_extra_or_changed_runs(self):
        config = run_stage.expected_config()
        run_stage.validate_request("source", 1, config, None)
        for count in (0, 2, 3):
            with self.assertRaises(ValueError):
                run_stage.validate_request("source", count, config, None)
        changed = copy.deepcopy(config)
        changed["agent"]["provider_preferences"]["allow_fallbacks"] = True
        with self.assertRaises(ValueError):
            run_stage.validate_request("source", 1, changed, None)
        with self.assertRaises(ValueError):
            run_stage.validate_request("source", 1, config, Path("checkpoint"))

    def test_independent_cap_survives_new_output_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy = root / "integrated-pilot-source-slot.json"
            legacy.write_text('{"run_id":"completed-258"}\n')
            before = legacy.read_bytes()
            with mock.patch.object(run_stage, "common_git", return_value=root):
                run_stage.allocate("source", {}, root / "raw1")
                with self.assertRaises(FileExistsError):
                    run_stage.allocate("source", {}, root / "raw2")
            self.assertEqual(legacy.read_bytes(), before)
            self.assertTrue((root / run_stage.SLOT).exists())

    def test_visible_fields_and_delimiters_preserve_exact_text(self):
        text = 'Consider this:\n```bash\nprintf "x"\n```\n  trailing  '
        message = {"reasoning": text, "reasoning_details": [
            {"type": "reasoning.text", "text": text}]}
        self.assertEqual(visible_reasoning(message), [
            ("reasoning", text), ("reasoning_details[0].text", text)])
        self.assertIn(text, fenced(text, []))
        self.assertTrue(fenced(text, []).startswith("````text\n"))
        with self.assertRaises(ValueError):
            fenced("secret-value", ["secret-value"])

    def test_602_actual_fresh_resume_wire_settings(self):
        sys.path.insert(0, str(run_stage.ROOT / "pilot/tests"))
        from test_sampling import SamplingTest
        original_read = Path.read_text
        config_path = run_stage.ROOT / "pilot/configs/first_pilot.json"

        def read_config(path, *args, **kwargs):
            if path == config_path:
                return json.dumps(run_stage.expected_config())
            return original_read(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", read_config):
            SamplingTest("test_actual_openrouter_fresh_resume_wire_settings") \
                .test_actual_openrouter_fresh_resume_wire_settings()


if __name__ == "__main__":
    unittest.main()
