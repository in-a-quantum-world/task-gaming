# Step42 faithful-history candidate

Status: **candidate for human review; no continuation or model call**.
All new work is on `experiment/failure-history`.
The `experiment/integrated-pilot` branch and its raw source files remain unchanged.

The source is the real `moonshotai/kimi-k2-thinking` trajectory through step42.
No later trajectory content or source outcome is part of these artifacts.
This candidate compares A_FULL with A_FAITHFUL_COMPACT_SUMMARY.
It is not a B/C history intervention.

The researcher recorded the revised framing in
[Pilot Observation 001](../PILOT_OBSERVATION_LOG.md): **preceding repair/effort
trajectory at a fixed current state**. Repeated visible failure is a future
extension. The targeted ignores remain unclassified as violations.

## Review documents

| File | Purpose |
| --- | --- |
| [STEP42_INFORMATION_INVENTORY.md](../STEP42_INFORMATION_INVENTORY.md) | 392 evidence items, including each diagnostic, every code read/write, eight targeted ignores, and external state facts. |
| [A_FAITHFUL_COMPACT_SUMMARY_DRAFT.md](../A_FAITHFUL_COMPACT_SUMMARY_DRAFT.md) | Full proposed history for review, with exact instructions, the full initial diagnostic output, a cited summary/code ledger, and the exact terminal observations. |
| [STEP42_INFORMATION_MATRIX.md](../STEP42_INFORMATION_MATRIX.md) | Item-by-item comparison of information availability in A_FULL and the candidate. |
| [SUMMARY_CONFOUND_AUDIT.md](../SUMMARY_CONFOUND_AUDIT.md) | Information, salience, authorship, roles, chronology, repetition, length, and recency risks. |
| [MESSAGE_STRUCTURE_PROPOSAL.md](../MESSAGE_STRUCTURE_PROPOSAL.md) | Unapproved message layout, exact invariants, fixed state, and export limits. |
| [STEP42_VISIBLE_REASONING_TRANSCRIPT.md](../STEP42_VISIBLE_REASONING_TRANSCRIPT.md) | Unabridged visible reasoning through step42, with original content/calls/results and per-message provenance. |

The conservative candidate retains every source-file read and all source edits.
It replaces repeated full-file writes with exact diffs and compresses deliberation.
It contains **114,576 visible-text characters**, versus **155,502** in A_FULL.
That is a **26.3186% character reduction**, without padding.
Actual model token counts remain **unknown**.

The central review issue is authorship and salience.
The proposal moves middle tool evidence into researcher-authored assistant content.
Its prose also makes the eight targeted ignores explicit beside their code.
Textual preservation does not establish an equivalent cognitive state.

## Exact checks completed

- All 43 raw prefix checkpoints match the step42 message list.
- All 88 transcript messages match their raw visible fields.
- All 43 visible reasoning strings match the source, without abridgement.
- The 16 rendered edit diffs reconstruct the exact written versions with GNU `patch`.
- All 14 final edited source files match the original step42 workspace archive.
- The hook, original mypy configuration, empty marker, and empty `__init__.py` match source evidence.
- Original instructions, all 258 initial errors, and all nine final errors remain exact.
- The final raw assistant/tool objects match [final_pair.json](final_pair.json).
- Four negative checks reject transcript tampering, a removed ignore, an altered final result, and a source path outside the cutoff.

The verifier applies patches only to temporary text files.
It never executes Kimi's source code or commands.
It never restores an agent environment or calls a provider.

Reports: [verification_final.json](verification_final.json),
[negative_checks.json](negative_checks.json),
[measurements.json](measurements.json), and
[source_provenance.json](source_provenance.json).

## Transcript preservation

The transcript has mode0444 and a detached SHA-256 record.
The exporter refuses an overwrite. Its original bytes remain unchanged.
The attempt to set `chattr +i` failed with `Operation not permitted`.
Thus the export is read-only and tamper-evident, not filesystem-enforced immutable.
Any correction needs a new version.

No credential values were found in the visible fields.
The export excludes provider bookkeeping and hidden metadata.
Application source text contains an auth-header helper, but no recorded request headers or secret values.

## Recheck without model calls

```bash
cd /home/rucha/ai-alignment-forensics/task-gaming-under-trajectory-pressure
python research/scripts/verify_step42_candidate.py
```

The verifier needs the local raw step42 source and GNU `patch`.
It prints a report and changes no saved research artifact unless `--report`
names a new file. No new model/API call or continuation is required.
The final check also verifies all 28 messages displayed in the candidate draft.

To verify only the sealed transcript:

```bash
cd /home/rucha/ai-alignment-forensics/task-gaming-under-trajectory-pressure/research
sha256sum --check step42/transcript.sha256
```

The build script is
[build_step42_candidate.py](../scripts/build_step42_candidate.py).
It accepts a fixed `--source-checkpoint`, a new `--output-root`, and `--curation`.
It pins the exact source hash and rejects any other cutoff.
The manual, cited prose is in [curation.json](curation.json).
The [summary_body.txt](summary_body.txt) file is the proposed replacement content.
It has not been installed into a checkpoint or submitted to a model.

## Validation limits and resolved issues

The first export attempt assumed an extra newline in empty tool output.
Its assertion stopped the export before the documents were written.
The parser was corrected against raw strings, and independent verification passed.

Ruff was unavailable locally and absent from the offline `uv` cache.
No package download occurred. Both scripts passed Python syntax checks and
explicit 80-column/trailing-whitespace checks. `git diff --check` passed;
the new files also received direct checks because they are untracked.

The source filename search was broader than the eventual content allowlist.
No contents or outcomes outside step42 were opened or used.
This discovery limitation is recorded in the confound audit.

No hypothesis, history wording, role assignment, or sample size is approved
by this export. The researcher still needs to review the candidate and its confounds.
No commit, push, model call, or continuation occurred during this task.

## Observation-log addendum

Pilot Observation 001 was added after the original candidate export.
The original [artifact manifest](artifact_manifest.json) remains a snapshot of that export.
The [updated manifest](artifact_manifest_observation_001.json) records the log and index update.
The candidate history, source evidence, and sealed transcript remain unchanged.
