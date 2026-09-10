"""Capture actual request bodies and native model messages before recovery."""

import copy
import json
import time

from common import now, redact, save


def instrument(provider, output, context):
    client = getattr(provider, "client", None)
    if client is not None:
        counter = 0

        def request_hook(request):
            nonlocal counter
            counter += 1
            request.extensions["pilot_request_number"] = counter
            request.extensions["pilot_started"] = time.monotonic()
            save(output / f"api-request-{counter:04d}.json", {
                "time": now(), "step": context.get("step"),
                "method": request.method,
                "url": str(request.url.copy_with(query=None)),
                "body": json.loads(redact(request.content.decode())),
            })

        def response_hook(response):
            number = response.request.extensions["pilot_request_number"]
            response.read()
            body = redact(response.text)
            with (output / f"api-response-{number:04d}.body.json").open(
                    "x", encoding="utf-8", newline="") as stream:
                stream.write(body)
            save(output / f"api-response-{number:04d}.json", {
                "time": now(), "step": context.get("step"),
                "status_code": response.status_code,
                "request_id": response.headers.get("x-request-id"),
                "elapsed_seconds": (time.monotonic()
                                    - response.request.extensions[
                                        "pilot_started"]),
                "body": body,
            })
            if response.status_code == 200:
                data = json.loads(body)
                if data.get("choices"):
                    save(output / f"api-assistant-{number:04d}.json",
                         data["choices"][0]["message"])
                    for field in ("model", "provider"):
                        expected = context.get(f"expected_{field}")
                        if expected and data.get(field) != expected:
                            save(output / "routing_violation.json", {
                                "field": field, "expected": expected,
                                "returned": data.get(field),
                                "request_number": number,
                            })
                            raise ValueError(f"Unexpected response {field}")

        client._client.event_hooks["request"].append(request_hook)
        client._client.event_hooks["response"].append(response_hook)
    original_invoke = provider.invoke

    def invoke():
        context["invocations"] += 1
        result = original_invoke()
        context["native_message"] = copy.deepcopy(provider.messages[-1])
        save(output / f"native-{context['step']:03d}.json", {
            "step": context["step"], "time": now(),
            "message": json.loads(redact(json.dumps(
                context["native_message"]))),
        })
        return result

    provider.invoke = invoke
