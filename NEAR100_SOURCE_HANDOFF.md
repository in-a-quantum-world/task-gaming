# Handoff: one prospective 108-error Kimi source

## How to resume

Worktree: /home/rucha/ai-alignment-forensics/near100-source-pilot.
Branch: experiment/near100-source-pilot.
This is the pre-source handoff. Read NEAR100_SOURCE_PREREG.md before action.

## Standing interaction rules

Apply /home/rucha/.codex/skills/standard-technical-coding-practices/SKILL.md and
/home/rucha/.codex/skills/standard-technical-handoff-convention/SKILL.md.
The user authorized one isolated source, the existing preservation machinery,
and chronological application of the original checkpoint rule.
Do not expose credentials, reset source ledgers, or run model continuations.

## Task and current state

All 13 generated variants were independently measured in the original image.
The selected existing variant is src_108, exactly 108 strict-mypy errors.
The selection was fixed before any model request. No source has yet run.

## Done in this context

Created an isolated branch from integrated-pilot at 098c7886244478bda4363aa969afdda8cf8c46a8.
Recorded the unchanged 258 and 602 ledger/raw hashes. Adapted reviewed host-stage
infrastructure with a separate near100-source-slot.json. Source image/code unchanged.

## Remaining work

Finish all offline gates, commit the freeze, preflight, and run exactly one source.
Review each prefix chronologically before whole-run analysis or transcript rendering.
Validate a potential earliest checkpoint with two offline restores before selection.
Preserve all artifacts and report provisional findings for researcher adjudication.

## Verified state

- Image: sha256:271a3daf958c33c9e6ad7332624015f9303ef06bf2a805abd12004abff8ddbae.
- Upstream: 56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb, with existing sampling patch.
- Measured variants: research/evidence/near100/variant-counts.json.
- Selection: research/evidence/near100/selection-freeze.json.
- Exact source config: NEAR100_SOURCE_CONFIG.yaml; only target_errors changes from 258 to 108.

## Quirks and discoveries

The original checkpoint rule excludes comment-only edits and suppression from repair episodes.
Ambiguous prefix compliance blocks automatic eligibility. Researcher adjudication is final.

## Decisions taken — do not reopen

One prospective src_108 source. No outcome-based retry, model fallback, or alternate variant.
Previous pilots remain intact. No A/B/C histories or model continuations.

## Decisions open

Researcher behavioral and checkpoint adjudication after ordered review.

## Multi-agent coordination

None.

## QSCHA state

None.
