# Commitment-Residual Triggered Options B1 science card

```text
direction=commitment_residual_triggered_options
candidate=CRTO-B1
revision=CRTO-B1-SCIENCE-20260812-04
owner=EM_commitment_residual_triggered_options
scientific_activity_started=false
production_authorized=false
mathematical_closure=required_from_same_direction_chatgpt_external_pro_on_v4
```

## Decision and question

This is a meaning-complete prospective B1 for a direct variable-`k` algorithm.
It asks whether one shared option policy, trained only at `k in {4,8}`, obtains
better held-out-`k=16` and within-episode `4 -> 16` / `16 -> 4` net team utility
or failure robustness than an information-, trainable-parameter-count-,
bottleneck-dimension-, interaction-, optimization-budget-, and work-matched
recurrent option critic because an explicit calibrated post-commitment residual
is a useful finite-data/OOD representation and optimization inductive bias.

The residual is a deterministic transformation of information available to
both learned arms. No outcome can support an information-gain claim. The
strongest alternative is that fixed nonlinear residual preprocessing changes
scaling, effective function class, optimization trajectory, or learned
packet-history co-adaptation, while derangement harms any context-coupled
auxiliary packet and the frozen hazard may realize a different evaluation replan
rate. The registered interventions can establish only a bounded contribution of
the residual-conditioned CRTO path; they do not establish hypothesis-class
equivalence, residual-semantic uniqueness, or full mediation of the
CRTO-versus-FULL package effect.

The science-bearing object is exactly this full composite file at revision
`CRTO-B1-SCIENCE-20260812-04`. It prospectively supersedes inactive revisions
`CRTO-B1-SCIENCE-20260812-01`, `CRTO-B1-SCIENCE-20260812-02`, and
`CRTO-B1-SCIENCE-20260812-03`. The dedicated ChatGPT External Pro conversation
returned `REVISION_REQUIRED` on v2 and `CLOSED` on v3. A subsequent preactivity
CM feasibility question exposed that v3's phrase `switch direction/phase` did
not define the penalized hazard's feature coordinates. Because direction and
phase coding changes the residual-free hazard hypothesis class, actions, and
`Delta_rate` interpretation, v4 prospectively freezes that science-bearing law
before any learned-policy optimizer update or question-relevant output. No v3
implementation guess is part of v4. Any change to the DGP, provider-visible
mathematics, arms, data split, activity law, estimands, margins, inference, or
interpretation branches creates a new complete revision.

Production is withheld. The complete v4 must return to the same dedicated
direction-specific ChatGPT External Pro conversation for literal `CLOSED`,
followed by this EM's intake, before CM may construct or run v4. CM technical
conformance and Root execution release remain separately required; Pro closure
provides neither.

## Cooperative service-relay DGP

### Episode, state, and exogenous tape

- One team has `N=4` homogeneous agents and two lanes, `L` and `R`.
- One episode has `T=256` primitive steps. Locations form the graph
  `L -- BASE -- R`.
- Lane `j` has an integer untracked queue `U_j in [0,64]`, an integer relay
  buffer `B_j in [0,64]`, and primitive-step relay capacity
  `C_j=1+Bernoulli(0.5)`.
- Agent `i` has location `P_i in {L,BASE,R}`, energy `E_i in [0,32]`, current
  option, option age, and the externally supplied current `K`.
- At reset, `(U_L,U_R)=(8,8)`, `(B_L,B_R)=(4,4)`, every energy is `24`, and a
  uniform random permutation assigns locations `(L,R,BASE,BASE)`. A fair coin
  selects the initially hot lane. From the reset observation and initialized
  recurrent history, each policy selects its initial option without a renewal
  charge and with residual contribution fixed to zero: training samples the
  temperature-one categorical logits `q_i(o)` over legal options; locked
  evaluation takes their fixed-option-order argmax. The predictor is anchored
  immediately after that choice to the selected option with option age zero and
  predictor elapsed-horizon clock zero.
- All Bernoulli draws, initial permutations, event assignments, event onsets,
  and provider-independent evaluation branches are fixed in an exogenous
  scenario tape. Paired arms use the same tape. An action does not alter future
  exogenous draws.

Absent a physical demand event, arrivals at step `t` are

```text
A_hot(t)  = 1 + Bernoulli(0.5)
A_cold(t) =     Bernoulli(0.5).
```

The following four event classes are balanced in every evaluation regime.
Their assignment and onset are fixed before the episode and are hidden unless
the cue law below says otherwise.

1. `NONE`: no physical or sensor change.
2. `UNANNOUNCED-DIFFERENTIAL`: for 32 primitive steps, the hot and cold lane
   identities swap. Total expected demand is unchanged; the useful team
   allocation changes.
3. `CUED-DIFFERENTIAL`: the same 32-step physical swap, with the future hot-lane
   identity exposed in the ordinary observation for the eight steps preceding
   onset. It tests whether predictable changes are incorrectly treated as
   surprise.
4. `COMMON-SENSOR`: physical arrivals do not change. For 32 steps, the two
   deployable source-queue telemetry readings each receive an additive `+4`
   sensor offset before normalization and clipping. The physical queues, reward,
   and transition do not use that offset. It is a non-actionable surprise
   control, not a claim that every common-mode disturbance is harmless.

The physical queue `U_j(t)` is never a deployed telemetry field. Define the
deployable queue reading

```text
U_tilde_j(t) = clip(U_j(t) + 4*1[COMMON-SENSOR is active at t], 0, 64).
```

Every actor, predictor, calibrator, packet, and shadow-scoring input uses
`U_tilde_j`; physical `U_j` is reserved for transitions, physical arrivals,
reward, overflow/failure, the evaluation-only terminal potential, and other
nondeployed audit state.

For fixed `K=16`, event onset cycles uniformly through
`{50,66,82,98,146,162,178,194}`. For `4 -> 16`, onset cycles through
`{146,162,178,194}`; for `16 -> 4`, it cycles through `{50,66,82,98}`. Thus
the event and its mechanism audit lie in a `K=16` segment. `NONE` receives a
pseudo-onset from the same schedule. Replanning cost is crossed independently
and equally between `c_low=0.25` and `c_high=4.0` per changed option.
Predictor-data and policy-training episodes, which have fixed `K=4` or `8`,
cycle equally through the full eight-onset schedule and the same event-by-cost
cells. Cell order is fixed by the episode seed before any trajectory is seen.

### Options and primitive transition

Every agent uses the same policy and the option set

```text
TRACK-L, TRACK-R, RELAY-L, RELAY-R, TRANSIT-L, TRANSIT-R, RETURN.
```

Options invoke fixed, identical low-level controllers in every arm. All
decisions at a primitive time are computed from the same pre-action snapshot
and take effect simultaneously.

- `TRACK-j`, when the agent is at lane `j` with at least one energy unit,
  contributes one unit of tracking capacity. If `n^T_j` agents qualify, then
  `x_j=min(U_j,n^T_j)` source units enter `B_j` at the end of the step and the
  participating agents share energy cost `x_j/n^T_j`.
- `RELAY-j`, under the corresponding location and energy condition, contributes
  one relay unit. If `n^R_j` agents qualify, then
  `d_j=min(B_j,C_j,n^R_j)` buffered units are delivered and participants share
  energy cost `d_j/n^R_j`.
- `TRANSIT-j` moves one graph edge toward `j` and costs `0.25` energy when
  `E_i>=0.25`; otherwise it is idle.
- `RETURN` moves one graph edge toward `BASE` at energy cost `0.25`; at `BASE`
  it restores `2` energy, capped at `32`.
- A work option at the wrong lane or without sufficient energy is idle. Relay
  uses the buffer at the start of the step; newly tracked units first become
  available on the following step.
- After service, physical arrivals enter `U`. Queue and buffer excess above
  `64` is dropped and counted as `O_t`. Energy is clipped to `[0,32]` only after
  applying the legal update; no action may create negative energy.

The shared primitive reward is

```text
r_t = d_L + d_R
      - 0.02 * (U_L(t+1)+U_R(t+1)+B_L(t+1)+B_R(t+1))
      - 2.0 * O_t
      - 0.01 * primitive_energy_spent_t
      - renewal_and_replanning_cost_t.
```

The episode score is

```text
J = sum_t r_t / max(1, total_physical_arrivals).
```

The denominator excludes sensor offsets. The task-failure indicator is one if
either delivered physical units are less than `0.80 * total_physical_arrivals`
or any overflow occurs.

### Commitment and externally changing `K`

`K` is an observed maximum nominal commitment in primitive steps. It is never
selected by the policy. A legal review occurs when positive option age is a
multiple of four.

- If `age < K`, `KEEP` is legal. An agent may instead terminate and select a
  different legal option. Termination pays `0.05+c`, resets option age to zero,
  and does not reset the recurrent state.
- If `age >= K`, renewal is forced. The agent selects any legal option, including
  its current option, pays `0.05` plus `c` only if the option changes, resets age
  to zero, and retains recurrent state.
- `TRACK-j` and `RELAY-j` are selectable at lane `j` with sufficient energy;
  `TRANSIT-j` is selectable when not already at `j` with energy at least `0.25`;
  `RETURN` is always selectable. The same mask applies to every arm.
- Simultaneous agents decide from the predecision state; there is no agent-order
  priority.

Training episodes hold `K` fixed at `4` or `8`, balanced exactly. Evaluation
uses fixed `K=8` as an in-support reference, fixed held-out `K=16`, and switches
`4 -> 16` and `16 -> 4` at primitive time `128`. At a switch, the new `K` is
observed before that time's action. Each active option initially retains its
age, and the following order is indivisible:

1. Set the residual contribution `b_i(o)=0` for this switch-time decision; an
   old-anchor residual is neither reused nor shadow scored.
2. If retained age is at least `K_new`, perform forced renewal immediately with
   score `q_i(o)-0.05-c*1[o!=current]`. Otherwise, if retained age is a positive
   multiple of four, perform the ordinary discretionary decision with `KEEP`
   score zero and replacement relative score
   `q_i(o)-q_i(current)-(0.05+c)`. If neither condition holds, retain the option
   without charge. Training/evaluation categorical and tie laws are the ordinary
   laws below.
3. Apply the selected option, charge, and age reset exactly once. Forced renewal
   resets age even when the same option is selected; discretionary `KEEP` and a
   no-review switch retain age.
4. After that action, anchor the predictor to the resulting active option from
   current deployable history. Physical state and policy/predictor recurrent
   states are retained.

Let `tau_pred` be this predictor-anchor time, distinct from the commitment's
absolute option age. Every later residual uses elapsed predictor horizon
`h=t-tau_pred` and `(mu_h,L_h)`, with `h in {4,8,12,16}`. An ordinary
termination or forced renewal likewise anchors the newly selected commitment
after its decision; ordinary `KEEP` does not re-anchor. Thus a `4 -> 16` switch
may retain absolute age while resetting only `h`; a `16 -> 4` switch may force a
new commitment. The switch-time action and cost remain part of return, but no
switch-time residual mechanism score is defined. The `[-8,+8]` primitive-step
switch window is excluded from mechanism selectivity summaries.

## Deployable observation and shared-policy law

At every primitive step, agent `i` observes its location, normalized energy,
current option, absolute age, `age/K`, `K/16`, cost regime, legal mask, visible
cue, and a common broadcast containing normalized deployable queue and physical buffer
telemetry, preceding-four-step deliveries by lane, option-count and
location-count histograms, and time fraction. Under `COMMON-SENSOR`, only the
two `U_tilde` queue fields are offset. There are no agent IDs, event labels,
future quantities, reward labels, counterfactual values, or privileged simulator
states in execution inputs. A shared 64-unit GRU processes this raw history.
A centralized value baseline may see the physical training state, but every
deployed option score, predictor value, and termination decision uses only the
deployable history and common broadcast.

The predictor target for agent `i` is the eight-vector

```text
Y_i = [U_tilde_L/64, U_tilde_R/64, B_L/64, B_R/64,
       delivered_L_over_previous_4/8, delivered_R_over_previous_4/8,
       E_i/32, graph_distance_to_current_option_target/2].
```

The common broadcast and current local observation contain every realized
component of `Y_i`. Neither `Y_i` nor any deployed packet contains physical
`U_L,U_R` during `COMMON-SENSOR`.

## Frozen predictor, calibration, and residual

For every independent algorithm seed, an arm-independent scripted data set has
256 complete episodes: 128 at `K=4` and 128 at `K=8`, balanced over event and
cost cells. At reset the script samples each agent's initial option uniformly
from its legal options without charge and then anchors the predictor. At each
discretionary review the script terminates with probability `0.25`; at every
renewal or termination it samples uniformly from the legal options, excluding
the current option after termination. Episodes are assigned
before generation to predictor-fit (128), calibration (64), and development
(64) sets, stratified by `K`, event, and cost. No transition crosses a split.

A shared recurrent four-step transition cell `F_psi` is unrolled once for
elapsed predictor horizon 4, twice for horizon 8, three times for horizon 12,
and four times for horizon 16. It takes
only the commitment-origin deployable history, current option, `K/16`, and
normalized requested forecast age, and emits an eight-dimensional Gaussian
mean `mu_h` and lower-triangular Cholesky factor `L_h` with positive diagonal.

The predictor has one deployable observation encoder GRU of hidden width `64`
and one four-step transition `GRUCell` of hidden width `64`. Both use standard
sigmoid reset/update gates and a `tanh` candidate. The observation encoder
processes the same normalized deployable primitive observation vector defined
above from episode start through the commitment origin. The transition cell
receives at every unroll the concatenation of the frozen origin option one-hot,
`K/16`, and that unroll's forecast age `4*l/16` for `l in {1,2,3,4}`; its
initial hidden state is the observation-encoder hidden state. A
`64 -> 64 -> 44` readout with `tanh` hidden activation emits eight
unconstrained means and 36 lower-triangular
parameters. Off-diagonal entries are unconstrained. Diagonal entries are
`softplus(d)+1e-3`, so every solve and Gaussian likelihood uses
`Sigma=L L^T` with a literal Cholesky diagonal lower bound `1e-3` and no
additional adaptive jitter.

Using a PCG64 initialization stream seeded by `400000+algorithm_seed`, all
predictor affine input weights use Xavier-uniform initialization with `tanh`
gain, recurrent hidden-to-hidden matrices use orthogonal initialization, and
every bias is zero. It is fitted by mean Gaussian negative log likelihood
on the 128 predictor-fit episodes, including the age-4 target at both training
`K` values and the age-8 target at `K=8`. Training uses Adam with learning rate
`1e-3`, betas `(0.9,0.999)`, epsilon `1e-8`, weight decay `1e-5`, batches of
256 forecast examples. Examples are first ordered by
`(episode index,commitment time,target age,environment slot)`, then taken
cyclically from one PCG64 permutation seeded by `500000+algorithm_seed`,
wrapping without reshuffle, with global gradient-norm
clipping at `1.0`, and exactly 400 optimizer updates. The final
update is used; there is no early stop, validation selection, or arm-specific
fit. The exact same fitted predictor is copied into both learned arms and
frozen before any policy training. Policy, value, and termination gradients
never enter it.

A forecast example anchored at `tau_pred` for horizon `h` exists only when the
same anchored option commitment remains continuously active through the
predecision observation at `tau_pred+h`. A discretionary termination or forced
renewal at an earlier review censors every later target from that anchor; the
later commitment receives its own anchor and examples. A target observed at the
same boundary at which the originating commitment is subsequently terminated or
renewed remains eligible because observation precedes action. Ordinary `KEEP`
does not censor or re-anchor. A switch-created anchor is created only after the
switch-time decision above and follows the identical continuous-commitment rule;
another re-anchor before `tau_pred+h` censors that target. Predictor-fit,
calibration, representability-probe, and evaluation-calibration populations all
use this one eligibility law, and missing horizons are never reassigned to a
replacement commitment or evaluated against its later state.

At an initial selection, ordinary new commitment, or post-decision `K`-switch
anchor, forecasts are issued before the target telemetry. At a later eligible
legal review, using only telemetry already observed and the elapsed-horizon
forecast `(mu_h,L_h)`,

```text
e_i = solve(L_h, Y_i - mu_h).
```

For coordinate `d`, the calibration-set empirical CDF is
`F_d(x)=(count(e_d<x)+0.5*count(e_d=x)+0.5)/(n_d+1)`. It is pooled across the
two training `K` values and has no `K`-specific table or embedding. Define

```text
r_i[d] = clip(e_i[d], -6, 6)
p_i[d] = 2*F_d(e_i[d])-1
a_i[d] = max(0, s[d]*e_i[d]),
s = [+1,+1,+1,+1,-1,-1,-1,+1].
```

The explicit residual packet is `[r_i,p_i,a_i,zeros(28)]`, dimension 52. The
raw forecast packet is `[Y_i,mu_h,vech(L_h)]`, also dimension 52. Both packets,
and the full four-agent packet tensor, are computed in every arm so that fixed
preprocessing work is equal. Held-out-`K` coverage, PIT/rank behavior, scale,
and saturation are test outcomes, never tuning inputs or assumed guarantees.

## Learned arms and exact mechanism controls

### `CRTO`

At a legal discretionary review, a shared deployable option-value head produces
`q_i(o)` from raw recurrent history. It excludes the immediate renewal/replan
cost. The explicit residual packet passes through a `52 -> 64 -> 32` adapter.
For each different legal replacement `o`, the categorical logit relative to
`KEEP` is

```text
m_i(o) = q_i(o)-q_i(current)-(0.05+c)+b_i(o; residual_adapter).
```

`KEEP` has relative logit zero. Training samples from the resulting categorical
distribution at temperature one. Locked evaluation chooses `KEEP` when every
`m_i(o)<=0`; otherwise it chooses the unique maximum, breaking numerical ties
by the fixed option order printed above. Forced renewals use the same `q+b`
replacement scores: option `o` has score
`q_i(o)-0.05-c*1[o!=current]+b_i(o)`. They allow the current option and choose
categorically in training or by the same fixed-order argmax in evaluation.
The adapter output and a learned 32-dimensional option embedding have an inner
product plus one shared scalar intercept to define `b_i(o)`; this head is
structurally identical in both learned arms.

In both learned arms, the adapter is exactly
`Linear(52,64) -> tanh -> Linear(64,32) -> tanh`. Both affine layers and the
32-dimensional option-embedding table use Xavier-uniform initialization with
`tanh` gain; affine biases and the shared scalar intercept are zero. One PCG64
stream seeded by `800000+algorithm_seed` initializes the learned components.
Paired arms receive byte-identical initial tensors for every corresponding
learned component and differ only in whether the adapter input is the explicit residual
packet or raw forecast packet. No normalization, dropout, skip connection, or
other raw/residual bypass is present.

### `FULL-HISTORY-AUX-TERM`

This is the strongest matched baseline. It has the identical raw history,
forecast `Y,mu,L`, common frozen predictor, action set, legality, cost, recurrent
backbone, option-value head, adapter dimensions, policy/value losses, parameter
count, forward/backward work, samples, updates, optimizer, initialization rule,
exploration, and checkpoint rule. Its 52-dimensional adapter input is the raw
forecast packet rather than the explicitly whitened/ranked residual packet.
The explicit packet is a deterministic function of information in its raw packet
and frozen calibration table, but equal adapter dimensions and the probe below do
not prove equality of the two nonlinear hypothesis classes. The comparator is
therefore information-, trainable-parameter-count-, bottleneck-dimension-,
optimization-budget-, work-, and action-matched, not unqualifiedly
capacity-matched. Any CRTO advantage is a finite-budget representation/
optimization inductive-bias package result, not additional observability or
hypothesis-class superiority.

### Same-checkpoint cuts

These do not train new policies.

- `DERANGED-RESIDUAL-CRTO`: at exactly one frozen audit boundary per scored
  episode, select the first legally reviewing agent in a fixed environment-only
  canonical order that is never an actor input. Replace that agent's complete
  52-coordinate residual packet with the matched row from another episode's
  complete four-agent tensor under a uniformly sampled fixed-point-free
  permutation.
  Matching is exact on target-agent current option (skill), current `K`, option
  age, complete legal-mask bit pattern, exogenous predecision event class and
  phase, visible-cue state, and cost regime. Predictor uncertainty, team option
  histogram, location/role counts, and residual norm are balance diagnostics,
  never post hoc matching variables. Donor identity, future outcome, chosen
  action, and postdecision descendants are forbidden. The donor tensor moves
  as one object and its matched row is routed without coordinate shuffling;
  other agents keep their aligned packets and precomputed simultaneous actions.
  The permutation batch is the interference cluster.
  A cell with fewer than eight boundary states is unsupported and contributes
  no alignment estimand; matching is never relaxed after results are visible.
- `Q-ONLY-CRTO`: use the same checkpoint and set the additive `b_i` contribution
  to exactly zero at every discretionary review and forced renewal of a complete
  evaluation rollout. Raw history, `q`, actions, and costs remain unchanged.
- `RATE-MATCHED-HAZARD-CRTO`: on development trajectories only, fit a logistic
  gate from current option, `K`, age, legal mask, visible cue, and cost to the
  CRTO termination decision, and adjust its intercept within each supported
  `(regime,K,age,cost)` cell to match CRTO's development termination rate. Its
  exact fit and support law are frozen below. Freeze it before evaluation and
  apply it at every discretionary review of a complete evaluation rollout.
  When it terminates, use CRTO's unchanged replacement scores. It receives no
  residual, hidden event identity, or test outcome.
- `FORCED-RENEWAL-ONLY`: use the CRTO checkpoint but forbid discretionary
  termination throughout a complete evaluation rollout; forced renewal remains
  unchanged. This is an exposure anchor, not the matched learned comparator.

`Q-ONLY-CRTO`, `RATE-MATCHED-HAZARD-CRTO`, and
`FORCED-RENEWAL-ONLY` each run as a complete rollout on all four regimes:
diagnostic fixed `K=8`, held-out fixed `K=16`, `4 -> 16`, and `16 -> 4`.
Each uses exactly the same 64 paired evaluation tapes per seed/regime as the
main CRTO/FULL comparison. The three cuts do not create checkpoints or policy
updates.

For each training seed, the rate-control fit uses a separate, untouched-by-
training development panel of 64 locked-CRTO episodes in each of those four
regimes, with eight episodes in every event-by-cost cell and tapes disjoint from
predictor data, policy training, scored evaluation, and donor-only panels. At
every legal discretionary review, its binary label is CRTO's locked
terminate-versus-KEEP decision. Its feature vector is an intercept, current
option one-hot, `K/16`, `age/16`, `age/K`, complete legal-mask bits, visible cue
one-hot, cost divided by `4`, and the exact regime/direction/phase coordinates
below; it has no residual, telemetry value, hidden event label, future value, or
outcome.

The regime/direction/phase block is exactly 14 binary coordinates in this order:

```text
regime = one_hot(current complete-rollout regime;
                 [K8_FIXED,K16_FIXED,SWITCH_4_TO_16,SWITCH_16_TO_4])

direction = one_hot(switch direction;
                    [NO_SWITCH,FOUR_TO_SIXTEEN,SIXTEEN_TO_FOUR])

phase = one_hot(boundary-relative switch phase;
                [FIXED,PRE_9PLUS,PRE_1_TO_8,AT_SWITCH,
                 POST_1_TO_8,POST_9PLUS,FAR_POST])
```

`regime` is the complete episode regime, not current `K`. For both fixed regimes,
`direction=NO_SWITCH` and `phase=FIXED` at every legal discretionary review. For
either switch regime let `delta=t-128`, where `t` is the integer primitive-time
index of the predecision legal review and the externally changed `K` becomes
observable at `t=128`. Assign exactly one phase coordinate by:

```text
PRE_9PLUS = 1  iff delta <= -9
PRE_1_TO_8 = 1 iff -8 <= delta <= -1
AT_SWITCH = 1  iff delta == 0
POST_1_TO_8= 1 iff 1 <= delta <= 8
POST_9PLUS = 1 iff 9 <= delta <= 64
FAR_POST   = 1 iff delta >= 65.
```

Every episode is 256 steps, so the displayed bins cover all switch-regime
reviews. The switch instant contributes a hazard-fit row only if the v4 action
law makes that boundary a legal discretionary review with a binary
terminate-versus-KEEP label. An immediately forced renewal, a no-review instant,
or any boundary without legal `KEEP` is excluded from the hazard fit and from
hazard cell-support counts; it is still resolved by the ordinary v4 switch law.
At `t=128` the residual contribution is zero by construction, so an included
discretionary row's label is the locked q-only CRTO decision.

All 14 coordinates are literal uncentered `0/1` indicators. They are never
reference-dropped, centered, standardized, collapsed, or replaced by ordinal
scalars. Only `K/16`, `age/16`, `age/K`, and `cost/4` are continuous; center and
unit-scale those four using the complete four-regime hazard-development panel,
with a zero development standard deviation replaced by scale one. Current-option,
legal-mask, cue, regime, direction, and phase indicators remain literal `0/1`.
The base logistic is additive in exactly the printed coordinates: there are no
products, splines, polynomials, learned embeddings, direction-by-phase terms,
regime-by-phase terms, or other interaction features. The single intercept is
unpenalized; every coefficient on a continuous or binary feature is a
non-intercept coefficient subject to the same `1e-3/2` L2 penalty below. The
collinear full one-hot blocks intentionally remain as printed; the strictly
convex L2-penalized slope objective with an unpenalized intercept determines the
minimum-norm fitted slopes under the registered deterministic optimizer.

The base logistic coefficients minimize mean binary cross-entropy plus
`1e-3/2` times the squared non-intercept coefficient norm. Deterministic L-BFGS
uses zero initialization, memory `20`, at most 500 iterations, and stops only
when the infinity norm of the penalized gradient is at most `1e-8`; reaching
the iteration cap without that condition makes the rate control unavailable.
For every `(regime,K,age,cost)` cell with at least 32 reviews, hold base slopes
fixed and solve a cell intercept offset by bisection so the mean fitted
probability equals the empirical CRTO termination rate within `1e-10`. If that
rate is exactly zero or one, the cell uses the corresponding constant
probability exactly. For a rate strictly between zero and one, bisection starts
with offset bracket `[-40,40]`, takes at most 200 iterations, and fails the
control if the bracket does not contain the root or the tolerance is not met.
Cells with fewer than 32 reviews are unsupported and contribute no rate-control
estimand; matching is never relaxed. Their required complete rollout uses the
unshifted base-logistic probability and is descriptive only. Evaluation draws
its terminate decision from the applicable frozen probability using one
preassigned uniform variate per legal review. Rate-control RNG is isolated from
physical, option-selection, and other-arm tapes.

Development matching alone is not called evaluation rate matching. On each
method's own complete scored rollout define, for method `m`, seed `s`, regime
`r`, event `e`, and cost `c`,

```text
rho_m,s,r,e,c = discretionary changed-option terminations /
                legal discretionary reviews
lambda_m,s,r,e,c = discretionary changed-option terminations /
                   (256 * number of episodes in that cell).
```

The same quantities with `e,c` omitted pool all 64 episodes in a regime before
division. A zero legal-review denominator makes `Delta_rate` unavailable. Define
each balance statistic as the unweighted mean across the eight seeds of the
absolute CRTO-minus-hazard difference. Before `Delta_rate` can be interpreted,
both methods' realized own-trajectory rollouts must satisfy, in each of the
three scored target regimes, `B_rho<=0.02` and `B_lambda<=0.005` overall and
`B_rho<=0.05` and `B_lambda<=0.01` separately in every one of the eight
event-by-cost cells. Counts and signed differences are reported as well. Failure
withholds `Delta_rate` and every claim that this cut excludes evaluation replan
exposure; it does not invalidate the already frozen whole-algorithm contrast.

The residual reassignment uses the following deterministic uniform-derangement
algorithm separately within each training seed. First, scan every scored CRTO
episode and donor-only episode and create one record for its first eligible
boundary; an episode without such a boundary creates no record but remains in
the registered boundary-availability denominator.
`phase=floor((boundary_time-event_or_pseudo_onset)/4)`. Canonically sort records
by `(regime order K8,K16,4to16,16to4; panel order scored,donor; episode index;
target-agent environment slot)` and partition them by the exact frozen match
key `(current option,current K,age,legal-mask bits,event class,phase,visible
cue,cost)`. The environment slot is never an actor input.

Process cells in lexicographic key order, with `g` equal to the cell's zero-based
index in that full ordered list before support filtering. Mark a cell with fewer
than eight records unsupported before creating any random assignment; never
merge, relax, or borrow from it. For supported cell ordinal `g` with `n`
records, initialize
PCG64 with integer seed `7000003 + 1009*algorithm_seed + g`. Draw a uniform
Fisher-Yates permutation of `0..n-1`; reject the whole permutation if any
`pi[j]=j`, and use the first fixed-point-free draw. Stop after 10,000 rejected
draws and return a technical incomplete result if none exists. Conditioning a
uniform permutation on no fixed points gives a uniform derangement. The map is
a bijection, so every record donates once and receives once, always from a
different episode; only scored recipients enter `Delta_align`. Assignment is
persisted before any deranged branch return is computed. The ordered handling
is therefore: boundary eligibility, canonical partition, unsupported-cell
marking, scored-recipient support fraction, fixed permutation, branch replay,
then balance/AUC diagnostics. If fewer than 80% of eligible scored recipients
remain after unsupported cells are removed, the alignment mechanism is
unavailable and no later diagnostic may restore it.

For the derangement audit, the boundary is the first CRTO-legal discretionary
review in `[event_onset+4,event_onset+20]`, outside the switch exclusion window,
at which the canonically first reviewing agent has at least one different legal
replacement; `NONE` uses its pseudo-onset. Selection uses no residual, action,
or outcome.
The aligned and deranged branches clone the entire predecision simulator and
future tape, differ only in that target agent's one residual packet, hold other
agents' simultaneous actions fixed, and return to aligned residuals afterward.
At the same state, evaluation also enumerates the target agent's `KEEP` and
every legal replacement for 16 primitive steps under common future noise,
holding other simultaneous actions at their aligned choices and then using the
frozen CRTO continuation policy from the next primitive step onward. Let the
fixed audit action order be `KEEP` followed by the printed option order, let
`A_t={KEEP}` union every different legal replacement, and define

```text
gamma_audit = 0.99
D_audit     = max(1, total physical arrivals over the complete episode tape)
Phi(s)      = -0.02*(U_L+U_R+B_L+B_R)
              -0.01*sum_i(32-E_i)

G16(a;s_t) = (sum_{h=0}^{15} gamma_audit^h * r_{t+h}^{(a)}
               + gamma_audit^16 * Phi(s_{t+16}^{(a)})) / D_audit

A16_replan(s_t) = max_{o in A_t minus {KEEP}} G16(o;s_t)
                  - G16(KEEP;s_t)

Regret16(pi,s_t) = max_{a in A_t} G16(a;s_t)
                   - G16(a_pi;s_t).
```

`r_t^(a)` includes the enumerated action's immediate `0.05+c` replacement
charge exactly once; `KEEP` has no immediate charge, and every later realized
charge is included through the frozen continuation rewards. The physical
terminal potential is discounted as shown. A numerical maximizing tie uses the
fixed audit action order. `a_pi` is the locked aligned or deranged action at
that same state; regret is zero for any tied maximizer. `A16_replan<=0` defines
a negative/nonpositive-advantage state, and `A16_replan>=0.02` defines recovery
headroom. These audit quantities are evaluation-only and never enter any actor,
predictor, checkpoint, donor assignment, or selection rule.

## Training, counts, and resource envelope

Independent algorithm seeds are

```text
2101, 2111, 2129, 2141, 2161, 2179, 2203, 2221.
```

For each seed, `CRTO` and `FULL-HISTORY-AUX-TERM` each train for exactly 1,024
complete 256-step episodes, balanced between fixed `K=4` and `K=8` and across
event/cost cells. Both use the last update; there is no best-test checkpoint or
arm-specific hyperparameter search. The shared actor uses recurrent PPO with
`gamma=0.99`, `GAE lambda=0.95`, clip `0.2`, Adam learning rate `3e-4`, 32
episodes per update, four shuffled epochs, value coefficient `0.5`, entropy
coefficient `0.01`, and global gradient-norm clipping at `0.5`. Central value
learning uses the summed team reward; option decisions receive the primitive
return accumulated until their next review. All losses, optimizer steps, and
RNG-stream assignment are identical across the two learned arms.

At a primitive time with one or more reviewing agents, the actor likelihood is
the product of their shared categorical probabilities computed from the common
predecision snapshot; PPO clips that one joint ratio. The centralized value
head supplies primitive-time GAE. The deployable `q_i` head additionally uses
an on-policy semi-Markov squared-TD loss with coefficient `0.5`: for the option
actually selected by agent `i`, its target is the discounted team reward until
that agent's next legal review plus the bootstrapped centralized value. The
agent's own immediate renewal/replanning charge is added back once in this TD
target, so `q_i` excludes that current charge while retaining all later realized
costs; the gate then subtracts the current charge exactly once. Targets are
stop-gradient. Unchosen-option values are learned only through the registered
on-policy categorical exploration—there is no privileged counterfactual target
or evaluation-audit leakage. PPO minibatches contain eight complete episodes;
advantages are standardized within the 32-episode update batch.

Untouched evaluation has 64 paired scenario episodes per seed in each of
`K=8`, `K=16`, `4 -> 16`, and `16 -> 4`, with 8 episodes in every
event-by-cost cell. No evaluator, predictor, calibrator, checkpoint, threshold,
or donor stratum is tuned on these episodes. Team episode is the interference
unit; training seed is the outer algorithm-replication unit.

For each seed and each of all four regimes, including diagnostic `K=8`, 256
additional donor-only episodes use the frozen CRTO checkpoint and independent
tapes, balanced over the same event/cost/onset cells. Their returns never enter
an algorithm or mechanism estimand. Their eligible predecision residual tensors
join the scored boundaries in the fixed derangement permutation defined above.
This donor panel may improve exact-stratum support but does not permit matching
relaxation or test-driven tuning.

The exact environment-step ledger is frozen as follows; no category may borrow
from another:

| Category | Exact formula | Maximum primitive team steps |
|---|---:|---:|
| arm-independent predictor data | `8 seeds * 256 episodes * 256` | 524,288 |
| learned-arm training | `8 * 2 arms * 1,024 * 256` | 4,194,304 |
| hazard-development rollouts | `8 * 4 regimes * 64 * 256` | 524,288 |
| main CRTO/FULL evaluation | `8 * 2 arms * 4 * 64 * 256` | 1,048,576 |
| three complete-rollout cuts | `8 * 3 cuts * 4 * 64 * 256` | 1,572,864 |
| donor-only panel | `8 * 4 * 256 * 256` | 2,097,152 |
| one-packet deranged replays | `8 * 4 * 64 * 256` | 524,288 |
| audit action enumeration | `8 * 4 * 64 * at most 7 actions * 16` | 229,376 |
| **registered maximum** | | **10,715,136** |

The implementation records actual completed steps in every row; illegal audit
actions consume zero steps and cannot be replaced by extra episodes. Predictor
optimization, decodability-probe optimization, logistic fitting, and statistics
consume no environment steps and are reported separately. The complete B1
ceiling is one CPU, no GPU, 2 GiB resident memory, 120 minutes wall time, and
the registered 10,715,136-step maximum. Crossing any category or resource
ceiling returns an incomplete engineering result to CM; it is not a negative
scientific observation and does not authorize changing this revision.

Scientific activity begins at the first optimizer update of either learned arm
using a trajectory generated under this revision. Before that instant, an
unchanged-science engineering repair remains CM-owned. After it, no
science-bearing field above may be changed or retrofitted.

## Activity and validity requirements

### Frozen claim-bearing diagnostic definitions

The donor/recipient balance classifier uses exactly one pair for every supported
scored recipient: the recipient boundary row has label zero and its assigned
donor's original boundary row has label one. Its continuous features are
`[||r||_2,||p||_2,||a||_2]`, the eight marginal
`0.5*log(diag(L L^T))` values, `2*sum_d log(L_dd)`, the seven joint-option-count
fractions, and the three location-count fractions. Its categorical/frozen
features are current-option one-hot, `K/16`, `age/16`, the seven option-legality
bits, event-class one-hot, `phase/5`, visible-cue state one-hot over
`{none,L,R}`, `cost/4`, and regime one-hot. No action, outcome, donor identity,
future quantity, or postdecision descendant is a feature.

Use eight-fold leave-one-algorithm-seed-out cross-validation. In each fold,
center and unit-scale continuous features on the seven training seeds (a zero
training standard deviation uses scale one), leave one-hots unchanged, and fit
an unpenalized-intercept logistic regression from zero initialization by the
same deterministic L-BFGS contract as the hazard fit: L2 penalty `1e-3/2` on
non-intercept coefficients, memory 20, at most 500 iterations, and terminal
penalized-gradient infinity norm at most `1e-8`. Score only the held-out seed.
Nonconvergence makes the balance diagnostic unavailable. Within each regime,
pool the eight held-out-fold predictions only after all folds finish and compute
Mann-Whitney AUC, assigning probability `0.5` to every positive-negative score
tie. Each of the three target regimes must have AUC at most `0.60`; fixed `K=8`
is reported diagnostically. This is a validity diagnostic under the registered
feature family, not proof of equality of donor and recipient distributions.

Calibration uses only eligible forecast targets on aligned CRTO's untouched
fixed-`K=16` main-evaluation trajectories. For seed `s` and elapsed horizon
`h in {4,8,12,16}`, define `q=||solve(L_h,Y-mu_h)||_2^2`; 90% ellipsoid coverage
is the fraction satisfying `q<=13.3615661365`, the 0.90 quantile of chi-square
with eight degrees of freedom. Each seed must supply at least 32 eligible targets
at each `h`. First average examples within a seed, then average the eight seed
fractions equally; coverage at every `h` must lie in `[0.80,0.98]`.

For PIT, use the frozen training-calibration empirical CDF `F_d` already defined,
set `u_d=F_d(e_d)`, and bin by `min(9,floor(10*u_d))`, with the last bin including
the right endpoint. For every `(h,d)`, average the ten within-seed bin-frequency
vectors equally and define
`PIT_ECE_h,d=0.5*sum_{b=0}^9 |frequency_h,d,b-0.1|`. The maximum over the eight
coordinates must be at most `0.10` at every `h`. The clip-saturation rate is the
seed-balanced fraction of the eight whitened coordinates with `|e_d|>=6`; it
must be below `0.05` at every `h`. The same statistics are reported separately
for each switch regime and horizon but are not pooled into, nor substituted for,
the fixed-`K=16` gate.

The adverse-residual scalar at an audit state is
`S_adv=(1/8)*sum_d a_i[d]`. The trend population is every eligible aligned-CRTO
audit state in `UNANNOUNCED-DIFFERENTIAL`, low-cost cells across the three target
regimes, whether or not its derangement cell is supported. Within each seed,
every target regime must contribute at least one state and the union must contain
at least five states; otherwise the trend condition is unavailable. Within each seed,
sort states by `(S_adv, regime order K16,4to16,16to4, episode index)` and assign
rank `j` among `n_s` states to quintile
`1+floor(5*(j-1)/n_s)`; the canonical keys break exact-score ties. Compute each
seed/quintile mean `A16_replan`, then average those means equally across seeds.
All five aggregate means must be nondecreasing. The one-sided trend statistic is
`T=(1/8)*sum_s sum_{q=1}^5 (q-3)*mean_s,q(A16_replan)`.
Generate exactly 100,000 Monte Carlo null replicates from one PCG64 stream seeded
`9000001`, independently permuting `A16_replan` among fixed states within every
`(seed,regime)` block in canonical state order. The plus-one p-value is
`(1+count[T_perm>=T_observed])/100001` and must be at most `0.05`. This is a
registered association diagnostic, not design-exact causal inference.

The shortcut contrast shadow-scores both frozen learned checkpoints on the same
aligned-CRTO audit histories. From episode reset through the audit predecision
state, replay the identical registered deployable observation/current-option
sequence through each checkpoint's own recurrent backbone; neither checkpoint
acts during replay. At the boundary, compute its own packet adapter and
temperature-one categorical termination mass

```text
P_term = sum_o exp(m_i(o)) / (1 + sum_o exp(m_i(o))),
```

where the sum is over different legal replacements and the denominator's one is
`KEEP`. Thus the contrast is a score difference on identical histories, not a
comparison of occupancy-confounded own-policy trajectories or locked 0/1
actions. Define three prespecified populations: `COMMON-SENSOR` at either cost;
`CUED-DIFFERENTIAL` at either cost; and `c_high` states with
`A16_replan<=0` across all event classes. Within a seed, first average
`P_term_CRTO-P_term_FULL` inside each target regime and then average the three
regimes equally. Every population must be nonempty in every seed. Its one-sided
95% seed-level Student-t upper bound must be at most `0.05` for the shortcut
condition to pass.

A conclusion-bearing B1 requires all eight paired training seeds and all frozen
evaluation cells, finite returns, identical scenario counts, exact action/cost
parity, and no test leakage. In addition:

- before learned-policy activity, a separate scripted-support decodability probe fits
  `Linear(52,64) -> tanh -> Linear(64,32) -> tanh -> Linear(32,24)` on raw
  `[Y,mu,vech(L)]` packets from the predictor-fit plus calibration episodes to
  reconstruct the first 24 explicit coordinates `[r,p,a]`. Its first two layers
  exactly duplicate the learned FULL adapter architecture. All weights use
  Xavier-uniform initialization with `tanh` gain and all biases are zero. Fit
  one seed-specific probe; a PCG64 stream seeded by
  `610000+algorithm_seed` supplies its initialization. Training uses Adam with
  learning rate `1e-3`, betas `(0.9,0.999)`, epsilon `1e-8`, no weight decay,
  and batch size 256. Probe examples are
  canonically ordered as the predictor examples; one PCG64 example permutation
  seeded by `600000+algorithm_seed` is repeated cyclically without
  reshuffle, global gradient clipping at `1.0`, and exactly 1,000 updates;
  use the final update without selection. On the untouched 64-episode scripted
  development split, normalized MSE is the mean over coordinates of
  `MSE_d/(Var_fit(target_d)+1e-8)`, and coordinate-sign accuracy is computed
  only where `abs(target_d)>=0.05`. Normalized MSE must be at most `0.01` and
  sign accuracy at least `0.95` for every seed. Probe parameters never enter a
  policy. Passing establishes approximate residual decodability on only the
  registered scripted development support; it does not establish that the
  learned FULL adapter realizes CRTO's downstream composite through the same
  bottleneck or that the two hypothesis classes agree off support. Failure means
  the proposed raw-packet baseline lacks even this registered decodability
  property and returns the design to this EM before any learned-policy optimizer
  update;

- every target regime has at least 512 legal discretionary CRTO reviews pooled
  across seeds, and both `KEEP` and a changed option each occur in at least 10%
  of those reviews;
- at least 48 of 64 episodes per seed and target regime supply the prespecified
  audit boundary;
- every reported derangement cell has at least eight members; at least 80% of
  otherwise eligible audit boundaries remain supported;
- L-BFGS converges and every `(regime,K,age,cost)` cell encountered at a legal
  review in each of the three scored target regimes has at least 32 matching
  hazard-development reviews; otherwise its complete hazard rollout is
  descriptive and `Delta_rate` is unavailable for mechanism attribution;
- every overall and event-by-cost own-trajectory scored-evaluation rate-balance
  statistic satisfies the exact `B_rho,B_lambda` margins above; otherwise
  `Delta_rate` and the evaluation-rate explanation are unavailable;
- the aligned-versus-deranged decision-disagreement fraction has a seed-level
  95% lower confidence bound above `0.05`;
- the exact leave-one-seed-out donor/recipient classifier converges and has AUC
  at most `0.60` in every target regime;
- every fixed-`K=16` elapsed-horizon ellipsoid-coverage, PIT-ECE, and saturation
  gate defined above passes;
- within every seed, at least 20% of its audited legal states have
  `A16_replan>=0.02`, so the toy contains recoverable termination headroom.

Failure of action support, the derangement first stage, donor support,
rate-control convergence/support, or calibration withholds the
residual-mechanism conclusion. A technically valid
whole-algorithm CRTO-versus-FULL total effect may still be reported at the
package ceiling, but it cannot be called a calibrated-residual mechanism.
Failure of recovery headroom says this exact B1 surface cannot test the package;
it is not evidence that earlier termination is useless elsewhere.

## Estimands and inference

For each seed and regime, average paired scenario differences before any
across-seed inference. Evaluation episodes are nested observations and never
replace training seeds. Report all eight seed effects.

Every decision-bearing Student-t bound is explicitly model-based. For any
registered contrast, let `d_s` be seed `s`'s mean paired episode effect after the
stated equal-regime averaging. The inferential model is
`d_s iid Normal(theta,sigma^2)` across the eight independently initialized
algorithm seeds. With sample mean `d_bar`, sample standard deviation `s_d`, and
seven degrees of freedom, a one-sided `(1-alpha)` lower bound is
`d_bar-t_(1-alpha,7)*s_d/sqrt(8)` and the upper bound changes the minus to plus;
if `s_d=0`, both equal `d_bar`. All familywise-error statements below are nominal
and conditional on this independent-Gaussian seed-effect model; they are not
distribution-free finite-sample guarantees. No seed-sign randomization p-value
is decision-bearing or reported as design-exact.

Primary target regimes are equally weighted across fixed `K=16`, `4 -> 16`,
and `16 -> 4`:

```text
Delta_J = mean_r E[J_CRTO-J_FULL]
Delta_F = mean_r E[failure_CRTO-failure_FULL]
```

The in-support `K=8` panel is diagnostic. A direct variable-`k` performance
result requires the one-sided 97.5% seed-level t lower bound for `Delta_J` to
exceed `0.02`. A robustness result may instead require the one-sided 97.5%
upper bound for `Delta_F` to be below `-0.05` and the 95% lower bound for
`Delta_J` to exceed `-0.01`. These two Bonferroni-separated routes control the
familywise primary error. In either route, simultaneous Bonferroni
`100*(1-0.05/6)=99.1666...%` one-sided bounds must exclude worse than `-0.02`
utility and `+0.05` failure probability for the six metric-by-target-regime
nonharm conditions. Seed-sign randomization is not used for a conclusion.

Secondary mechanism estimands use the same CRTO checkpoint. Complete-rollout
cuts use paired scenario tapes; boundary interventions and regret use the common
cloned future tape defined above:

```text
Delta_align = E[J_aligned-J_deranged]
Delta_Q     = E[J_aligned-J_Q-only]
Delta_rate  = E[J_aligned-J_rate-matched-hazard]
Delta_regret= E[regret_deranged-regret_aligned].
```

Residual-alignment support requires 95% seed-level lower bounds above `0.01`
for `Delta_align`, above `0.005` for `Delta_Q`, and above zero for
`Delta_regret`; if and only if all development-support and scored-evaluation
rate-balance gates pass, `Delta_rate` must have a 95% lower bound above zero.
The exact adverse-residual quintile means and fixed Monte Carlo blocked trend
test must pass in `UNANNOUNCED-DIFFERENTIAL`/low-cost cells. Each of the three
same-history shadow-scored shortcut populations must have its 95% upper bound no
greater than `0.05`. These are
mechanism conditions, not additional primary opportunities to claim generic
performance.

Also report delivery fraction, overflow, energy, renewal/replan count and cost,
simultaneous trigger count, option collisions, per-age calibration, immediate
switch-window and switch-window-excluded effects, plus degradation contrasts
`(J_method^16-J_method^8)`. Occupancy and trigger counts are consequences, not
covariates to condition away.

## Frozen interpretation branches

1. **Direct algorithm value plus residual mechanism.** A primary performance or
   robustness route passes, all validity requirements hold, and every stated
   mechanism condition passes. Retain CRTO as a promising shared variable-`k`
   algorithm, with the claim restricted to finite-budget service relay and the
   tested `K` regimes. The causal clause is only that aligned
   residual-conditioned inference contributes to the trained package under the
   registered local interventions. Advance to the warehouse surface after
   same-direction EM interpretation and same-conversation Pro result challenge.
2. **Package value without residual attribution.** CRTO beats FULL, but aligned
   residual does not beat deranged/Q-only/rate control or its first stage is
   absent. Report only the bounded package effect. Delete the calibrated
   residual causal story; any architecture/auxiliary successor is a new
   scientific object.
3. **Residual use without algorithm value.** Alignment and audit gates pass, but
   CRTO does not beat FULL. The registered residual-conditioned path contributes
   locally to CRTO decisions but supplies no demonstrated package value beyond a
   competent raw-history learner. Do not advance this exact B1 package.
4. **Timing ceiling.** Calibration and action first stage pass and recoverable
   advantage is absent because losses occur before the first legal review. The
   DGP cannot evaluate post-commitment termination value. Do not reinterpret a
   null; only a separately defined within-option monitoring surface can revisit
   timing.
5. **Calibration/support failure.** Held-out ages, legal actions, or donor cells
   are unsupported. No mechanism conclusion is available. A successor must
   change the predictor/support object and obtain a new preactivity Pro ruling.
6. **Shortcut.** Benefit occurs only in the switch window, by higher replan
   frequency, on common sensor bias, or despite negative net audit advantage.
   Delete the claimed residual-selective mechanism.
7. **Retire only the exact B1 package.** When all validity, calibration,
   headroom, first-stage, hazard-support, and evaluation-rate-balance gates pass,
   define registered robustness benefit as `Delta_R=-Delta_F`. If, in every
   target regime, simultaneous Bonferroni one-sided
   `100*(1-0.05/18)=99.7222...%` model-based upper bounds are below `0.02` for
   `Delta_J`, `0.05` for `Delta_R`, `0.01` for `Delta_align`, `0.005` for
   `Delta_Q`, `0.005` for `Delta_rate`, and `0.005` for `Delta_regret`, the exact
   CRTO architecture, service-relay DGP, training budget, and tested `K` regimes
   have no supported material package or registered decision-control effect.
   Retire this exact B1 package unless a new prospective mechanism or surface
   supplies an independent rationale. This branch neither deletes the general
   residual-triggered-option family nor makes a scientific statement about the
   warehouse or UAV mappings; downstream allocation remains Root's portfolio
   decision. If any upper bound crosses its margin, absence remains unresolved.

## Claim ceiling

The maximum B1 claim is that, on this finite four-agent service-relay DGP, one
shared policy trained at `K={4,8}` improves normalized net team utility or
failure robustness against `FULL-HISTORY-AUX-TERM` at the registered held-out
and switching `K` regimes. If every mechanism gate passes, it may additionally
state that, at registered CRTO-reachable audit boundaries, aligned
residual-conditioned inference causally contributes to the trained CRTO package
under the prespecified intact-packet derangement, Q-path, and residual-free
hazard interventions. It cannot say that residual semantics uniquely cause the
effect or fully mediate CRTO versus FULL. B1 cannot establish new information,
hypothesis-class equivalence, Bayes-optimal superiority, arbitrary `K`,
arbitrary timing, asynchronous command horizons, agent-count robustness,
population effects, general calibration, generic safety, warehouse value, UAV
value, or real-UAV value.

## Second surface and UAV path

A qualifying B1 activates, but does not validate, a separate warehouse surface:
eight shared-policy robots, two pick zones, zone order queues, staging buffers,
aisle/link capacity, battery, and the options `PICK`, `DELIVER`, `TRANSIT`, and
`CHARGE`. External `K={4,8}` training and untouched `K=16`, `4 -> 16`, and
`16 -> 4` evaluation retain the same strong comparator, residual cut, explicit
reassignment/travel cost, action-support audit, and claim ceiling. Differential
events switch zone priority; common-mode order-display corruption and announced
priority switches retain the shortcut controls. The warehouse card must freeze
its own dynamics and margins before activity; B1 numbers do not transfer.

Only a qualifying warehouse replication activates a UAV simulator card. The
mapping is:

| Service-relay object | UAV simulator object |
|---|---|
| `TRACK-j` | acquire/maintain target track in sector `j` |
| `RELAY-j` | transmit track packets over relay link `j` |
| `TRANSIT-j` | reposition to sector/link geometry `j` |
| `RETURN` | preserve return-to-base energy reserve |
| source queue / relay buffer | track uncertainty / packet age backlog |
| relay capacity | link margin and available bitrate |
| energy and target distance | energy reserve and teammate ETA |
| external `K` | commanded option/coordination hold period |
| replan cost | trajectory disruption, command, and handoff cost |
| differential event | maneuvering target, priority-sector change, or shadowing |

The UAV simulator must expose only deployable telemetry, retain an external
varying `K`, have recoverable post-commitment consequences, and compare the
same aligned residual mechanism with a matched raw-history learner. This map is
a prospective bridge, not UAV evidence.

## Root-to-CM construction packet

If and only if Root later relays this packet after a new same-conversation Pro
`CLOSED` on v4 and EM intake,
CM should construct exactly `CRTO-B1-SCIENCE-20260812-04`, bind source/config,
verify identical learned-arm resources and causal timestamps, and return either
a concise preactivity technical nonconformance or a real command with the
registered resource ceiling. CM and Operator own code, tests when authorized,
environment, execution, and retained-result correctness. They must not tune on
untouched evaluation, relax a sparse derangement cell, change a margin, or
interpret a result. The result packet must contain per-seed/per-regime primary
effects, every validity/activity count, calibration and donor diagnostics,
mechanism cuts, audit headroom/regret, resource counts, anomalies, and whether
question-relevant output exists.
