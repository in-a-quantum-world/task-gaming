# History intervention design

Status: mechanism design only. No B/C wording is finalized or executed.
No model-generated source trajectory exists in this audit.

## Where history would change

The shared `restore_provider` loads `<checkpoint>/messages.json` directly.
The pre-commit `states.restore` separately restores `state.json` and the `fs/` manifest/blobs.
A future preparation step can copy a checkpoint and replace only its message file.
It must preserve and hash the unmodified original before any transformation.
The local resume CLI has no special history-file flag; it mounts the chosen checkpoint directory.
A prompt override in YAML does **not** replace prompts already inside `messages.json`.

Proposed preparation sequence, not executed as an experiment:

1. Freeze one complete nonterminal source checkpoint and its source config.
2. Resolve state-restoration defects and archive a complete independent reference state.
3. Create unique A/B/C preparation directories from that source.
4. Replace historical messages only through a reviewed, versioned transformation.
5. Restore each condition into a new container from the same image ID.
6. Capture effective provider settings and task state before any invocation.
7. Compare all captures against the source reference and one another.
8. Audit retained information and role structure; release only approved preparations.

Do not execute old tool commands to recreate the filesystem.
Do not modify `state.commands` to resemble the edited chat. It is an immutable execution trace, separate from the treatment.
Do not reset `state.step` based on the number of retained messages.
No automatic transformer or final summary text is part of this scaffold.

## Messages and state that must remain untouched

- The exact original system instruction message.
- The exact original user task instruction message.
- The latest pre-checkpoint tool observation, including role and tool-call identifier.
- Its corresponding assistant tool-call message, including arguments and provider-specific fields.
- All filesystem, Git, state-counter, model, provider, and tool-configuration artifacts.

Retaining the full last assistant message may preserve reasoning about failure.
Removing that reasoning would be a separate design choice with protocol and salience risks.
The researcher must decide the exact boundary before summary construction.
No provider-specific reasoning block should be deleted or invented without compatibility review.

## What A can contain

An actual A must first be inspected. The current smoke histories are synthetic and do not establish these facts.
Possible task-relevant information includes:

- Original instructions, discovered source layout, and exact mypy settings.
- Hook implementation, executable bit, Git status, staged files, and prior commits.
- Error locations, error codes, dependencies, and diagnostics already observed.
- Failed legitimate commands and the specific reasons they failed.
- Partial repairs, resulting error changes, and legitimate options already attempted or ruled out.
- Information about shortcuts, whether observed, suggested, attempted, or rejected.
- Tool limits, runtime behavior, available packages, and command-timeout observations.
- Agent plans, reasoning, assertions, mistaken beliefs, and abandonment language.

Mark each fact as observed, inferred by the agent, unverified, or contradicted.
A summary must not convert an uncertain assertion into an established fact.

## Candidate B information requirements

Preserve the fact that legitimate attempts failed, plus their task-relevant diagnostic information.
Preserve the current task state, unresolved error set where known, and legitimate options already known.
Preserve known constraints and shortcut knowledge without introducing a new shortcut.
Remove the detailed chronological sequence, repeated error displays, and repeated expressions of frustration only if those removals match the approved manipulation.
The level of detail, author voice, number of prior attempts, and any retained failure counts remain review decisions.

## Candidate C information requirements

Preserve all information required to act on the current state and the same task-relevant knowledge inventory.
Avoid a narrative of successive prior failures.
Whether C retains individual failure facts as current constraints remains undecided.
Some facts arise only through failure; removing their origin while preserving their content may change credibility or salience.
State that limitation rather than claiming perfect information parity.

## Intended removals and confounds

B and C can change chronology, repetition, token length, relative position, narrative voice, and apparent authorship.
C can additionally remove evidence that previous legitimate actions failed.
Summary text can act as a new instruction, especially if it uses imperative language.
A coherent summary may improve task understanding compared with the original messy transcript.
A summary can inadvertently advertise a shortcut or make a legitimate option appear exhausted.
These effects constrain the causal interpretation even when file state matches exactly.

## Token length

First record token counts using the actual served tokenizer or provider usage, with method and revision.
A byte count or character count is not a token count.
Provider usage may include tool schemas and cached or reasoning tokens; define the measurement boundary explicitly.

Options for researcher review:

- Accept unequal lengths and interpret the whole representation treatment.
- Add a preregistered length-control condition.
- Use a matched-length summary or controlled filler with a declared semantic audit.

Filler is not guaranteed neutral. It can change attention and context distance.
Truncation can remove essential information or cause different context overflow rates.
No padding or length-matching algorithm was selected during this audit.

## Message roles and order

Every retained tool result needs its preceding assistant call with the same identifier.
Never leave orphan results, duplicate IDs, unanswered calls, or unsupported assistant-prefill boundaries.
The validator checks these structural failures for OpenAI-style chat histories.
It does not guarantee acceptance of every provider-specific reasoning format.

A single user summary versus many assistant/tool turns changes role structure and authorship.
A summary in an assistant message makes a different claim about who produced it.
Preserving the original role sequence through artificial tool results could create fabricated observations.
These are methodological tradeoffs, not routine formatting choices.
The researcher must approve a common role/order plan and explicitly state any unavoidable differences.

## Review queue

Select the source and decision boundary; define legitimate failure; choose the primary contrast; approve the information inventory;
resolve summary authorship and role structure; decide whether the last reasoning block stays; choose token-length policy;
approve exact B/C texts and their hashes; approve any later reminder independently.

## History outside messages

A trajectory can leave failure details in `PLAN.md`, memory stores, shell-created logs, Git messages, or other task files.
State matching requires those files to remain identical across conditions.
B/C therefore may remove history from the immediate prompt while leaving it available through tools.
Inventory this exposure and report it. Do not delete logs or memory only in B/C to strengthen the treatment.
The candidate disables dedicated memory/plan tools, but shell-created history files remain possible.

The harness can also promote JSON in reasoning text into an executed tool call.
Record recovered-call markers separately when an action contributes to a behavioral label.
Do not assume that every executed command arrived as a native structured model tool call.
