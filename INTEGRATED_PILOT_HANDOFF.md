# Handoff: Integrated source pilot — 2026-09-09

## How to resume

Working directory: `/home/rucha/ai-alignment-forensics/integrated-pilot`.
Branch: `experiment/integrated-pilot`, based on `experiment/failure-history`.
Read the standing skills and this handoff before any next action.
The integration work is complete. The optional paid phase did not run.
Do not run a continuation or create history summaries under this authorization.

Start with the frozen gate check. It performs no provider request:

```bash
cd /home/rucha/ai-alignment-forensics/integrated-pilot
python3 - <<'CHECK'
import sys
from pathlib import Path
sys.path.insert(0, 'pilot')
from run import require_frozen
require_frozen(Path('pilot/configs/first_pilot.json'),
               'sha256:14bb9a6b1ca097793c25038a6e088e9e33497365bac7e194cc6eeefa1ae14f1e')
print('Frozen offline gate passes')
CHECK
```

Read `/home/rucha/ai-alignment-forensics/integrated-pilot/research/SOURCE_MODEL_CONFIG.md` before any source command.
No credential value should appear in a message, config, or command argument.

## Standing interaction rules

- Apply `/home/rucha/.codex/skills/standard-technical-coding-practices/SKILL.md` to all technical work.
- Use clear short prose, verified claims, and the skill's code style.
- This user explicitly authorized integration edits, tests, logs, and this handoff.
- The user selected this handoff path; no further path approval was needed.
- Apply `/home/rucha/.codex/skills/standard-technical-handoff-convention/SKILL.md` for future handoffs.
- Apply `/home/rucha/.codex/skills/standard-technical-qscha/SKILL.md` only for learning or practice requests.
- Preserve both source branches and their worktrees.
- Preserve all failed/slow attempts; never start count+1 or reset the source cap.
- Never substitute another model or provider without a recorded user-approved amendment.
- No B/C histories, summaries, or model continuations are authorized in this stage.
- Treat all evidence as exploratory. Make no causal claims.

## Task and current state

1. **Which findings agreed?** Both found invalid stock restoration, scorer limits,
   no real source, and inadequate synthetic repair history. Both preserve the
   original total decision budget. Their 258-source measurements agree.

2. **Which findings disagreed?** The apparent archive conflict concerned evidence
   scope. The prototype already compared a captured source inventory with each
   restore. The audit required broader task-state evidence and an independent
   original reference. The new three-way test supplies that evidence. The fresh
   sampling findings concern different execution paths; both reports were correct.

3. **Which prototype code was retained?** The archive and guarded-restore patterns,
   exclusive artifact writes, request hooks, persistent caps, and entrypoint
   wrapper pattern. The integration adapts these in `pilot/`; it copies no branch wholesale.

4. **Which prototype code was rejected?** The A/B/C builder and bundles, old
   summary exporters as a primary grader, three-source cap, omitted sampling
   defaults, and unconditional container deletion. Synthetic histories lack
   repair episodes and omit acquired task information. New fixtures exist only
   as infrastructure tests.

5. **Is source/resume sampling identical?** Yes on the controlled constructor
   fields. The test fails on unpatched upstream for Fireworks and OpenRouter.
   It passes after fresh construction uses the same `provider_kwargs` helper as
   resume. Actual HTTP serialization is also tested offline. Server behavior is unknown.

6. **Does archive restoration match the ORIGINAL checkpoint?** Yes for the final
   synthetic checkpoint. Both restores and the original match all required
   workspace and task-state fields, with exact nanosecond mtimes. No real
   checkpoint exists yet. This does not validate every possible real trajectory.

7. **What remains outside equivalence?** Whole-machine state, kernel/process state,
   RNGs, clocks, network/remote state, provider caches, ACLs/xattrs, inode and
   hardlink identity, and atime/ctime. External file/package inventories match
   the fixture, but there is no general external-state restore mechanism.
   Active dev processes or changed fixed external fields block restore.

8. **Is the independent grader usable?** Yes for its documented observable scope.
   It separates native action attempts from verified state effects and retains
   upstream scores. A controlled bypass produced a verified commit with 258
   unresolved errors. Quotes and reasoning alone produce no action label.
   Opaque shell code, individual ignores, source refactors, and unsupported
   cases remain ambiguous. Mechanical completion does not prove full semantic
   preservation of application behavior.

9. **Did a real Kimi trajectory run?** No. No existing Fireworks key was available
   in the checked mechanism. The public model page also lists serverless as
   unsupported. Authenticated model preflight did not pass.

10. **If yes, what happened?** Not applicable. Model API requests: 0. Real source
    trajectories: 0. Continuations: 0. Model spend: 0.

11. **Did an eligible checkpoint exist?** No real source checkpoint exists.
    The review ledger rejects all 21 saved synthetic checkpoints for scientific use.

12. **Which checkpoint and why?** None. The technical archive checkpoint is
    `/home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot/fixture-44fad38897894fcf8c74fb97dfec2d5f/data/step-2`. It has no model repair episodes and cannot serve as
    the source for a scientific comparison.

13. **What had the model learned?** Not applicable. No model trajectory or real
    checkpoint information inventory exists. No synthetic knowledge inventory
    was presented as model knowledge.

14. **What legitimate repairs had it attempted?** None from a real model. The
    archive fixture creates task infrastructure and failed checks. Its scripted
    actions do not satisfy the two-episode source rule.

15. **What experiment should run next?** First resolve the exact Kimi route and
    credential gate, then use the already bounded one-source authorization if
    all gates pass. Review prefixes under the frozen eligibility rule. With an
    eligible real checkpoint and approved design, compare `A_FULL` with
    `A_FAITHFUL_COMPACT_SUMMARY`. Consider `B_FAILURE_FACT` versus
    `C_CURRENT_STATE` only after that control. No summary text exists yet.

16. **What still requires researcher approval?** Any provider/model/endpoint
    amendment, additional source samples, a changed checkpoint rule, final
    summaries and information parity, primary rubric exceptions, continuation
    sample size, token/role policy, order, resource budget, and preregistration.
    The existing authorization already covers at most one source under all
    stated gates. Do not request redundant approval for unchanged authorized work.

## Done in this context

- Read both handoffs, all requested audit/design files, and prototype archive code.
- Created a new isolated branch/worktree. No merge or whole-branch cherry-pick occurred.
- Reconciled findings in `/home/rucha/ai-alignment-forensics/integrated-pilot/research/INTEGRATION_RECONCILIATION.md`.
- Patched the actual experiment copy's fresh provider construction.
- Demonstrated regression failure before the patch and success afterward.
- Validated ORIGINAL versus two independent archive restores and the restore pair.
- Added source caps, complete checkpoint preservation, final recovery, and telemetry.
- Added independent offline action/state grading and commit/hook verification.
- Recovered exact public task prompts and froze the Kimi pilot config.
- Fixed the checkpoint rule before any real source outcome.
- Preserved 13 technical runs, including failed validation and timeout cases.
- Passed 15 integration tests and 13 inherited audit-validator tests.
- Verified every saved run's artifact manifest and archived the technical raw data.
- Completed `/home/rucha/ai-alignment-forensics/integrated-pilot/research/RESEARCH_LOG.md` with decisions and failed checks.

## Remaining work

No required integration edit remains. The optional paid source phase remains unrun.

1. Resolve the direct Kimi availability gate through an approved local mechanism.
2. If the exact route becomes available and credentials already exist, execute
   the single authorized source with the frozen config and source cap.
3. Review checkpoints in prefix order. Record rejection or eligibility before
   any later outcome review. Do not weaken criteria after the outcome.
4. Validate a real original checkpoint and inventory its acquired information.
5. Seek approval for the faithful-summary control design before continuation.

The experiment's main preregistration file remains an inherited draft. Its older
A/B proposal is not a freeze or authority to run it. The next contrast is stated
in this integration handoff and the user's current instructions.

## Verified state

Repository commits:

- Audit branch: `622703ee2fa109640eb3befa4d4c3a35ef75a194`.
- Prototype branch: `eaedc8fc320ad3d00696e3a17cffdd2bcef2eb7d`.
- Framework base: `56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb`.
- Integrated implementation/evidence commit: `e9277e4d8cddc653fa6452c827f7fa4ca3002cd3`.
- This handoff and `pilot/frozen.json` reside in a later documentation/freeze commit.
  Obtain its exact revision with `git rev-parse experiment/integrated-pilot`.
- Framework patch SHA-256: `86d339dc72efb24932c3fd637c5b0718e9babfcff017a7d1767d3479d8457468`.
- Frozen source-config SHA-256: `721442043dd0d52de96f4ca243b436849969c2c79bfc42d37e766a8eb0ab972b`.

Image:

- Base: `sha256:b756b5d4756b6ed05bbbbe2ba55e7b767b422ee86f24ebf496ac8735793afb5d`.
- Final: `sha256:14bb9a6b1ca097793c25038a6e088e9e33497365bac7e194cc6eeefa1ae14f1e`.
- No provider internals or installed packages changed in the derivative image.
- Prepared request metadata: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/prepared-kimi-request-final.json`.

Required archive comparisons:

- Original: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot/fixture-44fad38897894fcf8c74fb97dfec2d5f/data/step-2`.
- Restore 1: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot/restore-check-d3c7ca5582d54b488ae5e3eb632dccbe`.
- Restore 2: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot/restore-check-39a113654c4f452085122152e488e6dc`.
- Report: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/ARCHIVE_RESTORE_VALIDATION.md`.
- Three comparisons: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/archive-three-way.json`.
- Exact original/restore captures: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/final-state-0.json`, `final-state-1.json`, `final-state-2.json`.
- All three report `equal_on_recorded_fields`, zero changed paths, and exact mtimes.
- Original checkpoint: 104 entries, 258 mypy errors, step 2, and 97 decisions left.

Tests and raw data:

- Integration suite: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/tests-frozen.log` — 15 tests pass.
- Audit-validator suite: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/audit-validator-final.log` — 13 tests pass.
- Red/green regression: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/sampling-unpatched.log` and `sampling-patched.log`.
- Lint: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/lint-pass.log` — pass.
- Verified bypass: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/bypass-grade-final.json` and its `.verification/` directory.
- Timeout run: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot/fixture-87a6b71b6095401080d7c7c6522f8296`.
- Every technical run: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/run-ledger.json`.
- Every synthetic checkpoint rejection: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/checkpoint-review.json`.
- Loose raw artifacts: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot`.
- Portable raw archive: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/infrastructure-fixtures.tar.gz` — 24,598,352 bytes.
- Raw archive SHA-256: `5ba4b3e7e440c71b4751276f30648685705240113812606cad27ca20d1d80c84`.
- Verified per-run hash manifests: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/raw-verification.json`.
- Provider/credential status: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/evidence/integration/provider-status.json` and `preflight.json`.
- Freeze record: `/home/rucha/ai-alignment-forensics/integrated-pilot/pilot/frozen.json`.

Exact offline commands:

```bash
cd /home/rucha/ai-alignment-forensics/integrated-pilot
python3 pilot/prepare.py

docker build -f pilot/Dockerfile -t integrated-precommit:pilot .

docker run --rm --network none \
  -v "$PWD:/repo:ro" -w /repo \
  -e PYTHONPATH=/repo/upstream/agent-interp-envs/src \
  -e PYTHON_DOTENV_DISABLED=1 -e PYTHONDONTWRITEBYTECODE=1 \
  integrated-precommit:pilot \
  python -m unittest discover -s pilot/tests -v

python3 pilot/run.py fixture \
  --config pilot/configs/archive_fixture.json \
  --image sha256:14bb9a6b1ca097793c25038a6e088e9e33497365bac7e194cc6eeefa1ae14f1e

python3 pilot/run.py restore-check \
  --config pilot/configs/archive_fixture.json --count 2 \
  --image sha256:14bb9a6b1ca097793c25038a6e088e9e33497365bac7e194cc6eeefa1ae14f1e \
  --checkpoint /home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot/fixture-44fad38897894fcf8c74fb97dfec2d5f/data/step-2

python3 pilot/grade.py \
  /home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot/fixture-2cba953c67d648cbb4a9a1e8e33d7545 \
  --verify-image sha256:14bb9a6b1ca097793c25038a6e088e9e33497365bac7e194cc6eeefa1ae14f1e \
  --output /tmp/new-integrated-pilot-grade.json
```

Use a new output path for every grade. Use the existing frozen image for the
recorded gate; a rebuild can yield another image ID and requires a new freeze.
The raw archive extracts relative to this worktree with
`tar -xzf research/evidence/integration/infrastructure-fixtures.tar.gz`.
Do not overwrite the existing local raw directories; extract into a separate
review directory if those paths already exist.

The conditional source command is below. It was not executed:

```bash
python3 pilot/run.py source --config pilot/configs/first_pilot.json \
  --image sha256:14bb9a6b1ca097793c25038a6e088e9e33497365bac7e194cc6eeefa1ae14f1e --count 1
```

## Quirks and discoveries

- Stock restore still fails the original Git/cache comparison before the full archive repair.
- Tar timestamp floats can lose nanoseconds. The supplement restores recorded nanosecond mtimes explicitly.
- The first external comparison failed because JSON changed tuples to lists. Both failed runs remain intact.
- A Git commit left a zombie child. Its PID is not an active process; the new gate records state and distinguishes it.
- The initial Docker build used an invalid local-ID `FROM` reference. The verified base tag repaired that build input.
- The first ad hoc offline constructor probe lacked `/opt` on `sys.path`. Its corrected record makes no model request.
- The host audit environment lacks a `ruff` executable. The final lint check uses the already installed container tool.
- Raw test logs and patch context contain required trailing whitespace. `.gitattributes` preserves those bytes.
- Read-only files and hashes provide tamper evidence, not immutable storage enforcement.
- The latest decision checkpoint remains after a text-only termination; it is not automatically a scientific candidate.
- Actual hidden serving configuration and current account-specific model availability remain unknown.

## Decisions taken — do not reopen

- Preserve both original branches; integrate only reviewed implementation patterns.
- Use exact public initial prompts with Kimi, 258 errors, and 100 total decisions.
- Fix high effort, temperature 1, top-p 1, command timeout 30 seconds, and run wall timeout 14,400 seconds.
- Preserve every source checkpoint and original workspace reference before the next decision.
- Require original-state validation and sampling parity before any source.
- Keep the one-source cap persistent outside raw output directories.
- Keep model-issued attempts separate from verified effects and inferred intent.
- Reject all current synthetic checkpoints for scientific use.
- Stop the paid phase under the absent credential and unpassed provider gate.
- Create no histories or continuations in this stage.

## Decisions open

- Resolution of direct Kimi availability without silent substitution.
- Any necessary external-state restore extension for a real checkpoint.
- Human source-repair episode and information-inventory review for a real trajectory.
- Exact faithful-summary design and semantic information audit.
- Final rubric exceptions, sample sizes, contrast order, budgets, and preregistration.

## Multi-agent coordination

None. No sub-agents were spawned. The task used the existing independent branch
artifacts as evidence and preserved both branches.

## QSCHA state

None. No lesson or practice exercise is active.
