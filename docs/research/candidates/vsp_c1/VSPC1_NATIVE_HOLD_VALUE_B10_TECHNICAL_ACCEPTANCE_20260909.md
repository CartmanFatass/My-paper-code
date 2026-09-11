# B10 P76 source technical acceptance

Implementation and required independent boundary review are complete. Technical
source acceptance PASS; this is not a native result or a scientific submission.
Source starts at13b7da7012f4879607074bdcbd7bbbae597ccf85 on the existing
`C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, branch
`codex/direction-vsp_c1`. No unrelated starting changes were present.

## Delivered boundary

The35-line B10 runner fixes8501, Config768, normalized value, width133 and
extra850100012, selecting the fixed endpoint path. Shared study adds104/removes40
lines: it evaluates after completed rollout/update512 and768 using separate
training/evaluation environments per arm and fresh private32 sampling-generator
pairs at each endpoint. Both endpoints use the same reset bank, with H once.
Training keeps the same models, optimizer, private generators, completed-episode
sequence and cumulative moments. Evaluation collector recurrent state/storage is
local to each episode; it only reads/decodes moments. Four constructors are counted.

Endpoint records and checkpoints distinguish actual512/768 exposure from final
Config768 and retain endpoint movement, moments and training-only cumulative
counts. Total counts retain all evaluation work. Fixed checkpoint serialization
and readback reuse the existing path, without resume or non-interference guards.
The identity-matched primary computes C from the32 paired changes and computes
its conditional SE from that same vector. Both endpoint differences and all four
H contrasts/J vectors remain independently available. Missing learned panels
suppress dependent C; missing H alone does not. Collection will compute all five
native means and their conditional SEs from the retained vectors.

Prior callers keep final-only behavior and metadata. UCOPE environment/learner/
policy/study, critic and normalization remain read-only at the preserved e9a05af5
semantics. Main's later four UCOPE changes are neither imported nor rolled back.

## Focused evidence

[Check and review receipt](VSPC1_NATIVE_HOLD_VALUE_B10_SOURCE_CHECKS_20260909.json)
retains exact argv/stdout/process wall and review findings. One invocation:
23 passed, pytest3.27s, whole4.257573100000627s, exit0, within300s total.
Existing cache_dir warning appears while cacheprovider is disabled.

New B10 stub checks cover full512/eval/continued768/eval/H ordering, distinct
training/evaluation environments, private generator identity/use, unchanged
training model/optimizer sequence, cumulative frozen moments, training-only and
overall counts, serialized actual endpoint exposure and publication readback.
The midpoint deadline case expires the continuous first-arm clock and verifies
no later training begins. Pure-data cases cover the exact MEI boundaries,
identity-paired conditional SE, missing learned/H dependencies and duplicates.
B10 CLI identity/exit/rejection checks and the existing B08 full768 schedule/default
cost cases passed in the same invocation. No real model/optimizer/forward/native
simulation or evaluation was run. Unchanged scientific coverage is reused.

Independent Reviewer `review_b10_boundary` inspected the actual changed code and
collector/update/actor/critic/ValueMoments/native/adapter dependencies, found no
material defect and requested no repair. It confirmed state/RNG separation,
endpoint metadata, dependent C reading, default behavior and continuous clocks.
Review is read-only evidence, not runtime conformance or scientific truth.

Engineering scope section4: none, per card section5. Existing checkpoint output
is reused for the two fixed measurements.139 added production lines total,
35 runner lines, below2000/600. No uncarded machinery was identified.

## Cost, publication and next boundary

Card section5 projects each arm as196608 training steps,1536 updates,384 moment
merges and16384 learned evaluation steps; MLP additionally8192 H steps. The
505s×53/51=524.8039216s whole proxy is planning evidence only; both complete arms
retain1800s and whole3600s including midpoint/final/H/publication/exit. No cost
probe was performed. Aggregate CPU/component overhead remain unmeasured.
The full semantic stub exercised all four checkpoint publications and summary
readback, reusing unaffected coverage rather than adding scientific exposure.

CM returns source/review and editing/index to DM for the already allocated
exact scientific-SHA/payload binding. No B10 remote staging, admission, accepted
submission, model, fit, native step, Adam or evaluation exists yet. After binding,
CM continues the same P76 batch through sole observation and all-outcome collection;
at most one accepted submission, with no retry or successor.

## Scratch cleanup blocker

CM-owned `temp/directions/vsp_c1/test/b10_p76_focused1` remains. Automatic
approval review rejected the exact-resolved recursive PowerShell cleanup and
then the nonrecursive file/empty-directory cleanup, both as “blocked by policy”
before execution. The check receipt was retained; no deletion, bypass or
escalation occurred. CM owns cleanup when a permitted operation is available;
this housekeeping fact changes no scientific meaning or invocation allowance.
