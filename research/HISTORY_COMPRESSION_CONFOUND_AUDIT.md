# Final compression and treatment audit

This audit applies to `human-review-v2`, before human approval. No continuation behavior was inspected. Automated equality checks establish bytes and provenance constraints; they do not establish equal psychological effects.

## B-only tone and meaning

The B-only material is one declarative, first-person sentence reporting counts of inspected files and issued edit commands, followed by a blank line. It contains no file names, mypy results, suppression names, step numbers, external speaker, deadline, evaluation, or future action. The numbers count actions, including writes with local ignores; they do not label those actions legitimate or successful.

| Dimension | Wording audit | Residual qualification |
|---|---|---|
| Urgency | No deadline, countdown, time or speed request | Prior activity can still imply elapsed time; that inference is unmeasured |
| Encouragement | No praise, approval, reassurance or imperative | No guarantee of pragmatic neutrality |
| Discouragement | No failure label, warning or negative evaluation | No guarantee of pragmatic neutrality |
| Sunk-cost framing | No investment metaphor or argument for continuing | Any effort-based inference is a possible response to the intended fact, not a claimed internal mechanism |
| Completion pressure | No shipping reminder, remaining-work count, commitment or next step | Original task wording is identical |
| Success framing | No zero-exit claim or claim that edits fixed errors | Counts are issued actions, not verified repairs |
| Difficulty framing | No easy/hard/substantial/burden adjective or comparison | Counts make amount of prior activity explicit; that is the treatment |
| Shortcut salience | No names of files, ignores, settings or hook workarounds | Shared current bodies and diagnostics still expose source-known suppressions |
| Oversight salience | No new user/system role or reviewer/human reference | Synthetic first-person prose has researcher authorship; this is disclosed to the researcher, not added as a model cue |
| Instruction-like wording | Past-tense statement; no should/must/need/continue | The condition remains a factual attribution, not a command |
| Tone | Neutral vocabulary, one sentence, no heading calling it effort | Perceived tone cannot be proven identical without behavioral evidence |
| Repetition | One set of aggregates; no file-by-file replay | Numeric aggregation is more explicit than the distributed source evidence |

Revisions from v1 removed “preceding assistant”, its separate effort heading, the repeated episode list and decision ordinals, and the zero-exit sentence. Missing editing methods, empty initializer knowledge and relevant sample-hook names were added to both technical suffixes. The researcher judgment about whether code comments demonstrate safety was removed from model-visible prose. These changes followed the source-only audit, not any continuation result.

C retains the entire shared technical suffix and the exact current result. B has no extra editing method or shortcut knowledge. The tests inspect source-body/definition and local-ignore coverage and diagnostic notes, not just the prefix equality. No harness-only intermediate count or post-checkpoint runtime failure appears in any active text.

## A_FULL versus A_FAITHFUL_COMPACT

Preserved: original instructions; exact initial and final error observations; every pre-final visible reasoning string and assistant content; all tool observations; prior code observations; command order; targeted ignores; configuration-weakening consideration and rejection at 258; original uncertainties and subjective language; full shell-prefix/suffix mechanics; reconstructable authored code; exact final pair and IDs.

Removed from the direct representation: repeated unchanged lines in 16 primary and 12 replication full-file write commands, historical separate tool/assistant role envelopes, historical tool-call IDs and duplicated SDK reasoning aliases. Earlier source text remains in exact read observations, and every changed write body reconstructs from a preceding visible version. No substantive repair episode or ordering is intentionally removed. The shorter representation is consequently still long: it is a conservative compact ledger, not an aggressively shortened paraphrase.

Introduced: section labels, decision labels derived from prefix order, unified-diff syntax, one synthetic assistant content message, and a different placement of quoted reasoning into content. These are representation changes, not new source discoveries or instructions. A_FULL has no such edits. The public Kimi template places the final pair in the suffix where its visible reasoning is retained; this is checked offline. Actual provider serialization is not observed here.

## Shared residual confounds

| Dimension | Audit result |
|---|---|
| Semantic information loss | No loss of quoted reasoning/observations or reconstructable writes in faithful arm; B/C intentionally omit old states and detailed personal provenance. Equal shared bytes do not prove every inference from A survives. |
| Shortcut salience | B/C show known current ignores in code and diagnostics, with no B-only advertisement. The shared 258 settings-conflict paraphrase is shorter and differently placed than the original deliberation. |
| Difficulty salience | Initial totals and literal burden prose remain in A arms, omitted from both B/C. Aggregate B counts expose effort amount without evaluative adjectives. |
| Instruction salience | Original prompts remain exact. Long context length differs across A arms; shorter distance from instructions can change their influence. |
| Authorship | All compact bodies are researcher-constructed assistant content. B intentionally attributes source actions to “I”; there is no new human-message cue. |
| Message roles | A_FULL has 88/68 messages; each compact arm has five. B/C role layout and message count match exactly. |
| Chronology | Faithful arm retains decision order; B has an aggregate prior-action attribution; C lacks that narrative. Necessary stale-observation qualifiers remain shared. |
| Repetition | A_FULL repeats complete files; faithful arm removes unchanged rewrite lines. B/C current bodies appear once. The two B action-count clauses are not repeated elsewhere. |
| Token length | No filler. B adds 24 local-template tokens at each checkpoint. A arms differ by thousands of tokens. Provider counts are unknown. |
| Recency | B's prefix occurs before identical K and F; it does not move the final diagnostic behind a summary. A faithful compression changes the token distance of earlier events. |
| Final-observation position | Tool result is the final message in every arm; no follow-up user message or reminder is added. |
| Residual history in C | 108 final assistant says “again” and expects a check of fixed errors; 258 final pair and stale-state qualifiers also supply limited history. C means no long personal-effort treatment, not no conceivable history inference. |
| Budget/timeouts | 57/67 decisions fixed by checkpoint; request/tool/wall caps must stay fixed. Honest repair may need more decisions than a workaround; that limitation remains. No new timeout was sampled. |
| Physical state | Constructor never restores or modifies a task workspace. Fixed source archives are metadata; equivalence during later execution belongs to the independent integration check. |
| Provider | Model/route/settings fixed in manifests. Public local-template rendering is known; actual outgoing payload and server accounting require independent confirmation. |

## Items that should block freezing the complete experiment

1. Obtain outcome-free evidence that the integration runner sends the approved message structure and visible reasoning, restores the selected workspace, and assigns exactly 57/67 future decisions. This work does not establish that execution equivalence.
2. Approve an observable prohibited-action rubric before seeing continuation outcomes, including whether particular targeted ignores are allowed, how pre-existing suppressions are handled, and how an attempt differs from a successful bypass. The original task text is untouched; the history constructor must not invent a new prohibition.
3. Record the researcher's acceptance of the first-person aggregate treatment and residual “again”/observation-age cues. If the intended contrast requires absolutely no inference of past action in C, that target conflicts with the mandated unchanged final pair and requires a different protocol.

Exact provider-billed counts alone need not block freezing if approximate local counts are accepted and length is reported as a residual. The unchanged required final pair also need not block the stated narrower effort-information question. These are review decisions, not reasons to inspect outcomes or to rewrite histories after observing them.
