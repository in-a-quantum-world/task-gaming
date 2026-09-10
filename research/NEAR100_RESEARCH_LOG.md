# Intermediate source pilot research log

## 2026-09-11 — Prospective variant choice

- TIME: Exact measurement and selection times are in the evidence receipts.
- QUESTION: Which existing image variant is closest to 100 strict-mypy errors?
- PREVIOUS BELIEF: Directory labels might match actual counts but required independent verification.
- EVIDENCE: Actual `mypy src/` as dev measured all 13 variants under the same pristine strict config. Counts match the labels. src_108 is closest, at distance 8.
- DECISION: Fix src_108 and target_errors 108 before any model request. No alternate variant is allowed.
- WHY: This implements the requested prospective choice without a model-outcome selection.
- WHAT COULD MAKE THIS WRONG: Source variants differ in code, not only error count. This is not a causal error-count intervention.

## 2026-09-11 — Isolated source stage

- TIME: Before paid use.
- QUESTION: How can this source preserve the existing 258 and 602 pilots?
- PREVIOUS BELIEF: Both earlier source slots must stay consumed.
- EVIDENCE: Prior ledger hashes and all 258/602 raw manifests verified; recorded in prior-state.json.
- DECISION: Base an isolated near100 worktree on integrated commit 098c788. Reuse unchanged source image/code, with a separate host ledger and raw root.
- WHY: Exactly one new exploratory source is authorized. The reviewed 602 wrapper already implements an independent cap.
- WHAT COULD MAKE THIS WRONG: A future manual ledger reset could defeat the host guard. Never reset any slot.

## 2026-09-11 — Original checkpoint rule

- TIME: Before paid use and future behavior inspection.
- QUESTION: How should the original checkpoint rule constrain review?
- PREVIOUS BELIEF: The earliest eligible prefix must not depend on a later dramatic outcome.
- EVIDENCE: research/SOURCE_CHECKPOINT_RULE.md defines episodes, seven criteria, prefix order, and ambiguity handling.
- DECISION: Keep that rule unchanged. Open one prefix, record all criteria, then open the next. Validate a potential earliest candidate against its actual original archive before selection.
- WHY: Whole-run transcript or grading could reveal future behavior and contaminate the choice.
- WHAT COULD MAKE THIS WRONG: Repair legitimacy and compliance can remain ambiguous. The researcher retains final behavioral and checkpoint adjudication.
