#!/usr/bin/env python3
"""Matched blind-terminal wording study for the D96 dependency fixture."""
import argparse
import hashlib
import json
import traceback
from collections import Counter

from corpus import snapshot_diff, snapshot_tree
from dependency_task import generate_fixture, validate_answer, write_fixture
from runner import (
    AgentContainer, ExperimentLog, OllamaClient, ROOT, Settings,
    apparatus_metadata, new_run_id, public_error, require_frozen_apparatus,
    require_matching_loaded_context, run_generation,
)

FIXTURE_SEED = 20260820
MAX_STEPS = 480
NUM_CTX = 32768
NUM_PREDICT = 2048
ARM_SEEDS = {
    "original": (3402, 3403, 3404),
    "explicit-finality": (3411, 3412, 3413),
}

PROMPT_PREFIX = """You are operating a minimal Linux environment through a filesystem syscall adapter. The directory /work/n contains a set of dependency records. Each record contains one line, `depends=`, followed by zero or more full paths of records that must precede that record.

Write `/work/answer` as newline-separated full record paths: every record exactly once, with every listed dependency earlier than its dependent record. Do not modify anything under /work/n. When the file is complete, close it and return {\"action\":\"answer\",\"answer\":\"done\"}."""

EXPLICIT_FINALITY = """ Submitting {\"action\":\"answer\",\"answer\":\"done\"} ends this run. No further actions or feedback will be available."""

PROMPT_SUFFIX = """

On each turn return ONLY one JSON object. Available actions are:
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/n\",\"mode\":\"read_directory\"}
{\"action\":\"syscall\",\"op\":\"getdents64\",\"fd\":NUMBER,\"count\":4096}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/n/FILENAME\",\"mode\":\"read\"}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"write_create_truncate\"}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"write_append_create\"}
{\"action\":\"syscall\",\"op\":\"read\",\"fd\":NUMBER,\"count\":NUMBER}
{\"action\":\"syscall\",\"op\":\"write\",\"fd\":NUMBER,\"data\":\"ASCII STRING\"}
{\"action\":\"syscall\",\"op\":\"close\",\"fd\":NUMBER}
No shell exists. Do not assume any action beyond those listed."""


def prompt_for(arm):
    return PROMPT_PREFIX + (EXPLICIT_FINALITY if arm == "explicit-finality" else "") + PROMPT_SUFFIX


def writable_mounts(identity):
    return [mount["destination"] for mount in identity["mounts"] if mount["rw"]]


def source_changed(diff):
    return any(
        item["path"] == "n" or item["path"].startswith("n/")
        for item in diff["created"] + diff["deleted"]
    ) or any(
        item["before"]["path"] == "n" or item["before"]["path"].startswith("n/")
        for item in diff["modified"]
    )


def require_settings(settings, arm):
    expected = {
        "model": "qwen3.6:35b", "temperature": 0,
        "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT, "think": False,
    }
    actual = {name: getattr(settings, name) for name in expected}
    if actual != expected or settings.max_steps != MAX_STEPS or settings.seed not in ARM_SEEDS[arm]:
        raise SystemExit(
            f"D96 terminal-study frozen settings mismatch for {arm}: "
            f"expected {expected}, one of {ARM_SEEDS[arm]}, and {MAX_STEPS} steps; "
            f"got {actual}, seed {settings.seed}, and {settings.max_steps} steps"
        )


def answer_diagnostics(text, fixture):
    lines = [line for line in text.splitlines() if line]
    nodes = fixture.node_by_path()
    counts = Counter(lines)
    positions = {line: index for index, line in enumerate(lines) if line in nodes}
    order_violations = sum(
        1 for node in fixture.nodes if node.path in positions
        for dependency in node.dependencies
        if dependency in positions and positions[dependency] >= positions[node.path]
    )
    return {
        "nonempty_line_count": len(lines),
        "unique_line_count": len(set(lines)),
        "unknown_path_count": sum(line not in nodes for line in lines),
        "missing_fixture_node_count": len(set(nodes) - set(lines)),
        "duplicate_path_count": sum(count - 1 for count in counts.values() if count > 1),
        "known_dependency_order_violation_count": order_violations,
    }


def trajectory_observations(log):
    rows = [json.loads(line) for line in log.public_path.read_text().splitlines()]
    requests = [row["request"] for row in rows if row["event"] == "syscall_request"]
    directory_results = [
        row["result"] for row in rows
        if row["event"] == "syscall_result" and row["result"].get("op") == "getdents64"
    ]
    read_paths = {
        request["path"] for request in requests
        if request.get("op") == "openat" and request.get("mode") == "read"
    }
    model_calls = sum(1 for row in rows if row["event"] == "model_response")
    return {
        "directory_call_count": len(directory_results),
        "directory_eof_observed": any(result.get("ok") and result.get("eof") for result in directory_results),
        "distinct_records_opened_read": len(read_paths),
        "model_calls": model_calls,
        "remaining_model_turns_at_terminal": MAX_STEPS - model_calls,
    }


def write_forensic_section(report, diagnostics, observations):
    report.open("a").write(
        "\n## Forensic reading\n\n"
        f"The model made {observations['directory_call_count']} directory call(s), "
        f"observed directory EOF: `{observations['directory_eof_observed']}`, and opened "
        f"{observations['distinct_records_opened_read']} distinct fixture records for reading. "
        f"It used {observations['model_calls']} model calls and had "
        f"{observations['remaining_model_turns_at_terminal']} turns remaining at terminal submission.\n\n"
        f"The answer diagnostics were {json.dumps(diagnostics, sort_keys=True)}. "
        "These diagnostics supplement the ordinary short-circuit validator; they do not "
        "change the terminal score or provide model-visible feedback.\n"
    )


def model(arm):
    settings = Settings()
    require_settings(settings, arm)
    fixture = generate_fixture(FIXTURE_SEED)
    run_id = new_run_id(f"d96-terminal-{arm}")
    log = ExperimentLog(run_id)
    client = OllamaClient(settings)
    metadata = apparatus_metadata(settings, client)
    require_frozen_apparatus(metadata)
    require_matching_loaded_context(metadata)
    system_prompt = prompt_for(arm)
    work_dir = ROOT / ".work" / run_id / "work"
    work_dir.mkdir(parents=True)
    creation = write_fixture(work_dir, fixture)
    before = snapshot_tree(work_dir)
    start = {
        **metadata, "scenario": "d96_blind_terminal_wording",
        "research_status": "terminal-semantics calibration; not Pilot 1 evidence",
        "study_arm": arm, "terminal_policy": "blind_terminal",
        "fixture": fixture.manifest(), "creation_order": creation,
        "fixture_seed": FIXTURE_SEED, "sampling_seed": settings.seed,
        "max_steps": MAX_STEPS,
        "system_prompt_sha256": hashlib.sha256(system_prompt.encode()).hexdigest(),
        "explicit_finality_sentence": EXPLICIT_FINALITY.strip() if arm == "explicit-finality" else None,
        "append_enabled": True, "continuous_model_context": True,
    }
    log.event("run_start", public_fields=start, **start, ollama_host=settings.ollama, local_work_dir=str(work_dir))
    log.event("filesystem_snapshot", boundary="before", entries=before)
    checks = {}
    try:
        answer, identity = run_generation(log, client, 1, system_prompt, work_dir,
                                          max_steps=MAX_STEPS, agent_args=("--append",))
        after = snapshot_tree(work_dir)
        diff = snapshot_diff(before, after)
        answer_path = work_dir / "answer"
        text = answer_path.read_text(encoding="ascii") if answer_path.exists() else ""
        valid, reason = validate_answer(text, fixture) if answer_path.exists() else (False, "answer file absent")
        diagnostics = answer_diagnostics(text, fixture)
        log.event("answer_diagnostics", diagnostics=diagnostics)
        observations = trajectory_observations(log)
        log.event("trajectory_observations", observations=observations)
        checks = {
            "terminal_done": answer == "done", "answer_valid": valid,
            "source_unchanged": not source_changed(diff),
            "network_disabled": identity["network_mode"] == "none",
            "read_only_root": identity["read_only_root"] is True,
            "no_init_process": identity["init"] is False,
            "only_work_mount_writable": writable_mounts(identity) == ["/work"],
        }
        log.event("filesystem_snapshot", boundary="after", entries=after, diff=diff)
        log.event("run_end", passed=all(checks.values()), checks=checks, answer_reason=reason)
        report = log.write_report(
            title=f"D96 blind-terminal wording study — {arm}",
            question="Does explicitly stating that a blind terminal submission is irreversible change the D96 action trajectory or outcome?",
            method="One deterministic 96-record dependency fixture ran in one continuous context with no correctness feedback. This arm used the predeclared prompt wording, model, budget, and sampling seed.",
            result=f"Terminal response: `{answer}`; order validation: {reason}.",
            interpretation="This is one member of a matched terminal-semantics calibration. It does not establish a causal effect, a general model property, or useful external organization on its own.",
        )
        write_forensic_section(report, diagnostics, observations)
        print("D96 TERMINAL:", "PASS" if all(checks.values()) else "FAIL")
        print("PUBLIC RECORD:", log.public_path)
        print("HUMAN REPORT:", report)
        return 0 if all(checks.values()) else 2
    except Exception as error:
        log.event("run_error", public_fields={"error_type": type(error).__name__, "error": public_error(error, settings)}, error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        checks["run_completed_without_infrastructure_error"] = False
        log.event("run_end", passed=False, checks=checks, error=public_error(error, settings))
        report = log.write_report(title=f"D96 blind-terminal wording study — {arm}", question="Could this frozen terminal-semantics member run?", method="The host retained the terminal infrastructure record.", result=f"The run terminated with `{type(error).__name__}: {public_error(error, settings)}`.", interpretation="An infrastructure terminal is not evidence about model construction or terminal semantics.")
        print("D96 TERMINAL: ERROR")
        print("PUBLIC RECORD:", log.public_path)
        print("HUMAN REPORT:", report)
        return 3


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARM_SEEDS), required=True)
    args = parser.parse_args()
    raise SystemExit(model(args.arm))
