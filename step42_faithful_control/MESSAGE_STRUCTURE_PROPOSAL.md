# MESSAGE_STRUCTURE_PROPOSAL

CANDIDATE ONLY — not installed in any runner or checkpoint

| Position | A_FULL | Proposed A_FAITHFUL_COMPACT_SUMMARY |
|---|---|---|
| 0 | Original system message m0 | Exact m0, same role |
| 1 | Original user message m1 | Exact m1, same role |
| Middle | Original assistant/tool turns through step41 | One assistant content message with the indexed evidence summary |
| Penultimate | Step42 assistant m86 | Exact visible projection of m86, including tool-call data |
| Final | Step42 tool result m87 | Exact m87, including ID and nine-error content |

The source raw A_FULL checkpoint remains untouched.
A_FULL_VISIBLE_REFERENCE.json is a credential-screened reference, not a replacement for raw A_FULL.
Only visible fields appear in exported artifacts; private provider metadata are absent.
The final visible pair retains both equal reasoning aliases and the exact original tool-call structure.
Visible source strings and tool-call IDs remain identical; JSON whitespace is not preserved as a wire byte stream.
No experimental condition label, new system message, or new user instruction enters the candidate payload.
The inventory, audit, workspace hashes, and transcript are researcher documents, not additional model messages.

## Why this is only a proposal

An assistant summary avoids an explicit new user instruction but has artificial authorship.
It also creates adjacent assistant messages before the final tool result.
Provider acceptance, field normalization, and rendering are untested because API calls were forbidden.
The candidate does not assert that the API will accept this layout unchanged.
Do not silently convert the summary to a new user or system message.
Such a change needs its own documented review because it changes perceived authority.

## Data boundary

The summary uses only the raw step42 cumulative messages and the actions they describe.
The archive audit verifies known file content without adding unseen Git IDs or hidden state to the summary.
The final observation remains last; no summary, reminder, or conclusion follows it.
Tool schemas, generation settings, budget, and workspace bytes are outside this history-edit proposal.
Their equality would need validation in a later authorized experiment.
No runner, resume command, model request, or continuation was executed for this task.
