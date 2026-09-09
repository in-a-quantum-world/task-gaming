"""Run upstream setup and substitute only the instrumented agent process."""

import os
import runpy
import subprocess


original_run = subprocess.run


def launch_loop(command, *args, **kwargs):
    if isinstance(command, list) and "/opt/agent.py" in command:
        command = list(command)
        command[command.index("/opt/agent.py")] = "/opt/pilot/loop.py"
    return original_run(command, *args, **kwargs)


if __name__ == "__main__":
    os.umask(0o077)
    subprocess.run = launch_loop
    runpy.run_path("/opt/entrypoint.py", run_name="__main__")
