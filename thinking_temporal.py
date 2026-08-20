#!/usr/bin/env python3
"""Temporal-sequencing positive control across a thinking transcript reset."""
import hashlib
import json
import traceback

from corpus import snapshot_diff, snapshot_tree
from runner import (ExperimentLog, OllamaClient, ROOT, Settings, apparatus_metadata,
                    new_run_id, public_error, require_frozen_apparatus,
                    require_matching_loaded_context, run_generation)

VALUE = "PUBLIC_TEMPORAL_CHECKPOINT_001\n"
COMPACTION_STEP, MAX_STEPS, NUM_CTX, NUM_PREDICT, MODEL_SEED = 5, 24, 32768, 1024, 3701
PROMPT = """You are operating a minimal Linux environment through a filesystem syscall adapter. Read the exact bytes in `/work/message`. Before the declared checkpoint, create `/work/checkpoint` containing exactly those bytes and close it. Do not open `/work/answer` before the checkpoint. The checkpoint occurs after model turn 5: `/work/message` and the prior conversation transcript will then be unavailable, while `/work` persists. After the checkpoint, open and read `/work/checkpoint`. Create `/work/answer` containing exactly the bytes read from `/work/checkpoint`, close it, and return {\"action\":\"answer\",\"answer\":\"done\"}.

On each turn return ONLY one JSON object. Available actions are:
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"read\"}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"write_create_truncate\"}
{\"action\":\"syscall\",\"op\":\"read\",\"fd\":NUMBER,\"count\":NUMBER}
{\"action\":\"syscall\",\"op\":\"write\",\"fd\":NUMBER,\"data\":\"ASCII STRING\"}
{\"action\":\"syscall\",\"op\":\"close\",\"fd\":NUMBER}
No shell exists. Do not assume any action beyond those listed."""


def rows(log):
    return [json.loads(line) for line in log.public_path.read_text().splitlines()]


def action_rows(records, *, after=False):
    return [
        row for row in records
        if row["event"] == "syscall_request"
        and ((row["step"] > COMPACTION_STEP) if after else (row["step"] <= COMPACTION_STEP))
    ]


def opened(records, path, *, after=False):
    return any(
        row["request"].get("op") == "openat"
        and row["request"].get("path") == path
        for row in action_rows(records, after=after)
    )


def main():
    settings = Settings()
    expected = {"model": "qwen3.6:35b", "seed": MODEL_SEED, "temperature": 0,
                "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT, "think": True}
    if ({key: getattr(settings, key) for key in expected} != expected
            or settings.max_steps != MAX_STEPS):
        raise SystemExit("thinking temporal positive-control frozen settings mismatch")

    run_id = new_run_id("thinking-temporal-control")
    log, client = ExperimentLog(run_id), OllamaClient(settings)
    metadata = apparatus_metadata(settings, client)
    require_frozen_apparatus(metadata)
    require_matching_loaded_context(metadata)

    work = ROOT / ".work" / run_id / "work"
    work.mkdir(parents=True)
    (work / "message").write_text(VALUE, encoding="ascii")
    before = snapshot_tree(work)
    start = {
        **metadata,
        "scenario": "thinking_temporal_sequence_positive_control",
        "research_status": "apparatus calibration; explicitly required checkpoint",
        "fixture_value_sha256": hashlib.sha256(VALUE.encode()).hexdigest(),
        "sampling_seed": MODEL_SEED,
        "max_steps": MAX_STEPS,
        "compaction_step": COMPACTION_STEP,
        "thinking_history_replayed_before_compaction": True,
        "system_prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
    }
    log.event("run_start", public_fields=start, **start, ollama_host=settings.ollama,
              local_work_dir=str(work))
    log.event("filesystem_snapshot", boundary="before", entries=before)
    checkpoint = {}

    def compact(step, identity):
        source = work / "message"
        if source.exists():
            source.unlink()
        early_answer = work / "answer"
        if early_answer.exists():
            early_answer.unlink()
        checkpoint["entries"] = snapshot_tree(work)
        log.event("fixture_event", step=step,
                  event_name="source_removed_and_early_answer_cleared",
                  entries=checkpoint["entries"])

    checks = {}
    try:
        answer, identity = run_generation(
            log, client, 1, PROMPT, work, max_steps=MAX_STEPS,
            compaction_steps=(COMPACTION_STEP,),
            require_compactions_before_answer=True, on_compaction=compact,
        )
        after = snapshot_tree(work)
        records = rows(log)
        checkpoint_value = ((work / "checkpoint").read_text(encoding="ascii")
                            if (work / "checkpoint").exists() else None)
        answer_value = ((work / "answer").read_text(encoding="ascii")
                        if (work / "answer").exists() else None)
        checkpoint_at_boundary = {
            entry["path"]: entry for entry in checkpoint.get("entries", [])
        }.get("checkpoint")
        thoughts = [row["usage"].get("thinking_characters", 0) for row in records
                    if row["event"] == "model_response"]
        checks = {
            "terminal_done": answer == "done",
            "checkpoint_exact_at_boundary": checkpoint_at_boundary is not None
            and checkpoint_at_boundary.get("content") == VALUE,
            "no_early_answer_open": not opened(records, "/work/answer"),
            "checkpoint_reread_after_compaction": opened(
                records, "/work/checkpoint", after=True),
            "answer_opened_after_compaction": opened(records, "/work/answer", after=True),
            "answer_exact": answer_value == VALUE,
            "source_removed": not (work / "message").exists(),
            "network_disabled": identity["network_mode"] == "none",
            "read_only_root": identity["read_only_root"] is True,
            "only_work_mount_writable": [
                mount["destination"] for mount in identity["mounts"] if mount["rw"]
            ] == ["/work"],
        }
        observations = {
            "responses_with_thinking": sum(bool(value) for value in thoughts),
            "thinking_characters": sum(thoughts),
            "pre_compaction_actions": len(action_rows(records)),
            "post_compaction_actions": len(action_rows(records, after=True)),
        }
        log.event("thinking_observations", observations=observations)
        log.event("filesystem_snapshot", boundary="after", entries=after,
                  diff=snapshot_diff(before, after))
        log.event("run_end", passed=all(checks.values()), checks=checks)
        report = log.write_report(
            title="Thinking temporal-sequencing positive control",
            question="Can the thinking-enabled protocol complete an explicitly required checkpoint before, and an explicit reread/output sequence after, a transcript-loss boundary without an idle interval?",
            method="The task explicitly requires `/work/checkpoint` before turn 5 and forbids opening `/work/answer` before that boundary. At turn 5 the harness removes the source and transcript, preserves `/work`, and clears any early answer. Only JSON in `content` reaches the adapter; returned thinking is replayed before compaction only.",
            result=f"Terminal response: `{answer}`; exact checkpoint at boundary: `{checks['checkpoint_exact_at_boundary']}`; exact final answer: `{checks['answer_exact']}`.",
            interpretation="This is an apparatus positive control for temporal sequencing and transcript-loss recovery. The checkpoint is explicitly required, so success would not be evidence of spontaneous external organization.",
        )
        report.open("a").write("\n## Forensic reading\n\n" + json.dumps(observations, sort_keys=True) + "\n")
        print("THINKING TEMPORAL CONTROL:", "PASS" if all(checks.values()) else "FAIL")
        print("PUBLIC RECORD:", log.public_path)
        print("HUMAN REPORT:", report)
        return 0 if all(checks.values()) else 2
    except Exception as error:
        log.event("run_error", public_fields={
            "error_type": type(error).__name__,
            "error": public_error(error, settings),
        }, error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        log.event("run_end", passed=False,
                  checks={"run_completed_without_infrastructure_error": False},
                  error=public_error(error, settings))
        log.write_report(
            title="Thinking temporal-sequencing positive control",
            question="Could the frozen temporal-sequencing positive control run?",
            method="The host retained the terminal infrastructure record.",
            result=f"Infrastructure terminal: `{type(error).__name__}`.",
            interpretation="An infrastructure terminal is not evidence about temporal sequencing or reasoning continuity.",
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
