# VQFP-FERL r04 generator, policy and analyzer manifest

```text
owner=direction:voronoi_quadrature_field_policy
object=VQFP-FIXED-EFFORT-RIDGELINE-SAMPLING-DEFINITION
revision=VQFP-FERL-SCIENCE-20260821-04
manifest=VQFP-FERL-R04-GENERATOR-ANALYZER-1
status=prospective_definition_only
```

This manifest is a required nonselectable ordered restatement of the complete
r04 science card. It adds no science-bearing choice, cannot override the card,
and does not authorize or describe a code implementation. Any contradiction is
a pre-activity invalidity returned to the EM.

## 1. Index and ordering conventions

```text
seed block b=0,...,23
episode tick t=0,...,63
evaluation episode e=0,...,127
physical agent rank i=1,...,N
mode order m=0:SENSE, 1:RELAY
joint action coordinate order=(s_1,r_1,s_2,r_2,...,s_N,r_N)
layout order=IID,CLUSTER
registered N order=4,6,8,12
held-out N order=6,12
endpoint order=U,D90,R
```

All lexicographic, neighbor and cyclic operations use physical rank before the
opaque-handle permutation. Array storage order has no scientific meaning.

## 2. Logical random-tape contract

Exact production lattices are

```text
Q_x=3517578215424000,
Q_E=52776558133248.
```

Each seed block has one future 256-bit `M_b`. The exact address record and raw
word are

```text
A=VQFPFERL04|b=DD|p=P|N=DD|l=L|e=DDDDDDDD|t=DDD|
  s=SSSS|a=HHHHHHHH|d=HHHHHHHH
R(A)=uint64_BE(SHA256(M_b || 0x00 || UTF8(A))[0:8]),
U(A)=(R(A)+1/2)/2^64 as an exact rational.
```

The record contains no displayed line break. Field ranges, sentinel values,
stream tags `GAPS,HNDL,MU00,VEL0,SIGN,LINK,INIT,CELL,MBAT,AFER,AFRE,ANOP`,
entity meanings and INIT tensor ordinals are exactly those in the card.
Unbiased bounded integers reject words at or above
`floor(2^64/k)*k`. Gamma draws are correctly rounded binary64 generalized
inverse CDF values at exact rational `U`. There is no mutable PRNG state.

- Geometry, handles, plume, sign and link words are arm-free and common.
- Common tensors use the same INIT addresses in all learned arms.
- Learned-arm action tags are disjoint.
- An intact/reassociated pair reuses the same complete action-address vector.
- Worker/batch order must leave every word, certified transform and applied
  effort count bit-identical.

All trainable/physical floating values are canonical binary64. Exact dyadic
superaccumulators precede reductions; no fast math, contraction or
reassociation is permitted. Every named transcendental/special function must
be correctly rounded with a certificate. Uncertified output fails validity.

The 24 seed blocks are fresh and disjoint from prior VQFP objects. This manifest
defines their statistical/address relationship, not numerical run coordinates.

## 3. Reset and physical generator

For one `(b,phase,cell,episode)`:

1. Draw `N+1` certified Gamma weights and apportion the exact floor plus
   remaining spatial quanta into positive `GAP_j` counts; compute rational
   `g,x,b,C,v` exactly.
2. Draw one addressed unbiased Fisher-Yates opaque-handle permutation.
3. Draw the two initial centers uniformly over their registered spatial-grid
   ranges, exact lattice velocities, independent signs and link-phase count.
4. Set every `B_i(0)=0`, every learned GRU state to zero, and every own/present-
   neighbor previous-action coordinate to zero.
5. For an absent neighbor, set its seven content coordinates and length port to
   zero and its boundary bit to one.

At tick `t`:

1. Construct `p_t,H_t,gradient_mass,high_gradient_length` by exact rational
   piecewise-linear arithmetic and `link` by the certified binary64 integral.
2. Construct actor/critic inputs.
3. Produce one simultaneous integer count vector summing exactly to `Q_E`.
4. Convert named rational ratios once and compute the canonical binary64
   coverage, acquisition, unserved length, delivery, backlog and reward.
5. Record endpoint components, policy-mean support fields and event coverage.
6. Apply the independent tick-32 sign multiplier only when `t=32`, then perform
   the exact one-reflection position/velocity recurrence for `t+1`.
7. Store realized actions as the next tick's previous-action coordinates.

The tick-63 action and endpoint components are included. `mu(64)` and `B(64)`
may be retained for arithmetic checks but create no tick-64 event or action.

## 4. Exact actor tensor map

For each physical agent define seven length-free content coordinates

```text
c_i=[gradient_mass_i/v_i,
     B_i,
     link_i,
     previous_s_i/E_total,
     previous_r_i/E_total,
     N/12,
     t/63].
```

For any record slot `(c,boundary)`, use one shared encoder

```text
E(c,b)=tanh(W2*tanh(W1*[c;b]+a1)+a2),
W1 shape=(64,8), W2 shape=(64,64).
```

For agent `i`, let absent-neighbor content be the registered zeros and define

```text
self_i = E(c_i,0),
msg_i  = E(c_predecessor,b_left)+E(c_successor,b_right),
u_i    = concat(self_i,msg_i),                    # length 128
h_i(t) = GRU_64(u_i,h_i(t-1)).
```

The GRU is exactly

```text
z=sigmoid(W_z*u+U_z*h_prev+b_z),
r=sigmoid(W_r*u+U_r*h_prev+b_r),
h_tilde=tanh(W_h*u+U_h*(r elementwise_mul h_prev)+b_h),
h=(1-z) elementwise_mul h_prev + z elementwise_mul h_tilde.
```

Base logits are

```text
q_i=W_q*h_i+b_q, shape(q_i)=2.
```

Let the arm-specific supplied lengths be `lambda_j`: true `v_j` for intact
measure-bearing arms, `1/N` for every present record in NO-MEASURE, or
`v_(P_e(j))` under reassociation. Define absent length ports as zero and

```text
ell_i=[log(lambda_i),
       b_left,(1-b_left)*log(lambda_left),
       b_right,(1-b_right)*log(lambda_right)].

rho_i=W_rho*concat(h_i,ell_i)+b_rho, shape(rho_i)=2.
```

Every `W_rho` and `b_rho` element is initialized to exact zero. The factor and
arm logits are

```text
factor_i=log(lambda_i),
FERL:   logits_i=factor_i+q_i+0*rho_i,
FREE:   logits_i=factor_i+q_i+rho_i,
NO_PORT logits_i=log(1/N)+q_i+rho_i.
```

The scalar factor broadcasts to both modes. Softmax is over the flattened joint
coordinate order. Compute it in binary256 and correctly round every `pi` to
binary64; any zero, nonfinite or underflowed share is a numeric validity failure
with no clamp. This map contains no base-route length path. For each slot,
obtain the arm-tagged midpoint `U`, certified binary64 inverse-Gamma value at
shape `64*pi`, and latent binary64 share. Convert exact dyadic Gamma ratios to
`Q_E` integer counts by floor plus largest fractional remainders, with physical-
coordinate ties ascending. Applied effort is `count/(5*Q_E)` and previous-
action content uses the applied count ratio. PPO retains latent shares and uses
the registered continuous-Dirichlet working density/entropy; the finite sampler
and applied counts carry no exact continuous-Dirichlet marginal claim.

## 5. Centralized training critic

At tick `t`, critic-only per-agent input is

```text
d_i=concat(c_i,
           log(v_i),
           high_gradient_length_i/v_i,
           x_i).
```

The critic uses

```text
k_i=tanh(K2*tanh(K1*d_i+k1)+k2),  width 64,
k_bar=(1/N)*sum_i k_i,
V=w_V*concat(k_bar,N/12,t/63)+b_V.
```

It receives true current physical quantities, never future plume motion or arm
identity. It is absent at evaluation and no critic coordinate reaches actor
forward execution. Its true-measure values nevertheless affect finite-training
GAE/advantages and hence PPO policy-gradient coefficients in every learned arm.
The critic route is common and matched across FERL, FREE and NO_PORT. Therefore
NO_PORT removes actor-forward/actor-execution length access only; it does not
remove true measure from centralized training.

## 6. Initialization and arm matching

Every non-residual affine or GRU matrix uses Xavier uniform with gain one:

```text
W_ab ~ Uniform[-sqrt(6/(fan_in+fan_out)),
                +sqrt(6/(fan_in+fan_out))].
```

All biases are zero. The same seed-block draws initialize every common tensor
of FERL, FREE and NO_PORT. Residual-output tensors are then overwritten with
exact zeros in all three arms. FERL executes the residual affine map but
multiplies its output and gradient by zero; its zero-weight-decay optimizer slots
remain registered.

## 7. PPO update equations

One update has 2,048 joint decision ticks from 32 complete episodes. With
terminal value zero, compute

```text
delta_t=r_t+0.99*V_(t+1)-V_t,
A_t=sum_(l>=0) (0.99*0.95)^l * delta_(t+l),
G_t=A_t+V_t.
```

Standardize `A` once over all 2,048 ticks with the population variance and
epsilon `1e-8`. Freeze old joint log likelihoods. For a minibatch `M`,

```text
ratio_t=exp(log p_theta(action_t|history_t)-log p_old(action_t|history_t)),
L_policy=-mean_M min(ratio_t*Ahat_t,
                     clip(ratio_t,0.8,1.2)*Ahat_t),
L_value=mean_M (V_theta(t)-G_t)^2,
L_entropy=mean_M registered_Dirichlet_working_entropy(64*pi_t),
L_total=L_policy+0.5*L_value-0.01*L_entropy.
```

Each epoch uses a frozen optimizer-order shuffle of all 32 complete episode
indices, partitions that order into four minibatches of eight complete episodes,
preserves tick order, recomputes hidden states from zero and backpropagates
through all 64 ticks.
AdamW takes one step per minibatch. Four epochs therefore produce 16 optimizer
steps per PPO update and 9,600 steps over 600 updates. Gradient clipping is the
global Euclidean norm over all trainable actor/critic tensors before each step.

There is no value clipping, KL stop, learning-rate schedule, reward/value/
observation normalization, auxiliary loss, burn-in, hidden-state carry between
episodes or omitted terminal transition.

### Certified deterministic controls

EQUAL emits exactly `Q_E/(2N)` counts in every slot. ANALYTIC enumerates
conceptually the finite set of nonnegative integer `2N`-vectors summing to
`Q_E` and minimizes the canonical binary64 current-state objective. Its output
is the lexicographically largest count vector among all exact objective-bit
ties. The solver must emit, and an independent checker must verify, a global
lower-bound/exclusion certificate for the complete unvisited lattice. Missing
certification is `INVALID_OR_INCOMPLETE/reason=ANALYTIC_CERTIFICATE`; a local or
tolerance-based candidate is never substituted.

## 8. Closed-loop reassociation algorithm

For checkpoint arm `A in {FERL,FREE}` and evaluation episode `e`, start from the
same physical reset, zero backlog, zero GRU state and same arm-specific action
uniforms as intact `A`. Define `P_e` from episode parity.

At every tick:

1. Construct true content `c_i` from the intervention trajectory's current
   backlog/previous actions and the common exogenous field/link tape.
2. Substitute `lambda_j=v_(P_e(j))` at the fixed factor and every present own or
   neighbor residual-length port.
3. Produce the intervened action with the same raw action uniforms as intact.
4. Apply it to the true physical `v_j`, update physical backlog and recurrent
   state recursively, and continue.

Do not copy intact backlog, previous actions, actor hidden state or action after
tick zero. Do not alter physical cells, exogenous fields, boundary tokens or
service equations.

## 9. Endpoint analyzer

For every episode retain:

```text
U numerator, U denominator, U ratio,
R delivered numerator, R offered denominator, R ratio,
all event tuples (front,cell,entry tick),
entry-tick-inclusive cumulative coverage,
completion tick or censor flag,
raw delay, cap, normalized delay.
```

For one seed/cell/arm, compute `U_seed` and `R_seed` as the arithmetic means of
128 episode ratios. Pool all event delays. If `M>0`, apply nearest rank at
`ceil(0.90*M)` with no interpolation or averaging of adjacent order statistics.
If `M=0`, store `D90_seed=1`, `d90_storage_sentinel=true` and
`event_sufficient_seed=false`. For `M>0`, store
`d90_storage_sentinel=false` and `event_sufficient_seed=(M>=40)`.

The `M=0` sentinel and any real D90 with `M<40` are retained only to totalize
the atomic record and 180-vector. They cannot enter an interpreted D90
predicate. Compute `EVENT_SUFFICIENT` as the conjunction `M>=40` for every one
of 24 seeds and every registered `N`-by-layout cell. Because event counts are
action-independent, this gate is common across arms. Evaluate it immediately
after validity and return `ENDPOINT_NONANSWERABLE`, `reason=EVENT_COUNT`, before
any interpreted D90 use when false.

## 10. Support analyzer

For each of 8,192 learned-arm ticks, compute `a_i,d,S,Rmode` from policy mean
`pi`. Count the two exact predicates. The integer thresholds are 4,096 and
6,554. Store both counts for each seed. An arm/cell pass is the integer count of
passing seeds `>=20`.

## 11. Master inference manifest

The 180 ordered sample-vector entries are:

1. entries 1-84: held-out cells in `(N,layout,endpoint,comparison)` order using
   the science card's seven comparison order;
2. entries 85-108: FERL and FREE versus EQUAL at training `N`, ordered
   `(arm,N,layout,endpoint)`;
3. entries 109-132: NO_PORT versus EQUAL across every registered cell, ordered
   `(N,layout,endpoint)`;
4. entries 133-156: `C_A`, ordered `(arm,N,layout)`; and
5. entries 157-180: `Q_A`, in the same order.

Promote each binary64 seed value exactly to a dyadic rational. Compute the mean
and unbiased variance exactly; correctly round the square root and interval
arithmetic to 256-significand-bit base-2 round-to-nearest-ties-even. Let

```text
c_180=correctly_rounded_binary256_t_quantile(7199/7200,df=23),
halfwidth=c_180*sample_sd/sqrt(24).
```

The quantile carries a directed CDF-bracket certificate. Reverse intervals are
exact `[-U,-L]` binary256 pairs. Margins are exact rationals promoted to
binary256; strict and non-strict predicates are literal comparisons with no
epsilon. Failure of any rounding/certificate is a validity failure with
`reason=NUMERIC_CONTRACT`.

These are fixed nominal Bonferroni-adjusted Student intervals. No exact finite-
sample marginal or 0.95 familywise coverage is asserted. All predicate
endpoints in the science card come from this registered nominal simultaneous
Student criterion. For a reverse contrast negate and swap endpoints exactly.

## 12. Branch evaluation algorithm

Evaluate the science card's 15 decisions in numerical order and return the
first true predicate:

```text
1  INVALID_OR_INCOMPLETE
2  ENDPOINT_NONANSWERABLE / EVENT_COUNT
3  NO_PHYSICAL_OPPORTUNITY
4  NO_ALLOCATION_ACTION_SUPPORT
5  FERL_TARGET_HARM
6  LEARNED_OR_CONTAINING_COMPETENCE_FAILURE
7  ENDPOINT_NONANSWERABLE / INTERIORITY_OR_FERL_FREE_PRECISION
8  HETEROGENEOUS_FERL_FREE_EFFECTS
9  FERL_TREATMENT_SPECIFIC_VALUE
10 FREE_MEASURE_SUPERIORITY
11 EXPLICIT_MEASURE_PORT_ONLY_VALUE
12 GENERIC_ALLOCATION_VALUE_WITHOUT_MEASURE_SPECIFICITY
13 ALLOCATION_VALUE_WITH_MEASURE_SPECIFICITY_UNRESOLVED
14 TARGET_SPECIFIC_NO_MATERIALITY
15 UNRESOLVED_VALID_EVIDENCE
```

Decision 2 preempts every interpreted D90 use. In decision 6, inspect every
failed `NH_X(A,EQUAL,c)`: report exact arm/endpoint/cell harm if the registered
`HARM_X(A,EQUAL,c)` predicate is true, otherwise report non-harm unresolved.
The disposition remains competence failure unless decision 5 already matched.

Decision 1 emits `NUMERIC_CONTRACT` for any spatial/effort/address/transform or
binary256 certificate failure and `ANALYTIC_CERTIFICATE` for any uncertified
global control action. No approximate or tolerance-based branch is evaluated.

Every `exists N*` requires the same named `N*` across both layouts and all
conjuncts in that branch. “Every held-out cell” means the Cartesian product
`{6,12} x {IID,CLUSTER}`. All interval predicates use the nominal Student
criterion. Every NO_PORT comparison is conditional on the common measure-
informed critic and concerns actor-forward/actor-execution ports only. No
missing, sentinel-protected, nonanswerable or failed-prerequisite interval may
be treated as zero, equivalent, non-harmful or generic.

The analyzer emits the branch label and reason code, every prerequisite Boolean
with its underlying count/interval, all decision-6 harm annotations, the common
qualifying `N*` when applicable, every raw seed vector and a statement of which
downstream contrasts are descriptive. It performs no automatic successor launch
or family deletion.

## 13. Required atomic lifecycle

One conclusion-bearing panel is complete only when all 24 seed blocks, three
intact learned arms, two reassociated evaluations, two deterministic controls,
all eight registered evaluation cells, raw endpoint/event/support records,
event counts, D90 sentinel/sufficiency flags, the global event gate, every
address/transform/correct-rounding/global-control certificate and all 180
inference vectors plus binary256 certificates exist under the one frozen
composite. Partial panels may be
checkpointed atomically but are not interpreted. Resume may complete missing
technical work only without changing any scientific coordinate. Sentinel-
protected or event-insufficient D90 values remain noninferential.
