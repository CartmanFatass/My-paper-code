# SCDMP target-bound end-to-end order-value science card

> **Superseded before external review or scientific activity.** Portfolio replaced
> this generic ground-carrier draft with
> `SCDMP-UAV-SUSPENDED-PAYLOAD-ORDER-VALUE-DEFINITION`. Nothing in this draft is
> an active treatment, threshold, coordinate, cost, or authority source.

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-TARGET-BOUND-END-TO-END-ORDER-VALUE
revision=SCDMP-TBOV-E2E-ORDER-VALUE-SCIENCE-20260820-01
owner=EM_semigroup_consistent_duration_model_policy
stage=definition_only
portfolio_envelope=SCDMP-TARGET-BOUND-END-TO-END-ORDER-VALUE-DEFINITION
scientific_activity_started=false
source_build_test_probe_authorized=false
identity_coordinate_model_checkpoint_authorized=false
training_evaluation_compute_lease_authorized=false
relation_assay_authorized=false
stage_b_authorized=false
```

## Question and scientific value

This card defines one materially new fixed-roster ground-carrier payload task.
It asks:

> Can one shared finite-budget controller use the physical order of a latch
> event and a gust event to improve direct safe-delivery performance or worst-
> regime robustness when the externally announced action-hold period `k` is
> fixed at unseen values or switches in-episode, relative to a competent
> strictly containing direct controller, the same treatment under a tied
> reversed-order intervention, and a strong permutation-invariant controller?

The learnable treatment is named `ORDER-RISK-MONOTONE`. It is specified from
the new task law before any activity. It is not selected from an old assay,
checkpoint, representation, factor, seed, subgroup or result.

This object moves directly from ordered event history to physical mission
return. It has no upstream checkpoint, segment-prediction objective,
transition/reward relation loss, `ORDER-TR`, `ORDER-Q`, checkpoint repair,
support/representation factor or Stage-A/Stage-B selector.

## Explicit isolation from prior SCDMP objects

No r07 or SRF constant, row, threshold, margin, seed, master, coordinate,
substream, tape, checkpoint, optimizer state, factor, estimate, branch fact,
competence value, representation choice or claim enters this object. In
particular, this card does not reuse 600 steps, ten seeds, `rho=0.65`, any r07
word, any SRF cell, or either old treatment label.

The completed r07/SRF evidence only motivates the prospective ban on another
checkpoint-repair layer. It supplies no input, prior, calibration, threshold,
treatment choice or confirmatory evidence here.

## New physical task

### State, observation and event prelude

Three fixed public ground-carrier roles pull one rigid payload along a straight
bounded corridor. At primitive time `t` the physical state is

```text
x_t=(p_t,v_t,s_t,c_t,l_1,t,l_2,t,l_3,t,u_1,t-1,u_2,t-1,u_3,t-1,d,m,t).
```

`p` is payload progress, `v` is forward speed, `s` is accumulated tether
strain, `c in {0,1}` records whether the immediately preceding primitive tick
had excessive formation imbalance, `l_i` are carrier loads, `u_i,t-1` are the
last held traction commands, `d` is latent tether damage, and `m in {0,1}` is
the latch state. The goal is `p>=200`; the common primitive control horizon is
315 ticks.

Before control, the payload is stationary in a passive cradle with

```text
p=0, v~Uniform[0,0.08], s=0, c=0, l_i=0, u_i,-1=0, d=0, m=0.
```

Exactly two visible physical events then occur while the cradle prevents any
change to the public kinematics:

```text
LATCH: m <- 1
GUST:  d <- clip(d+0.55*m,0,1).
```

The two prospectively balanced histories are:

```text
LG = LATCH then GUST, giving d=0.55
GL = GUST then LATCH, giving d=0.
```

Both histories have the same event multiset, duration, final latch state and
public physical observation. Only their order changes latent damage. Every arm
observes the same two raw event tokens as they occur, but no arm receives `d`,
an order label, a scenario/seed identity or a future `k` schedule.

The deployable boundary observation is

```text
o_t=(p/200,v/2.4,s/0.75,c,l_1/1.3,l_2/1.3,l_3/1.3,
     u_1,t-1/2,u_2,t-1/2,u_3,t-1/2,t/315,k_t/15) in R^12.
```

At `t=0` it is exactly identical for the paired `LG` and `GL` histories.
Later public loads and strain may reveal consequences of prior commands; that
is ordinary shared physical feedback, not an order label.

### Actions and primitive dynamics

At each renewal boundary the centralized fixed-roster controller chooses one
joint traction command

```text
u=(u_1,u_2,u_3), each u_i in {0,1,2},
```

from the 27 lexicographically ordered joint actions. It is held unchanged for
the currently announced external period `k_t`, unless success or physical
failure occurs first. No arm has an extra mid-period observation, action,
communication or termination opportunity.

For one primitive tick define

```text
A = mean_i u_i
B = max_i |u_i-A|
l_i' = 0.16 + 0.27*u_i + 0.18*|u_i-A| + 0.22*d*A^2
C(d) = 1.05 - 0.18*d
e = max(0,max_i l_i' - C(d)).
```

One fresh address-stable disturbance `xi_t` is independently equiprobable in
`{-0.012,+0.012}` and is shared across paired arms. The dynamics are

```text
v' = clip(0.93*v + 0.11*A - 0.018*d*A^2 + xi_t,0,2.4)
p' = p + v'
s' = 0.85*s + e
c' = 1[B>1.10].
```

Tether overload occurs when `s'>0.75`. Formation loss occurs when `c=1` and
`c'=1`. Either is an absorbing payload-drop failure. Safe delivery occurs on
the first tick with `p'>=200` before failure. Timeout at tick 315 is not a
safety failure but is not safe delivery.

Per-tick training reward is

```text
r_t = 0.004*(p'-p) - 0.0005*mean_i(u_i^2) - 0.002*(s')^2,
```

with terminal `+1` for safe delivery and `-1` for payload drop. The direct
scientific endpoints below are computed from physical outcomes and do not
reuse this scalar reward as their definition.

### Why order and external `k` can change value

For equal traction `u_i=2`, healthy `GL` has load `0.70<C(0)=1.05`, whereas
damaged `LG` has load `1.184>C(0.55)=0.951`. A short hold can accumulate
recoverable strain, while a long hold can cross the absorbing overload limit
before another decision. Equal traction `u_i=1` remains below capacity in both
histories but is slower. Thus the task law prospectively makes both event order
and the announced hold period relevant to the safe speed/strain tradeoff.

This arithmetic is a task-law property, not an empirical qualification or
learner input.

## External-`k` regimes and one shared parameterization

Training and all tuning use only fixed periods

```text
K_train={3,9}.
```

Frozen evaluation uses

```text
fixed 5
fixed 15
5->15
15->5.
```

For switches, the change occurs at a renewal boundary at primitive tick 120 or
180, balanced prospectively and hidden from the controller until the new `k`
is announced. Both switch times are legal boundaries for 5 and 15. All fixed
and switched regimes end at the common tick-315 horizon.

Every learned arm uses one weight vector, one optimizer state and the same
normalization across every `k`. The current `k` is observed. No per-`k` head,
lookup table, expert, initializer, optimizer, reset, training run, fine-tuning
or evaluation update is legal. A switch does not reset any controller state.

The scheduler, event order, initial speed, disturbance tape and switch time are
mutually independent and balanced inside every registered block. Evaluation
weights are frozen before target episodes exist.

## Treatment and controls

### Common risk index and base architecture

For joint action `u`, define the fixed task-law risk index

```text
risk(u)=0.7*(mean_i u_i/2) + 0.3*(max_i|u_i-mean_j u_j|/2).
```

It is nonnegative and increases with collective traction and imbalance.

All learned arms use a two-hidden-layer `SiLU` base actor
`B_theta:R^12->R^27`, widths 64 and 64, and a two-hidden-layer risk-scale
network `g_theta:R^12->R`, widths 32 and 32, with
`alpha_theta(o)=softplus(g_theta(o))`. A separate critic has input
`concat(o,q) in R^13`, hidden widths 64 and 64, and one scalar output. Affine
maps have biases. Xavier-uniform row-major initialization and float32 model/
optimizer arithmetic are frozen; all biases are zero.

### `ORDER-RISK-MONOTONE` treatment

From the raw event history compute the exact task-law order statistic

```text
q(LG)=1
q(GL)=0.
```

The treatment logits are

```text
logit_T(u|o,q)=B_theta(o)_u - q*alpha_theta(o)*risk(u).
```

Thus the only actor path carrying order is a learned nonnegative penalty on
task-law risk after the damaged order. The base logits never receive `q`.
The policy is categorical over all 27 legal actions. The entire actor and
critic are trained directly from mission reward; there is no auxiliary
transition, segment, relation, order-label or checkpoint target.

The treatment has 12,317 trainable parameters: 6,747 in `B`, 449 in `g`, and
5,121 in the critic.

### Strictly containing `FREE-DIRECT`

`FREE-DIRECT` has the same base/risk/critic object and adds one unrestricted
residual actor `R_psi:R^13->R^27`, widths 64 and 64:

```text
logit_FREE(u|o,q)
  = B_theta(o)_u - q*alpha_theta(o)*risk(u) + R_psi(o,q)_u.
```

The residual output layer is initialized exactly zero. Setting every residual
parameter to zero recovers every treatment policy exactly; nonzero residuals
can violate the monotone order-risk restriction. `FREE-DIRECT` is therefore an
analytic strict function-class superset, not merely a wider baseline. It has
19,128 trainable parameters. Its extra geometry is an explicit strongest
alternative, not hidden by disconnected padding.

### Tied `REVERSED` control

`REVERSED` is not separately trained. It evaluates the final treatment weights
on paired independent episodes while replacing only

```text
q <- 1-q.
```

The current physical state, raw event multiset, `k`, reward, disturbance tape,
action set and every other computation remain unchanged. This gives the wrong
order interpretation exactly the treatment's optimizer history and capacity;
it cannot learn to undo a deterministic reversal.

### Permutation-invariant `SET-DIRECT`

`SET-DIRECT` is independently trained with the exact treatment architecture
and parameter count but replaces the order statistic by the symmetric
expected-damage value

```text
q_SET=0.5
```

for both histories. It sees the two event identities and their multiset, but no
event position, timestamp or order-reconstructive feature. Its actor is exactly
invariant to the two event permutations while retaining the same current
physical observation, `k`, action set, risk template and training opportunity.

### Equal opportunity and initialization pairing

For each fresh seed, the treatment, `SET-DIRECT` and the shared portion of
`FREE-DIRECT` begin from byte-identical values for every same-shaped tensor.
`FREE-DIRECT`'s residual hidden layers use a disjoint initializer and its output
layer is zero. Every learned arm receives the same paired initial states,
event-order counts, `k` counts, disturbance addresses, number of primitive
environment ticks, episodes, optimizer updates, stopping law, tuning budget,
reward, critic privilege, action support and evaluation information.

The learned arms differ only in the frozen actor restriction above and the
unavoidable containing residual. `REVERSED` shares the treatment weights.
Internal model computation never creates an extra physical action or sensing
opportunity.

## Direct training law

There are 16 fresh paired training seeds. For each seed, each of the three
learned arms receives 128 PPO updates. Every update contains exactly 16
complete 315-tick episodes: eight at `k=3`, eight at `k=9`, with both event
orders exactly balanced within each `k`. Initial-speed and disturbance
addresses are paired across arms; on-policy actions may make later states
diverge.

At a decision boundary, primitive rewards are accumulated using the current
hold period:

```text
R_j=sum_(ell=0)^(k_j-1) gamma^ell r_(tau_j+ell)
    + gamma^k_j V(o_(tau_j+k_j),q),
gamma=0.995.
```

PPO uses GAE `lambda=0.95`, clip `0.20`, value coefficient `0.5`, entropy
coefficient `0.01`, one global gradient-norm clip at `1.0`, and AdamW with
learning rate `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`, weight decay
`1e-5`, and constant schedule. Each update uses four epochs and four
seed-keyed minibatches of 280 decision records, for exactly 16 AdamW steps per
update. There is no early stopping, checkpoint selection, learning-rate search,
architecture menu or target-`k` tuning. Only the final update-128 checkpoint is
eligible for evaluation.

All hyperparameters, initializers, normalization constants, batch order and
episode allocation are common and immutable after activity begins.

## Fresh identity and blinding law

Only after separate empirical authorization may the owning CM create one fresh
256-bit master from the operating-system cryptographic RNG. Sixteen seed keys
are derived with HMAC-SHA256 under the new prefix

```text
SCDMP-TBOV-E2E-ORDER-VALUE-r01/seed/<uint32_be(s)>.
```

Disjoint domains bind initialization, training initial states, training event
order, training disturbances, PPO action uniforms, minibatch order, evaluation
initial states, evaluation event order, evaluation switch time, evaluation
disturbances, and oracle-support coordinates. No old namespace or materialized
identity is imported.

Training frontiers are create-only and blinded by seed/arm. Evaluation opens
only after every learned arm's final checkpoint is technically accepted. The
complete result is atomic across all 16 seeds, four controllers and six regimes.
No seed, arm, regime, endpoint, interval or branch may be inspected before the
complete panel exists.

## Evaluation panel and direct endpoints

For each seed and controller in `{TREAT,FREE,REVERSED,SET}`, run exactly 128
fresh paired episodes in each of:

```text
fixed 3, fixed 9, fixed 5, fixed 15, 5->15, 15->5.
```

The fixed-3/fixed-9 cells are competence diagnostics only. The four held-out/
switch cells are the target-value panel. Event order is exactly balanced in
every fixed cell. In switch cells, event order and switch time `{120,180}` are
jointly balanced. All controllers share each exogenous scenario tape.

For controller `A` and seed `s`, define on the four target regimes:

```text
P_A,s = pooled safe-delivery fraction
W_A,s = minimum regime-specific safe-delivery fraction
T_A,s = mean min(safe-delivery time,315)
E_A,s = mean over primitive ticks of mean_i(u_i^2)/4
O_A,s = tether-overload failure fraction
F_A,s = formation-loss failure fraction.
```

`P` is direct performance and `W` is external-`k` robustness. `T` and `E` are
physical-time/useful-work non-harm endpoints. `O` and `F` remain separate
safety endpoints; aggregate reward cannot hide them.

## Competence, support and action-sensitivity qualifications

For `FREE-DIRECT` and the treatment separately, compute safe-delivery means in
the four training-diagnostic cells `(k in {3,9}) x (order in {LG,GL})`. Across
16 seeds use one family of five one-sided Student-t lower bounds: four cell
bounds and one pooled bound, Bonferroni family error `0.05`. A controller is
competent when every cell lower bound exceeds `0.65` and the pooled lower bound
exceeds `0.75`. Exact boundary contact does not pass.

On a fresh oracle-support panel, for each seed and each fixed target `k in
{5,15}`, draw 64 public initial observations. For both latent histories and all
27 first-boundary actions, execute exactly one held interval under paired
disturbances. `ORDER_SUPPORT` requires a one-sided Bonferroni lower bound above
`0.30` for the fraction of states whose unique best action differs between
`LG` and `GL`, and a lower bound above `0.04` for their mean absolute best-action
value separation. `ACTION_SENSITIVITY` requires a lower bound above `0.08` for
the mean absolute direct-value difference between the all-zero and all-two
joint actions. These three bounds form one family at error `0.05`.

The support panel is a task qualification only. It cannot train, tune or select
a controller, seed, threshold or subgroup.

## Simultaneous treatment comparisons

Across the 16 paired seeds compute 14 two-sided Student-t intervals with
`df=15` in one Bonferroni family of error `0.05`:

1. `P_T-P_C` and `W_T-W_C` for each
   `C in {FREE,REVERSED,SET}`: six intervals;
2. `T_T-T_FREE` and `E_T-E_FREE`: two intervals; and
3. `O_T-O_C` and `F_T-F_C` for each control: six intervals.

Higher is better for `P,W`; lower is better for `T,E,O,F`. The prospective
benefit margins are:

```text
P over FREE: +0.04; P over REVERSED/SET: +0.03
W over FREE: +0.05; W over REVERSED/SET: +0.04.
```

The other primary endpoint must be noninferior to `FREE` with lower bound
greater than `-0.03`. Non-harm requires:

```text
upper(T_T-T_FREE) < 12 primitive ticks
upper(E_T-E_FREE) < 0.05
upper(O_T-O_C) < 0.02 for every control C
upper(F_T-F_C) < 0.02 for every control C.
```

Define a `P` route and a `W` route. A route is `PASS` only when treatment and
`FREE` competence, support, action sensitivity, its three benefit bounds, the
other-primary noninferiority bound, and every non-harm bound pass strictly. A
necessary route condition is `FAIL` only when the opposite simultaneous bound
conclusively violates its margin; otherwise it is `UNRESOLVED`. A route is
`EXCLUDED` when any necessary condition is `FAIL` and `UNRESOLVED` otherwise.

No unadjusted subgroup, point-estimate, per-seed, trained-`k`, reward, oracle or
secondary sign interpretation may activate a result branch.

## Exhaustive first-true result map

After complete technical acceptance apply exactly:

1. `INVALID-EVIDENCE` if the atomic panel is incomplete; identities, pairing,
   event aliasing, strict containment, tied reversal, set invariance, external-
   `k` law, equal opportunity, direct endpoint or simultaneous family is
   violated; a per-`k` parameter/update exists; or any registered value is
   nonfinite. No treatment claim follows.
2. `RETAIN-ORDER-RISK-MONOTONE` if either the `P` route or `W` route is `PASS`.
   Retain only this exact finite-budget package.
3. `DECLINE-ORDER-RISK-MONOTONE` if evidence is valid, both routes are
   `EXCLUDED`, and `FREE-DIRECT`, support and action-sensitivity qualifications
   pass. Decline only this exact package.
4. `DIRECT-ORDER-VALUE-NONIDENTIFIED` otherwise. This includes comparator
   incompetence, inadequate task support/action sensitivity, unresolved
   competence, or any interval pattern that neither retains nor excludes both
   routes.

The map is exhaustive. Exact contact with any margin is unresolved. No branch
creates a checkpoint, representation, factor, threshold, seed, subgroup,
optimizer, budget, relation assay or Stage B successor.

## Prospective workload and full cost

The registered training workload is:

```text
16 seeds x 3 learned arms x 128 updates x 16 episodes = 98,304 episodes
30,965,760 primitive training ticks
6,881,280 on-policy training decisions
98,304 AdamW steps
27,525,120 minibatch decision-example traversals
48 final learned checkpoints.
```

The registered evaluation workload is:

```text
16 seeds x 4 controllers x 6 regimes x 128 episodes = 49,152 episodes
15,482,880 primitive evaluation ticks
2,523,136 policy decisions.
```

The oracle-support panel contains 221,184 action-interval rollouts and
1,105,920 primitive ticks. Total registered primitive work is therefore
47,554,560 task ticks, excluding optimizer tensor operations and static checks.

Prospective construction, lifecycle, conformance, statistics and independent
review are estimated at 8--12 experienced-engineer days. A serialized CPU
realization is provisionally 8--20 core-hours; 4 GiB RAM is the minimum and
8 GiB preferred; plan 3 GiB scratch and under 1 GiB durable checkpoints,
manifests and final results. These are definition-stage estimates for later CM
independent acceptance, not a lease or activity authorization.

## Strongest alternatives and claim ceiling

Even a retained result would establish only a finite-budget package effect.
The strongest alternatives are `FREE-DIRECT` underoptimization despite class
containment; generic monotone risk regularization; numeric-`k` conditioning;
base/residual parameter count, initialization, curvature, clipping and AdamW
geometry; shared centralized credit; reward-weight choice; observable physical
feedback after the first action; passive scenario heterogeneity; and a `k`
range whose decision-frequency effect is task-specific.

The maximum possible positive claim is:

> On this exact fixed-three-carrier payload task, under sixteen fresh paired
> seeds, one frozen controller parameterization across the registered unseen
> fixed and switched external periods, and the simultaneous direct-value
> family, the prospectively specified monotone order-risk package improved
> safe-delivery performance or worst-regime robustness over a competent
> strictly containing direct controller while separating from tied reversed-
> order and permutation-invariant controls without registered physical-time,
> energy or safety harm.

No result establishes unique semigroup mediation, generic order reasoning,
arbitrary `k`, variable `N`, another task or surface, UAV transfer, safety,
deployment or flight value. A decline or nonidentified result concerns only
this exact treatment, task and budget; it does not delete the SCDMP family.

## Activity and authority boundary

Scientific activity begins immediately before the first fresh master candidate,
seed identity, stochastic initial state, disturbance coordinate, initializer,
training/evaluation episode, model parameter or task outcome is materialized,
whichever occurs first. From that moment every task constant, treatment,
control, `k` regime, seed count, architecture, optimizer, endpoint, margin,
family, branch and claim boundary is immutable.

The current definition envelope authorizes only this EM science card,
same-conversation ChatGPT Pro mathematical/causal closure, same-direction EM
intake, and later CM read-only static bindability, observability, comparator
feasibility and full-cost assessment. It authorizes no source, build, test,
probe, identity, coordinate, model, checkpoint, training, evaluation, lease,
compute, relation assay, Stage B, second surface or UAV activity.

If the exact object cannot be Pro-closed or statically bound without changing
science or material cost class, return that precise reason. Do not repair it by
importing an old object, adding a menu or silently changing a condition.
