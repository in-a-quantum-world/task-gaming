"""Use the frozen offline grader with a 108-aware original-file inventory."""

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pilot"))
import grade
from common import save
from run_stage import IMAGE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    original = subprocess.run

    def verify_108(command, *positional, **keywords):
        if isinstance(command, list) and "/opt/pilot/verify_outcome.py" in command:
            command = list(command)
            index = command.index(IMAGE)
            command[index:index] = [
                "-v", f"{ROOT / 'near100/verify_outcome.py'}:"
                "/opt/pilot/verify_outcome.py:ro"]
        return original(command, *positional, **keywords)

    subprocess.run = verify_108
    try:
        result = grade.grade_run(args.run.resolve(), IMAGE,
                                 args.output.resolve().with_suffix(".verification"))
    finally:
        subprocess.run = original
    save(args.output, result)


if __name__ == "__main__":
    main()
