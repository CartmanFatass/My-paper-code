# RISP witness-independent prevalence census R01 blocker intake

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-PREVALENCE-CENSUS-R01
source_revision=1bea5cc9b0780a8986fb66df65976de376eb57e6
status=NO_UNIQUE_SOURCE_GROUNDED_POPULATION_LAW
scientific_activity=READ_ONLY_AUTHORITY_AND_IMPLEMENTATION_AUDIT
census_executed=false
tracked_result_intake_read=true
completed_result_artifact_observed=false
new_result_observation=false
registered_rerun_executed=false
learning_executed=false
code_changed=false
portfolio_changed=false
```

## Question and non-goals

Can current source authority, without selecting from or searching around the completed four
`RISP-ECR-R01` witness histories, uniquely determine both:

1. a normalized distribution over reachable public decision histories, including horizon/stopping,
   action, completed-duration, hidden/ACK, decision-opportunity, and current next-`k` laws; and
2. a prospective numeric materiality rule for reopening learned RISP work?

This intake does not choose a population, calculate prevalence or regret, inspect the complete
result beyond `RISP_ECR_R01_RESULT_INTAKE.md`, rerun the registered certificate, introduce learning,
or change `DIRECTION.md` or `PORTFOLIO.md`.

## Direct observations: frozen components

Current ECR authority fixes the following scientific pieces:

- public actions `LEFT < CENTER < RIGHT`, public ACKs `+/-`, and that printed order as the
  deterministic action tie break;
- uniform initial hidden-sector belief;
- duration support `{4,8,12}`;
- the conditional hidden transition
  \(P_k=J/3+(15/16)^k(I-J/3)\);
- ACK probability `4/5` after a completion-sector match and `1/5` otherwise;
- hold completion, motion, ACK, private update, then next-action event order;
- the action-visible next duration and next-hold value
  \(Q(a\mid b,k)=k[-3/5+(6/5)(bP_k)(a)]\); and
- the exact information projections for full-history, duration-erased, and last-ACK controllers.

The implementation admits public envelopes with one through eight completed events. That is a
validation/resource bound, not a probability law or stopping rule. The registered history builder
sets next `k=4`, but only for its literal registered rows; the general public-history validator
admits every next `k` in `{4,8,12}`.

For registered reachability, the source multiplies the conditional ACK-sequence mass by
`(1/3)^N`, corresponding to an independent uniform reference-action factor. It supplies no factor
for the event count, completed-duration sequence, selected decision opportunity, or current next
duration. The two registered twin populations instead use literal row weights `1/2`.

The exact controller implementation forms `FULL_BAYES_K_ERASED` and `LAST_ACK_BAYES` beliefs by
grouping the enumerated rows by their information views and averaging their full posteriors with
the supplied `population_weight`. The reference path mass is recorded separately and is not the
weight used for this marginalization. Thus a new population law is part of the definition of each
competent coarsened Bayes controller, not merely a later reporting weight.

## Direct observations: missing components

No current source fixes:

- a distribution over renewal count or a primitive-time stopping rule;
- probabilities over duration strings or historical schedule roles;
- whether the observational unit is an episode-terminal decision, every renewal opportunity, a
  uniformly selected opportunity, or a physical-time-weighted opportunity;
- a population law for current next `k`;
- whether the uniform reference-action factor is promoted from registered reachability to the new
  prevalence population, rather than replaced by another prospectively justified behavior law;
- unconditional versus disagreement-conditional regret, or raw next-hold utility regret versus
  physical-time-normalized regret when next `k` varies;
- whether general-census ties are included under the printed deterministic tie break, excluded from
  the action-difference denominator, or reported separately; or
- a numeric prevalence or regret floor, the logic combining those floors, or whether the branch is
  evaluated separately for duration-erased and last-ACK Bayes.

The direction and result intake state that the witness-independent distribution and any
materiality floor must be prospectively frozen before enumeration. They do not supply either one.

## Historical five-schedule adjudication

The historical G-initialization target supplies a coherent `T=192` episode and five deterministic
schedules (`k=4`, `k=8`, `k=12`, `4->12`, and `12->4`), but it does not uniquely select a new ECR
prevalence population. It contains several different populations: a two-schedule training mixture,
five evaluation schedules, an equal-weight target made from only `k=12` and the two switch
schedules, and schedule-specific eligible-row windows. It also distinguishes learned deployed
action laws from a separate uniform control. Selecting one of those populations, row windows, or
action cells would be a new prospective choice.

The historical and ECR hidden dynamics are mathematically consistent, not contradictory: the
historical per-tick matrix has diagonal `23/24`, off-diagonal `1/48`, stationary component `J/3`,
and nontrivial eigenvalue `23/24 - 1/48 = 15/16`, hence its `k`-step matrix is the ECR `P_k`.
The blocker is population authority, not the conditional hidden/ACK mechanism.

Current `DIRECTION.md` explicitly keeps the fresh ECR support law separate from the historical
five-schedule implementation, and `IMPLEMENTATION_THRESHOLD.md` says it neither modifies that host
nor inherits its result polarity. The historical law is therefore a source-compatible candidate
for a separately frozen successor, not silently inherited current authority. Its old numeric
answerability thresholds apply to learned physical-return, headroom, policy-motion, and update-value
observables; none is a prevalence or coarsening-regret floor.

## Constructive non-uniqueness without witness use

Two example normalized laws can be specified without consulting any registered witness. Both draw
all completed durations, public actions, and current next duration independently and uniformly on
their frozen supports, use the frozen hidden/ACK mechanism, and evaluate the terminal decision, but
they use different stopping laws:

- `COUNT-UNIFORM-IID`: `P(N=n)=1/8` for every `n` in `{1,...,8}`.
- `COUNT-DYADIC-IID`: `P(N=n)=2^(8-n)/255` for every `n` in `{1,...,8}`.

Both have full support on the same bounded public-history surface, are exact and normalized, and
are independent of witness outcomes. Both obey the frozen host and public-history surface, but they
assign different mass to history lengths and therefore define different population-conditioned
controllers and estimands; no numerical equality
between them is implied or established. Neither is selected by source authority. Many other laws,
including distinct historical-schedule and decision-opportunity mixtures, are equally compatible.
No result value was calculated for any example.

## Judgment impact and claim ceiling

The smallest decisive blocker is the absent rational law over

\[
(N, K_{1:N}, K_{\mathrm{next}}, \text{decision/opportunity selection}),
\]

even if the uniform reference-action factor and frozen hidden/ACK conditional mechanism are
retained. Without that law, a strongest same-information coarsened Bayes controller
\(E[b(H)\mid V(H)]\), action-difference probability, and expected regret are undefined. The
missing numeric materiality rule is a separate blocker: after a population is chosen and the exact
estimands exist, no current authority maps their values to `material` versus `negligible` or to a
lifecycle branch.

This is a definition-level nonidentification, not a null prevalence result. It does not weaken the
accepted four-history existence theorem, imply negligible natural mass, reject event-conditioned
Bayesian recurrence, or authorize a learned successor. The direction-local recommendation to Root
is to keep standalone RISP `PARKED` until both blockers are prospectively resolved.

## Smallest next discriminator

Before any enumeration or code change, obtain one result-independent target-population authority
and freeze:

1. the exact normalized law over stopping/count, duration sequence, action behavior, sampled
   decision opportunity, and current next `k`;
2. the law-conditioned duration-erased and last-ACK Bayes nulls;
3. action-difference and regret estimands, denominators, normalization, and tie handling; and
4. numeric materiality floors plus an exact comparator-specific branch rule.

If no independently justified target-population law and floor can be supplied, the reactivation
condition cannot be evaluated and no census should run. If they are supplied, the next evidence is
one separately registered exact enumeration; the completed `RISP-ECR-R01` identity remains sealed.

## Evidence paths

- `AGENTS.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/research/portfolio/PORTFOLIO.md`
- `docs/research/candidates/renewal_indexed_score_plasticity/DIRECTION.md`
- `docs/research/candidates/renewal_indexed_score_plasticity/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/renewal_indexed_score_plasticity/RISP_ECR_R01_RESULT_INTAKE.md`
- `docs/research/candidates/renewal_indexed_score_plasticity/RISP_G_INITIALIZATION_REACHABILITY_SCIENCE_CARD_R01.md`
- `docs/research/candidates/renewal_indexed_score_plasticity/RISP_G_INIT_REACH_R01_DORMANT_FALLBACK_PORTFOLIO_DISPOSITION_20260823.md`
- `docs/research/candidates/renewal_indexed_score_plasticity/RISP_B3_TRACK_RELAY_GATED_COMPOSITE_R03.md`
- `experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/contract.py`
- `experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/exact_probability.py`
- `experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/reference_host.py`
- `experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/reachable_twins.py`
- `experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/controllers.py`
- `experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/analysis.py`
- `experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/schemas/`
