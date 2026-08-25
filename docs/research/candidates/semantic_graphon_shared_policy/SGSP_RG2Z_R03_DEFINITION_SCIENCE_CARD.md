# SGSP RIDGEGATE-2Z revision-03 definition science card

```text
direction=semantic_graphon_shared_policy
portfolio_object=SGSP-TARGET-BOUND-TWO-ZONE-DEFINITION
revision=SGSP-RG2Z-SCIENCE-20260815-03
task_name=RIDGEGATE-2Z
owner=EM_semantic_graphon_shared_policy
object=definition_only_variable_N_two_zone_surveillance_relay_discriminator
supersedes=SGSP-RG2Z-SCIENCE-20260815-02_before_scientific_activity
scientific_activity_started=false
empirical_coordinates_bound=false
mathematical_closure=pending_same_conversation_ChatGPT_External_Pro
gemini_innovation=submitted_unverified_no_response_advisory_non_gating
construction_authorization=none
test_or_probe_authorization=none
training_or_evaluation_authorization=none
compute_authorization=none
old_result_transfer=forbidden
```

## Conclusion first

`RIDGEGATE-2Z` is a new, finite-horizon, cooperative two-basin surveillance
and relay task. One shared recurrent policy controls stable public roles across
two training roster sizes and is deployed unchanged at smaller and larger
held-out rosters. `PHY-TRUST` constrains its role/load interaction residuals
near a reward-independent terrain/radio kernel. `EDGE-FLEX` begins at the
identical complete policy, receives identical information and physical inputs,
uses the identical parameterization and training opportunity, and strictly
contains the treatment through a wider residual box.

The one question is whether the narrow physical prior provides an
action-sensitive, task-valued cold-start advantage at one fixed budget after
the containing EDGE learner has demonstrated competence on the seen roster
sizes. A positive must beat EDGE directly at both held-out sizes, improve more
there than at the seen sizes, preserve the worse basin, and lose more of its
advantage than EDGE when the same physical sender-role association is broken.
Every other valid, answerable complete panel with competent EDGE does not
retain the fixed prior as the default for this exact task and budget.

Revision 03 preserves revision 02's task family, roster axis, comparator
nesting, one 512-update budget, six margins, 18-quantity simultaneous family,
branch precedence and claim ceiling. It accepts the r02 same-conversation Pro
review's three exact prospective repairs: event-origin FIFO age persistence,
the trained-arm domain of composite answerability, and literal predicates for
branch-4 reporting. Revisions 01 and 02 remain immutable unexecuted precursors.

This card authorizes no source, build, test, probe, stochastic coordinate,
rollout, checkpoint, training, evaluation or compute.

## Five-line science card

- **Question.** At one fixed useful-work budget, does a terrain/radio-derived
  interaction prior protect a shared surveillance/relay policy from cold-start
  degradation at unseen fleet sizes relative to a competent, strictly
  containing, matched EDGE learner?
- **Treatment.** `PHY-TRUST` uses the declared physical kernel and the same 18
  output-connected load-residual coefficients as EDGE, projected into a narrow
  trust box.
- **Comparator.** `EDGE-FLEX` starts at the identical policy, sees every public
  physical input, uses identical architecture, data, optimizer and work, and
  permits those same coefficients over a strictly wider box.
- **Observable.** Seed-level return, held-out-minus-seen return interaction,
  worst-basin timely delivery, and a same-cut comparison of legal-action TV,
  treatment return loss and PHY-versus-EDGE advantage attenuation.
- **Strongest alternative and ceiling.** A positive can still be a useful
  finite-budget constraint, regularizer or preconditioner rather than semantic
  truth. It supports only this exact toy, budget and held-out roster set, not a
  learning curve, arbitrary terrain, churn or UAV efficacy.

## 1. New-object, revision and legacy firewall

No SGSP B1/r06 roster, task state, kernel coefficient, network state, budget,
seed, threshold, checkpoint, tape, interval, label or result enters this
object. The only inherited qualitative lesson is the portfolio-supplied
requirement that harm from one wrong center cannot retain SGSP without direct
value over a fair strictly containing EDGE learner.

Revision 03 is prospective and preactivity. It changes no observed empirical
object because no `RIDGEGATE-2Z` stochastic value or policy output exists. The
r02 same-conversation Pro response required only the three clarifications named
above. No treatment, comparator, budget, estimand, margin, multiplicity law,
cut, branch precedence, claim ceiling, wrong-center arm, old result or second
surface is added or changed.

## 2. Exact `RIDGEGATE-2Z` task

### 2.1 Public roles and variable rosters

There are two static basins, `WEST` and `EAST`, separated by a ridge. Every
agent has one stable public role for the whole episode:

```text
WEST-SURVEYOR
EAST-SURVEYOR
RIDGE-RELAY
```

Agents are exchangeable within role. Identity, role-local index, hidden rank
and learned role assignment are forbidden policy inputs. Every registered
roster is balanced with exactly `N/3` agents in each role. One shared
parameterization trains only at

```text
N_train={9,15}
```

and is deployed without adaptation at

```text
N_heldout={6,21}.
```

Role multiplicities are therefore `3,5` during training and `2,7` at held-out
deployment. Membership and roles are fixed within an episode. No roster-
specific head, embedding, normalization, recurrent initialization,
calibration, finetuning, validation or replay is allowed.

### 2.2 Events, reports, buffers and actions

An episode has slots `t=0,...,11`. Independently in each basin, exactly three
event times are sampled uniformly without replacement from `0,...,7`. Each
event has a simulator-only equality ID `(basin,event_ordinal)` used for
deduplication. It is never a policy or message feature.

A surveyor detects its basin's event independently with probability `0.75`
only if it chooses `SCAN` in the event slot. A detection creates one report
with that equality ID and event time. There is no confidence variable. A
report is timely only if a first base arrival occurs at a slot `u` satisfying
`u-event_time<=3`. Thus it is valid through the end of the fourth event-
inclusive slot and expires before decision `event_time+4`.

Each surveyor has a FIFO capacity of two reports; each relay has a FIFO
capacity of four. Copies with the same event ID may coexist in different
buffers. On overflow, insert at the tail and drop the oldest head. Expired
items are never transmitted. The common union action alphabet is

```text
SCAN | UPLINK | LISTEN_WEST | LISTEN_EAST | FORWARD_BASE | HOLD
```

with fixed role masks:

- a surveyor may use `SCAN`, `UPLINK`, `HOLD`;
- a relay may use `LISTEN_WEST`, `LISTEN_EAST`, `FORWARD_BASE`, `HOLD`.

Relays are half duplex because each slot permits exactly one of listen,
forward or hold. Both learned arms have identical masks, buffers, transition
support and legal-action probability floor.

### 2.3 Within-slot state-transition order

Every slot uses this order, identically for all arms:

1. Process mission packets scheduled to arrive before decision `t`. A relay
   accepts a nonexpired uplink copy at its FIFO tail. The base counts the first
   timely arrival of each event ID and acknowledges every successfully decoded
   forward, including a duplicate. Arrivals at `t>=event_time+4` are discarded
   as expired and cannot score.
2. Apply acknowledgements to the sender buffers. A surveyor removes its FIFO
   head if at least one relay decoded its preceding uplink. A relay removes its
   FIFO head after any decoded base forward, whether or not the event was a new
   delivery. Failed transmissions leave the head in place for later
   retransmission.
3. Purge every remaining report with `t>=event_time+4` and form the exact
   predecision observations in Section 2.5.
4. Encode one status message per agent, form the role summaries, update the
   recurrent actor once, and sample one legal action per agent.
5. `UPLINK` and `FORWARD_BASE` select the predecision FIFO head. Resolve the
   conditional collision/channel law in Section 2.4 and schedule successful
   arrivals for `t+1`. An empty-buffer action schedules nothing.
6. Resolve `SCAN`. A report detected at slot `t` is appended only after radio
   actions, so it cannot be uplinked before slot `t+1`.
7. Record action-level waste once the slot's reception outcome is known and
   retain the postaction buffers for the next slot.

After the actions at `t=11`, the episode ends. Packets scheduled for `t=12`
cannot score and their initiating radio actions have no successful reception.
This order gives a newly scanned report a minimum surveyor-to-relay-to-base
arrival at `event_time+3`.

At `t=0`, every surveyor and relay FIFO and every in-flight-arrival set is
empty, every recurrent state is zero, and every previous-action and previous-
outcome observation field is zero. FIFO positions are always exposed and
updated head-to-tail.

### 2.4 Conditional packet, collision and base-link law

The role-pair physical table and load law are defined in Section 3. They are
pre-contention reception probabilities. Mission uplink uses only the entries
whose receiver is `RIDGE-RELAY` and sender is the appropriate surveyor role.

For each basin and slot:

- zero transmitting surveyors produces no uplink;
- two or more transmitting surveyors collide completely, with no capture;
- with exactly one nonempty `UPLINK` sender, every relay choosing the matching
  `LISTEN` action independently decodes that report with probability
  `p_RELAY,b(n_b)`; successful copies arrive before decision `t+1`;
- different listening relays' reception coins are conditionally independent.

An uplink physically decoded at `t+1` but then expired is link-acknowledged and
dequeued by the surveyor, discarded by the relay, counted as waste, and never
sets the policy's success field. A base-link decode of a duplicate or expired
packet is likewise link-acknowledged and dequeued, but it does not score and
does not set the policy's success field.

The base is a separate physical endpoint, not a tenth learned role-pair edge.
With relay multiplicity `n_R`, its pre-contention success probability is

```text
p_BASE(n_R)=logistic(logit(0.90)-0.22*(n_R-1)), latency=1 slot.
```

Exactly one nonempty relay `FORWARD_BASE` transmitter is decoded with that
probability. Two or more relay transmitters collide completely, with no
capture. A decoded duplicate or expired report is acknowledged and removed
but does not increase timely distinct delivery.

Define one waste indicator for every radio action (`UPLINK`, either `LISTEN`,
or `FORWARD_BASE`):

- an `UPLINK` is waste iff no matching listening relay both decodes and
  enqueues a nonexpired copy;
- a `LISTEN_b` is waste iff that relay decodes no nonexpired report from basin
  `b` in the slot;
- a `FORWARD_BASE` is waste iff it produces no new timely distinct base
  delivery, including empty buffer, collision, channel failure, duplicate,
  expiry or horizon overrun.

There is no capture, receiver choice, adaptive retransmission priority or
hidden routing rule. Every stochastic coin is arm-independent under the
potential-outcome coupling in Section 5.3.

### 2.5 Exact observation and status-message information

At each predecision time, agent `i` receives a fixed 22-vector `x_i,t`:

```text
public role one-hot                                      3
slot t/11                                                1
public role counts (n_W,n_E,n_R)/7                       3
four FIFO positions: occupied bit and clipped age/3      8
previous union action one-hot                            6
previous radio-outcome success bit                      1
                                                        --
total                                                   22
```

Every packet copy permanently carries its originating physical `event_time`.
Queue transfer, relay duplication, retransmission and movement between a
surveyor FIFO and relay FIFO never reset it. For an occupied FIFO position at
predecision slot `t`,

```text
packet_age(t)=max(0,t-event_time)
age_feature(t)=min(packet_age(t),3)/3.
```

Every empty FIFO position is exactly `(occupied=0,age_feature=0)`. Surveyors
encode positions three and four exactly as `(0,0)`. The success bit is one only
when the agent's preceding radio action succeeded in its policy-relevant sense:
surveyors had at least one relay decode and enqueue a nonexpired report;
listening relays decoded and enqueued at least one nonexpired report;
forwarding relays caused a new timely distinct base delivery. It is zero for
nonradio actions and every other outcome. Link-layer acknowledgement/dequeue
of a late or duplicate packet is part of the transition law, not an observed
success bit.

Raw counts are available only to the declared kernel/load calculation; the
actor observes the normalized counts above. Report IDs, event order, undetected
events, future events, role-local agent index, packet coins, other buffers and
reward components are absent.

Before the action, every agent maps `x_i,t` to one 32-vector status message.
These fixed-width status messages use a noiseless, one-round, abstract policy
communication bus shared by both arms. They do not consume the half-duplex
mission radio, never contain report payloads or equality IDs, never enqueue or
deliver reports, and have no simulator or reward effect. Role sums include the
receiver's own message. Communication volume is exactly one 32-vector per
agent per slot in both arms.

### 2.6 Return and physical endpoints

Let `D_z` be the number of that basin's three distinct event IDs first
delivered to base on time. Let `WASTE` be the number of waste indicators above
divided by the number of radio actions, and define it as zero if there is no
radio action. The episode return is

\[
J=0.65\frac{D_W+D_E}{6}
 +0.25\frac{\min(D_W,D_E)}{3}
 +0.10(1-WASTE)\in[0,1].
\]

The evaluator also records each basin's timely-delivery rate `D_z/3`, duplicate
and expired arrivals, collision loss, empty actions, all radio decisions and
new timely deliveries per radio decision. Only realized legal actions and task
return establish value. The reward never queries a policy kernel, residual,
message embedding or learned state.

## 3. Reward-independent physical semantic kernel

The declared normalized ridge/link model is frozen before reward weights,
events, learning or outcomes. With receiver rows and sender columns ordered
`(WEST-SURVEYOR,EAST-SURVEYOR,RIDGE-RELAY)`, it is

\[
P^0=\begin{bmatrix}
0.92&0.48&0.88\\
0.48&0.92&0.82\\
0.86&0.78&0.90
\end{bmatrix},\qquad
L=\begin{bmatrix}
1&2&1\\
2&1&1\\
1&1&1
\end{bmatrix}.
\]

For sender-role multiplicity `n_b`,

\[
p_{ab}(n_b)=\operatorname{logistic}
(\operatorname{logit}P^0_{ab}-0.22(n_b-1)),\qquad
K^0_{ab}(n_b)=p_{ab}(n_b)/L_{ab}.
\]

`P0_RELAY,WEST`, `P0_RELAY,EAST` and their unit latencies drive the mission
uplink transition. The separately declared base law drives relay-to-base
transition. All other `P0/L` entries define only the public role-pair policy
prior; they are not simulator transition probabilities or a reward table. The
simulator never queries `K0` or learned weights. Reward relabeling/rescaling
leaves every physical table unchanged. This is a normalized toy law, not field
calibration.

## 4. Exact policy families and strict containment

### 4.1 Common message encoder and recurrent actor

Each learned arm has a separate parameter copy with identical initialization:

```text
message encoder: Linear(22,64) -> tanh -> Linear(64,32) -> tanh
actor input:     concat(x_i,t[22], Z_i,t[32], D_role[1]) = 55
actor core:      GRU(input=55, hidden=64), one update per slot
actor head:      Linear(64,6) union-action logits
```

The recurrent state is zero at episode start and updated after the same-slot
status messages are formed. Illegal logits are masked to negative infinity,
softmax is taken over the role's legal set, and the executed policy is

\[
\pi(a|h)=0.96\,\operatorname{softmax}_{legal}(\ell)_a
          +0.04/|A_{role}|.
\]

The GRU convention is frozen rather than delegated to a library default. For
actor input `u_t` and prior hidden state `h_{t-1}`, with gate order `z,r,n`,

\[
z_t=\sigma(W_z u_t+U_z h_{t-1}+b_z),\qquad
r_t=\sigma(W_r u_t+U_r h_{t-1}+b_r),
\]

\[
\widetilde h_t=\tanh(W_n u_t+U_n(r_t\odot h_{t-1})+b_n),\qquad
h_t=(1-z_t)\odot\widetilde h_t+z_t\odot h_{t-1}.
\]

There are three separate `W` matrices of shape `64 x 55`, three separate `U`
matrices of shape `64 x 64`, and one bias per gate. The reset is applied before
the recurrent candidate multiplication. There is no packed alternative,
second bias or alternate update convention.

The 18 edge coefficients, encoder, GRU and actor head are all execution
parameters. There is no roster-specific tensor or learned `N x N` object.

For sender multiplicities `n in {2,3,5,7}` define

\[
v(n)=\frac{2\log n-\log14}{\log(7/2)},\quad
r_{ab}(n)=\beta_{ab0}+\beta_{ab1}v(n),\quad
\omega_{ab}(n)=K^0_{ab}(n)e^{r_{ab}(n)}.
\]

There are two coefficients for each of nine directed public role pairs. With
`q_j` the 32-vector message and `b(j)` its public role,

\[
Q_b=\sum_{j:b(j)=b}q_j,\quad
D_a=\sum_b n_b\omega_{ab}(n_b),\quad
Z_{i}=\frac{\sum_b\omega_{ab}(n_b)Q_b}{D_a+10^{-12}},
\]

where `a` is receiver `i`'s role. Self messages are included. Every coefficient
affects both `Z` and `D` through a live actor input; no dummy or delayed gate is
allowed.

### 4.2 `PHY-TRUST` and `EDGE-FLEX`

Both arms initialize all `beta` values to zero. `PHY-TRUST` projects each
coefficient after every optimizer step into

```text
[-0.15,+0.15],
```

while `EDGE-FLEX` performs the same operation with

```text
[-1.50,+1.50].
```

Every treatment policy is therefore literally available to EDGE with identical
action probabilities on every legal input and registered roster. A live value
`beta=0.60` is an explicit strict-capacity witness unavailable to treatment.
Both begin at the identical complete function `omega=K0`, use the same chart,
derivatives and optimizer geometry in the common interior, and receive the
same physical tables and public inputs.

The arms have identical trainable parameter count, message volume, forward and
backward operators, batch count, gradient calls, recurrent state, legal support
and optimizer opportunity. Each performs three role reductions, nine kernel
evaluations, 18 residual multiply-adds, nine exponentials, one encoder per
agent and one actor call per agent per slot. Deployment is implicit `O(N+9)`
work with `O(N)` messages.

### 4.3 Cut-state convention

For a shadow cut, hold the intact predecision local observations and incoming
recurrent states fixed, replace only the current role-kernel summary, perform
one alternative GRU update, and compare the resulting legal distributions.
Do not propagate the shadow state. A full rotated rollout starts from the same
zero recurrent state and applies the rotated kernel at every slot, allowing
the entire action/state trajectory to change under common potential outcomes.

## 5. One exact prospective training budget

### 5.1 Centralized Monte-Carlo actor-critic

Each learned arm uses the same centralized-training/decentralized-execution
algorithm. The training-only team critic is

```text
input: concatenate the three rolewise means of x_i,t       66
critic: Linear(66,64) -> tanh -> Linear(64,64) -> tanh
        -> Linear(64,1)
```

It sees no future/undetected event or other arm and is absent at execution.
The only episode reward is terminal `J`; discount is `1.0`. For every agent and
slot, the stopped actor advantage is `J-V(g_t)`. Per episode, average the actor
log-probability and entropy first over its agents and 12 slots; average critic
squared error over the 12 team states. Average those episode losses equally
over the batch, so `N=15` does not receive extra weight from more agent rows:

\[
L=-E[\log\pi(a)(J-V)_{stop}]-0.01E[H(\pi)]
  +0.5E[(V-J)^2].
\]

Backpropagate through the full 12-slot recurrent unroll with no truncation.
There is no GAE, importance ratio, replay, auxiliary loss, weight decay,
validation or target network.

The sole budget is

```text
512 training updates
64 fresh complete episodes per update
32 episodes at N=9 and 32 at N=15, alternating in batch order
one full-batch forward/backward gradient call per arm per update
only_evaluable_checkpoint=immediately_after_update_512
```

Use projected Adam jointly over encoder, GRU, actor head, critic and 18 edge
coefficients:

```text
learning_rate=0.0003
beta1=0.9
beta2=0.999
epsilon=1e-8
weight_decay=0
global_gradient_norm_clip=0.5
numeric_training_precision=IEEE-754 float32
```

For each update, compute gradients, clip the common global norm, update Adam
moments and parameters, then project only `beta` into the arm's box; retain the
unprojected Adam moments. There is one such step, no inner epoch or minibatch.
Evaluation and registered statistical reductions use float64.

### 5.2 Initialization and matched optimization

For an affine matrix with fan-in `m`, fan-out `n` and gain `g`, draw entries
i.i.d. from

\[
\operatorname{Uniform}\left[-g\sqrt{6/(m+n)},+g\sqrt{6/(m+n)}\right].
\]

Use `g=1` for both encoder layers, each GRU input matrix, both critic hidden
layers and the critic output; use `g=0.01` for the actor output. For each of the
three recurrent matrices in `z,r,n` order, draw a separate `64 x 64` matrix of
i.i.d. standard normals, compute `M=QR`, and multiply column `k` of `Q` by
`sign(R_kk)`, taking `sign(0)=+1`; the resulting gain-one `Q` is `U_z`, `U_r`
or `U_n`. All biases, all edge coefficients, Adam moments and recurrent initial
states are exactly zero. Within a seed, every common tensor draw is copied bit-
for-bit between arms; each arm then owns separate parameters and optimizer
state. Exact future seed numbers remain unbound.

### 5.3 Arm-independent potential-outcome coupling

A later coordinate binding must address every random variable by stable,
arm-independent semantic identity, including phase, training seed, roster,
update/evaluation episode, basin, event ordinal, slot, public role and hidden
role-local simulator index, sender, receiver and random-variable kind. Event
times, detection coins, packet coins, initialization draws and inverse-CDF
action uniforms exist at those addresses whether or not a divergent policy
uses them. No arm consumes a sequential RNG stream conditionally on prior
actions. Arms share the addressed potential outcomes within the same seed,
roster and episode; different roster sizes use independent world coordinates.
Role-local indices are simulator coordinates only and never policy inputs.

Exact numeric seed labels, counter prefix and artifact/run names remain
definition-external. A later binding may not reuse an SGSP B1/r06 identity or
observed value and must preserve this coupling law.

### 5.4 Competence floor

`UNIFORM-LEGAL` samples uniformly from the same role mask and is evaluated on
the same addressed worlds. It is an untrained task floor, not an algorithmic
comparator. At each seen size `N in {9,15}`, define the seed contrast

\[
e_s(N)=J^{EDGE,int}_s(N)-J^{UNIFORM}_s(N).
\]

`EDGE_TRAIN_COMPETENT` requires the simultaneous lower bound for each `e(N)`
to exceed `0.08` and each two-sided `PHY-TRUST - EDGE-FLEX` training interval
to lie wholly inside `[-0.04,+0.04]`.

## 6. Evaluation, exact estimands and inference

### 6.1 Prospective evaluation population

A later separately authorized empirical object uses 24 independent training-
seed blocks and 256 fresh evaluation episodes per roster and seed. Evaluation
samples from the frozen stochastic policy, including the `0.04` uniform
mixture; it is not greedy. Held-out rosters cannot enter training,
normalization, adaptation, replay, calibration or checkpoint selection.

For arm `A`, condition `c` and basin `z`, define seed-level episode means

\[
J^{A,c}_s(N)=\frac1{256}\sum_e J^{A,c}_{s,e}(N),\qquad
T^{A,c}_{s,z}(N)=\frac1{256}\sum_e D^{A,c}_{s,e,z}/3.
\]

All branch quantities are functions of these 24 seed-level values. Agents,
slots, reports and episodes are not inferential replicates.

### 6.2 Direct, interaction and worst-zone estimands

On intact policies,

\[
d_s(N)=J^{PHY,int}_s(N)-J^{EDGE,int}_s(N),
\]

\[
d_s^{seen}=\tfrac12[d_s(9)+d_s(15)],\qquad
c_s(N)=d_s(N)-d_s^{seen},\quad N\in\{6,21\},
\]

and the worst-zone contrast is

\[
z_s(N)=\min_z T^{PHY,int}_{s,z}(N)-
       \min_z T^{EDGE,int}_{s,z}(N).
\]

Direct practical margin is `delta_R=0.04`, cold-start interaction margin is
`delta_C=0.03`, and worst-zone margin is `delta_Z=0.02`.

### 6.3 One simultaneous family

Use paired seed-level Student-`t` intervals under one fixed Bonferroni family
of exactly 18 quantities:

```text
4  intact direct contrasts d(N), N=9,15,6,21
2  seen-size competence contrasts e(N), N=9,15
2  held-out interactions c(N), N=6,21
2  held-out worst-zone contrasts z(N), N=6,21
6  three cut quantities at each held-out N
2  composite endpoint-interiority/action-support scalars A(N), N=6,21
--
18
```

Every interval is two-sided with per-quantity error `0.05/18`, so the family-
wise error is at most `0.05`. No allocation or endpoint is selected from
results.

### 6.4 Two composite endpoint-interiority and action-support quantities

For any bounded mean `x in [0,1]`, define

\[
h(x;\delta)=\min(x,1-x)-\delta.
\]

Define

```text
TRAINED_ARMS={PHY-TRUST,EDGE-FLEX}.
```

`UNIFORM-LEGAL` appears only in `e_s(9)` and `e_s(15)` and is excluded from
every composite-answerability minimum. For held-out `N`, define six per-seed
support slacks:

\[
A^{dir}_s(N)=\min_{A\in TRAINED\_ARMS}
h(J^{A,int}_s(N);\delta_R),
\]

\[
A^{interaction}_s(N)=
\min_{A\in TRAINED\_ARMS,m\in\{N,9,15\}}
h(J^{A,int}_s(m);\delta_C),
\]

\[
A^{zone}_s(N)=
\min_{A\in TRAINED\_ARMS,z\in\{WEST,EAST\}}
h(T^{A,int}_{s,z}(N);\delta_Z),
\]

\[
A^{cut}_s(N)=\min_{c\in\{int,rot\}}
h(J^{PHY,c}_s(N);\delta_{cutR}),
\]

\[
A^{atten}_s(N)=
\min_{A\in TRAINED\_ARMS,c\in\{int,rot\}}
h(J^{A,c}_s(N);\delta_I).
\]

For an intact treatment policy distribution `p_h` at a registered predecision
history with `m_h` legal actions and floor `ell_h=0.04/m_h`, the maximum TV to
any other distribution with the same legal mask and floor is

\[
TV_{sup}(p_h)=1-(m_h-1)\ell_h-\min_{a\in A_h}p_h(a).
\]

Let

\[
A^{TV}_s(N)=\operatorname{mean}_{e,t,i}TV_{sup}(p_{e,t,i})-\delta_{TV}.
\]

The one registered answerability scalar at that held-out size is

\[
A_s(N)=\min(A^{dir},A^{interaction},A^{zone},A^{cut},A^{atten},A^{TV}).
\]

Its simultaneous lower interval endpoint must exceed zero. This preserves
exactly two answerability quantities while excluding score-endpoint saturation
for every positive efficacy/mechanism gate and proving that the masked legal
simplex permits action-TV beyond the registered margin. It does not claim a
global oracle envelope or that every return contrast is attainable. Once these
checks and EDGE competence pass, failure of the observed arms to meet an
efficacy or cut gate is a target-level failure under branch 4, not saturation
non-identification. Failure of `A(N)` itself is `NONIDENTIFIED`, not
equivalence, inferiority or mechanism absence. Structural validity separately
requires complete atomic evidence, positive basin/event/role support, exact
legal support, fixed masks, no leakage, matching, nesting and finite values.

The remaining fresh margins are

```text
cut treatment return-drop delta_cutR=0.05
cut treatment legal-action-TV delta_TV=0.08
differential advantage-attenuation delta_I=0.03
```

## 7. Action-sensitive symmetric semantic cut

At each held-out size, `SEMANTIC-COLUMN-ROTATE` cyclically rotates the physical
sender columns

```text
WEST-SURVEYOR -> EAST-SURVEYOR -> RIDGE-RELAY -> WEST-SURVEYOR
```

for both learned arms separately, while learned residual coefficient indices,
public counts, sender messages, receiver role, local observations, actor,
recurrent/critic parameters, simulator physics, events, reward, masks and
potential-outcome tapes remain fixed. Balanced roles preserve every receiver-
row coefficient multiset. For EDGE this cut is used only to define differential
attenuation; it is never a replacement comparator.

On intact treatment predecision histories, define legal-action TV on the common
six-action alphabet, with illegal probabilities zero:

\[
V_s(N)=\operatorname{mean}_{e,t,i}
\frac12\sum_{a=1}^{6}|\pi^{PHY,int}_{e,t,i}(a)-
                         \pi^{PHY,shadow-rot}_{e,t,i}(a)|.
\]

From full paired rollouts define arm-specific cut losses

\[
C^A_s(N)=J^{A,int}_s(N)-J^{A,rot}_s(N),
\]

and differential advantage attenuation

\[
I_s(N)=
[J^{PHY,int}_s-J^{EDGE,int}_s]-
[J^{PHY,rot}_s-J^{EDGE,rot}_s]
=C^{PHY}_s(N)-C^{EDGE}_s(N).
\]

The three registered cut quantities at each held-out size are `C_PHY`, `V`
and `I`. `KERNEL_USE_PASSES` requires their simultaneous lower endpoints to
exceed `0.05`, `0.08` and `0.03`, respectively, at both sizes. A summary
change is insufficient. Cut harm cannot rescue a failed intact comparison.

## 8. Result-blind outcome branches

Apply the separate revision-03 decision map in this order:

1. Structural invalidity, incomplete evidence, leakage, mismatched information,
   parameter/work/optimizer opportunity, failed nesting, support or stochastic
   coupling yields no scientific relation.
2. Failed composite answerability at either held-out size or failed
   `EDGE_TRAIN_COMPETENT` at either seen size yields `NONIDENTIFIED`.
3. Select `RETAIN_PHYSICAL_PRIOR_COLDSTART` only when every prior gate passes;
   direct held-out lower bounds exceed `0.04` at both sizes; both interaction
   lower bounds exceed `0.03`; both worst-zone lower bounds exceed `0.02`; and
   all six cut thresholds pass.
4. Every other complete, valid, answerable panel with competent EDGE selects
   `DO_NOT_RETAIN_FIXED_PRIOR_AS_DEFAULT` for this exact task and budget.
   Record every applicable failed-qualification predicate in this fixed order:

   1. `HELDOUT_DIRECT_RETURN_NOT_ESTABLISHED` iff at least one held-out `d(N)`
      lower endpoint is not above `delta_R`;
   2. `COLDSTART_INTERACTION_NOT_ESTABLISHED` iff at least one held-out `c(N)`
      lower endpoint is not above `delta_C`;
   3. `WORST_ZONE_ADVANTAGE_NOT_ESTABLISHED` iff at least one held-out `z(N)`
      lower endpoint is not above `delta_Z`;
   4. `ACTION_SENSITIVE_ATTRIBUTION_NOT_ESTABLISHED` iff at least one
      registered `C_PHY`, `V` or `I` lower endpoint is not above its threshold.

   Then record `PRACTICAL_EQUIVALENCE` only if both held-out `d(N)` intervals
   lie wholly inside `[-delta_R,+delta_R]`, and `EDGE_MATERIALLY_SUPERIOR` only
   if both held-out `d(N)` upper endpoints are below `-delta_R`, in that order.
   An exact interval pattern may be reported numerically, but failure of a
   positive gate alone is not proof of zone imbalance, mixed-sign roster
   effects, or absence of a causal mechanism. No label authorizes a new budget
   or wrong-center rescue.

This is not universal deletion of graph policies or physical priors.

## 9. Strongest alternative

Even a fully qualifying positive cannot distinguish correct semantic knowledge
from the entire package of a narrower projection domain, load normalization,
curvature, regularization and optimizer preconditioning around a physically
reasonable table. Identical initialization, literal nesting, common local
chart, exact optimizer/trainer matching, seen-size competence, cold-start
interaction and differential cut attenuation reduce comparator-handicap
explanations but do not identify kernel truth or faster learning.

The strongest rival is that `PHY-TRUST` is simply the better finite-budget
regularizer on this simulator while `EDGE-FLEX` needs more useful work. That is
still a bounded package-level inductive-bias result, not an asymptotic or
ontological semantic claim.

## 10. Claim ceiling and UAV boundary

A fully qualifying positive supports at most:

> In the exact static two-basin `RIDGEGATE-2Z` toy, one shared recurrent policy
> constrained near a reward-independent terrain/radio role kernel achieved an
> action-sensitive return advantage over a competent, equally initialized and
> strictly containing matched EDGE learner at adaptation-free held-out
> `N={6,21}` after exactly 512 matched updates; the advantage was larger than
> at seen `N={9,15}`, preserved the worse basin, and attenuated more than EDGE
> under the same sender-role semantic cut.

It does not establish a learning curve, faster convergence, asymptotic
superiority, kernel truth, unique physical correctness, another budget or
roster, arbitrary terrain or role mixtures, in-episode churn, mobile zones,
fading robustness, perception validity, flight dynamics, collision safety,
energy feasibility, regulatory compliance, real-radio performance, a second
surface or UAV mission benefit.

The bounded toy-to-UAV mapping is: west/east surveyors generate time-limited
observations; ridge relays allocate half-duplex reception and forwarding; and
fleet-size change alters contention while public role physics remains stable.
A positive justifies only later portfolio consideration of the physical-prior
component, never UAV simulation or production.

## 11. Definition-only authority boundary

Scientific activity begins with the earliest materialization, generation,
inspection, summary or use of a new-task initialization, event, detection,
packet, collision, action uniform, policy output, checkpoint or endpoint.
Static symbolic reasoning and CM read-only feasibility/cost analysis are
preactivity.

Before any empirical construction, this exact revision requires
same-conversation ChatGPT External Pro `CLOSED` and EM intake. Gemini remains
independent, advisory and non-gating. After closure, CM may perform only the
portfolio-authorized static bindability, observability, comparator-feasibility
and prospective-cost review. Neither provider review nor CM static feasibility
authorizes source, build, test, probe, coordinate, rollout, training,
evaluation, compute lease, second surface or UAV action.
