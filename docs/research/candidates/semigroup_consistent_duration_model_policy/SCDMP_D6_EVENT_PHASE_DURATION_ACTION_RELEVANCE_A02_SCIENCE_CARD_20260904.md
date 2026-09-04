# SCDMP D6 event-phase duration-action relevance A02 science card

Frozen: 2026-09-04, before any A02 smoke, source state, tape or scientific outcome.

## Identity and authority

- Object ID: `SCDMP-D6-EVENT-PHASE-DURATION-ACTION-RELEVANCE-A02`
- Evidence class: A/RECON
- Scientific status: prospectively specified; unexecuted
- Direction authority: `PRO_FINAL=ADMIT_ONE_PROSPECTIVE_A_RECON`
- Claim ceiling: finite A/RECON only
- Learner status: no model, optimizer, training dataset, checkpoint or learned parameter
- B authorization: none

This is the sole additional population admitted by the complete archived convergence decision.
There is no second source population, host sweep, countdown sweep, learner, D6/D8 B or automatic
derivative.

## Question and non-goals

> On the unchanged SCDMP native row, does a public time-to-event coordinate create native
> duration-action relevance with the sign predicted by renewal alignment: `k=7` favored when the
> event is seven ticks away, and `k=13` favored when the event is seventy-eight ticks away, under
> an otherwise identical event-responsive action rule?

The question is whether renewal phase relative to an observable event changes which fixed duration
has native return value. It does not ask whether D6 learns that relation; whether cross-`k`
parameter sharing, regularization or sample efficiency helps; whether D2 interruption has value;
or whether the result transfers beyond the exact finite population.

## Mechanism trace and live explanations

```text
public native state plus fixed public time-to-next-event
→ fixed renewal clock k ∈ {7,13}
→ common neutral pre-event action
→ scheduled existing HR or RH event sequence
→ zero-tick LEVEL_RELEASE
→ event order becomes public
→ renewal clock fixes latency to the next action decision
→ fixed event-order-matched action
→ native cable, motion, dock, failure and timeout dynamics
→ full-mission endpoint U
```

The primary prediction is a native consequence of opposed renewal alignment. The strongest legal
null is the same-information alternative clock. Other live explanations are a general longer-hold
docking-time advantage, endpoint insensitivity to six ticks, heterogeneous state effects, or
event application that cannot be represented without changing protected native semantics.
Prediction accuracy without an action or native-return difference is not valuable evidence.

## Exact host and protected semantics

Retain exactly:

```text
TAU_LEAK = 0.92
Z_LIMIT  = 0.25
HORIZON  = 364 primitive ticks

initial_v   = 0.015
initial_y   = 0
initial_phi = 0

pre_event_p = (1,2,3,4)
pre_event_q = 0
```

All native transition equations, numerical precision, action semantics, HR/RH transformations,
failure predicates, dock predicate, observation normalization, terminal ordering and
`LEVEL_RELEASE` semantics remain unchanged from A01. The only new population coordinate is a
fixed public event calendar. The existing HR/RH operators move from immediately before the
duration choice to a prospectively fixed future tick; they are not altered.

## Source-population law

Use one fixed root seed:

```text
A02_ROOT_SEED = 9173
```

Generate two treatment-common source trajectories with address-separated domains:

| source domain | source action | source renewal clock |
| --- | ---: | ---: |
| `SCDMP-D6-A02/SOURCE/K7` | `COMMON=0` | `k=7` |
| `SCDMP-D6-A02/SOURCE/K13` | `COMMON=0` | `k=13` |

Retain native source states at exact ticks `91`, `182` and `273`. They are legal renewal
boundaries for both clocks because `91=lcm(7,13)`; no first-after-target search is used. The two
domains and three ticks yield six base states. Clone each base state into public countdowns
`time_to_event ∈ {7,78}`, yielding twelve scenario states.

For every scenario state:

1. record the native public observation and public countdown;
2. clone into balanced `HR` and `RH` event-order worlds;
3. begin both clock policies from identical native state bytes;
4. apply the chosen event sequence after exactly the declared countdown;
5. apply `LEVEL_RELEASE` immediately after the event sequence;
6. make the observed order available to the fixed continuation rule; and
7. expose no latent assignment, future disturbance, endpoint, oracle return or counterfactual
   outcome.

Event ordering at the scheduled tick is exactly:

```text
complete the transition reaching the event tick
→ apply HR or RH event sequence
→ apply zero-tick LEVEL_RELEASE
→ perform any renewal decision due at that same tick
```

If the population or ordering cannot be represented without changing protected native semantics,
publish the declared population branch. Do not substitute a calendar, source state, target tick or
event offset.

## Treatment and strongest same-information comparator

The finite treatment is `EVENT_CLOCK_7`; the strongest competent same-information comparator is
`EVENT_CLOCK_13`. The roles are symmetric for interpretation: each is the other clock's null at a
given countdown.

`EVENT_CLOCK_7` uses renewal period 7. `EVENT_CLOCK_13` uses renewal period 13. Both use the same
rule:

```text
before the event: choose COMMON=0 at every renewal
at the first renewal at or after the event:
    HR observed → choose action 10
    RH observed → choose action 12
afterwards: retain the corresponding matched action at every renewal
```

The two policies differ only in renewal timing. They receive the same native state, public
countdown, disturbance tape, event, pre-event action, observed-order-to-action map and terminal
endpoint. There is no D2-style interruption; decisions occur only on the selected fixed clock.

The response latencies are fixed prospectively:

| public countdown | `k=7` latency | `k=13` latency | predicted sign |
| ---: | ---: | ---: | --- |
| `7` | `0` ticks | `6` ticks | `k=7` favored |
| `78` | `6` ticks | `0` ticks | `k=13` favored |

## Endpoint, tapes and pairing

The endpoint remains

$$
U=\mathbf 1\{\mathrm{safe\ dock}\}
\left(1-\frac{\mathrm{dock\ tick}}{364}\right),
$$

with native failure or timeout equal to zero.

Use evaluation domain `SCDMP-D6-A02/EVALUATION`. For each of the six base states, materialize
exactly tapes `0,1,…,15`. Address each disturbance by

```text
(base_state, tape_index, primitive_tick, disturbance_channel)
```

and exclude countdown, clock policy and graph. The same tape is shared across both countdowns,
both clock policies and both HR/RH worlds. Freeze all tapes before any endpoint is read. There is
no redraw, extension, replacement, state substitution or result-conditioned schedule change. A01
domain `9029` and its tapes are not reused.

## Observable, estimand and exact material units

For base state \(b\), countdown \(d\in\{7,78\}\), clock \(k\in\{7,13\}\), graph \(g\), and tape
\(t\), define

$$
Y_{b,d,k,g,t}=
\begin{cases}
364-\operatorname{dock\_tick}_{b,d,k,g,t}, & \text{safe dock},\\
0, & \text{failure or timeout}.
\end{cases}
$$

The paired duration contrast is

$$
K_{b,d}=\sum_{g\in\{HR,RH\}}\sum_{t=0}^{15}
\left(Y_{b,d,7,g,t}-Y_{b,d,13,g,t}\right).
$$

Each base/countdown contrast contains 32 paired endpoint cells, so a one-tick mean advantage is
exactly 32 numerator units. Aggregate over the six base states:

$$
K_d=\sum_{b=1}^{6}K_{b,d},
$$

where a one-tick aggregate mean advantage is `6×32=192` numerator units. Also record

$$
N_7^+=\#\{b:K_{b,7}\ge32\},\qquad
N_7^-=\#\{b:K_{b,7}\le-32\},
$$

$$
N_{78}^-=\#\{b:K_{b,78}\le-32\},\qquad
N_{78}^+=\#\{b:K_{b,78}\ge32\}.
$$

Define exactly:

```text
SHORT_ALIGNMENT =
    K_7 >= 192
    and N_7+ >= 4
    and N_7- <= 1

LONG_ALIGNMENT =
    K_78 <= -192
    and N_78- >= 4
    and N_78+ <= 1
```

Publish every `Y`, `K_b,d` and `K_d`; event-to-first-matched-action latency; safe-dock, timeout
and every native failure-family count; missions, native transitions and evaluator calls; and mean
utility by base state, countdown, graph and clock.

## Work inventory, cost and resource bound

```text
source trajectories:                 2
base states:                          6
public countdown conditions:         2
clock policies:                       2
graphs:                               2
tapes per base state:                16

candidate missions: 6×2×2×2×16 =   768

models:                               0
training datasets:                    0
optimizer updates:                    0
AdamW steps:                          0
learner evaluations:                  0

source ceiling:       2×364 =        728 primitive ticks
candidate ceiling:  768×364 =    279,552 primitive ticks
total ceiling:                    280,280 primitive ticks
```

This is one fixed panel, not a sweep. Before execution its runner's single outcome-blind technical
smoke must produce a numeric projection:

$$
P=2\left(t_{\mathrm{native\ mission}}\times770\right)+60\ \mathrm{s},
$$

where 770 counts two source trajectories plus 768 missions. No numeric A02 projection exists at
freeze. The A01 wall time `8.115556099975947 s` is historical evidence only and must not be used as
the A02 projection.

The projection cap and hard observed scientific-invocation cap are each `1,800 s`. Immediately
before the scientific invocation run the repository memory preflight and require at least `4 GiB`
physical and effective available memory. A missing/failed projection, refusal, or cap stop has no
scientific polarity and creates no scientific root.

## Exposure line

```text
NO_LEARNED_PARAMETERS — exposure not applicable
```

There is no parameter-displacement denominator, learner exposure, optimizer exposure or
model-selection exposure. This does not satisfy or replace the treatment-head exposure line for
any later learned B.

## Stop rule

1. Freeze this complete object before an A02 smoke or outcome.
2. Run one technical smoke solely to obtain the prospective numeric cost row.
3. Take the fresh `4 GiB` admission immediately before the single scientific invocation.
4. Generate the two fixed sources and retain only ticks `91`, `182` and `273`.
5. If all six base states or the declared event calendar cannot be established, publish only the
   population branch.
6. Otherwise materialize all fixed tapes before reading an endpoint.
7. Execute all 768 missions.
8. Do not stop for an interim clock advantage, failure pattern, zero gap or favorable phase.
9. Analyze once after the complete terminal inventory exists.
10. Add or substitute no countdown, event tick, state, stream, action rule, graph, tape, host
    constant or endpoint.
11. No valid result permits a second A02 population or countdown sweep.

## Ordered finite result rule

Apply the first matching branch.

1. **`A02_NO_RESULT_RESOURCE_REFUSAL`** — the smoke-derived cost row is absent; projection exceeds
   `1,800 s`; fresh admission is absent/fails; or the invocation never begins. No scientific
   observation; the object remains unobserved.
2. **`A02_INVALID_EVIDENCE`** — a mission is missing, duplicated, nonterminal or nonfinite; tape
   pairing is wrong; event timing is not `7` or `78`; latency arithmetic differs from the declared
   renewal order; hidden event information enters early; the declared source/action/event law is
   not executed; a coordinate is outcome-replaced; required transition/evaluator counts are zero;
   the hard wall cap is crossed before completion; or publication is incomplete. No scientific
   observation; repair only and do not interpret partial values.
3. **`A02_EVENT_PHASE_POPULATION_NOT_ESTABLISHED`** — either source lacks all three exact common
   renewals; a base state terminates before its event; the event cannot be applied in the declared
   order under unchanged native semantics; or public countdown and visible post-event order cannot
   be represented. No replacement population, learner or B is authorized.
4. **`A02_EXPECTED_TWO_SIDED_EVENT_ALIGNMENT`** — `SHORT_ALIGNMENT=true` and
   `LONG_ALIGNMENT=true`. The panel supports the predicted event-phase opportunity. Reopen
   convergence to decide whether a separately frozen D6/D8 B on a fresh mixed-phase population is
   warranted; this branch does not authorize B.
5. **`A02_REVERSED_EVENT_ALIGNMENT`** — `(K_7 <= -192 and N_7- >= 4)` or
   `(K_78 >= 192 and N_78+ >= 4)`. At least one countdown has a material state-consistent sign opposite
   the latency prediction. Reopen only to record a park decision; do not search countdowns.
6. **`A02_SHORT_ALIGNMENT_ONLY`** — `SHORT_ALIGNMENT=true`, `LONG_ALIGNMENT=false`, and branch 5
   did not match. This supplies a finite `k=7` opportunity but lacks the opposed control. Reopen
   convergence; no B is authorized.
7. **`A02_LONG_ALIGNMENT_ONLY`** — `SHORT_ALIGNMENT=false`, `LONG_ALIGNMENT=true`, and branch 5
   did not match. This again supplies only longer-duration advantage. Park at the next convergence
   intake unless evidence outside this source-search lineage supplies a qualitatively new
   mechanism.
8. **`A02_ZERO_DURATION_POLICY_SPAN`** — every `K_b,d=0`. Renewal phase changes no native endpoint
   in this panel. Park the action-choice family; no learner comparison is decision-relevant here.
9. **`A02_NONMATERIAL_OR_HETEROGENEOUS_EVENT_ALIGNMENT`** — every other valid complete result.
   Effects are too small, inconsistent or heterogeneous for this question. Reopen convergence to
   record parking or assess only a qualitatively new non-search mechanism. No further population
   census is authorized.

The branches are finite and exhaustive by first-match ordering. No branch authorizes B or changes
Portfolio state.

## Predictions on record

- **DM prediction, 2026-09-04 before implementation:**
  `A02_EXPECTED_TWO_SIDED_EVENT_ALIGNMENT`, low confidence. Exact opposed six-tick response
  latencies make both signs plausible; A01's uniform 179--197-unit `k=13` advantage is the strongest
  reason the prediction may fail.
- **Owner prediction:** `not taken (unattended)`.

Predictions do not alter the rule.

## Finite claim ceiling and later boundary

A favorable branch could establish only that, on the exact `.92/.25` host, six declared base
states, countdowns `{7,78}`, fixed event-responsive clocks, balanced HR/RH events, sixteen paired
tapes and stated endpoint, renewal phase produced the declared finite native duration-action
pattern. It cannot establish D6/D8 competence, sharing value, sample efficiency, regularization,
negative-transfer causation, endogenous duration selection, D2 interruption value,
unseen-duration transfer, semigroup invariance, general MARL superiority, safety or deployment.

After valid intake, reopen `em:semigroup_consistent_duration_model_policy:convergence` with the
complete result. Only that node may decide whether a newly frozen B is warranted or the family
parks. An adverse result implicates only this exact event-phase population and fixed policy panel.

## Implementation ownership and engineering scope

Owned paths are:

- `experiments/candidates/scdmp_variable_k/d6_event_phase_duration_action_relevance_a02/`
- `scripts/run_scdmp_d6_event_phase_duration_action_relevance_a02.py`
- `tests/experiments/candidates/scdmp_variable_k/d6_event_phase_duration_action_relevance_a02/`
- `temp/directions/semigroup_consistent_duration_model_policy/exp/d6_event_phase_duration_action_relevance_a02/`
- this card, its later result evidence and intake.

The implementation may reuse unchanged A01/native helpers but must not import or execute the
stopped B learner, optimizer, B branch rule or stopped scientific state. Core files are not owned.

**Engineering scope specification §4: this object needs none of the default-prohibited items.**
Use one research module, one argparse runner, the nine exact branch tests and one toy end-to-end
smoke under 60 seconds. Add no scheduler, queue, retry/resume/checkpoint system, lock, heartbeat,
manifest or provenance guard, incident tree, schema/version framework, registry, compatibility
shim or telemetry beyond wall time and peak RSS. Keep research-code changes below 2,000 lines
excluding tests/card, the runner below 600 lines and orchestration below 30% of the diff.

Technical success establishes only that the fixed calendar, pairing, integer arithmetic, counts,
artifact shape and cost row are implemented. It cannot establish that the population exists, that
renewal phase changes native value, any A02 branch, or any D6/D8 scientific claim.
