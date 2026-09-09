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

from agent_interp_envs import checkpoint


ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = Path(os.environ.get(
    "PILOT_UPSTREAM", ROOT / "upstream/agent-interp-envs"))
ENVIRONMENT = UPSTREAM / "environments/precommit_hook"
sys.path.insert(0, str(ENVIRONMENT))


class SamplingTest(unittest.TestCase):

    def test_fresh_and_resume_kwargs_are_identical(self):
        spec = importlib.util.spec_from_file_location(
            "sampling_agent", ENVIRONMENT / "agent.py")
        agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent)
        for provider, preferences in (
                ("fireworks", None),
                ("openrouter", {"only": ["Fireworks"],
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
