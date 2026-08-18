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

## Remaining boundaries

The log is complete at the adapter boundary, not a kernel-wide trace. The hidden startup open of `/work`, container runtime setup, and host activity are outside the model action trajectory. The protocol is ASCII and caps a single read or directory request at 4096 bytes. The adapter does not expose directory creation, renaming, deletion, execution, or compilation. These are intentional Pilot 1 constraints, not general operating-system semantics.
