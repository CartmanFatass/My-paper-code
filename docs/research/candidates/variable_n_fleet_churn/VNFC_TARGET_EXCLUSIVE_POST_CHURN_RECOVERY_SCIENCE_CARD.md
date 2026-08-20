# VNFC target-exclusive post-churn recovery science card

Owner: `direction:variable_n_fleet_churn_b4` Explorer Manager  
Definition envelope: `VNFC-TARGET-EXCLUSIVE-POST-CHURN-RECOVERY-DEFINITION`  
Treatment identity: `VNFC-TEPR-LRDA`  
Revision: `VNFC-TEPR-SCIENCE-20260815-04`
Current authority: definition, independent same-direction External-Pro and
External-Gemini consultation, EM intake, and CM static feasibility/full-cost
assessment only

## Decision, independence, and activity boundary

This is a new target-bound science object. It is not a modification, rerun,
partial panel, cost-reduced execution, or empirical continuation of
`VNFC-B4-SCIENCE-20260815-05`. It imports no B4 host, utility, action row, seed,
threshold, panel, checkpoint, result, feasibility observation, technical
acceptance, Pro disposition, or claim. The only reused resources are the
already-authorized same-direction remote conversation identities.

The target is prospective and result-blind. Machine PRNG integer labels and
world coordinates remain unbound. The twenty replicate roles, their independent
namespaces, every distribution, treatment, count, estimand, margin, diagnostic,
and outcome branch below are frozen. A later empirical authorization could bind
fresh injective machine labels to those exchangeable roles without changing the
science object, provided no outcome or implementation observation informs the
binding.

This definition authorizes no source inspection or construction, build, unit or
integration test, probe, dry run, seed or world-coordinate binding, training,
evaluation, exact-panel generation, lease, or compute. No treatment outcome
exists until the complete indivisible activity block defined below is installed.

## Question and causal hypothesis

After an unannounced executor UAV leaves a two-zone surveillance mission, can one
shared permutation-equivariant learned bidder, trained only with post-event
active rosters `N in {3,5}` and frozen before any `N=7` use, restore a larger
fraction of demanded surveillance data at post-event `N=7` than all of:

1. a same-information learned `DIRECT-SET` policy whose stochastic policy class
   strictly contains the complete `L-RDA` policy class;
2. a deployable, causal, physics/history-aware full-horizon fixed controller;
   and
3. the same frozen L-RDA checkpoint after whole learned bid rows are reassigned
   among public-type- and legal-mask-matched, potentially state-distinct UAVs
   (`L-RDA-PERMUTE`)?

The hypothesis is not that additive bids are more expressive. The common RDA is
surjective onto every legal target-role matching, and DIRECT-SET contains the
L-RDA stochastic branch exactly. The prospective mechanism is a finite-budget,
capacity-aligned inductive bias: an agent-shared bidder may learn useful marginal
recovery scores for an unordered changing roster while the exact matching layer
enforces the target's real single-user resources. A positive PERMUTE contrast
would add only that each complete learned row was useful when bound to the
physical UAV record that generated it.

## Independently grounded target exclusivity

### Target class

The target is a pair of separated unattended surveillance-data gateways. Each
zone `z in {1,2}` has:

- one surveyed service volume `S_z`, modeled as a closed ball of diameter eight
  metres;
- a mandatory minimum airborne separation `d_min=15 m` inside the surveyed
  terminal area;
- one mechanically steered optical/narrow-beam terminal with exactly one
  pointing/acquisition chain, one modem, one authenticated session controller,
  no secondary acquisition chain, and no make-before-break multi-UAV handover;
  and
- one surveyed relay volume `R_z`, also diameter eight metres, for the terminal's
  single relay beam.

An **executor** is a UAV inside `S_z` that has acquired the terminal, holds its
authenticated session, observes the local target, and transmits the unique
surveillance stream. Because `diam(S_z)<d_min`, two UAVs cannot lawfully occupy
the service volume. The terminal also refuses a second simultaneous session.
Thus at most one executing UAV per zone follows independently from airspace and
terminal feasibility; it is not a reward penalty, action-space convenience, or
post hoc duplicate-service rule.

The relay volume and relay beam are likewise single-user. `EXECz` and `RELAYz`
are serial resources in one unique end-to-end surveillance stream. `EXECz` is
the sole authenticated terminal-session endpoint. `RELAYz` transparently
forwards that already authenticated stream; it does not originate another
stream, open another terminal session, or require a second terminal pointing
chain, modem, or acquisition chain. A relay UAV is not a second executor and
cannot generate zone observations. For each zone,

```text
inf_{x in S_z,y in R_z} ||x-y|| >= d_min.
```

Thus one executor and one relay may simultaneously occupy their distinct
volumes without violating the airborne-separation rule. Reserves remain at the
command base. A handover is non-overlapping under the exact clearance law below.
The acquired relay loiter ball is separated from the surveyed transit lane
through the `R_z` waypoint; relay occupancy therefore does not manufacture a
sliding-puzzle ingress block.

This target premise is rejected rather than repaired if the intended physical
system admits two separation-compliant vehicles in `S_z`, has a secondary
pointing/acquisition chain, multiplexes two authenticated sessions, requires a
second terminal pointing/modem/acquisition/session for simultaneous execution
and relay, supports make-before-break multi-UAV acquisition, obtains additional
unique value from simultaneous viewpoints, or can deliver the same unique
stream through two independent executors. Such a finding deletes this
target-exclusive object; it may not be converted into an artificial action
mask.

### Fixed graph, clocks, and motion

The command base is `B`. Each zone has relay node `R1` or `R2` and service node
`S1` or `S2`. The surveyed undirected corridor graph has standard-UAV edge
times:

| Edge | standard time |
|---|---:|
| `B <-> R1` | 20 s |
| `R1 <-> S1` | 20 s |
| `B <-> R2` | 30 s |
| `R2 <-> S2` | 20 s |
| `R1 <-> R2` | 40 s |

All other travel uses a shortest path. The only graph route from `B` to `S_z`
passes through the `R_z` waypoint, but the transit lane and relay loiter ball are
distinct as stated above. Every modeled directed edge is a surveyed collection
of mutually deconflicted transit lanes with capacity for all eight registered
UAVs. Simultaneous same-direction and opposing-direction traffic creates no
additional timing, feasibility, or action coupling. The failed-airframe
emergency-egress corridor is disjoint from all controllable transit lanes except
for the registered service-volume hazard lock. If these transit facts are false
for the intended target, the exact object is invalid until a common corridor
scheduler, legality grammar, reachability law, witness, comparators, and
complexity statement are prospectively redefined; no scheduler is silently
implied here. A fast UAV's edge time is
`max(5, 5*ceil(0.75*T_standard/5))` seconds. Physics advances in exact one-second
ticks. Mission assignments occur every twenty seconds. A UAV on an edge must
finish its committed route before accepting another destination. A service-
volume arrival needs six consecutive seconds of acquisition; a relay-volume
arrival needs four.

A **free UAV** is an active controllable UAV that is not on a directed edge at
the decision boundary. En-route UAVs are not variables in the current matching;
they retain their existing destination and token commitment. A token command
persists through the registered shortest path. Arrival at an intermediate node
atomically registers continuation onto the next route edge, whose motion begins
in the next physical second, without a new high-level command. Thus an
intermediate arrival coincident with a decision boundary remains an en-route
fixed commitment when the observation is serialized. A relay token may be
acquired before its executor exists, but produces no delivery until both serial
resources are acquired in a `BLOCKED` zone.

For ordinary token handover, reissuing the same token to its stationary acquired
holder preserves acquisition, and reissuing it to a stationary acquiring holder
preserves elapsed consecutive acquisition. If a stationary acquired or
acquiring holder is not reissued that token, its delivery and acquired state end
and its acquisition elapsed resets at the command boundary. It spends the first
following physical second clearing the token volume while beginning its outbound
route; the volume becomes clear at the end of that second. A successor assigned
at the same boundary may travel immediately but cannot begin acquisition until
the ordinary one-second clearance and any failed-airframe hazard lock have
ended. The failed-service-volume lock on `[0,20)` supersedes ordinary clearance;
entry at timestamp `20` is legal.

For every physical second `[s,s+1)`, demand and obstruction are constant and the
following ordered physics is exact:

1. A UAV on an edge at timestamp `s` consumes its registered flight energy and
   advances one second. Arrival occurs at `s+1`; it performs no acquisition,
   charging, service-energy consumption, or delivery during that same second.
2. A stationary UAV at `B` whose command is `B` charges for the full second. A
   UAV arriving at `B` at `s+1` starts charging only in the next second.
3. A stationary unacquired UAV at its commanded token node performs one full
   acquisition second, consuming no energy and supplying no delivery. If this
   completes acquisition, it becomes acquired at `s+1`.
4. A UAV already acquired at `s`, reissued the identical token, and not clearing
   consumes the registered executor or relay service energy for the full second,
   even when obstruction or the missing complementary serial resource makes
   delivered rate zero.
5. Delivery on `[s,s+1)` uses only UAVs already acquired at timestamp `s`.

Consequently, a UAV requiring `T` travel seconds and `A` acquisition seconds
first supplies service at timestamp `t+T+A`.

Energy is represented in fifth-units, so all state transitions are integer.
Capacity is 160 energy units and the hard reserve is 20. Standard flight consumes
1 unit/s, fast flight 1.2 units/s, acquired execution 0.4 units/s, acquired relay
0.2 units/s, and base charging restores 2 units/s up to capacity. A token is
legal only under the exact contingency below. For a free UAV-token candidate at
boundary `t`, ETA is the earliest acquisition-completion timestamp minus `t`
under continuous execution of that candidate, including multiedge travel,
ordinary handover, failed-airframe clearance, and acquisition. For an illegal
candidate, its mask bit, ETA feature, and return-margin feature are exactly zero.
An en-route UAV has all four variable legal-token mask bits zero and supplies no
sampled, scored, or likelihood-bearing bid edge.

The safe-return contingency issues the candidate at `t` and retains it through
`[t,t+20)`. At every subsequent twenty-second boundary, including a synthetic
return boundary at `t=120` if needed, an edge commitment continues; otherwise
the UAV is commanded to `B`. If it reaches the candidate after `t+20` but before
the next boundary, it may acquire and serve until that next boundary commands
`B`. The contingency continues beyond the reward horizon, without additional
reward or demand transition, until `B` is reached. A candidate is legal iff all
compatibility, occupancy, clearance, and commitment conditions hold and energy
never falls below 20 over this complete contingency. Its return-energy margin
is the minimum energy over the contingency minus 20. The same exact legality
function is used by every arm and by the fixed controller.

At a decision boundary the order is:

1. finish physics on `[t-20,t)`, apply arrivals, acquisition, service, energy,
   and persistent-route continuation, and shift the exact public-history block
   described below;
2. advance public demand and obstruction states, except at `t=-120`;
3. apply the sole membership event and start its physical clearance process at
   `t=0`;
4. recompute current delivered rates, then serialize the public observation and
   legal-token masks; and
5. choose and start the next common low-level command.

### UAV types and roster law

There are eight latent physical UAVs. Their public type sequence, before any
opaque row permutation, is:

| latent position | flight class | radio capacity |
|---:|---|---:|
| 1 | fast | 2 |
| 2 | standard | 2 |
| 3 | fast | 1 |
| 4 | standard | 1 |
| 5 | fast | 2 |
| 6 | standard | 2 |
| 7 | fast | 1 |
| 8 | standard | 1 |

Radio capacity is a public physical rate in unique data units per second. It is
not an identity label. Pre-event active rosters are the first `N+1` physical
UAVs for target post-event size `N`. Training target sizes are `N=3` and `N=5`,
sampled equally; their pre-event rosters therefore have sizes four and six. The
held-out conclusion population has post-event `N=7` and pre-event size eight.

At every observation boundary, a treatment-blind uniform permutation presents
the active agent records. It is counter-keyed by replicate role, world
coordinate, and physical time, common across arms in that world, and independent
across boundaries. A separate treatment-blind episode-level uniform total rank
over latent UAVs breaks exact physical/action ties and keys audit mappings; it
is also common across arms. Row order and opaque rank are never model or fixed-
controller features.

### Demand, obstruction, relay, and delivered service

Each zone has public demand `q_z(t) in {1,2}` and public obstruction
`h_z(t) in {CLEAR,BLOCKED}`. States change only at decision boundaries and are
independent across zones and between demand and obstruction. At `t=-120`, each
binary state is uniform. The transition matrices, in the displayed state order,
are:

```text
P_q = [[4/5, 1/5],
       [3/10, 7/10]]

P_h = [[4/5, 1/5],
       [2/5, 3/5]]
```

An acquired executor of radio capacity `g_e` delivers
`min(q_z(t),g_e)` unique units/s when the zone is `CLEAR`. When it is `BLOCKED`,
direct delivery is zero; an acquired relay of capacity `g_r` at `R_z` yields
`min(q_z(t),g_e,g_r)` unique units/s. With no acquired executor, delivery is
zero. With no acquired relay in `BLOCKED`, delivery is zero. Duplicate packets
cannot increase delivery, and the one executor/one relay hardware admits no
duplicate session.

Let `a_z(t)` be that delivered unique rate. The sole reward and conclusion
utility over the post-event horizon `[0,120)` is

```text
U_rec = integral_0^120 [a_1(t)+a_2(t)] dt
        / integral_0^120 [q_1(t)+q_2(t)] dt .
```

`U_rec` is the fraction of demanded zone-data-time acknowledged at command. It
lies in `[0,1]`, values prompt and sustained recovery automatically through lost
physical seconds, and contains no algorithm, bid, identity, handover, duplicate,
or exclusivity bonus. Safety and reserve are hard feasibility constraints rather
than compensable reward terms. Training optimizes exactly this terminal utility.

### Treatment-blind natural prehistory and churn

At `t=-120`, every pre-event active UAV is at `B`, fully charged, uncommitted,
and has zeroed public history counters. One arm-blind deterministic operations
controller runs at `t=-120,-100,-80,-60,-40,-20`. At each boundary it enumerates
all legal variable target-role matchings conditional on the fixed en-route
commitments, thereby producing complete commands. It first restricts to
matchings that
retain every currently acquired executor that remains legal and every currently
acquired relay whose zone is currently `BLOCKED` and whose retention remains
legal. It then chooses the lexicographically minimum serialization after
applying, in order:

1. greater number of filled executor tokens;
2. for `EXEC1` and then `EXEC2`, smaller tuples
   `(time to acquired service,negative radio capacity,opaque rank)`, with a null
   executor represented by an infinite sentinel;
3. greater number of filled relay tokens required by currently `BLOCKED` zones;
4. for `RELAY1` and then `RELAY2`, smaller tuples
   `(negative radio capacity,time to acquired relay,opaque rank)`, with a null
   required relay represented by an infinite sentinel; and
5. the registered exact complete-command serialization.

Every free UAV not selected for a token is commanded to `B`. A relay in a
`CLEAR` zone is not required and is returned to `B` unless selected for another
token.

Given the frozen graph, energy, roster prefixes, and 120-second prehistory, this
controller has both service tokens acquired before `t=0` for every registered
world. It is not told which zone will fail.

At `t=0`, after the public demand/obstruction transition, the presampled
`z_fail` label selects the acquired executor holding `S_z_fail`. That vehicle
suffers an unannounced terminal-interface failure and leaves the controllable
active roster immediately, but it does not disappear physically. Its intact
low-level safety autopilot follows the target's surveyed emergency-egress path
for exactly twenty seconds. The failed service volume is hazard-locked on
`[0,20)`; no successor may enter or acquire it. At `t=20` the failed airframe has
cleared the terminal area and leaves the physical model. This clearance object
has no treatment action, consumes no roster slot, provides no service, follows
the same deterministic law in every arm, and is represented by public
`clearance_remaining in {20,19,...,0}`. No other membership event occurs.

Each executor and relay token has exactly one of three public states:
`VACANT`, `COMMITTED_OR_ACQUIRING`, or `ACQUIRED`; the acquisition-elapsed
scalar supplies progress. At each boundary after completing the preceding
interval and before the new demand/obstruction transition and `t=0` failure,
one history block is shifted for every active UAV. The inserted block contains
the token command governing the final second, acquisition elapsed at interval
end, the UAV's attributed delivered rate in that final second, and time since
its most recent second of positive attributed delivery saturated at 120. An
acquired executor is attributed the zone's unique acknowledged rate. An
acquired relay is attributed that same rate only while forwarding the active
`BLOCKED`-zone stream; this duplicate feature never duplicates reward. The zone
time-since-acknowledged-delivery counter resets after a second with `a_z>0` and
otherwise increments to 120. At `t=-120` all history-present bits are zero;
each inserted block has history-present one. After the boundary transition and
any `t=0` failure but before action, current delivered rate is recomputed from
the resulting physical state. The nonfailed zone's clearance field is zero.

Failure and clearance are revealed through the ordinary membership/heartbeat
and terminal-area observation at the same boundary. The remaining controllable
state plus clearance object is cloned exactly across arms before any learned or
comparison action. Future demand/obstruction tapes are common across arms within
a world.

The event is executor-conditioned because the target question is recovery from
loss of a current single-user service holder, not the unconditional probability
that a random spare leaves. Failure-zone labels are marginally fair but
panel-stratified, not mutually independent within a registered batch or panel:

- for each replicate, arm-independent training outer batch, and final roster
  size `N in {3,5}`, a uniform random permutation of sixteen `ZONE1` and sixteen
  `ZONE2` labels is assigned in world-coordinate order;
- for each replicate and validation size `N in {3,5}`, an independent uniform
  permutation of thirty-two labels of each kind is assigned; and
- for each replicate conclusion panel, an independent uniform permutation of
  sixty-four labels of each kind is assigned.

These permutations are counter-keyed independently of UAV types, demands,
obstructions, opaque ranks, row orders, learned parameters, latent actions, and
outcomes. Each label is presampled before prehistory and hidden from its
controller. No rejection, top-up, outcome-conditioned relabeling, or independent
per-world failure coin is permitted.

## Information and observation law

Every deployable arm receives the identical current public observation:

- an unordered active-agent set containing flight/radio type, current node or
  edge and remaining travel time, energy/capacity, current token, acquisition
  time, exact legal-token mask, zone-specific ETA and return-energy margin, and
  the previous three assignment epochs of token, acquisition, delivered rate,
  and time since most recent positive attributed delivery;
- two labeled zone records containing current demand, obstruction, current
  executor/relay occupancy and acquisition state, current delivered rate, time
  since acknowledged delivery, and failed-airframe clearance remaining; and
- normalized post-event time, `log(1+N)/log(8)`, and the public cumulative
  post-event demand
  `D_past(t)=integral_0^t [q_1(s)+q_2(s)] ds`, normalized by `480`.

The canonical agent record has width 65: flight-class one-hot (2), radio scalar
(1), node-or-directed-edge one-hot over five nodes and ten directed edges (15),
remaining edge time (1), energy (1), current-token one-hot including null (5),
acquisition elapsed (1), legal-token mask (4), four token ETAs (4), four
return-energy margins (4), three history blocks each containing token one-hot
plus acquisition, delivered rate, and time since positive attributed delivery
(24),
and three history-present bits (3). Each zone record has width 14: demand (1),
obstruction one-hot (2), executor and relay occupancy/acquisition-state one-hots
(6), executor and relay acquisition elapsed (2), delivered rate (1), time since
acknowledged delivery (1), and clearance remaining (1). The three global
scalars are normalized time, normalized log-cardinality, and normalized
`D_past`.

Categorical values are exact one-hots or mask bits. Every scalar is encoded by
the following literal table; `clip(x,0,M)/M` is used where stated and there is no
other saturation or calibration:

| physical scalar | encoding |
|---|---|
| radio capacity or delivered-rate history/current rate | `clip(x,0,2)/2` |
| remaining directed-edge time | `clip(x,0,40)/40` |
| energy | `clip(x,0,160)/160` |
| acquisition elapsed, executor or relay | `clip(x,0,6)/6` |
| token ETA including clearance wait and acquisition | `clip(x,0,140)/140` |
| return-energy margin above the hard reserve | `clip(x,0,140)/140` |
| time since positive attributed or acknowledged delivery | `clip(x,0,120)/120` |
| post-event time | `t/120` |
| set cardinality | `log(1+N)/log(8)` |
| cumulative post-event demand | `D_past/480` |
| clearance remaining | `clearance_remaining/20` |
| zone demand | `q_z/2` |

Missing history before `t=-120` is zero with its separate history-present bit.
No learned normalization, running statistic, `N`-specific calibration, padding
position, or slot index exists.

No executable arm receives future demand/obstruction, the failed-zone coin before
the event, future membership, realized utility, advantage or critic output,
another arm's state/action, an arm or replicate label, opaque rank, latent row
position, or a ceiling action. The full-horizon fixed controller receives the
same current public state and the registered transition law, never a realized
future tape.

For replicate `i` and learned arm `A in {L-RDA,DIRECT-SET}`, `A`'s training
support collection consists only of the pre-action public states actually
encountered by `A` in its own 4,096 training trajectories. A deterministic
validation or conclusion state reached by `A` is supported iff every named
categorical
component and every exact pre-normalization discrete physical scalar value in
that state occurred at least once in `A`'s own collection. The only exemptions
are the held-out set cardinality `N=7`, its normalized scalar, and multiplicity
of already-supported record types. The other learned arm, validation,
conclusion, initialization, fixed controller, and PERMUTE cannot supply support.
L-RDA supplies the reference for PERMUTE. Unsupported states remain in `U_rec`.

## Common command and target-role grammar

The four labeled physical tokens are
`T={EXEC1,RELAY1,EXEC2,RELAY2}`. A legal mission command is a partial injective
matching `X` from currently available tokens to active free UAVs, conditional on
the fixed en-route route/destination commitments `C`. A stationary currently
occupied token remains available for either reissue to its holder or assignment
to one successor under the handover law; a token fixed by an en-route commitment
is unavailable. A UAV receives at most one token, and each token receives at
most one fixed or variable UAV. Tokens may be null. En-route agents retain their
route and destination; unmatched free agents are commanded to `B`. Terminal
compatibility, energy, occupancy clearance, and edge commitment enter one common
legality mask. Fixed commitments supply no bid term.

For `N` free agents, the unmasked grammar has

```text
|F(o)| <= sum_{k=0}^4 C(4,k) * N!/(N-k)! = O(N^4).
```

At `N=7` the upper bound is 1,961 matchings. Streaming enumeration and the
selected action require `O(N^4)` time and `O(N)` live memory for the fixed four
tokens. No arbitrary-token-count or growing-task scalability claim is made.

Given fixed commitments `C` and any legal variable matching `X`, bids `+2` on
its agent-token edges and `-2` on every other legal variable edge make `X` the
unique maximum-sum matching, with null bid zero and the canonical tie law below.
Thus the RDA is surjective onto every legal variable decision conditional on
`C`. Every arm uses the same complete-command serializer and low-level
motion/acquisition controller.

### Exact complete-command serialization

The world's eight opaque ranks are the integers `1,...,8`; sentinel `9` denotes
null or padding. At a decision, `C` is the set of fixed en-route destination and
token commitments and `X` is the variable matching from free UAVs to available
tokens. In the exact token order `EXEC1,RELAY1,EXEC2,RELAY2`, define
`occ_tau(C,X)` as the fixed committed UAV's rank when `tau` is fixed by `C`,
otherwise the free UAV rank assigned by `X`, and otherwise `9`.

Let `B(C,X)` be the ascending ranks of all active UAVs whose post-command
destination is `B`, including unmatched free UAVs and fixed en-route-to-`B`
UAVs, padded on the right with `9` to length eight. The complete serialization
is

```text
[occ_EXEC1,occ_RELAY1,occ_EXEC2,occ_RELAY2,B(C,X)].
```

Every equal-score or equal-value decision takes the lexicographically smallest
serialization. In DIRECT's residual branch, `|X|` counts only variable free-
UAV/token edges. Fixed commitments `C` are represented in public state but do
not enter the cardinality one-hot, selected-edge sum, or selected-edge maximum.

### Static action-value witness

The frozen law contains a positive-probability reachable held-out state after
failure of zone 1 in which:

- a capacity-2 standard UAV is acquired at `R1` with energy at least 100;
- a capacity-1 standard reserve and a capacity-1 fast reserve are at `B` with
  energy at least 120;
- zone 1 is `BLOCKED`, its executor is absent, and both candidate executor/relay
  matchings are legal.

Condition on the positive-probability tape on which zone 1 remains `BLOCKED`
through the first forty-six post-event seconds. Compare two legal first
commands: (A) retain the capacity-2 standard UAV at `R1` and send the capacity-1
standard reserve from `B` to `S1`; and (B) send the capacity-2 standard UAV from
`R1` to `S1` and the capacity-1 fast reserve from `B` to `R1`. At `t=20` and
`t=40`, reissue the same intended token assignments whenever they remain legal;
no other continuation difference is introduced. The physical clearance lock
lifts at `t=20`. Command A first restores a capacity-1 blocked-zone stream at
46 seconds; command B first restores it at 26 seconds. Because `q_1(t)>=1`, B
therefore delivers at least twenty additional unique demand-weighted
data-seconds on the common tape. This is an existential physical-action witness,
not a policy input, retained-world condition, empirical probe, or outcome gate.

## Learned treatments

### Common learned encoder and critic

Each learned arm has its own independently initialized parameters. Actor and
critic parameters are disjoint. The actor maps the width-65 agent record through
`affine 64 -> tanh -> affine 64 -> tanh`. Its width-159 common set summary is
the concatenation of coordinatewise mean and maximum of the width-64 agent
embeddings, the two width-14 zone records, and the three global scalars. The
critic owns an independently initialized agent encoder of the identical
`65 -> 64 -> 64` architecture, constructs its own width-159 summary, and maps
that summary through `affine 64 -> tanh -> affine 1`. It never shares, reads, or
backpropagates through an actor tensor.

Every linear matrix is independently Haar-uniform on the appropriate row- or
column-Stiefel manifold conditional on
`(replicate role,arm,actor-or-critic,tensor name)`. Hidden matrices have gain
`1`; policy-output matrices have gain `0.01`; critic output has gain `1`. All
biases are zero. Each embedded bidder's four learned token log standard
deviations start at `-1`. After every Adam update they are projected
componentwise onto `[-3,0]`; the projected values are used for subsequent data
collection, likelihoods, entropy, and checkpoint metadata. No forward-only
clamp, alternate reparameterization, or framework default is permitted.

### L-RDA

For each active agent and token, the shared bid head receives the width-241
concatenation `(agent embedding,common set summary,token one-hot,associated zone
record)` and maps it through
`affine 64 -> tanh -> affine 32 -> tanh -> affine 1` to a Gaussian mean. During
training, independent Gaussian latent bids with the learned token-specific
standard deviations are sampled for all legal edges; illegal edges are absent.
The common RDA returns the maximum-sum legal matching. During evaluation, means
replace samples. Null-token bid is exactly zero.

This is one shared parameterization across all agents, tokens, training roster
sizes, and the untouched held-out roster. Opaque identity and presented row
position never enter the bidder or recurrent state; the policy is exactly
permutation-equivariant.

### Strictly containing DIRECT-SET

DIRECT-SET receives the identical observation and legal matching set. It has:

1. an embedded branch that is an exact copy of the entire L-RDA bidder,
   Gaussian latent law, RDA, and tie serializer;
2. a residual branch whose edge encoder receives the identical width-241
   concatenation and maps it through
   `affine 64 -> tanh -> affine 64 -> tanh`; and
3. a learned Bernoulli gate over the embedded and residual branches.

For legal matching `X`, the residual branch concatenates the width-159 common
summary, sum and coordinatewise maximum of its selected width-64 edge
embeddings, and the exact five-way one-hot of `|X| in {0,1,2,3,4}`. Sum and max
are all-zero for the empty matching. This width-292 vector maps through
`affine 64 -> tanh -> affine 64 -> tanh -> affine 1`. A separate trainable
five-vector `c_card` adds `c_card[|X|]` to that score. The categorical
probability is the exact Euclidean sparsemax projection of the complete score
vector onto the legal-matching simplex. It is sampled during training and uses
its greatest probability at evaluation, with canonical ties. Shannon entropy
uses `0 log 0 = 0`. The projection is the unique minimizer
`argmin_(p in simplex)||p-score||_2^2`. For backpropagation, its positive support
`S={j:p_j>0}` uses Jacobian
`d p_j/d score_k=1[j=k]-1/|S|` for `j,k in S` and zero otherwise; an exactly
zero coordinate is inactive. Entropy differentiates only through that positive
support under the same convention. This prospectively fixes the boundary
subgradient rather than delegating it to a library default.

The gate receives exactly the width-159 common summary and maps through
`affine 32 -> tanh -> affine 1` to `g`. Its embedded probability is the hard
sigmoid `p_emb=clip((g+1)/2,0,1)`. The gate samples in training. At evaluation,
`p_emb>=1/2` selects embedded, with the exact tie going to embedded. All
`c_card` entries initialize to zero. Bernoulli entropy uses `0 log 0=0`; its
gradient with respect to `g` is the usual interior chain-rule value for
`-1<g<1` and exactly zero for `g<=-1` or `g>=1`, including the boundary
points. This is also the hard-sigmoid derivative convention.

Containment is exact: `p_emb=1` is attainable under the hard sigmoid, and
copying any L-RDA actor and standard-deviation parameters then reproduces the
complete L-RDA latent and environmental-action distribution.

Containment is also strict. At any registered legal observation with at least
one one-edge matching, set the residual neural score to zero,
`c_card[1]=1`, all other `c_card[k]=-1`, and `p_emb=0`. Sparsemax then assigns
equal positive mass to the one-edge matchings and exact zero mass to the legal
empty matching and every other legal cardinality. By contrast, every L-RDA
token standard deviation is at least `exp(-3)>0`. For every legal matching the
registered `+2/-2` RDA witness contains an open Gaussian-bid neighborhood on
which that matching is uniquely selected, and the independent Gaussian density
is positive on that neighborhood. Every L-RDA environmental-action distribution
therefore has full support and cannot equal the residual witness. Thus the
DIRECT stochastic class strictly contains L-RDA without adding an illegal or
projection-equivalent action.

DIRECT's larger capacity, sparse residual policy, and different optimization
geometry are part of the containing-policy package. The executed-residual-use
gate below requires the additional branch to be behaviorally active. Any
positive L-RDA
contrast is limited to finite-budget capacity-aligned inductive bias or
trainability relative to that package, never superior expressivity or
optimizer-independent architecture value. DIRECT has no unregistered token,
identity table, or `N`-specific parameter.

## Nonlearned and intervention comparators

### Deployable full-horizon fixed controller

`FIXED-FH` is a causal, closed-loop, result-independent exact finite-horizon
Bellman controller inside one prospectively fixed physics/history-aware analytic
action family. It receives the identical public state, including `D_past`, and
the registered transition law, never a realized future tape or learned tensor.

For every legal agent-token edge `e=(i,tau)`, form the seven exact oriented
features

```text
phi_1 = 1 if i is acquired on tau, else 0
phi_2 = 1 - min(140,ETA(i,tau))/140
phi_3 = clip(return-energy-margin(i,tau),0,140)/140
phi_4 = radio_capacity(i)/2
phi_5 = clip(time-since-acknowledged-service(zone(tau)),0,120)/120
phi_6 = 1 if tau is a vacant executor, or a missing relay in a BLOCKED zone,
        else 0
phi_7 = 1 - min(80,release_loss_20(i))/80 .
```

`release_loss_20(i)` is the nonnegative raw unique delivered data lost on the
current twenty-second physical interval by releasing `i` from its current
acquired token and leaving that token vacant, holding every other current token
and the current demand/obstruction state fixed; it is zero when `i` has no
acquired token. It is an analytic current-state quantity, not a realized-future
or learned value.

For every nonzero `w in {0,1}^7`, bid `w dot phi(e)` on each legal edge, zero on
null, and use the common RDA and canonical tie law. `A_bid(o)` is the set of the
at most 127 distinct resulting legal matchings. Add two registered greedy-
marginal candidates:

- `X_20(o)` maximizes exact expected delivered data on
  `[t,min(t+20,120))` over every legal current matching; and
- `X_40(o)` is the first action maximizing exact expected delivered data on
  `[t,min(t+40,120))`, where the second boundary uses `X_20` in its reached
  public state only when `t+20<120`; at `t=100` there is no second action.

Both expectations integrate the registered Markov law and use canonical ties.
The fixed candidate set is
`A_fix(o)=A_bid(o) union {X_20(o),X_40(o)}`. This includes the strong
short-horizon greedy-marginal alternative rather than comparing L-RDA only with
a nearest-UAV or rigid future heuristic.

The full-horizon policy is defined by exact backward induction over the six
post-event decision epochs. At boundary `t`, for each `X in A_fix(o_t)`, let
`C_future(X,kappa_FH)` be all unique delivered data on `[t,120)` when `X` is
used now and the already-defined later-time `kappa_FH` action is used at every
future public state. Let `D_future` be total demand on `[t,120)`. Define

```text
Q_FH(o_t,X) = E[ C_future(X,kappa_FH)
                 / (D_past(t)+D_future) | o_t ].
```

At `t=100` this has no later decision; earlier epochs use the policy defined at
the next epoch. The expectation is exact over the finite demand/obstruction law
and physical state transitions, including clearance. The greatest-`Q_FH`
matching is executed with canonical ties. Past delivered data is absent because
its additive numerator is common to all candidate actions, while the realized
past-demand denominator is supplied by `D_past`. The same recursion is
recomputed from the newly observed state at every real boundary, so the
controller reacts to failure, clearance, demand, obstruction, motion, energy,
and roster state for the full remaining horizon.

`FIXED-FH` is the strongest registered deployable fixed controller for this
object. It is exact only within `A_fix`; it is not globally optimal over all
possible nonlearned state-feedback policies. No result supports a claim against
that larger unregistered class.

### L-RDA-PERMUTE

At every conclusion decision, first compute the frozen deterministic L-RDA bid
row for every free agent. Partition agents by exact `(flight class,radio
capacity,legal-token mask)`. Location, energy, commitment, and public history
may differ within a block; that state-row-to-physical-recipient relation is the
intervention target. Within a block of size at least two, order agents by
opaque rank and draw independently and uniformly from all fixed-point-free
permutations under the counter key

```text
(replicate role,"TEPR-permute",world coordinate,variant 0..7,
 physical time,ordered opaque-rank tuple).
```

Blocks of size zero or one use identity. Assign the complete source row of four
bids to the recipient physical UAV, then run the common RDA. Physical state,
record multiset, masks, exogenous tape, action cardinality, and low-level control
are unchanged. Opaque rank chooses the intervention mapping but is never an
L-RDA feature.

Eight independently keyed full-rollout variants are generated from the same
frozen checkpoint and world. Subsequent decisions repeat the same rule on the
reached state. This cuts the association between a learned state-conditioned row
and the type-and-legality-matched physical UAV it controls without deleting any
row or changing the observed record multiset, legal action set, row multiset, or
low-level controller. It is not a test of physical interchangeability, opaque
identity, or consistent relabeling; an equivariant L-RDA would reproduce a
consistent relabeling exactly. Any supported inference is limited to useful
state-row/recipient association.

## Training law

There are twenty independent replicate roles. Within each replicate, L-RDA and
DIRECT-SET have independent parameter/latent-action namespaces and common
training world coordinates. No parameter, optimizer state, trajectory, or
normalization is shared across arms.

Each learned arm receives 64 outer batches of 64 complete post-event episodes.
Every batch contains exactly 32 final-`N=3` and 32 final-`N=5` worlds; within
each size, sixteen worlds fail zone 1 and sixteen fail zone 2. Thus each arm and
replicate receives 4,096 trajectories, 24,576 post-event policy decisions, and
256 Adam steps. Prehistory is simulated for each world but supplies no learned
action or gradient.

At each of the six post-event decisions, the critic predicts terminal `U_rec`.
The return target is the realized terminal utility. Raw advantages are
`A_d=U_rec-V_old(o_d)`. They are standardized once across all 384 decision
samples using the population mean and population standard deviation; if that
standard deviation is zero, all standardized advantages are zero.

For L-RDA, the exact decision log density is the sum of the independent legal-
edge Gaussian log densities. For DIRECT with sampled branch `g`, it is

```text
log pi_d = log Bernoulli(g;p_emb)
           + 1[g=embedded] * sum_(e legal) log Normal(z_e;mu_e,sigma_e^2)
           + 1[g=residual] * log sparsemax(score)[X_sampled] .
```

Only a positive-probability branch/action can be sampled. The old legal mask,
branch, latent bids, residual matching, and old log density are recorded once
and reused in every epoch. When every new factor is positive, the PPO ratio is
the exponential of the new minus old complete decision log density.
Operationally it is computed factorwise as new probability or density over the
recorded positive old probability or density. If a new gate or sparsemax factor
is exactly zero, the complete ratio is exactly zero and uses the registered
zero/inactive-support subgradient; no `log(0)` library behavior is invoked. No
agent-level replication of team return occurs.

L-RDA decision entropy is the arithmetic mean of legal-edge Gaussian entropies,
or zero for an empty legal-edge set. DIRECT decision entropy is

```text
H_Bernoulli(p_emb)
  + p_emb * mean_legal_Gaussian_entropy
  + (1-p_emb) * H_sparsemax_categorical,
```

where a one-action categorical and an empty legal Gaussian set have zero
entropy. The batch entropy is the arithmetic mean over the 384 decisions; it is
not pooled or summed by latent-variable or legal-action count.

For decision sample `d`, let `r_d` be that exact factorwise ratio. One
full-batch epoch minimizes

```text
L = -mean_d min(r_d*A_d,clip(r_d,0.8,1.2)*A_d)
    + 0.5*mean_d (V(o_d)-U_rec)^2
    - 0.01*mean_d H_d .
```

There is one Adam optimizer over the disjoint actor and critic tensors with
learning rate `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`, no weight decay or
schedule, and joint maximum gradient norm `1`. Each outer batch receives four
such full-batch epochs, hence four Adam updates. The projected log-standard-
deviation law is applied after each update. `gamma=1`; there is no GAE, critic
clipping, reward shaping, minibatching, or framework-default loss reduction.

The initial checkpoint is recorded before the first environment interaction and
the sole final checkpoint after outer batch 64. No intermediate checkpoint is
evaluated or selectable. Network dimensions, optimizer, budget, margins, and all
analysis are frozen without `N=7` data.

## Validation, conclusion panel, and observables

For each replicate, deterministic initial and final learned checkpoints are
evaluated on 64 fresh final-`N=3` and 64 fresh final-`N=5` validation worlds,
equally stratified by failed zone. These worlds establish only in-support
competence and executed DIRECT residual use.

For every supported final-checkpoint DIRECT validation decision define

```text
I_select = 1[p_emb < 0.5]
I_executed_change = 1[p_emb < 0.5 and X_residual != X_embedded],
```

where the exact `p_emb=0.5` tie selects embedded, `X_residual` is the canonical
deterministic sparsemax action, and `X_embedded` is the canonical deterministic
mean-bid RDA action. For each replicate, final size in `{3,5}`, and failed-zone
cell, average each indicator over all supported DIRECT validation decisions in
that cell.

The untouched conclusion panel contains 128 fresh final-`N=7` worlds per
replicate, with 64 failures of each zone. Every world includes the common
prehistory and common post-event exogenous tape. It evaluates:

- final deterministic L-RDA;
- final deterministic DIRECT-SET;
- FIXED-FH;
- all eight full-rollout L-RDA-PERMUTE variants; and
- registered treatment-blind support, reachability, action-sensitivity, and
  association counterfactuals.

For every arm/world, record `U_rec`, time to first restored nonzero delivery in
the failed zone, delivered units by zone, every matching, mask, row-to-physical
mapping, token acquisition, energy/reserve integrity, and the full public state.
Only `U_rec` is claim-bearing; the other quantities diagnose validity and the
registered mechanism gates.

For each world, also record the total number `K_h in {0,...,10}` of obstruction
state changes across both zones at the five post-event transition boundaries
`t=20,40,60,80,100`. Report the paired `L-RDA minus FIXED-FH` mean separately
for every exact `K_h` value, with empty cells explicit. This is a predeclared
descriptive reactivity diagnostic only; it is not an inferential family, gate,
subgroup claim, or basis for changing the fixed controller.

### Practical margin and replicate rows

The new recovery margin is `delta_rec=0.025`. At the minimum possible demand
denominator of 240 units, this is six unique delivered data-seconds: one complete
executor acquisition interval. It is chosen from the new target clock, not from
another VNFC object. Define `Better(a,b)` when the simultaneous 95% lower bound
for mean `U_rec(a)-U_rec(b)` is strictly greater than `delta_rec`. Define
`Equivalent(a,b)` when the simultaneous 90% interval lies strictly inside
`[-delta_rec,+delta_rec]`.

Within each replicate, world coordinates are averaged first. Replicate roles,
not worlds, decisions, UAVs, or permutation variants, are inferential units.
Efficacy coordinates include aggregate and failed-zone-1/failed-zone-2 means for
`L-DIRECT`, `L-FIXED`, `L-PERMUTE`, and `DIRECT-FIXED`. The PERMUTE value is the
equal mean over the eight variants within each world.

### Registered simultaneous inference

There are exactly three separately simultaneous families:

1. **Held-out efficacy, 12 coordinates:** population in
   `{aggregate,failed-zone-1,failed-zone-2}` crossed with contrast in
   `{L-DIRECT,L-FIXED,L-PERMUTE,DIRECT-FIXED}`.
2. **Training competence, 8 coordinates:** learned arm in
   `{L-RDA,DIRECT-SET}` crossed with final `N in {3,5}` and failed zone in
   `{1,2}`, for final-checkpoint minus initial-checkpoint `U_rec`.
3. **Validity/mechanism, 16 coordinates:** DIRECT residual-selection rate at
   each `(N in {3,5},failed zone)` (4); DIRECT executed-residual-change rate in
   the same four cells (4); conclusion action-
   sensitivity rate by failed zone (2); permutation-opportunity rate by failed
   zone (2); association immediate-matching-change rate by failed zone (2); and
   association mean raw `Delta C_40` by failed zone (2).

Every coordinate first reduces worlds, states, or state-variant pairs inside
each replicate exactly as defined below; the twenty replicate values form its
rows. For a family with replicate row vector `d_i` and population center
`theta`, the twenty row vectors are prospectively assumed iid and exactly
centrally symmetric as complete vectors about `theta`. This is a constitutive
claim-limiting model assumption, not a consequence of independence, a property
assessed from realized rows, or a gate that can be accepted after seeing data.

For candidate null center `theta_0`, form residual rows `r_i=d_i-theta_0`. For
each coordinate use `T_j=sqrt(20)*mean(r_.j)/sd(r_.j)`, where `sd` is the
ordinary sample standard deviation with divisor `19`. Set `T_j=0` when mean and
standard deviation are both zero and to signed infinity when standard deviation
is zero but mean is nonzero. Enumerate all `2^20` row-sign vectors, applying one
common sign to every coordinate in a row. The two-sided family statistic is
`max_j |T_j|`; tail equality is included. The confidence set contains every
`theta_0` not rejected at the family alpha, and coordinate intervals are exact
projections of that closed set. The held-out efficacy family is inverted once at
`alpha=.05` for superiority and once at `alpha=.10` for equivalence. The
competence and validity/mechanism families are inverted only at `alpha=.05`.
No bootstrap, seed-level
t test, world pooling, asymptotic substitution, or data-selected family is
allowed. Every inferential claim is conditional on this exact symmetry model.

The `U_rec>=0.75` competence floors, physical-viability rates, and component-
support rates are descriptive finite-panel point gates, not additional
confidence coordinates. For a validation floor, average worlds inside each
replicate for the named arm, size, and failed-zone cell, then average the twenty
replicate means equally. For viability, form one world indicator, average worlds
inside replicate and failed-zone stratum, then average replicate rates equally.
For support, average all deterministic conclusion decision-state indicators
inside replicate, learned arm, and failed-zone stratum, then average replicate
fractions equally. No world pooling or alternate reduction is permitted.

## Prospective validity and mechanism gates

All forty-second viability, action-sensitivity, and association diagnostics use
only decision states at `t in {0,20,40,60,80}`. The `t=100` action remains in
every complete `U_rec` rollout but is excluded from those diagnostic
denominators; no reward-bearing state or tape exists beyond `t=120`.

On the treatment-blind `t=0` post-failure clone, physical viability enumerates
every legal first matching, simulates it on the common realized tape to `t=20`,
then enumerates every legal second matching in its reached state. A world is
viable iff some legal pair produces nonzero acknowledged failed-zone delivery
at a physical second before `t=40` without reserve or exclusivity violation.
This calculation selects no world and uses no learner or comparator action.

For action sensitivity, use deterministic diagnostic continuation
`kappa_diag`: the exact prehistory matching law is reapplied to the current
post-event public state and legal roster, with no future tape or failure-label
access. At each supported deterministic L-RDA conclusion state and each legal
current matching `X`, execute `X` for twenty seconds, apply `kappa_diag` at the
next boundary, and simulate to `t+40` on the common tape. Let `C_40(X)` be raw
unique delivered data-seconds. The state is action-sensitive iff
`max_X C_40(X)-min_X C_40(X)>=6`; fewer than two legal current matchings counts
as not sensitive and remains in the denominator. For each replicate and failed-
zone stratum, the denominator for both action sensitivity and permutation
opportunity is every supported deterministic L-RDA conclusion state at these
five epochs. The action-sensitivity numerator is the number satisfying the
registered `C_40` threshold; the permutation-opportunity numerator is the
number with at least one registered block of size at least two and complete row
mappings.

An association-opportunity state is a supported deterministic L-RDA conclusion
state in the registered diagnostic epochs having a permutation block of size at
least two and complete row mappings. For every such state and each of eight
derangements, compare the unpermuted and deranged immediate actions. At `t+20`
both paths use ordinary frozen deterministic L-RDA in their respectively reached
states, then terminate at `t+40` on the common tape. State-variant pairs have
equal weight within replicate. Thus the association denominator is every pair
`(association-opportunity state,variant k)` for `k in {0,...,7}`. For both
action sensitivity and association,

```text
C_40(pi;s_t) = integral_t^(t+40) [a_1^pi(u)+a_2^pi(u)] du.
```

If a replicate validation cell has no supported DIRECT decisions, its residual-
selection and executed-residual-change entries are both zero. If a replicate
failed-zone stratum has no supported L-RDA diagnostic states, its action-
sensitivity and permutation-opportunity entries are both zero. If it has no
association state-variant pairs, its association matching-change and mean
`Delta C_40` entries are both zero. These numeric zeros enter the registered
`20 x 16` validity/mechanism matrix and the corresponding gate fails. No
replicate, state, world, variant, or denominator is omitted, replaced, or topped
up.

A positive L-RDA branch requires all of the following separately in each failed-
zone stratum when stated:

1. **Integrity and exclusivity:** exact event order, clearance object,
   one-session/one-volume and transparent serial-relay law, deconflicted transit,
   common worlds, legal masks, target-role matching, `D_past`, utility, row
   mappings, and complete activity block all conform. No collision, reserve, or
   duplicate-data violation occurs.
2. **Physical viability and headroom:** the equal-replicate point viability rate
   is at least `0.90`. This establishes reachable recovery opportunity; the
   action-sensitivity gate separately requires nontrivial choice headroom.
3. **Arm-specific component support:** for both L-RDA and DIRECT-SET, the equal-
   replicate supported-state fraction is at least `0.95` in each failed-zone
   stratum.
4. **Learned competence:** all eight training-competence coordinates have
   simultaneous 95% lower bounds strictly above `delta_rec`, and each learned
   arm's equal-replicate validation point mean is at least `0.75` for every
   training size and failed-zone cell.
5. **Strict-containing executed capacity use:** in each of the four validation
   size-by-failed-zone cells, the simultaneous 95% lower bounds for both
   `I_select` and `I_executed_change` are strictly above `0.10`. Thus the
   residual branch must be selected and must actually change the executed
   action on the same supported decisions. Empty supported denominators use the
   registered zero-row law and fail.
6. **Fixed competence:** FIXED-FH's equal-replicate validation point mean is at
   least `0.75` for every training size and failed-zone cell.
7. **Action sensitivity:** the simultaneous 95% lower bound for the registered
   action-sensitive-state rate is strictly above `0.25` in each failed-zone
   stratum.
8. **Permutation opportunity:** the simultaneous 95% lower bound for the
   opportunity-state rate is strictly above `0.50` in each failed-zone stratum.
9. **Association sensitivity:** the simultaneous 95% lower bound for immediate
   matching-change rate is strictly above `0.25`, and the simultaneous 95%
   lower bound for mean
   `Delta C_40=C_40(unpermuted)-C_40(deranged)` is strictly above six raw unique
   delivered data-seconds, in each failed-zone stratum.

All forty-second quantities are diagnostic only. Full-rollout
`Better(L,PERMUTE)` remains separately necessary.

No gate may be repaired after activity by adding worlds, states, variants,
training, checkpoints, margins, mappings, or alternative comparators.

## Exhaustive retain/delete outcome map

Apply the following map only after the complete activity block exists. The words
retain and delete concern this exact target/mechanism at the registered budget
and claim boundary; they are not portfolio allocations.

First apply the validity map in order:

1. **Delete invalid target/object.** If independent domain facts contradict the
   service-volume, clearance, transparent serial-relay, single-chain/session, or
   deconflicted-transit law, or integrity, exclusivity, or activity validity
   fails, delete this target-exclusive object. Make no algorithm claim and do
   not replace the law with a mask.
2. **Delete nonidentifying physical discriminator.** If physical viability,
   either arm's component support, or action sensitivity fails, delete this exact
   experiment as a discriminator. Make no claim that learned or fixed recovery
   is absent.
3. **Delete the four-way comparison for comparator failure.** If DIRECT or
   FIXED competence fails, or DIRECT strict-containing executed residual use
   fails,
   L-RDA cannot be retained against those comparators. Report only valid
   descriptive rows; do not weaken or replace a comparator.
4. **Delete L-RDA for treatment incompetence.** If L-RDA competence fails,
   delete L-RDA-specific value. If competent DIRECT is Better than competent
   FIXED in all three populations, retain only the broad learned-set hypothesis;
   if FIXED is Equivalent to or Better than DIRECT in all three, retain only
   fixed sufficiency; otherwise report a mixed finite result.
5. **Delete the state-row association mechanism.** If permutation opportunity
   or association sensitivity fails, or `Better(L,PERMUTE)` fails in any of the
   three populations, delete L-RDA's registered row/recipient mechanism. Apply
   the same DIRECT-versus-FIXED submap from branch 4; the remaining L contrasts
   are descriptive only.

If every validity and competence gate passes, apply the first efficacy branch:

6. **Retain bounded L-RDA mechanism.** Retain only if
   `Better(L,DIRECT)`, `Better(L,FIXED)`, and `Better(L,PERMUTE)` all hold in the
   aggregate and separately for failures of zone 1 and zone 2. This is the sole
   positive L-RDA branch.
7. **Delete L-RDA; retain broad learned-set hypothesis.** If branch 6 fails but
   `Better(DIRECT,FIXED)` holds in all three populations, delete L-RDA-specific
   value and retain only a future hypothesis that broad set-conditioned learning
   has target value. No successor is authorized automatically.
8. **Delete learned target mechanism; fixed control sufficient.** If branch 6
   fails and FIXED is Equivalent to or Better than both learned arms in all
   three populations, delete learned recovery value for this object at the
   registered budget. This does not claim global optimality of FIXED-FH.
9. **Delete robust L-RDA claim; mixed finite result.** Every other valid complete
   pattern—including one-zone-only superiority, an interval crossing a margin,
   L-RDA beating one comparator but not all, conflicting directional contrasts,
   or aggregate/stratum disagreement—deletes the exact robust L-RDA mechanism.
   Report only registered contrasts; do not search a checkpoint, threshold,
   roster, utility, inference family, or fixed controller.

No outcome reopens immutable B4, authorizes a partial substitute, or creates an
automatic empirical successor.

## Maximum claim and strongest alternative

If and only if branch 6 is reached, the maximum claim is:

> Conditional on the registered iid centrally symmetric replicate-row model and
> the exact single-aperture/single-session, transparent serial-relay,
> deconflicted-transit, and physical-clearance target law,
> one frozen shared
> permutation-equivariant L-RDA bidder trained only after executor loss at active
> rosters `N=3,5` achieved a material increase in acknowledged two-zone recovery
> utility at post-loss `N=7` relative separately to a competent strictly
> containing and executively residual-using DIRECT-SET learner, the registered
> deployable full-horizon fixed
> controller, and the exact same-checkpoint whole-row reassociation intervention,
> separately for each failed zone and in aggregate. The registered opportunity and
> forty-second cuts additionally support only that complete learned bid rows
> were useful when associated with their originating physical UAV records.

Because DIRECT-SET contains L-RDA, this is finite-budget inductive-bias or
trainability evidence, not superior expressivity. The strongest alternative is
that a capacity-one target collapses to ordinary physical matching and any
advantage comes from pruning/regularizing the exploration distribution, while
surplus `N=7` reserves make recovery easier. The within-`N=7` paired comparisons,
failed-zone strata, competent fixed controller, containing learner, and
association cut limit but do not eliminate that package-level explanation.

No result establishes arbitrary-`N` scaling, repeated or endogenous churn,
benefit when multiple executors or viewpoints are valuable, a globally optimal
fixed baseline, robustness to another inference/initialization/optimizer/budget,
decentralized control, communication-loss behavior outside the modeled relay,
continuous flight dynamics, real-hardware performance, UAV safety, deployment,
or another target.

## Indivisible activity block

Question-relevant activity begins only when one atomic manifest contains all of:

1. twenty initial and final L-RDA and DIRECT checkpoints and complete optimizer
   states;
2. all registered training-support states and learned latent-action identities;
3. complete `N=3,5` initial/final validation panels and competence/executed-
   residual-use rows;
4. all 128 `N=7` conclusion worlds per replicate with common prehistory and
   exogenous tapes;
5. complete L-RDA, DIRECT, FIXED-FH, and eight PERMUTE full-rollout rows;
6. every physical state, clearance state, cumulative-demand field, mask,
   matching, sparsemax support, branch identity, bid-row mapping, acquisition,
   delivery, utility, and reserve-integrity record needed by the outcome map;
7. viability, component-support, action-sensitivity, permutation-opportunity,
   allocation-change, forty-second association, and obstruction-toggle
   descriptive rows;
8. every `A_fix`, `X_20`, `X_40`, exact FIXED-FH expectation, canonical tie,
   and backward-induction record needed to reproduce the fixed action;
9. the complete `20 x 12`, `20 x 8`, and `20 x 16` simultaneous-inference
   matrices, all point-gate reductions, and the prospectively accepted symmetry
   declaration; and
10. the immutable card, treatment identities, model/optimizer law, counter
   namespaces, and machine-coordinate binding manifest.

Before that boundary, a build, unit test, dry run, partial arm, partial world,
checkpoint, solver output, or diagnostic is not a treatment observation. After
it, no missing scientific item may be added and no treatment condition may be
changed. Unchanged-science engineering repair before activity remains CM work.

## Definition-only CM handoff

After same-conversation Pro closure and EM intake, CM is asked only to assess:

- whether the physical target, event order, finite state, masks, common matching,
  utility, observation, learned arms, FIXED-FH, PERMUTE, inference, gates, and
  atomic activity block are statically bindable and observable;
- whether DIRECT contains L-RDA exactly and strictly without illegal-action or
  information advantage;
- whether the single-aperture/terminal law, transparent serial relay,
  deconflicted transit law, and static action-value witness are representable
  without reward leakage or artificial exclusivity; and
- full prospective engineering, training, validation, conclusion,
  full-horizon-expectation, sign-enumeration, wall-time, memory, storage, and
  technical-acceptance cost, including the dominant uncertainty.

CM must not inspect or construct source, run a build/test/probe, bind a coordinate,
create a lease, train, evaluate, or compute. Missing implementation is cost, not
a scientific stop. Any meaning-changing ambiguity returns to this EM.

## External-Pro mathematical-closure request

This section is a review instruction, not a treatment condition. Review this
entire complete revision independently for mathematical and causal closure. The
revision-03 ruling found the conditional capacity-one premise defensible and the
prior zero-support PPO defect resolved, but required four complete binding
families: serial transparent relay plus deconflicted transit; a literal free-
agent, route, handover, tick, legality, ETA, margin, token, and history law;
canonical complete-command serialization; and executed DIRECT residual use plus
numeric empty-denominator rows. Revision 04 incorporates those four families
together without changing any already-closed treatment or panel condition.

Audit the conditional physical capacity-one and serial-relay premise,
deconflicted transit, exact clock/route/handover/history process, failure-zone
strata, complete observation and tensor law, command serialization, strict
stochastic-containment witness, executed-residual-use gate, full-horizon fixed
controller, training treatment, arm-specific support, exact simultaneous
families and empty-row laws, point reductions, diagnostics, claim ceiling, and
exhaustive outcome map. Return `VERDICT: CLOSED` only if this exact composite
has no remaining outcome-changing mathematical or causal ambiguity. Otherwise
return `VERDICT: REVISION_REQUIRED`, naming each defect, its consequence, and
the smallest complete replacement. Do not assess code, host availability,
engineering feasibility, runtime cost, portfolio priority, or another direction.
