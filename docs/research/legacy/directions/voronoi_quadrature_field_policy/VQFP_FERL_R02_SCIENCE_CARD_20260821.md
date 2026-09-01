# VQFP fixed-effort ridgeline sampling definition — revision 02

```text
owner=direction:voronoi_quadrature_field_policy
object=VQFP-FIXED-EFFORT-RIDGELINE-SAMPLING-DEFINITION
revision=VQFP-FERL-SCIENCE-20260821-02
host=RIDGELINE-PLUME-FRONT-1D-FIXED-EFFORT-v2
stage=prospective_definition_only
supersedes_for_future_work=VQFP-FERL-SCIENCE-20260821-01
scientific_activity_begun=false
construction_authorized=false
empirical_activity_authorized=false
pro_closed=false
```

## Decision first

Revision 02 is one complete replacement for r01, not an erratum layer. It
preserves the fixed-total-effort variable-`N` question, `FERL-MEASURE`, literal
strict-containing `FREE-MEASURE-CONTAIN`, matched `FREE-NO-MEASURE-PORT`,
`EQUAL-MASS`, current-state `ANALYTIC-ONE-STEP`, the direct `U`, `D90` and `R`
endpoints, 24 paired training seeds, the original 84 claim-bearing contrasts
and the finite one-dimensional claim ceiling.

It makes the generator, recurrent inputs, counterfactual intervention,
seed-level estimands, support/competence gates, simultaneous inference, branch
quantifiers and mean-procedure claim single-valued. No r01 result, threshold,
seed, coordinate, checkpoint or reviewer conclusion is empirical evidence for
r02.

The directly required structured companion is:

`docs/research/candidates/voronoi_quadrature_field_policy/VQFP_FERL_R02_GENERATOR_ANALYZER_MANIFEST_20260821.md`

This card is the complete normative scientific object. The manifest is its
required ordered generator/analyzer restatement and introduces no selectable
alternative or additional semantics. It cannot override the card. Any
contradiction between them makes the composite invalid and returns to this EM
before activity.

## Scientific question

Can one permutation-equivariant shared policy trained once at `N in {4,8}` use
a correctly associated hard Voronoi-cell-length factor to improve direct
fixed-budget sensing/relay utility at untouched `N in {6,12}` over a competent
free-residual controller that literally contains the hard-factor policy?

The causal contrast is the allocation rule under one roster-invariant physical
effort budget. A positive `FERL-MEASURE` contrast can support only finite-
training-procedure inductive-bias value in the exact qualifying cells. A common
gain of measure-bearing learned arms over equal effort without FERL-versus-FREE
separation supports allocation or explicit-port value, not hard-factor
superiority.

## Exact physical host

### Episode clock, domain and roster

One episode has decision ticks `t=0,...,63`. State at tick `t` is observed
before a simultaneous joint action; the action produces acquisition, delivery,
reward and backlog `B(t+1)`. An episode terminates after the tick-63 transition.

The physical domain is `[0,1]`. For roster size `N`, draw `N+1` independent raw
gaps `raw_j ~ Gamma(alpha,1)` and define

```text
g_j = 0.02/(N+1) + 0.98*raw_j/sum_(l=0..N) raw_l,  j=0,...,N,
x_i = sum_(j=0..i-1) g_j,                              i=1,...,N.
```

Use `alpha=1` for layout `IID` and `alpha=0.35` for layout `CLUSTER`. Physical
rank is increasing `x_i`. Define

```text
b_0=0,
b_N=1,
b_i=(x_i+x_(i+1))/2, i=1,...,N-1,
C_i=[b_(i-1),b_i),   i<N,
C_N=[b_(N-1),1],
v_i=b_i-b_(i-1).
```

Every `v_i>0` and `sum_i v_i=1`. A fresh uniform permutation maps physical rank
to opaque actor handles. Neither rank nor handle is an actor coordinate. Every
neighbor, cyclic intervention and tie-break below is defined in physical rank
before that permutation.

Training balances `N={4,8}` and both layouts. Evaluation crosses
`N={4,6,8,12}` with both layouts. Only `N={6,12}` is claim-bearing. Every learned
arm uses one parameter tensor set, recurrent law, optimizer state and
normalization law across all registered `N`; no per-`N` head, fine-tuning,
checkpoint selection or evaluation adaptation exists.

### Action-independent plume-front recurrence

At episode initialization draw independently

```text
mu_1(0) ~ Uniform[0.10,0.40],
mu_2(0) ~ Uniform[0.60,0.90],
q_m(0)  ~ Uniform({-0.012,-0.008,+0.008,+0.012}), m=1,2,
F_m     ~ Uniform({-1,+1}),                       m=1,2.
```

`F_1` and `F_2` are independent. The tick-32 sign event affects exactly the
`32 -> 33` transition. At each tick, first construct the current field from
`mu_m(t)`. After the tick-t action, define

```text
q_pre = F_m*q_m(t), if t=32,
        q_m(t),     otherwise,
y     = mu_m(t)+q_pre.

if y<0:  mu_m(t+1)=-y;   q_m(t+1)=-q_pre,
if y>1:  mu_m(t+1)=2-y;  q_m(t+1)=-q_pre,
else:    mu_m(t+1)=y;    q_m(t+1)=q_pre.
```

Because `abs(q)<=0.012`, at most one boundary reflection occurs in one
transition. This is an elastic reflection with persistent velocity reversal.
No actor observes `mu`, `q`, `F` or future motion.

With `w=0.08`, `A_1=1` and `A_2=0.7`, define at the pre-action state

```text
p_t(x)=min(1,sum_(m=1..2) A_m*max(0,1-abs(x-mu_m(t))/w)),
H_t={x:p_t(x)>=0.40},
gradient_mass_i(t)=integral_(C_i) p_t(x) dx,
high_gradient_length_i(t)=length(C_i intersection H_t).
```

The integrals and threshold intersections are analytic and use exact cell
boundaries. Fronts, field and event identities never depend on actions.

### Relay field and fixed physical effort

Draw `zeta_0 ~ Uniform[0,1)` independently at episode initialization. Define

```text
link_t(x)=0.55+0.35*cos(pi*(x-zeta_0-0.004*t))^2,
link_i(t)=(1/v_i)*integral_(C_i) link_t(x) dx.
```

At every tick the joint action has nonnegative sensing effort `s_i(t)` and
relay effort `r_i(t)` satisfying exactly

```text
sum_i (s_i(t)+r_i(t)) = E_total = 0.20.
```

`E_total` never scales with roster size. Initialize `B_i(0)=0` and compute

```text
coverage_i(t)=1-exp(-4*s_i(t)/v_i),
acquired_i(t)=coverage_i(t)*gradient_mass_i(t),
unserved_length_i(t)=(1-coverage_i(t))*high_gradient_length_i(t),
delivered_i(t)=min(B_i(t)+acquired_i(t),3*link_i(t)*r_i(t)),
B_i(t+1)=B_i(t)+acquired_i(t)-delivered_i(t).
```

All arms and controls use these same physical equations and the true `v_i`,
including under a reassociated actor-length intervention.

### Reward

After the joint action define

```text
u_t = sum_i unserved_length_i(t) /
      max(sum_i high_gradient_length_i(t),1e-12),
b_t = sum_i B_i(t+1) /
      max(sum_(tau=0..t) sum_i gradient_mass_i(tau),1e-12),
reward_t = -(0.6*u_t+0.4*b_t).
```

The common team reward contains no future field, analytic action, control label
or arm identity.

## Exact direct endpoints and seed aggregation

For evaluation episode `e`, lower is better:

```text
U_e = sum_(t,i) unserved_length_i(t) /
      sum_(t,i) high_gradient_length_i(t),

R_e = 1 - sum_(t,i) delivered_i(t) /
          sum_(t,i) gradient_mass_i(t).
```

All denominators must be positive. For each seed, arm/control and evaluation
cell, exactly 128 episodes are evaluated and

```text
U_seed=(1/128)*sum_(e=0..127) U_e,
R_seed=(1/128)*sum_(e=0..127) R_e.
```

No pooled-component ratio replaces these equal-episode means. Episode
numerators, denominators and ratios are retained.

### Complete discovery-delay analyzer

Cell membership is evaluated only at integer decision ticks using the cell
interval convention above. A continuously crossed cell that contains no front
center at an integer tick creates no event.

For front `m`, cell `i` and tick `t`, an event `(m,i,t)` exists exactly when

```text
t>=2,
mu_m(t) in C_i,
mu_m(t-1) not in C_i,
mu_m(t-2) not in C_i.
```

Thus the two immediately preceding consecutive ticks must both be outside.
For an event at `t`, include entry-tick coverage and define the completed delay
as the smallest integer `d in {1,...,64-t}` such that

```text
sum_(tau=t..t+d-1) coverage_i(tau) >= 0.75.
```

If no such `d` exists, assign `d=64-t+1`. Normalize every event delay by
`64-t+1`. Pool all normalized event delays across the 128 episodes for one
seed/arm/evaluation cell. With `M` pooled events sorted nondecreasing as
`d_(1),...,d_(M)`, define the nearest-rank statistic

```text
D90_seed = d_(ceil(0.90*M)).
```

Fewer than 40 events for any seed in a held-out evaluation cell makes that
cell nonanswerable. Event count is action-independent but is retained for every
arm record. Raw event identities, completion flags, unnormalized delays and
censoring caps are retained.

## Actor information boundary

Define the current deployable content vector

```text
c_i(t) = [gradient_mass_i(t)/v_i,
          B_i(t),
          link_i(t),
          previous_s_i(t)/E_total,
          previous_r_i(t)/E_total,
          N/12,
          t/63].
```

At `t=0`, `previous_s_i/E_total=0` and `previous_r_i/E_total=0` for every
agent. At `t>0`, they equal the realized tick-`t-1` actions. The same rule
applies when a neighbor record is present.

Each actor receives its own content vector and the vectors of the immediate
physical predecessor and successor. For an absent neighbor, every numeric
content coordinate and its length port is zero and a separate boundary bit is
one; for a present neighbor the boundary bit is zero. The self boundary bit is
always zero.

Cell length is a separate explicit port. The base trainable route receives no
own or neighbor length coordinate. The residual route receives the own and
present-neighbor `log(v)` values plus boundary bits. Both principal arms receive
identical content, length ports and boundary tokens.

No actor sees the simulator-truth high-gradient mask/length, absolute physical
rank, opaque handle, layout label, front identity/center/velocity/sign event,
future field, analytic action, evaluation cell, intervention label or arm
label. The current gradient-density coordinate is the exact noise-free cell-
average sensor reading for this object. No noisy or point-sensor claim follows.

## Shared learned policy and literal containment

All learned arms use:

- one shared two-layer width-64 `tanh` content encoder;
- the sum of encoded predecessor and successor records as the bounded-degree
  permutation-invariant neighbor message;
- one shared width-64 GRU per physical agent, reset only at episode start;
- two base logits (`SENSE`,`RELAY`) from GRU state;
- two affine residual logits from GRU state, own/neighbor length ports and
  boundary bits; and
- one matched two-layer width-64 set-mean centralized critic used only during
  training.

For a record slot, define the shared encoder

```text
E(c,b)=tanh(W2*tanh(W1*[c;b]+a1)+a2),
W1 shape=(64,8), W2 shape=(64,64).
```

With absent-neighbor content equal to the registered zeros,

```text
self_i=E(c_i,0),
msg_i=E(c_predecessor,b_left)+E(c_successor,b_right),
u_i=concat(self_i,msg_i),
h_i(t)=GRU_64(u_i,h_i(t-1)).
```

The GRU equations are

```text
z=sigmoid(W_z*u+U_z*h_prev+b_z),
r=sigmoid(W_r*u+U_r*h_prev+b_r),
h_tilde=tanh(W_h*u+U_h*(r elementwise_mul h_prev)+b_h),
h=(1-z) elementwise_mul h_prev + z elementwise_mul h_tilde.
```

Base logits are `q_i=W_q*h_i+b_q`. For supplied arm-specific present lengths
`lambda_j`, define

```text
ell_i=[log(lambda_i),
       b_left,(1-b_left)*log(lambda_left),
       b_right,(1-b_right)*log(lambda_right)],
rho_i=W_rho*concat(h_i,ell_i)+b_rho.
```

Absent length ports are zero. `lambda_j=v_j` intact, `1/N` in NO-MEASURE, and
`v_(P_e(j))` under reassociation.

Every non-residual affine and GRU matrix uses gain-one Xavier uniform,

```text
W_ab ~ Uniform[-sqrt(6/(fan_in+fan_out)),
                +sqrt(6/(fan_in+fan_out))],
```

and all biases start at zero. Within one seed block, all three learned arms have
identical initial values for every common tensor. Every residual-output weight
and bias starts at exact zero.

The training-only critic uses current true physical state but no future value:

```text
d_i=concat(c_i,log(v_i),high_gradient_length_i/v_i,x_i),
k_i=tanh(K2*tanh(K1*d_i+k1)+k2),
k_bar=(1/N)*sum_i k_i,
V=w_V*concat(k_bar,N/12,t/63)+b_V.
```

No critic coordinate reaches actor execution.

For physical agent `i` and mode `m`:

```text
FERL-MEASURE:
  logit_(i,m)=log(v_i)+q_(i,m).

FREE-MEASURE-CONTAIN:
  logit_(i,m)=log(v_i)+q_(i,m)+rho_(i,m).
```

Both arms execute and retain the residual tensors and optimizer slots. FERL
fixes the residual multiplier to zero and no residual gradient reaches its
optimizer; FREE uses multiplier one. Setting FREE's residual output to zero
makes its logits, Dirichlet parameters and complete recurrent action law
identical to FERL for every supplied history. Nonzero residuals make FREE a
strictly larger class.

For every learned arm,

```text
pi_(i,m)=softmax_over_all_2N_slots(logit)_(i,m),
y ~ Dirichlet(64*pi),
action_(i,m)=E_total*y_(i,m).
```

The total concentration is exactly 64 for every roster. Policy likelihood is
the exact joint Dirichlet density. Evaluation remains stochastic. Support
diagnostics use `pi`, not sampled `y`.

Before any production identity or scientific activity, TEST-only fixtures must
show for every registered `N`/layout/history: residual-zero FREE and FERL have
identical distribution parameters; opaque-handle permutation of complete
associated records permutes action shares and recurrent states; array-order
changes alone do not alter physical allocations; and total effort is exactly
conserved. Failure makes the object invalid, not evidence against FERL.

## Controls

### EQUAL-MASS

`EQUAL-MASS` means equal effort:

```text
s_i(t)=r_i(t)=E_total/(2N)
```

at every tick. It sees no future state and is the basic allocation control, not
the strong learned comparator.

### FREE-NO-MEASURE-PORT

This third learned arm is identical to `FREE-MEASURE-CONTAIN` except every
explicit own/neighbor length supplied to the fixed factor and residual port is
the constant `1/N`. True lengths traverse only a masked zero-gradient work-
matching path and have no behavioral or trainable route. The base content route
already excludes length. Within each seed it shares the exact initial common
tensors, physical tapes and update schedule with FERL and FREE, while using its
own pre-frozen independent arm-namespaced action-uniform stream. It must pass
the same support and competence gates.

### ANALYTIC-ONE-STEP

At each tick this control sees only the current physical state and chooses a
global minimizer of the exact next-tick `0.6*u_t+0.4*b_t` over the same
nonnegative `2N` simplex summing to `E_total`. It uses no future state. Among
all global minimizers, choose the lexicographically **largest** allocation in
the fixed coordinate order

```text
(s_1,r_1,s_2,r_2,...,s_N,r_N)
```

defined by physical rank before handle permutation. This total ordering makes
the action unique. It is a feasible one-step opportunity witness, not a dynamic
bound, actor, training target or deployment comparator.

### REASSOCIATED-MEASURE — closed-loop cyclic intervention

For evaluation episode index `e=0,...,127`, define on physical ranks

```text
P_e(i)=i+1 modulo N, if e is even,
P_e(i)=i-1 modulo N, if e is odd,
```

where modulo maps `N+1 -> 1` and `0 -> N`. At every tick, replace every explicit
length associated with physical cell `j` in the fixed factor and in all own or
neighbor residual-length ports by `v_(P_e(j))`. Boundary tokens remain tied to
actual domain endpoints. The base content route remains unchanged because it
never receives length.

The intervention is a complete closed-loop rollout. Preserve the exogenous
layout, plume, link and event tapes and use the same arm-specific evaluation
uniforms as the corresponding intact rollout. Apply intervened actions to the
original physical cells and true service law. Then recursively update backlog,
previous-action coordinates and GRU state under the intervened trajectory.
Those descendants are not held fixed. Initial backlog and GRU state are zero in
both intact and intervention rollouts.

Apply the intervention separately to frozen FERL and FREE checkpoints without
retraining. The incoming length multiset and total effort are preserved. This
off-manifold functional intervention can identify dependence on correct port
association; it cannot prove natural mediation.

## Frozen training and evaluation law

Use 24 fresh paired seed blocks indexed `b=0,...,23`, disjoint from every prior
VQFP tape, coordinate and checkpoint. No numerical run coordinate is created by
this definition.

For each seed and learned arm:

- train exactly 600 PPO updates;
- collect exactly 32 complete 64-tick episodes per update, exactly eight from
  each training `N` by layout cell, in a frozen seed-addressed permutation;
- use GAE `gamma=0.99`, `lambda=0.95`, PPO clip `0.20`, value coefficient
  `0.5`, Dirichlet-entropy coefficient `0.01`, global gradient-norm clip `0.5`,
  four epochs and four minibatches of eight complete episodes (`512` joint
  decision ticks) per epoch;
- preserve within-episode order and use full 64-tick recurrent backpropagation;
- use AdamW with constant learning rate `3e-4`, betas `(0.9,0.999)`, epsilon
  `1e-8` and zero weight decay;
- standardize the 2,048 team advantages once per update as
  `(A-mean(A))/sqrt(population_variance(A)+1e-8)`; do not normalize rewards,
  value targets or observations beyond formulas in this card;
- use the exact clipped joint-Dirichlet PPO objective, unclipped squared value
  error and exact Dirichlet differential entropy under the equations below;
- evaluate only the checkpoint immediately after update 600; and
- forbid early stopping, budget/checkpoint/seed search, threshold tuning,
  architecture menus and result-dependent continuation.

With terminal value zero, GAE uses

```text
delta_t=r_t+0.99*V_(t+1)-V_t,
A_t=sum_(l>=0) (0.99*0.95)^l*delta_(t+l),
G_t=A_t+V_t.
```

For a minibatch, let `ratio` be the exponential difference of new and frozen
old **joint Dirichlet** log likelihoods. The minimized loss is

```text
-mean min(ratio*Ahat,clip(ratio,0.8,1.2)*Ahat)
+0.5*mean (V-G)^2
-0.01*mean exact_Dirichlet_differential_entropy(64*pi).
```

There is no value clipping, KL stop, learning-rate schedule, auxiliary loss,
burn-in or hidden-state carry between episodes. AdamW takes 16 steps per PPO
update and 9,600 steps in 600 updates.

Each seed evaluates intact FERL, intact FREE, intact FREE-NO-MEASURE-PORT,
reassociated FERL, reassociated FREE, EQUAL-MASS and ANALYTIC-ONE-STEP on exactly
128 fresh complete episodes in every registered `N` by layout cell. Physical
tapes are common across all arms and controls. Distinct learned arms use
independent pre-frozen arm-namespaced stochastic-action uniforms. Within an
intact/reassociated checkpoint pair, the exact same uniforms are used.
Only seed-level aggregates enter inference.

## Allocation/action support

At every evaluated learned-arm tick define policy-mean total share

```text
a_i(t)=pi_(i,SENSE)(t)+pi_(i,RELAY)(t),
d(t)=max_i a_i(t)-min_i a_i(t),
S(t)=sum_i pi_(i,SENSE)(t),
Rmode(t)=sum_i pi_(i,RELAY)(t).
```

For one seed, arm and evaluation cell, pool exactly all `128*64=8192` ticks.
That seed passes support exactly when at least 4,096 ticks have `d(t)>=0.03`
and at least 6,554 ticks simultaneously have `S(t)` and `Rmode(t)` in
`[0.15,0.85]`. An arm/cell passes when at least 20 of 24 seeds pass. Sampled
Dirichlet noise cannot satisfy this predicate.

## Simultaneous inference

For lower-is-better endpoint `X`, define seed-level benefit

```text
Delta_X(A,B)=X_B-X_A.
```

The original 84 claim-bearing contrasts remain exactly:

```text
3 endpoints
* 2 held-out N
* 2 layouts
* 7 comparisons
=84,

comparisons:
FERL vs FREE,
FERL vs EQUAL-MASS,
FREE vs EQUAL-MASS,
FERL-intact vs FERL-reassociated,
FREE-intact vs FREE-reassociated,
FREE vs FREE-NO-MEASURE-PORT,
ANALYTIC-ONE-STEP vs EQUAL-MASS.
```

To make every prerequisite simultaneously evaluable, place those 84 in one
prospectively expanded 180-statistic master family together with:

- 24 additional FERL/FREE versus EQUAL-MASS endpoint contrasts at training
  `N={4,8}`;
- 24 FREE-NO-MEASURE-PORT versus EQUAL-MASS endpoint contrasts across all four
  registered `N` and both layouts;
- 24 competence quantities
  `C_A=(U_EQUAL-U_A)-0.20*(U_EQUAL-U_ANALYTIC)` for three learned arms, four
  `N` and two layouts; and
- 24 relay-ceiling quantities `Q_A=0.90-R_A` for the same arm/cell grid.

For every statistic, form a two-sided Student interval over its 24 seed values
with 23 degrees of freedom and critical quantile

```text
t_(1-0.05/(2*180),23).
```

Thus all 180 intervals have Bonferroni familywise coverage at least 0.95. Raw
seed vectors, means, sample standard deviations and interval endpoints are
retained. No episode is treated as an independent inferential unit.

Margins are

```text
m_U=0.04,
m_D90=0.05,
m_R=0.04,
nonharm_X=m_X/2.
```

For an interval `[L_X(A,B,c),U_X(A,B,c)]` in cell `c`, define

```text
MAT_X(A,B,c)  iff L_X(A,B,c)>m_X,
HARM_X(A,B,c) iff U_X(A,B,c)<-m_X,
NH_X(A,B,c)   iff L_X(A,B,c)>-m_X/2,
EQ_X(A,B,c)   iff L_X(A,B,c)>=-m_X and U_X(A,B,c)<=m_X.
```

The reverse comparison uses `[-U,-L]`. Failure to prove `NH` is not established
harm. Only `HARM` supports a harm statement.

## Ordered prerequisites

1. **Validity:** the complete atomic 24-seed panel exists; conservation,
   nonnegative actions/backlogs, residual-zero containment, permutation/array
   identities, no leakage/selection, positive denominators, exact event and
   stored arithmetic identities all hold.
2. **Physical opportunity:** in each held-out cell,
   `L_U(ANALYTIC,EQUAL)>0.08` and either
   `L_D90(ANALYTIC,EQUAL)>m_D90` (permitted only when every seed has at least
   40 events) or `L_R(ANALYTIC,EQUAL)>m_R`; the across-seed mean of EQUAL-MASS
   `U_seed` is in `[0.20,0.85]`.
3. **Allocation/action support:** every one of the three learned arms passes the
   exact held-out-cell support predicate above.
4. **FERL target harm adjudication:** before competence, established FERL harm
   is tested exactly as defined in branch 4 below.
5. **Per-`N` competence:** for every learned arm, registered `N` and layout, the
   master-family lower endpoints satisfy `L(C_A)>0`, every endpoint contrast
   versus EQUAL-MASS satisfies `NH_X(A,EQUAL)`, and `L(Q_A)>0` (equivalently the
   simultaneous upper endpoint for mean `R_A` is below `0.90`).
6. **Answerability/headroom/interiority:** every held-out seed/cell has at least
   40 discovery events; the across-seed mean of each learned arm's seed-level
   `U`, `D90` and `R` is in `[0.08,0.92]`; and every held-out FERL-versus-FREE
   interval half-width is no greater than `m_X/2` for its endpoint.

Failure at a prerequisite makes all later contrasts descriptive. It does not
establish equivalence, absence of mechanism or family deletion.

## Ordered exhaustive result map

The first matching branch controls. Every quantifier below is literal.

1. `INVALID_OR_INCOMPLETE`: validity fails.
2. `NO_PHYSICAL_OPPORTUNITY`: validity passes and any held-out opportunity or
   EQUAL-MASS headroom predicate fails.
3. `NO_ALLOCATION_ACTION_SUPPORT`: opportunity passes and any learned arm fails
   support in any held-out cell.
4. `FERL_TARGET_HARM`: support passes and either (a) there exists one held-out
   `N` for which both layouts satisfy `HARM_U(FERL,EQUAL)`, (b) any held-out
   cell satisfies `HARM_R(FERL,EQUAL)`, or (c) any held-out cell with at least
   40 events in every seed satisfies `HARM_D90(FERL,EQUAL)`. This branch
   supports harm only in the exact qualifying cells and endpoints.
5. `LEARNED_OR_CONTAINING_COMPETENCE_FAILURE`: branch 4 does not match and any
   one of the three learned arms fails any competence predicate. A failed
   non-harm proof is reported as unresolved competence, not harm.
6. `ENDPOINT_NONANSWERABLE`: competence passes and any event, interiority or
   FERL/FREE precision predicate fails.
7. `HETEROGENEOUS_FERL_FREE_EFFECTS`: answerability passes and there exist two
   held-out cells `c,c'` such that `MAT_U(FERL,FREE,c)` and
   `MAT_U(FREE,FERL,c')`. Report cell-specific opposing effects; make no target-
   wide retain/delete decision.
8. `FERL_TREATMENT_SPECIFIC_VALUE`: branch 7 does not match; there exists one
   common `N* in {6,12}` such that both layouts at `N*` satisfy
   `MAT_U(FERL,FREE)`, `MAT_U(FERL,EQUAL)` and
   `MAT_U(FERL-intact,FERL-reassociated)`; and every held-out cell satisfies
   `NH_U(FERL,FREE)` plus, for `X in {D90,R}`, both `NH_X(FERL,FREE)` and
   `NH_X(FERL,EQUAL)`. Retain only a cell-specific hard-factor value claim.
9. `FREE_MEASURE_SUPERIORITY`: branch 7 does not match; there exists one common
   `N*` whose two layouts satisfy `MAT_U(FREE,FERL)`; every held-out cell
   satisfies `NH_U(FREE,FERL)` and, for `X in {D90,R}`,
   `NH_X(FREE,FERL)` and `NH_X(FREE,EQUAL)`. Retain the containing free family
   only for the exact qualifying cells; do not infer other rosters.
10. `EXPLICIT_MEASURE_PORT_ONLY_VALUE`: every FERL-versus-FREE endpoint interval
    is `EQ` in every held-out cell; there exists one common `N*` whose two
    layouts satisfy `MAT_U(FERL,EQUAL)`, `MAT_U(FREE,EQUAL)`,
    `MAT_U(FREE,FREE-NO-MEASURE-PORT)`,
    `MAT_U(FERL-intact,FERL-reassociated)` and
    `MAT_U(FREE-intact,FREE-reassociated)`; and every held-out cell satisfies
    secondary-endpoint `NH` for FERL/EQUAL and FREE/EQUAL. Retain only correct
    explicit measure-port/binding value, not hard-factor superiority or natural
    mediation.
11. `GENERIC_ALLOCATION_VALUE_WITHOUT_MEASURE_SPECIFICITY`: there exists one
    arm `A in {FERL,FREE}` and one common `N*` whose two layouts satisfy
    `MAT_U(A,EQUAL)`; all held-out cells satisfy `NH_D90(A,EQUAL)` and
    `NH_R(A,EQUAL)`; and every endpoint interval in every held-out cell is `EQ`
    for FERL/FREE, FERL-intact/reassociated, FREE-intact/reassociated and
    FREE/FREE-NO-MEASURE-PORT. Only then may the exact family be modified toward
    generic scarcity allocation without a Voronoi-specific claim.
12. `ALLOCATION_VALUE_WITH_MEASURE_SPECIFICITY_UNRESOLVED`: a common-arm/common-
    `N*` allocation-value condition from branch 11 holds with global secondary
    non-harm, but branches 7-11 do not match. Retain correct association,
    generic allocation, optimization geometry and insufficient mechanism-
    control precision as live explanations; make no automatic deletion or
    modification.
13. `TARGET_SPECIFIC_NO_MATERIALITY`: every endpoint interval in every held-out
    cell is `EQ` for FERL/FREE, FERL/EQUAL, FREE/EQUAL,
    FERL-intact/reassociated, FREE-intact/reassociated and
    FREE/FREE-NO-MEASURE-PORT. Close only this exact target without a positive,
    negative-general or arbitrary-`N` claim.
14. `UNRESOLVED_VALID_EVIDENCE`: every prerequisite passes and no earlier
    branch matches. Report all intervals and define no automatic successor.

No branch creates new seeds, budget, checkpoint, surface, construction, UAV
production or deployment. Any successor requires a new Portfolio decision.

## Strongest alternatives

A positive FERL contrast can arise because the fixed `log(v)` term and removal
of residual freedom improve finite-600-update conditioning, exploration or
optimization geometry under a global `2N` softmax. Global softmax itself may be
the useful scarcity allocator. Backlog/link features or the registered front-
width/layout law may dominate. Centralized critic normalization may not survive
decentralization. Reassociation is off-manifold and reveals functional port
dependence, not natural mediation.

## Maximum claim and nonclaims

The maximum possible claim is:

> Under the frozen 24-seed initialization, training and evaluation law for
> `RIDGELINE-PLUME-FRONT-1D-FIXED-EFFORT-v2`, the registered FERL training
> procedure—each seed producing one parameterization shared across agents and
> roster sizes—had a positive simultaneous mean seed-level direct-endpoint
> contrast in only the exact qualifying held-out roster/layout cells,
> conditional on every prerequisite and branch predicate.

No outcome supports one selected checkpoint, every training run, arbitrary
`N`, in-episode roster change, asymptotic or optimizer-independent superiority,
unique mechanism mediation, two-dimensional terrain/plume value, hardware
transfer, flight, safety or deployment. A no-material result is exact-target
evidence only.

## UAV bridge and missing step

The toy maps to a ridgeline UAV team whose fixed loiter locations induce unequal
coverage cells, whose shared physical duty-cycle budget must be divided between
sensing a moving plume/fire-front urgency ridge and relaying accumulated data
through a spatially varying link. Variable `N` changes the roster sharing that
same total duty-cycle budget; local cell-average sensing, backlog, link quality
and immediate-neighbor records are deployable abstractions. The hypothesized
benefit is robust scarcity allocation without per-roster retraining.

Before any two-dimensional or flight claim, a separately authorized object must
show direct value in a 2-D terrain/communication simulator with moving or
reassigned footprints, realistic noisy point/footprint sensing, aircraft
dynamics, energy/communication overhead and at least one held-out roster or
in-episode membership change. This r02 cannot supply that step.

## Activity boundary and exact later engineering question

Question-relevant activity begins immediately before the first optimizer
mutation of a production FERL or FREE model, or the first production evaluation
used in a conclusion, whichever occurs first. TEST-only formula, analyzer,
analytic arithmetic and native/reference equivalence on explicitly non-
scientific tapes do not cross it. No activity is authorized here.

Only after same-conversation Pro `CLOSED` plus EM intake may Portfolio consider
requesting static CM feasibility and full prospective cost for this exact
composite: native-first C++ batched reset-to-terminal host; analytic integrals;
fixed-total two-mode action; recurrent policy/critic and exact PPO; all controls;
closed-loop reassociation; event analyzer; 180-statistic intervals; exhaustive
branch map; atomic checkpoint/result lifecycle; and full construction,
training, evaluation, CPU/GPU, wall, RAM, scratch and durable-storage cost.

This card authorizes no source, build, probe, identity, coordinate, model,
training, evaluation, result, lease, compute, production, deployment or Git
action.
