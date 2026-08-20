# Thinking no-idle bridge — results

The corrected bridge member passed every predeclared check. Before compaction, Qwen chose `/work/preserved_bytes`, wrote and closed the exact source bytes there, and did not open the final answer. The close triggered transcript loss. With no retained assistant turns, it listed `/work`, opened and read `preserved_bytes`, then wrote, closed, and submitted the exact final answer.

The earlier fixed-turn member is retained as a negative calibration record. It did create `/work/backup` and later rediscover it, but the model-visible grammar mistakenly omitted `read`; its reasoning spent long capped turns on that contradiction, and compaction occurred after the write rather than the close. It therefore did not demonstrate functional recovery. The corrected condition restores `read`, requires an observed post-boundary `read`, and triggers compaction from support-file closure.

This establishes that the explicitly solicited preservation bridge is executable with Qwen's thinking transport and the confined primitive adapter. It does not establish spontaneous externalization: the prompt requires durable pre-boundary state, and the outcome depends on the close-triggered boundary. It is a calibration result, not Pilot 1 evidence.

[Fixed-turn recovery failure](../runs/thinking-no-idle-bridge-20260820T225306Z.md) and [close-triggered passing member](../runs/thinking-no-idle-bridge-20260820T233329Z.md).

## Non-thinking descriptive member

After a one-shot trigger correction, the `think:false` member also passed every check. It chose `/work/message_copy`, closed it to trigger compaction, enumerated `/work`, reread the file, created the exact answer, closed it, and submitted `done` in 15 calls. Ollama returned no thinking characters and 380 completion tokens. The same task's thinking-enabled member used 14 calls, returned 26,256 thinking characters, and used 4,449 completion tokens.

This is not a causal comparison: it uses a fresh seed, and the earlier non-thinking seed-3804 record exposed a harness trigger defect rather than a model outcome. It does show that this small, explicitly specified bridge does not require exposed reasoning to complete under the corrected apparatus.

[Non-thinking passing record](../runs/thinking-no-idle-bridge-20260820T235130Z.md).
