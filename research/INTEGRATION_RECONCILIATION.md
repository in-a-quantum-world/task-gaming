> 2026-09-10 amendment: the user authorized Kimi through OpenRouter,
> pinned to novita/bf16 with no fallback. SOURCE_PILOT_CONFIG.yaml and
> SOURCE_PILOT_PREREG.md supersede historical Fireworks access/config claims.
> The earlier audit/prototype reconciliation and archive evidence remain valid
> for their recorded image; new-image validation is required before source use.

# Integration reconciliation

Exploratory work before final preregistration. No causal claims.
The integration branch starts at audit commit `622703e`.
The reviewed prototype commit is `eaedc8f`; implementation originated at `a1336ea`.
Both inspect framework commit `56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb`.
No merge or whole-branch cherry-pick occurred. Neither source branch changed.

All framework paths below are relative to the pinned framework checkout.

| FINDING | AUDIT AGENT RESULT | PROTOTYPE AGENT RESULT | SOURCE-CODE EVIDENCE | RESOLUTION | CONSEQUENCE FOR EXPERIMENT |
|---|---|---|---|---|---|
| Stock snapshot/restore | Git drift, inherited-entry loss, and stat-gate omissions | Stock restore changes 12 entries | `checkpoint.py:ManifestSnapshot.update/restore`; `states.py:_new_snapshot` | Both correct. Full archives supplement every checkpoint. | Stock manifests alone cannot support state matching. |
| Full archive scope | Equal replicas may share a wrong reconstruction | Four restores match measured workspace inventories | `prototype/loop.py:save_archive/restore_archive`; new `pilot/workspace.py` | Prototype already compares against its captured source inventory. The audit warning still requires broader checks. | New validation compares actual ORIGINAL, restore 1, and restore 2 through the audit validator. |
| Git state | Fresh entrypoint recreates initial commit and index | Archive repairs observed Git changes | `entrypoint.py:setup_precommit_hook`; complete `.git` archive | Retain every Git file. Check HEAD, index bytes, status, and both diffs. | No Git exclusions or rebuilt substitute commits are allowed. |
| Mypy cache | Upstream excludes caches | Full archive includes them | `states.py:_FS_EXCLUDE_PREFIXES/_new_snapshot`; archive covers every `/agent` entry | Retain complete cache bytes and modes. Independent probes disable cache writes. | Equal error counts alone remain insufficient. |
| External state | `/home/dev`, processes, packages, network, and other state may differ | Scope limitation acknowledged; final Docker diff recorded | `tool_calling.py:_agent_env/run_command`; new `external_inventory` | Inventory home, memory, relevant tmp files, packages, fixed tools/config, and dev processes. | This is a bounded file/task guarantee, not whole-machine equivalence. |
| Source variants | Both 258 and 602 exist at this pin | Used 258 successfully; no contrary current measurement | `entrypoint.py` source selector; checked-in `src_258`/`src_602`; audit measured counts | No substantive disagreement. Older absent-602 reports use another pin. | Fix source to 258; final fixture measures 258 errors. |
| Fresh/resume parameters | Fresh drops temperature and top-p | Wrapper uses shared `provider_kwargs` already | `agent.py:main` versus `checkpoint.py:restore_provider` | Both correct about their different paths. Patch the actual experiment copy of `agent.py`. | Regression fails unpatched and passes for both Fireworks and OpenRouter after the patch. |
| Model configuration | DeepSeek baseline is provisional; serving details unresolved | DeepSeek config retains omitted sampling defaults | Both local YAMLs; provider factory and Fireworks adapter | User now selects Kimi. Neither prior proposal controls this source pilot. | Exact explicit pilot settings are frozen; no claim of hidden paper settings. |
| Published prompt | Exact original prompt not recovered | Copied local config; not a published reconstruction | Pinned Model-Forensics dataset initial messages in `evidence/integration/published-prompts.json` | Recovered exact published initial message strings differ from both local configs. | Use the public dataset prompt. Do not add a stronger prohibition or deadline variant. |
| Scorer correctness | False `good` and quote-triggered `bad` counterexamples | Same limitations acknowledged | `score.py:score_precommit_hook`; prototype `summarize.py` | Retain upstream output only for comparison. Use independent action/state grading. | Attempts need native actions; success needs a verified effect. Ambiguity stays explicit. |
| Remaining budget | Saved step k leaves `max_steps-k-1` decisions | Step 4 fixture leaves 95 of 100 | `agent.py:main` increments restored step; `BaseState.step` | Full agreement. Preserve state and total cap. | A step 2 validation checkpoint leaves 97 decisions, not a fresh 100. |
| Run preservation | Upstream starts count+1 and deletes slow survivors | Wrapper starts one and uses persistent caps | Upstream `scripts/run.py`; prototype `run.py` | Adapt exclusive directories and caps; add final workspace recovery and a single source slot. | Failures and timeouts survive. No automatic replacement or extra source sample. |
| Raw API metadata | History dumps omit full transport metadata | Request/response hooks tested offline | Fireworks `invoke`; prototype `instrument_provider` | Adapt hooks; retain request IDs, usage bodies, and native replies before recovery. | Actual requests can be audited separately from config and transformed chat history. |
| History manipulation | Mechanically feasible; semantic parity unproved | B/C filesystem matches; summaries omit acquired information | `checkpoint.py:restore_provider`; prototype `histories.py` and confound register | No contradiction. Technical feasibility does not establish information equivalence. Reject old summaries. | Next design contrast is full history versus faithful compact summary, after a real checkpoint and review. |
| Candidate source | No real checkpoint exists | No real checkpoint; repeated checks are not repair episodes | Both handoffs and candidate register | Full agreement. Freeze an episode rule before source outcomes. | No synthetic checkpoint is eligible for scientific use. |
| Credential/provider gate | Checked credentials absent | Checked credentials absent | New presence-only check; official Fireworks model page | Still absent. Public page also lists serverless as unsupported. | Paid phase stops. No Kimi run and no DeepSeek substitution. |

The apparent archive disagreement concerns scope and evidence strength.
The prototype's source inventory is useful evidence; it is not merely a replica
comparison. The integration expands that evidence to task diagnostics and budget.
It also adds exact timestamp restoration and explicit external-state checks.

The handoffs describe some pre-commit worktree states. Current Git refs supersede
those historical status descriptions. Their substantive audit findings remain
separate from those stale handoff status lines.

Retained adaptations: archive capture, guarded restore, exclusive artifact writes,
request hooks, persistent caps, and the upstream-entrypoint wrapper pattern.
Rejected code: A/B/C builder and bundles, summary exporters as a primary grader,
three-source cap, omitted sampling defaults, and unconditional container removal.
The final runner has no model continuation mode.
