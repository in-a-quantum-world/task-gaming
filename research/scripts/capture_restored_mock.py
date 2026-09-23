#!/usr/bin/env python3
"""Prepare one synthetic resume and capture it before any model invocation.

Run only inside the precommit image with a mock config. The source checkpoint
mount is /opt/source-checkpoint, so entrypoint setup cannot resume implicitly.
"""

import copy
import inspect
import json
import os
from pathlib import Path
import runpy
import sys
from unittest import mock

import yaml

from agent_interp_envs.tool_calling import _agent_env, run_command

sys.path.insert(0, "/opt")
sys.path.insert(0, "/opt/research-scripts")

import validate_state_equivalence as validator


def main() -> int:
    config = yaml.safe_load(Path("/opt/config.yaml").read_text())
    if config["agent"]["provider"] != "mock":
        raise ValueError("Only synthetic mock checkpoints are allowed")
    setup_config = copy.deepcopy(config)
    setup_config["agent"]["max_steps"] = 0
    with mock.patch("agent_interp_envs.config.load_config",
                    return_value=setup_config):
        try:
            runpy.run_path("/opt/entrypoint.py", run_name="__main__")
        except SystemExit as error:
            if error.code != 0:
                raise
    from states import restore
    from tools import get_tools
    state, provider = restore(config, Path("/opt/source-checkpoint"))
    runtime = {
        "model": provider.model, "provider": "mock",
        "request_kwargs": {"offline_mock": True}, "tools": get_tools(config),
        "agent_cwd": os.getcwd(), "agent_environment": _agent_env(),
        "image_id": os.environ["AUDIT_IMAGE_ID"],
        "command_timeout_seconds": inspect.signature(
            run_command,
        ).parameters["timeout"].default,
    }
    Path("/opt/runtime.json").write_text(json.dumps(runtime))
    state.to_json("/opt/pre-invoke-state.json")
    Path("/opt/pre-invoke-messages.json").write_text(provider.dump_history())
    sys.argv = [
        "validate_state_equivalence.py", "capture", "--workspace", "/agent",
        "--config", "/opt/config.yaml", "--state", "/opt/pre-invoke-state.json",
        "--messages", "/opt/pre-invoke-messages.json",
        "--runtime", "/opt/runtime.json",
        "--reference-config", "/opt/task/pyproject.toml",
        "--output", "/opt/validation.json",
    ]
    return validator.main()


if __name__ == "__main__":
    raise SystemExit(main())
