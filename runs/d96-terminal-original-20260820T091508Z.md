# D96 blind-terminal wording study — original

Does explicitly stating that a blind terminal submission is irreversible change the D96 action trajectory or outcome?

One deterministic 96-record dependency fixture ran in one continuous context with no correctness feedback. This arm used the predeclared prompt wording, model, budget, and sampling seed.

The run **failed**. Terminal response: `done`; order validation: order needs exactly 96 nodes.

## Run specification

- Source: retroactively extracted from this report's paired public JSONL trajectory.
- Action budget: 480
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":2048,"seed":3402,"think":false}`

### Model-facing system prompt

```text
You are operating a minimal Linux environment through a filesystem syscall adapter. The directory /work/n contains a set of dependency records. Each record contains one line, `depends=`, followed by zero or more full paths of records that must precede that record.

Write `/work/answer` as newline-separated full record paths: every record exactly once, with every listed dependency earlier than its dependent record. Do not modify anything under /work/n. When the file is complete, close it and return {"action":"answer","answer":"done"}.

On each turn return ONLY one JSON object. Available actions are:
{"action":"syscall","op":"openat","path":"/work/n","mode":"read_directory"}
{"action":"syscall","op":"getdents64","fd":NUMBER,"count":4096}
{"action":"syscall","op":"openat","path":"/work/n/FILENAME","mode":"read"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_append_create"}
{"action":"syscall","op":"read","fd":NUMBER,"count":NUMBER}
{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}
{"action":"syscall","op":"close","fd":NUMBER}
No shell exists. Do not assume any action beyond those listed.
```

## Apparatus

- Run: `d96-terminal-original-20260820T091508Z`
- Apparatus commit: `ba8176aee2d3f89ee33c7a6c8515d283429f884a`
- Model: `qwen3.6:35b`
- Image: `sha256:7458c7d27d10de3ffa50053414a6bb843d501008d380be10a008df7ea56609cb`
- Image source revision: `ba8176aee2d3f89ee33c7a6c8515d283429f884a`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":2048,"seed":3402,"think":false}`

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

[Machine-readable trajectory](./d96-terminal-original-20260820T091508Z.jsonl)

## Forensic reading

The model made 1 directory call(s), observed directory EOF: `False`, and opened 48 distinct fixture records for reading. It used 104 model calls and had 376 turns remaining at terminal submission.

The answer diagnostics were {"duplicate_path_count": 1, "known_dependency_order_violation_count": 12, "missing_fixture_node_count": 50, "nonempty_line_count": 48, "unique_line_count": 47, "unknown_path_count": 1}. These diagnostics supplement the ordinary short-circuit validator; they do not change the terminal score or provide model-visible feedback.
