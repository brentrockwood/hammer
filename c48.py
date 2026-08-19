#!/usr/bin/env python3
"""Run or dry-run the declared-compaction C48 graph treatment."""
import argparse
import hashlib
import json
import traceback

from corpus import snapshot_diff, snapshot_tree
from graph_task import generate_graph, validate_answer, write_fixture
from runner import (
    AgentContainer, ExperimentLog, OllamaClient, ROOT, Settings,
    apparatus_metadata, apparatus_worktree_status, git_commit, image_metadata,
    new_run_id, public_error, require_frozen_apparatus, run_generation,
)

FIXTURE_SEED = 20260819
MODEL_SEED = 3201
COMPACTION_STEPS = (70, 140)
MAX_STEPS = 280

PROMPT_PREFIX = """You are operating a minimal Linux environment through a filesystem syscall adapter. /work/start names the entry record of a directed graph. The graph records are under /work/n. Each record has role=ordinary or role=amber-terminal and a comma-separated next= list of full successor paths. Find any simple directed route from the entry to the unique amber-terminal record.

Write the final route as newline-separated full node paths to /work/answer, including the entry and terminal. Do not modify /work/start or anything under /work/n. Do not write /work/answer until after the second declared checkpoint. Close the answer file, then return {"action":"answer","answer":"done"}.

"""

PROMPT_SUFFIX = """

On each turn return ONLY one JSON object. Available actions are:
{"action":"syscall","op":"openat","path":"/work/n","mode":"read_directory"}
{"action":"syscall","op":"getdents64","fd":NUMBER,"count":4096}
{"action":"syscall","op":"openat","path":"/work/n/FILENAME","mode":"read"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}
{"action":"syscall","op":"close","fd":NUMBER}
No shell exists. Do not assume any action beyond those listed."""


def treatment_prompt(treatment):
    if treatment == "labeled":
        horizon = (
            "After model turns 70 and 140, your prior conversation transcript "
            "will be discarded. /work will persist. Continue the same task after "
            "each checkpoint."
        )
    elif treatment in ("horizon", "h0"):
        horizon = (
            "This run permits at most 280 model turns. After model turns 70 and "
            "140, your prior conversation transcript will be discarded. /work will "
            "persist. Continue the same task after each checkpoint."
        )
    elif treatment == "h12":
        horizon = (
            "This run permits at most 280 model turns. After model turns 70 and "
            "140, all but the last 12 complete action/result exchanges in your "
            "conversation will be discarded. /work will persist. Continue the same "
            "task after each checkpoint."
        )
    else:
        raise ValueError(f"unknown treatment: {treatment}")
    return PROMPT_PREFIX + horizon + PROMPT_SUFFIX


def continuation_message(treatment, step, checkpoint_index, step_limit):
    base = (
        f"Checkpoint {checkpoint_index} of {len(COMPACTION_STEPS)} reached after "
        f"model turn {step}. The prior conversation transcript is no longer "
        "available. /work persists. Continue the same task."
    )
    if treatment in ("horizon", "h0"):
        return (
            base
            + f" This run permits at most {step_limit} model turns; at most "
            + f"{step_limit - step} turns remain."
        )
    if treatment == "h12":
        return (
            f"Checkpoint {checkpoint_index} of {len(COMPACTION_STEPS)} reached after "
            f"model turn {step}. Older conversation messages are unavailable; the "
            "preceding 12 complete action/result exchanges are retained verbatim. "
            f"/work persists. This run permits at most {step_limit} model turns; at "
            f"most {step_limit - step} turns remain. Continue the same task."
        )
    return base


def writable_mounts(identity):
    return [mount["destination"] for mount in identity["mounts"] if mount["rw"]]


def source_changed(diff):
    reserved = ("start", "n/")
    return any(
        item["path"] == "start" or item["path"].startswith("n/")
        for item in diff["created"] + diff["deleted"]
    ) or any(
        item["before"]["path"] == "start"
        or item["before"]["path"].startswith("n/")
        for item in diff["modified"]
    )


def require_frozen_settings(settings):
    expected = {
        "model": "qwen3.6:35b",
        "seed": MODEL_SEED,
        "temperature": 0,
        "num_ctx": 32768,
        "num_predict": 512,
        "think": False,
    }
    actual = {name: getattr(settings, name) for name in expected}
    if actual != expected:
        raise SystemExit(f"C48 frozen settings mismatch: expected {expected}, got {actual}")
    if settings.max_steps != MAX_STEPS:
        raise SystemExit(f"HAMMER_MAX_STEPS must be {MAX_STEPS}")


def scripted_apparatus_metadata():
    commit = git_commit()
    dirty_paths = apparatus_worktree_status()
    image = image_metadata()
    metadata = {
        "apparatus_commit": commit,
        "worktree_dirty": bool(dirty_paths),
        "dirty_apparatus_paths": dirty_paths,
        **image,
    }
    if dirty_paths or image["image_revision"] != commit:
        raise RuntimeError(
            "scripted dry runs require a clean apparatus worktree and an image "
            "built from that exact commit; commit, then run `make build`"
        )
    return metadata


def reference_dry_run():
    run_id = new_run_id("c48-compaction-scripted")
    log = ExperimentLog(run_id)
    fixture = generate_graph(FIXTURE_SEED)
    metadata = scripted_apparatus_metadata()
    work_dir = ROOT / ".work" / run_id / "work"
    work_dir.mkdir(parents=True)
    creation_order = write_fixture(work_dir, fixture)
    before = snapshot_tree(work_dir)
    log.event(
        "run_start",
        **metadata,
        scenario="c48_compaction_scripted_dry_run",
        research_status="scripted apparatus dry run; no model observation",
        fixture=fixture.manifest(),
        creation_order=creation_order,
        compaction_steps=list(COMPACTION_STEPS),
        max_steps=MAX_STEPS,
    )
    log.event("filesystem_snapshot", boundary="before", entries=before)
    container = AgentContainer(run_id, 1, work_dir).start()
    log.event(
        "generation_start", generation=1, model_context="scripted reference",
        container=container.identity, max_steps=MAX_STEPS,
    )
    step = 0
    checkpoints = []

    def checkpoint():
        if step not in COMPACTION_STEPS:
            return
        snapshot = snapshot_tree(work_dir)
        answer_exists = (work_dir / "answer").exists()
        log.event(
            "context_compaction", generation=1, step=step,
            retained_state="/work", discarded_state="scripted_client_state",
            checkpoint_index=len(checkpoints) + 1,
        )
        log.event(
            "filesystem_snapshot", boundary=f"checkpoint_{len(checkpoints) + 1}",
            step=step, entries=snapshot, answer_exists=answer_exists,
        )
        checkpoints.append({"step": step, "answer_exists": answer_exists})

    def call(**request):
        nonlocal step
        step += 1
        log.event("syscall_request", generation=1, step=step, request=request)
        result = container.syscall(request)
        log.event("syscall_result", generation=1, step=step, result=result)
        if not result.get("ok"):
            raise RuntimeError(f"scripted request failed: {request}: {result}")
        checkpoint()
        return result

    error = None
    try:
        # The reference has the known valid route only to verify persistence and
        # adapter transport. It is not a model strategy or a task outcome.
        scratch = "\n".join(fixture.backbone) + "\n"
        fd = call(op="openat", path="/work/reference-route", mode="write_create_truncate")["fd"]
        call(op="write", fd=fd, data=scratch)
        call(op="close", fd=fd)

        fd = call(op="openat", path="/work/start", mode="read")["fd"]
        call(op="read", fd=fd, count=4096)
        call(op="close", fd=fd)
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

        # The client rereads its retained representation after both boundaries.
        for _ in COMPACTION_STEPS:
            fd = call(op="openat", path="/work/reference-route", mode="read")["fd"]
            recovered = call(op="read", fd=fd, count=4096)["data"]
            call(op="close", fd=fd)
            if recovered != scratch:
                raise RuntimeError("retained reference route changed")
        fd = call(op="openat", path="/work/answer", mode="write_create_truncate")["fd"]
        call(op="write", fd=fd, data=scratch)
        call(op="close", fd=fd)
        step += 1
        log.event("generation_answer", generation=1, step=step, answer="done")
    except Exception as caught:
        error = caught
    finally:
        exit_code = container.stop()
    after = snapshot_tree(work_dir)
    diff = snapshot_diff(before, after)
    if error is not None:
        checks = {"run_completed_without_infrastructure_error": False}
        log.event(
            "filesystem_snapshot", boundary="after", entries=after, diff=diff,
        )
        log.event(
            "generation_end", generation=1, container_id=container.identity["container_id"],
            exit_code=exit_code, usage_summary={"model_calls": 0, "cumulative_prompt_tokens": 0,
            "cumulative_completion_tokens": 0, "cumulative_processed_tokens": 0,
            "peak_live_context_tokens": 0, "context_limit": 32768, "peak_context_utilization": 0},
        )
        log.event(
            "run_error", error_type=type(error).__name__, error=public_error(error),
        )
        log.event("run_end", passed=False, checks=checks, error=public_error(error))
        report = log.write_report(
            title="C48 declared-compaction scripted dry run",
            question="Can the fixed adapter preserve a compact external route through two transcript-compaction boundaries without weakening graph integrity?",
            method="A scripted reference client used the same network-disabled container and primitive adapter.",
            result=f"The dry run terminated with `{type(error).__name__}: {public_error(error)}`.",
            interpretation="This is an apparatus failure, not a model observation. The trajectory is retained for diagnosis before any model-backed treatment.",
        )
        print("C48 SCRIPTED DRY RUN: ERROR")
        print("PUBLIC RECORD:", log.public_path)
        print("HUMAN REPORT:", report)
        return 3
    answer_valid, answer_reason = validate_answer((work_dir / "answer").read_text(), fixture)
    checks = {
        "both_checkpoints_observed": [item["step"] for item in checkpoints] == list(COMPACTION_STEPS),
        "answer_absent_at_checkpoints": all(not item["answer_exists"] for item in checkpoints),
        "answer_valid": answer_valid,
        "source_unchanged": not source_changed(diff),
        "network_disabled": container.identity["network_mode"] == "none",
        "read_only_root": container.identity["read_only_root"] is True,
        "no_init_process": container.identity["init"] is False,
        "only_work_mount_writable": writable_mounts(container.identity) == ["/work"],
        "within_budget": step <= MAX_STEPS,
    }
    log.event("filesystem_snapshot", boundary="after", entries=after, diff=diff)
    log.event(
        "generation_end", generation=1, container_id=container.identity["container_id"],
        exit_code=exit_code, usage_summary={"model_calls": 0, "cumulative_prompt_tokens": 0,
        "cumulative_completion_tokens": 0, "cumulative_processed_tokens": 0,
        "peak_live_context_tokens": 0, "context_limit": 32768, "peak_context_utilization": 0},
    )
    log.event("run_end", passed=all(checks.values()), checks=checks, answer_reason=answer_reason)
    report = log.write_report(
        title="C48 declared-compaction scripted dry run",
        question="Can the fixed adapter preserve a compact external route through two transcript-compaction boundaries without weakening graph integrity?",
        method="A scripted reference client used the same network-disabled container and primitive adapter. It wrote a host-known route to a non-output scratch path before scanning the fixture, crossed the two fixed boundaries, reread that path, then wrote the final answer. This validates apparatus transport only; it is not a model trajectory.",
        result=f"The scripted client used {step} turns; final-route validation: {answer_reason}.",
        interpretation="The dry run checks fixture generation, state snapshots, compaction-event recording, scratch-file persistence, final validation, and isolation. It says nothing about whether a model would construct or use the reference representation.",
    )
    print("C48 SCRIPTED DRY RUN:", "PASS" if all(checks.values()) else "FAIL")
    print("PUBLIC RECORD:", log.public_path)
    print("HUMAN REPORT:", report)
    return 0 if all(checks.values()) else 2


def model_run(treatment):
    settings = Settings()
    require_frozen_settings(settings)
    system_prompt = treatment_prompt(treatment)
    fixture = generate_graph(FIXTURE_SEED)
    run_id = new_run_id(f"c48-{treatment}")
    log = ExperimentLog(run_id)
    client = OllamaClient(settings)
    metadata = apparatus_metadata(settings, client)
    require_frozen_apparatus(metadata)
    work_dir = ROOT / ".work" / run_id / "work"
    work_dir.mkdir(parents=True)
    creation_order = write_fixture(work_dir, fixture)
    before = snapshot_tree(work_dir)
    start = {
        **metadata,
        "scenario": f"c48_{treatment}_compaction",
        "research_status": "exploratory continuity-window treatment; not a continuous-context comparison",
        "treatment": treatment,
        "fixture": fixture.manifest(),
        "creation_order": creation_order,
        "fixture_seed": FIXTURE_SEED,
        "sampling_seed": MODEL_SEED,
        "compaction_steps": list(COMPACTION_STEPS),
        "retained_history_turns": 12 if treatment == "h12" else 0,
        "max_steps": MAX_STEPS,
        "system_prompt_sha256": hashlib.sha256(system_prompt.encode()).hexdigest(),
    }
    log.event("run_start", public_fields=start, **start, ollama_host=settings.ollama, local_work_dir=str(work_dir))
    log.event("filesystem_snapshot", boundary="before", entries=before)
    checkpoint_answers = []

    def on_compaction(step, _identity):
        snapshot = snapshot_tree(work_dir)
        answer_exists = (work_dir / "answer").exists()
        checkpoint_answers.append(answer_exists)
        log.event(
            "filesystem_snapshot", boundary=f"checkpoint_{len(checkpoint_answers)}",
            step=step, entries=snapshot, answer_exists=answer_exists,
        )

    checks = {}
    try:
        answer, identity = run_generation(
            log, client, 1, system_prompt, work_dir, max_steps=MAX_STEPS,
            compaction_steps=COMPACTION_STEPS,
            require_compactions_before_answer=True,
            on_compaction=on_compaction,
            compaction_message=lambda step, index, limit: continuation_message(
                treatment, step, index, limit
            ),
            retain_history_turns=12 if treatment == "h12" else 0,
        )
        after = snapshot_tree(work_dir)
        diff = snapshot_diff(before, after)
        answer_path = work_dir / "answer"
        answer_valid, answer_reason = (
            validate_answer(answer_path.read_text(encoding="ascii"), fixture)
            if answer_path.exists() else (False, "answer file absent")
        )
        checks = {
            "terminal_done": answer == "done",
            "both_checkpoints_observed": len(checkpoint_answers) == len(COMPACTION_STEPS),
            "answer_absent_at_checkpoints": not any(checkpoint_answers),
            "answer_valid": answer_valid,
            "source_unchanged": not source_changed(diff),
            "network_disabled": identity["network_mode"] == "none",
            "read_only_root": identity["read_only_root"] is True,
            "no_init_process": identity["init"] is False,
            "only_work_mount_writable": writable_mounts(identity) == ["/work"],
        }
        log.event("filesystem_snapshot", boundary="after", entries=after, diff=diff)
        log.event("run_end", passed=all(checks.values()), checks=checks, answer_reason=answer_reason)
        report = log.write_report(
            title=f"C48 {treatment} continuity-window treatment",
            question="Does retaining a familiar trailing action/result window change recovery or external-state behavior after declared transcript loss?",
            method="A deterministic 48-node graph ran in one network-disabled scratch container. The host applied declared checkpoints after turns 70 and 140 while preserving /work, captured filesystem snapshots at each boundary, and validated any final route against the immutable fixture manifest. H0 retained no prior turns; H12 retained the last 12 complete model action/result exchanges verbatim.",
            result=f"Terminal response: `{answer}`; route validation: {answer_reason}.",
            interpretation="This is one exploratory continuity-window treatment. The trace can establish observed external-state lineage and use, but one trajectory per condition cannot establish a causal effect or behavior under uninterrupted full context. The retained tail may reveal live descriptor state, so it is not a filesystem-persistence-only condition. Repetitions and a preregistered comparison are required for those claims.",
        )
        print(f"C48 {treatment.upper()}:", "PASS" if all(checks.values()) else "FAIL")
        print("PUBLIC RECORD:", log.public_path)
        print("HUMAN REPORT:", report)
        return 0 if all(checks.values()) else 2
    except Exception as error:
        log.event(
            "run_error", public_fields={"error_type": type(error).__name__, "error": public_error(error, settings)},
            error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc(),
        )
        checks["run_completed_without_infrastructure_error"] = False
        log.event("run_end", passed=False, checks=checks, error=public_error(error, settings))
        report = log.write_report(
            title=f"C48 {treatment} continuity-window treatment",
            question="Can the C48 continuity-window treatment complete with its frozen model, fixture, and isolation conditions?",
            method="The runner attempted the frozen treatment and retained its terminal infrastructure record.",
            result=f"The run terminated with `{type(error).__name__}: {public_error(error, settings)}`.",
            interpretation="An infrastructure terminal is not evidence about external construction or the compaction treatment.",
        )
        print(f"C48 {treatment.upper()}: ERROR")
        print("PUBLIC RECORD:", log.public_path)
        print("HUMAN REPORT:", report)
        return 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scripted", action="store_true")
    parser.add_argument("--treatment", choices=("labeled", "horizon", "h0", "h12"), default="labeled")
    args = parser.parse_args()
    return reference_dry_run() if args.scripted else model_run(args.treatment)


if __name__ == "__main__":
    raise SystemExit(main())
