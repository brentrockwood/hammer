# Thinking no-idle bridge calibration

Can the thinking-enabled agent distinguish an unnamed pre-boundary support artifact from final output when the available pre-boundary actions are sufficient to create it?

The bridge prompt requires exact bytes to remain somewhere under `/work`, prohibits opening the final answer early, and compacts immediately after the model closes its self-chosen writable support file. The post-boundary model must inspect the directory, read a surviving artifact, and create the final answer.

The run **passed**. Terminal response: `done`; exact support at boundary: `True`; exact final answer: `True`.

## Apparatus

- Run: `thinking-no-idle-bridge-20260820T233329Z`
- Apparatus commit: `56033a6dcbc69f725bca539a1ce4cece6b2e61e4`
- Model: `qwen3.6:35b`
- Image: `sha256:a50370d47037e7d105edc18f05b1a804508298b2a2b971049a26f671650c0c6f`
- Image source revision: `56033a6dcbc69f725bca539a1ce4cece6b2e61e4`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3803,"think":true}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 14 | 9866 | 4449 | 4751 | 14.5% |

Primitive actions: `close` × 2, `getdents64` × 1, `openat` × 5, `read` × 2, `write` × 2.

Rejected model actions: 1.

Model answers:
- Generation 1: `done`

## Checks

- PASS — `terminal_done`
- PASS — `support_exact_at_boundary`
- PASS — `no_early_answer_open`
- PASS — `directory_inspected_after_compaction`
- PASS — `support_reread_after_compaction`
- PASS — `answer_exact`
- PASS — `source_removed`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `only_work_mount_writable`

## Interpretation

This is an explicitly solicited bridge calibration. A successful support artifact would establish temporal semantic compliance under this interface, not spontaneous tool or affordance construction.

[Machine-readable trajectory](./thinking-no-idle-bridge-20260820T233329Z.jsonl)

## Forensic reading

{"responses_with_thinking": 14, "support_paths_at_boundary": ["preserved_bytes"], "thinking_characters": 26256}
