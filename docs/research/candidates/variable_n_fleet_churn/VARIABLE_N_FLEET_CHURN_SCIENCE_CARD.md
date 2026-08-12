# Variable-N fleet-churn B1 science card

Owner: `direction:variable-n-fleet-churn` Explorer Manager  
Candidate A: `MASS-CALIBRATED-SET-ACTOR-CRITIC` (`MC-SAC`)  
Candidate B: `EVENT-TRIGGERED-ROLE-REBINDING` (`ETRR`, built on A)  
Treatment identity: `VNFC-B1-CHURNED-CAPABILITY-MATCHING-v1`

This is a prospective construct-first experiment. A missing toy, runner, model,
adapter, or joint-action decoder is CM construction work and does not change the
scientific question.

## Project-facing question

Can one shared-parameter MARL allocator, without retraining for a particular fleet
size, use either explicit fleet-mass calibration (A) or fleet-mass calibration plus
event-triggered persistent role rebinding (B) to improve at least one of:

1. post-join/drop robustness; or
2. held-out-fleet-size task performance,

relative to a capacity-matched generic mean-pooled set policy on fleet sizes that
were absent from training?

The direct variable axis is the active number of agents `N`. Training exposes only
`N in {3,5,7}`. The sole conclusion panels include static `N in {4,6}` and
within-episode membership changes that pass through those held-out sizes. Every
learned arm is one shared policy and parameterization across all of its sizes; no
per-`N` model, fine-tuning, threshold, or checkpoint is allowed.

The experiment crosses two capacity regimes so that a gain is interpretable:

- `CAPACITY_NORMALIZED`: changing `N` changes roster cardinality and the identity
  of available specialists, but total potential capacity for each task is held
  constant. This asks for robustness to set size without granting real extra mass.
- `TRUE_EXPANSION`: each joining agent brings stable additional capacity and each
  departing agent removes it. This asks whether the algorithm can exploit or
  survive genuine fleet expansion and contraction.

## Churned Capability Matching host

An episode has three allocation segments `t=0,1,2`. At `t=0` the initial roster is
installed. Between later segments the host applies the prescribed join or drop,
then asks the policy for a new allocation. A static episode holds the roster fixed
after `t=0`; all arms then hold their initial allocation. A churn episode therefore
has exactly three policy events and two exogenous membership events.

There are three persistent, task-indexed roles `r in {0,1,2}` and a dummy role
`DUMMY`. They can be read as sensing, relay, and response in the later UAV mapping,
but B1 gives them no spatial dynamics. Every active agent is assigned to exactly
one of the four roles. Multiple agents may serve the same real task, and dummy is a
safe unused/loiter assignment.

### Agent pool and capabilities

Each episode has a private pool of enough stable agent identities to realize its
three rosters. Identity handles are opaque host keys used only to preserve an
agent across events and map outputs back after row permutations. Their numeric or
text representation is never a neural input.

Each agent has a fixed raw capability vector `u_i in R^3`. Its specialty
`s_i in {0,1,2}` is balanced by constructing repeated random permutations of the
three specialty labels. Conditional on `s_i`, independently draw

- `u_i[s_i] ~ Uniform(0.80,1.00)`; and
- `u_i[r != s_i] ~ Uniform(0.15,0.45)`.

The episode demand vector is a random permutation of `(0.55,0.65,0.75)` and is
fixed for all three segments. Roster construction is independent of model arm and
is rejection-sampled only until every active roster contains at least one agent of
each specialty. Joining agents are previously unseen identities from the episode
pool; dropped identities do not return in B1. Legal join/drop subsets are sampled
uniformly under that specialty-coverage condition. Report drop and join outcomes
also by whether the changed set contains the pre-event highest-capability agent for
each task; that label is diagnostic and never conditions training or selection.

For the active roster `R_t`, the actual capacity exposed to every arm is:

- `CAPACITY_NORMALIZED`:
  `c_i[r] = 1.35 * d[r] * u_i[r] / sum_(j in R_t) u_j[r]`.
  Therefore `sum_i c_i[r] / d[r] = 1.35` for each task and segment, up to ordinary
  floating arithmetic, regardless of `N`. Survivor capacities are recomputed when
  the roster changes; this artificial renormalization is the intended control.
- `TRUE_EXPANSION`: `c_i[r] = 0.42 * u_i[r]`. Survivor capacities remain fixed,
  and adding or removing agents changes total available mass.

All random draws are counter-keyed by base seed, split, base-world index, regime,
agent identity, and field. Arm execution order cannot shift world generation.

### Observation, action, and reward

At each policy event the observation contains:

- one unordered row per active agent: its three current capacities `c_i`, previous
  role one-hot over four roles (all zero at `t=0`), and the two bits `survived` and
  `newly_joined`;
- three persistent task rows: task-index one-hot and demand `d[r]`;
- global segment index, event kind (`RESET`, `JOIN`, or `DROP`), and scalar `N/7`.

No arm sees the future roster, generator stratum, oracle action, correct assignment,
arm label, or opaque handle value. Agent rows are freshly permuted at every event.
Task indices remain stable because persistent task identity is part of candidate B.

For joint assignment `a`, let

`x_r(a) = sum_i 1[a_i=r] * c_i[r] / d[r]`,

`service_r(a) = min(x_r(a),1)`, and

`waste_r(a) = min(max(x_r(a)-1,0),1)`.

For `t>0`, let `switch(a)` be the fraction of surviving agents whose new role,
including dummy, differs from its previous role; it is zero at `t=0`. The shared
segment reward is

`reward(a) = mean_r service_r(a) - 0.10*mean_r waste_r(a) - 0.04*switch(a)`.

The same reward is delivered to every active agent. Membership changes and future
capabilities are exogenous, so an action affects only the current reward and the
next segment's previous-role field/switch cost. There is no reward shaping, hidden
task label, per-agent private reward, skill-period change, or action-dependent
churn in B1.

## Learned arms and mechanism isolation

All learned arms use the same shared agent encoder, task encoder, bid head, and
centralized set critic. The proposed implementation is:

- agent MLP: `9 -> 64 -> 64`, SiLU activations;
- task MLP: `4 -> 32 -> 32`, SiLU activations;
- one shared bid MLP applied to every agent-task pair and one shared dummy head;
- one centralized critic with the same set summaries used by that arm.

The exact common context vector has fixed width for every arm. It always includes
the mean agent embedding, task embeddings, demands, event/segment fields, and
`N/7`. Reserved extensive fields are the sum of agent embeddings and the three
log pressure ratios

`rho[r] = log((d[r]+1e-6)/(sum_i c_i[r]+1e-6))`.

The generic arm receives zeros in those reserved fields; A, the joint-decoder
control, and B receive their real values. Thus G and A have the same trainable
parameter count and raw observation information, while A supplies an explicit
intensive/extensive inductive decomposition. CM may choose the exact fixed-width
concatenation needed to realize the stated encoders, but every learned arm must have
identical trainable parameter count and hidden widths, and the emitted result must
state both.

The arms are:

1. `G-MEAN` -- generic comparator. Per-agent four-role categorical distributions
   are conditionally independent given the mean-pooled set context.
2. `A-MASS` -- candidate A. It uses the real extensive and pressure fields but the
   same factorized per-agent action distribution as G.
3. `A-JOINT` -- causal diagnostic, not a third candidate. It uses A's network and
   an exact joint coverage-aware decoder, but no persistence term.
4. `B-REBIND` -- candidate B. It uses the same A network and joint decoder, plus
   task-indexed previous bindings for event-triggered persistence.
5. `GREEDY-ORACLE` -- nonlearned reference. It enumerates the current legal joint
   assignments and selects the one with maximum actual current segment reward
   relative to its own previous allocation. It is myopic, not a horizon-optimal
   upper bound, and is never used as a training label or feature.

For access diagnosis, also compute an arm-conditioned one-step best response at
each emitted learned-arm state: enumerate the assignment with maximum current
reward using that learned arm's own previous allocation. This counterfactual is a
valid current-step ceiling for that arm and does not become an executed trajectory.

For G and A, joint log probability is the sum of per-agent categorical log
probabilities. For the two joint-decoder arms, enumerate all `4^N` assignments
(`N<=7`) and define the common learned bid contribution

`bid(a) = (1/N) * sum_i logit_i[a_i]`.

Let `coverage(a)=mean_r service_r(a)-0.10*mean_r waste_r(a)` and let
`keep(a)` be the fraction of survivors retaining their previous task-indexed role,
including dummy. The exact joint scores are

- `score_A-JOINT(a) = bid(a) + coverage(a)`;
- `score_B(a) = bid(a) + coverage(a) + 0.04*keep(a)` at `t>0`, and the same as
  A-JOINT at `t=0`.

Training samples from the exact temperature-one softmax over these scores; final
evaluation takes the maximum-score assignment. Enumeration is over handle-mapped
agents, not input-row positions. Equal-score ties use task index followed by stable
opaque handle order, so input permutation cannot select a different physical
assignment. The dummy role makes deliberate nonassignment possible.

All four learned arms are queried only at reset or an actual membership event and
hold their allocation between such events. On membership change, B rematches the
whole active roster while its `keep` term represents surviving bindings; departed
bindings disappear and new agents have no previous binding. `A-JOINT` controls for
the exact enumerator and coverage term. Therefore B versus A-JOINT is the named
persistence/rebinding contrast; B versus A alone is only an end-to-end package
contrast.

The strongest alternative explanation is that any B advantage comes from a
hand-structured coverage-aware joint action decoder, not learned persistent role
binding or mass calibration. `A-JOINT` is required to expose that alternative.

## Exact train, validation, and conclusion distributions

No even fleet size appears in training or validation.

### Training

Every training episode uses one of these active-roster sequences, uniformly:

`3->5->3`, `3->5->7`, `5->3->5`, `5->7->5`, `7->5->3`, `7->5->7`.

The two capacity regimes are equiprobable. Join/drop subsets follow the generator
above. A fresh input-row permutation is drawn at every event. Training therefore
contains batch-size-two churn among odd fleet sizes but no static episode and no
`N=4` or `N=6` observation.

Validation is reporting-only and uses the same six odd-size schedules and both
regimes on disjoint worlds. It cannot select a checkpoint, seed, model width,
threshold, or hyperparameter.

### Held-out static panel

For each capacity regime, construct 48 paired base pools per seed. Each pool yields
one static `N=4` episode and a nested static `N=6` episode obtained by adding two
agents while keeping the three demands and the first four identities/capabilities
fixed. The added specialists are balanced across tasks. This gives 192 base static
episodes per seed before permutation replication.

### Held-out churn panel

For each capacity regime and each sequence below, construct 24 disjoint base worlds
per seed:

`4->3->4`, `4->5->4`, `6->5->6`, `6->7->6`, `4->6->4`, `6->4->6`.

The first four sequences test unseen one-agent membership changes; the last two
test size-two changes while remaining entirely on held-out even sizes. This gives
288 base churn episodes per seed before permutation replication.

Every held-out base episode is evaluated greedily under four frozen agent-row
orders at every segment: stable-handle order, its reverse, and two independent
counter-keyed random permutations. Map outputs back to handles before comparison,
then average the four replicas before a world enters any seed-level estimand.
Ordinary comparisons use `rtol=1e-5, atol=1e-6`; no bit-level, serialization-byte,
or float64-identity gate exists. Report probability, assignment, and reward
differences across replicas. A material mapping disagreement is an implementation
or equivariance defect, not scientific evidence for or against A or B.

Train, validation, and test worlds, opaque identities, capability draws, model
initializations, and input-permutation tapes are disjoint and counter-keyed.

## Learning rule, matching, and smallest useful budget

All learned arms train from the shared environment reward with centralized-training
PPO; there is no oracle imitation, behavior cloning, pretraining, replay from another
direction, or arm-to-arm parameter transfer.

Use:

- Adam learning rate `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`, no weight decay;
- PPO clip `0.20`, value coefficient `0.5`, entropy coefficient `0.01`;
- `gamma=0.99`, GAE `lambda=0.95`, gradient-norm clip `0.5`;
- 32 rollout updates, 128 three-segment episodes per update;
- four PPO epochs per update, minibatch 192 event rows; and
- the final update-32 checkpoint only.

The eight paired base seeds are

`[1103,1129,1151,1171,1193,1213,1237,1277]`.

World, model-initialization, action-sampling, minibatch-order, and evaluation
namespaces are derived separately from each base seed. Arms share paired exogenous
worlds but initialize and train their own weights.

Per learned arm and seed, training is exactly 4,096 episodes and 12,288 segment
rows. Across four learned arms and eight seeds this is 393,216 training segment
rows and 8,192 optimizer steps. Validation uses 192 disjoint episodes per arm and
seed. Final evaluation uses the 480 base episodes above, each under four row-order
replicas, or 1,920 episodes per arm and seed. These counts are the smallest useful
B1 budget: eight seeds support paired uncertainty, all odd training sizes are
balanced, both held-out even sizes occur, and both one- and two-agent churn are
represented.

Capacity and resource matching are interpreted as follows:

- G versus A has the same network, parameter count, event count, optimizer work,
  and factorized decoder.
- A-JOINT versus B has the same network, parameter count, exact `4^N` enumeration,
  event count, optimizer work, and capacity/coverage calculation.
- Every learned arm receives the same episode, update, and final-evaluation budget.
- B versus G/A is an end-to-end algorithm comparison, not a compute-neutral causal
  comparison. Report training CPU seconds, peak RSS, and event inference p50/p95 at
  each `N`; do not hide the joint decoder's cost. Also report final-panel utility
  from the latest common update completed by every arm at the minimum of their
  training wall times as a secondary equal-time description.

The complete run has a 4 GiB peak-RSS and three-hour wall-time envelope on the
assigned CPU host. A resource or launcher problem does not alter the treatment and
returns to CM for unchanged-science repair. If the exact joint enumeration itself
cannot fit the envelope, that is a genuine B1 engineering-cost observation for
Root; it is not a negative robustness/performance result.

## Estimands and support conditions

For arm `a`, base seed `s`, and episode `e`, let

`J[a,s,e] = (reward_0 + reward_1 + reward_2)/3`.

Average row-order replicas within each base episode, then worlds within a seed.
The seed is the analysis unit. Retain every per-segment service, waste, switch,
assignment, joint log probability, fleet size, capacity regime, churn sequence,
and oracle reward.

The two project-facing primary estimands are:

- held-out-size performance `P[a,s]`: mean `J` over the `TRUE_EXPANSION` static
  `N=4` and nested `N=6` panels;
- churn robustness `H[a,s]`: mean of segment rewards at `t=1,2` over all held-out
  churn sequences and both capacity regimes.

Also report:

- post-churn one-step access regret `Ogap[a,s]`, defined from the arm-conditioned
  best response above rather than from the greedy oracle's different history;
- true-expansion capture
  `X[a,s]=mean_world(J[a,N=6]-J[a,N=4])` on paired nested static worlds;
- the same `N=6-N=4` change under `CAPACITY_NORMALIZED`;
- critical-versus-benign drop and relief-versus-neutral join strata;
- input-permutation probability, assignment, and reward deviations; and
- train/validation learning curves, actual parameter/step counts, resource use,
  and per-`N` inference latency.

For each contrast report the eight seed values, paired mean, standard deviation,
and two-sided 95% Student-t interval. A candidate is project-promising at B1 if,
against `G-MEAN`, it satisfies either of these independently:

1. robustness: mean `H` advantage at least `0.05` and its paired 95% lower bound
   is above zero; or
2. performance: mean `P` advantage at least `0.05` and its paired 95% lower bound
   is above zero.

Both are not required. These are materiality statements for portfolio navigation,
not universal pass/fail labels. A claim that the algorithm specifically exploits
true fleet expansion additionally requires `X` to exceed G by at least `0.03` with
a paired 95% lower bound above zero. A B-specific persistent-rebinding claim
requires B to exceed `A-JOINT` by at least `0.03` on `H` or `P`, again with a paired
95% lower bound above zero. Without that contrast, a B package advantage is
attributed to the structured joint decoder unless later evidence separates it.

Practical equivalence is supported only when the 90% paired interval for the named
contrast lies wholly inside `[-0.03,+0.03]`. Other small or imprecise patterns are
unresolved rather than relabeled as success or failure.

## Activity boundary and outcome map

Question-relevant scientific activity begins when all four learned arms from one
base seed have frozen update-32 checkpoints and have emitted a complete paired
conclusion block containing both capacity regimes, static `N=4` and `N=6`, every
one- and two-agent churn sequence, all four row-order replicas, and the greedy
oracle rows. Training loss, a partial arm, a single `N`, a launcher attempt, or a
unit check is not question-relevant output.

Interpret complete output as follows:

1. `A-MASS > G-MEAN` on held-out performance or churn robustness supports a
   finite-budget benefit from explicit intensive/extensive mass calibration in
   this host. A gain confined to `TRUE_EXPANSION` narrows the interpretation to
   using real additional capacity; a gain also present under normalization supports
   broader roster-size robustness.
2. `A-JOINT > A-MASS` but `B-REBIND ~= A-JOINT` attributes the useful increment to
   coverage-aware joint action construction, not persistent rebinding.
3. `B-REBIND > A-JOINT` on the prespecified B contrast supports event-to-event
   task-indexed binding as an additional contributor here.
4. B beating G/A while failing to beat A-JOINT leaves the end-to-end B package
   useful but does not support the named persistence mechanism.
5. High static scores but a large post-churn oracle gap identify membership-change
   recovery, not ordinary task access, as the next discriminator. Low scores for
   every learned arm with a strong oracle indicate learner/decoder access failure;
   more seeds alone are not the next action.
6. If G, A, A-JOINT, and B are practically equivalent and close to the oracle, the
   generic set policy is sufficient at this host/budget and the extra mechanisms
   receive no further investment without a harder UAV-aligned surface.
7. If all learned arms are equivalent but far from the oracle, B1 does not compare
   the mechanisms. The same EM should localize representation, action-support, or
   optimization access before any new treatment.
8. A row-order disagreement, split contamination, changed roster sequence, missing
   panel cell, wrong reward recomputation, nonfinite output, or arm-dependent world
   is non-identifying. Before the activity boundary it is CM engineering work; after
   the boundary, unaffected complete seed blocks remain observations but the broken
   contrast has no conclusion.
9. Excess latency is reported as an algorithm cost. A scientifically positive B1
   result can still be unsuitable for UAV promotion if the decoder cannot later be
   replaced by a scalable event-time allocator within the control budget.

## Toy-to-UAV development path

B1 is only the first surface. A supported candidate follows this path without
changing its core variable-`N` claim:

1. **B1 -- Churned Capability Matching.** Establish mass use and/or rebinding on
   `N=3..7`, including static held-out `N={4,6}` and in-episode joins/drops.
2. **Second surface -- Kinematic Fleet Service.** Preserve the same shared actor,
   extensive ratios, task-indexed roles, dummy role, and churn semantics, but add
   2-D travel time, battery, task service duration, and a communication-relay
   constraint for `N=4..12`. Replace toy enumeration with a scalable auction or
   min-cost-flow decoder and compare it with the exact B1 decoder on overlapping
   small rosters. Train on selected sizes, test held-out sizes and single/double
   failure or reinforcement events. Measure task utility, recovery time, energy,
   connectivity violations, and event-decision latency.
3. **Project UAV simulator.** Map agents to heterogeneous UAVs; the three task roles
   to sensing/search, communication relay, and response/delivery; raw capabilities
   to sensor quality, link budget, speed/endurance, and payload; dummy to safe
   loiter/return; and churn to failure, lost link, return-to-base, or reinforcement.
   Use one parameterization across fleet sizes. Include at least one held-out fleet
   size or an in-mission membership change, and compare mission completion,
   degradation/recovery, energy/safety constraints, and control latency against a
   matched generic set allocator and the strongest surviving structured ablation.

Only an outcome that changes selection among A, B, the generic baseline, or the
next transfer surface justifies further investment. B1 need not and does not test
variable skill period `k`; satisfying the variable-`N` axis plus either robustness
or performance is sufficient for project value.

## Claim ceiling and CM construction request

The maximum B1 claim is that, in this constructed three-task, three-segment,
`N=3..7` capability-allocation host, one shared policy using the named mass
calibration and/or role-rebinding package improves the prespecified held-out-size
performance or post-churn robustness measure at the frozen finite budget. A
B-versus-A-JOINT separation may further attribute part of the gain to persistent
role binding within this exact decoder and reward.

No B1 outcome establishes UAV performance, safety, decentralized execution,
scalability beyond `N=7`, superiority under arbitrary churn, generic MARL benefit,
variable-`k` adaptation, the necessity of HMASD skills, or the necessity of exact
enumeration. The capacity-normalized regime is an artificial causal control, and
the strongest remaining alternative is that the host's explicit coverage function
and persistent three-role ontology favor the structured decoder.

CM should construct the isolated generator, four learned arms, greedy oracle,
shared PPO train/evaluate/analyze runner, permutation mapper, and retained result
from this card. Return question-relevant activity status; complete per-seed and
per-cell observations; primary and diagnostic contrasts; actual parameter, sample,
optimizer, time, latency, and resource counts; material anomalies; and remaining
unknowns. Ordinary focused engineering checks are allowed, but there is no separate
scientific smoke run and no hash, byte-count, line-ending, receipt, or bitwise-float
gate.
