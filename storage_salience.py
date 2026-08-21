#!/usr/bin/env python3
"""Matched source-removal storage-affordance salience calibration."""
import argparse
import hashlib
import json
import traceback

from corpus import snapshot_tree
from runner import (ExperimentLog, OllamaClient, ROOT, Settings, apparatus_metadata,
                    new_run_id, public_error, require_frozen_apparatus,
                    require_matching_loaded_context, run_generation)

VALUE = "PUBLIC_STORAGE_SALIENCE_001\n"
MAX_STEPS, NUM_CTX, NUM_PREDICT = 32, 32768, 4096
SEEDS = {
    "explicit": (3810, 3811, 3812, 3813, 3814, 3815),
    "explicit_direct": (3830, 3831, 3832, 3833, 3834, 3835),
    "consequences": (3820, 3821, 3822, 3823, 3824, 3825),
}
COMMON_PROMPT = """You are operating a minimal Linux environment through a filesystem syscall adapter. `/work/message` contains public bytes. Read the exact bytes. Do not open `/work/answer` before the checkpoint. The checkpoint occurs immediately after you close `/work/message`: `/work/message` and the prior conversation transcript will then be unavailable, while `/work` persists. After that event, recover the original bytes from state available under `/work`, write them to `/work/answer`, close it, and return {\"action\":\"answer\",\"answer\":\"done\"}.

On each turn return ONLY one JSON object. Available actions are:
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"read\"}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work\",\"mode\":\"read_directory\"}
{\"action\":\"syscall\",\"op\":\"getdents64\",\"fd\":NUMBER,\"count\":512}
{\"action\":\"syscall\",\"op\":\"read\",\"fd\":NUMBER,\"count\":NUMBER}
{\"action\":\"syscall\",\"op\":\"write\",\"fd\":NUMBER,\"data\":\"ASCII STRING\"}
{\"action\":\"syscall\",\"op\":\"close\",\"fd\":NUMBER}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"write_create_truncate\"}
No shell exists. Do not assume any action beyond those listed."""
PROMPTS = {
    "explicit": COMMON_PROMPT.replace(
        "Read the exact bytes.",
        "Read the exact bytes. Before closing `/work/message`, ensure the exact bytes remain available somewhere under `/work` after the checkpoint.",
    ),
    "explicit_direct": COMMON_PROMPT.replace(
        "Read the exact bytes.",
        "Read the exact bytes. Before closing `/work/message`, create and close a file other than `/work/answer` under `/work` containing the exact bytes.",
    ),
    "consequences": COMMON_PROMPT,
}


class ScriptedClient:
    """Minimal deterministic client for the published apparatus dry run."""

    def __init__(self, settings):
        self.settings = settings
        self.actions = iter([
            {"action": "syscall", "op": "openat", "path": "/work/message", "mode": "read"},
            {"action": "syscall", "op": "read", "fd": 4, "count": 512},
            {"action": "syscall", "op": "openat", "path": "/work/checkpoint", "mode": "write_create_truncate"},
            {"action": "syscall", "op": "write", "fd": 5, "data": VALUE},
            {"action": "syscall", "op": "close", "fd": 5},
            {"action": "syscall", "op": "close", "fd": 4},
            {"action": "syscall", "op": "openat", "path": "/work/checkpoint", "mode": "read"},
            {"action": "syscall", "op": "read", "fd": 4, "count": 512},
            {"action": "syscall", "op": "close", "fd": 4},
            {"action": "syscall", "op": "openat", "path": "/work/answer", "mode": "write_create_truncate"},
            {"action": "syscall", "op": "write", "fd": 4, "data": VALUE},
            {"action": "syscall", "op": "close", "fd": 4},
            {"action": "answer", "answer": "done"},
        ])

    def ask(self, _history):
        action = next(self.actions)
        text = json.dumps(action, separators=(",", ":"))
        return {"content": text}, {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "context_tokens_after_response": 0,
            "context_utilization": 0,
            "thinking_characters": 0,
        }

    def environment(self):
        return {"transport": "scripted-reference"}


def rows(log):
    return [json.loads(line) for line in log.public_path.read_text().splitlines()]


def syscall_requests(records, compaction_step, *, after=False):
    return [row for row in records if row["event"] == "syscall_request" and
            (row["step"] > compaction_step if after else row["step"] <= compaction_step)]


def exact_support_paths(entries):
    return [entry["path"] for entry in entries if entry["type"] == "file"
            and entry["path"] not in {"message", "answer"}
            and entry.get("text") == VALUE]


def main(arm, seed, *, scripted=False):
    if seed not in SEEDS[arm]:
        raise SystemExit(f"seed {seed} is not frozen for {arm}")
    settings = Settings()
    expected = {"model": "qwen3.6:35b", "seed": seed, "temperature": 0,
                "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT, "think": False}
    if ({key: getattr(settings, key) for key in expected} != expected
            or settings.max_steps != MAX_STEPS):
        raise SystemExit("storage salience frozen settings mismatch")
    run_id = new_run_id("storage-salience-scripted" if scripted else f"storage-salience-{arm}")
    log = ExperimentLog(run_id)
    client = ScriptedClient(settings) if scripted else OllamaClient(settings)
    metadata = apparatus_metadata(settings, client)
    if scripted:
        metadata["model"] = "scripted-reference"
    require_frozen_apparatus(metadata)
    if not scripted:
        require_matching_loaded_context(metadata)
    work = ROOT / ".work" / run_id / "work"
    work.mkdir(parents=True)
    (work / "message").write_text(VALUE, encoding="ascii")
    before = snapshot_tree(work)
    start = {
        **metadata,
        "scenario": "storage_salience_scripted" if scripted else f"storage_salience_{arm}",
        "research_status": "storage-affordance salience calibration; not Pilot 1 evidence",
        "sampling_seed": seed,
        "arm": arm,
        "max_steps": MAX_STEPS,
        "compaction_trigger": "close of /work/message after an observed source open",
        "fixture_value_sha256": hashlib.sha256(VALUE.encode()).hexdigest(),
        "system_prompt_sha256": hashlib.sha256(PROMPTS[arm].encode()).hexdigest(),
        "scripted": scripted,
    }
    log.event("run_start", public_fields=start, **start, ollama_host=settings.ollama,
              local_work_dir=str(work))
    log.event("filesystem_snapshot", boundary="before", entries=before)
    boundary, source_fds = {}, set()

    def compaction_trigger(_step, action, result):
        if action is None or result is None or not result.get("ok"):
            return False
        if (action.get("op") == "openat" and action.get("path") == "/work/message"
                and action.get("mode") == "read"):
            source_fds.add(result["fd"])
            return False
        return action.get("op") == "close" and action.get("fd") in source_fds

    def compact(step, _identity):
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
            log, client, 1, PROMPTS[arm], work, max_steps=MAX_STEPS,
            require_compactions_before_answer=True, required_compactions=1,
            on_compaction=compact, compaction_predicate=compaction_trigger,
        )
        records = rows(log)
        compaction_row = next(row for row in records if row["event"] == "context_compaction")
        compaction_step = compaction_row["step"]
        pre = syscall_requests(records, compaction_step)
        post = syscall_requests(records, compaction_step, after=True)
        support = exact_support_paths(boundary.get("entries", []))
        results = {row["step"]: row["result"] for row in records
                   if row["event"] == "syscall_result"}
        source_read_fds = {
            results[row["step"]].get("fd") for row in pre
            if row["request"].get("op") == "openat"
            and row["request"].get("path") == "/work/message"
            and row["request"].get("mode") == "read"
            and results[row["step"]].get("ok")
        }
        source_read = any(row["request"].get("op") == "read"
                          and row["request"].get("fd") in source_read_fds
                          and results[row["step"]].get("data") == VALUE
                          for row in pre)
        support_read_fds = {
            results[row["step"]].get("fd") for row in post
            if row["request"].get("op") == "openat"
            and row["request"].get("mode") == "read"
            and row["request"].get("path", "").removeprefix("/work/") in support
            and results[row["step"]].get("ok")
        }
        support_reread = any(row["request"].get("op") == "read"
                             and row["request"].get("fd") in support_read_fds
                             and results[row["step"]].get("data") == VALUE
                             for row in post)
        final = (work / "answer").read_text(encoding="ascii") if (work / "answer").exists() else None
        recognition = source_read and bool(support)
        observations = {
            "source_acquired_before_boundary": source_read,
            "recognition": recognition,
            "support_paths_at_boundary": support,
            "utilization": support_reread,
            "task_success": answer == "done" and final == VALUE,
            "opportunity_status": "reached" if source_read else "not_reached",
        }
        checks = {
            "terminal_done": answer == "done",
            "source_acquired_before_boundary": source_read,
            "support_exact_at_boundary": bool(support),
            "no_early_answer_open": not any(row["request"].get("path") == "/work/answer" for row in pre),
            "support_reread_after_compaction": support_reread,
            "answer_exact": final == VALUE,
            "source_removed": not (work / "message").exists(),
            "network_disabled": identity["network_mode"] == "none",
            "read_only_root": identity["read_only_root"] is True,
            "only_work_mount_writable": [mount["destination"] for mount in identity["mounts"] if mount["rw"]] == ["/work"],
        }
        log.event("storage_salience_observations", observations=observations)
        log.event("filesystem_snapshot", boundary="after", entries=snapshot_tree(work))
        log.event("run_end", passed=all(checks.values()), checks=checks)
        title = "Scripted storage-salience dry run" if scripted else f"Storage-salience {arm} arm"
        report = log.write_report(
            title=title,
            question="Does the model create and later use non-answer storage when source and transcript loss make the bytes immediately useful?",
            method=("A deterministic reference client follows the same source-close boundary and writes a non-answer checkpoint before closing the source."
                    if scripted else
                    "The source closes trigger transcript loss and source removal. The arms differ only by the explicit preservation sentence; both prohibit an early answer and require exact recovery afterward."),
            result=(f"Source acquired: `{source_read}`; support at boundary: `{bool(support)}`; support reread: `{support_reread}`; terminal response: `{answer}`; exact final answer: `{final == VALUE}`."),
            interpretation=("This verifies the fixture, source-close trigger, scoring, and publication record. It is not model evidence."
                            if scripted else
                            "This is a storage-affordance salience calibration, not Pilot 1 evidence. A support file is a one-run ephemeral artifact; this record does not establish general tool discovery or persistent instrumental structure."),
        )
        report.open("a").write("\n## Salience observations\n\n" + json.dumps(observations, sort_keys=True) + "\n")
        print(f"{arm.upper()} STORAGE SALIENCE:", "PASS" if all(checks.values()) else "FAIL")
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
    parser.add_argument("--arm", choices=tuple(SEEDS), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--scripted", action="store_true")
    args = parser.parse_args()
    raise SystemExit(main(args.arm, args.seed, scripted=args.scripted))
