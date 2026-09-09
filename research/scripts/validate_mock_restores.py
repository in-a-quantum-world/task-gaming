#!/usr/bin/env python3
"""Compare two prepared mock restores without continuation model calls."""

import argparse
import json
from pathlib import Path
import subprocess

import yaml

from validate_state_equivalence import compare


def prepare(image: str, config: Path, checkpoint: Path, output: Path) -> dict:
    """Run the container-only capture helper and retain failures."""
    output.mkdir()
    scripts = Path(__file__).resolve().parent
    container = subprocess.check_output([
        "docker", "create", "--network", "none",
        "-e", f"AUDIT_IMAGE_ID={image}",
        "-v", f"{config.resolve()}:/opt/config.yaml:ro",
        "-v", f"{checkpoint.resolve()}:/opt/source-checkpoint:ro",
        "-v", f"{scripts}:/opt/research-scripts:ro",
        image, "python", "/opt/research-scripts/capture_restored_mock.py",
    ], text=True).strip()
    record = {"container": container, "image_id": image, "model_calls": 0}
    try:
        with (output / "capture.log").open("w") as log:
            run = subprocess.run(
                ["docker", "start", "-a", container], stdout=log,
                stderr=subprocess.STDOUT, timeout=90,
            )
        record["exit_code"] = run.returncode
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", container], capture_output=True)
        record.update(exit_code=None, timeout=True)
    finally:
        copied = subprocess.run([
            "docker", "cp", f"{container}:/opt/validation.json",
            str(output / "validation.json"),
        ], capture_output=True, text=True)
        record["capture_copy_exit_code"] = copied.returncode
        if copied.returncode:
            record["copy_error"] = copied.stderr
        logs = subprocess.run(["docker", "logs", container],
                              capture_output=True, text=True)
        (output / "container.log").write_text(logs.stdout + logs.stderr)
        subprocess.run(["docker", "rm", "-f", container], check=True,
                       capture_output=True)
    (output / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    if config["agent"]["provider"] != "mock":
        parser.error("This utility accepts only provider: mock")
    for name in ["state.json", "messages.json", "fs/manifest.json"]:
        if not (args.checkpoint / name).is_file():
            parser.error(f"Checkpoint is missing {name}")
    args.output.mkdir(parents=True, exist_ok=False)
    image = subprocess.check_output([
        "docker", "image", "inspect", "--format", "{{.Id}}", args.image,
    ], text=True).strip()
    records = []
    for label in ["left", "right"]:
        records.append(prepare(image, args.config, args.checkpoint,
                               args.output / label))
    if any(r["capture_copy_exit_code"] for r in records):
        print("A capture failed; inspect retained logs.")
        return 2
    left = json.loads((args.output / "left/validation.json").read_text())
    right = json.loads((args.output / "right/validation.json").read_text())
    report = compare(left, right)
    (args.output / "comparison.json").write_text(
        json.dumps(report, indent=2) + "\n",
    )
    print(json.dumps(report, indent=2))
    return {"equal_on_recorded_fields": 0, "different": 1,
            "inconclusive": 2}[report["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
