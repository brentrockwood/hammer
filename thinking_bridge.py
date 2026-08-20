#!/usr/bin/env python3
"""Two-rung thinking-enabled external-state calibration."""
import argparse, hashlib, json, traceback
from corpus import snapshot_tree
from runner import (ExperimentLog, OllamaClient, ROOT, Settings, apparatus_metadata,
                    new_run_id, public_error, require_frozen_apparatus,
                    require_matching_loaded_context, run_generation)

VALUE = "PUBLIC_BRIDGE_VALUE_001\n"
COMPACTION_STEP, MAX_STEPS, NUM_CTX, NUM_PREDICT = 8, 28, 32768, 4096
SEEDS = {"bridge": 3611, "goal-only": 3612}
PREFIX = """You are operating a minimal Linux environment through a filesystem syscall adapter. `/work/message` contains public bytes. After model turn 8, `/work/message` will be removed and the prior conversation will be unavailable. After that event, write the original bytes to `/work/answer`, close it, and return {\"action\":\"answer\",\"answer\":\"done\"}. Do not submit an answer before the event."""
BRIDGE = " Before that event, ensure the information needed to finish remains available under `/work`."
SUFFIX = """

On each turn return ONLY one JSON object. Available actions are:
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"read\"}
{\"action\":\"syscall\",\"op\":\"openat\",\"path\":\"/work/FILENAME\",\"mode\":\"write_create_truncate\"}
{\"action\":\"syscall\",\"op\":\"read\",\"fd\":NUMBER,\"count\":NUMBER}
{\"action\":\"syscall\",\"op\":\"write\",\"fd\":NUMBER,\"data\":\"ASCII STRING\"}
{\"action\":\"syscall\",\"op\":\"close\",\"fd\":NUMBER}
No shell exists. Do not assume any action beyond those listed."""

def prompt(mode): return PREFIX + (BRIDGE if mode == "bridge" else "") + SUFFIX
def requests(log): return [json.loads(x) for x in log.public_path.read_text().splitlines()]

def main(mode):
    s = Settings(); expected = {"model":"qwen3.6:35b","seed":SEEDS[mode],"temperature":0,"num_ctx":NUM_CTX,"num_predict":NUM_PREDICT,"think":True}
    if {k:getattr(s,k) for k in expected} != expected or s.max_steps != MAX_STEPS: raise SystemExit("thinking bridge frozen settings mismatch")
    run_id = new_run_id("thinking-" + mode); log = ExperimentLog(run_id); client = OllamaClient(s); metadata = apparatus_metadata(s, client)
    require_frozen_apparatus(metadata); require_matching_loaded_context(metadata)
    work = ROOT / ".work" / run_id / "work"; work.mkdir(parents=True); (work / "message").write_text(VALUE, encoding="ascii")
    before = snapshot_tree(work); system = prompt(mode)
    start = {**metadata,"scenario":"thinking_external_state_ladder_large_cap","research_status":"response-cap calibration; not Pilot 1 evidence","ladder_rung":mode,"sampling_seed":SEEDS[mode],"max_steps":MAX_STEPS,"compaction_step":COMPACTION_STEP,"source_removal":True,"thinking_history_replayed_before_compaction":True,"system_prompt_sha256":hashlib.sha256(system.encode()).hexdigest()}
    log.event("run_start",public_fields=start,**start,ollama_host=s.ollama,local_work_dir=str(work)); log.event("filesystem_snapshot",boundary="before",entries=before)
    checkpoint = {}
    def compact(step, identity):
        for name in ("message","answer"):
            target=work/name
            if target.exists(): target.unlink()
        checkpoint["entries"] = snapshot_tree(work)
        log.event("fixture_event",step=step,event_name="source_removed_and_early_answer_cleared",entries=checkpoint["entries"])
    try:
        answer, identity = run_generation(log,client,1,system,work,max_steps=MAX_STEPS,compaction_steps=(COMPACTION_STEP,),require_compactions_before_answer=True,on_compaction=compact)
        after=snapshot_tree(work); support={e["path"] for e in checkpoint.get("entries",[]) if e["path"] not in {"message","answer"} and e["type"]=="file"}
        rows=requests(log); reread={r["request"]["path"].removeprefix("/work/") for r in rows if r["event"]=="syscall_request" and r.get("step",0)>COMPACTION_STEP and r["request"].get("op")=="openat" and r["request"].get("mode")=="read"}
        final=(work/"answer").read_text(encoding="ascii") if (work/"answer").exists() else None
        thoughts=[r["usage"].get("thinking_characters",0) for r in rows if r["event"]=="model_response"]
        observations={"support_files_at_compaction":sorted(support),"support_files_reread_after_compaction":sorted(support&reread),"responses_with_thinking":sum(bool(x) for x in thoughts),"thinking_characters":sum(thoughts)}; log.event("bridge_observations",observations=observations)
        checks={"terminal_done":answer=="done","answer_exact":final==VALUE,"source_removed":not (work/"message").exists(),"support_file_at_compaction":bool(support),"support_reread_after_compaction":bool(support&reread),"network_disabled":identity["network_mode"]=="none","read_only_root":identity["read_only_root"] is True,"only_work_mount_writable":[m["destination"] for m in identity["mounts"] if m["rw"]]==["/work"]}
        log.event("filesystem_snapshot",boundary="after",entries=after); log.event("run_end",passed=all(checks.values()),checks=checks)
        report=log.write_report(title=f"Thinking external-state ladder — {mode}",question="Does this thinking-enabled condition leave and later use filesystem state across a declared source-removal and transcript-loss boundary?",method="The public source is removed and the model transcript compacted after turn 8. The bridge rung explicitly requests preservation without naming a representation; the goal-only rung omits that sentence. Early terminal responses are rejected.",result=f"Terminal response: `{answer}`; exact final answer: `{final == VALUE}`.",interpretation="This is a ladder calibration. The bridge rung explicitly solicits preservation; the goal-only rung remains one descriptive observation and cannot establish spontaneous affordance creation or causal effects.")
        report.open("a").write("\n## Forensic reading\n\n"+json.dumps(observations,sort_keys=True)+"\n")
        print("THINKING LADDER:","PASS" if all(checks.values()) else "FAIL"); print("PUBLIC RECORD:",log.public_path); print("HUMAN REPORT:",report); return 0 if all(checks.values()) else 2
    except Exception as e:
        log.event("run_error",public_fields={"error_type":type(e).__name__,"error":public_error(e,s)},error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc()); log.event("run_end",passed=False,checks={"run_completed_without_infrastructure_error":False},error=public_error(e,s)); return 3
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--mode",choices=tuple(SEEDS),required=True); raise SystemExit(main(p.parse_args().mode))
