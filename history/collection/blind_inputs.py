"""Normalize sealed evidence only after the collection-wide release gate."""

import difflib
from pathlib import Path
import tarfile

from blind import verify_release
from contract import read, sha


def archive_text(archive, path):
    if archive is None:
        return None
    with tarfile.open(archive) as stream:
        try:
            member = stream.getmember("agent/" + path)
        except KeyError:
            return None
        if not member.isfile():
            return None
        data = stream.extractfile(member).read()
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return "[NON-UTF8 CONTENT: inspect exact hashed archive bytes]"


def changes(before, after, before_archive, after_archive):
    result = []
    for path in sorted(before.keys() | after.keys()):
        if before.get(path) == after.get(path):
            continue
        row = {"path": path, "before": before.get(path),
               "after": after.get(path)}
        if (path.startswith(("src/", ".git/hooks/"))
                or path in ("pyproject.toml", ".git/config")):
            old = archive_text(before_archive, path) or ""
            new = archive_text(after_archive, path) or ""
            row["text_diff"] = "".join(difflib.unified_diff(
                old.splitlines(True), new.splitlines(True),
                fromfile=path + ":before", tofile=path + ":after"))
        result.append(row)
    return result


def normalize_run(directory, source, release, schedule_sha256):
    verify_release(release, schedule_sha256)
    hashes = read(directory / "artifact_sha256.json")
    for name, expected in hashes.items():
        path = (directory / name).resolve()
        if (not path.is_relative_to(directory.resolve())
                or sha(path) != expected):
            raise ValueError("Released raw artifact manifest differs")
    baseline = Path(source["checkpoint"])
    for name in ("validation.json", "workspace.tar.gz"):
        if sha(baseline / name) != source["checkpoint_sha256"][name]:
            raise ValueError("Original checkpoint reference changed")
    before = read(baseline / "validation.json")["files"]
    before_archive = baseline / "workspace.tar.gz"
    data = directory / "data"
    native_steps = {int(path.stem.split("-")[1])
                    for path in data.glob("native-*.json")}
    saved_steps = {int(path.name.split("-")[1])
                   for path in data.glob("step-*") if path.is_dir()}
    steps = []
    for step in sorted(native_steps | saved_steps):
        if not source["first_continuation_step"] <= step < 100:
            raise ValueError("Unexpected post-checkpoint decision index")
        checkpoint = data / f"step-{step}"
        if (checkpoint / "actions.json").is_file():
            action = read(checkpoint / "actions.json")
        else:
            action = {"native_message": read(data / f"native-{step:03d}.json")[
                "message"], "executions": []}
        if (checkpoint / "validation.json").is_file():
            state = read(checkpoint / "validation.json")
            archive = checkpoint / "workspace.tar.gz"
            evidence = {
                "mypy": state["mypy"],
                "git": {key: state["git"][key] for key in
                        ("head", "status", "tracked_files")},
                "workspace_changes": changes(before, state["files"],
                                              before_archive, archive),
                "verification_status": {
                    "source": "preserved_checkpoint",
                    "probe_mutations": state["probe_mutations"],
                    "git_probe_failures": [key for key, result in
                                           state["git"].items()
                                           if result["returncode"] != 0],
                },
            }
            before, before_archive = state["files"], archive
        else:
            evidence = {"mypy": None, "git": None, "workspace_changes": [],
                        "verification_status": "missing_checkpoint_ambiguous"}
        steps.append({"native_message": action["native_message"],
                      "executions": action["executions"],
                      "verified_state": evidence})
    return steps


if __name__ == "__main__":
    raise PermissionError("Raw outcome normalization remains locked")
