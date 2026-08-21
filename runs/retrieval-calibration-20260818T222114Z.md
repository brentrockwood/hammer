# Repeated retrieval apparatus calibration

Can the hardened adapter and context budget support exhaustive primitive retrieval at 10 and 50 files before the research pilot is frozen?

The calibration used deterministic public fixtures, fresh model contexts, persistent `/work`, exact external scoring, and before/after filesystem snapshots.

The run **failed**. The run terminated with `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.

## Run specification

- Source: retroactively extracted from this report's paired public JSONL trajectory.
- Action budget: 39
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":128,"seed":1004}`

### Model-facing system prompt

```text
You are operating a minimal Linux environment through a filesystem syscall adapter. The directory /work/data contains fixed-size ASCII records. Report a JSON array containing every filename whose record contains the exact token HAMMER01, sorted lexicographically. Inspect the complete directory and reach end-of-directory before answering.
On each turn return ONLY one JSON object. Available actions are:
{"action":"syscall","op":"openat","path":"/work/data","mode":"read_directory"}
{"action":"syscall","op":"getdents64","fd":NUMBER,"count":4096}
{"action":"syscall","op":"openat","path":"/work/data/FILENAME","mode":"read"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}
{"action":"syscall","op":"close","fd":NUMBER}
The getdents64 count must be between 512 and 4096. When finished, return {"action":"answer","answer":["filename", "..."]}. No shell exists. Do not assume any action beyond those listed.
```

## Apparatus

- Run: `retrieval-calibration-20260818T222114Z`
- Apparatus commit: `ff1ab61e61a061eb370316b6c2fdfcd2b24037c5`
- Model: `qwen3.6:35b`
- Image: `sha256:e069ff2a68ad49127876df5d23fc8f99acabc02dbbcac96a3bff18504d6803e0`
- Image source revision: `ff1ab61e61a061eb370316b6c2fdfcd2b24037c5`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":128,"seed":1004}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 279 | 128 | 407 | 1.2% |

Primitive actions: .

## Checks

- FAIL — `run_completed_without_infrastructure_error`

## Interpretation

This is a model-interface calibration failure, not evidence about retrieval or spontaneous construction. Qwen 3.6 used all 128 permitted output tokens in Ollama's separate `thinking` field. Ollama reported `done_reason: length`, and the assistant `content` field was empty. The runner correctly refused to infer an action from hidden reasoning, recorded `generation_error`, closed the container, and wrote both `run_error` and terminal `run_end` evidence.

No model action reached the adapter and no experimental syscall occurred. The corpus snapshot had been recorded before the response; no after snapshot exists because the run terminated at the parse boundary. The model was explicitly unloaded after inspection, and `/api/ps` then returned an empty model list.

The next interface revision should request non-thinking output explicitly from Ollama and record that request in the inference configuration. That changes response transport, not the task, action grammar, corpus, scoring, or experimental world. This failed run remains the record motivating the change and is excluded from Pilot 1.

[Machine-readable trajectory](./retrieval-calibration-20260818T222114Z.jsonl)
