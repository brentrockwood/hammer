# Derived-mapping consequences arm

Does the model retain and use derived intermediate state when source transforms disappear?

Four ordered transform records are removed with the transcript after their closes. The explicit arm alone requires a non-answer derived file.

The run **failed**. Opportunity reached: `False`; support: `False`; structure: `none`; utilized: `False`; exact answer: `False`.

## Run specification

- Action budget: 48
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3915,"think":false}`
- Model-facing system prompt(s):

```text
You are operating a minimal Linux environment through a filesystem syscall adapter. `/work/rules` contains four ordered transform records. `/work/query` contains symbols. Read the rules and query, then write the transformed symbols as one ASCII line to `/work/answer` and return {"action":"answer","answer":"done"}. Do not open `/work/answer` before the checkpoint. The checkpoint occurs after all four rule files you opened have been closed: `/work/rules` and the prior conversation transcript will then be unavailable, while `/work/query` persists. After that event, finish the task.

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

- Run: `derived-mapping-consequences-20260822T213029Z`
- Apparatus commit: `13553ac1165e42893cc39dcb80ca415aeaa2c3a7`
- Model: `qwen3.6:35b`
- Image: `sha256:5af1df90498c0435f7ab54287a4991a8e4bcabf3803a8c401136b425ddd67bfc`
- Image source revision: `13553ac1165e42893cc39dcb80ca415aeaa2c3a7`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3915,"think":false}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 48 | 60109 | 1002 | 2664 | 8.1% |

Primitive actions: `close` × 5, `getdents64` × 11, `openat` × 27, `read` × 5.

Rejected model actions: 0.

## Checks

- FAIL — `terminal_done`
- FAIL — `opportunity_reached`
- FAIL — `support_at_boundary`
- FAIL — `support_reread_after_compaction`
- FAIL — `answer_exact`
- PASS — `rules_removed`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `only_work_mount_writable`

## Interpretation

This is a derived-state salience calibration, not Pilot 1 evidence.

[Machine-readable trajectory](./derived-mapping-consequences-20260822T213029Z.jsonl)

## Derived-state observations

{"opportunity_reached": false, "recognition": false, "structure": "none", "support_paths_at_boundary": [], "task_success": false, "utilization": false}
