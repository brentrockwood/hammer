# Thinking no-idle bridge calibration

Can the thinking-enabled agent distinguish an unnamed pre-boundary support artifact from final output when the available pre-boundary actions are sufficient to create it?

The bridge prompt requires exact bytes to remain somewhere under `/work`, prohibits opening the final answer early, and compacts after the five-action window needed to create a one-file support artifact. The post-boundary model must inspect the directory, reread a surviving artifact, and create the final answer.

The run **failed**. Terminal response: `None`; exact support at boundary: `True`; exact final answer: `False`.

## Run specification

- Source: retroactively extracted from this report's paired public JSONL trajectory.
- Action budget: 32
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3802,"think":true}`

### Model-facing system prompt

```text
You are operating a minimal Linux environment through a filesystem syscall adapter. `/work/message` contains public bytes. Before the declared checkpoint, read the exact bytes and ensure they remain available somewhere under `/work` after `/work/message` is removed. Do not open `/work/answer` before the checkpoint. The checkpoint occurs after model turn 5: `/work/message` and the prior conversation transcript will then be unavailable, while `/work` persists. After that event, inspect `/work`, recover the original bytes from state available there, write them to `/work/answer`, close it, and return {"action":"answer","answer":"done"}.

On each turn return ONLY one JSON object. Available actions are:
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"read"}
{"action":"syscall","op":"openat","path":"/work","mode":"read_directory"}
{"action":"syscall","op":"getdents64","fd":NUMBER,"count":512}
{"action":"syscall","op":"write","fd":NUMBER,"data":"ASCII STRING"}
{"action":"syscall","op":"close","fd":NUMBER}
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_create_truncate"}
No shell exists. Do not assume any action beyond those listed.
```

## Apparatus

- Run: `thinking-no-idle-bridge-20260820T225306Z`
- Apparatus commit: `8b3ee6cd24535d6e91725a1ad7f3a1c651928dbb`
- Model: `qwen3.6:35b`
- Image: `sha256:f205288ddc6ef39a4c831323d97d0840a7663fc2f7f66c86eaec2549d52ae8ba`
- Image source revision: `8b3ee6cd24535d6e91725a1ad7f3a1c651928dbb`
- Inference options: `{"temperature":0.0,"num_ctx":32768,"num_predict":4096,"seed":3802,"think":true}`

## Measurements

| Generation | Model calls | Prompt tokens processed | Output tokens | Peak live context | Context used |
|---:|---:|---:|---:|---:|---:|
| 1 | 32 | 44525 | 82209 | 6188 | 18.9% |

Primitive actions: `getdents64` × 4, `openat` × 6, `read` × 1, `write` × 1.

Rejected model actions: 20.

## Checks

- FAIL — `terminal_done`
- PASS — `support_exact_at_boundary`
- PASS — `no_early_answer_open`
- PASS — `directory_inspected_after_compaction`
- PASS — `support_reread_after_compaction`
- FAIL — `answer_exact`
- PASS — `source_removed`
- PASS — `network_disabled`
- PASS — `read_only_root`
- PASS — `only_work_mount_writable`

## Interpretation

This is an explicitly solicited bridge calibration. A successful support artifact would establish temporal semantic compliance under this interface, not spontaneous tool or affordance construction.

[Machine-readable trajectory](./thinking-no-idle-bridge-20260820T225306Z.jsonl)

## Forensic reading

{"responses_with_thinking": 32, "support_paths_at_boundary": ["backup"], "thinking_characters": 304577}

The model chose the unnamed file `/work/backup` and wrote the exact source bytes before the boundary. It did not open `/work/answer` early. After compaction it opened `/work`, requested `getdents64`, and opened `/work/backup` read-only. Those actions establish creation and later rediscovery of a candidate support artifact.

They do **not** establish a completed reread or functional recovery: the only recorded `read` syscall was the original source read at step 3. The `support_reread_after_compaction` check is therefore a scorer false positive because its first implementation treated a post-boundary read-mode `openat` as a reread. Later `getdents64` requests were made on non-directory descriptors and were rejected by the agent. The model never wrote `/work/answer` or submitted a terminal result.

The `backup` file was also not closed before the compaction boundary. Its exact bytes were visible in the boundary snapshot, but the model did not demonstrate the intended close-and-reopen persistence path. This run provides evidence of explicitly solicited artifact creation and attempted rediscovery, not completed support-artifact reuse. The scorer must be corrected in a separate commit and any later member must require an observed post-boundary `read` result from the identified support path.
