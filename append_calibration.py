#!/usr/bin/env python3
"""Calibrate the explicit reopenable append affordance without a model."""
from corpus import snapshot_diff, snapshot_tree
from runner import AgentContainer, ExperimentLog, ROOT, git_commit, image_metadata, new_run_id


def writable_mounts(identity):
    return [mount["destination"] for mount in identity["mounts"] if mount["rw"]]


def metadata():
    image = image_metadata()
    commit = git_commit()
    if image["image_revision"] != commit:
        raise RuntimeError("append calibration requires an image built from HEAD")
    return {"apparatus_commit": commit, **image}


def main():
    run_id = new_run_id("append-calibration")
    log = ExperimentLog(run_id)
    work_dir = ROOT / ".work" / run_id / "work"
    work_dir.mkdir(parents=True)
    before = snapshot_tree(work_dir)
    start = {
        **metadata(),
        "scenario": "append_affordance_scripted_calibration",
        "research_status": "apparatus calibration; no model observation",
        "append_enabled": True,
        "expected_text": "first line\\nsecond line\\n",
    }
    log.event("run_start", **start)
    log.event("filesystem_snapshot", boundary="before", entries=before)
    container = AgentContainer(run_id, 1, work_dir, agent_args=("--append",)).start()
    log.event("generation_start", generation=1, model_context="scripted reference",
              container=container.identity, max_steps=9)
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
    recovered = None
    try:
        fd = call(op="openat", path="/work/journal", mode="write_create_truncate")["fd"]
        call(op="write", fd=fd, data="first line\n")
        call(op="close", fd=fd)
        fd = call(op="openat", path="/work/journal", mode="write_append_create")["fd"]
        call(op="write", fd=fd, data="second line\n")
        call(op="close", fd=fd)
        fd = call(op="openat", path="/work/journal", mode="read")["fd"]
        recovered = call(op="read", fd=fd, count=4096)["data"]
        call(op="close", fd=fd)
    except Exception as caught:
        error = caught
    finally:
        exit_code = container.stop()
    after = snapshot_tree(work_dir)
    checks = {
        "scripted_sequence_completed": error is None,
        "append_round_trip": recovered == "first line\nsecond line\n",
        "network_disabled": container.identity["network_mode"] == "none",
        "read_only_root": container.identity["read_only_root"] is True,
        "no_init_process": container.identity["init"] is False,
        "only_work_mount_writable": writable_mounts(container.identity) == ["/work"],
    }
    log.event("filesystem_snapshot", boundary="after", entries=after,
              diff=snapshot_diff(before, after))
    log.event("generation_end", generation=1, container_id=container.identity["container_id"],
              exit_code=exit_code, usage_summary={"model_calls": 0,
              "cumulative_prompt_tokens": 0, "cumulative_completion_tokens": 0,
              "cumulative_processed_tokens": 0, "peak_live_context_tokens": 0,
              "context_limit": 32768, "peak_context_utilization": 0})
    log.event("run_end", passed=all(checks.values()), checks=checks,
              error=None if error is None else type(error).__name__)
    report = log.write_report(
        title="Reopenable append affordance calibration",
        question="Does the opt-in append mode preserve a file through close and reopen while retaining the fixed isolation boundary?",
        method="A scripted client, not a model, wrote one line with truncate-on-create, closed the descriptor, reopened the same path with append enabled, wrote a second line, then reopened it read-only.",
        result=("The recovered bytes were exactly the two-line sequence." if checks["append_round_trip"] else "The expected two-line sequence was not recovered."),
        interpretation="This calibrates one explicit filesystem primitive. It does not show that a model will select, reuse, or benefit from append.",
    )
    print("APPEND CALIBRATION:", "PASS" if all(checks.values()) else "FAIL")
    print("PUBLIC RECORD:", log.public_path)
    print("HUMAN REPORT:", report)
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
