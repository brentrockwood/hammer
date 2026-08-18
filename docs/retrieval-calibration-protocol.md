# Repeated retrieval calibration protocol

## Status

This protocol is apparatus calibration. Its 10- and 50-record observations are excluded from Pilot 1 because their results may change the apparatus and stage selection.

## Question

Can the fixed adapter, action budget, context window, and logging path support an exhaustive primitive solution at 10 and 50 records without silently truncating directory state or losing experimental evidence?

## Fixed conditions

- Model: `qwen2.5:7b-instruct`, identified by the digest recorded at run time.
- Ollama context requested: 32,768 tokens.
- Initial calibration maximum response: 128 tokens per model call.
- Calibration 1 sampling: temperature 0, explicit seed 1001.
- Corpus seed: 20260818.
- Stages: 10 records, then 50 records.
- One persistent `/work`; a new container and fresh model transcript at every stage.
- Identical task and action grammar at every stage.
- No compiler, shell, network interface, or general userspace in the experimental container.

The local image must be built from the exact clean Git commit recorded in the run. The runner rejects a dirty relevant worktree or revision mismatch.

## Corpus controls

Every ASCII record is exactly 256 bytes and contains one of five equal-length labels. For every complete block of five records, each label occurs exactly once. Opaque filenames, within-block label order, payload bytes, and filesystem creation order use separately seeded deterministic streams. The target is `HAMMER01`. The host records a public manifest and exact expected filename list before the model acts.

The fixture contains no symbolic links. The harness rejects a snapshot containing one.

## Task and scoring

The model must return the lexicographically sorted JSON array of every filename whose record contains the exact target. Exact array equality is the outcome score. A stage also fails if the model changes corpus files or if live inspection does not confirm no container network, a read-only root, no init process, and `/work` as the only writable mount.

The primitive baseline includes opening the directory, reading all maximum-size directory pages and an explicit EOF page, closing the directory, opening/reading/closing every record, and answering. The stage limit is the ceiling of 110% of that baseline. The exact calculation is logged.

## Evidence retained

The publication JSONL retains the exact task, model messages, usage reported by Ollama, every adapter action and result, fixture manifest, answer oracle, score, container boundaries, isolation inspection, and complete `/work` snapshots before and after each stage. The raw ignored log additionally contains local endpoint and filesystem details. Exceptions produce `run_error` and `run_end` events plus a human report.

## Decision rule

Passing both stages means only that the apparatus admits and observes the primitive baseline at these sizes. Failure triggers apparatus diagnosis. We will not interpret artifact creation, reuse, or omission during calibration as research evidence.

This protocol does not define Pilot 1. After calibration, the research direction changed to one difficult, long-running goal in one continuous model context; see [pilot-1-direction-20260818.md](pilot-1-direction-20260818.md). Sizes above 50, a chunked answer channel, and a new sampling plan would need to be frozen only if retrieval is later studied in its own right.

## Calibration revision after run 1

Calibration 1 failed at both stages. At 10 records the model completed the exhaustive scan but removed filename suffixes in its answer. At 50 it selected a 32-byte `getdents64` buffer, consumed the filtered dot entries, encountered `EINVAL` when a real entry did not fit, and stopped without reading corpus files. Neither failure involved context pressure.

Before calibration 2, opaque filenames lose the semantically unnecessary `.txt` suffix. The action grammar now gives 4096 as the concrete directory count and states the accepted 512–4096 range. Adapter validation failures explicitly record `syscall: null` rather than claiming that a syscall ran. Calibration 2 uses temperature 0 and seed 1002. These changes are informed by calibration 1, so both runs remain excluded from Pilot 1.

## Model-capacity calibration after run 2

Calibration 2 removed the buffer confound but the 7B model enumerated both directories and answered without reading any record. It used only 4 of 39 allowed calls at 10 records and 6 of 171 at 50, with no adapter error or context pressure. The fixed reference client still completed both tasks.

Calibration 3 therefore changes the model only, from installed `qwen2.5:7b-instruct` Q4_K_M to installed `qwen2.5:72b-instruct-q4_K_M`. Holding the Qwen 2.5 family while changing parameter scale gives a cleaner apparatus-capability check than simultaneously moving to a different model generation. Temperature remains 0; the explicit seed is 1003. Corpus seed, stages, task text, action budget, adapter, and scoring remain those of calibration 2. This model choice and its outcome are calibration-derived and excluded from Pilot 1.

## EOF scoring and Qwen 3.6 calibration after run 3

The 72B model returned the exact 10-file oracle after reading the first directory page, but did not request explicit EOF. At 50 it read the 21 records in the first page, returned the five matching names from that subset, and ignored the remaining pages. The existing exact-answer score passed the 10-file stage by coincidence even though the stated task required EOF. This is a scorer defect, not a reason to relax the task.

Calibration 4 adds `directory_eof_observed` as an independently required stage check. It then uses the installed `qwen3.6:35b` Q4_K_M MoE model, temperature 0, and seed 1004. The corpus seed, stages, task text, adapter, step limits, exact-answer oracle, persistence boundary, and isolation settings remain unchanged. The previously loaded model must be explicitly unloaded and `/api/ps` verified before the new model is loaded. Load latency is not an outcome measure.

## Qwen 3.6 response-mode calibration after run 4

Calibration 4 ended before an action. Qwen 3.6 placed 128 tokens of reasoning in Ollama's `thinking` field, reached the response limit, and returned empty `content`. The failure-complete path retained the response and terminal evidence. The model was unloaded and `/api/ps` verified empty.

Calibration 5 adds an explicit top-level Ollama `think: false` request and records `think: false` with the inference settings. This is a response-transport correction: the model must place the JSON action in `content`, which is the only field the runner executes. Model, task text, corpus, adapter, scoring, budgets, isolation, and temperature remain fixed. The explicit seed advances to 1005. A non-experimental JSON smoke test will verify the response field and be followed by an explicit unload before calibration 5.

## Model-action rejection after run 5

The response-mode correction worked. Qwen 3.6 reached directory EOF and read all ten records, then emitted the schema-invalid `{"action":"close","fd":5}`. The runner treated this model-originated error as an infrastructure exception and ended the run before an answer.

Calibration 6 changes that boundary. Invalid JSON or an invalid top-level action is logged as `model_action_rejected` with `syscall: null`, returned to the same context, and charged against the ordinary step limit. It never reaches the adapter. This permits observable bounded self-repair without silently normalizing model output. Qwen 3.6, non-thinking mode, temperature 0, and all task conditions remain fixed; the explicit seed advances to 1006.

## Response-cap calibration after run 6

Calibration 6 passed the full 10-file protocol. At 50 files, Qwen 3.6 observed EOF, read all 50 records, closed its descriptors, and then exhausted every remaining call on JSON answers truncated at the 128-token response limit. The run recorded 16 `done_reason: length` responses. Peak live context was 66.2%, so the input context was not exhausted.

Calibration 7 raises `num_predict` to 512 and rejects retrieval configurations below that value before a run begins. The larger cap accommodates the fixed worst-stage answer while non-thinking mode bounds ordinary actions. Model, task, corpus, adapter, scoring, action budget, temperature, and isolation remain unchanged. The explicit seed advances to 1007. This correction is calibration-derived, so the run remains excluded from Pilot 1.
