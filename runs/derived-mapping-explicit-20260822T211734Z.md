# Derived-mapping explicit arm

Does the model retain and use derived intermediate state when source transforms disappear?

Four ordered transform records are removed with the transcript after their closes. The explicit arm alone requires a non-answer derived file.

The run **failed**. Opportunity reached: `False`; support: `False`; structure: `none`; utilized: `False`; exact answer: `False`.

## Run specification

- Action budget: 48
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3905,"think":false}`
- Model-facing system prompt(s):

```text
You are operating a minimal Linux environment through a filesystem syscall adapter. `/work/rules` contains four ordered transform records. `/work/query` contains symbols. Read the rules and query, derive the total transformation, and before the checkpoint create and close a non-answer file under `/work` containing sufficient derived information to finish, then write the transformed symbols as one ASCII line to `/work/answer` and return {"action":"answer","answer":"done"}. Do not open `/work/answer` before the checkpoint. The checkpoint occurs after all four rule files you opened have been closed: `/work/rules` and the prior conversation transcript will then be unavailable, while `/work/query` persists. After that event, finish the task.

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

- Run: `derived-mapping-explicit-20260822T211734Z`
- Apparatus commit: `6c1f8af0fe8056e3e54ce54c3795ab2ba7055e1a`
- Model: `qwen3.6:35b`
- Image: `sha256:25f904c8d4b1db22568754422f88a5bb188f6f483beb35c8fd9d3c3f9194b1d1`
- Image source revision: `6c1f8af0fe8056e3e54ce54c3795ab2ba7055e1a`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3905,"think":false}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 48 | 61306 | 997 | 2686 | 8.2% |

Primitive actions: `close` × 5, `getdents64` × 11, `openat` × 26, `read` × 5, `write` × 1.

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

[Machine-readable trajectory](./derived-mapping-explicit-20260822T211734Z.jsonl)

## Derived-state observations

{"opportunity_reached": false, "recognition": false, "structure": "none", "support_paths_at_boundary": [], "task_success": false, "utilization": false}
