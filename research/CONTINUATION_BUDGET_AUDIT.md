# Offline continuation-budget audit

Date: 2026-09-11. All runs here use deterministic mock responses and synthetic
state cursors. No actual source checkpoint was restored in this audit. No model
API call occurred. The sealed A_FULL scientific outcome remains unopened.

| Source reference | Saved cursor | First permitted decision | Last permitted decision | Maximum decisions | Decision 100 |
|---|---|---|---|---|---|
| 258 step 42 | 42 | 43 | 99 | 57 | Rejected |
| 108 step 32 | 32 | 33 | 99 | 67 | Rejected |

The pinned agent increments the saved cursor once after restore, then executes
while step < max_steps. max_steps remains 100. Each decision is saved before the
cursor increment. A final cursor of 100 therefore means decision 99 was the last
allowed decision; it does not mean the model made decision 100.

## Deterministic evidence

The audit executes the actual pinned agent loop, original run_step implementation,
and actual MockProvider. The provider has more commands than either budget permits,
so script exhaustion cannot cause the observed stop. Each decision produces a
native mock call and tool result; actual checkpoint.dump writes synthetic state
and messages. Shell execution is a deterministic recorder. The synthetic restore
stub supplies only a cursor; this isolates budget semantics from archive fidelity.

The valid runs invoke/save exactly 43–99 (57 calls/results) and 33–99 (67 calls/results).
They retain unused scripted commands and never invoke 100. The transport guards
independently reject 100 and 101, as well as a decision before the valid start.
They also reject a missing pre-invocation manifest. Guard checks execute isolated
factory AST code with a fake client; no checkpoint restore or real provider is used.

Two deliberate in-memory mutations replace < with <= in the loop. Both then emit
an extra **mock** decision 100 and fail the exact-range regression assertions.
These negative fixtures do not modify the pinned implementation. Their artifacts
are explicitly labeled mutant; they are not scientific continuations.

Docker runs with --network none, dotenv disabled, and socket connection rejection.
The pinned image ID is
`sha256:271a3daf958c33c9e6ad7332624015f9303ef06bf2a805abd12004abff8ddbae`.
The image's agent.py hash matches the pinned local upstream copy. Full mock step
lists and guard/mutation evidence are in
[mock-budget-receipt.json](evidence/history/budget-audit/mock-budget-receipt.json).

## Sealed A_FULL launch contract: pre-invocation evidence only

The actual A_FULL pre_invocation_manifest.json records saved step 42, next step
43, remaining_decisions 57, max_steps 100, and zero provider invocations so far.
Its contract/config, allocation state, image/implementation paths, original
restored state, and checked runtime agree. The allocation cites pre-launch freeze
commit c6660b9d6c1d36f6af2b198dd51dc58f8dbee5b6. Archived pre-launch loop/contract/
bootstrap files match the frozen hashes. Their guard forbids decision 100.

Only an explicit allowlist of pre-invocation records inside the sealed directory
was read. The receipt lists each path and SHA-256:
[afull-pre-invocation-audit.json](evidence/history/budget-audit/afull-pre-invocation-audit.json).
No API responses, post-invocation histories, saved behavioral checkpoints,
termination records, final diffs, or scientific outcomes were opened. This verifies
the **launch contract**, not the number of decisions actually taken by that run.

## Prepared 108 path

[history/prepared108](../history/prepared108/README.md) contains reviewed copies of
the same launcher/bootstrap/contract/restore/transport-guard machinery, adapted
for the actual src_108 step-32 reference and 67-decision range. Its config exactly
matches the original 108 source. The error-count gate expects six diagnostics.
Every code change is visible in ADAPTATION.diff. Original frozen A_FULL files and
source ledgers remain unchanged. No new branch was created.

The prepared path is disabled at both main and launch, before any side effect.
No 108 restore, continuation, paid call, or ledger allocation was invoked. Synthetic
cursor/guard tests do not certify this uninvoked path's archive or wire fidelity.
Fresh offline restoration/wire gates and new researcher authorization remain
necessary before future execution. No scientific history condition was created.

## Commands and artifact locations

Executed inside the pinned image, with the repo read-only and an output mount:

```bash
python /repo/history/budget_audit/mock_runs.py /evidence/mock-runs
```

The complete host Docker command is recorded in command.json under the evidence
directory. Synthetic artifacts were then preserved locally at
`/home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/budget-audit/mock-runs-20260911`.
Their manifest is tracked as mock-artifact-sha256.json. No source or sealed paid
artifact was moved or modified. Files are 0400 and directories 0500; hashes provide
bounded tamper evidence, not external write-once storage.
