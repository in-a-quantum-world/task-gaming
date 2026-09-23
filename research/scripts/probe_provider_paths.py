#!/usr/bin/env python3
"""Compare actual provider-construction kwargs without API access."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
from unittest import mock

from agent_interp_envs import checkpoint


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    environment = args.upstream / "environments/precommit_hook"
    sys.path.insert(0, str(environment.resolve()))
    spec = importlib.util.spec_from_file_location("precommit_agent",
                                                  environment / "agent.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = {
        "agent": {
            "provider": "fireworks", "model": "offline-constructor-probe",
            "max_steps": 0, "reasoning_effort": "low", "temperature": 0.7,
            "top_p": 0.8,
        },
        "task": {"tools": ["execute_command"]},
        "prompts": {"system_prompt": "system", "user_prompt": "user"},
    }
    captured = {}

    def factory(**kwargs):
        captured.update(kwargs)
        return mock.Mock()

    with mock.patch.object(socket.socket, "connect", side_effect=RuntimeError(
        "Network is disabled for the constructor probe",
    )), mock.patch.dict(os.environ, {"PYTHON_DOTENV_DISABLED": "1"}):
        with mock.patch.object(module, "load_config", return_value=config), \
             mock.patch.object(module, "init_fs_tracking"), \
             mock.patch.object(module, "print_final_results"), \
             mock.patch.object(module, "create_provider",
                               side_effect=factory), \
             mock.patch.object(module, "Path") as fake_path:
            fake_path.return_value.exists.return_value = False
            module.main()
        fresh = dict(captured)
        captured.clear()
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / "messages.json").write_text(json.dumps(fresh["messages"]))
            with mock.patch.object(checkpoint, "create_provider",
                                   side_effect=factory):
                checkpoint.restore_provider(config, folder, fresh["tools"])
        resumed = dict(captured)
    record = {
        "fresh_keys": sorted(fresh), "resume_keys": sorted(resumed),
        "fresh_temperature": fresh.get("temperature"),
        "resume_temperature": resumed.get("temperature"),
        "fresh_top_p": fresh.get("top_p"),
        "resume_top_p": resumed.get("top_p"),
        "model_calls": 0,
    }
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
