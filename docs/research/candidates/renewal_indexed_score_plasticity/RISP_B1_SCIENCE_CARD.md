# Renewal-Indexed Score Plasticity B1 science card

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-B1
revision=RISP-B1-SCIENCE-20260813-04
supersedes=RISP-B1-SCIENCE-20260813-03_CM_CLARIFICATION_REQUIRED
owner=/root/em_renewal_indexed_score_plasticity
paired_cm=/root/cm_renewal_indexed_score_plasticity
artifact_status=FROZEN_FOR_CM_FEASIBILITY_AND_EXTERNAL_REVIEW
scientific_activity_started=false
production_authorized=false
external_mathematical_closure=not_yet_requested
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
RISP-INTACT       RISP-TWIN-YOKED
SIGN-RNN-INTACT   SIGN-RNN-TWIN-YOKED.
```

Yoking is evaluation-only and uses a prospectively keyed, exact pre-interval
environment twin. It substitutes only the advantage sign. It does not retrain
the policy, select an opposite sign, reveal an unchosen action, or use an
observed treatment outcome to choose a donor.

The strongest alternatives are generic reward-conditioned recurrence, the
fixed coordinate prior and its optimization path, critic calibration, and
different numbers of renewal opportunities per physical time. The toy removes
differential critic fitting and matches work/update opportunity within every
schedule, but it cannot remove the genuine fact that smaller `k` permits more
legal actions. All task effects are therefore measured per primitive time and
renewal counts are reported separately.

The maximum claim is finite and toy-local. RISP-B1 cannot establish an unbiased
full-return policy-gradient update, necessity of natural scores, arbitrary or
unknown `k`, continual learning, learned termination, mid-hold adaptation,
skill rebinding, variable `N`, cooperative credit, safety, UAV value, or real
deployment value. No observation, threshold, or acceptance from another
direction is used here.

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
recipient next hidden target, twin outcome, or future `k`. A shared feedback
engine observes the selected action and realized rewards, constructs the packet
defined below, and exposes only its controller-visible view. This restriction
is identical in both architecture arms and both feedback cells.

The per-agent task endpoint is physical-time mean reward. The episode endpoint
averages both agents:

```text
J = (1/(2*T)) * sum_i sum_(t=0)^(T-1) r_(i,t).
```

Also report the first 48 post-switch ticks (`t=96,...,143`), physical-time
regret against the exact-state-oracle descriptive controller, action entropy,
renewal count, and recovery curves indexed separately by physical ticks and by
completed renewals. None replaces `J` as the primary endpoint.

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
finite exact DGP. In a twin-yoked cell this same filter is deliberately driven
by the supplied twin sign, never the hidden recipient outcome. It is then a
counterfactual controller belief rather than an oracle belief about the
recipient environment. This prevents a later baseline or packet from leaking a
previous recipient sign back into the yoked controller. No parameter is fitted,
and no training, held-out, switch, or outcome-selected datum calibrates the
filter.

For any candidate action,

```text
m_n(a) = E[r_t | b_n,a] = b_n(a)-0.5.
```

The frozen action-independent critic baseline is the current-policy expectation

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
packet equality is required in the exact one-boundary forks used for the twin
cut and conformance diagnostics: the pre-update state, action, policy, duration,
score, Fisher, eligibility, critic belief, and baseline are cloned before the
two outcome draws. Claiming literal equality across already divergent on-policy
trajectories is explicitly forbidden.

## Prospective exact-twin sign yoke

The feedback intervention is applied only after final checkpoints are frozen.
For every recipient interval in a yoked cell:

1. At `tau_n`, clone the complete pre-interval simulator state, including
   hidden `c_n`, visible time, recipient analytic belief, policy distribution,
   chosen action, duration, and stored eligibility.
2. Before either interval outcome is inspected, bind a separate twin RNG key
   determined only by algorithm seed, schedule, episode, agent, and renewal
   index.
3. Force the twin to execute the same selected action for the same duration.
   Draw an independent `Y_twin` from the same conditional law and set its held
   primitive rewards to that outcome. Do not simulate or expose unchosen
   actions.
4. Use the recipient's same `B_n` to form
   `delta_twin=R_twin-B_n` and apply the exact zero/deadband sign rule.
5. Substitute only `s_twin` (and deterministic fields derived from it,
   `s_twin*e_n` and `s_twin*||e_n||`) into the recipient fast transition. The
   recipient environment continues with its actual outcome and hidden target.
   Its reward, residual, belief update, and next target remain inaccessible to
   the yoked controller; its controller belief is updated from `s_twin` only.

Conditional on the complete pre-interval state and chosen action, the twin sign
has exactly the recipient sign's marginal law and is independent of the
recipient outcome draw and recipient next target. This is context matching by
construction, not nearest-neighbor donor selection. The intervention never
chooses a discordant or opposite sign. Because horizons and schedules contain
only complete holds, there is no missing twin renewal. A missing or nonfinite
twin record invalidates the paired replicate and is never imputed.

For each target schedule, feedback integrity requires all of the following on
the registered evaluation panel:

- at least `0.10` empirical probability for each nonzero twin sign within each
  `(k, selected-action-matches-hidden-target)` stratum;
- recipient/twin nonzero-sign discordance in `[0.20,0.80]` in each such stratum;
- zero-sign rate below `0.05` in every cell;
- identical counts and timing of recipient and twin packets; and
- no policy-visible recipient reward, residual magnitude, belief, posterior,
  hidden target, or next-target field.

Failure makes the feedback interaction nonidentifying. It is not repaired by
permuting donors, selecting opposite signs, widening strata, or conditioning on
observed performance.

The immediate causal timing diagnostic forks each frozen controller at its
first completed nonterminal interval wholly under fixed held-out `k=12`, and at
the first completed nonterminal interval after each switch. The intact and
twin-sign copies share the exact pre-update state and packet, then act freely
for the next legal hold. Report their next-action total variation and next-hold
physical return. Full-episode factorial `J` remains the value endpoint; the
fork only proves that any feedback effect occurs after a legal completed
renewal rather than during the current hold.

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
uses exactly 64 complete episodes. The intact and twin-yoked cells clone the
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
outcomes, but cannot change consumption count or order. The exact twin at
renewal `n` uses one separately instantiated stream and one raw word:

```text
TWIN_KEY = 30_000_000_000
           + 1_000_000_000*algorithm_seed
           + 100_000_000*schedule_id
           + 1_000_000*episode
           + 1_000*agent + n.
```

It applies the same action-match threshold to the cloned hidden target and
recipient action. Architecture, feedback, action, reward, and performance never
enter a key. Changing a key, draw count, consumption order, conversion, or
conditional mapping after any question-relevant output creates a new science
revision.

Descriptive `UNIFORM` and `STATE-ORACLE` controllers are evaluated on the same
64 episode tapes. `UNIFORM` samples all three actions equally. `STATE-ORACLE`
observes the experimenter-only current target `c_n` and, with the same `0.05`
support floor, assigns the remaining mass to that target action. It is a
privileged-information headroom control, not a primary comparator and cannot
establish algorithm value by itself.

The registered maximum, excluding the cheap exact twins, is

```text
training:   8 seeds * 2 architectures * 4096 episodes * 2 agents * 192 ticks
          = 25,165,824 agent-ticks
evaluation: 8 * 4 factorial cells * 5 schedules * 64 episodes * 2 * 192
          = 3,932,160 agent-ticks
controls:   8 * 2 controllers * 5 * 64 * 2 * 192
          = 1,966,080 agent-ticks
total     = 31,064,064 agent-ticks.
```

Exact twins add at most one outcome-only simulation for each nonterminal yoked
packet and never call another policy. The requested technical class is one CPU
process, no GPU, at most 1 GiB RSS and 60 minutes wall time. A CM finding that
these limits are not conservative returns a resource-concept clarification;
it does not authorize fewer seeds, episodes, schedules, cells, or updates.

## Activity, parity, and validity conditions

Question-relevant activity begins only when a frozen evaluation cell completes
a nonterminal hold, constructs a finite packet, applies exactly one registered
fast update, and a later legal policy decision actually reads the resulting
state. Training loss, parameter change, a completed terminal hold, a packet
without a later action, or any mid-hold diagnostic is not question-relevant
activity.

Every conclusion additionally requires:

1. exact decision/update counts in the table, complete `T=192` episodes, common
   action support, and no mid-hold policy rows;
2. identical 117-scalar architecture counts, optimizer exposure, BPTT/detach
   law, packet schema, and transition matvec count;
3. the algebraic mask-translation conformance identity;
4. `||e_n||_2>0.05` for at least 95% of nonzero-sign target packets;
5. projection active on fewer than 10% of target updates;
6. next-policy total variation at least `0.005` after at least 25% of nonzero
   target updates in both intact architectures;
7. every feedback-integrity condition above;
8. final checkpoints and all slow/recurrent parameters frozen before any
   target or yoked episode; and
9. a finite complete result for all eight algorithm seeds.

To rule out a deliberately untrained generic comparator, SIGN-RNN-INTACT must
capture at least 20% of the `STATE-ORACLE minus UNIFORM` mean-reward gap at both
seen schedules. The gap itself must be at least `0.10`, and neither primary arm
may capture more than 95% of it. Failure makes OOD architecture attribution
nonidentifying; it is not a reason to add updates or tune on target schedules.
For the narrower statement that the score anchor specifically improves OOD
transfer rather than all finite-budget learning, the two-sided 90% seed-level
interval for `RISP-INTACT minus SIGN-RNN-INTACT` must also lie within
`[-0.02,+0.02]` at each seen schedule.

## Estimands and frozen interpretation

Episodes are averaged within algorithm seed, schedule, architecture, and
feedback cell. The eight algorithm seeds, not episodes or agents, are the
independent uncertainty units. Let `J_AF,s(r)` be that seed-level mean, with
`A in {R,G}` and `F in {I,Y}`. For every schedule define

```text
D_I(r)   = mean_s [J_RI,s(r)-J_GI,s(r)]
D_Y(r)   = mean_s [J_RY,s(r)-J_GY,s(r)]
Psi(r)   = mean_s [(J_RI,s-J_GI,s)-(J_RY,s-J_GY,s)]
C_R(r)   = mean_s [J_RI,s(r)-J_RY,s(r)].
```

The primary target quantities average seed-level effects over exactly the three
target schedules `{12,4->12,12->4}` before computing a `df=7` paired t
interval. Exact `2^8` sign-flip p-values and all seed effects are reported but
do not replace intervals or margins.

A **feedback-dependent RISP finite-toy advantage** requires all validity and
adequacy conditions plus:

- the one-sided 95% lower bound for pooled target `D_I` exceeds `+0.020` mean
  reward per primitive tick;
- the one-sided 95% lower bound for pooled target `Psi` exceeds `+0.015`;
- the one-sided 95% lower bound for pooled target `C_R` exceeds `+0.015`;
- for each of the three target schedules, its simultaneous one-sided
  `1-0.05/3` lower bound for `D_I(r)` exceeds `-0.010`; and
- the two-sided 90% interval for pooled target `D_Y` lies wholly inside
  `[-0.010,+0.010]`.

The final condition prevents a coordinate advantage that survives severing
recipient feedback from being called signed-score plasticity. The immediate
fork must also show that the first changed policy/output occurs only after the
completed update; it has no separate numeric success margin.

Interpret outcomes in this order:

1. **Invalid or nonidentifying.** Any activity, packet, support, parity,
   containment, critic, yoke, count, freeze, output, headroom, or finite-value
   condition fails. No positive, negative, equivalence, or null claim follows.
2. **Material harm.** If valid, a one-sided 95% upper bound for pooled target
   `D_I` is below `-0.020`, or any simultaneous target-schedule upper bound is
   below `-0.030`, reject this exact RISP treatment on this toy. This overrides
   a favorable interaction elsewhere.
3. **Feedback-dependent finite-toy advantage.** All positive conditions pass.
   Retain the composite score-anchored coordinate prior as a direct variable-`k`
   candidate on this finite surface. If the seen equivalence condition also
   passes, the result supports the narrower finite-budget OOD-inductive-bias
   reading; otherwise it supports only an overall finite-budget package effect.
4. **Package value without feedback integrity.** Pooled target `D_I` passes but
   `Psi`, `C_R`, or yoked equivalence does not. Report an architecture/training
   package effect only; do not attribute it to recipient signed-score feedback.
5. **Generic sign memory sufficient.** The two-sided 90% intervals for pooled
   `D_I` and `Psi` both lie within `[-0.010,+0.010]`, both intact arms clear
   adequacy, and intervals are otherwise conclusive. On this treatment and
   budget, the explicit score anchor adds no registered minimum value beyond
   generic sign-state recurrence. This does not prove global equivalence.
6. **Feedback useful generically.** Both architectures improve intact over
   yoked by at least the registered `+0.015` lower-bound magnitude while `Psi`
   is equivalent to zero. Recipient feedback matters, but RISP specificity is
   unsupported.
7. **Statistically unresolved.** Valid data fit none of the above. Do not add
   seeds, weaken margins, select a favorable schedule, or automatically rerun.

An effect visible per renewal but absent from physical-time `J`, or an effect
confined to one switch direction, is reported as update-frequency geometry or
directional hysteresis and cannot satisfy the pooled variable-`k` claim.

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
