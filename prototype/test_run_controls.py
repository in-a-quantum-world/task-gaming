"""Check that live preflight cannot bypass credentials or pilot caps."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import run


class RunControlTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.results = self.root / "prototype_results"
        (self.results / "metadata").mkdir(parents=True)
        (self.results / "raw").mkdir()
        self.config = {"task": {"target_errors": 258}, "agent": {
            "provider": "fireworks", "model": "offline-test-model",
            "max_steps": 100}}
        self.config_path = self.root / "config.json"
        self.config_path.write_text(json.dumps(self.config))
        for name, value in (("ROOT", self.root), ("RESULTS", self.results)):
            patch = mock.patch.object(run, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def execute(self):
        with mock.patch("sys.argv", ["run.py", "--config",
                                    str(self.config_path), "--condition",
                                    "BASELINE"]):
            run.main()

    def add_record(self, number, fingerprint=None):
        directory = self.results / "raw" / f"run-{number}"
        directory.mkdir()
        (directory / "run.json").write_text(json.dumps({
            "condition": "BASELINE", "image_id": "sha256:offline",
            "config_sha256": fingerprint or run.fingerprint(self.config),
        }))

    def test_missing_key_starts_no_container(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with mock.patch.object(run.subprocess, "check_output") as check:
                with self.assertRaisesRegex(ValueError, "FIREWORKS_API_KEY"):
                    self.execute()
                check.assert_not_called()
        self.assertFalse(list((self.results / "raw").iterdir()))

    def test_fourth_baseline_is_rejected(self):
        for number in range(3):
            self.add_record(number)
        with mock.patch.dict("os.environ", {"FIREWORKS_API_KEY": "offline"}):
            with mock.patch.object(run.subprocess, "check_output",
                                   return_value="sha256:offline"):
                with mock.patch.object(run.subprocess, "run") as start:
                    with self.assertRaisesRegex(ValueError, "cap reached"):
                        self.execute()
                    start.assert_not_called()
        self.assertEqual(len(list((self.results / "raw").iterdir())), 3)

    def test_changed_live_config_is_rejected(self):
        self.add_record(0, fingerprint="other-config")
        with mock.patch.dict("os.environ", {"FIREWORKS_API_KEY": "offline"}):
            with mock.patch.object(run.subprocess, "check_output",
                                   return_value="sha256:offline"):
                with self.assertRaisesRegex(ValueError, "config/image"):
                    self.execute()


if __name__ == "__main__":
    unittest.main()
