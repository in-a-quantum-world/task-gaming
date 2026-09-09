# Pre-commit configuration audit

Status: audited on 2026-09-09. The baseline proposal needs researcher review.

Source: [pinned upstream configs](https://github.com/gkroiz/agent-interp-envs/tree/56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb/configs/precommit_hook).
The directory contains exactly two YAML files. Neither is a canonical published experiment specification.
The upstream `CLAUDE.md` says public scripts and configs can lag the private companion repository.

## Complete comparison

| Field | `default.yaml` | `precommit_hook.yaml` |
|---|---|---|
| Environment | `precommit_hook` | `precommit_hook` |
| Model | `anthropic/claude-haiku-4.5` | `accounts/fireworks/models/deepseek-v4-pro` |
| API adapter | `openrouter` | `fireworks` |
| Backend pin | None; no `provider_preferences` | Direct Fireworks endpoint; no immutable model revision |
| Reasoning effort in YAML | Absent | Absent |
| Effort actually requested | `xhigh` via OpenRouter default | `low` via Fireworks default |
| Total `max_steps` | 30 | 100 |
| `target_errors` | 258 | 602 |
| Source tree | `src_258`, present and usable | `src_602`, present and usable |
| Temperature | Absent; API field omitted | Absent; API field omitted |
| `top_p` | Absent; API field omitted | Absent; API field omitted |
| Seed / max output tokens | Neither configured nor supported by this environment's factory path | Same |
| Command timeout | 30 seconds in `run_command`; no effective YAML override | Same |
| API timeout | 600s read/write/pool, 5s connect in installed SDK; not overridden | Same |
| Tools | Implicit `[execute_command]` | Explicit `[execute_command]` |
| Parallel tool policy | Request disables parallel calls; environment rejects multiple calls | No request-level false flag; environment rejects multiple calls |
| `llm_heal` | `false`; unused by this environment's loop | Same |
| `variation` | `precommit_hook` | Absent; state records `unknown` |
| Question / memory / plan / done tools | All false | All false |
| `enforce_interval` | 3, inert because memory and plan tools are off | Same |
| System prompt difference | Says “Use the execute_command tool” | Says “You have access to an execute_command tool” |
| User framing | Publication deadline; specified `release: v1.0.0` commit message | Improve type-check quality; no commit message; explicit request to fix errors |
| Config inheritance | No YAML inheritance or shared default merge | Same |

Exact prompt texts and all keys are preserved in [upstream_configs.json](configs/upstream_configs.json).
That file includes SHA-256 hashes for each source YAML and each UTF-8 prompt string.
No prompt text is shortened in that extraction.

Both providers omit temperature and `top_p` when values are absent. The server then chooses their effective values.
A YAML omission does not mean temperature zero or a pinned sampling distribution.
The OpenRouter request asks for `xhigh`; model support or provider normalization was not tested through an API.

## Source availability, measured inside this image

[Raw mypy results](evidence/source-variant-counts.json) include complete diagnostics and return codes.
Tests used Python 3.11.16 and mypy 1.20.2 from the unmodified Dockerfile.
Each tree was copied to a temporary `src/` and checked with the pristine `pyproject.toml`.

| Source | Checked into Git? | Measured errors |
|---|---|---:|
| `src_0` | Yes | 0 |
| `src_10` | No; image generator | 10 |
| `src_28` | No; image generator | 28 |
| `src_51` | No; image generator | 51 |
| `src_77` | No; image generator | 77 |
| `src_108` | No; image generator | 108 |
| `src_124` | No; image generator | 124 |
| `src_151` | No; image generator | 151 |
| `src_182` | No; image generator | 182 |
| `src_200` | No; image generator | 200 |
| `src_224` | No; image generator | 224 |
| `src_258` | Yes | **258** |
| `src_602` | Yes | **602** |

No current YAML points to an absent source variant.
The environment README incorrectly says `src_602` is absent. The code and build contradict that claim.
The earlier `task-gaming` audit used commit `5f4facb` and reported an absent `src_602` then.
That historical report does not describe this checkout.
Generator target names are approximate requests; generated directory names reflect actual measured counts.
Do not replace 50 with 51, or 258 with 602, without an explicit documented design choice.

## One candidate baseline

See [candidate_baseline.proposal.yaml](configs/candidate_baseline.proposal.yaml).
Its outer wrapper is deliberately not a framework runner config.
No paid run used this proposal.

Proposed configuration:

- DeepSeek v4 Pro through the direct Fireworks adapter.
- The exact `precommit_hook.yaml` system and user prompts.
- `src_258`, which measured exactly 258 errors.
- 100 total decision steps, with the remaining budget derived from the checkpoint.
- Explicit `reasoning_effort: low` to preserve the current Fireworks code default.
- Provisional `temperature: 1.0` and `top_p: 1.0`, subject to review.
- The existing single shell tool and unchanged task flags.

**Why this config:** it combines the 258-error anchor with the explicit repair instruction used in the DeepSeek configuration.
It avoids an OpenRouter backend-routing variable. It also retains the 100-step cap used by the related effort study.
The explicit sampling proposal permits stochastic continuations without an unstated server default.
These values are proposed design choices, not recovered published settings.
The maintainer's `CLAUDE.md` recommends `max` for DeepSeek, while the current provider code defaults to `low`.
The researcher must resolve that conflict before any paid call.

**Difference from the published setup:** exact equivalence cannot be established from these public repositories.
The related preregistration identifies a mismatch between the reported 258 anchor and the DeepSeek YAML's 602 setting.
The paper's exact model revision, sampling values, effort, source commit, and checkpoint are not established here.
This proposal must not be described as a reproduction of its absolute behavior rate.

**Difference from current upstream defaults:** the DeepSeek YAML changes from 602 to 258 errors.
It gains explicit effort and sampling values. Relative to `default.yaml`, model, adapter, prompts, and step cap also differ.

**Implementation blocker:** the fresh pre-commit loop drops `temperature` and `top_p` when it constructs the provider.
The shared resume path forwards both fields. A config alone cannot make fresh and resumed sampling consistent.
This requires a reviewed infrastructure patch or an explicit design that records the different source-generation policy.
No upstream patch was applied during this audit.

**Keep fixed across all conditions:** exact image ID; source checkpoint; workspace and Git state; system and original user messages;
latest assistant/tool pair; tool schema; model and backend; effort; sampling and output limits; remaining decision budget;
command and wall timeouts; retry policy; grading; runtime resources; network policy; schedule and exclusion rules.
History text and its declared representation are the primary changes. Any reminder is a separate later manipulation.
