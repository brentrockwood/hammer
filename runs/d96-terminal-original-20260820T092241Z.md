# D96 blind-terminal wording study — original

Does explicitly stating that a blind terminal submission is irreversible change the D96 action trajectory or outcome?

One deterministic 96-record dependency fixture ran in one continuous context with no correctness feedback. This arm used the predeclared prompt wording, model, budget, and sampling seed.

The run **failed**. Terminal response: `done`; order validation: order needs exactly 96 nodes.

## Apparatus

- Run: `d96-terminal-original-20260820T092241Z`
- Apparatus commit: `db3ee65e17666df0373b2acc2330c4fcdd88fc23`
- Model: `qwen3.6:35b`
- Image: `sha256:ea2ccf104b79fa00b6b0dffd30b0165dc1d3e536fc534eee879e6ea886987dd6`
- Image source revision: `db3ee65e17666df0373b2acc2330c4fcdd88fc23`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":2048,"seed":3403,"think":false}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 104 | 707308 | 8209 | 15299 | 46.7% |

Primitive actions: `close` × 1, `getdents64` × 1, `openat` × 50, `read` × 48, `write` × 1.

Rejected model actions: 2.

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

[Machine-readable trajectory](./d96-terminal-original-20260820T092241Z.jsonl)

## Forensic reading

The model made 1 directory call(s), observed directory EOF: `False`, and opened 48 distinct fixture records for reading. It used 104 model calls and had 376 turns remaining at terminal submission.

The answer diagnostics were {"duplicate_path_count": 1, "known_dependency_order_violation_count": 12, "missing_fixture_node_count": 50, "nonempty_line_count": 48, "unique_line_count": 47, "unknown_path_count": 1}. These diagnostics supplement the ordinary short-circuit validator; they do not change the terminal score or provide model-visible feedback.
