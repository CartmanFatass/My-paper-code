# VQFP-FERL r05 generator, policy and analyzer manifest

```text
owner=direction:voronoi_quadrature_field_policy
object=VQFP-FIXED-EFFORT-RIDGELINE-SAMPLING-DEFINITION
revision=VQFP-FERL-SCIENCE-20260821-05
manifest=VQFP-FERL-R05-GENERATOR-ANALYZER-1
status=prospective_definition_only
```

This manifest is a required nonselectable ordered restatement of the complete
r05 science card. It adds no science-bearing choice, cannot override the card,
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
A=VQFPFERL05|b=DD|p=P|N=DD|l=L|e=DDDDDDDD|t=DDD|
  s=SSSS|a=HHHHHHHH|d=HHHHHHHH
R(A)=uint64_BE(SHA256(M_b || 0x00 || UTF8(A))[0:8]),
U(A)=(R(A)+1/2)/2^64 as an exact rational.
```

The record contains no displayed line break. Episode-specific streams use
actual phase/`N`/layout and training `e=32*u+q` or evaluation `e=0..127`.
`N=00,l=X` occurs only for `INIT,CELL,MBAT`. Exact stream coordinates are:

```text
INIT: p=T,N=00,l=X,e=0,t=255,a=random-tensor ordinal,d=row-major element.
CELL: p=T,N=00,l=X,e=u,t=255,a=j,d=rejection attempt.
MBAT: p=T,N=00,l=X,e=u,t=255,a=32*h+j,d=rejection attempt.
GAPS: episode fields,t=255,a=gap index,d=0.
HNDL: episode fields,t=255,a=j,d=rejection attempt.
MU00,VEL0: episode fields,t=255,a=front-1,d=rejection attempt.
SIGN: episode fields,t=032,a=front-1,d=rejection attempt.
LINK: episode fields,t=255,a=0,d=rejection attempt.
AFER,AFRE,ANOP: episode fields,t=actual tick,a=2*(i-1)+m,d=0.
```

Every displayed decimal/hex field is zero-padded to the card's fixed width.
For an unbiased integer in `0,...,k-1`, start `d=0`, reject
`R>=floor(2^64/k)*k`, increment only `d`, and accept `R mod k`. `INIT` uses
`d=row-major element index`; `GAPS` and `AFER`/`AFRE`/`ANOP` direct midpoint
words use `d=0`. Exhaustion after `d=FFFFFFFF` is
`NUMERIC_CONTRACT/REJECTION_COUNTER_EXHAUSTED`; there is no wrap or mutable
PRNG state.

`CELL` starts from `[(04,I)x8,(04,C)x8,(08,I)x8,(08,C)x8]`, shuffles
descending `j=31..1`, and assigns output position `q` to global episode
`32*u+q`. `MBAT` independently starts each epoch from
`[32*u,...,32*u+31]`, shuffles descending `j=31..1`, and partitions four
consecutive groups of eight. `HNDL` starts from physical-rank list `[1,...,N]`
and shuffles descending `j=N-1..1`; final position `i-1` is rank `i`'s handle.
All three use the addressed range `k=j+1`. `MU00`, `VEL0`, `SIGN` and `LINK`
index exactly the ordered finite lists frozen in the card. Gamma draws are
correctly rounded binary64 generalized inverse-CDF values at exact rational
midpoints.

- Geometry, handles, plume, sign and link words are arm-free and common.
- Common tensors use the same INIT addresses in all learned arms.
- Learned-arm action tags are disjoint.
- An intact/reassociated pair reuses the same complete action-address vector.
- Worker/batch order must leave every word, certified transform and applied
  effort count bit-identical.

All trainable/physical floating values are canonical binary64. Exact dyadic
superaccumulators precede reductions; no fast math, contraction or
reassociation is permitted. Every named transcendental/special function must
be correctly rounded with a certificate. Q2 softmax uses only the card's
unbounded-exponent binary256S; inference binary256 is unchanged. Every stored
Q2 numerical zero is canonical binary64 `+0`. Uncertified output fails
validity.

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
5. Record endpoint components, rounded-softmax target-share support fields and
   event coverage.
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
`v_(P_e(j))` under reassociation. Define length coordinates piecewise and do
not evaluate an absent logarithm:

```text
L_self=CR64(log(lambda_i)),
L_left=0 if b_left=1, else CR64(log(lambda_left)),
L_right=0 if b_right=1, else CR64(log(lambda_right)),
ell_i=[L_self,b_left,L_left,b_right,L_right].

rho_i=W_rho*concat(h_i,ell_i)+b_rho, shape(rho_i)=2.
```

The identical piecewise rule applies intact, under no-port substitution and
under reassociation; all evaluated self/present lengths are strictly positive.

Every `W_rho` and `b_rho` element is initialized to exact zero. The factor and
arm logits are

```text
factor_i=log(lambda_i),
FERL:   logits_i=factor_i+q_i+0*rho_i,
FREE:   logits_i=factor_i+q_i+rho_i,
NO_PORT logits_i=log(1/N)+q_i+rho_i.
```

The scalar factor broadcasts to both modes. Flatten logits in joint-coordinate
order and compute exactly

```text
M=the earliest numerical binary64 maximum,
x_j=RN256S(exact(logit_j)-exact(M)),
w_j=CR256S(exp(x_j)),
W=RN256S(exact_dyadic_sum_j w_j),
p_j=RN256S(w_j/W),
tilde_pi_j=RN64(p_j).
```

`binary256S` is the card's Q2-local unbounded-exponent, 256-significand-bit
format and does not alter inference binary256. All binary256S rounds/divisions
and exponentials carry directed certificates.
Every target share must be finite, normal and positive; there is no clamp or
renormalization. Set `alpha_j=64*tilde_pi_j` and actual
`alpha_0=exact_dyadic_sum alpha`. For each slot obtain its arm-tagged midpoint
and certified positive binary64 Gamma-CDF-inverse value. Exact Gamma ratios define
exact-simplex `z`, diagnostic-only `y=RN64(z)`, and the `Q_E` count vector by
floor plus largest fractional remainders with physical-coordinate ties
ascending. Applied effort is `count/(5*Q_E)`. PPO uses exact `z`, actual
`alpha_0`, and the card's complete working score/entropy formulas. The sampler
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

The random tensor order is exactly

```text
W1,W2,W_z,U_z,W_r,U_r,W_h,U_h,W_q,K1,K2,w_V
```

with the shapes and row-major convention in the card. For ordinal `a` and
element `d`, compute `c=CR64(sqrt(6/(fan_in+fan_out)))` and initialize with
`RN64(-c+RN64((2*c)*U(INIT)))`. Biases, `W_rho,b_rho` and all Adam moments are
exact zero and consume no word. The gradient/optimizer tensor order is exactly

```text
W1,a1,W2,a2,W_z,U_z,b_z,W_r,U_r,b_r,W_h,U_h,b_h,
W_q,b_q,W_rho,b_rho,K1,k1,K2,k2,w_V,b_V.
```

## 7. PPO update equations

One update collects 2,048 joint decision ticks from the exact `CELL` order.
Store exact `z`, the old working score and rollout values. With terminal value
zero, use the card's rounded backward recurrence

```text
delta_t=ES64(r_t,RN64(gamma*V_(t+1)),-V_t),
A_63=delta_63,
A_t=ES64(delta_t,RN64(gamma_lambda*A_(t+1))),
G_t=ES64(A_t,V_t).
```

Compute the once-per-update population mean and variance from exact dyadic
sums of the 2,048 stored values, then use exactly

```text
mean_A=RN64(exact_dyadic_sum_t A_t/2048),
c_t=RN64(A_t-mean_A),
var_A=RN64(exact_dyadic_sum_t exact(c_t*c_t)/2048),
den_A=CR64(sqrt(RN64(var_A+RN64(1/100000000)))),
Ahat_t=RN64(c_t/den_A).
```

`Ahat,G`, old score, `z`, action, reward, observation and rollout state are
detached.

Each epoch uses the exact `MBAT` permutation, four consecutive minibatches of
eight complete episodes, zero initial recurrent state, preserved tick order and
full 64-tick backpropagation. For each tick compute actual `alpha_0`, exact `z`
and

```text
working_log_score=ES64(L0,-L1,...,-LK,c1,...,cK),
working_entropy=ES64(L1,...,LK,-L0,e0,-e1,...,-eK),
ratio=CR64(exp(RN64(new_score-old_score))).
```

The 512-tick minimized loss is exactly the card's clipped policy-objective mean,
unclipped squared-value mean and working-entropy mean. Clip derivative is one
only strictly inside `(4/5,6/5)`; `min` ties select the unclipped operand.

The action sampler is not reparameterized. The exact analytic shape gradients
are

```text
d_score/d_alpha_j=ES64(digamma(alpha_0),-digamma(alpha_j),log(z_j)),
d_entropy/d_alpha_j=
 ES64(RN64((alpha_0-K)*trigamma(alpha_0)),
       -RN64((alpha_j-1)*trigamma(alpha_j))).
```

All special-function values are correctly rounded and certified at their exact
arguments. If `g_alpha_j` is the combined upstream shape adjoint, backward
through the rounded softmax uses only

```text
weighted=RN64(exact_dyadic_sum_j exact(alpha_j*g_alpha_j)/alpha_0),
g_logit_k=RN64(alpha_k*RN64(g_alpha_k-weighted)).
```

This declares `D alpha_j/D logit_k =
alpha_j*(indicator(j=k)-alpha_k/alpha_0)`, treats actual `alpha_0` as locally
fixed and bypasses literal differentiation through rounded softmax values.

Every other rounding node is straight-through; tanh/sigmoid use their stored-
output analytic derivatives. Local products round once; contributions to one
parameter use an exact dyadic superaccumulator and one rounding. Physical,
permutation, Gamma, count and environment branches are detached. FERL residual
gradients are exact zero.

Clip jointly over every parameter in the registered tensor order:

```text
norm=CR64(sqrt(exact_dyadic_sum_k exact(g_k*g_k))),
scale=1 if norm=0 or norm<=1/2, else RN64((1/2)/norm),
gbar_k=RN64(g_k*scale).
```

For one-based step `r=16*u+4*h+g+1`, recurrently round `B1_r=beta1*B1_(r-1)`
and `B2_r=beta2*B2_(r-1)`, update binary64 moments, divide by
`1-B1_r,1-B2_r`, and use

```text
adam_den=ES64(CR64(sqrt(vhat)),RN64(1/100000000)),
theta_new=RN64(theta_old-RN64(RN64(3/10000)*RN64(mhat/adam_den))).
```

The full moment operation order is exactly the card's displayed recurrence;
epsilon is outside the square root, weight decay is zero and every coordinate
commits simultaneously. Four epochs produce 16 steps per update and 9,600
steps total. There is no value clipping, KL stop, learning-rate schedule,
reward/value/observation normalization, auxiliary loss, burn-in, hidden-state
carry between episodes or omitted terminal transition.

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

For each of 8,192 learned-arm ticks, compute `a_i,d,S,Rmode` from binary64
target shares `tilde_pi` using exact-superaccumulator/binary64 reductions.
These are not asserted to be exact applied-action means. Count the two exact
predicates. The integer thresholds are 4,096 and
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

Decision 1 emits `NUMERIC_CONTRACT` for any spatial/effort/address/transform,
binary256S softmax or binary256 inference certificate failure and
`ANALYTIC_CERTIFICATE` for any uncertified
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
