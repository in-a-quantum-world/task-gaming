"""One direct Kimi request preflight, without a source trajectory."""

import json
import os
from pathlib import Path
import sys

sys.path.insert(0, "/opt")
from agent_interp_envs import checkpoint
from agent_interp_envs.providers import create_provider
from agent_interp_envs.types import ToolResult
from tools import get_tools

from common import now, redact, save
from provider import configure, PROVIDER_NAME
from telemetry import instrument


def main():
    output = Path("/opt/preflight-output")
    config = json.loads(Path("/opt/config.yaml").read_text())
    result = {"passed": False, "time": now(), "model_requests": 0}
    try:
        provider = configure(create_provider(
            **checkpoint.provider_kwargs(config), tools=get_tools(config),
            messages=[{"role": "user", "content": (
                "This is a synthetic API preflight. Use execute_command once "
                "with command printf PILOT_PREFLIGHT_OK. After the synthetic "
                "tool result, reply PREFLIGHT_OK with no tool call.")}]),
            config)
        context = {"step": 0, "invocations": 0,
                   "expected_model": provider.model,
                   "expected_provider": PROVIDER_NAME}
        instrument(provider, output, context)
        save(output / "settings.json", provider.kwargs)
        result["model_requests"] = 1
        response = provider.invoke()
        if (not response.tool_calls or len(response.tool_calls) != 1
                or response.tool_calls[0].name != "execute_command"):
            raise ValueError("Preflight requires one native tool call")
        native = json.loads((output / "api-assistant-0001.json").read_text())
        if not native.get("reasoning_details") and not native.get("reasoning"):
            raise ValueError("No visible reasoning returned")
        tool = response.tool_calls[0]
        provider.add_tool_result(ToolResult(
            id=tool.id, name=tool.name, content="PILOT_PREFLIGHT_OK"))
        context["step"] = 1
        result["model_requests"] = 2
        second = provider.invoke()
        request = json.loads((output / "api-request-0002.json").read_text())
        replayed = request["body"]["messages"][1]
        exact = all(replayed.get(field) == native.get(field)
                    for field in ("content", "reasoning", "reasoning_details"))
        result.update(passed=exact and bool(second.response)
                      and not second.tool_calls,
                      visible_reasoning_replayed_exactly=exact,
                      returned_provider=PROVIDER_NAME,
                      returned_model=provider.model,
                      actual_tool_execution=False,
                      caveat="Server use of prior reasoning is not observable")
    except Exception as error:
        result.update(error_type=type(error).__name__,
                      error=redact(str(error)))
    save(output / "preflight.json", result)
    for path in output.glob("*.json"):
        os.chown(path, int(os.environ["RESULT_UID"]),
                 int(os.environ["RESULT_GID"]))


if __name__ == "__main__":
    main()
