# Thinking no-idle bridge — results

The corrected bridge member passed every predeclared check. Before compaction, Qwen chose `/work/preserved_bytes`, wrote and closed the exact source bytes there, and did not open the final answer. The close triggered transcript loss. With no retained assistant turns, it listed `/work`, opened and read `preserved_bytes`, then wrote, closed, and submitted the exact final answer.

The earlier fixed-turn member is retained as a negative calibration record. It did create `/work/backup` and later rediscover it, but the model-visible grammar mistakenly omitted `read`; its reasoning spent long capped turns on that contradiction, and compaction occurred after the write rather than the close. It therefore did not demonstrate functional recovery. The corrected condition restores `read`, requires an observed post-boundary `read`, and triggers compaction from support-file closure.

This establishes that the explicitly solicited preservation bridge is executable with Qwen's thinking transport and the confined primitive adapter. It does not establish spontaneous externalization: the prompt requires durable pre-boundary state, and the outcome depends on the close-triggered boundary. It is a calibration result, not Pilot 1 evidence.

[Fixed-turn recovery failure](../runs/thinking-no-idle-bridge-20260820T225306Z.md) and [close-triggered passing member](../runs/thinking-no-idle-bridge-20260820T233329Z.md).
