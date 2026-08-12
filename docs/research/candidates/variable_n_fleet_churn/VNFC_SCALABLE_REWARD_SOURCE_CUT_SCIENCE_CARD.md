# VNFC scalable reward-source and allocation cut science card

Owner: `direction:variable-n-fleet-churn` Explorer Manager  
Treatment identity: `VNFC-B3-SCALABLE-REWARD-SOURCE-CUT-v1`  
Candidate family: `SALA-RDA` (Shared Set/Lease Actor with Residual-Demand Auction)  
Current prospective revision: `SP-RDA-MATH-CLOSURE-20260812-07`  
Superseded revisions: `SP-RDA-COMPLEXITY-CORRECTION-20260812-01`,
`SP-RDA-MATH-CLOSURE-20260812-02`, and
`SP-RDA-MATH-CLOSURE-20260812-03`,
`SP-RDA-MATH-CLOSURE-20260812-04`, and
`SP-RDA-MATH-CLOSURE-20260812-05`, and
`SP-RDA-MATH-CLOSURE-20260812-06`  
Hard complexity contract: `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`  

## Decision first

This is a new prospective treatment, not a repair, extension run, or positive
evidence transfer from `VNFC-B1`. B1 established that exact reward-aware joint
construction can outperform factorized actions on its small host, while its
explicit mass bundle was practically equivalent to the generic arm, its fixed
keep term did not separate from the coverage-aware decoder, and a reward-complete
greedy rule exceeded the learned B package. Those observations motivate the
question below but provide no support, threshold, checkpoint, row, or warm start
for this treatment.

The successor is frozen as one prospective full Stage-1 plus conditional-Stage-2
composite under the revision above. The existing same-direction ChatGPT Pro
conversation returned `CLOSED` on v6. It confirmed that the complete mathematical,
causal, operational, bounded-work, and claim definitions were single-valued and
that the fixed-three-task SP-RDA derivation is `O(N log N)`/`O(N)`. A subsequent
preactivity deterministic CM proof probe found the first required training bank
non-instantiable before any metric, model update, or treatment output: for every
raw index `0,...,95` at seed 1601 and schedule `6->9`, no one shared history could
lie within `0.02` of all four variant-specific pre-service optima. V7 is therefore
a prospective science-bearing panel-law correction, not a run repair or negative
treatment result. It replaces only that contradictory benchmark with the best
attainable shared minimax-regret benchmark while preserving the four matrices,
one history across variants, the numerical `0.02` tolerance, all later treatment
definitions, and the primary return contrast.
It is not CM- or production-released. The prior CM acceptance and every earlier
mathematical revision are non-operative. Only a new Pro `CLOSED` verdict on this
exact full v7 plus
same-direction owner intake permits Root to relay it; CM must then explicitly
accept its changed generator, action, comparator, panel, analysis, activity, and
count contracts before any Stage-1 production command.
The earlier unimplemented dense-rescoring allocator draft is superseded: it used
`N` rounds that rescored all remaining agent-task pairs and therefore had a
forbidden `O(N^2 R)` deployment path. No construction, process, or result used
that draft, so this is a pre-activity correction of the same scientific object,
not a repair run or a result-conditioned change.

The corrected common allocator is `SP-RDA`, a sparse single-pass residual-demand
auction. It constructs at most the three real-task edges of each agent once,
heapifies them once, and consumes every edge exactly once. For the frozen
three-task host its deployment cost is `O(E log E)` with `E <= 3N`, hence
`O(N log N)`, and its live edge memory is `O(E)=O(N)`. It contains no dense
agent-agent path, repeated all-edge rescoring, exact fallback, or rollout search.

Stage 1 is a family-eliminating learned-value cut. It asks whether learned,
roster-conditioned bids add material value beyond preregistered comparative-
advantage and history/handoff-aware frozen priorities when every action uses the
same polynomial, reward-input-blind allocator conditional on supplied bids.
Pressure and adaptive-lease arms are already defined but
may consume no production compute unless the registered Stage-1 trigger passes.

This staging is intentionally asymmetric. A Stage-1 negative does not prove that
analytic pressure or persistence is universally useless; it says this
SALA-RDA learned-allocation family has not earned those rescue branches on this
surface. B1 evidence cannot override that outcome.

`VNFC-B2-TYPED-CAPSULE-RETENTION-v1` is unchanged and outside this treatment. No
B2 evidence, threshold, treatment, or compute transfers here.

## Question and project relation

Can one permutation-equivariant shared policy, trained only at active decision
sizes `N in {6,9,12}`, use learned agent-task bids through one common scalable,
reward-input-blind `O(N log N)` sparse residual-demand auction to improve the
registered three-tick post-churn physical return `J` at an unseen active size
`N=15` relative to preregistered comparative-advantage and history/handoff-aware
frozen priorities?

If and only if learned bids pass that cut, two conditional questions follow:

1. Does an explicit demand-to-mass pressure vector improve finite-budget learning
   specifically when physical fleet mass changes, beyond a strong sum/attention
   policy that can derive the same statistic?
2. Does an adaptive survivor lease retain useful assignments in `KEEP_OPTIMAL`
   churn while releasing more survivors in `SWITCH_REQUIRED` churn, beyond both
   release-all and a frozen local hysteresis rule, while remaining noninferior in
   registered physical return `J` and recovery time `Trec`?

The direct variable axis is active roster size. Every learned arm is one shared
parameterization across all training and evaluation sizes. There is no per-`N`
model, normalization refit, threshold, allocator retuning, fine-tuning, or
evaluation-time adaptation. `N=15` is strictly above the training maximum, so a
positive result supports one-point above-range generalization rather than only
inside-range interpolation.

## Second-surface host

### Physical process

There are three persistent tasks `r in {0,1,2}` and a safe `DUMMY` assignment.
Each trial contains:

1. a prescribed pre-event roster and common pre-event assignment `p_i`;
2. one exogenous join or drop of a three-agent block;
3. one post-event allocation decision; and
4. three equal one-unit service ticks `tau in {0,1,2}` during which that allocation
   is held.

Every active agent receives exactly one task or `DUMMY`. Multiple agents may serve
one task. A new agent or a survivor kept on its previous task contributes at all
three ticks. A survivor assigned to a different real task incurs a physical
one-tick handoff: its contribution is zero at `tau=0` and its full capacity is
available at `tau=1,2`. A survivor moved to or from `DUMMY` is also a switch and
has the same one-tick delay before contributing to a real task. There is no
explicit switch reward or keep bonus.

For assignment `a`, define effective contribution

`c_eff[i,r,tau,a] = 1[a_i=r] * c_i[r] * h[i,r,tau]`,

where `h=1` for a new agent or a survivor with `r=p_i`, and for a switched
survivor `h=0` at `tau=0` and `h=1` thereafter. Let

`x[r,tau,a] = sum_i c_eff[i,r,tau,a] / d[r]`,  
`service[r,tau,a] = min(x[r,tau,a],1)`,  
`waste[r,tau,a] = min(max(x[r,tau,a]-1,0),1)`, and  
`u[tau,a] = mean_r service[r,tau,a] - 0.10*mean_r waste[r,tau,a]`.

The shared trial return is

`J(a) = mean_tau u[tau,a]`.

The same `J` is delivered to every active agent. Membership, capacities, demand,
and future service are exogenous. `Trec(a)` is the first service tick at which
every task has `service >= 0.90`; use `Trec=3` if no such tick occurs. Retain
per-tick service, waste, switch fraction, dummy fraction, and task assignment.

This replaces B1's algebraically reward-coded switch term with a fixed physical
handoff consequence. It remains a one-event allocation surface, not a long-horizon
navigation or communication task.

### Paired mass and capability geometry

Every agent is generated in an ordered three-agent block. For each
`(seed, split, schedule, raw_index)`, run Fisher-Yates on task-source indices
`[0,1,2]` with the counter namespace
`(seed,split,schedule,raw_index,"demand-permutation")`, and set
`d[r]=(0.95,1.00,1.05)[pi_d[r]]`. This is the complete task-demand law; the same
`d` is used by every derived mass, geometry, history, arm, and row-order variant.
For block `b` and final task `r`, independently draw
`q_b[r] ~ Uniform(0.28,0.36)` from namespace
`(seed,split,schedule,raw_index,"block-mass",b,r)` and set
`m_b[r]=q_b[r]*d[r]`. For within-block agent indices `j=0,1,2`, set the raw
capacity rows by these exact matrices; there is no additional row or task
permutation inside the capability construction:

`SEPARABLE = [[.80*m[0],.10*m[1],.10*m[2]],`  
`             [.10*m[0],.80*m[1],.10*m[2]],`  
`             [.10*m[0],.10*m[1],.80*m[2]]]`

`COUPLED   = [[.48*m[0],.48*m[1],.04*m[2]],`  
`             [.48*m[0],.04*m[1],.48*m[2]],`  
`             [.04*m[0],.48*m[1],.48*m[2]]]`.

For each task column, both geometries have exactly the same block mass. The
coupled geometry concentrates each agent on two tasks and creates one-role
opportunity cost without changing `N`, demand, or task-wise total capacity.

Let `Bmax=max(N_pre,N_post)/3`. The raw base contains ordered blocks
`B_0,...,B_(Bmax-1)`. The pre-event roster is exactly
`B_0,...,B_(N_pre/3-1)` and the post-event roster is exactly
`B_0,...,B_(N_post/3-1)`. A join adds the highest-index required blocks and a
drop removes the highest-index excess blocks; no block is sampled conditionally
on its capacity. Within each world, opaque handle rank is lexicographic
`(block_index,within_block_agent_index)`, equivalently `3b+j`. Neither coordinate
nor the rank is a learner input.

Cross both geometries with the following exact mass transform:

- `REAL_MASS`: `c_pre_i[r]=c_raw_i[r]` for pre-event agents and
  `c_post_i[r]=c_raw_i[r]` for post-event agents. A joined or dropped block adds
  or removes real task-wise capacity.
- `FIXED_MASS`: pre-event capacities remain raw,
  `c_pre_i[r]=c_raw_i[r]`. At the sole post-event decision define
  `alpha[r]=1.25*d[r]/sum_(j in A)c_raw_j[r]` and
  `c_post_i[r]=alpha[r]*c_raw_i[r]`. Thus only the decision-time active fleet has
  task-wise total capacity exactly `1.25*d[r]`; survivor capacities are
  recomputed once at the event.

Mass and geometry labels are never observations. Both regimes occur at every
registered roster size and event type. Pair geometry worlds on the same demand,
block masses, identities, event, and random tapes. Pair mass worlds on the same
raw blocks before the fixed-mass post-event rescaling.

### Paired churn necessity

For one post-event roster, capability matrix, demand, and membership event,
construct two distinct pre-event assignments using an offline solver. Because one
history is deliberately shared across all four mass/geometry variants, define its
quality relative to the best attainable shared compromise, not four mutually
incompatible variant-wise optima. For variant `v`, first compute its individual
pre-service optimum `S_star^v`. For one shared history `p`, define worst variant
regret

`Delta(p)=max_(v in V)(S_star^v-S_pre^v(p))`

and the best attainable shared regret

`Delta_star=min_p Delta(p)`.

Both selected histories must satisfy

`Delta(p)<=Delta_star+0.02`,

equivalently `S_pre^v(p)>=S_star^v-Delta_star-0.02` for every variant. The four
capability matrices, one shared history across variants, and numerical `0.02`
slack are unchanged. The selected histories differ only in survivor task history:

- `KEEP_OPTIMAL`: the best post-event allocation constrained to keep every
  survivor on its previous role is within `0.01` of the unrestricted post-event
  physical-return ceiling.
- `SWITCH_REQUIRED`: the unrestricted ceiling exceeds the best all-survivors-kept
  allocation by at least `0.10`; every allocation within `0.01` of the ceiling
  switches at least one survivor; and each old survivor role remains locally
  feasible, so no invalidity mask reveals the answer.

The condition is certified using the offline physical-return solver. The selected
pre-event history vector `p_KEEP` or `p_SWITCH` is part of the constructed physical
state. For every active survivor, and only for that purpose, its selected previous
role is exposed through the registered previous-role one-hot. Joiners receive the
all-zero previous-role vector.

No arm receives the history name `KEEP_OPTIMAL` or `SWITCH_REQUIRED`, its mixed-
radix rank, any certificate feasibility flag, any certificate objective value,
`t_K`, `q_W`, `S_star`, `Q`, `R`, `K`, an optimizing post-event assignment, an
`RC-MIP` action, an `RC-MIP` value, a solver bound, or solver metadata. Thus the
selected `p` vector is the sole certificate-derived object exposed to an arm, and
it is exposed only as ordinary pre-event role history. All other certificate
outputs remain unavailable. Certificate construction follows the finite,
deterministic panel law below; unbounded rejection sampling is forbidden. The
paired cells share event kind, roster, capacities, demand, survivor set, and
three-tick physical horizon; only the pre-event assignment differs.

Physical raw-base draws are counter-keyed only by seed, split, schedule,
raw-candidate index, block, agent, and field. They exclude mass regime, geometry,
and churn necessity. From one raw base, deterministically derive all four
`mass x geometry` variants, and use one shared pair of pre-event assignment vectors
for KEEP and SWITCH across all four variants. Thus paired variants share demand,
raw blocks, identities, membership event, survivor set, task/row tapes, and both
history vectors. Fixed-mass rescaling and the registered geometry matrix are the
only variant transformations. Arm order cannot change a world.

## Observation and learned policy

At the sole post-event decision, each unordered active-agent row contains:

- the three current capacities `c_i`;
- previous role one-hot over three tasks plus `DUMMY`, or all zeros for a joiner;
- `survived` and `newly_joined` bits.

Each task row contains task-index one-hot and demand. Global input contains event
kind (`JOIN` or `DROP`) and `log(1+N)/log(16)`. No arm sees mass, geometry, churn-
necessity or template labels, future information, opaque handle values, reward
coefficients, any optimizing post-event assignment, or any certificate/solver
quantity except the selected physical pre-event role history exposed exactly as
specified above. Agent rows are freshly permuted. Opaque handles exist only in
the external mapper and deterministic tie rule.

Every learned arm instantiates the same exact function class. An `MLP(a,64,64)`
means affine `a->64`, SiLU, affine `64->64`, SiLU. The agent encoder is
`MLP(9,64,64)` and the task encoder is `MLP(4,64,64)`. Let `h_i` and `g_r` be
their outputs, and let `S=sum_i h_i` and `M=mean_i h_i`.

Task-to-agent attention is one standard four-head scaled-dot-product block. The
learned matrices `W_Q,W_K,W_V,W_O` are all `64x64`. Split each projected vector
into four 16-dimensional heads. For head `h`,

`alpha[h,r,i]=softmax_i(Q[h,r]^T K[h,i]/sqrt(16))`,

concatenate `sum_i alpha[h,r,i] V[h,i]` over the four heads and apply `W_O` to
obtain the 64-dimensional `A_r`. Attention is only from three fixed task queries
to `N` agent keys/values; it never creates an agent-agent or `N x N` object.

Let `g_event` be the two-coordinate JOIN/DROP one-hot concatenated with
`log(1+N)/log(16)`. After the lease vector is fixed or sampled, define

`leased_load[r]=sum_i ell_i*1[p_i=r]*c_i[r]/d[r]`.

For every structural edge `(i,r)`, the shared bid head receives exactly
`[h_i,g_r,S,M,A_r,g_event,rho,ell_i,leased_load]`, uses an affine map from that
exact concatenation to 64, SiLU,
then affine `64->1`, and returns `mu_theta[i,r](o,ell)`. Use `ell_i=0` for a
joiner or other ineligible agent. The lease head is evaluated only for eligible
survivors and receives stop-gradient
`[h_i,S,M,g_(p_i),A_(p_i),g_event,rho]`; it uses an affine map from that exact
concatenation to 32, SiLU, affine
`32->1`, then sigmoid. The centralized critic receives
`[S,M,sum_r g_r,mean_r g_r,g_event,rho]`, uses an affine map from that exact
concatenation to 64, SiLU, affine
`64->1`, and receives no sampled lease, bid, allocator action, or certificate
quantity.

Every learned arm retains every tensor in this actor/lease/critic class. Generic
pressure slots are exactly zero. Release and fixed-lease arms retain lease-head
parameters even though their outputs are unauthorized and excluded from action,
likelihood, and loss. All affine weights use Xavier-uniform initialization and all
biases are zero. Within a paired seed, common initial tensors are bit-identical
across learned arms; exogenous world and minibatch-order tapes are paired, while
arm-specific action tapes use disjoint counter namespaces.

The three reserved pressure slots are zero for generic arms and contain

`rho[r] = log(d[r]/sum_i c_i[r])`.

for pressure arms. Raw capacities and demand are already visible, so pressure adds
no information to the strong sum/attention comparator; it can support only a
finite-budget inductive-bias claim. Registered demands and capacity sums are
strictly positive. In `FIXED_MASS`, `sum_i c_i[r]=1.25d[r]`, so every pressure
coordinate is exactly the constant `log(1/1.25)`.

For every lease-authorized structural agent-task edge, the actor samples

`z_i,r ~ Normal(mu_i,r(o,ell), 0.20^2)` and emits `b_i,r=tanh(z_i,r)`.

Final evaluation uses `tanh(mu(o,ell))` for bids. For an adaptive-lease arm it uses the
deterministic rule `ell_i=1[p_i(o)>=0.5]`, where `ell_i=1` means retain the real
previous task and a tie at `0.5` retains. Release-all and fixed-lease arms use only
their deterministic registered lease vectors. Lease heads exist in every learned
architecture so parameter counts and forward work are matched; unused outputs are
excluded from both action and likelihood. Bidder backbone, critic, widths, and
optimizer budget are identical.

Freeze the stochastic action before any allocation outcome. One actor forward
pass emits every lease-head output and at most `3N` bid means. For arm `A`, let
`L_A(o)` contain survivors with a real previous task only when `A` has an adaptive
lease; it is empty for release-all and deterministic fixed-lease arms. Construct
the complete arm lease vector `ell^A`: sample Bernoulli variables only for
`i in L_A(o)`, set every survivor to release for a release-all arm, and apply the
registered deterministic threshold for a fixed-lease arm. Deterministic leases are
conditioning inputs, never probability terms. Then form `U(ell^A)`,
`delta0(ell^A)`, and the pre-bid structural edge set `E(o,ell^A)` without
inspecting any sampled bid value. Sample bid latents only for that structural set
and define

`A_lat=(ell_i : i in L_A(o), z_i,r : (i,r) in E(o,ell^A))`,

`pi_theta(ell,z|o)`
` = product_(i in L_A(o)) Bernoulli(ell_i;p_theta_i(o))`
` * product_((i,r) in E(o,ell)) Normal(z_i,r;mu_theta_i,r(o,ell),0.20^2)`.

Thus bid means are explicitly conditional on the complete realized lease vector
through `ell_i` and `leased_load`. For release and fixed-lease arms, `ell` is
deterministic and contributes no likelihood term, but the same deterministic
vector is supplied to the bid head. Joint old and new log probabilities are
evaluated on the same realized `ell` and `z`; no density is assigned to an
unauthorized edge.

Store `A_lat` and its old-policy joint log probability. PPO uses exactly one joint
ratio per trial,

`ratio_theta=exp(log pi_theta(A_lat|o)-log pi_old(A_lat|o))`,

and applies one clipped PPO surrogate to this unnormalized joint ratio and one
centralized-critic advantage per trial. The joint log probability is never divided
by the number of agents, edges, or latent variables; value loss and the shared team
return also occur once per trial.

For trial `t`, let `m_t` be the number of authorized Bernoulli and Gaussian latent
variables in its stored `A_lat`. Define

`H_t=0` if `m_t=0`, and otherwise

`H_t=(1/m_t)*sum_(j=1,...,m_t) H_t,j`,

where Bernoulli entropy is evaluated at the current lease probability and
Gaussian entropy is the entropy of the authorized latent Normal `z`, not of the
transformed bid `tanh(z)`. For each eight-trial optimizer minibatch `B`, define

`H_B=(1/8)*sum_(t in B) H_t`.

Use `H_B` in that minibatch's `L_total`. Do not pool latent variables across
trials, across minibatches, or across the full 128-trial update. The stored
realized lease vector and its resulting structural edge set determine which
latent variables are authorized for both old- and new-policy evaluation. This
preserves one-team-decision weighting. Do not replicate or sum one team return as
`N` agent examples or apply per-agent/per-edge clipped ratios.

A bid mask may depend only on observations, sampled leases, and the resulting
pre-bid structural edge set. It may not depend on realized bid rank, winning or
discard status, final assignment change, or return. In Stage 1, release-all,
positive capacities, and positive initial demands make the bid set exactly `3N`.
There is no oracle imitation, reward shaping, behavior cloning, B1 replay,
checkpoint transfer, or per-`N` adaptation.

The learned forward path is `O(NR)` with frozen `R=3`: the task attention is
task-to-agent, not agent-to-agent self-attention, and the bid head emits at most
the three real-task bids for each active agent. No learned arm may instantiate an
`N x N` tensor, message graph, attention map, or pairwise agent kernel.

## Common scalable reward-input-blind allocator

Every arm except the offline ceiling uses exactly this Sparse Single-Pass
Residual-Demand Auction (`SP-RDA`). Its edge rule, key arithmetic, heap, tie
rule, dummy handling, and scan are arm-invariant.

1. A leased survivor is fixed to its previous real task. New agents and all
   nonleased survivors enter the free set `U`. `DUMMY` survivors are always free.
2. Initialize
   `delta0[r]=max(d[r]-sum_(i leased to r)c_i[r],0)` and
   `freecap0[r]=sum_(i in U)c_i[r]`.
3. Compute one static arm-supplied bid matrix `b in [-1,1]` before allocation.
4. Construct the candidate edge set once:

   `E = {(i,r): i in U, r in {0,1,2}, c_i[r] > 0, delta0[r] > 0}`.

   Every free agent has at most three real-task edges, so `|E| <= 3|U| <= 3N`.
   `DUMMY` is an implicit outside option and is not placed in the heap. This
   rule includes every service-capable edge for every task with initial residual
   demand; it does not use a top-bid, learned-neighbor, reward, oracle, condition,
   or future-dependent pruning rule.
5. Key every retained edge exactly once using only event-entry quantities:

   `fill0[i,r] = min(c_i[r],delta0[r])/(delta0[r]+1e-6)`,  
   `lambda0[r] = clip(delta0[r]/(freecap0[r]+1e-6),0,1)`,  
   `key[i,r] = b[i,r] + lambda0[r]*fill0[i,r]`.

   `SP-RDA` is a maximum-priority allocator. Place the `E` immutable records in
   one binary max heap and pop keys in descending numerical order. Equal keys are
   ordered by ascending task index and then ascending opaque-handle rank fixed by
   the ordered block law; row permutation and arm execution order cannot change
   that rank. An implementation using a min-heap must store exactly
   `(-key,task_index,handle_rank)`. No other tie quantity is inspected.
6. Set `delta=delta0`. Pop every edge exactly once. If agent `i` is still free and
   `delta[r] > 0`, assign `i` to `r`, update
   `delta[r]=max(delta[r]-c_i[r],0)`, and mark `i` assigned. Otherwise discard the
   edge. Do not change any surviving edge key, rebuild a heap, or rescore a
   remaining pair. If every residual is already zero, continue popping and
   discarding the immutable records so Stage-1 arms execute the same `E`-record
   scan. When the heap is empty, assign every still-free agent to `DUMMY`.

`SP-RDA` may enforce membership and one-role feasibility and use current capacity
and demand exactly as written. It may not evaluate or receive `J`, service reward,
waste penalty, handoff loss, switch count, an oracle action, future demand/churn,
a churn-necessity label, or a global optimality/invalidation flag. It cannot
distill from or fall back to the ceiling.

Thus `SP-RDA` is mechanically reward-input-blind at deployment conditional on its
supplied bids. The learned bidder is reward-trained, and the decoder contains
substantial hand-coded demand, capacity, fill, and scarcity structure. No claim
calls the complete learned decision rule reward-independent or the decoder
structure-blind.

For fixed `R=3`, the learned forward emits at most `3N` bid scores and uses
`O(NR)=O(N)` time and live activation memory. Conditional on leases, the allocator
constructs `E<=3|U|<=3N` edge records, evaluates exactly `E` immutable edge keys,
Floyd-heapifies them in `O(E)`, performs exactly `E` heap pops at
`O(log max(E,2))` each, and performs at most `|U|<=N` residual updates. Full
event-decision time is `O(NR+E log max(E,2))=O(N log N)` and live deployment
memory is `O(NR+E+N)=O(N)`.
The implementation must record `E`, edge-key evaluations, heap-build records,
heap pops, heap-key comparisons, residual updates, live edge records, and whether
any `N x N` allocation or learned tensor was instantiated. Hard per-event guards
are:

- `E <= 3N`, edge-key evaluations `=E`, heap pops `=E`, and residual updates
  `<=N`;
- heap-key comparisons `<=8E*ceil(log2(max(E,2)))`;
- no dynamic edge insertion, surviving-edge rekey, repeated all-edge pass,
  dense agent-agent object, exact fallback, tree/beam/MCTS search, or hypothetical
  trajectory rollout.

The Stage-1 analytic-operation gate passes iff, for every full decision:

1. key evaluations equal `E`;
2. Floyd heap construction occurs exactly once over exactly `E` records;
3. heap pops equal `E`;
4. residual updates are at most `|U|`; and
5. insertion, rekeying, heap rebuilding, edge rescanning, exact search, beam/tree
   search, fallback, and hypothetical rollout counters are all zero.

The no-dense gate passes iff no simultaneously live learned/allocation tensor,
array, matrix, or explicit container has two dimensions whose lengths both vary
with `N`. Let `M_dep(N)` be the total simultaneously live machine words across
objects with at least one `N`-dependent dimension, excluding fixed model
parameters and fixed three-task constants. The linear-memory gate passes iff
`M_dep(N)<=1024N` on every registered audit call, the median
`M_dep(N)/N` at each audited `N` is at most twice its `N=15` value, and total
process peak RSS is at most 2 GiB. These are pass predicates, not implementation
suggestions.

Every active agent remains action-addressable: it is either fixed by a valid
lease, has all of its positive-capability edges represented, or takes the implicit
`DUMMY` outside option. A `c_i[r]=0` edge cannot deliver task service, and an edge
with `delta0[r]=0` cannot become useful because residual demand never increases
during this one event allocation. Therefore the frozen toy excludes no
service-relevant edge. If an implementation drops any other edge, the affected
world does not instantiate this treatment; it is an unchanged-science CM repair,
not a negative learned-bid result.

Residual demand is substantial hand structure and may itself solve the task. That
is why the frozen and zero controls are primary rather than decorative.

## Arms and prospective stages

### Stage 1: learned-value family cut

1. `ZERO-RDA`: all bids zero; release every survivor. Nonlearned.
2. `FROZEN-RDA`: release every survivor and use preregistered static
   comparative-advantage bids
   computed once before allocation:

   `v[i,r]=clip(c_i[r]/(d[r]+1e-6),0,1)`,  
   `b_F[i,r]=v[i,r]-max_(q != r)v[i,q]`.

   This is the preregistered comparative-advantage frozen priority. It sees no
   previous-role bonus, reward coefficient, future fact, or condition label; it
   is not claimed to dominate all simple heuristics.
3. `HANDOFF-RDA`: release every survivor and use a preregistered history/handoff-
   aware frozen priority. Define the three-tick effective-capacity multiplier

   `eta[i,r]=1` for a newly joined agent or a survivor with `p_i=r`, and
   `eta[i,r]=2/3` for every other survivor-task pair, including a survivor moving
   from `DUMMY`. Let

   `v_H[i,r]=clip(eta[i,r]*c_i[r]/(d[r]+1e-6),0,1)`,
   `b_H[i,r]=v_H[i,r]-max_(q != r)v_H[i,q]`.

   The `eta`-adjusted capacity is used only to form HANDOFF bids. SP-RDA
   residuals, free capacity, `fill0`, `lambda0`, assignment feasibility, and
   three-tick physical execution continue to use actual `c_i[r]`.

   This rule receives exactly the previous-role and known one-tick physical
   handoff information available to the learner. It uses no `J`, waste coefficient,
   future fact, condition label, ceiling, learned value, or arm outcome. It is the
   primary frozen baseline for promotion.
4. `G-RELEASE`: the strong generic learned set bidder with zero pressure slots;
   all survivors are released into the same `SP-RDA`.
5. `G-PERMUTE` is a same-checkpoint deterministic evaluation intervention, not a
   trained arm. Within survivors and joiners separately, order agents by ascending
   opaque-handle rank. For a stratum of size `m>=2`, the agent at rank `j` receives
   the complete three-task deterministic bid vector emitted for rank
   `(j+1) mod m`; strata of size zero or one are unchanged. Use this same
   handle-level cyclic permutation under all four input-row replicas. Apply it
   after evaluation bids are emitted and before SP-RDA keys are formed. This
   preserves the bid-vector multiset and task columns while cutting agent
   association before the common allocator.
6. `RC-MIP`: offline reward-complete mixed-integer ceiling maximizing the actual
   three-tick `J` relative to the common history. It is evaluated once per base
   world and never supplies an action, label, feature, threshold choice, or
   training signal to another arm.

Zeroing `G-RELEASE` bids is algebraically identical to `ZERO-RDA` under the common
mapper and tie rule. Confirming that equality is an implementation diagnostic.
`G-RELEASE-ZERO-RDA` and `G-RELEASE-G-PERMUTE` are controlled bid-channel
interventions, not formal mediation estimators: they can support value from
nonzero correctly agent-associated ranks, not identify which feature supplied it.

### Stage 2: conditional component cut

Stage 2 may run only if every Stage-1 release condition below holds. It adds four
separately trained learned arms on the already frozen distributions:

1. `P-RELEASE`: real pressure slots; release all survivors.
2. `G-FIXEDLEASE`: generic bids plus a frozen local lease. Retain a survivor iff
   its previous role is real and
   `c_i[p_i]/(max_r c_i[r]+1e-6) >= 0.85`; otherwise release it. The rule is
   fixed before data and sees no global condition or reward.
3. `G-LEASE`: generic bids plus learned adaptive leases.
4. `P-LEASE`: real pressure slots plus learned adaptive leases.

The generic/pressure by release/adaptive cells identify only the two
preregistered average main-effect estimands defined below. No pressure-by-
adaptive-lease interaction support claim is defined or authorized in this
revision. `G-FIXEDLEASE` tests whether a simple local hysteresis rule is
sufficient. No Stage-2 arm may be trained speculatively, used to tune Stage 1, or
used to rescue a Stage-1 negative.

## Train, evaluation, and compute budget

The eight new paired base seeds are

`[1601,1621,1657,1669,1693,1721,1747,1783]`.

They share no model, action, world, or evaluation namespace with B1 or B2.

Training schedules are uniformly

`6->9`, `9->6`, `9->12`, and `12->9`.

The seed list and schedule order above are normative: seed order is exactly the
written list; training schedule order is `6->9`, `9->6`, `9->12`, `12->9`.
Conclusion schedule order is `9->12`, `15->12`, `12->15`, `18->15`. Every
counter-key includes the integer seed, split string `training|conclusion`, the
zero-based index in that ordered schedule list, raw index, then the named field
suffix. Raw indices are scanned in increasing numerical order starting at zero.

Each update contains exactly four trials from every
`schedule x mass x geometry x churn-necessity` cell: 4 schedules x 2 x 2 x 2 x 4
= 128 trials. Each learned arm and seed receives:

- 32 updates and 4,096 one-decision trials;
- Adam `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`, no weight decay;
- PPO clip `0.20`, value coefficient `0.5`, entropy coefficient `0.01`, gradient
  norm clip `0.5`;
- eight PPO epochs per update and sixteen minibatches of eight whole trials per
  epoch; and
- the final update-32 checkpoint only.

This is exactly `8*16=128` optimizer steps per update and 4,096 optimizer steps
per learned arm and seed. Stage 1 trains only `G-RELEASE`: 32,768 trials and
32,768 optimizer steps across eight seeds. Conditional Stage 2 trains four more
arms: 131,072 additional trials and 131,072 additional optimizer steps. The
maximum fully released program is 163,840 learned trials and 163,840 optimizer
steps. Training curves are descriptive and cannot select a checkpoint, threshold,
arm, or stage trigger.

At update `u`, assemble the 128 trials using retained base `u` from all four
training schedules, all eight mass/geometry/churn cells, and all four stochastic
action replicas. For trial `t`, define `A_t=J_t-V_old(o_t)`. Standardize the 128
advantages once using `(A_t-mean(A))/sqrt(sample_variance(A)+1e-8)` and keep them
fixed for all PPO epochs. The old policy and old critic are frozen for the whole
update. Counter-keyed minibatch-order tapes form sixteen minibatches of eight
trials in each of eight epochs.

For the one joint trial ratio already defined, optimize

`L_clip=mean_t min(ratio_t*A_t,clip(ratio_t,0.80,1.20)*A_t)`,

`L_value=mean_t (V_theta(o_t)-J_t)^2`, and

`L_total=-L_clip+0.50*L_value-0.01*H_B`,

where `H_B` is the exact per-trial-then-minibatch entropy reduction registered
above. Use Adam learning rate `3e-4`, betas
`(0.9,0.999)`, epsilon `1e-8`, zero weight decay, and global gradient-norm clip
`0.5`. There is no value clipping, replay, early stopping, validation selection,
or checkpoint selection. Only update 32 is evaluated. Because Gaussian scale is
fixed at 0.20, its entropy is constant with respect to bid means; exploration
comes from fixed sampling variance rather than a Gaussian entropy gradient.

Before any learned training, construct the complete training bank and evaluation
panel under the following finite joint-certificate law. For one shared raw base let `P` be the
pre-event roster, `A` the post-event roster, `S=P intersect A` the survivors, and
`V={FIXED-SEPARABLE,FIXED-COUPLED,REAL-SEPARABLE,REAL-COUPLED}` the four variants.
For a pre-event assignment vector `p`, define in variant `v`

`S_pre^v(p) = mean_r min(sum_(i in P) 1[p_i=r] c_pre_i^v[r]/d[r],1)`,

the exact pre-event service-only functional, and

`Q^v(p) = mean_r min(sum_(i in S) 1[p_i=r] c_post_i^v[r]/d[r],1)`,

the survivor-only retained-coverage proxy. `DUMMY` contributes zero. Let

`R^v(p)=max_a J_v(a;p)` and
`K^v(p)=max_(a: a_i=p_i for every i in S) J_v(a;p)`.

All maxima range over one task or `DUMMY` per active agent. `J_v(a;p)` is exactly
the registered three-tick physical return, with history `p` supplying the handoff
indicator. Order pre-event agents by the base world's opaque-handle tie rank and
encode tasks as `0,1,2,DUMMY=3`. Define the unique mixed-radix history rank

`rank(p)=sum_j code(p[h_j])*4^(|P|-1-j)`.

Every optimization below is a fixed-small offline MIP with certified absolute
objective gap at most `1e-9`. The routine executes at most these 25 logical solver
calls in exactly this order:

1. Calls 1--4 compute `S_star^v=max_p S_pre^v(p)` in fixed variant order
   `FIXED-SEPARABLE`, `FIXED-COUPLED`, `REAL-SEPARABLE`, `REAL-COUPLED`.
2. Call 5 minimizes `Delta(p)=max_v(S_star^v-S_pre^v(p))` over one shared history
   and records the certified optimum `Delta_star`. This call has no post-event
   assignment or treatment arm.
3. Call 6 jointly chooses one shared history `p` and one all-survivors-kept
   post-event assignment per variant, subject to
   `Delta(p)<=Delta_star+0.02`, and maximizes their minimum physical return `t_K`.
   Call 7 repeats those constraints with `t_K>=t_K_star-1e-9` and minimizes
   `rank(p)`; its unique history is `p_KEEP`.
4. Call 8 chooses one shared history `p` that satisfies the same shared-regret
   bound and differs from `p_KEEP` on at least one survivor, minimizing
   `q_W=max_v Q^v(p)`. Call 9 repeats with `q_W<=q_W_star+1e-9` and minimizes
   `rank(p)`; its unique history is `p_SWITCH`.
5. Calls 10--25, in the same fixed variant order, compute exactly
   `R^v(p_KEEP)`, `K^v(p_KEEP)`, `R^v(p_SWITCH)`, and `K^v(p_SWITCH)`.

The shared history pair qualifies only if, for every variant,

- both histories satisfy `Delta(p)<=Delta_star+0.02`;
- every survivor's old role is `DUMMY` or has positive post-event capability;
- `R^v(p_KEEP)-K^v(p_KEEP)<=0.01`; and
- `R^v(p_SWITCH)-K^v(p_SWITCH)>=0.10`.

The final inequality implies that every assignment within `0.01` of the SWITCH
ceiling changes at least one survivor role. Failure of an exact optimization
problem to find a qualifying shared pair is a registered certificate miss even if
another search heuristic might have found one. A timeout, missing optimality
certificate, numerical failure, or deviation from the fixed call/objective order
is instead a preactivity CM engineering failure: stop panel construction and do
not relabel it as a certificate miss or advance to another raw index.

For the training split, in each seed and training schedule scan shared raw-base
indices `0,...,95` in ascending counter-keyed order and retain the first 32 joint
successes. At update `u=0,...,31`, use retained base `u` once for each of its eight
`mass x geometry x churn` cells and execute four counter-keyed stochastic action
replicas per cell. Across four schedules this is exactly 128 whole trials per
update and 4,096 per seed. The four action replicas are nested training exposures,
not distinct physical worlds or analysis units.

For the conclusion split, in each seed and conclusion schedule scan shared raw-base
indices `0,...,63` and retain the first 24 joint successes. There is no solver
restart, threshold relaxation, randomized retry, variant-specific history,
independent variant retention, or top-up beyond the registered cap. Fewer than 32
training successes or 24 conclusion successes makes that seed-schedule bank
incomplete: do not train a learned arm and return panel infeasibility before
scientific activity.

Across both disjoint splits the complete ceiling is 5,120 shared raw bases, 20,480
derived variant records, and 128,000 certificate-solver calls. The training bank
contains 1,024 retained shared bases, 8,192 physical cell-worlds, and 32,768
stochastic trials. Every actual call and outcome is recorded inside the 90-minute
Stage-1 envelope. Certificate objectives and ceiling values define the frozen
training distribution but are never supplied as observations, labels, rewards,
actions, or auxiliary losses.

For a retained conclusion success, the eight unrestricted values
`R^v(p_KEEP)` and `R^v(p_SWITCH)` from calls 10--25 are the retained `RC-MIP`
ceiling outputs and are reused exactly; the 6,144 retained conclusion ceilings are
a tagged subset of the certificate-call ledger, never additional or recomputed
solver calls.

Conclusion schedules are:

- seen-range reference: `9->12` and `15->12`;
- above-range primary: `12->15` and `18->15`.

For each seed, use 24 disjoint paired base worlds in every
`schedule x mass x geometry x churn-necessity` cell: 768 base worlds per seed.
Evaluate every executable arm/intervention under exactly these four active-agent
row orders: (0) ascending opaque-handle rank; (1) descending opaque-handle rank;
(2) Fisher-Yates applied to the ascending list using namespace
`(seed,"conclusion",schedule_index,raw_index,"agent-row-order",2)`; and (3) an
independent Fisher-Yates permutation using the identical key with final component
`3`. These two random row-order tapes depend on the base world and replica only,
not arm, mass, geometry, or churn-history label. They are reused unchanged across
all paired derivatives. Map outputs back to handles and average replicas before a
world enters a seed estimand. Training agent-row orders are independent
Fisher-Yates permutations keyed by
`(seed,"training",schedule_index,raw_index,"agent-row-order",action_replica)` and
shared across paired mass/geometry/churn derivatives and learned arms. `RC-MIP` is
computed once per retained base world. Stage 1 therefore has 3,072 row-order replicas per
executable policy/control/intervention per seed. With `ZERO-RDA`, `FROZEN-RDA`,
`HANDOFF-RDA`, `G-RELEASE`, and `G-PERMUTE`, this is 15,360 executable evaluations
per seed and 122,880 across eight seeds. The 6,144 retained-world `RC-MIP` values
are the tagged unrestricted outputs already computed by the joint-certificate
routine; do not solve or count them twice.

The learned arms have identical network widths, training trials, optimizer steps,
minibatch reuse, and hyperparameters. Fixed controls intentionally use no training;
they receive the same observation, `SP-RDA` candidate-edge construction, immutable
heap rule, action epoch, and physical service horizon, so the learned claimant has
strictly more capacity and training cost rather than an artificial disadvantage.
Stage-2 learned contrasts are parameter-, exposure-, and optimizer-matched.

All arms receive one decision at the same physical event and the same three service
ticks. Within a given event, allocator work follows the same frozen `SP-RDA` rule
for every arm. Lease arms may have fewer free-agent edges as a physical
consequence; report both `N` and `|U|`, and compare work against `E<=3|U|` rather
than padding it with forbidden repeated rescoring. Report training CPU/wall time,
peak RSS, candidate-edge/key/heap/residual counters, learned forward operation
counts, and full event-decision latency p50/p95 for `N={6,9,12,15}`.

Also run a non-rewarded, inference-only complexity audit at
`N={15,30,60,120}`. Its immutable source is retained-success index zero: the first
jointly certified conclusion raw base, in ascending raw-index order, for seed
`1601` and conclusion schedule index 2, namely `12->15`. Let `r_star` denote that
retained base's actual raw-candidate index. Use its `FIXED_MASS`, `COUPLED`,
`SWITCH_REQUIRED` derivative. For `G-RELEASE` and `G-PERMUTE`, use the seed-1601
update-32 `G-RELEASE` checkpoint. If the corresponding seed-schedule conclusion
bank is incomplete, Stage-1 activity does not begin and the audit source is
unavailable; raw candidate zero is never substituted merely because its index is
zero.

For scale factor `q in {1,2,4,8}`, clone original post-event handle
`h in {0,...,14}` into `(h,k)`, `k in {0,...,q-1}`, with cloned capacity `c[h]/q`
and copied history/status fields. Define the unique clone opaque-handle rank as

`rank_q(h,k)=q*h+k`.

The clone rank is external and is never a neural input. Use ascending clone-rank
input order for every warmup and timed audit call; no row-order randomization is
performed in the timing audit. Retain task demand and event kind and recompute
only the registered global `N` feature. Thus the audit preserves total task-wise
mass and has exactly `15q` addressable agents without using reward or an optimal
action.

Before panel construction or learned training, CM must freeze one audit
environment: host class, numerical precision, process and thread settings,
allocator/model execution mode, timer, and timer-resolution treatment. That
configuration is immutable through all Stage-1 statistical and timing activity
and cannot be selected or changed after observing a checkpoint, return, or
preliminary timing.

For each `N` and executable Stage-1 arm, perform 64 untimed warmup calls and then
256 sequential timed full forward-plus-allocation calls, rebuilding candidate
edges and the heap each call; do not batch repeats. It excludes environment
trajectories and the offline ceiling and cannot select a model or threshold. For
every timed repeat, measure `M_dep(N)` using exactly the machine-word definition
registered in the common complexity contract. An edge record contributes the
total machine words occupied by all of its live fields, not one abstract edge
element. For each arm and `N`, every repeat must satisfy `M_dep(N)<=1024N`;
compute the median over the 256 repeats of `M_dep(N)/N`; that median must be at
most twice the corresponding `N=15` median. No separate tensor-element,
container-count, or edge-object-count memory metric enters the release gate.
Those quantities may be reported only as decompositions. The total-process
2-GiB peak-RSS condition remains unchanged. For
one arm and `N`, sort the measured durations as

`t_(1) <= ... <= t_(256)`

and define `p95(N)=t_(244)` because `ceil(0.95*256)=244`. Use these exact p95
values for both absolute latency gates and every per-arm doubling ratio
`p95(2N)/p95(N)`. For every repeat require all analytic operation guards above,
no `N x N` allocation or learned object, and the exact machine-word predicate
above. The
practical latency gates are full event-decision p95 at `N=15 <=25 ms`, full event-
decision p95 at `N=120 <=100 ms`, and every measured full-decision doubling ratio
`p95(2N)/p95(N) <=2.75` for `N=15,30,60`. Report allocator-only timing as a
decomposition, not as a substitute. The analytic operation guards, not empirical
timing alone, establish the complexity class. The offline ceiling is resource-
unmatched and excluded from these bounds.

Stage-1 resource envelope, including the inference-only scaling audit, is 2 GiB
peak RSS and 90 minutes. Conditional Stage 2 has an additional 3-hour, 4-GiB
envelope. The complete formal program therefore remains below the project
eight-hour cap. It performs no hypothetical trajectory search and has no
candidate library beyond the frozen arms. A launcher, dependency, implementation,
or resource failure before question-relevant output returns to CM for unchanged-
science repair. Exceeding the registered inference bound after valid data is an
algorithm-cost observation, not evidence against the learned statistical effect.

## Observables and analysis

For every registered contrast, average row-order replicas within base world,
base worlds within cell, and the contrast's registered cells with equal weight
within seed to obtain `D_s`, `s=1,...,8`. The eight seeds are the independent
analysis units. Let `Dbar=mean_s D_s` and `SE=sd_s(D_s)/sqrt(8)`. Report all eight
paired seed contrasts, `Dbar`, standard deviation, and the two-sided 95%
Student-`t` interval `Dbar +/- t_(0.975,7)SE`. Its lower endpoint is used wherever
a superiority condition below requires a positive lower endpoint.

An explicitly designated one-sided 95% noninferiority lower bound is
`Dbar-t_(0.95,7)SE`; an explicitly designated one-sided 95% recovery upper bound
is `Dbar+t_(0.95,7)SE`. Practical equivalence uses the 90% interval
`Dbar +/- t_(0.95,7)SE` and passes only when both endpoints lie strictly inside
`[-0.03,+0.03]`; otherwise an unsupported small effect is unresolved, not
equivalent. Point-estimate floors such as `0.05` and `0.03` are practical release
thresholds; a confidence endpoint above zero does not assert that the population
effect itself exceeds the point-estimate floor.

The statistical superiority and noninferiority components of Stage 1 form an
intersection-union test: their null is that at least one required component fails,
and all must pass, so this single composite statistical assertion needs no
multiplicity adjustment. The full seven-condition release rule is a conjunctive
scientific/operational decision that also contains descriptive assignment and
engineering gates; those gates are not confidence-controlled hypotheses. Separate
geometry, pressure, lease, subgroup, or other claims retain marginal intervals
unless a distinct simultaneous family and correction is preregistered.

Primary observables are `J`, ceiling regret `GAP=J_RC-MIP-J_arm`, `Trec`, survivor
switch fraction, dummy fraction, per-task/per-tick service and waste, assignment,
and physical action disagreement under bid interventions.

### Stage-1 estimands and release conditions

The primary learned-value contrast is

`L15 = J[G-RELEASE]-J[HANDOFF-RDA]`

at active `N=15`, `COUPLED` geometry, equally averaging both event schedules,
mass regimes, and churn-necessity cells. Stage 2 is released only if all of these
hold:

1. `L15` has mean at least `0.05` and the lower endpoint of its two-sided 95%
   interval is above zero.
2. In `FIXED_MASS`, coupled `N=15`, the mean learned advantage is at least `0.03`
   and the lower endpoint of its two-sided 95% interval above zero. This prevents
   added capacity alone from opening the gate.
3. In `SWITCH_REQUIRED`, coupled `N=15`, `G-RELEASE-HANDOFF-RDA` has mean at least
   `0.03` and the lower endpoint of its two-sided 95% interval above zero; in
   `KEEP_OPTIMAL`, its explicitly one-sided 95% noninferiority lower bound is above
   `-0.03`. Learning must improve the hard repair cell without materially harming
   the keep cell.
4. On the same primary panel, `G-RELEASE-ZERO-RDA` has mean at least `0.05`, while
   each of `G-RELEASE-FROZEN-RDA` and `G-RELEASE-G-PERMUTE` has mean at least
   `0.03`; the lower endpoint of every corresponding two-sided 95% interval is
   above zero.
5. G versus each of ZERO, FROZEN, HANDOFF, and PERMUTE satisfies the exact
   finite-panel assignment-disagreement rates defined under Activity boundaries:
   overall rate at least `0.20` and each churn-specific rate at least `0.10`.
6. `RC-MIP-HANDOFF-RDA` has mean at least `0.05` and the lower endpoint of its
   two-sided 95% interval is above zero, so the primary panel contains unrestricted
   physical headroom. Precisely, for seed `s`,
   `D_RC,s=equal_cell_mean(J[RC-MIP]-J[HANDOFF-RDA])` at post-event `N=15`,
   `COUPLED`, equally weighting the two `N=15` schedules, both mass regimes, and
   both churn histories. Apply the mean and interval rule to these eight seed
   values. This does not establish headroom reachable through `SP-RDA`.
7. Every Stage-1 executable arm satisfies the `SP-RDA` edge/key/heap/residual and
   no-dense-path operation guards, the `N=15` full event-decision p95 is at most
   `25 ms`, the `N=120` full event-decision p95 is at most `100 ms`, every registered
   latency doubling ratio is at most `2.75`, and the registered `M_dep` machine-
   word and total-RSS memory gates pass.

For seed `s`, define `L12_s` as the equal-cell mean of

`J[G-RELEASE]-J[HANDOFF-RDA]`

restricted to post-event `N=12`, `COUPLED` geometry, schedules `9->12` and
`15->12`, both mass regimes, and both churn histories. Define the above-range
change as

`D_range,s=L15_s-L12_s`,

where `L15_s` is the registered primary seed-level `N=15` contrast. One passing
`N=15` point supports only one-point above-range generalization.

For seed `s`, define the geometry modifier

`D_geometry,s=equal_cell_mean((J[G]-J[HANDOFF])_COUPLED-(J[G]-J[HANDOFF])_SEPARABLE)`

over schedules `12->15` and `18->15`, both mass regimes, and both churn histories,
using paired derivatives of the same retained raw bases. A geometry-specific
learned-effect clause is permitted only if `mean(D_geometry)>=0.03` and the lower
endpoint of its two-sided 95% Student-`t` interval over the eight
`D_geometry,s` values is above zero. This is an `N=15` effect-modification claim
only, not identification of a particular learned mechanism. Report ceiling gaps
descriptively; their difference relative to a common comparator is algebraically
redundant with the corresponding return contrast.

### Stage-2 pressure conditions

Use compact arm names `GR=G-RELEASE`, `PR=P-RELEASE`,
`GF=G-FIXEDLEASE`, `GA=G-LEASE`, and `PA=P-LEASE`. Within each seed, average row
orders within worlds and worlds within registered cells before arm differences.
For `M in {REAL_MASS,FIXED_MASS}`, define

`D_rho^M=0.5*((J[PR]-J[GR])+(J[PA]-J[GA]))`,

equally averaged over both `N=15` schedules, both geometries, and both churn
histories within `M`. Define

`I_rho=D_rho^REAL_MASS-D_rho^FIXED_MASS`, and

`D_rho^COUPLED=0.5*((J[PR]-J[GR])+(J[PA]-J[GA]))`,

equally averaged over both `N=15` schedules, both mass regimes, and both churn
histories restricted to `COUPLED`. A finite-budget analytic-pressure effect is
supported only if:

1. `mean(D_rho^REAL_MASS) >= 0.03` with the lower endpoint of its two-sided 95% interval
   above zero;
2. `mean(I_rho) >= 0.03` with the lower endpoint of its two-sided 95%
   interval above zero;
3. the 90% interval for `D_rho^FIXED_MASS` lies strictly inside
   `[-0.03,+0.03]`; and
4. the explicitly one-sided 95% lower endpoint for `D_rho^COUPLED` is greater
   than `-0.03`.

Pressure is deterministic from visible sums and demand. Even this full pattern
supports only an optimization/inductive-bias benefit, not new information or
necessity.

### Stage-2 adaptive-lease conditions

For a world with survivor set `S`, define realized switch fraction

`W[a,p]=(1/|S|)*sum_(i in S) 1[a_i != p_i]`,

including transitions to or from `DUMMY`. For adaptive arm `a` and its eligible
survivor set `L(o)`, define the pre-threshold world-level lease score

`P_a(o)=(1/|L(o)|)*sum_(i in L(o)) p_a,i(o)`.

Define its executed evaluation lease fraction as

`Lambda_a(o)=(1/|L(o)|)*sum_(i in L(o)) 1[p_a,i(o)>=0.5]`.

Lease estimands are evaluated only on the prospectively defined lease-opportunity
worlds, so `L(o)` is nonempty. All following effects use `N=15`, `COUPLED`, the
frozen lease-opportunity worlds, and equal weight over both schedules and mass
regimes. For `C in {KEEP,SWITCH}`, define

`D_lease^C=0.5*((J[GA]-J[GR])+(J[PA]-J[PR]))`.

Define

`D_switch^KEEP=0.5*((W[GR]-W[GA])+(W[PR]-W[PA]))`,

`D_Trec^SWITCH=0.5*((Trec[GA]-Trec[GR])+(Trec[PA]-Trec[PR]))`,

`D_prob=0.5*((P_GA^KEEP-P_GA^SWITCH)+(P_PA^KEEP-P_PA^SWITCH))`.

For each paired KEEP/SWITCH raw base define

`D_ell,exec=0.5*((Lambda_GA(o_KEEP)-Lambda_GA(o_SWITCH))`
` +(Lambda_PA(o_KEEP)-Lambda_PA(o_SWITCH)))`,

reduced using exactly the existing lease weighting: row replicas within world,
worlds within opportunity cell, equal weight over the two `N=15` schedules and
two mass regimes, one value per seed, then the eight seed values with `df=7`.

Finally define

`D_fixed=J[GA]-J[GF]`, equally averaging both mass regimes, both schedules, and
both churn histories on the same opportunity panel. Adaptive release is supported
only if:

1. `mean(D_lease^KEEP)>=0.03` and its two-sided-95 lower endpoint is above zero;
2. `mean(D_switch^KEEP)>=0.10` and its two-sided-95 lower endpoint is above zero;
3. the one-sided-95 lower endpoint for `D_lease^SWITCH` is greater than `-0.03`;
4. the one-sided-95 upper endpoint for `D_Trec^SWITCH` is at most `0.25` physical
   ticks;
5. `mean(D_ell,exec)>=0.20` and its two-sided-95 lower endpoint is above zero; and
6. `mean(D_fixed)>=0.03` and its two-sided-95 lower endpoint is above zero.

Report `D_prob` and its marginal interval descriptively. It does not enter
adaptive-lease support because a pre-threshold probability difference can be
behaviorally inert under the registered deterministic evaluation threshold.

Fewer switches without the registered `J` and `Trec` conditions is fixed inertia,
not supported adaptive persistence. No service-only noninferiority claim is
authorized; per-task and per-tick service remain descriptive observables. A
supported adaptive result identifies a learned one-event retain/release policy
that improves registered KEEP return and reduces KEEP switching, executes
materially more retention in KEEP than SWITCH, remains noninferior in SWITCH
physical return and recovery time, and exceeds the registered fixed local lease.
It does not establish service-only noninferiority, durable memory, or typed
lifecycle state.

### Serial Stage-2 inference

All Stage-2 algorithms, function classes, optimizer laws, seeds, random
namespaces, panels, estimands, margins, and tests in this v7 composite are frozen
before Stage-1 activity. Their potential outputs are mathematically defined even
when Stage 2 is not executed. Let `A1` be the complete seven-condition Stage-1
release event and let `A2_pressure` and `A2_lease` be the complete corresponding
Stage-2 support conjunctions above. The reportable serial events are exactly
`A1 AND A2_pressure` and `A1 AND A2_lease`.

Stage-2 Student-t intervals are marginal under the predeclared seed-generating
law. No 95% coverage conditional on `A1` and no unbiased conditional-on-passage
effect estimate is claimed. For a true Stage-2 null `H2`,
`Pr(A1 and reject H2 | H2) <= Pr(reject H2 | H2)`; the serial gate therefore does
not increase the nominal marginal false-positive probability of its frozen
Stage-2 test. Pressure and adaptive-lease support are separate marginal claim
families; neither is a simultaneous two-family claim. No architecture, optimizer,
seed, panel, margin, test, or analysis choice may change after observing `A1`.

## Activity boundaries

After the finite panel is frozen, a `contested bid world` is one in which
`ZERO-RDA`, `FROZEN-RDA`, and `HANDOFF-RDA` produce at least two distinct full
assignments and at least one of them is `0.05` or more below `RC-MIP`. Never reject,
replace, or top up a retained world using ZERO, FROZEN, HANDOFF, G, PERMUTE, or
ceiling outcomes. Compute the contested count only after panel freeze.

A primary opportunity cell is exactly one
`seed s x conclusion schedule h x mass m x COUPLED x churn c` combination, where
`h in {12->15,18->15}`, `m in {FIXED_MASS,REAL_MASS}`, and
`c in {KEEP_OPTIMAL,SWITCH_REQUIRED}`. Each such cell has 24 retained worlds. Every
one of the eight cells within each seed must contain at least 16 contested worlds;
otherwise the conjunctive Stage-1 release is non-identifying and Stage 2 is barred,
while completed contrasts remain reportable.

For each `X in {ZERO,FROZEN,HANDOFF,PERMUTE}`, define within every primary cell

`q_X[s,h,m,c] = count_w 1[a_G(w) != a_X(w)] / count_w 1[w contested]`.

Assignments are the opaque-handle-mapped canonical assignments. The four row-order
replicas must agree after mapping; otherwise that arm-world input is unavailable
rather than counted as agreement or disagreement. Define

`q_X_all = mean_(s,h,m,c) q_X[s,h,m,c]` and
`q_X_churn[c] = mean_(s,h,m) q_X[s,h,m,c]`.

Stage-1 condition 5 requires `q_X_all>=0.20` and both churn-specific values
`q_X_churn[c]>=0.10` for every `X`. These are descriptive equal-cell-weight gates,
not binomial confidence claims.

Activity is estimand-specific. A completed contrast becomes question-relevant
when all of its arms, paired worlds, mappings, observables, and opportunity
conditions are complete. The conjunctive Stage-1 release decision becomes
identifying only when every input to all seven conditions, all eight final
checkpoints, and the complete scaling audit are available. Actual learned bids
need not vary or change an action: a constant or behaviorally inert treatment is
a negative result once its registered opportunity exists. A prelaunch realization
that instantiates a dense path or violates the analytic edge/heap bound is not this
treatment and returns to CM for unchanged-science correction before activity; it
is not a negative scientific observation.

Stage-2 activity begins only after the Stage-1 release is recorded and all four new
learned arms complete all eight final checkpoints and registered panels. A world
has a lease opportunity iff at least one survivor `i` has a real old role with
`c_i[p_i]>0`, retaining `i` on that role is legal, and the release-all structural
graph contains at least one edge `(i,q)` with `q!=p_i`, `c_i[q]>0`, and
`delta0[q]>0`. Every primary opportunity cell defined above must contain at least
16 such worlds per seed.

For pressure activity, in every
`seed x N=15 conclusion schedule x REAL_MASS x geometry x churn` cell, the 24
worlds must contain at least two pressure vectors whose `L_infinity` distance is
at least `1e-6`. A constant lease or pressure response after these exact
opportunities is a result, not non-identification.

Missing arms, cells, paired worlds, opportunity support, ceiling output, physical
ticks, row mapping, or scaling counters prevents only the comparison or release
decision that consumes that input. It does not erase a completed contrast and is
neither a negative treatment response nor evidence for another comparison. Before
the relevant activity boundary it is CM engineering work. No observed treatment
response is itself required for activity.

## Interpretation and exact no-rescue rules

1. If any Stage-1 release condition fails, do not train Stage 2. Pressure, leases,
   extra seeds, tuning, more widths, B1 support, or B2 cannot rescue this treatment.
   The family has not shown learned scalable allocation value on its declared
   high-information surface.
2. If ZERO, FROZEN, or HANDOFF matches G and is close to the ceiling, retain
   `SP-RDA` only as a structured operations-research controller; learned
   coordination is unsupported. In particular, beating ZERO or FROZEN cannot
   rescue failure against HANDOFF.
3. If G fails but all `SP-RDA` arms are far from the ceiling, the combined tested
   bidder/allocator package leaves unrestricted physical headroom. `RC-MIP` does
   not distinguish inadequate bid learning from an `SP-RDA` reachability limit.
   More actor seeds are not the next action; attributing the gap requires a new,
   preregistered best-reachable-`SP-RDA` diagnostic, and changing the allocator is
   a new treatment.
4. If G helps at `N=12` but not `N=15`, do not claim above-range robustness or run
   Stage 2. In-range value does not rescue extrapolation failure.
5. If the learned gain occurs only in `REAL_MASS`, extra capacity remains sufficient
   and the fixed-mass release condition fails.
6. If zeroing, using either fixed priority, or permuting bids does not materially
   reduce value and change assignments after contested opportunities exist,
   semantic learned bidding is unsupported even if a weaker comparator contrast
   is positive.
7. Delete the pressure claim if any of the four registered pressure-support
   conditions fails: the `REAL_MASS` average effect, the real-minus-fixed
   interaction, the aggregate `FIXED_MASS` equivalence condition, or the
   `COUPLED` noninferiority condition. A passing result supports only the
   registered equal-cell-average finite-budget pressure effect and mass-regime
   interaction. It does not support a positive coupled-geometry pressure effect,
   cellwise fixed-mass invariance, or homogeneity across geometry, schedule, or
   churn cells. Report cell-specific heterogeneity descriptively. It defeats the
   pressure claim only through failure of one of the four prospectively defined
   aggregate conditions; no unregistered cellwise gate may be applied after
   observing results.
8. If adaptive leases reduce switches but violate `SWITCH_REQUIRED` physical-
   return or recovery noninferiority, delete adaptive persistence. Total return
   in KEEP, switch reduction alone, or comparison only with release-all cannot
   rescue it.
9. If adaptive lease does not beat the frozen lease, simple local hysteresis remains
   sufficient; added gate complexity receives no claim.
10. If only `RC-MIP` performs well, there is no scalable learned survivor. The
    ceiling cannot become a candidate or teacher after the fact.
11. If any executable arm constructs more than `3N` task edges, rekeys a surviving
    edge, rescans all remaining pairs after a placement, instantiates an `N x N`
    allocation/learned object, exceeds the heap-operation bound, or uses an exact
    fallback, it does not instantiate this treatment. A positive return cannot
    rescue the forbidden realization; CM must correct it without changing science.
12. The toy must retain every positive-capability edge to every initially deficient
    task. Excluding any such edge makes the affected result unavailable, even if
    ZERO, FROZEN, or G performs well. Do not add a reward/oracle/condition-guided
    neighbor selector after seeing the result.
13. Any decoder access to reward, future facts, condition labels, or ceiling output
    invalidates affected contrasts; more seeds cannot repair leakage.
14. Per-agent/per-edge PPO ratios, an outcome-dependent latent mask, division of
    the joint log probability by latent count, or replication of one team return
    changes the treatment. A positive result cannot rescue that credit-path defect.
15. Exceeding 96 training or 64 conclusion shared raw bases per seed-schedule, or
    25 logical certificate-solver calls per raw base, using variant-specific
    histories or retention, relaxing a certificate, or topping up a bank from
    Stage-1 arm/intervention outcomes changes the target law. Missing joint-
    certified bases make the split incomplete; they may not be repaired after
    viewing results.
16. Equivalence is claimed only by the registered 90% interval rule. All other
    imprecise effects remain unresolved.
17. If the analytic complexity guards pass but a registered practical latency or
    memory-scaling gate fails, the statistical effect remains reportable but Stage
    2 and the kinematic/UAV bridge are not released. Faster hardware, batching, an
    exact fallback, or an unregistered pruning rule cannot rescue it.

Reconsidering a stopped branch requires a scientifically new surface or mechanism
with a reason independent of this result, not a relabeled retry.

## Strongest alternative explanation

The strongest alternative is that residual-demand arithmetic plus a fixed
history/handoff-aware priority already supplies the useful coordination; the
learned set network merely recovers the known three-tick contribution difference
and perturbs a structured controller. Even when learned bids beat HANDOFF, a second
alternative is finite-budget fit to this certificate-conditioned template bank
rather than transferable population composition. The ZERO/FROZEN/HANDOFF controls,
bid-association cut, exact ceiling, equal-mass geometry pairs, fixed-mass
above-range panel, and paired keep/switch construction bound those explanations
without eliminating host specificity.

V7 adds a sharper alternative: value may be specific to histories selected as the
best shared minimax-regret compromise across four deliberately crossed capability
variants, rather than histories generated by an operational pre-churn allocation
policy. The experiment may identify learned value conditional on that target law;
it cannot claim that the history law itself is operationally optimal in any one
variant or representative of deployed fleet history.

## Claim ceiling and bridge

The maximum Stage-1 positive claim is:

> In this constructed three-task, one-event fleet-allocation surface, one shared
> sum/attention policy trained at `N={6,9,12}` emitted agent-associated bids that,
> through a common sparse single-pass reward-input-blind residual-demand auction
> conditional on those bids, with `E<=3N`, analytic `O(N log N)` deployment time,
> and linear edge memory, achieved the following bounded result. On the coupled-
> geometry `N=15` primary estimand—equally averaging the two above-range schedules,
> both mass regimes, and both certified churn histories—the registered paired-seed
> mean return of `G-RELEASE` exceeded `HANDOFF-RDA`, `ZERO-RDA`, `FROZEN-RDA`, and
> the same-checkpoint cyclic `G-PERMUTE` intervention by their respective
> preregistered materiality and interval conditions. Separately, `G-RELEASE`
> exceeded `HANDOFF-RDA` in the coupled fixed-mass subgroup and in the coupled
> `SWITCH_REQUIRED` subgroup, and was noninferior to `HANDOFF-RDA` in the coupled
> `KEEP_OPTIMAL` subgroup. Its handle-mapped assignments differed from every
> registered control/intervention at the required contested-world rates, and the
> complete decision procedures passed the registered operation, machine-word
> memory, total-RSS, and latency gates. The underlying raw bases and history pairs
> were jointly certified under the shared minimax-regret pre-service benchmark
> across both mass regimes and both geometries before learning, but the primary
> superiority claim itself is restricted to coupled geometry and this robust-
> compromise-conditioned history distribution.

Equivalently, the maximum causal interpretation is finite-budget value of nonzero,
correctly agent-associated learned bid vectors through the exact common SP-RDA,
relative to the named fixed priority rules and interventions, on the registered
coupled `N=15` aggregate panel, with a separately supported fixed-mass and churn-
necessity result only against `HANDOFF-RDA`. The Stage-1 release does not establish
that the selected shared histories are individually near-optimal or representative
of an operational pre-event allocator. It does not establish
fixed-mass superiority over `ZERO-RDA`, `FROZEN-RDA`, or `G-PERMUTE` separately.
It does not establish superiority in `SEPARABLE` geometry. A separable-versus-
coupled statement is authorized only through the separately registered
`D_geometry` effect-modification estimand. It does not claim formal feature
mediation.

A supported pressure or lease result may add only its registered finite-budget
inductive-bias or one-event adaptive-release clause. An adaptive pass requires
the executed-lease contrast and supports only one-event adaptive retain/release
value in registered `J`, switching, and recovery—not service-only noninferiority,
durable memory, or typed lifecycle retention. No outcome establishes
arbitrary-`N` performance, a growing task set, learned neighbor selection,
long-horizon MARL, decentralized execution, typed lifecycle retention, identity
authentication, variable skill period, best-reachable-`SP-RDA` performance,
feature-level mediation, UAV performance, or safety. The analytic
complexity statement applies only to the frozen three-task candidate-edge rule;
the statistical generalization statement remains one held-out point at `N=15`.
`RC-MIP` supports only the statement that unrestricted physical headroom exists;
it cannot attribute an SP-RDA deficit to the bidder because the unrestricted
optimum may be unreachable through SP-RDA's immutable-edge greedy map.

The stable toy-to-UAV interface is:

- unordered agent records with opaque external identity mapping;
- persistent task records and current demand;
- shared agent-task bid matrix plus optional survivor lease/release decisions;
- a reward-input-blind constrained allocator returning task or safe outside option;
- explicit membership events and physical handoff time.

Only a Stage-1 scalable survivor may enter Kinematic Fleet Service. The first added
physical constraint is 2-D reachability/travel time with battery-conditioned
service availability; define reachable capacity as current capability multiplied
by travel/deadline and battery feasibility. Then add relay connectivity as a
constraint or sparse hyperedge without exposing mission reward to the bidder or
allocator. Preserve the same bid/lease/assignment interface and one shared policy
across sizes. Compare on overlapping small rosters with the offline constrained
ceiling and at a held-out above-training size. Measure mission service, post-event
recovery time, energy, connectivity/safety violations, and full decision latency.

If that bridge has more than three service nodes, its candidate graph is a new
audited scientific assumption. The prospective reward-input-blind construction first
removes physically unreachable agent-task pairs, then retains at most 16 tasks per
agent by ascending physical slack
`deadline - lower_bound_travel_time`, then distance, then persistent task index;
it may not use bid magnitude, reward, oracle membership, future demand, or a
mission-condition label. Every active agent still receives a bounded list plus
the safe outside option, but not every reachable task edge is guaranteed to
survive. On overlapping fixed-small rosters, compare this sparse graph with the
dense constrained reference. If the reference's selected service uses an excluded
edge and the sparse graph loses at least `0.03` normalized service, misses a
deadline, or introduces a connectivity/safety violation, the bridge fails through
relevant-edge exclusion. Do not add a dense fallback or result-adaptive neighbor
rule; redesigning the graph is a new prospective treatment.

Promotion stops if the learned advantage disappears under the common scalable
allocator, fails above-range fixed-mass evaluation, is explained by frozen
priorities, requires reward-complete scoring, exceeds the decision-time bound, or
increases connectivity/safety violations. Relevant-edge exclusion on the audited
UAV graph is also a stop. Changing to an unrelated planner, reward-shaped edge
score, stable-slot identity embedding, per-size model, dense pairwise path, or
exact fallback silently replaces the scientific object.

## Root-to-CM Stage-1 packet

This conditional packet becomes available to Root only after the existing
same-direction ChatGPT Pro conversation returns `CLOSED` on this exact revision
and the scientific owner records its intake. Until then no CM conformance or
production release is authorized. The conditional exact handoff is:

> Construct `VNFC-B3-SCALABLE-REWARD-SOURCE-CUT-v1` from
> `docs/research/candidates/variable_n_fleet_churn/VNFC_SCALABLE_REWARD_SOURCE_CUT_SCIENCE_CARD.md`.
> Use prospective revision `SP-RDA-MATH-CLOSURE-20260812-07`.
> `SP-RDA-COMPLEXITY-CORRECTION-20260812-01`,
> `SP-RDA-MATH-CLOSURE-20260812-02`,
> `SP-RDA-MATH-CLOSURE-20260812-03`,
> `SP-RDA-MATH-CLOSURE-20260812-04`,
> `SP-RDA-MATH-CLOSURE-20260812-05`,
> `SP-RDA-MATH-CLOSURE-20260812-06`, and the prior CM production acceptance are
> superseded; preserve the allocator complexity proof but do not launch or accept
> production against either old composite. Implement the
> isolated paired generator, three-tick handoff host, strong task-to-agent
> sum/attention actor/critic, and one common reward-input-blind `SP-RDA` for
> `ZERO-RDA`, `FROZEN-RDA`, new primary `HANDOFF-RDA`, learned `G-RELEASE`, and
> same-checkpoint `G-PERMUTE`. Construct
> every positive-capability edge to each initially deficient one of the three
> tasks exactly once (`E<=3N`), key it once from frozen entry residuals and bids,
> heapify once, pop each edge exactly once without rekey/rescan, and send all
> unassigned agents to `DUMMY`. Implement the offline `RC-MIP` ceiling separately;
> it may never supply an edge, key, label, action, fallback, or training signal.
> Before learned training, derive all four mass/geometry variants and execute the
> exact 25-call shared-history certificate routine for shared raw bases in ascending
> counter-keyed order. Compute four variant-specific `S_star` values, then the
> minimum attainable shared worst-variant regret `Delta_star`; require both shared
> histories to satisfy `Delta(p)<=Delta_star+0.02`. Do not substitute the
> infeasible v6 requirement that one shared history lie within `0.02` of every
> separate variant optimum. In each seed and training schedule, scan at most 96 and
> retain the first 32 joint successes; use retained base `u` at update `u` with four
> stochastic action replicas per cell. In each seed and conclusion schedule, scan
> at most 64 and retain the first 24 joint successes. Never restart, relax, use
> variant-specific histories/retention, select with a Stage-1 arm/intervention, or
> top up. An incomplete seed-schedule returns preactivity bank infeasibility. Across
> both splits record at most 5,120 raw bases, 20,480 variant records, and 128,000
> certificate-solver calls. Tag the 6,144 retained conclusion ceiling outputs
> inside that ledger; do not recompute or double-count them. Never expose any
> certificate scalar, label, solver metadata, optimizing post-event assignment,
> or ceiling output to the learner. Intentionally expose the selected `p_KEEP` or
> `p_SWITCH` vector only through the registered previous-role one-hot because it
> defines the physical pre-event history.
> Implement the arm-specific lease-first pre-bid structural latent action and
> deterministic adaptive evaluation rule, with unused/fixed lease outputs excluded,
> the exact per-trial-then-eight-trial-minibatch entropy reduction, and exactly one
> unnormalized joint PPO ratio, clipped surrogate, centralized advantage, value
> loss, and team return per trial; never use outcome-dependent masks or per-edge/
> per-agent clipped ratios. Use the exact epsilon-free pressure formula even though
> Stage 2 remains untrained.
> No executable arm may create an `N x N` allocation/learned tensor, dynamic edge,
> dense pairwise path, exact fallback, or hypothetical trajectory search. Record
> the card's edge/key/heap/residual/memory guards before production and return their
> measured counters. Train and evaluate Stage 1 only: 32,768 learned trials,
> 32,768 optimizer steps (4,096 per seed), 768 base evaluation worlds per seed with four row-order replicas
> for each of five executable Stage-1 policies/controls/interventions: 15,360
> executions per seed and 122,880 total; the 6,144 retained ceiling values are the
> already tagged certificate outputs.
> Also run the
> frozen inference-only `N={15,30,60,120}` complexity audit from retained-success
> index zero for seed 1601 schedule `12->15`, with the exact clone ranks,
> seed-1601 update-32 G checkpoint, ascending clone-row order, pre-panel frozen
> environment, 64 warmups, and 256 repeats per size and executable Stage-1 arm;
> define p95 as sorted duration 244. Use no reward/environment trajectory or
> ceiling.
> The complete Stage-1 envelope, including certificate screening and the added
> fixed comparator, remains 90 minutes and 2 GiB; CM must reproject and accept that
> exact composite without silently expanding it. Require full event-decision p95 at
> `N=15<=25 ms`, full event-decision p95 at `N=120<=100 ms`, every latency doubling
> ratio `<=2.75`, every-repeat `M_dep(N)<=1024N`, median per-agent machine-word
> scaling at most twice the N=15 reference, and total peak RSS at most 2 GiB. No
> tensor-element or abstract edge-object count substitutes for machine words. Do
> not train or use
> `P-RELEASE`, `G-FIXEDLEASE`, `G-LEASE`, or `P-LEASE`; do not modify or initialize
> B1 or B2; do not import B1 checkpoints, rows, thresholds, or evidence. Return
> whether each estimand-specific activity boundary and the full Stage-1 release
> boundary were crossed, the exact contested/opportunity denominators and equal-
> cell assignment rates, every paired seed/cell
> contrast and conjunctive release condition, bid-intervention assignment rates,
> ceiling gaps, physical service and recovery observations, actual
> sample/optimizer/edge/heap/time/memory/latency counts, material anomalies, and
> what remains unknown. Any positive-capability edge to an initially deficient
> toy task that is excluded makes the affected result unavailable. A pre-activity
> complexity misinstantiation returns to CM for unchanged-science repair; a valid
> statistical effect that misses a practical scaling gate is reported but cannot
> release Stage 2 or the UAV bridge.

Root retains compute scheduling and portfolio authority. The packet authorizes no
Stage-2 production run, External-Pro transport, B2 change, Git action, or user
contact.
