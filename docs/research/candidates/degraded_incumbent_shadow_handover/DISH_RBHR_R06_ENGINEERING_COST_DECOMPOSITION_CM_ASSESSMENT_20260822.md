# DISH RBHR r06 engineering-cost decomposition CM assessment — 2026-08-22

```text
document_kind=code_manager_assessment_only_engineering_cost_decomposition
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
owner=Operational-Root-owned Code Manager /root/dish_r05_preactivity_repair_cm
source_packet=docs/session/PORTFOLIO_TO_ROOT_DISH_RBHR_R06_ENGINEERING_COST_DECOMPOSITION_20260822.md
units=experienced_engineer_days
implementation_authorized=false
expanded_envelope_authorized=false
runtime_resource_envelope_changed=false
```

## Assessment result

Read-only review of the current R06 interfaces and frozen workload supports a
finite expanded estimate of **43 / 73 / 117 experienced engineer-days**
(low / central / high). These are cost-distribution estimates, not approved
ceilings, schedules or authority to implement.

### Five concrete production flows

| Flow | Low | Central | High | Scope and principal uncertainty |
|---|---:|---:|---:|---|
| Master-addressed 32-lane TRAIN reset rows | 3 | 5 | 8 | Complete block/regime/schedule/lane/episode-wave address allocation; training-only stochastic route, turn, geometry and phase draws; native row equivalence. High case is driven by allocation-table edge cases and resume-coordinate audit. |
| Native-to-policy recurrent action loop and persistent trainer | 8 | 14 | 22 | Tick-order policy forward, four recurrent copies, snapshot/promotion state, 4,096-transition fragmentation, PPO/auxiliary update, optimizer/Welford persistence through 1,024 updates and sole checkpoint. This is the largest semantic and performance risk. |
| Checkpoint-loaded five-arm mask-on/off evaluator | 7 | 12 | 19 | Load 120 sole checkpoints, execute all five arm masks on paired views, preserve common exogenous bytes and all-tapes-retained law, emit complete opaque reducer rows. High case covers arm-mask or recurrent-state divergence found late. |
| First-application-valid REAL/SHAM runner | 4 | 7 | 11 | Detect the frozen first valid application, clone exact state, apply REAL versus SHAM at the registered suborder, execute 100 paired ticks and preserve byte-identical prefork telemetry/lineage. |
| Complete 24-by-6,990 reducer and inference data plane | 6 | 10 | 16 | Map every population/contrast/endpoint/phase row, verify 24 block rows per estimand, run 99,999 joint resamples, common-anchor schedule/regime intersections and exhaustive first-match result firewall. High case is dominated by completeness/audit failures rather than arithmetic. |
| **Five-flow subtotal** | **28** | **48** | **76** | Does not include integration or acceptance below. |

### Cross-cutting work

| Work family | Low | Central | High | Included work |
|---|---:|---:|---:|---|
| Cross-flow integration | 4 | 7 | 12 | One identity/coordinate, stage-to-stage byte contracts, checkpoint/evaluation/fork/reducer lineage, create-only frontier and successor-slice continuity. |
| Independent TEST acceptance | 5 | 8 | 13 | Deterministic oracles, tamper/stale-parent/duplicate/missing-coordinate cases, arm/mask equivalence, recurrent persistence, fork suborder and 6,990-row completeness. |
| End-to-end production-chain reacceptance | 3 | 5 | 8 | Result-blind full-chain canaries, failure injection, crash/resume, final firewall and no-partial-output audit. |
| Resource remeasurement | 2 | 3 | 5 | Current-byte CPU/wall throughput, eight-worker scaling, simultaneous RSS, scratch/durable/I/O and complete-panel projection. |
| Exact lease-request preparation | 1 | 2 | 3 | Immutable source/artifact manifest, Root lease schema/validator, one-identity binding, slice rules, exact CLI and rollback/terminal receipts. |
| **Cross-cutting subtotal** | **15** | **25** | **41** | Independent of the five-flow subtotal. |
| **Rolled-up total** | **43** | **73** | **117** | Engineer-days; parallel work changes calendar duration, not this total. |

## Assumptions

- The Pro-closed R06 science, native host recurrence, controller graph, PPO,
  optimizer, thresholds, branches and resource ceilings do not change.
- Existing native protocol/CAS/promotion, deterministic evaluation population,
  TEST training update, lifecycle primitives and inference algebra remain valid
  building blocks, but seam evidence is not treated as a production executor.
- One experienced engineer-day means one focused implementation/verification
  day with the existing Windows CPU toolchain and repository familiarity.
- Estimates include code, review-quality self-audit, fixtures and acceptance
  artifacts; they exclude the later 302.2-CPU-hour empirical panel itself.
- No provider, deployment, flight, Git publication or scientific result
  interpretation is included.

## Critical path and safe parallelism

The semantic critical path is:

```text
TRAIN address/reset binding
 -> persistent native/policy training loop
 -> sole checkpoint contract
 -> five-arm paired evaluator
 -> first-valid REAL/SHAM rows
 -> complete reducer/inference
 -> end-to-end reacceptance
 -> resource remeasurement
 -> exact lease request
```

Safe parallel work is limited but material:

- TRAIN coordinate generation can proceed alongside reducer identity/source-map
  construction after their schemas are frozen.
- REAL/SHAM runner implementation can proceed alongside the evaluator, sharing
  only a frozen state/row interface.
- TEST oracle design can begin with each flow, while independent end-to-end
  acceptance waits for all five.
- Resource tooling and lease-schema drafting can proceed late in integration,
  but final measurements and hashes must use the combined accepted bytes.

With three qualified engineers, low/central calendar duration might compress
to roughly 20/32 working days; high-case critical-path coupling remains roughly
50 working days. These calendar figures are planning illustrations, not extra
estimates or authority.

## Uncertainty and invalidation conditions

Largest uncertainty drivers are recurrent hidden-state equivalence across
native/policy/checkpoint boundaries; mask-on/off common-random-number coupling;
first-valid fork timing under resume; and exhaustive reducer source mapping.
The high case also covers late discoveries requiring repeated eight-worker
reacceptance.

This decomposition is invalid and must return for reassessment if any of the
following occurs:

- a treatment, comparator, threshold, branch, checkpoint, coordinate or claim
  change is required;
- the 11,520/120/115,200/6,912/6,990 inventories change;
- a second identity, partial panel or Python rollout fallback is proposed;
- current-byte projection exceeds ordinary `320 CPUh/65 h` or any hard ceiling;
- retained native recurrence, PPO persistence or REAL/SHAM suborder cannot be
  implemented without changing science; or
- reusable substrate is unavailable and must be replaced rather than bound.

## R06-specific versus reusable-within-DISH

| Family | R06-specific | Reusable within DISH |
|---|---|---|
| TRAIN reset generation | R06 prefix and exact training allocation binding | Counter-address builder, finite-draw validation, native row schema |
| Persistent trainer | Arm masks, checkpoint/update inventory and R06 job keys | Recurrent policy/native loop, PPO state persistence, Welford/optimizer resume |
| Evaluator | Speed-stratified R06 population and mask pair schedule | Batched checkpoint evaluation, common-random-number views, opaque row lifecycle |
| REAL/SHAM | R06 first-application-valid population binding | Clone/suborder/lineage machinery and paired 100-tick execution |
| Reducer/inference | 6,990 identities, speed anchors and schedule/regime intersections | Block-row registry, joint max-t engine, completeness and result firewall |
| Integration/lease | Exact R06 object hashes and stage totals | Same-identity frontier, resource guards, successor slices and create-only receipts |

Approximately 45–55% of central engineering effort is reusable within later
DISH revisions if their scientific interfaces remain compatible; none is
claimed reusable across unrelated directions without a separate assessment.

## Preserved invariants

Every estimate assumes and preserves:

```text
panel=INDIVISIBLE_11520_TAPES|120_TRAINING_JOBS|115200_EVALUATIONS|6912_FORKS|6990_ESTIMANDS
identity=ONE_FRESH_BLINDED_NONREPLACEABLE_R06_MASTER_IDENTITY_COORDINATE
native=FULL_RESET_STEP_RECURRENCE|NO_PYTHON_ROLLOUT_FALLBACK
persistence=MODEL|OPTIMIZER|WELFORD|RECURRENT_STATE|SOLE_UPDATE_1024_CHECKPOINT|ATOMIC_RESUME
fork=FIRST_APPLICATION_VALID|PAIRED_REAL_SHAM|REGISTERED_SUBORDER|100_TICKS
inference=COMPLETE_24x6990|99999_JOINT_RESAMPLES|COMMON_ANCHOR_INTERSECTIONS|15_FIRST_MATCH
firewall=RESULT_BLIND|NO_PARTIAL_POPULATION_OR_VALUE|CREATE_ONLY_COMPLETE_RESULT
atomicity=SAME_IDENTITY_SUCCESSOR_SLICES|NO_PANEL_SHRINK|NO_REPLACEMENT
```

```text
observed_fact=Read-only decomposition estimates the missing unchanged-science production data plane at 43/73/117 experienced engineer-days low/central/high; runtime-resource evidence remains inside the existing envelope.
local_action_fence=Assessment only; no source, TEST, runtime, lease request, lease, identity, coordinate, model, checkpoint or output action.
does_not_imply=Expanded engineering authority|lease authority|science change|partial panel|R05 action.
scientific_stage_continuation=R06 remains the applied empirical and sole direct-UAV object while Portfolio decides whether the expanded engineering cost is justified.
continuation_owner=Portfolio for the cost/value decision; Operational Root and same DISH CM only after an explicit expanded envelope.
root_decision_class=ASSESSMENT_ONLY_COST_DECOMPOSITION|PORTFOLIO_DECISION_REQUIRED.
```
