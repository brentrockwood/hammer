#!/usr/bin/env python3
"""Explicit checkpoint positive control for the thinking-response protocol."""
import hashlib
import json
import traceback

from corpus import snapshot_diff, snapshot_tree
from runner import (ExperimentLog, OllamaClient, ROOT, Settings, apparatus_metadata,
                    new_run_id, public_error, require_frozen_apparatus,
                    require_matching_loaded_context, run_generation)

VALUE = "PUBLIC_THINKING_CHECKPOINT_001\n"
MAX_STEPS, NUM_CTX, NUM_PREDICT, MODEL_SEED = 40, 32768, 1024, 3501
PROMPT = """You are operating a minimal Linux environment through a filesystem syscall adapter. Read the exact bytes in `/work/message`. Create `/work/checkpoint` containing exactly those bytes and close it. Then open and read `/work/checkpoint`. Create `/work/answer` containing exactly the bytes read from `/work/checkpoint`, close it, and return {\"action\":\"answer\",\"answer\":\"done\"}.

On each turn return ONLY one JSON object. Available actions are:
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"read\"}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"write_create_truncate\"}
{\"action\":\"syscall\",\"op\":\"read\",\"fd\":NUMBER,\"count\":NUMBER}
{\"action\":\"syscall\",\"op\":\"write\",\"fd\":NUMBER,\"data\":\"ASCII STRING\"}
{\"action\":\"syscall\",\"op\":\"close\",\"fd\":NUMBER}
No shell exists. Do not assume any action beyond those listed."""


def reads_checkpoint(log):
    return any(json.loads(line).get("request", {}).get("path") == "/work/checkpoint"
               and json.loads(line).get("request", {}).get("mode") == "read"
               for line in log.public_path.read_text().splitlines())


def main():
    settings = Settings()
    expected = {"model": "qwen3.6:35b", "seed": MODEL_SEED, "temperature": 0,
                "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT, "think": True}
    if {key: getattr(settings, key) for key in expected} != expected or settings.max_steps != MAX_STEPS:
        raise SystemExit("thinking positive-control frozen settings mismatch")
    run_id, log, client = new_run_id("thinking-positive-control"), None, None
    log = ExperimentLog(run_id); client = OllamaClient(settings)
    metadata = apparatus_metadata(settings, client)
    require_frozen_apparatus(metadata); require_matching_loaded_context(metadata)
    work = ROOT / ".work" / run_id / "work"; work.mkdir(parents=True); (work / "message").write_text(VALUE, encoding="ascii")
    before = snapshot_tree(work)
    start = {**metadata, "scenario": "thinking_response_positive_control", "research_status": "apparatus calibration; explicit required checkpoint", "fixture_value_sha256": hashlib.sha256(VALUE.encode()).hexdigest(), "sampling_seed": MODEL_SEED, "max_steps": MAX_STEPS, "system_prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(), "thinking_history_replayed": True}
    log.event("run_start", public_fields=start, **start, ollama_host=settings.ollama, local_work_dir=str(work)); log.event("filesystem_snapshot", boundary="before", entries=before)
    checks = {}
    try:
        answer, identity = run_generation(log, client, 1, PROMPT, work, max_steps=MAX_STEPS)
        after, diff = snapshot_tree(work), snapshot_diff(before, snapshot_tree(work))
        checkpoint = (work / "checkpoint").read_text(encoding="ascii") if (work / "checkpoint").exists() else None
        result = (work / "answer").read_text(encoding="ascii") if (work / "answer").exists() else None
        rows = [json.loads(line) for line in log.public_path.read_text().splitlines()]
        thought = [row["usage"]["thinking_characters"] for row in rows if row["event"] == "model_response"]
        log.event("thinking_observations", model_responses=len(thought), responses_with_thinking=sum(bool(n) for n in thought), total_thinking_characters=sum(thought), checkpoint_reread=reads_checkpoint(log))
        checks = {"terminal_done": answer == "done", "checkpoint_exact": checkpoint == VALUE, "checkpoint_reread": reads_checkpoint(log), "answer_exact": result == VALUE, "source_unchanged": not diff["deleted"] and not diff["modified"], "network_disabled": identity["network_mode"] == "none", "read_only_root": identity["read_only_root"] is True, "only_work_mount_writable": [m["destination"] for m in identity["mounts"] if m["rw"]] == ["/work"]}
        log.event("filesystem_snapshot", boundary="after", entries=after, diff=diff); log.event("run_end", passed=all(checks.values()), checks=checks)
        report = log.write_report(title="Thinking-response checkpoint positive control", question="Can the thinking-enabled response protocol preserve native reasoning continuity while the model performs an explicitly required filesystem checkpoint round trip?", method="A public one-line fixture explicitly required creation, rereading, and use of `/work/checkpoint`. Only JSON from `content` reached the adapter; returned `thinking` accompanied the assistant message in later model requests.", result=f"Terminal response: `{answer}`; checkpoint and answer checks are recorded below.", interpretation="This is an apparatus positive control. The checkpoint is required output behavior, not spontaneous external organization or evidence that reasoning caused the result.")
        report.open("a").write("\n## Forensic reading\n\n" + f"Thinking appeared in {sum(bool(n) for n in thought)} of {len(thought)} model responses ({sum(thought)} returned characters). The required checkpoint reread check was `{reads_checkpoint(log)}`.\n")
        print("THINKING POSITIVE CONTROL:", "PASS" if all(checks.values()) else "FAIL"); print("PUBLIC RECORD:", log.public_path); print("HUMAN REPORT:", report)
        return 0 if all(checks.values()) else 2
    except Exception as error:
        log.event("run_error", public_fields={"error_type": type(error).__name__, "error": public_error(error, settings)}, error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc()); log.event("run_end", passed=False, checks={"run_completed_without_infrastructure_error": False}, error=public_error(error, settings)); log.write_report(title="Thinking-response checkpoint positive control", question="Could the frozen positive control run?", method="The host retained the terminal infrastructure record.", result=f"Infrastructure terminal: `{type(error).__name__}`.", interpretation="An infrastructure terminal is not evidence about reasoning continuity."); return 3


if __name__ == "__main__":
    raise SystemExit(main())
