"""One explicit 602-stage source; reuse the unchanged preservation launcher."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pilot"))
import run as preserved
from common import now, redact, save, seal, sha256

IMAGE = "sha256:271a3daf958c33c9e6ad7332624015f9303ef06bf2a805abd12004abff8ddbae"
RAW = ROOT / "research/data/raw/stress602"
SLOT = "602-stress-source-slot.json"
KEY_FILE = ROOT.parent / "integrated-pilot/.env"
LEGACY_HASHES = preserved.code_hashes


def expected_config():
    config = json.loads((ROOT / "SOURCE_PILOT_CONFIG.yaml").read_text())
    config["task"]["target_errors"] = 602
    return config


def validate_request(mode, count, config, checkpoint):
    if count < 1 or (mode == "source" and count != 1):
        raise ValueError("This stage permits exactly one source")
    if config["task"]["target_errors"] != 602:
        raise ValueError("This stage requires src_602")
    if mode == "source":
        if config != expected_config() or checkpoint is not None:
            raise ValueError("Only target_errors may differ; no continuation")
    elif config["agent"]["provider"] != "mock":
        raise ValueError("Only synthetic offline archive probes are permitted")
    if (mode == "restore-check") != (checkpoint is not None):
        raise ValueError("Only an offline restore-check accepts a checkpoint")


def common_git():
    path = Path(preserved.output(["git", "rev-parse", "--git-common-dir"]))
    return path if path.is_absolute() else ROOT / path


def verify_legacy():
    frozen = json.loads((ROOT / "pilot/frozen.json").read_text())
    if LEGACY_HASHES() != frozen["code_sha256"]:
        raise ValueError("The frozen 258 implementation was changed")
    prior = json.loads((ROOT / "research/evidence/stress602/prior-state.json")
                       .read_text())
    if sha256(prior["old_258_slot_path"]) != prior["old_258_slot_sha256"]:
        raise ValueError("The 258 source slot changed")


def stage_hashes():
    paths = sorted((ROOT / "stress602").glob("*.py"))
    paths.extend([ROOT / "stress602/archive_fixture.json",
                  ROOT / "stress602/README.md"])
    paths.extend(ROOT / name for name in (
        "STRESS_602_CONFIG.yaml", "STRESS_602_PREREG.md"))
    return {str(path.relative_to(ROOT)): sha256(path) for path in paths}


def require_frozen(config_path):
    verify_legacy()
    frozen = json.loads((ROOT / "stress602/frozen.json").read_text())
    if (sha256(config_path) != frozen["config_sha256"]
            or stage_hashes() != frozen["stage_code_sha256"]
            or frozen["image_id"] != IMAGE):
        raise ValueError("602 config, code, or image freeze changed")
    for name, digest in frozen["gate_artifacts"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError("602 gate evidence changed")
    gates = json.loads((ROOT / frozen["gates_path"]).read_text())
    if not all(gates[key] for key in (
            "baseline_602", "archive_original_match", "sampling_pass",
            "separate_stage_cap")):
        raise ValueError("602 infrastructure gates have not passed")


def allocate(mode, metadata, raw=RAW):
    raw.mkdir(parents=True, exist_ok=True)
    common = common_git()
    with (common / "602-stress.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        run_id = f"{mode}602-{uuid.uuid4().hex}"
        if mode == "source":
            save(common / SLOT, {
                "run_id": run_id, "allocated_at": now(),
                "stage": "602-stress", "target_errors": 602,
                "policy": "One source; failures consume the slot",
            })
        directory = raw / run_id
        directory.mkdir(mode=0o700)
        save(directory / "run.json", {
            **metadata, "run_id": run_id, "mode": mode, "start": now(),
            "stage": "602-stress", "target_errors": 602,
        })
        shutil.copytree(ROOT / "stress602", directory / "stage_implementation",
                        ignore=shutil.ignore_patterns("__pycache__"))
    return directory


def preflight(config_path, directory):
    name = f"stress602-preflight-{uuid.uuid4().hex}"
    command = [
        "docker", "run", "--rm", "--name", name,
        "-e", "OPENROUTER_API_KEY", "-e", f"RESULT_UID={os.getuid()}",
        "-e", f"RESULT_GID={os.getgid()}",
        "-v", f"{directory}:/opt/preflight-output",
        "-v", f"{config_path}:/opt/config.yaml:ro", IMAGE,
        "python", "/opt/pilot/provider_preflight.py",
    ]
    save(directory / "command.json", command)
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=660)
        save(directory / "process.json", {
            "returncode": result.returncode, "stdout": redact(result.stdout),
            "stderr": redact(result.stderr),
        })
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", name], capture_output=True)
        save(directory / "preflight_timeout.json", {"passed": False})
    finally:
        subprocess.run([
            "docker", "run", "--rm", "--network", "none",
            "-v", f"{directory}:/artifacts", IMAGE, "chown", "-R",
            f"{os.getuid()}:{os.getgid()}", "/artifacts"],
            check=True, capture_output=True)
        seal(directory)
    path = directory / "preflight.json"
    return path.exists() and json.loads(path.read_text())["passed"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("source", "fixture", "restore-check"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text())
    checkpoint = args.checkpoint.resolve() if args.checkpoint else None
    validate_request(args.mode, args.count, config, checkpoint)
    verify_legacy()
    image = preserved.output(["docker", "image", "inspect", IMAGE,
                              "--format", "{{.Id}}"])
    if image != IMAGE:
        raise ValueError("The actual experimental image differs")
    if args.mode == "source":
        require_frozen(config_path)
        if (common_git() / SLOT).exists():
            raise ValueError("The 602 source slot is already consumed")
        from dotenv import dotenv_values
        key = dotenv_values(KEY_FILE).get("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("Approved local OpenRouter key is unavailable")
        os.environ["OPENROUTER_API_KEY"] = key
        RAW.mkdir(parents=True, exist_ok=True)
        directory = RAW / f"preflight602-{uuid.uuid4().hex}"
        directory.mkdir(mode=0o700)
        if not preflight(config_path, directory):
            raise SystemExit("602 preflight failed; no source allocated")
    # Stage-local substitutions only. No legacy file or 258 ledger is edited.
    preserved.allocate = allocate
    preserved.code_hashes = lambda: {
        "legacy": LEGACY_HASHES(), "stress602": stage_hashes()}
    codes = []
    for _ in range(args.count):
        directory, code = preserved.launch(
            args.mode, config_path, IMAGE, checkpoint)
        print(directory, flush=True)
        codes.append(code)
    verify_legacy()
    raise SystemExit(0 if all(code == 0 for code in codes) else 1)


if __name__ == "__main__":
    main()
