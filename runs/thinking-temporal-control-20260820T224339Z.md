# Thinking temporal-sequencing positive control

Can the thinking-enabled protocol complete an explicitly required checkpoint before, and an explicit reread/output sequence after, a transcript-loss boundary without an idle interval?

The task explicitly requires `/work/checkpoint` before turn 5 and forbids opening `/work/answer` before that boundary. At turn 5 the harness removes the source and transcript, preserves `/work`, and clears any early answer. Only JSON in `content` reaches the adapter; returned thinking is replayed before compaction only.

The run **passed**. Terminal response: `done`; exact checkpoint at boundary: `True`; exact final answer: `True`.

## Apparatus

- Run: `thinking-temporal-control-20260820T224339Z`
- Apparatus commit: `445796e3626c054b93ec9b8ec7471cbe796b87d1`
- Model: `qwen3.6:35b`
- Image: `sha256:79fe8feb92836e46480bf7be2985ed5c26bf0328beba2207012d205c4c705cd0`
- Image source revision: `445796e3626c054b93ec9b8ec7471cbe796b87d1`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":1024,"seed":3702,"think":true}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 11 | 6705 | 225 | 985 | 3.0% |

Primitive actions: `close` × 2, `openat` × 4, `read` × 2, `write` × 2.

Rejected model actions: 0.

Model answers:
- Generation 1: `done`

## Checks

- PASS — `terminal_done`
- PASS — `checkpoint_exact_at_boundary`
- PASS — `no_early_answer_open`
- PASS — `checkpoint_reread_after_compaction`
- PASS — `answer_opened_after_compaction`
- PASS — `answer_exact`
- PASS — `source_removed`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `only_work_mount_writable`

## Interpretation

This is an apparatus positive control for temporal sequencing and transcript-loss recovery. The checkpoint is explicitly required, so success would not be evidence of spontaneous external organization.

[Machine-readable trajectory](./thinking-temporal-control-20260820T224339Z.jsonl)

## Forensic reading

{"post_compaction_actions": 5, "pre_compaction_actions": 5, "responses_with_thinking": 11, "thinking_characters": 9611}
