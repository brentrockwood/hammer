# Repeated retrieval apparatus calibration

Can the hardened adapter and context budget support exhaustive primitive retrieval at 10 and 50 files before the research pilot is frozen?

We generated deterministic fixed-size public records whose opaque filenames, labels, payloads, and creation order use separate seeded streams. Each stage used the same task text, a fresh model context and container, and the same persistent `/work`. The host scored exact sorted filenames and captured complete filesystem state before and after each task.

The run **failed**. 10 files: pass; 50 files: fail.

## Run specification

- Source: retroactively extracted from this report's paired public JSONL trajectory.
- Action budget: 39, 171
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":128,"seed":1006,"think":false}`

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

- Run: `retrieval-calibration-20260818T222648Z`
- Apparatus commit: `ccf99669e6ca65246e30b841ed1654ba1d7671cd`
- Model: `qwen3.6:35b`
- Image: `sha256:04cbfa8a944fb424730a8f77ea6cccf31c7e04d7ce31c1d7bbed1962b0747cde`
- Image source revision: `ccf99669e6ca65246e30b841ed1654ba1d7671cd`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":128,"seed":1006,"think":false}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 36 | 93558 | 909 | 4285 | 13.1% |
| 2 | 171 | 1846186 | 5886 | 21681 | 66.2% |

Primitive actions: `close` × 62, `getdents64` × 5, `openat` × 62, `read` × 60.

Rejected model actions: 17.

Model answers:
- Generation 1: `['r-3d28224cc1863c071f43', 'r-52b696b80ac67d3f13f8']`

## Checks

- PASS — `stage_10_exact_sorted_answer`
- PASS — `stage_10_directory_eof_observed`
- PASS — `stage_10_corpus_unchanged_by_model`
- PASS — `stage_10_network_disabled`
- PASS — `stage_10_read_only_root`
- PASS — `stage_10_no_init_process`
- PASS — `stage_10_only_work_mount_writable`
- FAIL — `stage_50_exact_sorted_answer`
- PASS — `stage_50_directory_eof_observed`
- PASS — `stage_50_corpus_unchanged_by_model`
- PASS — `stage_50_network_disabled`
- PASS — `stage_50_read_only_root`
- PASS — `stage_50_no_init_process`
- PASS — `stage_50_only_work_mount_writable`

## Interpretation

The 10-file stage passed the complete revised protocol. Qwen 3.6 observed explicit directory EOF, read all ten records, repaired one schema-invalid close action after the runner rejected it, closed its descriptors, and returned the exact two-name oracle. No malformed action reached the adapter.

At 50 records the model observed EOF, read all 50 records, closed the record and directory descriptors, and began answering at step 156 of 171. The 10-name JSON answer exceeded the configured 128-token response cap. Ollama reported `done_reason: length`; the runner rejected the truncated JSON and returned the error. Every subsequent answer attempt hit the same cap. Sixteen length-truncated responses consumed the remaining calls, so no complete answer was available for exact scoring.

The response cap, not the context window, was the binding apparatus limit. Peak live context was 21,681 of 32,768 tokens, or 66.2%. The model completed all required primitive reads and EOF observation before answering. One early truncated attempt also contained a non-target filename, while later truncated prefixes differed; because no complete answer exists, this run cannot establish what final exact array the model would have returned with sufficient output space.

The action-rejection mechanism behaved as designed: one schema error in generation 1 and sixteen truncations in generation 2 were recorded with no syscall and remained bounded by the step limit. No corpus byte changed and all isolation checks passed. Calibration seven should raise and predeclare the response cap while changing no task semantics. This run remains excluded from Pilot 1.

[Machine-readable trajectory](./retrieval-calibration-20260818T222648Z.jsonl)
