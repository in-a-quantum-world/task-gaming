"""Exercise actual fresh and shared resume provider construction."""

import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock

import httpx
from openai import OpenAI
from agent_interp_envs import checkpoint
from agent_interp_envs.providers import create_provider


ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = Path(os.environ.get(
    "PILOT_UPSTREAM", ROOT / "upstream/agent-interp-envs"))
ENVIRONMENT = UPSTREAM / "environments/precommit_hook"
sys.path.insert(0, str(ENVIRONMENT))
sys.path.insert(0, str(ROOT / "pilot"))
from provider import configure


class SamplingTest(unittest.TestCase):

    def test_actual_openrouter_fresh_resume_wire_settings(self):
        config = json.loads((ROOT / "pilot/configs/first_pilot.json")
                            .read_text())
        config["agent"]["max_steps"] = 0
        spec = importlib.util.spec_from_file_location(
            "wire_agent", ENVIRONMENT / "agent.py")
        agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent)
        providers, requests, constructors = [], [], []

        def respond(request):
            requests.append(json.loads(request.content))
            return httpx.Response(200, json={
                "id": "offline", "model": config["agent"]["model"],
                "created": 0, "object": "chat.completion",
                "provider": "Novita", "choices": [{
                    "index": 0, "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "OK",
                                "reasoning": "Exact visible trace.\n",
                                "reasoning_details": [{
                                    "type": "reasoning.text",
                                    "text": "Exact visible trace.\n"}]}}],
            })

        def factory(**kwargs):
            constructors.append({k: v for k, v in kwargs.items()
                                 if k != "messages"})
            provider = create_provider(**kwargs)
            provider.client.close()
            provider.client = OpenAI(
                api_key="offline-sentinel",
                base_url="https://openrouter.ai/api/v1",
                http_client=httpx.Client(transport=httpx.MockTransport(
                    respond)))
            providers.append(configure(provider, config))
            return provider

        with mock.patch.dict(os.environ,
                             {"OPENROUTER_API_KEY": "offline-sentinel"}), \
             mock.patch.object(socket.socket, "connect",
                               side_effect=AssertionError("network")), \
             mock.patch.object(agent, "load_config", return_value=config), \
             mock.patch.object(agent, "init_fs_tracking"), \
             mock.patch.object(agent, "print_final_results"), \
             mock.patch.object(agent, "create_provider", factory), \
             mock.patch.object(agent, "Path") as fake_path:
            fake_path.return_value.exists.return_value = False
            agent.main()
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp)
                (path / "messages.json").write_text(
                    json.dumps(providers[0].messages))
                with mock.patch.object(checkpoint, "create_provider", factory):
                    checkpoint.restore_provider(
                        config, path, agent.get_tools(config))
            for provider in providers:
                self.assertEqual(provider.client.max_retries, 0)
                provider.invoke()
                provider.client.close()
        self.assertEqual(constructors[0], constructors[1])
        self.assertEqual(requests[0], requests[1])
        body = requests[0]
        self.assertEqual(body["model"], config["agent"]["model"])
        self.assertEqual(body["provider"],
                         config["agent"]["provider_preferences"])
        self.assertEqual(body["reasoning"], config["pilot"]["reasoning"])
        self.assertEqual(body["temperature"], 1.0)
        self.assertEqual(body["top_p"], 1.0)
        self.assertEqual(body["tools"], agent.get_tools(config))
        self.assertEqual(body["max_tokens"], 16384)
        self.assertNotIn("effort", body["reasoning"])
        self.assertNotIn("parallel_tool_calls", body)

    def test_fresh_and_resume_kwargs_are_identical(self):
        spec = importlib.util.spec_from_file_location(
            "sampling_agent", ENVIRONMENT / "agent.py")
        agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent)
        for provider, preferences in (
                ("fireworks", None),
                ("openrouter", {"only": ["novita/bf16"],
                                "allow_fallbacks": False})):
            with self.subTest(provider=provider):
                config = {
                    "agent": {
                        "provider": provider, "model": "offline-test",
                        "max_steps": 0, "reasoning_effort": "high",
                        "temperature": 0.73, "top_p": 0.91,
                        "provider_preferences": preferences,
                    },
                    "task": {"tools": ["execute_command"]},
                    "prompts": {"system_prompt": "s", "user_prompt": "u"},
                }
                factory = mock.Mock(return_value=mock.Mock())
                with mock.patch.object(socket.socket, "connect",
                                       side_effect=AssertionError("network")), \
                     mock.patch.object(agent, "load_config",
                                       return_value=config), \
                     mock.patch.object(agent, "init_fs_tracking"), \
                     mock.patch.object(agent, "print_final_results"), \
                     mock.patch.object(agent, "create_provider", factory), \
                     mock.patch.object(agent, "Path") as fake_path:
                    fake_path.return_value.exists.return_value = False
                    agent.main()
                    fresh = factory.call_args.kwargs
                    with tempfile.TemporaryDirectory() as temp:
                        path = Path(temp)
                        (path / "messages.json").write_text(
                            json.dumps(fresh["messages"]))
                        with mock.patch.object(checkpoint, "create_provider",
                                               factory):
                            checkpoint.restore_provider(
                                config, path, fresh["tools"])
                    self.assertEqual(fresh, factory.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
