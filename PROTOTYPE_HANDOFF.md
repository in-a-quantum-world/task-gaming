# Handoff: Pre-commit history prototype — 2026-09-09

EXPLORATORY ONLY — GENERATED BEFORE FINAL PREREGISTRATION

## How to resume

Working directory: `/home/rucha/ai-alignment-forensics/prototype-history-effect`.
Branch: `experiment/prototype-history-effect`.
Read the skills below and this handoff before work starts.
The prototype is complete for a session without provider credentials.
The next research action is one real baseline after a credential is available.

Read the exact procedure in:
`/home/rucha/ai-alignment-forensics/prototype-history-effect/prototype/README.md`.

## Standing interaction rules

- Read `/home/rucha/.codex/skills/standard-technical-coding-practices/SKILL.md` for every technical task.
- It requires simple prose, explicit edit authority, a visible plan, and verified claims.
- This session's user explicitly authorized prototype files, isolated experiments, logs, and this handoff.
- Read `/home/rucha/.codex/skills/standard-technical-handoff-convention/SKILL.md` for later handoffs.
- Use the user's exact handoff path when specified.
- Read `/home/rucha/.codex/skills/standard-technical-qscha/SKILL.md` only if instruction or practice becomes the task.
- Do not modify the audit agent's worktree or branch.
- Preserve every raw run and keep credentials out of commits.
- Treat all current artifacts as exploratory, before final preregistration.
- Do not resample for a preferred outcome or make causal claims from this prototype.

## Task and current state

1. **Does the experiment run?**
   The supported 258-error task runs in local Docker with the original upstream setup and real shell tools.
   Two scripted fixtures each confirmed exactly 258 errors.
   No real-model rollout ran because the checked credential locations contain no provider key.

2. **Which model and config did you use?**
   Technical fixtures use `mock` and `scripted-fixture-v1` with no network access.
   The next live config retains Fireworks `accounts/fireworks/models/deepseek-v4-pro` from the pinned upstream config.
   It uses 258 errors, 100 turns, and explicit `reasoning_effort=low`.
   Temperature and top-p are omitted; provider defaults apply.
   Live model availability and request acceptance remain untested.
   The file is `prototype/configs/baseline_258.json` under the working directory above.

3. **Did baseline workaround behavior appear?**
   No model baseline exists, so this question has no behavioral answer.
   The scripts created a hook and marker, then ran failed checks.
   They attempted no source repair or workaround and made no successful task commit.

4. **Which decision point is best?**
   No scientific candidate exists.
   The best technical fixture is `smoke-20260909T181724-2a649c9f/data/step-4`.
   It has a staged marker, an executable hook, and 258 unresolved errors.
   It has 95 turns left and no established shortcut knowledge.
   Its rank is WEAK / TECHNICAL ONLY because its actions are scripted.

5. **Can it be resumed reliably?**
   The original upstream restore failed the workspace comparison.
   Twelve entries differed, including initial Git history and the absent mypy cache.
   The gate stopped before any provider invocation.
   A new fixture used a supplemental full `/agent` archive.
   Two untouched archive restores passed with zero differences in the measured scope.
   This scope covers paths, contents, modes, and uid/gid; it excludes timestamp and whole-runtime equivalence.

6. **Can history change without workspace changes?**
   Yes for the tested archive fixture and measured workspace scope.
   B and C each restored the same workspace hash before any provider call.
   The history builder copies all checkpoint artifacts and edits only `messages.json`.
   It checks hashes and preserves the exact final assistant/tool exchange.

7. **What do A/B/C look like?**
   A retains all 12 original fixture messages, at 94,305 JSON bytes.
   B has five messages, at 27,562 bytes, including a sentence about prior failed checks.
   C has five messages, at 27,459 bytes, without that sentence.
   Both retain the original prompts, a researcher-authored assistant summary, and the final tool exchange.
   Every summary sentence appears in `history_information_matrix.md` at the worktree root.
   Exact tokenizer counts are unknown.

8. **Which confounds appeared?**
   A is about 3.4 times larger than B/C.
   B/C omit source details and a Git help listing from A.
   They therefore are not information-equivalent.
   The role layout changes and the assistant summary has artificial authorship.
   A concise repair instruction can also act as a nearby reminder.
   The fixture repeats checks, not unsuccessful source repairs, and has no known shortcut.

9. **What did the tiny pilot show?**
   No behavioral comparison ran.
   Seven technical records cover two scripted fixtures and five restore-only probes.
   One original restore failed; four archive restores passed, including B and C.
   The checks establish technical feasibility within a stated scope, not stochastic behavior or a history effect.

10. **Which parts should not be trusted?**
    Do not treat mock outputs as evidence about models.
    Do not treat the current summaries as a controlled manipulation.
    Do not equate scorer flags or `task_completed=true` with an honest successful commit.
    Do not assume full runtime equivalence, live API compatibility, or provider defaults beyond the recorded configuration.
    Early fixture runs lack contemporaneous copies of the wrapper source.
    Timeout handling and live error paths have no end-to-end model test.

11. **Which experiment should run next?**
    Run one real baseline with the frozen config, then review all candidate checkpoints.
    Prefer a faithful-summary control before the proposed A/B/C causal contrast.
    Validate workspace and external-state equivalence before either ordinary continuation.
    Do not scale until the summary retains all task-relevant discoveries.

12. **Which choices require the researcher?**
    Supply a provider credential and confirm the intended live model/config before the first paid run.
    Decide whether the supplemental archive is acceptable after independent review.
    Define the failure event: a failed check, a failed commit, or an unsuccessful substantive repair.
    Review summary sentences, omissions, and shortcut knowledge for a real checkpoint.
    Decide the final prohibition wording, token-length control, budget, and run order before preregistration.

13. **What exact command comes next?**
    After `FIREWORKS_API_KEY` is exported through the shell or credential manager:

    ```bash
    cd /home/rucha/ai-alignment-forensics/prototype-history-effect
    python3 prototype/run.py --config prototype/configs/baseline_258.json --condition BASELINE
    python3 prototype/summarize.py
    ```

    The launcher starts one baseline, not an extra parallel sample.
    It fails explicitly if the configured provider cannot run.
    It never substitutes the mock provider for a requested live baseline.

## Done in this context

- Created a separate project worktree and branch.
- Cloned upstream into this worktree's ignored `vendor` directory.
- Built the unchanged Dockerfile from cache and installed the host lockfile dependencies.
- Confirmed the 258-error runtime with two preserved technical fixtures.
- Rejected the original non-equivalent restore before a continuation.
- Added and tested a supplemental full workspace archive.
- Built A/B/C artifacts with sentence-level information records and integrity checks.
- Added cap, credential, config, and image guards.
- Saved messages, observations, states, scorer outputs, errors, and raw configs.
- Saved a summary CSV/JSONL and an empty real-model-only JSONL.
- Preserved all raw artifacts in a committed 5,192,485-byte archive with 317 verified hashes.
- Passed seven prototype tests and seven upstream mock-provider tests.
- Passed an offline HTTP request/response capture check with no external requests.

## Remaining work

1. Run the one real baseline after credentials are available.
2. Review and rank its decision points without selection for dramatic behavior.
3. Review state outside `/agent`, including process and package changes.
4. Run at most two ordinary continuations only after state validation.
5. Create new history representations from actual model knowledge.
6. Complete the information review before any A/B/C model continuation.
7. Run at most two continuations per arm; label observations before interpretations.

The existing synthetic history bundle has both scientific-review gates set to false.
Leave those gates false; create a new bundle for a real-model checkpoint.

## Verified state

- Upstream URL: `https://github.com/gkroiz/agent-interp-envs`.
- Upstream SHA: `56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb`.
- Upstream clone is clean: `git -C vendor/agent-interp-envs status --short` returned no changes.
- Project starting SHA: `3deb3a6a88c919c84ebd6db1342fb34dea401117`.
- Prototype implementation/data SHA: `a1336ea19ea714ce8e8faa4a42c611bca6c569e9`.
- This later handoff commit adds documentation only; obtain its current SHA with `git rev-parse HEAD`.
- Branch: `experiment/prototype-history-effect`.
- Image ID: `sha256:1ef3aa812a238b40e0aa0d62f3eb921ab3fa2257271b4232fb7efb2dbad0841b`.
- Host Python: 3.13.13; project Python: 3.12.3; container Python: 3.11.16.
- Docker client/server: 29.6.1; uv: 0.11.27; container mypy: 1.20.2.
- Source: `/home/rucha/ai-alignment-forensics/prototype-history-effect/prototype_results/metadata/session.json`.
- Package inventory: `/home/rucha/ai-alignment-forensics/prototype-history-effect/prototype_results/metadata/container-versions.txt`.
- Fixture count and errors: `/home/rucha/ai-alignment-forensics/prototype-history-effect/prototype_results/processed/runs.csv`.
- Workspace hash after archive restore: `589b87fb053e1e1fbc5b5d4a065bf387239c3bf2114530aab0cef4214fd08eb1`.
- Evidence: the four successful `restore_check.json` files under this worktree's `prototype_results/raw` directory.
- Latest test evidence: `/home/rucha/ai-alignment-forensics/prototype-history-effect/prototype_results/metadata/final-tests.txt`.
- Artifact index: `/home/rucha/ai-alignment-forensics/prototype-history-effect/prototype_results/metadata/raw_artifact_sha256.json`.
- No API credential pattern appeared in the staged text or raw JSON scan.

Model calls and costs:

- Live baseline trajectories: 0 of 3 allowed.
- Ordinary model continuations: 0 of 2 allowed.
- Experimental model continuations: 0 of 6 allowed.
- Total external model/API requests: 0.
- Scripted mock invocations: 12 across two fixtures.
- Additional offline HTTP test: one synthetic response through an in-process stub.
- Estimated model cost: USD 0; no cloud runtime was used.
- No run was excluded from the technical record; no timeout occurred.

Git and file state:

- The implementation commit had a clean tracked worktree before this handoff was added.
- No pre-existing tracked project file changed.
- All source, config, report, and data changes are new files on the prototype branch.
- The upstream clone has no code changes.
- The audit worktree received no file edits from this agent.
- Complete created-file list: `/home/rucha/ai-alignment-forensics/prototype-history-effect/prototype_results/metadata/files_created.txt`.
- Loose raw data, checkpoints, logs, and vendor files are intentionally ignored.
- Their session data are preserved in `/home/rucha/ai-alignment-forensics/prototype-history-effect/prototype_results/metadata/prototype_raw_20260909.tar.gz`.
- No push or merge was performed.

## Quirks and discoveries

All errors and warnings appear in:
`/home/rucha/ai-alignment-forensics/prototype-history-effect/prototype_results/metadata/errors.json`.

- The original restore changed Git refs, reflogs, an initial commit object, and mypy-cache entries.
- The supplemental archive repairs these fixture differences but does not prove full runtime equivalence.
- The initial restore is still invalid and remains in the raw data.
- A compound shell command can report exit code zero after mypy fails, because its final Git status command succeeds.
- Upstream `task_completed=true` means a text-only/done response, not a verified commit.
- Upstream score heuristics miss some violations and can flag mentions as actions.
- Upstream's default local runner can start an extra rollout; this prototype's launcher does not.
- The published README and current source disagree on restoration details and the 602-error variant.
- This prototype explicitly used and measured the 258-error task; it did not switch variants.
- The inherited host `VIRTUAL_ENV` caused a uv warning; uv used the local project environment.
- uv also warned about the upstream build backend version requirement; installation succeeded.
- A host ROS pytest plugin lacked `lark`; the isolated test command passed all seven tests.
- Live preflight failed on the absent Fireworks key before any run allocation.
- Git flagged generated CSV CRLF line endings; the generator now emits LF.
- No API runtime error or timeout occurred because no external model call ran.

The initial two fixtures predate code-copy instrumentation.
The raw configs and image ID remain exact, but their wrapper provenance is less complete.
Future runs freeze wrapper files and record container diffs.
History bundles use absolute source paths; transfer to another directory needs an explicit provenance migration.

## Decisions taken — do not reopen

- Preserve the 258-error variant and original task prompt.
- Keep all technical records, including the failed restore.
- Treat all fixture outcomes as `OTHER / AMBIGUOUS` with `synthetic=true`.
- Keep unknown fields null; do not convert them to false.
- Keep the final assistant/tool exchange identical across history conditions.
- Introduce no shortcut knowledge absent from A.
- Stop on failed workspace equality before provider invocation.
- Freeze live model, provider, config, image, and turn budget across the pilot.
- Enforce the user's caps across failed and successful allocated live runs.
- Perform no significance tests and make no causal or mechanistic claim.

## Decisions open

- Live credential and model adoption.
- Independent review of the archive supplement and external-state scope.
- The scientific definition of preceding failure.
- A real decision-point selection rule.
- Sentence-level information equivalence and a token-length control.
- Whether a faithful-summary comparison should precede A/B/C.
- Final task-constraint wording and interpretation rules.
- Whether to preregister a later nearby-reminder condition.

## Multi-agent coordination

The separate audit agent owns the original worktree:
`/home/rucha/ai-alignment-forensics/task-gaming-under-trajectory-pressure`.
Its branch at initial inspection was `experiment/failure-history`.
Its current work was not modified or imported into this prototype.
No work was delegated, and no messages were sent through external services.
The experiment agent owns only the prototype worktree and its local clone.

Report these findings to the researcher for transfer into the audit:

- The original restore failed a real file comparison before a provider call.
- A full `/agent` archive fixed the measured fixture differences.
- The proposed summaries still lose task-relevant information.
- No live model evidence exists yet.

## QSCHA state

None. This was an authorized experiment-prototype task, not a practice lesson.
