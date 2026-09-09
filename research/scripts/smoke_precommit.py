#!/usr/bin/env python3
"""Run one credential-free mock smoke test and preserve its full artifacts."""

import argparse
import json
from pathlib import Path
import subprocess
import time

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    if config["agent"]["provider"] != "mock":
        parser.error("This script accepts only provider: mock")
    if config["agent"]["max_steps"] > 3:
        parser.error("This smoke test permits at most three mock steps")
    args.output.mkdir(parents=True, exist_ok=False)
    image_id = subprocess.check_output([
        "docker", "image", "inspect", "--format", "{{.Id}}", args.image,
    ], text=True).strip()
    container = subprocess.check_output([
        "docker", "create", "--network", "none",
        "-v", f"{args.config.resolve()}:/opt/config.yaml:ro", image_id,
    ], text=True).strip()
    result = {"image_id": image_id, "container": container, "model_calls": 0}
    started = time.monotonic()
    try:
        with (args.output / "rollout.log").open("w") as log:
            run = subprocess.run(
                ["docker", "start", "-a", container], stdout=log,
                stderr=subprocess.STDOUT, timeout=120,
            )
        result["returncode"] = run.returncode
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", container], check=False)
        result.update(returncode=None, timeout=True)
    finally:
        for name, source in [("checkpoints", "/opt/output"),
                             ("workspace", "/agent")]:
            copied = subprocess.run(
                ["docker", "cp", f"{container}:{source}",
                 str(args.output / name)], capture_output=True, text=True,
            )
            result[f"copy_{name}"] = copied.returncode
        logs = subprocess.run(
            ["docker", "logs", container], capture_output=True, text=True,
        )
        (args.output / "container.log").write_text(logs.stdout + logs.stderr)
        subprocess.run(["docker", "rm", "-f", container], check=True,
                       capture_output=True)
    result["wall_seconds"] = round(time.monotonic() - started, 3)
    text = json.dumps(result, indent=2) + "\n"
    (args.output / "result.json").write_text(text)
    print(json.dumps(result, indent=2))
    return 0 if result["returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
