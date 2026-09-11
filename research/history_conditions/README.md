# Offline history-condition packages

Start with [the condition specification](../HISTORY_CONDITION_SPEC.md).
Then read [the checkpoint comparison](../HISTORY_CHECKPOINT_COMPARISON.md)
and [the confound audit](../HISTORY_COMPRESSION_CONFOUND_AUDIT.md).
The [information map](../HISTORY_CONDITION_INFORMATION_MAP.md) covers both inventories.

Each checkpoint folder contains:

- a detailed inventory and sentence-level draft provenance;
- current source evidence and a faithful chronological representation;
- pinned source/config hashes, archive checks, and budget metadata;
- a pending external review record;
- four prepared candidate message files and manifests.

`prepared/*/VISIBLE_DRAFT.md` presents the candidate message content for review.
`prepared/*/messages.json` is the exact machine candidate.
`A_FULL/messages.json` is a local byte-for-byte copy of its cutoff source.
No raw trajectory was overwritten.

From the prototype worktree, run the offline tests:

```bash
python3 research/history_conditions/test_protocol.py
```

To export a new review draft for the primary checkpoint:

```bash
python3 research/history_conditions/protocol.py build \
  --checkpoint 258_step42 \
  --output /tmp/history-review-258-v2 \
  --allow-draft
```

For the replication:

```bash
python3 research/history_conditions/protocol.py build \
  --checkpoint 108_step32 \
  --output /tmp/history-review-108-v2 \
  --allow-draft
```

Use new output paths if these paths already exist.
Omit `--allow-draft` only after an external reviewer completes the hash-bound review record.
Even a reviewed build remains non-runnable; this script contains no provider interface.

The local source paths are fixed to the two selected checkpoint directories.
The builder validates message boundaries and raw hashes before each export.
Raw files are not committed here as full source workspaces; keep those input checkpoints available locally.
No tokenizer, Docker, provider or task command is needed for this scaffold.
Python's standard library is sufficient.

Known limitation: structural provenance checks cannot prove that a paraphrase faithfully expresses its cited evidence.
That decision remains with the external reviewer.
