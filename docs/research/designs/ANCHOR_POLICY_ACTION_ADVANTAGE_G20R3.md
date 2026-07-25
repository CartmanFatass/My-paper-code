# Anchor-policy action advantage, re-registered contract (G20R3)

```text
status=DRAFT_AWAITING_GATE_A
algorithm=ANCHOR_POLICY_ACTION_ADVANTAGE_G20R3
supersedes=ANCHOR_POLICY_ACTION_ADVANTAGE_G20R2
authority=external_pro_20260725_g20r2_prefreeze_grill
ruling=docs/external-review/rounds/20260725_g20r2_prefreeze_grill/21_PRO_OPEN_RAW.md
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
compute_authorized=none
```

Draft. Not frozen, not grilled, authorizes nothing. Written against the nine
blockers of the G20R2 ruling; each section names the blocker it discharges.

## Why G20R2 is retired

`CHANGES_REQUIRED`. The mathematical C1 class is unchanged, the exact-zero fast
anchor remains valid, active-set centering remains valid in its registered scope,
and P2 remains untested. What failed was the audit's realization and its result
semantics.

Retired outright by the ruling:

- the pairwise `epsilon_audit` calibration as the gate for a K-centered energy;
- action-space cosine as evidence of residual-parameter update alignment;
- the assembled G20R2 screen as an interpretable evidence path;
- a binary Stage A failure interpreted as absence of source action effect.

## 1. Fixed conditioning history — Blocker 1

The G20R2 implementation replaced suffix noise from the intervention timestep
onward, **including positions strictly before `j`**. Earlier same-step actions
therefore varied across replicates, the prefix seen by token `j` varied, `h_j`
was not fixed, and the oracle averaged over different decision histories. This
invalidated Stages A, B1 and B2 and the resolution calibration together.

The suffix split at intervention time `t`, position `j`, is exactly:

```text
positions < j at time t : fixed factual prefix noise and actions
position   j at time t : the forced probe action
positions > j at time t : suffix-policy randomness, common across probes within a replicate
times      > t         : suffix-policy randomness, common across probes within a replicate
```

The critic response must be evaluated at the **same** prefix as the oracle. The
G20R2 code replayed the critic with the original prefix noise while the oracle
had moved, so the two were evaluated at different histories.

## 2. Stage A — cross-replicate action-effect energy, no floor — Blocker 2

`epsilon_audit` is gone. Not recalibrated: **removed**. A scalar floor was never
the right object, and three successive attempts to fix it were fixing a
construction that should not exist.

For each fixed history `h` and fixed set of `K` probe actions, obtain two
estimates from **disjoint suffix-replicate sets**, both using the **same
within-history K-action centering rule as Stage A's own estimand**:

```text
Ahat^(1)_hk = A*_hk + e^(1)_hk
Ahat^(2)_hk = A*_hk + e^(2)_hk

S_source_cross = E_{h,k} [ Ahat^(1)_hk * Ahat^(2)_hk ]
```

With disjoint, conditionally independent replicate sets and unbiased return
estimates, `E[ Ahat^(1) Ahat^(2) | h, a_k ] = (A*_hk)^2`. The cross-product
estimates the action-effect energy **with no positive noise bias**, so nothing
needs to be subtracted and no resolution constant needs registering.

What is pre-registered is the *procedure*, not a number: the policy snapshot at
which the audit occurs, the action-probe distribution, the suffix continuation
policy, the number of suffix replicates, the episode and history distribution,
the clustering unit, and the inferential rule. The realized noise scale is not
frozen and does not need to be.

## 3. Result semantics — three states, not two — Blocker 3

`passed = lcb > threshold` is retired. Every gate reports a **lower and upper**
bound and resolves to one of three states:

| State | Condition | Smallest claim |
|---|---|---|
| `CONTRADICTED` | upper bound at or below the null | genuine absence or anti-alignment on this support |
| `SUPPORTED` | lower bound above the null | the effect is present and resolved |
| `UNRESOLVED` | interval spans the null | the audit could not decide — **not** evidence of absence |

This binds Stage A, B1 and B2 alike. A positive point estimate whose lower bound
crosses zero is **underpowered**, and must not receive the same smallest
proposition as an upper bound at or below zero.

Stage A additionally separates a source that is locally action-insensitive from
one whose effect is **concentrated** on a minority of tokens — the G18 case,
where reward saturation makes a genuinely active member's marginal effect exactly
zero. Concentration is a property of the source, not a failure to identify, and
those zeros stay in the estimand. They are never removed using observed `A*`.

## 4. Stage B2 — residual-parameter space — Blocker 4

The action-space cosine is retired. Stage B2 compares gradients in the
**parameter space of all residual-actor parameters updated by the delayed policy
loss** — not a subset, and not the action-space score composed with a shared
Jacobian.

```text
require |g*_res| > 0  and  LCB95( cos(ghat_res, g*_res) ) > 0
```

with both directions taken over that full parameter set.

The `|g*_res| = 0` authority check is a **statistical test against the estimator's
own resolution**, not an exact-zero tolerance. The G20R2 realization compared a
sample mean over ~192 noisy rows against `1e-8` while its sampling noise was
~`1e-3`, making the `SOURCE_EFFECT_OUTSIDE_CENTERED_AUTHORITY` branch unreachable
— one of the two separations that re-registration existed to add.

## 5. Requalification cadence — Blocker 5

A final-only audit is insufficient, and G20R2 was worse: **initial-only**. One
qualification at the anchor licensed 100 and 300 delayed updates with no
requalification, no per-block audit and no final audit.

This contract freezes an actor-update **block size**, and requalifies the critic
before each block under the new snapshot. Frozen alongside it: requalification
timing, the policy and action-probe support at each new snapshot, the critic-fit
and audit data for each block, and whether Stage B2 compares **gradients or
Adam-applied updates**.

Block size and cadence are registered in section 11 and are load-bearing: a
`PROMISING` reading obtained without them is the "late audit cannot retroactively
validate hundreds of updates" failure inverted in time.

## 6. Identification failure emits its branch — Blocker 6

An identification failure must terminate that source **cleanly**, emit its
registered branch, and perform no residual update. It must not become an
operational exception.

G20R2 called `begin_delayed_phase(stage_b_passed=...)` unconditionally on a
method that raises when the flag is false, so any Stage A, authority, B1 or B2
failure raised before the source could return its branch — and because sources
run in order, a G17 failure prevented the independent G18 source from running at
all. That is the masking defect this line exists to retire, rebuilt as a crash.

Sources are **independent**. One source's failure never suppresses another's
result, and each writes its own branch and serializes.

The G17 "diagnostic compatibility pass under an unqualified critic" is also
corrected. If the critic does not qualify, the residual actor cannot legally
train, so evaluating the unchanged anchor afterwards is an **anchor regression**,
not evidence that a trained residual preserved G17. The branch retains the precise
identification failure rather than a generic diagnostic label.

## 7. The audit measure is registered, not only its support — Blocker 7

Freezing the active support is insufficient; the **history weighting** must be
frozen too. G20R2's forced G18 pivotal point placed one third of the probe mass
on a single decision point, changing `S_source`, its structural-zero fraction and
its confidence interval.

Registered: **natural active-token occupancy**, with the pivotal intervention
reported separately rather than mixed into the expectation.

At later policy snapshots the action probes must cover the **current policy
region as well as the frozen anchor baseline region**.

Clustering: confidence intervals are clustered at the episode-ledger and
suffix-replication level, and the clusters must be genuinely independent
randomization units. G20R2 bootstrapped eight audit episodes that shared three
underlying G18 ledgers.

## 8. `M_t` equivalence, stated — Blocker 8

The contract names active, lifecycle and membership-transition state as part of
`H_Q`. The implementation passes the active mask explicitly and relies on
observation columns for age, previous effort, rotating status and phase.

This may be information-equivalent for the two registered sources, but the
contract must **say so explicitly** and identify which membership-transition
information is recoverable from `X_t` and `R_t`. Otherwise the design claims to
supply `M_t` while the implementation supplies a subset under an undocumented
assumption. No new source field is required if equivalence is established; a
frozen semantic statement is.

## 9. Assembled-path exercise — Blocker 9

`run_screen` has never executed end to end at any scale. That disclosure is
material because the assembled path contains at least one branch-reachability
defect and one fixed-history defect that isolated tests did not expose.

Before any bounded screen, one **proof-sized, non-conclusion-bearing** exercise
must establish: a successful qualification path; a Stage A failure path; a B1/B2
failure path; clean source-local termination; independent continuation to the
second source; snapshot requalification; and result serialization.

It is not the screen, is not interpreted as evidence, and must not be used to
tune any threshold.

## 10. Result system

Sequential, source-specific, first match. Unchanged in shape from G20R2 except
that each gate now resolves three-valued per section 3, and no global `all(...)`
exists across sources.

Branch claims are bounded by what they can identify. A G18 Stage A failure
updates the audit distribution, the budget, the effect density, or G18's
suitability as an unconditional identification carrier. **It does not refute C1
or P2**, because G18 already contains a specific constructive delayed-effect
intervention.

## 11. Constants

To be frozen at Gate A. Deliberately empty in this draft: registering numbers
before the grill would repeat the G20R2 error of freezing a value nobody
questioned.

Required: suffix replicate count per estimate; `K`; audit episodes and probe
points; actor-update block size and requalification cadence; audit seed block
disjoint from every earlier package; and whether Stage B2 compares gradients or
Adam-applied updates.

## 12. Files

To be assigned after Gate A. The G20R2 package stays in the tree as the evidence
that produced this ruling and is not extended.

No run is authorized by this document.
