# Hammer

A minimal pre-funding apparatus spike for an agent-designed OS experiment.

`agent` is a static binary in a `scratch` image. It exposes five JSON-line operations which directly invoke Linux syscalls: `openat`, `read`, `write`, `close`, and `getdents64`. There is no shell, compiler, package manager, or userspace utility in the experimental image.

The model loop is deliberately host-side. Docker Compose runs the experimental service with `network_mode: none`, so its model communication is not routed through the container network namespace. The host harness makes requests to Ollama and exchanges the model's actions with the agent over the container's standard input/output pipes.

## Run

Prerequisites: Docker Compose, Python 3, and an Ollama endpoint. The default model is `qwen2.5:7b-instruct`; it completed the initial task promptly in the validation run. `OLLAMA_HOST` defaults to `http://localhost:11434` and can be set to another endpoint.

```sh
cd /Users/br/src/hammer
docker compose build
python3 harness.py
```

Or choose another installed Ollama model:

```sh
OLLAMA_HOST=http://ollama.example:11434 OLLAMA_MODEL=qwen3.6:35b python3 harness.py
```

Each execution writes a complete JSONL trajectory under `logs/`: raw model responses, the action selected, the adapter request, and its syscall result. `harness.py` is outside the experimental world; it is the fixture/harness boundary rather than an accidental container service.

Every execution now writes two records in parallel. Raw logs under `logs/` include local paths and endpoint details and remain ignored by Git. Publication records under `runs/` omit local infrastructure but preserve the prompts, model responses, syscall requests/results, timing, apparatus commit, image identity, generation boundaries, and explicit pass/fail checks. Each reviewed experiment gets its own commit and push.

## Initial task

The image seeds `/work/message` with the deliberately public value `PUBLIC_TEST_VALUE_HAMMER_001`. The model is told only that the value is in a file somewhere under `/work`; the expected path is discovery through `getdents64`, followed by `openat` and `read`.

## Persistence/restart experiment

The persistence experiment gives two sequential containers the same host-created `/work` fixture while giving each generation a fresh model context. Generation 1 creates a marker through `openat`, `write`, and `close`; its container is destroyed. Generation 2 starts in a new network-disabled container, discovers the marker through `getdents64`, and reads it back. The host verifies the exact bytes, distinct container identities, both network modes, and the final answer.

```sh
docker compose build
python3 persistence.py
```

The local persisted fixture is retained under ignored `.work/` state for post-run inspection. The experimental image still contains no compiler or general-purpose userspace.
