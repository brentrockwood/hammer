# Repeated retrieval apparatus calibration

Can the hardened adapter and context budget support exhaustive primitive retrieval at 10 and 50 files before the research pilot is frozen?

The calibration used deterministic public fixtures, fresh model contexts, persistent `/work`, exact external scoring, and before/after filesystem snapshots.

The run **failed**. The run terminated with `ValueError: model returned neither syscall nor answer`.

## Run specification

- Source: retroactively extracted from this report's paired public JSONL trajectory.
- Action budget: 39
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":128,"seed":1005,"think":false}`

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

- Run: `retrieval-calibration-20260818T222343Z`
- Apparatus commit: `7357e0461be1ed002501028258b3f6e7910f8130`
- Model: `qwen3.6:35b`
- Image: `sha256:293c00d80fed5e81e955e9c80522aa83adee7befae000cc8a040c07c773a905d`
- Image source revision: `7357e0461be1ed002501028258b3f6e7910f8130`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":128,"seed":1005,"think":false}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 24 | 46088 | 697 | 3616 | 11.0% |

Primitive actions: `getdents64` × 2, `openat` × 11, `read` × 10.

## Checks

- FAIL — `run_completed_without_infrastructure_error`

## Interpretation

The non-thinking response mode worked. Qwen 3.6 opened the directory, observed an explicit EOF page, and read all ten records. It kept each record descriptor open rather than closing it immediately. At step 24 it tried to begin cleanup with `{"action":"close","fd":5}` instead of the declared `{"action":"syscall","op":"close","fd":5}` envelope.

The runner parsed that JSON but classified it as neither a syscall nor an answer, raised `ValueError`, closed the container, and emitted the terminal failure record. No malformed action reached the adapter. The run stopped before the model answered, with 24 of 39 calls used and peak live context of 3,616 tokens. This is not action or context exhaustion, and it is not evidence about the retrieval answer.

The classification exposed another apparatus defect: a model-originated schema error is an observed behavior, not an infrastructure exception. It should consume one model step, be recorded as a rejected action with no syscall, and be returned to the same context so the model can repair it. The ordinary step limit already bounds repeated rejection. Calibration five remains excluded from Pilot 1 and motivates that change.

The model was explicitly unloaded after the run. No persistent artifact was created and no corpus byte was changed before termination.

[Machine-readable trajectory](./retrieval-calibration-20260818T222343Z.jsonl)
