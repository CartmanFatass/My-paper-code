# ONLGR target-bound heterogeneity screen definition

Owner: `direction:opportunity_normalized_lease_gated_rebinding` Explorer Manager  
Object: `ONLGR-TARGET-BOUND-HETEROGENEITY-SCREEN-DEFINITION`  
Revision: `ONLGR-TBH-SCREEN-DEF-20260815-03`  
Classification: prospective definition-only two-UAV timing-rate heterogeneity screen  
Question-relevant activity: not authorized and not started  

## Definition-stage conclusion

This object defines a new target-bound screen for a two-UAV tracking-and-relay
task. It does not restart ONLGR-B2, reuse its host or coordinates, or infer
heterogeneity from its result. The new screen asks whether a route-planner
timing fact that is observable before an event decision identifies two
physically different event-rate responses that materially outperform the best
single pooled rate.

The three future controller families are:

```text
GLOBAL-BEST:        one calibration-best constant event rate for both strata
TWO-STRATUM:        one constant rate for SHORT and one for LONG
FLEX-CONTAIN:       a timing-rate function that contains every TWO-STRATUM
                    controller as an exact subfamily
```

The sole heterogeneity-screen contrast is `TWO-STRATUM - GLOBAL-BEST` on a
fresh, held-out, paired target-task panel. `FLEX-CONTAIN` is a containing
comparator and interpretation guard; it does not replace that contrast.

This revision freezes the scientific meaning and later decision logic only.
It deliberately selects no simulator, repository, stochastic coordinate,
seed, route instance, sample count, implementation, optimizer budget, compute
lease, or production action. A later Root-authorized executable science card
must freeze those facts and receive its own same-conversation Pro closure
before any task trajectory, calibration response, or result is generated or
inspected.

## Physical task

The task contains exactly two controlled UAVs and one fixed ground station:

- tracker UAV `T` follows a moving target, maintains a target-state estimate,
  and produces timestamped target packets;
- relay UAV `R` positions itself to maintain the `T-R` air link and the
  `R-B` backhaul to the ground station `B`; and
- a fixed, common low-level flight and safety controller executes waypoint
  plans and emergency separation behavior in every arm.

At physical time `t`, a valid end-to-end target service indicator is

```text
q_t = 1[
  tracker error <= epsilon_track
  AND the target packet reaches B by deadline d_packet
  AND both air-link validity conditions hold
].
```

`epsilon_track`, `d_packet`, link thresholds, flight envelope, battery budget,
and separation constraints are target-task requirements, not tunable outcomes.
The later executable card must bind their exact physical units before choosing
any stochastic coordinates.

The event controller chooses only between:

- `KEEP`: continue the current tracker estimate/control plan and relay
  waypoint/backhaul plan; and
- `JOINT-UPDATE`: recompute both plans from the current common state through
  one fixed deterministic planner shared by all arms.

`JOINT-UPDATE` has the same nonzero radio/compute energy charge, fixed service
blackout, and minimum legal lockout `tau_lock` in every arm. The event-rate
controller cannot alter the payload, planner, low-level controller, safety
override, or physical cost. A safety override is common, externally imposed,
and carries no event-policy score. Its occurrences and consequences must be
reported separately and cannot count as voluntary event-rate support.

## Prospective ex-ante strata

The route generator prospectively alternates two physically named
line-of-sight/contact-corridor classes:

```text
SHORT = transient handoff corridor with scheduled contact tenure 2*tau_lock
LONG  = sustained clear corridor with scheduled contact tenure 8*tau_lock
```

Each class and its scheduled start/end time are fixed by the exogenous target
route, terrain/occlusion map, and relay contact plan before the controller acts.
At corridor entry, and before every event decision inside it, all arms receive
the current class and scheduled remaining tenure. The current label cannot be
changed by an action, reward, tracking success, realized link success, learned
state, or later outcome. Realized service is never used to relabel a corridor.

Every future calibration and held-out analysis block must contain both classes
and both class orders under a prospectively balanced route template. Pooled
mission endpoints weight every physical second, so the longer class contributes
its true longer duration; stratum-specific endpoints are also reported. The
strata may not be re-cut, merged, thresholded, or selected after any response
curve or task outcome is observed.

This is a target-task package contrast. Even a positive result would not prove
that scheduled tenure alone is causal: `SHORT` also denotes the registered
transient handoff geometry, while `LONG` denotes the registered sustained
corridor geometry.

## Why one pooled rate may physically fail

At entry to a `SHORT` corridor the target bearing and relay line-of-sight
geometry change rapidly. A stale joint plan can miss the narrow handoff before
the corridor ends, so prompt updates can recover target packets and backhaul
service. In a `LONG` corridor the geometry changes slowly and a valid plan has
long useful tenure. Unnecessary updates consume radio/compute energy and create
the common service blackout without equivalent tracking benefit.

The prospective directional hypothesis is therefore

```text
lambda_SHORT > lambda_LONG.
```

This sign is part of the screen; it is not inferred from later fitted rates.
The physical mechanism predicts a reciprocal response: the SHORT-selected rate
should improve SHORT service relative to using the LONG-selected rate, and the
LONG-selected rate should improve LONG service relative to using the
SHORT-selected rate. A pooled rate can otherwise appear suboptimal merely from
selection noise or an asymmetric mission mixture.

## Common event law and admissible rates

After the lockout expires, let `e` be elapsed legally eligible physical time
since the last voluntary event opportunity. Every arm converts its current
rate to the same event probability:

```text
p_event(e, lambda) = 1 - exp(-lambda*e).
```

If the lockout has not expired, `KEEP` is deterministic. If an event occurs,
the sole voluntary mark is `JOINT-UPDATE`. Thus rate access is the only
controller-family difference; the screen does not compare event links, marks,
leases, planners, actions, or safety laws.

Define the common dimensionless one-lockout event-probability set

```text
Q = {0, 1/8, 2/8, 3/8, 4/8, 5/8, 6/8, 7/8}
lambda(q) = -log(1-q) / tau_lock.
```

Both constant-rate families select only from this same set. It includes the
no-voluntary-update endpoint and spans to a high but non-deterministic legal
rate. The fixed set cannot be narrowed, expanded, or shifted after calibration
or held-out output is seen.

## Controller families

### `GLOBAL-BEST`

For every `q in Q`, evaluate the corresponding constant rate on the complete
future calibration panel, pooling both corridor classes with physical-time
weights. Select exactly one `q_G` by this fixed lexicographic calibration rule:

1. highest pooled mean valid-service fraction;
2. then highest pooled lower-tail endpoint;
3. then lowest mean voluntary update count; and
4. then lowest `q`.

Freeze `q_G` before opening the held-out panel. `GLOBAL-BEST` then uses
`lambda(q_G)` in both classes. Every candidate rate receives the same complete
paired calibration tapes. This is the best pooled constant in the declared
finite actuator-feasible family, not an arbitrarily initialized learned
constant and not a value selected from the held-out panel.

### `TWO-STRATUM`

For every pair `(q_S,q_L) in Q x Q`, evaluate the controller that uses
`lambda(q_S)` in `SHORT` and `lambda(q_L)` in `LONG` on the same complete
paired calibration panel. Select exactly one ordered pair by this lexicographic
total order:

1. highest physical-time-pooled calibration mean service;
2. then highest calibration lower-CVaR at 10%;
3. then fewest total voluntary `JOINT-UPDATE` actions;
4. then smallest `lambda(q_S)+lambda(q_L)`;
5. then smallest `q_S`; and
6. then smallest `q_L`.

Freeze the first pair in this total order before any held-out evaluation. No
held-out endpoint, reciprocal-response result, or flexible-comparator result
enters selection.

The controller has one parameterization across the complete mission. It may
read only the exogenous current corridor label for rate selection; it is not
retrained, recalibrated, checkpoint-selected, or replaced between strata.

### `FLEX-CONTAIN`

Let

```text
r = scheduled remaining corridor tenure / scheduled corridor tenure
t_anchor = max(corridor-entry time, last voluntary JOINT-UPDATE time),
           with the entry time used when no voluntary update has occurred
a = min((current time - t_anchor) / (8*tau_lock), 1)
s = current exogenous corridor label.
```

The containing timing-rate family is

```text
q_F(s,r,a) = clip_[0,7/8](alpha_s + beta_s*(r-1/2) + gamma_s*(a-1/2))
lambda_F  = -log(1-q_F) / tau_lock.
```

Setting `beta_s=gamma_s=0` and `alpha_SHORT=q_S`,
`alpha_LONG=q_L` exactly reproduces every `TWO-STRATUM` member, including an
endpoint rate. Setting both intercepts equal also contains every
`GLOBAL-BEST` member.

The executable card must freeze a finite coefficient domain `Theta_F` under
the ordering

```text
(alpha_SHORT, alpha_LONG,
 beta_SHORT, beta_LONG,
 gamma_SHORT, gamma_LONG)
```

such that

```text
(q_S,q_L,0,0,0,0) is in Theta_F
for every (q_S,q_L) in Q x Q.
```

Thus the finite searched class, not merely its unconstrained formula, contains
every registered two-stratum controller. The flexible selector uses only the
complete calibration panel and this lexicographic total order:

1. highest physical-time-pooled calibration mean service;
2. then highest calibration lower-CVaR at 10%;
3. then fewest total voluntary `JOINT-UPDATE` actions;
4. then smallest physical-time-weighted mean `lambda_F` over calibration
   opportunity rows; and
5. then lexicographically smallest coefficient tuple in the ordering above.

The frozen selected `TWO-STRATUM` controller is also supplied as an explicit
fallback candidate. If the finite flexible search returns no conforming
candidate that ranks at least as high as that fallback under the complete
flexible total order, the fallback is selected. The selected flexible
controller is frozen before any held-out evaluation.

`FLEX-CONTAIN` is intentionally a larger timing function. Its result cannot
attribute value to remaining tenure, update age, or the corridor label
individually. A later executable card must freeze all non-subfamily points in
its finite coefficient domain, calibration work, and any complexity control
before activity.

## Physical endpoints

For episode `i` of physical duration `H_i`, define

```text
Y_i = integral(q_t dt) / H_i,
```

the fraction of physical mission time during which a timely valid target state
is delivered through the tracker-relay-ground chain. Update blackout is already
counted because `q_t=0` whenever the update prevents timely delivery. The hard
per-UAV battery budget is enforced in the dynamics; service after battery
exhaustion is zero. Report raw tracker error, packet delay/goodput, link
availability, energy, update count, blackout time, and safety/separation facts
alongside `Y_i` so a composite reward cannot hide the physical cause.

The two claim-bearing endpoints are:

```text
MEAN_VALUE = mean_i(Y_i)
TAIL_VALUE = lower-CVaR_0.10(Y_i), the mean of the worst 10% of episode values.
```

The same endpoints are computed separately within `SHORT` and `LONG` physical
time. For controller `C`, held-out episode `i`, and stratum `s`, define

```text
Y_i,s(C) = valid-service physical time in stratum s
           / total physical time in stratum s.
```

The later executable card must freeze a standard finite-sample fractional
quantile convention and enough complete episodes per independent replicate to
make the 10% tail defined. No reward learned by an arm and no post-hoc scalar
combination may replace these endpoints.

Safety, separation, and the physical battery envelope are hard non-harm gates.
An arm that gains service by exceeding a common hard constraint cannot qualify.

## Reproducibility and leakage rules

A later executable card may activate this definition only if it prospectively
freezes all of the following before any calibration or task outcome exists:

- one target simulator and exact physical units, dynamics, target route,
  terrain/occlusion, observation, planner, flight/safety controller, update
  cost, blackout, lockout, service thresholds, battery and constraint facts;
- a fresh namespace, blinded stochastic coordinates, independent-replicate
  count, complete route templates, and calibration/held-out split;
- counter-keyed target motion, wind, sensing, packet/link, safety, and action
  uniforms paired across every controller evaluated on the same coordinate;
- the complete `Q` and `Q x Q` calibration panels, coefficient domain and
  selector for `FLEX-CONTAIN`, all analysis formulas, uncertainty estimators,
  support rules, and missing-data treatment;
- two fixed disjoint calibration-block halves `C_1` and `C_2`, each containing
  both corridor classes and both corridor orders, with their assignment rule
  frozen alongside the executable coordinates;
- the held-out reciprocal confirmation controllers defined below, paired on
  the same held-out disturbances as the selected controllers;
- one immutable controller per family after calibration, with no held-out
  checkpoint, seed, episode, rate, stratum, or panel selection; and
- complete-panel release: no arm value, response curve, support count, or
  endpoint is exposed for scientific interpretation until every mandatory
  calibration and held-out cell and conformance fact is complete.

Calibration coordinates and held-out coordinates are disjoint. The held-out
panel may not change a selected rate, flexible coefficient, task definition,
minimum effect, or branch. Every independent analysis replicate contains both
strata and both orders. Analysis uses paired replicate-level differences; it
does not treat correlated physical ticks or episodes as independent evidence.

The definition itself authorizes none of those freezes or activities. They are
requirements for a distinct future production card.

## Competence, response, and headroom rules

For any controller pair `(q_S,q_L)`, calibration half `h in {1,2}`, and class
`s in {S,L}`, define the class-conditional calibration service functional

```text
mu_s^(h)(q_S,q_L) =
  total valid-service physical time occurring in class s
  / total physical time occurring in class s,
```

pooled over the paired blocks in `C_h`. Define `mu_s^(cal)` analogously on the
complete calibration panel. After the complete calibration panel selects
`(q_S*,q_L*)`, define

```text
M_S^(h)   = argmax_[q in Q] mu_S^(h)(q,q_L*)
M_L^(h)   = argmax_[q in Q] mu_L^(h)(q_S*,q)
M_S^(cal) = argmax_[q in Q] mu_S^(cal)(q,q_L*)
M_L^(cal) = argmax_[q in Q] mu_L^(cal)(q_S*,q).
```

Ties remain sets. Define grid-step distance

```text
d_Q(q,q') = 8*abs(q-q')
d_Q(q,M)  = min_[q' in M] d_Q(q,q').
```

Conditional-rate identification requires

```text
M_S^(cal) intersection M_L^(cal) is empty
AND d_Q(q_S*,M_S^(h)) <= 1 for h=1,2
AND d_Q(q_L*,M_L^(h)) <= 1 for h=1,2.
```

This is a calibration stability condition, not held-out evidence.

The reciprocal-response confirmation uses only the independent held-out panel
after `(q_S*,q_L*)` is frozen. Evaluate these three controllers on identical
held-out coordinates:

```text
C*       = (q_S*,q_L*)
C_S<-L   = (q_L*,q_L*)
C_L<-S   = (q_S*,q_S*).
```

Using paired independent-replicate estimates, define

```text
D_S = E[Y_S(C*) - Y_S(C_S<-L)]
D_L = E[Y_L(C*) - Y_L(C_L<-S)].
```

The executable card must freeze the independent replicate, estimator, and
interval construction before activity. Require separately

```text
D_S >= 0.02 AND paired two-sided 95% LCB(D_S) > 0
D_L >= 0.02 AND paired two-sided 95% LCB(D_L) > 0.
```

The future screen is identified only when all of these prospective conditions
hold on the complete package:

1. `PACKAGE_VALID`: all frozen calibration, selection, held-out, physical,
   pairing, support, safety, and reporting facts are complete and conforming.
2. `GLOBAL_COMPETENT`: `GLOBAL-BEST` satisfies every hard constraint and the
   executable card's prospectively frozen positive minimum held-out counts for
   both voluntary `KEEP` and voluntary `JOINT-UPDATE` in each stratum. Define
   the calibration ceiling-headroom quantity

   ```text
   H_GLOBAL = 1 - MEAN_VALUE_cal(GLOBAL-BEST),
   ```

   where `1` is the exact upper bound of valid-service fraction, and require
   `H_GLOBAL >= 0.05`. This is only a calibration competence/headroom gate,
   not treatment-effect evidence. A support or headroom failure makes the
   screen nonidentified.
3. `RATE_RESPONSE_IDENTIFIED`: the selected pair is in the complete-panel
   calibration maximizer set over `Q x Q`; holding the other selected rate
   fixed, the conditional SHORT and LONG maximizer sets are disjoint; each
   independent calibration half places the selected value within one `Q` grid
   step of its corresponding conditional maximizer set.
4. The prospective sign holds: `q_S > q_L`.
5. Both independently held-out reciprocal-response gates `D_S` and `D_L`
   defined above hold.

The target has material pooled headroom only if `TWO-STRATUM` versus
`GLOBAL-BEST` also satisfies both physical gates on held-out paired replicates:

```text
Delta_mean = MEAN_VALUE_TWO-STRATUM - MEAN_VALUE_GLOBAL-BEST >= 0.02
paired two-sided 95% lower confidence bound for Delta_mean > 0

Delta_tail = TAIL_VALUE_TWO-STRATUM - TAIL_VALUE_GLOBAL-BEST >= 0.05
paired two-sided 95% lower confidence bound for Delta_tail > 0.
```

These are absolute fractions of mission time: two percentage points in mean
valid target service and five percentage points in worst-decile service. The
tail rule prevents a mean-only gain purchased by worse failure episodes.

Define

```text
TARGET_HETEROGENEITY_QUALIFIES =
  PACKAGE_VALID
  AND GLOBAL_COMPETENT
  AND RATE_RESPONSE_IDENTIFIED
  AND q_S > q_L
  AND both reciprocal-response gates
  AND both pooled mean/tail headroom gates
  AND all hard non-harm gates.
```

If package validity, competence, response identification, or physical headroom
is absent, the screen is nonidentifying for its exact reason. It does not prove
global-rate sufficiency. If all those prerequisites hold but the registered
mean/tail gates do not, the exact target screen does not justify a two-stratum
rate investment and the best pooled global rate remains the target comparator.

## Role of the containing comparator

`FLEX-CONTAIN` is evaluated on the same held-out coordinates after calibration
and must report both physical endpoints and paired contrasts to
`TWO-STRATUM` and `GLOBAL-BEST`.

- If target heterogeneity qualifies and `FLEX-CONTAIN` preserves both endpoints
  within `0.01` absolute service of `TWO-STRATUM`, the result is compatible with
  a future timing-rate algorithm family. It still does not identify an
  individual timing coordinate.
- If target heterogeneity qualifies but `FLEX-CONTAIN` loses more than `0.01`
  on either endpoint, report only that the finite flexible search-and-selection
  procedure did not preserve the two-stratum controller's held-out performance;
  flexible estimation, search, or generalization remains unresolved. The local
  two-rate physical result remains unchanged.
- If `TWO-STRATUM` does not qualify but `FLEX-CONTAIN` beats `GLOBAL-BEST` on
  both registered pooled gates, that is a distinct continuous-timing signal.
  It returns for a new prospective definition and cannot retroactively make the
  two-stratum screen pass.
- If neither nonconstant family clears the gates in a valid, competent package,
  the exact target supplies no current evidence for moving beyond its best
  pooled global rate.

No branch may be chosen from calibration performance alone.

## Strongest alternatives

Even after a future positive screen, the strongest alternatives are:

- the registered corridor label packages transient geometry, scheduled tenure,
  and route phase, so the result need not be caused by tenure alone;
- the advantage may be a fixed architecture/resource-allocation benefit of two
  constants rather than evidence for a general adaptive event-rate mechanism;
- the finite calibration selector, mission mixture, update blackout, energy
  budget, or common deterministic planner may create the response crossover;
  and
- a containing flexible controller may fail from its own optimization or
  finite-budget geometry even though its mathematical class contains the
  two-stratum controller.

A negative or nonidentified screen likewise does not establish that global
rates are generally sufficient or that another target task lacks timing
heterogeneity.

## Claim ceiling

At this definition stage there is no empirical claim. Pro closure can establish
only that this is a coherent prospective target-bound screen and that its later
branches do not exceed their observables.

If a separately authorized future executable package passed every registered
condition, the maximum result claim would be:

> On the exact constructed two-UAV tracking-and-relay task, two prospectively
> labeled route/contact classes observable before action had reciprocally
> different calibration-best legal joint-update rates, and one shared
> two-stratum controller improved both mean and worst-decile held-out valid
> target-service time over the best pooled constant rate under common physics,
> planner, action, energy, safety, event link, and paired disturbances.

No outcome could establish scheduled-tenure causality apart from the corridor
package, ONLGR-B2 rescue, eligible-exposure-link causality, lease or rebinding
causality, literal hazard semantics, arbitrary or continuous `k`, variable
`N`, within-resource-cap success, real-aircraft transfer, other-UAV-task
generalization, or general algorithm superiority.

## Definition-stage completion and handoff

This definition becomes complete for the present stage only after:

1. the exact revision receives `CLOSED` in the existing ONLGR ChatGPT External
   Pro conversation;
2. the same-direction EM intakes that ruling without silently changing the
   revision; and
3. the named same-direction CM returns a document-level feasibility and
   prospective cost/unknowns packet without sourcing, code inspection, build,
   test, probe, coordinate selection, training, evaluation, or compute.

Neither closure nor CM feasibility authorizes a later executable card or any
scientific activity. Root and the dedicated portfolio owner retain all future
investment, target selection, resource, and production decisions.
