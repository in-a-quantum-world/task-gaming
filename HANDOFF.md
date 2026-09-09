# WHAT I COMPLETED

- Pinned and audited all three public repositories.
- Created `experiment/failure-history` in the host repository and framework checkout.
- Read the pre-commit implementation, both YAML configs, shared snapshot/provider code, and relevant runners/tests.
- Built only the pre-commit environment from the unchanged upstream Dockerfile.
- Measured all thirteen source variants. Both 258 and 602 are present and match their labels.
- Created the research audits, preregistration draft, history design, run schema, validator, and offline probes.
- Preserved all synthetic smoke and restore outputs. No A/B/C histories or paid model runs occurred.

# WHAT WORKS

The Docker build and both 258/602 offline mock smoke tests pass.
The validator captures files, Git state, error sets, prompts, budgets, and supplied runtime metadata.
Its final Docker captures have no probe-induced workspace changes.
Its unit suite passes 13 tests. Scaffold lint and JSON Schema checks pass.
The restore-pair helper reproduces the upstream Git mismatch without model calls.

# WHAT DOES NOT WORK

**Stock resume does not establish the strict state equivalence required by this experiment.**

- Unchanged initial Git metadata can differ after restore.
- A second-generation checkpoint can lose untouched inherited changes.
- Same-size file edits with preserved mtime can escape upstream snapshot capture.
- Fresh pre-commit runs drop temperature and `top_p`; resumed runs pass them through.
- The upstream scorer can label an uncommitted, non-executable no-op hook setup `good`.
- One upstream unit assertion expects `high`; current OpenRouter code requests `xhigh` by default.

Provider credentials were absent in the checked shell and local `.env` paths.
No intended paid model/config was unambiguous. The optional paid pilot was skipped.
There is no eligible model-generated source checkpoint yet.

# WHAT I LEARNED FROM THE REPOSITORIES

The current framework uses file manifests, not command replay. Its README is stale on that point.
The README also says source 602 is absent, but this pin includes it and builds it successfully.
Public scripts and configs are convenience copies; upstream documentation says they can lag a private companion repository.
The fresh local runner launches `count+1` by default and deletes slow survivors. Always disable that behavior for future research.
The Modal runner removes failed local downloads. Its remote preservation does not guarantee a complete local analysis dataset.
The related study has useful preregistration and independent-grading patterns, but its retry paths reuse some artifact filenames.
The game resampling repository does not directly support pre-commit and does not certify history-rewrite equivalence.

# IMPORTANT DIFFERENCES FROM THE PAPER / PRIOR EXPERIMENTS

The exact published setup was not recovered from a complete original config and trajectory.
The related study identifies 258 as the reported anchor but documents a DeepSeek YAML with 602.
That study used upstream `5f4facb`; this audit pins `56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb`.
Its report of absent source 602 applies to its older checkout, not this one.
Its main local Qwen/vLLM effort experiment differs from the proposed DeepSeek/Fireworks history study.
Current Docker dependencies also differ from the frozen host environment: OpenAI SDK 3.11.0 versus 2.14.0.
The container's mypy is 1.20.2; the host dev environment has mypy 2.1.0.
All source-count measurements used container mypy.

# METHODOLOGICAL RISKS I FOUND

- Equal replicas can share a wrong reconstruction. Compare each with the actual original source-state archive too.
- Token length, recency, role layout, summary authorship, and information loss can accompany a history rewrite.
- The last preserved assistant/tool pair can itself contain failure facts or reasoning.
- Unchanged workspace logs or plans can let B/C recover history through tools.
- Tool-call recovery can promote reasoning text into an executed action; distinguish those artifacts.
- Total decision budget differs from a fresh continuation allowance; saved step k leaves `max_steps - k - 1` decisions.
- Prefix actions must not count as post-intervention behavioral outcomes.
- Timeout, context-limit, retry, and slow-run exclusion policies can select on history length or legitimate repair effort.
- Upstream heuristic labels do not establish successful commits, real type repair, or honest hook enforcement.
- A single checkpoint supports a local conditional estimate, not a general account of failure pressure or internal intent.

# DECISIONS THE RESEARCHER MUST MAKE

1. Select the model/config and resolve effort `low` versus the maintainer's suggested `max` for DeepSeek.
2. Approve or revise the one proposed 258-error baseline and its provisional sampling values.
3. Select an eligible source trajectory and pre-action checkpoint without selecting for a dramatic result.
4. Approve a complete state archive/restore repair before strict state-matched collection.
5. Define the primary behavioral rubric, successful violation, honest completion, and suppression exceptions.
6. Freeze the primary contrast, N, timeout policy, retry/exclusion rules, and credit budget.
7. Review the information inventory, role layout, token-length policy, and exact B/C texts.
8. Decide whether a later nearby constraint reminder merits a separate experiment.

None of these choices was silently finalized.

# EXACT NEXT COMMAND TO RUN

This command checks the local validator. It makes no network or model requests.
Expected result: 13 tests pass.

```bash
cd /home/rucha/ai-alignment-forensics/task-gaming-under-trajectory-pressure
env -u PYTHONPATH -u VIRTUAL_ENV \
  upstream/agent-interp-envs/.venv/bin/python \
  -m unittest discover -s research/scripts -p 'test_*.py' -v
```

Then read the state-restoration evidence before any paid continuation.
The reusable restore-pair command is in [EXPERIMENT_SETUP.md](/home/rucha/ai-alignment-forensics/task-gaming-under-trajectory-pressure/research/EXPERIMENT_SETUP.md).
Its expected nonzero comparison result documents the upstream mismatch.

## Git status

At handoff preparation:

```text
## experiment/failure-history
?? .gitignore
?? HANDOFF.md
?? research/
```

The host HEAD remains `3deb3a6a88c919c84ebd6db1342fb34dea401117`.
The research scaffold is uncommitted. No push, PR, or remote write occurred.
All three reference worktrees are clean. The framework branch is `experiment/failure-history`; the other clones are read-only on `main`.
Pin a new experiment commit before future collection and record any dirty source artifacts explicitly.

## Files created

Base directory: `/home/rucha/ai-alignment-forensics/task-gaming-under-trajectory-pressure`.

| Path relative to the base | Contents |
|---|---|
| `.gitignore` | Excludes reference clones, credentials, caches, and local raw/processed outputs. |
| `HANDOFF.md` | This report. |
| `research/REPO_AUDIT.md` | Implementation audit with file/function/implication tables. |
| `research/CONFIG_AUDIT.md` | Both configs, measured variants, and one reviewed-later baseline proposal. |
| `research/PRIOR_ART_PRACTICES.md` | Exact implementation patterns and reuse judgments. |
| `research/CHECKPOINT_VALIDATION.md` | Guarantees, reconstruction, demonstrated limits, and validator use. |
| `research/PREREGISTRATION_DRAFT.md` | All fifteen requested sections; unresolved choices marked. |
| `research/HISTORY_INTERVENTION_DESIGN.md` | Mechanism and review queue; no B/C text. |
| `research/EXPERIMENT_SETUP.md` | Pins, reproducible local commands, runtime differences, and blockers. |
| `research/RESEARCH_LOG.md` | Decisions, failures, fixes, and scope record. |
| `research/configs/` | Exact config extraction, non-runner proposal wrapper, two mock configs. |
| `research/scripts/` | Validator, 13 tests, snapshot/provider probes, mock capture and restore helpers, offline test runner. |
| `research/data/run_schema.json` | Draft schema with every requested continuation field. |
| `research/data/run_record.example.json` | Clearly labeled synthetic schema example; never analyze as data. |
| `research/data/raw/` | Complete synthetic smoke/capture artifacts, ignored by Git. |
| `research/evidence/` | Build logs, package inventories, test output, source diagnostics, hashes, and counterexamples. |
| `research/requirements-audit.txt` | Optional schema validator pin. |
| `research/analysis/README.md` | Empty analysis area with no experiment results. |
| `upstream/` | Three ignored shallow reference clones. |

No pre-existing tracked project file or upstream implementation file was modified.
Generated `.venv` and pytest caches are ignored within the framework checkout.

## Tests run and results

| Check | Result | Evidence |
|---|---|---|
| Frozen dependency sync | Pass | `research/evidence/uv-sync.log` |
| Original pytest attempt | Failed before collection: unrelated ROS plugin lacked `lark` | `research/evidence/upstream-tests.log` |
| Clean-shell broad selection | 148 passed, 2 skipped, 13 failed at missing-credential construction | `research/evidence/upstream-tests-clean.log` |
| Selected offline host suite, socket calls blocked | 155 passed, 2 skipped, 1 stale effort assertion failed | `research/evidence/offline-tests.log` |
| Same selected suite in built image, network disabled | 156 passed, 1 skipped, same 1 failure | `research/evidence/container-offline-tests.log` |
| New validator tests | 13 passed | `research/evidence/validator-tests-final.log` |
| Scaffold lint | Pass | `research/evidence/scaffold-lint-final.log` |
| Python compile check | Pass | `python3 -m compileall -q research/scripts` |
| Schema meta-validation and example | Pass | `research/evidence/schema-final.log` |
| Schema negative cases | Missing fields and intent string rejected | `research/evidence/schema-record-validation.log` |
| Source variants | All 13 measured labels match, including 0/258/602 | `research/evidence/source-variant-counts.json` |
| Mock smoke, 258 and 602 | Both pass; complete artifacts copied | `research/data/raw/smoke-*/result.json` |
| Snapshot limits | Three defects reproduced; no model calls | `research/evidence/snapshot-limits.json` |
| Fresh/resume request settings | Dropped fresh temperature/`top_p` reproduced | `research/evidence/provider-paths.json` |
| Final Docker restore pair | Both captures valid; comparison correctly reports different Git state | `research/evidence/restored-pair-final.json` |
| Scorer counterexamples | `good` without a commit; `bad` for a quoted bypass string | `research/evidence/scorer-counterexamples.json` |
| Git diff whitespace check | Pass | `git diff --check`; new-file lint and link checks also ran. |

The credential-dependent selection included API integration tests, but missing keys stopped every request at construction.
Later selections explicitly exclude integration tests and disable network connections.
No failed test was edited away or silently treated as a pass.
Early validator captures found an index side effect. The corrected probe disables Git's automatic index refresh; all old artifacts remain.

## Docker build result

Success, with unchanged upstream Dockerfile. Only `precommit_hook` was built.
Image ID: `sha256:b756b5d4756b6ed05bbbbe2ba55e7b767b422ee86f24ebf496ac8735793afb5d`.
Build log and image metadata live in `research/evidence/`.
The base image and unpinned pip dependencies can change on rebuild. Source SHA alone is insufficient.
No audit container remains running after cleanup.

## API activity and blockers

Paid baseline rollouts: **0**. A/B/C continuations: **0**. LLM judge calls: **0**.
Model API requests: **0**. Model API cost: **$0**.
The only agent-loop smoke activity used a deterministic local mock provider with container network access disabled.
Public Git, package, and browser reads supported the repository audit.

Blockers for the future experiment are state-restoration fidelity, missing approved source/config, missing checked credentials,
and the unresolved methodological choices above. They did not prevent completion of this audit and scaffold.

## How to resume

Working directory: `/home/rucha/ai-alignment-forensics/task-gaming-under-trajectory-pressure`.
Read the standing skills below, then start with the exact local test command above.
Next read [CHECKPOINT_VALIDATION.md](/home/rucha/ai-alignment-forensics/task-gaming-under-trajectory-pressure/research/CHECKPOINT_VALIDATION.md).
Do not launch the proposal wrapper as a framework config.

## Standing interaction rules

- Apply [standard-technical-coding-practices](/home/rucha/.codex/skills/standard-technical-coding-practices/SKILL.md) to every technical task.
- Use simple, verified prose and the skill's code style. Respect the user's explicit authorization and task scope.
- The user authorized this autonomous audit and scaffold, with no clarification questions during the hour.
- That authorization explicitly excludes A/B/C execution and final B/C wording. It does not approve a large or costly experiment.
- Read [standard-technical-handoff-convention](/home/rucha/.codex/skills/standard-technical-handoff-convention/SKILL.md) for future handoffs.
- Use the QSCHA skill only if a later request concerns learning or practice. No lesson is active here.
- Do not print credentials, add `.env` to Git, send external messages, or silently change the scientific design.

## Task and current state

The requested audit, reproducibility setup, environment validation, and experiment scaffold are complete.
The proposed experiment itself remains unrun and unapproved.
The source-state defects are prominent findings, not hidden substitutions.

## Done in this context

All ten requested phases were addressed. Phase 8 was explicitly skipped under its eligibility rule.
Phase 9 produced design notes only. Raw synthetic output and failures remain preserved.

## Remaining work

1. Researcher review of the baseline, checkpoint, rubric, and contrast.
2. A complete reference-state archive and tested restore repair, including unchanged Git and inherited edits.
3. Consistent fresh/resume sampling propagation, with actual request metadata.
4. Preservation-first continuation runner and independent outcome grader.
5. Approved B/C histories, preregistration freeze, justified N, budget, and collection policy.
6. Only then, any paid source or continuation calls under explicit authorization.

## Verified state

- Framework pin: `56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb`, in `research/evidence/provenance.json`.
- 258 and 602 actual errors: `research/evidence/source-variant-counts.json`.
- Restore failures: `research/evidence/snapshot-limits.json` and `research/evidence/restored-pair-final.json`.
- Fresh/resume sampling difference: `research/evidence/provider-paths.json`.
- Image and dependency pins: `research/evidence/docker-image.json`, `container-pip-freeze.txt`, and `host-uv-freeze-clean.txt`.
- Full raw artifact hashes: `research/evidence/raw-artifact-manifest.json`.
- Clean reference worktrees: `research/evidence/reference-status.json`.

## Quirks and discoveries

`git diff` refreshed the index even with optional locks disabled; the validator now disables `diff.autoRefreshIndex` too.
Host and container Python/SDK/mypy versions differ. The host virtual environment has no pip module; `uv pip` provides package inspection.
Checkpoint steps are zero-based. Framework `task_completed` means the loop terminated, not verified successful task completion.
Final files and current error count alone cannot establish that a required hook actually governed a commit.

## Decisions taken — do not reopen

No paid calls. No B/C wording. No A/B/C execution. No upstream code modifications.
Use measured source counts and preserve every raw diagnostic attempt.
Keep intent annotations separate from primary behavioral fields.
Treat the baseline and preregistration as proposals for researcher review.

## Decisions open

All scientific and future-collection choices listed under DECISIONS THE RESEARCHER MUST MAKE remain open.

## Multi-agent coordination

None. No sub-agents were spawned.

## QSCHA state

None. No teaching exercises or answers were prepared.
