# Hammer

Hammer is an experimental apparatus for studying whether language-model agents construct useful higher-level capabilities from minimal computational primitives. The larger question is whether an inventory of explicitly supplied tools describes the agent's effective capability surface, or whether ordinary operations can be composed into persistent state, working conventions, indexes, protocols, and eventually executable tools that the system designer did not provide.

The project keeps that question deliberately narrow. It does not assume that useful structures will emerge, and it does not treat every file an agent leaves behind as a tool. Hammer records the model's complete adapter-visible action trajectory and filesystem lineage so that construction, use, reuse, and failure can be examined rather than inferred from the final answer alone.

The initial research pilot is being designed around one difficult, long-running goal in which external intermediate state could help the model's current objective without being requested by the prompt. A later experiment will study agents that know their environment will outlive the current context. See the [research overview](docs/research-overview.md) for the premise, scope, questions, and safety relevance.

## Apparatus

`agent` is a static binary in a `scratch` image. It exposes five JSON-line operations backed by one Linux filesystem syscall apiece: confined `openat` actions use `openat2`; the others use `read`, `write`, `close`, and `getdents64`. There is no shell, compiler, package manager, init process, or userspace utility in the experimental image. The root filesystem is read-only, all capabilities are dropped, and model-controlled paths are restricted beneath `/work` without following symbolic links.

The model loop is deliberately host-side. Docker Compose runs the experimental service with `network_mode: none`, so its model communication is not routed through the container network namespace. The host harness makes requests to Ollama and exchanges the model's actions with the agent over the container's standard input/output pipes.

## Run

Prerequisites: Docker Compose, Python 3, and an Ollama endpoint. The default model is `qwen3.6:35b`, the model used for the final clean retrieval calibration. `OLLAMA_HOST` defaults to `http://localhost:11434` and can be set to another endpoint.

```sh
cd hammer
make build
python3 harness.py
```

Or choose another installed Ollama model:

```sh
OLLAMA_HOST=http://ollama.example:11434 OLLAMA_MODEL=qwen3.6:35b python3 harness.py
```

The harness explicitly requests a 32,768-token context, a 128-token maximum response, temperature 0, and non-thinking output. Override these with `HAMMER_NUM_CTX`, `HAMMER_NUM_PREDICT`, `HAMMER_TEMPERATURE`, and `HAMMER_THINK`. The reasoning-mode request is recorded with the other inference settings. Every model turn records Ollama's native input/output token counts, timing fields, done reason, live-context estimate, and context utilization. Each task summary distinguishes peak live context from cumulative token processing.

Each execution writes the complete adapter-visible JSONL trajectory under `logs/`: raw model responses, the action selected, the adapter request, and its syscall result. This is not a kernel-wide trace of hidden container setup. `harness.py` is outside the experimental world; it is the fixture/harness boundary rather than an accidental container service.

Every execution now writes three records. Raw JSONL under `logs/` includes local paths and endpoint details and remains ignored by Git. Publication JSONL under `runs/` omits local infrastructure but preserves the prompts, model responses, syscall requests/results, timing, apparatus commit, image identity, generation boundaries, and explicit pass/fail checks. A companion Markdown report explains the question, method, result, measurements, anomalies, and interpretation boundary for a human reader. Each reviewed experiment gets its own commit and push.

## Initial task

The image seeds `/work/message` with the deliberately public value `PUBLIC_TEST_VALUE_HAMMER_001`. The model is told only that the value is in a file somewhere under `/work`; the expected path is discovery through `getdents64`, followed by `openat` and `read`.

## Persistence/restart apparatus check

The persistence check gives two sequential containers the same host-created `/work` fixture while giving each generation a fresh model context. Generation 1 is explicitly instructed to create a marker through `openat`, `write`, and `close`; its container is destroyed. Generation 2 starts in a new network-disabled container, discovers the marker through `getdents64`, and reads it back. The host verifies the exact bytes, distinct container identities, both network modes, and the final answer.

```sh
make build
python3 persistence.py
```

The local persisted fixture is retained under ignored `.work/` state for post-run inspection. The experimental image still contains no compiler or general-purpose userspace. This proves that state can cross a restart; because the prompt requires the marker, it is not evidence of spontaneous persistence.

## Repeated-retrieval calibration

`retrieval.py` is an apparatus calibration, not Pilot 1. It grows one persistent public corpus from 10 to 50 fixed-size records while replacing the container and model context between stages. Filenames, record labels, payloads, and creation order come from separately seeded deterministic streams. The task text is identical at both stages and asks only for an exact retrieval outcome. The host records the external answer oracle, exact score, independently required directory-EOF observation, action budget, complete before/after `/work` snapshots, agent-created artifacts, isolation state, model usage, and terminal failures.

Scientific runs refuse to start unless the relevant apparatus files are clean and the local image label names that exact Git commit. Commit the apparatus before building it:

```sh
make build
HAMMER_SEED=1007 HAMMER_NUM_PREDICT=512 OLLAMA_MODEL=qwen3.6:35b \
  OLLAMA_HOST=http://ollama.example:11434 python3 retrieval.py
```

The default corpus seed is `20260818`. Sampling seed is mandatory, and retrieval calibration refuses a response cap below 512 tokens because the ten-name 50-file answer does not fit in 128. Calibration defaults to temperature 0. The current 10% step margin is measured against a primitive exhaustive scan. Sizes above 50 remain provisional for any future retrieval study.

Run the model-independent reference client with:

```sh
make test
```

It performs complete 10- and 50-record scans with valid 512-byte directory pages, verifies EOF pagination and exact retrieval, exercises JSON escaping, rejects path and symlink escapes, protects the control descriptors, and inspects the live container isolation settings. Schema rejections explicitly report that no syscall was executed.

## Current research direction

The retrieval work calibrated the apparatus, but it also exposed an incentive error in the proposed experiment. A model given a fresh context, one independent task, and no reason to expect a successor has no reason to build infrastructure for that successor. Repeated host-side tasks do not by themselves create a model-visible future.

Pilot 1 is therefore being redesigned around one difficult, long-running goal in one continuous context. The task should make interim external state useful now without asking for notes, indexes, tools, caching, or future planning. Its first product will be a forensic record of successful, failed, and abandoned external constructions. A small deterministic task-outcome check will close each observation, but will not reward a preferred strategy or decide whether an artifact is interesting. See the [forensic-observation protocol](docs/forensic-observation-protocol.md).

Known-future persistence across context resets is a separate later experiment. In that condition, the existence of future work is an explicit treatment variable rather than information available only to the experimenter. The concrete Pilot 1 task, controls, budgets, repetitions, seeds, and artifact rubric still need to be frozen before a research run.

## Model-serving environment

Pilot runs use a dedicated AMD Strix Halo system with 128 GB unified memory. The controlled Ollama environment permits one loaded model and one request at a time, uses the model's native 32K context, retains `f16` KV-cache precision, and enables Flash Attention. The public environment settings are recorded in `infrastructure/ollama-experiment.env`; each run additionally records the live Ollama version, model digest, advertised and loaded contexts, and loaded VRAM allocation.

## Protocol notes

- [Experiment index and naming convention](docs/index.md)
- [Research overview](docs/research-overview.md)
- [Pilot readiness criteria](docs/pilot-readiness.md)
- [Pilot 1 forensic-observation protocol](docs/forensic-observation-protocol.md)
- [C48 declared-compaction treatment protocol](docs/pilot-1-c48-compaction-protocol.md)
- [C48 horizon-information follow-up protocol](docs/c48-horizon-information-protocol.md)
- [Pilot 1 task-selection draft](docs/pilot-1-task-selection.md)
- [Pilot 1 live-reconciliation semantic task draft](docs/pilot-1-live-reconciliation-spec.md)
- [Live-reconciliation adversarial review and rejection](docs/pilot-1-live-reconciliation-adversarial-review.md)
- [Pilot 1 G32 semantic task draft](docs/pilot-1-g32-spec.md)
- [G32 adversarial review and decision](docs/pilot-1-g32-adversarial-review.md)
- [2026-08-18 Pilot 1 direction correction](docs/pilot-1-direction-20260818.md)
- [Future VM execution and escape-canary design](docs/vm-execution-design.md)
- [Retrieval calibration protocol](docs/retrieval-calibration-protocol.md)
- [2026-08-18 apparatus hardening record](docs/apparatus-hardening-20260818.md)
- [2026-08-18 calibration summary and readiness decision](docs/calibration-summary-20260818.md)
