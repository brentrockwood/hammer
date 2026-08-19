# C48 continuity-window pair — frozen protocol

## Question

Does retaining a familiar recent transcript tail change recovery, action selection, or filesystem externalization after a declared context boundary? This is an ecological continuity treatment, not a pure test of filesystem memory or spontaneous tool construction.

## Matched pair

Both conditions use the C48 fixture seed `20260819`, checkpoints after turns 70 and 140, a 280-turn maximum, `qwen3.6:35b`, sampling seed `3201`, temperature 0, `think:false`, a 32,768-token context, and a 512-token response cap. Both state the total horizon and remaining turns at each checkpoint.

`C48-H0` replaces the history with the system prompt and continuation notice. `C48-H12` retains the last 12 complete model-turn exchanges verbatim: each model response followed by its syscall result or rejection. It keeps the system prompt, discards earlier messages, then adds a factual continuation notice. The tail is model-produced content, not a host summary.

The public trajectory records the exact continuation, retained-turn count, retained message count, and first retained turn. The preceding model-response and result events make every retained message reconstructable.

## Boundary

H12 deliberately exposes recent adapter state, including any descriptor number appearing in the retained results. Its outcome therefore measures ordinary trailing-window continuity plus any usable live process state; it cannot isolate filesystem persistence. The container and `/work` remain live in both conditions. No model is asked to create notes, files, indexes, tools, or a preferred representation.

## Interpretation

The completed C48, C48-L, and earlier C48-H records remain historical full-reset observations. This pair starts after the H0/H12 protocol and source have been frozen; it does not retroactively turn the earlier records into matched controls. One paired seed is exploratory. A visible difference motivates preregistered replications; no difference does not demonstrate equivalence.
