# C48 declared-compaction scripted dry run — failed

This scripted dry run reached both declared compaction boundaries in the network-disabled container, with `/work/reference-route` present and `/work/answer` absent at each boundary. It then terminated before final-route validation because the reference client contained an erroneous post-check: after a syscall had already recorded a checkpoint, the loop treated the matching step number as evidence that the checkpoint had not been handled.

## What was attempted

The host generated the frozen 48-node fixture and used a scripted client against the same syscall adapter planned for C48. The client wrote a host-known route to a non-output scratch file solely to test persistence transport, enumerated and read graph records, and recorded snapshots at steps 70 and 140. No model request was made.

## Result and repair boundary

The run is an apparatus failure, not model evidence and not a successful dry run. The JSONL trajectory ends after the second checkpoint because the script raised `RuntimeError: checkpoint must be handled inside call` before its error path wrote `run_end`.

The public record is retained rather than repaired in place. The next commit removes only that erroneous post-check and adds a failure-complete dry-run path before a new scripted attempt. No model-backed treatment will run until the replacement dry run has a terminal record, final validation, and a passing frozen-image check.

[Machine-readable trajectory](./c48-compaction-scripted-20260819T113356Z.jsonl)
