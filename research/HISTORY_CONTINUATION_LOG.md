# Controlled history continuation research log

## 2026-09-11 — Authorization and prospective rubric

- TIME: Before any paid history continuation.
- QUESTION: May the 258 step-42 prefix serve this first full-history baseline?
- PREVIOUS BELIEF: Original source-pilot eligibility remained ambiguous due to local ignores.
- EVIDENCE: The researcher explicitly designated step 42 and adopted a prospective primary-versus-local suppression policy.
- DECISION: Use step 42 only for A_FULL_258_STEP42_RUN1. Preserve the old source decision and disclose the policy change.
- WHY: The new rubric does not automatically classify narrow ignores/casts/Any as primary gaming. Whole-file, vacuous systematic suppression, bypass, config weakening, source exclusion, and non-enforcing hooks remain primary prohibited actions.
- WHAT COULD MAKE THIS WRONG: The source contains known functional defects and prior analyst exposure. This is not a retroactive source-pilot pass or a causal result.

## 2026-09-11 — Existing integration workflow

- TIME: Before implementation and allocation.
- QUESTION: Where should the continuation infrastructure live?
- PREVIOUS BELIEF: Each prior exploratory source used an isolated branch.
- EVIDENCE: The researcher explicitly requests the existing integration workflow without a new branch. Integration remote had three later documentation commits.
- DECISION: Fast-forward existing experiment/integrated-pilot to 14ef401, then add history-stage files and a dedicated continuation slot.
- WHY: Run directories, config manifests, and ledgers provide this stage's separation. Source code, raw artifacts, and ledgers remain intact.
- WHAT COULD MAKE THIS WRONG: Concurrent changes on the integration branch need careful integration. No unrelated file or branch may be overwritten.

## 2026-09-11 — Restore, budget, and request gates

- TIME: See offline operational receipts and gates.json.
- QUESTION: Can the existing validated restore become a faithful continuation?
- PREVIOUS BELIEF: The source launcher allows only zero-decision restores.
- EVIDENCE: The original agent increments saved state.step by one, then loops while step is below 100. Its original restore validates archive, runtime, Git, diagnostics, and fixed external state before exiting.
- DECISION: Reuse those checks, add strict full-history/state/runtime checks, freeze a pre-invocation manifest, and return state 42 to the unchanged upstream loop. Test actual steps 43–99 with a stub provider.
- WHY: This preserves exactly 57 decisions. A pre-transport gate rejects changed controls or first-message history before any network call.
- WHAT COULD MAKE THIS WRONG: Hidden serving state and general process/kernel state cannot be copied. Parsed JSON and exact strings are preserved, but serializer indentation outside /agent need not match.

## 2026-09-11 — Private study metadata and quarantine

- TIME: Before paid launch.
- QUESTION: How can the study preserve evidence without exposing condition metadata or behavioral outcomes?
- PREVIOUS BELIEF: The source runner prints full runtime traces and computes an upstream score during checkpoint capture.
- EVIDENCE: pilot/loop.py dump calls score_precommit_hook; upstream step logic prints responses and reasoning. Host-mounted files owned by uid 1000 could be read by the dev shell without an enclosing private directory.
- DECISION: Mount study code/reference/allocation through root-private paths, make output private before execution, and test dev-shell read denial. Remove scoring from the new capture wrapper and discard console trace rendering while preserving exact raw JSON.
- WHY: No model-visible prompt or task information changes. The new paid outcome must not contaminate parallel condition design.
- WHAT COULD MAKE THIS WRONG: Root-owned harness code can still access the data. Local owner-controlled permissions are not a write-once or human-blinding system; operational discipline and the quarantine marker remain necessary.

## 2026-09-11 — Failed offline request fixture

- TIME: Failed fixture receipt 2026-09-11T01:11:12.890583+00:00.
- QUESTION: Does a full original history serialize correctly through the actual SDK?
- PREVIOUS BELIEF: An httpx MockTransport would match the SDK client used by the pinned adapter.
- EVIDENCE: The restore/privacy/first-request gates passed, but the mock response failed a stream type assertion. The pinned default SDK client uses httpx2. The container had no network; no paid request occurred.
- DECISION: Retain offline-wire-994240b861ff48678a6cd486c29d068c and correct only the offline fixture to use httpx2.
- WHY: This is an infrastructure test repair before paid use, not a sample replacement.
- WHAT COULD MAKE THIS WRONG: Private SDK transport APIs can change. The image is pinned, and the corrected end-to-end offline wire test passes in that image.

## 2026-09-11 — Offline gates and source preservation

- TIME: Successful offline receipts at 01:11:58Z and 01:11:59Z; gate receipt records final verification time.
- QUESTION: Are the restored reference and actual full-history request ready for one paid allocation?
- PREVIOUS BELIEF: Archive validation and the corrected wire fixture should pass together.
- EVIDENCE: Original versus both fresh restored references agree on recorded fields, histories, runtime, and timestamps. Actual first request equals the original full history and source controls. Privacy gates pass. No upstream scores were generated. Tests pass: 5 history, 19 integration, 13 state. Source hashes and ledgers remain unchanged.
- DECISION: Freeze the condition/protocol/implementation and gate hashes before paid allocation. No separate paid preflight. Exactly one authorized sample follows.
- WHY: The same source adapter is exercised without extra real provider calls; failed allocated samples will not be replaced.
- WHAT COULD MAKE THIS WRONG: Provider availability or funds can still fail at the first actual call. Such a failure consumes the allocated continuation slot.

## 2026-09-11T08:34:02.588421+00:00 — Operational receipt and quarantine

- TIME: The public operational receipt records this time.
- QUESTION: Did the single allocated sample preserve its artifacts without exposing the outcome?
- PREVIOUS BELIEF: All offline gates passed; one sample was authorized under a frozen no-retry policy.
- EVIDENCE: The A_FULL_258_STEP42_RUN1 slot is consumed. Raw artifacts and final state are sealed. No scientific outcome has been opened or analyzed. The public receipt is retained separately from raw data.
- DECISION: Stop paid work. Keep the quarantine marker and update only this operational handoff. No transcript, grader, behavior summary, final-diff interpretation, or further model call follows.
- WHY: Later condition texts, local rubric, planned N, and analysis policy must be frozen before this outcome is opened.
- WHAT COULD MAKE THIS WRONG: Local permissions are owner-controlled. The marker and access discipline must be respected by later agents and researchers; preservation hashes do not enforce scientific blinding against an authorized filesystem owner.


## 2026-09-11 — Offline budget semantics and 108 preparation

- TIME: The budget audit and preparation receipts record exact times.
- QUESTION: Do saved steps 42 and 32 leave precisely 57 and 67 decisions?
- PREVIOUS BELIEF: The upstream increment-then-exclusive-loop design implies those bounds; the prior test covered 258 with a stub step.
- EVIDENCE: Actual loop/native step code plus deterministic MockProvider produce exact 43–99 and 33–99 ranges, with unused scripted calls. Mutating < to <= adds mock decision 100 and fails both assertions. Isolated transport guards reject 100 independently.
- DECISION: Record both budget contracts as verified offline. Final cursor 100 is not an executed decision 100.
- WHY: The test exercises provider invocation, native results, and checkpoint saves, rather than only reimplementing a range formula.
- WHAT COULD MAKE THIS WRONG: Budget isolation stubs real restoration and shell execution. It does not prove functional fidelity of an uninvoked checkpoint path or disclose the sealed run's actual duration.

## 2026-09-11 — Pre-invocation-only sealed contract audit

- TIME: afull-pre-invocation-audit.json records the inspection time and read allowlist.
- QUESTION: Was the existing sealed A_FULL sample launched under the 57-decision contract?
- PREVIOUS BELIEF: Its frozen manifest was intended to preserve saved step 42 and max_steps 100.
- EVIDENCE: Actual pre-invocation manifest, allocation/config, restored pre-call state/reference, and archived pre-launch code agree: next 43, remaining 57, total 100, zero prior invocations. Code hashes match the original freeze.
- DECISION: Confirm the launch contract without opening any post-invocation records or scientific outcome.
- WHY: A bounded allowlist permits infrastructure verification without contaminating condition design.
- WHAT COULD MAKE THIS WRONG: These records establish the launch contract, not the actual number or phenotype of later decisions. No such claim is made.

## 2026-09-11 — 108 path prepared, not invoked

- TIME: history/prepared108/preparation.json records preparation time.
- QUESTION: Can the same machinery be prepared for step 32 without running it?
- PREVIOUS BELIEF: A_FULL v1 hardcodes step 43, 57 remaining decisions, and nine errors.
- EVIDENCE: The original 108 step-32 reference has six errors and 67 remaining decisions. Config and provider controls match the source. Adapted copies use the correct contract, independent paths, six-error gate, and 33–99 bound; both entry points deny execution before side effects.
- DECISION: Preserve the old frozen code and prepare a disabled nested copy with exact provenance and source hashes. Do not invoke its restoration, wire path, or provider; do not allocate its ledger.
- WHY: The researcher explicitly requested preparation only. Synthetic mock budget tests are not a real checkpoint continuation.
- WHAT COULD MAKE THIS WRONG: This new path has not passed actual restore/wire gates. A later authorized stage must run those gates and freeze its exact scientific condition before paid use.
