"""Full workspace archives and independent source-state references."""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import posixpath
import shutil
import sys
import tarfile

from common import save, sha256

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "research/scripts"))
import validate_state_equivalence as validator


WORKSPACE = Path("/agent")


def archive_workspace(destination, workspace=WORKSPACE):
    """Capture original files before extraction or independent probes."""
    files, times, issues = validator.inventory(workspace)
    if issues:
        raise ValueError(issues)
    with tarfile.open(destination / "workspace.tar.gz", "x:gz",
                      format=tarfile.PAX_FORMAT) as archive:
        archive.add(workspace, arcname="agent")
    after, after_times, issues = validator.inventory(workspace)
    if issues or files != after or times != after_times:
        raise ValueError("Source workspace changed during archive capture")
    save(destination / "original_inventory.json", {
        "files": files, "mtimes_ns": times,
        "workspace_hash": validator.digest(files),
        "archive_sha256": sha256(destination / "workspace.tar.gz"),
    })


def validate_members(members):
    """Reject external paths and extraction through symlink parents."""
    links = {m.name for m in members if m.issym()}
    names = set()
    for member in members:
        path = Path(member.name)
        if (path.is_absolute() or ".." in path.parts or not path.parts
                or path.parts[0] != "agent" or member.name in names):
            raise ValueError("Invalid or repeated archive member")
        names.add(member.name)
        if any(str(parent) in links for parent in path.parents):
            raise ValueError("Archive member has a symlink parent")
        if not (member.isfile() or member.isdir() or member.issym()
                or member.islnk()):
            raise ValueError("Special files require a new restore design")
        if member.issym() or member.islnk():
            target = member.linkname
            if member.issym():
                target = posixpath.join(str(path.parent), target)
            target = posixpath.normpath(target)
            if target != "agent" and not target.startswith("agent/"):
                raise ValueError("External links require external restore")
            if member.islnk() and target in links:
                raise ValueError("Hardlink targets a symlink")


def restore_archive(source, workspace=WORKSPACE):
    """Restore all recorded bytes and metadata into a disposable tree."""
    reference = json.loads((source / "original_inventory.json").read_text())
    if sha256(source / "workspace.tar.gz") != reference["archive_sha256"]:
        raise ValueError("Archive hash mismatch")
    if workspace == WORKSPACE and not Path("/opt/task/src_258").is_dir():
        raise ValueError("Restore must run inside the task container")
    with tarfile.open(source / "workspace.tar.gz", "r:gz") as archive:
        validate_members(archive.getmembers())
        previous_cwd = Path.cwd()
        os.chdir(workspace.parent)
        try:
            if workspace.exists():
                shutil.rmtree(workspace)
            if workspace.name != "agent":
                raise ValueError("The disposable tree must be named agent")
            archive.extractall(workspace.parent, filter="fully_trusted")
            # PAX timestamps can lose nanoseconds through float conversion.
            for name, stamp in sorted(reference["mtimes_ns"].items(),
                                      key=lambda item: -len(item[0])):
                path = workspace / name
                os.utime(path, ns=(stamp, stamp), follow_symlinks=False)
        finally:
            os.chdir(previous_cwd)
    files, times, issues = validator.inventory(workspace)
    if (issues or files != reference["files"]
            or times != reference["mtimes_ns"]):
        raise ValueError("Restore differs from ORIGINAL inventory")


def external_inventory():
    """Inventory task-relevant external files without secret values."""
    roots = {}
    for root in ("/home/dev", "/.kimi", "/tmp"):
        path = Path(root)
        if not path.exists():
            roots[root] = {"exists": False}
            continue
        files, _, issues = validator.inventory(path)
        if root == "/tmp":
            files = {k: v for k, v in files.items()
                     if k != "." and not k.startswith(".fs_blob_cache")
                     and k != "config.yaml"}
        roots[root] = {"exists": True, "files": files, "issues": issues}
    fixed = {}
    for name in ("/root/.gitconfig", "/etc/gitconfig", "/etc/passwd",
                 "/etc/group", "/usr/local/bin/mypy", "/bin/sh"):
        path = Path(name)
        fixed[name] = sha256(path) if path.is_file() else None
    processes = []
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            status = (proc / "status").read_text()
            uid_line = next(s for s in status.splitlines()
                            if s.startswith("Uid:"))
            if "1000" in uid_line.split()[1:]:
                state = next(s for s in status.splitlines()
                             if s.startswith("State:")).split()[1]
                processes.append({"pid": proc.name, "uid": uid_line,
                                  "state": state,
                                  "comm": (proc / "comm").read_text()})
        except (FileNotFoundError, PermissionError, StopIteration):
            continue
    return {
        "roots": roots, "fixed_files": fixed,
        "packages": sorted((d.metadata["Name"], d.version)
                           for d in importlib.metadata.distributions()),
        "agent_process_inventory": processes,
        "live_agent_processes": [p for p in processes if p["state"] != "Z"],
        "excluded_tmp": ["config.yaml", ".fs_blob_cache", "root metadata"],
        "limits": "No process, network, clock, kernel, or whole-machine copy",
    }


def compare_external(original, restored):
    """Compare fixed external data; record but exclude dead process IDs."""
    fixed = ("roots", "fixed_files", "packages", "excluded_tmp")
    return (all(original[k] == restored[k] for k in fixed)
            and not original["live_agent_processes"]
            and not restored["live_agent_processes"])


def capture_checkpoint(destination, config_path, runtime_path):
    args = argparse.Namespace(
        workspace=WORKSPACE, config=Path(config_path),
        state=destination / "state.json",
        messages=destination / "messages.json", runtime=Path(runtime_path),
        reference_config=Path("/opt/task/pyproject.toml"),
        extra_root=[], skip_mypy=False, timeout=60,
        output=destination / "validation.json")
    result = validator.capture(args)
    save(destination / "validation.json", result)
    save(destination / "external.json", external_inventory())
    return result
