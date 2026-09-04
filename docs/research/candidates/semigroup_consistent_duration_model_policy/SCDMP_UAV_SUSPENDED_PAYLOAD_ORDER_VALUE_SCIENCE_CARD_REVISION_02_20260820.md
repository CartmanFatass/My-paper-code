# SCDMP UAV suspended-payload order-value science card — revision 02

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-UAV-SUSPENDED-PAYLOAD-ORDER-VALUE
task=TRI-UAV-SLING-CORRIDOR-36M-v1
treatment=TAUT-GUST-RISK-TILT
revision=SCDMP-UAV-SP-ORDER-VALUE-SCIENCE-20260820-02
owner=EM_semigroup_consistent_duration_model_policy
stage=definition_only
portfolio_envelope=SCDMP-UAV-SUSPENDED-PAYLOAD-ORDER-VALUE-DEFINITION
scientific_activity_started=false
external_review_state=revision_01_pro_defect_repaired_awaiting_same_pro_closure
source_build_test_probe_authorized=false
identity_coordinate_model_checkpoint_authorized=false
training_evaluation_compute_lease_authorized=false
relation_assay_authorized=false
stage_b_authorized=false
uav_production_deployment_flight_authorized=false
```

## Question and target value

This card freezes one new target-bound planar simulator task:
`TRI-UAV-SLING-CORRIDOR-36M-v1`. Three fixed quadrotor carriers transport one
cable-suspended payload through a straight inspection corridor. It asks:

> Can one shared finite-budget controller use whether a crosswind impulse
> occurred before or after cable retension to improve direct payload-delivery
> performance or worst-regime robustness when the externally announced
> command-hold period `k` is fixed at unseen values or switches in-episode,
> relative to a competent strictly containing direct controller, the identical
> treatment under tied reversal, and a competent unrestricted
> order-insensitive controller?

The sole treatment is `TAUT-GUST-RISK-TILT`. It is frozen from the task's
unilateral-cable and zero-order-hold physics before source, identity, model or
outcome exists. It is trained only by mission return. There is no transition,
relation, order-label, segment, checkpoint or representation objective.

This is a finite fixed-`N=3` UAV-simulator question. It does not reuse or reopen
the completed r07/SRF checkpoint route.

## Exact isolation from prior SCDMP work

No r07 or SRF checkpoint, parameter, word, factor, threshold, margin, seed,
master, coordinate, random tape, optimizer state, step budget, representation,
subgroup, estimate, branch result or claim enters this object. No generic
ground-carrier draft supplies a constant or authority. The new task,
treatment, controls, identities, coordinates and inference law are prospective
and independent.

The only inherited direction-level fact is the portfolio fence: answer the
new end-to-end UAV value question without another checkpoint repair, relation
assay or Stage B.

## Named physical task

### Plant, clocks and state

`TRI-UAV-SLING-CORRIDOR-36M-v1` is a dimensioned planar abstraction, not a
flight-dynamics or safety certificate. Three identical quadrotor carriers hold
a point payload on three unilateral elastic cables while tracking a level
triangular formation down a `36 m` corridor. One primitive physics tick is
`Delta t=0.1 s`; the horizon is `420` ticks (`42 s`). Delivery occurs when the
payload first reaches `x>=36 m` without a registered physical failure.

At primitive tick `n`, the simulator state is

```text
X_n=(x,v,phi,omega,z,f,tau_1,tau_2,tau_3,
     u_1,n-1,u_2,n-1,u_3,n-1,d,m,n).
```

`x` and `v` are payload corridor position and forward speed; `phi` and `omega`
are payload swing angle and rate; `z` is filtered cable-overload exposure; `f`
is formation-tracking error; `tau_i` are normalized cable tensions; `u_i,n-1`
are prior held commands; `d` is an unobserved normalized loss of cable/damper
reserve; and `m in {0,1}` is the common slack/taut mode.

The initial public state is

```text
x=0, v~Uniform[0,0.04] m/s,
phi~Uniform[-0.015,0.015] rad, omega=0,
z=f=tau_i=0, u_i,-1=0, d=0, m=0.
```

The initial `v` and `phi` draws are paired across all arms. The fixed roster,
payload mass class, cable geometry, primitive clock and all failure limits are
identical for every arm.

### Passive equal-slot event pair and exact order noncommutation

Before control, the payload is locked in a staging cradle. Two visible,
equal-duration, action-independent event slots at setup ticks `n=-2` and
`n=-1` contain exactly one
`RETENSION` event and one `CROSSWIND` event:

```text
RETENSION: m <- 1
CROSSWIND: d <- clip(d + 0.55*m,0,1).
```

`RETENSION` represents a common slack-to-taut cable transition.
`CROSSWIND` represents the same lateral impulse in either slot. While slack,
the cradle carries the impulse; while taut, the impulse loads a sacrificial
cable/damper element and reduces latent reserve. After the second slot the
cradle re-centers every public kinematic/tension variable and releases the
payload. It does not reset `d` or `m`.

The two prospectively balanced histories are therefore

```text
RG = RETENSION then CROSSWIND: m=1, d=0.55
GR = CROSSWIND then RETENSION: m=1, d=0.
```

They have identical event identities, magnitudes, durations, final taut mode,
mission time and public post-event observation. They differ only in latent
reserve. Setup slots are outside the 420-tick mission horizon: the first
renewal is exactly `n=0`, and setup slots contribute no reward, completion
time, energy denominator or workload tick. Both raw event tokens are broadcast
at their common setup slots;
no controller receives `d`, a safe/damaged label, order-cell identity, seed,
scenario identity or future `k` schedule.

This registered hybrid event map is the task definition. Literature on
multi-quadrotor suspended loads supports unilateral cable tension,
slack/taut mode switches and retension resets; it does not establish this
particular sacrificial-damper event pair as a real-aircraft effect. The exact
pair is therefore claimed only inside this simulator.

### Observation, joint action and zero-order hold

At every renewal boundary the common deployable observation is

```text
o_n=(x/36,v/1.8,phi/0.48,omega/0.5,z/0.55,f/0.42,
     tau_1/1.25,tau_2/1.25,tau_3/1.25,
     u_1,n-1/2,u_2,n-1/2,u_3,n-1/2,n/420,k_n/14) in R^14.
```

Every controller also receives the same two raw setup-event tokens. At the
first renewal the numeric `o_n` is exactly aliased between `RG` and `GR`.
Later tensions, swing and overload may reveal action-dependent consequences;
that shared physical feedback is not an order label.

The centralized fixed-roster policy chooses one lexicographically indexed
joint forward-demand command

```text
u=(u_1,u_2,u_3), each u_i in {0,1,2},
```

from 27 legal commands. A common inner stabilizer, identical for all arms,
maps the discrete demand to carrier thrust and level-formation tracking. The
joint command is held for the currently announced external `k_n` primitive
ticks, or until success/failure. No arm can sense, communicate, terminate or
act mid-hold. Events and safety are integrated on the primitive clock.

### Frozen planar dynamics and failure law

For one primitive tick define

```text
a = mean_i u_i
b = max_i |u_i-a|
tau_i' = 0.42 + 0.17*u_i + 0.11*|u_i-a|
         + 0.20*d*a^2 + 0.07*|phi|
cap(d) = 1.04 - 0.16*d
epsilon = max(0,max_i tau_i' - cap(d)).
```

Two fresh address-stable disturbances, shared across paired arms, are
independently equiprobable in

```text
eta_v in {-0.004,+0.004}
eta_omega in {-0.006,+0.006}.
```

The registered update is

```text
omega' = 0.90*omega - 0.12*phi + 0.055*b + 0.035*d*a + eta_omega
phi'   = clip(phi + 0.1*omega',-0.70,0.70)
v'     = clip(0.94*v + 0.06*a - 0.018*d*a^2
              - 0.025*|phi'| + eta_v,0,1.8)
x'     = x + 0.1*v'
z'     = 0.86*z + epsilon
f'     = 0.84*f + 0.09*b + 0.08*|phi'|.
```

The remaining next-state assignments are exact:

```text
tau_i <- tau_i'
u_i,n-1 <- u_i
d' <- d
m' <- m
n' <- n+1.
```

The first occurrence of any of the following is an absorbing mission failure:

```text
cable overload/drop: z'>0.55
payload swing-envelope violation: |phi'|>0.48
formation-tracking loss: f'>0.42.
```

Timeout is unsuccessful delivery but is not relabeled as a safety failure.
All post-transition predicates are evaluated together. Any physical failure
dominates same-tick `x'>=36` delivery. Physical failure labels are nonexclusive:
if two or three limits first cross on the same tick, every crossed `O/G/F`
indicator is recorded. Post-absorption slots contain no physics integration,
policy query, reward or energy command; they exist only as masked allocation
slots for equal workload accounting. The direct mission endpoints keep the
three physical failure modes separate.

Per-tick training reward is

```text
r_n = 0.02*(x'-x) - 0.001*mean_i(u_i^2)
      - 0.002*(phi')^2 - 0.002*(f')^2,
```

plus `+1` at safe delivery, `-1` at a physical failure and `-0.5` at timeout.
No claim-bearing endpoint is defined by this scalar reward.

### Prospective order and `k` relevance

For balanced maximum demand `u=(2,2,2)` at zero swing,

```text
tau_i'=0.76, cap=1.04 in GR (d=0)
tau_i'=1.20, cap=0.952 in RG (d=0.55).
```

Thus the identical action has no instantaneous overload excess in `GR` but an
excess of `0.248` in `RG`; repeated held ticks accumulate `z`. Balanced demand
`u=(1,1,1)` stays below capacity in both histories but advances more slowly.
An externally longer hold removes recovery opportunities and repeats the same
loading/swing dynamics before a new decision. These are exact task-law facts,
not observed competence, value or treatment evidence.

## External-`k` registry and single parameterization

Training and all hyperparameter choice use only fixed

```text
K_train={4,10}.
```

Frozen target evaluation uses

```text
fixed 6
fixed 14
6->14
14->6.
```

In switch regimes the change occurs at a renewal boundary at tick `168` or
`252`, balanced and independent of event order and all disturbances. Both
times are common boundaries for 6 and 14. The new `k` is revealed only when it
becomes current. Setup events always precede control on the primitive clock and
never move across an observation boundary with `k`.

Every learned arm has one weight vector, one optimizer state, one
normalization and one scalar `k` input across every registered period. There
is no per-`k` head, table, expert, initializer, optimizer, training run,
fine-tuning, reset or evaluation update. A `k` switch does not reset any model
state. The policy is feed-forward; only the physical plant carries state.

## Treatment and controls

### Physics-specified joint-risk ordering

For a legal joint command define

```text
rho(u)=0.75*(a/2) + 0.25*(b/(4/3)), in [0,1].
```

`rho` is a prospectively frozen surrogate ordering anchored to collective
cable demand and formation imbalance. It is not claimed to rank exact
one-step or long-horizon physical hazard globally: discrete joint-action
redistribution and signed swing dynamics can violate such a ranking. It is not
learned, fitted or selected from outcomes.

All arms use a two-hidden-layer SiLU base actor
`B:R^14->R^27`, widths `64,64`. A one-hidden-layer SiLU risk-scale network
`g:R^14->R`, width `32`, gives `alpha(o)=softplus(g(o))`. The critic receives
`concat(o,q) in R^15`, uses SiLU widths `64,64`, and emits one scalar. Affine
maps include biases. Float32 model/optimizer arithmetic, Xavier-uniform
row-major weight initialization and zero biases are frozen.

### Sole treatment: `TAUT-GUST-RISK-TILT`

The exact binary chronology statistic is

```text
q(RG)=1
q(GR)=0.
```

Treatment action logits are

```text
logit_T(u|o,q)=B_theta(o)_u - q*alpha_theta(o)*rho(u).
```

The base actor does not receive `q`; the risk tilt is the only direct actor
path from event order. Because `alpha>=0`, changing `q` from 0 to 1 is an
exponential tilt toward lower `rho`, so the action-risk distribution is
monotone without constraining potentially stabilizing individual thrust
coordinates. `o`, including current `k`, may change the learned strength of
the tilt. The policy is categorical over all 27 commands and is learned only
from duration-correct mission return.

The treatment has exactly `12,637` trainable parameters: `6,875` in `B`,
`513` in `g`, and `5,249` in the critic.

### Competent strictly containing `FREE-DIRECT`

`FREE-DIRECT` has the complete treatment actor/critic and adds an unrestricted
residual actor `R_psi:R^15->R^27`, widths `64,64`:

```text
logit_FREE(u|o,q)=B_theta(o)_u-q*alpha_theta(o)*rho(u)
                  +R_psi(o,q)_u.
```

The residual output layer starts exactly at zero. Setting all residual
parameters to zero reproduces every treatment policy. A residual that raises a
higher-risk logit only when `q=1` violates the treatment ordering, establishing
strict rather than nominal containment. `FREE-DIRECT` has `19,576` trainable
parameters, including `6,939` in the residual. Its additional optimization
geometry is visible and remains a strongest finite-budget alternative; no
disconnected padding hides it.

### Tied `REVERSED` chronology control

`REVERSED` is not trained. It evaluates the final treatment weights on the
same paired target scenarios while replacing only the actor's chronology
input by

```text
q <- 1-q.
```

Current physical observation, raw event multiset, `k`, action set, reward,
disturbance tape, weights and physical time remain unchanged. It therefore
tests the wrong orientation without giving another fit an opportunity to undo
a bijective label reversal. The critic is unused in evaluation.

### Strongest order-insensitive control: `SET-FREE`

`SET-FREE` is independently trained with the exact `FREE-DIRECT` architecture,
parameter count and unrestricted residual, but its verified set compositor
replaces chronology with

```text
q_SET=0.5
```

for both event permutations. It receives both event identities and magnitudes
as an unordered multiset, current public physics and `k`, but no event
position, timestamp, recency, padding or trace from which order can be
reconstructed. It is exactly invariant to swapping `RETENSION` and
`CROSSWIND` while retaining full direct-action flexibility and later shared
physical feedback.

### Equal information, action, work and optimizer opportunity

For each fresh seed, identically shaped shared tensors in treatment,
`FREE-DIRECT` and `SET-FREE` start byte-identically. Residual hidden tensors
use paired disjoint addresses and both residual output layers start at zero.
All trained arms receive the same event identities, primitive observations,
current `k`, action set, actuator bounds, physical-time slots, paired exogenous
scenarios, reward, critic information, episode budget, environment-slot
budget, update count, optimizer, hyperparameter opportunity, stopping law and
evaluation information. The only information transform is the registered
chronology removal in `SET-FREE`; the only class enlargement is the explicit
residual in the two FREE controllers. `REVERSED` shares treatment weights.

The two-event statistic equals last-event identity in this task. Even a
positive result therefore identifies only correct use of this registered
binary chronology bit, not recurrent composition or general sequence
reasoning.

## Frozen training law

There are `18` fresh paired training replicates. For each replicate, each of
the three learned arms (`TREAT`, `FREE`, `SET`) receives `144` PPO updates.
Every update allocates 12 complete horizon slots: six at `k=4` and six at
`k=10`, with exactly three `RG` and three `GR` episodes inside each `k`.
Initial state and disturbance addresses are paired across arms; on-policy
actions may make later physical states diverge.

At every real training renewal, the categorical action is sampled by inverse
CDF in the fixed lexicographic 27-action order using one fresh address-stable
`Uniform[0,1)` action variate. The same variate address is paired across arms;
different logits may select different actions. No other exploration process,
temperature or action noise exists.

Success or failure enters an absorbing state through tick 420. No policy is
queried after absorption. Absorbing slots count toward equal physical-time
allocation but are masked from loss.

At a real renewal `j` with realized duration `h_j<=k_j`, the rollout-time
actor and critic first use the arm-specific chronology input defined below.
Immediately after all twelve slots are collected, snapshot

```text
logp_old,j = log pi_old(a_j|o_j,q_j)
V_old,j = V_old(o_j,q_j)
```

for every valid record. The complete old actor/critic parameter values,
`logp_old,j` and `V_old,j` are stop-gradient and immutable through all four
epochs. Define once

```text
rbar_j = sum_(ell=0)^(h_j-1) gamma^ell*r_(tau_j+ell)
delta_j = rbar_j
          + 1[nonterminal_j]*gamma^h_j*V_old,j+1
          - V_old,j
A_raw,j = delta_j
          + 1[nonterminal_j]*(gamma*lambda)^h_j*A_raw,j+1
Y_j = stop_gradient(A_raw,j + V_old,j),
gamma=0.996, lambda=0.94,
```

with backward recursion ending at `A_raw=0` after delivery, physical failure
or timeout. Thus both discount and trace decay advance on the primitive clock.
The value loss targets the immutable unnormalized `Y_j`. Once per arm/update,
all valid `A_raw,j` are transformed once into the immutable actor advantage

```text
Ahat_j = stop_gradient(
  (A_raw,j-mean_all_valid(A_raw))/sqrt(popvar_all_valid(A_raw)+1e-8)
).
```

The displayed fixed observation scaling is the sole observation
normalization; there are no running state/reward/value statistics.

For each current minibatch `M`, with every valid renewal record weighted
equally regardless of realized `h_j`, define the current-policy ratio and the
only legal scalar losses:

```text
ratio_j(theta) = exp(log pi_theta(a_j|o_j,q_j)-logp_old,j)

L_policy = -mean_(j in M) min(
  ratio_j(theta)*Ahat_j,
  clip(ratio_j(theta),0.82,1.18)*Ahat_j
)

L_value = 0.5*mean_(j in M) (
  V_theta(o_j,q_j)-Y_j
)^2

L_entropy = mean_(j in M) H(
  pi_theta(.|o_j,q_j)
)

L_total = L_policy + 0.55*L_value - 0.012*L_entropy.
```

Entropy is that of the current 27-action categorical actor. There is no Huber
loss, value clipping, KL term, dual clipping, primitive-time weighting or
other loss. Actor, critic and entropy reductions use the identical valid
records. One backward pass of this single joint loss differentiates the
complete arm parameter set: `B`, `g`, critic, and, for `FREE`/`SET`, the
residual actor. There are no separate actor/critic optimizers.

The complete combined float32 gradient is clipped once before optimization:
if its global L2 norm over every trainable scalar exceeds `0.9`, multiply every
gradient by `0.9/||g||_2`; a zero or smaller gradient is unchanged. A single
AdamW optimizer then updates every named trainable matrix and bias, including
biases, using

```text
m_t = 0.9*m_(t-1) + 0.1*g_t
v_t = 0.999*v_(t-1) + 0.001*g_t^2
mhat_t = m_t/(1-0.9^t)
vhat_t = v_t/(1-0.999^t)
theta_t = theta_(t-1)
          - 2.5e-4*(mhat_t/(sqrt(vhat_t)+1e-8)
                     + 2e-5*theta_(t-1)).
```

This is decoupled weight decay on all matrices and biases. For each arm,
`m_0=v_0=0` is created once, optimizer step `t` is globally one-based from 1
through `144*16=2,304`, and parameters, moments and bias-correction index never
reset at an epoch or PPO-update boundary. AMSGrad, maximize mode and every
other optimizer variant are absent.

For `TREAT` and `FREE`, true `q in {0,1}` is used in every actor, critic,
rollout log probability, old-value snapshot, GAE bootstrap and loss occurrence.
For `SET`, `q_SET=0.5` replaces true chronology in every one of those
occurrences; physical rewards still arise from the correct latent task state,
but no true chronology bit reaches its actor or critic optimizer. `REVERSED`
remains evaluation-only and has no critic, rollout loss or optimizer operation.

Each update makes four epochs over all valid decision records. In each epoch,
a seed/update/epoch-keyed permutation is split into four nonempty minibatches
whose sizes differ by at most one, giving exactly 16 joint AdamW steps per
update. There is no early stop, architecture/trainer menu, learning-rate
search, checkpoint selection or target-`k` tuning. Only update 144 is eligible.

## Fresh identities, blinding and atomicity

Only after a later empirical authorization may the CM generate a fresh
256-bit master with the operating-system cryptographic RNG. Eighteen replicate
keys are derived under the new HMAC-SHA256 prefix

```text
SCDMP-UAV-SP-ORDER-VALUE-r02/replicate/<uint32_be(s)>.
```

Disjoint domains bind initialization, training initial state, training
setup-event order, training disturbances, training action uniforms, minibatch
order, evaluation state, evaluation setup-event order, evaluation switch time,
evaluation disturbances, support states and support disturbances. No prior
namespace or materialized identity is imported.

Training frontiers are create-only and blinded by replicate/arm. Evaluation
opens only after all 54 final learned checkpoints are technically accepted.
The scientific result is atomic across all 18 replicates, four controllers,
six regimes and every qualification/endpoint. No partial arm, regime,
endpoint, interval, seed or branch may be inspected or reported.

At evaluation every controller, including `REVERSED`, uses deterministic
lexicographic argmax of its 27 frozen logits. Exact logit ties select the
lexicographically first joint action. No evaluation action uniform, sampling,
temperature or exploration noise exists.

## Evaluation and direct mission endpoints

For every replicate and controller in
`{TREAT,FREE,REVERSED,SET}`, run 120 fresh paired episodes in each of

```text
fixed 4, fixed 10, fixed 6, fixed 14, 6->14, 14->6.
```

Fixed 4 and 10 are competence-only diagnostics. The four held-out/switched
regimes form the claim-bearing target panel. Event order is exactly balanced
in every fixed cell. Event order and switch time `{168,252}` are jointly
balanced in switch cells. All controllers share each exogenous scenario tape.

For controller `A` and replicate `s`, on the four target regimes define

```text
P_A,s = pooled safe-delivery fraction
W_A,s = minimum regime-specific safe-delivery fraction
T_A,s = mean(delivery time if safely delivered, else 42 s)
E_A,s = mean over active through-terminal primitive ticks of mean_i(u_i^2)/4
O_A,s = maximum regime-specific cable-overload/drop fraction
G_A,s = maximum regime-specific swing-envelope-violation fraction
F_A,s = maximum regime-specific formation-loss fraction.
```

Here `T` equals safe-delivery time only for a delivered episode and equals
exactly `42 s` for every physical failure or timeout; it is not the earlier
failure time. `E` ends on the terminal tick and never includes masked
post-absorption slots. `P` is direct task performance and `W` external-`k`
robustness. `T` is restricted physical completion time, `E` normalized
commanded effort, and
`O,G,F` are distinct worst-regime physical non-harm endpoints. Aggregate
reward cannot activate a branch.

## Competence, order support and action sensitivity

For each of `TREAT`, `FREE` and `SET`, compute safe-delivery fractions in the
four competence cells `(k in {4,10}) x (order in {RG,GR})` and one pooled
fraction. Across 18 replicates, the 15 one-sided Student-t lower bounds form
one Bonferroni family with family error `0.05`. A controller is competent only
when every cell lower bound is strictly above `0.58` and its pooled lower bound
is strictly above `0.70`. `FREE-DIRECT` and `SET-FREE` competence are mandatory
for an order-value claim; treatment competence is also mandatory for retention.

On a fresh support panel, for each replicate and target fixed `k in {6,14}`
draw 72 public first-renewal states using a disjoint `support-state` identity
domain. Each state has `x=0`, `v~Uniform[0,0.04]`,
`phi~Uniform[-0.015,0.015]`, `omega=z=f=tau_i=0`, prior `u_i=0`, `m=1`,
and `n=0`. The same public state is instantiated once with `d=0.55` (`RG`) and
once with `d=0` (`GR`). For each `(replicate,k,state-index)`, one fresh
`support-disturbance` tape of length `k` is shared across both histories and
all 27 actions. Each action is held until the interval ends or physical
failure occurs; an early failure uses its terminal state and no later
disturbance. Define the qualification-only one-interval physical score

```text
J = Delta x/(0.18*k)
    -2*1[physical failure]
    -0.5*(z_end/0.55)
    -0.25*(|phi_end|/0.48)
    -0.25*(f_end/0.42).
```

For replicate `s`, let `M_s,k,r,h` be the full set of all actions attaining the
maximum `J` for history `h` at public state `r`; exact ties remain in the set.
Define

```text
Q_order,s = mean_(k,r) 1[M_s,k,r,RG != M_s,k,r,GR]
D_order,s = mean_(k,r) |max_u J_s,k,r,RG(u)-max_u J_s,k,r,GR(u)|
D_action,s = mean_(k,r,h) |J_s,k,r,h(0,0,0)-J_s,k,r,h(2,2,2)|.
```

The denominators are respectively `144`, `144` and `288` cells per
replicate. Across replicates, `ORDER_SUPPORT` requires one-sided Bonferroni
lower bounds strictly above `0.20` for `Q_order` and above `0.05` for
`D_order`. `ACTION_SENSITIVITY` requires a lower bound above `0.10` for
`D_action`. These three bounds are one family at error `0.05`.

This oracle panel never trains, tunes or selects a controller, coordinate,
threshold or subgroup. Failure of support or sensitivity makes the learned
comparison nonidentified, not evidence for a different treatment.

## Simultaneous direct comparisons

Across the 18 paired replicates compute 17 two-sided Student-t intervals with
`df=17` in one Bonferroni family of error `0.05`:

1. `P_T-P_C` and `W_T-W_C` for each
   `C in {FREE,REVERSED,SET}`: six intervals;
2. `T_T-T_FREE` and `E_T-E_FREE`: two intervals; and
3. `O_T-O_C`, `G_T-G_C` and `F_T-F_C` for each control: nine intervals.

The prospective superiority margins are

```text
P over FREE: +0.035; P over REVERSED/SET: +0.025
W over FREE: +0.045; W over REVERSED/SET: +0.035.
```

The nonselected primary endpoint must be noninferior to `FREE` with lower
bound strictly above `-0.025`. Physical non-harm requires

```text
upper(T_T-T_FREE) < 1.5 s
upper(E_T-E_FREE) < 0.04
upper(O_T-O_C) < 0.015 for every C
upper(G_T-G_C) < 0.015 for every C
upper(F_T-F_C) < 0.015 for every C.
```

For a higher-is-better requirement with margin `m`, its state is `PASS` when
the adjusted lower bound is `>m`, `FAIL` when the adjusted upper bound is
`<=m`, and `UNRESOLVED` otherwise. For a lower-is-better upper-margin
requirement, it is `PASS` when the adjusted upper bound is strictly below the
margin, `FAIL` when the adjusted lower bound is at or above it, and
`UNRESOLVED` otherwise. Competence and support qualifications use only their
registered one-sided lower bounds: they are `PASS` when the lower bound is
strictly above threshold and `UNRESOLVED` otherwise; they never independently
take `FAIL`. Exact boundary contact never passes.

Define one `P` route and one `W` route. A route is `PASS` only when treatment,
`FREE` and `SET` competence, order support, action sensitivity, that route's
three superiority comparisons, the other-primary noninferiority comparison,
and every physical non-harm comparison pass. A route is `EXCLUDED` when any
necessary item is `FAIL`; it is `UNRESOLVED` otherwise.

No unadjusted subgroup, point estimate, per-replicate sign, trained-`k` value,
reward, oracle score or secondary diagnostic activates a result branch.

## Exhaustive first-true result-to-action map

After complete CM technical acceptance, apply exactly:

1. `INVALID-EVIDENCE` if the atomic panel is incomplete; identity, pairing,
   event-slot equality, public aliasing, event noncommutation, strict
   containment, tied reversal, set invariance, shared-parameter external-`k`
   law, equal opportunity, endpoint or simultaneous-family conformance fails;
   any per-`k` parameter/update or post-absorption policy query exists; or any
   registered value is nonfinite. No treatment conclusion follows.
2. `RETAIN-TAUT-GUST-RISK-TILT` if either the `P` route or the `W` route is
   `PASS`. Retain only this exact finite task/treatment/training package.
3. `DECLINE-TAUT-GUST-RISK-TILT` if evidence is valid, both routes are
   `EXCLUDED`, and `FREE-DIRECT`, `SET-FREE`, order-support and
   action-sensitivity qualifications pass. Decline only this exact package.
4. `DIRECT-UAV-ORDER-VALUE-NONIDENTIFIED` otherwise. This includes comparator
   incompetence, inadequate task support or action sensitivity, unresolved
   qualification, imprecise primary contrasts, or any valid pattern that
   neither retains nor precisely excludes both routes.

The map is exhaustive. It opens no checkpoint, representation, factor,
threshold, seed, coordinate, architecture, trainer, optimizer, budget, relation
assay, Stage B, second surface, deployment or flight successor.

## Prospective workload and full cost

Maximum registered training work is

```text
18 replicates x 3 learned arms x 144 updates x 12 episodes = 93,312 episodes
39,191,040 allocated primitive slots
6,858,432 maximum real policy decisions
124,416 AdamW steps
27,433,728 maximum minibatch decision-record traversals
54 final learned checkpoints.
```

Maximum registered evaluation work is

```text
18 x 4 controllers x 6 regimes x 120 episodes = 51,840 episodes
21,772,800 allocated primitive slots
2,998,080 maximum real policy decisions.
```

The support panel has `139,968` action-interval rollouts and at most
`1,399,680` primitive integration ticks. The full registered upper bound is therefore
`62,363,520` primitive simulator slots, excluding optimizer tensor operations,
static conformance and visualization. Early absorption can reduce realized
integration/decision work; realized counts are recorded only after the atomic
panel and have no branch or stopping role.

Prospective end-to-end cost is `15--24` experienced engineer-days for simulator
construction, analytic/event/containment fixtures, lifecycle, runner,
statistics and independent review; `24--72` CPU core-hours and approximately
`24--72` hours serialized single-core wall time for the registered panel, or
`7--20` elapsed hours with four independent CPU workers including merge/I/O;
minimum `8 GiB` and preferred `12 GiB` RAM; at most `6 GiB` scratch and `2 GiB`
durable checkpoints/manifests/result artifacts. No GPU is assumed or required.
These are EM planning bounds awaiting independent CM static feasibility and
cost acceptance. They are not a construction authorization or compute lease.

## Strongest alternatives and claim ceiling

The strongest alternatives are finite-budget regularization from the
restricted actor; underoptimization/curvature/initialization effects in the
larger `FREE-DIRECT`; numeric-`k` conditioning rather than order use; generic
task-law risk aversion; reward-weight choice; centralized credit and common
inner stabilization; residual and base parameter geometry; on-policy support;
post-action physical revelation of damage; binary last-event shortcut; a
misspecified surrogate ranking `rho` relative to exact state-dependent
physical hazard; and the simulator-specific cable/damper abstraction. Tied
reversal and `SET-FREE`
bound but do not eliminate these alternatives.

The maximum possible positive claim is:

> In the exact planar fixed-three-UAV `TRI-UAV-SLING-CORRIDOR-36M-v1`
> simulator, under eighteen fresh paired training replicates, one frozen
> controller parameterization across the registered held-out fixed and switched
> external periods, and the registered simultaneous direct-mission family, the
> prospectively specified `TAUT-GUST-RISK-TILT` finite-budget package improved
> payload-delivery performance or worst-regime robustness over a competent
> strictly containing direct controller while separating from tied reversed
> chronology and a competent unrestricted order-insensitive controller without
> registered completion-time, energy, cable, swing or formation harm.

No outcome establishes unique semigroup mediation, general chronology,
arbitrary event sequences, arbitrary `k`, variable `N`, another payload,
another simulator/surface, six-degree-of-freedom flight dynamics, real-aircraft
transfer, safety, deployment or flight value. A decline or nonidentified result
concerns only this exact object and does not delete the SCDMP family.

Here `worst-regime` means the minimum over exactly the four registered
external-`k` regime definitions after their balanced event-order/switch-time
pooling; it is not a worst-event-order or worst-switch-time claim. Completion
time and commanded-effort non-harm are only relative to `FREE-DIRECT`.
Cable-overload, swing-envelope and formation-loss non-harm are relative to all
three controls. No per-order, per-switch-time, aviation-safety or deployment
non-harm claim is available.

## Closure, activity and authority boundary

The exact science becomes immutable only after existing-conversation ChatGPT
Pro `CLOSED` and same-direction EM intake. Scientific activity would begin
immediately before the first source encoding of the frozen task, fresh master,
identity, stochastic coordinate, initializer/model, rollout, task outcome or
task-informed probe is materialized, whichever is first. That activity needs a
later distinct Portfolio/Root authorization and, for heavy work, a Root lease.

The current envelope authorizes this EM definition, existing-SCDMP-Pro
mathematical/causal closure and EM intake only. It authorizes no source, build,
test, probe, identity, coordinate, model, checkpoint, training, evaluation,
lease, compute, checkpoint repair, relation assay, Stage B, second surface,
production, deployment or real/UAV flight activity.

If this exact object cannot be Pro-closed without a science-bearing or material
cost-class change, return the precise defect. Do not import an old object, add a
menu, or silently alter a condition.

## Physics provenance boundary

The abstraction uses only these general source-backed primitives: unilateral
cable tension and slack/taut hybrid dynamics in multi-quadrotor suspended-load
models; a discrete retension transition; and zero-order-hold sampled actuation
whose physical behavior depends on hold duration. Source-specific masses,
cable lengths, gains, resonance values and sampling thresholds are not copied.
The registered event map and all numeric task constants are prospective
simulator definitions, not empirical claims about a real aircraft.

- K. Sreenath and V. Kumar, “Dynamics, Control and Planning for Cooperative
  Manipulation of Payloads Suspended by Cables from Multiple Quadrotor Robots,”
  RSS 2013: https://www.roboticsproceedings.org/rss09/p11.pdf
- K. Sreenath, N. Michael and V. Kumar, “Trajectory Generation and Control of a
  Quadrotor with a Cable-Suspended Load—A Differentially-Flat Hybrid System,”
  ICRA 2013: https://hybrid-robotics.berkeley.edu/publications/ICRA2013.pdf
- P. Kotaru, G. Wu and K. Sreenath, “Dynamics and Control of a Quadrotor with a
  Payload Suspended through an Elastic Cable,” ACC 2017:
  https://hybrid-robotics.berkeley.edu/publications/ACC2017_QuadLoad_ElasticCable.pdf

## Existing-ChatGPT-Pro mathematical/causal closure request

This revision-02 complete successor is the provider-visible frozen composite.
Revision 01 received `REVISION_REQUIRED` only because its PPO minibatch loss
and joint AdamW update map were not single-valued; the provider found every
other reviewed section coherent. Continue only the existing dedicated SCDMP
ChatGPT Pro conversation. Review mathematical and
causal closure, not code, repository state, runtime, files, hashes, receipts,
technical feasibility, provider mechanics or portfolio priority.

Determine whether:

1. the named planar multi-UAV task defines a genuine same-multiset physical
   order intervention, exact post-event public aliasing, and an external-`k`
   direct mission-value question without transferring old evidence;
2. `TAUT-GUST-RISK-TILT` is independently and globally specified, its
   chronology-to-action monotonicity is not bypassed, and it remains learnable
   end to end under duration-correct return;
3. `FREE-DIRECT` analytically and strictly contains the treatment, while tied
   `REVERSED` and competent `SET-FREE` isolate orientation and binary-order
   information without unequal physical opportunity;
4. the one-parameterization fixed/switched-`k` law, competence, task support,
   action sensitivity, direct endpoints and simultaneous inference family
   make the exhaustive first-true result map noncontradictory;
5. every workload count, cost boundary, strongest alternative, claim ceiling
   and activity fence is prospective and complete; and
6. the explicit binary-last-event ceiling prevents any unsupported general
   chronology, semigroup, arbitrary-`k`, variable-`N`, flight or safety claim.

Return exactly one leading line:

```text
CLOSED
```

or

```text
REVISION_REQUIRED
```

Then state every exact remaining mathematical, causal, comparator, endpoint,
branch, cost, activity-boundary or claim defect. Do not propose old-object
reuse, post-result treatment selection, a factor/architecture menu,
threshold/seed/budget repair, source, construction, activity, relation assay,
Stage B, another surface or portfolio action.
