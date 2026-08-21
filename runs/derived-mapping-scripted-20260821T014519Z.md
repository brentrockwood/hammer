# Scripted derived-mapping dry run

Does the model retain and use derived intermediate state when source transforms disappear?

Four ordered transform records are removed with the transcript after their closes. The explicit arm alone requires a non-answer derived file.

The run **passed**. Opportunity reached: `True`; support: `True`; structure: `derived_mapping`; utilized: `True`; exact answer: `True`.

## Run specification

- Action budget: 48
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3901,"think":false}`
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

- Run: `derived-mapping-scripted-20260821T014519Z`
- Apparatus commit: `586c4f624e45ac6b625d4c72a3b127e1551cf641`
- Model: `scripted-reference`
- Image: `sha256:35da68fc60598ecec6d33a704de236498aa7698001886694219b9afb749d7310`
- Image source revision: `586c4f624e45ac6b625d4c72a3b127e1551cf641`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3901,"think":false}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 25 | 0 | 0 | 0 | 0.0% |

Primitive actions: `close` × 8, `openat` × 8, `read` × 6, `write` × 2.

Rejected model actions: 0.

Model answers:
- Generation 1: `done`

## Checks

- PASS — `terminal_done`
- PASS — `opportunity_reached`
- PASS — `support_at_boundary`
- PASS — `support_reread_after_compaction`
- PASS — `answer_exact`
- PASS — `rules_removed`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `only_work_mount_writable`

## Interpretation

This is a derived-state salience calibration, not Pilot 1 evidence.

[Machine-readable trajectory](./derived-mapping-scripted-20260821T014519Z.jsonl)

## Derived-state observations

{"opportunity_reached": true, "recognition": true, "structure": "derived_mapping", "support_paths_at_boundary": ["derived"], "task_success": true, "utilization": true}
