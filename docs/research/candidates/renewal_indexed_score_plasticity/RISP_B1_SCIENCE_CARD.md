# Renewal-Indexed Score Plasticity B1 science card

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-B1
revision=RISP-B1-SCIENCE-20260813-05
supersedes=RISP-B1-SCIENCE-20260813-04_PRO_REVISION_REQUIRED
owner=/root/em_renewal_indexed_score_plasticity
paired_cm=/root/cm_renewal_indexed_score_plasticity
artifact_status=FROZEN_FOR_ROOT_PUBLICATION_AND_SAME_CONVERSATION_PRO_REREVIEW
scientific_activity_started=false
production_authorized=false
external_mathematical_closure=r05_pending_same_conversation_rereview_r04_revision_required
```

## Decision question and claim boundary

RISP-B1 asks whether an explicit selected-action signed natural-score anchor is
a useful finite-training inductive bias for episode-local adaptation when one
policy must act under externally varied skill periods. Each algorithm arm has
one slow parameterization trained jointly at `k in {4,8}`. Slow and recurrent
parameters are then frozen. The only evaluation-time mutation is a two-scalar
per-agent fast state that is updated once after a genuine completed hold and is
read by the next legal policy decision. Evaluation covers fixed held-out
`k=12` and the seen-to-held-out and held-out-to-seen switches `4 -> 12` and
`12 -> 4`.

The treatment is `RISP`. Its primary comparator is `SIGN-RNN`, an
equal-dimensional sign-state recurrent controller with the same policy port,
packet, parameter count, affine transition work, optimizer exposure, update
count, action support, and reset law. The two transition function classes are
exactly the same: a fixed coordinate mask gives RISP a selected-score anchor
and gives SIGN-RNN a generic sign accumulator, while an unconstrained learned
matrix can translate either parameterization into the other. A positive result
therefore supports only a finite-budget coordinate/optimization prior, never
exclusive expressivity or a categorical distinction between plasticity and
recurrence.

The conclusion-bearing design is the `architecture x feedback` crossing

```text
RISP-INTACT       RISP-MARGINAL-TWIN
SIGN-RNN-INTACT   SIGN-RNN-MARGINAL-TWIN.
```

Yoking is evaluation-only. At every boundary it draws an independent replicate
sign from the recipient outcome law conditional on the controller's complete
pre-outcome information set and selected action, after analytically
marginalizing the recipient-only hidden target. It substitutes only that sign.
The marginal-twin generator never reads the recipient hidden target, current or
past recipient outcomes, recipient next state, an unchosen action, or observed
performance. It does not retrain the policy or select an opposite sign.

The strongest alternatives are a learned score-oriented recurrence inside the
function-equivalent SIGN-RNN, the fixed coordinate prior and its optimization
path, temporal-correlation sensitivity, critic calibration, and
different numbers of renewal opportunities per physical time. The toy removes
differential critic fitting and matches work/update opportunity within every
schedule, but it cannot remove the genuine fact that smaller `k` permits more
legal actions. All task effects are therefore measured per primitive time and
renewal counts are reported separately.

The maximum positive claim is: on this exact two-independent-agent renewal toy,
under the registered finite training budget, the explicit selected-score
coordinate prior improves mean physical-time value over the function-equivalent
SIGN-RNN parameterization on the registered held-out/post-feedback target-window
mixture, and that architecture difference depends on coupling updates to the
realized outcome rather than to an outcome-history-independent conditional
replicate. Even this claim is a finite coordinate/optimization-prior result. It
does not establish benefit in each switch direction unless the separate
bidirectional label passes. RISP-B1 cannot establish an unbiased full-return
policy-gradient update, necessity of natural scores, arbitrary or unknown `k`,
continual learning, learned termination, mid-hold adaptation, skill rebinding,
variable `N`, cooperative credit, safety, UAV value, or real deployment value.
No observation, threshold, or acceptance from another direction is used here.

## Fixed two-agent renewal toy

There are exactly two parameter-sharing agents. They do not communicate and
the B1 reward decomposes by agent, so B1 makes no coordination or multi-agent
credit claim. It tests whether a single reusable local controller can adapt
across duration schedules while two independent copies execute concurrently.

An episode has `T=192` primitive ticks. Each agent has a hidden target
`c_n in {LEFT, HOLD, RIGHT}` at renewal `n`; it is not in the policy
observation. At the episode start, `c_0` is uniform. At boundary `tau_n`, agent
`i` samples one action `a_n` from the common three-action library and holds it
unchanged over `[tau_n,tau_(n+1))`, where

```text
d_n = tau_(n+1)-tau_n = k_n.
```

No actor, critic, fast-state update, termination check, action mask change, or
new policy row occurs inside that interval.

At selection, the environment draws a latent interval outcome `Y_n in
{-1,+1}`:

```text
P(Y_n=+1 | a_n=c_n)  = 0.75
P(Y_n=+1 | a_n!=c_n) = 0.25.
```

The primitive reward equals the realized interval outcome throughout the hold:

```text
r_(tau_n+j)=Y_n, j=0,...,d_n-1.
```

This is physical reward accrued while the macro remains active, not a
fabricated policy or learning row. It makes the duration-discounted residual
analytically auditable and prevents critic calibration from differentially
flipping the two architectures' feedback signs.

At completion the next hidden target is

```text
c_(n+1) = a_n                         if Y_n=+1
c_(n+1) = uniform over A \ {a_n}      if Y_n=-1.
```

Thus a completed outcome is informative about the next legal macro decision:
positive evidence favors retaining the selected action, while negative
evidence favors suppressing it. This is a deliberately finite renewal POMDP,
not a claim about all action-hold systems. Changing `k` genuinely changes the
number of legal decisions and hidden-target transitions per physical horizon;
that geometry is part of the tested environment and is never normalized away.

The policy-visible boundary observation is exactly

```text
o_n = [tau_n/T, k_n/12].
```

The policy never receives `c_n`, `Y_n`, primitive reward samples, the
discounted reward magnitude, critic belief, baseline, TD residual magnitude,
recipient next hidden target, replicate outcome, or future `k`. In intact cells
the feedback engine uses the realized recipient reward; in marginal-twin cells
it uses only the independent replicate sign construction below. It exposes only
the controller-visible packet view. This restriction is identical in both
architecture arms.

The full-episode per-agent task endpoint is physical-time mean reward. The
episode endpoint averages both agents:

```text
J = (1/(2*T)) * sum_i sum_(t=0)^(T-1) r_(i,t).
```

For conclusion-bearing target inference, fixed `k=12` uses this full-episode
endpoint. Each switch schedule uses only ticks after the first completed hold
under the new duration has updated the fast state and a later action can read
it:

```text
Q(12)      = mean reward over t=0,...,191
Q(4->12)   = mean reward over t=108,...,191
Q(12->4)   = mean reward over t=100,...,191.
```

Each mean includes both agents and divides by exactly twice the displayed
number of primitive ticks. The windows deliberately exclude the first new-k
hold, because its action was selected before any new-k outcome existed. Full
episode switch `J`, the first 48 post-switch ticks, physical-time regret against
the exact-state-oracle descriptive controller, action entropy, renewal count,
and recovery curves indexed separately by physical ticks and by completed
renewals are report-only diagnostics. A pooled `Q` result is a claim about the
registered three-window mixture; it is not a claim of benefit in each switch
direction. A separate bidirectional label is allowed only under the literal
schedule bounds defined below.

## Exact policy and low-rank fast-state port

Each architecture/algorithm seed has one policy shared by both agents and all
durations. The two architecture arms are initialized from paired common-module
draws and trained separately on the same episode tapes; they are not forced to
share learned tensor values after optimization. There is no duration lookup,
per-`k` head, per-agent parameter, arm flag, or evaluation-time slow update.

The boundary encoder and base logits are

```text
h_n = tanh(Linear(8,4)(tanh(Linear(2,8)(o_n))))
l_base = Linear(4,3)(h_n).
```

For agent `i`, the fast state is exactly `x_i,n in R^2`. The common low-rank
port is

```text
l_fast = U diag(x_i,n) V^T h_n,
U in R^(3x2), V in R^(4x2).
```

The unbounded logits `l_base+l_fast` pass through

```text
l_safe = 6*tanh((l_base+l_fast)/6)
soft = softmax(l_safe)
pi(a|o,x) = 0.95*soft(a) + 0.05/3.
```

All three actions therefore have common positive support in every cell. Action
labels and physical meanings never change with `k`. The fast perturbation is a
rank-at-most-two adapter of the common final policy map.

The encoder has 60 trainable scalars, the base head 15, and `(U,V)` 14, for 89
policy scalars. The transition below has 28 learned scalars. Each primary arm
therefore has exactly 117 trainable scalars, all on a path to action logits.

## Boundary indexing and completed-interval packet

At `tau_n`, before sampling `a_n`, the feedback engine opens one pending record
per agent containing

```text
(episode, agent, n, tau_n, o_n, k_n, x_n,
 a_n, pi_n, log pi_n(a_n), g_n, F_n, e_n, b_n).
```

The behavior-policy score is evaluated in the pre-update fast-state
coordinates:

```text
g_n(a) = grad_x log pi(a | o_n,x_n)
g_n    = g_n(a_n)
F_n    = sum_(a in A) pi_n(a) g_n(a) g_n(a)^T
v_n    = solve(F_n + 0.05 I, g_n)
e_n    = v_n / max(1, ||v_n||_2/1.0).
```

The mixture distribution, smooth logit bound, common action set, and
regularizer make this an analytic finite-support quantity. `e_n` is stored
through the hold, consumed exactly once, and then discarded. There is no
cross-renewal eligibility trace. A nonfinite score, Fisher solve, eligibility,
return, baseline, or sign invalidates that evaluation replicate; it is never
replaced by zero.

Use the fixed physical discount `gamma=0.99` per primitive tick:

```text
R_n = sum_(j=0)^(d_n-1) gamma^j r_(tau_n+j)
C(d_n) = (1-gamma^d_n)/(1-gamma).
```

The feedback engine maintains a three-entry deployable controller belief
`b_n(c)`. Initially `b_0=(1/3,1/3,1/3)`. In an intact cell the supplied sign
equals `Y_n` under the exact baseline below, so the target-transition law gives
the exact update

```text
b_(n+1) = one_hot(a_n)                 if supplied sign is +1
b_(n+1) = uniform over A \ {a_n}       if supplied sign is -1.
```

The zero-sign branch leaves `b` unchanged, although it cannot occur under the
finite exact DGP. In a marginal-twin cell this same filter is deliberately
driven by the supplied replicate sign, never the hidden recipient outcome. It
is then a counterfactual controller belief rather than an oracle belief about
the recipient environment. A separate non-policy-visible marginal law `rho`
defined below generates replicate signs without reading the recipient hidden
state or outcome lineage. No parameter is fitted, and no training, held-out,
switch, or outcome-selected datum calibrates either recursion.

For any candidate action,

```text
m_n(a) = b_n(a)-0.5.
```

The frozen action-independent controller baseline functional is

```text
B_n = C(d_n) * sum_a pi_n(a) m_n(a).
delta_n = R_n-B_n.
```

Because the support floor keeps the policy-average `m_n` strictly between
`-0.5` and `+0.5`, `sign(delta_n)=Y_n` for every finite registered row.
`delta_n` is a duration-correct completed-interval contextual advantage
residual. It is not presented as a full-return TD error: the bootstrap is
exactly zero because this packet deliberately assigns only the just-completed
hold's discounted reward. This choice avoids an architecture-specific future
value bootstrap and defines the bounded score-feedback hypothesis being tested.
The outer training loss below uses the same residual.

The sign rule is exact:

```text
s_n = +1 if delta_n>0
s_n =  0 if delta_n=0
s_n = -1 if delta_n<0.
```

There is no fitted scale and the deadband is exactly zero. IEEE nonfinite values
invoke the invalid-replicate rule above. The controller-visible packet is

```text
(a_n one-hot, s_n, e_n, s_n*e_n, s_n*||e_n||_2,
 k_n/12, tau_n/T).
```

It contains no reward magnitude, baseline, belief, posterior, hidden state,
future duration, or next observation field capable of reconstructing the
recipient residual.

When a nonterminal hold completes at `tau_(n+1)`, the engine first finalizes
the old-`k_n` packet, updates the fast state once, discards `e_n`, and only then
allows the next legal policy query. If an external schedule changes `k`, it is
latched at this boundary: the completed record remains owned by old `k_n`, and
the next observation contains new `k_(n+1)`. The current hold is never shortened
or rebound. A hold completing exactly at terminal produces a diagnostic record
but no fast update because no later action can consume it. An unfinished
terminal hold produces neither a completed packet nor an update. All registered
schedules divide `T`, so the latter case is an anomaly rather than an expected
row.

## RISP and matched SIGN-RNN transitions

Both primary arms use the same ordered 13-vector

```text
p_n = concat[
  x_n,                         # 2
  one_hot(a_n),                # 3
  s_n,                         # 1
  e_n,                         # 2
  s_n*e_n,                     # 2
  s_n*||e_n||_2,               # 1
  k_n/12, tau_n/T              # 2
]                              # total 13.
```

Let `u=(1,1)/sqrt(2)`. Define two fixed `2 x 13` masks:

```text
M_RISP:     identity in the two columns occupied by s_n*e_n; zero elsewhere.
M_SIGN_RNN: u in the column occupied by s_n*||e_n||_2; zero elsewhere.
```

Each arm has an unconstrained learned `W in R^(2x13)` and `b in R^2`, and uses
the identical affine work, fixed per-boundary step `eta=0.10`, and Euclidean
projection:

```text
x_(n+1) = Project_(||x||_2<=3) [x_n + eta*((W+M_arm)p_n+b)].
```

RISP therefore contains an explicit `eta*s_n*e_n` selected-score update plus a
learned residual. SIGN-RNN contains a norm-matched generic sign-state anchor;
its learned transition receives every RISP packet field, including score
orientation. `eta` is constant. There is no `w(k)`, per-duration gain, analytic
decay, duration-dependent clipping, repeated micro-update, or hand-coded dose
normalization. Raw `k_n` is merely equal controller information and may be used
by the learned affine recurrence in either arm.

The two transition classes have exact containment with no approximation. For
any fitted RISP `(W_R,b_R)`, set

```text
W_G = W_R + M_RISP-M_SIGN_RNN
b_G = b_R.
```

Then the preprojection increment, projected next state, and next-policy logits
are identical for every packet and state. The reverse translation also holds.
CM conformance must verify this identity on a deterministic finite packet bank
to ordinary `1e-6` float tolerance; this is a technical implementation check,
not empirical evidence. Any observed difference can therefore be attributed
only to the fixed coordinate prior together with initialization, regularization,
finite data, and optimization, not to representational exclusion.

At episode start each agent has `x_0=(0,0)`. State resets nowhere else. It
persists across `4 -> 12` and `12 -> 4`, hidden-target transitions, and all
completed renewals. The two agents never share fast state. A team score, summed
joint likelihood, public adapter, optimizer moment, extra trace, running
normalizer, or switch reset would define a different treatment.

On freely acting trajectories, both architectures use byte-identical packet
construction and exactly the same deployable information, but their numerical
packets can differ after their actions and histories diverge. Literal numerical
packet equality is required in the exact one-boundary forks used for the
marginal-twin cut and conformance diagnostics: the controller filtration,
pre-update state, action, policy, duration, score, Fisher, eligibility, critic
belief, `rho`, and baseline are cloned before the recipient and replicate
draws. Claiming literal equality across already divergent on-policy trajectories
is explicitly forbidden.

## Prospective information-set marginal-twin sign yoke

Let `H_n` be the controller's complete pre-outcome filtration: initial schedule,
visible observations through `tau_n`, all previously selected actions, all
previously supplied signs, the resulting controller belief and fast state, the
current policy, selected `a_n`, duration, score, Fisher, eligibility, and
baseline. It excludes every recipient hidden target, recipient outcome/reward,
recipient residual, and recipient next state.

The yoke engine maintains `rho_n`, the exact distribution of the recipient
hidden target conditional on `H_n` when actual recipient outcomes are never
revealed. Initially `rho_0=(1/3,1/3,1/3)`. For selected `a_n`, define

```text
pbar_n = P(Y_n^R=+1 | H_n,a_n) = 0.25 + 0.50*rho_n(a_n)
rho_(n+1)(a_n)      = pbar_n
rho_(n+1)(c!=a_n)   = (1-pbar_n)/2.
```

The update marginalizes the registered recipient transition over its unobserved
actual outcome. It uses the action history but neither the actual outcome nor
the supplied replicate sign. Because earlier supplied signs are generated from
this law independently of the recipient lineage, induction makes `rho_n` the
correct information-set conditional recipient law.

The feedback intervention is applied only after final checkpoints are frozen.
For every recipient interval in a marginal-twin cell:

1. Freeze `H_n`, including the chosen action, duration, policy, eligibility and
   baseline, before the recipient outcome or replicate uniform is inspected.
2. Bind a separate prospective RNG key determined only by algorithm seed,
   schedule, episode, agent and renewal index.
3. Draw one independent uniform and set `Y_n^T=+1` iff it is below `pbar_n`;
   otherwise set `Y_n^T=-1`. Set `R_n^T=C(d_n)Y_n^T`, form
   `delta_n^T=R_n^T-B_n`, and apply the exact sign rule. No hidden target or
   unchosen action is simulated or read.
4. Substitute only `s_n^T` and its deterministic packet products into the
   recipient fast transition. Drive the controller belief only from `s_n^T`.
   Independently advance `rho` by the marginalized formula above.
5. Let the recipient environment continue from its actual `Y_n^R` and target
   transition for task scoring only. Neither value enters `rho`, `b`, `x`, a
   later supplied sign, or any policy-visible field.

Thus, prospectively and for every history,

```text
Law(s_n^T | H_n,a_n) = Law(s_n^R | H_n,a_n)
s_n^T independent of (Y_0:n^R,c_0:n+1^R) conditional on H_n,a_n.
```

This is controller-context matching by exact marginalization, not hidden-state
matching, donor selection, opposite-sign selection or nearest-neighbor yoking.
It severs the recipient outcome lineage from the supplied sign sequence while
preserving the sign law available at the controller information set. Because
horizons contain complete holds, there is no missing replicate renewal. A
missing or nonfinite record invalidates the paired replicate and is never
imputed.

For each architecture and target schedule separately, pooling its eight seeds
and 64 episodes only after the complete panel exists, feedback integrity
requires all of the following:

- the logged `pbar_n` is in `[0.25,0.75]` on every replicate row and both
  empirical nonzero sign probabilities are at least `0.10` within each
  `(k, selected-action)` stratum;
- recipient/replicate sign discordance is in `[0.20,0.80]` within each
  `(k, selected-action-matches-recipient-hidden-target)` audit stratum;
- zero-sign rate is exactly zero up to a fail-closed nonfinite anomaly;
- recipient and replicate packet counts and timing are identical; and
- deterministic dependency sentinels confirm that changing recipient hidden
  targets and outcomes while holding `H`, actions and replicate uniforms fixed
  changes no `rho`, supplied sign, controller belief, fast state or later
  policy-visible packet field.

Failure makes the architecture-by-feedback interaction nonidentifying. It is
not repaired by permuting donors, selecting opposite signs, widening strata, or
conditioning on observed performance.

The immediate causal timing diagnostic forks each architecture from its
registered marginal-twin trajectory at the first completed nonterminal interval
wholly under fixed held-out `k=12`, and at the first completed nonterminal
interval after each switch. The copies share the exact recipient environment,
pre-update controller state, packet and `rho`; one uses the realized recipient
sign at that boundary and one uses the prospectively drawn marginal replicate
sign, then they act freely for the next legal hold. The prehistory remains the
same outcome-history-free marginal-twin history in both copies. Report
next-action total variation and next-hold physical return. The registered `Q`
windows remain the value endpoint; the fork only establishes that the first
possible current-sign effect is after a legal completed renewal.

## Training, schedules, randomization, and fixed counts

There are eight independent algorithm seeds `0,...,7`. For each seed, RISP and
SIGN-RNN use paired initial draws for all learned tensors; only the fixed masks
differ. Every trainable weight uses Xavier uniform from the seed's model stream,
every bias is zero, and both arms use identical traversal. No arm receives a
larger initialization search.

The model stream is `PCG64(60_000_000_000+algorithm_seed)` with the `U53(x)`
conversion defined below. In this order, fill row-major float64 arrays for the
`8 x 2` encoder weight, `4 x 8` encoder weight, `3 x 4` base-head weight,
`3 x 2` matrix `U`, `4 x 2` matrix `V`, and `2 x 13` transition weight `W`.
For a matrix with `(fan_out,fan_in)`, each scalar is

```text
sqrt(6/(fan_in+fan_out)) * (2*U53(raw)-1).
```

Cast each completed array once to float32. All corresponding biases, including
the transition bias, are exact zero and consume no draw. Clone these arrays
into both architecture arms before adding their immutable masks. No library
default reset runs afterward.

Each architecture/seed is trained for exactly 256 Adam updates with batch size
16 complete two-agent episodes. Every batch contains eight constant-`k=4` and
eight constant-`k=8` episodes in a fixed alternating order. Thus each
architecture/seed sees exactly 4,096 training episodes, 2,048 at each `k`, and
no switch or `k=12` episode. There is no validation-selected checkpoint or
early stop; evaluation uses update 256. RISP and SIGN-RNN share episode tapes,
minibatch order, action-uniform random numbers, optimizer-update count, and
hyperparameters, while actions cause their on-policy histories to diverge.

Adam uses learning rate `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`, and
decoupled weight decay `1e-4` on every learned scalar but never on a fixed mask.
Global gradient norm is clipped at `1.0`. There is no architecture- or
duration-specific tuning.

For one batch, the outer objective is

```text
L = -(1/(16*2*T)) * sum_(episodes,agents,renewals)
      [ stopgrad(delta_n)*log pi_n(a_n)
        + 0.002*C(d_n)*Entropy(pi_n) ].
```

The recurrence is differentiated through the complete episode renewal history.
There is no truncated BPTT and no detach of the fast state. Sampled actions,
rewards, analytic belief, `delta_n`, its sign, the score/Fisher solve, and
`e_n` are detached; this excludes second derivatives through the inner score
update equally in both arms. Training uses intact signs only.

The five scored schedules are:

| id | schedule | role | true decisions | nonterminal updates |
|---:|---|---|---:|---:|
| 0 | fixed `k=4` | seen diagnostic | 48 | 47 |
| 1 | fixed `k=8` | seen diagnostic | 24 | 23 |
| 2 | fixed `k=12` | held-out target | 16 | 15 |
| 3 | `k=4` on `[0,96)`, then `k=12` | seen-to-held-out target | 32 | 31 |
| 4 | `k=12` on `[0,96)`, then `k=4` | held-out-to-seen target | 32 | 31 |

At `t=96` the old hold completes, its packet updates fast state, and the next
decision first observes the new `k`. No state resets. Both switch directions
therefore cross seen and held-out support. There is no switch exposure during
training.

For every algorithm seed, schedule, architecture, and feedback cell, evaluation
uses exactly 64 complete episodes. The intact and marginal-twin cells clone the
same final checkpoint. Episode environment streams are paired across all four
factorial cells; the yoke uses a disjoint prospective twin namespace. Initial
target, interval outcome, and negative-target choice draws use NumPy `PCG64`
and the unsigned conversion

```text
U53(x) = float64(x >> 11) * 2^-53.
```

One stream is instantiated for every episode-agent. The collision-free integer
keys are

```text
TRAIN_KEY = 10_000_000_000
            + 1_000_000*algorithm_seed
            + 1_000*optimizer_update
            + 10*episode_in_batch + agent

EVAL_KEY  = 20_000_000_000
            + 1_000_000*algorithm_seed
            + 100_000*schedule_id
            + 100*episode + agent.

TRAIN_ACTION_KEY = 40_000_000_000
                   + 1_000_000*algorithm_seed
                   + 1_000*optimizer_update
                   + 10*episode_in_batch + agent

EVAL_ACTION_KEY  = 50_000_000_000
                   + 1_000_000*algorithm_seed
                   + 100_000*schedule_id
                   + 100*episode + agent.
```

At episode start consume one raw word and set
`c_0=floor(3*U53(raw_init))` in action order. At every true renewal consume exactly
two more words, `raw_Y` then `raw_alt`, whether or not the second is used. Set
`Y=+1` when `U53(raw_Y)` is below `0.75` for `a=c` or below `0.25` otherwise. If
`Y=-1`, sort the two actions other than `a` in policy action order and select
index `floor(2*U53(raw_alt))`; if `Y=+1`, discard `raw_alt`. There are no other
environment draws.

The separate action stream consumes exactly one raw word at each true boundary.
Sample the first action in fixed order `LEFT,HOLD,RIGHT` whose float64 policy
CDF is strictly greater than `U53(raw_action)`; because `U53<1` and all probabilities
are positive, this always selects one action. Paired architecture/feedback
cells and descriptive stochastic controllers reuse the same action uniforms;
their probabilities may map a uniform to different actions but cannot change
draw count or order.

Every integer index appearing in a key is zero-based over its declared count:
`optimizer_update=0,...,255`, `episode_in_batch=0,...,15`,
`episode=0,...,63`, and `agent=0,1`. Schedule IDs are the zero-based IDs in
the five-row schedule table. The renewal index starts at `n=0` for the first
interval of each episode. No one-based reinterpretation is permitted.

All architectures, feedback cells, and descriptive controllers reuse these
base streams. Their on-policy actions may map a shared uniform to different
outcomes, but cannot change consumption count or order. The marginal twin at
renewal `n` uses one separately instantiated stream and one raw word:

```text
TWIN_KEY = 30_000_000_000
           + 1_000_000_000*algorithm_seed
           + 100_000_000*schedule_id
           + 1_000_000*episode
           + 1_000*agent + n.
```

It sets `Y_n^T=+1` exactly when `U53(raw_twin)<pbar_n`; it never reads or clones
the recipient hidden target. Architecture, feedback, action, reward, and
performance never enter a key. Changing a key, draw count, consumption order,
conversion, or conditional mapping after scientific activity begins creates a
new science revision and is forbidden for the active confirmatory lock.

The immediate timing diagnostic is run for all eight seeds, both architectures,
all 64 marginal-twin episodes and the three target schedules. At the registered
fork boundary both branches reuse one action uniform and two environment raw
words from disjoint streams:

```text
FORK_ENV_KEY = 70_000_000_000
               + 1_000_000*algorithm_seed
               + 100_000*schedule_id
               + 100*episode + agent

FORK_ACTION_KEY = 80_000_000_000
                  + 1_000_000*algorithm_seed
                  + 100_000*schedule_id
                  + 100*episode + agent.
```

`FORK_ACTION_KEY` consumes one word per agent; both branches map that same
uniform through their branch-specific policies. `FORK_ENV_KEY` consumes
`raw_Y,raw_alt` once per agent in that order and both branches reuse
the pair under their possibly different selected actions. No target-init word
is consumed because the recipient pre-fork environment is cloned. The
diagnostic adds exactly `3,072` paired forks and `114,688` agent-ticks of
one-hold continuation (`1,024 pairs per schedule * 2 branches * 2 agents *
(12+12+4)`). It cannot enter any efficacy estimand or branch margin.

Descriptive `UNIFORM` and `STATE-ORACLE` controllers are evaluated on the same
64 episode tapes. `UNIFORM` samples all three actions equally. `STATE-ORACLE`
observes the experimenter-only current target `c_n` and, with the same `0.05`
support floor, assigns the remaining mass to that target action. It is a
privileged-information headroom control, not a primary comparator and cannot
establish algorithm value by itself.

The registered base maximum, excluding marginal-replicate draws, is

```text
training:   8 seeds * 2 architectures * 4096 episodes * 2 agents * 192 ticks
          = 25,165,824 agent-ticks
evaluation: 8 * 4 factorial cells * 5 schedules * 64 episodes * 2 * 192
          = 3,932,160 agent-ticks
controls:   8 * 2 controllers * 5 * 64 * 2 * 192
          = 1,966,080 agent-ticks
total     = 31,064,064 agent-ticks.
```

The same ledger contains exactly `4,718,592` training action decisions,
`4,587,520` nonterminal training updates, `622,592` factorial evaluation
decisions, `602,112` factorial nonterminal updates, and `311,296` descriptive
control decisions. Including the fixed immediate-fork continuation gives
`31,178,752` agent-ticks before outcome-only marginal-replicate arithmetic.

The two marginal-twin architecture cells add exactly `301,056` outcome-only
draws (`8 seeds * 2 architectures * 64 episodes * 2 agents *
(47+23+15+31+31)`) and never call another policy. The requested technical class is one CPU
process, no GPU, at most 1 GiB RSS and a 60-minute launch estimate. The memory
bound is deterministic; wall time is a later CM engineering measurement and
acceptance fact, not a mathematical certificate. A CM finding that these limits
are not conservative returns a resource-concept clarification; it does not
authorize fewer seeds, episodes, schedules, cells, or updates.

## Two-lock answerability and deterministic capability certificate

Lock 1 is deterministic and precedes every random word. It may check only
structural answerability and implementation conformance. It may not initialize
a learned checkpoint, draw or fit a stochastic object, inspect an efficacy or
held-out contrast, select a seed/checkpoint/hyperparameter, or estimate learned
competence. Lock 2 is the complete frozen training/evaluation experiment above.
It begins only after Lock 1 passes and uses the already registered disjoint
model, training, evaluation, action and marginal-twin namespaces without any
development data.

Lock 1 uses schema `RISP-B1-LOCK1-20260813-05`, IEEE binary64 reference
arithmetic and IEEE binary32 candidate tensors. Stable softmax subtracts the
maximum safe logit before exponentiation. Euclidean projection is identity for
norm at most three and otherwise multiplies by `3/||x||_2`. Candidate/reference
absolute error must be at most `1e-6` for state, logits and probabilities.
This tolerance is frozen; nonfinite values fail the certificate.

The ordered zero-based packet coordinates are exactly

```text
0:1 x; 2:4 action one-hot; 5 sign; 6:7 e; 8:9 sign*e;
10 sign*||e||; 11 k/12; 12 tau/T.
```

`M_RISP[0,8]=1`, `M_RISP[1,9]=1`, and all other entries are zero.
`M_SIGN_RNN[:,10]=(1,1)/sqrt(2)` and all other entries are zero. The
hand-authored containment bank uses `W_R=0`, `b=0`, and
`W_G=M_RISP-M_SIGN_RNN`:

| row | `x` | action | `s` | `e` | `k/12,t/T` | expected preprojection = postprojection |
|---|---|---|---:|---|---|---|
| C1 | `(0,0)` | LEFT | `+1` | `(0.6,-0.8)` | `(1/3,1/4)` | `(0.06,-0.08)` |
| C2 | `(2.99,0)` | HOLD | `+1` | `(1,0)` | `(1,1/2)` | pre `(3.09,0)`, post `(3,0)` |
| C3 | `(0.2,-0.1)` | RIGHT | `-1` | `(-0.3,0.4)` | `(2/3,3/4)` | `(0.23,-0.14)` |

For every row, the complete 13-vector is constructed literally from the named
components. Both arms must produce the displayed state and identical logits
and probabilities under any shared policy port. The finite bank checks the
implementation; the algebraic translation proves equality for the full class.

The deterministic action-reachability fixture sets the shared base logits to
zero and the shared port so that `V^T h=(1,0)`, the first column of `U` is
`(1,0,-1)`, and its second column is zero. This is realized by a constant
encoder with second-layer bias `(atanh(1/2),0,0,0)` and a first V column
`(2,0,0,0)`. From `x=(0,0)`, use the C2 packet components without its old state;
both translated transitions produce `x'=(0.1,0)` and unbounded fast logits
`(0.1,0,-0.1)`. The no-update clone remains uniform. After the registered safe
logit and support-floor maps, every action probability is at least `1/60` and
the updated-versus-no-update TV is greater than `0.03`. This fixture proves only
structural prospective reachability; it is not a learned TV or competence gate.

The no-leakage sentinel starts `rho=(1/3,1/3,1/3)`, selects LEFT, and fixes the
replicate uniform at `0.4`, hence `pbar=5/12` and supplied sign `+1`. It compares
two recipient worlds with actual first outcomes `+1` and `-1`. Both must produce
the same controller belief, fast state and `rho'=(5/12,7/24,7/24)`. With the
same next action HOLD and next replicate uniform `0.4`, both use
`pbar=19/48` and supplied sign `-1`, again producing identical later
controller-visible fields despite different recipient hidden-state lineages.
Actual recipient rewards and targets may differ and must be absent from the
dependency trace.

Lock 1 also checks the literal schedule/index domains, terminal-update rule,
every key formula, unsigned 64-bit range, fixed per-row draw budgets, namespace
collision inequalities, and the published decision/update/draw totals. Its
resource manifest fixes binary32 learned tensors, at most 48 renewal states per
episode graph, vectorized 16-episode batches split by duration, serial seed
lifecycle, discarded graphs after each Adam update, streamed seed/schedule
summaries, no per-tick graph, and no per-row durable JSON. A static live-memory
bound below 1 GiB is required; 60-minute wall remains a later engineering fact.

Scientific activity begins irreversibly when Lock 2 consumes or materializes
its first random word from the seed-zero model stream or any registered
confirmatory environment/action/marginal-twin stream, whichever occurs first. The first
training initialization therefore starts activity. After that boundary there
is no treatment, host, objective, seed, key, checkpoint, threshold, window,
branch, or certificate change. A Lock-1 conformance failure permits only
unchanged-science engineering repair before any Lock-2 word; exhaustion of the
fixed certificate does not authorize a stochastic development menu.

## Activity, parity, and validity conditions

The activity boundary is the Lock-2 first-random-word rule above. For reporting
whether the mechanism was actually exercised, a separate outcome flag requires
a frozen evaluation cell to complete a nonterminal hold, construct a finite
packet, apply one registered fast update, and have a later legal decision read
the resulting state. Failure of that outcome flag makes the result
nonidentifying but never rewinds activity or licenses a new run.

Every conclusion additionally requires:

1. Lock 1 passed before the activity boundary; the complete Lock-2 panel exists;
   and every architecture/feedback/target-schedule cell contains at least one
   nonterminal fast update that a later legal decision reads;
2. exact decision/update counts in the table, complete `T=192` episodes, common
   action support, and no mid-hold policy rows;
3. identical 117-scalar architecture counts, optimizer exposure, BPTT/detach
   law, packet schema, and transition matvec count;
4. the algebraic mask-translation conformance identity;
5. separately in every architecture-by-feedback cell, pooling its eight seeds
   and three target schedules only after completion, `||e_n||_2>0.05` for at
   least 95% of its nonzero-sign target packets; seed-by-schedule fractions are
   reported and never select the panel;
6. separately in every architecture-by-feedback cell, projection is active on
   fewer than 10% of its target updates, with seed-by-schedule fractions
   reported but not used for selection;
7. for every nonterminal, nonzero-sign target update in an intact cell, define
   the no-update clone by retaining `x_n` while holding the same next
   observation `o_(n+1)`, and compute
   `TV_update=0.5*sum_a |pi(a|o_(n+1),x_(n+1))-pi(a|o_(n+1),x_n)|`;
   pooling all such rows over all eight seeds, 64 episodes and three target
   schedules separately within each architecture, at least 25% must have
   `TV_update>=0.005`; seed-by-schedule proportions are also reported but do
   not select or stop the panel;
8. every feedback-integrity condition above;
9. final checkpoints and all slow/recurrent parameters frozen before any
   target or marginal-twin episode; and
10. a finite complete result for all eight algorithm seeds.

To rule out a deliberately untrained comparator, define at each seen schedule
from the eight seed-level full-episode means

```text
Gap(r) = mean_s[J_ORACLE,s(r)-J_UNIFORM,s(r)]
Capture_A(r) = mean_s[J_AI,s(r)-J_UNIFORM,s(r)] / Gap(r).
```

The learned SIGN-RNN competence condition is `Gap(r)>=0.10`,
`Capture_G(r)>=0.20`, and both intact `Capture_R(r)` and `Capture_G(r)` are at
most `0.95`, separately at fixed `k=4` and fixed `k=8`. This is a prospective
complete-panel Lock-2 observation, never Lock-1 evidence or a reason to stop,
select, add updates, or tune on target schedules. Failure makes OOD architecture
attribution nonidentifying.
For the narrower statement that the score anchor specifically improves OOD
transfer rather than all finite-budget learning, the two-sided 90% seed-level
interval for `RISP-INTACT minus SIGN-RNN-INTACT` must also lie within
`[-0.02,+0.02]` at each seen schedule.

## Estimands and frozen interpretation

Episodes are averaged within algorithm seed, schedule, architecture, and
feedback cell. The eight algorithm seeds, not episodes or agents, are the
independent uncertainty units. Let `Q_AF,s(r)` be the registered seed-level
target-window mean above, with `A in {R,G}` and `F in {I,M}` for intact and
marginal-twin feedback. For every target schedule define

```text
D_I(r)   = mean_s [Q_RI,s(r)-Q_GI,s(r)]
D_M(r)   = mean_s [Q_RM,s(r)-Q_GM,s(r)]
Psi(r)   = mean_s [(Q_RI,s-Q_GI,s)-(Q_RM,s-Q_GM,s)]
C_R(r)   = mean_s [Q_RI,s(r)-Q_RM,s(r)]
C_G(r)   = mean_s [Q_GI,s(r)-Q_GM,s(r)].
```

For every pooled target quantity, first average its three within-seed effects
over exactly `{12,4->12,12->4}`, then compute a `df=7` paired t interval across
the eight seed averages. Exact `2^8` sign-flip p-values and all seed effects are
reported but do not replace intervals or margins. The full-episode `J` values
for switch schedules are descriptive and never substituted for `Q`.

A **realized-sign-coupled explicit-anchor finite-toy advantage** requires every
validity condition and the literal SIGN-RNN seen-schedule competence condition
plus:

- the one-sided 95% lower bound for pooled target `D_I` exceeds `+0.020` mean
  reward per primitive tick;
- the one-sided 95% lower bound for pooled target `Psi` exceeds `+0.015`;
- the one-sided 95% lower bound for pooled target `C_R` exceeds `+0.015`;
- for each of the three target schedules, its simultaneous one-sided
  `1-0.05/3` lower bound for `D_I(r)` exceeds `-0.010`; and
- the two-sided 90% interval for pooled target `D_M` lies wholly inside
  `[-0.010,+0.010]`.

The final condition prevents a coordinate advantage that survives replacement
of realized signs by outcome-history-independent conditional replicates from
being attributed to realized-sign coupling. The immediate fork must also show
that the first changed policy/output occurs only after the completed update; it
has no separate numeric success margin.

Interpret outcomes in this order:

1. **Invalid or nonidentifying.** Lock 1 did not pass before activity, or any
   activity, packet, support, parity, containment, critic, yoke, count, freeze,
   learned competence, output, headroom, or finite-value condition fails. No
   positive, negative, equivalence, or null claim follows. A complete Lock-2
   panel is still retained; these learned conditions never stop or select it.
2. **Material harm.** Apply one Bonferroni family to four one-sided upper-bound
   tests: pooled target `D_I` and each of the three schedule-specific `D_I(r)`
   use alpha `0.05/4`, hence one-sided 98.75% upper bounds. If the pooled upper
   bound is below `-0.020`, or any schedule upper bound is below `-0.030`, reject
   this exact RISP treatment on this toy. This familywise-0.05 disposition
   overrides a favorable interaction elsewhere.
3. **Realized-sign-coupled explicit-anchor advantage.** All positive conditions
   pass. Retain the composite score-anchored coordinate prior on the registered
   finite target-window mixture. If the seen equivalence condition also passes,
   the result supports the narrower OOD finite-budget prior reading; otherwise
   it supports only an overall finite-budget package effect. It does not prove
   natural-score necessity or exclusive expressivity.
4. **Intact package value without the registered coupling interaction.** The
   pooled `D_I` lower bound exceeds `+0.020`, but one or more of `Psi`, `C_R`, or
   marginal-twin `D_M` equivalence fails. Report only an intact-regime
   architecture/training package effect.
5. **No registered minimum benefit of the explicit score anchor.** The
   two-sided 90% intervals for pooled `D_I` and `Psi` both lie wholly inside
   `[-0.010,+0.010]` and the literal SIGN-RNN competence condition passes. This
   says only that the fixed explicit anchor adds no registered minimum benefit
   over the function-equivalent SIGN-RNN parameterization at this budget;
   SIGN-RNN may itself learn score-oriented transitions.
6. **Statistically unresolved.** Valid data fit none of the above. Do not add
   seeds, weaken margins, select a favorable schedule, or automatically rerun.

After the primary disposition, compute two compatible secondary labels. They do
not change branch precedence:

- `BOTH_ARCHITECTURES_FAVOR_REALIZED_SIGN_REGIME` applies iff the one-sided 95%
  lower bounds for pooled `C_R` and pooled `C_G` both exceed `+0.015` and the
  two-sided 90% interval for pooled `Psi` lies wholly inside
  `[-0.010,+0.010]`. It means only that both registered architectures outperform
  their marginal-twin cells; it is not a no-feedback or generic-feedback claim.
- `BIDIRECTIONAL_POSTFEEDBACK_POSITIVE` applies iff the one-sided
  `1-0.05/2=97.5%` simultaneous lower bounds for `D_I(4->12)` and
  `D_I(12->4)` both exceed zero. Without this label, the primary pooled result
  makes no claim of benefit in each direction.

An effect visible per renewal but absent from physical-time `Q` is reported as
renewal-geometry sensitivity. Directional concentration is reported from the
schedule intervals and cannot be relabeled as bidirectional benefit.

## Prospective action-hold bridge

Only branch 3 would justify asking Root for a separately frozen second surface.
The prospective bridge uses two UAVs with the same parameter-shared high-level
controller and separate local fast states. Each selects one of three held
heading/airspeed macros. `k` is an externally imposed high-level control or
communication hold. A completed macro supplies only its realized local
duration-correct advantage sign and selected-action score; it never supplies
unchosen macro outcomes or changes the current command. A local wind/link mode
affected by maneuver success supplies the renewal persistence analogous to the
toy hidden target.

Before activation, that surface must define a deployable learned critic,
partial-observation calibration, real low-level integrator state, coordination
reward, action masks, simulator costs, and a new matched comparator and yoke.
No B1 margin, evidence, exact belief filter, or twin simulator privilege
transfers. B1 itself contains no UAV, safety, coordination, or flight evidence.

## CM and external-review boundary

This card rejects the alternative full-action audit/semigroup toy: revealing
terminal outcomes for unselected actions or updating with a centered
all-action vector would change the protected selected-action mechanism and is
not RISP-B1.

CM may assess static constructability and resource class against this exact
revision. It must not bind the object to the existing standalone R30 lane,
which does not supply the required online boundary/switch semantics. Missing
candidate-local code is engineering work, not scientific evidence. No
construction, tests, stochastic materialization, or run is authorized by this
card.

Before production, this entire science-bearing revision requires a literal
same-conversation ChatGPT External Pro disposition of `CLOSED` or
`REVISION_REQUIRED`, followed by same-direction EM intake. Pro closure would
not authorize implementation or compute; CM retains technical acceptance and
Root retains portfolio, resource, and production sequencing authority.
