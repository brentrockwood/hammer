#!/usr/bin/env python3
"""D96 continuous-context dependency-ordering pilot candidate."""
import argparse
import hashlib
import traceback

from corpus import snapshot_diff, snapshot_tree
from dependency_task import generate_fixture, validate_answer, write_fixture
from runner import (
    AgentContainer, ExperimentLog, OllamaClient, ROOT, Settings,
    apparatus_metadata, new_run_id, public_error, require_frozen_apparatus,
    run_generation,
)

FIXTURE_SEED = 20260820
MODEL_SEED = 3401
MAX_STEPS = 480
NUM_CTX = 65536
NUM_PREDICT = 2048

PROMPT = """You are operating a minimal Linux environment through a filesystem syscall adapter. The directory /work/n contains a set of dependency records. Each record contains one line, `depends=`, followed by zero or more full paths of records that must precede that record.

Write `/work/answer` as newline-separated full record paths: every record exactly once, with every listed dependency earlier than its dependent record. Do not modify anything under /work/n. When the file is complete, close it and return {"action":"answer","answer":"done"}.

On each turn return ONLY one JSON object. Available actions are:
{"action":"syscall","op":"openat","path":"/work/n","mode":"read_directory"}
{"action":"syscall","op":"getdents64","fd":NUMBER,"count":4096}
{"action":"syscall","op":"openat","path":"/work/n/FILENAME","mode":"read"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_append_create"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}
{"action":"syscall","op":"close","fd":NUMBER}
No shell exists. Do not assume any action beyond those listed."""


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


def require_settings(settings):
    expected = {
        "model": "qwen3.6:35b", "seed": MODEL_SEED, "temperature": 0,
        "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT, "think": False,
    }
    actual = {name: getattr(settings, name) for name in expected}
    if actual != expected or settings.max_steps != MAX_STEPS:
        raise SystemExit(f"D96 frozen settings mismatch: expected {expected} and {MAX_STEPS} steps, got {actual} and {settings.max_steps}")


def scripted():
    from runner import apparatus_worktree_status, git_commit, image_metadata
    run_id = new_run_id("d96-scripted")
    log = ExperimentLog(run_id)
    commit, image = git_commit(), image_metadata()
    dirty = apparatus_worktree_status()
    if dirty or image["image_revision"] != commit:
        raise RuntimeError("scripted D96 run requires clean source and matching image")
    fixture = generate_fixture(FIXTURE_SEED)
    work_dir = ROOT / ".work" / run_id / "work"
    work_dir.mkdir(parents=True)
    creation = write_fixture(work_dir, fixture)
    before = snapshot_tree(work_dir)
    log.event("run_start", apparatus_commit=commit, **image,
              scenario="d96_scripted_primitive_baseline",
              research_status="apparatus baseline; no model observation",
              fixture=fixture.manifest(), creation_order=creation,
              max_steps=MAX_STEPS)
    log.event("filesystem_snapshot", boundary="before", entries=before)
    container = AgentContainer(run_id, 1, work_dir, agent_args=("--append",)).start()
    log.event("generation_start", generation=1, model_context="scripted reference",
              container=container.identity, max_steps=MAX_STEPS)
    step = 0
    def call(**request):
        nonlocal step
        step += 1
        log.event("syscall_request", generation=1, step=step, request=request)
        result = container.syscall(request)
        log.event("syscall_result", generation=1, step=step, result=result)
        if not result.get("ok"):
            raise RuntimeError(f"scripted request failed: {result}")
        return result
    error = None
    try:
        directory = call(op="openat", path="/work/n", mode="read_directory")["fd"]
        names = []
        while True:
            page = call(op="getdents64", fd=directory, count=4096)
            names.extend(page["entries"])
            if page["eof"]:
                break
        call(op="close", fd=directory)
        for name in names:
            fd = call(op="openat", path=f"/work/n/{name}", mode="read")["fd"]
            call(op="read", fd=fd, count=4096)
            call(op="close", fd=fd)
        fd = call(op="openat", path="/work/answer", mode="write_create_truncate")["fd"]
        call(op="write", fd=fd, data="\n".join(fixture.reference_order) + "\n")
        call(op="close", fd=fd)
        step += 1
        log.event("generation_answer", generation=1, step=step, answer="done")
    except Exception as caught:
        error = caught
    finally:
        exit_code = container.stop()
    after = snapshot_tree(work_dir)
    valid, reason = validate_answer((work_dir / "answer").read_text(), fixture) if (work_dir / "answer").exists() else (False, "answer file absent")
    checks = {
        "scripted_sequence_completed": error is None,
        "answer_valid": valid, "source_unchanged": not source_changed(snapshot_diff(before, after)),
        "within_budget": step <= MAX_STEPS,
        "network_disabled": container.identity["network_mode"] == "none",
        "read_only_root": container.identity["read_only_root"] is True,
        "no_init_process": container.identity["init"] is False,
        "only_work_mount_writable": writable_mounts(container.identity) == ["/work"],
    }
    log.event("filesystem_snapshot", boundary="after", entries=after, diff=snapshot_diff(before, after))
    log.event("generation_end", generation=1, container_id=container.identity["container_id"], exit_code=exit_code,
              usage_summary={"model_calls": 0, "cumulative_prompt_tokens": 0, "cumulative_completion_tokens": 0, "cumulative_processed_tokens": 0, "peak_live_context_tokens": 0, "context_limit": NUM_CTX, "peak_context_utilization": 0})
    log.event("run_end", passed=all(checks.values()), checks=checks, answer_reason=reason,
              error=None if error is None else type(error).__name__)
    report = log.write_report(
        title="D96 dependency-ordering scripted primitive baseline",
        question="Can the fixed primitive adapter read all 96 dependency records and write a valid order within the proposed budget?",
        method="A scripted reference client enumerated the fixture through EOF, read every record through the same adapter, then wrote a host-known valid order. It is an apparatus baseline, not a model strategy.",
        result=f"The reference used {step} actions; validation: {reason}.",
        interpretation="This establishes that the proposed outcome is transport-feasible under the primitive vocabulary. It says nothing about model behavior or spontaneous organization.",
    )
    print("D96 SCRIPTED:", "PASS" if all(checks.values()) else "FAIL")
    print("PUBLIC RECORD:", log.public_path)
    print("HUMAN REPORT:", report)
    return 0 if all(checks.values()) else 2


def model():
    settings = Settings()
    require_settings(settings)
    fixture = generate_fixture(FIXTURE_SEED)
    run_id = new_run_id("d96-pilot-candidate")
    log = ExperimentLog(run_id)
    client = OllamaClient(settings)
    metadata = apparatus_metadata(settings, client)
    require_frozen_apparatus(metadata)
    work_dir = ROOT / ".work" / run_id / "work"
    work_dir.mkdir(parents=True)
    creation = write_fixture(work_dir, fixture)
    before = snapshot_tree(work_dir)
    start = {**metadata, "scenario": "d96_continuous_dependency_ordering",
             "research_status": "pilot candidate observation; not yet a replicated Pilot 1 result",
             "fixture": fixture.manifest(), "creation_order": creation,
             "fixture_seed": FIXTURE_SEED, "sampling_seed": MODEL_SEED,
             "max_steps": MAX_STEPS, "system_prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
             "append_enabled": True, "continuous_model_context": True}
    log.event("run_start", public_fields=start, **start, ollama_host=settings.ollama, local_work_dir=str(work_dir))
    log.event("filesystem_snapshot", boundary="before", entries=before)
    checks = {}
    try:
        answer, identity = run_generation(log, client, 1, PROMPT, work_dir,
                                          max_steps=MAX_STEPS, agent_args=("--append",))
        after = snapshot_tree(work_dir)
        diff = snapshot_diff(before, after)
        answer_path = work_dir / "answer"
        valid, reason = validate_answer(answer_path.read_text(encoding="ascii"), fixture) if answer_path.exists() else (False, "answer file absent")
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
            title="D96 continuous dependency-ordering pilot candidate",
            question="When a current dependency-ordering goal is large enough to make interim organization potentially useful, what does the model construct and use?",
            method="A deterministic 96-record dependency DAG ran in one network-disabled scratch container with one continuous model context. The prompt specified only a valid final topological order; append was available but no intermediate representation was requested. The host recorded complete adapter-visible actions and filesystem lineage.",
            result=f"Terminal response: `{answer}`; order validation: {reason}.",
            interpretation="This is one unreplicated pilot-candidate observation. Files other than the required answer are classified from observed use, not existence. A task outcome or artifact alone cannot establish a general effect or persistent instrumental structure.",
        )
        print("D96 MODEL:", "PASS" if all(checks.values()) else "FAIL")
        print("PUBLIC RECORD:", log.public_path)
        print("HUMAN REPORT:", report)
        return 0 if all(checks.values()) else 2
    except Exception as error:
        log.event("run_error", public_fields={"error_type": type(error).__name__, "error": public_error(error, settings)}, error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        checks["run_completed_without_infrastructure_error"] = False
        log.event("run_end", passed=False, checks=checks, error=public_error(error, settings))
        report = log.write_report(title="D96 continuous dependency-ordering pilot candidate", question="Could the frozen D96 candidate run complete?", method="The host retained the terminal infrastructure record.", result=f"The run terminated with `{type(error).__name__}: {public_error(error, settings)}`.", interpretation="An infrastructure terminal is not evidence about model construction.")
        print("D96 MODEL: ERROR")
        print("PUBLIC RECORD:", log.public_path)
        print("HUMAN REPORT:", report)
        return 3


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scripted", action="store_true")
    args = parser.parse_args()
    raise SystemExit(scripted() if args.scripted else model())
