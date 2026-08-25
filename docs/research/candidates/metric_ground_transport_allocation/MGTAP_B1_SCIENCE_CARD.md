# MGTAP B1 science card

```text
direction=metric_ground_transport_allocation
revision=MGTAP-B1-SCIENCE-20260813-04
owner=EM_metric_ground_transport_allocation
object=result-blind direct-variable-N finite-budget discriminator
scientific_activity_started=false
mathematical_closure=CLOSED_EXACT_REVISION_04_OWNER_INTAKE_COMPLETE
cm_static_audit=revision_04_ACCEPTED
cm_release=construction_planning_only
construction_authorization=none
compute_authorization=none
chatgpt_external_pro=revision_04_CLOSED_same_conversation
external_gemini=revision_02_PREPARED_NOT_SENT_ROOT_WITHHELD
```

## Conclusion first

MGTAP is a meaning-complete and answer-changing direct variable-`N` candidate.
Exact revision 04 has literal same-conversation ChatGPT External Pro
mathematical closure, owner intake, and same-direction CM static constructibility
acceptance. It is released only for CM construction planning and Root's next
authorization decision. B1 asks whether a
useful finite-budget optimization and inductive bias for a capacity-feasible
agent-to-task coupling policy trained once at `N={4,8}` and deployed unchanged
at held-out `N={6,12}`.

The primary comparator is not a smaller policy. `FREE-EDGE-FEASIBLE` has the
same 60 trainable scalars, observations, full free-edge score class, legal
couplings, autoregressive decoder, action support, training examples,
hyperparameter-search budget, updates, optimizer, communication, and
output-relevant work. Its dense orthogonal edge map is an unstructured
coordinate system. The treatment replaces that map with an invertible
ground-neighborhood map. For every fixed binding regime the two deployed
hypothesis classes are exactly equal, so the comparator both nests and is
nested by the treatment. Any treatment advantage can therefore support only a
finite-budget metric-aligned optimization/regularization benefit, never a
larger reachable policy class.

The cheapest discriminator crosses a metric-binding transposition with
matched demand placements. The binding placement uses the two task endpoints
whose coordinates are transposed; the inert negative-control placement uses
the two interior tasks whose own displayed coordinates do not move. The dense
metric map can nevertheless change interior-task logits indirectly, so inert
equality is an empirical causal gate rather than a structural guarantee. Both
placements have the same demand multiset. A metric-specific result
requires held-out-size value over `FREE-EDGE-FEASIBLE`, attenuation under the
binding cut, a legal oracle-aligned coupling change in the binding placement,
no corresponding action change in the inert placement, exact identity
permutation, common oracle headroom, and complete useful-work evidence.

No source, provider, implementation, run, or result establishes that MGTAP
works. No provider send, construction, test, compute, production, or Git action
is authorized by this card.

## Five-line science card

- **Question.** Does a correct public ground metric improve finite-budget
  held-out-roster allocation performance or size robustness for one unchanged
  shared coupling policy relative to an exactly equal-class free-edge policy?
- **Treatment.** `METRIC-GROUND`: a full free-edge linear actor whose eight
  role-task score channels are expressed through an invertible dense map built
  from observable capability/task ground neighborhoods.
- **Primary comparator.** `FREE-EDGE-FEASIBLE`: the same actor expressed through
  a dense orthogonal nonmetric map, with identical action, feasibility,
  information, parameters, tuning, samples, optimization, decoder, and useful
  work. `PUBLIC-LOAD-SOFTMAX` is diagnostic only.
- **Observable.** Paired normalized two-epoch return at `N={6,12}`, size
  degradation, direct binding-value benefit, inert-value equivalence, oracle-aligned coupling
  response, exact identity permutation, oracle headroom, and atomic
  coupling/work ledgers.
- **Strongest alternative and ceiling.** Even a qualifying result is a
  finite-training-budget conditioning or regularization benefit of the correct
  metric on this centralized two-role/four-task toy. It is not superior policy
  expressivity, general optimal transport, arbitrary `N`, churn, decentralized
  communication, task generalization, or UAV value.

## 1. Source provenance and claim boundary

The local corpus is inspiration and a warning boundary only.

- `P18-CL001` supplies the definition-level idea of a coupling under a chosen
  ground cost. `P18-CL002` suggests resource management as a prospective
  OT--MARL interface. `P18-CL005/006` state the computational and evidence
  limits: the position paper supplies no theorem, benchmark, sample size, or
  held-out-`N` result. `P18-CL007` is a curator proposal to compare a specified
  allocator with a matched non-OT baseline under fixed cost, intervention, and
  compute; it is not evidence.
- `B03-CL001/006/008` motivate declaring the local/history/communication
  information set explicitly. B1 instead declares a centralized public
  allocator and makes no decentralized-execution or UAV result claim.
  `B03-CL007` warns that solving separate instances at different `N` is not one
  policy generalization; B1 freezes one checkpoint across all sizes.
- `P16-CL001` is an existential shared-parameter counterexample, not a general
  claim against sharing. B1 therefore keeps decision-relevant capability and
  role tokens observable. `P16-CL006` warns that within-game update theory does
  not establish cross-`N` generalization.

Repository-relative source locators are:

```text
docs/new-libs/corpus/papers/P18/claims.jsonl
docs/new-libs/corpus/papers/P18/overview.md
docs/new-libs/corpus/papers/B03/claims.jsonl
docs/new-libs/corpus/papers/P16/claims.jsonl
```

None supplies efficacy, a margin, a threshold, a treatment definition, or
authority for B1.

## 2. Frozen two-role, four-task allocation process

### 2.1 Roster sizes, supply, and observable roles

Every episode uses one even roster size. Training uses only

```text
N_train={4,8}
```

and evaluation adds

```text
N_heldout={6,12}.
```

Exactly `N/2` agents have public role/capability `LEFT` with coordinate
`x=0`, and exactly `N/2` have public role/capability `RIGHT` with coordinate
`x=6`. Every agent supplies exactly one indivisible service quantum at each of
two dispatch epochs. There is no agent ID, row embedding, persistent handle,
private health, hidden role, or role inference. Fresh row positions and fresh
decoder priority ranks are generated every decision and are not policy
features.

Raw extensive supply `N` and every raw task demand are retained. The actor may
also use frozen ratios such as `d_j/N`; this does not replace the extensive
records.

### 2.2 Tasks, true utility, and metric-binding regimes

There are four public semantic task tokens with true coordinates

\[
(z_1,z_2,z_3,z_4)=(0,2,4,6).
\]

The deterministic physical service utility of assigning role coordinate `x`
to task `j` is

\[
u(x,j)=1-\frac{|x-z_j|}{6}.
\]

Thus the true role-by-task utility table is

\[
U=\begin{bmatrix}
1&2/3&1/3&0\\
0&1/3&2/3&1
\end{bmatrix},
\]

with rows `LEFT,RIGHT`. This table is an environment law used by reward and the
offline nonanticipating oracle. The learned actor receives role/task semantics
and the displayed coordinate, not `U` or the oracle.

There are two separately trained binding regimes:

```text
INTACT: displayed coordinates (0,2,4,6)
CUT:    displayed coordinates (6,2,4,0)
```

`CUT` transposes only the displayed coordinates of semantic tasks 1 and 4.
Task tokens, true physical utility, demand, reward, feasibility, legal actions,
and all other fields remain attached to their original tasks. The coordinate
multiset and all pairwise-coordinate histograms are preserved. Both learned
arms are trained and evaluated wholly inside each regime. An evaluation-only
corruption is forbidden.

### 2.3 Two-epoch demand family

An episode is indexed by an ordered pair `(a,b)` of distinct task tokens and a
public epoch-2 load flag `L in {SLACK,OVERLOAD}`. Every training update contains
all 12 ordered pairs, both flags, and both training roster sizes exactly once.

Epoch 1 demand is

\[
d_{a,1}=d_{b,1}=N/2,\qquad d_{j,1}=0\quad(j\notin\{a,b\}).
\]

Epoch 2 is exogenous and public when that epoch begins:

\[
L=\mathrm{SLACK}:\quad d_{a,2}=N/2,\quad d_{j,2}=0\ (j\ne a),
\]

\[
L=\mathrm{OVERLOAD}:\quad d_{a,2}=d_{b,2}=N,\quad
d_{j,2}=0\ (j\notin\{a,b\}).
\]

`SLACK` has only `N/2` demanded quanta, so a filled plan has `N/2` semantic
idle quanta. `OVERLOAD` has `2N` demanded quanta, so a full-supply plan leaves
`N` semantic unmet quanta. Epoch 2 does not depend on epoch-1 action or reward;
B1 is a two-decision public workload-shift problem, not a delayed-credit,
forecasting, or hidden-demand claim.

The named matched discriminator placements are

```text
BINDING ordered pairs={(1,4),(4,1)}
INERT   ordered pairs={(2,3),(3,2)}.
```

Their epochwise demand multisets are identical. The cut changes the endpoint
ground binding used by `BINDING` but leaves both active `INERT` task coordinates
unchanged. The other eight ordered pairs remain in the overall deployment
mixture and support/robustness audit; they are not post-hoc subgroups.

`INERT` means that the demanded tasks' own displayed coordinates are unchanged,
not that every entry of the dense metric map is unchanged. The endpoint
transposition also permutes their cross-similarities to raw endpoint edge
channels, which can change task-2/3 logits after learning. This intended
spillover makes `INERT` a stringent empirical negative control: a
metric-specific reading is allowed only when its legal coupling and return
responses remain practically zero.

### 2.4 Legal coupling action and semantic slack

At epoch `e`, the integral joint action is `(X,iota,mu)` with

\[
X_{ij}\in\{0,1\},\quad \iota_i\in\{0,1\},\quad
\mu_j\in\mathbb Z_{\ge0},
\]

\[
\sum_{j=1}^4X_{ij}+\iota_i=1\quad\forall i,
\]

\[
\sum_{i=1}^NX_{ij}+\mu_j=d_{j,e}\quad\forall j.
\]

All 4N real agent--task edges are feasible. Task demand is a column capacity;
each agent has one indivisible assignment unit. `iota` is actual parked/idle
supply and `mu` is actual unserved demand, never dummy padding. Assigning every
agent idle and leaving all demand unmet proves the common feasible polytope is
nonempty for every size, epoch, placement, binding regime, and learned arm.

The fixed action budget is exactly `N` agent decisions at each epoch. No
fractional flow, rounding, per-decision LP/MILP, generalized assignment, or
arm-specific feasibility projection is part of B1.

### 2.5 Reward and normalized endpoint

For a legal action,

\[
R_e=\sum_{i,j}X_{ij}u(x_i,j)
-\frac1{20}\sum_i\iota_i
-\frac1{20}\sum_j\mu_j.
\]

The episode endpoint is

\[
Y=\frac{R_1+R_2}{2N}.
\]

Reward is deterministic conditional on the action. It provides no hidden
counterfactual table to the actor. The two epoch rewards are trained as two
separate public allocation decisions; no future return is credited to epoch 1.

### 2.6 Information and communication boundary

The deployed object is a centralized allocator. Before each decision it
receives:

- `N` unordered agent records `(public_role,public_capability,raw_supply=1)`;
- four unordered task records
  `(semantic_task_token,displayed_coordinate,raw_demand)`;
- the raw roster size and epoch indicator.

It receives no future load, oracle value, physical utility table, reward,
opaque identity, row position, other direction output, or held-out statistic.
The epoch-2 load is revealed only at epoch 2. There are no agent-to-agent
messages and no decentralized-execution claim.

The semantic input is `3N+14` scalar words per decision: three fields per agent,
three per task, and two globals. The decoder additionally consumes `N` fresh
unique priority ranks and `N` fresh action variates. Those random objects are
common for paired evaluation, move with the agent record under permutation,
and are not learned-policy inputs. Every learned arm has the same input,
output, and zero-message budget.

## 3. Shared full free-edge actor

### 3.1 Canonical edge and feature order

The eight observable real-edge classes are ordered

```text
(LEFT,1),(LEFT,2),(LEFT,3),(LEFT,4),
(RIGHT,1),(RIGHT,2),(RIGHT,3),(RIGHT,4).
```

For state `s`, define the common six-vector

\[
\phi(s)=\left[1,\frac{d_1}{N},\frac{d_2}{N},
\frac{d_3}{N},\frac{d_4}{N},e-1\right]^\top.
\]

Each arm has a real-edge parameter matrix `W in R^(8 x 6)` and an idle-score
matrix `V in R^(2 x 6)`. Let

\[
v(s)=W\phi(s),\qquad q^A(s)=B_Av(s),
\]

and let the role-specific idle score be

\[
q^0_r(s)=V_r\phi(s).
\]

`q^A_(r,j)` is expanded to every agent of role `r` and semantic task `j`.
Both real and idle logits are clipped to `[-6,6]` immediately before the common
decoder. The full factorial demand design must have feature rank six before
activity. Since every arm map below is invertible, every one of the 60 raw
trainable scalars affects a legal logit on the frozen support.

### 3.2 `METRIC-GROUND` edge map

For binding regime `C in {INTACT,CUT}`, let the displayed task coordinate be
`z_j^C` and define the observable edge descriptor

\[
y^C_{rj}=(x_r,z_j^C).
\]

For distinct edge classes `e,e'`, define

\[
S^C_{ee'}=2^{-\left(|x_r-x_{r'}|+|z_j^C-z_{j'}^C|\right)},
\qquad S^C_{ee}=0.
\]

Let

\[
m_C=\max_e\sum_{e'}S^C_{ee'},\qquad
G_C=S^C/m_C,
\]

and freeze

\[
B_{METRIC,C}=I_8+\frac12G_C.
\]

`G_C` is symmetric with maximum absolute row sum one, so all eigenvalues of
`B_METRIC,C` lie in `[1/2,3/2]`; the map is invertible. Nearby observable
capability/task edges share raw-coordinate influence. With ordinary isotropic
weight decay and finite SGD, this is a ground-correlated optimization/prior
geometry. It does not remove a feasible edge or a reachable score table.

### 3.3 `FREE-EDGE-FEASIBLE` edge map

The primary comparator uses the normalized dense Walsh--Hadamard matrix

\[
B_{FREE}=\frac1{\sqrt8}
\begin{bmatrix}
1&1&1&1&1&1&1&1\\
1&-1&1&-1&1&-1&1&-1\\
1&1&-1&-1&1&1&-1&-1\\
1&-1&-1&1&1&-1&-1&1\\
1&1&1&1&-1&-1&-1&-1\\
1&-1&1&-1&-1&1&-1&1\\
1&1&-1&-1&-1&-1&1&1\\
1&-1&-1&1&-1&1&1&-1
\end{bmatrix}.
\]

It is dense, orthogonal, independent of ground coordinates, and invertible.
All 64 products contribute to one or more output scores; it is not an identity
multiply, ignored head, or output-disconnected work pad. In raw-parameter
coordinates, isotropic weight decay remains isotropic.

For any fixed binding regime and any treatment parameters `(W_M,V_M)`, the
comparator reproduces every treatment logit for every legal state via

\[
W_F=B_{FREE}^{\top}B_{METRIC,C}W_M,\qquad V_F=V_M.
\]

Conversely, the treatment reproduces every comparator via

\[
W_M=B_{METRIC,C}^{-1}B_{FREE}W_F,\qquad V_M=V_F.
\]

Thus the primary policy classes are exactly equal, not merely nominally
parameter-matched. `FREE-EDGE-FEASIBLE` is the strongest bounded comparator for
the stated question: it concedes no representational deficit, feasibility
deficit, or information deficit. B1 tests the finite-budget consequences of
the correct versus nonmetric score coordinate system.

### 3.4 Exact tractable common decoder

A global Gibbs law over all transport plans is forbidden because its partition
function and exact sampler are not supplied by an assignment solver. Both arms
instead use the following fixed-length autoregressive decoder.

At each decision, sample one uniform random permutation of the `N` ephemeral
agent instances and attach its unique integer priority ranks `0,...,N-1` to the
complete agent records. Retain those `N` ranks. There is no priority tie or
identity/row fallback. Under a row replay, the rank moves with the complete
agent tuple. For priority step `t=1,...,N`:

1. Compute residual demand from preceding sampled assignments.
2. Form the categorical law in canonical semantic-token order
   `(task1,task2,task3,task4,IDLE)`, irrespective of current task presentation
   order. Presentation order never enters cumulative-probability order.
3. Mask a task exactly when its residual demand is zero. `IDLE` is never
   masked.
4. Apply softmax at temperature one to the clipped learned logits over the
   legal set, then mix `0.05` uniform mass over that same legal set:

   \[
   \pi=0.95\,\mathrm{softmax}(q)+0.05/|A_t|.
   \]
5. Sample by inverse CDF from the one retained action uniform for this priority
   rank and update residual demand.

The coupling log probability is the sum of the `N` retained categorical log
probabilities. The entropy term is the mean of the `N` categorical entropies.
The decoder always returns an integral legal coupling; `iota` is the sampled
idle indicator and `mu` is the final residual demand. Both arms perform exactly
`4N` real-edge score lookups, `N` idle lookups, `N` mask updates, and `N`
five-category decoder passes. No MAP solver, rounding law, or arm-specific
shortcut is used in training or learned evaluation.

The random priority construction is exchangeable. A row permutation that moves
the complete agent tuple and its priority rank/action uniform together must
inverse-permute the coupling exactly. Task presentation permutation moves token,
coordinate, demand, score, mask, and output column together while the sampler
still canonicalizes by semantic token. Exactly `N` priority-rank words and `N`
action-uniform words are consumed per decision.

## 4. Oracle, diagnostic, and answerability panels

### 4.1 Nonanticipating allocation oracle

For every frozen public state, `ORACLE` selects the legal integral coupling
maximizing the same immediate `R_e`. It knows the frozen environment utility
law but no future load or learned action variate. With one unit per agent and
integer task slots, it is an expanded-slot linear assignment with semantic idle
slots; unmet demand is the unused task capacity. It is computed offline once
per common panel and is never a policy input, training label, or arm-specific
solver.

The retained oracle action is aggregate and permutation-invariant, not an
arbitrary individual assignment returned in solver row order. Let `C_{rj}` be
the integer number of agents of public role `r in {LEFT,RIGHT}` allocated to
semantic task `j`, let `I_r` be the role-idle counts, and let `U_j` be task-unmet
counts. Among all immediate-reward maximizers, choose the lexicographically
smallest integer vector in the fixed semantic order

```text
(C_LEFT,1,...,C_LEFT,4,C_RIGHT,1,...,C_RIGHT,4,
 I_LEFT,I_RIGHT,U_1,...,U_4).
```

The offline solver must implement that secondary law exactly (for example by
sequential fixed-objective solves); it may not expose a library-specific
agent/slot tie. Oracle reward, headroom, and action-alignment quantities use
this canonical aggregate record. No individual-level oracle expansion or
oracle permutation replay is an evidence field.

### 4.2 `PUBLIC-LOAD-SOFTMAX` diagnostic

The diagnostic uses the common autoregressive decoder with

\[
q^{load}_{ij}=\log(1+d_j/N),\qquad q^{load}_{i,IDLE}=0,
\]

and no role, capability, metric, task token, training, or learned parameter. Its
exact expected reward is computed by finite dynamic programming over remaining
`LEFT/RIGHT` counts and four residual demands. It is reported descriptively and
used only to certify that a panel contains allocation headroom. It is never the
primary comparator and cannot promote the metric mechanism.

For state `s`, define normalized headroom

\[
H(s)=\frac{R_{ORACLE}(s)-E[R_{LOAD}(s)]}{N}.
\]

Before activity, every claim state at every `N in {4,6,8,12}` must satisfy

\[
H(s)\ge 1/12.
\]

The independently chosen `1/12` margin is the smallest exact role-allocation
gap in the interior-task slack panels under the frozen rational utility table.
Failure means the panel cannot answer the question; it is not evidence against
either arm. No generated training episode may begin until the common panel
certificate is complete.

### 4.3 Metric-binding and legal-action activity

For the balanced epoch-1 `BINDING` state define oracle-aligned coupling mass

\[
A^{bind}(X)=\frac1N\left[
\sum_{i:r_i=LEFT}X_{i1}+\sum_{i:r_i=RIGHT}X_{i4}
\right].
\]

For the balanced epoch-1 `INERT` state define

\[
A^{inert}(X)=\frac1N\left[
\sum_{i:r_i=LEFT}X_{i2}+\sum_{i:r_i=RIGHT}X_{i3}
\right].
\]

The cut changes `B_METRIC` throughout the dense map, including possible
cross-channel influence on task-2/3 logits, even though those tasks' own
coordinates remain unchanged. A metric-specific result requires a legal change
in `A^bind`, not merely a matrix, hidden score, or gradient change, and requires
empirical practical equality of `A^inert`. Failure of inert equality identifies
generic global reparameterization spillover, not endpoint metric binding.

### 4.4 Static answerability certificate

Before scientific activity, CM may use only literal arithmetic, hand-written
fixtures, schema checks, and offline deterministic oracle/diagnostic panel
construction to certify:

- nonempty common feasible polytopes with real scarce capacity, slack, and
  unmet demand at every size;
- oracle-versus-load headroom `>=1/12` in every claim state;
- feature rank six and invertibility of all three edge maps;
- exact two-way score-class transforms between treatment and comparator;
- a nonzero metric-map change under the cut on binding edges and no task-2/3
  coordinate change;
- exact common decoder semantics and one legal action change on a hand-written
  nonzero-score fixture;
- identical semantic input, output, parameter, useful-operation, solver, and
  communication counts; and
- an atomic evidence schema containing the fields in Section 7.

These are answerability facts, not predicted efficacy. The certificate cannot
substitute for training, held-out inference, or Pro mathematical closure.

## 5. Training, tuning, and fixed resource match

### 5.1 Initialization and objective

Every raw parameter is initialized to zero, so all learned arms begin with
identical zero logits and the same action distribution. For episode `h`, its
stochastic policy/entropy term is

\[
\ell_h=-\frac12\sum_{e=1}^2
\frac{R_e}{N}\log\pi(X_e\mid s_e)
-0.005\frac12\sum_{e=1}^2\bar H_e.
\]

For the fixed 48-episode update batch, the exact optimized loss is

\[
\mathcal L_{batch}=\frac1{48}\sum_{h=1}^{48}\ell_h
+\lambda\left(\lVert W\rVert_F^2+\lVert V\rVert_F^2\right).
\]

The regularizer is applied exactly once per batch, not once per episode.
`bar H_e` is mean decoder-step entropy. Training uses float64 plain SGD without
momentum, global gradient-norm clipping at 5, and no critic, replay, curriculum,
early stop, per-`N` head, or validation-dependent checkpoint. Reward is
immediate per epoch because epoch 2 is exogenous.

### 5.2 Symmetric train-size-only calibration

Each `(arm,binding)` cell receives the same six-configuration grid:

```text
learning_rate in {0.01,0.03,0.10}
lambda in {0,0.0001}
```

Every configuration uses four registered calibration seeds, 64 updates, and
the exact 48-episode full-factorial update. Evaluate the fit only at updates 32
and 64 on a separate fixed train-size-only validation panel containing exactly
16 retained decoder tapes for each element of

```text
N in {4,8} x ordered_pair in 12 distinct pairs x L in {SLACK,OVERLOAD}.
```

The validation namespace is
`(validation,calibration_seed,N,ordered_pair,L,tape,epoch)` and is disjoint from
training/final evaluation. All arms and configurations share the same priority
ranks and action uniforms at the same namespace address. Select the largest
mean update-64 validation `Y` across all cells, tapes, and four calibration
seeds; ties within exact arithmetic choose smaller learning rate and then larger
`lambda`. Held-out `N`, binding/action estimands, and final seeds are unavailable
during selection.

For the selected configuration define

\[
slope_{32}=\frac{\bar V_{64}-\bar V_{32}}{32},
\]

where both means use the same validation cells, tapes, and four seeds. If the
selected configuration is on either learning-rate or `lambda` grid boundary and
`|32*slope_{32}|>0.005` normalized return, the corresponding comparator relation
is optimization-nonidentified.
No grid expansion or result-responsive tuning is allowed after activity; a
successor would require a new prospective revision.

Calibration seeds are

```text
1103,1129,1151,1171.
```

### 5.3 Conclusion-bearing fits

Each selected `(arm,binding)` configuration is fit from scratch on exactly 16
paired seed blocks:

```text
2003,2027,2053,2081,2111,2141,2179,2203,
2237,2269,2297,2333,2357,2389,2417,2447.
```

Every fit uses exactly 128 updates. Every update contains exactly one episode
for each element of

```text
N in {4,8} x ordered_pair in 12 distinct pairs x L in {SLACK,OVERLOAD},
```

for 48 episodes, 96 decisions, and no sample replacement. Update 128 is the
only conclusion-bearing checkpoint. One parameterization is shared across both
training sizes and later evaluated unchanged at all four sizes.

Within a paired seed block, all arms share the episode order, priority ranks,
action uniforms, row permutations, and task presentation permutations. The
physical process is deterministic conditional on action. Different actions may
produce different rewards; information law, examples, opportunities, and
exogenous tapes are nevertheless identical.

### 5.4 Useful work and deployment resource equality

Each primary arm has exactly

```text
real-edge coefficients=8*6=48
idle coefficients=2*6=12
total trainable scalars=60.
```

For every decision both arms execute the same feature construction, eight
six-term edge dot products, two six-term idle dot products, one dense `8 x 8`
output-relevant map, `4N` edge expansion, `N` priority steps, masks, softmaxes,
samples, log probabilities, and record writes. The dense Hadamard comparator
map has no zero or ignored output channel. Every gradient, optimizer state,
calibration configuration, update, sample, decoder call, action opportunity,
and retained record is paired. No arm receives dummy epochs, disconnected
parameters, no-op solver calls, ledger-only padding, extra communication, or an
offline oracle during learning.

The deployment path is `O(N)` edge expansion and `N` constant-width decoder
steps for four tasks. The offline oracle/diagnostic certificate is common panel
work and excluded from learned-arm deployment claims. B1 makes no runtime
speedup claim.

### 5.5 Frozen prospective resource envelope

All calibration, final fitting, evaluation, permutation replay, analysis, and
artifact installation form one future heavy-compute class requiring a separate
Root lease. The scientific package must be runnable sequentially in one CPU-only
process with at most four numerical-library threads, no child worker, peak RSS
below 4 GiB, elapsed wall below eight hours, and a complete temporary-plus-final
disk frontier below 8 GiB. Concurrent fits or evaluators are forbidden.

The frozen workload is 96 calibration fits (`4 arm/binding cells x 6 grid
points x 4 seeds`), 64 conclusion-bearing fits (`4 cells x 16 seeds`), two
validation checkpoints with 16 tapes per train-size cell, and 64 evaluation
tapes per final cell plus one paired permutation replay. If CM's preactivity
projection or construction cannot meet any bound, it returns a resource-class
expansion request to Root before scientific activity; it does not silently
reduce samples, omit records, parallelize, or begin a partial run.

A decision here means one epoch-level allocation. The exact frozen execution
counts are 589,824 calibration-training decisions, 294,912 validation
decisions, 786,432 conclusion-training decisions, and 786,432 base final-
evaluation decisions; permutation replay adds another 786,432 final-evaluation
decisions. Across the frozen roster balance these are exactly 21,823,488
autoregressive agent steps in total. A two-epoch tape is never
counted as one decoder invocation.

## 6. Evaluation, permutations, and complete evidence

### 6.1 Frozen evaluation

Every final seed/checkpoint is evaluated at each

```text
N in {4,6,8,12}
ordered_pair in 12 distinct pairs
L in {SLACK,OVERLOAD}
```

using exactly 64 retained decoder tapes per cell. Training, calibration,
validation, and evaluation namespaces are disjoint. The same learned checkpoint
serves every `N`; no per-size tuning, normalization update, adapter, or
finetuning is allowed.

### 6.2 Identity and presentation permutation

For every learned evaluation decision, generate one nonidentity agent-row
permutation and one nonidentity task-presentation permutation. Move the complete
agent tuple, priority rank, and action uniform together; move the complete task tuple and
output column together. After inverse permutation, require exact equality of
the semantic coupling `(X,iota,mu)`, reward, and endpoint. The unique rank
permutation has no tie or row/identity fallback. Canonical semantic-token
category order makes scalar inverse-CDF sampling task-presentation equivariant.
A failure is technical
nonconformance, not negative scientific evidence.

### 6.3 Atomic seed packet

The training seed is the inferential unit. A seed packet is scientifically
available only if one atomic install contains all four `(arm,binding)` fits,
all four roster sizes, all 24 ordered-pair/load cells, all 64 tapes, intact
and cut records, permutation replays, oracle and load panels, support and
tuning facts, and useful-work ledgers.

Every evaluated decision group must retain together:

```text
revision, arm, binding, phase, training_seed, tape_address,
N, ordered_pair, load_flag, epoch,
agent_records, task_records, raw_supply, raw_demand,
displayed_coordinates, true_utility_table_key,
priority_ranks, action_uniforms, permutations,
feature_vector, edge_map_key, raw_edge_scores, expanded_Nx4_logits,
idle_logits, step_masks, categorical_probabilities,
sampled_step_actions, coupling_X, idle_iota, unmet_mu,
feasibility_residuals, reward, normalized_endpoint,
oracle_panel_key, oracle_role_task_counts, oracle_role_idle_counts,
oracle_unmet_counts, oracle_reward,
load_diagnostic_expectation, headroom,
parameter_count, feature_ops, map_ops, edge_evaluations,
decoder_steps, softmax_categories, input_words, output_words, messages.
```

The final artifact is one fresh directory tree containing `manifest.json`, one
compressed typed-numeric `tables.npz`, sixteen compressed typed-numeric
`seed_<seed>.npz` packets, and `summary.json`. Frozen constants, edge maps, true
utility, oracle/load panels, and common addresses are stored exactly once in
`tables.npz`; decision rows use in-container integer keys. Each seed packet
retains base and replay couplings/actions/endpoints, but replay rows may refer to
unchanged base features by key. No scientific field may refer outside the final
tree. The entire tree is built under one fresh temporary sibling and installed
only by a single final atomic directory rename after every table, seed, and
summary closes and the total tree is below 8 GiB. A missing group, arm, size,
field, or seed is not replaced after activity and supports no efficacy mean.
File hashes, byte counts, line endings, or floating-point bit identity are not
scientific gates; CM owns ordinary compression, conformance, and installation.

## 7. Estimands, inference, and margins

### 7.1 Cell means and deployment value

For arm `A in {M,F}`, binding `C in {I,K}`, seed `s`, and roster `n`, let
`V_s^{A,C}(n)` be mean `Y` over all 12 ordered pairs, both load flags, and 64
tapes. Let `V_s^{A,C}(n,g)` restrict to `g=BINDING` or `g=INERT`, averaging its
two ordered pairs, both loads, and tapes.

Define paired intact performance differences

\[
\Delta_s(n)=V_s^{M,I}(n)-V_s^{F,I}(n),\qquad n\in\{6,12\}.
\]

Define worst-size degradation

\[
D_s^A=\frac12[V_s^{A,I}(4)+V_s^{A,I}(8)]
-\min_{n\in\{6,12\}}V_s^{A,I}(n),
\]

and metric robustness improvement

\[
\Delta_s^R=D_s^F-D_s^M.
\]

Define the intact training-reference contrast

\[
T_s=\frac12\Big(
[V_s^{M,I}(4)-V_s^{F,I}(4)]
+[V_s^{M,I}(8)-V_s^{F,I}(8)]\Big).
\]

This prevents a treatment that starts uniformly worse at training sizes from
appearing more robust merely because it has less value left to lose.

### 7.2 Binding specificity

For held-out `n`, define direct treatment binding and inert value effects

\[
\Theta_s^B(n)=V_s^{M,I}(n,B)-V_s^{M,K}(n,B),
\]

\[
\Theta_s^J(n)=V_s^{M,I}(n,J)-V_s^{M,K}(n,J),
\]

and the supplementary difference-in-differences

\[
\Psi_s(n)=
\Big([V_s^{M,I}(n,B)-V_s^{F,I}(n,B)]
-[V_s^{M,K}(n,B)-V_s^{F,K}(n,B)]\Big)
\]

\[
-\Big([V_s^{M,I}(n,J)-V_s^{F,I}(n,J)]
-[V_s^{M,K}(n,J)-V_s^{F,K}(n,J)]\Big),
\]

where `B=BINDING` and `J=INERT`. `Psi` is descriptive only because a positive
difference-in-differences can arise when both direct cut effects have the wrong
sign. Metric-specific value instead requires positive `Theta^B` and practical
equivalence of `Theta^J` at each held-out size.

For each held-out `n`, let `Gamma_s^B(n)` be treatment intact-minus-cut mean
`A^bind`, and let `Gamma_s^J(n)` be treatment intact-minus-cut mean `A^inert`.
Binding activity requires positive legal oracle-aligned action movement in
`Gamma^B`; cut isolation requires `Gamma^J` to be practically zero.

Because the free map and its actor features do not depend on displayed
coordinates, paired `FREE` intact/cut checkpoints and outputs must be exactly
equal under the same seed/tape. A difference is technical leakage and
invalidates specificity inference.

### 7.3 Inferential unit, stochastic independence, and simultaneous intervals

The 16 paired training-seed blocks are the only replicates. Agents, decoder
steps, episodes, and evaluation tapes are not independent replicates. Form
ordinary paired Student-`t` intervals over the following twelve registered
seed-level quantities:

```text
Delta(6), Delta(12), Delta_R, T,
Theta_B(6), Theta_B(12),
Theta_J(6), Theta_J(12),
Gamma_B(6), Gamma_B(12),
Gamma_J(6), Gamma_J(12).
```

Every distinct stochastic address is an independent draw from its declared
law, except that the same addressed object is deliberately reused for registered
common-random-number pairing across arms, bindings, configurations, and
permutation replay. Priority permutations are uniform over `N!`; action
uniforms are independent `Uniform[0,1)` variates; registered nonidentity row and
task-presentation permutations are uniform over their respective nonidentity
supports. The sixteen final seed blocks are mutually independent draws from the
registered training-randomness law.

Use nominal simultaneous two-sided family coverage 95% by Bonferroni: every
interval uses quantile `t_(15,1-0.05/(2*12))`. The coverage interpretation
assumes independent seed blocks and the usual approximate Student-`t`
seed-contrast model; it is not distribution-free exact coverage. An exact
point interval is permitted only
for a separately proved deterministic identity such as paired FREE intact/cut
equality. Zero sample variance in any learned registered contrast is not such a
proof and invalidates the family, as do nonfinite input or an undefined interval.

The prospectively chosen normalized-return margins are

```text
delta_performance=0.02
delta_robustness=0.02
heldout_noninferiority=-0.01
training_reference_noninferiority=-0.01
delta_binding_value=0.02
epsilon_inert_value=0.02
```

The legal coupling-response and inert-equivalence margins are

```text
delta_action_binding=0.10 of total supply
epsilon_action_inert=0.02 of total supply.
```

They are B1-specific: two percentage points of normalized task return,
robustness, binding value, or inert value; one percentage point of
noninferiority; ten percent reallocation on the endpoint binding challenge; and
two percent inert action tolerance. No margin is imported from another
direction.

### 7.4 Primary relation labels

For the two held-out performance intervals:

- `METRIC_MATERIALLY_BETTER`: both lower endpoints exceed `+0.02`;
- `FREE_MATERIALLY_BETTER`: both upper endpoints are below `-0.02`;
- `PRACTICALLY_EQUIVALENT`: both intervals lie inside `[-0.02,+0.02]`;
- `SIZE_INTERACTION`: one interval is wholly above `+0.02` and the other wholly
  below `-0.02`;
- `UNRESOLVED`: every other configuration.

No pooling across opposite size effects is allowed.

### 7.5 Literal interval-status vocabulary

For any positive material criterion with margin `m`, classify its simultaneous
interval `[L,U]` as:

- `SUPPORTED_POSITIVE(m)` iff `L>m`;
- `AFFIRMATIVELY_BELOW_MATERIAL(m)` iff `U<=m`;
- `POSITIVE_UNRESOLVED(m)` otherwise.

For either two-sided equivalence criterion `[-epsilon,+epsilon]`, classify an
interval `[L,U]` as:

- `EQUIVALENT(epsilon)` iff `L>=-epsilon` and `U<=+epsilon`;
- `AFFIRMATIVELY_OUTSIDE_EQUIVALENCE(epsilon)` iff `U< -epsilon` or
  `L>+epsilon`;
- `EQUIVALENCE_UNRESOLVED(epsilon)` otherwise.

A failed support or equivalence gate is not automatically affirmative evidence
of absence, spillover, or generic conditioning. Noninferiority uses the same
positive-status vocabulary with its registered margin `m=-0.01`.

Define the three-way robustness alternative:

```text
ROBUSTNESS_SUPPORTED iff
  Delta_R is SUPPORTED_POSITIVE(+0.02) and
  Delta(6) is SUPPORTED_POSITIVE(-0.01) and
  Delta(12) is SUPPORTED_POSITIVE(-0.01) and
  T is SUPPORTED_POSITIVE(-0.01).

ROBUSTNESS_AFFIRMATIVELY_REJECTED iff at least one of
  Delta_R is AFFIRMATIVELY_BELOW_MATERIAL(+0.02),
  Delta(6) is AFFIRMATIVELY_BELOW_MATERIAL(-0.01),
  Delta(12) is AFFIRMATIVELY_BELOW_MATERIAL(-0.01), or
  T is AFFIRMATIVELY_BELOW_MATERIAL(-0.01).

ROBUSTNESS_UNRESOLVED otherwise.
```

These three states are mutually exclusive and exhaustive. Define
`HELDOUT_VALUE_CLEARS` iff the primary relation is
`METRIC_MATERIALLY_BETTER` or `ROBUSTNESS_SUPPORTED`.

## 8. Result-blind decision map

Apply the following branches in numbered order. They are mutually exclusive by
first-match precedence and exhaustive because branch 6 is a catch-all.

### 8.1 Branch 1 — `BOUNDED_NONIDENTIFICATION_STRUCTURAL`

Take this branch on any invalid common feasibility or score-class transform;
missing `1/12` headroom; boundary-selected optimization still changing beyond
the frozen slope limit; missing/incomplete/nonfinite atomic evidence or interval;
zero variance in a learned registered contrast; identity/task-presentation
failure; FREE intact/cut leakage; hidden/forbidden input; or failed equality of
useful parameters, information, samples, tuning, optimizer, communication,
decoder, output records, or actual useful work. Extra treatment resources route
only here. This branch supports no positive, negative, generic, or equivalence
claim and does not delete the family.

### 8.2 Branch 2 — `RETAIN_METRIC_FINITE_BUDGET`

All structural validity, headroom, tuning, complete-evidence, identity, and
FREE cut-equality conditions must hold. In addition require:

1. `HELDOUT_VALUE_CLEARS`.
2. Both direct `Theta_B(n)` lower bounds exceed `+0.02`.
3. Both direct `Theta_J(n)` intervals lie wholly inside `[-0.02,+0.02]`.
4. Both `Gamma_B(n)` lower bounds exceed `+0.10`.
5. Both `Gamma_J(n)` intervals lie wholly inside `[-0.02,+0.02]`.

The maximum conclusion is: on this balanced two-role, four-task, two-epoch
centralized toy, a correctly bound ground-neighborhood score coordinate system
improves finite-training-budget held-out-roster performance or robustness over
an equal-class free-edge coordinate system.

### 8.3 Branch 3 — `DELETE_METRIC_EQUAL_CLASS`

After branch 2 fails, delete the metric-specific contribution on this support
iff the primary relation is `FREE_MATERIALLY_BETTER`, or it is
`PRACTICALLY_EQUIVALENT` and robustness is
`ROBUSTNESS_AFFIRMATIVELY_REJECTED`. This is affirmative equal-class evidence
against both registered value routes and requires complete structural validity
from branch 1. Reaching only the public-load diagnostic is never a deletion
predicate.

An allocation actor may remain useful, but B1 supplies no reason to retain the
metric-specific parameterization.

### 8.4 Branch 4 — `GENERIC_FINITE_BUDGET_EFFECT`

After branches 2–3 fail, take this branch iff `HELDOUT_VALUE_CLEARS` and at
least one affirmative nonmetric causal predicate holds at either held-out size:

- `Theta_B` is `AFFIRMATIVELY_BELOW_MATERIAL(+0.02)`;
- `Theta_J` is `AFFIRMATIVELY_OUTSIDE_EQUIVALENCE(0.02)`;
- `Gamma_B` is `AFFIRMATIVELY_BELOW_MATERIAL(+0.10)`; or
- `Gamma_J` is `AFFIRMATIVELY_OUTSIDE_EQUIVALENCE(0.02)`.

This is affirmative evidence that value lacks the registered metric-specific
path. Attribute at most generic conditioning, regularization, task-token
memorization, or optimization; do not activate a second surface. An unresolved
specificity interval does not enter this branch.

### 8.5 Branch 5 — `SIZE_INTERACTION`

After branches 2–4 fail, take this branch iff the primary relation is
`SIZE_INTERACTION`. Report both sizes without pooling. It is not positive direct
variable-`N` evidence and may motivate only a new prospective boundary
discriminator.

### 8.6 Branch 6 — `BOUNDED_NONIDENTIFICATION`

Every otherwise-valid configuration not matched above takes this catch-all,
including primary `UNRESOLVED`; any `POSITIVE_UNRESOLVED` or
`EQUIVALENCE_UNRESOLVED` binding/inert/action interval; a pattern suggestive
only of training-size or load interaction; or held-out value without an
affirmatively established causal attribution branch. It supports no family
deletion, generic attribution, equivalence claim, or second-surface activation.
No threshold weakening, seed replacement, post-hoc checkpoint, or automatic
rerun is allowed.

In particular, `PRACTICALLY_EQUIVALENT + ROBUSTNESS_SUPPORTED` routes to
retention when all metric-specific gates pass, to generic effect when an
affirmative nonmetric causal predicate holds, and otherwise to this catch-all.
`PRACTICALLY_EQUIVALENT + ROBUSTNESS_UNRESOLVED` also routes here.

## 9. Second surface and UAV bridge

No second-surface result is part of B1. A fully qualifying B1 result may
activate exactly one warehouse-zone surface before any UAV simulator.

### 9.1 Warehouse-zone surface

- agents: mobile warehouse robots available at dispatch start;
- observable role/capability: payload and aisle-access class;
- task: four public zone-service queues;
- supply: one pallet/tote service quantum per dispatch wave;
- demand: raw zone backlog;
- ground: static shortest-path travel time or energy;
- action: capacity-feasible robot-to-zone coupling with idle robots and unmet
  backlog;
- varying axis: one unchanged allocator across fleet sizes;
- outcome: fulfilled work or held-out-fleet robustness against the same
  equal-class free-edge comparator.

The surface is invalid if routing interactions, collisions, or nonadditive
multi-robot service dominate the one-quantum coupling abstraction.

### 9.2 UAV mapping and boundary

The strongest later mapping is variable-fleet delivery: drones provide one
payload/sortie quantum to four public drop-zone queues; observable payload/range
class is the role token; shortest safe-path energy is the candidate ground;
idle drones and unmet deliveries remain explicit. Sensing is credible only
after zones are discretized into approximately additive dwell/coverage quanta.
Relay is credible only for independent packet-airtime demand at fixed sites
with fixed topology and orthogonal channels.

Connectivity thresholds, interference, multi-drone complementarity, dynamic
routing, collision avoidance, wind, hidden health, in-episode dropout, and
churn violate B1's additive finite coupling and require a new object. B1 makes
no warehouse or UAV efficacy claim.

## 10. Activity, closure, ownership, and return

Question-relevant scientific activity begins at the earliest materialization
or inspection of any registered stochastic training, calibration, validation,
or evaluation object—including an episode order, priority permutation, row or
task-presentation permutation, action variate, stochastic policy output,
coupling, reward, loss, or gradient—or at the first optimizer update, whichever
occurs first. That boundary may occur only after the exact complete revision is
frozen, ChatGPT External Pro returns literal `CLOSED`, this EM accepts that
ruling, CM statically accepts the constructible object, and Root separately
sequences construction/compute. Source inspection, owner artifact preparation,
provider question preparation, symbolic matrices, hand-written deterministic
fixtures, schemas, and offline deterministic oracle/headroom certificates are
preactivity.

After activity begins, no arm, binding, demand, score map, decoder, margin,
seed, tuning rule, endpoint, interval, branch, or claim may change in response
to a result.

- EM owns this question, card, interpretation, claim ceiling, and any
  science-bearing clarification.
- CM owns source, tests, exact implementation, environment, technical
  conformance, launcher, Operator dispatch, unchanged-science repair, resource
  proposal, and atomic retained-result installation.
- A technically accepted complete result returns directly from the named CM to
  this EM for scientific intake.
- Root owns new provider conversations, compute leases, portfolio choice,
  cross-direction relay, Git, canonical integration, and user contact.

The dedicated ChatGPT External Pro conversation returned `REVISION_REQUIRED`
for revisions 02 and 03, then literal `CLOSED` with no required correction for
this exact complete revision 04. This EM accepts that ruling without changing
the scientific object. The independent revision-02 External Gemini request
remains mutually blind, `PREPARED_NOT_SENT`, and Root-withheld; it must not be
released as a revision-04 request. The closed composite is released to the
named CM for construction planning only. No source construction, test,
stochastic-object materialization, optimizer, production, or compute authority
follows.
