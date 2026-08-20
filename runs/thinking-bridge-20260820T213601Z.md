# Thinking external-state ladder — bridge

Does this thinking-enabled condition leave and later use filesystem state across a declared source-removal and transcript-loss boundary?

The public source is removed and the model transcript compacted after turn 8. The bridge rung explicitly requests preservation without naming a representation; the goal-only rung omits that sentence. Early terminal responses are rejected.

The run **failed**. Terminal response: `None`; exact final answer: `False`.

## Apparatus

- Run: `thinking-bridge-20260820T213601Z`
- Apparatus commit: `a34538e788e73fc830a72b0244001ea5734f8e50`
- Model: `qwen3.6:35b`
- Image: `sha256:394a459bf226efd92a4987faa2fdb353630ce3714be5bcb65518c118e8321a0e`
- Image source revision: `a34538e788e73fc830a72b0244001ea5734f8e50`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3611,"think":true}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 28 | 26621 | 78007 | 5629 | 17.2% |

Primitive actions: `close` × 1, `openat` × 5, `read` × 1, `write` × 1.

Rejected model actions: 20.

## Checks

- FAIL — `terminal_done`
- FAIL — `answer_exact`
- PASS — `source_removed`
- FAIL — `support_file_at_compaction`
- FAIL — `support_reread_after_compaction`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `only_work_mount_writable`

## Interpretation

This is a ladder calibration. The bridge rung explicitly solicits preservation; the goal-only rung remains one descriptive observation and cannot establish spontaneous affordance creation or causal effects.

[Machine-readable trajectory](./thinking-bridge-20260820T213601Z.jsonl)

## Forensic reading

All 28 responses carried a non-empty returned `thinking` field (298,249 characters in total). The model executed eight primitive actions at steps 1, 2, 3, 4, 6, 8, 9, and 21. Step 9 was one post-compaction action; step 21 opened `/work/answer`, but no later action wrote it. The remaining 20 turns were rejected because `content` contained no executable action.

Nineteen of 28 responses ended with `done_reason:length` at the 4,096-token cap. Peak live context was 5,629 of 32,768 tokens (17.2%), so the observed response-cap exhaustion is not ordinary loaded-context exhaustion. The wider cap delayed the empty-`content` pattern and allowed two isolated post-boundary actions, but did not produce a support file, its reread, a completed answer artifact, or a terminal submission.

This failed bridge member is a response-policy calibration result. It does not test the intended bridge-versus-goal-only preservation contrast cleanly, and it does not support a conclusion about whether the model would externalize useful state under an adequate action protocol. The goal-only partner was not started: with this bridge member still blocked by the action-channel condition, it would not make the intended comparison interpretable.
