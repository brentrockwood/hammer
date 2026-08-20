# D96 blind-terminal wording study — results

## Result

All six predeclared members submitted invalid answers through the blind terminal channel. None observed directory EOF, none created a non-output support artifact, and every isolation and source-integrity check passed.

Within each arm, the three members had identical adapter action sequences and identical public diagnostic summaries. Across arms, the sequences differed. The explicit-finality wording did not produce more complete work; it was associated with an earlier, smaller invalid submission.

| Arm | Members | Terminal result | Model calls | Records read | EOF | Answer lines | Missing nodes | Turns unused |
| --- | ---: | --- | ---: | ---: | --- | ---: | ---: | ---: |
| Original wording | 3 | Invalid: needs 96 nodes | 104 | 48 | No | 48 | 50 | 376 |
| Explicit finality | 3 | Invalid: needs 96 nodes | 49 | 21 | No | 42 | 54 | 431 |

The original arm's answer also had one duplicate, one malformed path, and 12 dependency-order violations among listed valid nodes. The explicit-finality arm had no duplicate or malformed path, but had 17 such ordering violations. Both arms stayed well below the verified 32,768-token loaded context: their peak recorded live contexts were 15,299 (46.7%) and 8,186 (25.0%) tokens respectively.

## What the study establishes

The explicit-finality sentence closed the possibility that `done` was being used as a probe for a correctness oracle: both arms were blind, and both terminal submissions ended their runs without feedback. It did not make the observed model trajectory more exhaustive or more likely to succeed on this fixture.

For these six records, the sentence is associated with an earlier commitment after reading only the first directory page and the 21 records named there. It is not evidence that the wording generally causes early commitment, nor that the model understood or strategically reacted to the sentence in any particular way.

## Adversarial interpretation boundary

The arm assignment also used disjoint sampling-seed sets: `3402–3404` for original wording and `3411–3413` for explicit finality. Although each arm repeated exactly at the recorded action level under temperature zero, this design does not identify whether that server/model path treats the seed as behaviorally irrelevant. The wording comparison is therefore confounded with seed assignment and cannot support a causal wording claim.

The runs also use one model digest, one fixture, one prompt family, and one action vocabulary. They are terminal-semantics calibration, not Pilot 1 evidence and not a measurement of useful external organization. The lack of support artifacts is an observed negative result, not a claim that the model cannot construct them under other conditions.

## Correction for any follow-up

A causal prompt comparison should use the same predeclared seed set in both arms, ideally as paired runs on each seed, with the model load state and context verified before every member. It should retain blind terminal scoring and report complete trajectory distributions rather than select a best result. A second fixture family would be needed before treating a D96-specific pattern as a broader behavior.

## Member records

- Original wording: [3402](../runs/d96-terminal-original-20260820T091508Z.md), [3403](../runs/d96-terminal-original-20260820T092241Z.md), [3404](../runs/d96-terminal-original-20260820T093013Z.md).
- Explicit finality: [3411](../runs/d96-terminal-explicit-finality-20260820T093734Z.md), [3412](../runs/d96-terminal-explicit-finality-20260820T094132Z.md), [3413](../runs/d96-terminal-explicit-finality-20260820T094531Z.md).
