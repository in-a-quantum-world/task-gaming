#!/usr/bin/env python3
"""Run selected upstream tests with all socket connections disabled."""

import argparse
import os
from pathlib import Path
import socket
from unittest import mock

import pytest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True)
    args = parser.parse_args()
    tests = args.upstream / "tests"
    paths = [
        str(tests / "src/test_checkpoint.py"),
        str(tests / "src/test_mock_provider.py"),
        str(tests / "src/test_openrouter_provider_preferences.py")
        + "::TestProviderPreferencesConstruction",
        str(tests / "src/test_openrouter_provider_preferences.py")
        + "::TestCreateProviderFactory",
        str(tests / "scripts/test_resume_cli_overrides.py"),
        str(tests / "environments/test_privilege_separation.py"),
    ]
    offline_env = {
        "OPENROUTER_API_KEY": "offline-test-placeholder",
        "PYTHON_DOTENV_DISABLED": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    }
    with mock.patch.dict(os.environ, offline_env), mock.patch.object(
        socket.socket, "connect", side_effect=RuntimeError(
            "Network disabled for offline audit tests",
        ),
    ):
        return pytest.main(["-q", "-p", "no:cacheprovider", *paths])


if __name__ == "__main__":
    raise SystemExit(main())
