"""One direct Kimi request preflight, without a source trajectory."""

import json
import os
from pathlib import Path
import sys

sys.path.insert(0, "/opt")
from agent_interp_envs import checkpoint
from agent_interp_envs.providers import create_provider
from tools import get_tools

from common import now, redact, save
from telemetry import instrument


def main():
    output = Path("/opt/preflight-output")
    config = json.loads(Path("/opt/config.yaml").read_text())
    result = {"passed": False, "time": now(), "model_requests": 0}
    try:
        provider = create_provider(
            **checkpoint.provider_kwargs(config), tools=get_tools(config),
            messages=[{"role": "user", "content": "Reply with OK."}])
        instrument(provider, output, {"step": "preflight", "invocations": 0})
        # A preflight uses no automatic retry or model substitution.
        client = provider.client.with_options(max_retries=0, timeout=60)
        result["model_requests"] = 1
        response = client.chat.completions.create(
            model=provider.model, messages=provider.messages,
            max_tokens=256, **provider.kwargs)
        result.update(model_requests=1, returned_model=response.model,
                      passed=response.model == provider.model
                      and bool(response.choices))
    except Exception as error:
        result.update(error_type=type(error).__name__,
                      error=redact(str(error)))
    save(output / "preflight.json", result)
    for path in output.glob("*.json"):
        os.chown(path, int(os.environ["RESULT_UID"]),
                 int(os.environ["RESULT_GID"]))


if __name__ == "__main__":
    main()
