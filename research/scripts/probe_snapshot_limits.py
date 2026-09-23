#!/usr/bin/env python3
"""Reproduce upstream snapshot limits without model calls."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from agent_interp_envs.checkpoint import ManifestSnapshot


def init_repo(workspace: Path, date: str) -> str:
    """Create the same worktree with a controlled initial commit date."""
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir()
    (workspace / "source.py").write_text("value = 1\n")
    git_env = dict(os.environ)
    git_env.update({
        "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date,
        "GIT_AUTHOR_NAME": "Probe", "GIT_COMMITTER_NAME": "Probe",
        "GIT_AUTHOR_EMAIL": "probe@example.test",
        "GIT_COMMITTER_EMAIL": "probe@example.test",
    })
    for args in [("init", "-q"), ("add", "."), ("commit", "-qm", "base")]:
        subprocess.run(
            ["git", *args], cwd=workspace, env=git_env, check=True,
            capture_output=True,
        )
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=workspace, text=True,
    ).strip()


def probe(root: Path) -> dict:
    """Return observations from fresh and repeated restore paths."""
    workspace = root / "workspace"
    first = root / "first"
    second = root / "second"
    original_head = init_repo(workspace, "2026-01-01T00:00:00Z")
    def make_snapshot():
        return ManifestSnapshot(
            roots=[workspace], baseline_roots=[workspace],
            blob_cache=root / "blobs",
        )

    original = make_snapshot()
    original.prime()
    (workspace / "precommit-probe.txt").write_text("checkpoint content\n")
    original.save(first)
    init_repo(workspace, "2026-01-02T00:00:00Z")
    restored = make_snapshot()
    restored.restore(first)
    resumed_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=workspace, text=True,
    ).strip()
    first_content_restored = (workspace / "precommit-probe.txt").exists()
    restored.save(second)
    second_manifest = json.loads((second / "fs/manifest.json").read_text())
    init_repo(workspace, "2026-01-03T00:00:00Z")
    make_snapshot().restore(second)
    second_content_restored = (workspace / "precommit-probe.txt").exists()
    init_repo(workspace, "2026-01-01T00:00:00Z")
    same_stat = make_snapshot()
    same_stat.prime()
    source = workspace / "source.py"
    source_stat = source.stat()
    source.write_text("value = 2\n")
    os.utime(source, ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns))
    same_stat.save(root / "same-stat")
    stat_manifest = json.loads(
        (root / "same-stat/fs/manifest.json").read_text()
    )
    return {
        "original_head": original_head, "resumed_head": resumed_head,
        "unchanged_git_head_preserved": original_head == resumed_head,
        "first_restore_added_file_preserved": first_content_restored,
        "resume_of_resume_added_file_preserved": second_content_restored,
        "second_manifest_entry_count": len(second_manifest["entries"]),
        "same_size_mtime_edit_captured": any(
            entry["path"] == str(source)
            for entry in stat_manifest["entries"]
        ),
        "model_calls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="snapshot-probe-") as temp:
        result = probe(Path(temp))
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
