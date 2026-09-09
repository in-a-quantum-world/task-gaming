# Pre-commit history prototype

EXPLORATORY ONLY — GENERATED BEFORE FINAL PREREGISTRATION

The 258-error task runs locally. No provider key was available on 2026-09-09.
The saved examples use a deterministic command script, not a language model.

## Files and scope

- `bootstrap.py` runs the original entrypoint and substitutes the prototype loop.
- `loop.py` uses upstream task setup, tools, step logic, and scorer.
- `run.py` starts one run and enforces persistent live-run caps.
- `histories.py` copies checkpoints and edits only their message history.
- `summarize.py` exports observable records and separate manual annotations.
- `make_configs.py` records the derivation of the committed configs.

The wrapper adds independent probes and full `/agent` archives.
It passes the same provider parameters on fresh runs and resumes.
It records raw HTTP request bodies and response bodies without authentication headers.
It records tool outputs through upstream message dumps.
It does not change the task prompt or source variant.

The original snapshot failed a content comparison.
The supplemental archive passed four fixture restore checks.
That scope covers `/agent` paths, content, modes, and ownership.
It does not prove full equivalence for timestamps or state outside `/agent`.
Future container diffs identify paths outside that scope for review.

## Exact local setup

Use this worktree:

```bash
cd /home/rucha/ai-alignment-forensics/prototype-history-effect
git clone https://github.com/gkroiz/agent-interp-envs.git vendor/agent-interp-envs
git -C vendor/agent-interp-envs checkout --detach 56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb
uv sync --frozen --project vendor/agent-interp-envs
docker build -f vendor/agent-interp-envs/environments/precommit_hook/Dockerfile -t prototype-precommit:56fd0c11 vendor/agent-interp-envs
```

The checkout and image already exist in this session.
Skip the clone when that pinned checkout exists.
The Docker build uses upstream's original Dockerfile.
Its base image and most Python packages are not fully pinned.
The saved image ID identifies this session's exact image.
The host lockfile does not pin the container dependency installation.

## Next live baseline

Export `FIREWORKS_API_KEY` through your credential manager or shell.
Do not place its value in a config or command committed to Git.
Then run exactly one baseline:

```bash
python3 prototype/run.py --config prototype/configs/baseline_258.json --condition BASELINE
python3 prototype/summarize.py
```

This config retains upstream's Fireworks model:
`accounts/fireworks/models/deepseek-v4-pro`.
The live endpoint and model availability were not tested.
The config sets 100 total turns and explicit low reasoning effort.
Temperature and top-p remain omitted from requests, as in the upstream default.
The provider chooses their defaults; those defaults are not known here.
Each shell command has upstream's 30-second timeout.
The launcher caps a run at 3,600 seconds.
The cap counts model turns, not individual shell subcommands.

The live config enables the supplemental workspace archive.
A live baseline uses the model and route above or fails explicitly.
The launcher never substitutes a mock when a live run fails.

Persistent caps count every allocated live run, including API and runtime failures:

- Three baselines.
- Two ordinary continuations.
- Two continuations per A/B/C condition.

Keep the raw run directories to preserve these counters.
The launcher never starts an extra rollout or drops a slow run.
Its code and config copies freeze at run allocation.
The first two technical fixtures predate this code-copy feature.

## Resume and history steps after a live baseline

Choose a checkpoint through a documented content review.
Use the same config and image for the entire pilot.
Do not choose a checkpoint on the basis of its subsequent outcome.

```bash
python3 prototype/run.py --config prototype/configs/baseline_258.json --condition ORDINARY --checkpoint /absolute/path/to/run/data/step-N
```

Repeat once from the same untouched checkpoint.
The gate compares workspace files before either continuation calls the provider.
Any difference stops the continuation and consumes its slot.

Create an information-items JSON file from the real checkpoint.
Use the fixture facts file only as a schema example.
Every sentence needs A message indices, an inclusion decision, and a confound note.

```bash
python3 prototype/histories.py --checkpoint /absolute/path/to/run/data/step-N --facts /absolute/path/to/reviewed_information_items.json --output /absolute/path/to/new_history_bundle
```

Review the generated matrix and all omitted information.
Only then fill the bundle's `researcher_review.json` fields.
The synthetic fixture review remains false.
The launcher checks the bundle hashes before each run.
It also requires two equivalent ordinary restores from the source checkpoint.

```bash
python3 prototype/run.py --config prototype/configs/baseline_258.json --condition A_FULL --checkpoint /absolute/path/to/new_history_bundle/A_FULL
python3 prototype/run.py --config prototype/configs/baseline_258.json --condition B_FAILURE_FACT --checkpoint /absolute/path/to/new_history_bundle/B_FAILURE_FACT
python3 prototype/run.py --config prototype/configs/baseline_258.json --condition C_STATE_ONLY --checkpoint /absolute/path/to/new_history_bundle/C_STATE_ONLY
```

A second run per arm is the maximum, not a required target.
Set the run order before any outcomes are visible.
Do not edit a used bundle; create and name a new version with a log entry.

## Local verification

```bash
python3 -m unittest discover -s prototype -p 'test_*.py' -v
python3 prototype/run.py --config prototype/configs/smoke_258_archive.json --condition SMOKE
```

Mock mode disables container network access.
It uses the same original task and real tools.
Its fixture does not count toward live pilot caps or empirical evidence.

## Data semantics

`raw/<run_id>` contains immutable configs, logs, and task output.
Future runs also freeze the wrapper code and record `docker diff`.
`processed/model_runs.jsonl` includes only actual model runs; it is currently empty.
`processed/runs.jsonl` also includes fixtures, with `synthetic=true`.
`null` means unknown or unmeasured, never false.
Exact token counts are unknown; byte counts are available.
The byte-divided-by-four value is only a rough proxy.

`workspace_hash` describes the workspace at the start of the run or continuation.
`final_workspace_hash` describes the last recorded state.
`steps_after_checkpoint` counts attempted provider invocations, including text-only turns.
Probes are privileged harness diagnostics; the agent never receives them as messages.
They add wall time and cache activity under `/opt`, which need review before scale-up.

Raw data remain local and ignored as loose files.
A compressed session archive and SHA-256 index accompany the handoff.
Extract that archive into this worktree to reconstruct the recorded paths.
Absolute source paths in history provenance require migration for another location.
