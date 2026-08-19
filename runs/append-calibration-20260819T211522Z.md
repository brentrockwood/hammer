# Reopenable append affordance calibration

Does the opt-in append mode preserve a file through close and reopen while retaining the fixed isolation boundary?

A scripted client, not a model, wrote one line with truncate-on-create, closed the descriptor, reopened the same path with append enabled, wrote a second line, then reopened it read-only.

The run **passed**. The recovered bytes were exactly the two-line sequence.

## Apparatus

- Run: `append-calibration-20260819T211522Z`
- Apparatus commit: `051cc60816bf149d649f5aafcaf91452093cc14d`
- Model: `not recorded`
- Image: `sha256:99f892d5c0fb4b330d452e69c65b3114004bc51b55bc4aa1af3879ffaa1802bd`
- Image source revision: `051cc60816bf149d649f5aafcaf91452093cc14d`
- Inference options: `{}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0.0% |

Primitive actions: `close` × 3, `openat` × 3, `read` × 1, `write` × 2.

Rejected model actions: 0.

## Checks

- PASS — `scripted_sequence_completed`
- PASS — `append_round_trip`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `no_init_process`
- PASS — `only_work_mount_writable`

## Interpretation

This calibrates one explicit filesystem primitive. It does not show that a model will select, reuse, or benefit from append.

[Machine-readable trajectory](./append-calibration-20260819T211522Z.jsonl)
