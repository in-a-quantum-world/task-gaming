# B/C treatment audit

This audit applies to the prepared histories in commit `a83c633ab0d23b21eb1999fe67e8e89bb42ce12d`.
The histories and their original manifests remain unchanged.

The exact difference is confined to a prefix at JSON pointer `/2/content`.
That structural result does not certify a pure effort-provenance manipulation.
The prefix changes emphasis, and C has identified knowledge omissions.
The protocol is not ready for final scientific approval.

## Exact diffs

| Checkpoint | Human-readable diff, C to B | Exact inserted text | Machine insertion proof |
|---|---|---|---|
| 258/42 | [C_TO_B.exact.diff](258_step42/C_TO_B.exact.diff) | [Prefix](258_step42/B_ONLY_EFFORT_PREFIX.txt) | [Patch record](258_step42/C_TO_B.string_patch.json) |
| 108/32 | [C_TO_B.exact.diff](108_step32/C_TO_B.exact.diff) | [Prefix](108_step32/B_ONLY_EFFORT_PREFIX.txt) | [Patch record](108_step32/C_TO_B.string_patch.json) |

Each unified diff compares the synthetic assistant content, with zero unchanged context lines.
It contains only additions of the declared effort prefix; it contains no technical-content replacements.
The companion text files contain the exact before and after strings.
The machine record specifies a custom string insertion, not an RFC6902 JSON Patch operation.
Insertion of that string into C reconstructs the complete B message array exactly.
The audit rejects changes to any other message or to the common technical suffix.

| Check | 258/42 | 108/32 |
|---|---:|---:|
| Prefix Unicode characters / UTF-8 bytes | 1,247 / 1,247 | 1,066 / 1,066 |
| Unchanged message indices | 0,1,3,4 | 0,1,3,4 |
| Original instructions and final pair | Exact | Exact |
| Current/copy file-body representations checked | 17 | 26, including12 temporary copies |
| Actual tokenizer counts | Unknown | Unknown |

## Tone, urgency, salience and implied instruction

The [258 sentence audit](258_step42/PREFIX_SENTENCE_AUDIT.md)
and [108 sentence audit](108_step32/PREFIX_SENTENCE_AUDIT.md)
cover the heading and every sentence in the B-only prefix.
The audit separates observable wording from possible psychological effects.
No model response was sampled to test those effects.

| Dimension | Finding | Status |
|---|---|---|
| Explicit tone | Sentences describe counts, edit methods and shell results. No praise, emotional state, or burden adjective is added. | Factual wording; tone equivalence remains unproved. |
| Implied tone | The heading calls the actions effort; repeated totals and episodes emphasize investment. | Partly the intended treatment, but not psychologically neutral. |
| Explicit urgency | No new deadline, countdown, time limit, or demand appears. The original shipping instruction is identical in B/C. | Pass for explicit urgency. |
| Implied urgency | Decision ordinals may cue elapsed time or consumed budget. | Possible extra cue; the prefix gives no actual remaining budget. |
| Salience | Aggregate counts precede a repeated file-by-file list. Repeated rewrites receive separate entries. | May increase perceived burden beyond the bare existence of prior actions. |
| File attention | The list names possible next repair targets, including files that contain local ignores. | May change attention to files and suppressions without adding a new bypass concept. |
| Implied instruction | No imperative or next-action recommendation appears. The success sentence may encourage reliance on prior edits. | Absence of an explicit instruction does not rule out pragmatic pressure. |
| Authorship | “The preceding assistant” can imply a different actor. | Confounds personal prior effort with a handoff from another agent. |
| Success salience | “These edit commands returned exit code zero” highlights shell success. | Does not show that repairs passed mypy; may imply more progress than warranted. |
| Tool information | The108 prefix names a one-line sed edit; C does not name sed. | Concrete technical-knowledge imbalance within B/C. |

The B-only prefix contains no global configuration-weakening proposal.
The shared258 shortcut paragraph can still make that source-known option more salient than A_FULL.
The108 prefix repeats `metrics.py`, whose shared current body contains ignores.
This can make an existing suppression more prominent without adding a new technique.

## C current-knowledge audit

The [258 coverage table](258_step42/C_KNOWLEDGE_COVERAGE.md)
and [108 coverage table](108_step32/C_KNOWLEDGE_COVERAGE.md)
compare C with source-visible evidence at the fixed cutoff.
The audit reconstructs known file bodies from earlier reads and authored writes.
It does not infer extra code behavior from execution or import tests.

C retains the exact original instructions and current diagnostics.
It retains current known source bodies, mypy settings, dependencies and local ignores.
It preserves the observed mypy path, and the version only for108 where it was observed.
It retains Git knowledge limits, marker facts and source-visible hook knowledge.
The258 hook's executable state is preserved; the108 hook's physical absence is not falsely called an observation.
It retains known temporary-file path/body relations in108.

The following gaps prevent a claim that C retains all relevant current knowledge:

| Gap | Source provenance | Status and significance |
|---|---|---|
| `sed -i` accepted on source text at108 | step23, m48/m49 | B names sed; C does not. A known legitimate edit method differs across conditions. |
| Shell here-document and `cp` edit capability | Actual source write/copy commands and zero exit results | C retains resulting bodies and copy paths, but not all explicit tool-method knowledge. |
| Empty108 `src/__init__.py` | Zero-byte file in step1/m5 listing; no later edit to this file | C lists its name but omits the known empty state. |
| Existing258 sample-hook paths | step3/m9 hook-directory listing | C omits these available examples. Their relevance to current repair needs human review. |
| Prior rejection of global weakening |258 step10/m22 reasoning | C preserves the option and requested-settings conflict as a paraphrase. Equal stance and salience are not established. |

Some routine listing details, such as old sizes and timestamps, are also omitted.
They are not silently promoted to current facts.
The audit does not claim that every historical observation must enter C.
It does require an explicit decision about each current task-relevant omission.
The initial error total is an intentionally omitted historical burden anchor in both B and C.

C also retains residual history cues in the mandatory final pair.
The108 assistant says “again” and expects a check of fixed errors.
That cue is identical in B/C and is not part of the B-only diff.
Stale Git qualifiers and current edited code can imply earlier action too.

## Data boundary

Only the original step42 and step32 message prefixes were read as source evidence.
Their hashes are recorded in each verification file.
The audit does not open any newly generated continuation, runtime validation output, or later trajectory.
It does not run task commands, imports of task code, mypy, or a provider.
No harness-only intermediate error count is introduced.
The only observed count pairs are258→9 and108→6.
The existing258 `/home/user` failure is retained because Kimi saw it at step41.
No newly discovered runtime failure is added to a condition or proposed shared block.

## Revision decisions before approval

1. Put source-supported edit-tool capability facts into the common B/C block.
2. Add the known empty108 initializer state to that common block.
3. Decide whether sample-hook availability is relevant enough to preserve explicitly.
4. Choose an attribution that matches the intended personal-effort hypothesis.
5. Decide whether totals plus a full episode list are necessary, or add avoidable repetition.
6. Remove or redesign the B-only zero-exit sentence if progress confidence is outside the intended treatment.
7. Review the shared258 rejected-shortcut paraphrase for stance and salience.

These are revision recommendations, not edits to the frozen treatment.
Any revised version needs new hashes, exact diffs, and external review.
A prefix-only diff must not be described as proof of semantic information equivalence.

## Reproduce the offline checks

From the prototype worktree:

```bash
python3 research/history_conditions/bc_audit_v1/audit_bc_treatment.py \
  --output /tmp/bc-audit-new-review
```

Choose a new output directory if that path already exists.
The script rejects different frozen input hashes and cannot alter the histories.
It has no provider or task execution interface.
