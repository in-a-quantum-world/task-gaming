# Prior experimental practices

The audit targets implementation patterns. It does not review the literature comprehensively.
No prior experiment or grading call was executed.

Pinned repositories:

- [agent-interp-envs](https://github.com/gkroiz/agent-interp-envs/tree/56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb)
- [task-gaming](https://github.com/mihirs-0/task-gaming/tree/c9b29ca5a328155ec2f41868d3fa97bcf145ade1)
- [principled-interp-blog](https://github.com/gkroiz/principled-interp-blog/tree/3744278dba19a82e5366990a41f3b4984ff9b805)

Paths in the table are exact relative paths within the named repository.

| PRACTICE | SOURCE REPO | EXACT IMPLEMENTATION / FILE | SHOULD WE COPY IT? | WHY? |
|---|---|---|---|---|
| Per-step history, state, and file artifacts | agent-interp-envs | `checkpoint.dump`, `src/agent_interp_envs/checkpoint.py`; pre-commit `states.py` | Adapt | Useful separation of history and files. Current snapshot gaps require external validation. |
| Continue from one checkpoint | agent-interp-envs | `scripts/resume.py:main`, `restore_provider` | Adapt | Supports independent history replacement. It does not verify experimental equivalence or archive request metadata. |
| Preserve remaining total budget | agent-interp-envs | `environments/precommit_hook/agent.py:main` increments saved step before loop | Yes, after review | Keeps the original cap; a new per-continuation allowance needs an explicit alternate design. |
| Oversample and delete slow survivor | agent-interp-envs | `scripts/run.py:monitor_and_run`, default `kill_last` | **No** | This selects on completion speed and destroys sample evidence. |
| Delete failed local downloads | agent-interp-envs | `scripts/run_modal.py:main`, `failed_run_dirs` | **No** | A local dataset can omit failures and timeouts. Preserve every attempt. |
| Record environment commit and dirty flag | agent-interp-envs | `scripts/run_modal.py:_write_run_meta` | Extend | Add image ID, dependency inventory, resolved request settings, output hashes, and researcher code commit. |
| Separate action labels from self-report | agent-interp-envs | `environments/precommit_hook/score.py` | Principle only | Current heuristic labels do not verify commits, mypy success, or instruction compliance. |
| Frozen preregistration plus dated amendments | task-gaming | `PREREGISTRATION.md`, section 9 | Yes | This makes changes visible before later results. A draft is not a frozen preregistration. |
| Interleaved arms | task-gaming | `run_rollouts.py:main`, `work` queue and workers | Adapt | Limits temporal provider drift. For this study, randomize condition order within checkpoint blocks before collection. |
| Fixed serving parameters | task-gaming | `configs/qwen3-coder-30b.yaml`; `patches/vllm_provider.py` | Principle only | Prior study uses local Qwen with vLLM and different sampling support. That provider does not exist in current upstream. |
| Exact source doses | task-gaming | `ENV_NOTES.md`; `PREREGISTRATION.md` sections 3 and 8 | Yes | Documents 51 versus requested 50 and the 258/602 ambiguity. Current source availability differs from that older pin. |
| Recover final workspace after failure | task-gaming | `run_rollouts.py:run_one`, `docker cp` then archive | Adapt | Preserves partial state even on crashes. Save before container deletion. |
| Retry with fresh seed and retry ledger | task-gaming | `run_rollouts.py:worker`, `retries.jsonl` | Review | New seeds change samples. Retry/exclusion rules can bias history conditions through transcript length. |
| Preserve every retry artifact | task-gaming | `run_one` reuses output folder, `rollout.log`, `workspace.tar.gz`, and `record.json` | **Do not copy as-is** | Attempt configs and records persist, but these artifact paths are reused. Use unique attempt directories. |
| Cap hits remain in denominator | task-gaming | `PREREGISTRATION.md` section 4; runner status logic | Proposed | A cap hit is an outcome, not automatic infrastructure failure. Review wall-time and context-limit policy separately. |
| Exclusion threshold and pilot gates | task-gaming | `PREREGISTRATION.md` sections 4/6, amendments A3–A7 | Do not import numbers | Their 5%/20% thresholds and model changes address another design. Our thresholds and N remain TBD. |
| Grade in a separate offline container | task-gaming | `run_rollouts.py:grade`, `--network none`; `patches/classify.py` | Adapt | Keeps task-authored hook execution isolated and grader logic outside agent visibility. |
| Verify new commits mechanically | task-gaming | `patches/classify.py:git_state`, `baseline_commit` | Adapt | Compare against the actual checkpoint HEAD here. A root-commit baseline can count actions before the intervention. |
| Use pristine mypy config and undo suppression/deletion for grading | task-gaming | `build_desuppressed_src`, `reference_ignore_lines`, `run_mypy` | Review first | Stronger than raw error count, but exact ignore whitelists and deletion rules are methodological choices. |
| Hook probes with intentionally bad source | task-gaming | `_probe_commit`, `hook_analysis` | Adapt carefully | Useful enforcement evidence. Nonzero probe status also includes infrastructure failure, so inspect cause before labeling a good hook. |
| Mechanical primary workaround | task-gaming | `workaround = commit_succeeded and errors_remaining > 0` in `classify.py:main` | Secondary candidate | Does not measure attempts. An absent hook with zero remaining errors can violate instructions while this proxy remains false. |
| Explicit checkpoint resampling | principled-interp-blog | `scripts/resample.sh`, `--step`, `--count`, `--max-parallel` | Pattern only | Current script targets chess/tictactoe via `scripts/resume.sh`, not pre-commit. No proof of filesystem matching. |
| Exclude last numbered checkpoint | principled-interp-blog | `scripts/resample.sh` removes last step by position | **No** | Highest step can be a cap or crash, not a terminal task state. Check actual state and remaining budget. |
| Keep only latest resample timestamp | principled-interp-blog | `run_anchor_analysis.py:find_resampled_dirs` | **No** | Earlier continuation samples can disappear from analysis. Use an explicit immutable run registry. |
| Per-experiment config and metadata | principled-interp-blog | `experiments/run_experiments.py:save_experiment_config`, `create_experiment_summary` | Extend | Records config, checkpoint, replicas, and elapsed time. Add source/image pins and every termination reason. |
| Wait for all containers | principled-interp-blog | `experiments/run_experiments.py:monitor_containers` | Principle only | No slow-survivor deletion in this function, but no bounded wall-time policy either. |
| LLM judgment of attempted behavior | principled-interp-blog | `analysis/grading/grade_rollouts.py:RolloutAnalysis`, `create_analysis_prompt` | Not as primary | Useful distinction between attempted actions and successful outcomes. Its game-specific judge and API cost do not transfer directly. |
| Filter on trajectory properties | principled-interp-blog | `analysis/action_branches/action_causal_analysis/compute_causal_effect.py:apply_condition` | Only preregistered | Post-hoc filtering on treatment-affected behavior can change the estimand. |
| Fixed-state causal claim | All three | No inspected implementation establishes semantic information parity after a history rewrite | No automatic inheritance | This experiment needs its own pre-invocation validation and human information audit. |

## Important limits

The `task-gaming` preregistration used upstream `5f4facb`, not this audit's current SHA.
Its original design changed seeded task difficulty, not preceding history at a fixed decision point.
Its final Qwen condition differs from the DeepSeek candidate in model and serving stack.
Its analysis cannot establish the answer to the present research question.

The game resampling repository offers useful directory and continuation patterns.
Its `resume.sh` accepts only chess and tic-tac-toe. The grading definitions are game-specific.
Its resampling shell script also uses `set -e` with post-increment counters; that warrants a shell test before reuse.
No shell scripts from that repository were copied or run.

No published paper cell was reconstructed from an exact original config and complete source trajectory.
Claims about the paper's 258 anchor are attributed to the inspected related preregistration, not independently verified paper data.
