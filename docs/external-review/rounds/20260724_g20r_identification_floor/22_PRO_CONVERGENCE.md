# Reconsidered scientific ruling — G20R identification floor

**Stage remains:** `52d89863f02c9a86520952d086a26b58ce8caf3d`

The central direction of my earlier answer stands:

1. the registered `Q-spread / slow-return-std` floor is invalid;
2. changing only that numerical floor is insufficient;
3. the disclosed G18 behavior does not refute P2 or the mathematical C1 estimator;
4. P2 remains untested.

On fuller review, however, I would make **four material refinements**:

* Replace the “single floor” with a sequential **source-effect → critic-identification → actor-credit-direction** qualification.
* Do **not** use raw, uncalibrated `NMSE < 1` as a mandatory criterion. Because the actor normalizes advantages, positive scale error is not itself disqualifying; use held-out positive-scale predictive skill plus gradient-direction agreement.
* The critic-information defect is substantially broader than the first two missing G18 fields I named. It also omits the full member observation table, recurrent/lifecycle state, G17 focal capacity, and the member-labelled action prefix; the present critic receives only a prefix **sum**.
* Held-out qualification and “no actor update before critic qualification” are mandatory. Literal (K)-fold cross-fitting is one acceptable realization, but is not itself the protected semantic requirement.

I would also narrow my previous statement that the G18 reading lowers C1’s scientific plausibility. It raises the **implementation and evidence risk** of C1, but, because the declared (h_j) was not actually instantiated and the actor was allowed to move under an unqualified critic, it supplies no formal mechanism-level update to C1.

---

## 1. What the present screen actually established

The screen established two clean facts:

* the zero fixed point was repaired—the residual output moved on both sources;
* the frozen fast anchor remained bitwise unchanged with exact replay.

It did **not** establish critic identification. Its registered statistic was merely the standard deviation of the learned (Q_j) across eight resampled anchor actions, compared with one per cent of the raw slow-return standard deviation. The former is within-state action sensitivity; the latter is mostly between-state return variation. Their ratio therefore has no stable identification meaning.

More importantly, a nonzero (Q)-spread does not establish that:

* the sign of the action effect is correct;
* the relative member effects are correct;
* the critic predicts the true conditional action contrast;
* or the resulting residual-head update points in the oracle policy-gradient direction.

A random or systematically wrong critic can have large spread. The disclosed G18 pattern—old floor passed, while utility and rotating-member effort moved sharply in the wrong direction—is a concrete warning that **variation is not identification**, although first-match precedence means those behavioral numbers were not registered as a result against P2.

---

# 2. Question 1 — How should identification be defined?

## Decision: replace the scalar floor with a sequential qualification protocol

The object to identify is not raw (Q)-variation. It is the action-dependent component of the slow return under the same pre-action decision history and the declared continuation policy.

Let (h_{j,t}) denote the complete pre-action history for routing position (j), and let

[
\bar G(h_{j,t},a)
=================

\mathbb E_{\zeta}
\left[
G^{\text{slow}}*t
\mid h*{j,t},a,\zeta
\right]
]

denote the expected slow return when token (j) takes action (a), with the suffix and later policy execution generated under the frozen policy snapshot being audited. The variable (\zeta) denotes suffix and later policy randomness, not a different environment state.

For each frozen history, evaluate a pre-registered set of action probes containing the relevant anchor and current-policy support. Define the within-history oracle action advantage

[
A^\star(h,a)
============

## \bar G(h,a)

\mathbb E_{\tilde a\sim\pi_0(\cdot\mid h)}
\bar G(h,\tilde a).
]

This is the true counterpart of C1’s learned advantage

[
\widehat A(h,a)
===============

## \widehat Q(h,a)

\mathbb E_{\tilde a\sim\pi_0(\cdot\mid h)}
\widehat Q(h,\tilde a).
]

The registered identification process should then be:

---

## Stage A — Is there a source action effect to identify?

Define

[
S_{\mathrm{source}}
===================

\mathbb E_{h,a}
\left[
\left(A^\star(h,a)\right)^2
\right].
]

Pass Stage A only when the clustered 95% lower confidence bound for the **conditional action-effect energy**, after accounting for suffix Monte Carlo uncertainty, is above the numerical replay/noise floor:

[
\operatorname{LCB}*{95}!\left(S*{\mathrm{source}}\right)

>

\epsilon_{\mathrm{audit}}^2.
]

Here (\epsilon_{\mathrm{audit}}) is only the registered numerical or paired-rollout resolution. It is not an effect-size threshold such as “one per cent of total return variance.”

This separates:

* a source whose return is locally action-insensitive on the audited support;
* from a source with a small but estimable marginal action effect;
* from a source where the available audit is too noisy to decide.

A tiny but accurately measurable effect passes identification. Whether it is large enough to meet the behavioral utility margin belongs to the downstream behavior gate, not the identification gate.

### Additional P2 authority check

For P2, the source effect must also have a nonzero component in the trainable active-set-centered authority. Let (s^{\mathrm{res}}(h,a)) denote the score or Jacobian seen by the centered residual parameters. Define the oracle residual-head direction

[
g^\star_{\mathrm{res}}
======================

\mathbb E
\left[
s^{\mathrm{res}}(h,a)A^\star(h,a)
\right].
]

If (S_{\mathrm{source}}>0) but

[
\left|g^\star_{\mathrm{res}}\right|=0,
]

then the source contains an action effect, but that effect lies outside P2’s authority. That is **not** a critic failure. It is a source–authority mismatch. The prior derivation established that the registered G18 constructive direction is centered, so this is mainly a fail-closed audit against accidental support or clipping changes rather than a reopening of centering.

---

## Stage B1 — Did the critic identify the source action contrast?

On histories and action probes never used to fit the critic, center both the oracle return response and critic prediction within each history:

[
g_{hk}
======

## \bar G(h,a_k)

\frac{1}{K}\sum_{\ell=1}^{K}\bar G(h,a_\ell),
]

[
q_{hk}
======

## \widehat Q(h,a_k)

\frac{1}{K}\sum_{\ell=1}^{K}\widehat Q(h,a_\ell).
]

The load-bearing test should be out-of-sample predictive and directional.

First require positive contrast alignment:

[
\rho_{\Delta}
=============

\frac{\mathbb E[qg]}
{\sqrt{\mathbb E[q^2]\mathbb E[g^2]}},
\qquad
\operatorname{LCB}*{95}(\rho*{\Delta})>0.
]

Second, because the policy loss normalizes advantages, do not reject a critic merely for a positive multiplicative scale error. Fit a nonnegative scalar (\alpha) on a calibration split and evaluate it on the untouched audit split:

[
\alpha^\star
============

\arg\min_{\alpha\ge 0}
\mathbb E_{\mathrm{cal}}
\left[
(g-\alpha q)^2
\right],
]

[
R^2_{+,\mathrm{audit}}
======================

1-
\frac{
\mathbb E_{\mathrm{audit}}
[(g-\alpha^\star q)^2]
}{
\mathbb E_{\mathrm{audit}}[g^2]
}.
]

Require

[
\operatorname{LCB}*{95}
\left(
R^2*{+,\mathrm{audit}}
\right)>0.
]

This asks whether the learned action response is better than the zero-action-effect predictor after allowing the positive scale freedom that the normalized actor loss makes non-load-bearing.

### Revision to my previous NMSE proposal

My previous raw criterion

[
\operatorname{UCB}_{95}(\mathrm{NMSE})<1
]

was directionally useful but too rigid as a mandatory rule if calculated without positive rescaling. A critic satisfying (q=10g) would fail raw NMSE despite inducing the same normalized actor direction; a critic satisfying (q=0.01g) could pass. I would therefore retain raw NMSE as a diagnostic and replace it as a gate with the held-out, positively recalibrated (R^2) above.

---

## Stage B2 — Does the identified critic produce the correct actor direction?

Even a critic with some predictive action skill may interact badly with:

* active-token normalization;
* token ordering;
* the centered residual Jacobian;
* and the score-function factorization.

Therefore compare the critic-induced actor direction with the oracle paired-return direction:

[
\widehat g_{\mathrm{res}}
=========================

\mathbb E
\left[
s^{\mathrm{res}}(h,a)\widehat A(h,a)
\right],
]

[
g^\star_{\mathrm{res}}
======================

\mathbb E
\left[
s^{\mathrm{res}}(h,a)A^\star(h,a)
\right].
]

Require a nonzero oracle direction and positive held-out cosine:

[
\operatorname{LCB}*{95}
\left(
\frac{
\langle \widehat g*{\mathrm{res}},g^\star_{\mathrm{res}}\rangle
}{
|\widehat g_{\mathrm{res}}|
|g^\star_{\mathrm{res}}|
}
\right)>0.
]

This is the most direct distinction between:

* a critic that recognizes some action dependence;
* and a critic whose credit would actually move the residual actor in the correct direction.

The project’s evidence principles require mechanism identifiability to be separated from behavior and require the measurement itself to be corrected when it cannot identify its proposition.

---

# 3. Question (a) — Does Stage A require exact state reset?

## Yes, in its strongest form—but both registered sources can supply it by deterministic reconstruction

Stage A requires two or more action interventions beginning from the same pre-action environment and policy history. It does **not** require a dedicated `clone_state()` method if exact state can be reconstructed from the start of the episode.

### G18

G18 already demonstrates the required construction at (t=0):

* two new environments receive the same immutable ledger;
* one receives the constructive first action;
* the other receives the counterfactual first action;
* immediate service is equal;
* both then receive the same deterministic constructive continuation;
* the later return differs.

For an arbitrary later history, the environment can be reconstructed by creating a new `BatteryRosterEnv` from the same ledger and replaying the identical action prefix. Its state variables—time, active and charging masks, battery, previous effort and age—are deterministic functions of the ledger and past actions.

Thus G18 satisfies exact paired reconstruction under its present source semantics.

### G17

G17 pre-generates all exogenous variation in the immutable ledger:

* capacities;
* load;
* target mix;
* presentation priority;
* membership events.

Those values are deterministic functions of `master_seed`, `episode_id` and stream index. The environment transition is then deterministic given the action sequence.

The actor’s stochastic action noise is likewise pre-generated deterministically from episode and action seed.

Consequently, two fresh G17 environments with the same ledger and identical pre-intervention actions reconstruct the same state exactly. The current package also reports exact policy replay and a bitwise-preserved anchor, confirming that the pre-action policy history is reproducible rather than merely approximately recoverable.

### Token-level branching

For a token (j) inside one environment step, the paired audit must additionally preserve:

* `hidden_before`;
* the routing order;
* every factual action before position (j);
* the policy snapshot;
* and the future random-number streams.

After replacing (a_j), later token actions must be regenerated from the same policy using the same base random numbers but the modified prefix. They must not simply be held fixed, because the policy is autoregressive.

This is feasible in both sources by replay from the episode start plus teacher-forced policy reconstruction. The absence of a convenience mid-episode branch API is an engineering cost, not a scientific obstacle.

---

## Fallback when exact reconstruction is unavailable

The strongest fallback that still cancels state variance is a **cross-fitted conditional residualization audit** using the policy’s known stochastic action assignment.

Fit, on data not used for evaluation,

[
m(h)=\mathbb E[G\mid h].
]

On a held-out fold define

[
G^\perp=G-\widehat m(h),
]

and compare it with the critic’s within-history action contrast

[
\widehat A(h,a)
===============

## \widehat Q(h,a)

\mathbb E_{\tilde a\sim\pi_0}
\widehat Q(h,\tilde a).
]

Because the action is randomized by the known stochastic policy conditional on complete (h), an orthogonalized covariance or residual-on-residual regression can identify action dependence without normalizing by total state variance.

This fallback cancels state variation **in expectation**, not pathwise. It therefore requires:

* complete (h);
* known action support and propensity;
* strict cross-fitting;
* overlap;
* and held-out evaluation.

It should be registered as a weaker observational identification route. If neither exact paired reconstruction nor valid conditional residualization is available, the correct result is `SOURCE_ACTION_EFFECT_UNRESOLVED`, not critic failure and not C1 failure.

For G17 and G18, this fallback is unnecessary because exact replay is available.

---

# 4. Question (b) — What is the complete (Q_j) input contract?

## The previous answer’s two G18 fields were not a complete list

The design declares that (h_{j,t}) contains:

* critic state and focal local observation;
* active-set context;
* lifecycle and recurrent state;
* routing position;
* every action in the prefix before (j).

But the frozen implementation contract later reduces the critic inputs to:

[
(\text{critic state},\text{active mask},j,\text{prefix through }j).
]

The actual network confirms that reduction. Its input dimension contains only:

* aggregate critic state;
* raw capacity-wide active mask;
* routing-position one-hot;
* one `action_dim` vector for the accumulated prefix.

It does not receive the declared observation or recurrent/lifecycle information.

Moreover, `prefix_through` is constructed from `prefix_action_sums + current_action`. It is a cumulative sum, not the full ordered member-labelled prefix.

That is a material mismatch with C1’s defined (h_j).

---

## Why the omitted information is load-bearing on G18

G18’s current per-member observation contains:

1. individual battery;
2. current demand;
3. active count;
4. lifecycle age;
5. previous effort;
6. rotating-membership announcement;
7. time;
8. spike-phase indicator.

The aggregate critic state contains only demand, active count, **group-mean** persistent and rotating battery, time and phase.

The delayed consequence depends on:

* which member is rotating;
* that member’s battery;
* which members previously spent effort;
* and how future policy actions respond to previous effort, age and recurrent state.

The current prefix sum loses the assignment of effort to members. For example, one unit spent by a rotating member and one unit spent by a persistent member can have the same prefix sum while producing the opposite delayed consequence. That is precisely the causal distinction G18 was constructed to expose.

There is an additional finite-toy hazard: the three fixed slot permutations and raw slot-indexed active mask may allow the critic to memorize a role pattern through slot configuration and routing position. Such memorization can generate (Q)-spread without learning an anonymous member-state action effect. G18’s permutation control is therefore necessary but does not make the reduced history scientifically equivalent to the declared (h_j). The source explicitly assigns persistent and rotating roles through three fixed slot orders.

---

## Why the omitted information is load-bearing on G17

G17’s marginal action effect depends directly on the focal member’s two capacity coordinates:

[
\text{served}_0
===============

\sum_i
\text{effort}_i
\text{mix}*i
\text{capacity}*{i,0},
]

[
\text{served}_1
===============

\sum_i
\text{effort}_i
(1-\text{mix}*i)
\text{capacity}*{i,1}.
]

Yet the critic state contains only the **aggregate** capacities, while focal capacities, presentation priority, age and prior actions reside in the per-member observation.

Two histories can therefore share:

* critic state;
* active mask;
* routing position;
* and cumulative action prefix,

while assigning the current position to members with different capacities and hence different action effects. Unlike the finite G18 role patterns, G17 capacities are generated continuously and independently per episode, so position and mask cannot reconstruct them reliably.

Thus G17’s low (Q)-spread is not only potentially a bad normalization artifact. The critic class is also missing a variable that directly multiplies the action’s reward effect.

---

## Exact contract I would freeze

For a policy snapshot (\pi^{(v)}), (Q_j) should condition on a permutation-consistent, pre-action sufficient statistic:

[
H^Q_{j,t}
=========

\left(
c_t,;
X_t^{\sigma_t},;
R_t^{\sigma_t},;
M_t^{\sigma_t},;
j,;
A_{<j,t}^{\sigma_t},;
a_{j,t}
\right).
]

Where:

* (c_t): authorized centralized critic state at time (t);
* (X_t^{\sigma_t}): the **full masked table of current per-member observations**, arranged in the anonymous routing order (\sigma_t);
* (R_t^{\sigma_t}): detached pre-action recurrent states for all active lifecycle rows, or an information-equivalent actor-state summary;
* (M_t^{\sigma_t}): active, lifecycle and current membership-transition state available at action time;
* (j): current routing position;
* (A_{<j,t}^{\sigma_t}): the **full ordered action prefix paired with its member context**, not merely its sum;
* (a_{j,t}): the post-tanh requested action submitted to the environment.

The continuation policy version (v) is part of the evidence record. It need not be a neural input if fitting, credit generation and audit are all performed under one frozen policy snapshot, but data from different policy versions must not be treated as if they shared one stationary (Q^\pi).

The critic must receive no:

* action at a position greater than (j);
* next state;
* future reward;
* unannounced future membership event;
* source ledger identity unavailable at decision time;
* or hard-coded semantic interpretation of observation coordinates.

The representation must be equivariant to simultaneous permutation of lifecycle rows. Routing position may identify a factor in the chain; it must not become a fixed member identity.

---

## Does this leak information into the protected fast path?

**No, not if the existing ownership boundaries remain strict.**

The added information is for a centralized training critic. Much of it is already present in the actor’s own observation or recurrent state. The fast path remains protected when:

1. critic inputs are detached collection-time snapshots;
2. the critic has separate parameters or a verified stop-gradient boundary;
3. critic regression has no gradient to the fast actor or residual actor;
4. the advantage is detached before the PPO surrogate;
5. no critic feature is fed into the action mean;
6. the fast actor, `log_std`, base critic and immediate baseline remain frozen during the delayed phase;
7. exact bitwise anchor invariance remains an operational gate.

The frozen design already declares these detach and freeze requirements, and the completed screen verified bitwise anchor preservation.

What must be prohibited is not “critic sees observation.” It is **critic-to-actor information flow outside the detached scalar credit path**.

---

# 5. Question (c) — Are cross-fitting and held-out validation required?

## Held-out critic qualification: required

The current collection computes and freezes the action advantage using the critic **before** the critic is updated on that collection.

During the delayed update, the residual actor is updated first from that frozen advantage, and only afterward is the prefix critic fitted to the return target.

At the first delayed update, the prefix critic is therefore randomly initialized. It can generate nonzero, member-distinct but arbitrary credit, move the residual away from zero, and change the future data distribution before it has demonstrated any true action-response skill.

The registered identification statistic is then measured only on the final training trajectory, not on data held aside from critic or actor optimization.

A late nonzero (Q)-spread cannot retrospectively validate hundreds of earlier actor updates.

Therefore the re-registered screen must satisfy:

> **No residual-actor update may occur until the critic has passed out-of-sample Stage B qualification under the policy snapshot whose actions it will credit.**

This is mandatory.

---

## Exact split required for the screen

The protected semantic requirement is three disjoint information roles:

### 1. Critic-fit split (D_{\mathrm{fit}})

Used only to fit (Q_j) under a frozen policy snapshot.

### 2. Actor-credit split (D_{\mathrm{credit}})

Collected under the same policy snapshot. The qualified critic is frozen; its detached advantages drive the residual actor. These trajectories must not have been used to fit the critic before their actor update.

### 3. Identification-audit split (D_{\mathrm{audit}})

Contains the paired action interventions and oracle return contrasts used for Stages A, B1 and B2. It is never used to update either critic or actor.

The splits must use disjoint episode/action/suffix random streams. Confidence intervals must be clustered at the episode/ledger and suffix-replication level, not treat every active token as an independent sample.

The initial delayed phase must first be a **critic-only qualification phase at the exact fast anchor**. Only after Stage A and Stage B pass may the first residual update occur.

After the policy changes, (Q^{\pi}) also changes. The screen must therefore either:

* requalify the critic before each bounded actor-update block under the new policy snapshot; or
* freeze a pre-registered block size and demonstrate on the audit split that identification remains valid throughout that block.

A final-only audit is insufficient.

---

## Is literal cross-fitting mandatory?

**No particular (K)-fold construction is mandatory.**

What is mandatory is:

* out-of-sample critic evaluation;
* no actor update from an unqualified critic;
* separation of fit, credit and audit information;
* policy-snapshot consistency.

Three independent streams satisfy that contract. (K)-fold cross-fitting is an acceptable data-efficient realization, especially for Stage B, but it is not the only legitimate realization.

So I sharpen my earlier statement as follows:

> **Held-out qualification and role separation are required; literal (K)-fold cross-fitting is optional.**

---

# 6. Question (d) — Joint or sequential gates, and what does each failure mean?

## The gates must be sequential and source-specific

Stage B has no scientific meaning if Stage A cannot establish a source action effect. Dividing critic error by a near-zero action-effect scale is unstable and would again conflate source and critic failure.

The revised sequence should be:

| Order | Gate                                                                                             | Failure classification                               | Scientific update                                             |
| ----: | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------- | ------------------------------------------------------------- |
|     1 | Operational, replay, exact-history reconstruction, anonymity, leakage and suffix-policy contract | `INVALID_G20R_EVIDENCE_CONTRACT`                     | Implementation or estimand only                               |
|     2 | Stage A source-local action effect                                                               | `SOURCE_LOCAL_ACTION_EFFECT_NOT_IDENTIFIED_<source>` | Source/action-support/audit pair only; critic and P2 unjudged |
|     3 | Oracle effect inside centered residual authority                                                 | `SOURCE_EFFECT_OUTSIDE_CENTERED_AUTHORITY_<source>`  | P2 scope on that source; not critic failure                   |
|     4 | Stage B1 held-out critic action-response skill                                                   | `NON_IDENTIFIED_ACTION_CRITIC_<source>`              | This critic/input/training realization only                   |
|     5 | Stage B2 oracle-versus-learned residual-gradient alignment                                       | `NON_IDENTIFIED_ACTION_CREDIT_DIRECTION_<source>`    | This C1 factorization/normalization realization only          |
|     6 | Behavioral compatibility and delayed mechanism                                                   | Existing behavior branches                           | Only now can C1 behavior be supported or refuted              |

This is a four-way separation before behavior:

1. no measurable source effect;
2. source effect outside P2 authority;
3. critic failed to learn it;
4. critic response exists but produces the wrong actor direction.

The previous three-way taxonomy omitted the second and fourth cases.

---

## Do not combine G17 and G18 identification with a global `all(...)`

The current result code requires both sources to satisfy one global identification Boolean before any behavioral branch can fire.

That is too coarse for the smallest claim.

### G18

G18 critic and action-credit qualification are load-bearing before either a positive or negative delayed-credit conclusion. It is the source on which C1 is claimed to carry member-resolved delayed credit.

### G17

G17 compatibility is directly observed behavior. If G17 performance passes after the actual delayed training procedure, that pass need not be masked merely because G17’s slow critic lacks a separately identified member-level effect. It supports the narrow statement that the trained residual did not destroy the fast controller in that run.

However, if G17 compatibility **fails**, that failure may be attributed to C1 only if the G17 source effect and critic credit are qualified. Otherwise the correct result is “unqualified critic caused or may have caused compatibility loss,” not C1 incompatibility.

Thus:

* a G17 identification failure with a G17 behavioral **pass** is diagnostic and should not mask a qualified G18 result;
* a G17 identification failure with a G17 behavioral **failure** prevents interpreting that failure against C1.

This removes the exact defect seen in the present screen: G17’s invalid normalization masked the G18 path even though every G17 compatibility threshold would have passed.

---

# 7. Question 2 — Is repairing the floor sufficient?

## No

A numerical replacement alone leaves three deeper defects.

### 1. The critic does not instantiate the declared decision history

The design’s formal (h_j) includes local observation, recurrent/lifecycle state and the full prefix, but its executable critic receives only an aggregate state, raw mask, position and cumulative prefix sum.

On G17, it omits the focal capacity that directly determines the action’s immediate effect. On G18, it omits member-resolved battery, role announcement, previous effort and the member assignment of preceding effort.

A better threshold cannot make an information-insufficient critic estimate (Q_j(h_j,a_j)).

### 2. The actor moves before the critic is qualified

The first residual update is driven by an untrained critic, and later identification is measured only at the end. This makes the trajectory path-dependent on arbitrary initial credit.

A better final threshold cannot retrospectively validate those updates.

### 3. Spread does not establish correctness

Even after replacing the normalizer, a criterion based only on nonzero (Q)-variation cannot distinguish:

* correct action response;
* wrong sign;
* wrong member ordering;
* or a slot-pattern shortcut.

The true paired action contrast and actor-direction audit are required.

Therefore the current package is not eligible for “same implementation, new floor, rerun.” The critic information and evidence sequencing define a materially different C1 realization and require a freshly registered screen mapping.

---

## Does the disclosed G18 reading refute C1?

**No.**

The disclosed observation is compatible with at least four explanations:

1. the critic never represented the true (h_j);
2. it learned slot or position shortcuts rather than anonymous member effects;
3. it had nonzero spread but wrong action-effect sign or ordering;
4. early random critic credit moved the actor into a bad region before identification.

The current evidence does not separate them.

The G18 reading does refute a much smaller informal proposition:

> Nonzero critic action spread, nonzero residual movement and bitwise fast-anchor preservation are sufficient to establish usable member-resolved credit.

They are not.

It also demonstrates that a **late** spread measurement cannot qualify the **earlier** credit that produced the trajectory.

But because the branch that fired explicitly licensed no P2 update, and because the downstream behavior was recorded as reachable but not reached, it must not be promoted post hoc into a C1 negative.

Only a re-registered screen in which the critic passes the paired, held-out qualification before acting can produce an interpretable C1 behavioral result.

---

# 8. Question 3 — Does P2’s status change?

## P2 remains unchanged and untested

P2’s scientific proposition is the active-set decomposition:

* fast common-mode authority;
* slow anonymous redistribution authority.

The current result neither tests nor contradicts that decomposition. Exact centering remains operational, and the screen’s fired branch was explicitly registered as an estimator-identification failure with no P2 update.

### C1 status

I would record C1 on two axes:

* **scientific evidence status:** unresolved and not yet validly tested;
* **portfolio/realization risk:** at risk, because its critic sufficiency and qualification burden are now concrete rather than hypothetical.

The following should be retired:

* the `Q-spread / raw-return-std` identification measurement;
* the reduced critic history
  ((\text{critic state},\text{raw mask},j,\text{prefix sum}))
  as an exact realization of declared C1;
* an evidence protocol that allows the residual actor to move before critic qualification;
* final-trajectory spread as retrospective qualification.

What remains live:

* C1 with a sufficient anonymous decision history and qualified out-of-sample action critic;
* C2, the slow-(Q) tangent projected into the centered action subspace, still parked and not selected;
* exact paired action contrasts as an audit instrument, not as the deployed algorithm.

A valid future C1 behavioral failure would refute only:

> This qualified anchor-policy conditional action-advantage realization is sufficient on the registered G18 source.

It would still not retire all per-agent counterfactual credit or P2 as a broader action-authority candidate. That boundary is already part of the prior re-registration decision.

---

# 9. What I add, sharpen or retract from the curtailed answer

## Stands unchanged

* Raw return variance is the wrong normalizer.
* A floor change alone is insufficient.
* G18 does not refute C1 or P2.
* P2 remains untested.
* Critic identification must precede behavioral interpretation.

## Sharpened

* Stage A is not merely “some (\Delta G\neq0).” It must measure the true within-history action advantage on the C1 action support under the declared suffix policy.
* The critic-information defect includes:

  * all member observations;
  * all relevant lifecycle/recurrent state;
  * the focal G17 capacity;
  * the full member-labelled prefix;
  * policy-snapshot consistency;
  * and anonymity/equivariance.
* A G17 critic-identification failure must not automatically mask G18 when direct G17 compatibility passes.
* The taxonomy needs distinct branches for:

  * no source effect;
  * effect outside centered authority;
  * unfit critic;
  * wrong actor-credit direction;
  * and qualified behavioral failure.

## Retracted or revised

* I retract **raw unscaled NMSE < 1** as a mandatory identification gate. Use positive-scale held-out (R^2), contrast alignment and oracle actor-gradient alignment.
* I retract any implication that `rotating_mask` and individual battery were the complete missing input inventory.
* I refine “cross-fitting is required” to: **independent fit/credit/audit roles and held-out qualification are required; literal (K)-fold cross-fitting is optional.**
* I refine “G18 lowers C1 plausibility” to: it lowers confidence in the **current implementation and qualification protocol**, but creates no formal evidence update to the mathematical C1 class.

---

# 10. Recommended next evidence action

The next action should be a **zero-compute re-registration of the G20R identification and result contract**, freezing:

* the complete anonymous (Q_j) history;
* the exact paired-replay Stage A estimand;
* the Stage B1 contrast-fit criterion;
* the Stage B2 oracle gradient-alignment criterion;
* the fit/credit/audit data roles;
* the no-actor-before-qualification rule;
* policy-snapshot ownership;
* source-specific branch precedence;
* and the smallest interpretation of each branch.

Only after that contract exists could a new screen be interpretable.

**This ruling authorizes neither implementation nor nonformal or formal compute.**
