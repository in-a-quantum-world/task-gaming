"""Apply the same explicit pilot request policy after either construction."""

import copy
from types import MethodType


MODEL = "moonshotai/kimi-k2-thinking"
BACKEND = "novita/bf16"
PROVIDER_NAME = "Novita"


def configure(provider, config):
    """Configure the reviewed OpenRouter adapter without editing its code."""
    if config["agent"]["provider"] == "mock":
        return provider
    if (config["agent"]["provider"] != "openrouter"
            or provider.model != MODEL):
        raise ValueError("Only the frozen OpenRouter Kimi route is permitted")
    policy = config["pilot"]
    provider.kwargs["extra_body"]["reasoning"] = copy.deepcopy(
        policy["reasoning"])
    provider.kwargs["max_tokens"] = policy["max_output_tokens"]
    # The selected endpoint does not advertise this request parameter.
    provider.kwargs.pop("parallel_tool_calls", None)
    if provider.kwargs.get("tools"):
        provider.kwargs["tool_choice"] = "auto"
    provider.client = provider.client.with_options(
        max_retries=0, timeout=policy["request_timeout_seconds"])
    # The upstream adapter also has an outer tenacity retry decorator.
    provider.invoke = MethodType(type(provider).invoke.__wrapped__, provider)
    return provider
