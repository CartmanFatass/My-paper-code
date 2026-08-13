# Semigroup-Consistent Duration Model Policy B1 science card

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-B1
revision=SCDMP-B1-SCIENCE-20260812-05
supersedes_revision=SCDMP-B1-SCIENCE-20260812-04_PRO_CLOSED
owner=EM_semigroup_consistent_duration_model_policy
source_inspiration=SCDMP-VK-FAMILY-CUT-01
source_is_evidence=false
artifact_status=FROZEN
scientific_activity_started=false
production_authorized=false
chatgpt_external_pro_math_closure=CLOSED_ON_EXACT_V5
em_closure_intake=accepted_without_science_change
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
`SCDMP-B1-SCIENCE-20260812-05`. V1 and v2 were `PREPARED_NOT_SENT`; v3 received
`REVISION_REQUIRED`; and v4 received literal same-conversation Pro `CLOSED`
plus same-direction EM intake before question-relevant activity. During v4
construction, CM correctly returned one unresolved science-bearing
reproducibility ambiguity: the fit-set standard deviations did not state their
denominator or exact reduction API. V5 prospectively supersedes v4, chooses the
population standard deviation of the complete registered fit-set target
population (`ddof=0`), and freezes its enumeration, NumPy API, floor, one-time
float32 cast, sharing and every downstream standardized use. It changes no DGP,
arm, information, architecture, sample, loss term or weight, numeric gate,
estimand, branch, activity boundary, RNG stream, resource ledger, claim ceiling,
second-surface rule, or UAV boundary. No result or runtime value informed this
choice. A change to its DGP, observation, word law, arms, losses, scaling law,
activity rule, training/evaluation split, estimands, margins, inference,
interpretation, or resources creates a new complete revision.

Because the denominator affects the optimized objective and thresholded
standardized observables, v4 closure did not transfer automatically. Exact v5
has now received literal same-conversation Pro `CLOSED`, and this EM has
accepted that ruling without a science-bearing change. The mathematical and
causal closure boundary is complete for v5. This does not authorize CM
construction, technical acceptance, execution, or production; Root retains
relay and sequencing authority.

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

### Exact raw-bit and non-audit reset law

Every science-bearing pseudo-random stream uses NumPy `1.26.3` and exactly the
bit-generator API `numpy.random.PCG64(seed).random_raw()`. One call returns one
unsigned 64-bit integer. The implementation must not wrap the bit generator in
`Generator` and must not call `default_rng`, `random`, `uniform`, `integers`,
or `standard_normal`. Define, with integer shift before the float64 cast,

```text
U0(x)   = float64(x >> 11) * 2^-53
Umid(x) = (float64(x >> 11) + 0.5) * 2^-53.
```

`U0` is the sole uniform transform for environment resets and Xavier draws.
For the initialization-only standard-normal transform, two consecutive raw
words `(x,y)` produce, in this order,

```text
radius = numpy.sqrt(-2.0*numpy.log(Umid(x)))
angle  = 2.0*pi64*Umid(y)
Z0     = radius*numpy.cos(angle)
Z1     = radius*numpy.sin(angle),
pi64   = float.fromhex('0x1.921fb54442d18p+1').
```

All functions in this transform are the float64 ufuncs of NumPy `1.26.3`.
No spare normal is cached across a recurrent-gate matrix.

At every non-audit episode reset, consume exactly nine raw words in this order:

```text
raw_q,
raw_e1,raw_e2,raw_e3,raw_e4,
raw_v1,raw_v2,raw_v3,raw_v4.
```

Set `q_rotation=raw_q mod 4` and left-rotate
`q_base=(+1,-1,+1,-1)` by that slot count. In slot order `i=1,...,4`, compute

```text
e_i_raw = -0.20 + 0.40*U0(raw_ei)
v_i     = +0.10 + 0.20*U0(raw_vi)
mean_e  = (((e_1_raw+e_2_raw)+e_3_raw)+e_4_raw)/4.0
e_i     = e_i_raw-mean_e.
```

These operations and the deterministic host dynamics/reward are IEEE float64;
only the normalized neural input is cast once to float32. No reset variable is
interleaved, vectorized through another RNG API, or redrawn. Primitive dynamics
have no random draw.

Science-bearing streams are disjoint. Corpus generation instantiates
`PCG64(730000+algorithm_seed)` once, then consumes resets in duration order
`k=2,4,8` and episode-index order `0,...,63` within each duration. Scored regime
`r` instantiates `PCG64(750000+1000*algorithm_seed+r)` and consumes episode
resets `0,...,31`; regime indices follow the printed evaluation order below.
Words, classes, actions, and switches use the deterministic schedules in this
card and consume no raw word. Paired arms reuse the resulting episode object
and never advance a separate stream. The audit panel has no random draw and
uses its exact arithmetic map below. Actions never alter later word choices.

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

The stated input widths include `k/12`. Every model tensor is IEEE float32.
Initialization uses one NumPy 1.26.3 `PCG64(710000+algorithm_seed)` object and
calls only its `random_raw()` method under the exact `U0` and Box-Muller
transforms defined above. It follows this immutable traversal: node-encoder
linear 1, node-encoder linear 2,
action-embedding linear, word-GRU gates, `F` linear 1/2/3, `G_node` linear
1/2, then `G_edge` linear 1/2. Within a linear weight, row-major order consumes
one raw word per element, maps it with `U0`, then applies
`weight=-bound+2*bound*U0(raw)` with
`bound=(5/3)*numpy.sqrt(6.0/(fan_in+fan_out))`, all in NumPy float64, and casts
each completed array once to float32. Every
non-GRU bias is zero and consumes no draw.

The word encoder is the reset-after GRU with gate order `r,z,n`:

```text
r = sigmoid(W_ir*x + b_ir + W_hr*h + b_hr)
z = sigmoid(W_iz*x + b_iz + W_hz*h + b_hz)
n = tanh(W_in*x + b_in + r*(W_hn*h + b_hn))
h_next = (1-z)*n + z*h.
```

Its three `32 x 5` input-gate slices are initialized, in `r,z,n` order, by the
same raw-word Xavier rule. For each recurrent gate in `r,z,n` order, fill one
row-major `32 x 32` float64 matrix `M` using consecutive Box-Muller pairs
`Z0,Z1` in that order; because 1,024 is even, no normal remains. Compute
`Q,R=numpy.linalg.qr(M,mode='reduced')` under NumPy `1.26.3`. Set `s_j=+1`
when `R[j,j]>=0` and `s_j=-1` otherwise and define
`Q_plus=Q*numpy.asarray(s)[None,:]`. This removes QR column-sign ambiguity,
including the `R[j,j]=0` convention. `Q_plus` is cast once to float32 and
assigned to the corresponding recurrent slice. Both GRU bias vectors are zero.
Paired arms use byte-identical tensors from this one traversal. No library-
default parameter reset may run afterward. There is no per-`k` head, duration
lookup table, clipping of `k`, dropout, arm flag, privileged state, or raw
target-word cache.

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
`O(k*C + N*A^3*C)` per boundary and `O(N*A^2+N*C)` memory for `A=3`, model
width constant `C`, and word length `k`; the `A^3` factor is the exact-cycle
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

One training-bank row is one complete four-agent true-boundary witness, never a
node or edge row. It contains the boundary's full joint physical state, full
joint held action, complete word, terminal joint physical state, four node
cumulative rewards, and four ordered-cycle edge cumulative rewards. Endpoint
bank `E_tau` contains exactly the fit-set boundaries from episodes whose
external duration is `tau`, for `tau in {2,4,8}`; its targets use the complete
held interval. Composition bank `C_22` contains the same complete rows as
`E_4`, split after two primitive steps, and `C_44` contains the same complete
rows as `E_8`, split after four. The intermediate state and suffix word are
stored in each composition row. No row crosses a true boundary, episode reset,
padding, or duration switch.

For each algorithm seed separately, freeze exactly four fit-set scales before
optimization: `s_e`, `s_v`, `s_node`, and `s_edge`. Paired arms share the same
four values. Each scale uses only target atoms from the complete fit-set
endpoint banks `E_2,E_4,E_8`, never input states, composition-bank duplicate
views, support-probe rows, audit rows, scored evaluation, model predictions, or
either arm's outputs. Enumerate target atoms into four C-contiguous one-
dimensional arrays in duration order `2,4,8`, then episode index `0,...,47`,
true-boundary index ascending, and slot `1,...,4`. For `e` and `v`, append the
true terminal coordinate for that slot; for node reward, append that slot's
true complete-word cumulative node reward; for edge reward, append the true
complete-word cumulative reward of directed edge `i -> i+1` in slot order.

There are `48*(32+16+8)=2,688` complete endpoint rows and therefore exactly
`n=2,688*4=10,752` float64 atoms in each of the four arrays. Raw pooling is
intentional: do not average bank variances, reweight durations, duplicate
`E_4/E_8` through `C_22/C_44`, pool seeds, or apply Bessel correction. On NumPy
`1.26.3`, for each array `x` execute the mathematical equivalent of exactly:

```text
x64     = numpy.asarray(x, dtype=numpy.float64, order='C')
sigma64 = numpy.std(x64, axis=None, dtype=numpy.float64, ddof=0)
scale64 = numpy.maximum(sigma64, numpy.float64(1e-3))
scale32 = numpy.float32(scale64)
```

Thus the variance denominator is exactly `n`, not `n-1`; `numpy.nanstd`,
`torch.std`, an online estimator, a bankwise reduction, or another `correction`
is not equivalent. Every source atom is finite by construction, so no NaN-
skipping rule exists. The four `scale32` values are copied once as shared scalar
float32 model constants before update-zero materialization, never updated, and
used only as divisors: no fit-set mean is subtracted from an error or neural
input. The existing explicit neural inputs `[e/1.5,v/0.6,q]` remain unchanged.

These four scalers govern every occurrence of a standardized physical endpoint,
node-reward, or edge-reward residual: `bar(delta_F)`, `bar(delta_Gn)`, and
`bar(delta_Ge)` in `L_endpoint` and `L_comp`; update-zero `D_comp_init`; the
untouched train-support composite RMSE; every REAL, SHAM, or pooled
`D_comp_m_*`/`Delta_comp_REAL`; and every REAL, SHAM, or pooled
`E_pred_m_*`/`Delta_pred_REAL`. A reporting-only residual explicitly printed in
standardized units uses the same corresponding scale; a raw-coordinate or raw-
reward report stays raw. No task-return, failure, oracle-action, oracle-regret,
state-support, output-variance-ratio, reversal, action-disagreement,
candidate-score, `Delta_J`, `Delta_task`, `Delta_fail`, `Delta_rob`,
`Delta_spec`, confidence-bound, or resource quantity uses these fit-set
scalers unless its definition above explicitly contains a standardized model
residual. There is no duration-, class-, word-, arm-, or evaluation-specific
scaler.

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
updates. Within each of `E_2,E_4,E_8,C_22,C_44`, rows are partitioned into the
eight strata `(REAL,word_row_0..3)` then `(SHAM,word_row_0..3)`. A stratum's
canonical order is `(episode_index,boundary_index)` ascending.

One `PCG64(720000+algorithm_seed)` stream constructs exactly one permutation
per bank-stratum in bank order `E_2,E_4,E_8,C_22,C_44` and then the printed
stratum order. A permutation is the following exact Fisher-Yates operation.
For `j=m-1,...,1`, call this batch stream's `random_raw()` until
`raw < 2^64-(2^64 mod (j+1))`, set `h=raw mod (j+1)`, and swap positions
`j,h`. Each bank-stratum has its own cursor through that one permutation; it
wraps to position zero without reshuffling.

At every update, batch assembly visits banks in the printed order, then strata
in the printed order, and takes the next eight complete rows from each cursor.
Thus an update has 64 complete rows from each endpoint bank (192 endpoint rows)
and 64 from each composition bank (128 composition rows). Loss first averages
nodes or edges within a complete row, then rows within a stratum, the eight
strata within a bank, and finally the three endpoint banks or two composition
banks equally. No `node_or_edge` item exists in a permutation key. Paired arms
use the same locked rows; each update evaluates and steps SCDMP first and
NOCOMP second with separate Adam states. There is no stochastic layer, so this
fixed arm order changes no model RNG. The final update is the only checkpoint;
there is no early stop, validation selection, hyperparameter search, or
arm-specific repair.

## Activity, support, and oracle headroom

Before optimization, materialize update zero using the exact bank/cursor law
and verify that its endpoint rows contain all three training durations and its
composition rows contain both pair types, both REAL and SHAM, all four word
rows, at least two distinct joint actions, and every scalar skill. At the paired
initial checkpoint, report `D_comp_init` on these exact composition rows; it is
a reproducibility diagnostic defined as `sqrt(L_comp)` before either optimizer
has stepped, not a decision gate, and may not change any threshold.
Question-relevant scientific activity begins when the SCDMP forward
pass for optimizer update zero is invoked on that locked, conforming batch.
Before that exact call, construction, corpus/bank creation, initialization,
batch materialization, and diagnostic evaluation are not scientific activity.
Report the complete-row denominators and whether every condition held.

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
3. On the common untouched audit panel, the 32 REAL reversal twins per seed
   have median across
   states of `max_u |S_true(w,u)/k-S_true(reverse(w),u)/k| >= 0.01`, where
   `S_true=R_true+H(y_true_terminal)`, and the constrained one-word oracle
   action differs on at least 10% of twins.
   SHAM reversal twins must agree to numerical tolerance `1e-10`. This proves
   that order matters physically rather than merely by label.
4. The NOCOMP actor has recoverable held-out REAL headroom. For seed `s`, use
   exactly its 64 REAL word-state instances and define `h_s` as the fraction on
   which NOCOMP's selected action is at least `0.02` normalized reward per
   primitive step below the exact constrained one-word oracle under the same
   `R+H` score, and `r_s` as its mean per-step regret over all 64 instances.
   The gate is `mean_s(h_s)>=0.20` and `mean_s(r_s)>=0.01`. Corresponding SHAM
   and pooled-128 values are controls or descriptive diagnostics only. The
   oracle receives exactly the same state, word, held-action constraint, and
   81-action set; it rolls the known DGP only for audit and is never an actor
   input or training target. It enumerates joint actions in the same slotwise
   lexicographic order `LEFT < COAST < RIGHT` as the learned actor and retains
   the first exact float64 score maximum, with no tolerance-based tie. The REAL
   reversal gate compares these uniquely selected oracle actions.
5. The arithmetic mean across seeds of NOCOMP's REAL-only post-training
   composite held-out defect `D_comp_NOCOMP_REAL` defined below is at least
   `0.05` standardized units. For each seed let `a_s` be the fraction of its 64
   REAL word-state instances on which SCDMP and NOCOMP select different joint
   actions; the actor gate is `mean_s(a_s)>=0.10`. These are representation and
   actor first stages, not outcome claims. Pooled defect is descriptive and
   cannot satisfy this gate.
6. Neither arm has nonfinite outputs; no more than 1% of audit predictions hit
   an `F` output bound. On the untouched train-support probe, each arm's
   composite standardized endpoint/node-reward/edge-reward RMSE is at most
   `0.35`. On the 64 REAL target word-state instances and their 81-action
   panels, the across-seed mean `E_pred_NOCOMP_REAL` is at most `0.75`; a
   composition-specific or convoy-negative claim additionally requires the
   across-seed mean `E_pred_SCDMP_REAL` to be at most `0.50`. Pooled and SHAM
   target RMSE remain reported controls and cannot establish competence. For
   each predicted physical coordinate, SCDMP audit variance is
   between `0.25` and `4.0` times the corresponding true-terminal variance.
   For each seed let `b_s` be the fraction of its 64 REAL word-state instances
   whose predicted best-minus-worst candidate score range is at least `0.02*k`;
   require `mean_s(b_s)>=0.20`. Lower composition defect with
   collapsed physical outputs, inaccurate endpoints, or an actor-insensitive
   score is not a valid mechanism first stage.

The audit panel is common and evaluation-independent. For every seed it has 32
`k=6` and 32 `k=12` boundary states. Let duration block `d=0` mean `k=6` and
`d=1` mean `k=12`; let local index `a=0,...,31` and global audit index
`g=32*d+a`. Define class `c=floor(a/16)` (`0=REAL,1=SHAM`), target word row
`w=floor((a mod 16)/4)`, cyclic slot offset `r=a mod 4`, and severity
`s=(w+r) mod 2` (`0=MILD,1=SEVERE`). This crosses every class with every word
row and every slot offset once; severity is two/two within each class-word cell
and is also balanced within every class-offset marginal.

The base reset states are

```text
MILD:   e=(-0.06,+0.02,+0.06,-0.02), v=(0.17,0.23,0.19,0.21)
SEVERE: e=(-0.18,+0.06,+0.18,-0.06), v=(0.10,0.30,0.14,0.26)
q_base=(+1,-1,+1,-1).
```

Apply the same left cyclic rotation by `r` slots to `e`, `v`, and `q_base`.
Offsets zero/two and one/three intentionally repeat the two physical alternating
`q` patterns; the rotated physical initial states remain separately registered.
There are no audit reset draws and no post hoc severity labels.

Each audit reset is advanced for exactly 48 primitive steps at
training-supported `k=4`, giving 12 held-action boundaries. At warm-up boundary
`b=0,...,11`, use class `c`, the `k=4` word-table row `(w+b) mod 4`, and
base-three joint-action index `(g+31*algorithm_seed+b) mod 81`, with the same
slot/digit convention as the corpus. The resulting step-48 physical state is
the shared target state. Pair it with target-table word row `w` and with the
literal token-order reverse of that word. For each of the two words, roll all
81 joint actions from separately cloned copies of the identical target state.
The original and reverse rollouts jointly define each REAL/SHAM reversal twin;
neither is reconstructed from the other. The panel is opened only after both
final checkpoints, and its outcomes never select a checkpoint, threshold, or
revision. The provisional CM analytic probe values are not evidence and are
not inputs to any v5 threshold.

Audit denominators are immutable: 64 physical states and 64 reversal twins per
seed; 128 word-state instances after counting target and reverse separately;
and `128*81` word-state-action rollouts. Coordinate-support conditions use the
64 physical states and reversal/order conditions use 64 twins. The
conclusion-bearing oracle headroom, composition defect, true prediction error,
and actor disagreement use exactly the 64 REAL word-state instances and their
`64*81` action panels. The corresponding 64 SHAM instances and pooled 128
instances are controls or descriptive diagnostics. Output-bound/variance and
candidate-score-sensitivity checks retain their stated denominators.

Failure of activity, support, REAL order effect, SHAM identity, or REAL-specific
oracle headroom makes the B1 result nonidentifying for its positive-mechanism
and convoy-negative routes, regardless of pooled headroom. It is not evidence
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

For each seed `s`, average paired episode differences within each dynamics
class and regime before across-seed inference. Episodes are not independent
training replicates. Let `d_J_s(r)` and `d_fail_s(r)` be the REAL-class means
for each of all six scored regimes; higher values favor SCDMP. Define

```text
Delta_J(r) = mean_s d_J_s(r)
Delta_task = mean over the four target r of Delta_J(r)

Gap_m_s = mean(J_m | REAL, k in {4,8}, seed s)
          -mean(J_m | REAL, four target regimes, seed s)
Delta_rob = mean_s(Gap_NOCOMP_s-Gap_SCDMP_s)

Delta_fail(r) = mean_s d_fail_s(r)

D_comp_m_REAL_s = mean(
  RMS_REAL_standardized_F_cocycle_defect,
  RMS_REAL_standardized_node_reward_cocycle_defect,
  RMS_REAL_standardized_edge_reward_cocycle_defect)
D_comp_m_REAL = mean_s D_comp_m_REAL_s
Delta_comp_REAL = mean_s(D_comp_NOCOMP_REAL_s-D_comp_SCDMP_REAL_s)

E_pred_m_REAL_s = mean REAL standardized true
                      endpoint/node-reward/edge-reward RMSE
E_pred_m_REAL = mean_s E_pred_m_REAL_s
Delta_pred_REAL = mean_s(E_pred_NOCOMP_REAL_s-E_pred_SCDMP_REAL_s)

Delta_spec = mean_s[(mean over target r of d_J_s_REAL(r))
                    -(mean over target r of d_J_s_SHAM(r))].
```

For each seed and arm, each `D_comp_m_REAL_s` component uses all 64 REAL
word-state instances, all 81 joint actions, and both legal target
decompositions (`2+4`/`4+2` for six and `4+8`/`8+4` for twelve). Within a
component, standardized squared residuals are averaged equally over the two
decompositions, word-state instances, joint actions, and physical coordinates
or four node/edge outputs, then square-rooted; the three component RMS values
are averaged equally. `E_pred_m_REAL_s` applies the same equal weighting to the
direct whole-word prediction against the true endpoint and true cumulative
node/edge rewards, without a decomposition index. Every paired interval for
`Delta_comp_REAL` or `Delta_pred_REAL` uses the eight seed-level arm
differences printed above. Corresponding SHAM-only and pooled-128 metrics are
reported under the same reduction but are descriptive controls; they cannot
satisfy a conclusion-bearing REAL first stage.

The four prespecified REAL word subgroups are the four registered initial word
rows `j=0,...,3`. For seed `s`, define

```text
d_word_s(j) = (1/4) * sum over the four target regimes r of
              mean[J_SCDMP-J_NOCOMP | REAL, seed s, r,
                   initial word row j].
Delta_J_word(j) = mean_s d_word_s(j).
```

Each inner mean has exactly four scored episodes. The four prespecified target
duration/regime subgroups are the already defined `Delta_J(r)` for fixed six,
fixed twelve, `6->12`, and `12->6`; each seed-level mean has exactly 16 REAL
episodes. These eight subgroup estimands and no post hoc subdivision are
covered by the convoy-negative conclusion.

Also report direct-versus-recursive prediction disagreement, oracle regret,
action disagreement, word-reversal effects, per-word results, collision
probability, minimum-gap CVaR at 10%, position/velocity error, clipping, energy
proxy, action changes, messages, and latency. Occupancy, chosen actions, and
model confidence are descendants and are never conditioned away in the
primary effect.

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

A composition-specific mechanism attribution additionally requires one-sided
95% seed-level lower bounds above `0.10` for `Delta_comp_REAL`, above `0.05`
for `Delta_pred_REAL`, above `0.010` for `Delta_rob`, and above `0.005` for
`Delta_spec`, plus every activity/support/REAL-headroom/REAL-defect/
true-prediction-competence/actor-first-stage condition. These replace the
pooled composition and prediction quantities in every conclusion-bearing
gate; no numeric threshold is relaxed. They are not extra opportunities for a
generic performance claim. Since there is no separately trained
adjacency-shuffled-loss arm, even this branch attributes the bounded
composition-loss package and its order-selective signature; it does not prove
unique mediation by the mathematically correct cocycle.

The adverse-effect family contains exactly 12 REAL seed-level estimands: the
six `Delta_J(r)` values and six `Delta_fail(r)` values for the printed scored
regime order. For each estimand use a one-sided Bonferroni simultaneous upper
bound with per-estimand confidence `1-0.05/12`, eight paired seed values, and
`df=7`. Material reward harm is established when any reward upper bound is
strictly below `-0.005` normalized reward per primitive step. Material failure
harm is established when any failure upper bound is strictly below `-0.05`.
These margins reuse the registered reward non-harm and failure-robustness
magnitudes; they do not create a weaker route.

## Frozen interpretation branches

Outcome precedence is exact. Failure of question-relevant activity, technical
or resource conformance, no-leakage, complete output, state support, physical
REAL order, SHAM identity, or finite/output-validity conditions invokes branch
7 and precludes every other claim. For a result passing those core conditions,
evaluate branch 6 first; it overrides every positive, regularity, or
sufficiency label. If no adverse bound fires and a direct-value route passes,
use branch 1 when all mechanism gates pass and branch 2 otherwise. If neither
direct-value route passes, absent REAL oracle headroom or a sub-floor REAL
NOCOMP defect invokes branch 4 before any convoy-negative reading. Otherwise
apply branch 3 and its stronger deletion rule when eligible. Branch 5 is an
attribution modifier: it can narrow a valid direct package result to branch 2,
but can never create a positive or negative result. Any remaining missing gate
invokes branch 7. This precedence prevents a favorable average from hiding a
registered harmful regime and prevents SHAM-only headroom from licensing a
REAL negative claim.

1. **Direct variable-`k` value with composition signature.** At least one
   direct-value route passes, all validity and non-harm conditions hold, and
   all composition-specific gates pass. Retain SCDMP as a promising finite-budget
   variable-`k` algorithm on this deterministic forecast-visible surface.
2. **Package value without algebraic attribution.** A direct-value route passes
   but composition, prediction, REAL-versus-SHAM, or actor first stage fails.
   Report only the bounded learned-package result. Do not claim the semigroup
   mechanism; any successor aimed at that attribution is a new revision.
3. **Model regularity without decision value.** SCDMP reduces REAL composition
   and true-prediction error, but neither direct-value route passes. The loss
   shapes the model without demonstrated task value. Apply the convoy-treatment
   deletion rule below if its stronger conditions hold; otherwise make no
   positive claim.
4. **Free model sufficient.** NOCOMP lacks the registered REAL oracle headroom
   or its REAL composition defect is below the registered `0.05` first-stage
   floor. Pooled or SHAM headroom cannot override this branch. The toy cannot
   distinguish whether explicit consistency would help in an order-active
   setting where the free model has room to improve. Do not tune or reinterpret
   the null.
5. **Shortcut/generic regularization.** Any apparent gain is equally large on
   SHAM labels, lacks an order-selective signature despite verified physical
   order activity, accompanies collapsed endpoints, or lacks action
   disagreement. Delete the order-selective causal story; at most retain the
   package effect if its primary route remains valid.
6. **Adverse effect.** At least one of the exact 12 simultaneous upper bounds
   crosses its frozen negative margin. Reject this exact treatment on the
   convoy surface, name every triggering reward/failure regime and its bound,
   and do not issue a positive or second-surface activation claim even if an
   average direct-value route would otherwise pass.
7. **Nonidentifying.** Activity, support, headroom, resource, leakage, complete
   output, or deterministic-cocycle conditions fail. No positive, negative,
   null, equivalence, or convoy-treatment deletion conclusion is available.

### Prospective convoy-treatment deletion condition

Delete further investment in this exact SCDMP B1 treatment on the registered
convoy DGP, duration split, architecture, and budget if and only if all
activity, technical validity, leakage, state support, physical order, SHAM
identity, REAL oracle headroom, output-variance, and REAL actor-first-stage
conditions hold; `mean_s D_comp_NOCOMP_REAL_s>=0.05`; the REAL
true-prediction competence ceilings hold; the one-sided 95% lower bound for
`Delta_comp_REAL` exceeds `0.10`; and the one-sided 95% lower bound for
`Delta_pred_REAL` exceeds `0.05`; yet all of the following no-use conditions
hold:

1. for every one of the four target regimes, the one-sided 95% upper bound for
   `Delta_J(r)` is below `0.010` and the corresponding upper bound for
   `Delta_fail(r)` is below `0.03`;
2. the one-sided 95% upper bound for `Delta_spec` is below `0.005`; and
3. for every one of the four prespecified REAL initial-word-row estimands
   `Delta_J_word(j)`, the one-sided 95% upper bound is below `0.010`.

The four target-regime bounds are the prespecified duration/regime subgroup
bounds; together with the four word-row bounds they cover exactly the eight
subgroups defined above. Because the negative assertion is the intersection
that every covered effect is below its margin, requiring all one-sided 95%
upper-bound tests is an intersection-union rule and adds no multiplicity
opportunity. Absence of a lower-bound significance result is never evidence of
absence.

That outcome says a successfully imposed REAL composition and true-prediction
first stage has no registered minimum useful decision value on this exact
forecast-visible convoy treatment despite a competent-but-imperfect free
comparator. It does not scientifically delete the separately specified ground-
payload or UAV surfaces and does not transfer any negative threshold or
evidence to them. Root may separately decline to invest in those surfaces as a
portfolio decision, but that is not a B1 causal conclusion. If either REAL
composition or true-prediction first stage is absent, only this loss realization
lacks its required mechanism evidence; if REAL oracle headroom or support is
absent, the result is nonidentifying rather than convoy-negative. Wide intervals
are indeterminate and do not authorize a threshold change or automatic rerun.

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

A convoy-negative result can claim only that this exact SCDMP B1 treatment did
not provide the registered minimum useful decision value on this deterministic
convoy at the frozen budget despite REAL headroom and verified REAL composition
and true-prediction first stages. It cannot delete the ground-payload or UAV
surface, other stochastic or partially observed duration models, or every
semigroup-consistent algorithm.

## Second surface and UAV bridge

A qualifying B1 means branch 1 only. It activates, but does not validate, a
separate fixed-four-robot payload-towing surface. Branches 2--7 do not activate
this path; any later investment after them is a new Root portfolio decision
without transferred B1 evidence. Four ground robots pull a shared sled around
a closed course. The external supervisory/communication period is `k`; each
boundary reveals a finite friction/slope forecast word, relative pose/velocity, tether
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
intake, CM may construct only `SCDMP-B1-SCIENCE-20260812-05`, bind its source
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
common audit warm-up:  8*64*48                         =   24,576
audit target words:    8*81*(32*6 + 32*12)            =  373,248
audit reverse twins:   8*81*(32*6 + 32*12)            =  373,248
registered maximum                                            1,606,656
```

The ledger categories are not interchangeable and do not include neural
forward passes. A resource overrun or missing complete result is
nonidentifying, not an algorithm result. The result packet must report all
seed/regime/class effects, actual activity/support denominators, model and
actor first stages, REAL/SHAM order checks, oracle headroom/regret, resource
counts, anomalies, and whether question-relevant output exists.
