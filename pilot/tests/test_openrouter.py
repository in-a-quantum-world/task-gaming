"""Validate raw trace capture, backend guards, and the zero-retry policy."""

import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock

import httpx
from openai import APIConnectionError, OpenAI, RateLimitError
from agent_interp_envs.providers import create_provider
from agent_interp_envs.checkpoint import provider_kwargs

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from provider import configure
from telemetry import instrument


ROOT = Path(__file__).resolve().parents[2]


class OpenRouterTest(unittest.TestCase):

    def exercise(self, status, backend="Novita"):
        config = json.loads((ROOT / "pilot/configs/first_pilot.json")
                            .read_text())
        calls = []
        native = {"role": "assistant", "content": "OK",
                  "reasoning": "Trace with\n  exact spaces.\n",
                  "reasoning_details": [{"type": "reasoning.text",
                                         "text": "Original trace.\n"}]}

        def respond(request):
            calls.append(request)
            return httpx.Response(status, json={
                "id": "offline", "model": config["agent"]["model"],
                "created": 0, "object": "chat.completion",
                "provider": backend,
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": native}] if status == 200 else [],
                "error": None if status == 200 else {"message": "rate limit"},
            })

        with tempfile.TemporaryDirectory() as temp, \
             mock.patch.dict("os.environ",
                             {"OPENROUTER_API_KEY": "offline-sentinel"}), \
             mock.patch.object(socket.socket, "connect",
                               side_effect=AssertionError("network")):
            provider = create_provider(**provider_kwargs(config), tools=[],
                                       messages=[])
            provider.client.close()
            provider.client = OpenAI(
                api_key="offline-sentinel",
                http_client=httpx.Client(transport=httpx.MockTransport(
                    respond)))
            configure(provider, config)
            path = Path(temp)
            instrument(provider, path, {
                "step": 0, "invocations": 0, "expected_provider": "Novita",
                "expected_model": config["agent"]["model"],
            })
            if status != 200:
                with self.assertRaises(RateLimitError):
                    provider.invoke()
            elif backend != "Novita":
                with self.assertRaises(APIConnectionError) as raised:
                    provider.invoke()
                self.assertIsInstance(raised.exception.__cause__, ValueError)
                self.assertEqual(provider.messages, [])
            else:
                provider.invoke()
                captured = json.loads(
                    (path / "api-assistant-0001.json").read_text())
                self.assertEqual(captured, native)
                raw = json.loads(
                    (path / "api-response-0001.body.json").read_text())
                self.assertEqual(raw["choices"][0]["message"], native)
            self.assertEqual(len(calls), 1)
            provider.client.close()

    def test_exact_native_trace_capture(self):
        self.exercise(200)

    def test_rate_limit_has_no_hidden_retry(self):
        self.exercise(429)

    def test_wrong_backend_stops_before_tool_execution(self):
        self.exercise(200, "Different backend")


if __name__ == "__main__":
    unittest.main()
