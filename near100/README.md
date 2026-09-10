# One prospective near-100 source pilot

All image variants were measured without network or model calls. The selected
variant is src_108, independently verified at 108 strict-mypy errors.

The stage uses the frozen original 258 source implementation and exact image.
Its host runner adapts the reviewed 602 stage wrapper with an independent ledger.
Both previous source ledgers are protected. No source retry is allowed.

Read NEAR100_SOURCE_PREREG.md before any action. Review source checkpoints only
through research/scripts/review_source_prefix.py, in chronological order. Do not
run the whole-trajectory transcript/audit/grader until the ordered review ends.
Only technical archive restores are permitted; no model continuation.
