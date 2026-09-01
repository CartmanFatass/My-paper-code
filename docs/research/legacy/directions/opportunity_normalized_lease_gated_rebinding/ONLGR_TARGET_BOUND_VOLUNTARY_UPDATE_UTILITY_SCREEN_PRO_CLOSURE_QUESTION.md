# ONLGR target-bound voluntary-update utility-screen mathematical closure

Continue only within this exact existing ONLGR ChatGPT External-Pro conversation. The completed HEADLAND-90 r03 result and your prior `CONVERGED` interpretation remain immutable. Portfolio has authorized only a new definition-stage object; no r03 rerun, rate repair, coordinate, construction, activity, or timing claim is in scope.

Adjudicate the exact complete prospective revision `ONLGR-TBVUUS-SCIENCE-20260821-02` reproduced below. Return exactly one leading disposition:

- `CLOSED` with `SCIENCE_BEARING_DEFECT_COUNT=0`, the strongest surviving alternative, exact maximum claim ceiling, and the single most valuable next discriminator permitted by the result map; or
- `REVISION_REQUIRED` with every remaining mathematical or causal defect, its smallest prospective correction, and the resulting claim boundary.

Focus only on whether the one-shot ROAD-PATCH versus NEVER/SHAM design is meaning-complete, causally answerable, support-qualified before any timing question, statistically total, and correctly bounded. Do not review code, runtime, files, hashes, receipts, implementation feasibility, or portfolio priority. Do not authorize construction, coordinates, a lease, empirical activity, a rate/timing successor, a second surface, or deployment.

## Exact frozen revision 02 composite

# ONLGR target-bound voluntary-update utility-screen science card

Owner: `direction:opportunity_normalized_lease_gated_rebinding` Explorer Manager  
Object: `ONLGR-TARGET-BOUND-VOLUNTARY-UPDATE-UTILITY-SCREEN-DEFINITION`  
Revision: `ONLGR-TBVUUS-SCIENCE-20260821-02`  
Host package: `HEADLAND-90-ROAD-TRACK-PATCH-UTILITY-v1`  
Classification: prospective, definition-only, result-blind  
Question-relevant activity: not authorized and not started  

## 1. Bounded question and separation from completed r03

The completed `ONLGR-HEADLAND90-R03-CAL-HOLD-FULL-PANEL` selected the same
never-voluntarily-update map for every logical controller. It therefore did not
identify route-package timing or FLEX. That result is immutable and supplies no
coordinate, threshold, selector, effect estimate, or action-support evidence to
this object.

This new object asks one prerequisite question:

> At one prospectively fixed legal physical instant, does a road-constrained
> patch of the target state carried in the tracker/relay packet improve direct
> held-out physical-time valid target service over `NEVER-UPDATE`, net of the
> action's one-second zero-service blackout, while instantiating and recording
> the same energy debit and lockout state as the completed host's action?

The new mechanism is `ROAD-TRACK-ESTIMATE-PATCH` (`ROAD-PATCH`). It is not the
r03 `JOINT-UPDATE`: it never changes the tracker waypoint, relay waypoint,
planner, flight controller, route label, rate, or event process. It changes
only the packetized target estimate at the first legal scored tick by fitting
fresh target observations to the public road registry.

There is one fixed action instant and no action-time, frequency, rate, route,
tenure, remaining-time, or class-indexed treatment axis. SHORT/LONG outputs are
diagnostic only. No result from this card can reinterpret or rescue r03.

## 2. Exact inherited host law

Except where this card replaces the voluntary-action surface, inherit the exact
definitions in `ONLGR-TBH-HOST-CARD-20260815-03` for:

- `HEADLAND-90-TRACK-RELAY-2UAV-v1` geometry, route templates, resets, clocks,
  target perturbation, sensing, BOOT, radio, packet deadline, blackout, energy,
  battery, flight, safety, hard failures, and direct valid-service indicator;
- the 0.25 s tick, four-second pre-roll, one-second blackout, four-second
  lockout, 200 J per-UAV action charge, 8 s SHORT tenure, and 32 s LONG tenure;
- physical-time `MEAN_VALUE` and lower-CVaR-0.10 `TAIL_VALUE` endpoints;
- complete paired blocks, action-independent tapes, controller-free coordinate
  keys, hard-nonharm facts, paired safety-override accounting, and atomic
  all-cell release; and
- the paired 128-replicate Student-t inference convention with
  `t_(0.975,127)=1.97882`.

The following r03 objects are not inherited: the production namespace and
coordinates, stochastic action uniforms, `Q`, lambda/event-rate mapping,
GLOBAL/TWO/FLEX selectors, reciprocal controls, rate-response gates, selected
controller identities, observed results, and every timing interpretation.

## 3. Common public road registry

All arms receive one static road registry before the encounter. It contains
exactly the eight directed templates already used to construct the host:

```text
J = {SHORT,LONG} x {d=-1,d=+1} x {ell=-8,ell=+8}.
```

For `j in J`, `x_base^j(t)`, `T^j(t)`, and `N^j(t)` are the exact base-route,
travel-direction tangent, and registered left normal from the frozen host,
including the four-second backward-tangent pre-roll. The registry is public
mission geometry, not the hidden realized target state. It contains no route
label supplied by the environment, future disturbance, service value, link
trial, reward, remaining tenure, controller identity, or outcome.

The registry ordering for exact ties is:

```text
SHORT before LONG;
d=-1 before d=+1;
ell=-8 before ell=+8.
```

Every arm has the same registry. Giving it to `NEVER-UPDATE` prevents the road
prior itself from being treatment access; only assimilation of fresh samples
at the frozen action instant differs.

## 4. Frozen action instant and information boundary

The sole voluntary opportunity is the first legal scored tick, `t=0`, after
the common BOOT blackout and lockout have ended. The current tick's sensor fact
is exposed before the action, as in the inherited tick order. After this tick,
every arm deterministically uses `KEEP` through the scheduled endpoint. No arm
reads an action uniform.

Let `(t_1,z_1),(t_2,z_2)` be the two most recent visible timestamped target
samples after BOOT, in increasing time order, with `t_2<=0`. Samples before
BOOT are unavailable because BOOT cleared the buffer. Define

```text
ROAD_FIT_AVAILABLE = exactly two such samples exist and t_1<t_2.
```

When available, for every `j in J` compute

```text
R_j = ||z_1-x_base^j(t_1)||_2^2 + ||z_2-x_base^j(t_2)||_2^2.
```

Choose the minimum `R_j`, then the frozen registry order. No tolerance creates
a tie. Let the selected template be `j*`. Define

```text
eta_raw   = (z_2-x_base^j*(t_2)) dot N^j*(t_2)
eta_patch = clip(eta_raw,-15 m,+15 m)
x_patch   = x_base^j*(0) + eta_patch*N^j*(0)
v_patch   = v_g*T^j*(0)
```

where `v_g=4*pi m/s`. This is the exact road-track target-state patch. It uses
only current/past samples, timestamps, and public geometry. It does not consult
the true template, hidden perturbation, realized class label, future tape,
service, link outcome, reward, or controller response.

If `ROAD_FIT_AVAILABLE=false`, ROAD-PATCH uses the exact identity fallback: it
preserves the incumbent `(x_hat,v_hat)`. The scheduled action shell still
occurs and remains in the intention-to-treat panel. No cell is removed or
replaced because the payload could not change state.

Define an effective payload application by the prospective materiality rule

```text
EFFECTIVE_ROAD_PATCH = ROAD_FIT_AVAILABLE
  AND (||x_patch-x_hat_pre||_2>=1 m
       OR ||v_patch-v_hat_pre||_2>=1 m/s).
```

This predicate is an answerability/support fact, never a row-selection rule.

## 5. Four fixed arms

Every arm begins from the same BOOT state, sees the same samples, consumes the
same disturbance tapes, and uses the same persistent tracker and relay
waypoints.

### 5.1 `NEVER-UPDATE`

At `t=0`, execute voluntary `KEEP`. Preserve estimator, buffer, and waypoints;
pay no action charge; start no blackout or new lockout. Use KEEP thereafter.
The arm still computes the counterfactual ROAD-FIT and effective-patch audit
from its pre-action state without changing dynamics.

### 5.2 `OVERHEAD-SHAM`

At `t=0`, execute one voluntary action shell. Charge 200 J to each UAV, start
the common one-second blackout and four-second lockout, and clear the two-sample
buffer. Preserve `(x_hat,v_hat)`, tracker waypoint, and relay waypoint exactly.
Use KEEP thereafter.

### 5.3 `RAW-ESTIMATE-PATCH`

At `t=0`, execute the same shell, costs, blackout, lockout, and buffer clear as
OVERHEAD-SHAM. Apply the inherited r03 two-sample estimate-only update:

```text
x_hat = z_2
v_hat = clip_norm((z_2-z_1)/(t_2-t_1),20 m/s)
```

when `ROAD_FIT_AVAILABLE=true`. Otherwise apply the same identity fallback as
ROAD-PATCH. Never invoke the planner and never change either waypoint. Use
KEEP thereafter. This is a nominal interpretation control, not a
claim-bearing ingredient contrast.

### 5.4 `ROAD-TRACK-ESTIMATE-PATCH`

At `t=0`, execute the same shell, costs, blackout, lockout, and buffer clear.
If ROAD-FIT is available, install `(x_patch,v_patch)` as the packetized target
state; otherwise apply the identity fallback. Never invoke the planner and
never change either waypoint. Use KEEP thereafter.

Absent battery exhaustion or a hard failure, all four arms therefore have the
same UAV waypoint commands, nominal flight targets, and physical wind/link
geometry. ROAD-PATCH minus NEVER is the direct valid-service effect net of the
one-second blackout. The registered energy debit and lockout state are
instantiated and logged, but energy has no terminal utility and lockout creates
no foregone action because every arm keeps after `t=0`. ROAD-PATCH minus SHAM
isolates the target-state payload from the blackout/action shell. ROAD-PATCH
minus RAW is nominal descriptive evidence only.

## 6. Fresh paired coordinates and finite package

The new production namespace is prospectively frozen as

```text
ONLGR-TBVUUS-HEADLAND90-20260821-v1.
```

It has no coordinate identity in r03. Coordinates retain the inherited exact
tuple encoding and counter-based stream construction, except no `action`
uniform is generated or consumed. The split is only

```text
HOLD: 128 independent paired replicates b=0,...,127.
```

There is no calibration, model selection, payload selection, rate grid, seed
adaptation, threshold search, or early stopping. Each replicate contains the
same 20 paired SHORT/LONG blocks and both orders/templates as the inherited
host. All four arms use the complete shared tapes within a replicate.

The exact scientific workload is

```text
4 arms * 128 replicates = 512 controller-replicates
3,840 ticks per controller-replicate
total canonical physical ticks = 1,966,080.
```

No physical-alias deduplication is claim-bearing because estimator and service
states differ. Complete execution and analysis of all 512 assigned cells is
mandatory.

## 7. Support, comparator competence, and non-harm

`TBVUUS_PACKAGE_VALID` requires all of the following and inherits no obsolete
r03 selector or calibration predicate:

- exact revision, host-package, and fresh namespace identity;
- exactly four arms by 128 assigned replicates, every replicate containing all
  20 paired blocks, both route classes, balanced orders, and the frozen
  templates;
- exact controller-free paired disturbance coordinates and no generated or
  consumed action word;
- exact arm transitions at `t=0`, all later KEEP actions, complete road-fit,
  availability, selected-template, effective-payload, estimator, buffer,
  blackout, energy, lockout, waypoint, service, safety, and endpoint ledgers;
- ROAD and RAW identity fallback exactly when ROAD-FIT is unavailable;
- RAW conformance in every cell even though its contrast is non-gating;
- no absent, duplicated, substituted, imputed, deleted, best-attempt, or
  outcome-triggered replacement cell; and
- one indivisible complete package and one atomic result release after all
  assigned cells and audits exist.

`SHAM_VALID` requires exact equality of common pre-action state and tapes with
NEVER; bitwise-unchanged estimator and waypoints; only the registered action
ledger, buffer clear, 200 J per-UAV debit, blackout, and lockout differences;
paired tickwise `q_SHAM<=q_NEVER`; and, absent battery exhaustion, equality
after blackout. Any other state or service path invalidates the package.

`ACTION_SHELL_SUPPORT_OK` requires ROAD-PATCH, RAW-PATCH, and SHAM to execute
exactly one voluntary action in every one of the 40 encounters per replicate,
for exactly 5,120 actions per arm. Any missing or extra action is package
nonconformance. NEVER must execute zero voluntary actions.

`EFFECTIVE_ROAD_PATCH_SUPPORT_OK` requires:

```text
at least 512 EFFECTIVE_ROAD_PATCH encounters in HOLD;
at least 96 of 128 replicates contain at least one EFFECTIVE_ROAD_PATCH.
```

Counts by SHORT/LONG are mandatory diagnostics but cannot gate, select, or
support a timing/heterogeneity interpretation. Any future timing object must
prospectively establish nonzero effective action support separately inside
every timing stratum on new coordinates; pooled support here cannot transfer.

`NEVER_COMPETENT` requires:

```text
TBVUUS_PACKAGE_VALID
HOLD_HARD_SAFE(NEVER)
MEAN_VALUE(NEVER)>=0.25
TAIL_VALUE(NEVER)>=0.10
1-MEAN_VALUE(NEVER)>=0.05
```

`ROAD_NONHARM` is a new HOLD-only predicate. It requires zero ROAD-PATCH
terrain penetrations, geofence exits, separation breaches,
`NO_SAFE_CONTROL`, `NO_PLANNER_SOLUTION`, battery exhaustions, and numerical
faults in every assigned cell, plus

```text
UCB95[override(ROAD)-override(NEVER)]<=0.01.
```

`HOLD_HARD_SAFE(NEVER)` is the same zero-failure family applied only to the 128
NEVER cells. RAW is package-mandatory but its effect sign is non-gating.

ROAD-FIT availability, effective-patch status, selected template, route class,
template, support, competence, and qualification never define rows, weights,
subgroup estimands, or conditional confidence intervals. Every claim-bearing
interval is an unconditional full-panel intention-to-treat interval over all
128 assigned replicates.

## 8. Claim-bearing estimands and inference

For held-out replicate `b`, bind the endpoint notation exactly as

```text
VALUE_b,mean(C) = M_b(C)
VALUE_b,tail(C) = T_b(C),
```

where each arm's 20-block lower-tail functional is formed before any paired
difference. For `e in {mean,tail}`, define

```text
d_AN,b,e = VALUE_b,e(ROAD-PATCH)-VALUE_b,e(NEVER)
d_AH,b,e = VALUE_b,e(ROAD-PATCH)-VALUE_b,e(OVERHEAD-SHAM)
d_AR,b,e = VALUE_b,e(ROAD-PATCH)-VALUE_b,e(RAW-PATCH).
```

For every contrast/endpoint, use all 128 assigned replicate differences. Let
`mu`, `sd`, and `[LCB95,UCB95]` be their mean, Bessel-corrected sample standard
deviation, and inherited two-sided Student-t interval. The primary net gates
are

```text
mean(d_AN,mean)>=0.02 and LCB95(d_AN,mean)>0
mean(d_AN,tail)>=0.05 and LCB95(d_AN,tail)>0.
```

The payload-isolation gates are

```text
mean(d_AH,mean)>=0.02 and LCB95(d_AH,mean)>0
mean(d_AH,tail)>=0.05 and LCB95(d_AH,tail)>0.
```

ROAD-PATCH qualifies only when all four gates pass together with package,
support, comparator-competence, and non-harm gates. `d_AR` is always reported
with intervals but has no positive threshold and cannot enlarge the claim.

For each of the four claim-bearing gates, record exactly one status:

```text
PASS                  = point threshold passes and LCB95>0
PRECISE_REGISTERED_NONPASS
                      = PASS is false and sd<=0.080 for mean
                        or sd<=0.200 for tail
POWER_NONIDENTIFYING  = PASS is false and the corresponding SD limit is exceeded.
```

A passing gate is not invalidated by a larger SD. The 0.080/0.200 limits are
per-gate planning statements for effects of 0.02/0.05; they do not promise 80%
joint power for the four-way conjunction. Any failed gate above its limit is
power nonidentification, not a negative inference about smaller positive
effects. No sample-size, threshold, or row change is allowed.

## 9. Exhaustive ordered result map

Apply the first matching branch:

1. If `TBVUUS_PACKAGE_VALID` or `SHAM_VALID` is false, or the common host,
   pairing, or endpoint audit is invalid, return the exact common package
   nonidentification reason.
2. If NEVER is not competent, return `NEVER_UPDATE_COMPARATOR_NONIDENTIFIED`.
3. If action-shell or effective-payload support fails, return
   `ROAD_PATCH_ACTION_SUPPORT_NONIDENTIFIED`. This is not evidence against
   voluntary updating.
4. If `ROAD_NONHARM` is false, return
   `ROAD_PATCH_EXACT_PACKAGE_NONHARM_FAILED` with the concrete physical fact; no
   positive claim or timing successor follows.
5. If both net gates and both payload-isolation gates pass, return
   `ROAD_PATCH_DIRECT_UTILITY_QUALIFIES`.
6. If any failed gate is `POWER_NONIDENTIFYING`, return
   `ROAD_PATCH_POWER_NONIDENTIFYING` and report the complete four-gate status
   vector, including any separately precise nonpasses.
7. If both net gates pass but either ROAD-minus-SHAM gate is a precise
   registered nonpass, return
   `NET_VALUE_WITHOUT_PAYLOAD_ISOLATION`. Direct net value is descriptive, but
   the registered payload-isolation claim does not pass and no timing successor
   opens. This is not equivalence or proof of zero payload value.
8. If both ROAD-minus-SHAM gates pass but either net gate is a precise
   registered nonpass, return
   `PAYLOAD_BENEFIT_WITHOUT_MATERIAL_NET_UTILITY`. The payload offsets action
   blackout on the registered endpoints but does not establish the material
   direct-value prerequisite.
9. For every other all-precise failed-gate pattern, return
   `VALID_ROAD_PATCH_DIRECT_UTILITY_NONPASS` with the four-gate vector.

Every branch reports ROAD-minus-RAW point estimates and nominal 95% intervals
descriptively. No threshold, familywise error rule, ingredient classification,
or successor decision is attached to this contrast. It cannot substitute for
ROAD qualification or revive r03.

Only branch 5 makes a separately defined future timing/rate question eligible
for Portfolio consideration, and only for the unchanged qualified ROAD
transform, availability/fallback law, action shell, host, endpoints, and claim
boundary on fresh coordinates. Any payload, estimator, waypoint, or shell
change requires another direct-value screen. Eligibility does not authorize a
timing question, construction, coordinates, or activity. No other branch
supports timing, fixed-rate sufficiency, general no-update, or
action-uselessness claims.

## 10. Strongest alternatives and claim ceiling

The strongest alternative to a positive result is that the public road-model
prior, synchronized encounter clock, single `t=0` probe, and this simulator's
15 m tracking-validity boundary make fresh-sample assimilation useful without
establishing voluntary-update utility at other times, frequencies, route
phases, or tasks. The registry exactly contains the true base-route generator;
the comparator's BOOT estimate deliberately ignores several seconds of visible
pre-roll samples. A benefit may therefore reflect a privileged road prior or
generic fresh-sample assimilation rather than road regularization itself.

Physical-time pooling weights LONG four times SHORT and can conceal
class/template harm. Computation latency, packet-size cost, road-map error, and
terminal energy value are absent from the analytic host. Unchanged waypoints
exclude a claim about replanning, multi-UAV motion coordination, or relay-portal
control. ROAD-minus-RAW is nominal descriptive evidence and cannot eliminate
these alternatives.

The maximum positive claim is:

> On fresh paired coordinates of the exact analytic
> `HEADLAND-90-ROAD-TRACK-PATCH-UTILITY-v1` package, one shared
> intention-to-treat controller executed the registered action shell in every
> encounter, installed the frozen road-track target-state patch whenever the
> two-sample fit was available, otherwise used the identity fallback, and met
> the registered effective-payload support floor. It improved both mean and
> lower-tail physical-time valid target service over BOOT-only
> `NEVER-UPDATE`, net of the one-second blackout, and also improved both
> endpoints over the blackout-matched identity action, while retaining the
> registered energy debit, lockout state, UAV waypoints, physics, radio, safety
> law, and paired disturbances.

No outcome can establish optimal action timing, repeated-update value,
route-package heterogeneity, arbitrary or adaptive `k`, variable `N`, joint
replanning or relay-portal value, scheduled-tenure causality, real-aircraft
transfer, safety certification, deployment, terminal-energy utility, or general
algorithm superiority.

A valid adequately powered nonpass applies only to this exact one-shot road
patch. It cannot establish that voluntary updating, target-bound adaptation, or
timing-dependent control is generally useless.

## 11. Preactivity boundary and full prospective cost

This definition stage authorizes only card authorship, same-existing-Pro
mathematical/causal closure, EM intake, and CM static feasibility,
observability, comparator, and full-cost assessment. It authorizes no source,
build, test, probe, coordinate, random word, trajectory, evaluation, result,
lease, or production activity.

If a later Portfolio decision authorizes construction, scientific activity
begins at the first materialization of a word in the new production namespace
or the first controller tick on a new production coordinate, whichever occurs
first. No science-bearing field may change after that boundary.

The prior accepted C++ host throughput of 2,232--2,891 complete ticks/s implies
a purely arithmetic raw projection of about 11.3--14.7 CPU minutes for
1,966,080 ticks and about 34--44 CPU minutes at the inherited three-times
full-lifecycle reserve. These are inherited measurements, not a new benchmark
or CM acceptance.

CM must independently return the complete incremental engineering work,
compiler/native/source/schema implications, memory/storage limits, executable
panel cost, and the strongest semantics-preserving implementation alternative.
A prospective estimate above 10 focused engineer-days, 10 CPU hours, 16 GiB
RAM, 4 GiB storage, or requiring a changed physics/sensing/endpoint law is a
material object/cost change and returns before any construction or activity.

## 12. Definition completion and return

The exact composite is definition-complete only when:

1. the existing ONLGR ChatGPT External-Pro conversation returns `CLOSED` or an
   accepted fully re-closed revision;
2. the same-direction EM intakes that ruling without an unreviewed
   science-bearing change; and
3. the named CM returns static feasibility, observability, comparator
   preservation, and full prospective cost.

Completion returns to Root and the dedicated Portfolio owner for a separate
empirical invest/no-invest decision. It never authorizes a HEADLAND r03 rerun,
rate repair, coordinates, construction, lease, timing screen, or empirical
activity.
