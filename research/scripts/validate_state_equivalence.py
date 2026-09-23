#!/usr/bin/env python3
"""Capture and compare task state before a continuation's first model call.

Capture inside a disposable task container. This utility makes no model calls.
An equal result covers only the recorded fields, never semantic history parity.
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys


VERSION = 1
RUNTIME_REQUIRED = {
    "model", "provider", "request_kwargs", "tools", "agent_cwd",
    "agent_environment", "image_id", "command_timeout_seconds",
}


def digest(value: object) -> str:
    """Hash canonical JSON, or bytes without conversion."""
    data = value if isinstance(value, bytes) else json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()
    return hashlib.sha256(data).hexdigest()


def read_document(path: Path) -> object:
    """Read JSON or YAML without a model provider dependency."""
    if path.suffix == ".json":
        return json.loads(path.read_text())
    import yaml
    return yaml.safe_load(path.read_text())


def command(argv: list[str], cwd: Path, timeout: int = 60) -> dict:
    """Keep failures explicit so two failed probes never imply equality."""
    try:
        result = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0",
                 "PYTHONDONTWRITEBYTECODE": "1"},
        )
        return {
            "returncode": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr, "timeout": False,
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "returncode": None, "stdout": "", "stderr": str(error),
            "timeout": isinstance(error, subprocess.TimeoutExpired),
        }


def inventory(root: Path) -> tuple[dict, dict, list[str]]:
    """Hash all files and links, including Git and generated files."""
    entries, times, errors = {}, {}, []
    pending = [root]
    while pending:
        path = pending.pop()
        name = path.relative_to(root).as_posix()
        try:
            before = path.lstat()
            entry = {
                "mode": stat.S_IMODE(before.st_mode),
                "uid": before.st_uid, "gid": before.st_gid,
            }
            if stat.S_ISLNK(before.st_mode):
                entry.update(kind="symlink", target=os.readlink(path))
            elif stat.S_ISREG(before.st_mode):
                entry.update(kind="file", sha256=digest(path.read_bytes()))
            elif stat.S_ISDIR(before.st_mode):
                entry.update(kind="directory")
                pending.extend(sorted(path.iterdir(), reverse=True))
            else:
                entry.update(kind="special")
                errors.append(f"Special file requires review: {name}")
            after = path.lstat()
            if (before.st_mtime_ns, before.st_size) != (
                after.st_mtime_ns, after.st_size,
            ):
                errors.append(f"File changed during capture: {name}")
            entries[name] = entry
            times[name] = before.st_mtime_ns
        except OSError as error:
            errors.append(f"Cannot inspect {name}: {error}")
    return entries, times, errors


def validate_messages(messages: list[dict]) -> list[str]:
    """Check complete OpenAI chat tool-call groups at a decision boundary."""
    errors, pending, seen = [], set(), set()
    if len(messages) < 2 or [m.get("role") for m in messages[:2]] != [
        "system", "user",
    ]:
        errors.append("Expected initial system and user messages")
    for index, message in enumerate(messages):
        role = message.get("role")
        if role == "system" and index != 0:
            errors.append(f"Additional system instruction at message {index}")
        if role == "assistant":
            if pending:
                errors.append(f"Unanswered tool calls before message {index}")
            for call in message.get("tool_calls") or []:
                call_id = call.get("id")
                if not call_id or call_id in seen:
                    errors.append(f"Missing or duplicate tool ID at {index}")
                pending.add(call_id)
                seen.add(call_id)
        elif role == "tool":
            call_id = message.get("tool_call_id")
            if call_id not in pending:
                errors.append(f"Orphan or repeated tool result at {index}")
            pending.discard(call_id)
        elif pending:
            errors.append(f"Non-tool message interrupts results at {index}")
        if role not in {"system", "user", "assistant", "tool"}:
            errors.append(f"Unsupported message role at {index}")
    if pending:
        errors.append("Checkpoint contains unresolved tool calls")
    if messages and messages[-1].get("role") != "tool":
        errors.append("This validator requires a post-tool decision checkpoint")
    return errors


def mypy_probe(workspace: Path, config: Path, timeout: int) -> dict:
    """Measure current errors under an explicit config without cache writes."""
    argv = [
        sys.executable, "-m", "mypy", "src", "--config-file", str(config),
        "--no-incremental", "--cache-dir", "/dev/null",
        "--no-color-output", "--no-error-summary", "--show-error-codes",
    ]
    result = command(argv, workspace, timeout)
    lines = result["stdout"].replace(str(workspace) + "/", "").splitlines()
    errors = sorted(line for line in lines if re.search(r": error:", line))
    valid = result["returncode"] == 0 or (
        result["returncode"] == 1 and bool(errors)
    )
    return {
        **result, "config_sha256": digest(config.read_bytes()),
        "error_count": len(errors) if valid else None,
        "errors": errors, "errors_hash": digest(errors), "valid": valid,
    }


def capture(args: argparse.Namespace) -> dict:
    """Record actual task files and supplied effective runtime settings."""
    workspace = args.workspace.resolve()
    if args.output.resolve().is_relative_to(workspace):
        raise ValueError("Write the capture outside the task workspace")
    config = read_document(args.config)
    messages = read_document(args.messages)
    state = read_document(args.state)
    runtime = read_document(args.runtime) if args.runtime else None
    issues = validate_messages(messages)
    if runtime is None or not RUNTIME_REQUIRED.issubset(runtime):
        issues.append("Effective runtime fields are incomplete or absent")
    files, times, fs_issues = inventory(workspace)
    issues.extend(fs_issues)
    git_args = {
        "head": ["rev-parse", "HEAD"],
        "status": ["status", "--porcelain=v1", "--untracked-files=all"],
        "diff": ["diff", "--binary", "--no-ext-diff", "--no-textconv"],
        "staged_diff": [
            "diff", "--cached", "--binary", "--no-ext-diff",
            "--no-textconv",
        ],
        "tracked_files": ["ls-files", "--stage"],
    }
    git = {
        name: command(
            ["git", "-c", "diff.autoRefreshIndex=false", *argv], workspace,
        )
        for name, argv in git_args.items()
    }
    for name, result in git.items():
        if result["returncode"] != 0:
            issues.append(f"Git probe failed: {name}")
    agent = config.get("agent", {})
    checkpoint_step = state.get("step")
    max_steps = agent.get("max_steps", 30)
    steps_remaining = max_steps - checkpoint_step - 1
    if steps_remaining <= 0 or state.get("task_completed"):
        issues.append("Checkpoint is terminal or has no action budget")
    latest_tool = next(
        (m for m in reversed(messages) if m.get("role") == "tool"), None,
    )
    latest_call = next(
        (m for m in reversed(messages) if m.get("tool_calls")), None,
    )
    mypy = {}
    if args.skip_mypy:
        issues.append("Mypy checks were skipped")
    else:
        paths = {"active": workspace / "pyproject.toml"}
        if args.reference_config:
            paths["reference"] = args.reference_config.resolve()
        else:
            issues.append("Pristine mypy config was not supplied")
        for name, path in paths.items():
            mypy[name] = mypy_probe(workspace, path, args.timeout)
            if not mypy[name]["valid"]:
                issues.append(f"Mypy probe failed: {name}")
    extra_roots = {}
    for path in args.extra_root:
        entries, _, extra_issues = inventory(path.resolve())
        extra_roots[str(path.resolve())] = entries
        issues.extend(extra_issues)
    after_files, _, after_issues = inventory(workspace)
    issues.extend(after_issues)
    probe_mutations = sorted(
        key for key in set(files) | set(after_files)
        if files.get(key) != after_files.get(key)
    )
    if probe_mutations:
        issues.append("Task workspace changed during validation")
    return {
        "version": VERSION,
        "captured_at": datetime.datetime.now(
            datetime.timezone.utc,
        ).isoformat(),
        "workspace_root": str(workspace), "files": files,
        "workspace_hash": digest(files), "mtimes_ns": times,
        "probe_mutations": probe_mutations,
        "git": git, "extra_roots": extra_roots,
        "config_hash": digest(config), "state_hash": digest(state),
        "checkpoint_step": checkpoint_step, "max_steps": max_steps,
        "steps_remaining": steps_remaining,
        "system_prompt_hash": digest(messages[0]),
        "user_prompt_hash": digest(messages[1]),
        "latest_observation_hash": digest(latest_tool),
        "latest_call_hash": digest(latest_call),
        "history_hash": digest(messages),
        "history_message_roles": [m.get("role") for m in messages],
        "history_token_count": None,
        "runtime": runtime, "mypy": mypy,
        "mypy_version": command(
            [sys.executable, "-m", "mypy", "--version"], workspace,
        ),
        "capture_process_cwd": os.getcwd(),
        "capture_uid": os.geteuid(), "capture_gid": os.getegid(),
        "issues": sorted(set(issues)),
    }


def compare(left: dict, right: dict) -> dict:
    """Fail closed on missing probes and report exact field differences."""
    fixed = [
        "version", "workspace_root", "workspace_hash", "git",
        "extra_roots", "config_hash", "state_hash", "checkpoint_step",
        "max_steps", "steps_remaining", "system_prompt_hash",
        "user_prompt_hash", "latest_observation_hash", "latest_call_hash",
        "runtime", "mypy_version",
    ]
    missing = [key for key in fixed if key not in left or key not in right]
    different = [key for key in fixed if left.get(key) != right.get(key)]
    for key in ["active", "reference"]:
        a, b = left.get("mypy", {}).get(key), right.get("mypy", {}).get(key)
        if not a or not b or not a.get("valid") or not b.get("valid"):
            missing.append(f"mypy.{key}")
        elif any(a.get(k) != b.get(k) for k in [
            "config_sha256", "error_count", "errors_hash", "returncode",
        ]):
            different.append(f"mypy.{key}")
    issues = left.get("issues", []) + right.get("issues", [])
    for label, record in [("left", left), ("right", right)]:
        for key in fixed:
            if record.get(key) is None:
                missing.append(f"{label}.{key}")
        if record.get("version") != VERSION:
            issues.append(f"{label} has an unsupported capture version")
        for key in ["checkpoint_step", "max_steps", "steps_remaining"]:
            if type(record.get(key)) is not int or record[key] < 0:
                issues.append(f"{label} has an invalid {key}")
        if all(type(record.get(k)) is int for k in [
            "max_steps", "checkpoint_step", "steps_remaining",
        ]) and record["steps_remaining"] != (
            record["max_steps"] - record["checkpoint_step"] - 1
        ):
            issues.append(f"{label} action budget is inconsistent")
        if "files" not in record or digest(record["files"]) != record.get(
            "workspace_hash",
        ):
            issues.append(f"{label} workspace hash is missing or inconsistent")
        runtime = record.get("runtime")
        if not runtime or not RUNTIME_REQUIRED.issubset(runtime):
            missing.append(f"{label}.runtime")
        elif any(runtime.get(key) is None for key in RUNTIME_REQUIRED):
            missing.append(f"{label}.runtime_null_fields")
    changed_files = sorted(
        key for key in set(left.get("files", {})) | set(right.get("files", {}))
        if left.get("files", {}).get(key) != right.get("files", {}).get(key)
    )
    verdict = "different" if different else (
        "inconclusive" if missing or issues else "equal_on_recorded_fields"
    )
    return {
        "verdict": verdict, "different_fields": different,
        "changed_files": changed_files, "missing_checks": sorted(set(missing)),
        "issues": sorted(set(issues)),
        "history_equal": left.get("history_hash") == right.get("history_hash"),
        "message_roles_equal": left.get("history_message_roles") == right.get(
            "history_message_roles",
        ),
        "mtimes_equal": left.get("mtimes_ns") == right.get("mtimes_ns"),
        "limits": [
            "Semantic information parity needs human review.",
            "External files, processes, clocks, and APIs are not certified.",
            "Runtime metadata must come from the prepared provider object.",
            "File timestamps require review even when content matches.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    cap = subparsers.add_parser("capture")
    for name in ["workspace", "config", "messages", "state", "output"]:
        cap.add_argument(f"--{name}", type=Path, required=True)
    cap.add_argument("--runtime", type=Path)
    cap.add_argument("--reference-config", type=Path)
    cap.add_argument("--extra-root", type=Path, action="append", default=[])
    cap.add_argument("--skip-mypy", action="store_true")
    cap.add_argument("--timeout", type=int, default=60)
    diff = subparsers.add_parser("compare")
    diff.add_argument("left", type=Path)
    diff.add_argument("right", type=Path)
    diff.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = capture(args) if args.mode == "capture" else compare(
            read_document(args.left), read_document(args.right),
        )
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 2
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with args.output.open("x") as stream:
            stream.write(output)
    if args.mode == "compare":
        print(output, end="")
        return {
            "equal_on_recorded_fields": 0, "different": 1, "inconclusive": 2,
        }[result["verdict"]]
    issue_count = len(result["issues"])
    print(f"Captured {result['workspace_hash']}; issues={issue_count}")
    return 2 if result["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
