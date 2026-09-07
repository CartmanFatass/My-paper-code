Claim: One paired training instance measures whether multiplicative duration-conditioned action values improve complete work served over a same-information fully conditioned value learner on the fixed reactive two-queue task.
Binding MARL structure: (b) temporal abstraction — exogenous action holding changes successor queues, the partner's response and the value of the current allocation.

# VSPC1-K4-REACTIVE-QUEUES-B01 — frozen 2026-09-06

Class **B/EXPLORE**. Direction family selected `PRO_FINAL` by
[Convergence §§II–VII](pro_packets/20260906_reactive_queues_convergence/archive/RESPONSE.md)
at immutable commit `67f4d3837c78749cb7f7369083ecbc3ffa4b133d`; accepted in the
[decision intake](VSPC1_K4_REACTIVE_QUEUES_CONVERGENCE_INTAKE_20260906.md).
DM freezes the conforming card under the 2026-09-03 unattended object-tier delegation.
This card selects two complete arm invocations, one new root seed 401, and no extension.
Source acceptance and Root integration precede execution under the current assignment.

## 1. Question, claim ceiling and decision value

Does FACTOR help or hurt full native return against GENERIC after 256 real updates when
holding an allocation changes both queue state and the next partner action? The result may
justify explicitly selecting one or two independent training seeds in the same comparison,
or stopping automatic pursuit of this parameterization combination. It is one local learning
comparison; paired evaluation episodes are not independent training seeds.

There is one learning focal worker and one known, fixed, non-learning reactive partner.
The renewal state is Markov for this stationary control task. No partner co-adaptation,
learned termination, roster change, decentralized multi-learner credit, strict low-rank
constraint, unique sharing mechanism, stable superiority, transfer or optimality is claimed.
Both models share features. Network/initialization/optimization differences remain alternatives.
The ended public-plan, six-step, eight-context family remains ended by content.

**Headroom/baseline record:** this host has no tuned baseline set or measured upper-reference
gap. The first GENERIC curve supplies a host observation, not a tuned competence certificate.
Old B01/B02 observations, action consequences, information and budget do not match this host;
their reference 5/6 and old A01 missing headroom are not transplanted. No reference search,
baseline sweep or exact policy-class maximum precedes this B.

**MEI:** absolute normalized return 0.025, equivalent to 2.4 jobs per 48-tick episode.
This is a practical exploratory scale chosen for completed work, not an equivalence margin,
statistical-significance threshold or cross-direction investment rule.

## 2. Host, information and native consequence

Two persistent workers, two queues of capacity 4, horizon H=48 ticks, initial queues (2,2),
initial previous focal allocation h a fair random bit. External period d is fixed within
each episode at 2 or 6; training and evaluation give both periods equal episode weight.

At a renewal t, the focal observes only the current (q0,q1,h,t,d), chooses action a in {0,1},
then holds it for d ticks with no new policy inputs or intervening action choice. At **every**
tick the partner uses the current queues and **old** h: choose the longer queue, break a queue
tie by choosing 1-h. It cannot see the focal's simultaneously selected new action. Distinct
queues may each serve one existing job; coincident workers serve at most one job in total;
an empty queue serves zero. After service, each queue independently receives Bernoulli(0.7)
arrivals, clips to capacity 4 and records overflow. Finally h becomes the held focal action.
The partner may therefore change its next tick's action during a focal holding segment.
Arrival tapes and future partner trajectories are never policy inputs.

Event → ownership → information → action/credit → exposure → consequence: random arriving
work and imbalance → persistent focal/partner roles → renewal-only focal state and per-tick
partner state → held allocation and joint queue service → actual segment reward plus
successor-state TD update → complete episode work served, unused service, overflow and backlog.

Native J = total jobs served over all 48 ticks / 96. Collisions, empty queues and zero-service
ticks stay in the denominator. Final-tick arrivals cannot be served in this episode. Record
overflow, final total backlog and unused service capacity (sum of 2 minus jobs served per
tick) as descriptive consequences; none adds reward or changes normalization.

## 3. Arms and real learning

Common feature order is [q0/4,q1/4,t/48,one_hot(h),one_hot(a)], seven coordinates;
one-hot order is 0 then 1. GENERIC additionally uses [1[d=2],1[d=6]].

| Arm | Online Q | Trainable parameters |
| --- | --- | ---: |
| FACTOR | 7→24 tanh→4 biased linear feature, dotted with a learned 2×4 duration embedding | 300 |
| GENERIC | 9→28 tanh→1 biased linear scalar | 309 |

Each arm has its own initialization and one non-optimized target copy. All dense weights
use Xavier uniform, dense biases zero; FACTOR embeddings use Normal(0,0.5). The 9-parameter
GENERIC excess is retained. GENERIC has full state/duration information and nonlinear
duration interactions; this is not sharing versus no sharing or low rank versus full rank.

For u=1,…,256 collect 16 **new complete** episodes under unchanged online parameters,
eight per d. Use epsilon-greedy with epsilon_u=1−0.9(u−1)/255, uniform two-action exploration;
greedy and evaluation ties choose 0. Score both actions even when taking exploration.
Then perform exactly **one** Adam step over every actual renewal row and clear the batch.
No replay, counterfactual periods, skip transitions, modelled future rollouts or extra search.

For actual segment t→t+d, R is that segment's served jobs /96. Its successor s′ is after
the segment's final service, arrivals and h update. Nonterminal target:
y = R + Q_target(s′, argmax_a Q_online(s′,a,d), d). At t+d=48 use y=R and do not score a
terminal next action. Targets are detached; gamma=1 is the finite undiscounted task target.
Loss L=(1/16) sum_e [(1/n_e) sum_j (Q_online(s_ej,a_ej,d_e)−y_ej)^2], n_e=48/d_e.
Each episode and therefore each period has equal weight; do not divide segment reward by d.
Preserve per-update, per-period mean squared TD losses as learning descriptions.

Adam: lr=0.01, betas=(0.9,0.999), eps=1e-8, weight_decay=0; global gradient-norm clip 5.
Target equals online initially and is copied **after** updates 16,32,…,256, before next
collection/backup. Evaluation uses the updated online model. No tuning from evaluation,
best-checkpoint selection, early stopping or learning-rate selection.

## 4. Data, RNG and exposure

Root seed 401 only. Initialization streams are arm-specific. Training arrivals, initial h,
exploration decisions and exploration actions have separate named streams. Exogenous and
exploration draws are shared across arms by preassigned episode/primitive-tick slots, not
consumption order; both periods' evaluation tapes are mutually independent and independent
of training, shared across arms and checkpoints. CM records the concrete deterministic seed
mapping before outcome-bearing execution. No claim of equal initial parameters/policies.

One pair means two trained models, one independent paired training instance. Before launch
retain a machine-generated configuration/exposure line showing real trainable online
parameters, the nonzero update path and fixed budget; it may use an equivalent can-move
statement under evidence-spec §11.4. Actual initial parameter norms and final displacement
are measured during these actual calls. They are currently unknown: neither old B02 movement,
nominal lr nor an arbitrary displacement-ratio gate is a new-host measurement. No separate
movement experiment is selected. Consultation/preparation exposure remains zero in the
[machine-generated preparation record](VSPC1_K4_REACTIVE_QUEUES_PREPARATION_COUNTS_20260906.json).

## 5. Primary measurement and descriptive reading

Evaluate greedily at updates 0,32,64,96,128,160,192,224,256: 256 complete episodes per point,
128 per d on the fixed independent evaluation tapes. Primary Delta_d is FACTOR minus GENERIC
mean J at update 256; Delta=(Delta_2+Delta_6)/2. Retain both raw arm means, per-period means
and differences, initial values and every fixed curve point. Publish the endpoint episode
J values indexed by period/episode so the paired difference and evaluation noise are readable.

Normalized full AUC is trapezoidal integral over updates 0:256 divided by 256, equivalently
[0.5J_0+J_32+…+J_224+0.5J_256]/8, per period and equal-weight mean. It is descriptive and
never replaces the endpoint. No mixing with old hosts/windows or post-hoc initial-value subtraction.
Use the existing paired endpoint arrays to report conditional SE of Delta:
0.5 sqrt(s_2²/128+s_6²/128), where s_d² is sample variance of paired episode differences.
This adds no evaluation and estimates only evaluation noise for these fixed trained models,
not training-instance uncertainty or a training-population confidence interval.

**How the result will be interpreted:** a mean gain reaching MEI without material period
loss supports considering one or two new seeds; a gain with a material loss is a task-specific
tradeoff. Inside MEI gives insufficient practical-gain reason here, retaining its sign;
opposite-sign MEI challenges carrying FACTOR on this combination. Near-boundary sampling
uncertainty limits the reading. Null/adverse results do not close K4; no result automatically
extends the budget. The following branches govern this B's descriptive intake.

| Observation | Reading and recommended next choice |
| --- | --- |
| Damaged primary reward, information or update dependency, or no comparable endpoint | No dependent performance conclusion; preserve trustworthy independent observations and name the gap. No scientific negative or automatic rerun. |
| Delta >= 0.025 with neither Delta_d <= -0.025 | Favorable local native signal; may subsequently select one or two independent seeds in the same comparison, retaining every result. No automatic extra invocation. |
| Favorable mean with a period loss <= -0.025, or material opposite signs across periods | Retain mean benefit and harmed period as a tradeoff; keep weights and arms. Decide its use before selecting a follow-up; no clear use means no addition. |
| Delta <= -0.025 | Favors GENERIC in this instance; stop automatic pursuit of this FACTOR combination, without a sharing-failure mechanism or K4 closure. |
| abs(Delta) < 0.025, or evaluation precision leaves the MEI boundary unresolved | Insufficient practical-gain reason from this comparison; preserve small effects/uncertainty, no equivalence or automatic longer training/evaluation. A specific new question must justify further work. |
| Endpoint and full-curve readings differ | Report both, with endpoint primary. No winner selected from AUC, best checkpoint or initial-value gain. |

Period tradeoff qualifies the mean branches; it does not erase the mean. Read absolute returns
and changes from initialization too. Both arms low or unmoved may reveal a concrete trainer
question, not solved competence or a mandatory optimal-reference investigation. B has no
consumption state; repairs/new invocations require their actual object-tier decision and budget.

**Prediction on record (DM adopts the node's stated working prediction):** abs(Delta)<0.025
is more likely than reaching MEI in either direction; no clear two-period joint gain is expected.
GENERIC already has duration nonlinearities and shared features; no queue-specific advantage
of FACTOR is established. abs(Delta)>=0.025 contradicts the first descriptive prediction;
both Delta_d>=0.025 especially contradicts the second. Report sampling uncertainty without
rescoring a miss as a hit. Owner prediction: **not taken (unattended)** at freeze.

## 6. Work, execution budget and stop

One host × two arms × one seed. Per arm: initialization + 256×[16×48 training ticks +
one update on 256 renewal rows, 240 nonterminal] + 9×[256×48 evaluation ticks] + 17 target
copies including initialization + required checks/publication. Partner has one simple call
per tick and zero updates. There is no nested candidate/trajectory search.

| Quantity | Per arm | Pair |
| --- | ---: | ---: |
| Training episodes / joint steps | 4,096 / 196,608 | 8,192 / 393,216 |
| Training renewal rows / optimizer steps | 65,536 / 256 | 131,072 / 512 |
| Evaluation episodes / joint steps | 2,304 / 110,592 | 4,608 / 221,184 |
| Evaluation decisions | 36,864 | 73,728 |
| All episodes / joint steps | 6,400 / 307,200 | 12,800 / 614,400 |
| All focal decisions | 102,400 | 204,800 |

The [preparation counts](VSPC1_K4_REACTIVE_QUEUES_PREPARATION_COUNTS_20260906.json) remain a
prospective arithmetic record (its old `prospective_not_authorized` label records its writing
time). Its per-arm 454,656 scalar Q predictions count ordinary action scoring/backup/loss;
they are not forward calls, FLOPs or seconds. Nine-point evaluation adds 172,032 pair joint
steps above the same-training initial/end-only alternative; the selected curves retain
initial/transient/endpoint differences. No smaller alternative was executed.

New-host runtime is **unknown**; old six-tick wall times do not forecast it. Cap **2,700 s
per whole arm/seed invocation**, covering imports, initialization, training, all evaluation,
checking, primary publication and exit. Sum of caps 5,400 s is neither study elapsed nor a
forecast; no borrowing, slicing to reset a cap, automatic retry, extra seed or extension.
Stop after update 256 and final evaluation/publication, or the whole-invocation cap/concrete
failure. Preserve partial facts on failure; never fabricate an endpoint or silently shorten.

CPU float32, one compute thread, batch 16 training episodes in process. Host is portable
within that boundary, not part of the estimand; use configured `.codex/hmasd-compute.toml`
`remote_first` node wsl_4070, exact committed source in a detached worktree, `agent-task` and
fresh node-local memory admission immediately before each invocation. Existing local fallback
conditions only; do not migrate or duplicate an accepted process. Freeze exact argv, output
root, launch SHA and existing supervisor stop command in the technical launch record.
Root integration precedes result execution in this assignment. Use existing independent Monitor
adoption for accepted handles; CM owns observation until ACK and retains collection/acceptance.

## 7. Implementation surface and acceptance

Code: `experiments/candidates/vsp_c1/k4_reactive_queues_b01/`; thin runner
`scripts/run_vspc1_k4_reactive_queues_b01.py`; tests mirror that attempt under
`tests/experiments/candidates/vsp_c1/k4_reactive_queues_b01/`. Preserve prior VSP-C1 source,
cards and evidence. Runtime output is `temp/directions/vsp_c1/exp/k4_reactive_queues_b01_<run>/`.
Durable result evidence later uses this direction's card → E0 result → intake sequence.

Engineering scope §4: **needs none**. Ordinary learner target state and in-process batching
need no new scheduler, recovery system, guard, registry or telemetry framework. Use the existing
resource/remote/Monitor facilities. Normal ≤2,000 non-test research lines, ≤600 runner lines,
one focused changed-semantics/primary-output suite within the five-minute directory budget;
no new result-bearing smoke, optimum solver, exhaustive census, full historical replay or
profiling exercise. Proportional rule tests protect the table, not a confirmation claim.

Acceptance protects queue/service conservation; old-h simultaneous decisions; holding without
new focal inputs; actual segment and terminal targets; equal episode/period loss; declared RNG
pairing and separation; real counts/movement and readable primary output/branch handling.
Use an independent reviewer for new scientific/numerical/RNG meaning. No repeat smoke merely
at a launch boundary. Required learner and measurement facts go in one summary.json per arm,
with launch SHA, counts, complete fixed curve means, endpoint paired values, descriptive native
consequences, per-period TD losses, initial norm/final movement, wall and peak RSS. Resource-only
gaps are `resources_unmeasured`; learner/primary gaps limit their dependent claim under §11.8.7.

Controlling acceptance references: evidence-spec §§4, 5.2, 11.4, 11.7–11.9 and scope-spec
§§3–5. Implementation-relevant literature pointers are in proposal §5 (ACAC timing, UTE
executed segment transitions); the verified retrieval motivates clear timing/exposure, not a
new library dependency or FACTOR advantage.
