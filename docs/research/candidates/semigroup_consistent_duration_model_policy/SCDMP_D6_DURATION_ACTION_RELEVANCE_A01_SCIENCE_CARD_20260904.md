# SCDMP D6 duration-action relevance A01 — science card (2026-09-04)

## Freeze and provenance

- Object: `SCDMP-D6-DURATION-ACTION-RELEVANCE-A01`
- Direction: `semigroup_consistent_duration_model_policy`
- Evidence class: **A/RECON**
- Scientific status: **FROZEN before implementation, smoke, cost measurement or observation**;
  CM may append only the outcome-blind numeric cost row required below, changing no scientific
  field
- Launch readiness: **HELD only for conforming implementation, its single technical-smoke cost
  row, and the fresh mandatory resource admission**
- Direction authority: `PRO_FINAL — SPLIT_A_RECON_THEN_REOPEN_B`, response SHA-256
  `a98efe074a2bd0ec714e5495209555b4745d724a9894c2f8c72669c40bdb8621`
- Current B status: `SCDMP-D6-CROSS-K-Q-SHARING-B01` is
  `NOT_LAUNCHABLE_SECTION_11_4_METHOD_CONFLICT`
- No smoke, resource admission, census, dataset, model, optimizer, learner, evaluator mission or
  result exists at this freeze.

This is the only object admitted by the correcting convergence decision. It is a finite
host/population/action census, not an algorithm experiment and not a disguised B launch gate. A
valid intake returns to the same convergence binding; no A branch authorizes B.

## Question, claim ceiling and non-goals

**Question.** On the exact declared SCDMP row, fixed six-state public source population, balanced
HR/RH counterfactual twins, six composite actions and sixteen paired tapes per state, does native
full-mission return exhibit all of:

1. a material preference for `k=7` in at least one state;
2. a material preference for `k=13` in at least one state; and
3. a nonzero candidate-action value span?

Material means a state-level best-across-skill cross-duration mean difference of at least one
endpoint tick, `1/364`.

**Maximum claim.** A positive branch supports only finite native duration-action relevance on this
exact host, six states, action catalogue and sixteen-tape panel. An adverse branch rejects at most
this exact host/source/population/action panel as a substrate for the proposed action-linked D6
question. Neither polarity establishes or refutes D6 on another population or host.

**Non-goals.** No branch tests or establishes D6 value-sharing benefit or harm; D8 competence;
regularization, optimization or negative-transfer causation; graded B01 order value; D2
interruption or learned termination; endogenous duration acquisition; unseen-`k` or held-out-`k`
transfer; semigroup/duration invariance; stable superiority; general MARL value; safety,
deployment or flight readiness; or authorization to launch a later B object.

## Native host and protected semantics

Use the existing SCDMP native host with exactly:

```text
TAU_LEAK = 0.92
Z_LIMIT  = 0.25
HORIZON  = 364 primitive ticks
```

All other native equations, constants, HR/RH event transformations, failure predicates, dock
predicate, observation normalization, numerical precision and side effects remain unchanged. Use
the unchanged reset scalars `initial_v=0.015`, `initial_y=0`, and `initial_phi=0`. No return from
the earlier graded diagnostic is imported.

## Fixed source population

Execute exactly two treatment-common source trajectories:

| source stream | source action | source clock |
| ---: | --- | --- |
| `9011` | `COMMON=0` | fixed `k=7` |
| `9013` | `COMMON=0` | fixed `k=13` |

Both streams use:

```text
pre_event_p = (1,2,3,4)
pre_event_q = 0
```

`pre_event_q` is literal: never draw, alternate, select or key it by stream, duration, target,
tape or outcome. The stream identifiers address only their deterministic native disturbance
coordinates.

From each stream retain the first legal renewal at or after each target tick `64`, `160`, and
`256`, yielding the intended six states. At each retained state:

1. clone the source state into HR and RH worlds;
2. apply the corresponding event order;
3. apply the common zero-tick `LEVEL_RELEASE`; and
4. require byte-equal actor-visible public observations immediately before the candidate action.

The latent graph, assignment, future tape, oracle action and oracle return are evaluator-only.
There is no learner. No B01 or FCEOV foundation, state, checkpoint, tape, `q_by_cell`, selected
action map, result root, threshold or inference rule may be read or reused. If a source trajectory
terminates before one of its three renewals, or a required twin lacks the common public
observation, apply the source-population branch below; substitute no state.

## Actions, continuation and endpoint

```text
Z = {0,10,12}
K = {7,13}
A = Z × K
```

The fixed order is `(0,7),(0,13),(10,7),(10,13),(12,7),(12,13)`. For each action, hold `z` for
exactly `k` primitive ticks, then execute `COMMON=0` on that selected action's same fixed `k`
renewal clock until safe dock, native failure or timeout.

The endpoint is

```text
U = 1{safe dock} × (1 - dock_tick / 364)
```

and native failure or timeout gives `U=0`.

## Fixed evaluation tapes and RNG

Use the card's deterministic address-stable native disturbance generator under evaluation domain
`9029`. Before any outcome is read, materialize tape indices `0..15` for every state. Each
state/tape realization is shared across both HR/RH twins and all six actions. Never redraw,
replace, extend or outcome-select a tape.

These tapes are A-only evidence. A later B, if separately frozen, must use fresh training and
learner-evaluation domains. This A table cannot become a later learner's evaluation panel or a B
launch condition. No library-global RNG may select a scientific coordinate.

## Exact observables and estimands

For state `j`, action `a`, graph `g` and tape `t`, define the integer endpoint numerator

```text
Y[j,a,g,t] = 364 - dock_tick[j,a,g,t]   if safe dock
             0                           if failure or timeout
```

Then define

```text
S_j(a) = sum over g∈{HR,RH}, t∈{0..15} of Y[j,a,g,t]
V_j(a) = S_j(a) / (32 × 364)

B_j,7  = max over z∈{0,10,12} S_j((z,7))
B_j,13 = max over z∈{0,10,12} S_j((z,13))
D_j    = B_j,7 - B_j,13
```

Every action mean has 32 endpoint cells, so a mean difference of `1/364` is exactly 32 numerator
units:

```text
R7  = 1{there exists j with D_j >= 32}
R13 = 1{there exists j with D_j <= -32}

W_j = max_a S_j(a) - min_a S_j(a)
W   = sum over j=1..6 of W_j
```

The integer rule avoids letting a lexicographic tie decide whether a duration is materially
preferred. Report every `S_j(a)` and `V_j(a)`; every `B_j,7`, `B_j,13` and `D_j`; `R7`, `R13`,
every `W_j` and `W`; safe-dock, failure-family and timeout counts by state/action/graph; and actual
native transition, mission and evaluator-call counts.

## Work law, exposure, resource admission and cost

Scientific inventory:

| quantity | exact count |
| --- | ---: |
| source trajectories | `2` |
| candidate-evaluation missions | `1,152` |
| models | `0` |
| training datasets | `0` |
| optimizer updates / AdamW steps | `0 / 0` |
| learner evaluations | `0` |

The census is `6 states × 6 actions × 2 graphs × 16 tapes = 1,152` native missions.
Conservative primitive-tick ceilings are `2 × 364 = 728` for source trajectories and
`1,152 × 364 = 419,328` for evaluation, totaling `420,056`. A partial table has no scientific
meaning.

**Exposure line.** This object has no model, optimizer, learned tensor or initialization scale.
Its exact exposure statement is `NO_LEARNED_PARAMETERS — exposure not applicable`. This is a
property of the A contract, not a measured result and not a substitute for the mandatory
treatment-head exposure line of any later learned B.

This is one A/RECON scientific invocation. Before it, run
`python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` and require both physical
and effective available memory to be at least 4 GiB. Peak RSS and wall time are recorded; missing
resource telemetry leaves a non-resource result valid as `resources_unmeasured`.

The A runner's single technical smoke must supply one prospective numeric row using

```text
P = 2 × (t_native_mission × 1,154
       + t_adamw_step × 0
       + t_candidate_score × 0)
    + 60 seconds
```

| technical smoke | `t_native_mission` | native missions | `t_adamw_step` | AdamW steps | `t_candidate_score` | candidate scores | `P` | cap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `2026-09-04 A01 toy` | `0.002741849995800294 s` | `1,154` | `0 s` | `0` | `0 s` | `0` | `66.32818979030708 s` | `1,800 s` |

No numeric projection exists at freeze. The scientific invocation is not started while that row
is absent or above `1,800 s`; its hard observed cap is also `1,800 s`. Failed admission, excessive
projection or a cap stop has no scientific polarity. The smoke is technical only: it must use toy
coordinates, create no scientific state/tape/result root and publish no A branch.

## Stop rule

1. A conforming implementation performs exactly one technical smoke and records the prospective
   A cost row.
2. Immediately before the single scientific invocation, take the fresh 4 GiB admission.
3. Execute both fixed source trajectories.
4. If the six-state treatment-common population is not established, publish only the declared
   source-population branch and stop.
5. Otherwise materialize the fixed A tapes and execute all 1,152 missions.
6. Do not stop for interim duration preference, favorable contrast, zero span or a partial state.
7. Analyze exactly once after every required terminal cell exists.
8. Add or substitute no state, stream, action, tape, parameter or coordinate.

## Ordered A/RECON result rule

Apply the first matching branch.

1. **`A_NO_RESULT_RESOURCE_REFUSAL`** — the smoke-derived cost row is absent; projected wall exceeds
   `1,800 s`; the fresh 4 GiB admission is absent/fails; or the scientific invocation is not
   started. No scientific observation; the A object remains unobserved.
2. **`A_INVALID_EVIDENCE`** — outside the intended source-population failure below, native
   execution or endpoint arithmetic is incomplete/nonfinite; a required cell is missing or
   duplicated; a state/tape is outcome-replaced; the declared source/tape law is not executed; the
   hard cap is crossed before completion; transition/evaluator counts are zero or incompatible;
   or publication is incomplete. No scientific observation; repair only.
3. **`A_SOURCE_POPULATION_NOT_ESTABLISHED`** — either fixed source stream fails to yield its three
   required legal renewals by the horizon, or any required twin lacks byte-equal actor-visible
   public observations before the candidate action. Reject this source law's intended six-state
   treatment-common population; reopen the direction; authorize no learner object.
4. **`A_TWO_SIDED_DURATION_ACTION_RELEVANCE`** — `W>0`, `R7=1`, and `R13=1`. On this exact finite
   panel at least one state materially prefers each duration and actions have nonzero return span.
   Reopen convergence to decide whether to freeze a newly named D6-versus-D8 B; this branch does
   not authorize it.
5. **`A_ONE_SIDED_DURATION_ACTION_RELEVANCE`** — `W>0` and exactly one of `R7`,`R13` equals 1.
   Reopen convergence to decide whether one prospectively different source population is
   scientifically justified; launch no automatic derivative.
6. **`A_ACTION_RELEVANT_NO_MATERIAL_CROSS_K_PREFERENCE`** — `W>0`, `R7=0`, and `R13=0`. Actions
   affect native return, but this panel cannot support the intended duration-linked D6 question;
   reopen for an independently justified population change or park assessment.
7. **`A_ZERO_ACTION_VALUE_SPAN`** — `W=0`. All six actions have identical paired native return on
   this panel; reopen for an independently justified host change or park assessment.

The branches are exhaustive because every `W_j>=0` and `R7`,`R13` are binary. No branch authorizes
B or changes Portfolio state.

## Predictions on record

- **DM prediction, 2026-09-04 before implementation:**
  `A_TWO_SIDED_DURATION_ACTION_RELEVANCE`, at low confidence. Early/middle/late renewal states make
  a state-dependent `k=7` versus `k=13` native consequence plausible, while the tiny mixed-sign
  graded observation is the strongest reason this prediction may fail.
- **Owner prediction:** `not taken (unattended)`.

Predictions do not alter the ordered rule.

## Later-B boundary

This card creates no B. After valid A intake, the exact direction-tier question is:

> Does the completed A census establish `W>0`, `R7=1`, and `R13=1` on the exact declared host and
> six-state population, such that a newly named, three-seed D6-versus-D8 B/EXPLORE learner/evaluator
> using fresh training and evaluation tapes and no pre-learner census gate is decision-relevant?
> If not, does the observed A branch justify one prospectively different host or source-population
> object, or should D6 be parked?

Any later B must be newly frozen, run its complete real environment/learner/trainer/evaluator path,
report nonzero transitions, optimizer updates and learner evaluations, use fresh tapes, contain no
A result as a launch condition, and retain a finite B/EXPLORE claim ceiling. D6/D8 architecture,
three-seed or cost/exposure details from the withdrawn card are only prospective inputs to that
later decision, not current authorization.

## Implementation ownership and engineering scope

Owned paths for this A object are:

- `experiments/candidates/scdmp_variable_k/d6_duration_action_relevance_a01/`
- `scripts/run_scdmp_d6_duration_action_relevance_a01.py`
- `tests/experiments/candidates/scdmp_variable_k/d6_duration_action_relevance_a01/`
- `temp/directions/semigroup_consistent_duration_model_policy/exp/d6_duration_action_relevance_a01/`
- this card, its later result evidence and intake.

The implementation may reuse unchanged canonical native equations and outcome-blind helper code,
but it must not execute or import a B learner, optimizer, B branch rule, B result artifact or
stopped-object scientific state. Core files are not owned.

**Engineering scope §4: this object needs none of the prohibited items.** Use one argparse runner
and a plain documented smoke/run command. Add no scheduler, queue, retry, resume, checkpoint,
lock, heartbeat, manifest/hash/provenance guard, incident tree, schema/version field, registry,
framework, compatibility shim or telemetry beyond wall/peak RSS. Research code is limited to
2,000 new lines excluding tests/card, the runner to 600 lines, and orchestration to under 30%.
Tests comprise exact seven-branch rule tests and one toy-size end-to-end smoke under 60 seconds.

Technical success can establish only that the fixed source/census arithmetic, counts, artifact
shape and numeric cost row are implemented. It cannot establish source-population existence,
duration-action relevance, any A branch or any D6/D8 scientific claim.
