# D96 first-observation forensic addendum

This addendum analyzes the published D96 candidate trajectory without changing its run record or score. It is a post-hoc diagnostic, not a new model observation and not a revised terminal policy.

## What failed

The recorded validator failed at its first check: `/work/answer` had 48 nonempty lines, while the fixture required exactly 96. That is the immediate scored failure.

The fuller diagnostic identifies additional independent defects. The answer contained 47 unique paths because one fixture path was repeated; one path was malformed by omitting the slash between `/work/n` and the filename; 50 fixture nodes were missing. Restricting analysis to the listed valid nodes still finds 12 dependency-order violations. The ordinary validator did not reach those checks because it short-circuits at the cardinality failure.

## What preceded it

The model requested one `getdents64` page. It received 21 directory entries with `eof:false`, then never requested a subsequent page or EOF. It opened and read 48 distinct dependency records, wrote `/work/answer`, closed it, and submitted `done` at model turn 104. The 480-turn budget therefore had 376 turns remaining.

Two earlier model responses were empty rather than JSON and were rejected without a syscall at turns 45 and 100. They cost ordinary turns, but cannot account for the incomplete acquisition or the decision to submit.

## What this can and cannot say

The trajectory establishes incomplete directory enumeration, partial graph acquisition, and a voluntary terminal submission under the original blind-terminal wording. It does not establish why the model submitted: the record cannot distinguish a mistaken belief that the file was complete from confusion about paging, bookkeeping, task interpretation, or other model-internal causes.

The next matched study retains blind scoring and changes only whether the prompt explicitly says that `done` ends the run with no further actions or feedback. That change closes a possible verifier-probing interpretation without turning the harness into a correctness oracle.
