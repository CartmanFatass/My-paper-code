# D7.S R5 obligation F — branch semantics, frozen before any treatment data

`D7_S_R5_DEVELOPMENT_OBLIGATIONS_NOT_A_RESULT`

Closes obligation **F**. Pro ordered it first, ahead of C–E, for a specific
reason: **close the result logic before generating any treatment data, so a
development observation cannot acquire an interpretation the comparator does not
support.** Purely synthetic — no environment, no episode, no audit-path import,
no `D_A` inference.

Harness: `scripts/d7_s_r5_obligation_f_branch_semantics.py`.

## The frozen map

Precedence is fail-closed and severity-ordered. **An instrument that did not do
what it claims never emits a mechanism reading, however clean its numbers look.**

```text
1  not exposure_ok            -> INVALID_EVENT_ALIGNED_AUDIT
2  not post_start_total       -> DERANGEMENT_CONTROL_NOT_TOTAL_ON_TOPOLOGY
3  not pretreatment_support   -> DERANGEMENT_CONTROL_SUPPORT_INSUFFICIENT
4  statistics may now speak:
     equivalent               -> COUNTEREXAMPLE_TO_PERSISTENCE_NECESSITY
     materially worse         -> MIN_DISTANCE_DERANGEMENT_WORSE
     otherwise                -> DERANGEMENT_CONTROL_UNRESOLVED
```

with, on the registered R4 contrast convention and
`D_A = G(derangement) − G(constructive_mixed)`:

```text
equivalent        LCB95(D_A + 5) > 0  AND  LCB95(5 − D_A) > 0
materially worse  UCB95(D_A + 5) < 0
```

`equivalent AND materially_worse` is structurally unreachable — `D_A` cannot be
both inside and below the margin — and is mapped to
`INVALID_EVENT_ALIGNED_AUDIT` rather than resolved by ordering. **Refusing beats
picking**, because a future numeric change must not be able to silently choose
the friendlier of two contradictory readings.

## Results

```text
exhaustive enumeration        56 cases      mismatches 0
labels reached                6 / 6
PERSISTENCE_NECESSARY_SOURCE  produced by 0 of 56 cases
                              present in the frozen vocabulary: False
```

**Every frozen label is reachable.** This is checked rather than assumed because
R4's post-mortem turned on a branch that could not fire: a result state that no
input can produce reads as coverage forever after. All six are demonstrated
live.

**The forbidden label is unreachable, and the check is structural.** There is no
path from `MIN_DISTANCE_DERANGEMENT_WORSE` to `PERSISTENCE_NECESSARY_SOURCE`,
and the string is not in the vocabulary at all. Both are asserted separately:
absence from the vocabulary is a design fact, unreachability across the whole
input grid is a measured one, and either alone could be satisfied while the
other failed.

## Paired negatives — each goes red

| Mutation | Detected |
|---|---|
| worse read as necessity — the R4-shaped error | yes |
| support miss read as equivalence — "no data looks like no effect" | yes |
| exposure failure ignored, statistics allowed to speak | yes |
| post-start infeasibility drops the episode instead of aborting the topology | yes |

The first is the one this obligation exists for. `π_der` is a **member** of the
no-persistence policy class, not its optimum, so `V_D ≤ V*_¬P`: a worse result
bounds only this least-distance derangement and says nothing about the class. A
map that promoted it to necessity would be the R4 error repeated with better
apparatus.

## Interpretations travel with the labels

Each label carries the reading it licenses, in the same module, so a branch
cannot be paired downstream with a meaning it was never given. In particular
`MIN_DISTANCE_DERANGEMENT_WORSE` states in its own text that source necessity
remains **unresolved**, and that is asserted by the harness rather than left to
a reader's memory.

## Status

**F closes.** A, B, Step 0 and F are done. **C, D, E, the integrated witness and
G remain**, and all of C–E require applying the derangement rather than
observing or simulating it. No confirmatory panel is frozen; `D7.3` and `D8`
remain blocked.
