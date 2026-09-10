> 2026-09-10 amendment: the user authorized Kimi through OpenRouter,
> pinned to novita/bf16 with no fallback. SOURCE_PILOT_CONFIG.yaml and
> SOURCE_PILOT_PREREG.md supersede historical Fireworks access/config claims.
> The earlier audit/prototype reconciliation and archive evidence remain valid
> for their recorded image; new-image validation is required before source use.

# Infrastructure patches

Status: exploratory infrastructure; no paid model trajectory.

## Fresh and resume construction

Framework base: `56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb`.
Patch: `pilot/patches/fresh-provider-kwargs.patch`.
Target: `environments/precommit_hook/agent.py` in the isolated experiment copy.

The fresh path previously listed provider fields by hand. It omitted
`temperature` and `top_p`. The shared resume path already uses `provider_kwargs`.
The patch makes fresh construction use that same helper. Provider code is intact.
This also preserves applicable provider preferences through the same path.

`pilot/tests/test_sampling.py` intercepts the real fresh `main()` and the shared
`restore_provider()`. It compares complete constructor kwargs, including tools
and initial messages. It tests Fireworks and explicit OpenRouter preferences.
Socket connections are blocked. No credential is required.

- Before patch: two subtest failures, one for each provider.
- After patch: both pass with identical constructor kwargs.
- Evidence: `evidence/integration/sampling-unpatched.log` and `sampling-patched.log`.

The runner executes that patched upstream loop. It does not maintain a separate
fresh-generation policy. The telemetry test also exercises actual SDK request
serialization through an offline HTTP transport. Server normalization is unknown.

## Archive and validator supplement

The full `/agent` archive includes unchanged baseline Git files and excluded
caches. It is mandatory at every completed decision boundary.
The wrapper stores the original inventory before any extraction. It compares
the source again after archive creation and after independent diagnostic probes.
It restores nanosecond timestamps from the original inventory after tar extraction.
This avoids float-rounding loss in Python tar metadata.

Path checks reject escape paths and extraction through symlink parents.
External symlinks and special files stop restoration for explicit design review.
The archive preserves valid internal file and directory symlinks and ownership.
Full-tree capture avoids the upstream stat gate and inherited-manifest omission.

Two initial integrated restores passed workspace validation but failed the extra
external gate. The comparator compared JSON lists with in-memory package tuples.
Both saved external inventories matched. The repair compares persisted forms.
Both failed attempts remain in the raw dataset.

A bypass fixture exposed a defunct Git child after a commit. The initial process
gate treated every PID as active and stopped after preservation. The revised
inventory records process state. It rejects active processes and excludes defunct
PIDs from the equality claim. A subsequent fixture confirms Git state `Z`.
This does not extend the guarantee to kernel or process state.

## Preservation and metadata

`pilot/run.py` allocates exactly the requested trajectory count. Source mode
requires count 1 and consumes one persistent slot before container launch.
The ledger resides in Git's common directory. Raw output paths cannot reset it.
There is no slow-survivor deletion or automatic sample replacement.

The host preserves all completed checkpoints, errors, and timeout records.
It copies the final workspace before container removal. Failed recovery leaves
the container for inspection. Original metadata survives in workspace tar files.
The runner seals ordinary artifact writes and records SHA-256 manifests.
This is tamper evidence; it is not an immutable storage service.

Native model replies precede harness recovery in separate artifacts. HTTP hooks
record actual request bodies and response bodies, including usage when supplied.
They exclude authentication headers and redact configured secret values.
The agent shell receives the upstream sanitized environment.

One image-build attempt used a local sha256 value in Dockerfile `FROM`. Docker
interpreted it as a registry image name and failed. The successful build uses
the existing base tag after verification of its immutable image ID.
No dependency installation or provider-internal patch was needed.

## OpenRouter source route (2026-09-10)

The actual upstream fresh/resume patch is unchanged. The new regression invokes
fresh main and shared restore_provider, then intercepts actual SDK serialization.
It compares model, provider, backend routing, reasoning, temperature, top_p,
complete tool definitions, token cap, and request policy. It fails on the pinned
unpatched upstream and passes with the patch. Evidence is in
`evidence/integration/openrouter-pilot/sampling-unpatched.log` and
`tests-final-image.log`. All 19 integration and 13 inherited audit tests pass.

The selected endpoint lacks native reasoning-effort and parallel_tool_calls
controls. `pilot/provider.py` removes the adapter's implicit xhigh and unsupported
parallel-call field, then applies explicit reasoning enablement, output cap, and
zero SDK/adapter retries in both construction paths. Provider source is unchanged.
HTTP guards verify returned model/provider before the loop can execute a tool.
Raw response bodies and assistant messages precede any history normalization.
The SDK wraps a guard rejection as APIConnectionError; a separate routing record
retains the cause. The wrong-backend test checks that no history/tool action occurs.

`restore-check` now also accepts the pinned real source config, only with a dummy
key and Docker network disabled. It constructs/restores state and exits before any
model invoke. This permits original-versus-restored validation of a real candidate.
