# Retrieval apparatus calibration — 2026-08-18

## Outcome

The Hammer apparatus is ready to support and observe the 10- and 50-record retrieval task. This does not freeze repeated retrieval as Pilot 1.

The final calibration admitted the complete primitive path without a binding harness limit: Qwen 3.6 enumerated every directory page, observed EOF, read all 50 records, closed its descriptors, and returned a complete answer within both action and context budgets. Its answer contained one false positive and omitted one true target. That is a clean model-level error under calibrated conditions, not a successful research result; every run in this sequence is excluded from Pilot 1 because the sequence informed the apparatus.

## Calibration sequence

| Run | Frozen revision | Model and seed | Result | Decision it motivated |
|---|---|---|---|---|
| [report](../runs/retrieval-calibration-20260818T220009Z.md) · [trajectory](../runs/retrieval-calibration-20260818T220009Z.jsonl) | `7feb738` | Qwen 2.5 7B, 1001 | Exhaustive 10-file scan returned filename stems; 50-file stage stopped after a 32-byte directory-buffer error. | Remove suffix normalization as a confound and state a valid directory-buffer contract. |
| [report](../runs/retrieval-calibration-20260818T220424Z.md) · [trajectory](../runs/retrieval-calibration-20260818T220424Z.jsonl) | `9d31b82` | Qwen 2.5 7B, 1002 | Reached directory EOF but read no records at either size, returning `[""]`. | Treat the 7B policy as a likely capability limit; check a larger same-family model. |
| [report](../runs/retrieval-calibration-20260818T220615Z.md) · [trajectory](../runs/retrieval-calibration-20260818T220615Z.jsonl) | `5d40310` | Qwen 2.5 72B, 1003 | Exact 10-file answer and partial 50-file answer, both without explicit EOF. | Add EOF as an independently scored requirement. |
| [report](../runs/retrieval-calibration-20260818T222114Z.md) · [trajectory](../runs/retrieval-calibration-20260818T222114Z.jsonl) | `ff1ab61` | Qwen 3.6 35B MoE, 1004 | Used all 128 output tokens in Ollama's `thinking` field; empty executable content. | Request and record non-thinking response mode. |
| [report](../runs/retrieval-calibration-20260818T222343Z.md) · [trajectory](../runs/retrieval-calibration-20260818T222343Z.jsonl) | `7357e04` | Qwen 3.6 35B MoE, 1005 | Reached EOF and read all ten records, then emitted a schema-invalid close action that the runner treated as fatal. | Record malformed model actions as bounded rejections and permit self-repair. |
| [report](../runs/retrieval-calibration-20260818T222648Z.md) · [trajectory](../runs/retrieval-calibration-20260818T222648Z.jsonl) | `ccf9966` | Qwen 3.6 35B MoE, 1006 | Full 10-file pass; full 50-file scan could not fit its answer in 128 output tokens. | Require a 512-token response allowance for 10/50 calibration. |
| [report](../runs/retrieval-calibration-20260818T223911Z.md) · [trajectory](../runs/retrieval-calibration-20260818T223911Z.jsonl) | `e0291e9` | Qwen 3.6 35B MoE, 1007 | Full 10-file pass; complete 50-file trajectory with one false positive and one false negative. | Close 10/50 apparatus calibration; do not change the task to accommodate a clean model error. |

Each run was committed and pushed before the apparatus changed.

## What is now controlled

- The static scratch-image agent confines opens beneath `/work` with one `openat2` call and refuses symlink traversal.
- Model-visible accepted operations map to one filesystem syscall; adapter and model-schema rejections explicitly record that no syscall ran.
- Directory descriptors paginate until explicit EOF instead of hiding open/read/close work in a compound action.
- Control descriptors are unavailable to the model. The root is read-only, `/work` is the only writable mount, no init process is injected, capabilities are dropped, and the container has no network.
- JSON strings preserve the declared ASCII protocol, including quotes, backslashes, tabs, and newlines.
- A reference client completes 10- and 50-record exhaustive scans and forces directory pagination.
- Corpus names, labels, payloads, and creation order are deterministic from separate recorded streams; record sizes and label frequencies are controlled.
- The host records exact oracles, model responses, usage, action requests, syscall results, model-action rejection, before/after persistent state, isolation inspection, source revision, image revision, and terminal failure.
- Scientific runs refuse a dirty relevant worktree or an image/source revision mismatch.

The trace is complete at the adapter boundary, not kernel-wide. Hidden container startup and the agent's initial `/work` open remain substrate activity outside the model trajectory.

## What the final run means

The final 50-file error should not be repaired by another apparatus accommodation. The record labeled `r-1b2d8427b1b0213fb7ce` contained `MALLET01` but appeared in the answer; `r-920f9d2c1318f501655e` contained `HAMMER01` but was omitted. The model had read both bytes. It had also observed EOF, remained inside its action budget, used 57.2% of the requested context, produced a complete non-truncated response, and encountered no stage-two schema rejection.

That makes the error useful for understanding the apparatus but not publishable pilot evidence. We know the primitive retrieval baseline is feasible at 50 and not perfectly reliable in one Qwen 3.6 trajectory. Any future retrieval study must predeclare repetitions and seeds so it measures a distribution rather than promoting one path.

## Subsequent research-design correction

The proposed next step had been to scale repeated retrieval while replacing the model context at each stage. That design contained a more fundamental problem than answer transport: the model was given no reason to expect another task. Persistent infrastructure might be useful from the experimenter's perspective while remaining irrational from the agent's. Repetition outside the model's context does not create a model-visible future.

Pilot 1 is therefore being redesigned around one difficult, long-running goal in one continuous context, where intermediate external state can help solve the current task. The prompt will not prescribe that state. A known-future, cross-context persistence condition remains a separate later experiment because knowledge of future work is itself a treatment variable. The change is recorded in [pilot-1-direction-20260818.md](pilot-1-direction-20260818.md).

The final JSON answer would still scale linearly if retrieval were extended beyond 50. A bounded out-of-band `answer_part` / `answer_done` channel is a reasonable future apparatus improvement, but it is no longer a prerequisite for Pilot 1 unless the selected long-horizon task produces a large final result. No Pilot 1 observation has been collected.
