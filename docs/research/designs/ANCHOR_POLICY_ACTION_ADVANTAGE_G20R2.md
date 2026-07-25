# Anchor-policy action advantage, re-registered contract (G20R2)

```text
status=DESIGN_FROZEN_BOUNDED_SCREEN
algorithm=ANCHOR_POLICY_ACTION_ADVANTAGE_G20R2
supersedes=ANCHOR_POLICY_ACTION_ADVANTAGE_G20R
authority=external_pro_20260724_g20r_identification_floor_convergence
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
compute_authorized=none_until_this_contract_is_accepted
```

Pro's section 10 requires a zero-compute re-registration before any screen is
interpretable. This is that contract. It freezes the nine items enumerated
there. Nothing here authorizes a run.

## Why the previous registration is retired

The G20R screen returned `NONFORMAL_NON_IDENTIFIED_ACTION_CRITIC_G20R`, and the
round that followed established the branch was not merely mis-thresholded:

- the identification floor normalized an action-sensitivity quantity by
  `slow_return_std`, a state-variance quantity, so it could not separate
  "critic did not identify" from "state variance dwarfs any action effect";
- `Q_j` never received the variables the delayed effect depends on, so it was
  fitting `Q(h_reduced, a)` rather than `E[G | h_true, a]` — structural
  non-identifiability, not undertraining;
- the actor was updated from an unqualified critic, and identification was
  measured only on the final training trajectory;
- one global identification Boolean let a G17 failure mask the G18 path.

The mathematical C1 class is unchanged by any of this, and P2 remains untested.

## 1. The `Q_j` history — complete and anonymous

For policy snapshot `v`, `Q_j` conditions on a permutation-consistent pre-action
sufficient statistic:

```text
H_Q[j,t] = ( c_t,               centralized critic state
             X_t[sigma_t],      FULL masked table of per-member observations,
                                in anonymous routing order
             R_t[sigma_t],      detached pre-action recurrent states for all
                                active lifecycle rows
             M_t[sigma_t],      active, lifecycle and membership-transition
                                state available at action time
             j,                 routing position
             A_<j,t[sigma_t],   FULL ordered action prefix paired with its
                                member context -- not merely its sum
             a_j,t )            post-tanh requested action
```

**Prohibited inputs**, each fail-closed: any action at a position greater than
`j`; next state; future reward; unannounced future membership event; source
ledger identity unavailable at decision time; hard-coded semantic interpretation
of observation coordinates.

The representation is equivariant to simultaneous permutation of lifecycle rows.
Routing position may index a factor in the chain; it must never become a fixed
member identity.

**Leakage guard.** The prohibition is not "the critic sees observation" — it is
**critic-to-actor information flow outside the detached scalar credit path**.
The fast path stays protected by the seven conditions the design already
declares: detached collection-time critic inputs; separate critic parameters or
a verified stop-gradient boundary; no critic-regression gradient to either
actor; advantage detached before the surrogate; no critic feature entering the
action mean; fast actor, `log_std`, base critic and immediate baseline frozen in
the delayed phase; and exact bitwise anchor invariance as an operational gate.

## 2. Stage A — is there a source action effect to identify?

Let `A*(h,a)` be the true within-history action advantage on the C1 action
support under the declared suffix policy, obtained by **paired replay** with
common random numbers. Define the conditional action-effect energy

```text
S_source = E_{h,a} [ ( A*(h,a) )^2 ]
```

Pass when the clustered 95% lower bound, after accounting for suffix Monte Carlo
uncertainty, exceeds the registered numerical resolution:

```text
LCB95( S_source ) > epsilon_audit^2
```

`epsilon_audit` is **only** the numerical / paired-rollout resolution floor. It
is not an effect-size threshold. A tiny but accurately measurable effect passes
identification; whether it is large enough to matter is the downstream behavior
gate's question, not this one. This is the exact error being retired.

Stage A separates three cases: a source locally action-insensitive on the
audited support; a source with a small but estimable marginal effect; and an
audit too noisy to decide.

### The probe distribution is the C1 action support, not the full grid

`E_{h,a}` is taken over the **C1 action support**, which is the *active* token
set — the same set the residual is centered over. An inactive routing position
carries no action into the environment, so `A*(h,a) = 0` there structurally, by
masking rather than by any property of the source.

Audit probe points must therefore be drawn only from `(t, position)` pairs where
that routing position is **active at that time**. Drawing uniformly from the
full `(horizon, capacity)` grid is a contract violation with a known sign: it
mixes structural zeros into the expectation, deflates `S_source`, and biases
Stage A toward `SOURCE_LOCAL_ACTION_EFFECT_NOT_IDENTIFIED` — a false negative on
identification, reported as a property of the source.

This is not hypothetical for the registered pair. G18 has `CAPACITY = 6` and
`HORIZON = 12` with a temporary-leave window at `t in [6, 10)`, so a large
fraction of the 72 grid cells hold no active member. A uniform-grid probe
distribution spends much of its budget measuring masking.

### P2 authority check

Let `s_res(h,a)` be **the score or Jacobian** seen by the centered residual
parameters — Pro's disjunction, restored verbatim; the first registration of
this contract dropped "or Jacobian" and thereby narrowed a choice Pro left
open. Either limb is contract-legal. The realized package takes the
action-space limb, `s_res = (raw_action - mean) / std^2`
(`residual_action_space_score`), so alignment in section 4 is measured in
action space rather than in residual parameter space. Any future switch to the
parameter-space Jacobian is a re-registration of this line, not a bug fix.

```text
g*_res = E[ s_res(h,a) * A*(h,a) ]
```

If `S_source > 0` but `|g*_res| = 0`, the source has an action effect lying
**outside P2's authority**. That is a source-authority mismatch, not a critic
failure. The prior derivation established the registered G18 constructive
direction is centered, so this is a fail-closed audit against accidental support
or clipping change, not a reopening of centering.

## 3. Stage B1 — did the critic identify the contrast?

On histories and action probes **never used to fit the critic**, center both the
oracle return response and the critic prediction within each history:

```text
g_hk = Gbar(h,a_k) - (1/K) * sum_l Gbar(h,a_l)
q_hk = Qhat(h,a_k) - (1/K) * sum_l Qhat(h,a_l)
```

**(1) Contrast alignment.**

```text
rho = E[q g] / sqrt( E[q^2] E[g^2] )        require LCB95(rho) > 0
```

**(2) Positive-scale recalibrated fit.** The policy loss normalizes advantages,
so a positive multiplicative scale error is not load-bearing. Fit a nonnegative
scalar on a calibration split and evaluate on the untouched audit split:

```text
alpha* = argmin_{alpha >= 0} E_cal[ (g - alpha q)^2 ]
R2_plus = 1 - E_audit[ (g - alpha* q)^2 ] / E_audit[ g^2 ]
                                            require LCB95(R2_plus) > 0
```

**Raw NMSE is retired as a gate** and retained as a diagnostic only. Pro's
reason, adopted: `q = 10g` fails raw NMSE while inducing the same normalized
actor direction, and `q = 0.01g` could pass.

## 4. Stage B2 — does the credit move the actor the right way?

A critic with some predictive skill may still interact badly with active-token
normalization, token ordering, the centered residual Jacobian, or the
score-function factorization. Compare directions:

```text
ghat_res = E[ s_res(h,a) * Ahat(h,a) ]
g*_res   = E[ s_res(h,a) * A*(h,a) ]

require |g*_res| > 0  and  LCB95( cos(ghat_res, g*_res) ) > 0
```

This is the direct distinction between a critic that recognizes action
dependence and one whose credit would actually move the residual correctly.

## 5. Data roles — three disjoint information streams

| Split | Used for | Never used for |
|---|---|---|
| `D_fit` | fitting `Q_j` under a frozen policy snapshot | crediting or auditing |
| `D_credit` | the qualified frozen critic's detached advantages driving the residual actor | fitting the critic before its own actor update |
| `D_audit` | paired action interventions and oracle contrasts for Stages A, B1, B2 | updating either critic or actor, ever |

Splits use disjoint episode / action / suffix random streams. Confidence
intervals are **clustered at the episode-ledger and suffix-replication level** —
active tokens are not independent samples.

Literal K-fold cross-fitting is **optional**. What is mandatory is out-of-sample
critic evaluation, no actor update from an unqualified critic, separation of fit
/ credit / audit information, and policy-snapshot consistency.

## 6. No actor update before qualification

> **No residual-actor update may occur until the critic has passed out-of-sample
> Stage B qualification under the policy snapshot whose actions it will credit.**

Mandatory. The delayed phase therefore opens with a **critic-only qualification
phase at the exact fast anchor**; the first residual update may occur only after
Stages A and B pass.

The retired screen violated this: it froze the advantage from the critic before
updating that critic, so the first delayed update credited from a randomly
initialized critic, moved the residual off zero, and changed the data
distribution before demonstrating any action-response skill. A late nonzero
Q-spread cannot retrospectively validate hundreds of earlier actor updates.

## 7. Policy-snapshot ownership

`Q^pi` changes when the policy changes. Fitting, credit generation and audit
must occur under **one frozen policy snapshot**; data from different policy
versions must never be pooled as though sharing one stationary `Q^pi`. The
snapshot version is part of the evidence record.

The screen must therefore either requalify the critic before each bounded
actor-update block under the new snapshot, or freeze a pre-registered block size
and demonstrate on `D_audit` that identification holds throughout that block.
**A final-only audit is insufficient.**

## 8. Result system — sequential, source-specific, first match

| # | Gate | Branch on failure | Smallest scientific update |
|---:|---|---|---|
| 1 | operational, replay, exact-history reconstruction, anonymity, leakage, suffix-policy contract | `INVALID_G20R2_EVIDENCE_CONTRACT` | implementation or estimand only |
| 2 | Stage A source-local action effect | `SOURCE_LOCAL_ACTION_EFFECT_NOT_IDENTIFIED_<source>` | that source / action-support / audit pair only; critic and P2 unjudged |
| 3 | oracle effect inside centered residual authority | `SOURCE_EFFECT_OUTSIDE_CENTERED_AUTHORITY_<source>` | P2 scope on that source; not a critic failure |
| 4 | Stage B1 held-out critic action-response skill | `NON_IDENTIFIED_ACTION_CRITIC_<source>` | this critic / input / training realization only |
| 5 | Stage B2 oracle-versus-learned residual-gradient alignment | `NON_IDENTIFIED_ACTION_CREDIT_DIRECTION_<source>` | this C1 factorization / normalization realization only |
| 6 | behavioral compatibility and delayed mechanism | existing behavior branches | only here can C1 behavior be supported or refuted |

Four separations exist before behavior is read at all: no measurable source
effect; effect outside P2 authority; critic failed to learn it; critic response
exists but points the actor wrong. The retired three-way taxonomy omitted the
second and fourth.

### Source-specific, never a global `all(...)`

The retired system required both sources to satisfy one global identification
Boolean. That is too coarse for the smallest claim, and it is the exact defect
the completed screen exhibited — G17's invalid normalization masked the G18 path
while every G17 compatibility threshold would have passed.

- **G18** identification and credit qualification are load-bearing before either
  a positive or a negative delayed-credit conclusion.
- **G17 identification failure with a behavioral pass** is diagnostic and must
  **not** mask a qualified G18 result. It supports the narrow statement that the
  trained residual did not destroy the fast controller in that run.
- **G17 identification failure with a behavioral failure** prevents attributing
  that failure to C1. The correct result is then "unqualified critic caused or
  may have caused compatibility loss", not C1 incompatibility.

## 9. Pre-freeze design check

Run per `AGENTS.md`, with the question this episode added.

1. **Signals at the mandated initial state** — the delayed phase now opens
   critic-only at the exact anchor, so no actor signal is consumed before
   qualification. Non-inertness of the residual gradient under an
   action-sensitive critic was demonstrated for G20R and is unchanged by this
   contract.
2. **Live gradient path at entry** — unchanged; the residual head's only path
   remains the detached member-resolved advantage weighting its own log-prob.
3. **Trivially satisfied invariants** — Stage A's floor is a numerical
   resolution bound, not an effect-size bound, so it cannot be passed by a
   source with no effect nor failed by one with a small measurable effect.
4. **Branch firing for a non-scientific reason** — the retired global Boolean is
   removed and branches are source-specific; gate 1 isolates contract failure
   from every scientific reading.
5. **Initialization cancelling the credit definition** — no; the anchor baseline
   is an expectation over resampled anchor actions.
6. **NEW — does the critic receive the variables the measured effect depends
   on?** This is the question whose absence produced the retired package. Under
   section 1 the critic receives the full masked per-member observation table,
   recurrent and membership state, and the member-paired ordered prefix. The
   check is discharged by construction, and any future narrowing of that input
   set re-opens it.

## 10. Files

- `ha_ctse_process/anchor_action_advantage_g20r2.py`
- `scripts/screen_anchor_action_advantage_g20r2.py`
- `tests/ha_ctse_process_anchor_action_advantage_g20r2_test.py`

The G20R package stays in the tree as the evidence that produced this ruling and
is not extended. `ha_ctse_process/continuous_roster_policy.py`, both source
modules and every closed result remain unchanged at their commits.

## 11. Screen constants

Behavioral thresholds and paired dual-source protocol are reused unchanged —
the source, compatibility claim and delayed-mechanism claim have not moved.
Identification constants and the qualification phase are new. Seeds are a fresh
block disjoint from every earlier package:

```text
g17_model=3019000
g17_train_ledger=3029000
g17_action=3039000
g17_evaluation_ledger=3049000
g17_evaluation_action=3059000
g17_audit=3069000
g18_model=3119000
g18_action=3139000
g18_audit=3149000
baseline_samples_K=8
```

### `epsilon_audit` is not yet registered — the screen is withheld

Section 2 gates Stage A on `LCB95(S_source) > epsilon_audit^2` and this section
froze no value for it. That is a defect in the first registration, not in the
implementation. The built package exposes `EPSILON_AUDIT = 1e-4` as a module
default and `scripts/screen_anchor_action_advantage_g20r2.py:887` calls
`stage_a_source_effect` without an explicit argument, so a run today would gate
identification on a number no document registers, and its Stage A branch would
not be interpretable.

**Derivation rule, registered here.** `epsilon_audit` is a measured property of
the audit estimator, never a chosen effect size.

The obvious null is wrong and is recorded here so it is not re-proposed.
Probing the factual action against itself under exact common random numbers
makes both arms bit-identical, returns exactly zero, and would register
`epsilon_audit = 0` — a floor no source could fail, which is precisely the
trivially-satisfied invariant section 9 question 3 forbids. Exact replay is a
strength of the pipeline here, not a measurement.

The registered null is a **replicate-split calibration**, because the noise
Stage A is actually exposed to is suffix Monte Carlo over the `K=8` anchor
resamples and the finite replicate count, not replay error. For a fixed
history and a fixed pair of distinct probe actions — the same pairing Stage A
uses, common random numbers intact — estimate `A*(h,a)` twice from **disjoint
suffix replicate sets**. The true difference between the two estimates is
exactly zero, so the observed difference is pure estimator resolution. With
`d` the observed difference between two half-sized estimates,

```text
epsilon_audit = upper tail of |d| / sqrt(2)
```

converts that difference back to the resolution of a single full-size estimate.

Four conditions make the number meaningful:

- the null must run at the **configured per-estimate Monte Carlo budget**
  (`K = 8` and the registered suffix replicate count), because that budget is
  what sets the resolution of a single `Ahat*` and a value measured under a
  different budget does not transfer. The **number of calibration points is not
  part of that budget** and must be raised well above the screen's own audit
  point count: those points do not change the resolution, they are draws *from*
  the resolution distribution, and estimating a 95th-percentile tail from the
  screen's ~24 points registers noise rather than a floor. This distinction was
  missed in the first statement of this rule, which conflated the two;
- the null must be drawn on the **C1 action support** defined above, since a
  probe on an inactive position returns an exact zero that describes masking
  rather than estimator resolution, and a calibration set half-full of such
  zeros collapses the tail onto a single extreme point;
- it is measured **per source**, since G17 and G18 have different return scales;
- the resulting value is written back into this section as a frozen constant
  before any screen run, and the screen must pass it **explicitly** — the module
  default must be made unreachable, so a missing registration fails closed
  rather than silently substituting `1e-4`.

The null calibration is a bounded measurement of estimator resolution, not the
screen, and it consumes no iteration. It produces one number per source and no
scientific reading whatsoever.

No run is authorized by this document. The screen stays withheld until
`epsilon_audit` is registered above by that calibration.
