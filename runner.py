"""Shared host-side runner for Hammer experiments."""
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in ("1", "true", "yes", "on"):
        return True
    if normalized in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"{name} must be true or false")


@dataclass(frozen=True)
class Settings:
    model: str = os.environ.get("OLLAMA_MODEL", "qwen3.6:35b")
    ollama: str = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    max_steps: int = int(os.environ.get("HAMMER_MAX_STEPS", "10"))
    temperature: float = float(os.environ.get("HAMMER_TEMPERATURE", "0"))
    num_ctx: int = int(os.environ.get("HAMMER_NUM_CTX", "32768"))
    num_predict: int = int(os.environ.get("HAMMER_NUM_PREDICT", "128"))
    seed: int | None = (
        int(os.environ["HAMMER_SEED"]) if os.environ.get("HAMMER_SEED") else None
    )
    think: bool = env_bool("HAMMER_THINK", False)

    def ollama_options(self):
        options = {
            "temperature": self.temperature,
            "num_ctx": self.num_ctx,
            "num_predict": self.num_predict,
        }
        if self.seed is not None:
            options["seed"] = self.seed
        return options

    def inference_options(self):
        return {**self.ollama_options(), "think": self.think}


def new_run_id(scenario):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{scenario}-{stamp}"


def git_commit():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


APPARATUS_PATHS = (
    ".dockerignore", "Dockerfile", "compose.yaml", "Makefile", "agent.c", "runner.py",
    "harness.py", "persistence.py", "retrieval.py", "c48.py", "corpus.py",
    "graph_task.py", "tests",
    "fixtures", "infrastructure",
)


def apparatus_worktree_status():
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--",
         *APPARATUS_PATHS],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    return result.stdout.strip().splitlines()


def image_metadata():
    result = subprocess.run(
        ["docker", "image", "inspect", "hammer-agent"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if result.returncode != 0:
        return {"image_id": "unavailable", "image_revision": "unavailable"}
    info = json.loads(result.stdout)[0]
    labels = info.get("Config", {}).get("Labels") or {}
    return {
        "image_id": info.get("Id", "unavailable"),
        "image_revision": labels.get(
            "org.opencontainers.image.revision", "unavailable"
        ),
    }


class ExperimentLog:
    """Write a private raw log and a publication-safe record in parallel."""

    def __init__(self, run_id):
        self.run_id = run_id
        self.raw_path = ROOT / "logs" / f"{run_id}.jsonl"
        self.public_path = ROOT / "runs" / f"{run_id}.jsonl"
        self.raw_path.parent.mkdir(exist_ok=True)
        self.public_path.parent.mkdir(exist_ok=True)

    def event(self, kind, *, public_fields=None, **fields):
        base = {"ts": time.time(), "run_id": self.run_id, "event": kind}
        raw = {**base, **fields}
        public = {**base, **(fields if public_fields is None else public_fields)}
        for path, row in ((self.raw_path, raw), (self.public_path, public)):
            with path.open("a") as stream:
                stream.write(json.dumps(row, separators=(",", ":")) + "\n")

    def write_report(self, *, title, question, method, result, interpretation):
        rows = [json.loads(line) for line in self.public_path.read_text().splitlines()]
        start = next(row for row in rows if row["event"] == "run_start")
        end = next(row for row in reversed(rows) if row["event"] == "run_end")
        generation_ends = [row for row in rows if row["event"] == "generation_end"]
        syscall_rows = [row for row in rows if row["event"] == "syscall_request"]
        answers = [row for row in rows if row["event"] == "generation_answer"]
        rejected_actions = [
            row for row in rows if row["event"] == "model_action_rejected"
        ]
        syscall_counts = {}
        for row in syscall_rows:
            operation = row["request"].get("op", "unknown")
            syscall_counts[operation] = syscall_counts.get(operation, 0) + 1

        report_path = ROOT / "runs" / f"{self.run_id}.md"
        status = "PASS" if end.get("passed") else "FAIL"
        lines = [
            f"# {title}",
            "",
            question,
            "",
            method,
            "",
            f"The run **{status.lower()}ed**. {result}",
            "",
            "## Apparatus",
            "",
            f"- Run: `{self.run_id}`",
            f"- Apparatus commit: `{start.get('apparatus_commit', 'not recorded')}`",
            f"- Model: `{start.get('model', 'not recorded')}`",
            f"- Image: `{start.get('image_id', 'not recorded')}`",
            f"- Image source revision: `{start.get('image_revision', 'not recorded')}`",
            f"- Inference options: `{json.dumps(start.get('inference_options', {}), separators=(',', ':'))}`",
            "",
            "## Measurements",
            "",
            "| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
        for row in generation_ends:
            usage = row.get("usage_summary", {})
            lines.append(
                "| {generation} | {calls} | {prompt} | {completion} | {peak} | {fraction:.1%} |".format(
                    generation=row.get("generation"),
                    calls=usage.get("model_calls", 0),
                    prompt=usage.get("cumulative_prompt_tokens", 0),
                    completion=usage.get("cumulative_completion_tokens", 0),
                    peak=usage.get("peak_live_context_tokens", 0),
                    fraction=usage.get("peak_context_utilization", 0),
                )
            )
        if not generation_ends:
            lines.append("| — | Not recorded by this apparatus version | — | — | — | — |")

        lines += ["", "Primitive actions: " + ", ".join(
            f"`{name}` × {count}" for name, count in sorted(syscall_counts.items())
        ) + "."]
        lines += ["", f"Rejected model actions: {len(rejected_actions)}."]
        if answers:
            lines += ["", "Model answers:"]
            for row in answers:
                lines.append(
                    f"- Generation {row.get('generation')}: `{row.get('answer')}`"
                )

        checks = end.get("checks", {})
        if checks:
            lines += ["", "## Checks", ""]
            for name, passed in checks.items():
                lines.append(f"- {'PASS' if passed else 'FAIL'} — `{name}`")

        lines += [
            "",
            "## Interpretation",
            "",
            interpretation,
            "",
            f"[Machine-readable trajectory](./{self.run_id}.jsonl)",
            "",
        ]
        report_path.write_text("\n".join(lines))
        return report_path


class OllamaClient:
    def __init__(self, settings):
        self.settings = settings

    def request(self, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            self.settings.ollama + path,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=180) as response:
            return json.load(response)

    def environment(self):
        version = self.request("/api/version")
        tags = self.request("/api/tags")
        show = self.request("/api/show", {"model": self.settings.model})
        running = self.request("/api/ps")
        tag = next(
            (item for item in tags.get("models", [])
             if item.get("name") == self.settings.model),
            {},
        )
        loaded = next(
            (item for item in running.get("models", [])
             if item.get("name") == self.settings.model),
            {},
        )
        advertised = next(
            (value for key, value in show.get("model_info", {}).items()
             if key.endswith(".context_length")),
            None,
        )
        return {
            "ollama_version": version.get("version"),
            "model_digest": tag.get("digest"),
            "model_advertised_context": advertised,
            "model_loaded_context": loaded.get("context_length"),
            "model_loaded_vram_bytes": loaded.get("size_vram"),
        }

    def ask(self, history):
        payload = {
            "model": self.settings.model,
            "messages": history,
            "stream": False,
            "format": "json",
            "think": self.settings.think,
            "options": self.settings.ollama_options(),
        }
        started = time.monotonic()
        data = self.request("/api/chat", payload)
        wall_seconds = round(time.monotonic() - started, 6)
        usage = {
            "prompt_tokens": data.get("prompt_eval_count"),
            "completion_tokens": data.get("eval_count"),
            "total_duration_ns": data.get("total_duration"),
            "load_duration_ns": data.get("load_duration"),
            "prompt_eval_duration_ns": data.get("prompt_eval_duration"),
            "eval_duration_ns": data.get("eval_duration"),
            "done": data.get("done"),
            "done_reason": data.get("done_reason"),
            "created_at": data.get("created_at"),
            "wall_seconds": wall_seconds,
        }
        prompt_tokens = usage["prompt_tokens"] or 0
        completion_tokens = usage["completion_tokens"] or 0
        live_context = prompt_tokens + completion_tokens
        usage["context_tokens_after_response"] = live_context
        usage["context_limit"] = self.settings.num_ctx
        usage["context_utilization"] = round(live_context / self.settings.num_ctx, 6)
        return data.get("message", {}), usage


def apparatus_metadata(settings, client):
    commit = git_commit()
    dirty_paths = apparatus_worktree_status()
    image = image_metadata()
    return {
        "schema_version": 1,
        "model": settings.model,
        "inference_options": settings.inference_options(),
        "server_environment": client.environment(),
        "apparatus_commit": commit,
        "worktree_dirty": bool(dirty_paths),
        "dirty_apparatus_paths": dirty_paths,
        **image,
        "apparatus_frozen": not dirty_paths and image["image_revision"] == commit,
    }


def require_frozen_apparatus(metadata):
    if metadata.get("apparatus_frozen"):
        return
    raise RuntimeError(
        "scientific runs require a clean apparatus worktree and an image built "
        "from that exact commit; commit, then run `make build`"
    )


def public_error(error, settings=None):
    """Retain useful failure text without publishing local paths or endpoints."""
    message = str(error).replace(str(ROOT), "[REPOSITORY]")
    if settings is not None:
        message = message.replace(settings.ollama, "[OLLAMA_ENDPOINT]")
    return message


def parse_action(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


class AgentContainer:
    def __init__(self, run_id, generation, work_dir=None):
        self.name = f"hammer-{run_id.lower()}-g{generation}"
        command = ["docker", "compose", "run", "--rm", "-T", "--name", self.name]
        if work_dir is not None:
            command += ["--volume", f"{work_dir}:/work"]
        command.append("agent")
        self.command = command
        self.proc = None
        self.identity = None

    def start(self):
        self.proc = subprocess.Popen(
            self.command, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, bufsize=1,
        )
        for _ in range(50):
            result = subprocess.run(
                ["docker", "inspect", self.name], text=True, capture_output=True,
            )
            if result.returncode == 0:
                info = json.loads(result.stdout)[0]
                self.identity = {
                    "container_id": info["Id"],
                    "network_mode": info["HostConfig"]["NetworkMode"],
                    "read_only_root": info["HostConfig"].get("ReadonlyRootfs"),
                    "init": bool(info["HostConfig"].get("Init")),
                    "mounts": [
                        {
                            "destination": mount.get("Destination"),
                            "rw": mount.get("RW"),
                            "type": mount.get("Type"),
                        }
                        for mount in info.get("Mounts", [])
                    ],
                }
                return self
            if self.proc.poll() is not None:
                raise RuntimeError(f"agent container exited with {self.proc.returncode}")
            time.sleep(0.1)
        raise RuntimeError("timed out while identifying agent container")

    def syscall(self, request):
        self.proc.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()
        response = self.proc.stdout.readline()
        if not response:
            raise RuntimeError("agent closed its output pipe")
        return json.loads(response)

    def stop(self):
        if self.proc is None:
            return None
        if self.proc.stdin:
            self.proc.stdin.close()
        exit_code = self.proc.wait(timeout=20)
        if self.proc.stdout:
            self.proc.stdout.close()
        return exit_code


def run_generation(
    log, client, generation, system_prompt, work_dir=None, max_steps=None,
    compaction_steps=(), require_compactions_before_answer=False,
    on_compaction=None,
):
    step_limit = max_steps or client.settings.max_steps
    container = AgentContainer(log.run_id, generation, work_dir).start()
    log.event(
        "generation_start", generation=generation,
        model_context="fresh", system_prompt=system_prompt,
        container=container.identity, max_steps=step_limit,
    )
    history = [{"role": "system", "content": system_prompt}]
    compaction_steps = tuple(compaction_steps)
    completed_compactions = []
    answer = None
    usages = []

    def compact_if_needed(step):
        if step not in compaction_steps:
            return
        completed_compactions.append(step)
        log.event(
            "context_compaction", generation=generation, step=step,
            retained_state="/work", discarded_state="model_transcript",
            checkpoint_index=len(completed_compactions),
        )
        if on_compaction is not None:
            on_compaction(step, container.identity)
        history[:] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Checkpoint reached: the prior conversation transcript "
                    "is no longer available. /work persists. Continue the task."
                ),
            },
        ]

    try:
        for step in range(1, step_limit + 1):
            message, usage = client.ask(history)
            model_text = message.get("content", "")
            usages.append(usage)
            log.event(
                "model_response", generation=generation, step=step,
                message=message, usage=usage,
            )
            print(f"[g{generation}:{step}] model: {model_text}")
            try:
                action = parse_action(model_text)
                if not isinstance(action, dict):
                    raise ValueError("top-level response must be a JSON object")
                if action.get("action") not in ("syscall", "answer"):
                    raise ValueError(
                        "action must be 'syscall' or 'answer'; syscall names belong in 'op'"
                    )
            except (json.JSONDecodeError, ValueError) as error:
                rejection = {
                    "ok": False,
                    "phase": "model_action_validation",
                    "syscall": None,
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
                log.event(
                    "model_action_rejected", generation=generation, step=step,
                    rejection=rejection,
                )
                history += [
                    {"role": "assistant", "content": model_text},
                    {
                        "role": "user",
                        "content": (
                            "action rejected; no syscall ran: "
                            + json.dumps(rejection, separators=(",", ":"))
                            + ". Return one valid object using the declared action grammar."
                        ),
                    },
                ]
                compact_if_needed(step)
                continue
            if action.get("action") == "answer":
                if require_compactions_before_answer and (
                    len(completed_compactions) != len(compaction_steps)
                ):
                    rejection = {
                        "ok": False,
                        "phase": "task_timing",
                        "syscall": None,
                        "error_type": "ValueError",
                        "error": "answer is not allowed before all declared context checkpoints",
                    }
                    log.event(
                        "model_action_rejected", generation=generation, step=step,
                        rejection=rejection,
                    )
                    history += [
                        {"role": "assistant", "content": model_text},
                        {
                            "role": "user",
                            "content": (
                                "action rejected; no syscall ran: "
                                + json.dumps(rejection, separators=(",", ":"))
                                + ". Continue the declared task."
                            ),
                        },
                    ]
                    compact_if_needed(step)
                    continue
                answer = action.get("answer")
                log.event(
                    "generation_answer", generation=generation,
                    step=step, answer=answer,
                )
                break
            request = {key: value for key, value in action.items() if key != "action"}
            log.event(
                "syscall_request", generation=generation,
                step=step, request=request,
            )
            result = container.syscall(request)
            log.event(
                "syscall_result", generation=generation,
                step=step, result=result,
            )
            print(f"[g{generation}:{step}] agent: {json.dumps(result, separators=(',', ':'))}")
            history += [
                {"role": "assistant", "content": model_text},
                {"role": "user", "content": "syscall result: " + json.dumps(result)},
            ]
            if usage["context_utilization"] >= 0.9:
                log.event(
                    "context_pressure", generation=generation, step=step,
                    threshold=0.9, usage=usage,
                )
            compact_if_needed(step)
        if answer is None:
            log.event(
                "generation_exhausted", generation=generation,
                max_steps=step_limit,
            )
    except Exception as error:
        log.event(
            "generation_error", generation=generation,
            public_fields={
                "generation": generation,
                "error_type": type(error).__name__,
                "error": public_error(error, client.settings),
            },
            error_type=type(error).__name__, error=str(error),
        )
        raise
    finally:
        exit_code = container.stop()
        prompt_total = sum(item["prompt_tokens"] or 0 for item in usages)
        completion_total = sum(item["completion_tokens"] or 0 for item in usages)
        peak_context = max(
            (item["context_tokens_after_response"] for item in usages),
            default=0,
        )
        log.event(
            "generation_end", generation=generation,
            container_id=container.identity["container_id"], exit_code=exit_code,
            usage_summary={
                "model_calls": len(usages),
                "cumulative_prompt_tokens": prompt_total,
                "cumulative_completion_tokens": completion_total,
                "cumulative_processed_tokens": prompt_total + completion_total,
                "peak_live_context_tokens": peak_context,
                "context_limit": client.settings.num_ctx,
                "peak_context_utilization": round(
                    peak_context / client.settings.num_ctx, 6
                ),
            },
        )
    return answer, container.identity
