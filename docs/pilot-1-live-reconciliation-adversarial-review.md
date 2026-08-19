# Live reconciliation adversarial review — 2026-08-19

## Decision

Do not implement or run the live-reconciliation draft as Pilot 1. The problem is not a missing generator or model setting. Its event mechanism confounds the behavior the task is meant to observe.

No fixture, reference client, task runner, or model-under-study trajectory was created. This is a design decision, not a negative model result.

## Why the task fails before implementation

The model is told that two amendments will arrive and that only the final state matters. It therefore has a rational direct strategy: delay substantive reconciliation until the second amendment, then solve the final version once. The task permits a provisional table or dependency representation, but it does not make one useful to the stated goal.

The proposed repair—deliver amendments after fixed action counts—makes the problem worse. Hammer has no idle or wait action. A model that reaches a provisional conclusion before an event must issue additional filesystem actions merely to advance the clock. Those actions may be repeated reads, rejected requests, or scratch writes. Any resulting file could then be an artifact of the timing mechanism rather than an independently useful construction.

Changing the trigger to “all source records have been read” would avoid idle calls but turns exhaustive inspection into a hidden gate. Changing it to a provisional answer write would make a maintained answer file an explicitly required intermediate protocol. Neither repair preserves the intended non-prescriptive task.

## Interpretation boundary

The full action/result trajectory still remains in model context. Even absent the timing defect, a scratch file could show organization or later consultation but not establish that it supplied memory or caused a performance improvement. A changing-world task can be useful for a later matched treatment, but it is not a sound first descriptive Pilot 1 under the current adapter.

## Consequence

The live-reconciliation draft remains a rejected design record, not the next central candidate. Do not build its generator, runner, or reference client merely because those components are mechanically feasible.

The next task search must first satisfy a sharper pressure criterion: within one static current goal and a full continuous transcript, the task must give an unprompted external representation a plausible role that does not depend on an action clock, a hidden inspection gate, an explicitly required provisional artifact, or a model-visible future task. If no such task exists under the current adapter, that is a substantive design finding. The next condition should then be an explicitly labeled change in the treatment—such as bounded transcript access or a visible context boundary—not a disguised workaround.
