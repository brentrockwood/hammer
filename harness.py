#!/usr/bin/env python3
"""Host-only Hammer harness: model API stays outside the experimental namespace."""
import json, os, re, subprocess, sys, time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MAX_STEPS = int(os.environ.get("HAMMER_MAX_STEPS", "8"))
LOG = ROOT / "logs" / f"run-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"

SYSTEM = """You are operating a minimal Linux experiment through a syscall adapter. Your task: a file somewhere under /work contains a hidden public test value. Discover it and report the exact value.
On each turn return ONLY one JSON object. To act, use one of:
{"action":"syscall","op":"getdents64","path":"/work"}
{"action":"syscall","op":"openat","path":"/work/FILENAME"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"close","fd":NUMBER}
When you know it, return {"action":"answer","answer":"EXACT STRING"}. No shell exists. Do not assume any tool besides these actions."""

def event(kind, **data):
    row = {"ts": time.time(), "event": kind, **data}
    with LOG.open("a") as f: f.write(json.dumps(row) + "\n")

def ask(history):
    payload = {"model": MODEL, "messages": history, "stream": False, "format": "json", "options": {"temperature": 0}}
    req = Request(OLLAMA + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=180) as response: data = json.load(response)
    return data["message"]["content"]

def action_from(text):
    try: return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match: raise
        return json.loads(match.group(0))

def main():
    LOG.parent.mkdir(exist_ok=True)
    event("run_start", model=MODEL, ollama_host=OLLAMA, task="read hidden public test value from /work")
    cmd = ["docker", "compose", "run", "--rm", "-T", "agent"]
    proc = subprocess.Popen(cmd, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    history = [{"role": "system", "content": SYSTEM}]
    try:
        for step in range(1, MAX_STEPS + 1):
            model_text = ask(history)
            event("model_response", step=step, content=model_text)
            print(f"[{step}] model: {model_text}")
            action = action_from(model_text)
            if action.get("action") == "answer":
                event("final_answer", step=step, answer=action.get("answer"))
                print("ANSWER:", action.get("answer")); return 0
            if action.get("action") != "syscall":
                raise ValueError("model returned neither syscall nor answer")
            wire = {k: v for k, v in action.items() if k != "action"}
            event("syscall_request", step=step, request=wire)
            proc.stdin.write(json.dumps(wire) + "\n"); proc.stdin.flush()
            result = proc.stdout.readline().rstrip("\n")
            event("syscall_result", step=step, result=result)
            print(f"[{step}] agent: {result}")
            history += [{"role": "assistant", "content": model_text}, {"role": "user", "content": "syscall result: " + result}]
        event("run_exhausted", max_steps=MAX_STEPS)
        print("No answer within step limit.", file=sys.stderr); return 2
    finally:
        if proc.stdin: proc.stdin.close()
        proc.wait(timeout=20)

if __name__ == "__main__":
    raise SystemExit(main())
