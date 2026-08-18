# Hammer

A minimal pre-funding apparatus spike for an agent-designed OS experiment.

`agent` is a static binary in a `scratch` image. It exposes five JSON-line operations backed by one Linux filesystem syscall apiece: confined `openat` actions use `openat2`; the others use `read`, `write`, `close`, and `getdents64`. There is no shell, compiler, package manager, init process, or userspace utility in the experimental image. The root filesystem is read-only, all capabilities are dropped, and model-controlled paths are restricted beneath `/work` without following symbolic links.

The model loop is deliberately host-side. Docker Compose runs the experimental service with `network_mode: none`, so its model communication is not routed through the container network namespace. The host harness makes requests to Ollama and exchanges the model's actions with the agent over the container's standard input/output pipes.

## Run

Prerequisites: Docker Compose, Python 3, and an Ollama endpoint. The default model is `qwen2.5:7b-instruct`; it completed the initial task promptly in the validation run. `OLLAMA_HOST` defaults to `http://localhost:11434` and can be set to another endpoint.

```sh
cd hammer
make build
python3 harness.py
```

Or choose another installed Ollama model:

```sh
OLLAMA_HOST=http://ollama.example:11434 OLLAMA_MODEL=qwen3.6:35b python3 harness.py
```

The harness explicitly requests a 32,768-token context, a 128-token maximum response, and temperature 0. Override these with `HAMMER_NUM_CTX`, `HAMMER_NUM_PREDICT`, and `HAMMER_TEMPERATURE`. Every model turn records Ollama's native input/output token counts, timing fields, done reason, live-context estimate, and context utilization. Each task summary distinguishes peak live context from cumulative token processing.

Each execution writes the complete adapter-visible JSONL trajectory under `logs/`: raw model responses, the action selected, the adapter request, and its syscall result. This is not a kernel-wide trace of hidden container setup. `harness.py` is outside the experimental world; it is the fixture/harness boundary rather than an accidental container service.

Every execution now writes three records. Raw JSONL under `logs/` includes local paths and endpoint details and remains ignored by Git. Publication JSONL under `runs/` omits local infrastructure but preserves the prompts, model responses, syscall requests/results, timing, apparatus commit, image identity, generation boundaries, and explicit pass/fail checks. A companion Markdown report explains the question, method, result, measurements, anomalies, and interpretation boundary for a human reader. Each reviewed experiment gets its own commit and push.

## Initial task

The image seeds `/work/message` with the deliberately public value `PUBLIC_TEST_VALUE_HAMMER_001`. The model is told only that the value is in a file somewhere under `/work`; the expected path is discovery through `getdents64`, followed by `openat` and `read`.

## Persistence/restart experiment

The persistence experiment gives two sequential containers the same host-created `/work` fixture while giving each generation a fresh model context. Generation 1 creates a marker through `openat`, `write`, and `close`; its container is destroyed. Generation 2 starts in a new network-disabled container, discovers the marker through `getdents64`, and reads it back. The host verifies the exact bytes, distinct container identities, both network modes, and the final answer.

```sh
make build
python3 persistence.py
```

The local persisted fixture is retained under ignored `.work/` state for post-run inspection. The experimental image still contains no compiler or general-purpose userspace.

## Repeated-retrieval calibration

`retrieval.py` is an apparatus calibration, not Pilot 1. It grows one persistent public corpus from 10 to 50 fixed-size records while replacing the container and model context between stages. Filenames, record labels, payloads, and creation order come from separately seeded deterministic streams. The task text is identical at both stages and asks only for an exact retrieval outcome. The host records the external answer oracle, exact score, independently required directory-EOF observation, action budget, complete before/after `/work` snapshots, agent-created artifacts, isolation state, model usage, and terminal failures.

Scientific runs refuse to start unless the relevant apparatus files are clean and the local image label names that exact Git commit. Commit the apparatus before building it:

```sh
make build
HAMMER_SEED=1001 OLLAMA_HOST=http://ollama.example:11434 python3 retrieval.py
```

The default corpus seed is `20260818`. Sampling seed is mandatory. Calibration defaults to temperature 0; Pilot 1 repetitions will use an explicitly frozen sampling policy and distinct recorded seeds. The current 10% step margin is measured against a primitive exhaustive scan. Sizes above 50 remain provisional until this calibration establishes action and context growth.

Run the model-independent reference client with:

```sh
make test
```

It performs complete 10- and 50-record scans with valid 512-byte directory pages, verifies EOF pagination and exact retrieval, exercises JSON escaping, rejects path and symlink escapes, protects the control descriptors, and inspects the live container isolation settings. Schema rejections explicitly report that no syscall was executed.

## Model-serving environment

Pilot runs use a dedicated AMD Strix Halo system with 128 GB unified memory. The controlled Ollama environment permits one loaded model and one request at a time, uses the model's native 32K context, retains `f16` KV-cache precision, and enables Flash Attention. The public environment settings are recorded in `infrastructure/ollama-experiment.env`; each run additionally records the live Ollama version, model digest, advertised and loaded contexts, and loaded VRAM allocation.

## Protocol notes

- [Pilot readiness criteria](docs/pilot-readiness.md)
- [Retrieval calibration protocol](docs/retrieval-calibration-protocol.md)
- [2026-08-18 apparatus hardening record](docs/apparatus-hardening-20260818.md)
