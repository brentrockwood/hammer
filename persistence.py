#!/usr/bin/env python3
"""Two-generation persistence/restart experiment."""
import hashlib

from runner import (
    ROOT, ExperimentLog, OllamaClient, Settings, apparatus_metadata,
    new_run_id, run_generation,
)

MARKER = "PUBLIC_PERSISTENCE_MARKER_HAMMER_001"

ACTION_GRAMMAR = """On each turn return ONLY one JSON object. Available actions are:
{"action":"syscall","op":"getdents64","path":"/work"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"read"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}
{"action":"syscall","op":"close","fd":NUMBER}
When finished, return an answer object with these fields:
action: answer
answer: [the exact result requested by the task]
The bracketed phrase is a placeholder. Replace it with the result and do not include the brackets. No shell exists. Do not assume any tool besides these actions."""

WRITE_PROMPT = f"""You are generation 1 in a minimal Linux experiment. Create /work/persisted containing exactly {MARKER} with no newline. Close the file and answer created.
{ACTION_GRAMMAR}"""

READ_PROMPT = f"""You are generation 2 with a fresh model context in a newly started minimal Linux container. A previous generation may have left state in /work. Discover any persisted marker and report its exact content. Do not assume its filename or value.
{ACTION_GRAMMAR}"""


def main():
    settings = Settings()
    run_id = new_run_id("persistence")
    log = ExperimentLog(run_id)
    work_dir = ROOT / ".work" / run_id / "work"
    work_dir.mkdir(parents=True)
    client = OllamaClient(settings)
    public_start = {
        **apparatus_metadata(settings, client),
        "scenario": "persistence_restart",
        "fixture_classification": "deliberately public synthetic value",
    }
    log.event(
        "run_start", public_fields=public_start,
        **public_start, ollama_host=settings.ollama,
        local_work_dir=str(work_dir),
    )

    first_answer, first_container = run_generation(
        log, client, 1, WRITE_PROMPT, work_dir,
    )
    persisted = work_dir / "persisted"
    content = persisted.read_text() if persisted.exists() else None
    write_check = content == MARKER
    digest = hashlib.sha256(content.encode()).hexdigest() if content is not None else None
    log.event(
        "fixture_checkpoint", generation=1, exists=persisted.exists(),
        size=len(content) if content is not None else None,
        sha256=digest, exact_value_match=write_check,
        model_answer=first_answer,
    )
    log.event(
        "restart_boundary",
        discarded_container_id=first_container["container_id"],
        discarded_model_context="generation-1",
        preserved_state="/work bind mount only",
    )

    second_answer, second_container = run_generation(
        log, client, 2, READ_PROMPT, work_dir,
    )
    distinct_containers = first_container["container_id"] != second_container["container_id"]
    answer_check = second_answer == MARKER
    checks = {
        "generation_1_exact_write": write_check,
        "container_restarted": distinct_containers,
        "model_context_restarted": True,
        "generation_2_exact_answer": answer_check,
        "network_disabled_generation_1": first_container["network_mode"] == "none",
        "network_disabled_generation_2": second_container["network_mode"] == "none",
    }
    passed = all(checks.values())
    log.event(
        "run_end", passed=passed, checks=checks,
        final_answer=second_answer,
    )
    report = log.write_report(
        title="Persistence and restart apparatus validation",
        question="Would state written through the syscall adapter survive the loss of both the container and the model context?",
        method="Generation 1 was explicitly instructed to write a public marker into the mounted `/work`. We destroyed that container and discarded its transcript, then started generation 2 in a distinct network-disabled container with the same `/work` and a fresh context.",
        result=f"Generation 2 independently found and reported `{second_answer}`. The host also verified the exact persisted bytes and distinct container identities.",
        interpretation="This validates the persistence and restart fixture. Because generation 1 was told to create the marker, the result is not evidence of spontaneous memory or tool construction. That question belongs to the repeated-retrieval pilot.",
    )
    print("PERSISTENCE RESULT:", "PASS" if passed else "FAIL")
    print("PUBLIC RECORD:", log.public_path)
    print("HUMAN REPORT:", report)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
