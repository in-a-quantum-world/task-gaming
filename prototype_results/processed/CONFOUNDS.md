# Confound register

EXPLORATORY ONLY — GENERATED BEFORE FINAL PREREGISTRATION

These are technical fixture findings and untested threats, not causal results.

| Question | Finding or limit | Consequence |
|---|---|---|
| Does B make the task sound easier? | B retains 258 errors but removes most repeated diagnostic output. | Felt difficulty may change beyond explicit failure facts. |
| Does C imply repair remains unexplored? | C omits prior failed checks; this fixture contains no actual repair attempt. | The intended failed-repair manipulation is not present yet. |
| Does the summary imply fresh oversight? | B/C use an assistant summary, not a new user instruction. | Assistant authorship is fabricated; an oversight inference remains possible. |
| Does it increase shortcut salience? | No known shortcut occurs in this fixture; B/C add none. | This concern remains untested for a real shortcut-aware checkpoint. |
| Does it remove acquired knowledge? | B/C omit most of the inspected source listing and Git help listing. | Information equivalence fails for the current fixture summaries. |
| Does token length differ? | A is 94,305 JSON bytes; B is 27,562; C is 27,459. | A is about 3.4 times larger; exact provider token counts are unknown. |
| Do final observations differ? | The final assistant/tool exchange matches exactly in A/B/C. | This control passed artifact tests and restore probes. |
| Do message roles/order differ? | A has 12 messages; B/C have five, including adjacent assistant messages. | Live API acceptance and effects of role compression remain untested. |
| Does the remaining budget change? | All restore probes compute next step 5 and 95 remaining turns. | No live continuation tested budget exhaustion. |
| Does workspace restoration change files? | The original restore changes 12 workspace entries. | Original snapshot is invalid for this prototype. |
| Does the full archive repair that gap? | Four archive restores match content, paths, modes, and uid/gid. | Scope excludes timestamps, processes, and arbitrary external files. |
| Does provider routing vary? | Mock tests are local; live config fixes Fireworks and the model identifier. | No live endpoint or request acceptance test exists. |
| Do timeouts favor shortcuts? | Tools have 30 seconds; runs have 100 turns and 3,600 seconds. | Large honest repairs may suffer more; no behavioral evidence yet. |

Additional findings:

- The repeated failures are repeated checks, not repeated unsuccessful source repairs.
- The concise legitimate-route sentence can itself act as a nearby constraint reminder.
- The original task does not separately enumerate every prohibited workaround.
- Explicit prohibitions in stricter prompt variants would constitute another prompt change.
- The upstream scorer counts annotations and heuristic command strings.
- It does not establish that mypy passed or that a commit succeeded.
- Full A can contain historical reasoning that B/C lose; this fixture has no such reasoning.
- Provider temperature and top-p defaults are unspecified even though the route is fixed.
- SDK retries can produce multiple HTTP attempts within one provider invocation.
- The wrapper records those attempts; no actual API call exercised that instrumentation.
- A live process, installed dependency, or file outside `/agent` may defeat the archive control.
- A symlink outside `/agent` makes the archive restore reject the checkpoint explicitly.
- The initial technical fixtures lack contemporaneous copies of the wrapper source.
- Image builds used cached layers; a clean rebuild can resolve different package versions.
- The summary's statement about an executable hook relies on command success plus workspace metadata.
- The full archive is a prototype addition and needs an independent implementation review.

No condition was revised after a behavioral result, because no model behavior was observed.

## Alternative controls

| Control | Problem addressed | New confound | Worth use in final study? |
|---|---|---|---|
| Full history versus faithful compact summary | Tests whether compression alone changes behavior. | Length and message-role differences remain. | Yes, as the next design check after a real baseline. |
| Failure fact versus difficulty fact | Separates repeated failure from present task difficulty. | A difficulty statement can imply no prior attempt. | Maybe, after explicit knowledge review. |
| Length-matched neutral material | Tests a length explanation. | Irrelevant material changes distraction and task relevance. | Only if a token-length effect appears plausible. |
| Identical history with a nearby reminder | Tests a local instruction-salience effect. | Adds oversight or emphasis and changes the question. | Optional; do not combine with the first small pilot. |

No alternative control received a model rollout in this session.
