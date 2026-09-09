"""Preserve exactly the requested runs, with one persistent source slot."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import uuid

from common import now, redact, save, seal, sha256


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research/data/raw/integrated-pilot"
UPSTREAM_SHA = "56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb"
MODEL = "accounts/fireworks/models/kimi-k2-thinking"


def output(argv, cwd=ROOT):
    return subprocess.check_output(argv, cwd=cwd, text=True).strip()


def code_hashes():
    paths = [p for p in (ROOT / "pilot").rglob("*") if p.is_file()
             and "__pycache__" not in p.parts and p.name != "frozen.json"]
    paths.extend(ROOT / name for name in (
        "research/SOURCE_CHECKPOINT_RULE.md",
        "research/scripts/validate_state_equivalence.py"))
    return {str(p.relative_to(ROOT)): sha256(p) for p in sorted(paths)}


def require_frozen(config_path, image):
    frozen = json.loads((ROOT / "pilot/frozen.json").read_text())
    if (sha256(config_path) != frozen["config_sha256"]
            or image != frozen["image_id"]
            or code_hashes() != frozen["code_sha256"]):
        raise ValueError("Frozen config, image, or implementation changed")
    for name, digest in frozen["gate_artifacts"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError("Validation gate artifact changed")
    gates = json.loads((ROOT / frozen["offline_gate"]).read_text())
    if not all(gates[k] for k in ("archive_original_match", "sampling_pass")):
        raise ValueError("Offline gates did not pass")
    return frozen


def allocate(mode, metadata, raw=RAW):
    raw.mkdir(parents=True, exist_ok=True)
    common_git = Path(output(["git", "rev-parse", "--git-common-dir"]))
    if not common_git.is_absolute():
        common_git = ROOT / common_git
    with (common_git / "integrated-pilot.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        run_id = f"{mode}-{uuid.uuid4().hex}"
        if mode == "source":
            # The ledger is outside output folders and shared by worktrees.
            save(common_git / "integrated-pilot-source-slot.json", {
                "run_id": run_id, "allocated_at": now(),
                "policy": "One slot; all allocated failures consume it",
            })
        directory = raw / run_id
        directory.mkdir(mode=0o700)
        save(directory / "run.json", {
            **metadata, "run_id": run_id, "mode": mode, "start": now(),
        })
    return directory


def validate_request(mode, count, config, source):
    if count < 1 or (mode == "source" and count != 1):
        raise ValueError("Source stage permits exactly one requested run")
    if config["task"]["target_errors"] != 258:
        raise ValueError("Only src_258 is approved for this pilot")
    if config["agent"]["max_steps"] != 100:
        raise ValueError("Total decision budget must remain 100")
    if (mode == "restore-check") != (source is not None):
        raise ValueError("Only restore-check accepts a checkpoint")
    if mode == "source":
        if (config["agent"]["provider"] != "fireworks"
                or config["agent"]["model"] != MODEL):
            raise ValueError("Requested Kimi route cannot be substituted")
        if "script" in config["pilot"]:
            raise ValueError("A real source cannot use a scripted fixture")
    elif config["agent"]["provider"] != "mock":
        raise ValueError("Technical probes require mock and no network")


def preflight(config, directory):
    """Run one request-acceptance probe; never change model or provider."""
    if not os.environ.get("FIREWORKS_API_KEY"):
        save(directory / "preflight.json", {
            "passed": False, "reason": "FIREWORKS_API_KEY absent",
            "model_requests": 0, "time": now(),
        })
        return False
    # Use the exact image adapter and schemas, without a task trajectory.
    image = json.loads((ROOT / "pilot/frozen.json").read_text())["image_id"]
    name = f"pilot-preflight-{uuid.uuid4().hex}"
    command = ["docker", "run", "--rm", "--name", name,
               "-e", "FIREWORKS_API_KEY",
               "-e", f"RESULT_UID={os.getuid()}",
               "-e", f"RESULT_GID={os.getgid()}",
               "-v", f"{directory}:/opt/preflight-output",
               "-v", f"{ROOT / 'pilot/configs/first_pilot.json'}:"
               "/opt/config.yaml:ro", image,
               "python", "/opt/pilot/provider_preflight.py"]
    try:
        subprocess.run(command, check=False, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", name], capture_output=True)
        save(directory / "preflight_timeout.json", {"passed": False})
        return False
    path = directory / "preflight.json"
    return path.exists() and json.loads(path.read_text())["passed"]


def launch(mode, config_path, image, source=None, timeout=None):
    config = json.loads(config_path.read_text())
    timeout = timeout or config["pilot"]["wall_timeout_seconds"]
    metadata = {
        "config_sha256": sha256(config_path), "image_id": image,
        "experiment_commit": output(["git", "rev-parse", "HEAD"]),
        "upstream_commit": output(["git", "rev-parse", "HEAD"],
                                  ROOT / "upstream/agent-interp-envs"),
        "experiment_dirty": bool(output(["git", "status", "--porcelain"])),
        "checkpoint": str(source) if source else None,
        "wall_timeout_seconds": timeout,
        "synthetic": mode != "source",
    }
    if metadata["upstream_commit"] != UPSTREAM_SHA:
        raise ValueError("Upstream pin changed")
    directory = allocate(mode, metadata)
    data = directory / "data"
    data.mkdir()
    shutil.copyfile(config_path, directory / "config.json")
    shutil.copytree(ROOT / "pilot", directory / "implementation",
                    ignore=shutil.ignore_patterns("__pycache__"))
    save(directory / "implementation_sha256.json", code_hashes())
    name = directory.name
    command = ["docker", "run", "--name", name,
               "-e", f"PILOT_IMAGE_ID={image}",
               "-e", "PYTHONDONTWRITEBYTECODE=1",
               "-v", f"{directory / 'config.json'}:/opt/config.yaml:ro",
               "-v", f"{data}:/opt/output"]
    if mode == "source":
        command.extend(["-e", "FIREWORKS_API_KEY"])
    else:
        command.extend(["--network", "none"])
    if source:
        command.extend(["-v", f"{source}:/opt/checkpoint:ro"])
    command.extend([image, "python", "/opt/pilot/bootstrap.py"])
    save(directory / "command.json", command)
    timed_out, interrupted, code = False, False, None
    process = None
    with (directory / "runtime.log").open("x") as log:
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True)

            def drain():
                for line in process.stdout:
                    log.write(redact(line))
                    log.flush()

            thread = threading.Thread(target=drain, daemon=True)
            thread.start()
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out, code = True, 124
        except KeyboardInterrupt:
            interrupted, code = True, 130
        finally:
            if process is not None and process.poll() is None:
                subprocess.run(["docker", "kill", name],
                               capture_output=True, check=False)
                process.wait(timeout=30)
            if process is not None:
                thread.join(timeout=30)
            # Keep the stopped container if any final recovery fails.
            recovery = subprocess.run([
                "docker", "cp", "-a", f"{name}:/agent",
                str(directory / "final_workspace")],
                capture_output=True, text=True, check=False)
            changes = subprocess.run(["docker", "diff", name],
                                     capture_output=True, text=True)
            save(directory / "recovery.json", {
                "workspace_copy_returncode": recovery.returncode,
                "workspace_copy_error": redact(recovery.stderr),
                "container_diff": changes.stdout,
                "container_diff_returncode": changes.returncode,
            })
            save(directory / "exit.json", {
                "end": now(), "returncode": code, "timed_out": timed_out,
                "interrupted": interrupted,
            })
            # Copy archive bytes before container deletion; never chmod /agent.
            if recovery.returncode == 0:
                shutil.make_archive(str(directory / "final_workspace"),
                                    "gztar", directory / "final_workspace")
                subprocess.run(["docker", "rm", name],
                               capture_output=True, check=False)
    # Docker root writes require host ownership for immutable host artifacts.
    subprocess.run([
        "docker", "run", "--rm", "--network", "none",
        "-v", f"{directory}:/opt/host-artifacts", image,
        "chown", "-R", f"{os.getuid()}:{os.getgid()}",
        "/opt/host-artifacts"], check=True, capture_output=True)
    seal(directory)
    return directory, code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("source", "fixture", "restore-check"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--fixture-timeout", type=int)
    args = parser.parse_args()
    os.umask(0o077)
    config = json.loads(args.config.read_text())
    source = args.checkpoint.resolve() if args.checkpoint else None
    validate_request(args.mode, args.count, config, source)
    image = output(["docker", "image", "inspect", args.image,
                    "--format", "{{.Id}}"])
    if args.mode == "source":
        if args.fixture_timeout is not None:
            raise ValueError("Real-run timeout is frozen in the config")
        require_frozen(args.config, image)
        directory = RAW / f"preflight-{uuid.uuid4().hex}"
        directory.mkdir(parents=True)
        if not preflight(config, directory):
            raise SystemExit("Kimi preflight failed; no source trajectory")
    codes = []
    for _ in range(args.count):
        path, code = launch(args.mode, args.config.resolve(), image, source,
                            args.fixture_timeout)
        print(path, flush=True)
        codes.append(code)
    raise SystemExit(0 if all(code == 0 for code in codes) else 1)


if __name__ == "__main__":
    main()
