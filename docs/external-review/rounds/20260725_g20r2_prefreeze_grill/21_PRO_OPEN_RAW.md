# Scientific ruling — G20R2 pre-freeze grill

**Stage reviewed:** `c2c99b642bdc6601d73dbf340438327bebecddaf`

## Overall verdict

**CHANGES_REQUIRED. The G20R2 bounded screen may not run under the current contract or implementation.**

The high-level G20R2 direction remains scientifically live:

* the exact-zero fast anchor remains valid;
* active-set centering remains valid within its registered scope;
* C1 remains unresolved rather than refuted;
* P2 remains untested.

My rulings are:

| Question | Ruling                                                                                                                                                                                                                                                                                                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q1**   | Snapshot consistency is load-bearing, but I do **not** approve a separately calibrated scalar `epsilon_audit` as the primary Stage A correction. Use an in-situ, cross-replicate unbiased estimator of action-effect energy. If a scalar resolution floor is retained as a secondary implementation, its procedure—not its value—is pre-registered, and its data must be disjoint from Stage A. |
| **Q2**   | Yes, the relevant support is the **active, likelihood-bearing, residual-controllable token set**. The same restriction binds Stage A, B1, B2, and any resolution calibration. Support alone is insufficient: the sampling measure over that support must also be frozen.                                                                                                                        |
| **Q3**   | Genuine zero-effect active tokens remain in the estimand. They must not be removed using observed (A^\star). The current binary Stage A failure is too coarse and must distinguish unresolved evidence from a genuinely concentrated effect pattern.                                                                                                                                            |
| **Q4**   | No. The current action-space cosine is insufficient for the claim that the residual actor will move in the correct direction. Stage B2 must compare gradients in the parameter space of **all residual-actor parameters updated by the delayed policy loss**.                                                                                                                                   |
| **Q5**   | No screen yet. In addition to the Q1–Q4 changes, the assembled audit does not hold the token history fixed, policy requalification after residual movement is absent, and identification failure currently raises instead of producing its registered branch.                                                                                                                                   |

---

# Q1 — `epsilon_audit`

## Ruling: freeze an in-situ procedure, not a numerical constant—but replace the current scalar-floor construction

The Project Manager is correct about the central temporal point: audit resolution depends on the suffix policy being evaluated. A number measured under an untrained policy cannot describe a Stage A audit performed after fast-policy training. The contract already treats (Q^\pi) and the audit as policy-snapshot-owned objects, and the two observed untrained-policy calibration values are large enough relative to the prior G20R quantities that snapshot mismatch could decide the branch by itself.

Therefore:

> **A fixed numerical constant measured before the trained fast anchor exists is not scientifically preferable.**

Pre-registration should freeze:

* the policy snapshot at which the audit occurs;
* the action-probe distribution;
* the suffix continuation policy;
* the number of suffix replicates;
* the episode and history distribution;
* the clustering unit;
* and the inferential rule.

It need not freeze the realized noise scale.

## The current calibration does not estimate the same quantity Stage A gates

The present Stage A implementation first estimates returns for (K=8) actions at one history, then centers all eight returns within that history:

[
\widehat A_{hk}
===============

## \widehat G(h,a_k)

\frac1K\sum_{\ell=1}^{K}\widehat G(h,a_\ell).
]

The calibration instead selects the first two actions, estimates their pairwise contrast twice, and uses

[
\frac{\left|\widehat\Delta^{(1)}-\widehat\Delta^{(2)}\right|}{\sqrt 2}.
]

These are not the same estimator. The variance of a two-action contrast is generally not the variance of one member of a (K)-action centered table, because the latter contains the shared estimated mean and action-to-action covariance induced by common random numbers. Squaring a 95th percentile of the former is also not a naturally matched null for the **mean squared** statistic used by Stage A.

The calibration’s statement that the folded quantity (|d|/\sqrt 2) has exactly the same distributional resolution as one full-size estimate also requires stronger distributional assumptions than are registered. Division by (\sqrt 2) matches variance for the unfurled difference of independent equal-variance errors; it does not make the entire absolute-error distribution identical for arbitrary finite-sample suffix returns.

## Preferred replacement: cross-replicate action-effect energy

For each fixed history and fixed set of (K) probe actions, use two disjoint suffix-replicate sets to obtain two independent estimates:

[
\widehat A^{(1)}_{hk}
=====================

A^\star_{hk}+e^{(1)}*{hk},
\qquad
\widehat A^{(2)}*{hk}
=====================

A^\star_{hk}+e^{(2)}_{hk}.
]

Both estimates must use the **same within-history (K)-action centering rule** as the actual Stage A estimand.

Then estimate:

[
\boxed{
S_{\mathrm{source}}^\times
==========================

\mathbb E_{h,k}
\left[
\widehat A^{(1)}*{hk}
\widehat A^{(2)}*{hk}
\right]
}
]

With disjoint, conditionally independent suffix-replicate sets and unbiased return estimates,

[
\mathbb E
\left[
\widehat A^{(1)}*{hk}
\widehat A^{(2)}*{hk}
\mid h,a_k
\right]
=======

\left(A^\star_{hk}\right)^2.
]

Thus the cross-product directly estimates the desired action-effect energy without the positive noise bias in

[
\mathbb E[(\widehat A)^2].
]

Stage A should pass when the clustered lower confidence bound satisfies

[
\operatorname{LCB}*{95}
\left(
S*{\mathrm{source}}^\times
\right)>0.
]

This has several advantages:

* no arbitrary numerical effect-size threshold;
* no comparison of unlike statistics;
* no policy-external fixed constant;
* finite suffix uncertainty is incorporated into the confidence interval;
* a truly zero effect has expectation zero rather than positive squared-noise bias;
* a small but accurately estimated effect can pass.

A separately reported replicate-difference distribution may remain as an audit-quality diagnostic, but it should not be the primary Stage A gate.

### Acceptable fallback if the repository retains `epsilon_audit`

If the existing form must be retained, then define its square in the units of Stage A:

[
N_{\mathrm{audit}}
==================

\mathbb E_{h,k}
\left[
\frac{
\left(
\widehat A^{(1)}_{hk}
---------------------

\widehat A^{(2)}_{hk}
\right)^2
}{2}
\right],
]

and freeze

[
\epsilon_{\mathrm{audit}}^2
===========================

\operatorname{UCB}*{95}
\left(
N*{\mathrm{audit}}
\right).
]

Then compare

[
\operatorname{LCB}*{95}(S*{\mathrm{observed}})

>

\epsilon_{\mathrm{audit}}^2.
]

This fallback still requires the exact (K)-action centered estimator. The current first-two-action upper-tail calibration is not sufficient.

## Q1a — Disjoint calibration data

Under either scalar-floor fallback or any separately estimated noise model, **calibration episode-ledger clusters must be disjoint from the Stage A effect-audit clusters**.

Using the same clusters is not inherently impossible, but it would require one jointly registered inferential procedure that resamples the dependence between the threshold and the statistic. The current architecture treats them as separate quantities and then plugs the first into the second. Under that architecture, data reuse would allow unusually quiet or noisy histories to affect both sides of their own gate.

The current choice of the same policy snapshot but disjoint episode blocks is therefore correct. The code already records and tests this disjointness.

Under my preferred cross-product estimator, the separate calibration block becomes unnecessary; the two suffix-replicate sets live inside `D_audit` and are never used for actor or critic training.

## Q1b — Fixed constant

This conditional does not apply because I do not require a fixed constant.

No pre-existing policy would be an acceptable substitute for the trained fast-anchor snapshot. Measuring under an untrained model would answer a different policy-conditional audit question.

## Q1c — Self versus self

The rejection is confirmed.

A factual action compared with itself under exact common random numbers measures:

* exact environment reconstruction;
* RNG replay;
* numerical determinism;
* and implementation equality.

Those are valuable operational checks. They do not measure Monte Carlo resolution of a **nontrivial action contrast**. Because both arms are bit-identical, the result is deterministically zero and cannot distinguish a genuinely effect-free source from an audit with infinite precision. The current design correctly recognizes that such a floor is trivially satisfied.

---

# Q2 — What is the C1 action support?

## Ruling: yes, with one refinement

The relevant support is:

> **The set of active, likelihood-bearing tokens for which the delayed residual parameterization can change the executed action distribution.**

Inactive routing positions must be excluded because they:

* receive no physical action;
* contribute no token likelihood;
* receive zero residual by mask;
* and cannot carry an actor score.

The former unrestricted sampler placed a large fraction of G18 probes on inactive rows; the repaired sampler correctly constructs only positions satisfying `position < active_count`.

The refinement matters for a general contract: an active token can still be outside residual authority if the active-set projection makes its residual Jacobian identically zero—for example, a singleton active set. The registered G17/G18 sources retain at least two active members, so “active token” and “residual-controllable token” coincide here. The generic definition should nevertheless state both.

## Q2a — Does the restriction bind B1 and B2?

**Yes. It binds every stage and the resolution estimator.**

### Stage A

Stage A asks whether there is an action effect on the action decisions the algorithm can actually make.

### Stage B1

A critic should be evaluated on the same decision support on which its output will be used for actor credit. Penalizing it for inactive action factors—or rewarding it for arbitrary variation there—has no scientific meaning.

### Stage B2

The residual gradient is defined only through likelihood-bearing, trainable action factors. Structurally masked positions contribute neither oracle nor learned actor direction.

### Resolution calibration

A calibration point on an inactive row measures mask determinism rather than suffix-estimation noise. Such points would falsely collapse the estimated noise floor.

Therefore the same token support binds all four objects:

* Stage A;
* Stage B1;
* Stage B2;
* and any calibration/null estimator.

## Support is not the same as the sampling measure

The current G18 sampler always inserts `(t=0, position=0)` and fills the remaining two points by uniform active-token sampling.

That is not a uniform expectation over active tokens. It is a mixture that assigns one third of each episode’s audit mass to the known pivotal point.

This is scientifically load-bearing because Q3 concerns how much zero-effect mass enters (S_{\mathrm{source}}). The contract must therefore freeze the **measure**, not merely its support.

My preferred measure is the active-token occupancy induced by the frozen audited policy:

[
\mu_{\mathrm{C1}}(h,j)
\propto
\Pr_{\pi^{(v)}}(h)
\mathbf 1{j\text{ active and residual-controllable}}.
]

The known G18 first-action intervention should remain a separate constructive source control, not be silently overweighted inside the population Stage A statistic. G18 already contains a direct equal-immediate-service, different-future-return intervention for that purpose.

Alternatively, the forced-pivotal mixture can remain, but then:

* its exact mixture weights must be frozen;
* every Stage A/B1/B2 claim must be explicitly limited to that mixture;
* and it must not be described as an average over natural active-token occupancy.

At later policy snapshots, the finite action-probe distribution must cover both the current policy’s factual action region and the frozen anchor-policy baseline region. At the exact anchor these coincide; after the residual moves they need not.

---

# Q3 — Genuine zero marginal effects at active tokens

## Ruling: retain them

A genuine zero-effect active token remains in (S_{\mathrm{source}}).

The G18 saturation case is scientifically meaningful: when other active members already clear demand, changing one additional member’s effort can have no effect on immediate or future return for that history. The source computes service as a capped function of aggregate executed effort, so such flat regions are inherent in its causal geometry rather than masking artifacts.

Removing a point because the observed (A^\star) is zero would be circular:

1. estimate the quantity whose population distribution is being tested;
2. condition inclusion on that estimate;
3. then claim the conditioned distribution identifies the original population effect.

It would systematically inflate effect density and turn Stage A into “is there an effect after discarding histories without an effect?”

Structural zeros also matter to the final algorithm. A credit mechanism that is informative only at a minority of natural decisions has a different learnability profile from one that is informative at nearly every decision.

## Q3a — Result mapping

The present binary Stage A mapping is too coarse.

Failure of

[
\operatorname{LCB}_{95}(S)>0
]

does not establish that the action effect is zero everywhere. It may mean:

* the effect is absent;
* it is concentrated on a minority of histories;
* the audit is underpowered;
* or the effect exists but lies below the audit’s current resolution.

The mapping should have at least three inferential states:

### 1. `SOURCE_ACTION_EFFECT_IDENTIFIED_<source>`

[
\operatorname{LCB}_{95}(S^\times)>0.
]

Stage A passes.

### 2. `SOURCE_ACTION_EFFECT_UNRESOLVED_<source>`

The confidence interval includes zero.

Smallest claim:

> Under the registered active-token measure and audit budget, the source’s conditional action-effect energy was not positively identified. The source, critic, C1 and P2 remain unjudged.

This is the ordinary outcome when evidence is compatible with both zero and nonzero energy.

### 3. `SOURCE_ACTION_EFFECT_BELOW_AUDIT_RESOLUTION_ON_REGISTERED_MEASURE_<source>`

This requires an equivalence-style upper bound showing that the action-effect energy is below the registered numerical-resolution region. It means:

> The source does not expose a resolvable aggregate action effect under the registered active-token measure and audit contract.

It still does **not** mean “no action effect anywhere.”

## Concentrated-effect classification

A separate `SOURCE_ACTION_EFFECT_CONCENTRATED_<source>` branch is legitimate only if a heterogeneity statistic is pre-registered.

One suitable diagnostic is to form per-history effect energies

[
S_h
===

\frac1K
\sum_k
A^\star(h,a_k)^2
]

and estimate the responsive-history mass

[
p_{\mathrm{resp}}
=================

\Pr_h
\left(
S_h
\text{ exceeds its matched null resolution}
\right).
]

If:

* the aggregate Stage A effect is unresolved;
* but a positive lower confidence bound establishes (p_{\mathrm{resp}}>0);

then the smallest supported claim is:

> The source contains identifiable action effects on a nonzero subset of active histories, but the effect is too concentrated to support an unconditional active-token identification claim under the registered audit measure and budget.

That is a source-suitability result, not evidence against C1.

The current audit budget—eight episodes and three probe histories per episode—may be too small for a reliable prevalence branch. If no adequately powered heterogeneity statistic is frozen, use `UNRESOLVED`; do not infer concentration from the observed zero fraction alone.

## Q3c — Meaning of a G18 Stage A failure

A G18 Stage A failure gives **no update to C1 or P2**.

G18’s own constructive information gate already contains a specific action intervention with equal immediate service and different later battery and utility consequences.

Therefore an aggregate Stage A failure would update:

* the chosen G18 audit distribution;
* the audit budget;
* the density of informative histories;
* or G18’s suitability as an unconditional identification carrier.

It cannot support “G18 has no action effect,” and it cannot refute the C1 action-advantage estimator.

---

# Q4 — Action-space versus parameter-space Stage B2

## Ruling: the current action-space limb is insufficient for the intended claim

The implemented score is

[
s_a
===

\frac{u-\mu}{\sigma^2},
]

the Gaussian pre-tanh location score. The implementation aggregates

[
\widehat g_a
============

\mathbb E[s_a\widehat A],
\qquad
g^\star_a
=========

\mathbb E[s_a A^\star]
]

into an `action_dim`-dimensional vector and compares their cosine.

That supports the narrower statement:

> Learned and oracle advantages induce aligned average Gaussian-mean score directions in primitive action coordinates.

It does **not** establish that the trainable residual network will move in the same parameter-space direction.

## Why the “shared Jacobian” implication does not hold

The actual parameter gradient is of the form

[
g_\theta
========

\mathbb E_n
\left[
J_\theta(h_n)^\top
P_{\mathrm{center}}(h_n)^\top
s_a(h_n,a_n)
A_n
\right],
]

where:

* (P_{\mathrm{center}}) is the active-set-centering map;
* (J_\theta(h_n)) is the observation-dependent Jacobian of the residual MLP;
* and (n) indexes histories, members and actions.

The residual is produced by an observation-dependent neural network and then centered jointly across active members.

Thus (J_\theta(h_n)) is not one common fixed Jacobian that can be factored outside the expectation. It varies by:

* observation;
* hidden activation;
* member;
* roster;
* and policy snapshot.

In general,

[
\cos
\left(
\mathbb E[s_a\widehat A],
\mathbb E[s_a A^\star]
\right)>0
]

does not imply

[
\cos
\left(
\mathbb E[J^\top P^\top s_a\widehat A],
\mathbb E[J^\top P^\top s_a A^\star]
\right)>0.
]

A varying Jacobian can reweight or rotate contributions from different histories so that action-coordinate aggregates align while parameter gradients do not.

The centering map creates an additional issue: changing one raw residual output changes every active member’s centered mean. A per-token unprojected location score does not by itself represent that coupled parameter authority.

## Q4b — Required parameter subset

Stage B2 should compare gradients over:

> **Every residual-actor parameter that the delayed policy optimizer updates.**

In the current package that is the complete parameter set returned by `residual_parameters()`—both layers of the observation-conditioned delayed residual head. The fast actor is frozen, and critic parameters belong to a different optimizer and are excluded.

Define the two directions using the actual actor-loss functional:

[
\widehat g_\theta
=================

\nabla_\theta
L_{\mathrm{actor}}
\left(
\theta;\widehat A
\right)
\bigg|_{\theta=\theta_v},
]

[
g^\star_\theta
==============

\nabla_\theta
L_{\mathrm{actor}}
\left(
\theta;A^\star
\right)
\bigg|_{\theta=\theta_v}.
]

The two losses must use exactly the same:

* replayed actions;
* likelihood masks;
* active-token normalization;
* advantage-centering and scaling rule;
* PPO ratio and clipping rule;
* active-set-centering graph;
* and residual parameterization.

Then require:

[
\left|g^\star_\theta\right|>0,
\qquad
\operatorname{LCB}*{95}
\left[
\cos
\left(
\widehat g*\theta,g^\star_\theta
\right)
\right]>0.
]

This directly tests the claim Stage B2 was introduced to test.

The action-space cosine may remain as a diagnostic that localizes a failure:

* action-space aligned, parameter-space misaligned → representation/Jacobian problem;
* both misaligned → credit problem upstream of the residual representation.

## Optimizer state after the first actor block

At the initial delayed update, Adam’s moments are zero, so gradient alignment is a reasonable proxy for update alignment.

After residual updates, persistent Adam moments can make the applied update differ from the current raw gradient. If later policy snapshots are requalified while preserving optimizer state, the contract must either:

* compare the actual preconditioned optimizer-step directions;
* or explicitly reset and re-register optimizer state at each qualified block.

This cannot remain implicit.

---

# Q5 — May the bounded screen run?

## No

The current screen is not yet capable of producing an interpretable Stage A/B1/B2 result, even if the explicit Q1–Q4 choices are patched.

## Blocker 1 — The paired oracle audit does not keep (h_j) fixed

The audit contract requires positions before token (j) at the intervention timestep to remain part of the fixed pre-action history. The previous ruling explicitly required the earlier token actions, routing order, hidden state and policy snapshot to be preserved while only the suffix is resampled.

The implementation instead performs:

```python
suffix_noise[intervention_time:] = ...
```

which replaces the noise for **every member at the intervention timestep**, including positions strictly before (j).

Consequences:

* earlier same-step actions vary across suffix replicates;
* the action prefix seen by token (j) varies;
* (h_j) is not fixed;
* the intervention mean can vary across replicates;
* and the oracle return is averaging over different decision histories rather than estimating (\bar G(h_j,a_j)) at one history.

The critic response is then evaluated using `_replay_decision_history` with the original `prefix_noise`, so the critic and oracle can be evaluated at different prefixes.

This invalidates Stage A, B1, B2, and the current resolution calibration.

The corrected suffix split at time (t) must be:

* positions (<j): fixed factual prefix noise/actions;
* position (j): forced probe action;
* positions (>j): suffix-policy randomness, common across action probes within a replicate;
* times (>t): suffix-policy randomness, common across action probes within a replicate.

## Blocker 2 — The Stage A null does not match Stage A’s estimator

As ruled under Q1, pairwise first-two-action contrast noise cannot gate the (K)-action centered energy without an additional derivation. The current calibration and Stage A must be replaced by the same-estimator cross-replicate construction.

## Blocker 3 — Stage A failure semantics are still binary

The current code records only `passed = lcb > threshold`.

It has no upper confidence bound and cannot distinguish:

* contradicted/below-resolution;
* concentrated;
* and underpowered/unresolved.

The result system must preserve those distinct interpretations. The project’s durable evidence contract explicitly says mixed and underpowered results preserve unresolved explanations rather than selecting a negative mechanism conclusion.

The same issue applies to B1 and B2:

* a positive point estimate whose LCB crosses zero is underpowered;
* an upper bound at or below zero is genuine non-identification or anti-alignment.

Those should not receive the same smallest proposition.

## Blocker 4 — Stage B2 is in the wrong space

The action-space gate must be replaced with the residual-parameter gradient gate ruled above.

## Blocker 5 — Policy-snapshot requalification is absent

The frozen design says that after the policy changes, (Q^\pi) changes. It requires either:

* requalification before every bounded actor-update block;
* or a frozen block size with evidence that identification remains valid throughout that block.

A final-only audit is explicitly insufficient.

The assembled screen performs one qualification and one identification audit at the exact anchor, then executes all delayed updates—100 for G17 and 300 for G18—without further qualification.

The contract therefore needs to freeze:

* actor-update block size;
* requalification timing;
* policy/action probe support at each new snapshot;
* critic-fit and audit data for each block;
* and whether Stage B2 compares gradients or Adam-applied updates.

## Blocker 6 — Identification failure does not reach the registered branch

`begin_delayed_phase` raises unless `stage_b_passed=True`.

The screen nevertheless calls:

```python
model.begin_delayed_phase(stage_b_passed=stage_b_passed)
```

unconditionally after identification.

If Stage A, the authority gate, B1 or B2 fails, the source run raises before it can return the source-specific first-match branch. Because G17 is processed before G18, a G17 qualification failure can also prevent the independent G18 source from running at all.

This contradicts both:

* the “no actor update before qualification” rule;
* and the source-specific result system.

An identification failure must terminate that source cleanly, emit its registered branch and perform no residual update. It must not become an operational exception.

The existing G17 “diagnostic compatibility pass under an unqualified critic” also needs clarification. If the critic does not qualify, the residual actor cannot legally train; evaluating the unchanged anchor afterward is not evidence that a **trained residual** preserved G17. It is only an anchor regression. The branch should retain the precise identification failure rather than replace it with a generic diagnostic compatibility label.

## Blocker 7 — The audit measure is not fully registered

The contract freezes the active support but not the exact history weighting. The forced G18 pivotal point changes (S_{\mathrm{source}}), its structural-zero fraction and its confidence interval. The audit must freeze either:

* natural active-token occupancy;
* uniform active-token sampling;
* or the exact forced-pivot mixture and weights.

My ruling prefers natural active-token occupancy with the pivotal intervention reported separately.

At later policy snapshots the action probes must include the current policy region as well as the frozen anchor baseline region.

## Blocker 8 — `M_t` needs an exact equivalence statement

The scientific contract names active, lifecycle and membership-transition state as part of (H^Q). The implementation passes the active mask explicitly and relies on observation columns for age, previous effort, rotating status and phase.

This may be information-equivalent for the two registered sources, but the contract should say so explicitly and identify which current membership-transition information is recoverable from (X_t) and (R_t). Otherwise the design says `M_t` is supplied while the implementation supplies only a subset and an undocumented equivalence assumption.

This need not require a new source field if equivalence is established; it does require a frozen semantic statement.

## Blocker 9 — No assembled-path exercise has occurred

The repository states that `run_screen` has never been executed end to end at any scale.

That disclosure is now material because the assembled path contains at least one definite branch-reachability defect and one fixed-history defect not exposed by isolated tests.

After the protected-semantic corrections are made, one proof-sized, non-conclusion-bearing end-to-end exercise should establish:

* successful qualification path;
* Stage A failure path;
* B1/B2 failure path;
* clean source-local termination;
* independent continuation to the second source;
* snapshot requalification;
* and result serialization.

It must not be interpreted as the bounded screen or used to tune thresholds.

---

# Smallest portfolio updates

## Refuted or retired

1. **Current pairwise `epsilon_audit` calibration as the gate for (K)-centered Stage A energy.**
2. **Action-space cosine as sufficient evidence of residual-parameter update alignment.**
3. **The current assembled G20R2 screen as an interpretable evidence path.**
4. **A binary Stage A failure interpreted as absence of source action effect.**

## Not refuted

* C1 as a conditional action-advantage estimator;
* P2 active-set authority decomposition;
* exact-zero anchor initialization;
* active-set centering on the registered G18 scope;
* the complete anonymous (Q_j) information contract in principle.

## Retained diagnostic alternatives

* action-space gradient alignment may remain as a localization diagnostic;
* replicate-difference calibration may remain as an audit-noise diagnostic;
* the G18 pivotal intervention remains a constructive source control;
* structural-zero prevalence should be reported as a source-density diagnostic.

---

# Final disposition

**The G20R2 screen remains withheld.**

The next scientific artifact should amend the frozen contract to include:

1. cross-replicate Stage A effect-energy identification;
2. the exact active-token sampling measure;
3. structural-zero and unresolved-result semantics;
4. parameter-space Stage B2;
5. fixed token-history suffix replay;
6. policy-snapshot requalification blocks;
7. clean source-local failure termination;
8. and the precise `M_t` information-equivalence statement.

Once those protected semantics are fixed, the orchestrator owns their implementation and verification. This response itself authorizes neither implementation nor bounded or formal compute.
