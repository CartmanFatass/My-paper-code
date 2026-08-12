# Voronoi Quadrature Field Policy B1 science card

Owner: `direction:voronoi_quadrature_field_policy` Explorer Manager
Candidate: `VQFP-VN-FAMILY-CUT-01`
Treatment: `VQFP-B1-PERIODIC-LOCAL-MEASURE-v1`
Exact Pro-closed prospective revision: `VQFP-B1-MATH-CLOSURE-20260812-04`
Superseded Pro-reviewed revisions:
`VQFP-B1-MATH-CLOSURE-20260812-02`,
`VQFP-B1-MATH-CLOSURE-20260812-03`
Superseded unsent revision: `VQFP-B1-MATH-CLOSURE-20260812-01`
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
question-relevant treatment run, checkpoint, or treatment result exists. The
dedicated same-direction ChatGPT External Pro returned literal `CLOSED` on this
exact revision, with zero science-bearing defects, and this owner has intaken
that complete ruling. The mathematical/causal closure boundary is therefore
complete. Any later science-bearing correction creates a new complete revision
and must return to the same Pro conversation. CM separately owns implementation
conformance and technical acceptance; Root owns production sequencing.

The additional Gemini conversation is an independent innovator only. It may
suggest counterexamples, mechanisms, scenario families, controls, or bridges,
but it cannot supply mathematical closure, result convergence, technical
acceptance, or portfolio selection.

The dedicated VQFP ChatGPT External Pro returned `REVISION_REQUIRED` with five
science-bearing defects for prospective revision `-02`; revision `-03`
substantively closed all five, but the same Pro conversation returned
`REVISION_REQUIRED` with one residual internal contradiction. This owner accepts
all six rulings. Revision `-03` froze the complete recurrent learning law;
requires both VQFP self-attenuation and architecture-by-cut attenuation in
`M`; fixes oracle-headroom and binding-support units; supplies the exact state
law and output vector for all four sampled structural controls; and fixes
`Gamma`, noisy reversal, material reverse, endpoint tradeoff, and successor
precedence. Revision `-04` makes the sole remaining prospective correction: the
registered `U_P/U_R` upper-bound pair is explicitly used by both
`MATERIAL_REVERSE` classifications and family deletion, eliminating the
contradictory word `only`. It changes no statistic, confidence level,
multiplicity family, threshold, branch ordering, sample, seed, panel, or compute
count. Revisions `-02` and `-03` are superseded and must never be resent;
revision `-01` produced no provider turn. No optimizer update or other question-
relevant activity has begun. The DGP, arms, architecture, parameter count,
seeds, samples, transition/state ceiling, direct margins, family-delete margin,
and narrow claim ceiling otherwise remain unchanged.

The same Pro conversation then naturally completed exact revision `-04` with
`CLOSURE_AUTHORITY_DECISION=CLOSED`, `RESULT_BLIND=true`, and
`SCIENCE_BEARING_DEFECT_COUNT=0`. It confirmed that the sole upper-bound-use
correction is sufficient and that every previously passed component remains
complete. This owner accepts that ruling without changing the scientific
object.

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
search proposal, observation, or deployment fallback. The legal all-`1/2`
joint action gives `u_j=1` everywhere and reward at least
`0.15*(1-exp(-1))-0.02>0`; hence `r_t^star>0`. Episode performance is

```text
J_episode = sum_(t=0..31) r_t / sum_(t=0..31) r_t^star.
```

Raw return, service mass, cost, overlap, and each action frequency are also
retained. `J_episode` is the only primary performance scale.

### Observations, timing, and leakage boundary

At tick `t`, before actions, sender `j` exposes the same tuple to both arms:

- current exact cell-average demand `s_j(t)`;
- previous effort as one four-way token in `{START,0,1/2,1}`, with `START`
  used only at `t=0`;
- signed periodic displacement and the two adjacent cyclic gaps;
- relative slot `PREV`, `SELF`, or `NEXT`; and
- the fixed scalar `N/16` as a receiver context.

The explicit scalar `v_j` is supplied through the registered aggregation-weight
port in both arms. Geometry remains visible, so the learned comparator can
reconstruct or ignore the explicit volume and is not declared incapable. No
actor sees absolute handle, cyclic rank, start-regime label, field phases or
velocities, future field, oracle action/value, evaluation-cell label, or whether
the volume port is intact or cut.

Actions are sampled after all observations and messages are formed. Reward is
then computed from the simultaneous joint action. The next exogenous field is
advanced afterward. Centralized training uses exactly the identical
permutation-invariant critic frozen below for both arms; critic state is never
routed to the actor.

## Shared policy and the one algorithmic difference

Both arms use one parameter-shared sender/edge encoder, a 64-unit GRU, the same
64-unit actor trunk, the same three-logit categorical head, and the same
centralized critic. These widths and structures are science-bearing because the
claim compares finite-budget inductive biases. CM may choose only numerically
equivalent tensor layouts, batching, stable elementary forms, serialization,
and ordinary implementation details that leave the following function,
parameter count, initialization and work unchanged.

For edge `(i,j)`, define the exact 11-vector

```text
e_ij = concat(
    s_j,
    one_hot(previous_effort_j in {START,0,1/2,1}),
    wrap(x_j-x_i) in [-1/2,1/2),
    g_(j-1), g_j,
    one_hot(relative_slot in {PREV,SELF,NEXT})).
```

The common edge encoder is

```text
q_ij = tanh(Linear(11,64)(e_ij))
w_ij = tanh(Linear(64,31)(q_ij))
h_ij = concat(s_j,w_ij)                         # exactly 32 values
ell_ij = Linear(64,1)(q_ij).
```

The first coordinate of `h_ij` is therefore an immutable raw pass-through. The
residual gate `ell_ij` is not included in `h_ij`, appended to an actor input, or
available by any route except the learned comparator's weighting equation.
Both arms execute the gate head. VQFP carries it as a zero-gradient unused
capacity/work match; the comparator may train and use it.

After the arm-specific aggregation below, the exact recurrent actor input is

```text
x_i^actor = concat(
    weighted_message_32,
    V_i,
    N/16,
    s_i,
    one_hot(previous_effort_i in {START,0,1/2,1}))  # exactly 39 values.
```

One 64-unit reset-after GRU with separate input and recurrent bias vectors
consumes `x_i^actor`. For prior state `u`, its update is exactly

```text
r = sigmoid(W_ir @ x + b_ir + W_hr @ u + b_hr)
z = sigmoid(W_iz @ x + b_iz + W_hz @ u + b_hz)
n = tanh(W_in @ x + b_in + r .* (W_hn @ u + b_hn))
u_next = (1-z) .* n + z .* u.
```

Here `@` is matrix-vector multiplication and `.*` is elementwise
multiplication. This is the PyTorch-style reset-after candidate equation,
not the alternative `W_hn @ (r .* u)` convention. The hidden state is exactly zero
at episode start and is reset only at episode end. The current `u_next` passes
through `tanh(Linear(64,64))` and then `Linear(64,3)` to the categorical effort
logits.
There is no layer normalization, batch normalization, dropout, attention layer,
second message-passing layer, skip route, or separate `N`-specific parameter.

The exact centralized critic is identical across arms and is never routed to
the actor. Each agent record is

```text
c_i = concat(sin(2*pi*x_i), cos(2*pi*x_i), v_i, s_i,
             one_hot(previous_effort_i in {START,0,1/2,1}))  # 8 values.
```

It applies `tanh(Linear(8,64))`, then `tanh(Linear(64,64))`, and physical-
measure pools `p=sum_i v_i*cembed_i`. The global critic input is

```text
concat(p, N/16, t/31,
       sin(2*pi*theta_1(t)), cos(2*pi*theta_1(t)),
       sin(2*pi*theta_2(t)), cos(2*pi*theta_2(t)),
       128*omega_1, 256*omega_2)                 # exactly 72 values,
```

where `theta_m(t)=(phi_m+omega_m*t) mod 1`. This input passes through
`tanh(Linear(72,64))`, `tanh(Linear(64,64))`, and `Linear(64,1)`. The critic may
use these centralized exogenous-state facts only during training.

Every non-gate linear weight uses Xavier-uniform initialization with gain one
and zero bias. Each of `W_ir`, `W_iz`, and `W_in` is initialized independently
by Xavier-uniform gain one. Each of the three 64-by-64 recurrent matrices
`W_hr`, `W_hz`, and `W_hn` is initialized independently by an orthogonal draw
with gain one. All six GRU bias vectors are zero. The residual-gate weight and
bias are exactly zero. Paired arms receive identical initial values for every
common parameter.
Including the executed gate head and centralized critic, each arm has exactly
40,996 nominal parameters. The VQFP gate parameters remain zero-gradient but
are retained in that count.

```text
edge/value/gate: (11*64+64) + (64*31+31) + (64*1+1) = 2,848
GRU:             3*64*39 + 3*64*64 + 6*64           = 20,160
actor trunk/head:(64*64+64) + (64*3+3)               = 4,355
critic embed:    (8*64+64) + (64*64+64)              = 4,736
critic global:   (72*64+64) + (64*64+64) + (64+1)   = 8,897
total:                                                     40,996.
```

For receiver `i`, let `S_i={i-1,i,i+1}` and `V_i=sum_(j in S_i)v_j`.

### Treatment: VQFP

The treatment fixes the aggregation weights to physical measure:

```text
alpha^V_ij = v_j/V_i
z^V_i = concat(
    V_i*sum_(j in S_i) alpha^V_ij*h_ij,
    V_i,
    N/16).
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
    N/16).
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

The first four named items below are independently sampled structural-control
panels. The fifth is a derived diagnostic on an already registered bank and is
not another panel:

- `WHOLE-TUPLE-PERMUTE`: permute each complete `(volume,message,relative
  metadata)` record; a set aggregation must be invariant;
- `EQUAL-VOLUME`: reassociation at equispaced starts must be invariant;
- `CONSTANT-FIELD`: the raw physical-mass coordinate must be invariant because
  the volume multiset and its sum are preserved;
- `IDENTITY-RESTORE`: restoring the original association must restore the
  original outputs; and
- `EXPLICIT-PORT-BYPASS`: report how much the learned comparator reconstructs
  the intact weighting from unchanged geometry when its explicit volume port is
  cut. It reuses, without any new state, episode, environment transition, or
  provider-selected subset, the learned-comparator intact/cut one-step records
  already produced for every tick and receiver of the held-out
  `MEASURE-CONFLICT` bank. It is a diagnostic, not a fifth structural-control
  panel and not a validity gate.

The exact sampled-control state law is prospective and common to both arms.
For each training seed, held-out `N`, and one of the four sampled control names,
generate exactly 128 independent tick-0 pre-action states once under a control-
specific counter namespace, then evaluate that identical bank in both arms.
Each arm evaluation is one registered one-step team state in the resource
account. The actor GRU state is zero and every previous-effort token is `START`.

`WHOLE-TUPLE-PERMUTE` and `IDENTITY-RESTORE` use independently sampled
`MEASURE-CONFLICT` layouts and fields. `EQUAL-VOLUME` uses `EQUAL` layouts with
the ordinary heterogeneous field. `CONSTANT-FIELD` uses `CLUSTER` layouts with
`d(x)=0.55`. For even state indices use the forward cyclic triplet shift and
for odd state indices use its inverse.

`WHOLE-TUPLE-PERMUTE` moves each complete sender record as a unit, including
its explicit volume operand, edge/message values, signed displacement,
adjacent gaps, relative-slot metadata, and residual logit. Metadata is not
recomputed for the destination array position. `EQUAL-VOLUME` and
`CONSTANT-FIELD` apply the registered volume-only `VOLUME-REASSOC` shift.
`IDENTITY-RESTORE` applies that shift and then its exact inverse before
evaluation.

Using the same stored actor hidden state, compare these registered outputs:

```text
WHOLE-TUPLE-PERMUTE: (weighted_message_32, actor_logits_3)
EQUAL-VOLUME:        (weighted_message_32, actor_logits_3)
CONSTANT-FIELD:      raw_mass_coordinate only
IDENTITY-RESTORE:    (weighted_message_32, actor_logits_3).
```

For deterministic control outputs, ordinary conformance means

```text
abs(x-y) <= 1e-8 + 1e-6*max(abs(x),abs(y)).
```

This is a stable numerical tolerance, not bit identity or an experimental
effect threshold. Every scalar in the registered output vector is compared
elementwise. A failure in any registered state, seed, arm, or held-out `N`
makes binding attribution unavailable while leaving an otherwise valid direct
package endpoint usable. These are exactly the registered 24,576 one-step team
states; `EXPLICIT-PORT-BYPASS` remains derived and adds no state.

## Training and evaluation freeze

### Learning law

Training is synchronous on-policy actor-critic over complete 32-tick episodes.
Each update batch contains exactly eight complete episodes and therefore
exactly 256 team transitions: two episodes in each of
`(N,regime)={(6,IID),(6,CLUSTER),(10,IID),(10,CLUSTER)}` under the fixed
balanced counter-keyed schedule.

Let `V_t` be the centralized critic output at the pre-action state of tick `t`.
Set `V_32=0` and `A_32=0` at the terminal episode boundary. With `gamma=0.99`,
`lambda=0.95`, and the raw scalar team reward, compute backward for
`t=31,...,0`:

```text
delta_t = r_t + gamma*stop_gradient(V_(t+1))
          - stop_gradient(V_t)
A_t = delta_t + gamma*lambda*A_(t+1)
Y_t = stop_gradient(A_t + V_t).
```

No reward, return, observation, value-target, or advantage normalization,
centering, clipping, or standardization is applied. The joint policy
factorizes conditionally across active agents, with

```text
logp_joint,t = sum_(i=1..N) log pi_i(a_i,t | history_i,t).
```

The exact full-batch loss is

```text
L = mean_over_256_team_transitions [
      -stop_gradient(A_t)*logp_joint,t
      + 0.5*(V_t-Y_t)^2
    ].
```

The actor computation graph is retained through all 32 GRU steps of each
episode. There is no within-episode hidden-state detachment, truncated BPTT,
cross-episode state carry, value clipping, entropy term, auxiliary term,
imitation or oracle target, importance reuse, per-agent ratio, or held-out
validation loss. Team transitions, not agent rows, are averaged.

For each arm, one separate Adam optimizer contains all of that arm's actor and
critic parameters, including the nominal VQFP gate parameters whose
mathematical loss gradient is exactly zero. No optimizer state is shared across
arms. Each optimizer uses:

```text
learning_rate=3e-4
beta1=0.9
beta2=0.999
epsilon=1e-8
weight_decay=0
amsgrad=false
no learning-rate schedule
```

Exactly one full-batch backward pass and one optimizer step occur per update.
Before that step, clip the global L2 norm of all non-`None` parameter gradients
jointly to `1.0`. There is no minibatch subdivision or additional optimizer
step. Exactly 375 updates produce 96,000 team transitions per arm/seed. The
final update-375 checkpoint is the only evaluated checkpoint. There is no
early stopping, checkpoint selection, hyperparameter sweep, warm start, or
retraining after evaluation.

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
- 128 one-step states at each held-out `N` for each of the four independently
  sampled structural controls: `WHOLE-TUPLE-PERMUTE`, `EQUAL-VOLUME`,
  `CONSTANT-FIELD`, and `IDENTITY-RESTORE`.

`EXPLICIT-PORT-BYPASS` consumes no additional state. It is computed from the
learned-comparator outputs already recorded during intact/cut one-step replay of
the 128-by-32-tick `MEASURE-CONFLICT` episodes. Consequently the registered
4,098,048 transition/state ceiling and the four-control term in its accounting
remain exact.

In the noisy `CLUSTER` panel, the `epsilon_i,t` draws are independent across
agents, ticks, episodes, training seeds, and held-out `N` values. The
corresponding draw is paired identically across arms. After addition to the
exact cell average, each observation is clipped to `[0,1]`; reward continues
to use the true field.

The noisy panel is a fixed falsification boundary, not a primary robustness
endpoint. It tests the counterexample that a large physical cell can give a
noisy isolated sensor excessive influence. It cannot expand the claim above
the registered noise-free cell-average observation. Its exact material-
reversal rule and successor precedence are frozen below; it does not identify
largest-cell noise as the causal mediator.

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
and `mean(R_s)`. This second Bonferroni pair is used only by the registered
`MATERIAL_REVERSE` classifications and the frozen family-delete branch below.
It cannot convert a nonqualifying result into a positive one.

The descriptive held-out-specific interaction is

```text
Gamma_s = mean_(n in {4,14},z)[VQFP-LEARNED]
          - mean_(n in {6,10},z)[VQFP-LEARNED].

Gamma = (1/12)*sum_s Gamma_s.
```

`Gamma` is the sole descriptive aggregate. Positive `Gamma` means `Gamma>0`,
negative `Gamma` means `Gamma<0`, and `Gamma=0` is neutral. Report every
`Gamma_s` and `Gamma`; attach no confidence interval or gate. Positive direct
value without positive `Gamma` supports one shared policy that works better at
the tested held-out sizes, but not a benefit caused specifically by crossing
the training-size boundary. Positive `Gamma` remains descriptive and does not
identify that crossing as a causal benefit.

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

D^V_s(n) = mu^MC_VQFP,intact,s(n)-mu^MC_VQFP,cut,s(n)

D^I_s(n) =
    [mu^MC_VQFP,intact,s(n)-mu^MC_LEARNED,intact,s(n)]
  - [mu^MC_VQFP,cut,s(n)-mu^MC_LEARNED,cut,s(n)]

M_s = min_(n in {4,14}) min{D^V_s(n),D^I_s(n)}.
```

Thus `M` requires both material VQFP self-attenuation under reassociation and
material architecture-by-cut attenuation at both held-out roster sizes in the
registered worst-size sense. Comparator improvement under the cut cannot by
itself establish VQFP return contribution.

For exact action and association units, index the 128 registered conflict
episodes by `e`. At every tick and receiver, replay intact and cut VQFP inputs
from the same intact-trajectory pre-input GRU hidden state; neither replay
updates that stored state. Define

```text
dE_s,n,e = mean_(t,i) [
    |Qhat_VQFP,cut,s,n,e,t,i-Q_s,n,e,t,i|/V_s,n,e,i
  - |Qhat_VQFP,intact,s,n,e,t,i-Q_s,n,e,t,i|/V_s,n,e,i]

dTV_s,n,e = mean_(t,i) [
    0.5*sum_(a in {0,1/2,1})
        |pi_VQFP,intact(a)-pi_VQFP,cut(a)|]

dJ_s,n,e = J_VQFP,intact,s,n,e-J_VQFP,cut,s,n,e.
```

The `mean_(t,i)` is equal weight over all `32*N` receiver-ticks in that episode.
The action probabilities are the categorical probabilities before sampling;
common action uniforms do not enter `dTV`. The return difference uses the
paired closed-loop intact and cut episode with the same exogenous field and
action-uniform tape. Define

```text
T_s(n) = mean_(e=1..128) dTV_s,n,e
T_s    = min_(n in {4,14}) T_s(n).
```

Across the 12 independent paired training seeds, form separate one-sided
Student-`t` `98.333333%` lower confidence bounds for `mean(K_s)`, `mean(M_s)`,
and `mean(T_s)`. Their three-way Bonferroni family has one-sided alpha at most
`0.05`. Binding is supported as a contributor only if the respective lower
bounds strictly exceed `0.02` normalized field density, `0.02` normalized
return, and `0.05` total-variation distance. The `M` bound therefore covers
joint VQFP self-attenuation and architecture-by-cut attenuation.

The `EXPLICIT-PORT-BYPASS` diagnostic is exactly

```text
B_s(n) = E_VQFP,cut,s(n)-E_LEARNED,cut,s(n).
```

It uses the same conflict one-step bank already counted above. Positive `B`
means the learned comparator stayed closer than cut VQFP to true mass by using
unchanged geometry or other matched information. Report every `B_s(n)` and its
equal-weight mean across the 24 `(seed,n)` cells; it is not a gate.

Two paired associations are fixed before data. Within every `(seed,n)` cell,
compute Spearman rank correlation across its 128 episode pairs between
`dE_s,n,e` and `dTV_s,n,e`, and separately between `dE_s,n,e` and `dJ_s,n,e`.
Use average ranks for ties. Report all 24 correlations for each association.
For each association, the sole aggregate summary is

```text
tanh(mean_(s,n) atanh(clip(rho_s,n,-1+1e-12,1-1e-12))).
```

If either variable is constant in any cell, that cell's correlation is
`UNDEFINED` and the aggregate summary is unavailable; do not substitute
Pearson correlation, pool receiver-ticks, drop the cell, or select a subgroup.
Both associations are descriptive and cannot rescue a failed `K`, `M`, or `T`
gate.

For the noisy falsification, let `mu^noise_A,s(n)` be the mean of the 128 intact
noisy-panel `J_episode` values and define

```text
D^noise_s = min_(n in {4,14})
              [mu^noise_VQFP,s(n)-mu^noise_LEARNED,s(n)].
```

Across the 12 training seeds form one one-sided Student-`t` 95% upper
confidence bound `U_noise` for `mean(D^noise_s)`. A registered noisy-panel
material reversal occurs if and only if

```text
U_noise < -0.03.
```

This uses the existing normalized-return material margin and no additional
data. It supports only material degradation under this exact clipped iid noise
panel; it does not identify largest-cell noise as the causal mediator. Failure
to meet the rule is not evidence of general noisy-sensor robustness.

A direct value result that passes `P` or `R` but fails any binding requirement
is a package-level result with no quadrature-mechanism attribution.

## Activity, support, and result availability

Question-relevant scientific activity begins when the first optimizer update is
applied to either arm after its first complete registered 256-team-transition
batch. Source construction, zero-gradient forwards, shape checks, and oracle
enumeration before that point are engineering work and do not start activity.
After activity begins, no observation, action, DGP, algorithm, comparator,
count, seed, margin, inference, or branch in this revision may be changed.

For endpoint headroom define, separately in each held-out `(n,z)` cell,

```text
bar_mu_LEARNED(n,z)
  = (1/12)*sum_s mu_LEARNED,s(n,z)

bar_CVaR10_LEARNED(n,z)
  = (1/12)*sum_s CVaR10_LEARNED,s(n,z).
```

The direct `P` endpoint is available only when all of the following hold:

1. all 12 paired final checkpoints and every registered primary episode exist;
2. one unchanged checkpoint per arm/seed serves every `N`, regime, cut, and
   falsification panel;
3. the comparator's `ell=0` setting reproduces the intact VQFP aggregate under
   the ordinary numerical tolerance before training;
4. the exact volume identities `v_i>0` and `sum_i v_i=1` hold within the same
   tolerance, with no clipped or duplicated neighbor;
5. `bar_mu_LEARNED(n,z)<=0.94` in every held-out primary cell, leaving at least
   twice the `0.03` material margin below the exact immediate-oracle ceiling;
   and
6. no held-out observation influenced training, normalization, checkpoint,
   threshold, correction, or rerun choice.

The direct `R` endpoint replaces item 5 by
`bar_CVaR10_LEARNED(n,z)<=0.94` in every held-out cell. An endpoint without its
registered headroom is unavailable because that surface cannot express twice
the target improvement; the other endpoint remains usable. Oracle headroom is
never itself positive treatment evidence.

Binding attribution additionally requires all of the following:

1. for panel `p` equal to `CLUSTER` or `MEASURE-CONFLICT`, define

   ```text
   CV_v(s,n,p,e)
     = sqrt((1/n)*sum_i (v_i-1/n)^2)/(1/n).
   ```

   In every `(s,n,p)` cell, the median across its 128 episodes, using the
   arithmetic mean of the 64th and 65th ordered values, is at least `0.25`;
2. in every held-out `MEASURE-CONFLICT (s,n)` cell, define

   ```text
   D_assoc(s,n)
     = mean_(e=1..128,t=0..31,i=1..n)
         |Q_i/V_i - (1/3)*sum_(j in S_i) s_j|,
   ```

   with equal weight over all `128*32*n` receiver-ticks, and require
   `D_assoc(s,n)>=0.08`;
3. for intact VQFP closed-loop `MEASURE-CONFLICT` rollouts define

   ```text
   f_s,n(a) = [1/(128*32*n)]
              * sum_(e,t,i) 1{a_VQFP,intact,s,n,e,t,i=a}.
   ```

   In every `(s,n)` cell, require at least two actions in `{0,1/2,1}` to have
   `f_s,n(a)>=0.05`. Cut actions, comparator actions, logits, and action
   probabilities do not enter this support frequency; and
4. all whole-tuple, equal-volume, constant-raw-field, and identity-restoration
   controls satisfy their exact registered state/output laws.

The registered `K`, `M`, and `T` gates must also pass for positive binding
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
RAM, eight cumulative wall-clock hours, exactly 40,996 nominal parameters per
arm under the frozen architecture (and therefore below the 250,000 ceiling),
and the counts above. CM must record a zero-compute complexity/resource bound
before launch. Implementation optimization that preserves this object is CM
work. Reducing counts, changing the graph, adding a dense path, changing the
frozen function/parameter count/initialization, or exceeding the formal cap
requires a new scientific revision or no launch; resource failure produces no
treatment conclusion.

## Strongest alternative and complete interpretation branches

The strongest positive-result alternative is not missing information in the
baseline. It is that the fixed base measure supplies a favorable optimization
or regularization bias under limited training, while a sufficiently optimized
learned gate could recover or improve the same law. A second alternative is
that volume is merely a compact density/gap cue and not a physically causal
quadrature operand. The exact-rule initialization, comparator expressibility,
reassociation interaction, proximal raw-mass error, and structural controls
bound but do not eliminate those explanations.

Let `L_P,L_R` be the registered 97.5% lower bounds and `U_P,U_R` the
registered 97.5% upper bounds. For each available endpoint `X in {P,R}` define

```text
POSITIVE_X         iff L_X >  0.03
MATERIAL_REVERSE_X iff U_X < -0.03.
```

A negative point estimate without `MATERIAL_REVERSE_X` is descriptive only.
Classify the direct outcome in this order:

1. **Direct-endpoint tradeoff.** If one endpoint is `POSITIVE` and the other
   available endpoint is `MATERIAL_REVERSE`, report the qualified benefit and
   material harm separately. Do not state an unqualified package advantage and
   do not activate the untempered 2-D surface.
2. **Direct value plus corrected binding.** If at least one endpoint is
   `POSITIVE`, no available endpoint is `MATERIAL_REVERSE`, and all `K`, `M`,
   `T`, support, and structural-null requirements pass, conclude that on this
   finite noise-free host VQFP improved the named held-out endpoint; the
   material VQFP self-attenuation, architecture-by-cut attenuation, mass-error,
   action-sensitivity, support, and structural-null results support correct
   explicit local volume-message binding as a functional contributor. Activate
   the untempered 2-D surface only if there is also no noisy-panel material
   reversal.
3. **Direct value without binding.** If at least one endpoint is `POSITIVE`, no
   available endpoint is `MATERIAL_REVERSE`, but a corrected binding requirement
   fails or is unavailable, conclude a package-level held-out advantage only.
   Do not attribute it to quadrature or transfer the mechanism to UAV work.
4. **Material comparator advantage.** If no direct endpoint is `POSITIVE` and
   at least one available endpoint is `MATERIAL_REVERSE`, describe the
   comparator as materially better only for that named endpoint.
5. **Family delete.** If no endpoint is `POSITIVE` or `MATERIAL_REVERSE`, all
   direct-value validity requirements and both endpoint-specific oracle-
   headroom requirements hold, and `U_P<0.03` and `U_R<0.03`, delete the hard-
   Voronoi-base family on the service-field -> 2-D plume -> UAV path. This
   excludes the registered practically material worst-held-out-cell advantage
   against a comparator containing the exact rule; it does not delete the
   quadrature identity or infer failure for another sensing/task class.
6. **Statistically indeterminate.** If neither a positive nor material-reverse
   rule applies and the family-delete rule does not hold, report no family
   conclusion. Do not weaken margins, add seeds, or rerun automatically.

Apply these nonexclusive interpretation modifiers after the direct class:

- **Binding without direct value:** if corrected binding gates pass but neither
  endpoint is `POSITIVE`, report that correct association affects computation
  but has not earned algorithm investment. It cannot replace or rescue the
  material-reverse, family-delete, or indeterminate direct class.
- **Noisy-panel material reversal:** `U_noise < -0.03` does not invalidate an
  otherwise valid noise-free B1 endpoint, but overrides any untempered 2-D
  activation. State only that the noise-free result does not extend to the
  registered clipped iid noisy-cell-average panel and that any noisy successor
  must test a separately Pro-closed reliability-tempered measure. Do not claim
  largest-cell noise as the mediator.
- **Only training-size or cluster-only pattern:** a benefit only at
  `N in {6,10}` is not variable-`N` value. A result confined to held-out
  `CLUSTER` reports irregular-sampling support only, not a general roster-size
  effect.
- **Invalid or incomplete:** withhold only the affected endpoint or mechanism
  conclusion. Missing data, unavailable associations, resource failure, or
  failed controls cannot be coded as positive, null, reverse, or favorable
  subset evidence.

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
> produced both material VQFP self-attenuation and material architecture-by-cut
> attenuation, together with the registered mass-error, action-sensitivity,
> support, and structural-null results, supporting correct explicit local
> volume-message binding as a functional contributor if and only if every
> corrected mechanism gate passes.

That statement is conditional on the observed start regimes, fields, seeds,
budget, local three-cell receptive field, exact cell-average sensor, and
inference above. The comparator remains capable of learning the same operator.

## Second surface and UAV bridge

The second surface is a bounded 2-D plume-uncertainty service simulator. It is
activated only by the `Direct value plus corrected binding` branch, with no
available material-reverse endpoint and no registered noisy-panel material
reversal. Replace periodic cell
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
`VQFP-B1-MATH-CLOSURE-20260812-04` in this file. The dedicated ChatGPT External
Pro conversation returned literal `CLOSED` on this exact revision, and the
same-direction owner intake is complete at
`docs/research/candidates/voronoi_quadrature_field_policy/VQFP_V4_EXTERNAL_PRO_CLOSED_INTAKE.md`.
The mathematical/causal review boundary is complete; this does not grant
technical acceptance or choose production timing. The unsent `-02` Gemini batch
is superseded and non-transport-ready. Its exact independent `-04` replacement
is frozen blind to every Pro answer at
`temp/sessions/agentify_transport_operator/independent_research_explorer/vqfp_b1_gemini_3_1_pro_extended_innovator_20260812_04/batch.json` and remains
`PREPARED_NOT_SENT`. Root may now relay the exact card and owner handoff to CM
for construction and technical acceptance. Production remains subject to
Root's sequencing and CM acceptance of source conformance plus the zero-compute
complexity bound.

CM's eventual result packet must state whether question-relevant activity began,
whether a complete valid result exists, the `P/R/K/M/T` endpoints and bounds,
`Gamma_s/Gamma`, every `D^V_s(n)/D^I_s(n)`, all support/control facts,
`D^noise_s/U_noise`, endpoint tradeoff/reverse labels, anomalies, resource
facts, and what remains unknown. Root returns that packet to this owner for
interpretation, then the same Pro conversation receives the bounded result-
convergence question.
