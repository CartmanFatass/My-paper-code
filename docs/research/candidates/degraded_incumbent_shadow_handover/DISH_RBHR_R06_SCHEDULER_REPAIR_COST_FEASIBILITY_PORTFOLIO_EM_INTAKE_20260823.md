# DISH RBHR r06 scheduler-repair cost/feasibility Portfolio-EM intake — 2026-08-23

```text
document_kind=direction_scheduler_repair_cost_feasibility_scientific_recommendation
owner=Portfolio-owned Explorer Manager /root/em_dish_scanner_terminal_intake
research_scope=direction:degraded_incumbent_shadow_handover
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
source_root_return=docs/session/ROOT_CM_TO_PORTFOLIO_DISH_RBHR_R06_SCHEDULER_REPAIR_COST_DECOMPOSITION_RETURN_20260823.md
source_cm_assessment=docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RBHR_R06_SCHEDULER_REPAIR_COST_FEASIBILITY_CM_ASSESSMENT_20260823.md
prior_prelaunch_intake=docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RBHR_R06_PRELAUNCH_RESOURCE_INCOMPATIBILITY_PORTFOLIO_EM_INTAKE_20260823.md
technical_fact_intake=ACCEPTED_WITHOUT_REPERFORMING_CM_ACCEPTANCE
scheduler_repair_engineer_days=LOW19|CENTRAL32|HIGH52
modeled_complete_wall_hours=LOW35.90|CENTRAL46.11|HIGH63.29|NOT_ACCEPTED_MEASUREMENT
future_lease_rule=VALIDITY_GE_B_PLUS_MAX_6H_OR_20PCT_B|STRICTLY_GT_B
science_bearing_ambiguity=none
question_relevant_activity=false
scientific_result=false
partial_value=false
r05=TERMINAL|CONSUMED|NO_CURRENT|UNTOUCHED
current_portfolio_cut=EMPIRICAL_3|ENABLING_CONSTRUCTION_1|DEFINITION_ONLY_0|UAV_EMPIRICAL_1|PRESERVE
portfolio_recommendation=INVEST_FINITE_NON_REPLENISHABLE_TWO_STAGE_SCHEDULER_REPAIR
recommended_managed_engineer_days=32
recommended_hard_ceiling_engineer_days=52
prior_consumed_caps_reused=false
portfolio_authority_enacted_by_this_intake=false
```

## Conclusion

I recommend that Portfolio invest in one finite, non-replenishable unchanged-
science scheduler-repair envelope for the immutable r06 panel: **32 experienced
engineer-days managed and 52 days hard**.

The envelope should be staged:

1. **S1 scheduler implementation and failure-atomic coordination:** 17 managed,
   28 hard days; then
2. **S2 conditional independent acceptance, exact resource remeasurement and
   future-request preparation:** 15 managed, 24 hard days.

The two managed allocations sum to 32 and the hard allocations sum to 52.
They are new forward authority based solely on this scheduler decomposition.
No unused or consumed E1/E2 construction cap is reused, transferred or
replenished, and unused S1 capacity cannot enlarge S2.

The modeled resource cases make finite investment scientifically and
operationally proportionate, but they are not accepted measurements. Portfolio
therefore buys S1 first and releases S2 only after an exact result-blind S1
return confirms the priced scheduler/atomic design, cumulative cost and
remaining forecast. A lease remains outside both stages.

This artifact recommends but does not enact the Portfolio decision.

## Observed cost and feasibility evidence

I intake the CM assessment without re-performing technical acceptance. The
read-only low/central/high engineering distribution is:

| Work family | Low | Central | High |
|---|---:|---:|---:|
| Scheduler implementation | 6 | 10 | 16 |
| Failure-atomic coordination | 4 | 7 | 12 |
| Independent plus end-to-end acceptance | 5 | 8 | 13 |
| Exact parallel-command resource remeasurement | 3 | 5 | 8 |
| Future lease-request preparation | 1 | 2 | 3 |
| **Total engineer-days** | **19** | **32** | **52** |

The priced design is concrete: at most eight process workers under an eight-
core total budget; each of the 120 block-arm jobs owns strictly ordered 1,024-
update state; downstream evaluation/fork/metric work is dependency released;
out-of-order worker completion is deterministically committed in frozen order;
and create-only parent-bound generations resume the same identity without
duplicating committed optimizer updates or REAL/SHAM forks.

The explicit low/central/high complete-wall models are 35.90 / 46.11 / 63.29
hours. They use the measured `7.324149699998088`-second update plus stated
effective concurrency, scheduler overhead and fixed coordination allowances.
The corresponding modeled CPU totals are approximately 273.14 / 286.39 /
318.22 core-hours. Modeled RSS, scratch, durable and I/O remain well below the
unchanged hard ceilings.

These are prospective assessment models, not accepted resource evidence. They
do not authorize division by eight, select a worker width, establish an actual
complete-run wall bound or replace the required cold/warm exact-command
measurement. No source, TEST, runtime, request, lease, sealed-master, identity,
coordinate, model, checkpoint, activity, result, partial value, provider, Git
or r05 action occurred.

## Scientific value and investment rationale

R06 remains the sole current direct-UAV empirical variable-`k` object. Its
indivisible complete panel is still the only current discriminator that jointly
separates STRUCTURED from strict-containing FLEX, NEVER, IMMEDIATE and
HYSTERESIS; full-package from first-application-valid REAL/SHAM actuation;
adaptive structure from simple-rule sufficiency; and competence, witness,
support, headroom, precision, nonharm, schedule/regime and common-anchor
outcomes.

Identifiability is unchanged and strong: a deterministic arm-independent
11,520-tape population with zero scientific-admission failure probability, all
five arms, paired mask views, the REAL/SHAM fork, 24 independent blocks, the
6,990-estimand simultaneous family, common-anchor intersections, exhaustive
branches and complete-result firewall. Every complete outcome can retain,
narrow, redirect or delete part of the candidate family. No smaller panel or
cheaper comparator set asks the same causal question.

The forward 32/52-day cost is material but finite. It is justified because the
panel is uniquely direct-UAV and high-information, the CM identifies a concrete
rather than speculative scheduler design, all modeled cases remain within the
ordinary CPU 320 h / wall 65 h targets, and the hard case remains bounded
without a substrate rewrite. No-current engineering investment would preserve
the entire question despite an evidence-backed repair whose modeled high wall
is below the ordinary target.

Approximately 55–65% of the central scheduler implementation/coordination work
is reusable within compatible DISH revisions: bounded process/core control,
worker health and shutdown, ordered receipt commit, create-only generation and
same-identity successor mechanics, and cold/warm resource observation. The
remaining work is r06-specific. This reuse is contingent, belongs only to DISH
engineering, and transfers no evidence, budget or authority to another
direction.

## Strongest alternative and unchanged claim ceiling

The strongest alternative to a favorable STRUCTURED result remains finite-
budget restriction or learnability: STRUCTURED may train more easily within
1,024 updates than strict-containing FLEX without showing that FLEX freedoms
are intrinsically harmful or that structured handover is uniquely causal. The
strongest population-specific alternative remains insufficient recoverable
headroom in the fixed speed/geometry factorial. Generic two-UAV redundancy,
favorable geometry, simple timing, message traffic, recurrent-state capacity
and event/role/token shortcuts remain secondary alternatives. Scheduler repair
cannot resolve any of them; it only makes the frozen discriminator executable.

The maximum claim remains finite-budget evidence on
`RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3` that one shared two-UAV policy improves
direct service or tail robustness at one common registered speed across every
claim schedule, remains noninferior and nonharmful across the other registered
speeds, and passes every competence, witness, support, REAL/SHAM, FLEX, simple-
rule, energy and continuity qualification.

No outcome can establish arbitrary or continuous `k`, arbitrary route speed,
variable `N`, natural prevalence, convergence, unique mediation, transfer,
safety, certification, deployment or flight.

## Protected scheduler stages

### S1 — real scheduler and failure-atomic coordinator

```text
stage=S1_REAL_SCHEDULER_AND_ATOMIC_COORDINATION
low_central_high_days=10|17|28
managed_days=17
hard_ceiling_days=28
allowed=bounded process scheduler implementation|eight-core total enforcement|dependency-aware block-arm job graph|deterministic receipt ordering|failure-atomic frontier and metric coordination|same-identity create-only recovery|result-blind local fixtures and self-audit
forbidden=independent final acceptance|production resource remeasurement|lease-request preparation or issuance|sealed-master access|nonfixture master/identity/coordinate|production activity|partial value|provider|Git
required_return=CM-authored S1 construction/self-audit packet with scheduler and atomic coordinator present, actual days, remaining total forecast, unresolved technical risks, modeled assumptions and every invalidation check
```

Operational Root must not release S2 unless the same CM establishes that the
real scheduler and atomic coordinator preserve the frozen job, receipt,
checkpoint, fork and one-identity laws; S1 spend is at most 28; the remaining
forecast keeps total work at or below 52; and no invalidation condition exists.
S1 produces no accepted wall bound, lease readiness or scientific value.

### S2 — conditional acceptance, measurement and future-request return

```text
stage=S2_ACCEPTANCE_REMEASUREMENT_AND_FUTURE_REQUEST
low_central_high_days=9|15|24
managed_days=15
hard_ceiling_days=24
hard_total_ceiling_days=52
allowed=independent serial-oracle equivalence|worker-death and commit-boundary failure injection|same-identity successor acceptance|complete TEST CLI and result-firewall acceptance|cold/warm width-bounded resource remeasurement|future lease-request preparation and validation
forbidden=lease issuance|opening withdrawn sealed master|nonfixture master/identity/coordinate|production training/evaluation/inference|partial panel/value|provider|Git
required_return=CM-authored complete scheduler technical-acceptance/current-byte resource packet and future lease-request eligibility or one atomic incompatibility
```

Unused S1 days cannot enlarge S2, unused S2 days cannot enlarge S1, and no
unused amount authorizes unrelated work. S2 ends before lease issuance or
identity creation. Its exact measurements—not the 35.90/46.11/63.29-hour
models—must establish the accepted complete-run wall bound `B` and every
CPU/RSS/storage/I/O fact.

## Resource and lease invalidation boundary

The envelope preserves the existing ordinary CPU 320 h / wall 65 h targets and
every hard ceiling; none is enlarged. The same CM stops before further work and
returns the exact fact if any of the following is observed or forecast:

- S1 would exceed 28 engineer-days, S2 would exceed 24 or total scheduler work
  would exceed 52;
- the exact 4,096-transition update changes materially from
  `7.324149699998088` seconds on the scheduler host;
- accepted effective training concurrency is below six or scheduler overhead
  exceeds 30 percent;
- aggregate CPU crosses 320 ordinary or 560 hard core-hours, complete wall
  crosses 65 ordinary or 110 hard hours, or any RSS/storage/I/O hard ceiling
  is projected or measured to fail;
- correctness requires more than eight total cores, GPU use, a different
  native host/substrate or a serial Python environment/rollout path;
- deterministic RNG/receipt ordering, persistent optimizer state, sole
  checkpoints, paired mask/fork lineage, complete reduction, result blindness
  or failure atomicity cannot be preserved; or
- science, inventory, panel, one-identity semantics, claim or result firewall
  would have to change.

The first resource deviations require a new engineering/resource decision;
the latter semantic deviations return as exact technical or science-bearing
incompatibilities. No sunk-cost, near-finish or completion-order argument
enlarges the non-replenishable envelope.

If S2 establishes an accepted complete-run wall bound `B`, any later fresh
Root lease must satisfy exactly:

```text
lease_validity_hours >= B + max(6 hours, 0.20 * B)
lease_validity_hours > B
```

No modeled wall value fixes `B`, and the withdrawn 24-hour lease remains
unusable. Future request preparation does not itself authorize request
issuance, lease issuance, sealed-master access or identity activity.

## Exact Portfolio and Operational actions requested

Portfolio should authorize the exact S1/S2 envelope above for
`DISH-RBHR-SCIENCE-20260822-06`: 32 managed, 52 hard, non-replenishable and
separate from every consumed prior construction cap. The current
`EMPIRICAL_3|ENABLING_CONSTRUCTION_1|DEFINITION_ONLY_0|UAV_EMPIRICAL_1` cut and
independent direction envelopes remain unchanged. This EM artifact does not
enact the decision.

If Portfolio accepts, Operational Root should transmit this artifact and the
exact CM assessment unchanged to the same DISH CM, release S1 only, collect its
exact CM return, and release S2 only if every gate above is satisfied.
Operational Root must not issue a lease, restore the withdrawn lease, open the
sealed master or permit an r06 identity, coordinate or question-relevant
activity as part of either engineering stage.

## Four-layer boundary and compact milestone

```text
conclusion=Recommend finite investment in unchanged-science r06 scheduler repair: 32 managed / 52 hard engineer-days, staged as S1 scheduler-plus-atomic coordination 17/28 and conditional S2 acceptance-remeasurement-request preparation 15/24.
recommended_portfolio_decision=AUTHORIZE_FINITE_NON_REPLENISHABLE_TWO_STAGE_SCHEDULER_REPAIR_ENVELOPE|MANAGED32|HARD52
scientific_value=R06 remains the sole current direct-UAV variable-k empirical and a strongly identified branch-complete discriminator with no cheaper equivalent scientific substitute.
strongest_alternative=Finite-budget STRUCTURED restriction/learnability versus strict-containing FLEX; secondarily, target-specific insufficient recoverable headroom; scheduler repair provides no efficacy evidence.
claim_ceiling=Unchanged finite-budget exact-host common-speed direct-service/tail value under every frozen qualification and nonharm gate; no arbitrary-k, variable-N, transfer, safety, certification, deployment or flight claim.
key_observation=Read-only CM assessment prices 19/32/52 engineer-days and models 35.90/46.11/63.29 complete wall-hours with explicit concurrency/overhead; modeled wall is not accepted measurement, and no implementation, runtime, lease, identity or partial value occurred.
reuse_significance=55-65 percent of central scheduler implementation/coordination is contingently reusable within compatible DISH revisions only; no cross-direction evidence, budget or authority transfers.
portfolio_effect=If accepted, continue exact r06 engineering under the new finite scheduler gates while preserving EMPIRICAL_3|ENABLING_CONSTRUCTION_1|DEFINITION_ONLY_0|UAV_EMPIRICAL_1; this EM recommendation is not final allocation authority.
next_discriminator=Immediate engineering discriminator is S1's real deterministic failure-atomic scheduler; S2 must then establish exact current-byte acceptance and measured resource bound B before any fresh lease, after which the scientific discriminator remains the indivisible complete r06 panel.
observed_fact=Assessment only: engineer-days and resource models exist, but accepted scheduler bytes, TEST acceptance, exact parallel-command measurements, lease request, lease, identity, activity, result and partial value do not.
local_fence=Until Portfolio acts, no scheduler implementation; throughout S1/S2 no lease, sealed-master access, scientific master/identity/coordinate, production activity or partial value, and r05 remains terminal/consumed/no-current.
scientific_continuation=Preserve immutable Pro-closed r06 and its one-identity/result-firewall laws through result-blind scheduler repair; only a complete later result may return for EM interpretation and same-Pro convergence.
root_decision_class=PORTFOLIO_FINITE_SCHEDULER_ENGINEERING_DECISION_REQUIRED|IF_ACCEPTED_OPERATIONAL_ROOT_RELEASES_S1_THEN_CONDITIONAL_S2|NO_LEASE_BY_THIS_DECISION
stage_return=S1 exact scheduler/atomic construction-self-audit and cost/forecast return before S2; S2 complete technical acceptance, exact resource measurement B and future-request-eligibility return before any lease or identity.
invalidation_boundary=Stop and return on S1>28|S2>24|TOTAL>52, update-time material change, concurrency<6, overhead>30 percent, ordinary/hard resource exceedance, >8-core/GPU/host/Python fallback need, or any frozen ordering/persistence/fork/inference/science/identity change.
future_lease_rule=Only after accepted B: validity >= B + max(6h,20 percent of B) and strictly > B; withdrawn lease remains unusable.
operational_root_action_requested=If Portfolio accepts, bind the same DISH CM to S1 at 17 managed/28 hard, collect its exact return, then release S2 at 15 managed/24 hard only if total forecast remains <=52 and every invariant holds; return accepted scheduler/resource/request-eligibility evidence without lease or empirical activity.
does_not_imply=Accepted resource bound|scientific result|science change|claim expansion|open-ended or replenishable budget|lease authority|partial-panel permission|replacement identity|r05 revival|cross-direction transfer|provider|Git|deployment|flight.
```
