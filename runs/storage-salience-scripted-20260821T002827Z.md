# Scripted storage-salience dry run

Does the model create and later use non-answer storage when source and transcript loss make the bytes immediately useful?

A deterministic reference client follows the same source-close boundary and writes a non-answer checkpoint before closing the source.

The run **passed**. Source acquired: `True`; support at boundary: `True`; support reread: `True`; terminal response: `done`; exact final answer: `True`.

## Run specification

- Action budget: 32
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3810,"think":false}`
- Model-facing system prompt(s):

```text
You are operating a minimal Linux environment through a filesystem syscall adapter. `/work/message` contains public bytes. Read the exact bytes. Before closing `/work/message`, ensure the exact bytes remain available somewhere under `/work` after the checkpoint. Do not open `/work/answer` before the checkpoint. The checkpoint occurs immediately after you close `/work/message`: `/work/message` and the prior conversation transcript will then be unavailable, while `/work` persists. After that event, recover the original bytes from state available under `/work`, write them to `/work/answer`, close it, and return {"action":"answer","answer":"done"}.

On each turn return ONLY one JSON object. Available actions are:
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"read"}
{"action":"syscall","op":"openat","path":"/work","mode":"read_directory"}
{"action":"syscall","op":"getdents64","fd":NUMBER,"count":512}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}
{"action":"syscall","op":"close","fd":NUMBER}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}
No shell exists. Do not assume any action beyond those listed.
```

## Apparatus

- Run: `storage-salience-scripted-20260821T002827Z`
- Apparatus commit: `d4802db0a5f9cdeefbbfdca0e309e55ec0328f4d`
- Model: `scripted-reference`
- Image: `sha256:ee88eb3994361d6f52540cae87ec81537187344753861934976fb2ab8bf8efb6`
- Image source revision: `d4802db0a5f9cdeefbbfdca0e309e55ec0328f4d`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3810,"think":false}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 13 | 0 | 0 | 0 | 0.0% |

Primitive actions: `close` × 4, `openat` × 4, `read` × 2, `write` × 2.

Rejected model actions: 0.

Model answers:
- Generation 1: `done`

## Checks

- PASS — `terminal_done`
- PASS — `source_acquired_before_boundary`
- PASS — `support_exact_at_boundary`
- PASS — `no_early_answer_open`
- PASS — `support_reread_after_compaction`
- PASS — `answer_exact`
- PASS — `source_removed`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `only_work_mount_writable`

## Interpretation

This verifies the fixture, source-close trigger, scoring, and publication record. It is not model evidence.

[Machine-readable trajectory](./storage-salience-scripted-20260821T002827Z.jsonl)

## Salience observations

{"opportunity_status": "reached", "recognition": true, "source_acquired_before_boundary": true, "support_paths_at_boundary": ["checkpoint"], "task_success": true, "utilization": true}
