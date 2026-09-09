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
