# DISH RBHR prospective population-instantiability support analysis — 2026-08-22

```text
document_kind=direction_definition_support_analysis
owner=Portfolio-owned Explorer Manager /root/em_dish_scanner_terminal_intake
research_scope=direction:degraded_incumbent_shadow_handover
stage=DISH-RBHR-POPULATION-INSTANTIABILITY-DEFINITION
terminal_predecessor=DISH-RBHR-SCIENCE-20260821-05
predecessor_result=false
predecessor_identity_reused=false
analysis_activity=definition_only
cross_direction_evidence=false
```

## 1. Question and predecessor boundary

The definition-stage question is whether a prospectively distinct DISH object
can instantiate its complete evaluation population with a bound that does not
depend on a future master, an observed qualifying rate, a result-selected cap,
or r05's terminal identity.

R05 cannot answer that question empirically. Its sole identity rejected the
first requested accepted-tape slot for attempts `0..99999`, then sealed with
zero accepted tapes. Those public result-blind facts establish only that the
r05 rejection sampler did not instantiate its first slot under its sole master
and cap. They do not reveal a tape, assay value, qualifying probability or
controller result. This analysis does not inspect, resume, reset, delete,
replace or reuse that identity, frontier, master, coordinate or incomplete
inventory.

The structural repair is to remove outcome-conditioned tape acceptance from
the successor population. Opportunity and learned behavior remain measured by
the already defined witness and support gates; they no longer decide whether a
physical tape exists.

## 2. Constructive finite evaluation population

Use the following finite indices:

```text
b=0,...,23
rho=0 TARGET_VISUAL_MASK | 1 TERRAIN_RELAY_MASK
s=0 K4 | 1 K8 | 2 K12 | 3 K4_TO_K12 | 4 K12_TO_K4
z=0 SPEED_4 | 1 SPEED_6 | 2 SPEED_8
ell=0,...,15
evaluation_slot j=16*z+ell, j=0,...,47
```

There is exactly one degraded evaluation tape for every `(b,rho,s,z,ell)` and
one deterministic mask-off view of the same tape. The complete degraded base
population is therefore

`24*2*5*3*16 = 11,520` tapes,

before learned action. No candidate-attempt coordinate, eligibility predicate,
advantage assay, rejection, accepted-tape frontier or replacement rule exists.
Terminal, missing handover opportunity, no learned trigger, competence failure
and unfavorable endpoints never remove a tape.

### 2.1 Fixed speed strata and initial geometry

Set

`v_g=(4,6,8)[z] m/s`.

Let

```text
X=(-80,-40,40,80)
Y=(-180,-120,120,180)
delta=(5*b+3*rho+7*s+11*z) mod 16
h=(ell+delta) mod 16
u_x=X[h mod 4]
u_y=Y[floor(h/4)].
```

For every `(b,rho,s,z)`, `ell=0,...,15` maps bijectively to all sixteen
`X x Y` initial offsets. Thus every speed stratum contains the complete initial-
geometry factorial once. The block/regime/schedule/stratum rotation changes
which offset is paired with each identity bit without selecting on a physical
or learned outcome.

Retain the r05 eight-way identity law within each speed stratum: the three bits
of `ell mod 8` select reflection, initial owner and assignment of `q_A/q_B` to
physical UAVs. Each combination occurs exactly twice in every sixteen-slot
speed stratum.

Set route turn magnitude and sign constructively:

```text
abs_theta=(25,35,45)[(ell+b+2*rho+s+z) mod 3] degrees
sign_theta=(-1,+1)[(ell+b+rho+s+z) mod 2].
```

Each sign occurs eight times per `(b,rho,s,z)`. Each magnitude occurs five or
six times in a sixteen-slot stratum; because the 24 blocks cycle the offset
exactly eight times through each residue, every magnitude occurs exactly 128
times for a fixed `(rho,s,z)` across all blocks. `rho` is the regime ordinal;
the incorporated host's reflection sign remains its distinct symbol `r`.

### 2.2 Onsets, switches and renewal phase

Retain the r05 clock law with `j=16*z+ell`:

- for fixed schedules, `tau_d=(42,54,66)[j mod 3]`;
- for switched schedules, with `q=j mod 12`, use
  `tau_d=(42,54,66)[q mod 3]` and
  `tau_k=(36,48,60,72)[floor(q/3)]`; and
- use the cell-wide addressed phase offset and
  `phi=(j+phi_offset) mod k_initial`.

Across the complete 48-tape cell, every fixed onset occurs sixteen times,
every switched `(tau_d,tau_k)` pair occurs four times, and every initial phase
occurs equally often because each allowed `k_initial` divides 48. Within each
sixteen-tape speed stratum, every fixed onset occurs at least five times, every
switched pair occurs at least once, and every phase occurs at least once. No
clock combination relies on rejection sampling.

### 2.3 Master-addressed quantities

A future successor master, if separately authorized, addresses only quantities
whose values do not determine population membership: training route/initial
draws, evaluation and training wind, camera/radio/SOURCE noise, phase rotation,
arm initialization/action/minibatch streams and bootstrap block indices. The
evaluation route speed, turn, initial offset, reflection, owner, physical-ID
assignment, onset and switch are the constructive functions above.

The SHA-derived open uniform lies strictly in `(0,1)`, so every inverse-CDF and
Box-Muller draw is finite. The host uses bounded initial geometry, bounded
route choices, clipped wind/velocity/action and `log10(max(d,1)/100)`. Extreme
but finite noise, early terminal, missing packets or absent recovery opportunity
remain valid tape outcomes. They cannot make a coordinate absent.

## 3. Support and complete-population failure bound

For every required `(b,rho,s,z,ell)` the displayed functions produce exactly one
total physical coordinate before a model acts. Therefore, conditional only on
a conforming implementation materializing the frozen coordinate map,

```text
P(number_of_degraded_evaluation_tapes = 11520)=1
P(population_incomplete_due_to_scientific_admission)=0.
```

This is a structural bound, not an estimated acceptance probability. It holds
for every possible future 256-bit successor master because no master-dependent
predicate admits or rejects a tape. Duplicate/missing coordinates, an illegal
address, nonfinite implementation output or disagreement with the constructive
map is `INVALID_PROTOCOL_OR_MEASUREMENT`; it is not a request for a second
master or a substitute tape.

The same proof covers all regimes, schedules, speed strata and slots:

| Required family | Constructive support |
|---|---|
| two regimes | `r` selects one total deterministic intervention package |
| five evaluation schedules | `s` selects one total fixed/switched clock recurrence |
| three strata | `z` fixes one of the three registered route speeds |
| sixteen slots/stratum | `ell` bijects to all sixteen initial offsets and balances all eight identity combinations twice |
| onset/switch combinations | deterministic `j` law covers every named value/pair |
| initial phases | cell rotation preserves exact full-cell balance and nonempty within-stratum support |
| paired views | mask-off is a deterministic intervention toggle on the same exogenous tape |
| five learned arms | all arms receive the identical base tape; no arm can select membership |

## 4. Scientific answerability after construction

Structural instantiability does not manufacture handover opportunity. Retain
the r05 arm-independent recovery witness, learned trigger-rate/behavior-changing
support bounds, NEVER headroom, competence, precision, nonharm, endpoint,
REAL/SHAM and FLEX/simple-rule gates. On the finite speed-stratified population:

- no qualifying recovery witness is the registered
  `NO_REGISTERED_RECOVERY_WITNESS` answer;
- no adequate learned trigger/action support is
  `EFFECTIVE_HANDOVER_SUPPORT_NOT_ESTABLISHED` unless a simple rule qualifies;
- low competence, headroom or precision returns its existing bounded
  nonidentification branch; and
- protocol invalidity is reserved for a malformed or incomplete object, not
  for lack of favorable physical opportunities.

This separation is the information gain: every scientific branch receives a
complete physical population, while opportunity and value remain allowed to
fail.

## 5. Bias, alternatives and claim boundary

The population is a prospectively fixed finite factorial, not a draw from an
unbounded operational distribution. Its principal advantages are guaranteed
coverage, arm independence and removal of post-generator conditioning on a
scripted counterfactual. Its principal alternative is that the finite route-
speed/geometry grid may contain too little recoverable headroom for an adaptive
handover policy even if a different UAV task would. That outcome is bounded
nonidentification for this target, not structural impossibility.

Other surviving alternatives remain r05's: generic two-UAV redundancy,
favorable standby geometry, a simple timing rule, finite-budget FLEX
underoptimization, predictor/critic/recurrent training effects, protocol
traffic and host-specific route/phase interactions. Deterministic factorial
assignment narrows master-specific imbalance but does not establish unique
mediation or a natural-world frequency claim.

Any positive result can support only finite-budget evidence on this exact
two-UAV host that one shared policy improves at least one registered route-speed
stratum common to every retained claim schedule without material harm across
the other speed strata, under the frozen fixed/held-out/switched external-`k`
schedules and all retained controls. It
cannot establish arbitrary/continuous `k`, arbitrary route speeds, variable
`N`, natural-world prevalence, unique mechanism, other terrain/sensor/radio
laws, safety, deployment or flight.

## 6. Prospective cost boundary

The new population has exactly one materialization per evaluation slot and no
candidate scan or 50-tick admission assay. It retains r05's 503,316,480
training transitions, 115,200 learned evaluation episodes, recovery witness,
forks and max-t analysis. The closest accepted same-direction measurement is
the r05 production remainder excluding rejected candidates:

```text
measured_remainder_cpu_core_hours=278.447917844373
measured_remainder_wall_hours=44.7681636558252
measured_simultaneous_rss_gib=2.57534790039062
measured_formula_scratch_gib=0.663042068481445
measured_formula_durable_gib=0.330453045666218
measured_formula_total_io_gib=34.0669612884521
```

Those are same-direction engineering facts, not acceptance of a future
successor. Because the successor deletes rather than expands scanner work, its
prospective ordinary empirical planning envelope is `<=320 CPU core-hours` and
`<=65 wall-hours` at up to eight workers, with hard preactivity return ceilings
unchanged at `560 CPU core-hours`, `110 wall-hours`, `40 GiB` aggregate RSS,
`120 GiB` scratch, `16 GiB` durable and `400 GiB` total I/O. A later CM must
remeasure the exact new bytes and may not infer technical acceptance from this
analysis.

The prospective engineering delta is limited to deterministic evaluation-slot
materialization, the R06 address namespace, speed-stratum reducers and the
changed branch vector. Plan `8/15/30 experienced engineer-days` low/central/
high. More than 30 days, any projection beyond a hard resource ceiling, or a
need to change controller/comparator/endpoint semantics returns to Portfolio
before identity or activity.

## 7. Definition-only fence

This analysis creates no successor revision by itself and authorizes no CM,
source, test, runtime, fixture, master, identity, coordinate, tape, model,
training, evaluation, inference, lease, compute, provider, Git, deployment or
flight action. It uses no cross-direction evidence and no private r05 state.
