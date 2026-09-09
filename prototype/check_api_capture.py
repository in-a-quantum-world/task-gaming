"""Check API capture with an offline HTTP transport inside the task image."""

import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, "/opt")
sys.path.insert(0, "/opt/prototype")

import httpx
from openai import OpenAI
from agent_interp_envs.providers.fireworks_provider import FireworksProvider
import loop


def response(request):
    """Return a synthetic provider response without a network call."""
    return httpx.Response(200, json={
        "id": "offline-capture-test", "object": "chat.completion",
        "created": 0, "model": "offline-fixture",
        "choices": [{"index": 0, "finish_reason": "stop",
                     "message": {"role": "assistant",
                                 "content": "Offline test response."}}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 4,
                  "total_tokens": 7},
    })


with tempfile.TemporaryDirectory() as directory:
    loop.OUTPUT = Path(directory)
    os.environ["FIREWORKS_API_KEY"] = "offline-test-placeholder"
    provider = FireworksProvider(
        model="offline-fixture", tools=[],
        messages=[{"role": "user", "content": "Offline test."}],
        reasoning_effort="low")
    provider.client.close()
    provider.client = OpenAI(
        api_key="offline-test-placeholder",
        base_url="https://api.fireworks.ai/inference/v1",
        http_client=httpx.Client(transport=httpx.MockTransport(response)))
    loop.instrument_provider(provider)
    result = provider.invoke()
    files = sorted(loop.OUTPUT.glob("*.json"))
    assert len(files) == 2, files
    bodies = "".join(path.read_text() for path in files)
    assert "offline-test-placeholder" not in bodies
    request = json.loads(files[0].read_text())
    reply = json.loads(files[1].read_text())
    assert request["body"]["reasoning_effort"] == "low"
    assert "temperature" not in request["body"]
    assert json.loads(reply["body"])["usage"]["total_tokens"] == 7
    assert result.response == "Offline test response."
    print(json.dumps({"passed": True, "external_requests": 0,
                      "captured_offline_requests": 1,
                      "auth_header_saved": False}))
    provider.client.close()
