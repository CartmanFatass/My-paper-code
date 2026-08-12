# Semigroup-Consistent Duration Model Policy B1 science card

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-B1
revision=SCDMP-B1-SCIENCE-20260812-01
owner=EM_semigroup_consistent_duration_model_policy
source_inspiration=SCDMP-VK-FAMILY-CUT-01
source_is_evidence=false
artifact_status=PREPARED_NOT_SENT
scientific_activity_started=false
production_authorized=false
chatgpt_external_pro_math_closure=required
```

## Direction decision and bounded question

This is a nonredundant direct variable-`k` family worth a prospective B1. It
does not use allocation or bids, residual-triggered termination, Voronoi
measure weighting, lifecycle exposure, or credit relay. Its single uncertainty
is whether an explicit dynamical composition/cumulative-reward cocycle loss is
a useful finite-budget OOD inductive bias when one shared model policy is
trained only on skill durations `k in {2,4,8}` and deployed at unseen
`k in {6,12}` and at within-episode `6 -> 12` / `12 -> 6` changes.

The treatment is `SCDMP`; the strongest comparator is `SCDMP-NOCOMP`. The two
arms have the same deployable information, continuous numeric `k`, word
forecast, model and policy architecture, parameters, endpoint supervision,
training trajectories, minibatches, optimizer updates, action search, and
deployment work. Their only gradient difference is that SCDMP gives nonzero
weight to two train-support composition losses. NOCOMP constructs the same
composition graph but multiplies it by zero; it receives no compensating
endpoint gradient. Repeating endpoint updates in NOCOMP would change endpoint
objective weight and is therefore deliberately excluded.

The strongest alternative is that the unrestricted `k`-conditioned NOCOMP
model learns the same rule from identical endpoints and context words. Thus a
positive result can support only a finite-budget/OOD inductive-bias claim, not
new information, unique expressivity, or a theorem that semigroup constraints
are necessary. A visible-label sham and reversed noncommuting event words bound
the still-strong alternative that any gain is generic regularization, duration
encoding, or training-path noise rather than useful physical composition.

The science-bearing object is this complete file at exact revision
`SCDMP-B1-SCIENCE-20260812-01`. A change to its DGP, observation, word law,
arms, losses, activity rule, training/evaluation split, estimands, margins,
inference, interpretation, or resources creates a new complete revision.
Production requires a literal `CLOSED` ruling on this exact revision from the
dedicated same-direction ChatGPT External Pro conversation, this EM's intake of
that ruling, CM technical acceptance, and Root scheduling.

## Deterministic four-agent convoy DGP

### Physical state, actions, and fixed-degree interaction

There are `N=4` homogeneous agents in fixed cyclic slots on a ring of
circumference four. Slot `i+1` follows slot `i`, with indices modulo four.
The moving formation reference advances at speed `v_star=0.20`. Agent `i` has
reference-relative unwrapped position error `e_i in [-1.5,1.5]`, velocity
`v_i in [-0.6,0.6]`, and a visible wind sign `q_i in {-1,+1}`. The four signs
are a cyclic rotation of `[+1,-1,+1,-1]`, selected by the exogenous episode
tape. The complete physical Markov state is

```text
y = ((e_1,v_1,q_1),...,(e_4,v_4,q_4)).
```

The directed circular gap from slot `i` to `i+1` is

```text
g_i = 1 + e_(i+1) - e_i.
```

At a true skill boundary, every agent selects one macro-action
`u_i in {-1,0,+1}`, named `LEFT`, `COAST`, and `RIGHT`. The complete joint
action `u` is held unchanged for all `k` primitive steps. There is no review,
termination, low-level reset, or actor call at a virtual composition split.
All four actions are selected from one predecision snapshot and take effect
simultaneously.

### Observable context words and micro-dynamics

At each true boundary an external scheduler supplies both the current duration
`k` and the complete upcoming length-`k` context word

```text
w = (m_1,...,m_k),
m_j in {A_REAL,B_REAL,A_SHAM,B_SHAM}.
```

The word is ordinary deployable information for both arms; it represents a
short weather/friction forecast. It is not chosen by the policy. A word never
changes after the action is selected. At primitive offset `j`, let

```text
(rho, sigma)(A_REAL) = (0.98,+1)
(rho, sigma)(B_REAL) = (0.82,-1)
(rho, sigma)(A_SHAM) = (0.90, 0)
(rho, sigma)(B_SHAM) = (0.90, 0).
```

The `A_SHAM` and `B_SHAM` labels and their order remain visible but have
identical physics. Conditional on the initial state, joint action, and word,
the transition is deterministic:

```text
v_i(t+1) = clip(rho_m * v_i(t) + 0.12*u_i + 0.06*sigma_m*q_i,
                -0.6, 0.6)
e_i(t+1) = clip(e_i(t) + 0.10*(v_i(t+1)-v_star),
                -1.5, 1.5).
```

The state includes every dynamical quantity; there is no hidden mode,
unobserved controller memory, process noise, or actor-induced state reset.
Consequently composition is a statement about the same held-action
intervention. The card makes no point-semigroup claim for conditional means in
a stochastic or partially observed process.

The primitive node and directed-edge rewards, evaluated from the post-transition
state, are

```text
r_i_node = 1/4
           - 0.50*e_i(t+1)^2/4
           - 0.25*(v_i(t+1)-v_star)^2/4
           - 0.02*u_i^2/4
           - 0.25*1[|e_i(t+1)|=1.5]/4

r_i_edge = -0.75*(g_i(t+1)-1)^2/4
           -2.00*1[g_i(t+1)<0.25]/4

r_t = sum_i (r_i_node+r_i_edge).
```

Equality in the clipping indicator means the update reached either position
boundary. Rewards are undiscounted. For a word of length `k`, cumulative reward
is `R=sum_(j=0)^(k-1) r_(t+j)`. An episode has `T=240` primitive steps and

```text
J = (1/T) * sum_(t=0)^(T-1) r_t.
```

The failure indicator is one if any edge gap falls below `0.25` or any position
update reaches a clipping boundary during the episode. Also report collision
steps, minimum gap, clipping steps, position-error RMS, worst-agent position
error, velocity-error RMS, action changes, energy proxy `mean(u_i^2)`, boundary
latency, and boundary-message count.

At reset, `e_i` are independent `Uniform[-0.20,0.20]` draws followed by
subtracting their four-agent mean, and `v_i` are independent
`Uniform[0.10,0.30]` draws. The cyclic `q` rotation, initial states, word
orders, and all evaluation cells are fixed by an exogenous PCG64 tape before
either arm acts. Paired arms use the same tape. Actions never alter later word
choices.

Science-bearing random streams are disjoint: corpus generation uses
`PCG64(730000+algorithm_seed)`, audit-state generation uses
`PCG64(740000+algorithm_seed)`, and scored regime `r` uses
`PCG64(750000+1000*algorithm_seed+r)` for the regime order printed below.
Within a stream, draws are consumed in episode, primitive-time, then slot
order. No arm-specific environment stream exists.

### Train-support and held-out words

Superscripts denote repeated tokens. REAL and SHAM use identical label
patterns; only the coefficients above differ.

| duration | optimization-visible words |
|---|---|
| `2` | `A^2`, `B^2`, `AB`, `BA` |
| `4` | `A^4`, `B^4`, `A^2B^2`, `B^2A^2` |
| `8` | `A^8`, `B^8`, `A^4B^4`, `B^4A^4` |

The untouched target words are

| duration | evaluation-only words |
|---|---|
| `6` | `A^2B^4`, `B^4A^2`, `A^4B^2`, `B^2A^4` |
| `12` | `A^4B^8`, `B^8A^4`, `A^8B^4`, `B^4A^8` |

Every target word is an ordered concatenation of train-supported length-two,
four, or eight words, but neither duration `6` nor `12`, no complete target
word, and no target/switch statistic is ever constructed or queried by an
optimizer, normalizer, checkpoint rule, architecture choice, or loss weight.
The fact that a training trajectory physically passes through its sixth step
does not create a length-six target or query.

Training episodes hold external `k` fixed at `2`, `4`, or `8`. Evaluation uses
fixed diagnostic `k=4` and `k=8`, target fixed `k=6` and `k=12`, and target
switches `6 -> 12` and `12 -> 6` at `t=120`. The switch time is a true boundary
for both durations. The next `k` is not revealed before `t=120`; at that
boundary it and the next word are observed before choosing a new action. No
physical, encoder, or model state is reset. All later decisions use the new
duration. Words cycle through the applicable four-entry table by the exogenous
tape and are balanced within each evaluation panel.

For any episode numbered `h` from zero and boundary numbered `b` within its
current constant-`k` segment, the selected word-table row is
`(h mod 4 + b) mod 4`. At a switch, `b` restarts at zero in the new duration's
table. Episode class is REAL when `h mod 8 < 4` and SHAM otherwise. Thus each
consecutive block of eight episodes contains every word-table offset once in
each class. This schedule, including future table rows, is exogenous; only the
one word beginning at the current true boundary is observed.

## Observation and shared model-predictive policy

At a boundary, every agent receives the common ordered ring broadcast of all
`(e_i,v_i,q_i)`, the present `k/12`, the complete word, the previous joint
macro-action, and the fact that this is a true boundary. No future state,
reward, hidden result, oracle action, event outcome, or arm identity is
available. There are no mid-skill messages or decisions. The fixed ordered
ring broadcast is allowed because B1 tests only variable `k`, not variable
`N` or decentralized bandwidth scaling.

Both arms use the same shared node transition model `F_theta`, shared node and
edge cumulative-reward models `G_theta^node,G_theta^edge`, and exact
fixed-degree max-sum actor. For a word `w`, they predict

```text
F(y_i,u_i,w)                         -> terminal (e_i',v_i')
G_node(y_i,u_i,w)                    -> node cumulative reward
G_edge(y_i,y_(i+1),u_i,u_(i+1),w)   -> directed-edge cumulative reward.
```

`q_i` is carried unchanged by `F`. The deployable model has:

- a shared node encoder `Linear(3,32) -> tanh -> Linear(32,32) -> tanh` on
  `[e_i/1.5, v_i/0.6, q_i]`;
- a shared action embedding `Linear(3,8) -> tanh` on the action one-hot;
- one shared word encoder, a width-32 GRU with zero initial hidden state, on
  the ordered sequence `[four-token one-hot, j/12]`;
- an `F` head `Linear(73,64) -> tanh -> Linear(64,64) -> tanh -> Linear(64,2)`;
  its two outputs pass through `1.5*tanh` and `0.6*tanh` respectively;
- a node-reward head `Linear(73,64) -> tanh -> Linear(64,1)`; and
- a directed-edge head `Linear(113,64) -> tanh -> Linear(64,1)` on ordered
  node encodings, ordered action embeddings, word embedding, and `k/12`.

The stated input widths include `k/12`. All affine input weights use
Xavier-uniform initialization with tanh gain, GRU recurrent matrices use
orthogonal initialization, and all biases are zero. Initialization stream
`PCG64(710000+algorithm_seed)` is paired byte-for-byte across arms. There is
no per-`k` head, duration lookup table, clipping of `k`, dropout, arm flag,
privileged state, or raw target-word cache.

With one copy of every shared module above, each arm has exactly 26,148
trainable scalar parameters: 1,184 in the node encoder, 32 in the action
embedding, 3,744 in the word GRU, 9,026 in `F`, 4,801 in `G_node`, and 7,361
in `G_edge`. No module is replicated by agent, edge, duration, or word class.

At a true boundary, the actor builds node scores for each of three actions and
directed-edge scores for each of nine neighbor-action pairs using the current
word. For a predicted terminal state `y_hat`, the frozen decomposed terminal
potential is

```text
H_node_i = -0.25*e_i_hat^2/4
           -0.125*(v_i_hat-v_star)^2/4
H_edge_i = -0.375*(g_i_hat-1)^2/4
           -1.00*1[g_i_hat<0.25]/4.
```

The score of a candidate joint action is the sum of predicted node and edge
cumulative rewards plus every `H_node` and `H_edge`. Thus both the terminal
transition prediction and cumulative reward prediction enter decisions. The
actor maximizes this factorized score exactly on the four-node cycle by
conditioning on the first slot's action and applying max-sum dynamic programming
around the remaining chain. It then selects the globally best consistent
cycle. Ties use the fixed lexicographic action order
`LEFT < COAST < RIGHT` over slots 1--4. The selected joint action is held for
the whole word. The actor has no separate learned parameter, sampling
temperature, early termination, or duration-specific branch. Both arms execute
the identical search.

Deployment has fixed-degree computation
`O(k*C + N*A^3*C)` per boundary and `O(N*A*C)` memory for `A=3`, model width
constant `C`, and word length `k`; the `A^3` factor is the exact-cycle
conditioning cost and is a fixed 27 here. There is no dense `N^2` attention. B1's
claim nevertheless remains fixed at `N=4`.

## Exact cocycle and training object

For any legal words `p,q`, concatenation `p q`, and a joint action held across
both pieces, the deterministic physical process satisfies the monoid-action
and undiscounted reward-cocycle equations

```text
F(y,u,pq) = F(F(y,u,p),u,q)
G_node(y,u,pq)
  = G_node(y,u,p) + G_node(F(y,u,p),u,q)
G_edge(y_i,y_j,u_i,u_j,pq)
  = G_edge(y_i,y_j,u_i,u_j,p)
    + G_edge(F(y_i,u_i,p),F(y_j,u_j,p),u_i,u_j,q).
```

These are the precise nonautonomous form meant by "semigroup consistency." A
virtual split neither calls the actor nor changes the action. `F(empty)=identity`
and each `G(empty)=0`. The lack of `gamma^|p|` is intentional because the card's
cumulative reward is undiscounted. No conclusion is transferred to stochastic
kernels, belief-state composition, or hidden context.

For each algorithm seed, an arm-independent corpus has 192 complete 64-step
behavior episodes: 64 at each training duration. Within each duration it is
balanced over REAL/SHAM and all four applicable words. At each true boundary a
counterbalanced schedule cycles through the 81 joint actions with a seed-specific
offset, so every scalar action and every joint action is represented at every
duration. Specifically, the base-three joint-action index is
`(global_boundary_index_within_duration+17*algorithm_seed) mod 81`, with slot
1 as the most significant base-three digit and digit order
`LEFT,COAST,RIGHT`. The action is held for the episode's external `k`.
Episodes are ordered in consecutive eight-episode blocks using the REAL/SHAM
and word-offset rule above. The first 48 episodes at each duration therefore
give six episodes per dynamics-class/word-offset cell and form the fit set;
the remaining 16 give two per cell and form an untouched train-support probe.
The split is fixed before generation. No transition crosses reset or a true
action boundary.

At every legal boundary, endpoint examples use prefixes of length `2`, `4`,
and `8` only when the same joint action is physically held that long.
Composition examples are exactly `(2,2)->4` and `(4,4)->8`; each suffix uses
the actual advanced physical state and suffix word. All state-coordinate and
reward scales are the fit-set standard deviations with a floor of `1e-3`,
frozen before optimization. Scaling is pooled across all fit-set training
durations and words: one scalar for each of the two physical coordinates, one
for node cumulative reward, and one for edge cumulative reward. There is no
duration-, class-, word-, or arm-specific scaler.

Let `bar(delta_F)` be coordinate-standardized physical endpoint error and
`bar(delta_Gn),bar(delta_Ge)` the corresponding standardized node and edge
reward errors. Endpoint loss gives the three duration types equal weight, and
composition loss gives the two pair types equal weight:

```text
L_endpoint = mean_tau mean_examples [
               ||bar(F_tau-y_tau)||^2/2
               + mean_i bar(G_node_tau-R_node_tau)^2
               + mean_edges bar(G_edge_tau-R_edge_tau)^2 ]

delta_F(p,q)  = F(y,u,pq)-F(F(y,u,p),u,q)
delta_Gn(p,q) = G_node(y,u,pq)
                -G_node(y,u,p)-G_node(F(y,u,p),u,q)
delta_Ge(p,q) = G_edge(y_i,y_j,u_i,u_j,pq)
                -G_edge(y_i,y_j,u_i,u_j,p)
                -G_edge(F_i(p),F_j(p),u_i,u_j,q)

L_comp = mean_pair_type mean_examples [
           ||bar(delta_F)||^2/2
           + mean_i bar(delta_Gn)^2
           + mean_edges bar(delta_Ge)^2 ]

L_SCDMP       = L_endpoint + 0.5*L_comp
L_SCDMP-NOCOMP= L_endpoint + 0.0*L_comp.
```

All paths through both the inner and outer model calls receive gradients in
SCDMP; there is no stop-gradient or target copy. The physical-coordinate
endpoint losses prevent latent-collapse explanations. NOCOMP executes the same
composition forward graph and zero-weight reduction, but the zero term
contributes no gradient. It does not repeat endpoint data.

Both arms use Adam `(lr=1e-3, betas=(0.9,0.999), eps=1e-8,
weight_decay=1e-5)`, global gradient-norm clipping at `1.0`, and exactly 1,000
updates. Each update has 192 endpoint examples, exactly 64 from each duration,
and 128 composition examples, exactly 64 from each pair type. Each group of 64
contains eight examples from every REAL/SHAM-by-four-word-offset stratum. Within
each stratum, examples are ordered by
`(episode,boundary,duration_or_pair,node_or_edge)` and one PCG64 stream seeded
by `720000+algorithm_seed` creates the stratum permutations in lexicographic
stratum order. Each permutation is consumed cyclically and wraps without
reshuffle. Paired arms use identical batches. The final update is the only
checkpoint; there is no early stop, validation selection, hyperparameter
search, or arm-specific repair.

## Activity, support, and oracle headroom

Question-relevant scientific activity begins when the first complete optimizer
update starts whose endpoint batch contains all three training durations and
whose composition batch contains both pair types, both REAL and SHAM tokens,
at least two distinct joint actions, and every scalar skill. Before that exact
event, construction, data generation, serialization, or launcher work is not
scientific activity. Report the actual denominators.

A result identifies the question only if all of these prospective conditions
hold:

1. The corpus, update, action, word, seed, and no-test-duration leakage counts
   conform exactly, and both arms finish the fixed final checkpoint within the
   resource envelope.
2. Every target word has its declared ordered train-supported decomposition;
   every joint action occurs at least four times among fit-set boundaries for
   each direct training duration; and at least 90% of target audit states have
   each normalized physical coordinate inside the fit-set coordinatewise
   minimum/maximum. A failed condition is reported, never relaxed.
3. On the common untouched audit panel, REAL reversal twins have median across
   states of `max_u |S_true(w,u)/k-S_true(reverse(w),u)/k| >= 0.01`, where
   `S_true=R_true+H(y_true_terminal)`, and the constrained one-word oracle
   action differs on at least 10% of twins.
   SHAM reversal twins must agree to numerical tolerance `1e-10`. This proves
   that order matters physically rather than merely by label.
4. The NOCOMP actor has recoverable held-out headroom: on at least 20% of audit
   states its selected action is at least `0.02` per primitive step below the
   exact constrained one-word oracle under the same `R+H` score, and its mean
   regret is at least `0.01`.
   The oracle receives exactly the same state, word, held-action constraint,
   and 81-action set; it rolls the known DGP only for audit and is never an
   actor input or training target.
5. The NOCOMP post-training composite held-out defect defined below is at least
   `0.05` standardized units, and SCDMP and NOCOMP select different joint
   actions on at least 10% of REAL audit states. These are representation and
   actor first stages, not outcome claims.
6. Neither arm has nonfinite outputs; no more than 1% of audit predictions hit
   an `F` output bound. On the untouched train-support probe, each arm's
   composite standardized endpoint/node-reward/edge-reward RMSE is at most
   `0.35`. On target audit queries, NOCOMP's composite RMSE is at most `0.75`;
   a composition-specific claim additionally requires SCDMP's to be at most
   `0.50`. For each predicted physical coordinate, SCDMP audit variance is
   between `0.25` and `4.0` times the corresponding true-terminal variance,
   and at least 20% of REAL audit states have a predicted best-minus-worst
   candidate score range of `0.02*k` or more. Lower composition defect with
   collapsed physical outputs, inaccurate endpoints, or an actor-insensitive
   score is not a valid mechanism first stage.

The audit panel is common and evaluation-independent: for every seed it has 32
`k=6` and 32 `k=12` boundary states from a scripted held-action generator,
balanced over REAL/SHAM, word, `q` rotation, and initial severity. All 81 joint
actions are rolled exactly. It is opened only after both final checkpoints.
Audit outcomes never select a checkpoint or threshold.

Each audit state begins from its own audit-stream reset and is advanced for
exactly 48 primitive steps at training-supported `k=4`. Its word offsets follow
the printed episode/boundary rule and its held actions cycle through base-three
joint-action indices beginning at `(audit_index+31*algorithm_seed) mod 81`.
The state at step 48 is paired with one target word; audit index modulo four
selects that word, and index modulo eight selects REAL/SHAM by the same rule.
Indices `0,...,31` receive `k=6` and `32,...,63` receive `k=12`.

Failure of activity, support, REAL order effect, SHAM identity, or oracle
headroom makes the B1 result nonidentifying for this family. It is not evidence
that composition is useless elsewhere.

## Evaluation, estimands, and inference

There are eight independent paired algorithm seeds `0,...,7`. Evaluation has
six regimes: diagnostics fixed `k=4` and `k=8`, plus targets fixed `k=6`, fixed
`k=12`, `6 -> 12`, and `12 -> 6`. Each arm/seed/regime receives 32 locked
240-step episodes, balanced 16 REAL and 16 SHAM and balanced over the four word
types and four initial-state replicates. Training, support-probe, audit, and
scored-evaluation tapes are disjoint. All evaluation uses the final checkpoint.
The regime indices used in the scored PCG64 seed are respectively
`0,1,2,3,4,5` in that printed order. Episode numbers `0,...,31` use the exact
class and word-offset law already specified, giving four replicates of every
dynamics-class/initial-word-offset cell.

For each seed, average paired episode differences within each dynamics class
and regime before across-seed inference. Episodes are not independent training
replicates. Define higher-is-better target effects

```text
Delta_J(r) = E[J_SCDMP-J_NOCOMP | REAL, target regime r]
Delta_task = mean_r Delta_J(r)

Gap_m = mean(J_m | REAL, k in {4,8})
        -mean(J_m | REAL, four target regimes)
Delta_rob = Gap_NOCOMP-Gap_SCDMP

Delta_fail(r) = E[failure_NOCOMP-failure_SCDMP | REAL,r]

D_comp_m = mean(
  RMS_standardized_F_cocycle_defect,
  RMS_standardized_node_reward_cocycle_defect,
  RMS_standardized_edge_reward_cocycle_defect)
Delta_comp = D_comp_NOCOMP-D_comp_SCDMP

E_pred_m = mean standardized true endpoint/node-reward/edge-reward RMSE
Delta_pred = E_pred_NOCOMP-E_pred_SCDMP

Delta_spec = mean_r Delta_J_REAL(r)-mean_r Delta_J_SHAM(r).
```

`D_comp` and `E_pred` use only the common audit panel and both legal target
decompositions (`2+4`/`4+2` for six and `4+8`/`8+4` for twelve). Also report
direct-versus-recursive prediction disagreement, oracle regret, action
disagreement, word-reversal effects, per-word results, collision probability,
minimum-gap CVaR at 10%, position/velocity error, clipping, energy proxy,
action changes, messages, and latency. Occupancy, chosen actions, and model
confidence are descendants and are never conditioned away in the primary
effect.

The two Bonferroni-separated direct-value routes are:

1. **Performance:** the one-sided 97.5% seed-level t lower bound for
   `Delta_task` exceeds `0.015` normalized reward per primitive step.
2. **Failure robustness:** the one-sided 97.5% lower bound for the mean of the
   four `Delta_fail(r)` exceeds `0.05`, while the 95% lower bound for
   `Delta_task` exceeds `-0.005`.

Either route additionally requires simultaneous one-sided Bonferroni 98.75%
lower bounds for every target `Delta_J(r)` above `-0.005` and corresponding
98.75% bounds for the two seen-duration effects above `-0.005`. Exact `2^8`
paired seed-sign randomization p-values and all eight seed effects accompany
the intervals but do not replace the frozen margins.

A composition-specific mechanism attribution additionally requires 95%
seed-level lower bounds above `0.10` for `Delta_comp`, above `0.05` for
`Delta_pred`, above `0.010` for `Delta_rob`, and above `0.005` for
`Delta_spec`, plus every activity/support/headroom/first-stage condition. These
are not extra opportunities for a generic performance claim. Since there is no
separately trained adjacency-shuffled-loss arm, even this branch attributes the
bounded composition-loss package and its order-selective signature; it does not
prove unique mediation by the mathematically correct cocycle.

## Frozen interpretation branches

1. **Direct variable-`k` value with composition signature.** At least one
   direct-value route passes, all validity and non-harm conditions hold, and
   all composition-specific gates pass. Retain SCDMP as a promising finite-budget
   variable-`k` algorithm on this deterministic forecast-visible surface.
2. **Package value without algebraic attribution.** A direct-value route passes
   but composition, prediction, REAL-versus-SHAM, or actor first stage fails.
   Report only the bounded learned-package result. Do not claim the semigroup
   mechanism; any successor aimed at that attribution is a new revision.
3. **Model regularity without decision value.** SCDMP reduces composition and
   prediction error, but neither direct-value route passes. The loss shapes the
   model without demonstrated task value. Apply the family-deletion rule below
   if its stronger conditions hold; otherwise make no positive claim.
4. **Free model sufficient.** NOCOMP is at the oracle ceiling or has defect
   below the registered first-stage floor. The toy cannot distinguish whether
   explicit consistency helps when a free model has room to improve. Do not
   tune or reinterpret the null.
5. **Shortcut/generic regularization.** Any apparent gain is equally large on
   SHAM labels, survives without physical order activity, accompanies collapsed
   endpoints, or lacks action disagreement. Delete the order-selective causal
   story; at most retain the package effect if its primary route remains valid.
6. **Adverse effect.** A simultaneous bound establishes material target or
   seen-duration harm. Reject this exact treatment on the convoy surface and
   report the affected regimes without averaging them away.
7. **Nonidentifying.** Activity, support, headroom, resource, leakage, complete
   output, or deterministic-cocycle conditions fail. No positive, negative,
   null, equivalence, or family-deletion conclusion is available.

### Prospective family-deletion condition

Delete further SCDMP-family investment on the convoy, ground-payload, and UAV
path defined here if and only if all activity, technical validity, leakage,
state support, physical order, SHAM identity, oracle headroom, output-variance,
and actor-first-stage conditions hold; the 95% lower bound for `Delta_comp`
exceeds `0.10`; yet for every target regime the one-sided 95% upper bound for
`Delta_J(r)` is below `0.010` and the upper bound for `Delta_fail(r)` is below
`0.03`, the upper bound for `Delta_spec` is below `0.005`, and no prespecified
REAL word or duration subgroup has a 95% lower bound above `0.010`.

That outcome says a successfully imposed composition bias has no minimum useful
decision value despite a physically active order effect and a competent-but-
imperfect free comparator. It deletes this explicit consistency family on this
forecast-visible action-hold path, not every possible temporal model. If
`Delta_comp` itself lacks a first stage, only this loss realization is rejected;
if oracle headroom or support is absent, the result is nonidentifying rather
than family-negative. Wide intervals are indeterminate and do not authorize a
threshold change or automatic rerun.

## Claim ceiling

The maximum B1 claim is that on this deterministic, fully observed,
forecast-visible, fixed-four-agent convoy, one shared model-predictive policy
trained only with durations `2,4,8` achieves a finite-budget performance or
failure-robustness advantage over an otherwise matched free duration model at
the registered held-out and switching `6/12` regimes, with an order-selective
composition-loss signature only when all mechanism gates pass.

B1 cannot establish additional information, unique expressivity, Bayes-optimal
superiority, arbitrary or unknown `k`, stochastic-kernel consistency, hidden
weather robustness, asynchronous agents, early termination value, variable
`N`, general decentralized MARL scaling, ground-robot value, UAV value, safety,
or real-flight validity.

## Second surface and UAV bridge

A qualifying B1 activates, but does not validate, a separate fixed-four-robot
payload-towing surface. Four ground robots pull a shared sled around a closed
course. The external supervisory/communication period is `k`; each boundary
reveals a finite friction/slope forecast word, relative pose/velocity, tether
tension, payload yaw, battery, and the complete low-level controller integrator
state. The high-level shared policy selects held tension/heading-rate setpoints.
The strongest comparator remains an identical free duration model; train
durations, held-out durations, noncommuting high/low-friction order twins,
label-sham, exact action hold, matched endpoint supervision, and oracle-headroom
audit receive a new prospectively frozen card. Outcomes are payload progress,
tension balance, tracking, energy, near-tip/collision events, messages, and
latency. No B1 number or margin transfers.

Only a qualifying second-surface result activates a UAV simulator card. The
prospective mapping is:

| Convoy object | UAV simulator object |
|---|---|
| ring slot error and velocity | relative loiter/formation pose and velocity |
| fixed-degree gaps | neighbor separation and relay geometry |
| visible REAL context word | forecast wind-shear/link-margin sectors |
| SHAM labels | forecast-label control with identical physics |
| held `LEFT/COAST/RIGHT` | held airspeed, heading-rate, or acceleration setpoint |
| external `k` | commanded high-level control/communication hold period |
| composition error | terminal pose/link and cumulative reward rollout error |
| clipping/collision | geofence, separation, and control-envelope excursion |

The UAV state must include pose, velocity, relative geometry, link estimate,
wind estimate/forecast, and every low-level integrator or filter state needed
for Markov composition. Candidate high-level skills may be
`TRACK`, `TRANSIT`, `RELAY`, and `HOLD`, but one selected command must remain
unchanged until the external boundary; a task requiring mid-action abort is
outside this family. The simulator must preserve an identical-information
NOCOMP arm, exact preview boundary, explicit energy/progress/separation/link
reward, and real replanning/communication cost. This is a path, not UAV
evidence.

## Root-to-CM construction boundary

If Root later relays this object after exact-revision Pro `CLOSED` and EM
intake, CM may construct only `SCDMP-B1-SCIENCE-20260812-01`, bind its source
and configuration, and assess exact technical conformance. CM and Operator own
code, environment, tests only when separately authorized, execution, resource
facts, and retained-result correctness. They do not change word support,
endpoint weights, margins, inference, or interpretation.

The prospective ceiling is one CPU, no GPU, at most 2 GiB resident memory,
90 minutes wall time, at most 75,000 trainable parameters per arm, and exactly
1,000 optimizer updates per arm/seed. Exact conformance requires the nominal
26,148 trainable parameters; 75,000 is only the resource-abort ceiling and does
not permit architectural additions. The environment-microstep ledger is:

```text
common training corpus: 8*192*64                       =   98,304
scored evaluation:     8*2*6*32*240                   =  737,280
common audit rollouts: 8*81*(32*6 + 32*12)            =  373,248
registered maximum                                            1,208,832
```

The ledger categories are not interchangeable and do not include neural
forward passes. A resource overrun or missing complete result is
nonidentifying, not an algorithm result. The result packet must report all
seed/regime/class effects, actual activity/support denominators, model and
actor first stages, REAL/SHAM order checks, oracle headroom/regret, resource
counts, anomalies, and whether question-relevant output exists.
