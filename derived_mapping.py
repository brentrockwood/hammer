#!/usr/bin/env python3
"""Derived-intermediate-state salience calibration."""
import argparse
import hashlib
import json
import traceback

from corpus import snapshot_tree
from runner import (ExperimentLog, OllamaClient, ROOT, Settings, apparatus_metadata,
                    new_run_id, public_error, require_frozen_apparatus,
                    require_matching_loaded_context, run_generation)

RULES = ("shift=1\n", "shift=3\n", "shift=2\n", "shift=4\n")
QUERY, ANSWER = "symbols=acegikmo\n", "kmoqsuwy\n"
MAX_STEPS, NUM_CTX, NUM_PREDICT = 48, 32768, 4096
SEEDS = {"explicit": (3901, 3902, 3903, 3904, 3905, 3906),
         "consequences": (3911, 3912, 3913, 3914, 3915, 3916)}
COMMON = """You are operating a minimal Linux environment through a filesystem syscall adapter. `/work/rules` contains four ordered transform records. `/work/query` contains symbols. Read the rules and query, then write the transformed symbols as one ASCII line to `/work/answer` and return {\"action\":\"answer\",\"answer\":\"done\"}. Do not open `/work/answer` before the checkpoint. The checkpoint occurs after all four rule files you opened have been closed: `/work/rules` and the prior conversation transcript will then be unavailable, while `/work/query` persists. After that event, finish the task.

On each turn return ONLY one JSON object. Available actions are:
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"read\"}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work\",\"mode\":\"read_directory\"}
{\"action\":\"syscall\",\"op\":\"getdents64\",\"fd\":NUMBER,\"count\":512}
{\"action\":\"syscall\",\"op\":\"read\",\"fd\":NUMBER,\"count\":NUMBER}
{\"action\":\"syscall\",\"op\":\"write\",\"fd\":NUMBER,\"data\":\"ASCII STRING\"}
{\"action\":\"syscall\",\"op\":\"close\",\"fd\":NUMBER}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"write_create_truncate\"}
No shell exists. Do not assume any action beyond those listed."""
PROMPTS = {"explicit": COMMON.replace("Read the rules and query,", "Read the rules and query, derive the total transformation, and before the checkpoint create and close a non-answer file under `/work` containing sufficient derived information to finish,"),
           "consequences": COMMON}


class ScriptedClient:
    def __init__(self, settings):
        self.settings = settings
        actions = [{"action":"syscall","op":"openat","path":"/work/query","mode":"read"},
                   {"action":"syscall","op":"read","fd":4,"count":512}, {"action":"syscall","op":"close","fd":4}]
        for index in range(3):
            actions += [{"action":"syscall","op":"openat","path":f"/work/rules/r{index}","mode":"read"}, {"action":"syscall","op":"read","fd":4,"count":512}, {"action":"syscall","op":"close","fd":4}]
        actions += [{"action":"syscall","op":"openat","path":"/work/rules/r3","mode":"read"}, {"action":"syscall","op":"read","fd":4,"count":512}, {"action":"syscall","op":"openat","path":"/work/derived","mode":"write_create_truncate"}, {"action":"syscall","op":"write","fd":5,"data":"shift=10\n"}, {"action":"syscall","op":"close","fd":5}, {"action":"syscall","op":"close","fd":4}, {"action":"syscall","op":"openat","path":"/work/derived","mode":"read"}, {"action":"syscall","op":"read","fd":4,"count":512}, {"action":"syscall","op":"close","fd":4}, {"action":"syscall","op":"openat","path":"/work/answer","mode":"write_create_truncate"}, {"action":"syscall","op":"write","fd":4,"data":ANSWER}, {"action":"syscall","op":"close","fd":4}, {"action":"answer","answer":"done"}]
        self.actions = iter(actions)
    def ask(self, _history):
        return {"content":json.dumps(next(self.actions), separators=(",",":"))}, {"prompt_tokens":0,"completion_tokens":0,"context_tokens_after_response":0,"context_utilization":0,"thinking_characters":0}
    def environment(self): return {"transport":"scripted-reference"}


def main(arm, seed, scripted=False):
    if seed not in SEEDS[arm]: raise SystemExit("unfrozen seed")
    settings = Settings(); expected = {"model":"qwen3.6:35b","seed":seed,"temperature":0,"num_ctx":NUM_CTX,"num_predict":NUM_PREDICT,"think":False}
    if {key:getattr(settings,key) for key in expected} != expected or settings.max_steps != MAX_STEPS: raise SystemExit("frozen settings mismatch")
    run_id = new_run_id("derived-mapping-scripted" if scripted else f"derived-mapping-{arm}")
    log = ExperimentLog(run_id); client = ScriptedClient(settings) if scripted else OllamaClient(settings)
    metadata = apparatus_metadata(settings, client); metadata["model"] = "scripted-reference" if scripted else metadata["model"]
    require_frozen_apparatus(metadata)
    if not scripted: require_matching_loaded_context(metadata)
    work = ROOT / ".work" / run_id / "work"; rules = work / "rules"; rules.mkdir(parents=True)
    for index, rule in enumerate(RULES): (rules / f"r{index}").write_text(rule, encoding="ascii")
    (work / "query").write_text(QUERY, encoding="ascii")
    start = {**metadata,"scenario":"derived_mapping_scripted" if scripted else f"derived_mapping_{arm}","research_status":"derived-mapping salience calibration; not Pilot 1 evidence","sampling_seed":seed,"arm":arm,"max_steps":MAX_STEPS,"compaction_trigger":"close of all four opened rule files","system_prompt_sha256":hashlib.sha256(PROMPTS[arm].encode()).hexdigest(),"scripted":scripted}
    log.event("run_start", public_fields=start, **start, ollama_host=settings.ollama, local_work_dir=str(work)); log.event("filesystem_snapshot", boundary="before", entries=snapshot_tree(work))
    opened, closed, boundary = {}, set(), {}
    def trigger(_step, action, result):
        if not action or not result or not result.get("ok"): return False
        if action.get("op") == "openat" and action.get("path","").startswith("/work/rules/") and action.get("mode") == "read": opened[result["fd"]] = action["path"]
        if action.get("op") == "close" and action.get("fd") in opened: closed.add(opened[action["fd"]])
        return len(closed) >= 4
    def compact(step, _identity):
        for path in (rules, work / "answer"):
            if path.is_dir():
                for child in path.iterdir(): child.unlink()
                path.rmdir()
            elif path.exists(): path.unlink()
        boundary["entries"] = snapshot_tree(work); log.event("fixture_event", step=step, event_name="rules_removed_and_early_answer_cleared", entries=boundary["entries"])
    try:
        answer, identity = run_generation(log, client, 1, PROMPTS[arm], work, max_steps=MAX_STEPS, require_compactions_before_answer=True, required_compactions=1, on_compaction=compact, compaction_predicate=trigger)
        rows=[json.loads(line) for line in log.public_path.read_text().splitlines()]; comp=next(row for row in rows if row["event"]=="context_compaction")["step"]
        req=[row for row in rows if row["event"]=="syscall_request"]; result={row["step"]:row["result"] for row in rows if row["event"]=="syscall_result"}
        pre=[row for row in req if row["step"]<=comp]; post=[row for row in req if row["step"]>comp]
        reads={row["request"].get("path") for row in pre if row["request"].get("op")=="openat" and row["request"].get("mode")=="read"}
        opportunity=set(f"/work/rules/r{i}" for i in range(4)).issubset(reads) and "/work/query" in reads
        support=[entry for entry in boundary.get("entries",[]) if entry["type"]=="file" and entry["path"] not in {"answer","query"}]
        support_paths={entry["path"] for entry in support}; support_fds={result[row["step"]].get("fd") for row in post if row["request"].get("op")=="openat" and row["request"].get("mode")=="read" and row["request"].get("path","").removeprefix("/work/") in support_paths and result[row["step"]].get("ok")}
        utilized=any(row["request"].get("op")=="read" and row["request"].get("fd") in support_fds for row in post); final=(work/"answer").read_text(encoding="ascii") if (work/"answer").exists() else None
        structure="derived_mapping" if any(entry.get("text")=="shift=10\n" for entry in support) else ("raw_or_other" if support else "none")
        obs={"opportunity_reached":opportunity,"recognition":bool(support),"support_paths_at_boundary":[entry["path"] for entry in support],"structure":structure,"utilization":utilized,"task_success":answer=="done" and final==ANSWER}; log.event("derived_mapping_observations", observations=obs); log.event("filesystem_snapshot", boundary="after", entries=snapshot_tree(work))
        checks={"terminal_done":answer=="done","opportunity_reached":opportunity,"support_at_boundary":bool(support),"support_reread_after_compaction":utilized,"answer_exact":final==ANSWER,"rules_removed":not rules.exists(),"network_disabled":identity["network_mode"]=="none","read_only_root":identity["read_only_root"] is True,"only_work_mount_writable":[m["destination"] for m in identity["mounts"] if m["rw"]]==["/work"]}; log.event("run_end", passed=all(checks.values()), checks=checks)
        report=log.write_report(title="Scripted derived-mapping dry run" if scripted else f"Derived-mapping {arm} arm", question="Does the model retain and use derived intermediate state when source transforms disappear?", method="Four ordered transform records are removed with the transcript after their closes. The explicit arm alone requires a non-answer derived file.", result=f"Opportunity reached: `{opportunity}`; support: `{bool(support)}`; structure: `{structure}`; utilized: `{utilized}`; exact answer: `{final==ANSWER}`.", interpretation="This is a derived-state salience calibration, not Pilot 1 evidence."); report.open("a").write("\n## Derived-state observations\n\n"+json.dumps(obs,sort_keys=True)+"\n"); return 0 if all(checks.values()) else 2
    except Exception as error:
        log.event("run_error", public_fields={"error_type":type(error).__name__,"error":public_error(error,settings)}, error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc()); log.event("run_end",passed=False,checks={"run_completed_without_infrastructure_error":False}); return 3

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--arm",choices=tuple(SEEDS),required=True); p.add_argument("--seed",type=int,required=True); p.add_argument("--scripted",action="store_true"); a=p.parse_args(); raise SystemExit(main(a.arm,a.seed,a.scripted))
