# Compression and confound audit

These are candidate-condition audits without behavioral evidence.

| Checkpoint | Condition | Role sequence | Messages | Unicode characters | UTF-8 bytes | Canonical JSON bytes | Actual tokens |
|---|---|---|---:|---:|---:|---:|---|
| 258_step42 | A_FULL | system,user,(assistant,tool)×43 | 88 | 155502 | 155512 | 196394 | unknown |
| 258_step42 | A_FAITHFUL_COMPACT | system,user,assistant,assistant,tool | 5 | 118146 | 118156 | 124065 | unknown |
| 258_step42 | B_EFFORT_HISTORY | system,user,assistant,assistant,tool | 5 | 60637 | 60643 | 64447 | unknown |
| 258_step42 | C_CURRENT_STATE | system,user,assistant,assistant,tool | 5 | 59390 | 59396 | 63179 | unknown |
| 108_step32 | A_FULL | system,user,(assistant,tool)×33 | 68 | 131172 | 131174 | 164321 | unknown |
| 108_step32 | A_FAITHFUL_COMPACT | system,user,assistant,assistant,tool | 5 | 94552 | 94554 | 100809 | unknown |
| 108_step32 | B_EFFORT_HISTORY | system,user,assistant,assistant,tool | 5 | 56463 | 56465 | 60157 | unknown |
| 108_step32 | C_CURRENT_STATE | system,user,assistant,assistant,tool | 5 | 55397 | 55399 | 59073 | unknown |

All final assistant/tool objects and original system/user objects compare equal to the source.

A_FULL also matches the raw messages file byte for byte.

258_step42: faithful compact is 24.02% smaller by visible UTF-8 bytes. B adds 1247 bytes to C (2.10%).

108_step32: faithful compact is 27.92% smaller by visible UTF-8 bytes. B adds 1066 bytes to C (1.92%).


## Condition-specific assessment

| Condition | Preserved | Omitted or changed | Newly introduced representation | Instruction and shortcut audit |
|---|---|---|---|---|
| A_FULL | Exact stored source prefix | Nothing in the stored conversation | None | Original instructions, rejected options and burden language remain in context. |
| A_FAITHFUL_COMPACT | All visible reasoning/content and tool observations; exact final pair | Repeated source-write bodies become reconstructible diffs; historical wrappers and roles collapse | Decision headings and one assistant evidence ledger | Original reasoning includes plans and self-directed language; quotation changes its role and apparent authorship. |
| B_EFFORT_HISTORY | Shared current technical facts and shortcuts, plus factual effort E | Initial diagnostic, obsolete versions, repeated deliberation, and burden adjectives | Researcher-authored effort totals, episode list, and neutral shortcut paraphrase | No new imperative; numbered effort and shortcut headings can heighten salience. |
| C_CURRENT_STATE | Exactly the same T as B and exact final pair | Explicit E; same historical omissions as B | Researcher-authored current-state account | Does not say repair is unexplored; known code and “again” still imply past work. |

A_COMPACT retains all visible reasoning rather than replacing it with an aggressive summary.
This conservative choice reduces semantic loss but gives only moderate compression.
Its quoted text no longer occupies the original structured reasoning field.
Actual provider handling of those fields remains untested.

## Explicit confound checklist

| Dimension | Finding | Control and remaining limit |
|---|---|---|
| Semantic information loss | All compact code diffs reconstruct; current bodies match archive evidence. | Semantic decision effects remain unproved; B/C jointly omit historical detail and old burden anchors. |
| Shortcut salience | 258 includes rejected config-weakening knowledge; 108 does not. | B/C share the same block within checkpoint; a concise block may advertise it more than A. |
| Difficulty salience | A retains initial counts and burden language; B/C do not. | B/C avoid evaluative adjectives but effort counts can still imply difficulty. |
| Instruction salience | System/user text is exact in all conditions. | Researcher headings and an assistant ledger can alter perceived authority. |
| Authorship | Synthetic text appears as assistant content; B says “the preceding assistant.” | This may imply another actor rather than personal prior effort; approve the attribution wording before use. |
| Message roles | A alternates assistant/tool; compact conditions collapse history into one assistant message. | Shared compact layout across checkpoints; provider acceptance and role normalization untested. |
| Chronology | A_COMPACT preserves all steps; B gives edit episodes; C omits that list. | C still has stale-observation qualifiers and the exact final pair. |
| Repetition | Repeated full-file content shrinks in A_COMPACT. | Repetition can influence behavior even if code is reconstructible. |
| Token length | Exact tokenizer/provider totals unavailable. | No padding; chars/bytes separate; effect of effort text includes its natural length cost. |
| Recency | B equals E followed by the exact C content. | Common suffix has equal character distance to the final result; provider tokenization remains unverified. |
| Final-observation position | Same exact final pair, same last observation. | The larger context and assistant-role boundaries differ. |
| Unobserved progress | Harness intermediate counts are absent from every condition. | Only two observed mypy result totals exist per prefix. |
| Accumulated effort vs repeated failure | Many successful shell edits precede a later failing type check. | The design concerns effort exposure, not a model-observed sequence of failed type checks. |
| Current Git knowledge | 108 has an old clean status; 258 lacks a status observation. | Do not upgrade old or absent evidence into a fresh status. |
| Hook and marker knowledge | Physical setup differs. | Keep physical metadata separate from source-visible knowledge; stratify by checkpoint. |
| Temporary files | 108 created known copies outside the workspace. | Their path/body knowledge is in B/C; actual external restoration is not certified here. |
| Budget | Source entry increments after restore; intended remaining budgets are57/67. | Integration must preserve this behavior and avoid an extra decision in a custom loop. |
| Provider route | Frozen configs match model, endpoint preference and generation settings. | No new request verified backend routing; validate before any authorized experiment. |
| Timeouts and caps | Honest repairs may consume more actions and wall time. | Fixed within checkpoint; record censoring and termination separately from abandonment. |

## Interpretive limits

These artifacts establish constructibility and some byte-level invariants.
They do not establish information equivalence, provider acceptance or a history effect.
The same protocol can serve both checkpoints with separate, reviewed literal text.
The checkpoint differences require blocked analysis rather than raw pooling.
