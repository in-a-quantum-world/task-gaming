"""One explicit 108-stage source; reuse the unchanged preservation launcher."""

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
RAW = ROOT / "research/data/raw/near100"
SLOT = "near100-source-slot.json"
KEY_FILE = ROOT.parent / "integrated-pilot/.env"
LEGACY_HASHES = preserved.code_hashes


def expected_config():
    config = json.loads((ROOT / "SOURCE_PILOT_CONFIG.yaml").read_text())
    config["task"]["target_errors"] = 108
    return config


def validate_request(mode, count, config, checkpoint):
    if count < 1 or (mode == "source" and count != 1):
        raise ValueError("This stage permits exactly one source")
    if config["task"]["target_errors"] != 108:
        raise ValueError("This stage requires src_108")
    if mode == "source":
        if config != expected_config() or checkpoint is not None:
            raise ValueError("Only target_errors may differ; no continuation")
    elif config["agent"]["provider"] != "mock":
        if mode != "restore-check" or config != expected_config():
            raise ValueError("Only the exact source config may be restored")
        # The preserved loop exits after restore validation, before any invoke.
    if (mode == "restore-check") != (checkpoint is not None):
        raise ValueError("Only an offline restore-check accepts a checkpoint")


def common_git():
    path = Path(preserved.output(["git", "rev-parse", "--git-common-dir"]))
    return path if path.is_absolute() else ROOT / path


def verify_legacy():
    frozen = json.loads((ROOT / "pilot/frozen.json").read_text())
    if LEGACY_HASHES() != frozen["code_sha256"]:
        raise ValueError("The frozen 258 implementation was changed")
    prior = json.loads((ROOT / "research/evidence/near100/prior-state.json")
                       .read_text())
    for slot in prior["old_slots"]:
        if sha256(slot["path"]) != slot["sha256"]:
            raise ValueError("A previous source slot changed")


def stage_hashes():
    paths = sorted((ROOT / "near100").glob("*.py"))
    paths.extend([ROOT / "near100/archive_fixture.json",
                  ROOT / "near100/README.md"])
    paths.extend(ROOT / name for name in (
        "NEAR100_SOURCE_CONFIG.yaml", "NEAR100_SOURCE_PREREG.md",
        "research/SOURCE_CHECKPOINT_RULE.md",
        "research/scripts/review_source_prefix.py"))
    return {str(path.relative_to(ROOT)): sha256(path) for path in paths}


def require_frozen(config_path):
    verify_legacy()
    frozen = json.loads((ROOT / "near100/frozen.json").read_text())
    if (sha256(config_path) != frozen["config_sha256"]
            or stage_hashes() != frozen["stage_code_sha256"]
            or frozen["image_id"] != IMAGE):
        raise ValueError("108 config, code, or image freeze changed")
    for name, digest in frozen["gate_artifacts"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError("108 gate evidence changed")
    gates = json.loads((ROOT / frozen["gates_path"]).read_text())
    if not all(gates[key] for key in (
            "baseline_108", "archive_original_match", "sampling_pass",
            "separate_stage_cap")):
        raise ValueError("108 infrastructure gates have not passed")


def allocate(mode, metadata, raw=RAW):
    raw.mkdir(parents=True, exist_ok=True)
    common = common_git()
    with (common / "near100-source.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        run_id = f"{mode}108-{uuid.uuid4().hex}"
        if mode == "source":
            save(common / SLOT, {
                "run_id": run_id, "allocated_at": now(),
                "stage": "near100-source", "target_errors": 108,
                "policy": "One source; failures consume the slot",
            })
        directory = raw / run_id
        directory.mkdir(mode=0o700)
        save(directory / "run.json", {
            **metadata, "run_id": run_id, "mode": mode, "start": now(),
            "stage": "near100-source", "target_errors": 108,
        })
        shutil.copytree(ROOT / "near100", directory / "stage_implementation",
                        ignore=shutil.ignore_patterns("__pycache__"))
    return directory


def preflight(config_path, directory):
    name = f"near100-preflight-{uuid.uuid4().hex}"
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
            raise ValueError("The 108 source slot is already consumed")
        from dotenv import dotenv_values
        key = dotenv_values(KEY_FILE).get("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("Approved local OpenRouter key is unavailable")
        os.environ["OPENROUTER_API_KEY"] = key
        RAW.mkdir(parents=True, exist_ok=True)
        directory = RAW / f"preflight108-{uuid.uuid4().hex}"
        directory.mkdir(mode=0o700)
        if not preflight(config_path, directory):
            raise SystemExit("108 preflight failed; no source allocated")
    # Stage-local substitutions only. No legacy file or 258 ledger is edited.
    preserved.allocate = allocate
    preserved.code_hashes = lambda: {
        "legacy": LEGACY_HASHES(), "near100": stage_hashes()}
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
