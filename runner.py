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


@dataclass(frozen=True)
class Settings:
    model: str = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    ollama: str = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    max_steps: int = int(os.environ.get("HAMMER_MAX_STEPS", "10"))


def new_run_id(scenario):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{scenario}-{stamp}"


def git_commit():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def tracked_worktree_dirty():
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    return bool(result.stdout.strip())


def image_id():
    result = subprocess.run(
        ["docker", "image", "inspect", "hammer-agent", "--format", "{{.Id}}"],
        cwd=ROOT, text=True, capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


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


class OllamaClient:
    def __init__(self, settings):
        self.settings = settings

    def ask(self, history):
        payload = {
            "model": self.settings.model,
            "messages": history,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        }
        request = Request(
            self.settings.ollama + "/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        started = time.monotonic()
        with urlopen(request, timeout=180) as response:
            data = json.load(response)
        return data["message"]["content"], round(time.monotonic() - started, 6)


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
        return self.proc.wait(timeout=20)


def run_generation(log, client, generation, system_prompt, work_dir=None):
    container = AgentContainer(log.run_id, generation, work_dir).start()
    log.event(
        "generation_start", generation=generation,
        model_context="fresh", system_prompt=system_prompt,
        container=container.identity,
    )
    history = [{"role": "system", "content": system_prompt}]
    answer = None
    try:
        for step in range(1, client.settings.max_steps + 1):
            model_text, latency = client.ask(history)
            log.event(
                "model_response", generation=generation, step=step,
                latency_seconds=latency, content=model_text,
            )
            print(f"[g{generation}:{step}] model: {model_text}")
            action = parse_action(model_text)
            if action.get("action") == "answer":
                answer = action.get("answer")
                log.event(
                    "generation_answer", generation=generation,
                    step=step, answer=answer,
                )
                break
            if action.get("action") != "syscall":
                raise ValueError("model returned neither syscall nor answer")
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
        if answer is None:
            log.event(
                "generation_exhausted", generation=generation,
                max_steps=client.settings.max_steps,
            )
    finally:
        exit_code = container.stop()
        log.event(
            "generation_end", generation=generation,
            container_id=container.identity["container_id"], exit_code=exit_code,
        )
    return answer, container.identity
