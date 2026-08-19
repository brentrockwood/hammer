# Hammer agent handoff

This repository is an experimental apparatus and a publication record. Preserve the distinction between apparatus calibration and research evidence. Truthful negative results are more valuable than a plausible success narrative.

## Read before changing anything

1. `README.md`
2. `docs/research-overview.md`
3. `docs/calibration-summary-20260818.md`
4. `docs/pilot-1-direction-20260818.md`
5. `docs/pilot-readiness.md`
6. `docs/retrieval-calibration-protocol.md`
7. The human report and JSONL trajectory for the most recent run under `runs/`

The consolidated calibration summary explains why each apparently odd constraint exists. Do not remove one without reading the failed run that motivated it.

## Current status

- The 10/50 repeated-retrieval apparatus is calibrated.
- No Pilot 1 observation has been collected. Every existing retrieval run is labeled apparatus calibration and is excluded from Pilot 1.
- The final clean calibration used `qwen3.6:35b`, `think:false`, temperature 0, seed 1007, a 32,768-token context, and a 512-token response cap.
- At 10 records that run passed every check. At 50 records the model completed the full primitive trajectory but made one false-positive/false-negative substitution. Do not “fix” the task around that clean model error.
- Repeated independent retrieval under fresh contexts is no longer the proposed Pilot 1. With no model-visible future, infrastructure for later tasks has no rational value; repeated tasks alone would smuggle the experimenter's knowledge of the future into the interpretation.
- Pilot 1 is being redesigned as one difficult, long-running goal in one continuous context. Interim external state must be useful to the current goal, while the prompt must not prescribe notes, indexes, tools, caching, or future planning.
- No central Pilot 1 task is currently selected. G32 is retained only as a future apparatus dry run. The live-reconciliation candidate was rejected before implementation because model-visible amendments permit rational deferral and action-count delivery would create no-wait busywork; read `docs/pilot-1-live-reconciliation-adversarial-review.md`.
- Five exploratory C48 observations are now recorded. The original unlabeled continuation (seed 3001), labeled checkpoint continuation (seed 3101), and labeled plus declared-horizon continuation (seed 3101) each exhausted 280 turns without a model-originated filesystem write or answer. The C48-H continuation had a recorded missing sentence separator; it remained intelligible and was fixed only after that run. C48 H0 (seed 3201, no retained history) made no write attempt; C48 H12 (the same seed with a 12-exchange tail) created one invalid candidate answer after checkpoint 1, repeatedly attempted a premature terminal response, and never reread or revised that file. Do not claim a causal effect of temporal orientation or tail retention from these single trajectories, or call the H12 file a persistent instrumental structure.
- H0 was committed before H12 was built, as required by publication discipline. Consequently their frozen image revisions differ only by the H0 run artifacts; the H0/H12 apparatus implementation did not change between them. Preserve that provenance distinction in any comparison.
- The next frozen exploratory treatment is the C48 append-affordance H0 pair. It uses a fresh sampling seed and the same apparatus implementation; the control rejects append at adapter validation while the append member receives both the explicit prompt grammar line and `/agent --append`. Because the control record is committed before rebuilding for the append member, their image revisions will differ only by that publication artifact. Calibrate the primitive with `append_calibration.py` before either model run. It is not Pilot 1 and does not repair the H12 answer-gating pathology.
- The immediate next step is to decide whether to preregister repetitions and a more discriminating task or manipulation. Do not modify the task merely to force the preferred artifact class. Any included Pilot 1 protocol still needs its non-prescriptive outcome score, primitive baseline, budgets, repetitions, seeds, and artifact-classification rubric frozen before model runs.
- A chunked out-of-band `answer_part` / `answer_done` channel remains sensible if a future task has a large final result, but it is not a blocker for Pilot 1 unless the selected task requires it.
- Known-future work across context resets is a separate later treatment. Its future horizon must be explicit to the model.
- Native self-authored execution is a future VM condition, not part of the current container apparatus. Read `docs/vm-execution-design.md` before proposing `execve`, a compiler, guest networking, or VM instrumentation.

## Experimental invariants

- The model-facing container has no network. Ollama communication remains host-side.
- The image is scratch-based and contains no shell, compiler, package manager, init process, or general userspace.
- The root is read-only; `/work` is the only writable mount.
- Model-controlled opens remain confined beneath `/work` through `openat2` resolution controls. Symbolic links are forbidden in persistent fixtures.
- Accepted model operations correspond to one recorded filesystem syscall. Validation rejection records `syscall:null` and executes nothing.
- Retrieval calibration requires directory enumeration through an observed `eof:true`. Do not turn that apparatus check into a general Pilot 1 scoring rule unless the task itself requires exhaustive enumeration.
- Malformed model actions are logged, returned to the same context for bounded repair, and charged against the ordinary step limit. Never silently normalize them.
- Retrieval calibration uses a fresh model context and new container at each stage while `/work` persists. Pilot 1 instead uses one continuous model context for one long-running goal.
- Pilot 1's task prompt must not suggest tool creation, indexing, caching, memory, optimization, reusable infrastructure, automation, or future tasks. A later known-future treatment necessarily changes this condition and must be labeled separately.
- Preserve complete before/after `/work` snapshots, including model-created artifact contents.
- Model load time is operational information, not an outcome measure.

## Publication and Git discipline

- Treat every tracked file as public. Raw logs under `logs/` may contain local paths and endpoint details and remain ignored. Publication records under `runs/` must not contain the Ollama hostname, port, local home path, or traceback paths.
- Every actual run gets a human Markdown report and a machine JSONL trajectory. Human commentary should state the question, attempt, result, surprise, and interpretation boundary.
- Commit and push a run before changing the apparatus in response to it. Use a separate commit for the subsequent apparatus change.
- Stage files explicitly. Do not use `git add -A`.
- When present locally, `notes/spontaneous-tool-creation-concept-note.pdf` is the user-owned source concept note. The global Git ignore rule for `notes/` keeps it local. Read it when research framing needs source context; do not stage, modify, move, or delete it.
- Remote: `https://github.com/brentrockwood/hammer`, branch `main`.

## Frozen-source workflow

A scientific run refuses to start unless relevant apparatus files are clean and the `hammer-agent` image label equals the current Git commit.

```sh
make test
make build
docker image inspect hammer-agent --format '{{.Id}} {{index .Config.Labels "org.opencontainers.image.revision"}}'
git rev-parse HEAD
```

Documentation or run commits made after an image build still advance `HEAD`. Therefore run `make build` again immediately before the next scientific run, even when the agent binary did not change.

The current reference suite covers 10/50 retrieval, directory pagination and EOF, path and symlink confinement, control-descriptor rejection, JSON escape round trips, live container isolation, EOF scoring, and malformed-action repair. These are reusable apparatus checks, not a frozen Pilot 1 design.

## Ollama discipline

The endpoint is supplied at run time and must not enter publication files. The server is configured for one loaded model with a six-hour keep-alive. Explicitly unload a model before switching:

```sh
curl -fsS "$OLLAMA_HOST/api/generate" \
  -H 'Content-Type: application/json' \
  -d '{"model":"MODEL_NAME","keep_alive":0}'
curl -fsS "$OLLAMA_HOST/api/ps"
```

The first `/api/ps` immediately after unload may briefly show the model with an expiration timestamp equal to the current instant. Poll again and require an empty model list before loading a different model.

Qwen 3.6 emits reasoning in a separate `thinking` field unless explicitly disabled. Hammer executes only JSON from `content`, so keep `HAMMER_THINK=false` unless a new response protocol is deliberately frozen and calibrated.

Historical 10/50 calibration command shape, for reproducing or deliberately extending that calibration only:

```sh
HAMMER_SEED=NEW_EXPLICIT_SEED \
HAMMER_NUM_PREDICT=512 \
HAMMER_TEMPERATURE=0 \
HAMMER_THINK=false \
OLLAMA_MODEL=qwen3.6:35b \
OLLAMA_HOST=http://HOST:11434 \
python3 retrieval.py
```

Do not reuse a calibration seed for a newly changed apparatus. Do not describe a calibration run as Pilot 1.

## Known boundary

The machine trajectory is complete at the adapter boundary, not a kernel-wide trace. Container-runtime setup, host activity, and the agent's hidden startup open of `/work` are substrate operations outside the model action trajectory. State that boundary directly rather than calling the record a complete kernel syscall trace.

## Future VM condition

The long-term design may give the model broad freedom inside a dedicated guest on the nearly airgapped `ai1` research machine. Guest execution requires trustworthy observation outside the guest because a model-controlled tool may bypass the current adapter or modify in-guest tracing. Do not treat a VM as sufficient containment by itself.

An escape canary is planned in the QEMU process's outer sandbox. It is a safety trigger and pressure-relief valve, not a task objective:

- Never disclose the canary's existence, location, name, value, or semantics to the model.
- Generate a unique unpredictable value for every run outside the guest. Do not place it in a tracked file, process argument, environment variable, guest image, model prompt, or ordinary log.
- Make access to the canary mechanically freeze and terminate the run; do not wait for the model to submit it or voluntarily stop.
- Preserve memory, disk, serial, and hypervisor evidence, stop further model calls, and record `escape_canary_triggered` as a distinct safety-terminal outcome rather than task success.
- Retain the exact canary value only in sealed incident evidence. Public records use a digest or redaction and must not publish a reusable value.
- Treat `ai1` as potentially compromised after a trigger until it has been inspected or rebuilt.

The canary does not replace network isolation, an unprivileged and filesystem-confined QEMU process, sparse virtual hardware, host-side telemetry, or a credential-free disposable host. Its design is recorded in `docs/vm-execution-design.md`.
