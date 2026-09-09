# Raw artifacts

These local folders contain synthetic offline checks only. They are not experimental condition samples.
Preserve their contents unchanged. The directory is ignored by Git except this README.

- `smoke-258` and `smoke-602`: complete mock-provider logs, checkpoints, workspace copies, and process metadata.
- `restore-*`: prepared mock restores; no continuation model invocation occurred.
- Early restore captures include the validator's detected Git index side effect.
  Later captures use the corrected read-only Git probe. All attempts remain available.

Every output has a distinct path. No provider API keys were mounted.
A future model trajectory must occupy a new directory with its own source and attempt metadata.
