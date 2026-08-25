# SGSP RIDGEGATE-2Z revision-02 ChatGPT External Pro closure request

You are continuing the existing dedicated SGSP scientific conversation. Audit
the exact prospective definition-only object
`SGSP-RG2Z-SCIENCE-20260815-02`. It is a new task and not a rerun, result or
trajectory continuation of SGSP B1/r06. Do not review code, files, runtime,
hashes or portfolio priority. Decide only whether the complete task,
comparison, inference and claim below are mathematically and causally closed.

Return exactly `CLOSED` or `REVISION_REQUIRED`. If revision is required, name
each science-bearing defect and the smallest exact correction. This layer
authorizes no source, test, probe, stochastic coordinate, training or
evaluation.

## 1. Identity and revision delta

```text
direction=semantic_graphon_shared_policy
portfolio_object=SGSP-TARGET-BOUND-TWO-ZONE-DEFINITION
revision=SGSP-RG2Z-SCIENCE-20260815-02
task=RIDGEGATE-2Z
definition_only=true
result_blind=true
scientific_activity_started=false
```

No old SGSP task, kernel, model state, budget, seed, threshold, checkpoint,
tape, interval or result enters this object. Revision 02 preserves revision
01's named task, variable-N axis, nested comparator, 512-update budget, six
margins, 18-quantity family, branches and claim ceiling. Before any provider or
scientific activity, it closes exact dynamics/trainer/estimand gaps and replaces
an algebraically degenerate treatment-only attenuation with the symmetric
PHY/EDGE cut contrast below. No wrong-center arm, second budget or second
surface is added.

## 2. Exact task and slot dynamics

There are static `WEST` and `EAST` basins and stable public roles
`WEST-SURVEYOR`, `EAST-SURVEYOR`, `RIDGE-RELAY`. Fleets are balanced with
`N/3` exchangeable agents per role. One shared policy trains at `N={9,15}` and
is deployed unchanged at held-out `N={6,21}`. Role multiplicities are thus
seen at `3,5` and held out at `2,7`. Identity and role-local index are forbidden
policy inputs. There is no roster-specific head, normalization, recurrent
initialization, calibration, adaptation or replay. Membership is fixed within
an episode.

An episode has slots `0,...,11`. Each basin independently has exactly three
event times sampled uniformly without replacement from `0,...,7`. An event has
a simulator-only equality ID. A surveyor detects its basin event independently
with probability `0.75` only on `SCAN` in that event slot. A detected report is
timely iff its first base arrival satisfies `arrival-event_time<=3`.
Surveyor FIFO capacity is two and relay FIFO capacity is four; overflow inserts
at the tail and drops the oldest head. Duplicate copies may exist but the base
deduplicates by equality ID.

The common union alphabet is
`SCAN|UPLINK|LISTEN_WEST|LISTEN_EAST|FORWARD_BASE|HOLD`. Surveyors may use
`SCAN|UPLINK|HOLD`; half-duplex relays may use either listen action,
`FORWARD_BASE|HOLD`.

Every slot has the same exact order:

1. Process packets scheduled before decision `t`; accept nonexpired relay
   arrivals; count only first timely base arrivals; acknowledge every decoded
   transmission, including a base duplicate.
2. Remove a surveyor head if at least one relay decoded its preceding uplink;
   remove a relay head after a decoded base forward. Failed transmissions keep
   the head for retransmission.
3. Purge items with `t>=event_time+4`; form predecision observations.
4. Encode status messages, aggregate, update the GRU once, and sample actions.
5. Radio actions select the predecision head, resolve collision/channel laws,
   and schedule successes for `t+1`; empty actions schedule nothing.
6. Resolve `SCAN` and append new detections after radio actions, preventing
   same-slot uplink.
7. Record waste after reception outcome and retain postaction buffers.

After slot 11, packets scheduled for 12 cannot score. A new report's fastest
surveyor-to-relay-to-base delivery is at `event_time+3`.

At `t=0`, all FIFOs and in-flight-arrival sets are empty, recurrent states are
zero, and previous-action/outcome observation fields are zero. FIFO positions
are exposed and updated head-to-tail.

## 3. Packet, observation and reward law

The physical role-pair table is

```text
P0 = [[0.92,0.48,0.88],
      [0.48,0.92,0.82],
      [0.86,0.78,0.90]]
L  = [[1,2,1],
      [2,1,1],
      [1,1,1]]
```

with receiver rows and sender columns in the public role order. Before
contention,

```text
p_ab(n_b)=logistic(logit(P0_ab)-0.22*(n_b-1))
K0_ab(n_b)=p_ab(n_b)/L_ab.
```

Mission uplink uses only the row `receiver=RIDGE-RELAY` and the sending
surveyor column. In a basin/slot, zero uplinks produces nothing; two or more
uplinks collide completely with no capture; with one nonempty sender, each
relay choosing that basin independently decodes with `p_RELAY,b(n_b)` and
receives at `t+1`.

The base is separate from the nine learned role-pair edges:

```text
p_BASE(n_R)=logistic(logit(0.90)-0.22*(n_R-1)), latency=1.
```

Exactly one nonempty forwarding relay is decoded with this probability; two or
more collide completely. A decoded duplicate/expired item is acknowledged and
removed but does not score.

An uplink decoded at `t+1` but then expired is link-acknowledged and dequeued by
the surveyor, discarded by the relay, counted as waste, and does not set the
policy success field. A duplicate or expired base decode is likewise link-
acknowledged and dequeued but neither scores nor sets that success field.

Every radio action has one waste indicator: an uplink is waste iff no matching
listening relay both decodes and enqueues a nonexpired copy; a listen is waste
iff that relay decodes no nonexpired report; a
forward is waste iff it creates no new timely distinct base delivery, including
empty, collision, channel failure, duplicate, expiry or horizon overrun.

The exact 22-vector predecision observation is role one-hot (3), `t/11` (1),
role counts divided by 7 (3), four FIFO positions each with occupied bit and
clipped age/3 (8), previous union action one-hot (6), and previous radio-
outcome success (1). That bit is one for uplink only when at least one relay
decodes and enqueues a nonexpired report, for listen only when the relay decodes
and enqueues a nonexpired report, and for forward only upon a new timely
distinct base delivery. Link acknowledgement/dequeue of late or duplicate
packets is not an observed success. Surveyors zero their unused final two FIFO
positions. There is no confidence. Event IDs, future/undetected events, raw
agent identity, packet coins, other buffers and reward components are absent.

Each agent encodes this vector into one 32-vector status message before action.
The fixed-width messages use a noiseless same-slot abstract policy bus shared
by both arms, include self in role sums, contain no report payload/ID, never
enqueue/deliver reports, and do not consume mission half-duplex radio.

If `D_z` is timely distinct delivery count and `WASTE` is waste radio actions
divided by all radio actions (zero when none),

```text
J=0.65*(D_W+D_E)/6 + 0.25*min(D_W,D_E)/3 + 0.10*(1-WASTE).
```

Reward never queries `K0`, a policy edge or learned state. `P0_RELAY,W/E`
drives uplink physics; the separately declared base law drives forwarding;
all other `P0/L` entries define only the public policy prior. `K0` itself is
never a simulator or reward answer table.

## 4. Exact nested policy families

The common execution network is

```text
message encoder: Linear(22,64)-tanh-Linear(64,32)-tanh
actor input:     concat(local x[22], role summary Z[32], physical mass D[1])
actor core:      GRU(55,64), zero initial state, one update per slot
actor head:      Linear(64,6)
```

Mask illegal logits, softmax over legal actions, then mix with legal uniform:

```text
pi=0.96*softmax_legal(logits)+0.04/|A_role|.
```

The GRU is not a library-default placeholder. With input `u_t`, prior state
`h`, and gate order `z,r,n`, it is exactly

```text
z=sigmoid(W_z*u+U_z*h+b_z)
r=sigmoid(W_r*u+U_r*h+b_r)
h_tilde=tanh(W_n*u+U_n*(r elementwise-multiplied by h)+b_n)
h_new=(1-z) elementwise-multiplied by h_tilde + z elementwise-multiplied by h.
```

There are separate `W_(z,r,n)` matrices of shape `64x55`, separate
`U_(z,r,n)` matrices of shape `64x64`, one bias per gate, reset-before-matrix,
and no packed alternative or second bias.

For `n in {2,3,5,7}`,

```text
v(n)=(2*log(n)-log(14))/log(7/2)
r_ab(n)=beta_ab0+beta_ab1*v(n)
omega_ab(n)=K0_ab(n)*exp(r_ab(n)).
```

There are 18 output-connected coefficients. With 32-vector messages `q_j`,

```text
Q_b=sum_{j:role(j)=b} q_j                 # self included
D_a=sum_b n_b*omega_ab(n_b)
Z_i=sum_b omega_ab(n_b)*Q_b/(D_a+1e-12).
```

`PHY-TRUST` projects each beta after every optimizer update into
`[-0.15,+0.15]`; `EDGE-FLEX` performs the identical projection operation into
`[-1.50,+1.50]`. Both initialize all betas at zero and start at the identical
complete policy `omega=K0`. Every treatment parameterization is literally in
EDGE; a live beta `0.60` is a strict witness outside treatment. Both use the
same coordinate chart/derivatives in the shared interior.

Arms have identical common tensors, trainable count, messages, communication,
forward/backward operators, recurrent state, critic, action support and
optimizer opportunity. There is no frozen padding, dummy gate, roster-specific
object or learned dense `N x N` tensor.

For shadow cuts, hold intact predecision observations and incoming hidden state,
alter only the current kernel summary, make one alternative GRU update and do
not propagate it. Full rotated rollouts reset to the same zero state and apply
the cut at every slot.

## 5. One exact trainer and budget

Each arm has an independent but identically initialized training-only team
critic:

```text
input: three rolewise means of the 22-vector = 66
Linear(66,64)-tanh-Linear(64,64)-tanh-Linear(64,1).
```

It sees no future/undetected events and is absent at execution. The terminal
return `J` is the undiscounted target (`gamma=1`). Each agent-slot advantage is
`stop_gradient(J-V(g_t))`. Average actor log-probability and entropy first over
agents/slots within each episode, critic MSE over the 12 team states, then
average episodes equally:

```text
L=-E[log pi(a)*(J-V)_stop] - 0.01*E[entropy(pi)]
  +0.5*E[(V-J)^2].
```

Backpropagate through all 12 slots with no truncation. There is no GAE,
importance ratio, replay, auxiliary loss, target network, validation or weight
decay.

The sole budget is 512 updates. Each update collects 64 fresh complete on-
policy episodes, alternating 32 at `N=9` and 32 at `N=15`, then performs one
full-batch forward/backward gradient call per arm. Only the immediate update-
512 checkpoint is evaluable. Projected Adam is

```text
lr=0.0003, betas=(0.9,0.999), eps=1e-8, weight_decay=0
global_gradient_norm_clip=0.5
training_precision=float32; registered statistical reductions=float64.
```

After clipping, update Adam moments/parameters, then project only beta; leave
moments unchanged. There is no inner epoch/minibatch.

For an affine weight with fan-in `m`, fan-out `n`, gain `g`, draw entries i.i.d.
`Uniform[-g*sqrt(6/(m+n)),+g*sqrt(6/(m+n))]`. Gain is 1 for both encoder
layers, each GRU input matrix, both critic hidden layers and critic output; gain
is `0.01` for actor output. For each recurrent matrix in `z,r,n` order, draw a
separate `64x64` iid standard-normal matrix, compute `M=QR`, and multiply column
`k` of `Q` by `sign(R_kk)`, with `sign(0)=+1`; use the resulting gain-one Q.
Biases, beta, Adam moments and hidden states start exactly at zero. Within a
seed, every common draw is copied bit-for-bit between arms.

Every random variable uses a stable arm-independent potential-outcome address:
phase, seed, roster, update/evaluation episode, basin/event, slot, public role,
hidden role-local simulator index, sender, receiver and random-variable kind.
Event, detection, packet, initialization and inverse-CDF action uniforms exist
whether or not divergent actions use them. No sequential action-dependent RNG
consumption defines pairing. Different roster sizes use independent world
coordinates. Exact numeric seeds/counter strings remain unbound and cannot
reuse old SGSP identities.

`UNIFORM-LEGAL` is evaluated on the same potential worlds solely as an
untrained competence floor. At seen `N`, let
`e_s(N)=J_EDGE,int_s(N)-J_UNIFORM_s(N)`. `EDGE_TRAIN_COMPETENT` requires both
simultaneous lower bounds to exceed `0.08` and both two-sided intact
`PHY-EDGE` training intervals to lie wholly within `[-0.04,+0.04]`.

## 6. Evaluation, estimands and 18-quantity family

A later empirical object, only if separately authorized, uses 24 independent
training-seed blocks and 256 fresh evaluation episodes per roster/seed. It
samples the stochastic policy, not greedy actions. Seeds are inferential units;
agents, slots and episodes are not. Held-out worlds never enter training,
normalization, adaptation, replay or selection.

For condition `c` and basin `z`, define seed episode means

```text
J_A,c_s(N)=mean_256 episode returns
T_A,c,s,z(N)=mean_256 D_z/3.
```

On intact policies,

```text
d_s(N)=J_PHY,int_s(N)-J_EDGE,int_s(N)
d_seen_s=0.5*(d_s(9)+d_s(15))
c_s(N)=d_s(N)-d_seen_s, N in {6,21}
z_s(N)=min_z T_PHY,int,s,z(N)-min_z T_EDGE,int,s,z(N).
```

Use paired seed-level Student-t intervals in one Bonferroni family of exactly
18 quantities: four `d(N)`; two competence `e(N)`; two interactions `c(N)`;
two worst-zone `z(N)`; the three cut quantities at each held-out size; and two
composite answerability scalars. Every interval is two-sided with per-quantity
error `0.05/18`.

Margins are

```text
delta_R=0.04                 direct return
delta_C=0.03                 held-out-minus-seen interaction
delta_Z=0.02                 worst-zone delivery
delta_cutR=0.05              treatment cut return loss
delta_TV=0.08                treatment cut legal-action TV
delta_I=0.03                 differential cut attenuation.
```

For `h(x;delta)=min(x,1-x)-delta`, each held-out seed defines

```text
A_dir(N)   = min_A h(J_A,int(N); delta_R)
A_inter(N) = min_{A,m in {N,9,15}} h(J_A,int(m); delta_C)
A_zone(N)  = min_{A,z} h(T_A,int,z(N); delta_Z)
A_cut(N)   = min_{c in {int,rot}} h(J_PHY,c(N); delta_cutR)
A_atten(N) = min_{A,c in {int,rot}} h(J_A,c(N); delta_I).
```

For an intact treatment distribution `p_h` with `m_h` legal actions and floor
`ell_h=0.04/m_h`, its TV supremum over distributions with the same mask/floor
is

```text
TVsup(p_h)=1-(m_h-1)*ell_h-min_{a legal} p_h(a).
A_TV(N)=mean_{episode,slot,agent} TVsup(p_h)-delta_TV.
```

The single answerability quantity per held-out size is

```text
A_s(N)=min(A_dir,A_inter,A_zone,A_cut,A_atten,A_TV).
```

Its simultaneous lower endpoint must exceed zero. This excludes score-endpoint
saturation for every positive efficacy/mechanism gate and proves the masked
legal simplex permits action-TV beyond the registered margin. It deliberately
does not claim a global oracle envelope or that every return contrast is
attainable. Once these checks and EDGE competence pass, failure of the observed
arms to meet an efficacy or cut gate is target-level failure under branch 4,
not saturation non-identification. Failure of `A(N)` itself means
`NONIDENTIFIED`. Validity separately requires complete atomic evidence,
positive basin/event/role support, exact legal support, fixed masks, no leakage,
exact matching/nesting/coupling and finite values.

## 7. Symmetric action-sensitive kernel cut

At both held-out sizes, cyclically rotate physical sender columns

```text
WEST-SURVEYOR -> EAST-SURVEYOR -> RIDGE-RELAY -> WEST-SURVEYOR
```

for each arm separately, leaving learned residual indices, counts, messages,
receiver role, local observations, actor/GRU/critic parameters, simulator,
events, reward, masks and potential outcomes fixed. Balanced roles preserve
each receiver-row coefficient multiset. EDGE's rotated rollout exists only for
differential attenuation.

On intact treatment histories, shadow replay gives

```text
V_s(N)=mean 0.5*sum_{six-action alphabet}|pi_PHY,int-pi_PHY,shadow-rot|,
```

with illegal probabilities zero. Full paired rollouts give

```text
C_A_s(N)=J_A,int_s(N)-J_A,rot_s(N)
I_s(N)=[J_PHY,int-J_EDGE,int]-[J_PHY,rot-J_EDGE,rot]
      =C_PHY_s(N)-C_EDGE_s(N).
```

The registered cut quantities are `C_PHY`, `V`, `I`. They pass only when lower
endpoints exceed `0.05`, `0.08`, `0.03`, respectively, at both held-out sizes.
Cut harm cannot rescue a failed intact comparison.

## 8. First-match decision law

1. Invalid/incomplete evidence, leakage, support/coupling failure, mismatch or
   noncontainment yields no relation.
2. Failed composite answerability at either held-out size or failed
   `EDGE_TRAIN_COMPETENT` at either seen size yields `NONIDENTIFIED`.
3. `RETAIN_PHYSICAL_PRIOR_COLDSTART` requires all earlier gates; direct
   held-out lower bounds above `0.04` at both sizes; interaction lower bounds
   above `0.03` at both; worst-zone lower bounds above `0.02` at both; and all
   six cut thresholds.
4. Every other complete, valid, answerable panel with competent EDGE selects
   `DO_NOT_RETAIN_FIXED_PRIOR_AS_DEFAULT` for this exact task/budget. Record
   every applicable descriptive subreason in this fixed order: practical
   equivalence, EDGE superiority, mixed/nonrobust roster effect, zone imbalance,
   absent action-sensitive attribution.

No branch authorizes a wrong-center arm, checkpoint/budget search, seed or
threshold change, old result pooling, source/test/probe, empirical coordinate,
second surface or UAV work.

## 9. Strongest alternative and claim ceiling

The strongest alternative is that the narrower projection domain, count/load
normalization, curvature, regularization or optimizer preconditioning—not
semantic correctness—provides finite-budget benefit. Identical initial policy,
literal nesting, common chart, exact trainer/optimizer matching, seen-size
competence, cold-start interaction and differential cut attenuation reduce but
cannot eliminate that explanation. No kernel-truth, rate or asymptotic claim is
available.

The maximum positive statement is:

> In the exact static two-basin `RIDGEGATE-2Z` toy, one shared recurrent policy
> constrained near a reward-independent terrain/radio role kernel achieved an
> action-sensitive return advantage over a competent, equally initialized and
> strictly containing matched EDGE learner at adaptation-free held-out
> `N={6,21}` after exactly 512 matched updates; the advantage was larger than
> at seen `N={9,15}`, preserved the worse basin, and attenuated more than EDGE
> under the same sender-role semantic cut.

It cannot establish a learning curve, faster convergence, asymptotic
superiority, kernel truth, another budget/roster, arbitrary terrain or role
mix, churn, moving zones, fading robustness, perception validity, flight
dynamics, safety, real-radio performance, a second surface or UAV mission
benefit. The toy-to-UAV mapping is limited to time-limited west/east
observations, half-duplex ridge relays and fleet-size-dependent contention.

## Required closure audit

1. Is the slot/channel/reward construction exact, physically coherent enough
   for the bounded toy claim, and independent of policy/reward answer tables?
2. Is `PHY-TRUST` literally and strictly contained in a non-handicapped EDGE
   family under identical initialization, information, training critic,
   parameter/work/optimizer opportunity and one checkpoint?
3. Does the exact actor-critic and arm-independent potential-outcome law give
   the 512-update budget and seed pairing fixed scientific meaning?
4. Are all 18 seed estimands, the two composite endpoint-interiority/action-
   support scalars and the first-match branches coherent, two-sided and result-
   blind? In particular, is the declared limited answerability role coherent,
   or does this exact claim require a prospectively computable task-conditioned
   attainable-return envelope despite the target-level deletion branch?
5. Does symmetric rotation make `I=C_PHY-C_EDGE` a genuine differential
   attenuation rather than an algebraic copy of treatment cut loss, while
   preserving action-sensitive interpretation?
6. Does the claim retain the unavoidable regularization/preconditioning
   alternative and the toy/UAV boundary?
7. May exact numeric seed/counter/artifact bindings remain unbound at this
   definition-only layer if they must preserve the declared coupling and return
   for closure whenever they change science?

## Required response format

```text
MATH_CLOSURE_DECISION=CLOSED|REVISION_REQUIRED
EXACT_REVISION=SGSP-RG2Z-SCIENCE-20260815-02
RESULT_BLIND=true

TASK_CHANNEL_AND_REWARD
<audit>

CONTAINMENT_AND_MATCHING
<audit>

TRAINER_AND_COLD_START_IDENTIFIABILITY
<audit>

INFERENCE_ANSWERABILITY_AND_BRANCH_LAW
<audit>

SYMMETRIC_CUT
<audit>

DEFECT_LEDGER
SCIENCE_BEARING_DEFECT_COUNT=<integer>
<NONE or numbered exact defects and smallest repairs>

STRONGEST_ALTERNATIVE
<remaining explanation>

CLAIM_CEILING
<maximum statement and exclusions>

FINAL_DISPOSITION=CLOSED|REVISION_REQUIRED
```
