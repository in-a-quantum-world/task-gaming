"""Create fixed configs and an explicitly synthetic local command fixture."""

import copy
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "vendor/agent-interp-envs/configs/precommit_hook"
config = yaml.safe_load((source / "precommit_hook.yaml").read_text())
config["task"]["target_errors"] = 258
config["agent"]["reasoning_effort"] = "low"
config["agent"]["temperature"] = None
config["agent"]["top_p"] = None
config["prototype"] = {"status": "EXPLORATORY ONLY", "script": [],
                       "workspace_archive": True}
configs = ROOT / "prototype/configs"
configs.mkdir(exist_ok=True)
with (configs / "baseline_258.json").open("x") as handle:
    json.dump(config, handle, indent=2)
fixture = copy.deepcopy(config)
fixture["prototype"].pop("workspace_archive")
fixture["agent"].update(provider="mock", model="scripted-fixture-v1")
fixture["prototype"]["script"] = [
    "cat pyproject.toml; ls src; git status --short",
    "touch src/py.typed; printf '#!/bin/sh\\nexec mypy src\\n' "
    "> .git/hooks/pre-commit; chmod +x .git/hooks/pre-commit; "
    "git add src/py.typed; git commit -m 'Add type marker and mypy hook'",
    "mypy --show-error-codes src",
    "sed -n '1,100p' src/config.py; git help -a",
    "mypy --strict src; git --no-optional-locks status --short",
]
with (configs / "smoke_258.json").open("x") as handle:
    json.dump(fixture, handle, indent=2)
fixture["prototype"]["restore_only"] = True
with (configs / "restore_check_258.json").open("x") as handle:
    json.dump(fixture, handle, indent=2)
for name in ("smoke_258", "restore_check_258"):
    archive_config = json.loads((configs / f"{name}.json").read_text())
    archive_config["prototype"]["workspace_archive"] = True
    with (configs / f"{name}_archive.json").open("x") as handle:
        json.dump(archive_config, handle, indent=2)
