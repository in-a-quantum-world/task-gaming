"""Intercept the adapter's real HTTP serialization without network access."""

import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock

import httpx
from openai import OpenAI
from agent_interp_envs.providers.fireworks_provider import FireworksProvider

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from telemetry import instrument


class TelemetryTest(unittest.TestCase):

    def test_wire_settings_native_response_and_credential_redaction(self):
        key = "synthetic-test-secret-never-real"

        def respond(request):
            self.assertEqual(request.headers["authorization"], f"Bearer {key}")
            return httpx.Response(200, headers={"x-request-id": "fixture-id"},
                                  json={
                "id": "fixture", "model": "frozen-kimi", "created": 0,
                "object": "chat.completion",
                "choices": [{"index": 0, "finish_reason": "stop", "message": {
                    "role": "assistant", "content": key,
                    "reasoning_content": "native reasoning preserved"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 3,
                          "total_tokens": 5},
            })

        with tempfile.TemporaryDirectory() as temp, \
             mock.patch.dict("os.environ", {"FIREWORKS_API_KEY": key}), \
             mock.patch.object(socket.socket, "connect",
                               side_effect=AssertionError("network")):
            provider = FireworksProvider(
                "frozen-kimi", [{"role": "user", "content": "fixture"}], [],
                temperature=0.73, top_p=0.91, reasoning_effort="high")
            provider.client.close()
            provider.client = OpenAI(
                api_key=key, base_url="https://api.fireworks.ai/inference/v1",
                http_client=httpx.Client(transport=httpx.MockTransport(respond)))
            path = Path(temp)
            instrument(provider, path, {"step": 0, "invocations": 0})
            provider.invoke()
            request = json.loads((path / "api-request-0001.json").read_text())
            self.assertEqual(request["body"]["temperature"], 0.73)
            self.assertEqual(request["body"]["top_p"], 0.91)
            self.assertEqual(request["body"]["reasoning_effort"], "high")
            native = json.loads((path / "native-000.json").read_text())
            self.assertEqual(native["message"]["reasoning_content"],
                             "native reasoning preserved")
            for artifact in path.glob("*.json"):
                self.assertNotIn(key, artifact.read_text())
            provider.client.close()


if __name__ == "__main__":
    unittest.main()
