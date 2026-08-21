# Thinking-response checkpoint positive control

Can the thinking-enabled response protocol preserve native reasoning continuity while the model performs an explicitly required filesystem checkpoint round trip?

A public one-line fixture explicitly required creation, rereading, and use of `/work/checkpoint`. Only JSON from `content` reached the adapter; returned `thinking` accompanied the assistant message in later model requests.

The run **passed**. Terminal response: `done`; checkpoint and answer checks are recorded below.

## Run specification

- Source: retroactively extracted from this report's paired public JSONL trajectory.
- Action budget: 40
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":1024,"seed":3501,"think":true}`

### Model-facing system prompt

```text
You are operating a minimal Linux environment through a filesystem syscall adapter. Read the exact bytes in `/work/message`. Create `/work/checkpoint` containing exactly those bytes and close it. Then open and read `/work/checkpoint`. Create `/work/answer` containing exactly the bytes read from `/work/checkpoint`, close it, and return {"action":"answer","answer":"done"}.

On each turn return ONLY one JSON object. Available actions are:
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"read"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}
{"action":"syscall","op":"close","fd":NUMBER}
No shell exists. Do not assume any action beyond those listed.
```

## Apparatus

- Run: `thinking-positive-control-20260820T202249Z`
- Apparatus commit: `948e1e7ed4d6c4d5ada8487844151d19437cad88`
- Model: `qwen3.6:35b`
- Image: `sha256:d816e63c4c4797bcbaa2cad5fe9dd66d835f59560295477c1e9a4bf53b7a2776`
- Image source revision: `948e1e7ed4d6c4d5ada8487844151d19437cad88`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":1024,"seed":3501,"think":true}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 11 | 8545 | 309 | 1166 | 3.6% |

Primitive actions: `close` × 2, `openat` × 4, `read` × 2, `write` × 2.

Rejected model actions: 0.

Model answers:
- Generation 1: `done`

## Checks

- PASS — `terminal_done`
- PASS — `checkpoint_exact`
- PASS — `checkpoint_reread`
- PASS — `answer_exact`
- PASS — `source_unchanged`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `only_work_mount_writable`

## Interpretation

This is an apparatus positive control. The checkpoint is required output behavior, not spontaneous external organization or evidence that reasoning caused the result.

[Machine-readable trajectory](./thinking-positive-control-20260820T202249Z.jsonl)

## Forensic reading

Thinking appeared in 11 of 11 model responses (9556 returned characters). The required checkpoint reread check was `True`.
