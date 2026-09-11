"""Create action-only packets after a separate dataset-wide release gate."""

import hashlib
import hmac
import json

RELEASE_ENABLED = False


def blind_id(sample_id, private_key):
    return hmac.new(private_key, sample_id.encode(), hashlib.sha256).hexdigest()


def primary_packet(steps, identifier):
    """Use only issued native actions, tool results, and state evidence."""
    events = []
    for relative, step in enumerate(steps, 1):
        message = step["native_message"] or {}
        calls = message.get("tool_calls") or []
        actions = []
        for call in calls:
            function = call["function"]
            actions.append({"name": function["name"],
                            "arguments": function["arguments"]})
        results = [{"command": item["command"],
                    "returncode": item["returncode"],
                    "output": item["output"]}
                   for item in step["executions"]]
        # Evidence text can itself disclose history. Never silently rewrite it.
        evidence = {key: step["verified_state"][key] for key in (
            "mypy", "git", "workspace_changes", "verification_status")}
        events.append({"relative_decision": relative,
                       "issued_native_actions": actions,
                       "tool_results": results, "resulting_state": evidence})
    return {"blind_id": identifier, "events": events,
            "primary_label": "UNADJUDICATED",
            "secondary_local_suppression": "UNADJUDICATED"}


def verify_release(release, schedule_sha256):
    if not RELEASE_ENABLED:
        raise PermissionError("All scientific outcomes remain quarantined")
    if (release["collection_complete"] is not True
            or release["explicit_researcher_release"] is not True
            or not release["researcher"] or not release["released_at_utc"]
            or release["schedule_sha256"] != schedule_sha256
            or release["allocated_samples"] != 32
            or release["operational_receipts"] != 32):
        raise PermissionError("Dataset-wide release gate is incomplete")


def export_packets(input_path, output_path, release, schedule_sha256, key):
    """Read normalized, custodian-verified evidence only after release."""
    verify_release(release, schedule_sha256)
    data = json.loads(input_path.read_text())
    packets, private_map = [], {}
    for record in data:
        identifier = blind_id(record["sample_id"], key)
        private_map[identifier] = record["sample_id"]
        packets.append(primary_packet(record["steps"], identifier))
    packets.sort(key=lambda row: row["blind_id"])
    output_path.mkdir(mode=0o700)
    with (output_path / "primary_packets.json").open("x") as stream:
        json.dump(packets, stream, indent=2, ensure_ascii=False)
    # Store the key/map separately from the graders' packet directory.
    return private_map


if __name__ == "__main__":
    raise PermissionError("Outcome export is locked until explicit release")
