# SCDMP target-bound competent-controller-first order-value science card — revision 01

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-TARGET-BOUND-COMPETENT-CONTROLLER-ORDER-VALUE
task=QUAD-UAV-PALLET-GANTRY-24P5M-v1
treatment=ORDERED-SUPPORT-GRAPH-SLACK
revision=SCDMP-TBCC-ORDER-VALUE-SCIENCE-20260821-01
owner=EM_semigroup_consistent_duration_model_policy
stage=definition_only
portfolio_envelope=SCDMP-TARGET-BOUND-COMPETENT-CONTROLLER-ORDER-VALUE-DEFINITION
scientific_activity_started=false
external_review_state=awaiting_existing_scdmp_pro_closure
source_build_test_probe_authorized=false
identity_coordinate_model_checkpoint_authorized=false
training_evaluation_compute_lease_authorized=false
relation_assay_authorized=false
stage_b_authorized=false
uav_production_deployment_flight_authorized=false
```

## Question and target value

This card freezes one materially new target-bound planar simulator task:
`QUAD-UAV-PALLET-GANTRY-24P5M-v1`. Four fixed quadrotor carriers transport one
rigid cable-suspended instrument pallet through an offset gantry and dock it at
`x=24.5 m`. It asks:

> After one treatment-independent, order-erased controller has established
> full-mission competence and is frozen, can a physics-specified ordered
> support-graph adapter improve direct safe-docking value or worst-regime
> robustness with one parameterization across unseen fixed and switched
> external command-hold periods, relative to the frozen foundation, a
> registered-`K_train`-competent strictly containing order-aware controller,
> tied reversal, and a registered-`K_train`-competent unrestricted order-
> insensitive controller?

The sole treatment is `ORDERED-SUPPORT-GRAPH-SLACK`. Its support-graph
composition, action-score orientation, controller foundation, target,
competence prerequisite, opportunity assay, controls, margins and branches are
all frozen before source, identity, controller or outcome exists.

The scientific sequence is prospective and nonadaptive:

1. train exactly one order-erased foundation law per fresh replicate under one
   frozen recipe;
2. accept only the registered final foundation checkpoint, retain every
   replicate, and evaluate one complete treatment-independent competence panel;
3. only if that complete panel passes, freeze every foundation actor and run
   one full-mission foundation-conditioned opportunity assay;
4. only if that assay passes, instantiate and train the already specified
   order-stage adapters while the foundation remains immutable; and
5. evaluate one atomic direct-value panel and apply one exhaustive first-true
   result map.

A nonpass at either prerequisite ends this exact object without another budget,
checkpoint, architecture, seed, threshold or treatment. The order treatment is
not instantiated before both prerequisites pass.

This is a fixed-`N=4` simulator question. It tests one controller
parameterization across registered external `k`; it does not test variable
team size.

## Exact isolation from consumed SCDMP objects

The complete `SCDMP-UAV-SP-R02-FULL-EMPIRICAL-PANEL` result supplies only the
same-direction motivation that local physical order opportunity can coexist
with a treatment-common end-to-end competence bottleneck. No r02, r07 or SRF
task law, retension/crosswind event, risk tilt, architecture, optimizer state,
checkpoint, parameter, support state, threshold, margin, budget, seed, master,
coordinate, random tape, estimate, subgroup, branch or result enters this
object.

The new target uses four carriers, a rigid pallet, a noncommuting discrete
cable-support graph, a new action catalogue, a newly trained order-erased
foundation, new `k` values, new workload, new identities and new inference.
It is not a checkpoint, seed, threshold, step, architecture or within-package
repair of any consumed object.

## Named physical target

### Plant, clocks and state

`QUAD-UAV-PALLET-GANTRY-24P5M-v1` is a dimensioned planar abstraction, not a
flight-dynamics or aviation-safety model. Four identical carriers support the
four corners of a rigid instrument pallet through unilateral cables. A common
low-level stabilizer maintains carrier altitude and the commanded formation;
the learned joint controller chooses forward demand and a zero-sum load-share
pattern at external renewal boundaries.

One primitive physics tick is `Delta t=0.1 s`. The horizon is `364` ticks
(`36.4 s`). The pallet must traverse a smooth lateral-offset gantry and dock at
`x>=24.5 m` with the registered alignment tolerances.

At primitive tick `n`, the simulator state is

```text
X_n=(x,v,y,w,phi,omega,z_1,z_2,z_3,z_4,f,
     a_n-1,r_1,n-1,r_2,n-1,r_3,n-1,r_4,n-1,p,n).
```

`x,v` are forward position and speed; `y,w` are lateral offset and speed;
`phi,omega` are pallet roll and roll rate; `z_i` are filtered cable-overload
exposures; `f` is formation error; `a_n-1,r_i,n-1` are the prior held joint
command; and `p` is the unobserved cable-support assignment. The initial public
state is

```text
x=0
v~Uniform[0,0.03] m/s
y~Uniform[-0.01,0.01] m
w=0
phi~Uniform[-0.01,0.01] rad
omega=0
z_i=f=0
a_-1=1
r_i,-1=0.
```

Initial public draws and every exogenous disturbance are paired across all
controllers. The carrier roster, pallet, geometry, primitive clock, gantry and
failure limits are identical across arms.

The offset gantry centerline is

```text
y_ref(x)=0                                      for x<8
y_ref(x)=0.18*sin(pi*(x-8)/8)                  for 8<=x<16
y_ref(x)=0                                      for x>=16.
```

### Same-multiset support-graph intervention

Before mission control, the pallet rests on a fixture and all cables are
unloaded. Four visible, equal-duration, action-independent setup slots contain

```text
SYNC
HOOK-HANDOFF and FORMATION-ROTATE in balanced order
LEVEL-RELEASE.
```

The middle events act on the cable assignment

```text
p=(p_1,p_2,p_3,p_4), initially (1,2,3,4),
```

where `p_i` is the pallet hook connected to public carrier position `i`.
Their exact maps are

```text
H(p_1,p_2,p_3,p_4)=(p_2,p_1,p_3,p_4)
R(p_1,p_2,p_3,p_4)=(p_4,p_1,p_2,p_3).
```

Thus

```text
H then R: p_HR=(4,2,1,3)
R then H: p_RH=(1,4,2,3)
```

and `R(H(p)) != H(R(p))`. `HOOK-HANDOFF` transfers one fixture-supported
front sling between adjacent hooks. `FORMATION-ROTATE` rotates the public
carrier positions one quarter-turn around the fixture while cable identities
remain attached. Both sequences use the same events, durations, fixture
support, total setup time, first sentinel, final sentinel and public carrier
release pose. `LEVEL-RELEASE` zeros public cable tensions and releases the
pallet; it does not change `p`.

The two final assignments are mapped prospectively to load-incidence vectors

```text
p_HR -> b_1=(+1,-1, 0, 0), q=1
p_RH -> b_0=( 0, 0,+1,-1), q=0.
```

`p` and `b_q` are latent. At the first actionable renewal, every public plant
variable, prior command, current `k`, release time and aggregate tension is
exactly aliased. Both raw middle-event tokens remain available to order-aware
controllers. The foundation and order-insensitive control receive only the
unordered event multiset. The common `LEVEL-RELEASE` sentinel prevents the
last raw token of the complete setup sequence from identifying the middle
ordering, but this remains a binary two-event task; no general chronology
claim is available.

This support-graph map is a prospective simulator law. It is not a claim that
real pallet-hook operations have these exact coefficients.

### Joint action and external hold

At every renewal, the centralized policy selects one of 18 legal joint actions

```text
A=(a,r)
a in {1,2}
r in R,
```

where `a` is common forward demand and

```text
R={
 ( 0, 0, 0, 0),
 ( 1,-1, 0, 0), (-1, 1, 0, 0),
 ( 0, 0, 1,-1), ( 0, 0,-1, 1),
 ( 1, 0,-1, 0), (-1, 0, 1, 0),
 ( 0, 1, 0,-1), ( 0,-1, 0, 1)
}.
```

Every load-share vector is zero-sum. A common inner stabilizer maps `(a,r)` to
carrier thrust and winch commands. The action is held for the currently
announced external `k_n` primitive ticks or until absorption. No controller
acts, terminates, communicates or queries the policy mid-hold.

### Frozen primitive dynamics

At one primitive tick, let

```text
e = y-y_ref(x)
b=b_q
tau_i = 0.38 + 0.12*a + 0.16*a*max(b_i,0)
        -0.10*r_i + 0.04*|phi| + 0.03*|e|
tau_bar = mean_i tau_i
mu = 0.5*sum_i b_i*(tau_i-tau_bar)
nu = 0.25*(r_1+r_4-r_2-r_3).
```

Three address-stable disturbances, paired across controllers, are independently
equiprobable in

```text
eta_v in {-0.003,+0.003}
eta_y in {-0.002,+0.002}
eta_omega in {-0.004,+0.004}.
```

The exact update is

```text
omega' = 0.90*omega - 0.12*phi + 0.08*mu + 0.02*w + eta_omega
phi'   = clip(phi + 0.1*omega',-0.50,0.50)
w'     = 0.88*w - 0.10*e - 0.03*phi + 0.025*nu + eta_y
y'     = y + 0.1*w'
v'     = clip(0.92*v + 0.08*(0.75*a)
              -0.02*|phi'| -0.02*|e| + eta_v,0,1.60)
x'     = x + 0.1*v'
z_i'   = 0.84*z_i + max(0,tau_i-0.88)
f'     = 0.86*f + 0.04*max_i|r_i| + 0.05*|phi'| + 0.04*|e|.
```

Then `a_n-1<-a`, `r_i,n-1<-r_i`, `p'<-p`, and `n'<-n+1`.

The registered gantry clearance after the update is

```text
C'=0.30-|y'-y_ref(x')|-0.55*|phi'|.
```

The first occurrence of any of these is an absorbing physical failure:

```text
cable overload/drop: max_i z_i'>0.25
gantry contact: 8<=x'<=16 and C'<=0
pallet attitude loss: |phi'|>0.32
formation loss: f'>0.40.
```

Failure labels are nonexclusive and dominate same-tick docking. Safe docking
occurs at the first tick with

```text
x'>=24.5, |y'|<=0.08, |phi'|<=0.08,
max_i z_i'<=0.25, f'<=0.40
```

and no physical failure. Timeout is unsuccessful docking but not relabeled as
a physical failure. After absorption there is no plant update, policy query,
reward or energy command.

The treatment-independent conservative action `(a=1,r=0)` is a prospective
instantaneous cable-load safety witness, not a full-mission competence or
empirical claim. At zero public deviation its
largest instantaneous cable load is `0.66<0.88` in either graph. The
graph-matched high-demand actions `(2,(1,-1,0,0))` for `q=1` and
`(2,(0,0,1,-1))` for `q=0` reduce the graph-loaded cable from `0.94` to `0.84`,
whereas a graph-mismatched high-demand action leaves it at `0.94`. Repeated
holds therefore create a prospective direct speed-versus-overload opportunity.
Only the registered full-mission competence and opportunity panels may
establish those qualifications.

### Deployable observation

Every controller receives the common scaled public vector

```text
o_n=(x/24.5,v/1.6,y/0.40,w/0.25,phi/0.35,omega/0.40,
     z_1/0.25,z_2/0.25,z_3/0.25,z_4/0.25,f/0.40,
     a_n-1/2,r_1,n-1,r_2,n-1,r_3,n-1,r_4,n-1,
     k_n/13,n/364) in R^18.
```

No controller receives `p`, `b_q`, a graph label, failure label, seed,
scenario identity or future `k` schedule. Order-aware arms additionally receive
the raw setup sequence from which the registered graph compositor produces
`q`; the foundation receives only the unordered setup multiset. After action,
public tensions and pallet motion may reveal graph consequences to every arm.
Any positive claim is therefore limited to earlier use of the registered order
before shared physical feedback makes it redundant.

### Training reward

The sole scalar learning reward per primitive tick is

```text
r_n = 0.015*(x'-x)
      -0.001*mean_i[(a+0.35*r_i)^2]
      -0.002*(phi')^2
      -0.002*(y'-y_ref(x'))^2,
```

plus `+1` on safe docking, `-1` on a physical failure and `-0.4` on timeout.
No reward, critic value, training curve or subgroup activates a scientific
branch.

## External-`k` registry and shared parameterization

Foundation and adapter training use only fixed

```text
K_train={5,11}.
```

The target panel uses

```text
fixed 7
fixed 13
7->13
13->7.
```

Switches occur at the common renewal boundaries `n=91` or `n=273`, balanced
and independent of graph order and disturbances. Current `k` is revealed only
when it becomes active. A switch resets no plant state, model state,
normalization, optimizer or controller parameter.

Every learned foundation and every later adapter has one weight vector across
all registered periods. There is no per-`k` head, table, expert, initializer,
optimizer, checkpoint selection, fine-tuning or evaluation update. The actor is
feed-forward; only the plant carries state. The claim concerns exactly these
four target schedules, not arbitrary or continuously varying `k`.

## Stage 1: treatment-independent competent foundation

### One frozen foundation law

For each fresh paired replicate `s in {0,...,23}`, train exactly one order-erased
`K-AWARE-ORDER-ERASED-SAFE-PROGRESS-FOUNDATION`. Its actor

```text
F_theta:R^18->R^18
```

has two SiLU hidden layers of width `96` and emits logits over the 18 actions.
Its critic has the same two hidden widths and emits one scalar. Affine maps
include biases. The foundation has `12,882` actor parameters and `11,233`
critic parameters, `24,115` total. It receives `o` and the unordered setup
multiset only; neither actor nor critic has a chronology or graph-mode path.

Float32 arithmetic is frozen. Unless named otherwise, every new affine weight
matrix uses row-major Xavier-uniform initialization with gain `1` and every
bias is zero. The later treatment-scale output weight is exactly zero with
output bias `0.001`; every FREE/SET residual output weight and bias is exactly
zero, while their hidden matrices use the global rule. There is one training
budget, one final checkpoint at update 160 and no alternative architecture,
checkpoint, seed subset, threshold or stopping rule.

### Foundation training

Each foundation replicate receives 160 PPO updates. Every update allocates 12
complete horizon slots: six at `k=5` and six at `k=11`, with three `q=0` and
three `q=1` episodes within each `k`. The public initialization and exogenous
physics are paired by prospective address; the foundation never receives q.

At each renewal, a categorical action is sampled by inverse CDF in the fixed
lexicographic 18-action order from one fresh address-stable `Uniform[0,1)`
variate. No other exploration or action noise exists.

The exact duration-correct PPO law common to foundation and later adapters is
defined below. Foundation actor and critic are jointly updated. Only the final
update-160 actor/critic checkpoint is eligible. All 24 final checkpoints must
be technically accepted before the complete competence panel is opened.

### Foundation competence panel

For each replicate, the final foundation is evaluated by deterministic
lexicographic argmax on 120 fresh episodes in
each of

```text
fixed 5, fixed 11, fixed 7, fixed 13, 7->13, 13->7.
```

Each regime has 60 episodes per support-graph order; switch time is balanced.
Across the 24 replicate-level summaries, compute one simultaneous family of
one-sided Student-t bounds with Bonferroni family error `0.05` and 17 members:

- 12 one-sided lower bounds for safe-docking rate in every
  `order x regime` cell;
- one pooled safe-docking lower bound; and
- four one-sided upper bounds. For each replicate and each physical failure,
  first pool both graph orders within each regime and then take the maximum
  failure rate across the six regimes.

The foundation competence prerequisite is `PASS` only if every cell lower
bound is strictly above `0.72`, the pooled lower bound is strictly above
`0.84`, and every physical-failure upper bound is strictly below `0.10`.
Boundary contact does not pass. Every other complete valid outcome is
`COMMON-CONTROLLER-COMPETENCE-NOT-ESTABLISHED`; it does not prove competent
control impossible and cannot trigger a repair inside this object.

No order-stage parameter, initializer or optimizer may be instantiated unless
the complete foundation competence prerequisite passes. Every foundation
replicate is retained; there is no passing-seed selection.

## Stage 1b: foundation-conditioned direct opportunity

After foundation competence passes and the foundation actors are frozen, run
one disjoint treatment-independent opportunity panel. For every replicate and
each target fixed `k in {7,13}`, draw 16 fresh aliased first-renewal public
states. Instantiate each state once under each support graph. Before any
rollout, bind exactly four fresh future-disturbance tapes to each
`(replicate,k,state)`; those four tapes are shared across graph modes and all
forced actions and are never selected or replaced.

For every one of the 18 legal actions and each of the four tapes, force that
action for exactly the announced first hold, then return control to the same
frozen order-erased foundation, using deterministic lexicographic argmax, for
the complete remaining mission. The forced first action is an intervention,
not a foundation policy query. No action is chosen using its realized future
disturbance tape.

For one completed rollout define the direct docking value

```text
U = 1[safe dock]*(1-t_dock/36.4),
```

where `t_dock=0.1*n'` seconds at the first post-update safe-docking tick and
`U=0` for failure or timeout. Average the four values before any optimization:

```text
bar_U(q,A)=0.25*sum_(ell=1)^4 U(q,A,tape_ell).
```

For each paired `(replicate,k,state)` define

```text
M_q = max_A bar_U(q,A)
C_common = max_A 0.5*(bar_U(0,A)+bar_U(1,A))
D_pair = 0.5*(M_0+M_1)-C_common
Q_pair = 1[Argmax_A bar_U(0,A) intersect
           Argmax_A bar_U(1,A) is empty],
```

where exact ties remain in the complete argmax sets. Thus `Q_pair` is one only
when no common action is optimal under both graph modes; unequal sets with a
shared optimum do not qualify.
Also define

```text
S_pair = 0.5*sum_q (max_A bar_U(q,A)-min_A bar_U(q,A)).
```

Average each quantity within replicate, then form three one-sided Bonferroni
Student-t lower bounds across 24 replicates with family error `0.05`. The
direct target opportunity gate passes only if

```text
lower(Q)>0.20
lower(D)>0.025
lower(S)>0.060.
```

`D=0.025` is a direct safe-docking completion-value difference, equivalent to
`0.91 s` of successful completion slack when success is unchanged. The panel
uses no proxy reward or one-interval score. It may reveal only its complete
registered qualification after atomic acceptance and may not revise the
already frozen task, treatment, actions or thresholds.

Every other valid complete outcome is
`TARGET-ORDER-OPPORTUNITY-NOT-ESTABLISHED` and ends the object before order
adapter instantiation. It is not a universal no-order statement.

## Stage 2 treatment and controls

### Physics-specified graph-slack score

For current public `o`, graph `q`, action `A=(a,r)` and current hold `k`, use
the exact primitive load formula to compute `tau_i`. Let the realizable planned
duration be

```text
h_plan=min(k,364-n).
```

Predict exposure after a constant action for that complete realizable hold,
without disturbances:

```text
z_i^hold = 0.84^h_plan*z_i
           + ((1-0.84^h_plan)/(1-0.84))*max(0,tau_i-0.88)
c_q(o,A,k)=0.25-max_i z_i^hold
u_req(o)=clip((24.5-x)/(0.075*max(1,364-n)),0,2)
```

and define

```text
J_q(o,A,k)=0.30*u_req(o)*(a-1)
           +0.10*clip(c_q/0.25,0,1)
           +1.00*min(c_q/0.10,0)
           -0.20*|mu|.
```

This is a frozen target-progress versus graph-load-slack ordering. It is not
claimed to be an exact value function or globally correct hazard ranking.

### `ORDERED-SUPPORT-GRAPH-SLACK`

Clone the exact frozen foundation actor for each replicate and never update it.
A treatment scale network `g:R^18->R` has one SiLU hidden layer of width 32 and
`641` parameters. Define

```text
alpha(o)=ReLU(g(o))
logit_T(A|o,q)=F_theta(o)_A + alpha(o)*J_q(o,A,k).
```

The output weights of `g` start at zero and its output bias starts at
`0.001`, so the adapter starts prospectively near, but not exactly at, the
foundation and has a live nonnegative gradient. `alpha>=0` makes the added
coordinatewise score contribution nonnegative: holding `F`, `alpha` and every
other action score fixed, increasing one action's `J` cannot decrease its
logit or categorical probability. Arbitrary foundation-logit differences can
still determine the total action ranking; no global ranking-by-`J` claim is
made. The score is the sole direct actor path from event order.

A new treatment critic receives `(o,q)`, has two SiLU layers of width 64 and
one scalar output (`5,505` parameters). Only `g` and this critic train; the
foundation actor, its normalization and the common inner stabilizer remain
immutable. Treatment has `6,146` trainable order-stage parameters.

### Competent strictly containing `FREE-DIRECT`

`FREE-DIRECT` contains the complete treatment and adds

```text
R_psi:R^19->R^18
```

with SiLU widths `64,64`:

```text
logit_FREE(A|o,q)=F_theta(o)_A+alpha(o)*J_q(o,A,k)+R_psi(o,q)_A.
```

The residual output layer starts exactly at zero. Setting every residual
parameter to zero reproduces treatment for all inputs. At any input where the
18-vector `J_q(o,.,k)` is nonconstant, treatment logits relative to the frozen
foundation lie in the one-dimensional nonnegative ray generated by `J`.
After quotienting the additive all-ones softmax constant, a residual output
vector outside `span{1,J_q(o,.,k)}` defines a policy unavailable to treatment.
Output biases make such a vector feasible, proving strict containment of the
deployed actor function class. This does not claim containment of finite
optimizer trajectories: residual gradients and global clipping change FREE's
geometry. FREE has `6,610` residual parameters and `12,756` total trainable
order-stage parameters including `g` and its critic.

### Tied `REVERSED`

`REVERSED` is never trained. It evaluates the final treatment weights,
foundation and physical episode while replacing only the graph supplied to
the registered treatment compositor by `q<-1-q`. Public plant feedback,
physical latent graph, `k`, action set, weights, disturbances and time remain
unchanged. It tests wrong support-graph orientation without another optimizer.

### Unrestricted order-insensitive `SET-FREE`

`SET-FREE` uses the same frozen foundation and the same `g`, residual and
critic architectures and parameter count as FREE, but every actor, critic,
old-policy, bootstrap and loss occurrence replaces order by

```text
q_SET=0.5
J_SET(o,A,k)=0.5*(J_0(o,A,k)+J_1(o,A,k)).
```

Its event compositor receives the unordered multiset only and is verified
invariant to middle-event permutation. No event position, timestamp, padding,
trace or recurrent state can reconstruct order. Later public physical feedback
remains available.

### `FOUNDATION-ONLY`

The exact frozen order-erased foundation is evaluated as a fifth controller.
It shows whether an adapter adds direct value to the already competent common
controller, rather than merely damaging it less than another adapter.

### Equal order-stage opportunity

Within each replicate, TREAT, FREE and SET clone byte-identical foundation
weights. Their order-stage tensors use disjoint paired identities. FREE and SET
have identical unrestricted residual shapes and zero output initialization.
All trained adapters receive equal scenario, physical-time, action, reward,
optimizer, update, minibatch and evaluation opportunity. The only information
change is true order versus invariant set; the only function-class enlargement
is FREE/SET's explicit residual. The harder finite-budget geometry of the
strictly containing comparator remains a strongest alternative, not a hidden
claim. “Strictly containing” refers only to the deployed actor function class
under the matched frozen recipe.

## Exact duration-correct training law

Each of the three order-stage arms receives 96 PPO updates per replicate.
Every update allocates 12 complete horizon slots: six at `k=5`, six at `k=11`,
and three episodes per graph within each `k`. Foundation actors are frozen.

At a real renewal record `j` of duration `h_j<=k_j`, snapshot the complete old
trainable actor/critic values, `logp_old,j` and `V_old,j`. With

```text
gamma=0.995
lambda=0.93
```

define

```text
rbar_j=sum_(ell=0)^(h_j-1) gamma^ell*r_(tau_j+ell)
delta_j=rbar_j+1[nonterminal_j]*gamma^h_j*V_old,j+1-V_old,j
A_raw,j=delta_j+1[nonterminal_j]*(gamma*lambda)^h_j*A_raw,j+1
Y_j=stop_gradient(A_raw,j+V_old,j).
```

Normalize all valid `A_raw` once per arm/update using population variance and
`1e-8`. The normalized actor advantage, old log probabilities, old values and
targets remain immutable through the update.

For current minibatch `M`, define

```text
ratio_j=exp(log pi(a_j|o_j,q_j)-logp_old,j)
L_policy=-mean min(ratio_j*Ahat_j,
                   clip(ratio_j,0.80,1.20)*Ahat_j)
L_value=0.5*mean(V(o_j,q_j)-Y_j)^2
L_entropy=mean H(pi(.|o_j,q_j))
L_total=L_policy+0.50*L_value-0.010*L_entropy.
```

For foundation training, q is absent everywhere. For TREAT and FREE, true q
is used everywhere. For SET, `q_SET=0.5` and `J_SET` replace order everywhere.
REVERSED and FOUNDATION-ONLY have no order-stage optimizer.

All new `g`, residual and order-stage critic hidden/output tensors follow the
global initialization rule and its named zero-output/`0.001` exceptions.
Automatic differentiation uses these exact tie conventions: `ReLU'(0)=0`;
the derivative of scalar `clip(x,l,u)` is zero at and outside either boundary
and one strictly inside; an exact equality between the two PPO `min` operands
uses the arithmetic mean of their two gradients. A combined gradient whose
norm is exactly `0.8` is unchanged.

One backward pass differentiates only the named trainable tensors. Clip the
combined gradient once to global L2 norm `0.8`. One persistent AdamW optimizer
uses

```text
beta_1=0.9
beta_2=0.999
epsilon=1e-8
learning_rate=3e-4
weight_decay=1e-5
```

on every trainable matrix and bias with ordinary decoupled decay. Moments start
at zero and never reset. With globally one-based optimizer index `t`, the exact
float32 update is

```text
m_t=0.9*m_(t-1)+0.1*g_t
v_t=0.999*v_(t-1)+0.001*g_t^2
mhat_t=m_t/(1-0.9^t)
vhat_t=v_t/(1-0.999^t)
theta_t=theta_(t-1)
        -3e-4*(mhat_t/(sqrt(vhat_t)+1e-8)
               +1e-5*theta_(t-1)).
```

For each foundation optimizer `t=1,...,1920`; for each order-stage arm
optimizer `t=1,...,1152`. No index or moment resets between PPO updates.

Each update makes three epochs over a fixed
address-keyed permutation split into four nonempty minibatches, exactly 12
AdamW steps. There is no early stop, learning-rate schedule, target tuning,
checkpoint selection, auxiliary order/graph loss, latent-state reconstruction,
reward normalization or running observation statistic.

## Final evaluation and direct mission endpoints

After all 72 order-stage checkpoints and all 24 foundation checkpoints are
technically accepted, evaluate each controller in

```text
FOUNDATION, TREAT, FREE, REVERSED, SET
```

on 120 fresh paired episodes per replicate in each of the six registered
regimes. Fixed cells balance graph order 60/60; switch cells jointly balance
graph order and switch time. Evaluation uses deterministic lexicographic
argmax of finite logits. There is no evaluation sampling, temperature,
adaptation or update.

For controller `A` and replicate `s`, on the four target regimes define

```text
U_episode=1[safe dock]*(1-t_dock/36.4)
V_A,s=pooled mean U_episode
W_A,s=minimum regime-specific mean U_episode
P_A,s=pooled safe-docking fraction
T_A,s=mean(t_dock if safe else 36.4 s)
E_A,s=mean over active-through-terminal ticks of
      (1/4)*sum_i (a+0.35*r_i)^2
O_A,s=maximum regime-specific cable-overload/drop fraction
G_A,s=maximum regime-specific gantry-contact fraction
L_A,s=maximum regime-specific pallet-attitude-loss fraction
F_A,s=maximum regime-specific formation-loss fraction.
```

Here `t_dock=0.1*n'` seconds at the first post-update safe-docking tick. `V`
is direct safe-docking performance with completion slack. `W` is direct
worst-regime robustness over exactly the four target schedules. Failure and
timeout have zero completion value and `T=36.4 s`. Energy excludes masked
post-absorption slots. Aggregate training reward activates no branch.

## Final competence and simultaneous inference

For TREAT, FREE and SET, compute safe-docking fractions in the four
`k in {5,11} x graph order` competence cells and one pooled fraction. Across
24 replicates, the 15 two-sided Student-t intervals form one Bonferroni family
at family error `0.05`.

A cell is `PASS` when its lower bound is strictly above `0.70`, `FAIL` when
its upper bound is at or below `0.70`, and `UNRESOLVED` otherwise. Pooled
competence uses threshold `0.82` with the same rule. A controller is competent
only if all five requirements pass. Treatment, FREE and SET competence are
mandatory for treatment retention. FREE and SET registered-`K_train`
competence are mandatory for decline. Foundation competence remains bound by
its prior disjoint all-regime gate. These final FREE/SET tests do not establish
target-schedule competence by themselves; target-distribution behavior remains
inside the direct `V/W` robustness comparisons.

Across the 24 paired replicates, compute 26 simultaneous two-sided Bonferroni
Student-t intervals at family error `0.05`:

1. `V_T-V_C` and `W_T-W_C` for each
   `C in {FOUNDATION,FREE,REVERSED,SET}`: eight intervals;
2. `P_T-P_FOUNDATION` and `E_T-E_FOUNDATION`: two intervals; and
3. each of `O_T-O_C`, `G_T-G_C`, `L_T-L_C`, `F_T-F_C` for all four controls:
   sixteen intervals.

The prospective superiority margins are

```text
V over FOUNDATION: +0.025
V over FREE:       +0.015
V over REVERSED:   +0.020
V over SET:        +0.020

W over FOUNDATION: +0.020
W over FREE:       +0.0125
W over REVERSED:   +0.0175
W over SET:        +0.0175.
```

The nonselected primary endpoint must be noninferior to FOUNDATION with lower
bound strictly above `-0.015`. Safe-docking rate must be noninferior to
FOUNDATION with lower bound strictly above `-0.03`. Physical non-harm requires

```text
upper(E_T-E_FOUNDATION)<0.06
upper(O_T-O_C)<0.025 for every C
upper(G_T-G_C)<0.025 for every C
upper(L_T-L_C)<0.025 for every C
upper(F_T-F_C)<0.025 for every C.
```

For higher-is-better margin `m`, a comparison is `PASS` when the adjusted
lower bound is `>m`, `FAIL` when the adjusted upper bound is `<=m`, and
`UNRESOLVED` otherwise. For upper-margin non-harm, `PASS` means upper is
strictly below the margin, `FAIL` means lower is at or above it, and otherwise
the state is `UNRESOLVED`. Exact boundary contact never passes.

Define a `V` route and a `W` route. A route passes only when foundation
competence, opportunity, TREAT/FREE/SET competence, that route's four
superiority comparisons, the other-primary noninferiority comparison, safe-
docking noninferiority and every physical non-harm comparison pass. A route is
`EXCLUDED` when any necessary item is `FAIL`; otherwise it is `UNRESOLVED`.

No unadjusted subgroup, point estimate, per-replicate sign, training curve,
reward, graph cell, switch time, support action or later physical revelation
activates a branch.

## Exhaustive first-true result-to-action map

Apply exactly:

For this map, a stage is “required” only when every preceding prerequisite
passes. A downstream stage prospectively forbidden by a valid prerequisite
nonpass is intentionally unopened, neither required nor incomplete.

1. `INVALID-EVIDENCE` if any stage required by the realized prerequisite path
   is incomplete; registered source,
   identity, pairing, event-map, public-aliasing, support-graph, set-invariance,
   strict-containment, foundation immutability, external-`k`, direct-endpoint,
   workload, atomicity or inference conformance fails; any partial inspection,
   per-`k` parameter/update, post-absorption policy query or nonfinite value
   exists. No scientific treatment conclusion follows.
2. `COMMON-CONTROLLER-COMPETENCE-NOT-ESTABLISHED` if the complete valid
   foundation competence prerequisite does not pass. No order-stage parameter
   exists and no order-treatment conclusion follows.
3. `TARGET-ORDER-OPPORTUNITY-NOT-ESTABLISHED` if foundation competence passes
   but the complete valid foundation-conditioned opportunity gate does not
   pass. No order-stage parameter exists. This declines only this exact target
   opportunity purchase, not physical order generally.
4. `RETAIN-ORDERED-SUPPORT-GRAPH-SLACK` if either final direct-value route
   passes. Retain only this exact support-graph treatment, task, foundation,
   finite budget and external-`k` registry.
5. `DECLINE-ORDERED-SUPPORT-GRAPH-SLACK` if opportunity and foundation
   competence pass, FREE and SET are registered-`K_train` competent, and both
   final routes are
   `EXCLUDED`. Decline only this exact structured treatment; a descriptive
   FREE-versus-SET pattern cannot create a new branch.
6. `DIRECT-TARGET-BOUND-ORDER-VALUE-NONIDENTIFIED` otherwise, including
   treatment/control competence uncertainty, imprecise direct contrasts,
   unresolved harm, one excluded and one unresolved route, or any valid pattern
   that neither retains nor decisively declines the exact treatment.

This map opens no automatic checkpoint, budget, seed, threshold, architecture,
relation assay, Stage B, new event family, second surface, deployment or flight
successor.

## Fresh identities, blinding and atomicity

Only after a distinct future empirical authorization may CM draw a fresh
256-bit operating-system master. The new namespace is

```text
SCDMP-TBCC-ORDER-VALUE-r01/replicate/<uint32_be(s)>.
```

Disjoint HMAC-SHA256 domains bind foundation initialization/training,
foundation competence, opportunity states/actions, adapter initialization and
training, final evaluation, setup order, switch time, disturbances, categorical
uniforms and minibatch permutations. No prior SCDMP identity or coordinate is
imported.

Foundation checkpoints, competence result and opportunity result are create-
only and stage-atomic. A valid prerequisite nonpass installs its exact terminal
branch atomically and makes later stages inapplicable rather than incomplete.
Order-stage identity materialization is forbidden until both complete gates
pass. Final evaluation opens only after all eligible final checkpoints are
technically accepted. Any final scientific result is atomic across every
replicate, controller, regime, competence item, interval and branch required by
its realized path. No partial value, arm, seed, graph, regime, endpoint or
interval may be opened or reported.

## Prospective workload and full cost

Maximum registered foundation training is

```text
24 replicates x 160 updates x 12 episodes = 46,080 episodes
16,773,120 allocated primitive slots
2,465,280 maximum real policy queries
46,080 AdamW steps
24 final foundation checkpoints.
```

Foundation competence evaluation is

```text
24 x 1 controller x 6 regimes x 120 episodes = 17,280 episodes
6,289,920 allocated primitive slots
768,960 maximum real policy queries.
```

The full-mission opportunity panel is

```text
24 x 2 k x 16 states x 2 graphs x 18 actions x 4 tapes
  = 110,592 rollouts
40,255,488 allocated primitive slots
4,313,088 maximum frozen-foundation policy queries
110,592 forced first-action interventions.
```

Maximum order-stage training is

```text
24 x 3 arms x 96 updates x 12 episodes = 82,944 episodes
30,191,616 allocated primitive slots
4,437,504 maximum real policy queries
82,944 AdamW steps
72 final order-stage checkpoints.
```

Final evaluation is

```text
24 x 5 controllers x 6 regimes x 120 episodes = 86,400 episodes
31,449,600 allocated primitive slots
3,844,800 maximum real policy queries.
```

The complete upper bound is therefore

```text
343,296 complete episodes/rollouts
124,959,744 allocated primitive simulator slots
15,829,632 maximum real policy queries
110,592 forced first-action interventions
129,024 AdamW steps
96 final learned checkpoints.
```

Early absorption can reduce realized integration and decision work. Realized
counts are recorded only after an atomic result and have no branch, stopping,
repair or claim role.

Prospective end-to-end cost is `24--40` experienced engineer-days for the new
hybrid support-graph plant, analytic fixtures, foundation gating, full-mission
opportunity service, models, lifecycle, runner, inference and independent
review; `80--240` CPU core-hours, approximately `80--240` serialized single-
core hours, or `24--72` elapsed hours with four independent CPU workers
including merge/I/O; minimum `12 GiB` and preferred `20 GiB` RAM; at most
`10 GiB` scratch and `4 GiB` durable artifacts. No GPU is required. These are
EM planning bounds awaiting independent CM static feasibility and cost
acceptance. A material cost-class change returns to Root before construction.

## Strongest alternatives and claim ceiling

The strongest alternatives are a foundation-conditioned full-mission bottleneck
despite nominal competence; later public tension/roll feedback making chronology
redundant; generic conservative graph-load control; foundation-only progress;
finite-budget regularization of the structured adapter versus underoptimization
of FREE; zero-output residual geometry; reward and critic credit; common inner
stabilization; numeric-`k` conditioning; action-catalogue limitations; graph/order
or switch imbalance; the binary middle-event classifier; the prospective graph-
slack surrogate being aligned with the simulator by construction; and the
simulator-specific cable-assignment abstraction. Controls bound but do not
eliminate these explanations.

The maximum possible positive claim is:

> In the exact planar fixed-four-UAV `QUAD-UAV-PALLET-GANTRY-24P5M-v1`
> simulator, after one order-erased shared controller package established the
> registered full-mission competence prerequisite and was frozen, one
> prospectively specified support-graph adapter with one parameterization across
> the registered fixed and switched external hold periods improved direct safe-
> docking value or worst-regime robustness over the frozen foundation, a
> registered-`K_train`-competent strictly containing order-aware controller,
> tied reversal and a registered-`K_train`-competent unrestricted order-
> insensitive controller, while remaining safe-docking-noninferior to the
> foundation, energy-nonharmful relative to the foundation, and cable-,
> contact-, attitude- and formation-nonharmful relative to every registered
> control under the exact prospective margins.

No outcome establishes unique support-graph mediation, general chronology,
semigroup composition, arbitrary event sequences, arbitrary `k`, variable
`N`, decentralized cooperation, another payload, another simulator/surface,
six-degree-of-freedom flight dynamics, real-aircraft transfer, aviation safety,
deployment or flight value. The two middle events still provide one binary
order bit. A negative or nonidentified branch concerns only this exact
target/treatment/foundation package and does not delete SCDMP.

## Closure, activity and authority boundary

The complete revision becomes immutable only after existing-conversation
ChatGPT Pro `CLOSED` and same-direction EM intake. This definition/review card,
provider question and owner intake are not scientific activity. Scientific
activity would begin immediately before the first executable simulator or
controller encoding, task-informed executable fixture, fresh master, identity,
stochastic coordinate, model, checkpoint, rollout or outcome is materialized,
whichever comes first.

The current envelope authorizes only this definition, existing-SCDMP-Pro
mathematical/causal closure, EM intake and paired-CM static bindability,
observability, comparator feasibility and full-cost assessment. It authorizes
no source, build, test, probe, fixture, identity, coordinate, model, checkpoint,
training, evaluation, result, compute lease, relation assay, Stage B, second
surface, production, deployment or flight activity.

If this object cannot be Pro-closed or CM-statically accepted without a
science-bearing or material cost-class change, return the exact defect. Do not
import an old object, add a menu or silently change a condition.

## Physics provenance boundary

Primary literature supports multi-quadrotor cable-suspended-load dynamics,
hybrid cable assignments and bounded sample-and-hold reasoning only at a
general level. It does not validate this exact pallet, event map, action
catalogue, coefficients, support-graph treatment or learned result.

- K. Sreenath and V. Kumar, “Dynamics, Control and Planning for Cooperative
  Manipulation of Payloads Suspended by Cables from Multiple Quadrotor Robots,”
  RSS 2013: https://www.roboticsproceedings.org/rss09/p11.pdf
- X. Han et al., “Controller Design and Disturbance Rejection of
  Multi-Quadcopters for Cable Suspended Payload Transportation Using Virtual
  Structure,” IEEE Access 2022: https://doi.org/10.1109/ACCESS.2022.3222031
- X. Liang et al., “Fault-tolerant control for the multi-quadrotors cooperative
  transportation under suspension failures,” Aerospace Science and Technology
  2021: https://doi.org/10.1016/j.ast.2021.107139
- H. Omran et al., “Stability analysis of some classes of input-affine
  nonlinear systems with aperiodic sampled-data control,” Automatica 2016:
  https://doi.org/10.1016/j.automatica.2016.02.013

## Existing-ChatGPT-Pro mathematical/causal closure request

Continue only the existing dedicated SCDMP ChatGPT Pro conversation. Review
this complete revision as one prospective scientific object, not code,
repository state, runtime, files, hashes, receipts, implementation acceptance
or portfolio priority.

Determine whether:

1. the named pallet/gantry task, event maps and latent support assignments form
   a genuine same-multiset noncommuting simulator intervention with exact first-
   renewal public aliasing and direct mission relevance;
2. the single treatment-independent order-erased foundation, all-replicate
   competence gate and full-mission foundation-conditioned opportunity assay
   prospectively separate common competence and target opportunity from order
   treatment without menus or post-result repair;
3. the graph-slack treatment is globally single-valued and supplies only the
   claimed nonnegative coordinatewise score tilt; FREE's deployed actor class
   analytically and strictly contains it modulo softmax constants; tied
   REVERSED, SET-FREE and FOUNDATION-ONLY isolate the relevant alternatives;
4. the shared fixed/switched-`k` law, exact training, endpoints, competence
   families, margins, routes and exhaustive branches are mathematically and
   causally noncontradictory;
5. identities, stage atomicity, workload, cost, strongest alternatives,
   activity boundary and claim ceiling are prospective and complete; and
6. no statement imports r02 evidence or overclaims general chronology,
   semigroup reasoning, arbitrary `k`, variable `N`, real-aircraft safety,
   deployment or flight.

Return exactly one leading line:

```text
CLOSED
```

or

```text
REVISION_REQUIRED
```

Then state every exact remaining mathematical, causal, target, competence,
opportunity, comparator, endpoint, inference, branch, cost, activity-boundary or
claim defect. Do not propose r02 repair, old checkpoint/coordinate reuse, a
budget/seed/threshold/architecture menu, source, construction, activity,
relation assay, Stage B, second surface or portfolio action.
