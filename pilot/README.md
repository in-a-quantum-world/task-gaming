# Integrated source pilot

Read SOURCE_PILOT_PREREG.md before any source call. SOURCE_PILOT_CONFIG.yaml
and pilot/configs/first_pilot.json are byte-identical JSON (also valid YAML).
The sole live source route is moonshotai/kimi-k2-thinking on OpenRouter,
provider only novita/bf16, no fallback, require_parameters true.

The reviewed upstream adapter receives explicit temperature 1, top_p 1,
reasoning enabled (native effort unsupported), and max_tokens 16384.
pilot/provider.py applies the same policy to fresh and resumed construction.
It removes the unsupported parallel_tool_calls field and disables both SDK
and outer adapter retries. Tool choice is auto. The existing harness rejects
multiple calls in a decision. Only execute_command is enabled.

## Offline validation

From /home/rucha/ai-alignment-forensics/integrated-pilot:

```bash
python3 pilot/prepare.py
docker build -f pilot/Dockerfile -t integrated-precommit:openrouter .
docker run --rm --network none -v "$PWD:/repo:ro" -w /repo \
  -e PYTHONPATH=/repo/upstream/agent-interp-envs/src \
  -e PYTHON_DOTENV_DISABLED=1 integrated-precommit:openrouter \
  python -m unittest discover -s pilot/tests -v
python3 pilot/run.py fixture --config pilot/configs/archive_fixture.json \
  --image integrated-precommit:openrouter
python3 pilot/run.py restore-check --count 2 \
  --config pilot/configs/archive_fixture.json \
  --image integrated-precommit:openrouter \
  --checkpoint /absolute/source/fixture/data/step-2
```

Both restores compare with the actual ORIGINAL source checkpoint. Compare the
two restored captures too. All required inventory/state/error fields, exact
nanosecond mtimes, and bounded external inventories must agree. These probes
make no model calls. A real checkpoint can also use restore-check with the
source config: it uses a dummy key, no network, and exits before any decision.

## Source run

Use the framework's locked host interpreter (it supplies python-dotenv):

```bash
/home/rucha/ai-alignment-forensics/task-gaming-under-trajectory-pressure/upstream/agent-interp-envs/.venv/bin/python \
  pilot/run.py source --config SOURCE_PILOT_CONFIG.yaml \
  --image EXACT_FROZEN_IMAGE_ID --count 1
```

The runner loads only OPENROUTER_API_KEY from the ignored local .env. It never
prints or embeds the value in a command. The config, image, code, protocol,
and offline gate hashes must match pilot/frozen.json. One two-request preflight
checks the exact settings and a synthetic tool exchange. Only success allows
allocation of the single persistent source slot in Git's common directory.
Allocated failure consumes the slot. There is no source retry or continuation
mode. Read the preregistration's outcome-blind checkpoint review procedure.

## Preservation and grading

Each unique raw directory preserves every completed checkpoint, upstream fs
snapshot, original full workspace archive, original inventories, messages,
state, exact response bodies, native assistant objects, actual requests, usage,
timing, and upstream scorer output. Native API traces precede SDK aliases or
harness recovery from text. The final workspace survives container removal;
failed recovery keeps the container. All failed/slow runs remain.

Read-only artifacts and SHA-256 manifests provide tamper evidence, not WORM.
External files are inventoried but not generally restored. No whole-machine
or hidden provider-state guarantee follows from workspace equality.

After checkpoint selection is recorded, grade all source outcomes offline:

```bash
python3 pilot/grade.py /absolute/source/run --verify-image EXACT_IMAGE_ID \
  --output /absolute/new/independent-grade.json
```

The grader distinguishes native actions, verified effects, and ambiguity.
Thoughts and quoted commands are not attempts. Semantic source correctness
and ambiguous scripts still need human review. Upstream scores stay separate.
No prototype A/B/C history builders or scientific bundles were imported.
