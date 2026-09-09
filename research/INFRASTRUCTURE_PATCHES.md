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
