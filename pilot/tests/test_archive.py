"""Adversarial archive and source-reference regression tests."""

import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workspace import (
    archive_workspace, compare_external, restore_archive, validate_members,
)


class ArchiveTest(unittest.TestCase):

    def test_two_generations_preserve_original_and_untouched_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = root / "agent"
            agent.mkdir()
            (agent / ".git").mkdir()
            (agent / ".git/HEAD").write_text("original HEAD")
            (agent / ".mypy_cache").mkdir()
            target = agent / ".mypy_cache/cache"
            target.write_text("aaaa")
            target.chmod(0o640)
            os.utime(target, ns=(1234567890123456789,) * 2)
            (agent / "link").symlink_to(".mypy_cache/cache")
            original = root / "original"
            original.mkdir()
            archive_workspace(original, agent)
            target.write_text("bbbb")
            restore_archive(original, agent)
            self.assertEqual(target.read_text(), "aaaa")
            second = root / "second"
            second.mkdir()
            archive_workspace(second, agent)
            target.unlink()
            restore_archive(second, agent)
            inventory_path = original / "original_inventory.json"
            left = json.loads(inventory_path.read_text())
            right = json.loads((second / "original_inventory.json").read_text())
            self.assertEqual(left["files"], right["files"])
            self.assertEqual(left["mtimes_ns"], right["mtimes_ns"])

    def test_reject_external_and_symlink_parent(self):
        for name, link in (("../escape", None),
                           ("agent/link", "../../escape")):
            member = tarfile.TarInfo(name)
            if link:
                member.type = tarfile.SYMTYPE
                member.linkname = link
            with self.assertRaises(ValueError):
                validate_members([member])
        member = tarfile.TarInfo("agent/link")
        member.type = tarfile.SYMTYPE
        member.linkname = "directory"
        with self.assertRaises(ValueError):
            validate_members([member, tarfile.TarInfo("agent/link/child")])

    def test_external_gate_distinguishes_live_and_dead_processes(self):
        original = {"roots": {}, "fixed_files": {}, "packages": [],
                    "excluded_tmp": [], "live_agent_processes": [],
                    "agent_process_inventory": [{"pid": 3, "state": "Z"}]}
        restored = {**original, "agent_process_inventory": []}
        self.assertTrue(compare_external(original, restored))
        restored["live_agent_processes"] = [{"pid": 3, "state": "S"}]
        self.assertFalse(compare_external(original, restored))
        restored["live_agent_processes"] = []
        restored["roots"] = {"/home/dev": {"changed": True}}
        self.assertFalse(compare_external(original, restored))


if __name__ == "__main__":
    unittest.main()
