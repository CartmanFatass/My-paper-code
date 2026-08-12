# Commitment-Residual Triggered Options B1 science card

```text
direction=commitment_residual_triggered_options
candidate=CRTO-B1
revision=CRTO-B1-SCIENCE-20260812-02
owner=EM_commitment_residual_triggered_options
scientific_activity_started=false
production_authorized=false
mathematical_closure=required_from_same_direction_chatgpt_external_pro
```

## Decision and question

This is a meaning-complete prospective B1 for a direct variable-`k` algorithm.
It asks whether one shared option policy, trained only at `k in {4,8}`, obtains
better held-out-`k=16` and within-episode `4 -> 16` / `16 -> 4` net team utility
or failure robustness than an information-, capacity-, interaction-, and
optimization-matched recurrent option critic because an explicit calibrated
post-commitment residual is a useful finite-data/OOD inductive bias.

The residual is a deterministic transformation of information available to
both learned arms. No outcome can support an information-gain claim. The
strongest alternative is that raw recurrent history, the same predictor, the
ordinary replan-versus-continue value margin, or merely a different replanning
rate explains any benefit. A frozen-boundary residual reassignment cut and
same-checkpoint Q-only and rate controls separate those explanations.

The science-bearing object is exactly this full composite file at revision
`CRTO-B1-SCIENCE-20260812-02`. It prospectively supersedes unsent revision
`CRTO-B1-SCIENCE-20260812-01`; no provider turn, implementation, or scientific
activity occurred under v1. Any change to the DGP, provider-visible
mathematics, arms, data split, activity law, estimands, margins, inference,
or interpretation branches creates a new complete revision. Production is
withheld until a clean dedicated direction-specific ChatGPT External Pro
conversation returns literal `CLOSED`, this EM intakes that ruling, CM accepts
technical conformance, and Root releases execution.

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
  selects the initially hot lane. The policy selects initial options without a
  renewal charge.
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
observed before that time's review and each active option retains its age. If
its age is already at least the new `K`, renewal is immediately forced;
otherwise its next multiple-of-four review uses the new cap. The predictor is
re-anchored at the switch from current deployable history and the unchanged
active option; policy/predictor recurrent state and physical state are not
reset. No residual action is scored at the switch instant, and the `[-8,+8]`
primitive-step switch window is excluded from mechanism selectivity summaries.

## Deployable observation and shared-policy law

At every primitive step, agent `i` observes its location, normalized energy,
current option, absolute age, `age/K`, `K/16`, cost regime, legal mask, visible
cue, and a common broadcast containing normalized physical queue/buffer
telemetry, preceding-four-step deliveries by lane, option-count and
location-count histograms, and time fraction. Under `COMMON-SENSOR`, only the
two stated queue fields are offset. There are no agent IDs, event labels,
future quantities, reward labels, counterfactual values, or privileged simulator
states in execution inputs. A shared 64-unit GRU processes this raw history.
A centralized value baseline may see the physical training state, but every
deployed option score, predictor value, and termination decision uses only the
deployable history and common broadcast.

The predictor target for agent `i` is the eight-vector

```text
Y_i = [U_L/64, U_R/64, B_L/64, B_R/64,
       delivered_L_over_previous_4/8, delivered_R_over_previous_4/8,
       E_i/32, graph_distance_to_current_option_target/2].
```

The common broadcast and current local observation contain every realized
component of `Y_i`.

## Frozen predictor, calibration, and residual

For every independent algorithm seed, an arm-independent scripted data set has
256 complete episodes: 128 at `K=4` and 128 at `K=8`, balanced over event and
cost cells. At each discretionary review the script terminates with probability
`0.25`; at every renewal or termination it samples uniformly from the legal
options, excluding the current option after termination. Episodes are assigned
before generation to predictor-fit (128), calibration (64), and development
(64) sets, stratified by `K`, event, and cost. No transition crosses a split.

A shared recurrent four-step transition cell `F_psi` is unrolled once for age
4, twice for age 8, three times for age 12, and four times for age 16. It takes
only the commitment-origin deployable history, current option, `K/16`, and
normalized requested forecast age, and emits an eight-dimensional Gaussian
mean `mu_a` and lower-triangular Cholesky factor `L_a` with positive diagonal.

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

At a commitment start or `K` switch, forecasts are issued before the target
telemetry. At a later legal review, using only telemetry already observed,

```text
e_i = solve(L_a, Y_i - mu_a).
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
raw forecast packet is `[Y_i,mu_a,vech(L_a)]`, also dimension 52. Both packets,
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
It therefore has all information required to reconstruct the residual but no
hard-coded residual representation. Any CRTO advantage is an inductive-bias or
learnability result, not additional observability.

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
one-hot, cost divided by `4`, regime one-hot, and switch direction/phase; it has
no residual, telemetry value, hidden event label, future value, or outcome.
Continuous features are centered and scaled using only this development panel.

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
review in `[event_onset+4,event_onset+20]`, outside the switch exclusion window;
`NONE` uses its pseudo-onset. Selection uses no residual, action, or outcome.
The aligned and deranged branches clone the entire predecision simulator and
future tape, differ only in that target agent's one residual packet, hold other
agents' simultaneous actions fixed, and return to aligned residuals afterward.
At the same state, evaluation also enumerates the target agent's `KEEP` and
every legal replacement for 16 primitive steps under common future noise,
holding other simultaneous actions at their aligned choices and then using the
frozen CRTO continuation policy. The fixed terminal potential is
`-0.02*(U_L+U_R+B_L+B_R)-0.01*sum_i(32-E_i)`. This yields decision regret and
the exact finite-horizon net replan advantage without exposing either quantity
to the policy.

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
optimization, capacity-probe optimization, logistic fitting, and statistics
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

A conclusion-bearing B1 requires all eight paired training seeds and all frozen
evaluation cells, finite returns, identical scenario counts, exact action/cost
parity, and no test leakage. In addition:

- before learned-policy activity, a separate capacity audit fits
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
  policy. Failure means the proposed FULL adapter is not an adequate
  representational baseline and returns the design to this EM before any
  learned-policy optimizer update;

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
- the aligned-versus-deranged decision-disagreement fraction has a seed-level
  95% lower confidence bound above `0.05`;
- a cross-validated classifier using residual packet norms, predictor
  uncertainty, joint option-count histogram, role/location counts, and frozen
  predecision stratum fields cannot distinguish donor from recipient with AUC
  above `0.60`;
- the held-out-`K=16` 90% Gaussian ellipsoid coverage lies in `[0.80,0.98]`,
  ten-bin PIT expected calibration error is at most `0.10`, and fewer than 5%
  of residual coordinates hit either clipping boundary, reported separately at
  ages `4`, `8`, `12`, and `16`;
- at least 20% of audited legal states have a best 16-step net replan advantage
  of at least `0.02` normalized utility, so the toy contains recoverable
  termination headroom.

Failure of action support, the derangement first stage, donor support,
rate-control convergence/support, or calibration withholds the
residual-mechanism conclusion. A technically valid
whole-algorithm CRTO-versus-FULL total effect may still be reported at the
package ceiling, but it cannot be called a calibrated-residual mechanism.
Failure of recovery headroom says this toy cannot test the family; it is not
evidence that earlier termination is useless elsewhere.

## Estimands and inference

For each seed and regime, average paired scenario differences before any
across-seed inference. Evaluation episodes are nested observations and never
replace training seeds. Report all eight seed effects.

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
familywise primary error. In either route, simultaneous Bonferroni 98.33%
one-sided bounds must exclude worse than `-0.02` utility and `+0.05` failure
probability in every individual target regime. Exact `2^8` paired seed-sign
randomization p-values accompany, but do not replace, the frozen margins.

Secondary mechanism estimands use the same CRTO checkpoint and common cloned
future tape:

```text
Delta_align = E[J_aligned-J_deranged]
Delta_Q     = E[J_aligned-J_Q-only]
Delta_rate  = E[J_aligned-J_rate-matched-hazard]
Delta_regret= E[regret_deranged-regret_aligned].
```

Residual-alignment support requires 95% seed-level lower bounds above `0.01`
for `Delta_align`, above `0.005` for `Delta_Q`, and above zero for
`Delta_regret`; `Delta_rate` must be positive with a 95% lower bound above
zero. In `UNANNOUNCED-DIFFERENTIAL`/low-cost cells, adverse-residual quintile
must monotonically order the enumerated net termination advantage by a
seed-blocked permutation trend test at `p<=0.05`. In `COMMON-SENSOR`, cued, and
high-cost negative-advantage audit states, CRTO's excess termination probability
over FULL must have a 95% upper bound no greater than `0.05`. These are
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
   tested `K` regimes. Advance to the warehouse surface after same-direction EM
   interpretation and same-conversation Pro result challenge.
2. **Package value without residual attribution.** CRTO beats FULL, but aligned
   residual does not beat deranged/Q-only/rate control or its first stage is
   absent. Report only the bounded package effect. Delete the calibrated
   residual causal story; any architecture/auxiliary successor is a new
   scientific object.
3. **Residual use without algorithm value.** Alignment and audit gates pass, but
   CRTO does not beat FULL. The residual influences decisions but supplies no
   demonstrated value beyond a competent raw-history learner. Do not advance
   this family.
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
7. **Family deletion on this target path.** Treat the complete CRTO family
   specified here as deleted from further service-relay, warehouse, and UAV
   investment if all validity/calibration/headroom/first-stage requirements pass
   yet the 95% upper bounds are below `0.01` for CRTO-minus-FULL and below
   `0.005` for each of aligned-minus-deranged and aligned-minus-Q-only in every
   target regime, with no prespecified event/cost subgroup benefit. This is
   strong evidence that the explicit residual neither adds package value nor
   controls useful decisions despite available recoverable opportunities. It
   is not a universal theorem about every possible residual controller.

## Claim ceiling

The maximum B1 claim is that, on this finite four-agent service-relay DGP, one
shared policy trained at `K={4,8}` improves normalized net team utility or
failure robustness against `FULL-HISTORY-AUX-TERM` at the registered held-out
and switching `K` regimes, and that explicit residual alignment explains that
finite-budget improvement only if all mechanism gates pass. B1 cannot establish
new information, Bayes-optimal superiority, arbitrary `K`, arbitrary timing,
asynchronous command horizons, agent-count robustness, population effects,
general calibration, generic safety, warehouse value, UAV value, or real-UAV
value.

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

If and only if Root later relays this packet after Pro `CLOSED` and EM intake,
CM should construct exactly `CRTO-B1-SCIENCE-20260812-02`, bind source/config,
verify identical learned-arm resources and causal timestamps, and return either
a concise preactivity technical nonconformance or a real command with the
registered resource ceiling. CM and Operator own code, tests when authorized,
environment, execution, and retained-result correctness. They must not tune on
untouched evaluation, relax a sparse derangement cell, change a margin, or
interpret a result. The result packet must contain per-seed/per-regime primary
effects, every validity/activity count, calibration and donor diagnostics,
mechanism cuts, audit headroom/regret, resource counts, anomalies, and whether
question-relevant output exists.
