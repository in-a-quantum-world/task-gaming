# Checkpoint validation

**Current conclusion: vanilla upstream resume is insufficient for a strict state-matched experiment.**
The audit reproduced state differences without a single model API call.
A successful Docker process or equal error count does not establish checkpoint equivalence.

## 1. What the framework guarantees, within its implementation limits

At this pin, `messages.json` stores the provider's message list and `state.json` stores the state dataclass.
`fs/manifest.json` plus blobs record selected cumulative file differences against a pristine workspace.
The restore path applies captured content instead of executing historical commands.
For recorded regular-file entries, it applies bytes, ordinary permissions, mtime, and uid/gid when root.
It checks a pristine content digest before restore when the manifest has that field.

These are narrow implementation properties, not a guarantee of byte-identical workspaces or machines.
The baseline digest excludes `.git`. Unchanged baseline files are not stored as blobs.
Old manifests without a baseline digest only produce a warning.

## 2. What resume reconstructs

- A new container and Python process from the selected image.
- A new `/agent` source tree and initial Git commit through `entrypoint.py`.
- A new provider object from saved messages and current config.
- Tool definitions from current config.
- Files described by the manifest, applied over the new baseline.
- A next decision index of `saved_step + 1`.

A checkpoint at zero-based step 5 under `max_steps: 100` leaves 94 decisions.
Do not set `step` from the shorter B/C message count. Do not grant a fresh 100 decisions by accident.
Prompt text in the YAML does not supersede messages already saved in the checkpoint.
No process, RNG, network, shell-session, or model-cache snapshot exists.

## 3. Confirmed failure cases

| Probe | Result | Evidence |
|---|---|---|
| Restore an unchanged initial Git history over an otherwise identical baseline | Original HEAD differs from resumed HEAD | `evidence/snapshot-limits.json`; `scripts/probe_snapshot_limits.py` |
| Save after restore without touching an inherited added file, then resume again | Added file disappears; second manifest has zero entries | Same probe |
| Edit bytes without changing size or mtime | Upstream stat gate misses the edit | Same probe |
| Two actual prepared Docker restores from the same synthetic checkpoint | Git/index/history differ despite identical messages and task source | `evidence/restored-pair-comparison*.json`; raw capture folders |
| Fresh versus resume provider constructor | Temperature and `top_p` drop on fresh path but reach resume | `evidence/provider-paths.json` |

The first probe deliberately controls initial commit dates, so the Git failure does not depend on a clock race.
The Docker pair tests actual entrypoint and restore code. They invoke no continuation model.
The source smoke checkpoint contains a probe-file command, not an experimental failed-repair history.
Do not use it as condition A.

The inherited-entry failure is distinct from baseline digest checking.
The upstream repeated-resume unit test changes the same file again; that case passes while untouched inherited files can disappear.

## 4. Automatic validator

[`scripts/validate_state_equivalence.py`](scripts/validate_state_equivalence.py) provides `capture` and `compare` commands.
Run capture inside a disposable prepared container before `provider.invoke()`.
Its output must live outside the task workspace.
It does not restore a checkpoint or call a model.

It records or compares:

| Property | Method | Limit |
|---|---|---|
| Workspace bytes and generated files | Recursive SHA-256 inventory of every regular file | A file can change outside the measurement window. |
| File modes and ownership | `lstat`; includes directories and symlink targets | No ACL, xattr, hardlink graph, or device-state equivalence. |
| Git HEAD, status, staged/unstaged diffs, tracked entries | Explicit Git subprocesses and full `.git` inventory | Initial commit timestamps can change Git bytes. No differences are silently ignored. |
| Hook and mypy configuration | File hashes and permissions included in inventory | The utility does not execute arbitrary hook content or prove honest enforcement. |
| Current errors and error set | Same pinned mypy under active and pristine configs, cache disabled | This is current type-check state, not a de-suppressed honesty grader. |
| System/user instruction | Hash exact initial message objects | Stored hashes differ from the UTF-8 prompt-string hashes in the config extraction. |
| Latest observation and assistant call | Hash exact messages, including IDs | The preserved latest assistant reasoning may itself contain history. |
| Remaining budget | `max_steps - checkpoint_step - 1` | Valid for this pinned pre-commit loop only. |
| State counters and execution trace | Hash full `state.json` | Saved state can still omit external variables. |
| Config | Canonical full-document hash | Declared config cannot prove effective API settings. |
| Effective model/provider/settings/tools/cwd/environment | Supplied runtime JSON captured from actual prepared objects | The utility trusts the provenance of this input. |
| Extra roots | Optional repeated `--extra-root` inventories | No root is silently assumed equivalent if not captured. |
| Message protocol | Tool IDs, answered calls, initial roles, final tool boundary | Limited to OpenAI-style chat format; no provider-API acceptance test. |
| Token counts | Null unless separately measured | No tokenizer guess is made. |

Compare exit codes: 0 means `equal_on_recorded_fields`; 1 means a difference; 2 means incomplete or invalid evidence.
Missing mypy, missing runtime data, or two identical probe failures never produce an equality verdict.
Histories may differ by design. Their equality and role-sequence equality are reported separately.
Human approval is still required for role/order differences.
File mtimes are recorded and reported separately; they are not part of the content/mode ownership equality verdict.

### Example commands

Inside a prepared container, with runtime metadata from the provider object:

```bash
python /opt/research-scripts/validate_state_equivalence.py capture \
  --workspace /agent --config /opt/config.yaml \
  --state /opt/pre-invoke-state.json \
  --messages /opt/pre-invoke-messages.json \
  --runtime /opt/runtime.json \
  --reference-config /opt/task/pyproject.toml \
  --output /opt/validation.json
```

From the host repository:

```bash
python3 research/scripts/validate_state_equivalence.py compare \
  research/data/raw/restore-5/validation.json \
  research/data/raw/restore-6/validation.json
```

The archived comparison intentionally fails: it documents an upstream restoration defect.
Use new output paths for every capture. The utility refuses to overwrite existing output files.

## 5. Manual and external requirements

Archive a full original workspace reference at the source boundary, including `.git`, before the source container disappears.
Compare every condition against this original reference. Matching replicas alone can share the same wrong reconstruction.
Archive relevant `/home/dev`, `/tmp`, memory stores, package state, and generated files if the trajectory uses them.
Inspect surviving processes and commands with effects outside the snapshot roots.
Capture actual provider request kwargs, tool schemas, SDK version, routing results, usage, and request IDs.
Do not store API keys in these records.
Use an independent grader after continuation; preserve the pre-grading workspace.
Audit information content, known shortcuts, legitimate options, and current errors across histories manually.

## 6. What cannot be guaranteed

No automatic method here certifies semantic information equivalence, identical attention, identical model randomness, or identical hidden provider state.
Wall clock, process scheduling, network responses, API version drift, and context-cache behavior can differ.
Snapshot consistency is not atomic. Caches are omitted upstream and can affect timing.
Directory symlinks, ownership-only changes, directory permissions, and filesystem metadata need additional tests for trajectories that use them.
The snapshot stores ordinary permission bits, not every Unix metadata property.

## 7. Infrastructure choices for review

The safest next infrastructure task is a complete reference-state archive and a validated restore that preserves Git and inherited changes.
Possible implementations include a full-tree sidecar archive or a repaired manifest with complete baseline metadata and inherited entries.
Both require tests against the original source state and repeated resumes.
Do not hide a Git mismatch by excluding `.git` from the primary comparison.
If the researcher accepts a narrower task-state definition, document its excluded properties and scientific justification before collection.
No such relaxation or upstream repair was selected in this audit.

## 8. Probe side effects and identity

The first captures detected a Git index change caused by `git diff`.
`GIT_OPTIONAL_LOCKS=0` alone did not prevent that change in this image.
The final utility also sets `diff.autoRefreshIndex=false` and disables Python bytecode writes in probe subprocesses.
Final captures `restore-5` and `restore-6` have zero probe issues and no workspace mutations.
Their comparison still fails on Git state, as expected. See `evidence/restored-pair-final.json`.
Earlier captures remain intact as evidence of the validator repair.

Mypy probes run under the capture process identity, which is root in the supplied Docker helper.
They measure source/config diagnostics; they do not certify the exact observation a restricted `dev` shell would receive.
The inventory includes ownership and permissions, while runtime metadata records the agent environment.
Task histories with permission-dependent behavior require a separate agent-identity diagnostic check.
No arbitrary hook is executed by this utility.
