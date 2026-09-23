# Archive restore validation

Status: PASS on the final synthetic infrastructure fixture, against its actual
ORIGINAL source checkpoint. This historical fixture result is followed below by real-checkpoint validation.
No model continuation occurred during any validation probe.

Image ID: `sha256:14bb9a6b1ca097793c25038a6e088e9e33497365bac7e194cc6eeefa1ae14f1e`.
Base image ID: `sha256:b756b5d4756b6ed05bbbbe2ba55e7b767b422ee86f24ebf496ac8735793afb5d`.
Framework base commit: `56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb` plus recorded patch.

## Three-way comparison

| Comparison | Audit verdict | Changed paths | Timestamp match | External file/package gate |
|---|---|---:|---|---|
| ORIGINAL vs restore 1 | equal_on_recorded_fields | 0 | Exact nanoseconds | Pass |
| ORIGINAL vs restore 2 | equal_on_recorded_fields | 0 | Exact nanoseconds | Pass |
| Restore 1 vs restore 2 | equal_on_recorded_fields | 0 | Exact nanoseconds | Both match original |

All three captures have no validator issues or probe-induced workspace changes.
The original capture precedes every extraction and the next scripted decision.
Its independent inventory also matches the archive source inventory.
The original is not a reconstructed copy.

| Required field | Measurement and result |
|---|---|
| Complete `/agent` | All 104 entries, including the root; regular-file SHA-256 equality |
| Complete `.git` | All 76 entries included; no Git exclusions |
| HEAD | `0573cf81344c41b92c45cae9043a66e837a7240f` in all three |
| Index | Exact `.git/index` bytes and metadata; tracked-index entries also match |
| Git status | Exact porcelain output, with staged and unstaged state |
| Staged diff | Exact binary diff; staged marker and probe file |
| Unstaged diff | Exact binary diff; probe file differs from its staged bytes |
| Permissions | Exact ordinary mode bits for every entry |
| Symlinks | Exact targets; file link and directory link both present |
| Ownership | Exact uid/gid for every entry, including mixed root/dev data where present |
| Hook | Exact bytes, uid/gid, mode, and executable bits |
| `pyproject.toml` | Exact bytes and metadata; pristine strict policy |
| Mypy cache | Included in complete inventory and archive; no cache omission |
| Active mypy error set | 258 errors; exact diagnostic set and hash |
| Pristine-policy error set | 258 errors; exact diagnostic set and hash |
| `state.json` | Full dataclass hash equal, including command trace and counters |
| Current checkpoint step | 2, after its scripted action |
| Remaining decisions | `100 - 2 - 1 = 97` |
| Messages and tools | Exact message history, original prompts, last exchange, and schemas |
| Runtime parameters | Same actual mock-provider construction and fixed runtime metadata |
| Timestamps | Exact nanosecond mtime equality after explicit restoration |

Symlinks in this fixture: `{'dir-link': 'src', 'probe-link': 'probe.txt'}`.
The source fixture includes a same-size, preserved-mtime edit. A unit test also
checks loss of an untouched inherited file across two archive generations.
These are infrastructure tests, not model behavior or accumulated repair effort.
The fixture makes no substantive source repairs and has no eligible checkpoint.

## Relevant external state

The source and restores capture these task-relevant roots and properties:

- `/home/dev`, including files from any user-level package install.
- `/.kimi`, including explicit absence when memory tools are off.
- `/tmp` regular-file state, except separately recorded harness paths.
- Installed Python distribution names and versions.
- Shell/mypy executable content and fixed Git/user/group config hashes.
- Observed `dev` process IDs, names, and states.

The file/package comparator excludes `/tmp/config.yaml`, which has its own config
hash. It also excludes the harness blob cache and `/tmp` root metadata.
Defunct process IDs are recorded but excluded from equality. Active dev processes
block the gate. The successful fixture has no active dev process at capture.
`docker diff` records container-layer changes at termination for every run.

This inventory is not a general external-state restore mechanism. A real source
that changes captured external files may require a further archive design before
continuation. The restore gate fails when those fixed external fields differ.
The current source runner has no model continuation mode.

## Scope limits

No claim covers ACLs, xattrs, inode identity, hardlink graph identity, or atime/ctime.
No claim covers process state, file descriptors, kernel state, RNGs, clocks,
network services, remote resources, provider caches, or hidden serving state.
The validator's mypy probes run as root. The source's actual tool observations
remain available separately; permission-dependent diagnostic equivalence needs
additional review if a real source uses such behavior.
External symlinks and special files require a new reviewed restore design.
A full archive is not an atomic machine snapshot; before/after inventories and
active-process checks reject measured instability but cannot eliminate all races.

## Preserved failures and repairs

The first build attempt failed on a Docker `FROM` reference format.
Two early restores matched every workspace field but failed an external
list/tuple comparison. Both raw failures remain preserved.
A separate bypass fixture stopped on a defunct Git process. Its complete
checkpoint remains preserved. The revised process-state gate excludes only zombies.
No failed probe received a model continuation.

## Exact final evidence and paths

- Original checkpoint: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot/fixture-44fad38897894fcf8c74fb97dfec2d5f/data/step-2`.
- Restore 1: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot/restore-check-d3c7ca5582d54b488ae5e3eb632dccbe`.
- Restore 2: `/home/rucha/ai-alignment-forensics/integrated-pilot/research/data/raw/integrated-pilot/restore-check-39a113654c4f452085122152e488e6dc`.
- Complete comparison: `evidence/integration/archive-three-way.json`.
- Original capture: `evidence/integration/final-state-0.json`.
- Restored captures: `evidence/integration/final-state-1.json` and `final-state-2.json`.
- Original and restored independent inventories: `evidence/integration/final-inventory-*.json`.
- External inventories: `evidence/integration/final-external-*.json`.
- Exact commands: `evidence/integration/final-runs.json`.
- All attempts: `evidence/integration/run-ledger.json`.

Re-run the commands in `pilot/README.md` with unique run directories.
Use the original checkpoint for both restores. Never replace this test with a
replica-only comparison or suppress a Git/cache mismatch.

## 2026-09-10 OpenRouter image revalidation

PASS on image `sha256:271a3daf958c33c9e6ad7332624015f9303ef06bf2a805abd12004abff8ddbae`. The original synthetic checkpoint and both
independent restores match on every required field, nanosecond mtimes, and the
bounded external inventory. Each has 104 entries, 258 strict errors, saved step
2, and 97 decisions remaining. No model decisions occurred in either restore.

Exact paths and three pairwise comparisons:
`evidence/integration/openrouter-pilot/archive-three-way.json`.
Full state captures: `validation-0.json`, `validation-1.json`, `validation-2.json`
in that evidence directory. External captures: `external-0.json` through
`external-2.json`. All raw manifests verified. The scope limits above still apply.

## Real checkpoint 42 — 2026-09-10

The source was generated on image
`sha256:271a3daf958c33c9e6ad7332624015f9303ef06bf2a805abd12004abff8ddbae`.
Its original full archive and original inventory were captured before container
removal. Step42 was the earliest near-candidate in ordered review. Before opening
step43, two offline restores used the unchanged source config and a dummy key,
with Docker network disabled. No model invocation or continuation occurred.

All three pairs agree on every required recorded field. There are 99 workspace
entries and nine strict errors with the identical diagnostic set. Step42 and
57 remaining decisions match. Git HEAD/index/status/diffs, complete regular-file
bytes, .git, modes, symlinks, ownership, hook, pyproject, state, history, runtime,
and nanosecond mtimes match. Relevant external inventories also match.
No whole-machine or general external-state equivalence is asserted.

Evidence: `evidence/integration/real-source-review/checkpoint-042-three-way.json`.
The same directory contains all three validation, external, and original-inventory
copies. Original raw checkpoint:
`data/raw/integrated-pilot/source-4f522c3fe196414c975797817b07e35c/data/step-42`.
Restores:
`data/raw/integrated-pilot/restore-check-bd85003692844df1bc6778b5bda82f13/data/restored`
and
`data/raw/integrated-pilot/restore-check-b3b1c2293b9040eeb9f0518e1c8b9bb5/data/restored`.

Restoration fidelity does not certify scientific eligibility or functional
correctness. Earlier targeted ignores block automatic checkpoint selection.
Later offline probes also find a runtime import failure in the faithfully
restored source. The archive preserves that actual defect; it does not repair it.
