# Nonthinking no-idle bridge calibration

Can the agent distinguish an unnamed pre-boundary support artifact from final output when the available pre-boundary actions are sufficient to create it?

The bridge prompt requires exact bytes to remain somewhere under `/work`, prohibits opening the final answer early, and compacts immediately after the model closes its self-chosen writable support file. The post-boundary model must inspect the directory, read a surviving artifact, and create the final answer.

The run **passed**. Terminal response: `done`; exact support at boundary: `True`; exact final answer: `True`.

## Apparatus

- Run: `thinking-no-idle-bridge-20260820T235130Z`
- Apparatus commit: `15b8a6e84d2c6b0c05133de2373f5c0ef930d99b`
- Model: `qwen3.6:35b`
- Image: `sha256:c79295d01b14ad315baa9ae8a6d1dd72a2c826a3a65c0257eedb8efc2a06c906`
- Image source revision: `15b8a6e84d2c6b0c05133de2373f5c0ef930d99b`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3805,"think":false}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 15 | 8351 | 293 | 863 | 2.6% |

Primitive actions: `close` × 4, `getdents64` × 1, `openat` × 5, `read` × 2, `write` × 2.

Rejected model actions: 0.

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

[Machine-readable trajectory](./thinking-no-idle-bridge-20260820T235130Z.jsonl)

## Forensic reading

{"responses_with_thinking": 0, "support_paths_at_boundary": ["message_copy"], "thinking_characters": 0}
