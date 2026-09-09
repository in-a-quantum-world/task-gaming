"""Instrument the supported task loop without edits to upstream files."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import traceback
from datetime import datetime, timezone

sys.path.insert(0, "/opt")

from agent_interp_envs import checkpoint
from agent_interp_envs.config import load_config
from agent_interp_envs.providers import create_provider
from agent_interp_envs.providers.mock_provider import MockProvider
from run_step import run_step
from score import score_precommit_hook
import states
from tools import get_tools


OUTPUT = Path("/opt/output")


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    with Path(path).open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def inventory():
    """Hash every workspace entry, including Git files and caches."""
    entries = {}
    for path in sorted(Path("/agent").rglob("*")):
        info = path.lstat()
        entry = {
            "mode": stat.S_IMODE(info.st_mode),
            "uid": info.st_uid, "gid": info.st_gid,
        }
        if path.is_symlink():
            entry.update(kind="symlink", target=os.readlink(path))
        elif path.is_file():
            entry.update(kind="file", sha256=hashlib.sha256(
                path.read_bytes()).hexdigest())
        elif path.is_dir():
            entry.update(kind="directory")
        else:
            entry.update(kind="special")
        entries[str(path.relative_to("/agent"))] = entry
    digest = hashlib.sha256(json.dumps(
        entries, sort_keys=True).encode()).hexdigest()
    return {"sha256": digest, "entries": entries}


def command(args):
    result = subprocess.run(args, cwd="/agent", capture_output=True,
                            text=True, timeout=60)
    return {"argv": args, "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def diagnostics():
    """Keep probe caches outside the task and do not invoke its hook."""
    result = command(["mypy", "--cache-dir=/opt/probe-cache", "src"])
    match = re.search(r"Found (\d+) errors?", result["stdout"])
    count = int(match[1]) if match else None
    if result["returncode"] == 0:
        count = 0
    return {
        "mypy": result, "unresolved_error_count": count,
        "git_status": command(["git", "--no-optional-locks", "status",
                               "--porcelain=v1"]),
        "git_head": command(["git", "rev-parse", "HEAD"]),
        "git_log": command(["git", "log", "--format=%H %s"]),
    }


def compare(expected, actual):
    before, after = expected["entries"], actual["entries"]
    return {key: {"before": before.get(key), "after": after.get(key)}
            for key in sorted(before.keys() | after.keys())
            if before.get(key) != after.get(key)}


def save_archive(destination):
    """Save all workspace files, including unchanged Git data and caches."""
    with tarfile.open(destination / "workspace.tar.gz", "x:gz") as archive:
        archive.add("/agent", arcname="agent")


def restore_archive(source):
    """Replace only the disposable container's workspace."""
    with tarfile.open(source / "workspace.tar.gz", "r:gz") as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Archive path escapes the workspace.")
            if not path.parts or path.parts[0] != "agent":
                raise ValueError("Archive member is outside /agent.")
            if member.isdev() or member.isfifo():
                raise ValueError("Archive contains a special device.")
            if member.issym() or member.islnk():
                target = Path(member.linkname)
                if target.is_absolute() or ".." in target.parts:
                    raise ValueError("External links need manual review.")
        os.chdir("/")
        shutil.rmtree("/agent")
        archive.extractall("/", filter="fully_trusted")
        os.chdir("/agent")


def instrument_provider(provider):
    """Save request bodies and responses; never save request headers."""
    client = getattr(provider, "client", None)
    if client is None:
        return
    request_count = 0

    def request_hook(request):
        nonlocal request_count
        request_count += 1
        request.extensions["prototype_request_number"] = request_count
        save(OUTPUT / f"api-request-{request_count:04d}.json", {
            "time": now(), "method": request.method,
            "url": str(request.url.copy_with(query=None)),
            "body": json.loads(request.content),
        })

    def response_hook(response):
        number = response.request.extensions["prototype_request_number"]
        response.read()
        save(OUTPUT / f"api-response-{number:04d}.json", {
            "time": now(), "status_code": response.status_code,
            "body": response.text,
        })

    client._client.event_hooks["request"].append(request_hook)
    client._client.event_hooks["response"].append(response_hook)


def main():
    config = load_config(sys.argv[1])
    settings = config.get("prototype", {})
    saved = Path("/opt/checkpoint")
    state = states.CodingAgentState()
    provider = None
    invoked = 0
    termination = "runtime_error"
    started = now()
    try:
        if saved.exists():
            state, provider = states.restore(config, saved)
            actual = inventory()
            expected = json.loads((saved / "workspace.json").read_text())
            differences = compare(expected, actual)
            save(OUTPUT / "upstream_restore_check.json", {
                "equivalent": not differences, "differences": differences,
            })
            if settings.get("workspace_archive"):
                restore_archive(saved)
                actual = inventory()
                differences = compare(expected, actual)
            save(OUTPUT / "restore_workspace.json", actual)
            save(OUTPUT / "restore_check.json", {
                "equivalent": not differences, "differences": differences,
                "checkpoint_step": state.step,
                "next_step": state.step + 1,
                "remaining_steps": config["agent"]["max_steps"]
                - state.step - 1,
                "scope": "/agent content, paths, modes, uid/gid; no mtimes",
            })
            if differences:
                termination = "restore_non_equivalent"
                raise RuntimeError("Workspace differs; no provider call.")
            state.step += 1
        else:
            state.variant = str(config["task"]["target_errors"])
            states.init_fs_tracking()
            provider = create_provider(
                messages=[
                    {"role": "system", "content": config["prompts"][
                        "system_prompt"]},
                    {"role": "user", "content": config["prompts"][
                        "user_prompt"]},
                ], tools=get_tools(config),
                **checkpoint.provider_kwargs(config))
            save(OUTPUT / "initial_workspace.json", inventory())
            save(OUTPUT / "initial_diagnostics.json", diagnostics())
        if config["agent"]["provider"] == "mock":
            # The stock mock cursor resets on restore. Use the state step.
            provider = MockProvider(
                model=config["agent"]["model"], messages=provider.messages,
                tools=get_tools(config),
                mock_script=settings["script"][state.step:])
        instrument_provider(provider)
        save(OUTPUT / "initial_messages.json", provider.messages)
        save(OUTPUT / "effective_provider.json", {
            "provider": config["agent"]["provider"],
            "model": provider.model,
            "kwargs": getattr(provider, "kwargs", {}),
            "transport": "SDK request/response hooks; headers excluded",
        })
        if settings.get("restore_only"):
            termination = "restore_check_only"
            return
        while state.step < config["agent"]["max_steps"]:
            invoked += 1
            finished = run_step(provider, state, config)
            destination = checkpoint.step_dir(state.step)
            states.dump(state, provider, destination)
            if settings.get("workspace_archive"):
                save_archive(destination)
            save(destination / "workspace.json", inventory())
            save(destination / "diagnostics.json", diagnostics())
            save(destination / "scorer.json", score_precommit_hook(
                state.commands, Path("/agent")))
            state.step += 1
            if finished:
                termination = "text_only_or_done"
                break
        else:
            termination = "max_steps"
    except Exception as error:
        save(OUTPUT / "error.json", {
            "type": type(error).__name__, "message": str(error),
            "traceback": traceback.format_exc(),
        })
        raise
    finally:
        save(OUTPUT / "termination.json", {
            "start": started, "end": now(), "reason": termination,
            "provider_invocations": invoked, "next_step": state.step,
            "http_requests": len(list(OUTPUT.glob("api-request-*.json"))),
            "mock": config["agent"]["provider"] == "mock",
        })
        if provider is not None:
            save(OUTPUT / "messages.json", provider.messages)
        save(OUTPUT / "final_state.json", state.to_dict())
        save(OUTPUT / "scorer.json", score_precommit_hook(
            state.commands, Path("/agent")))


if __name__ == "__main__":
    main()
