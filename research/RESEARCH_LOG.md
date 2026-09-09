# Research log

## 2026-09-09 18:10 UTC — Scope

The researcher authorized an autonomous repository audit and local setup.
No A/B/C continuations or final history text are authorized.
A paid pilot needs an unambiguous approved model and environment.
Record all blockers and methodological choices. Do not choose them silently.

The host repository was clean on `main`. Its HEAD is in `evidence/provenance.json`.
Created `experiment/failure-history` in the host repository.
Reference checkouts go under ignored `upstream/`. Research artifacts stay in this repository.
Docker, Python 3.13.13, and uv 0.11.27 are available.
No `.env` file was created. No credential value was read into tool output.

## 2026-09-09 — Pin, build, and configuration evidence

All three public repositories were shallow-cloned and pinned in `evidence/provenance.json`.
The framework and host work branch are `experiment/failure-history`.
All upstream tracked files remain unchanged.
`uv sync --frozen` succeeded with Python 3.12.3. The shell initially reported Python 3.13.13.
The unmodified pre-commit Dockerfile built successfully. No other environment image was built.
The image contains Python 3.11.16 and mypy 1.20.2.
All thirteen source variants were checked. Directory labels matched the measured error counts, including exactly 258 and 602.
The environment README is stale about source 602 and command replay.

## 2026-09-09 — Tests and failures

The initial pytest command failed before collection because the host ROS plugin needed unavailable `lark`.
A clean-environment retry passed 148 tests, skipped 2, and failed 13 credential-dependent tests at provider construction.
That selection included integration tests; absent credentials prevented every API request.
The final selected provider tests exclude integration tests and block socket connections.
That offline suite passed 155 tests, skipped 2, and failed one stale effort-default assertion (`high` versus current `xhigh`).
No upstream tests or defaults were changed to hide this failure.

The new validator unit suite initially passed 11 tests; two additional missing-data/budget tests raised this to 13.
JSON Schema meta-validation passed. The example record passed; malformed and missing primary fields were rejected.
Two complete network-disabled mock smoke artifacts cover the 258 and 602 variants.
No paid model rollout, A/B/C continuation, LLM judge call, or provider discovery call occurred.
Model API calls: zero. Model API spend: $0.

## 2026-09-09 — State validation discoveries

A local deterministic probe confirmed that unchanged initial Git metadata can differ after restore.
It also confirmed that an untouched inherited file can disappear on a second resume.
A same-size byte edit with preserved mtime bypassed the upstream snapshot change gate.
A provider-constructor probe confirmed dropped fresh-run temperature and `top_p`, while resume forwarded both.
Two prepared mock Docker restores showed identical histories but different Git state.

The first validator captures detected their own Git index side effect.
A separate diagnostic isolated `git diff` as the cause, despite `GIT_OPTIONAL_LOCKS=0`.
The final utility sets `diff.autoRefreshIndex=false`; final captures had zero workspace mutations and no missing probes.
Those captures still failed pair equivalence on Git state. Earlier outputs remain intact.
The standalone restore-pair helper reproduced the mismatch with zero model invocations.

Pure filesystem scorer examples returned `good` without a commit and with a non-executable no-op hook.
A command that merely quoted a bypass string triggered `bad`.
These results strengthen the need for a separate behavioral rubric and outcome grader.

## 2026-09-09 — Methodological decisions left open

The candidate baseline is a proposal wrapper, not an approved runnable experiment config.
It proposes the DeepSeek prompt and direct Fireworks adapter with the measured 258 source.
It makes provisional effort and sampling values explicit. The researcher must approve or revise them.
A versus B is a proposed primary contrast. Endpoint definitions, N, exclusions, timeouts, retry rules, and checkpoint choice remain open.
B/C prose, role layout, token-length controls, and any reminder remain unbuilt.
No original-paper configuration or model-generated checkpoint was available.
No relaxed definition of state equivalence or upstream snapshot patch was silently adopted.

## 2026-09-09 — Final runtime cross-check

The same selected offline upstream suite also ran inside the built image with Docker network access disabled.
It passed 156 tests, skipped 1, and failed the same stale effort assertion.
The host run skipped an ownership test that the root container could execute.
The installed container SDK is OpenAI 3.11.0; the frozen host SDK is 2.14.0.
The host dev group installs mypy 2.1.0, while the task image pins 1.20.2.
All error-count claims came from the image, so these host differences did not contaminate the measurements.
The host uv environment lacks a pip module; `uv pip freeze` produced the package inventories.

## 2026-09-09T20:59:16.685248+00:00 — Integration start and gates


- TIME: 2026-09-09T20:59:16.685270+00:00
- QUESTION: Reconcile branches
- PREVIOUS BELIEF: Full archive likely repairs the measured gap
- EVIDENCE: Both handoffs; pinned implementation; source branches 622703e and eaedc8f
- DECISION: Port selected mechanisms only
- WHY: Synthetic histories have no source repairs
- WHAT COULD MAKE THIS WRONG: Real external state may add unsupported dependencies

- TIME: 2026-09-09T20:59:16.685284+00:00
- QUESTION: Sampling parity
- PREVIOUS BELIEF: Fresh drops sampling fields
- EVIDENCE: New constructor test fails unpatched in both provider cases and passes patched
- DECISION: Use shared provider_kwargs in fresh agent.py
- WHY: Fresh and resume need identical explicit fields
- WHAT COULD MAKE THIS WRONG: Provider may normalize fields differently on its server

- TIME: 2026-09-09T20:59:16.685292+00:00
- QUESTION: Source configuration
- PREVIOUS BELIEF: Local prompts might match the published task
- EVIDENCE: Pinned Model-Forensics dataset initial messages differ from both configs
- DECISION: Freeze recovered initial messages; Kimi direct Fireworks; high, 1.0, 1.0; 100 decisions
- WHY: User requested genuine accumulated repair context
- WHAT COULD MAKE THIS WRONG: Published hidden serving settings remain unknown

- TIME: 2026-09-09T20:59:16.685297+00:00
- QUESTION: Paid phase
- PREVIOUS BELIEF: Credentials might still be absent
- EVIDENCE: Shell and checked local .env paths lack FIREWORKS_API_KEY; official page says no serverless support
- DECISION: Do not call a model or substitute a provider/model
- WHY: Required gates do not pass
- WHAT COULD MAKE THIS WRONG: An approved account-specific endpoint may later exist

- TIME: 2026-09-09T20:59:16.685301+00:00
- QUESTION: Archive validation
- PREVIOUS BELIEF: Full /agent archive should pass
- EVIDENCE: Original and both restores match all validator fields and nanosecond mtimes; external gate false
- DECISION: Repair tuple/list comparison, retain both rejected probes
- WHY: Persisted external inventories match exactly
- WHAT COULD MAKE THIS WRONG: Other external-state differences could occur on a real run

- TIME: 2026-09-09T20:59:16.685305+00:00
- QUESTION: Docker build
- PREVIOUS BELIEF: Dockerfile FROM may accept local sha256 ID
- EVIDENCE: image-build.log records Docker registry lookup failure
- DECISION: Use verified existing base tag and record its immutable ID
- WHY: Avoid dependency rebuild and preserve exact installed runtime
- WHAT COULD MAKE THIS WRONG: A moved local tag needs identity re-verification

- TIME: 2026-09-09T20:59:16.685311+00:00
- QUESTION: Checkpoint rule
- PREVIOUS BELIEF: Two failed checks are insufficient repair history
- EVIDENCE: Audit and prototype agree their fixtures contain no repair episodes
- DECISION: Freeze SOURCE_CHECKPOINT_RULE.md before source outcomes
- WHY: Prevents outcome-selected checkpoints
- WHAT COULD MAKE THIS WRONG: Operationalized episodes still require human diff review

## 2026-09-09T21:04:34.774008+00:00 — Full archive versus actual original

- TIME: 2026-09-09T21:04:34.774034+00:00
- QUESTION: Full archive versus actual original
- PREVIOUS BELIEF: The comparator fix should permit equal external inventories
- EVIDENCE: fixture-fb0f9fc8 and restores bdcbaee0 / 82a29523 match all required fields
- DECISION: Retain full archive; repeat checks on the final image
- WHY: The original reference has 104 entries, 258 errors, step 2, and 97 decisions left
- WHAT COULD MAKE THIS WRONG: A real trajectory may use external files beyond this fixture

## 2026-09-09T21:04:34.774051+00:00 — Unexpected process record after a test commit

- TIME: 2026-09-09T21:04:34.774057+00:00
- QUESTION: Unexpected process record after a test commit
- PREVIOUS BELIEF: Any dev PID might mean active work
- EVIDENCE: fixture-17cefda3 stops after the native test bypass; fixture-2cba953c identifies git state Z
- DECISION: Record all observed dev processes; block active processes and exclude defunct PIDs from equality
- WHY: A zombie executes no code; process identity remains outside the guarantee
- WHAT COULD MAKE THIS WRONG: Other live background processes or kernel resource effects remain possible

## 2026-09-09T21:04:34.774066+00:00 — Grader action proof

- TIME: 2026-09-09T21:04:34.774070+00:00
- QUESTION: Grader action proof
- PREVIOUS BELIEF: A command flag does not prove successful bypass
- EVIDENCE: bypass-grade-first.json verifies a descendant commit with 258 errors and native --no-verify action
- DECISION: Report both attempt and successful effects; retain upstream score
- WHY: Committed-tree checks avoid confounding unstaged errors with committed errors
- WHAT COULD MAKE THIS WRONG: Arbitrary shell code or semantic source deletion can require manual adjudication

## 2026-09-09T21:04:34.774078+00:00 — Timeout preservation

- TIME: 2026-09-09T21:04:34.774081+00:00
- QUESTION: Timeout preservation
- PREVIOUS BELIEF: The wrapper should retain partial source state
- EVIDENCE: fixture-87a6b71b exit code124; timeout flag true; final workspace tar and logs retained
- DECISION: Keep timeout in the dataset and never replace it automatically
- WHY: A slow honest repair must not disappear
- WHAT COULD MAKE THIS WRONG: A host crash or exhausted disk could still leave incomplete artifacts

## 2026-09-09T21:04:34.774088+00:00 — Synthetic test scope

- TIME: 2026-09-09T21:04:34.774091+00:00
- QUESTION: Synthetic test scope
- PREVIOUS BELIEF: Prototype histories were useful only as fixtures
- EVIDENCE: No real source exists and old summaries lose information
- DECISION: Port no A/B/C builders or result bundles; new fixtures test infrastructure only
- WHY: Keeps the integration branch interpretable
- WHAT COULD MAKE THIS WRONG: A later test may need additional protocol-specific fixtures

## 2026-09-09T21:09:57.300369+00:00 — Final validation and source decision

- TIME: 2026-09-09T21:09:57.300383+00:00
- QUESTION: Can this stage launch a real source?
- PREVIOUS BELIEF: Offline repairs could pass while credentials remain absent
- EVIDENCE: Final image 14bb9a6b; three-way archive equality; 15 integration tests; 13 audit tests; lint pass; provider-status.json
- DECISION: Freeze the exact config and validated implementation; paid phase remains unrun
- WHY: No existing Fireworks key and no successful Kimi availability preflight
- WHAT COULD MAKE THIS WRONG: An approved account route could later become available; any configuration amendment needs a new record

No eligible real checkpoint exists. All 21 preserved synthetic checkpoints are rejected for scientific use.
No history summaries, B/C artifacts, or model continuations were created.

- TIME: 2026-09-09T21:10:38.279031+00:00
- QUESTION: Can the exact Kimi request object be constructed offline?
- PREVIOUS BELIEF: The installed adapter should construct the frozen request without network access
- EVIDENCE: First python -c probe lacked /opt on sys.path; corrected probe records prepared-kimi-request-final.json
- DECISION: Keep both artifacts; use the corrected offline constructor record
- WHY: The failure belongs to the probe import path, not model availability
- WHAT COULD MAKE THIS WRONG: A live server may reject or normalize a field despite successful offline construction
