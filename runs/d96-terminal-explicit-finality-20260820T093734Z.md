# D96 blind-terminal wording study — explicit-finality

Does explicitly stating that a blind terminal submission is irreversible change the D96 action trajectory or outcome?

One deterministic 96-record dependency fixture ran in one continuous context with no correctness feedback. This arm used the predeclared prompt wording, model, budget, and sampling seed.

The run **failed**. Terminal response: `done`; order validation: order needs exactly 96 nodes.

## Apparatus

- Run: `d96-terminal-explicit-finality-20260820T093734Z`
- Apparatus commit: `3a6be63dd702767b51694fcbb1aef2fca8a70137`
- Model: `qwen3.6:35b`
- Image: `sha256:b1b3ec988eb56c44318e5e4abf98f506e321aae1cf7b3f0f2c4408ce1587b690`
- Image source revision: `3a6be63dd702767b51694fcbb1aef2fca8a70137`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":2048,"seed":3411,"think":false}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 49 | 158407 | 4366 | 8186 | 25.0% |

Primitive actions: `close` × 1, `getdents64` × 1, `openat` × 23, `read` × 21, `write` × 1.

Rejected model actions: 1.

Model answers:
- Generation 1: `done`

## Checks

- PASS — `terminal_done`
- FAIL — `answer_valid`
- PASS — `source_unchanged`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `no_init_process`
- PASS — `only_work_mount_writable`

## Interpretation

This is one member of a matched terminal-semantics calibration. It does not establish a causal effect, a general model property, or useful external organization on its own.

[Machine-readable trajectory](./d96-terminal-explicit-finality-20260820T093734Z.jsonl)

## Forensic reading

The model made 1 directory call(s), observed directory EOF: `False`, and opened 21 distinct fixture records for reading. It used 49 model calls and had 431 turns remaining at terminal submission.

The answer diagnostics were {"duplicate_path_count": 0, "known_dependency_order_violation_count": 17, "missing_fixture_node_count": 54, "nonempty_line_count": 42, "unique_line_count": 42, "unknown_path_count": 0}. These diagnostics supplement the ordinary short-circuit validator; they do not change the terminal score or provide model-visible feedback.
