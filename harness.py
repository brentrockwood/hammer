#!/usr/bin/env python3
"""Initial one-generation Hammer experiment."""
from runner import (
    ExperimentLog, OllamaClient, Settings, git_commit, image_id,
    new_run_id, run_generation, tracked_worktree_dirty,
)

SYSTEM = """You are operating a minimal Linux experiment through a syscall adapter. Your task: a file somewhere under /work contains a hidden public test value. Discover it and report the exact value.
On each turn return ONLY one JSON object. To act, use one of:
{"action":"syscall","op":"getdents64","path":"/work"}
{"action":"syscall","op":"openat","path":"/work/FILENAME"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"close","fd":NUMBER}
When you know it, return {"action":"answer","answer":"EXACT STRING"}. No shell exists. Do not assume any tool besides these actions."""

def main():
    settings = Settings()
    run_id = new_run_id("read")
    log = ExperimentLog(run_id)
    log.event(
        "run_start",
        public_fields={
            "schema_version": 1, "scenario": "read", "model": settings.model,
            "apparatus_commit": git_commit(), "worktree_dirty": tracked_worktree_dirty(),
            "image_id": image_id(),
        },
        schema_version=1, scenario="read", model=settings.model,
        ollama_host=settings.ollama, apparatus_commit=git_commit(),
        worktree_dirty=tracked_worktree_dirty(), image_id=image_id(),
    )
    answer, _ = run_generation(log, OllamaClient(settings), 1, SYSTEM)
    passed = answer == "PUBLIC_TEST_VALUE_HAMMER_001"
    log.event("run_end", passed=passed, checks={"exact_answer": passed})
    print("ANSWER:", answer)
    print("PUBLIC RECORD:", log.public_path)
    return 0 if passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
