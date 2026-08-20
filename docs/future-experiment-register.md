# Future experiment register

This is a design register, not an experimental result. Entries record candidate treatments worth preserving while the apparatus and Pilot 1 design continue to change. A candidate must still receive a frozen protocol, adversarial review, and an explicit interpretation boundary before a run is represented as evidence.

## Terminal-feedback conditions for closed-ended tasks

The D96 candidate observation raises a basic apparatus choice: what happens when the model says it is done but its submitted artifact is invalid? The current blind terminal behavior accepts the declaration, ends the run, and scores the artifact afterward. That behavior retained an observation of premature commitment, but it is only one of several useful conditions.

| Candidate | Terminal behavior | Question it can address | Interpretation limit |
| --- | --- | --- | --- |
| Blind terminal | `answer: done` ends the run; the harness scores afterward and provides no outcome feedback. | Does the model itself recognize completion, incompleteness, and an irreversible commitment? | A failure cannot separate planning, bookkeeping, prompt comprehension, and sampling causes. |
| Reject without reason | The harness returns only that the answer is invalid and permits further actions. | Can the model diagnose and repair an invalid artifact without receiving its defect? | The rejection itself is a completion signal and creates an iterative verifier game. |
| Reject with reason | The harness identifies a class of defect, such as wrong cardinality or a dependency violation, and permits repair. | Can the model use explicit correctness feedback to repair a concrete artifact? | The verifier supplies task-relevant information; this does not measure unaided completion recognition. |

The primary closed-ended condition should remain blind-terminal unless the research question is deliberately changed. The prompt may state plainly that `answer: done` ends the opportunity to act. That makes the irreversible commitment legible without revealing whether the artifact is correct.

## Candidate analysis to preserve with every terminal condition

For any future run using one of these policies, preserve at least:

- the terminal policy and exact model-visible wording;
- the first submitted artifact and its full validation breakdown, including checks not reached by a short-circuit validator;
- the action and context budget remaining at first submission;
- whether directory enumeration reached EOF and what task data was actually read;
- for repair conditions, each validator response, subsequent mutation, and final artifact.

This makes an early invalid submission distinguishable from a verifier-assisted repair, rather than collapsing both into a final pass/fail value.
