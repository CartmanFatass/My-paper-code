Claim: One paired training instance tests whether multiplicative duration-conditioned action values improve three-queue service over a fully conditioned learner, and whether either learner adds value over a fixed legal queue rule.
Binding MARL structure: (b) temporal abstraction — a held allocation constrains service while queue state and a known partner's response continue to change.

# VSPC1-K4-SERVICE-ALLOCATION-B01 — frozen 2026-09-07

Class **B/EXPLORE**. The complete [Convergence response §§II–VI](pro_packets/20260907_service_allocation_convergence/archive/RESPONSE.md)
selects this one new object, `PRO_FINAL`, delivered at immutable Git commit
`2347dbf2fea870cdcd02aa2eb8b3cbaff147ec34` and archived at `5d3027ebe`.
The [decision intake](VSPC1_K4_SERVICE_ALLOCATION_CONVERGENCE_INTAKE_20260907.md)
checks current authority and records the delegated card freeze. This card selects exactly
two complete learning invocations, new root seed 402, and one fixed-rule evaluation within
the second invocation. Current Portfolio command `80a62f394` requests card and CM-handoff
preparation only; implementation and execution have not been dispatched.

## 1. Question, interpretation ceiling and headroom

When two workers cannot cover three queues simultaneously and the focal worker must hold its
allocation, does trained value control improve complete native service over an immediately
usable queue rule? If so, is there a useful FACTOR advantage over full-duration GENERIC?
The fixed rule makes this a controller-choice question rather than only another network
ranking. It is evaluated with the learners, never used as a prerequisite to training.

One learning focal worker and one known, fixed, non-learning partner persist throughout.
Renewal state is fully observed and Markov for this stationary finite control problem.
There is no roster change, learned termination, partner co-adaptation, decentralized
multi-learner credit, transfer, optimality or stable-superiority claim. Both networks share
features; four factor coordinates over two durations are not a restrictive low-rank
bottleneck. Initialization, optimization and the common trainer remain alternatives to
any uniquely attributed value-sharing mechanism.

**Headroom/baseline record:** no tuned same-information baseline set or upper-reference gap
exists on this three-queue host. GENERIC supplies a first fixed-budget learner observation;
LQ-EXCLUDE is an untuned legal rule, not an optimum or competence certificate. The old
two-queue observation, action count, arrival law, information dimensions, seed and evaluation
grid do not match. Its recorded-tape supply gap of 0.013997396 above observed GENERIC and
the earlier six-step reference 5/6 are not transferred here. Old A01's missing headroom stays
missing. No exact optimum, baseline sweep, support census or policy search precedes this B.

**MEI:** absolute J difference 0.025, equivalent to 2.4 completed jobs per 48-tick episode.
This preserves a concrete work scale; it is not lowered after the old small effect. Use the
same scale to describe differences from the rule, and -0.025 for material period losses.
It is not a significance threshold, equivalence bound or additional launch condition.

The host, arrivals, input dimensions, initial work, seed and evaluation grid were chosen
after seeing reactive B01. This is disclosed exploratory adaptation. A cross-host sign
change cannot uniquely identify coverage scarcity or establish cross-task superiority.
The six-step public-plan family remains ended; reactive two-queue B01 receives no additional
invocation. The reactive family and K4 remain open; no recast or Portfolio disposition follows.

## 2. Host, legal information and native consequence

Three queues of capacity 4, two persistent workers, H=48 primitive ticks t=0,...,47.
Initial queues are (2,2,2); initial previous focal allocation h is uniform on {0,1,2}.
Exogenous d is fixed within each episode at 2 or 6. Both periods have equal episode weight.
Each queue independently receives Bernoulli(0.5) arrivals after every service tick.
Offered work is 1.5 jobs/tick versus an instantaneous upper capacity of 2; this is not a
stability, attainable-return or finite-capacity headroom proof.

At a renewal t, the focal reads (q0,q1,q2,h,t,d), chooses a in {0,1,2}, and holds it for d
ticks. It receives no new policy inputs or choices inside that segment. At every tick the
partner reads the current queues and **old h**, chooses a longest queue, and resolves ties
in cyclic order [(h+1) mod 3,(h+2) mod 3,h]. It cannot read the focal's simultaneously
chosen new action. The partner has no learned parameters, gradient or hidden policy state.

Service is simultaneous: each distinct selected queue serves at most one existing job;
two workers selecting the same queue serve at most one job together; empty queues serve
zero. Then arrivals enter, queues clip to 4 and overflow is recorded. Finally h becomes
the held focal action. The next partner response can therefore change within a held segment.
Arrival tapes and future partner trajectories are never policy inputs.

Event → role → information → action/credit → exposure → native consequence:
three independent arrivals and queue competition → persistent focal/partner ownership →
renewal-only focal state and per-tick partner state → held queue allocation and joint
service → actual segment reward and actual successor-state TD update → full-episode jobs
served, with overflow, remaining backlog and unused capacity retained descriptively.

J = total jobs actually served over all 48 ticks /96. Collisions, empty queues and zero-service
ticks remain in the denominator; final-tick arrivals cannot be served this episode. Record
overflow, final total backlog and sum_t(2-served_t) as descriptions, not auxiliary rewards.
Do not normalize by supplied work, discard ticks, or mask the learners' legal actions.

## 3. Learners, fixed rule and actual segment updates

Common feature order is [q0/4,q1/4,q2/4,t/48,one_hot(h),one_hot(a)], ten coordinates;
three-way one-hots are ordered 0,1,2. GENERIC appends [1[d=2],1[d=6]].

| Controller | Form | Online trainable parameters |
| --- | --- | ---: |
| FACTOR | 10→24 tanh→4 biased linear features, dotted with learned 2×4 duration embedding | 372 |
| GENERIC | 12→28 tanh→1 biased scalar | 393 |
| LQ-EXCLUDE | At renewal, compute the partner's immediate action from current (q,h), then select the longest of the other two queues, ties by smallest queue index; hold for d ticks | 0 |

Keep the original hidden widths and GENERIC's 21-parameter excess; no parameter-matching
tuning. GENERIC has the same complete information and nonlinear duration interactions.
Each learning arm has an independent initialization and one non-optimized target copy.
Dense weights use Xavier uniform, biases zero, FACTOR embeddings Normal(0,0.5).

LQ-EXCLUDE has no training, tuning, future arrivals, model-based planning or within-segment
reallocation. It is a transparent legal comparator, not an optimality claim. Shared evaluation
tapes mean shared exogenous arrivals, initial h and d only: **all three controllers evolve
their own queues, h and partner actions**. Never replay another controller's endogenous state
or partner trajectory into the rule. The rule supplies no learner data, targets, rewards,
action masks or checkpoint-selection information.

For u=1,...,256, keep online parameters fixed while collecting 16 new complete episodes,
eight per d; then perform exactly one Adam update over all actual renewal rows and clear
the batch. Epsilon_u=1-0.9(u-1)/255; exploration is uniform over three actions. Score all
three actions even on exploration. Greedy and evaluation ties select the smallest index.
No replay, unexecuted-duration sample, skip transition, imagined trajectory or added search.

For the actual segment t→t+d, R is served jobs in that segment /96; s' is after its last
service, arrivals and h update. Nonterminal target:
y = R + Q_target(s', argmax_a Q_online(s',a,d), d).
At t+d=48, y=R with no terminal next-action scoring. Gamma=1; targets are detached;
the target network is not optimized. With n_e=48/d_e,
L=(1/16) sum_e [(1/n_e) sum_j (Q_online(s_ej,a_ej,d_e)-y_ej)^2].
Each episode and each period therefore has equal weight despite d2 having three times as
many renewal rows. Do not divide R by d. Retain per-update, per-period mean squared TD loss.

Adam lr=0.01, betas=(0.9,0.999), eps=1e-8, weight_decay=0; global gradient-norm clip 5.
Target initially equals online and is copied after updates 16,32,...,256. Evaluation reads
the updated online network. No tuning from evaluation, early stopping or best-checkpoint choice.

## 4. Data, RNG, independent unit and exposure

Root seed **402 only**. Preserve the existing namespace mapping in the new implementation:
init_FACTOR=11, init_GENERIC=12, train_arrivals=21, train_h=22, explore_coin=23,
explore_action=24, eval_arrivals=31, eval_h=32. NumPy streams are
PCG64(SeedSequence([402,namespace_id,d,u])); evaluation uses u=0, training u=1,...,256.
Initialization takes one uint64 SeedSequence word from [402,init_arm_id,0,0] as its Torch
seed. Preserve hidden/output construction and explicit initialization order from the prior
QNetwork, changing only the declared input/action dimensions; record this in source acceptance.

For each period/update, assign train arrays before policy branching: arrivals (8,48,3)
from uniform draws <0.5; initial h (8,) uniform integers 0..2; exploration coins (8,48);
exploration actions (8,48) uniform integers 0..2. Policies use exploration slots only at
actual renewal t. Evaluation arrivals (128,48,3) and initial h (128,) use their independent
namespaces. Both periods' evaluation tapes are mutually independent and independent of
training; share them across arms, five checkpoints and the one rule evaluation. Changing
policy branches never changes the assignment of external or exploration draws.

The independent learning unit is **one paired training instance**, containing two optimized
online models and two non-optimized target copies. Repeated evaluation episodes/checkpoints
are not training replicates. No equality of initial values, policies or parameters is assumed.

The [machine-generated configuration/count record](VSPC1_K4_SERVICE_ALLOCATION_B01_COUNTS_20260907.json)
states 372/393 trainable online parameters and 256 nonzero-lr Adam steps per arm over 65,536
actual-segment TD rows. CM checks this can-move path against delivered source; no extra
movement experiment is selected. Initial parameter norms and final displacements are
measured during the actual selected calls and remain unknown now. Old measured movement is
provenance, not a measurement of these new models; no displacement-ratio threshold is imposed.
This decision/card preparation has zero new model, environment, learner, evaluation or test
execution. Any later technical-fixture exposure is recorded separately from the selected B.

## 5. Primary measurements, descriptive branches and prediction

Evaluate each learner greedily at updates **0,64,128,192,256**: 256 complete episodes per
point, 128 per d. Evaluate LQ-EXCLUDE **once**, on the final same 256 tapes inside the second
complete invocation; no initial/intermediate rule calls. Primary Delta_d=J_F,d-J_G,d at
update 256 and Delta=(Delta_2+Delta_6)/2. Also report E_F,d=J_F,d-J_R,d and
E_G,d=J_G,d-J_R,d and their equal-period means, where R is LQ-EXCLUDE.
E_F-E_G=Delta; these correlated comparisons are not three independent success observations.

Retain every raw controller endpoint mean, period mean, each learner's five fixed points,
initial values, period losses and endpoint per-episode J indexed by period/episode/controller.
Use those same arrays for each contrast's conditional SE:
SE=0.5 sqrt(s_2^2/128+s_6^2/128), sample variance s_d^2 of paired episode differences.
This estimates only evaluation noise for the fixed policies, not training-population
uncertainty. Do not add evaluation to resolve a threshold or treat repeated points as seeds.

Full AUC on this grid is [0.5J_0+J_64+J_128+J_192+0.5J_256]/4, per period and equal-period
mean. Keep initial-to-final changes separately. The sparse-grid AUC neither resolves all
transients nor merges with old nine-point AUC. Endpoint remains primary; no favorable-metric
selection. If an endpoint advantage over the rule already existed at initialization, do not
attribute the entire advantage to subsequent learning.

**How the result will be interpreted:** a MEI-sized FACTOR advantage over both comparators
without material period loss supports considering one or two fresh independent instances.
A FACTOR win over GENERIC while both trail the rule is only a learner-ranking fact. Learning
above the rule with FACTOR inside MEI or worse supports value learning, not this factorization.
An opposite-sign MEI favors GENERIC on this instance; a material period loss is a tradeoff.
Inside MEI with no useful learning-over-rule signal provides no practical reason to continue
this object. Preserve signs, uncertainty and adverse observations; no branch grants more calls.

| Observation | Reading and recommended next choice |
| --- | --- |
| Damaged primary reward, information or real-update dependency, or no comparable endpoint | No conclusion on the damaged dependency; preserve trustworthy independent facts and name the gap, not a negative experiment. If only the rule is missing, retain a trustworthy Delta and leave rule-relative value unresolved; no automatic third call. |
| Delta >=0.025, neither Delta_d <=-0.025, and E_F >=0.025 with neither E_F,d <=-0.025 | Most direct local reason to consider one or two independent training instances of the same comparison. No additional calls selected here; no stable win. |
| Meaningful FACTOR-over-GENERIC gain but both learners still trail the rule | Retain the local learner gain and all curves; no demonstrated useful scheduling advantage. Favor retaining the rule and stopping this FACTOR combination unless a concrete trainer question justifies a separately selected revision. |
| At least one learner clearly improves over the rule, but FACTOR-over-GENERIC is inside MEI or adverse | Supports local learned-policy usefulness, not multiplicative structure. A GENERIC gain favors considering GENERIC versus the rule; no rescue arm, metric change or automatic new object. |
| Delta <=-0.025, or the mean masks a period Delta_d <=-0.025 | The first favors GENERIC in this instance; the second is a period tradeoff. Interpret alongside rule-relative returns; no reweighting, discarded loss, negative-transfer attribution or K4 closure. |
| Delta inside MEI with no useful learner-over-rule signal, or evaluation uncertainty leaves the relevant boundary unresolved | No practical continuation reason from this object; preserve sign and uncertainty and stop at this object boundary. No automatic extension, extra evaluation or search for another similar host; no equivalence or optimality claim. |
| AUC, initial-value changes and endpoint rankings differ | Report all, keep the complete fixed endpoint primary; no best checkpoint, seed or metric declared the winner. |

Branches can overlap: read dependency integrity, primary contrast, rule-relative usefulness
and period cost together. An absent rule does not retrospectively invalidate a trustworthy
learner contrast. Null/adverse B evidence does not close K4, and B has no consumption state.
Any proposed new invocation needs its own delegated selection and budget within current scope.

**Prediction on record:** DM adopts the node's prediction J_R >= min(J_F,J_G) for the final
equal-period means. If both learners exceed J_R, it misses on the designated observation;
MEI-sized gains make that contradiction more useful. FACTOR beating both comparators by
at least 0.025 in both periods especially contradicts the cautious expectation. Report
evaluation noise without rewriting a miss as a hit. Owner prediction: **not taken (unattended)**.

## 6. Complete work, execution boundary and stop

Two arms × one paired seed × [initialization + 256×(16×48 training ticks + one update on
256 renewal rows, 240 nonterminal) + 5×(256×48 evaluation ticks) + 17 target copies +
necessary checking/publication]. Add once 256×48 rule-evaluation ticks. The partner acts
once per tick with zero updates; three ordinary action scores are not a trajectory/policy search.

| Quantity | Each learner | Rule only | Total |
| --- | ---: | ---: | ---: |
| Training episodes / joint ticks | 4,096 /196,608 | 0 /0 | 8,192 /393,216 |
| Actual TD rows / nonterminal rows | 65,536 /61,440 | 0 /0 | 131,072 /122,880 |
| Adam updates | 256 | 0 | 512 |
| Evaluation episodes / joint ticks | 1,280 /61,440 | 256 /12,288 | 2,816 /135,168 |
| Evaluation focal decisions | 20,480 | 4,096 | 45,056 |
| All joint ticks | 258,048 | 12,288 | 528,384 |
| Scalar Q predictions | 569,344 | 0 | 1,138,688 |

Per learner the Q count is behavior 196,608 + online bootstrap 184,320 + target selected
action 61,440 + loss 65,536 + evaluation 61,440. Training TD rows are 49,152 for d2 and
16,384 for d6. Rule choices are 4,096 ordinary decisions with no nested search. Counts
are prospective arithmetic, not measured execution, forward-call counts, FLOPs or seconds.

Call order is **FACTOR, then GENERIC**. First complete call: 258,048 ticks. Second complete
call includes GENERIC, rule evaluation and paired publication: 270,336 ticks. Cap is
**2,700 seconds per complete call**, including imports, initialization, learning, every
selected evaluation, necessary checking/publication and exit. Rule work and paired output
cannot be placed outside the second clock. The sum 5,400 seconds is not predicted elapsed
time; no borrowing, slice reset, third call, automatic retry or unallocated seed/arm/config.
Stop at update 256 and complete final publication, or the original cap/concrete failure.
Preserve actual partial counts and trustworthy facts; do not fabricate or shorten an endpoint.

New-host runtime and implementation cost are unknown. Existing two-queue walls 4.84/5.48 s
are observations of another host, not this cost law. New work has 0.86 times the old ticks
but 1.252252... times the scalar Q predictions and larger inputs. No separate cost experiment
or exact reference is required to select this bounded ordinary implementation.

CPU float32, one compute thread, batch16 training episodes in process. Host is portable
within this boundary and is not part of the estimand. Follow `.codex/hmasd-compute.toml`
remote_first (`wsl_4070`), exact committed source in a detached worktree and existing
`agent-task` supervision. Commit/push before execution; fresh node-local memory admission
immediately precedes each actual invocation. Existing fallback rules apply only before any
remote process is accepted and with fresh destination admission. No migration or duplicate run.
Later execution records bind actual argv, source SHA, run root and stop command.

Root owns routine observation after adoption ACK under `EXPERIMENT_MONITOR.md`; CM retains
collection/technical acceptance and DM retains science. No independent Monitor task or new
heartbeat. No experiment handle exists at this preparation boundary.

## 7. Implementation surface and acceptance

New code: `experiments/candidates/vsp_c1/k4_service_allocation_b01/`; thin runner
`scripts/run_vspc1_k4_service_allocation_b01.py`; tests under
`tests/experiments/candidates/vsp_c1/k4_service_allocation_b01/`.
Use the existing reactive-B01 implementation as a read-only starting point for actual-segment
learning, RNG and publication; preserve its source, cards, results and stopped-call boundary.
Runtime outputs belong in `temp/directions/vsp_c1/exp/k4_service_allocation_b01_<run>/`.
Durable results use card → E0 result → intake in this direction directory.

Engineering scope §4: **needs none**. Ordinary target state, in-process batching, existing
resource admission and detached supervision require no new orchestration. Limits: <=2,000
new non-test research lines, <=600 runner lines and one proportionate focused suite within
the five-minute research-directory test budget. No new guard, registry, service, retry/lease
system, full-history replay, optimum solver, profiling exercise or repeated unchanged smoke.

Acceptance protects the changed three-queue transition/conservation and cyclic partner tie;
simultaneous old-h decisions; held actions and actual terminal/segment targets; equal
episode/period loss; three-action scoring and declared RNG separation/pairing; rule legality
and its own endogenous trajectories; and readable endpoint/contrast/SE/AUC/branch publication.
Retain independent scientific/numerical/RNG review for this changed control and measurement
path. Tests use focused synthetic fixtures and record actual exposure separately; no formal
seed402 invocation or complete runner smoke is commissioned in the preparation handoff.

Each arm's summary.json records source SHA, actual counts, fixed curves/period losses,
endpoint indexed returns, native-work descriptions, initial norm/final movement, wall and
peak RSS. The second call also publishes rule endpoint values and all three paired contrasts
and conditional SEs. Missing resource-only telemetry is `resources_unmeasured`; damaged
learner or primary instrumentation limits its dependent claim under evidence-spec §11.8.7.

Controlling acceptance: evidence-spec §§4, 5.2, 11.4, 11.7–11.9 and engineering-scope §§3–5.
The [CM handoff](VSPC1_K4_SERVICE_ALLOCATION_B01_CM_HANDOFF_20260907.md) supplies the five
bounded assignment items. Reused literature in [proposal §5](VSPC1_K4_SERVICE_ALLOCATION_QUESTION_20260907.md)
motivates timing, actual segment exposure and a queue-aware comparator; it provides no
new library dependency, optimum theorem or FACTOR performance evidence.
