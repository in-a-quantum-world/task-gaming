"""Build gate receipts only from identified synthetic validation runs."""

from contract import SOURCE_FILES, read, sha, validate_request
from freeze import implementation_hashes, save_new


def record_offline_gate(root, directory, row, source, mode, destination):
    if mode not in ("restore-check", "offline-wire"):
        raise PermissionError("Paid outcome is not an offline gate")
    metadata = read(directory / "run.json")
    if metadata["synthetic"] is not True or metadata["mode"] != mode:
        raise ValueError("Synthetic gate metadata differs")
    manifest_path = directory / "data/pre_invocation_manifest.json"
    manifest = read(manifest_path)
    if (manifest["mode"] != mode
            or manifest["provider_invocations_before_manifest"] != 0
            or manifest["remaining_decisions"] != source["remaining_decisions"]
            or manifest["next_step"] != source["first_continuation_step"]
            or manifest["model_cannot_read_study_artifacts"] is not True):
        raise ValueError("Pre-invocation offline gate differs")
    evidence = {"pre_invocation_manifest": sha(manifest_path)}
    requests = sorted((directory / "data").glob("api-request-*.json"))
    if mode == "restore-check" and requests:
        raise ValueError("Zero-request restore gate issued a request")
    if mode == "offline-wire":
        if len(requests) != 1:
            raise ValueError("Wire fixture must make exactly one mock request")
        request = read(requests[0])
        validate_request(request["body"], manifest["contract"], True,
                         request["step"])
        evidence["mock_request"] = sha(requests[0])
    kind = "restore" if mode == "restore-check" else "wire"
    save_new(destination / f"{directory.name}-{kind}-gate.json", {
        "passed": True, "real_model_calls": 0,
        "checkpoint": row["checkpoint"], "condition_id": row["condition_id"],
        "condition_file_sha256": row["condition_file_sha256"],
        "source_contract_sha256": sha(root / SOURCE_FILES[
            row["checkpoint"]][0]),
        "implementation_sha256": implementation_hashes(root),
        "config_sha256": row["config_sha256"],
        "remaining_decisions": source["remaining_decisions"],
        "image_id": source["image_id"], "kind": kind,
        "raw_synthetic_directory": str(directory), "evidence_sha256": evidence,
    })
