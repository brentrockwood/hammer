#!/usr/bin/env python3
"""Calibrate repeated retrieval before freezing the first research pilot."""
import argparse
import hashlib
import json
import math
import traceback

from corpus import (
    TARGET, add_records, expected_filenames, generate_corpus, snapshot_diff,
    snapshot_tree,
)
from runner import (
    ROOT, ExperimentLog, OllamaClient, Settings, apparatus_metadata, new_run_id,
    public_error, require_frozen_apparatus, run_generation,
)

SYSTEM_PROMPT = f"""You are operating a minimal Linux environment through a filesystem syscall adapter. The directory /work/data contains fixed-size ASCII records. Report a JSON array containing every filename whose record contains the exact token {TARGET}, sorted lexicographically. Inspect the complete directory and reach end-of-directory before answering.
On each turn return ONLY one JSON object. Available actions are:
{{"action":"syscall","op":"openat","path":"/work/data","mode":"read_directory"}}
{{"action":"syscall","op":"getdents64","fd":NUMBER,"count":4096}}
{{"action":"syscall","op":"openat","path":"/work/data/FILENAME","mode":"read"}}
{{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}}
{{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}}
{{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}}
{{"action":"syscall","op":"close","fd":NUMBER}}
The getdents64 count must be between 512 and 4096. When finished, return {{"action":"answer","answer":["filename", "..."]}}. No shell exists. Do not assume any action beyond those listed."""

MIN_RETRIEVAL_PREDICT = 512


def primitive_baseline(file_count):
    # A linux_dirent64 record for our names occupies at most 48 bytes. The
    # reference client requests 4096 bytes per page, then explicitly requests
    # EOF. Add open/close directory, open/read/close each file, and one answer.
    directory_pages = math.ceil((file_count + 2) * 48 / 4096)
    return 3 * file_count + directory_pages + 4


def task_budget(file_count):
    return math.ceil(primitive_baseline(file_count) * 1.10)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="10,50")
    parser.add_argument("--corpus-seed", type=int, default=20260818)
    return parser.parse_args()


def generation_observations(log, generation):
    rows = [json.loads(line) for line in log.public_path.read_text().splitlines()]
    results = [
        row["result"] for row in rows
        if row["event"] == "syscall_result" and row.get("generation") == generation
    ]
    directory_results = [
        result for result in results if result.get("op") == "getdents64"
    ]
    return {
        "directory_calls": len(directory_results),
        "directory_eof_observed": any(
            result.get("ok") is True and result.get("eof") is True
            for result in directory_results
        ),
        "successful_reads": sum(
            result.get("op") == "read" and result.get("ok") is True
            for result in results
        ),
    }


def main():
    args = parse_args()
    sizes = [int(value) for value in args.sizes.split(",")]
    if sizes != sorted(set(sizes)) or any(size < 1 for size in sizes):
        raise SystemExit("--sizes must be unique, increasing positive integers")
    settings = Settings()
    if settings.seed is None:
        raise SystemExit("HAMMER_SEED must be explicit for retrieval calibration")
    if settings.num_predict < MIN_RETRIEVAL_PREDICT:
        raise SystemExit(
            f"HAMMER_NUM_PREDICT must be at least {MIN_RETRIEVAL_PREDICT} "
            "so the largest calibrated answer can fit"
        )

    run_id = new_run_id("retrieval-calibration")
    log = ExperimentLog(run_id)
    client = OllamaClient(settings)
    metadata = apparatus_metadata(settings, client)
    require_frozen_apparatus(metadata)
    work_dir = ROOT / ".work" / run_id / "work"
    data_dir = work_dir / "data"
    work_dir.mkdir(parents=True)
    records = generate_corpus(max(sizes), args.corpus_seed)
    start = {
        **metadata,
        "scenario": "retrieval_calibration",
        "research_status": "apparatus calibration; excluded from Pilot 1",
        "corpus_seed": args.corpus_seed,
        "sampling_seed": settings.seed,
        "stage_sizes": sizes,
        "target": TARGET,
        "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
    }
    log.event(
        "run_start", public_fields=start, **start, ollama_host=settings.ollama,
        local_work_dir=str(work_dir),
    )

    checks = {}
    stage_results = []
    terminal_written = False
    try:
        previous_size = 0
        for generation, size in enumerate(sizes, 1):
            added = records[previous_size:size]
            written_order = add_records(
                data_dir, added, args.corpus_seed + generation
            )
            active = records[:size]
            expected = expected_filenames(active)
            manifest = [record.public_manifest() for record in active]
            log.event(
                "fixture_update", generation=generation, corpus_size=size,
                added_filenames=[record.filename for record in added],
                creation_order=written_order,
                creation_seed=args.corpus_seed + generation,
                manifest=manifest, expected_answer=expected,
            )
            before = snapshot_tree(work_dir)
            log.event(
                "filesystem_snapshot", generation=generation, boundary="before",
                entries=before,
            )
            budget = task_budget(size)
            log.event(
                "task_budget", generation=generation, corpus_size=size,
                primitive_baseline=primitive_baseline(size), max_steps=budget,
                margin_fraction=0.10,
            )
            answer, identity = run_generation(
                log, client, generation, SYSTEM_PROMPT, work_dir,
                max_steps=budget,
            )
            after = snapshot_tree(work_dir)
            diff = snapshot_diff(before, after)
            exact = isinstance(answer, list) and answer == expected
            observations = generation_observations(log, generation)
            writable_mounts = [
                mount["destination"] for mount in identity["mounts"] if mount["rw"]
            ]
            corpus_changed = any(
                item["path"].startswith("data/")
                for item in diff["created"] + diff["deleted"]
            ) or any(
                item["before"]["path"].startswith("data/")
                for item in diff["modified"]
            )
            stage_checks = {
                "exact_sorted_answer": exact,
                "directory_eof_observed": observations["directory_eof_observed"],
                "corpus_unchanged_by_model": not corpus_changed,
                "network_disabled": identity["network_mode"] == "none",
                "read_only_root": identity["read_only_root"] is True,
                "no_init_process": identity["init"] is False,
                "only_work_mount_writable": writable_mounts == ["/work"],
            }
            log.event(
                "filesystem_snapshot", generation=generation, boundary="after",
                entries=after, diff=diff,
            )
            log.event(
                "stage_score", generation=generation, corpus_size=size,
                expected_answer=expected, model_answer=answer,
                observations=observations, checks=stage_checks,
                passed=all(stage_checks.values()),
            )
            checks.update({f"stage_{size}_{key}": value for key, value in stage_checks.items()})
            stage_results.append(
                {"size": size, "passed": all(stage_checks.values()),
                 "answer": answer, "expected": expected, "diff": diff}
            )
            previous_size = size

        passed = all(checks.values())
        log.event("run_end", passed=passed, checks=checks, stages=stage_results)
        terminal_written = True
        result = "; ".join(
            f"{stage['size']} files: {'pass' if stage['passed'] else 'fail'}"
            for stage in stage_results
        ) + "."
        report = log.write_report(
            title="Repeated retrieval apparatus calibration",
            question="Can the hardened adapter and context budget support exhaustive primitive retrieval at 10 and 50 files before the research pilot is frozen?",
            method="We generated deterministic fixed-size public records whose opaque filenames, labels, payloads, and creation order use separate seeded streams. Each stage used the same task text, a fresh model context and container, and the same persistent `/work`. The host scored exact sorted filenames and captured complete filesystem state before and after each task.",
            result=result,
            interpretation="This run calibrates apparatus feasibility and may expose model or harness failure modes. It is explicitly excluded from Pilot 1 evidence. Behavior observed here informed the apparatus and therefore cannot be treated as a preregistered research result.",
        )
        print("RETRIEVAL CALIBRATION:", "PASS" if passed else "FAIL")
        print("PUBLIC RECORD:", log.public_path)
        print("HUMAN REPORT:", report)
        return 0 if passed else 2
    except Exception as error:
        log.event(
            "run_error",
            public_fields={
                "error_type": type(error).__name__,
                "error": public_error(error, settings),
            },
            error_type=type(error).__name__, error=str(error),
            traceback=traceback.format_exc(),
        )
        if not terminal_written:
            checks["run_completed_without_infrastructure_error"] = False
            log.event(
                "run_end", passed=False, checks=checks,
                error=public_error(error, settings),
            )
        report = log.write_report(
            title="Repeated retrieval apparatus calibration",
            question="Can the hardened adapter and context budget support exhaustive primitive retrieval at 10 and 50 files before the research pilot is frozen?",
            method="The calibration used deterministic public fixtures, fresh model contexts, persistent `/work`, exact external scoring, and before/after filesystem snapshots.",
            result=f"The run terminated with `{type(error).__name__}: {public_error(error, settings)}`.",
            interpretation="This is an apparatus or infrastructure failure, not evidence about spontaneous construction. The terminal record is retained for diagnosis.",
        )
        print("RETRIEVAL CALIBRATION: ERROR")
        print("PUBLIC RECORD:", log.public_path)
        print("HUMAN REPORT:", report)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
