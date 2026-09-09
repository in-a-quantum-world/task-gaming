"""Run the original entrypoint with the prototype loop as its child."""

import os
from pathlib import Path
import runpy
import subprocess


original_run = subprocess.run


def launch_loop(command, *args, **kwargs):
    """Replace only the original agent subprocess target."""
    if isinstance(command, list) and "/opt/agent.py" in command:
        command = list(command)
        command[command.index("/opt/agent.py")] = "/opt/prototype/loop.py"
    return original_run(command, *args, **kwargs)


subprocess.run = launch_loop
try:
    runpy.run_path("/opt/entrypoint.py", run_name="__main__")
finally:
    # Output ownership does not affect the agent workspace.
    for root, dirs, files in os.walk("/opt/output"):
        for path in [Path(root), *(Path(root) / f for f in files)]:
            os.chown(path, int(os.environ["RESULT_UID"]),
                     int(os.environ["RESULT_GID"]))
