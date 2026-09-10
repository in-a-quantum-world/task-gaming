# Separate 602 stress stage

The original pilot files are inherited unchanged. `run_stage.py` reuses their
preservation launcher in a separate process and source-ledger namespace. The
Docker image is identical to the 258 image. Only the experimental source config
changes target_errors. `verify_outcome.py` differs from the frozen analyst probe
only at the original-source inventory path. `grade_stage.py` mounts that probe
only in offline grading containers. No model continuation interface is provided.

See STRESS_602_PREREG.md before any paid phase. Source command:
`python stress602/run_stage.py source --config STRESS_602_CONFIG.yaml --count 1`.
It refuses a consumed 602 slot and verifies the original 258 slot is unchanged.
