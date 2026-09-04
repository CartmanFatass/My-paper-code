# ONLGR target-bound heterogeneity screen: corrected complete Pro closure

Object: `ONLGR-TARGET-BOUND-HETEROGENEITY-SCREEN-DEFINITION`  
Revision: `ONLGR-TBH-SCREEN-DEF-20260815-03`  
Conversation: continue the existing ONLGR ChatGPT External Pro conversation  
Question status: frozen before provider use  

You previously returned `REVISION_REQUIRED` with four conceptual defects. This
complete corrected composite fixes all four: a total two-rate selection order;
exact calibration-half, conditional-maximizer, and independent held-out
reciprocal-response definitions; a calibration ceiling-headroom and fixed-panel
support rule; and finite-domain flexible containment with a non-overattributing
held-out-loss interpretation.

Review this whole revision as one indivisible definition-only scientific
object. It is a new prospective target-bound screen, not an ONLGR-B2 restart,
reanalysis, executable science card, or empirical claim. No simulator,
repository, stochastic coordinate, seed, route instance, sample count, search
budget, implementation, training, evaluation, or compute is selected or
authorized here.

Return exactly one leading disposition:

```text
CLOSED
```

or

```text
REVISION_REQUIRED
```

If `CLOSED`, state that all four prior science-bearing defects are corrected,
identify any residual assumptions that properly belong to the later executable
card, and restate the maximum future claim in one bounded paragraph. If
`REVISION_REQUIRED`, enumerate every remaining exact mathematical or causal
defect, the smallest correction, and the claim boundary until corrected. Do
not review code, implementation feasibility, tests, runtime, compute,
repositories, files, hashes, receipts, or technical acceptance.

## Purpose and controller contrast

The object defines a two-UAV target-tracking and relay screen asking whether a
route/contact class observable before action has two materially different legal
joint-update-rate responses that outperform the best pooled constant rate.

The future families are:

```text
GLOBAL-BEST:  one calibration-best constant rate for both classes
TWO-STRATUM:  one constant rate for SHORT and one for LONG
FLEX-CONTAIN: a timing-rate function whose finite searched domain contains
              every TWO-STRATUM controller
```

The sole heterogeneity-screen contrast is `TWO-STRATUM - GLOBAL-BEST` on a
fresh independent held-out paired panel. `FLEX-CONTAIN` is a containing
comparator and interpretation guard only.

## Physical task, actions, and service

There are exactly two controlled UAVs and one fixed ground station. Tracker
UAV `T` follows a moving target, maintains a target-state estimate, and emits
timestamped target packets. Relay UAV `R` positions itself to maintain the
`T-R` air link and the `R-B` backhaul. A fixed common low-level flight and
safety controller executes plans in every family.

At physical time `t`, valid target service is

```text
q_t = 1[
  tracker error <= epsilon_track
  AND the target packet reaches B by deadline d_packet
  AND both air-link validity conditions hold
].
```

The later executable card must bind the exact physical units for tracking
tolerance, deadline, link thresholds, flight envelope, battery budget, and
separation constraints before coordinates. They are task requirements, never
outcome-tuned quantities.

At an event opportunity the rate controller chooses only:

- `KEEP`, continuing the current tracker and relay plans; or
- `JOINT-UPDATE`, recomputing both plans through one fixed deterministic joint
  planner from the current common state.

`JOINT-UPDATE` has the same nonzero radio/compute energy, fixed service
blackout, and minimum legal lockout `tau_lock` in every family. No rate
controller can alter the planner, payload, low-level controller, cost, or
safety law. External safety overrides are common, have no voluntary event
score, and cannot count toward voluntary support.

## Prospective ex-ante corridor packages

Before action, the exogenous route/contact plan fixes every corridor label and
scheduled start/end time:

```text
SHORT = transient handoff corridor, scheduled tenure 2*tau_lock
LONG  = sustained clear corridor, scheduled tenure 8*tau_lock.
```

The current class and scheduled remaining tenure are visible before every
event decision. They are fixed by route, terrain/occlusion, and contact plan
and cannot depend on actions, rewards, tracking/link success, learned state,
or later outcomes. Every future calibration half and held-out replicate
contains both classes and both class orders. A class cannot be recut, merged,
thresholded, or selected after any response is observed.

At SHORT entry, target bearing and relay line-of-sight geometry change rapidly;
prompt updates can prevent a missed narrow handoff. In LONG, geometry changes
slowly; redundant updates consume energy and blackout without comparable
benefit. The prospective directional hypothesis is

```text
lambda_SHORT > lambda_LONG.
```

Because the label packages scheduled tenure with registered corridor geometry,
no result can attribute an effect to scheduled tenure alone.

## Common event law and finite rate family

After lockout, let `e` be elapsed legally eligible physical time since the last
voluntary event opportunity. Every family uses

```text
p_event(e,lambda) = 1-exp(-lambda*e)
Q = {0,1/8,2/8,3/8,4/8,5/8,6/8,7/8}
lambda(q) = -log(1-q)/tau_lock.
```

Before lockout expiry, `KEEP` is deterministic; after an event, the sole mark
is `JOINT-UPDATE`. The screen does not compare event links, marks, planners,
actions, leases, or safety laws. `Q` is common and immutable after any
calibration or held-out output.

## Deterministic calibration selection

`GLOBAL-BEST` evaluates every `q in Q` on the complete paired calibration
panel, pooling both classes by physical time. It selects by this lexicographic
total order:

1. highest pooled mean valid-service fraction;
2. highest pooled lower-CVaR at 10%;
3. fewest total voluntary `JOINT-UPDATE` actions; and
4. smallest `q`.

Freeze the first `q_G` before held-out evaluation. Every rate receives the
same complete paired calibration tapes. `GLOBAL-BEST` is best only within the
declared finite family and then uses `lambda(q_G)` in both classes.

`TWO-STRATUM` exhaustively evaluates every ordered pair
`(q_S,q_L) in Q x Q` on the same complete paired calibration panel. It selects
by this lexicographic total order:

1. highest physical-time-pooled calibration mean service;
2. highest calibration lower-CVaR at 10%;
3. fewest total voluntary `JOINT-UPDATE` actions;
4. smallest `lambda(q_S)+lambda(q_L)`;
5. smallest `q_S`; and
6. smallest `q_L`.

Freeze the first pair `(q_S*,q_L*)` before held-out evaluation. No held-out
endpoint, reciprocal response, or flexible result enters either selection.
The two-rate controller is one immutable controller across the mission and its
rate selector reads only the prospective current class.

## Physical endpoints

For episode `i` of duration `H_i`, define

```text
Y_i(C) = integral(q_t(C) dt) / H_i.
```

This is the fraction of physical mission time with timely valid end-to-end
target service. Update blackout already counts as failure time; the common
hard battery budget is enforced in dynamics and service after exhaustion is
zero. The claim-bearing endpoints are

```text
MEAN_VALUE(C) = mean_i Y_i(C)
TAIL_VALUE(C) = lower-CVaR_0.10 of Y_i(C).
```

For stratum `s`, define

```text
Y_i,s(C) = valid-service physical time in s
           / total physical time in s.
```

Raw tracker error, packet delay/goodput, link availability, energy, event count,
blackout, and safety/separation facts are mandatory. The later executable card
freezes the finite-sample tail convention and independent replicate estimator.
No learned reward or post-hoc scalar may replace the physical endpoints. Hard
battery, flight, separation, and safety constraints are non-harm gates.

## Calibration halves and conditional response

Before any task outcome, the executable card partitions paired calibration
blocks into fixed disjoint halves `C_1` and `C_2`; each contains both classes
and both orders. The assignment rule is frozen with the executable
coordinates.

For controller pair `(q_S,q_L)`, half `h`, and class `s`, define

```text
mu_s^(h)(q_S,q_L) =
  total valid-service physical time in class s
  / total physical time in class s,
```

pooled over paired blocks in `C_h`. Define `mu_s^(cal)` on the complete
calibration panel. After `(q_S*,q_L*)` is selected, define set-valued
conditional maximizers

```text
M_S^(h)   = argmax_[q in Q] mu_S^(h)(q,q_L*)
M_L^(h)   = argmax_[q in Q] mu_L^(h)(q_S*,q)
M_S^(cal) = argmax_[q in Q] mu_S^(cal)(q,q_L*)
M_L^(cal) = argmax_[q in Q] mu_L^(cal)(q_S*,q).
```

Ties remain in the sets. Define

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

This is only a calibration stability condition.

## Independent reciprocal held-out confirmation

After `(q_S*,q_L*)` is frozen, evaluate on identical independent held-out
coordinates:

```text
C*     = (q_S*,q_L*)
C_S<-L = (q_L*,q_L*)
C_L<-S = (q_S*,q_S*).
```

Using paired independent-replicate estimates, define

```text
D_S = E[Y_S(C*) - Y_S(C_S<-L)]
D_L = E[Y_L(C*) - Y_L(C_L<-S)].
```

The later executable card freezes replicate construction, estimators, and
intervals before activity. Reciprocal response requires separately

```text
D_S >= 0.02 AND paired two-sided 95% LCB(D_S) > 0
D_L >= 0.02 AND paired two-sided 95% LCB(D_L) > 0.
```

Thus the higher selected SHORT rate must beat the selected LONG rate within
SHORT, and the lower selected LONG rate must beat the selected SHORT rate
within LONG, on data unused for selection.

## Competence, support, headroom, and pooled qualification

`PACKAGE_VALID` requires every frozen calibration, selection, held-out,
physical, pairing, support, safety, and reporting fact under one revision.

For `GLOBAL-BEST`, define calibration ceiling headroom

```text
H_GLOBAL = 1 - MEAN_VALUE_cal(GLOBAL-BEST),
```

where `1` is the exact upper bound of valid-service fraction. Require
`H_GLOBAL >= 0.05`. This is a calibration competence/headroom gate only, not a
treatment effect. The executable card also freezes positive minimum held-out
counts for both voluntary `KEEP` and `JOINT-UPDATE` in each stratum for
`GLOBAL-BEST`. Failure of either support or ceiling headroom is comparator
noncompetence and makes the screen nonidentified.

Require the prospective sign `q_S*>q_L*`, conditional-rate identification,
both reciprocal-response gates, and all hard non-harm gates. On held-out paired
independent replicates, also require

```text
Delta_mean = MEAN_VALUE(TWO-STRATUM) - MEAN_VALUE(GLOBAL-BEST) >= 0.02
paired two-sided 95% LCB(Delta_mean) > 0

Delta_tail = TAIL_VALUE(TWO-STRATUM) - TAIL_VALUE(GLOBAL-BEST) >= 0.05
paired two-sided 95% LCB(Delta_tail) > 0.
```

The margins are absolute physical service fractions: two mean percentage
points and five worst-decile percentage points. Define

```text
TARGET_HETEROGENEITY_QUALIFIES =
  PACKAGE_VALID
  AND GLOBAL_COMPETENT
  AND RATE_RESPONSE_IDENTIFIED
  AND q_S* > q_L*
  AND both held-out reciprocal gates
  AND both held-out pooled mean/tail gates
  AND all hard non-harm gates.
```

Missing completeness, global support/headroom, response identification, or
hard constraints is nonidentification, never global-rate sufficiency. If those
facts are valid and answerable but either registered effect gate fails, the
exact target does not justify its two-rate investment and `GLOBAL-BEST`
remains the target comparator.

## Finite-domain containing comparator

For scheduled remaining-tenure fraction `r`, class `s`, and

```text
t_anchor = max(corridor-entry time, last voluntary JOINT-UPDATE time),
           using entry when no voluntary update has occurred
a = min((current time-t_anchor)/(8*tau_lock),1),
```

define

```text
q_F(s,r,a) = clip_[0,7/8](alpha_s+beta_s*(r-1/2)+gamma_s*(a-1/2))
lambda_F  = -log(1-q_F)/tau_lock.
```

Under coefficient order

```text
(alpha_S,alpha_L,beta_S,beta_L,gamma_S,gamma_L),
```

the executable card freezes a finite `Theta_F` satisfying

```text
(q_S,q_L,0,0,0,0) in Theta_F
for every (q_S,q_L) in Q x Q.
```

Therefore the finite searched class contains every two-stratum member, and
equal intercepts also contain every global member. The flexible calibration
selector uses only the complete calibration panel and this total order:

1. highest physical-time-pooled calibration mean service;
2. highest calibration lower-CVaR at 10%;
3. fewest total voluntary `JOINT-UPDATE` actions;
4. smallest physical-time-weighted mean `lambda_F` over calibration
   opportunity rows; and
5. lexicographically smallest coefficient tuple.

The selected `TWO-STRATUM` controller is an explicit fallback candidate. If
the finite flexible search returns no conforming candidate ranking at least as
high as the fallback under that complete order, the fallback is selected. The
selected flexible controller is frozen before held-out evaluation.

`FLEX-CONTAIN` uses the same held-out paired panel. If it is lower than
`TWO-STRATUM` by more than `0.01` on either held-out endpoint, report only that
the finite flexible search-and-selection procedure did not preserve the
two-stratum controller's held-out performance; flexible estimation, search,
or generalization remains unresolved. Do not attribute the loss specifically
to optimization failure. If TWO-STRATUM fails but FLEX-CONTAIN independently
passes both registered global mean/tail gates, that is a separate prospective
continuous-timing hypothesis and cannot make this screen pass.

## Reproducibility and activity fence

Before any future activity, a distinct executable card must freeze one target
simulator and all physical dynamics/units; a fresh namespace and blinded
coordinates; complete route templates, replicate counts, calibration halves,
held-out split, and paired disturbance tapes; complete `Q`, `Q x Q`, reciprocal
confirmation, and finite `Theta_F` panels; all selectors, support counts,
estimators, uncertainty rules, non-harm rules, missing-data treatment, and
complete-panel release; and one immutable selected controller per family.

Calibration and held-out coordinates are disjoint. The held-out panel cannot
change a rate, coefficient, task definition, margin, or branch. Analysis uses
paired independent-replicate differences, never correlated ticks or episodes
as inferential units. No arm value, response curve, support count, or endpoint
may be scientifically exposed until every mandatory cell and conformance fact
is complete.

The present definition selects none of these executable facts, authorizes no
activity, and itself carries no empirical result.

## Strongest alternatives and claim ceiling

Even after a future positive screen, the class packages transient geometry,
scheduled tenure, and route phase; a benefit may reflect a fixed two-constant
architecture/resource allocation rather than a general adaptive-rate
mechanism; the finite selector, mission mixture, blackout, battery constraint,
or common planner may create the crossover; and a containing flexible
procedure may lose through estimation, search, or generalization despite exact
class containment.

At this definition stage, closure can establish only a coherent prospective
screen. After a separately authorized and independently Pro-closed executable
package, the maximum future claim would be:

> On the exact registered constructed two-UAV tracking-relay task, two
> route/contact packages labeled prospectively and observably before action
> exhibited reciprocally different legal joint-update-rate responses on
> independent held-out data, and one shared class-indexed two-rate controller
> improved both mean and lower-decile-tail valid end-to-end service time over
> the calibration-best pooled constant-rate controller under common physics,
> planner, event law, action cost, battery, safety constraints, and paired
> disturbances.

No outcome could identify scheduled tenure separately from the corridor
package, rescue ONLGR-B2, validate the exposure link against another link,
establish lease, `JOINT-UPDATE`, or hazard causality, prove arbitrary or
continuous `k`, support variable `N`, establish within-resource-cap success,
demonstrate real-aircraft transfer, generalize to another UAV task, or imply
general algorithm superiority.
