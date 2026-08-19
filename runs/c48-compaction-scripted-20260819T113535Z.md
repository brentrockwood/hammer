# C48 declared-compaction scripted dry run

Can the fixed adapter preserve a compact external route through two transcript-compaction boundaries without weakening graph integrity?

A scripted reference client used the same network-disabled container and primitive adapter. It wrote a host-known route to a non-output scratch path before scanning the fixture, crossed the two fixed boundaries, reread that path, then wrote the final answer. This validates apparatus transport only; it is not a model trajectory.

The run **passed**. The scripted client used 165 turns; final-route validation: valid route.

## Apparatus

- Run: `c48-compaction-scripted-20260819T113535Z`
- Apparatus commit: `not recorded`
- Model: `not recorded`
- Image: `not recorded`
- Image source revision: `not recorded`
- Inference options: `{}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0.0% |

Primitive actions: `close` × 54, `getdents64` × 3, `openat` × 54, `read` × 51, `write` × 2.

Rejected model actions: 0.

Model answers:
- Generation 1: `done`

## Checks

- PASS — `both_checkpoints_observed`
- PASS — `answer_absent_at_checkpoints`
- PASS — `answer_valid`
- PASS — `source_unchanged`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `no_init_process`
- PASS — `only_work_mount_writable`
- PASS — `within_budget`

## Interpretation

The dry run checks fixture generation, state snapshots, compaction-event recording, scratch-file persistence, final validation, and isolation. It says nothing about whether a model would construct or use the reference representation.

[Machine-readable trajectory](./c48-compaction-scripted-20260819T113535Z.jsonl)
