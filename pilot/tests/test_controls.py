"""Cap, retention, and request guards without model calls."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run
from common import seal, sha256


class ControlsTest(unittest.TestCase):

    def setUp(self):
        self.config = json.loads((run.ROOT / "pilot/configs/first_pilot.json")
                                 .read_text())

    def test_source_count_and_provider_are_fixed(self):
        for count in (0, 2, 3):
            with self.assertRaises(ValueError):
                run.validate_request("source", count, self.config, None)
        changed = json.loads(json.dumps(self.config))
        changed["agent"]["model"] = "deepseek"
        with self.assertRaises(ValueError):
            run.validate_request("source", 1, changed, None)
        run.validate_request("source", 1, self.config, None)
        for field, value in (("only", ["google-vertex"]),
                             ("allow_fallbacks", True)):
            changed = json.loads(json.dumps(self.config))
            changed["agent"]["provider_preferences"][field] = value
            with self.assertRaises(ValueError):
                run.validate_request("source", 1, changed, None)

    def test_source_slot_survives_failure_and_output_location_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with mock.patch.object(run, "output", return_value=str(root)):
                run.allocate("source", {}, root / "raw1")
                with self.assertRaises(FileExistsError):
                    run.allocate("source", {}, root / "raw2")

    def test_missing_credentials_make_zero_requests(self):
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.dict(run.os.environ, {}, clear=True), \
                 mock.patch.object(run.subprocess, "run") as subprocess_run:
                self.assertFalse(run.preflight(self.config, Path(temp)))
                subprocess_run.assert_not_called()

    def test_seal_does_not_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outside = root / "outside"
            outside.write_text("private")
            mode = outside.stat().st_mode
            raw = root / "raw"
            raw.mkdir()
            (raw / "link").symlink_to(outside)
            (raw / "artifact").write_text("evidence")
            seal(raw)
            self.assertEqual(outside.stat().st_mode, mode)
            hashes = json.loads((raw / "artifact_sha256.json").read_text())
            self.assertNotIn("link", hashes)
            self.assertEqual(hashes["artifact"], sha256(raw / "artifact"))

    def test_two_fixtures_launch_exactly_two_even_when_first_fails(self):
        config = run.ROOT / "pilot/configs/archive_fixture.json"
        argv = ["run.py", "fixture", "--config", str(config),
                "--image", "offline-test", "--count", "2"]
        with mock.patch.object(sys, "argv", argv), \
             mock.patch.object(run, "output", return_value="image"), \
             mock.patch.object(run, "launch", side_effect=[
                 (Path("failed-run"), 1), (Path("second-run"), 0)]) as launch:
            with self.assertRaises(SystemExit) as raised:
                run.main()
            self.assertEqual(raised.exception.code, 1)
            self.assertEqual(launch.call_count, 2)


if __name__ == "__main__":
    unittest.main()
