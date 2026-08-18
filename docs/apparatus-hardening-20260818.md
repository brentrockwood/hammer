# Apparatus hardening record — 2026-08-18

## Problem

The initial spike demonstrated a useful action loop but was not ready for repeated retrieval. Its directory action combined three syscalls, returned at most one 4 KiB page, and closed the directory before another page could be requested. The adapter accepted arbitrary paths and descriptors, the JSON string path did not preserve escapes reliably, the container root was writable, the ten-turn default could not admit an exhaustive scan, and the built image was not tied to the source revision. There was also no deterministic retrieval corpus, external oracle, filesystem lineage, or failure-complete calibration record.

## Changes

The adapter now preopens `/work` as hidden substrate setup and confines each model open with one `openat2` call using `RESOLVE_BENEATH`, `RESOLVE_NO_MAGICLINKS`, and `RESOLVE_NO_SYMLINKS`. Returned descriptors are typed and tracked; the model cannot operate on stdin, stdout, or the harness's `/work` descriptor. Directory descriptors remain open across explicit `getdents64` pages until EOF or close. Read results are length-aware, and the deliberately ASCII JSON protocol handles quotes, backslashes, tabs, and newlines.

Compose now supplies no network, a read-only root, no init process, no capabilities, and `no-new-privileges`. The host records those properties from the running container. Image builds carry `org.opencontainers.image.revision`; retrieval calibration refuses to start unless that value equals the clean relevant Git revision.

The new fixture generator produces deterministic, fixed-size public records with separately seeded filenames, label ordering, payloads, and creation order. The calibration runner preserves `/work` across fresh contexts and containers, calculates an exhaustive primitive action budget, records exact oracles and scores, snapshots every persistent byte around each task, and writes terminal evidence on caught failures.

## Validation so far

The static agent compiled with `-Wall -Wextra -Werror`. A scripted client completed full 10- and 50-record scans, forced multi-page directory enumeration with 128-byte requests, reached EOF without duplicates, and recovered the exact target sets. The same test verified JSON escape round trips, rejection of absolute, parent-component, and symlink path escapes, rejection of operations on control descriptors, and the live isolation settings.

These checks validate the apparatus path, not model behavior. The source-revision image check and the model-backed 10/50 calibration remain to be performed after this apparatus commit is frozen. Their exact commands, source and image identities, run records, and outcomes will be appended rather than inferred in advance.

## First model-backed calibration

The frozen image revision `7feb738761f1d15135fe69e4b7fae62b9eb667f0` passed its source-label check. Calibration run `retrieval-calibration-20260818T220009Z`, using temperature 0, sampling seed 1001, and corpus seed 20260818, failed exact scoring at both stages. At 10 records, the model exhaustively read every file and found both targets but removed their `.txt` suffixes. At 50 records, it chose a 32-byte directory buffer, reached `EINVAL` before any real entry could fit, and stopped without reading a corpus record. The public trajectory and human commentary were committed before the apparatus changed.

This exposed two task-irrelevant degrees of freedom. The next revision removes the filename suffix and makes the accepted directory buffer contract explicit: the prompt shows 4096, and the adapter accepts 512 through 4096. It also distinguishes schema rejection from kernel execution by emitting `syscall: null` for the former. A second calibration will use seed 1002 and a new frozen revision.

## Second model-backed calibration and model selection

Revision `9d31b82061d58a44437537d0f1ab56e282f7e50b` removed the first run's two confounders and again passed the complete reference scan. Calibration run `retrieval-calibration-20260818T220424Z` reached directory EOF at both sizes without an adapter error, but the 7B model returned `[""]` without reading a record. The run used only a small fraction of its action and context budgets. It was committed with human commentary before the next decision.

The installed serving set includes a same-family `qwen2.5:72b-instruct-q4_K_M`. Calibration 3 will change only model scale and sampling seed: 72B Q4_K_M at temperature 0 and seed 1003. Task, corpus seed, stages, prompt, adapter, budget, and scoring stay fixed. This is a capacity check for apparatus readiness, not a model comparison claimed as a Pilot 1 result.

## Remaining boundaries

The log is complete at the adapter boundary, not a kernel-wide trace. The hidden startup open of `/work`, container runtime setup, and host activity are outside the model action trajectory. The protocol is ASCII and caps a single read or directory request at 4096 bytes. The adapter does not expose directory creation, renaming, deletion, execution, or compilation. These are intentional Pilot 1 constraints, not general operating-system semantics.
