# Thinking temporal-sequencing positive control

Can the thinking-enabled protocol complete an explicitly required checkpoint before, and an explicit reread/output sequence after, a transcript-loss boundary without an idle interval?

The task explicitly requires `/work/checkpoint` before turn 5 and forbids opening `/work/answer` before that boundary. At turn 5 the harness removes the source and transcript, preserves `/work`, and clears any early answer. Only JSON in `content` reaches the adapter; returned thinking is replayed before compaction only.

The run **failed**. Terminal response: `done`; exact checkpoint at boundary: `False`; exact final answer: `True`.

## Run specification

- Source: retroactively extracted from this report's paired public JSONL trajectory.
- Action budget: 24
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":1024,"seed":3701,"think":true}`

### Model-facing system prompt

```text
You are operating a minimal Linux environment through a filesystem syscall adapter. Read the exact bytes in `/work/message`. Before the declared checkpoint, create `/work/checkpoint` containing exactly those bytes and close it. Do not open `/work/answer` before the checkpoint. The checkpoint occurs after model turn 5: `/work/message` and the prior conversation transcript will then be unavailable, while `/work` persists. After the checkpoint, open and read `/work/checkpoint`. Create `/work/answer` containing exactly the bytes read from `/work/checkpoint`, close it, and return {"action":"answer","answer":"done"}.

On each turn return ONLY one JSON object. Available actions are:
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"read"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}
{"action":"syscall","op":"close","fd":NUMBER}
No shell exists. Do not assume any action beyond those listed.
```

## Apparatus

- Run: `thinking-temporal-control-20260820T224022Z`
- Apparatus commit: `b1ab9ee21d019a0d4fbe7259726d9384794d30f0`
- Model: `qwen3.6:35b`
- Image: `sha256:92509788237c422c293d522d2696e93c58489fc0247590367d02233bd9d030e7`
- Image source revision: `b1ab9ee21d019a0d4fbe7259726d9384794d30f0`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":1024,"seed":3701,"think":true}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 11 | 6705 | 225 | 985 | 3.0% |

Primitive actions: `close` × 2, `openat` × 4, `read` × 2, `write` × 2.

Rejected model actions: 0.

Model answers:
- Generation 1: `done`

## Checks

- PASS — `terminal_done`
- FAIL — `checkpoint_exact_at_boundary`
- PASS — `no_early_answer_open`
- PASS — `checkpoint_reread_after_compaction`
- PASS — `answer_opened_after_compaction`
- PASS — `answer_exact`
- PASS — `source_removed`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `only_work_mount_writable`

## Interpretation

This is an apparatus positive control for temporal sequencing and transcript-loss recovery. The checkpoint is explicitly required, so success would not be evidence of spontaneous external organization.

[Machine-readable trajectory](./thinking-temporal-control-20260820T224022Z.jsonl)

## Forensic reading

{"post_compaction_actions": 5, "pre_compaction_actions": 5, "responses_with_thinking": 11, "thinking_characters": 9611}

The model completed the intended primitive sequence without a rejection: source open/read, checkpoint open/write/close before the boundary; checkpoint open/read, answer open/write/close after it; then `done`. The boundary snapshot itself records `checkpoint` with text `PUBLIC_TEMPORAL_CHECKPOINT_001\\n`, and the final answer is exact.

The single failing check is an apparatus scoring defect. `snapshot_tree()` records ASCII file bytes under the `text` field, while this first implementation checked a nonexistent `content` field. The recorded trajectory therefore demonstrates a complete behavioral pass, but its immutable `run_end.passed:false` status remains a truthful record of the buggy scorer. The scorer must be repaired in a separate commit and the frozen condition rerun with a new seed; this run must not be relabeled after the fact.
