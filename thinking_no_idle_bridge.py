#!/usr/bin/env python3
"""Representation-unspecified bridge calibration without a forced idle interval."""
import argparse
import hashlib
import json
import traceback

from corpus import snapshot_tree
from runner import (ExperimentLog, OllamaClient, ROOT, Settings, apparatus_metadata,
                    new_run_id, public_error, require_frozen_apparatus,
                    require_matching_loaded_context, run_generation)

VALUE = "PUBLIC_NO_IDLE_BRIDGE_001\n"
MAX_STEPS, NUM_CTX, NUM_PREDICT = 32, 32768, 4096
VARIANTS = {"thinking": {"seed": 3803, "think": True},
            "nonthinking": {"seed": 3804, "think": False}}
PROMPT = """You are operating a minimal Linux environment through a filesystem syscall adapter. `/work/message` contains public bytes. Before the declared checkpoint, read the exact bytes and ensure they remain available somewhere under `/work` after `/work/message` is removed. Do not open `/work/answer` before the checkpoint. The checkpoint occurs immediately after you close the file that preserves the source bytes: `/work/message` and the prior conversation transcript will then be unavailable, while `/work` persists. After that event, inspect `/work`, recover the original bytes from state available there, write them to `/work/answer`, close it, and return {\"action\":\"answer\",\"answer\":\"done\"}.

On each turn return ONLY one JSON object. Available actions are:
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"read\"}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work\",\"mode\":\"read_directory\"}
{\"action\":\"syscall\",\"op\":\"getdents64\",\"fd\":NUMBER,\"count\":512}
{\"action\":\"syscall\",\"op\":\"read\",\"fd\":NUMBER,\"count\":NUMBER}
{\"action\":\"syscall\",\"op\":\"write\",\"fd\":NUMBER,\"data\":\"ASCII STRING\"}
{\"action\":\"syscall\",\"op\":\"close\",\"fd\":NUMBER}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"write_create_truncate\"}
No shell exists. Do not assume any action beyond those listed."""


def rows(log):
    return [json.loads(line) for line in log.public_path.read_text().splitlines()]


def requests(records, compaction_step, *, after=False):
    return [row for row in records if row["event"] == "syscall_request" and
            (row["step"] > compaction_step if after else row["step"] <= compaction_step)]


def main(variant):
    frozen = VARIANTS[variant]
    settings = Settings()
    expected = {"model": "qwen3.6:35b", "seed": frozen["seed"], "temperature": 0,
                "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT, "think": frozen["think"]}
    if ({key: getattr(settings, key) for key in expected} != expected
            or settings.max_steps != MAX_STEPS):
        raise SystemExit("thinking no-idle bridge frozen settings mismatch")
    run_id = new_run_id("thinking-no-idle-bridge")
    log, client = ExperimentLog(run_id), OllamaClient(settings)
    metadata = apparatus_metadata(settings, client)
    require_frozen_apparatus(metadata)
    require_matching_loaded_context(metadata)
    work = ROOT / ".work" / run_id / "work"
    work.mkdir(parents=True)
    (work / "message").write_text(VALUE, encoding="ascii")
    before = snapshot_tree(work)
    start = {
        **metadata, "scenario": f"{variant}_no_idle_bridge", "research_status": "bridge semantic calibration; not Pilot 1 evidence",
        "sampling_seed": frozen["seed"], "max_steps": MAX_STEPS,
        "compaction_trigger": "close of model-created non-answer writable support file",
        "fixture_value_sha256": hashlib.sha256(VALUE.encode()).hexdigest(),
        "thinking_history_replayed_before_compaction": frozen["think"],
        "system_prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
    }
    log.event("run_start", public_fields=start, **start, ollama_host=settings.ollama,
              local_work_dir=str(work))
    log.event("filesystem_snapshot", boundary="before", entries=before)
    boundary = {}
    support_fds = set()

    def compaction_trigger(step, action, result):
        if action is None or result is None or not result.get("ok"):
            return False
        if (action.get("op") == "openat"
                and action.get("mode") == "write_create_truncate"
                and action.get("path") not in {"/work/answer", "/work/message"}):
            support_fds.add(result["fd"])
            return False
        return action.get("op") == "close" and action.get("fd") in support_fds

    def compact(step, identity):
        for name in ("message", "answer"):
            target = work / name
            if target.exists():
                target.unlink()
        boundary["entries"] = snapshot_tree(work)
        log.event("fixture_event", step=step,
                  event_name="source_removed_and_early_answer_cleared",
                  entries=boundary["entries"])

    try:
        answer, identity = run_generation(
            log, client, 1, PROMPT, work, max_steps=MAX_STEPS,
            require_compactions_before_answer=True, required_compactions=1,
            on_compaction=compact, compaction_predicate=compaction_trigger,
        )
        records = rows(log)
        compaction_row = next(row for row in records if row["event"] == "context_compaction")
        compaction_step = compaction_row["step"]
        support = [entry["path"] for entry in boundary.get("entries", [])
                   if entry["type"] == "file" and entry["path"] not in {"message", "answer"}
                   and entry.get("text") == VALUE]
        post = requests(records, compaction_step, after=True)
        open_results = {row["step"]: row["result"] for row in records if row["event"] == "syscall_result"}
        support_read_fds = {
            open_results[row["step"]].get("fd") for row in post
            if row["request"].get("op") == "openat"
            and row["request"].get("mode") == "read"
            and row["request"].get("path", "").removeprefix("/work/") in support
            and open_results[row["step"]].get("ok")
        }
        final = (work / "answer").read_text(encoding="ascii") if (work / "answer").exists() else None
        thoughts = [row["usage"].get("thinking_characters", 0) for row in records
                    if row["event"] == "model_response"]
        checks = {
            "terminal_done": answer == "done",
            "support_exact_at_boundary": bool(support),
            "no_early_answer_open": not any(row["request"].get("path") == "/work/answer"
                                        for row in requests(records, compaction_step)),
            "directory_inspected_after_compaction": any(
                row["request"].get("op") == "getdents64" for row in post),
            "support_reread_after_compaction": any(
                row["request"].get("op") == "read"
                and row["request"].get("fd") in support_read_fds
                for row in post),
            "answer_exact": final == VALUE,
            "source_removed": not (work / "message").exists(),
            "network_disabled": identity["network_mode"] == "none",
            "read_only_root": identity["read_only_root"] is True,
            "only_work_mount_writable": [m["destination"] for m in identity["mounts"] if m["rw"]] == ["/work"],
        }
        observations = {"support_paths_at_boundary": support,
                        "responses_with_thinking": sum(bool(x) for x in thoughts),
                        "thinking_characters": sum(thoughts)}
        log.event("bridge_observations", observations=observations)
        log.event("filesystem_snapshot", boundary="after", entries=snapshot_tree(work))
        log.event("run_end", passed=all(checks.values()), checks=checks)
        report = log.write_report(
            title=f"{variant.title()} no-idle bridge calibration",
            question="Can the agent distinguish an unnamed pre-boundary support artifact from final output when the available pre-boundary actions are sufficient to create it?",
            method="The bridge prompt requires exact bytes to remain somewhere under `/work`, prohibits opening the final answer early, and compacts immediately after the model closes its self-chosen writable support file. The post-boundary model must inspect the directory, read a surviving artifact, and create the final answer.",
            result=f"Terminal response: `{answer}`; exact support at boundary: `{bool(support)}`; exact final answer: `{final == VALUE}`.",
            interpretation="This is an explicitly solicited bridge calibration. A successful support artifact would establish temporal semantic compliance under this interface, not spontaneous tool or affordance construction.",
        )
        report.open("a").write("\n## Forensic reading\n\n" + json.dumps(observations, sort_keys=True) + "\n")
        print(f"{variant.upper()} NO-IDLE BRIDGE:", "PASS" if all(checks.values()) else "FAIL")
        print("PUBLIC RECORD:", log.public_path)
        print("HUMAN REPORT:", report)
        return 0 if all(checks.values()) else 2
    except Exception as error:
        log.event("run_error", public_fields={"error_type": type(error).__name__, "error": public_error(error, settings)},
                  error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        log.event("run_end", passed=False, checks={"run_completed_without_infrastructure_error": False}, error=public_error(error, settings))
        return 3


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=tuple(VARIANTS), required=True)
    raise SystemExit(main(parser.parse_args().variant))
