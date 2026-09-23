#!/usr/bin/env python3
"""Measure image source variants without model calls or source edits."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def main() -> None:
    task = Path("/opt/task")
    result = {"variants": []}
    result["python"] = sys.version
    result["mypy"] = subprocess.check_output(
        [sys.executable, "-m", "mypy", "--version"], text=True,
    ).strip()
    for variant in sorted(task.glob("src_*")):
        with tempfile.TemporaryDirectory(prefix="variant-probe-") as temp:
            workspace = Path(temp)
            shutil.copytree(variant, workspace / "src")
            shutil.copy(task / "pyproject.toml", workspace / "pyproject.toml")
            check = subprocess.run([
                sys.executable, "-m", "mypy", "src", "--strict",
                "--no-incremental", "--cache-dir", "/dev/null",
            ], cwd=workspace, capture_output=True, text=True, timeout=60)
            errors = [line for line in check.stdout.splitlines()
                      if ": error:" in line]
            summary = re.search(r"Found (\d+) errors?", check.stdout)
            count = int(summary[1]) if summary else (
                0 if check.returncode == 0 else None
            )
            result["variants"].append({
                "source": variant.name, "target": int(variant.name[4:]),
                "observed_errors": count, "error_lines": errors,
                "exit_code": check.returncode, "stderr": check.stderr,
                "stdout": check.stdout,
            })
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
