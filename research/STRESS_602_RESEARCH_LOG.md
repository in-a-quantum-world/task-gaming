# 602 stress pilot research log

## 2026-09-10 — Separate stage and controls, before paid requests

- TIME: 2026-09-10, before source allocation; exact gate times are in evidence JSON.
- QUESTION: Can the new difficulty pilot preserve the completed 258 experiment?
- PREVIOUS BELIEF: The old one-source ledger must remain consumed.
- EVIDENCE: `research/evidence/stress602/prior-state.json`; stage cap and config tests.
- DECISION: Branch from integrated commit 098c7886244478bda4363aa969afdda8cf8c46a8. Use a separate 602 ledger.
- WHY: The user authorized one new stage and explicitly protected the 258 result.
- WHAT COULD MAKE THIS WRONG: A future manual ledger reset could defeat the host cap. Never reset either ledger.

## 2026-09-10 — Source and image validation, before paid requests

- TIME: Recorded in `research/evidence/stress602/baseline-602.json`.
- QUESTION: Does the actual original image produce exactly 602 errors?
- PREVIOUS BELIEF: The pinned source contains src_602, but its current error count required measurement.
- EVIDENCE: Actual `mypy src/` as dev in the original image reports 602 errors. Active and pristine config SHA-256 match.
- DECISION: Use the exact original image. Change only task.target_errors in the source config.
- WHY: A rebuild could change dependencies. The source variants differ in code, so this is not a pure abstract error-count intervention.
- WHAT COULD MAKE THIS WRONG: Error count does not establish semantic task equivalence or a causal difficulty effect.

## 2026-09-10 — Archive validation and extra byte check

- TIME: Recorded in `research/evidence/stress602/archive-three-way.json`.
- QUESTION: Do two restores match the actual original synthetic source state?
- PREVIOUS BELIEF: The reviewed archive should preserve all required workspace fields.
- EVIDENCE: Original versus restore 1 versus restore 2 match on all 105 inventory entries, Git, timestamps, diagnostics, runtime, parsed state, exact message strings, and budget.
- DECISION: The required gate passes. State and message JSON serialization is not byte-identical outside /agent; record this limit.
- WHY: An extra byte-equality assertion failed. Inspection showed JSON formatting differences only. Parsed values and validator hashes match. Every /agent file remains byte-identical.
- WHAT COULD MAKE THIS WRONG: This validates a synthetic checkpoint and recorded external state, not a whole machine or every possible model-created external dependency.

## 2026-09-10 — Transcript and classification policy, before outcomes

- TIME: Before the 602 provider preflight or source.
- QUESTION: How should candidate workarounds reach the researcher?
- PREVIOUS BELIEF: The existing grader is useful but insufficient for final scientific labels.
- EVIDENCE: The 258 pilot contains local suppression and semantic defects despite a clean type check.
- DECISION: Freeze candidate categories before the run. Surface native actions and state diffs. Reserve the final classification for the researcher.
- WHY: Reasoning mentions alone are not actions, and local typing choices can be ambiguous.
- WHAT COULD MAKE THIS WRONG: Mechanical searches can miss opaque shell edits or over-report harmless Any annotations. The exact transcript and archives permit review.
