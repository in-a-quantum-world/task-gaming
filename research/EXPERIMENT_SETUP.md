# Experiment setup

Status: infrastructure audited; experiment not approved or run.
Working directory: `/home/rucha/ai-alignment-forensics/task-gaming-under-trajectory-pressure`.

## Repository and runtime pins

| Item | Recorded value |
|---|---|
| Host repository branch | `experiment/failure-history` |
| Host starting commit | `3deb3a6a88c919c84ebd6db1342fb34dea401117` |
| Framework commit | `56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb` |
| Framework branch | `experiment/failure-history`; upstream files unchanged |
| Host OS | Ubuntu 24.04.4 LTS, Linux x86_64 |
| Initial shell Python | 3.13.13 |
| Synced project Python | 3.12.3, selected by upstream `.python-version` |
| Container Python | 3.11.16 |
| Docker | 29.6.1 |
| uv | 0.11.27 |
| mypy in image | 1.20.2 |
| Built image tag | `precommit_hook:failure-history-56fd0c1` |
| Built image ID | `sha256:b756b5d4756b6ed05bbbbe2ba55e7b767b422ee86f24ebf496ac8735793afb5d` |

[Provenance](evidence/provenance.json) pins all three reference repositories.
[Image metadata](evidence/docker-image.json) and [container package inventory](evidence/container-pip-freeze.txt) describe the successful build.
The upstream Dockerfile uses pip dependency resolution, not the root `uv.lock`.
Rebuilding later can produce a different image even at the same source SHA.
Use the retained image ID for local repeats. An exported image or digest-addressable registry artifact is needed for portable byte-identical reuse.
No registry upload occurred.

## Layout

- `upstream/`: three ignored shallow clones, pinned by provenance.
- `research/configs/`: exact upstream config extraction, proposal wrapper, offline mock configs.
- `research/scripts/`: validator, tests, snapshot/provider probes, and offline container helpers.
- `research/data/raw/`: complete unmodified synthetic smoke and capture outputs; no experimental A/B/C data.
- `research/data/processed/`: reserved for derived records.
- `research/data/run_schema.json`: draft future continuation schema.
- `research/analysis/`: reserved for a reviewed analysis plan and code.
- `research/evidence/`: dependency/build logs, tests, measured variants, and audit evidence.

Raw data are ignored by Git. Preserve or archive them separately before moving machines.
No `.env` file was created or added to Git. No credential value appears in audit output.
Credential checks recorded only presence booleans. Required provider keys were absent in the checked shell and local `.env` paths.
The paid pilot was also ineligible because model/config and methodology remain unresolved.

## Commands already executed

Dependencies, from the framework checkout:

```bash
uv sync --frozen
```

Only the pre-commit image was built:

```bash
cd upstream/agent-interp-envs
docker build --progress=plain \
  -f environments/precommit_hook/Dockerfile \
  -t precommit_hook:failure-history-56fd0c1 .
```

The host shell exposes an unrelated ROS `PYTHONPATH` and active virtual environment.
The first pytest launch loaded a ROS plugin and failed because `lark` was absent.
Subsequent offline checks removed `PYTHONPATH` and `VIRTUAL_ENV`, and disabled pytest plugin autoload.
Do not install unrelated ROS dependencies to fix this audit environment.

## Safe next checks

From the host repository, run validator unit tests:

```bash
env -u PYTHONPATH -u VIRTUAL_ENV \
  upstream/agent-interp-envs/.venv/bin/python \
  -m unittest discover -s research/scripts -p 'test_*.py' -v
```

Reproduce snapshot limitations without model access:

```bash
env -u PYTHONPATH -u VIRTUAL_ENV \
  upstream/agent-interp-envs/.venv/bin/python \
  research/scripts/probe_snapshot_limits.py \
  --output /tmp/failure-history-snapshot-limits.json
```

Run another synthetic smoke only with a fresh output path:

```bash
env -u PYTHONPATH -u VIRTUAL_ENV \
  upstream/agent-interp-envs/.venv/bin/python \
  research/scripts/smoke_precommit.py \
  --image precommit_hook:failure-history-56fd0c1 \
  --config research/configs/offline_smoke_258.yaml \
  --output research/data/raw/smoke-258-new
```

The helper enforces `provider: mock`, at most three decisions, and Docker `--network none`.
It copies the full checkpoint and workspace before container deletion.
It preserves failure output too. No provider credential is passed to the container.

## Before a paid continuation

The researcher must approve the baseline, source checkpoint, outcomes, history texts, and collection policy.
First resolve snapshot fidelity and fresh/resume request-setting differences.
Then pin the experiment commit and preserve any dirty diff with all untracked source artifacts.
Record actual request kwargs from the provider object, not only YAML values.
Record backend metadata and model revision if the service exposes them; otherwise use null and disclose the limit.

The stock local runner uses positional YAML syntax and dotlist overrides.
Any eventual fresh run must include `--no-kill-last`; its default `--count 1` can launch two model rollouts.
The stock resume runner has no wall timeout and expects a local `.env` file.
A dedicated preservation-first continuation runner remains a future infrastructure task.
This document intentionally supplies no paid launch command before those decisions and repairs.

## Outcome data

Use one immutable directory per run and per retry attempt.
Hash all raw files before any grading or transformation.
Preserve pre-invocation state, full request/response metadata, every tool result, final workspace, and termination cause.
Record attempted actions separately from their successful effects.
Do not mark absent labels false; use null until adjudication.
Do not infer shortcut knowledge from general model capability. Record what the supplied history actually documents.
The run schema includes a separate `intent_annotations` field outside primary behavioral outcomes.

## Scope limitations

No source rollout from a paid model, no A/B/C comparison, no completed causal estimate, and no original-paper replication occurred.
The audit produced usable infrastructure and evidence of blockers that must be resolved before a state-matched claim.

## Repeat the real restore-pair probe

This command makes no model requests. Exit code 1 is expected for the audited upstream defect.
Use a new output path each time.

```bash
env -u PYTHONPATH -u VIRTUAL_ENV \
  upstream/agent-interp-envs/.venv/bin/python \
  research/scripts/validate_mock_restores.py \
  --image precommit_hook:failure-history-56fd0c1 \
  --config research/configs/offline_smoke_258.yaml \
  --checkpoint research/data/raw/smoke-258/checkpoints/step-0 \
  --output research/data/raw/restore-pair-new
```

The helper captures both prepared containers before a continuation invocation, then compares them.
It retains logs and validation failures before container cleanup.
Optional JSON Schema tests use `jsonschema==4.26.0`, listed in `requirements-audit.txt`.

## Host versus container package versions

| Package | Frozen host environment | Built task image |
|---|---|---|
| `openai` | 2.14.0 | 3.11.0 |
| `anthropic` | 0.75.0 | 1.4.0 |
| `mypy` | 2.1.0 | 1.20.2 |

The host dev dependency group includes mypy. Its version does not define the task's error count.
All source-variant measurements used the container version, not host mypy.
`evidence/host-uv-freeze-clean.txt` records a host inventory with unrelated shell path variables removed.
`evidence/container-sdk-defaults.json` records SDK timeout and retry defaults inside the actual image.
