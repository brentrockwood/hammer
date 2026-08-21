# Repeated retrieval apparatus calibration

Can the hardened adapter and context budget support exhaustive primitive retrieval at 10 and 50 files before the research pilot is frozen?

We generated deterministic fixed-size public records whose opaque filenames, labels, payloads, and creation order use separate seeded streams. Each stage used the same task text, a fresh model context and container, and the same persistent `/work`. The host scored exact sorted filenames and captured complete filesystem state before and after each task.

The run **failed**. 10 files: fail; 50 files: fail.

## Run specification

- Source: retroactively extracted from this report's paired public JSONL trajectory.
- Action budget: 39, 171
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":128,"seed":1002}`

### Model-facing system prompts

#### Generation 1

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

#### Generation 2

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

- Run: `retrieval-calibration-20260818T220424Z`
- Apparatus commit: `9d31b82061d58a44437537d0f1ab56e282f7e50b`
- Model: `qwen2.5:7b-instruct`
- Image: `sha256:aca464084f22a93e6e25f9afc78f06f3a311438eb29360ea359addf084ae7dc8`
- Image source revision: `9d31b82061d58a44437537d0f1ab56e282f7e50b`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":128,"seed":1002}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 1946 | 80 | 720 | 2.2% |
| 2 | 6 | 6191 | 130 | 1735 | 5.3% |

Primitive actions: `getdents64` × 6, `openat` × 2.

Model answers:
- Generation 1: `['']`
- Generation 2: `['']`

## Checks

- FAIL — `stage_10_exact_sorted_answer`
- PASS — `stage_10_corpus_unchanged_by_model`
- PASS — `stage_10_network_disabled`
- PASS — `stage_10_read_only_root`
- PASS — `stage_10_no_init_process`
- PASS — `stage_10_only_work_mount_writable`
- FAIL — `stage_50_exact_sorted_answer`
- PASS — `stage_50_corpus_unchanged_by_model`
- PASS — `stage_50_network_disabled`
- PASS — `stage_50_read_only_root`
- PASS — `stage_50_no_init_process`
- PASS — `stage_50_only_work_mount_writable`

## Interpretation

The directory contract change removed calibration 1's buffer-size failure. At 10 records the model opened the directory, requested one 1,024-byte page, requested and received explicit EOF, and then answered `[""]`. At 50 records it consumed three 1,024-byte data pages, requested explicit EOF, and returned the same empty-string answer. It never opened or read a corpus record in either stage.

This was not action-budget exhaustion: generation 1 used 4 of 39 allowed calls and generation 2 used 6 of 171. Peak live context was 720 and 1,735 tokens respectively, at most 5.3% of the requested context. No adapter errors occurred. No persistent artifact was created, no corpus byte changed, and all isolation checks passed.

The surprising result is that changing only the recorded sampling seed from 1001 to 1002 at temperature 0 coincided with a qualitatively different policy. Calibration 1 at 10 records read all ten records; calibration 2 at the same size read none. This does not by itself show that Ollama ignored the seed or that the backend is nondeterministic, because the apparatus and filename format also changed between runs. It does show that one nominally deterministic 7B trajectory is not a sufficient readiness test.

The fixed adapter now admits the reference solution and recorded every observed action, so the next calibration decision is model selection and repetition rather than another task-specific relaxation. This run is excluded from Pilot 1 evidence and will remain paired with its exact negative trajectory.

[Machine-readable trajectory](./retrieval-calibration-20260818T220424Z.jsonl)
