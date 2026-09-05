PRO_FINAL=ADMIT_ONE_PROSPECTIVE_A_RECON

## Smallest supported direction conclusion

The valid `SCDMP-D6-DURATION-ACTION-RELEVANCE-A01` result closes the **current stationary/post-event source population** as a substrate for the intended bidirectional D6 action-choice question. It does not justify a D6-versus-D8 B experiment: all six states materially favored `k=13`, `R7=0`, and the controlling prior decision expressly requires another direction decision before any B may exist.

Exactly one further A/RECON population is nevertheless justified. It is not a search across states or parameters for a favorable sign. It follows independently from the direction’s event/duration mechanism and the renewal arithmetic of the fixed menu `K={7,13}`:

* when the next observable event occurs **7 ticks** after the decision boundary, a `k=7` clock can react at the event while `k=13` reacts six ticks later;
* when the event occurs **78 ticks** after the boundary, `78=6×13`, while the adjacent `k=7` renewals are at ticks `77` and `84`; `k=13` can therefore react at the event while `k=7` reacts six ticks later.

These two countdowns are the opposed six-tick phase alignments of the two renewal lattices inside their `lcm(7,13)=91` cycle. They are selected algebraically before outcomes, not because A01 lacked a `k=7` sign. The direction record already identifies event/duration-order noncommutation and coordinated renewal as the temporal mechanism lineage, and defines D6 as sharing duration-conditioned values across `k`, distinct from D2 mid-segment interruption.

Accordingly:

> **Admit one event-phase A/RECON census. Do not authorize a learner, D6/D8 B object, host sweep, countdown sweep, or automatic derivative.**

A and B adaptation is permissible at the smallest implicated unit, and an A census may be used when it is the cheapest discriminator of whether the proposed action opportunity exists. It must remain a separate result, not a hidden B-launch condition.

## Direct evidence controlling this decision

The A01 evidence is complete and internally recomputed:

* all six frozen source states were established;
* all `1,152/1,152` paired native missions terminated;
* all missions safe-docked;
* there were `203,877` native transitions and `1,152` evaluator calls;
* there were no models, training datasets, optimizer updates, AdamW steps, or learner evaluations;
* `W=2498`, `R7=0`, and `R13=1`;
* every state’s best `k=13` action exceeded its best `k=7` action by `179–197` integer numerator units, versus the material threshold of `32`;
* the ordered branch was `A_ONE_SIDED_DURATION_ACTION_RELEVANCE`;
* exposure was `NO_LEARNED_PARAMETERS — exposure not applicable`;
* valid-result machine time was exactly `8.115556099975947 s`.

Because every mission safely docked, the observed preference was docking-time value rather than differential failure incidence. The strongest simple explanation is therefore that, on this source law, retaining the useful first action for longer is beneficial. Nothing in A01 observed parameter sharing, optimization, regularization, or negative transfer.

The frozen A01 rule maps a one-sided result to a convergence reopening for either one independently justified population or a park assessment; it does not authorize B.

# Prospective A/RECON object

## Identity

```text
Object ID:
SCDMP-D6-EVENT-PHASE-DURATION-ACTION-RELEVANCE-A02

Evidence class:
A/RECON

Scientific status:
Prospectively specified; unexecuted

Learner status:
No model, optimizer, training dataset, checkpoint, or learned parameter
```

This is the sole additional population admitted by this decision.

## Exact question

> On the unchanged SCDMP native row, does a public time-to-event coordinate create native duration-action relevance with the sign predicted by renewal alignment: `k=7` favored when the event is seven ticks away, and `k=13` favored when the event is seventy-eight ticks away, under an otherwise identical event-responsive action rule?

The object asks whether **renewal phase relative to an observable event** changes which fixed duration has native return value.

It does not ask whether D6 learns that relation or whether sharing `Q(s,z,k)` is advantageous.

## Independent mechanism trace

```text
public native state plus fixed public time-to-next-event
→ choose fixed renewal clock k ∈ {7,13}
→ execute the same neutral pre-event action
→ the existing HR or RH event sequence occurs at its scheduled tick
→ apply the same zero-tick LEVEL_RELEASE
→ the observed event order becomes available
→ the selected renewal clock determines latency to the next action decision
→ at that renewal, apply the same event-order-matched action map
→ native cable, motion, dock, failure and timeout dynamics evolve
→ full-mission endpoint U records the consequence of response latency
```

The exact response latencies are fixed by construction:

| Public event countdown | `k=7` response latency | `k=13` response latency | Prospective prediction |
| ---------------------: | ---------------------: | ----------------------: | ---------------------- |
|                    `7` |              `0` ticks |               `6` ticks | `k=7` favored          |
|                   `78` |              `6` ticks |               `0` ticks | `k=13` favored         |

This is a prospective timing hypothesis, not an inference that a return reversal must occur. Native consequences may be too small, heterogeneous, or contrary to the latency ordering.

## Host and protected semantics

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

All native transition equations, numerical precision, action semantics, HR/RH transformations, failure predicates, dock predicate, observation normalization, terminal ordering, and `LEVEL_RELEASE` semantics remain unchanged from A01. A01 itself used this host and finite action vocabulary.

The only new population coordinate is a fixed, public event calendar. The existing HR/RH event operators are moved from immediately before the duration choice to a prospectively fixed future tick within each mission. They are not altered.

## Source-population law

Use one fixed root seed:

```text
A02_ROOT_SEED = 9173
```

Address-separated source domains:

```text
SCDMP-D6-A02/SOURCE/K7
SCDMP-D6-A02/SOURCE/K13
```

Generate two treatment-common source trajectories:

| Source domain | Source action | Source renewal clock |
| ------------- | ------------: | -------------------: |
| `SOURCE/K7`   |    `COMMON=0` |                `k=7` |
| `SOURCE/K13`  |    `COMMON=0` |               `k=13` |

Retain the native source state at exact ticks:

```text
91, 182, 273
```

These are legal renewal boundaries for both clocks because `91=lcm(7,13)`. No first-after-target search is used.

The two source domains and three ticks yield six base states. Clone every base state into the two fixed public countdown conditions:

```text
time_to_event ∈ {7,78}
```

This yields twelve scenario states.

For each scenario state:

1. record the native public observation and the public countdown;
2. clone into balanced `HR` and `RH` event-order worlds;
3. begin both clock policies from identical native state bytes;
4. apply the selected HR or RH event sequence after exactly the declared countdown;
5. apply `LEVEL_RELEASE` immediately after the event sequence;
6. make the observed event order available to the fixed continuation rule;
7. permit no latent assignment, future disturbance, endpoint, oracle return, or counterfactual outcome in the available information.

The event application ordering at its scheduled tick is:

```text
complete the transition reaching the event tick
→ apply HR or RH event sequence
→ apply zero-tick LEVEL_RELEASE
→ perform any renewal decision due at that same tick
```

If this population or ordering cannot be represented without changing the protected native transition semantics, the source-population branch below applies. No replacement calendar, source state, target tick, or event offset may be selected.

## Finite treatment/comparator panel

Only two deterministic clock policies are compared.

### `EVENT_CLOCK_7`

```text
renewal period = 7
before the event: choose COMMON=0 at every renewal
at the first renewal at or after the event:
    HR observed → choose action 10
    RH observed → choose action 12
afterwards: retain the corresponding matched action at every renewal
```

### `EVENT_CLOCK_13`

Identical information and action rule, with:

```text
renewal period = 13
```

The two policies therefore differ only in renewal timing. Both use:

* the same native state;
* the same public countdown;
* the same disturbance tape;
* the same HR/RH event;
* the same pre-event action;
* the same observed-order-to-action map;
* the same terminal endpoint.

There is no D2-style interruption. Decisions occur only on the selected fixed clock.

The endpoint remains:

$$
U=
\mathbf 1\{\mathrm{safe\ dock}\}
\left(1-\frac{\mathrm{dock\ tick}}{364}\right),
$$

with native failure or timeout equal to zero.

## Tapes and pairing

Use evaluation domain:

```text
SCDMP-D6-A02/EVALUATION
```

For each of the six base states, materialize exactly tapes:

```text
0,1,…,15
```

The disturbance address is keyed by:

```text
(base_state, tape_index, primitive_tick, disturbance_channel)
```

It excludes countdown, clock policy, and graph, so the same tape is shared across:

* countdowns `7` and `78`;
* `EVENT_CLOCK_7` and `EVENT_CLOCK_13`;
* HR and RH worlds.

All tapes are fixed before any endpoint is read. There is no redraw, extension, replacement, state substitution, or result-conditioned schedule change. The A01 evaluation domain `9029` and its tapes are not reused.

## Exact observables and estimand

For base state \(b\), countdown \(d\in\{7,78\}\), clock policy \(k\in\{7,13\}\), graph \(g\), and tape \(t\), define:

$$
Y_{b,d,k,g,t}=
\begin{cases}
364-\operatorname{dock\_tick}_{b,d,k,g,t},
& \text{safe dock},\\
0,
& \text{failure or timeout}.
\end{cases}
$$

Define the paired duration contrast:

$$
K_{b,d}
=
\sum_{g\in\{HR,RH\}}
\sum_{t=0}^{15}
\left(
Y_{b,d,7,g,t}
-
Y_{b,d,13,g,t}
\right).
$$

Each base/countdown contrast contains 32 paired endpoint cells. A one-tick mean advantage is therefore exactly 32 numerator units.

Aggregate over the six base states:

$$
K_d=\sum_{b=1}^{6}K_{b,d}.
$$

A one-tick aggregate mean advantage is exactly:

$$
6\times32=192
$$

numerator units.

Record:

$$
N_7^+
=
\#\{b:K_{b,7}\ge32\},
\qquad
N_7^-
=
\#\{b:K_{b,7}\le-32\},
$$

$$
N_{78}^-
=
\#\{b:K_{b,78}\le-32\},
\qquad
N_{78}^+
=
\#\{b:K_{b,78}\ge32\}.
$$

Define:

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

Also report:

* every \(Y\), \(K_{b,d}\), and \(K_d\);
* response latency from event to first matched action;
* safe-dock, timeout, and each native failure-family count;
* missions, native transitions, and evaluator calls;
* mean utility by base state, countdown, graph, and clock policy.

Prediction accuracy without a native action or endpoint difference has no authority.

## Work inventory and budget

```text
source trajectories:                2
base states:                         6
public countdown conditions:        2
clock policies:                      2
graphs:                              2
tapes per base state:               16

candidate missions:
6 × 2 × 2 × 2 × 16 =              768

models:                              0
training datasets:                   0
optimizer updates:                   0
AdamW steps:                         0
learner evaluations:                 0
```

Conservative primitive-tick ceiling:

```text
source trajectories: 2 × 364   =       728
candidate missions:  768 × 364 =   279,552
total                                 280,280
```

The valid A01 machine time remains recorded exactly as:

```text
8.115556099975947 seconds
```

That is historical evidence only; it is not an A02 projection.

Before A02 execution, its runner’s single technical smoke must produce an outcome-blind numeric projection using:

$$
P
=
2\left(
t_{\mathrm{native\ mission}}\times770
\right)+60\ \mathrm{s},
$$

where `770` conservatively counts the two source trajectories plus 768 missions.

The A02 scientific invocation requires:

```text
fresh physical/effective memory admission: at least 4 GiB
prospective projected-time cap:            1,800 s
hard observed invocation cap:              1,800 s
```

No numeric A02 projection exists now. Failure of projection, admission, or runtime cap has no scientific polarity.

The engineering surface should remain one research runner and one result summary; no B gate, scheduler, resume system, provenance machinery, or additional infrastructure is part of this object.

## Exposure line

```text
NO_LEARNED_PARAMETERS — exposure not applicable
```

There is no parameter-displacement denominator, learner exposure, optimizer exposure, or model-selection exposure. This does not satisfy or replace the treatment-head exposure requirement of any later learned B.

## Stop rule

1. Freeze this complete object before any A02 smoke or scientific outcome.
2. Run one technical smoke solely to obtain the prospective cost row.
3. Take the fresh `4 GiB` admission immediately before the scientific invocation.
4. Generate the two fixed source trajectories and retain only ticks `91`, `182`, and `273`.
5. If the six base states or public event-calendar representation cannot be established, publish only the declared population branch.
6. Otherwise materialize all fixed tapes before reading an endpoint.
7. Execute all 768 missions.
8. Do not stop for an interim `k=7` advantage, `k=13` advantage, failure pattern, zero gap, or favorable event phase.
9. Analyze once after the complete terminal inventory exists.
10. Add or substitute no countdown, event tick, state, stream, action rule, graph, tape, host constant, or endpoint.
11. No valid result permits a second A02 population or a countdown sweep.

# Ordered finite result rule

Apply the first matching branch.

### 1. `A02_NO_RESULT_RESOURCE_REFUSAL`

Condition:

* the smoke-derived cost row is absent;
* projected time exceeds `1,800 s`;
* fresh memory admission is absent or fails;
* or the scientific invocation never begins.

Mapping:

> No scientific observation. The object remains unobserved. No duration or D6/D8 polarity.

### 2. `A02_INVALID_EVIDENCE`

Condition:

* missing, duplicate, nonterminal, or nonfinite mission;
* incorrect tape pairing;
* event timing differs from `7` or `78`;
* response-latency arithmetic differs from the declared renewal order;
* hidden event information enters before the event;
* declared source, action, or event law is not executed;
* a coordinate is replaced after an outcome;
* required native transition or evaluator counts are zero;
* hard wall cap is crossed before completion;
* or publication is incomplete.

Mapping:

> No scientific observation. Repair only; no reinterpretation or partial-result use.

### 3. `A02_EVENT_PHASE_POPULATION_NOT_ESTABLISHED`

Condition:

* either source trajectory fails to yield all three exact common renewals;
* a base state terminates before its scheduled event;
* the event cannot be applied with the declared ordering under unchanged native semantics;
* or the public countdown and post-event visible order cannot be represented as declared.

Mapping:

> This exact event-phase population was not established. No replacement population, learner, or B object is authorized.

### 4. `A02_EXPECTED_TWO_SIDED_EVENT_ALIGNMENT`

Condition:

```text
SHORT_ALIGNMENT = true
LONG_ALIGNMENT  = true
```

Mapping:

> The finite panel supports the predicted event-phase action opportunity: `k=7` is materially favored when it aligns with the event, and `k=13` is materially favored at the opposed renewal phase. Reopen convergence to decide whether a newly frozen D6-versus-D8 B on a mixed event-phase population is scientifically warranted. This branch does not authorize that B.

### 5. `A02_REVERSED_EVENT_ALIGNMENT`

Condition:

```text
(K_7 <= -192 and N_7- >= 4)
or
(K_78 >= 192 and N_78+ >= 4)
```

Mapping:

> At least one countdown produces a material, state-consistent sign opposite to the renewal-latency prediction. The proposed event-phase mechanism is contradicted on this panel. Reopen only to record a park decision; do not search additional countdowns.

### 6. `A02_SHORT_ALIGNMENT_ONLY`

Condition:

```text
SHORT_ALIGNMENT = true
LONG_ALIGNMENT  = false
```

and branch 5 did not match.

Mapping:

> Event alignment supplies a finite `k=7` opportunity but not the predicted opposed `k=13` control. Reopen convergence; no B is authorized. The missing control prevents treating this as a bidirectional D6 substrate.

### 7. `A02_LONG_ALIGNMENT_ONLY`

Condition:

```text
SHORT_ALIGNMENT = false
LONG_ALIGNMENT  = true
```

and branch 5 did not match.

Mapping:

> The population again supplies only a longer-duration advantage. Park the current D6 action-choice family at the next convergence intake unless evidence outside this source-search lineage supplies a qualitatively new mechanism.

### 8. `A02_ZERO_DURATION_POLICY_SPAN`

Condition:

```text
K_b,d = 0
for every base state and both countdowns
```

Mapping:

> Renewal phase changes no native endpoint in this exact panel. Park the current action-choice family; no learner comparison is decision-relevant here.

### 9. `A02_NONMATERIAL_OR_HETEROGENEOUS_EVENT_ALIGNMENT`

Condition:

Every other valid complete result.

Mapping:

> Event-phase effects are too small, inconsistent, or heterogeneous for the declared action-linked D6 question. Reopen convergence to record parking or, only if the pattern itself supplies a new non-search mechanism, assess that mechanism explicitly. This decision authorizes no further population census.

The branches are finite and exhaustive by first-match ordering.

# Why this population is prospective rather than outcome-driven

The population is grounded independently in three pre-outcome facts:

1. D6’s mechanism concerns values conditioned on duration and state, while the direction’s temporal lineage concerns event/duration ordering.
2. The fixed menu is `K={7,13}`.
3. Renewal arithmetic yields opposed maximal six-tick response delays at countdowns `7` and `78` within the 91-tick joint cycle.

No A01 return, `D_j`, state ranking, failure row, or observed sign was used to select:

* the countdowns;
* the common renewal ticks;
* the action rule;
* the number of states;
* the tapes;
* the material unit;
* or the result branches.

A01 motivates reopening because its branch requires a decision, but it does not determine the A02 coordinates. There is no scan across countdowns or target ticks.

# Strongest support

The strongest support is the existence of a sharply specified event-to-renewal mechanism that predicts both duration signs before outcomes. The timing contrast is exact, symmetric at six ticks, action-linked, and measurable through native return. It tests the missing source of short-duration value rather than merely asking another stationary state panel to reverse sign.

The current evidence standard permits such a separately named A object and permits transparent sequential adaptation; it forbids presenting the A result as a learner result or automatic B gate.

# Strongest contradiction

A01 found uniform `k=13` preference across:

* both source clocks;
* all three target regions;
* all six states;
* all 36 state/action rows;
* and all 1,152 safe-docking missions.

The six duration contrasts occupied a narrow range, `-179` through `-197`, rather than showing weak or borderline heterogeneity. That is strong evidence that the unchanged post-event action law rewards longer retention.

A02 therefore must not be described as a likely positive D6 result. It introduces an unobserved event-phase population, and the fixed matched response may still fail to produce a material endpoint change.

# Residual uncertainty

The evidence does not establish:

* that the scheduled event calendar can be represented under unchanged native semantics;
* that event order is usable at the first post-event renewal exactly as specified;
* that six ticks of response latency change dock time or failure incidence;
* that the opposed countdown classes generate both duration signs;
* that a learner can infer or exploit the public countdown;
* or that cross-`k` parameter sharing helps rather than regularizes, harms, or does nothing.

Even after a favorable A02 result, ordinary architecture/optimization effects and negative transfer remain live explanations for any later D6/D8 learner result.

# Next discriminator and later boundary

The next discriminator is only:

```text
SCDMP-D6-EVENT-PHASE-DURATION-ACTION-RELEVANCE-A02
```

After its valid intake, reopen:

```text
em:semigroup_consistent_duration_model_policy:convergence
```

with this exact question:

> Did A02 establish the prospectively predicted two-sided event-phase duration opportunity strongly enough that a complete, separately frozen D6-versus-D8 B/EXPLORE learner comparison on fresh mixed-phase states and fresh tapes would change a direction decision? If not, should the current D6 action-choice family be parked?

**No A02 branch authorizes B.** A learned object requires another complete convergence decision and must contain no A result as a launch condition.

No second source-population A, event-countdown sweep, or sign search is authorized by this decision.

# Finite claim ceiling

A favorable A02 branch could establish only:

> On the exact `.92/.25` native host, the six declared base states, public event countdowns `{7,78}`, fixed event-responsive clock policies, balanced HR/RH events, sixteen paired tapes, and stated endpoint, renewal phase produced the declared finite native duration-action pattern.

It could not establish:

* D6 or D8 competence;
* cross-`k` Q-sharing value;
* sample efficiency;
* regularization or negative-transfer causation;
* endogenous duration selection;
* D2 interruption value;
* unseen-duration transfer;
* semigroup or duration invariance;
* general MARL superiority;
* safety, deployment, or flight readiness.

An adverse branch implicates only this exact event-phase population and fixed policy panel.

Portfolio lifecycle, priority, capacity, ownership, fusion, registration, and investment remain outside this direction-tier decision, as required by the node contract. 

## Evidence paths actually read

All seven allowlisted paths were retrieved read-only from `CartmanFatass/My-paper-code` at exact ref `b42b5b23877a07dbac7464921d439c27e42b09b7`. No unlisted repository path, moving branch, web mirror, local clone, or pasted substitute was used.

1. `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_D6_DURATION_ACTION_RELEVANCE_A01_RESULT_EVIDENCE_20260904.md` — complete valid A01 result, counts, values, branch, exposure, and machine time.
2. `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_D6_DURATION_ACTION_RELEVANCE_A01_RESULT_INTAKE_20260904.md` — independent recomputation, bounded interpretation, alternatives, and convergence options.
3. `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_D6_DURATION_ACTION_RELEVANCE_A01_SCIENCE_CARD_20260904.md` — frozen source law, action panel, estimands, branch rule, exposure, and later-decision boundary.
4. `docs/research/candidates/semigroup_consistent_duration_model_policy/external/2026-09-04-scdmp-d6-section11-reopen-convergence-02/2026-09-04-scdmp-d6-section11-reopen-convergence-02--semigroup_consistent_duration_model_policy--attempt-01__02_RESPONSE.md` — controlling `SPLIT_A_RECON_THEN_REOPEN_B` decision and prohibition on automatic B authorization.
5. `docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md` — D6 mechanism, temporal lineage, historical boundaries, A01 result, and pending direction decision.
6. `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` — A/B evidence classes, adaptive iteration, smallest-unit interpretation, and section-11 boundary.
7. `docs/project/ENGINEERING_SCOPE_SPEC.md` — research-code, launch-condition, smoke, resource, and anti-overengineering boundaries.

```text
DECISION_FORMED=true
FINAL_DECISION=ADMIT_ONE_PROSPECTIVE_A_RECON
PRO_FINAL=ADMIT_ONE_PROSPECTIVE_A_RECON
SMALLEST_SUPPORTED_DIRECTION_CONCLUSION=The existing stationary/post-event A01 population is one-sided and cannot authorize D6-versus-D8 B. One final event-phase A/RECON population is independently justified by opposed renewal alignment at public countdowns 7 and 78; no source or countdown sweep is authorized.
STRONGEST_SUPPORT=The fixed K={7,13} renewal lattices generate an exact six-tick response-latency advantage for k=7 at countdown 7 and for k=13 at countdown 78, providing a prospective event-to-state-to-action rationale independent of A01 outcomes.
STRONGEST_CONTRADICTION=A01 completed all 1,152 missions with W=2498, R7=0 and R13=1; every state materially favored k=13 by 179–197 numerator units and every mission safe-docked, strongly supporting a simple longer-hold docking-time explanation on the existing source law.
RESIDUAL_UNCERTAINTY=The event-phase population may be unrepresentable, nonmaterial, heterogeneous, or contrary to the renewal-latency prediction; it supplies no learner, sharing, optimization or D6/D8 polarity.
CORRECTED_OBJECT=SCDMP-D6-EVENT-PHASE-DURATION-ACTION-RELEVANCE-A02; same TAU_LEAK=.92/Z_LIMIT=.25 host; root seed 9173; two source streams; base renewals 91/182/273; public countdowns 7/78; fixed EVENT_CLOCK_7 versus EVENT_CLOCK_13 policies; balanced HR/RH events; 16 paired tapes; 768 missions; exact integer native-return contrasts.
EXPOSURE_LINE=NO_LEARNED_PARAMETERS — exposure not applicable.
A01_VALID_RESULT_MACHINE_TIME=8.115556099975947 seconds.
NEXT_DISCRIMINATOR=SCDMP-D6-EVENT-PHASE-DURATION-ACTION-RELEVANCE-A02, followed by another complete direction-tier convergence decision.
B_AUTHORIZATION=NONE. No A02 branch authorizes D6-versus-D8 B, and this decision authorizes no additional A population, countdown sweep or automatic derivative.
```
