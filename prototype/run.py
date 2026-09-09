"""Launch one capped prototype run with immutable raw output."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid

from histories import verify_bundle


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "prototype_results"
CAPS = {"BASELINE": 3, "ORDINARY": 2, "A_FULL": 2,
        "B_FAILURE_FACT": 2, "C_STATE_ONLY": 2}
EXPERIMENTAL = {"A_FULL", "B_FAILURE_FACT", "C_STATE_ONLY"}


def save(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def fingerprint(config):
    core = {key: value for key, value in config.items()
            if key != "prototype"}
    core["workspace_archive"] = config.get("prototype", {}).get(
        "workspace_archive", False)
    return hashlib.sha256(json.dumps(
        core, sort_keys=True).encode()).hexdigest()


def require_gate(checkpoint, condition, config, image_id):
    """Require exact config and two equivalent ordinary restores."""
    if checkpoint is None:
        raise ValueError("A continuation requires --checkpoint.")
    provenance = checkpoint / "history_provenance.json"
    source = checkpoint
    if provenance.exists():
        history = verify_bundle(checkpoint)
        if history["condition"] != condition:
            raise ValueError("History condition does not match its label.")
        source = Path(history["source_checkpoint"])
    elif condition in EXPERIMENTAL:
        raise ValueError("Create the history bundle before this run.")
    baseline = source.parents[1] / "run.json"
    record = json.loads(baseline.read_text())
    if record["config_sha256"] != fingerprint(config):
        raise ValueError("The baseline config differs from this config.")
    if record["image_id"] != image_id:
        raise ValueError("The baseline Docker image differs.")
    code = baseline.parent / "implementation_sha256.json"
    if not code.exists():
        raise ValueError("The baseline lacks a frozen implementation.")
    saved_code = json.loads(code.read_text())
    for name in ("bootstrap.py", "loop.py"):
        digest = hashlib.sha256((ROOT / "prototype" / name).read_bytes())
        if digest.hexdigest() != saved_code[name]:
            raise ValueError("The task wrapper changed since baseline.")
    if condition not in EXPERIMENTAL:
        return
    checks = []
    for metadata in (RESULTS / "raw").glob("*/run.json"):
        run = json.loads(metadata.read_text())
        if (run["condition"] == "ORDINARY"
                and run["checkpoint"] == str(source)
                and run["config_sha256"] == fingerprint(config)
                and run["image_id"] == image_id):
            report = metadata.parent / "data" / "restore_check.json"
            if report.exists():
                checks.append(json.loads(report.read_text())["equivalent"])
    if len(checks) < 2 or not all(checks):
        raise ValueError("Two equivalent ordinary restores are required.")
    review = checkpoint.parent / "researcher_review.json"
    if not review.exists():
        raise ValueError("Complete the history and checkpoint review first.")
    approved = json.loads(review.read_text())
    if not approved.get("checkpoint_scientifically_usable"):
        raise ValueError("The checkpoint has no scientific-use review.")
    if not approved.get("history_information_review_complete"):
        raise ValueError("The history information review is incomplete.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--condition", choices=[*CAPS, "SMOKE",
                                               "RESTORE_CHECK"],
                        required=True)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--image", default="prototype-precommit:56fd0c11")
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    condition = args.condition
    provider = config["agent"]["provider"]
    if config["task"]["target_errors"] != 258:
        raise ValueError("This prototype is fixed at 258 errors.")
    if config["agent"]["max_steps"] != 100:
        raise ValueError("The frozen total step budget is 100.")
    if provider not in {"mock", "fireworks"}:
        raise ValueError("Only the frozen Fireworks route or mock is set up.")
    if provider == "mock" and condition in CAPS:
        raise ValueError("Scripted fixtures cannot count as model pilots.")
    if provider != "mock" and condition in {"SMOKE", "RESTORE_CHECK"}:
        raise ValueError("Technical fixture modes cannot call live models.")
    if provider == "fireworks" and not os.getenv("FIREWORKS_API_KEY"):
        raise ValueError("Export FIREWORKS_API_KEY; no run was started.")
    image_id = subprocess.check_output([
        "docker", "image", "inspect", args.image,
        "--format", "{{.Id}}"], text=True).strip()
    source = args.checkpoint.resolve() if args.checkpoint else None
    history_condition = None
    baseline_source = source
    if source and (source / "history_provenance.json").exists():
        history = verify_bundle(source)
        history_condition = history["condition"]
        baseline_source = Path(history["source_checkpoint"])
    if condition in {"ORDINARY", *EXPERIMENTAL}:
        require_gate(source, condition, config, image_id)
    if condition == "BASELINE" and source:
        raise ValueError("A baseline cannot start from a checkpoint.")
    raw = RESULTS / "raw"
    raw.mkdir(exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    run_id = (condition.lower() + "-" + datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    directory = raw / run_id
    with (RESULTS / "metadata" / "caps.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        prior = [json.loads(path.read_text())
                 for path in raw.glob("*/run.json")]
        if condition in CAPS:
            for run in prior:
                if run["condition"] in CAPS and (
                        run["config_sha256"] != fingerprint(config)
                        or run["image_id"] != image_id):
                    raise ValueError("The live pilot config/image is frozen.")
        count = sum(run["condition"] == condition for run in prior)
        if condition in CAPS and count >= CAPS[condition]:
            raise ValueError(f"Persistent cap reached for {condition}.")
        # A run allocation consumes its slot even if Docker/API later fails.
        directory.mkdir()
        save(directory / "run.json", {
            "run_id": run_id, "condition": condition,
            "history_condition": history_condition,
            "checkpoint": str(source) if source else None,
            "baseline_run_id": (baseline_source.parents[1].name
                                if baseline_source else run_id),
            "config_sha256": fingerprint(config),
            "image_id": image_id, "image_tag": args.image,
            "start": started, "timeout_seconds": args.timeout,
            "synthetic": provider == "mock",
        })
    data = directory / "data"
    data.mkdir()
    implementation = directory / "implementation"
    implementation.mkdir()
    hashes = {}
    for source_file in sorted((ROOT / "prototype").glob("*.py")):
        shutil.copy2(source_file, implementation / source_file.name)
        hashes[source_file.name] = hashlib.sha256(
            source_file.read_bytes()).hexdigest()
    save(directory / "implementation_sha256.json", hashes)
    save(directory / "config.json", config)
    cmd = ["docker", "run", "--name", run_id,
           "-e", f"RESULT_UID={os.getuid()}",
           "-e", f"RESULT_GID={os.getgid()}",
           "-v", f"{implementation}:/opt/prototype:ro",
           "-v", f"{directory / 'config.json'}:/opt/config.yaml:ro",
           "-v", f"{data}:/opt/output"]
    if provider == "mock":
        cmd.extend(["--network", "none"])
    else:
        cmd.extend(["-e", "FIREWORKS_API_KEY"])
    if source:
        cmd.extend(["-v", f"{source}:/opt/checkpoint:ro"])
    cmd.extend([image_id, "python", "/opt/prototype/bootstrap.py"])
    save(directory / "command.json", cmd)
    timed_out = False
    with (directory / "runtime.log").open("x") as log:
        try:
            result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=args.timeout)
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            subprocess.run(["docker", "kill", run_id], check=False,
                           stdout=log, stderr=log)
            returncode = 124
    save(directory / "exit.json", {
        "end": datetime.now(timezone.utc).isoformat(),
        "returncode": returncode, "timed_out": timed_out,
    })
    changes = subprocess.run(["docker", "diff", run_id], capture_output=True,
                             text=True, check=False)
    save(directory / "container_diff.json", {
        "returncode": changes.returncode, "stdout": changes.stdout,
        "stderr": changes.stderr,
    })
    subprocess.run(["docker", "rm", run_id], check=False,
                   stdout=subprocess.DEVNULL)
    print(directory, flush=True)
    raise SystemExit(returncode)


if __name__ == "__main__":
    main()
