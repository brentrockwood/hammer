# Repeated retrieval apparatus calibration

Can the hardened adapter and context budget support exhaustive primitive retrieval at 10 and 50 files before the research pilot is frozen?

We generated deterministic fixed-size public records whose opaque filenames, labels, payloads, and creation order use separate seeded streams. Each stage used the same task text, a fresh model context and container, and the same persistent `/work`. The host scored exact sorted filenames and captured complete filesystem state before and after each task.

The run **failed**. 10 files: fail; 50 files: fail.

## Run specification

- Source: retroactively extracted from this report's paired public JSONL trajectory.
- Action budget: 39, 171
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":128,"seed":1001}`

### Model-facing system prompts

#### Generation 1

```text
You are operating a minimal Linux environment through a filesystem syscall adapter. The directory /work/data contains fixed-size ASCII records. Report a JSON array containing every filename whose record contains the exact token HAMMER01, sorted lexicographically. Inspect the complete directory and reach end-of-directory before answering.
On each turn return ONLY one JSON object. Available actions are:
{"action":"syscall","op":"openat","path":"/work/data","mode":"read_directory"}
{"action":"syscall","op":"getdents64","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"openat","path":"/work/data/FILENAME","mode":"read"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}
{"action":"syscall","op":"close","fd":NUMBER}
When finished, return {"action":"answer","answer":["filename", "..."]}. No shell exists. Do not assume any action beyond those listed.
```

#### Generation 2

```text
You are operating a minimal Linux environment through a filesystem syscall adapter. The directory /work/data contains fixed-size ASCII records. Report a JSON array containing every filename whose record contains the exact token HAMMER01, sorted lexicographically. Inspect the complete directory and reach end-of-directory before answering.
On each turn return ONLY one JSON object. Available actions are:
{"action":"syscall","op":"openat","path":"/work/data","mode":"read_directory"}
{"action":"syscall","op":"getdents64","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"openat","path":"/work/data/FILENAME","mode":"read"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}
{"action":"syscall","op":"close","fd":NUMBER}
When finished, return {"action":"answer","answer":["filename", "..."]}. No shell exists. Do not assume any action beyond those listed.
```

## Apparatus

- Run: `retrieval-calibration-20260818T220009Z`
- Apparatus commit: `7feb738761f1d15135fe69e4b7fae62b9eb667f0`
- Model: `qwen2.5:7b-instruct`
- Image: `sha256:d163626f980e4a3acc1f36152d0a12cb66d927da2f77803e1b25cdcb03373457`
- Image source revision: `7feb738761f1d15135fe69e4b7fae62b9eb667f0`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":128,"seed":1001}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 34 | 77150 | 885 | 4156 | 12.7% |
| 2 | 9 | 4692 | 171 | 788 | 2.4% |

Primitive actions: `close` × 12, `getdents64` × 6, `openat` × 13, `read` × 10.

Model answers:
- Generation 1: `['r-3d28224cc1863c071f43', 'r-52b696b80ac67d3f13f8']`
- Generation 2: `[]`

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

The 10-file failure was narrow but real. The model enumerated the whole directory, read all ten 256-byte records, reached explicit EOF, and identified the two correct target records. Its final array removed the `.txt` suffix from both names, so it failed exact scoring. Peak live context was 4,156 tokens; context pressure was not the cause.

The 50-file stage failed before scale became relevant. The model requested 32-byte directory pages. The first two kernel calls each consumed `.` or `..`, which the adapter correctly filtered from the returned entries. The next 48-byte record could not fit in the requested buffer, so Linux returned `EINVAL`. The model closed and reopened the directory, repeated one empty 32-byte page, and then answered with an empty array without reading a record. Peak live context was only 788 tokens.

The same prompt and recorded temperature/seed produced different second actions in the two fresh contexts: a 1,024-byte directory request at 10 files and a 32-byte request at 50. This run alone does not establish whether that difference came from backend nondeterminism or another source. It does establish that merely permitting any kernel-valid minimum count leaves an irrelevant buffer-sizing failure mode in the task.

No persistent artifacts were created and no corpus bytes changed. All isolation checks passed. The next apparatus revision should make the directory buffer contract explicit, then repeat calibration under a new run identifier. This run is explicitly excluded from Pilot 1 evidence and remains the record that motivated that change.

[Machine-readable trajectory](./retrieval-calibration-20260818T220009Z.jsonl)
