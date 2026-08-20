# D96 continuous dependency-ordering pilot candidate

When a current dependency-ordering goal is large enough to make interim organization potentially useful, what does the model construct and use?

A deterministic 96-record dependency DAG ran in one network-disabled scratch container with one continuous model context. The prompt specified only a valid final topological order; append was available but no intermediate representation was requested. The host recorded complete adapter-visible actions and filesystem lineage.

The run **failed**. Terminal response: `done`; order validation: order needs exactly 96 nodes.

## Apparatus

- Run: `d96-pilot-candidate-20260820T004248Z`
- Apparatus commit: `99143a92d6530fd721573d3e6d993ac62430c909`
- Model: `qwen3.6:35b`
- Image: `sha256:b399ef6cea532e77fa206966c2d211ebc7328410973a493a5fce541f1055d51e`
- Image source revision: `99143a92d6530fd721573d3e6d993ac62430c909`
- Inference options: `{"temperature":0.0,"num_ctx":65536,"num_predict":2048,"seed":3401,"think":false}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 104 | 707308 | 8209 | 15299 | 23.3% |

Primitive actions: `close` × 1, `getdents64` × 1, `openat` × 50, `read` × 48, `write` × 1.

Rejected model actions: 2.

Model answers:
- Generation 1: `done`

## Forensic reading

The model enumerated `/work/n` once, read 48 distinct dependency records, and then submitted the required output after 104 model calls. It had 376 turns remaining. The only created file was `/work/answer`; no non-output support file, append request, or reread of model-created state occurred.

The answer contained 48 lines rather than the required 96, included one malformed path missing the slash after `/work/n`, and repeated one path. The ordinary terminal channel accepted `answer: done` rather than rejecting it to force later checkpoints or additional work. This is therefore a task-level failure trajectory, not an answer-gating artifact. It establishes neither useful external organization nor a general limitation of the model; one unreplicated trajectory cannot separate premature commitment from fixture, prompting, or sampling effects.

## Checks

- PASS — `terminal_done`
- FAIL — `answer_valid`
- PASS — `source_unchanged`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `no_init_process`
- PASS — `only_work_mount_writable`

## Interpretation

This is one unreplicated pilot-candidate observation. Files other than the required answer are classified from observed use, not existence. A task outcome or artifact alone cannot establish a general effect or persistent instrumental structure.

[Machine-readable trajectory](./d96-pilot-candidate-20260820T004248Z.jsonl)
