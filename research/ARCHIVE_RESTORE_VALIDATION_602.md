# 602 synthetic archive restore gate

The gate passes on the scientifically required recorded fields. Evidence:
[`archive-three-way.json`](evidence/stress602/archive-three-way.json).

Actual original fixture checkpoint 2 matches two independent offline restores.
All three pairwise comparisons pass. The fixture retains 602 strict errors and
97 model decisions. No real model or model continuation was called.

The comparison covers every regular file under /agent, .git contents, HEAD,
index, status, staged and unstaged diffs, ownership, modes, symlinks, timestamps,
hook, pristine configuration, diagnostic set and count, parsed state.json,
exact message values, checkpoint step, decision budget, and prepared runtime.
There are 105 recorded filesystem entries. Mypy cache contents are included.

The original archive and original inventory were captured in the source
container before removal. Each restore was compared to that original reference,
not just to another reconstructed copy.

An extra state/messages JSON byte check found serializer-format differences.
Parsed JSON values, exact message text, state hashes, and history hashes match.
The raw original JSON remains untouched. This exception is outside /agent;
all regular-file bytes inside /agent match exactly.

External inventory covers /home/dev, /.kimi, selected /tmp contents, Git
configuration, passwd/group, shell and mypy executables, installed packages,
and live dev processes. The fixed external fields match, with no live dev
process dependency. Dead process IDs are recorded but excluded from equality.

This is not whole-machine equivalence. Clocks, kernel, network services,
provider state, secrets, running process memory, and excluded /tmp infrastructure
are outside the guarantee. No real checkpoint restore or history condition is
part of this stage.
