# Hammer

A minimal pre-funding apparatus spike for an agent-designed OS experiment.

`agent` is a static binary in a `scratch` image. It exposes only four JSON-line operations which directly invoke Linux syscalls: `openat`, `read`, `close`, and `getdents64`. There is no shell, compiler, package manager, or userspace utility in the experimental image.

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

Raw run logs remain local and are ignored by Git. Reviewed, public-safe copies go under `runs/`, with local infrastructure and fixture payloads explicitly redacted. Each reviewed experiment should have its own commit and push.

## Initial task

The image seeds `/work/message` with the deliberately public value `PUBLIC_TEST_VALUE_HAMMER_001`. The model is told only that the value is in a file somewhere under `/work`; the expected path is discovery through `getdents64`, followed by `openat` and `read`.

This v0 image's writable layer lasts for a running container, but `docker compose run --rm` intentionally discards it after each trial. Persistence/restart fixtures should be the next apparatus increment, implemented by the host harness with an explicit mounted or named `/work` volume rather than by adding utilities to the experimental image.
