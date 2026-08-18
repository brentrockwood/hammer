# Repeated retrieval apparatus calibration

Can the hardened adapter and context budget support exhaustive primitive retrieval at 10 and 50 files before the research pilot is frozen?

We generated deterministic fixed-size public records whose opaque filenames, labels, payloads, and creation order use separate seeded streams. Each stage used the same task text, a fresh model context and container, and the same persistent `/work`. The host scored exact sorted filenames and captured complete filesystem state before and after each task.

The run **failed**. 10 files: pass; 50 files: fail.

## Apparatus

- Run: `retrieval-calibration-20260818T220615Z`
- Apparatus commit: `5d403100f2358fb18c8d3575fb929d9a61ec786b`
- Model: `qwen2.5:72b-instruct-q4_K_M`
- Image: `sha256:437aba04848fd61d0ecfc4967c109bbe6f519fef872262fbcee9dddf776bd4ed`
- Image source revision: `5d403100f2358fb18c8d3575fb929d9a61ec786b`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":128,"seed":1003}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 33 | 73148 | 849 | 4081 | 12.5% |
| 2 | 66 | 284151 | 1726 | 8092 | 24.7% |

Primitive actions: `close` × 31, `getdents64` × 2, `openat` × 33, `read` × 31.

Model answers:
- Generation 1: `['r-3d28224cc1863c071f43', 'r-52b696b80ac67d3f13f8']`
- Generation 2: `['r-0005abc89bf0d9426bb0', 'r-3d28224cc1863c071f43', 'r-52b696b80ac67d3f13f8', 'r-c98f84608f45782ca8b6', 'r-920f9d2c1318f501655e']`

## Checks

- PASS — `stage_10_exact_sorted_answer`
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

The 72B model followed the primitive record-reading path that the 7B calibrations did not. At 10 records it read all ten and returned the exact two-name oracle in 33 calls. At 50 records it read all 21 records present in the first directory page, returned the five target names among that subset, and omitted the five targets on later pages.

Neither generation requested another `getdents64` call after the first non-EOF page. The 10-file exact score passed only because all ten entries happened to fit in that page. It therefore violated the task's explicit instruction to reach end-of-directory even though its answer was complete. The current machine score checks exact answer but does not independently require observed EOF; that is a scoring defect discovered by this calibration. The 50-file exact failure made the run fail overall, but the 10-file check is too permissive and must not be cited as full protocol compliance.

At 50 records the model stopped after 66 of 171 available calls with peak live context of 8,092 tokens, 24.7% of the requested window. Action and context exhaustion were not responsible. It did not encounter an adapter error. No persistent artifact was created, no corpus byte changed, and all isolation checks passed.

The evidence supports a narrow conclusion: the fixed apparatus admits competent multi-step record retrieval, but the scorer must require an explicit EOF observation before Pilot 1. Model load and wall-clock time are operational details here, not outcome measures. This run is excluded from Pilot 1 and remains paired with the exact scoring caveat that it revealed.

[Machine-readable trajectory](./retrieval-calibration-20260818T220615Z.jsonl)
