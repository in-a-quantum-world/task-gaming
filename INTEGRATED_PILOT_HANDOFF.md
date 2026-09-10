# Handoff: Integrated Kimi source pilot — 2026-09-10

## How to resume

Working directory: `/home/rucha/ai-alignment-forensics/integrated-pilot`.
Branch: `experiment/integrated-pilot`, based on `experiment/failure-history`.
Read the standing skills and this handoff first. The user authorized exactly one
real source trajectory on Kimi through the verified OpenRouter Novita route.
All offline gates pass. The source has NOT started: the provider preflight returned
HTTP 402 because the account has no purchased credit. The key itself is valid.
The source slot remains unused. The user was asked to fund the account.

After funding, retain the failed preflight and rerun the unchanged frozen command:

```bash
cd /home/rucha/ai-alignment-forensics/integrated-pilot
/home/rucha/ai-alignment-forensics/task-gaming-under-trajectory-pressure/upstream/agent-interp-envs/.venv/bin/python \
  pilot/run.py source --config SOURCE_PILOT_CONFIG.yaml \
  --image sha256:271a3daf958c33c9e6ad7332624015f9303ef06bf2a805abd12004abff8ddbae \
  --count 1
```

This command checks the freeze and runs a new two-request tool preflight before
source allocation. It reads the ignored local `.env`; never print its contents.
Do not lower the token cap or switch a provider to bypass the credit gate.
Record funding and the repeated infrastructure preflight in the research log.

No B/C histories or model continuations are authorized. Stop after the source
trajectory, ordered checkpoint review, independent grading, and updated handoff.

## Standing interaction rules

- Apply `/home/rucha/.codex/skills/standard-technical-coding-practices/SKILL.md`
  to every technical task. Use concise verified prose and the prescribed style.
- The user explicitly authorized the integration edits, tests, logs, source run,
  and this handoff. The user specified this path. No new path approval is needed.
- Apply `/home/rucha/.codex/skills/standard-technical-handoff-convention/SKILL.md`
  to handoffs. Apply the QSCHA skill only for a learning/practice request.
- Preserve both original branches. Do not merge the prototype wholesale.
- Never expose credentials, reset the single-source slot, delete failed/slow runs,
  launch count+1, or silently substitute a model/provider.
- Keep raw reasoning exactly as returned. Use native actions for behavior labels.
- Make no causal claims. Preserve ambiguity and all negative/failed results.

## Task and current state

1. **Which findings agreed?** Both agents found incomplete stock restoration,
   scorer limits, no real source, and inadequate synthetic repair history.
   Both preserved the original total decision budget and measured src_258.
2. **Which disagreed?** The apparent archive dispute concerned scope. The
   prototype did capture an original source inventory. The audit required more
   task-state fields. Original-versus-two-restores validation now covers both.
   Sampling findings concerned different fresh/resume paths; both were correct.
3. **What prototype code was retained?** Reviewed archive/restore patterns,
   exclusive writes, request hooks, persistent caps, and entrypoint wrapper.
   The integration adds original-state probes, exact timestamp restore, final
   workspace recovery, native-message capture, and independent grading.
4. **What was rejected?** Synthetic A/B/C builders/results, old summaries as
   scientific conditions, a three-source cap, omitted sampling defaults, and
   unconditional container deletion. New fixtures test infrastructure only.
5. **Are fresh/resume controlled settings identical?** Yes in automated actual
   constructor and serialized-request tests. They compare exact model, provider,
   backend routing, reasoning enablement, temperature, top_p, tools, and token
   cap. The regression fails on pinned unpatched upstream. Native Kimi effort and
   parallel_tool_calls are not advertised; they are explicitly omitted. Seed is
   supported but intentionally unspecified. Actual server internals are unverified.
6. **Does archive restore match the ORIGINAL?** Yes for the final synthetic
   checkpoint, on all required recorded fields and nanosecond mtimes. Both
   restores also match each other. No real checkpoint exists yet.
7. **What is outside the guarantee?** General external-state restoration, ACLs,
   xattrs, inode/hardlink identity, atime/ctime, processes, kernel/RNG/clock state,
   remote services, hidden provider state, and server-side reasoning use. Relevant
   external files/packages are inventoried and compared, not universally restored.
8. **Is the grader usable?** Yes within its stated bounds. It distinguishes native
   attempts, verified effects, repair evidence, completion, no commit, cap, timeout,
   and ambiguity. It preserves upstream scores separately. Arbitrary scripts and
   semantic source correctness require human review. Earlier controlled bypass
   evidence and the current regression suite remain available.
9. **Did a real Kimi source run?** No. The key authenticated and two earlier small
   smoke calls succeeded. The frozen tool preflight failed at HTTP 402 before the
   single source slot was allocated.
10. **What happened?** The request cap was 16384 tokens. OpenRouter reported credit
    for only 15894 tokens. Read-only account checks report purchased credits zero,
    free-tier status, and no separate key spending limit. No cap was reduced.
11. **Did an eligible checkpoint exist?** Not evaluated: no source trajectory ran.
    This is not a scientifically valid negative pilot result.
12. **Which checkpoint and why?** None selected. The rule remains frozen before
    any source outcome. REAL_CHECKPOINT_REVIEW.md explicitly records this state.
13. **What information had Kimi learned?** No source-task information. Prior smoke
    and preflight conversations are separate from the future source history.
14. **What legitimate repairs occurred?** None in a real source. Synthetic
    infrastructure edits are not scientific repair episodes.
15. **What should run next?** Once funded, the unchanged preflight and exactly one
    source. Then review prefixes in order and record every rejection before the
    next prefix. Validate the first candidate offline before recording selection.
    After that source phase, consider A_FULL versus A_FAITHFUL_COMPACT_SUMMARY.
16. **What requires researcher action/approval?** The account needs usable credit.
    The one source is already authorized. Any continuation/history experiment,
    checkpoint-rule change, provider/model change, or extra source needs an
    explicit amendment. Approximately USD 20 is a conservative token allowance
    at listed prices, not an expected charge or an authorized automatic purchase.

## Done in this context

- Reconciled the two original branches without changes to either branch.
- Adapted the verified OpenRouter route to only `novita/bf16`, no fallbacks.
- Preserved raw decoded API bodies and exact assistant objects before normalization.
- Disabled SDK and outer adapter retries; enforced returned model/provider guards.
- Passed 19 integration tests and 13 inherited audit tests.
- Demonstrated the fresh/resume regression failure on unpatched upstream.
- Passed all three archive comparisons on the final image and verified raw hashes.
- Froze SOURCE_PILOT_CONFIG.yaml and SOURCE_PILOT_PREREG.md before source outcomes.
- Preserved the failed credit preflight and requested account funding.

## Remaining work

1. Wait for usable OpenRouter credit; record the external-state change.
2. Repeat the unchanged frozen preflight through the source command above.
3. If preflight passes, allow exactly one source allocation and preserve all output.
4. Monitor operational counts only. Do not inspect the final behavior first.
5. Review checkpoints in order. Save exclusive prefix decisions before later reads.
6. Validate the earliest candidate with offline restore-check and no model calls.
7. Finish REAL_CHECKPOINT_REVIEW.md, all checkpoint rejections, and grading.
8. Update this handoff with actual source outcomes and the next scientific decision.

## Verified state

All paths below are under `/home/rucha/ai-alignment-forensics/integrated-pilot`
unless written as absolute paths.

- Audit branch: `622703ee2fa109640eb3befa4d4c3a35ef75a194`.
- Prototype branch: `eaedc8fc320ad3d00696e3a17cffdd2bcef2eb7d`.
- Earlier integration: `2dd16ead647bf5510df9166e2ed0ef5bbc45c753`.
- OpenRouter implementation/evidence: `0a3824a`.
- Protocol/config/image freeze: `c79c16a`.
- Framework base: `56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb`, with only the
  recorded fresh-provider-kwargs patch in the isolated upstream checkout.
- Image: `sha256:271a3daf958c33c9e6ad7332624015f9303ef06bf2a805abd12004abff8ddbae`.
- Base image: `sha256:b756b5d4756b6ed05bbbbe2ba55e7b767b422ee86f24ebf496ac8735793afb5d`.
- Canonical config and exact prompt: SOURCE_PILOT_CONFIG.yaml.
- Protocol, episodes, review rule, retries: SOURCE_PILOT_PREREG.md.
- Frozen hashes and evidence: pilot/frozen.json.
- Gate result: research/evidence/integration/openrouter-pilot/offline-gates.json.
- Tests: tests-final-image.log (19 pass), audit-tests.log (13 pass), and
  sampling-unpatched.log (fresh/resume failures), in the same evidence directory.
- Three-way equality: archive-three-way.json, validation-0/1/2.json, and
  external-0/1/2.json in that evidence directory.
- Original fixture: research/data/raw/integrated-pilot/fixture-874c417569b24baabf2811c3544353be/data/step-2.
- Restore 1: research/data/raw/integrated-pilot/restore-check-923f12f4f0b14dd780e8122a9767d709/data/restored.
- Restore 2: research/data/raw/integrated-pilot/restore-check-b452a32f42f64cf59309e0fb7106bd3f/data/restored.
- Each capture has 104 entries, 258 strict errors, step 2, and 97 decisions left.
- Failed preflight: research/data/raw/integrated-pilot/preflight-f310510751d94e7fa71259376bf64a7e.
  It has exact requests/response/error, process output, and a verified hash manifest.
- Credit facts: research/evidence/integration/openrouter-pilot/credit-check.json
  and credit-block-094053.json. Only selected financial fields were recorded.
- Earlier successful access: research/evidence/integration/openrouter-smoke-20260910.json.
- Full methodological decisions: research/RESEARCH_LOG.md.

Exact offline commands:

```bash
docker build -f pilot/Dockerfile -t integrated-precommit:openrouter .
docker run --rm --network none -v "$PWD:/repo:ro" -w /repo \
  -e PYTHONPATH=/repo/upstream/agent-interp-envs/src \
  -e PYTHON_DOTENV_DISABLED=1 integrated-precommit:openrouter \
  python -m unittest discover -s pilot/tests -v
docker run --rm --network none -v "$PWD:/repo:ro" -w /repo \
  integrated-precommit:openrouter \
  python -m unittest discover -s research/scripts -p test_state_equivalence.py -v
python3 pilot/run.py fixture --config pilot/configs/archive_fixture.json \
  --image integrated-precommit:openrouter
python3 pilot/run.py restore-check --config pilot/configs/archive_fixture.json \
  --image integrated-precommit:openrouter --count 2 \
  --checkpoint /home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot/fixture-874c417569b24baabf2811c3544353be/data/step-2
```

## Quirks and discoveries

- OpenRouter's default Google route rate-limited the initial smoke call. Novita
  then served two successful calls. The source route pins the explicit backend.
- A valid key and small free-tier calls did not imply sufficient source credit.
- The SDK wraps a response-hook backend rejection as APIConnectionError. The
  independent routing_violation artifact retains the cause. No action occurs.
- Reasoning replay acceptance does not prove that the server uses previous
  reasoning. The smoke test's prompt-token counts warrant further study.
- Original archives require explicit nanosecond timestamp restoration. Stock
  snapshots omit cache data. Both original and restore evidence are necessary.
- Raw test logs include original trailing spaces. Preserve those bytes; the
  nested log attribute documents the exception instead of editing raw evidence.

## Decisions taken — do not reopen

- Exactly one source; no automatic source replacement or count+1.
- Same Kimi model, OpenRouter only novita/bf16, with no model/backend fallbacks.
- Explicit supported controls and honest reporting of unsupported settings.
- Keep canonical task prompts and the pre-outcome two-episode eligibility rule.
- Preserve failures, visible reasoning, all checkpoints, and original workspaces.
- Interpret native actions and verified effects separately from reasoning text.
- Keep the frozen output cap when free credit is insufficient.

## Decisions open

Account funding is pending. No additional source permission is needed once funded.
If the tool preflight reveals another incompatibility, record it before any repair.
The design and approval of any subsequent history experiment remain open.

## Multi-agent coordination

None. No subagents were spawned. The integration agent owns this worktree.

## QSCHA state

None. No lesson or exercise is in progress.
