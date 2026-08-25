# ONLGR-TBH target-host executable-card mathematical re-closure, revision 03

Continue only within the exact existing ONLGR ChatGPT External-Pro conversation.

Your immediately preceding review of revision 02 returned
`REVISION_REQUIRED` with two residual science-bearing defects. The Explorer
Manager accepted both and froze the complete prospective revision below.

First, selected FLEX must now be a coefficient tuple in the exact nonzero-slope
set `V` before it is adaptively answerable. A selected `L` member is only an
alternative contained two-stratum lookup/search diagnostic and cannot support
FLEX/GLOBAL qualification, FLEX/TWO timing compatibility, a
continuous-timing-definition question, powered negative timing evidence, or a
no-current-timing-evidence conclusion.

Second, exact selected-controller non-harm now requires calibration and
held-out zero-hard-failure predicates plus the held-out paired override bound
for selected GLOBAL, TWO, and FLEX. Reciprocal controls are prospectively and
explicitly held-out-only because their sole role is independent held-out swap
confirmation; each still requires complete held-out cells, the identical
zero-hard-failure predicate, and the paired override bound.

These corrections add no controller, coordinate, trajectory, threshold, or
compute. No source, repository, build, probe, random coordinate, trajectory,
calibration, training, evaluation, or compute exists for this object.
Question-relevant activity has not begun.

Adjudicate this exact complete composite for final mathematical and causal
closure. Return exactly one leading disposition:

- `CLOSED` with `SCIENCE_BEARING_DEFECT_COUNT=0`, the exact maximum claim
  ceiling, and any strongest surviving alternative; or
- `REVISION_REQUIRED` with every remaining science-bearing defect, its
  smallest prospective correction, and the resulting claim boundary.

Do not propose implementation, code review, runtime inspection, empirical
execution, a new host, continuous optimization, another provider identity, or
a broader UAV/general claim.

## Exact frozen revision 03 composite

# ONLGR-TBH target-host executable-card definition

Owner: `direction:opportunity_normalized_lease_gated_rebinding` Explorer Manager  
Object: `ONLGR-TBH-TARGET-HOST-EXECUTABLE-CARD-DEFINITION`  
Revision: `ONLGR-TBH-HOST-CARD-20260815-03`  
Host: `HEADLAND-90-TRACK-RELAY-2UAV-v1`  
Classification: prospective, target-bound, definition-only executable card  
Question-relevant activity: not authorized and not started  
Empirical investment: none  

## 1. Bounded question and protected inheritance

This card instantiates the Pro-closed abstract object
`ONLGR-TBH-SCREEN-DEF-20260815-03` on one analytic two-UAV host. It asks one
question: on a tracker/relay mission containing a prospectively named rapid
headland turn and a sustained straight corridor, does one shared controller
with one fixed legal event rate per route package outperform the
calibration-best pooled fixed rate in both mean and lower-tail valid target
service on fresh paired held-out coordinates?

The registered physical direction is

```text
q_SHORT > q_LONG.
```

The only claim-bearing treatment contrast is `TWO-STRATUM - GLOBAL-BEST`.
`FLEX-CONTAIN` is a containing interpretation comparator. It cannot rescue a
failed two-rate result, and a local two-rate result does not depend on FLEX
success.

This is not an ONLGR-B2 restart. It has a new host, namespace, coordinate
definition, selectors, and endpoints. It does not reopen eligible-exposure,
event-link, lease, rebinding, hazard, within-cap, arbitrary-`k`, variable-`N`,
or UAV-deployment claims. All controller families below share the same
physics, planner, legal actions, event transform, update payload, blackout,
energy charge, lockout, low-level controller, safety law, and disturbance
tapes. The rate accessor is the only family-varying interface.

Every numerical host value below is a constructed-task design constant, not a
claim about a real aircraft, radio, sensor, or coastline.

## 2. Natural host and physical reason

`HEADLAND-90-TRACK-RELAY-2UAV-v1` represents a tracker UAV `T` following a
ground vehicle around a radio-occluding headland while a relay UAV `R`
preserves the `T-R-B` chain to a fixed ground station `B`. The host has one
rapid 90-degree road bend around the headland and one long straight road above
it. A joint plan computed before the turn ages quickly as target bearing and
the best relay portal change. On the straight road, the same constant-velocity
target predictor and relay portal remain useful longer, so unnecessary
updates can lose service through blackout and energy charge.

This is a physical package hypothesis rather than a label-coded reward: class
labels are generated from nominal road pieces before action, while tracker
error, line of sight, radio success, flight, energy, and service are computed
from positions and stochastic tapes without consulting the label. The
strongest countermechanism is that the common planner or radio geometry makes
one pooled rate adequate, or that frequent updates hurt the short turn more
because its tenure is only twice the lockout.

## 3. Time, geometry, and mission construction

### 3.1 Units and clocks

All dynamics use SI units and one fixed tick:

```text
Delta_t             = 0.25 s
tau_lock            = 4.00 s = 16 ticks
tau_blackout        = 1.00 s = 4 ticks
SHORT tenure        = 2*tau_lock = 8.00 s = 32 scored ticks
LONG tenure         = 8*tau_lock = 32.00 s = 128 scored ticks
common pre-roll     = tau_lock = 4.00 s = 16 unscored ticks
packet deadline     = 0.50 s
```

Tick intervals are left-closed/right-open. An event taken at tick `n` starts
blackout on `[t_n,t_n+tau_blackout)` and lockout on
`[t_n,t_n+tau_lock)`. The first later legal decision is at `t_n+tau_lock`.
An action at the last scored tick is legal and its current-tick blackout and
energy consequences count; no value beyond the scheduled endpoint is added.

### 3.2 World and terrain

Horizontal coordinates lie in the geofence
`G=[-550,550] x [-350,350] m`. The fixed ground station is

```text
B = (-450, 250, 15) m.
```

The radio-opaque headland is the vertical prism

```text
O = [-80,80] x [-260,80] x [0,140] m.
```

Write `O_xy=[-80,80] x [-260,80]` and freeze

```text
d_O(x)   = inf_[y in O_xy] ||x-y||_2
G_legal  = G intersection {x : d_O(x)>=20 m}.
```

Thus equality at 20 m is legal and terrain penetration means `d_O<20 m`.
Every waypoint projection and every linear flight-tick feasibility check uses
the closed set `G_legal`. Radio occlusion instead uses the original undilated
three-dimensional prism `O`: a three-dimensional segment is line-of-sight
exactly when its open segment does not intersect `O`, and boundary contact
counts as blocked. Terrain and geofence geometry never read the route label or
a controller identity.

Tracker altitude is fixed at 80 m and relay altitude at 100 m. The different
fixed altitudes are common task roles, not learned actions. Horizontal minimum
UAV separation is 30 m.

### 3.3 Exogenous route packages

The nominal target speed is `v_g=4*pi m/s`. Let `u=t/T_s` on a scored route,
with `u in [0,1]`. Before any controller action, a route template fixes class,
direction `d in {-1,+1}`, lateral offset `ell in {-8,+8} m`, entry time, and
end time.

For `SHORT`, let `R=64 m`, `c=(80,80) m`, and

```text
phi(u) = pi/4 + d*(u-1/2)*pi/2
x_nom(u) = c + R*(cos(phi(u)), sin(phi(u)))
           + ell*(1,1)/sqrt(2).
```

This is a rigidly translated 90-degree turn around the northeast headland
corner, traversed in 8 s. For `LONG`, let

```text
x_nom(u) = (d*64*pi*(2*u-1), 200+ell) m.
```

This is a 32 s straight corridor traversed at the same nominal speed. Define
the complete unperturbed base route on encounter time `t in [-tau_lock,T_s]`
by

```text
x_base(t) = x_nom(t/T_s),                         0<=t<=T_s
x_base(t) = x_nom(0) + t*v_g*T(0),       -tau_lock<=t<0,
T(t)      = x_dot_base(t)/||x_dot_base(t)||_2
N(t)      = (-T_y(t),T_x(t)).
```

`T` is always the direction-of-travel tangent. At a scored-route endpoint it
is the left-limit tangent. `N` is the registered left normal; no right-normal,
radial, template-dependent, or implementation-selected alternative is
permitted. The second line is therefore the exact four-second backward-tangent
pre-roll.

Index every physical tick continuously through the encounter, with `n=0` at
`t_0=-tau_lock`, then advance through pre-roll and scored time. The
action-independent lateral perturbation and target position are

```text
zeta_0       = clip(2*Z_target[0], -6, 6) m
zeta_n+1     = clip(0.96*zeta_n
                    + 2*sqrt(1-0.96^2)*Z_target[n+1], -6, 6) m
x_target,n   = x_base(t_n) + zeta_n*N(t_n).
```

The target's along-route phase remains the nominal physical clock. Therefore
perturbations, actions, service, realized links, and tracking outcomes cannot
alter class, scheduled tenure, route endpoint time, or remaining-tenure
fraction. `SHORT` and `LONG` are observable package labels; the card makes no
tenure-only causal claim.

### 3.4 Blocks, orders, and resets

One route block contains one `SHORT` encounter and one `LONG` encounter. The
two encounters are independent prepared sorties: target/UAV/estimator/battery
state is reset from the same block coordinate before each encounter, so no
lockout, blackout, estimator, energy, or waypoint state crosses classes.
Execution order is `SHORT,LONG` when `(replicate+block)` is even and
`LONG,SHORT` otherwise. This balances order without making order part of the
dynamics. Each replicate has 20 blocks and therefore both orders ten times.

The template index is `(replicate+3*block) mod 4`, with the fixed ordering

```text
0: d=+1, ell=+8   1: d=+1, ell=-8
2: d=-1, ell=+8   3: d=-1, ell=-8.
```

The class, template, and scheduled times are committed in the coordinate
manifest before any output exists. They are never inferred or relabeled.

### 3.5 Exact encounter initialization

At pre-roll time `t=-tau_lock`, the target is at its perturbed backward-tangent
route point. `T` starts horizontally above that point at altitude 80 m with
ground velocity `v_g*T(t_0)`. `R` starts at
`(0,180,100) m` with zero ground velocity. Both positions are outside the
interior of the excluded region (`p_xy in G_legal`) and satisfy separation for
every template. At that exact tick
the first visible noisy target sample initializes the estimator as specified
in Section 4. The common `BOOT` planner invocation then occurs at that same
instant; its 200 J charge, one-second blackout, and four-second lockout are
included in the physical and energy ledgers and end no later than scored time
zero. If that current initial target sample is unexpectedly not visible, the
cell is a host-conformance failure, not an arm-specific fallback. Batteries
are initialized immediately before `BOOT`; every other dynamic state and
counter stream starts from its stated initial law. No selected controller may
change this initialization.

## 4. Target sensing and common estimator

At every tick, `T` timestamps and buffers a two-dimensional target-position
observation `(t_n,z_n)` when
its horizontal target distance is at most 250 m and the target-to-`T` segment
is line-of-sight through `O`. Conditional on visibility,

```text
z_n = x_target,n + 3*(Z_x,n,Z_y,n) m.
```

No observation is buffered when visibility fails. The buffer holds at most the
two most recent visible timestamped observations since the preceding `BOOT` or
voluntary update. The packetized target state is a constant-velocity estimate
`(x_hat,v_hat)`. At `t_0=-tau_lock`, `BOOT` uses only the current first sample
`z_0`, never a future sample, and sets

```text
x_hat,0 = z_0
v_hat,0 = clip_norm(v_g*T(t_0),20 m/s).
```

It invokes the common planner, charges the common update energy, clears the
observation buffer after use, and completes its blackout and lockout before
scored time. It is logged as `BOOT`, never as voluntary support.

At a voluntary `JOINT-UPDATE`, let `(t_1,z_1),(t_2,z_2)` be the two most recent
visible buffered observations in increasing timestamp order. With two, the
estimator sets

```text
x_hat = z_2
v_hat = clip_norm((z_2-z_1)/(t_2-t_1),20 m/s).
```

With exactly one buffered observation `(t_1,z_1)`, it sets `x_hat=z_1` and
retains the previous clipped velocity. With none, it retains the estimator
state already propagated to the current tick. The voluntary update then clears
the buffer. It never implicitly propagates `z_2`, divides by `Delta_t` in
place of the actual timestamp gap, or reads a future sample. Between updates,

```text
x_hat,n+1 = x_hat,n + Delta_t*v_hat,n,
v_hat,n+1 = v_hat,n.
```

The estimator, buffer rule, and fallback are identical in every arm. The
tracking-error fact at a service tick is

```text
E_track,n = ||x_hat,n - x_target,n||_2 <= epsilon_track,
epsilon_track = 15 m.
```

## 5. Common deterministic joint planner

The planner is invoked only by `BOOT` or `JOINT-UPDATE`. With horizon
`h=2 s`, its tracker waypoint is

```text
w_T = x_hat + h*v_hat at altitude 80 m,
```

whose horizontal component is projected onto the closed set `G_legal` by
minimum Euclidean distance, with lexicographically smallest `(x,y)` resolving
an exact projection tie. Its altitude is then fixed at 80 m. No other clipping
or terrain projection is permitted.

The relay candidate registry is the 15 horizontal points

```text
C_R = {B_xy + h*(w_T,xy-B_xy) + o :
       h in {1/2,3/4,1},
       o in {(0,0),(120,0),(-120,0),(0,120),(0,-120)}}.
```

Candidates whose horizontal points are outside `G_legal` are discarded.
For remaining candidate `c` at relay altitude 100 m,
define the no-shadow planning margin

```text
M0(A,D) = 25 - 20*log10(max(||A-D||_2,1)/100)
          - 30*1[segment(A,D) is blocked]  dB
score(c) = min(M0(w_T,c), M0(c,B)) - 0.01*||c-p_R||_2.
```

The planner chooses maximum score, then smallest travel distance, then
lexicographically smallest `(x,y)`. Its tracker and relay waypoints persist
until the next common planner invocation. The planner sees physical state and
terrain but never the controller family, rate, route label, future tape, or
reward. An empty candidate set records `NO_PLANNER_SOLUTION`, sets service to
zero thereafter, and fails host conformance and hard non-harm; no dynamic
candidate, arm-specific fallback, or outcome-driven repair is permitted.

## 6. Flight, wind, safety, and energy

At each tick the common low-level controller forms nominal ground velocity

```text
v_nom,j = clip_norm((w_j-p_j)/2 s, v_max,j),
v_max,T = 18 m/s, v_max,R = 22 m/s.
```

Wind for each UAV is a bounded action-independent AR(1) tape:

```text
w_j,0   = clip_norm(2*Z_wind,j,0, 4) m/s
w_j,n+1 = clip_norm(0.90*w_j,n + 2*sqrt(1-0.90^2)*Z_wind,j,n,
                    4) m/s.
```

For each UAV `j`, the deterministic controller enumerates air velocities with
the exact indices

```text
i_j=0:       (0,0)
i_j=1+h:     0.5*v_max,j*(cos(2*pi*h/16),sin(2*pi*h/16)), h=0,...,15
i_j=17+h:    1.0*v_max,j*(cos(2*pi*h/16),sin(2*pi*h/16)), h=0,...,15.
```

Thus zero is first, followed by every half-speed heading `h=0,...,15`, then
every full-speed heading `h=0,...,15`. The resulting ground velocity is
exactly `v_ground,j=v_air,j+w_j`. From the Cartesian product of the two
registries, the controller chooses the feasible pair by the total order:

1. minimum `sum_j ||v_ground,j-v_nom,j||_2^2`;
2. then minimum `sum_j ||v_air,j||_2`; and
3. then lexicographically smallest joint index `(i_T,i_R)`.

Feasibility requires both exact linear tick trajectories to remain in the
closed set `G_legal`, including the `d_O=20 m` boundary, and their exact linear
relative-motion minimum distance over the tick to be at least 30 m. If no pair
is feasible, the cell records `NO_SAFE_CONTROL`, service becomes zero
thereafter, and hard non-harm fails; no hidden recovery or arm-specific
controller is allowed. Section 14 separately defines the unconstrained
reference pair and the exact safety-override indicator.

Positions advance by the selected ground velocity for one tick. Energy obeys

```text
E_T,n+1 = E_T,n - Delta_t*(300 + 1.0*||v_air,T||^2)
                   - 200*1[action is BOOT or JOINT-UPDATE] joules
E_R,n+1 = E_R,n - Delta_t*(350 + 1.0*||v_air,R||^2)
                   - 200*1[action is BOOT or JOINT-UPDATE] joules.
```

Each encounter starts before `BOOT` with `E_T=40000 J` and `E_R=45000 J`.
Negative energy is clamped to zero, grounds that UAV, sets service to zero for
the remainder, and records hard battery exhaustion. Energy, flight, and safety
laws do not read the class label or controller identity.

## 7. Radio, packets, blackout, and valid service

For link `A-D`, three-dimensional distance `d`, line-of-sight indicator `L`,
and shadow state `xi`, define

```text
margin(A,D) = 25 - 20*log10(max(d,1)/100) - 30*(1-L) + xi  dB
p_link      = logistic(margin/3).
```

Independent `T-R` and `R-B` shadow tapes follow

```text
xi_0   = 3*Z_link,0 dB
xi_n+1 = 0.95*xi_n + 3*sqrt(1-0.95^2)*Z_link,n dB.
```

A link succeeds when its paired counter-keyed uniform is below `p_link`.
Every tick, `T` emits the current timestamped `(x_hat,v_hat)` packet. The two
hops reserve deterministic 0.125 s each; a packet is valid by the 0.50 s
deadline iff both link trials succeed on that tick. There is no queue, retry,
priority, or controller-specific payload. During update blackout both links
are unavailable, although physical motion and sensor buffering continue.

The tick order is fixed. At `t_n`, the current physical state and buffered
sensor facts are exposed; the legal event action is drawn; any update changes
the estimator/waypoints, charges energy, and starts blackout; the packet/link
trials and `q_n` are then evaluated from that current state; finally the common
low-level control advances UAVs, target perturbation, wind, shadow, energy, and
the next sensor buffer to `t_n+Delta_t`. This order is identical at pre-roll,
class-entry, blackout-end, lockout-end, and terminal boundaries.

For scored tick `n`,

```text
q_n = 1[
  E_track,n
  AND T-R succeeds
  AND R-B succeeds
  AND no update blackout
  AND neither UAV is exhausted
  AND no hard safety failure
].
```

Thus blackout is already valued as zero service. Raw tracking error,
visibility, both margins and trials, packet validity, UAV positions, energy,
updates, blackout, lockout, overrides, and safety facts are separately logged.

## 8. Event opportunities, actions, and rates

Pre-roll permits only `BOOT` and deterministic `KEEP`; no voluntary event is
scored. At scored ticks, a voluntary opportunity exists iff no lockout is
active. Locked ticks deterministically use `KEEP` and are not opportunity
rows.

Let `e` be eligible physical time since the previous legal opportunity. Locked
time is excluded; the first opportunity after lockout has `e=Delta_t`, as does
each consecutive eligible tick. At a legal opportunity the controller returns
`q`, and

```text
lambda(q) = -log1p(-q)/tau_lock
p_event   = -expm1(-lambda(q)*e).
```

The action is `JOINT-UPDATE` iff the paired action uniform is strictly below
`p_event`; otherwise it is voluntary `KEEP`. Every legal opportunity consumes
exactly its counter-addressed uniform even when `q=0`. Every family uses

```text
Q = {0,1/8,2/8,3/8,4/8,5/8,6/8,7/8}.
```

All arithmetic is IEEE-754 binary64 with round-to-nearest/ties-to-even. The
reference functions are correctly rounded `log1p` and `expm1`; a future
implementation must freeze one conformance-tested math library before
activity. No tolerance changes a comparison. Rate-output `q` is computed as an
exact rational before conversion to binary64. Tick counts and service
fractions remain exact integers/rationals through selector comparison. The
mean-lambda tie term is accumulated in lexicographic coordinate order with
binary64 Neumaier compensation; only bit-identical values tie. Coefficient
tuples then use exact rational lexicographic order.

For FLEX state,

```text
r = remaining scheduled tenure / scheduled tenure
t_anchor = max(corridor entry, last voluntary JOINT-UPDATE),
           using entry when no voluntary update exists
a = min((current time-t_anchor)/(8*tau_lock),1).
```

## 9. Controller registry and frozen finite selectors

### 9.1 `GLOBAL-BEST` and `TWO-STRATUM`

The 8 diagonal constant maps and all 64 `Q x Q` lookup maps use the complete
calibration panel. `GLOBAL-BEST` selects the first `q_G` under this exact total
order:

1. greatest calibration `MEAN_VALUE`;
2. then greatest calibration `TAIL_VALUE`;
3. then fewest voluntary `JOINT-UPDATE` actions; and
4. then smallest `q`.

`TWO-STRATUM` selects the first ordered pair `(q_S*,q_L*)` under:

1. greatest physical-time-pooled calibration `MEAN_VALUE`;
2. then greatest calibration `TAIL_VALUE`;
3. then fewest total voluntary `JOINT-UPDATE` actions;
4. then smallest `lambda(q_S)+lambda(q_L)`;
5. then smallest `q_S`; and
6. then smallest `q_L`.

Metrics are computed from every calibration cell before either identity is
sealed. Both selected controllers are frozen before held-out evaluation; no
held-out, reciprocal, or FLEX fact enters selection.

### 9.2 Exact finite `Theta_F`

For

```text
q_F(s,r,a) = clip_[0,7/8](alpha_s
                           + beta_s*(r-1/2)
                           + gamma_s*(a-1/2)),
```

define the exact 192-member ordered set `Theta_F=L union V`.

`L` contains the 64 tuples

```text
(q_S,q_L,0,0,0,0), (q_S,q_L) in Q x Q,
```

in lexicographic tuple order. Let `A={1/8,3/8,5/8,7/8}` and `d=1/8`.
For every `(alpha_S,alpha_L) in A x A`, `V` contains these eight slope
patterns, in the written order:

```text
( d, d, 0, 0)   (-d,-d, 0, 0)
( d,-d, 0, 0)   (-d, d, 0, 0)
( 0, 0, d, d)   ( 0, 0,-d,-d)
( 0, 0, d,-d)   ( 0, 0,-d, d),
```

where each row supplies `(beta_S,beta_L,gamma_S,gamma_L)`. `V` is ordered by
`alpha_S`, `alpha_L`, then the written pattern index. There are no other
coefficients, combinations, continuous fits, optimizer starts, or adaptive
searches.

This domain exactly contains every lookup controller and adds sparse shared
and opposite-signed remaining-tenure or post-update-age variation without a
six-axis Cartesian search. The selected TWO-STRATUM lookup is also tagged as
the explicit fallback. FLEX uses the closed five-part total order: pooled
mean, lower-CVaR, fewer updates, lower opportunity-row mean `lambda_F`, then
the coefficient tuple. The finite domain itself is the complexity control.

The fixed pre-outcome audit grid is

```text
A_RATE = {S,L} x {0,1/4,1/2,3/4,1} x {0,1/8,1/4,1/2,1}.
```

Selected FLEX is algebraically distinct from selected TWO-STRATUM only if
their `q` values differ by at least `1/32` on one audit row. It is realized-
support distinct under this exact construction. Let `R_F` be the multiset of
all held-out legal-opportunity records `(s,r,a,Delta_t)` realized by selected
FLEX, and let `R_T` be the corresponding multiset realized by selected TWO.
Form the disjoint tagged multiset

```text
U = ({F} x R_F) disjoint-union ({T} x R_T).
```

Duplicates and multiplicities are preserved. On every record in `U`,
cross-evaluate both pure rate maps at that record's same `(s,r,a)` and define

```text
F_diff = count_[u in U](abs(q_F(u)-q_TWO(u))>=1/32) / |U|
A_diff = sum_[u in U] Delta_t(u)*abs(q_F(u)-q_TWO(u))
         / sum_[u in U] Delta_t(u).
```

Every opportunity row here has `Delta_t=0.25 s`, so the registered weighting
also equals equal row weighting. Realized-support distinctness requires
`F_diff>=0.10` and `A_diff>=1/64`. An empty `U` is non-distinct. No row
deletion, deduplication, trajectory matching, or state-distribution
reweighting is permitted. Failure of algebraic or realized distinctness makes
FLEX a containment/search control only, even if its endpoint is high.

### 9.3 Identity-preserving deduplication

One immutable rate-map registry evaluates each of the 192 calibration
controllers once. GLOBAL and TWO selectors are views over their exact registry
members; they do not create another trajectory. Different coefficient tuples
are never deduplicated merely because clipping happens to match on observed
rows. On held-out data, the five logical tags are

```text
GLOBAL-BEST, TWO-STRATUM/C*, FLEX-CONTAIN, C_S<-L, C_L<-S.
```

Exact globally identical selected rate maps may share one trajectory, but all
logical tags and comparisons remain separately reported. Resources are booked
for the worst case of five unique maps.

## 10. Fresh coordinates and stochastic identity

The production namespace is the exact UTF-8 string

```text
ONLGR-TBH-HEADLAND90-20260815-v1
```

and has never appeared in an earlier ONLGR object. Coordinates are tuples

```text
(namespace, split, replicate, block, class, template, tick, stream, lane).
```

The future runner encodes every tuple field as decimal/UTF-8 preceded by its
decimal byte length and a colon, joins fields with `|`, and computes SHA-256 of
that exact byte string. A uniform is
`(uint32_big_endian(digest[0:4])+0.5)/2^32`. Distinct `lane` values address
additional words; there is no mutable PRNG cursor. Normals use fixed Box-Muller
pairs with the lower-address uniform as radius input. Streams are
exactly `target_lateral`, `wind_T`, `wind_R`, `sensor_x`, `sensor_y`,
`shadow_TR`, `shadow_RB`, `link_TR`, `link_RB`, and `action`. Controller
identity is absent from every disturbance key. Unused values are not consumed
or shifted.

Splits and counts are frozen as

```text
CAL:  48 independent replicates b=0,...,47
      C1={0,...,23}, C2={24,...,47}
HOLD: 128 independent replicates b=0,...,127
```

The split string is part of the key, so calibration and held-out tapes are
disjoint even when integer replicate labels match. Every controller sees the
same complete tapes within a split. Each replicate contains 20 blocks, both
classes, both orders, and all four templates five times up to the deterministic
balance induced above. No coordinate, count, half, stream, or controller cell
may be added, dropped, regenerated, or selected from an outcome.

This paragraph freezes coordinate identities only. No PRNG word, route,
trajectory, endpoint, or response curve is generated during the present
definition stage.

## 11. Endpoints and finite-sample convention

For controller `C`, replicate `b`, block `m`, define class service fractions

```text
Y_bm,S(C) = sum of q_n over the 32 SHORT scored ticks / 32
Y_bm,L(C) = sum of q_n over the 128 LONG scored ticks / 128
Y_bm(C)   = (32*Y_bm,S + 128*Y_bm,L)/160.
```

Thus pooled value weights every scored physical second, not each class
equally. For the 20 block values in a replicate, sort
`Y_b(1)<=...<=Y_b(20)` and define

```text
M_b(C) = mean_m Y_bm(C)
T_b(C) = (Y_b(1)+Y_b(2))/2.
```

This is the exact lower-CVaR 0.10 convention because `0.10*20=2`. More
generally, if a conforming audit ever encounters `n` complete values, lower
CVaR uses the first `floor(.1n)` plus fractional weight
`.1n-floor(.1n)` on the next value, divided by `.1n`; but mandatory cells have
exactly 20 and no missing value is admissible.

The panel endpoints are

```text
MEAN_VALUE(C) = mean_b M_b(C)
TAIL_VALUE(C) = mean_b T_b(C).
```

Class-specific service uses replicate means of the 20 corresponding
`Y_bm,s`. Tracking, packet, link, energy, update, blackout, and safety ledgers
are mandatory co-endpoints but cannot replace the two claim-bearing values.

## 12. Inference, precision, and prospective power

Held-out replicate `b` is the sole inferential unit. For every named contrast,
form its 128 paired replicate differences. The point estimate is their mean and
the frozen two-sided 95% interval is

```text
mean(d) +/- t_(0.975,127) * sd(d)/sqrt(128),
```

using Bessel-corrected sample standard deviation and the fixed Student-t
quantile `t_(0.975,127)=1.97882`. All four conjunctive positive requirements
are intersection-union tests: each named 95% lower bound must be positive; no
endpoint may compensate for another.

With 128 independent paired replicates, the prospective normal-approximation
design has at least 80% power at two-sided alpha 0.05 to reject zero for a true
effect of 0.02 when paired replicate SD is at most 0.080, and for a true effect
of 0.05 when SD is at most 0.200. A two-sided FLEX/TWO compatibility interval
at the absolute 0.01 margin has the registered planning precision when its
paired SD is at most 0.040 and the true difference is zero. These SD limits are
prospective design assumptions, not empirical claims.

For TWO, `TWO_NONPASS_POWER_ADEQUATE` means that every failed gate among
`D_S`, `D_L`, and `Delta_mean` has paired SD at most 0.080 and a failed
`Delta_tail` gate has paired SD at most 0.200. For FLEX versus GLOBAL,
`FLEX_NONPASS_POWER_ADEQUATE` applies the same 0.080 mean and 0.200 tail limits
to every failed positive gate, but has timing-family meaning only when
`FLEX_ADAPTIVE_ANSWERABLE` in Section 15. For the FLEX/TWO relation, each
endpoint whose absolute-compatibility or stable-loss conclusion is unresolved
must have SD at most 0.040 before that unresolved relation can be treated as
adequately powered.

No sample-size adaptation is allowed. A required positive gate that passes is
not invalidated by an SD above its planning limit. A failed gate whose observed
paired SD exceeds its corresponding limit is `POWER_NONIDENTIFYING`, not
evidence of absence. Counts, margins, or intervals are never changed to repair
power.

Calibration uses no inferential claim. Its 48 replicates are a finite selector
panel; `C1` and `C2` provide the already registered stability check.

## 13. Selection, competence, support, and reciprocal confirmation

For half `h in {C1,C2}`, class `s`, and lookup `(q_S,q_L)`, define

```text
mu_s^h(q_S,q_L) = valid scored ticks in class s over all cells of h
                  / total scored class-s ticks in h.
```

Define `mu_s^cal` analogously on all 48 calibration replicates. After the
complete panel selects `(q_S*,q_L*)`, form the set-valued conditional maxima

```text
M_S^h   = argmax_[q in Q] mu_S^h(q,q_L*)
M_L^h   = argmax_[q in Q] mu_L^h(q_S*,q)
M_S^cal = argmax_[q in Q] mu_S^cal(q,q_L*)
M_L^cal = argmax_[q in Q] mu_L^cal(q_S*,q).
```

Ties remain sets. With `d_Q(q,q')=8*abs(q-q')` and
`d_Q(q,M)=min_[q' in M] d_Q(q,q')`, define

```text
RATE_RESPONSE_IDENTIFIED =
  (M_S^cal intersection M_L^cal is empty)
  AND d_Q(q_S*,M_S^C1)<=1 AND d_Q(q_S*,M_S^C2)<=1
  AND d_Q(q_L*,M_L^C1)<=1 AND d_Q(q_L*,M_L^C2)<=1.
```

This is a stability/answerability gate, not held-out evidence. The selected
pair is, by construction, in the complete-panel `Q x Q` selector maximum.

`GLOBAL_COMPETENT` requires all of:

1. `SELECTED_CONTROLLER_NONHARM(GLOBAL)` as defined in Section 14;
2. calibration headroom `1-MEAN_VALUE_cal(GLOBAL)>=0.05`;
3. held-out `MEAN_VALUE(GLOBAL)>=0.25` and `TAIL_VALUE(GLOBAL)>=0.10`;
4. in each stratum, at least 256 voluntary `KEEP` and 256 voluntary
   `JOINT-UPDATE` actions pooled over held-out replicates; and
5. in each stratum, at least 96 of 128 held-out replicates contain at least one
   voluntary action of each kind.

The selected TWO and FLEX controllers must separately satisfy
`SELECTED_CONTROLLER_NONHARM` and meet voluntary-action support items 4 and 5
for any positive or adaptive interpretation. BOOT, locked KEEP, safety
override, or unused action uniforms never count as voluntary support.

For selected `C*=(q_S*,q_L*)`, the independently held-out reciprocal controls
are

```text
C_S<-L=(q_L*,q_L*)
C_L<-S=(q_S*,q_S*).
```

`RECIPROCAL_CONTROLS_VALID` requires both logical controls to be present and
complete on all 128 held-out coordinates and to satisfy
`RECIPROCAL_CONTROL_NONHARM` as defined in Section 14. Their scientific role is
exclusively the independently held-out swap confirmation, so no calibration
safety predicate or voluntary-action support minimum applies to these fixed
diagnostic controls.

Using paired replicate class means,

```text
D_S = E[Y_S(C*)-Y_S(C_S<-L)]
D_L = E[Y_L(C*)-Y_L(C_L<-S)].
```

Each must have point estimate at least 0.02 and paired 95% lower bound above
zero. The two pooled treatment effects must simultaneously satisfy

```text
Delta_mean >= 0.02 and LCB95(Delta_mean)>0
Delta_tail >= 0.05 and LCB95(Delta_tail)>0.
```

Define

```text
TWO_ANSWERABLE =
  PACKAGE_VALID AND GLOBAL_COMPETENT AND RATE_RESPONSE_IDENTIFIED
  AND TWO voluntary-action support AND SELECTED_CONTROLLER_NONHARM(TWO)
  AND RECIPROCAL_CONTROLS_VALID

REGISTERED_TWO_RATE_QUALIFIES =
  TWO_ANSWERABLE
  AND q_S*>q_L*
  AND both reciprocal gates
  AND both pooled mean/tail gates.
```

The corresponding `OPPOSITE_SIGN_TWO_RATE` flag substitutes `q_S*<q_L*` while
retaining every other condition. Equality satisfies neither flag.

## 14. Package validity, missing data, and non-harm

`PACKAGE_VALID` requires exact card identity; all 192-by-48 calibration cells
and exactly five logical held-out tags by 128 replicates (with auditable exact
physical aliases where maps coincide); every 20-block route manifest; exact
counter pairing; controller/source/content hashes; selector and alias ledgers;
all physical and endpoint ledgers; complete calibration halves; and successful
analytic identity, boundary, partition, and replay checks. Any absent,
duplicated, substituted, or partially released cell invalidates the package.
There is no imputation, cell deletion, outcome-triggered rerun, best-attempt
choice, or partial-result selection. A technical retry must use identical
source, controller, and coordinate identity and remains hidden until one
complete atomic package exists.

For each UAV tick, define the unconstrained reference pair over the same two
finite velocity registries by the same total order used in Section 6: minimum
summed squared ground-velocity deviation, then minimum total airspeed, then
lexicographically smallest `(i_T,i_R)`. This reference ignores only geofence,
terrain, and inter-UAV-separation feasibility. A team safety-override tick
occurs exactly when the feasible pair selected by Section 6 differs from that
unconstrained reference pair.

For held-out replicate `b` and logical controller `C`, define

```text
O_b(C)   = number of safety-override tick intervals over both encounters
           in all 20 blocks / (20*(48+144))
d_b^O(C) = O_b(C)-O_b(GLOBAL-BEST)
UCB95_O(C) = mean_b(d_b^O(C))
             + 1.97882*sd_b(d_b^O(C))/sqrt(128).
```

The denominator includes every pre-roll and scored interval. Override seconds
and causes are also separately reported. For an exact physical controller map
`C`, define `CAL_HARD_SAFE(C)` as zero terrain penetrations (`d_O<20 m`), zero
geofence exits, zero UAV separation breaches, zero `NO_SAFE_CONTROL` states,
zero `NO_PLANNER_SOLUTION` states, zero battery exhaustions, and no numerical
fault in every one of its 48 calibration cells. Define `HOLD_HARD_SAFE(C)` as
the same zero-failure predicate in every one of its 128 held-out cells. Then
freeze

```text
SELECTED_CONTROLLER_NONHARM(C) =
  CAL_HARD_SAFE(C) AND HOLD_HARD_SAFE(C) AND UCB95_O(C)<=0.01

RECIPROCAL_CONTROL_NONHARM(C) =
  HOLD_HARD_SAFE(C) AND UCB95_O(C)<=0.01.
```

`SELECTED_CONTROLLER_NONHARM` applies exactly to selected GLOBAL, selected TWO
for either sign interpretation, and selected FLEX for any positive,
compatibility, or negative timing interpretation. Their selected physical maps
already have all 48 calibration cells in the immutable registry; this adds no
trajectory. `RECIPROCAL_CONTROL_NONHARM` is prospectively held-out-only because
each reciprocal tag exists solely as an independent held-out swap confirmation,
not as a calibration-selected controller. Both predicates apply identically to
exact physical aliases under their separately reported logical tags. For
GLOBAL the paired override difference is identically zero, but both its
calibration and held-out hard-safety predicates remain mandatory. Energy may
differ through the common update charge but must remain within each fixed
battery budget.

## 15. FLEX comparisons and exhaustive result map

Define

```text
FLEX_TIMING_MEMBER =
  selected FLEX coefficient tuple belongs to V

FLEX_CONTAINMENT_ANSWERABLE =
  PACKAGE_VALID AND GLOBAL_COMPETENT
  AND FLEX voluntary-action support
  AND SELECTED_CONTROLLER_NONHARM(FLEX)
  AND FLEX algebraically distinct from TWO
  AND FLEX realized-support distinct from TWO

FLEX_ADAPTIVE_ANSWERABLE =
  FLEX_CONTAINMENT_ANSWERABLE AND FLEX_TIMING_MEMBER

FLEX_GLOBAL_QUALIFIES =
  FLEX_ADAPTIVE_ANSWERABLE
  AND Delta_FLEX_mean>=0.02 AND LCB95(Delta_FLEX_mean)>0
  AND Delta_FLEX_tail>=0.05 AND LCB95(Delta_FLEX_tail)>0.
```

`V` is the exact 128-member nonzero-slope set in Section 9.2; membership is a
coefficient-tuple fact, not a realized-trajectory inference. If selected FLEX
belongs to `L`, it is reported only as an alternative contained two-stratum
lookup selected under the FLEX total order. Even when
`FLEX_CONTAINMENT_ANSWERABLE`, an `L` member supplies no remaining-tenure,
post-update-age, continuous-timing, wider adaptive-family, powered-negative, or
no-current-timing-evidence conclusion. FLEX timing-membership, support, safety,
or distinctness failure is nonidentification, never negative timing evidence.

For each endpoint `e in {mean,tail}`, let
`d_e=VALUE_e(FLEX)-VALUE_e(TWO)` with its paired interval
`[LCB95_e,UCB95_e]`. Define the root-registered two-sided compatibility rule

```text
FLEX_TWO_ABSOLUTELY_COMPATIBLE =
  FLEX_ADAPTIVE_ANSWERABLE AND TWO_ANSWERABLE
  AND, for both endpoints e,
      abs(d_e)<=0.01 AND LCB95_e>-0.01 AND UCB95_e<0.01.
```

One-sided noninferiority is insufficient. `FLEX_STABLY_LOSES_TWO` holds only
when FLEX is adaptively answerable, TWO is answerable, and, for at least one
endpoint, `d_e<-0.01` and `UCB95_e<-0.01`. Every other adaptively answerable
relation is `FLEX_RELATION_UNRESOLVED`; if a relevant unresolved endpoint has
SD above 0.040, its relation is specifically
`FLEX_RELATION_POWER_NONIDENTIFYING`. A passing compatibility or stable-loss
interval is not invalidated by its SD. FLEX relation power is interpretive
only and never weakens a local TWO conclusion.

Apply this exhaustive ordered map:

1. If `PACKAGE_VALID`, `GLOBAL_COMPETENT`, or a common host, pairing, inference,
   or GLOBAL hard-safety requirement fails, return that exact common
   nonidentification reason. No negative timing claim follows and no FLEX
   contrast is inferential.
2. If `TWO_ANSWERABLE` is false, return the exact TWO support, response,
   reciprocal-control, or non-harm nonidentification reason. Independently, an
   adaptively answerable FLEX satisfying `FLEX_GLOBAL_QUALIFIES` opens one new
   prospective continuous-timing definition question; this does not repair TWO
   or activate empirical work.
3. If all four TWO gates (`D_S`, `D_L`, `Delta_mean`, `Delta_tail`) pass and
   `q_S*>q_L*`, set `REGISTERED_TWO_RATE_QUALIFIES`. This local positive result
   stands regardless of FLEX. Only if the selected FLEX is itself adaptively
   answerable
   and `FLEX_TWO_ABSOLUTELY_COMPATIBLE` may the finite timing-vector containing
   family be called compatible with the local two-rate result. FLEX stable
   loss, non-distinctness, nonanswerability, or an unresolved relation leaves
   the claim local to TWO.
4. If the same four gates pass and `q_S*<q_L*`, set
   `OPPOSITE_SIGN_TWO_RATE`: the registered physical direction is refuted while
   the opposite-sign package-specific crossover may be retained. FLEX cannot
   convert it into the registered direction, a general timing claim, or an
   automatic second surface.
5. In every other answerable TWO case, if any failed one of the four gates
   exceeds its Section 12 SD limit, return `TWO_POWER_NONIDENTIFYING`. Otherwise
   return `VALID_TWO_RATE_NONPASS`, including the `q_S*=q_L*` case: GLOBAL is
   retained as the exact target comparator and simplicity choice, not as an
   equivalent or sufficient rate law.
6. Separately whenever TWO does not set the registered positive flag, an
   adaptively answerable distinct FLEX satisfying `FLEX_GLOBAL_QUALIFIES` opens
   exactly the prospective continuous-timing definition question. If FLEX is
   adaptively answerable but fails a positive gate, its nonpass is negative
   timing evidence only when `FLEX_NONPASS_POWER_ADEQUATE`; otherwise it is
   `FLEX_POWER_NONIDENTIFYING`. FLEX timing-membership, support, non-harm,
   distinctness, or power failure is never negative evidence.
7. Only when TWO is answerable and FLEX is adaptively answerable and both are
   adequately powered nonpasses is there no current timing evidence on this
   host. GLOBAL remains the exact comparator and simplicity choice, never a
   claim of equivalence, sufficiency, or general fixed-rate optimality.

No branch activates UAV production, another ONLGR surface, cross-direction
fusion, a new provider identity, or empirical work.

## 16. Atomic lifecycle and activity boundary

The present stage permits only card authorship, provider review, EM intake, and
CM static feasibility/cost review. It performs no source lookup, repository
inspection, build, test, probe, PRNG draw, coordinate materialization,
trajectory, calibration, training, evaluation, compute, or lease request.

If portfolio later authorizes empirical construction, the lifecycle is:

1. implement the analytic host, controller registry, counter generator,
   analyzers, and immutable manifests without production coordinates;
2. pass deterministic formula, boundary, selector-containment, alias,
   action-law, clock, safety, and atomic-release conformance tests;
3. freeze source/content hashes, math library, compiler/interpreter,
   controller enumeration, worker count, storage schema, and resource lease;
4. generate the complete calibration panel under blinded endpoint output,
   select exactly once, and seal selected identities;
5. generate the complete held-out panel on disjoint coordinates, still blinded;
6. require every mandatory cell and conformance ledger, install one immutable
   complete package, obtain CM technical acceptance, and only then expose one
   result packet to EM.

There is no gradient training, PPO, optimizer, checkpoint, or learned model.
`training_work=0`; exhaustive finite calibration is selection work. Scientific
activity begins at the first materialization of a production-namespace random
word or the first controller tick on a production coordinate, whichever comes
first. After that boundary no science-bearing field in this card may change.

## 17. Exact prospective work and cost

`F=192`, `B_cal=48`, `B_hold=128`, and worst-case held-out `U=5` give

```text
calibration controller-replicates = 192*48 = 9,216
held-out controller-replicates    = 5*128  =   640
total canonical controller-reps   =             9,856
ticks per controller-replicate    = 20*(48+144) = 3,840
total canonical physical ticks    = 37,847,040
```

The 48 and 144 encounter ticks include the common 16-tick pre-roll. A
non-deduplicating implementation that separately repeats the 8 GLOBAL and 64
TWO candidates would add `72*48=3,456` controller-replicates, for a conservative
total of 13,312 and 51,118,080 ticks. That duplication is not authorized
because the immutable registry has exact identity aliases.

No runtime has been measured. The coupled safety candidate search makes an
explicit planning band of 100 to 2,000 complete host ticks per CPU-core-second
more conservative. Canonical raw simulation is therefore 5.3 to 105.1
CPU-hours. Reserving three times raw work for deterministic replay,
conformance, analysis, serialization, and failed-worker same-coordinate
recovery gives 15.8 to 315.4 CPU-hours. At eight authorized CPU workers, the
corresponding planned wall envelope is about 2.0 to 39.5 hours plus build and
technical review. A later static or measured projection above twice this upper
compute envelope (630.8 CPU-hours or 79 hours at eight workers), above the
frozen memory/storage allocations, above 17 engineer-weeks, or requiring a
high-fidelity physics substitution is a material cost/object change and returns
to portfolio before activity. A routine resource slice inside the accepted
envelope does not terminate the science.

The retained schema stores no complete all-cell tick dump. It retains a
maximum 32 KiB summary/conformance record per controller-replicate, all
manifests and hashes, and full tick traces only for these prospectively fixed
already-required cells: CAL replicates 0-7 for lookup maps `(0,0)` and
`(7/8,7/8)`, plus HOLD replicates 0-7 for each of the five logical held-out
tags. This is at most 56 traces and adds no trajectory. Expected retained
storage is below 1 GiB; a 4 GiB hard planning allocation covers JSON
overhead, atomic staging, and the prior package during installation. Streaming
working memory is host state plus summaries; plan 2 GiB RAM per worker and 16
GiB total for eight workers. No GPU is required.

Because this is a new analytic host rather than an existing instrumented
simulator, the static engineering estimate is 11-15 engineer-weeks:

```text
3-4  host geometry, routes, target, sensing, radio, packet and energy laws
2-3  joint planner, low-level flight and safety controller
2    immutable controller registry, selectors and FLEX containment
2-3  paired runner, inference, ledgers and atomic release
2-3  independent conformance, integration and retained-package verification
```

With two engineers this is approximately 6-9 calendar weeks before any
production lease. The range remains inside the previously disclosed
9-17-engineer-week build-from-scratch class. The analytic fidelity excludes
6-DoF aerodynamics, hardware autopilot timing, RF ray tracing, real terrain,
weather assimilation, and aircraft certification; adding any is a new host and
material cost decision.

## 18. Strongest alternatives and claim ceiling

Even a fully positive result could reflect a fixed two-constant architecture
or resource-allocation advantage tied to this exact bend/straight route,
finite selector, planner, blackout, update energy, and mission mixture. The
label bundles turn geometry, portal transition, and tenure, so scheduled tenure
alone is not identified. The analytic planner or radio model may create the
crossover. FLEX may fail because the sparse finite family or calibration
selection does not generalize, even though all lookup controllers are
contained.

At this definition stage there is no empirical claim. If a separately
authorized implementation completed every frozen gate, the maximum claim is:

> On `HEADLAND-90-TRACK-RELAY-2UAV-v1`, two prospectively observable,
> action-independent bend/straight route packages had reciprocally different
> calibration-best legal joint-update rates, and one immutable shared
> class-indexed two-rate controller improved both mean and worst-decile
> held-out valid target-service time over the best pooled constant rate under
> common analytic physics, planner, action, blackout, energy, battery, safety,
> event law, and paired disturbances.

No result can establish tenure-only causality, ONLGR-B2 rescue, event-link,
lease, rebinding, action, or hazard causality, arbitrary or continuous `k`,
variable `N`, within-resource-cap success, real-aircraft transfer, another UAV
task, or general algorithm superiority. A positive FLEX branch remains local
to the exact finite family unless a separately authorized successor tests a
broader adaptive object.

## 19. Definition-stage completion rule

This card becomes complete only after the exact composite receives `CLOSED` in
the existing ONLGR ChatGPT External-Pro conversation, the same-direction EM
intakes that ruling without an unreviewed science change, and the named CM
returns static bindability, observability, isolation, and full cost acceptance.
The mutually blind Gemini consultation is advisory and separately intaken; it
cannot close or block the card. Completion returns to Root and the dedicated
portfolio owner for a separate empirical invest/no-invest decision. It does not
authorize construction, coordinates, compute, or a lease.


