# VQFP variable-N physical-association value R01 science card — 2026-08-23

```text
document_kind=direction_empirical_science_card
owner=direction:voronoi_quadrature_field_policy
assignment=VQFP-POST-ANALYTIC-VARIABLE-N-EMPIRICAL-DEFINITION-R01
object=VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01
revision=VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01-SCIENCE-20260823-01
decision_marker=VQFP_VARIABLE_N_PHYSICAL_ASSOCIATION_VALUE_R01_DEFINITION_FROZEN_SELECT_CURRENT_20260823
host=VQFP-MARKOV-FIELD-COVERAGE-1D-VN-v1
stage=current_definition_only
source_theorem=VQFP-FERL-ANALYTIC-CONTAINMENT-R01-SCIENCE-20260823-03|PROVED_G|RETAIN_G_UNRESTRICTED
distinct_from_r05=true
r05_efficacy_evidence_imported=false
scientific_activity_begun=false
pro_closed=false
construction_authorized=false
empirical_activity_authorized=false
allocation_change=false
portfolio_selected=true
```

## Decision and question

Freeze this as one new empirical object, distinct from both the completed r03
theorem object and VQFP-FERL r05.

Question:

> On a bounded stochastic variable-`N` coverage host, does one shared
> roster-independent VQFP treatment trained only on `N={4,8}` improve
> held-out task performance or lower-tail robustness at `N={6,12}` over
> equal-mass and adaptive baselines, remain noninferior to a matched
> command-strict FREE policy, and lose value under geometry-only
> reassociation?

The completed r03 theorem supplies only exact, legal and decision-preserving
definitions for the treatment, FREE, reassociation, quantization and marginal
oracle controls. It supplies no efficacy, optimization, robustness or transfer
evidence. A positive empirical outcome can support a useful variable-`N`
physical-association inductive bias on this host; it cannot establish
physical-measure necessity.

## Isolation from r05 and the theorem

This object does not resume, relabel, replicate or revise r05. It imports no
r05 rows, seeds, checkpoints, thresholds, acceptance or conclusions. R05
remains unchanged and no-current.

The r03 theorem remains true independently of every outcome here. Empirical
failure cannot contradict `PROVED(G)`, and theorem success cannot count as an
empirical observation. The present object has its own identity, host,
stochastic population, training procedure, estimands, uncertainty and outcome
law.

## Host, population and stochastic dynamics

One episode has `T=32` decision steps. Roster size is fixed inside an episode.

```text
N_train={4,8}
N_heldout={6,12}
N_registered={4,6,8,12}
```

For roster `N`, form a geometry by drawing
`s=(s_1,...,s_N)` uniformly from the finite conditional support

```text
s_i in {-48,-24,0,24,48}
x_i=(2i-1)/(2N)+s_i/(384N)
max_i(v_i)-min_i(v_i) >= 1/(64N).
```

Uniform conditional sampling means independent uniform component draws are
rejected until the heterogeneity condition holds. Every accepted geometry is
in the frozen theorem class `G_N`: sites are on the `1/(384N)` grid, adjacent
gaps lie in `[3/(4N),5/(4N)]`, cells lie in
`[7/(8N),9/(8N)]`, sites stay strictly inside `[0,1]`, and the explicit
heterogeneity condition holds. Geometry remains fixed for the episode.

The field state is one of the six registered pairs

```text
beta in {-1/4,0,1/4}
gamma in {0,1/4}.
```

At step zero the pair is uniform over the six states. At each later step it
stays unchanged with probability `1/2` and moves to each of the other five
states with probability `1/10`. The transition is action-independent and has
the uniform stationary distribution.

At each step,

```text
f(x)=1+beta(2x-1)+gamma(6x(1-x)-1)
m_i=integral over physical cell C_i of f
d_i=m_i/v_i
dbar=(1/N)sum_i d_i.
```

The environment state is fully observed and exact. There is no observation
noise, motion, collision, communication, delayed actuation, future-state
projection or in-episode roster change in this toy.

## Observation, shared parameterization and legal action

Every cell exposes the record `(v_i,d_i,dbar,u_N)`, where `u_N=1/N` is a
fixed broadcast centering constant used only by the registered FREE residual.
The same coefficient vector is used for every cell and every roster; no
coefficient or learned head depends on `N`. Actor label and physical rank are
not policy inputs. The original left boundary is used only as the deterministic
largest-remainder tie key.

Let

```text
A={j/16:j=-64,...,64}
Q=120
a_i=n_i/600.
```

A legal action is a nonnegative integer vector summing to `Q`; all policies
map positive weights to that action through the exact frozen LR rule. The
lower-better step endpoint is

```text
U_t(n)=sum_i m_i v_i/(v_i+n_i/600).
```

The higher-better episode score is

```text
Z=1-(1/T)sum_{t=0}^{T-1} U_t(n_t).
```

No policy has a per-`N` head, per-roster coefficient, roster-specific
initialization, roster-specific optimizer setting or post-training tuning.

## Treatment and matched FREE

Treatment has one shared `theta in A^4`:

```text
q_i=theta_0+theta_1 d_i+theta_2 dbar+theta_3(d_i-dbar)^2
B_i=1+q_i^2
w_i^T=v_i B_i
n^T=LR(w^T).
```

Matched FREE uses the same `theta` law and one shared `phi in A^4`:

```text
r_i=clip[-1/2,1/2](
    phi_0+phi_1(d_i-dbar)+phi_2(v_i-1/N)
    +phi_3(d_i-dbar)(v_i-1/N))
w_i^F=v_i B_i(1+r_i)^2
n^F=LR(w^F).
```

FREE is matched on observations, action map, data, candidate count, validation
and evaluation. Its candidate set contains the paired trained treatment at
`phi=0`; exact command equality of that embedded candidate is a competence
audit, not efficacy evidence.

## Frozen controls

All controls act on the same physical cells, fields and episodes.

1. `EQ`: `n_i=Q/N`.
2. `DENS`: field-adaptive but measure-free weights `w_i=d_i`, followed by LR.
3. `MASS`: nonlearned physical-workload weights `w_i=m_i`, followed by LR.
4. `T-P`: evaluation-only geometry reassociation. Swap the smallest-index
   maximum- and minimum-length cells, supply
   `lambda_i=v_(P_g(i))` in place of `v_i` only inside the treatment weight,
   preserve `m_i,d_i`, original physical endpoint cells, commands and tie
   keys, and do not retrain.
5. `F-P`: the analogous evaluation-only reassociation inside FREE, reported as
   a secondary expressivity diagnostic.
6. `ORACLE`: at every step select the first `Q` exact marginal records
   `Delta_i(k)` under the frozen descending-value, increasing-cell-index,
   increasing-`k` order. This is the exact instantaneous minimizer of `U_t`
   and an unattainable-information ceiling, not a trainable comparator.
7. `FREE-EMBED`: the paired trained treatment coefficient with `phi=0`. It
   must issue exactly the treatment command on every audited record.

`DENS` tests field adaptation without physical cell measure; `MASS` tests a
generic nonlearned physical allocation; `T-P` tests whether correct physical
association changes value; `ORACLE` tests host headroom and representation/
optimization gaps.

## Frozen training and selection parity

Use 12 independent replicate keys

```text
r in {0,...,11}
counter_based_rng=Philox4x32-10
replicate_key=202608230100+r.
```

All coefficient draws use exact rejection sampling to be uniform on `A`.
All host draws use disjoint counter substreams. Within a replicate, every
candidate and both trainable arms see common-random-number episode batches.

For treatment replicate `r`:

1. Candidate set size is `K=2048`: include `theta=0` and draw 2047 vectors
   uniformly from `A^4`, with replacement.
2. Score every candidate on 64 development episodes, exactly 32 at `N=4` and
   32 at `N=8`.
3. Retain the 32 highest mean-`Z` candidates; break exact ties by
   lexicographically increasing coefficient tuple.
4. Score those 32 on 256 independent validation episodes, exactly 128 per
   training roster. Select the highest mean-`Z` candidate with the same tie
   law. This is the replicate treatment checkpoint.

For matched FREE replicate `r`:

1. Candidate set size is also `K=2048`: include the paired selected treatment
   as `(theta_T,phi=0)` and draw 2047 vectors uniformly from `A^8`, with
   replacement.
2. Use the identical 64 development and 256 validation episodes, candidate
   scoring, top-32 rule and tie law.

There is no adaptive candidate expansion, early stopping, hyperparameter
search, per-roster selection or result-dependent retraining. Training episode
draws and evaluation episodes are disjoint.

## Frozen evaluation panel

For every replicate and every `N in {4,6,8,12}`, evaluate the selected
treatment and FREE policies, `T-P`, `F-P`, `EQ`, `DENS`, `MASS`, `ORACLE` and
`FREE-EMBED` on the same 512 fresh episodes. The episode key is

```text
evaluation_key=202608239000+100*r+N.
```

Initial field states are deterministically balanced as evenly as 512 permits;
the remaining field transitions and geometries follow the frozen stochastic
law. There is no checkpoint selection or tuning on these episodes.

The full panel is 12 replicates by four rosters by 512 episodes and every named
policy/control. Training-roster results are diagnostics. Only `N={6,12}`
enters the primary value decision.

## Activity, competence and support gates

Question-relevant scientific activity begins with the first accepted
evaluation of a trainable candidate on a frozen host episode. After that
boundary, a change to host population, observations, actions, policy laws,
training, gates, estimands, uncertainty, thresholds, routing or claim ceiling
requires a new complete revision.

The following competence gates must all pass before any scientific estimand is
released:

1. A CM has separately accepted exact host, policy, LR, endpoint, oracle,
   reassociation, seed/substream, parity and serialization conformance.
2. All 12 replicates and every panel cell finish with the frozen counts and no
   missing or nonfinite normative value.
3. Every action is legal, the oracle is never worse than a legal control on an
   exact step endpoint, and `FREE-EMBED` equals treatment commands on every
   development, validation and evaluation record.
4. On its validation episodes, selected treatment is not worse than its
   included zero candidate, and selected FREE is not worse than its included
   `FREE-EMBED` candidate, under the exact selection score and tie law.

A gate failure means `NO_QUESTION_RELEVANT_DATA`. Release no partial policy
values; return unchanged science to CM for repair.

After competence, host support requires both:

```text
LCB_97.5(H_J) >= 1/500
```

where `H_J=min_{N in {6,12}}(J_ORACLE,N-J_EQ,N)`, and, separately for each
held-out roster, at least one quarter of the pooled `12*512` evaluation
episodes have
`n^ORACLE != n^EQ` and exact `U(ORACLE)<U(EQ)`. Failure returns
`HOST_SUPPORT_ABSENT`, a complete host-support result with no claim about the
treatment.

## Estimands

For policy `p`, roster `N` and replicate `r`, define:

```text
J_p,N,r = mean Z over its 512 evaluation episodes
R_p,N,r = mean of the 128 lowest Z values among those 512 episodes.
```

`J` is task performance; `R` is lower-quartile robustness. Aggregate each
metric by the mean over the 12 replicates. For `M` equal to `J` or `R`, define
the held-out composite contrasts:

```text
V_M = min over b in {EQ,DENS,MASS} and N in {6,12} of (M_T,N-M_b,N)
F_M = min over N in {6,12} of (M_T,N-M_FREE,N)
A_M = min over N in {6,12} of (M_T,N-M_T-P,N)
P_M = min over N in {6,12} of (M_FREE,N-M_T,N)
G_M = max over b in {EQ,DENS,MASS} of min over N in {6,12} of (M_b,N-M_T,N)
H_J = min over N in {6,12} of (J_ORACLE,N-J_EQ,N).
```

The minimum operators require a claim to hold at both held-out roster sizes;
`V_M` also requires treatment to exceed every frozen nonoracle baseline.

Meaningful-superiority margin is
`delta=1/500`; noninferiority margin is `nu=1/1000`.

## Uncertainty

Use a paired hierarchical bootstrap with 10,000 draws and frozen key
`202608239999`. Each draw samples 12 replicate identifiers with replacement,
then samples 512 episode identifiers with replacement inside each selected
replicate and roster. The same sampled indices apply to all policies and
controls. Recompute lower-quartile robustness and every min/max composite in
each draw.

Primary decisions use one-sided 97.5% percentile lower or upper bounds for
`V_M,F_M,A_M,P_M,G_M,H_J`. Using 97.5% separately for performance and
robustness controls the two-metric family at no more than 5% by Bonferroni.
Two-sided 95% paired intervals for component contrasts are descriptive only
and cannot change routing.

## Exact outcome routing

Apply the following precedence once, after the full panel and gates:

1. Any competence failure: `NO_QUESTION_RELEVANT_DATA`; no partial values or
   scientific polarity.
2. Competence passes but support fails: `HOST_SUPPORT_ABSENT`; make no
   treatment-value claim and return to Portfolio for host opportunity-cost
   judgment.
3. Define `PERFORMANCE_SUPPORTED` when
   `LCB(V_J)>=delta`, `LCB(F_J)>=-nu`, and `LCB(A_J)>=delta`.
4. Define `ROBUSTNESS_SUPPORTED` by the analogous three inequalities for
   `R`.
5. If both are true, return `ASSOCIATION_VALUE_SUPPORTED_BOTH`; if exactly one
   is true, return `ASSOCIATION_VALUE_SUPPORTED_PERFORMANCE` or
   `ASSOCIATION_VALUE_SUPPORTED_ROBUSTNESS`. The Portfolio successor is one
   separately defined 2-D UAV-bridge object, not automatic construction.
6. If neither is true and `max(LCB(P_J),LCB(P_R))>=delta`, return
   `FREE_PREFERRED`; a FREE-family successor requires a new object.
7. Otherwise, if `max(LCB(G_J),LCB(G_R))>=-nu`, return
   `GENERIC_ALLOCATION_SUFFICES`; do not attribute unique value to learned
   physical association.
8. Otherwise, if `UCB(A_J)<delta` and `UCB(A_R)<delta`, return
   `NO_ASSOCIATION_SEPARATION`.
9. Otherwise, if `UCB(V_J)<delta` and `UCB(V_R)<delta`, return
   `NO_TREATMENT_VALUE_OVER_FROZEN_BASELINES`.
10. Otherwise return `NONIDENTIFIED_WITHIN_FROZEN_BUDGET`.

No outcome changes the completed r03 theorem or transfers evidence to r05.

## No-partial-value boundary

Before every competence gate passes and the complete panel is durably
available, do not expose, interpret or use policy returns, contrasts,
confidence bounds, ranks, checkpoint choices or partial cells outside the
owning CM. A launcher, dependency, serialization, missing-cell or conformance
failure before this boundary is unchanged-science engineering work. There is
no adaptive stop for apparent success or failure.

After the complete release, the same-direction EM interprets exactly one
outcome under the frozen precedence. A provider result-convergence review is
then required before a final empirical claim.

## Claim ceiling by outcome

For a supported performance or robustness outcome, the maximum claim is:

> On the frozen 1-D Markov-field host, one shared treatment trained only on
> `N={4,8}` improved the named held-out metric at both `N=6` and `N=12`
> over every frozen nonoracle baseline, was noninferior to matched FREE, and
> lost value under geometry-only reassociation, within the frozen uncertainty
> law. This supports a useful physical-association inductive bias on this host.

It does not prove necessity: FREE contains treatment, the oracle and generic
allocations remain viable explanations, and training/selection can create an
inductive-bias advantage.

`FREE_PREFERRED` supports only that the richer matched class was better on a
held-out metric. `GENERIC_ALLOCATION_SUFFICES` supports only noninferiority of
a named generic baseline. `NO_ASSOCIATION_SEPARATION` and
`NO_TREATMENT_VALUE_OVER_FROZEN_BASELINES` are bounded null results on this
host. `HOST_SUPPORT_ABSENT` and `NONIDENTIFIED_WITHIN_FROZEN_BUDGET` support no
algorithm ranking beyond their exact statements.

No outcome establishes arbitrary-geometry generalization, in-episode roster
change, 2-D/UAV performance, flight, safety or deployment.

## Strongest alternatives

The strongest alternatives are:

- generic separable diminishing-return allocation, represented by the exact
  marginal oracle and approximated by `MASS`;
- field adaptation without physical measure, represented by `DENS`;
- the strictly richer FREE command class, which may match or exceed treatment;
- optimization regularization or lower-dimensional search, rather than
  physical association, as the source of a treatment advantage;
- LR quantization and residual clipping collapsing distinct parameterizations
  to the same commands; and
- insufficient oracle-over-equal-mass headroom in the sampled host.

Reassociation value preservation, equal-mass/adaptive noninferiority or FREE
noninferiority forbids a necessity claim.

## UAV bridge and nontransfer

The toy maps to ordered UAV stations along a ridgeline or linear corridor.
Cell length is patrol footprint, the Markov field is changing hazard demand,
cell mass is workload, and `n_i/600` is sensing duty under a shared team
budget. Held-out rosters test one shared allocation law under changed team
size.

The host omits 2-D polygon shape, terrain traversal, turning, propulsion,
collision avoidance, communication/relay constraints, moving footprints,
noisy sensing, in-episode membership changes, aircraft dynamics and safety.
Even a supported outcome only earns consideration of a separately defined 2-D
terrain/communication object with realistic travel/energy and a held-out
roster or membership change. Failure to transfer is a bridge limitation, not a
revision of the 1-D theorem.

## Prospective total-cost boundary

These are Portfolio planning projections, not CM estimates, leases or activity
authorizations:

| Case | Engineering | CPU core-hours | Parallel wall | Peak RSS | Scratch | Durable | GPU |
|---|---:|---:|---:|---:|---:|---:|---:|
| Low | 6 engineer-days | 150 | 8 h | 8 GiB | 10 GiB | 2 GiB | none |
| Central | 12 engineer-days | 600 | 24 h | 16 GiB | 40 GiB | 8 GiB | none |
| High | 20 engineer-days | 1,800 | 72 h | 32 GiB | 120 GiB | 24 GiB | none |

The projection includes native host and batched rollout construction,
treatment/FREE search, all controls, 12 complete replicates, the full
evaluation panel, hierarchical uncertainty, serialization and one accepted
result packet. Any materially higher class returns to Portfolio before
construction or compute.

## Provider and production boundaries

The complete revision requires same-conversation ChatGPT Pro mathematical and
causal closure before production. The separately frozen Gemini question is
innovation-only and cannot close, accept or select the object. The two
questions are mutually blind.

Pro `CLOSED` plus same-direction EM intake completes only the science-definition
boundary. Portfolio must separately select construction; Operational Root and
the matching CM must accept feasibility, implementation, full-panel
conformance and resource needs before any question-relevant activity.

## Stop and revisit law

Stop now at definition freeze. No provider operation, CM request,
construction, source, test, runtime, compute, identity, coordinate, model,
checkpoint, lease, panel, result, partial-value, Git, deployment or flight
action follows automatically.

If Pro returns `REVISION_REQUIRED`, only a complete replacement revision may
return to the same conversation. If Gemini proposes a science-bearing change
that this EM accepts, freeze a complete replacement and obtain Pro closure.

After activity begins, no host, treatment, comparator, budget, seed, gate,
estimand, uncertainty, threshold, route or claim change is allowed. A complete
supported outcome may justify one new 2-D bridge object. A clear FREE or
generic-control outcome redirects or ends investment in this treatment object.
A support-absent or nonidentified outcome returns to Portfolio for opportunity
cost; repetition requires a new object with a concrete changed discriminator,
not silent extra budget.

```text
observed_fact=The completed r03 theorem makes the exact VQFP treatment/FREE/control laws available as definition primitives but supplies no efficacy evidence; this new variable-N empirical object is meaning-complete and activity has not begun.
local_action_fence=This definition performs no provider, CM, source, runtime, compute, lease, result, partial-value, Git, deployment or flight action and imports no r05 evidence.
scientific_stage_continuation=Portfolio may select this exact revision as the current VQFP empirical definition and separately authorize mutually blind Pro closure and Gemini innovation turns.
root_decision_class=Portfolio current-definition/provider-investment decision; no automatic production or allocation change.
applies_to=VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01-SCIENCE-20260823-01 only.
does_not_imply=pro_closed|construction_feasible|empirical_activity|efficacy|held_out_N_value|measure_necessity|r05_resume|UAV_value|lease|compute|Git|deployment|flight
continuation_owner=Dedicated Portfolio Root for selection and provider authorization; same-direction VQFP EM for provider intake/revision; Operational Root and matching CM only after an exact Portfolio bridge.
```
