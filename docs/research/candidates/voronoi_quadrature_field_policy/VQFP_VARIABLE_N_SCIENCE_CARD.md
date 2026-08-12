# Voronoi Quadrature Field Policy B1 science card

Owner: `direction:voronoi_quadrature_field_policy` Explorer Manager
Candidate: `VQFP-VN-FAMILY-CUT-01`
Treatment: `VQFP-B1-PERIODIC-LOCAL-MEASURE-v1`
Exact prospective revision: `VQFP-B1-MATH-CLOSURE-20260812-01`
Hard complexity contract: `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`

## Decision first

VQFP is a promising and identifiable direct variable-`N` candidate on a
restricted class of spatial-integral tasks. It hard-codes the physical measure
represented by each sender into a bounded-degree message aggregation. The
candidate is not representationally unique: the matched learned-attention
comparator contains the exact Voronoi rule at initialization and may learn the
same or a better rule. A positive result can therefore establish only a useful
finite-budget inductive bias under the frozen roster and geometry shifts, not
an impossibility result for learned attention.

This document freezes a prospective B1 object. No VQFP parameter update,
question-relevant run, checkpoint, or result exists. Before production, this
exact revision must receive `CLOSED` from its dedicated same-direction ChatGPT
External Pro conversation and that ruling must be intaken by this owner. Any
accepted science-bearing correction creates a new complete revision and must
return to the same Pro conversation. CM separately owns implementation
conformance and technical acceptance; Root owns production sequencing.

The additional Gemini conversation is an independent innovator only. It may
suggest counterexamples, mechanisms, scenario families, controls, or bridges,
but it cannot supply mathematical closure, result convergence, technical
acceptance, or portfolio selection.

## Question and causal object

Can one parameter-shared policy trained once at `N in {6,10}` use correctly
associated periodic-Voronoi cell lengths in local messages to improve either
mean task performance or lower-tail robustness at untouched held-out
`N in {4,14}` over an information-, graph-, recurrence-, parameter-, sample-,
optimizer-, communication-, and work-matched learned sparse-attention policy?

The primary contrast is intact `VQFP - N-AWARE-DENSITY-KNN-ATTN` on two held-out
start regimes. The proposed mechanism is narrower: binding each cell-average
field sample to its own physical cell length prevents irregular agent density
from redefining spatial mass. A frozen-checkpoint `VOLUME-REASSOC` edge cut and
proximal quadrature/action measurements test whether that binding contributes
to any package advantage.

The direct variable axis is roster size. Each arm is one shared
parameterization across all training and evaluation sizes. There is no
per-`N` head, normalization refit, threshold, checkpoint choice, fine-tuning,
or evaluation-time adaptation. B1 changes `N` only between episodes and makes
no in-episode join, exit, failure, or churn claim.

## Periodic field-service host

### Domain, positions, and cell measure

The physical domain is the unit circle `T=[0,1)`. An episode has `H=32`
simultaneous team decisions. Agent positions are stationary within an episode.
After cyclically ordering the positions, define

```text
g_i = (x_(i+1)-x_i) mod 1
v_i = (g_(i-1)+g_i)/2.
```

`C_i` is the periodic Voronoi interval bounded by the two adjacent midpoints.
Consequently `v_i=length(C_i)>0` and `sum_i v_i=1` exactly in real arithmetic.
The cyclic predecessor and successor are the only external message neighbors;
including self, every receiver aggregates exactly three distinct sender tuples
for every registered `N`. The external graph degree is therefore two and does
not change at `N=4`.

For every episode, first draw positive raw gaps and then apply a fixed floor:

```text
raw_i ~ Gamma(alpha,1) independently
g_i = 0.05/N + 0.95*raw_i/sum_j raw_j.
```

Use `alpha=1` for `IID` starts and `alpha=0.25` for `CLUSTER` starts. Draw one
uniform rotation on the circle and one independent uniform permutation from
cyclic ranks to opaque environment handles. Neither cyclic rank nor handle is
an actor input. `EQUAL` control starts use `g_i=1/N` plus only the uniform
rotation. There is no rejection sampling, layout search, or fallback layout.

Training samples `N=6` and `N=10` equally and samples `IID` and `CLUSTER`
equally. Primary evaluation crosses `N in {4,6,10,14}` with both `IID` and
`CLUSTER`; only `N in {4,14}` enters the qualification estimands. `EQUAL` and
the constructed `MEASURE-CONFLICT` layout are diagnostic panels only.

### Exogenous physical field

In ordinary `IID`, `CLUSTER`, and heterogeneous `EQUAL` episodes, the demand
density is the following smooth physical field, independent of positions and
actions:

```text
d_t(x) = 0.55
         + 0.25*cos(2*pi*(x-phi_1-omega_1*t))
         + 0.15*cos(4*pi*(x-phi_2-omega_2*t)).
```

`phi_1` and `phi_2` are independent `Uniform[0,1)` draws. Independently,
`omega_1` is uniform on `{-1/128,+1/128}` and `omega_2` is uniform on
`{-1/256,+1/256}`. Thus `d_t(x)` lies in `[0.15,0.95]`. The simulator computes
the exact analytic cell average

```text
s_i(t) = (1/v_i) * integral_(C_i) d_t(x) dx
```

using the periodic sine antiderivative. The registered B1 observation is this
noise-free cell average, not a point sample. Hence

```text
sum_(j in S_i) v_j*s_j(t)
```

is the exact demand mass on the union of receiver `i`'s own, predecessor, and
successor cells. A later point-sensor or noisy-sensor result would be a new
scientific object.

The `MEASURE-CONFLICT` diagnostic uses a `CLUSTER` layout but a stationary field
constructed after the layout:

```text
d_conflict(x) = 0.55
                + 0.30*cos(2*pi*(x-c_max))
                - 0.15*cos(2*pi*(x-c_min)),
```

where `c_max` is the midpoint of the largest Voronoi cell and `c_min` is the
midpoint of the smallest. Ties are resolved by cyclic rank before handle
permutation. This geometry-conditioned field is used only to create an
association-sensitive functional probe; it is not population evidence or part
of the primary return claim. The constant-field null uses `d(x)=0.55`.

### Simultaneous service and cooperative reward

At each tick every agent simultaneously chooses one effort

```text
a_i in {0, 1/2, 1}.
```

For every physical point in cell `C_j`, the local service intensity is

```text
u_j = a_j + 0.5*a_(j-1) + 0.5*a_(j+1).
```

The team reward is

```text
r_t = sum_j v_j*s_j(t)*(1-exp(-u_j))
      - 0.08*sum_i v_i*a_i^2.
```

The exponential saturation makes overlapping neighboring effort redundant;
the physical-volume cost prevents roster size alone from changing the total
cost scale. The same scalar reward is delivered to every agent. Actions do not
alter the next field, positions, graph, or volumes. The drifting exogenous field
still makes the observation history useful, while the absence of action-to-field
feedback keeps B1 focused on spatial aggregation rather than long-horizon
credit.

For reporting only, an exact immediate oracle maximizes `r_t` over the three
efforts on the cyclic width-three factor graph. The ring dynamic program has
constant action width and `O(N*3^3)` time. It is never an actor, training target,
search proposal, observation, or deployment fallback. Since the all-zero action
is legal and demand is strictly positive, `r_t^star>0`. Episode performance is

```text
J_episode = sum_(t=0..31) r_t / sum_(t=0..31) r_t^star.
```

Raw return, service mass, cost, overlap, and each action frequency are also
retained. `J_episode` is the only primary performance scale.

### Observations, timing, and leakage boundary

At tick `t`, before actions, sender `j` exposes the same tuple to both arms:

- current exact cell-average demand `s_j(t)`;
- previous effort, with a zero start token at `t=0`;
- signed periodic displacement and the two adjacent cyclic gaps;
- relative slot `PREV`, `SELF`, or `NEXT`; and
- the current roster size `N` as a receiver context.

The explicit scalar `v_j` is supplied through the registered aggregation-weight
port in both arms. Geometry remains visible, so the learned comparator can
reconstruct or ignore the explicit volume and is not declared incapable. No
actor sees absolute handle, cyclic rank, start-regime label, field phases or
velocities, future field, oracle action/value, evaluation-cell label, or whether
the volume port is intact or cut.

Actions are sampled after all observations and messages are formed. Reward is
then computed from the simultaneous joint action. The next exogenous field is
advanced afterward. Centralized training may use the complete current physical
state in one identical permutation-invariant critic for both arms; critic state
is never routed to the actor.

## Shared policy and the one algorithmic difference

Both arms use one parameter-shared sender/edge encoder, a 64-unit GRU, the same
64-unit actor trunk, the same three-logit categorical head, and the same
centralized critic. The edge encoder emits a value vector `h_ij` and one scalar
residual gate logit `ell_ij`. Its first value coordinate is an immutable raw
pass-through of `s_j`; the remaining coordinates are learned. The residual gate
logit is not appended to either actor input or included inside `h_ij`. Both arms
append the same local represented length, roster size, and receiver-local state.
Tensor widths, forward calls, recurrent state, critic, message bytes, and
nominal parameter count are identical. VQFP carries the same residual-gate
output layer as a zero-gradient unused capacity match; the learned comparator
alone may use that intended extra freedom.

For receiver `i`, let `S_i={i-1,i,i+1}` and `V_i=sum_(j in S_i)v_j`.

### Treatment: VQFP

The treatment fixes the aggregation weights to physical measure:

```text
alpha^V_ij = v_j/V_i
z^V_i = concat(
    V_i*sum_(j in S_i) alpha^V_ij*h_ij,
    V_i,
    N).
```

The raw pass-through coordinate of `z^V_i` is therefore exactly the local
three-cell demand mass. Learned encodings may improve the policy, but they
cannot change the registered base weights.

### Strong comparator: N-AWARE-DENSITY-KNN-ATTN

The comparator uses the identical objects but lets the residual logit change
the aggregation weights:

```text
alpha^L_ij = softmax_(j in S_i)(log(v_j) + ell_ij)
z^L_i = concat(
    V_i*sum_(j in S_i) alpha^L_ij*h_ij,
    V_i,
    N).
```

The residual-gate output layer is initialized to exact zero in both arms.
Consequently the comparator starts at the exact VQFP policy architecture and
can retain it, cancel it through geometry-dependent logits, or learn a
content-dependent alternative. For any setting of the common encoder, GRU,
actor and critic, setting every `ell_ij=0` makes the comparator's actor input
identical to VQFP's. The comparator therefore contains the complete VQFP actor
class as a subfamily. A positive VQFP contrast is evidence for the hard
physical-measure constraint as a finite-budget regularizer; it cannot mean the
comparator lacked the correct operator.

The baseline name contains `KNN` only to denote its fixed cyclic nearest-
neighbor graph. It performs no neighbor search after the once-per-episode
cyclic sort and has no dense pairwise attention.

## Frozen-checkpoint mechanism cut and controls

`VOLUME-REASSOC` is evaluation-only and never retrained. For each receiver's
ordered triplet `(PREV,SELF,NEXT)`, replace only the explicit volume operands at
the aggregation-weight port by a nonidentity cyclic shift while leaving sender
messages, positions, gaps, identities, recurrent states, masks, and all random
streams unchanged. Even-numbered evaluation episodes use

```text
(v_PREV,v_SELF,v_NEXT) -> (v_NEXT,v_PREV,v_SELF),
```

and odd-numbered episodes use the inverse shift. The same shift is used for
both arms, all ticks, all channels, and every paired checkpoint. It preserves
the exact incoming volume multiset, `V_i`, graph, message multiset,
communication, and work. It is a functional edge intervention on the explicit
binding, not an on-manifold physical intervention: volumes remain determined by
the unchanged positions, and the learned comparator may reconstruct them from
geometry.

Evaluation proceeds in this order on the same frozen bank:

1. one-step replay records intact and cut local mass estimates and action
   distributions before any recurrent divergence;
2. closed-loop intact and cut rollouts reuse the same exogenous fields and
   action uniforms; and
3. the following structural controls are applied without model selection.

Structural controls are:

- `WHOLE-TUPLE-PERMUTE`: permute each complete `(volume,message,relative
  metadata)` record; a set aggregation must be invariant;
- `EQUAL-VOLUME`: reassociation at equispaced starts must be invariant;
- `CONSTANT-FIELD`: the raw physical-mass coordinate must be invariant because
  the volume multiset and its sum are preserved;
- `IDENTITY-RESTORE`: restoring the original association must restore the
  original outputs; and
- `EXPLICIT-PORT-BYPASS`: report how much the learned comparator reconstructs
  the intact weighting from unchanged geometry when its explicit volume port is
  cut. This is a diagnostic, not a validity failure.

For deterministic control outputs, ordinary conformance means

```text
abs(x-y) <= 1e-8 + 1e-6*max(abs(x),abs(y)).
```

This is a stable numerical tolerance, not bit identity or an experimental
effect threshold.

## Training and evaluation freeze

### Learning law

Training is synchronous on-policy actor-critic. The joint policy factorizes
conditionally across active agents. For one team transition its joint log
probability is the sum of all active-agent categorical log probabilities. The
actor loss uses that joint log probability times one shared team GAE advantage;
team transitions, not agent rows, are averaged. There is no importance reuse,
clipping, per-agent ratio, entropy bonus, auxiliary reward, imitation target,
oracle target, or held-out validation loss.

The common values are:

```text
gamma=0.99
GAE lambda=0.95
Adam learning rate=3e-4
gradient norm cap=1.0
256 team transitions per update
one optimizer pass per batch
375 updates = 96,000 team transitions per arm/seed
```

The critic squared-error coefficient is `0.5`. Every batch contains equal
numbers of `N=6` and `N=10` episodes and equal numbers of `IID` and `CLUSTER`
episodes, using a fixed balanced counter-keyed schedule. The final update-375
checkpoint is the only evaluated checkpoint. There is no early stopping,
checkpoint selection, hyperparameter sweep, warm start, or retraining after an
evaluation.

Use these 12 paired training seeds:

```text
2101, 2111, 2129, 2141, 2153, 2161,
2179, 2203, 2213, 2237, 2251, 2267.
```

Within a seed, arms share initial values for every common parameter, all
environment draws, and inverse-CDF action uniforms. Residual-logit output
weights and bias start at zero. Random namespaces include arm only where the
mathematical distributions differ; data and evaluation banks do not.

### Evaluation counts

Every final checkpoint receives:

- 128 intact episodes in every `N in {4,6,10,14}` by
  `{IID,CLUSTER}` cell;
- the same 128 held-out episodes in every `N in {4,14}` by
  `{IID,CLUSTER}` cell under `VOLUME-REASSOC`;
- 128 intact and 128 reassociated `MEASURE-CONFLICT` episodes at each held-out
  `N`;
- 128 intact `CLUSTER` episodes at each held-out `N` with observation-only
  Gaussian noise `epsilon_i,t ~ Normal(0,0.15^2)`, clipped to `[0,1]`, while
  reward continues to use the true field; and
- 128 one-step states at each held-out `N` for each structural null/control.

The noisy panel is a fixed falsification boundary, not a primary robustness
endpoint. It tests the precise counterexample that a large physical cell can
give a noisy isolated sensor excessive influence. It cannot expand the claim
above the registered noise-free cell-average observation; a clear reversal
narrows any successor to a reliability-tempered measure with a new Pro-closed
science object.

Evaluation draws use counter namespaces derived from `(training_seed,
panel,N,regime,episode,tick)` and are identical across arms and cuts. Held-out
rows are never exposed to training, checkpoint choice, normalization fitting,
or threshold selection.

## Estimands, margins, and inference

Let `mu_A(n,z)` be a paired training seed's mean intact `J_episode` for arm
`A` in roster/start cell `(n,z)`. Let `CVaR10_A(n,z)` be the empirical lower
10% mean, computed as the average of the lowest 12 observations plus `0.8` times
the thirteenth-lowest observation, divided by `12.8`.

For paired training seed `s`, define

```text
P_s = min over n in {4,14}, z in {IID,CLUSTER}
      [mu_VQFP,s(n,z)-mu_LEARNED,s(n,z)]

R_s = min over n in {4,14}, z in {IID,CLUSTER}
      [CVaR10_VQFP,s(n,z)-CVaR10_LEARNED,s(n,z)].
```

`P` is the worst-cell task-performance effect and `R` is the worst-cell
lower-tail robustness effect. Across the 12 independent paired training seeds,
form one-sided Student-`t` 97.5% lower confidence bounds for `mean(P_s)` and
`mean(R_s)`. The Bonferroni split gives familywise one-sided alpha at most
`0.05`. B1 meets the direct algorithm value criterion if either lower bound is
strictly above the preregistered material margin `0.03`. Report all eight
intact `N`-by-regime cell means, all held-out cell differences, and both bounds
regardless of sign.

Also form one-sided Student-`t` 97.5% upper confidence bounds for `mean(P_s)`
and `mean(R_s)`. This second Bonferroni pair is used only by the frozen family-
delete branch; it cannot convert a nonqualifying result into a positive one.

The descriptive held-out-specific interaction is

```text
Gamma_s = mean_(n in {4,14},z)[VQFP-LEARNED]
          - mean_(n in {6,10},z)[VQFP-LEARNED].
```

Positive direct value without positive `Gamma` supports one shared policy that
works better at the tested held-out sizes, but not a benefit caused specifically
by crossing the training-size boundary.

For receiver `i`, define the true local physical mass

```text
Q_i = sum_(j in S_i) v_j*s_j
```

and let `Qhat_A,c,i` be the actor's registered raw mass coordinate under intact
or cut port `c`. On the held-out `MEASURE-CONFLICT` bank define normalized
quadrature error `E_A,c,s(n)` as the mean over that seed's registered episodes,
ticks and receivers of `|Qhat_A,c,i-Q_i|/V_i`. Let
`mu^MC_A,c,s(n)` be that same seed's mean normalized closed-loop return on the
`MEASURE-CONFLICT` bank. Define

```text
K_s = min_(n in {4,14}) [E_VQFP,cut,s(n)-E_VQFP,intact,s(n)]

M_s = min_(n in {4,14})
      { [mu^MC_VQFP,intact,s(n)-mu^MC_LEARNED,intact,s(n)]
        - [mu^MC_VQFP,cut,s(n)-mu^MC_LEARNED,cut,s(n)] }.
```

Form separate one-sided 97.5% paired-`t` lower bounds. Binding is supported as
a contributor only if the lower bound for `K` exceeds `0.02` normalized field
density, the lower bound for `M` exceeds `0.02` normalized return, and the mean
one-step total-variation distance between intact and cut VQFP action
distributions exceeds `0.05`. Also report the paired association between the
increase in raw mass error and the action/return change; it is descriptive and
cannot rescue a failed gate.

A direct value result that passes `P` or `R` but fails any binding requirement
is a package-level result with no quadrature-mechanism attribution.

## Activity, support, and result availability

Question-relevant scientific activity begins when the first optimizer update is
applied to either arm after its first complete registered 256-team-transition
batch. Source construction, zero-gradient forwards, shape checks, and oracle
enumeration before that point are engineering work and do not start activity.
After activity begins, no observation, action, DGP, algorithm, comparator,
count, seed, margin, inference, or branch in this revision may be changed.

The direct `P` endpoint is available only when all of the following hold:

1. all 12 paired final checkpoints and every registered primary episode exist;
2. one unchanged checkpoint per arm/seed serves every `N`, regime, cut, and
   falsification panel;
3. the comparator's `ell=0` setting reproduces the intact VQFP aggregate under
   the ordinary numerical tolerance before training;
4. the exact volume identities `v_i>0` and `sum_i v_i=1` hold within the same
   tolerance, with no clipped or duplicated neighbor;
5. in every held-out primary cell, the learned comparator's mean normalized
   return is at most `0.94`, leaving at least twice the `0.03` material margin
   below the exact immediate-oracle ceiling; and
6. no held-out observation influenced training, normalization, checkpoint,
   threshold, correction, or rerun choice.

The direct `R` endpoint replaces item 5 by the same requirement on the learned
comparator's empirical `CVaR10`. An endpoint without its registered headroom is
unavailable because that surface cannot express twice the target improvement;
the other endpoint remains usable. Oracle headroom is never itself positive
treatment evidence.

Binding attribution additionally requires all of the following:

1. median per-episode coefficient of variation of `v_i` is at least `0.25` in
   every held-out `CLUSTER` and `MEASURE-CONFLICT` cell;
2. in each held-out `MEASURE-CONFLICT` cell, the mean receiver-level absolute
   difference between volume-weighted and unweighted raw field averages is at
   least `0.08`;
3. VQFP uses at least two of the three effort actions with frequency at least
   `0.05` in every held-out `MEASURE-CONFLICT` cell; and
4. all whole-tuple, equal-volume, constant-raw-field, and identity-restoration
   controls satisfy their stated meanings.

The registered `K`, `M`, and action-TV gates must also pass for positive binding
attribution. Missing binding support does not invalidate an otherwise available
direct package result.

If any item is absent, its affected value or mechanism conclusion is
unavailable, not positive or negative. An implementation defect that leaves the
science unchanged returns to CM. A science-bearing repair requires a new frozen
revision and same-conversation Pro ruling. Partial seed sets, subsets chosen by
outcome, post-hoc margins, and extra training are forbidden.

## Complexity and resource ceiling

The claimed deployment path is sparse:

- one cyclic sort per episode costs `O(N log N)` time and `O(N)` memory;
- Voronoi lengths and the `3N` self/neighbor message edges cost `O(N)`;
- encoder, GRU, actor, and action sampling cost `O(N)` per tick; and
- no dense pairwise attention, rollout search, tree search, beam search, or
  adaptive candidate library exists.

The evaluation-only ring oracle costs `O(N*3^3)` per tick and is not part of the
algorithm. Hypothetical candidate trajectories per controller episode are zero.
The `MEASURE-CONFLICT` field is constructed directly, not selected by search.

The frozen transition accounting is:

```text
training: 12 seeds * 2 arms * 96,000 = 2,304,000 team transitions
ordinary intact evaluation: 786,432 team transitions
held-out ordinary cut evaluation: 393,216 team transitions
conflict intact+cut evaluation: 393,216 team transitions
noisy falsification evaluation: 196,608 team transitions
one-step controls: 4 controls * 12 seeds * 2 arms * 2 held-out N
                   * 128 states = 24,576 team states
total environment transitions/states: at most 4,098,048.
```

The complete formal iteration must use at most one local CPU process, 2 GiB of
RAM, eight cumulative wall-clock hours, 250,000 trainable parameters per arm,
and the counts above. CM must record a zero-compute complexity/resource bound
before launch. Implementation optimization that preserves this object is CM
work. Reducing counts, changing the graph, adding a dense path, or exceeding
the formal cap requires a new scientific revision or no launch; resource
failure produces no treatment conclusion.

## Strongest alternative and complete interpretation branches

The strongest positive-result alternative is not missing information in the
baseline. It is that the fixed base measure supplies a favorable optimization
or regularization bias under limited training, while a sufficiently optimized
learned gate could recover or improve the same law. A second alternative is
that volume is merely a compact density/gap cue and not a physically causal
quadrature operand. The exact-rule initialization, comparator expressibility,
reassociation interaction, proximal raw-mass error, and structural controls
bound but do not eliminate those explanations.

Interpret every complete valid outcome as follows:

- **Direct value plus binding:** `P` or `R` clears `0.03`, and all `K`, `M`,
  action-sensitivity, support, and null-control requirements pass. Conclude that
  on this finite noise-free periodic field-service panel, one shared VQFP policy
  improved the registered held-out-size value endpoint over the stronger free
  gate and that correct explicit volume-message binding contributed. Activate
  the 2-D second surface.
- **Direct value without binding:** `P` or `R` clears `0.03`, but a binding gate
  fails. Conclude a package-level held-out advantage only. Do not attribute it
  to quadrature and do not transfer the mechanism to UAV work; the next
  discriminator must isolate the surviving non-quadrature difference.
- **Binding without direct value:** the cut behaves as predicted but neither
  `P` nor `R` clears `0.03`. Correct association affects computation but has not
  earned algorithm investment on this host. Do not rescue it with mechanism
  diagnostics alone.
- **Comparator match or reverse:** neither direct value endpoint qualifies, or
  the learned comparator is materially better. The hard physical-measure
  constraint has no registered value advantage; a reverse result supports the
  possibility that free reliability/content weighting is preferable.
- **Family delete:** if all direct-value validity requirements and both
  endpoint-specific oracle-headroom requirements hold, and the Bonferroni
  one-sided 97.5% upper confidence bounds for both `mean(P_s)` and `mean(R_s)`
  are strictly below `0.03`, delete the hard-Voronoi-base family on the
  service-field -> 2-D plume -> UAV path. It has excluded the registered
  practically material worst-held-out-cell advantage against a comparator that
  contains its exact rule. Do not delete the mathematical quadrature identity
  or infer failure on a different sensing model.
- **Statistically indeterminate:** if a valid endpoint's interval crosses its
  `0.03` decision margin and the family-delete rule does not hold, report no
  family conclusion. Do not weaken margins or automatically add seeds or a
  rerun.
- **Only training-size advantage:** a benefit at `N in {6,10}` without the
  held-out worst-cell result is not variable-`N` value.
- **Cluster-only effect:** report irregular-sampling support only; do not claim a
  general roster-size effect.
- **Noisy isolated-cell reversal:** narrow the observation claim to exact or
  sufficiently high-SNR cell averages. Any reliability-tempered successor is a
  new treatment requiring its own Pro closure.
- **Invalid or incomplete support:** withhold only the affected conclusion. Do
  not reinterpret missing data as treatment evidence and do not select a
  favorable subset.

No B1 outcome proves natural mediation because `VOLUME-REASSOC` is an
off-manifold computational edge intervention. No result proves asymptotic
superiority, learned-attention impossibility, arbitrary-`N` robustness,
in-episode membership robustness, point-sensor quadrature, safety, general
plume tracking, or UAV performance.

## Maximum claim ceiling

The maximum positive statement is:

> One parameter-shared VQFP policy trained at `N={6,10}` improved the
> preregistered worst held-out `N={4,14}` mean-return or lower-tail endpoint on
> the finite noise-free periodic field-service host over a matched free gate
> initialized at the exact volume rule; controlled frozen-checkpoint edge cuts
> support correct local volume-message binding as a contributor if and only if
> the registered mechanism gates also pass.

That statement is conditional on the observed start regimes, fields, seeds,
budget, local three-cell receptive field, exact cell-average sensor, and
inference above. The comparator remains capable of learning the same operator.

## Second surface and UAV bridge

The second surface is a bounded 2-D plume-uncertainty service simulator. It is
activated only by the `Direct value plus binding` branch. Replace periodic cell
lengths by clipped Voronoi areas in a fixed surveillance polygon. Recompute the
tessellation after motion or roster changes in `O(N log N)`. Use a Delaunay or
geometric neighbor graph pruned to maximum degree eight, and define the reward
over exactly the union of cells represented once by each receiver's registered
receptive field. Compare the same hard physical-area base measure with the same
representationally capable free gate and repeat an area-to-sender reassociation
cut, whole-tuple invariance, equal-area null, and proximal integral/action
measurements. This is a new science card and receives its own same-conversation
Pro closure before production.

The UAV-simulator mapping is explicit:

- varying `N`: one shared policy is trained on two fleet sizes and evaluated
  unchanged on at least one held-out size; later join/exit claims require real
  membership events not present in B1;
- observation: each UAV supplies its clipped-cell average of plume
  concentration or posterior uncertainty, cell area, relative geometry,
  previous sensing/relay effort, and local neighbor messages;
- action: shared high-level `DWELL / TRACK / RELAY-EFFORT` choices drive a
  common low-level flight controller and identical safety masks;
- coordination mechanism: physical-area-weighted sparse aggregation prevents
  dense clusters from multiplying represented mission area;
- failure mode: a learned gate may overcount clusters under roster shift, while
  hard area weighting may overtrust a large noisy or unresolved cell; and
- measured benefit: integrated plume-uncertainty reduction or mission return,
  lower-tail dropout robustness, communication/work, collision/safety facts,
  and proximal area-integral error against the matched free gate.

Only a qualifying 2-D result selects a concrete UAV simulator campaign. A real
UAV study would additionally require calibrated sensor error, wind/plume model
shift, localization/tessellation error, link loss, low-level control and safety
acceptance, and a separately authorized controlled protocol.

## Exact owner handoff

The direction-local scientific object is exactly revision
`VQFP-B1-MATH-CLOSURE-20260812-01` in this file. Root may establish two separate
same-direction external conversations from the prepared requesters, with no
answer sharing: ChatGPT External Pro for authoritative mathematical closure and
Gemini for additive divergent innovation. Production remains forbidden until
Pro returns `CLOSED`, this owner intakes that exact ruling, and CM accepts source
conformance plus the zero-compute complexity bound.

CM's eventual result packet must state whether question-relevant activity began,
whether a complete valid result exists, the `P/R/K/M` endpoints and bounds, all
support/control facts, noisy-panel behavior, anomalies, resource facts, and what
remains unknown. Root returns that packet to this owner for interpretation, then
the same Pro conversation receives the bounded result-convergence question.
