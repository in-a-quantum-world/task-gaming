# First source-pilot configuration

Status: exact local pilot config prepared; paid phase blocked.
Config: `pilot/configs/first_pilot.json`.
Freeze record: `pilot/frozen.json`.

| Field | Explicit value or policy |
|---|---|
| Environment | `precommit_hook` |
| Source | `src_258` |
| Provider | Direct Fireworks Chat Completions adapter |
| Model | `accounts/fireworks/models/kimi-k2-thinking` |
| Endpoint | `https://api.fireworks.ai/inference/v1` |
| Reasoning effort request | `high` |
| Temperature | `1.0` |
| Top-p | `1.0` |
| Provider preferences | Explicit `null`; routing preferences apply only to OpenRouter |
| Tools | Exact pinned upstream `execute_command` schema; one tool action per decision |
| Total decisions | `100` |
| Required checkpoint remainder | At least `30` |
| Command timeout | Upstream default `30` seconds |
| Run wall timeout | `14400` seconds, including setup and checkpoint probes |
| Timeout result | Preserve partial artifacts; no replacement |
| Source trajectory cap | `1` allocated real source attempt |
| Continuations | None in this stage |
| Optional memory, plan, question, done tools | All false |
| Exact output-token cap | API field omitted; factory has no supported output-token parameter |
| Sampling seed | API field omitted; no supported factory seed parameter |
| Source request retries | Unchanged adapter and SDK; recorded per HTTP attempt |
| Preflight retries | None; one non-task request with a 60-second API timeout |

The high effort request and sampling values are explicit pilot choices.
They do not recover the paper's hidden serving configuration or prove that Kimi
interprets effort as another model does. Actual request bodies are preserved.
The four-hour wall policy gives a long repair sequence more room than the
prototype's one-hour policy. The 100-decision cap comes from the user's request.

## Exact published prompt recovery

The first two message objects came from the public Model-Forensics dataset at
commit `9e8a5b84fb432346586f51b0f6580d501b9acbf2`, Kimi precommit run 100.
The extraction inspected only those initial messages. It did not inspect later
model behavior. The raw file hash and extracted strings appear in
`evidence/integration/published-prompts.json`.

Source: [published message file](https://huggingface.co/datasets/Model-Forensics/model-forensics/blob/9e8a5b84fb432346586f51b0f6580d501b9acbf2/precommit_hook/moonshotai-kimi-k2-thinking/2026-03-24_20-33-32-814747/run-100/step-29/messages.json).

The strings are copied exactly into the pilot config, including their whitespace.
They specify the existing mypy policy and the requested final commit message.
No task prompt appendage is enabled. The resolved runtime config and first
messages remain separate preserved artifacts for each source attempt.

System string SHA-256:
`bf6c2dd0644ad3722ffc7f951690177f929c96279d79dd44d7373d210d0b1cb1`.

User string SHA-256:
`58e1c9810401db646fb0943c6c6004e61ee11ef73078b04b9c38b17ae915621c`.

This recovers a published task prompt exactly. It does not establish one
universal prompt across all published runs or the full original run config.

## Provider preflight result

On 2026-09-09 the checked shell and local `.env` paths lack `FIREWORKS_API_KEY`.
No credential value was requested, printed, or stored. No authenticated request
or paid trajectory occurred.

The official [Fireworks model page](https://fireworks.ai/models/fireworks/kimi-k2-thinking)
also lists serverless support as unavailable. That public status is evidence of
a route blocker, not an authenticated account-specific availability test.
The upstream adapter explicitly supports Kimi's identifier and preserves
`reasoning_content`. Those code facts do not establish live endpoint availability.
The [Fireworks reasoning documentation](https://docs.fireworks.ai/guides/reasoning)
requires prior reasoning content for applicable interleaved tool sequences.

The live preflight remains failed or unverified. Do not substitute DeepSeek or
another route. An endpoint/model amendment requires researcher approval and a
new freeze. An account-specific route may exist, but none was established here.
