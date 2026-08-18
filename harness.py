#!/usr/bin/env python3
"""Initial one-generation Hammer experiment."""
from runner import (
    ExperimentLog, OllamaClient, Settings, apparatus_metadata,
    new_run_id, run_generation,
)

SYSTEM = """You are operating a minimal Linux experiment through a syscall adapter. Your task: a file somewhere under /work contains a hidden public test value. Discover it and report the exact value.
On each turn return ONLY one JSON object. To act, use one of:
{"action":"syscall","op":"openat","path":"/work","mode":"read_directory"}
{"action":"syscall","op":"getdents64","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"read"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"close","fd":NUMBER}
When you know it, return an answer object with these fields:
action: answer
answer: [the exact value read from the file]
The bracketed phrase is a placeholder. Replace it with the value and do not include the brackets. No shell exists. Do not assume any tool besides these actions."""

def main():
    settings = Settings()
    run_id = new_run_id("read")
    log = ExperimentLog(run_id)
    client = OllamaClient(settings)
    metadata = {**apparatus_metadata(settings, client), "scenario": "read"}
    log.event(
        "run_start",
        public_fields=metadata,
        **metadata, ollama_host=settings.ollama,
    )
    answer, _ = run_generation(log, client, 1, SYSTEM)
    passed = answer == "PUBLIC_TEST_VALUE_HAMMER_001"
    log.event("run_end", passed=passed, checks={"exact_answer": passed})
    report = log.write_report(
        title="Initial syscall retrieval spike",
        question="Could the model recover a value from a sparse Linux environment using only the syscall adapter?",
        method="We placed one deliberately public fixture in `/work`, started a network-disabled scratch container, and gave the model a fresh context describing only the available primitive actions.",
        result=f"The model reported `{answer}` after enumerating `/work` and reading the fixture.",
        interpretation="This was apparatus validation. It established that the action loop was usable; it did not test spontaneous construction or reuse of persistent structure.",
    )
    print("ANSWER:", answer)
    print("PUBLIC RECORD:", log.public_path)
    print("HUMAN REPORT:", report)
    return 0 if passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
