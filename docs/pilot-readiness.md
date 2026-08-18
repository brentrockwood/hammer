# Pilot 1 readiness criteria

## Status after 10/50 calibration

The criteria below are satisfied for the 10- and 50-record apparatus as of the calibration summarized in [calibration-summary-20260818.md](calibration-summary-20260818.md). The last run completed the full 50-record trajectory without a binding apparatus limit and produced a clean model-level exact-answer failure.

Pilot 1 is not yet ready at the proposed larger sizes. A scalable out-of-band result channel and the Pilot 1 repetition, sampling, stage, stopping, and interpretation rules remain to be frozen. All calibration runs are excluded from Pilot 1.

The first retrieval pilot should not begin merely because the model can complete a toy task. The apparatus must make a primitive solution possible, observe the complete action path, and distinguish model behavior from limits we accidentally imposed.

Before freezing Pilot 1, we require the following:

- directory enumeration continues across multiple `getdents64` pages and reaches EOF;
- each accepted action corresponds to exactly one recorded filesystem syscall, while validation rejections explicitly record that no syscall ran;
- every model-controlled path is confined beneath `/work`;
- the control-channel descriptors cannot be read, written, or closed by the model;
- quoted text, backslashes, tabs, and newlines survive a write/read round trip;
- the container has no network, a read-only root, and only `/work` writable;
- a scripted primitive client can solve the 10- and 50-file retrieval stages;
- task budgets permit that primitive solution with a recorded margin;
- corpus generation is deterministic from a recorded seed and does not correlate filenames, creation order, size, or target membership;
- every task has an external answer oracle and exact scoring;
- filesystem state is captured before and after every task, including the contents of agent-created artifacts;
- fresh model contexts are used between tasks while `/work` alone persists;
- inference parameters and sampling seeds are explicit;
- the built image identifies the clean source commit from which it was produced;
- infrastructure or model failures still produce a terminal event and human-readable report.

The 10- and 50-file runs performed while satisfying this list are apparatus calibration. They are not Pilot 1 observations and must use separate labels and seeds. Corpus sizes above 50 remain provisional until measured action and context growth show that exhaustive primitive retrieval is still feasible.
