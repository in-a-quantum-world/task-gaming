# Prepared history collection — execution locked

This nested adapter preserves the frozen v1 A_FULL implementation.
It contains no treatment prose and does not open paid outcomes.
The code is prepared for the proposed 32-slot design; 31 slots remain prospective.
No current count or draft file authorizes execution.

`EXECUTION_ENABLED = False` locks every host launch, including 108 restores.
`RELEASE_ENABLED = False` independently locks outcome normalization and packet export.
Do not change these locks without the corresponding researcher instruction and recorded gates.

## Files and safe offline commands

From the integration worktree:

```bash
python3 -B history/collection/test_collection.py
python3 -B history/collection/schedule.py --root . \
  --output /tmp/history-schedule-review.json
```

The second command creates a new draft only and refuses an existing output path.
`draft_schedule.json` records seed 20260911, block IDs, checkpoint strata, and replicate numbers.
Its condition hashes are null until external approval. Config hashes are already pinned.
Keep the original A_FULL sample in row 0; do not randomize or execute it again.

After external text approval, `freeze.py` can copy exact reviewed files into a new review bundle.
It never constructs summaries and never marks that bundle execution-authoritative.
It accepts a prototype `reviewed_dry_run` export plus separate final researcher approval.
See `approval_index.template.json` and `condition_review.template.json`.
Use immutable content hashes from the external review; do not compute approval from an unreviewed draft.

```bash
python3 -B history/collection/freeze.py --root . \
  --draft history/collection/draft_schedule.json \
  --approvals-index /path/to/approved-index.json \
  --output /path/to/new-review-bundle
```

This command does not call a model, restore a checkpoint, or allocate a continuation ledger.
The resulting schedule remains a review candidate, with execution_authorized=false.
Final freeze and activation require the researcher to approve the exact review artifacts.

## Runtime design for later activation

`run.py` reuses the original host launcher's Docker, timeout, capture, and recovery methods.
`loop.py` reuses the original checkpoint restore and archive capture machinery.
The original history must match the original workspace reference first.
Only then may the approved external message array replace provider.messages.
The exact original prompts and final assistant/tool pair remain fixed.
The first serialized HTTP request must match the frozen history and source controls.
Every later request must retain source controls and the correct remaining budget.

No SDK/adapter/outer retry or paid preflight is added.
The inherited telemetry preserves exact visible reasoning and native calls/results in sealed raw files.
The loop does not call the upstream or independent behavior grader.
The host emits operational receipts only. New markers require collection-wide release.

`ledger.py` allocates one exclusive file per future sample in the common Git directory.
It rejects the historical A_FULL ID and checks prior scheduled operational receipts.
It uses O_EXCL, fsync, a shared lock, and separate completion records.
An allocated failure consumes its slot even when no provider response arrives.
Source ledgers and the original A_FULL ledger remain unchanged.
Owner-controlled permissions are bounded preservation, not external write-once storage.

The prepared interface handles one specified scheduled sample per launch.
After authorization, a serial operator follows the frozen order and waits for each operational receipt.
Never launch all B first, skip a slot for its behavior, or invoke count+1.
Stop on infrastructure failure, preserve its slot, and review infrastructure before later scheduled slots.

## Gates that still block freeze or activation

- Final external condition text, semantic/role audits, and hash-bound researcher approval.
- Final primary and local-suppression rubrics, analysis policy, and planned N.
- Activation review of the new adapter; its host and container paths remain uninvoked.
- Actual ORIGINAL-versus-two-restores fidelity tests for the final 258 and 108 adapter.
- Exact request serialization gates for each final checkpoint/condition payload.
- A synthetic host-launch/recovery/ledger acceptance test for the final adapter.
- Hash-bound gate receipts, implementation/config/source pins, and explicit collection authorization.

Prior original A_FULL and budget tests support this work; they do not certify the new adapter.
`gates.py` prepares receipt extraction from identified synthetic validation directories only.
`freeze.template.json` leaves these gates empty and authorization false.
Removing one execution lock alone cannot satisfy the manifest, approval, ledger, and request checks.

The grading workflow has a separate release gate and acceptance review.
See `research/HISTORY_BLIND_GRADING.md`. No current sealed artifact is an input to this preparation.
