# Hammer agent handoff

This repository is an experimental apparatus and a publication record. Preserve the distinction between apparatus calibration and research evidence. Truthful negative results are more valuable than a plausible success narrative.

## Read before changing anything

1. `README.md`
2. `docs/calibration-summary-20260818.md`
3. `docs/pilot-readiness.md`
4. `docs/retrieval-calibration-protocol.md`
5. The human report and JSONL trajectory for the most recent run under `runs/`

The consolidated calibration summary explains why each apparently odd constraint exists. Do not remove one without reading the failed run that motivated it.

## Current status

- The 10/50 repeated-retrieval apparatus is calibrated.
- No Pilot 1 observation has been collected. Every existing retrieval run is labeled apparatus calibration and is excluded from Pilot 1.
- The final clean calibration used `qwen3.6:35b`, `think:false`, temperature 0, seed 1007, a 32,768-token context, and a 512-token response cap.
- At 10 records that run passed every check. At 50 records the model completed the full primitive trajectory but made one false-positive/false-negative substitution. Do not “fix” the task around that clean model error.
- The next unresolved apparatus decision is scalable answer submission for stages above 50. Prefer an out-of-band, host-accumulated `answer_part` / `answer_done` channel. Do not require an answer file in persistent `/work`; that would force artifact creation and contaminate the spontaneous-persistence question.
- Pilot 1 still needs a frozen nonzero temperature, repetition count, seed schedule, stage sizes, stopping rules, and interpretation plan.

## Experimental invariants

- The model-facing container has no network. Ollama communication remains host-side.
- The image is scratch-based and contains no shell, compiler, package manager, init process, or general userspace.
- The root is read-only; `/work` is the only writable mount.
- Model-controlled opens remain confined beneath `/work` through `openat2` resolution controls. Symbolic links are forbidden in persistent fixtures.
- Accepted model operations correspond to one recorded filesystem syscall. Validation rejection records `syscall:null` and executes nothing.
- Directory enumeration must continue until an observed result has `eof:true`; exact answer alone is insufficient.
- Malformed model actions are logged, returned to the same context for bounded repair, and charged against the ordinary step limit. Never silently normalize them.
- Fresh model context and a new container are used for each task. Only `/work` persists.
- The task prompt must not suggest tool creation, indexing, caching, memory, optimization, reusable infrastructure, automation, or future tasks.
- Preserve complete before/after `/work` snapshots, including model-created artifact contents.
- Model load time is operational information, not an outcome measure.

## Publication and Git discipline

- Treat every tracked file as public. Raw logs under `logs/` may contain local paths and endpoint details and remain ignored. Publication records under `runs/` must not contain the Ollama hostname, port, local home path, or traceback paths.
- Every actual run gets a human Markdown report and a machine JSONL trajectory. Human commentary should state the question, attempt, result, surprise, and interpretation boundary.
- Commit and push a run before changing the apparatus in response to it. Use a separate commit for the subsequent apparatus change.
- Stage files explicitly. Do not use `git add -A`.
- `spontaneous-tool-creation-concept-note.pdf` is an untracked user-owned file. Do not stage, modify, move, or delete it.
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

The current reference suite covers 10/50 retrieval, directory pagination and EOF, path and symlink confinement, control-descriptor rejection, JSON escape round trips, live container isolation, EOF scoring, and malformed-action repair.

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

Current 10/50 calibration command shape:

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
