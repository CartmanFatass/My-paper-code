# UAV temporary transit coverage handoff

## 2026-09-28 UTC — bounded design, source reconstruction and concrete comparison

This is the new direct DM's design-only assignment. No implementation, training,
collection, evaluation, simulation probe, refit or failure retry is authorised by
this entry. It declares **zero started fits and zero new environment/model rollout
steps**. Reading, authoring, primary-source retrieval and scientific review have
real, incompletely measured cost. There is no accepted operation or run handle.

The published starting decision is [the current plan at
31c37c467](https://github.com/CartmanFatass/My-paper-code/blob/31c37c4671a9a3d752a044f16d4afe936c4fa2e9/docs/research/RESEARCH.md#current-research-plan).
The [completed portfolio review](../../archive/2026-09-28/RESEARCH.md#portfolio-review-completed-four-dm)
is reused for selecting this question; a new session does not require its raw-data
audit again. Current routing was added by Root in `31159b4a2`; Root maintains that
block. This notebook owns the new concrete algorithm/comparator decision below.
PPC/FSD pauses, G33, existing exposure including 957001–957032, SCC/T-prime closure
and other DMs' evidence remain binding boundaries. No App message is sent.

### Inherited evidence and its effect on this design

| Evidence, with frozen source | What carries forward | Effect on the comparison |
| --- | --- | --- |
| [B02 fixed contract, result and independent reading](../uav_cooperative_planning/NOTES.md#2026-09-27--complete-native-b02-reading), input `9f72afd2223baccd9ed554b0ef86bcbe5277afb5` | One actual offline fit/5,000 updates; L−P QoS −.016488229 and raw J −55.388987 on 32 new worlds. L chose 4,575 holds in 4,582 discretionary windows. That is a completed adverse package, not diagnosed extrapolation, bad credit or impossibility of learning. | No retuning/retraining that Q package. New support trajectories change the decision problem; their ordinary comparator receives exactly those trajectories. |
| [B04](../energy_relay_availability/NOTES.md#2026-09-27--complete-native-b04-reading), input `025350669bc5e8ab99fc71954f749ae47a6853e9` | P−H QoS +.01057845 and J +34.73585; 21 favourable and 11 adverse worlds. P is a useful ordinary asset, not an optimum. | Keep P as the secondary competence reference; a win over P alone cannot establish learned handoff value. |
| [B05](../energy_relay_availability/NOTES.md#2026-09-27--complete-native-b05-reading), input `754d5d34d905a81b58b78e69ae85b8a07cb19aad` | Five_ten−one_step QoS +.01607076 and J +35.80811; extra return cost +6.20218. World 28092823 gains service but loses 260.94523 J, minimum battery .07430702, reserve exposure .16279167. Strict floating ordering and approximation remain part of the package. | Ordinary temporal prediction can already be useful; retain risk tails and exact tie semantics. Do not equate geometric coverage with native delivery or zero cutoff with safety. |
| B02 adverse world 29102732; favourable worlds 29102704/20 and 29102727 | B02's risk loss and positive cases remain. Its mean saving against H is dominated by one world; neither reliable conservatism nor universal harm was established. | No risk-saving rescue interpretation. Every new comparison must preserve all worlds and full native endpoints. |
| [Portfolio reconstruction of SET/diagnostics failures](../../archive/2026-09-28/RESEARCH.md#portfolio-review-completed-four-dm) | The two fresh SET attempts and the incomplete masking comparison do not have complete endpoints. | No policy ranking from technical failures; no failure rerun or project-wide repair task is purchased here. |

At `31159b4a2`, the inspected H1/feedback/observation, B04 controller and native
energy/routed environment files have no diff from the B05 input revision. Relevant
shared background is [RESEARCH sections 1–4, 6 and
8](../../RESEARCH.md#研究背景与共享认识), read at this published boundary: joint action
rights, information, finite learning and complete usefulness are distinct. This
changes the design concretely: use central-information matching; read actual
submitted/executed trajectories under the shield; do not call a model score or a
policy update a service result; use a capable ordinary scheduler as primary.

### Actual interfaces and the meaning of fixed H1

Source identities below are pinned to B05 input; function names identify the
inspected passages without relying on later line numbers.

- [H1 `LayoutHeuristic.plan`, `_assign_targets`, `act`](https://github.com/CartmanFatass/My-paper-code/blob/754d5d34d905a81b58b78e69ae85b8a07cb19aad/experiments/candidates/energy_relay_benchmark/b01/heuristic.py): six k-means service centroids, two relay targets on the BS-to-centroid-mean line, relay-first priority, Hungarian distance matching with 300 m previous-target hysteresis; nominal horizontal/vertical limits 30/5 m/s and 1 s primitive steps. The configured comparison refreshes every ten steps. H1's assignment availability is the supplied previous shield-mode mask, not a new donor-eligibility mask.
- [Controller and `central_plan_inputs`](https://github.com/CartmanFatass/My-paper-code/blob/754d5d34d905a81b58b78e69ae85b8a07cb19aad/experiments/candidates/energy_relay_benchmark/b01/evaluation.py): current central user/BS xy is available only at replans; own UAV and station data come from observations. The adapter must not pass the raw SET state or future user velocities/waypoints to either selector.
- [Observation decoders](https://github.com/CartmanFatass/My-paper-code/blob/754d5d34d905a81b58b78e69ae85b8a07cb19aad/experiments/candidates/energy_relay_benchmark/b01/observation.py): all eight own positions and the energy suffix provide battery, availability, charging, returning/dock flags, waiting, return thresholds/margins and station records. S2 has 30 users, one BS, two charging stations. Float32 energy observations are not raw float64 simulator state.
- [Production shield `apply_feedback_params`](https://github.com/CartmanFatass/My-paper-code/blob/754d5d34d905a81b58b78e69ae85b8a07cb19aad/experiments/candidates/energy_relay_benchmark/b01/feedback.py): recompute effective mode every primitive step, enter at margin ≤0 and exit at ≥.05; overwrite all four action coordinates for affected members, choose nearest valid station and set dock request. Other members' proposals survive this layer. A previous `False` mode alone does not establish current donor eligibility.
- [B04 `TransitHoldHeuristic.plan`](https://github.com/CartmanFatass/My-paper-code/blob/754d5d34d905a81b58b78e69ae85b8a07cb19aad/experiments/candidates/energy_relay_availability/b04/transit_hold.py): temporary execution targets and `h1_targets_xy` are separate. P selects all-move/single hold by `(q0+2*q5+q10)/4`, but falls back to all-move if **any** shield mode is active or any margin is entering. Thus B02 did not test a different unshielded member's support trip.
- [Energy action, charging and guard override](https://github.com/CartmanFatass/My-paper-code/blob/754d5d34d905a81b58b78e69ae85b8a07cb19aad/envs/pettingzoo/relay/energy_aware.py): native action preparation handles failure/exhaustion, limp-home, docking capture and charging. `available` means above service cutoff and not failed; it does not mean neither charging nor returning. A genuine station-directed dock/return action can bypass the backhaul guard; a support donor with dock bit zero cannot borrow that exemption.
- [Routed `_apply_backhaul_action_guard`](https://github.com/CartmanFatass/My-paper-code/blob/754d5d34d905a81b58b78e69ae85b8a07cb19aad/envs/pettingzoo/relay/routed_core.py): critical service/relay moves can be stopped if they break an existing dependent path. Exact checks use live routing/association state, which the selector does not receive. Nominal reachability is not certified execution. The unchanged native guard decides actual motion.

**Fixed means the H1 generator, matching rule and continuation memory are
unchanged, and the current H1 assignment is immutable across candidates at a
given real boundary.** Recompute H1 at the next ten-step boundary from the actual
new observation using its own previous H1 targets. Never feed a temporary waypoint
back into its hysteresis memory. This is not a promise of numerically identical
future assignments across policies: motion changes future distances/modes. Such a
promise would require a different frozen/exogenous assignment experiment. No old
P trajectory or future H1 assignment is replayed as truth.

There are consequently three different feasibility statements: a donor is
eligible for a legal proposal now; its nominal trip may satisfy the approximate
model; actual motion remains subject to shield/guard/energy logic at each step.
An exact future-execution guarantee is unavailable at these information rights.
No additional hidden guard query or bypass is proposed to manufacture it.

### One concrete action interface: finite support visits

The candidate is deliberately a bounded centralized joint selector over eight
fixed low-level H1 controllers, not independently learning low-level agents or
a new decentralized MARL architecture. The following numbers define the design
alternative being assessed, not registered run inputs or an instruction to code.

1. At each real clock 0,10,…, obtain the ordinary H1 plan first. Keep its targets
   and its previous-target memory in a separate base object. Compute effective
   shield modes from the same float32 legal margins using the production rule;
   use them for donor eligibility only, without changing H1's original interface.
2. A departure event for source i is observed when its effective shield mode
   changes False→True, or when a non-returning assigned member begins a transit
   with H1 horizontal distance >300 m. Transit events rearm only after distance
   falls to ≤30 m; shield events rearm on release. At reset transit flags are
   unarmed/False, so an initial long departure is an opportunity. No prediction
   of hidden future motion or failure creates an event. If entry occurs between
   clocks, the event is registered at the next clock, at that observed position;
   do not label it anticipation of the earlier departure.
3. Each source event fixes `w_i = current source xy` and expires 60 steps after
   registration. Source xy then moving does not move the waypoint. End the event
   on shield release (return event) or completion of the transit predicate at
   ≤30 m (transit event), or on expiry. Simultaneous events are allowed; none
   constitutes evidence that a service hole actually exists.
4. With no active support visit, candidate 0 is **no handoff**, ordinary all-move
   H1. For each live source event choose its nearest eligible *other* member
   within 900 m of its fixed waypoint (distance ties by UAV index). The donor
   must have effective mode False, positive return margin, availability True,
   charging/returning/dock False and a finite current H1 target. There is at most
   one donor candidate per source: at most nine joint candidates including 0.
   This shared nearest-donor restriction is not an optimal donor search; it may
   miss a less damaging second donor. It bounds this actual comparison, equally
   for learning and ordinary scheduling, without claiming an exhaustive library.
5. Selecting (i,j,w) changes only donor j's horizontal target, preserving H1
   altitude and action scales; dock stays zero. Others follow their current H1
   plan. At most one support visit is active. At later clocks the choices are
   continue that same visit or release it, not a free new joint assignment.
   Entering a 30 m disk marks arrival; continue at w for ten primitive steps.
   The visit ends at dwell completion, event end/expiry, release, or donor
   ineligibility. It cannot renew its 60-step expiry by repeated selection.
6. Upon ending, resume the **latest current H1 target**, never the target saved
   at departure. Native shield takeover cancels the visit immediately and
   supersedes that resumption. A guard rejection is retained as realised
   zero/reduced motion, consumes time and does not reset the timer. Arrival may
   never occur; the visit still expires. Between clocks there is no new user/BS
   query or new learned decision; only these deterministic option/shield rules.

P's old single-self-hold library is **not** silently added to this interface.
P is a separate secondary complete controller. Thus O−P or L−P is a package
comparison, not an isolated effect of expanding an action superset. The primary
L−O contrast alone holds this new executable library fixed.

### Primary ordinary alternative O: rolling finite-candidate rollout

Every ten steps O scores all legal joint candidates by a **60-step deterministic
nominal rollout**, executes only the selected next ten steps, and replans on the
real new observation. The active visit's arrival/dwell/expiry/release rules above
operate inside each forecast. Beyond the present choice, a started/continued
visit completes by its rules; no additional support visit starts in the forecast.
H1 recomputes on predicted positions/modes at ten-step boundaries with static
current users, retaining its base memory. The no-handoff forecast uses H1.

The nominal state is rebuilt from permitted observation fields and known S2
configuration, **not a deepcopy of live private state followed by partial
overwrites**. User and BS positions stay fixed; no velocities, future RNG,
association history, hidden failure schedule or learned model is provided.
Initialize association/routing afresh from that geometry, and evolve their
predicted state within the nominal rollout. Batteries, stations and observable
charging/wait state initialize from legal decodes; use native equations for
motion, propulsion, return margin, shield hysteresis, charging arbitration,
routing and guard on this reconstructed state. Hidden quantities that cannot be
reconstructed must have a documented deterministic initialization, shared by L
and O; this forecast is an approximation, not an exact state clone. S2 has no
injected failure process. No forecast invokes real future world evolution.

Rank by the sum of predicted **original native** reward over 60 steps, including
QoS, native return penalties, any cutoff/depletion terms and original potential
formula. No extra waypoint, arrival, handoff or energy bonus; no arbitrary
distance reward. Use no learned terminal value after the 60th step. Respect
the episode horizon if fewer than 60 steps remain, with the native terminal
potential treatment. Use float64 scores, strict comparison, no-handoff then
source/donor index for exact ties; record score gaps rather than retroactively
change a tolerance after inspecting results.

This ordinary scheduler is stronger than a geometric nearest-replacement rule:
it prices the donor's lost service, actual nominal travel/dwell, other moving
members, native energy/charging and the subsequent H1 recovery. It remains a
restricted rollout controller, not globally optimal MPC. Longer lookahead,
multi-visit search, better lawful motion forecasts and donor search are capable
ordinary substitutes; no known result establishes that neural choice beats them.
Making O weaker merely to make learning win would change the scientific use.

### Concrete learned alternative L and its exact execution relation

Use a standard **on-policy residual categorical actor with PPO**, with exactly
O's library, forecast outputs, action constraints, real clock and model calls.
For legal candidate a at boundary h, let s(h,a) be O's predicted reward sum
divided by its actual nominal horizon. Define

`pi_theta(a | h) = softmax_a( s(h,a)/0.02 + f_theta(h,a) )`.

`f_theta` is one shared two-hidden-layer 128/128 tanh MLP with a scalar output;
initialize its output layer to zero. The untrained policy is the soft version of
the ordinary scores, not claimed to equal O's deterministic argmax. Candidate
masking precedes the softmax; a one-option context has probability one. There is
no separate policy for the returning member, no local credit label, no old B02
checkpoint/replay and no imitation prefit. This is conventional residual policy
optimization applied to a new interface, not a proposed new PPO theorem.

Actor inputs are the current time/horizon; own xyz and decoded energy/station
fields above; current and previous base H1 targets with validity masks; current
central user/BS xy; previous/effective shield modes; each live event's source,
fixed xy, type and age; active donor/event, arrival/dwell counter and expiry;
and candidate identity plus the common predicted native reward/QoS/return cost,
guard stops and final positions/batteries/margins. Use fixed physical scales
(8 km xy, native height interval, H3000 time, 60-step option time) and masks;
no evaluation-fitted normalizer. This history summary is not asserted Markov.
O has the same primitive data, option state and model outputs.

The scalar critic has two 128/128 tanh layers over the same global data plus
mean-pooled valid candidate features; it has no privileged state. Train the
actor/critic jointly from actual on-policy ten-step segments. A segment's reward
is the sum of the **real original native rewards**, divided by ten only as a
fixed unit change, never a model score or counterfactual label. Use gamma=1 for
the finite H3000 objective, GAE lambda=.95 per decision, clip=.2, value-loss
coefficient=.5, entropy coefficient=.01, Adam 3e-4, gradient norm cap .5. These
are proposed single settings, with no search, annealing or adaptive stopping.

One possible first exposure is 64 H3000 training worlds in 32 successive rounds
of two complete episodes. After each round take four shuffled epochs, minibatch
size 200 with its final partial minibatch included. With all worlds full-length,
that gives 19,200 macrosegments, 384 joint optimizer steps and 76,800 sampled
segment exposures. Actual early terminations reduce these amounts and are never
replaced. Keep forced rows in value training; their categorical actor gradient
is already zero, without a new shield-gradient intervention. Native termination
and the declared finite H3000 endpoint both have zero continuation; a segment
ending early keeps its actual length/reward. Only the final 64-world endpoint
is selected. Save counts, parameters, policy probabilities and hashes to establish
actual training, not merely recurrent-state change.

At evaluation, freeze weights and sample the learned categorical policy once
per decision with a separate predeclared policy RNG per world. Do not switch
post hoc to greedy or add action-stream panels after seeing scores. O and P are
deterministic under their pinned arithmetic. L's sample-path uncertainty remains
part of this first conditional comparison. Online experience can in principle
correct static-user/model-initialization errors or value later consequences;
its finite data, critic bias, entropy and control variance can also hurt.
That is a conjecture about usefulness, not an explanation of old B02's failure.

### Primary methods checked on 2026-09-28, and what they can replace

The search/read is bounded and not a complete novelty review. Titles/years below
come from the primary papers, not a claim that this is the globally newest work.

| Primary source and checked passage | Relevance and substitutability |
| --- | --- |
| [ALMA, NeurIPS 2022, §§2/4.1](https://arxiv.org/html/2205.14205) | Hierarchical allocation and jointly learned low-level execution already exist. Its composite-task setting and subtask information differ; calling this design allocation/hierarchy is not a new contribution. |
| [MAT, NeurIPS 2022, §4 and Algorithm 1](https://arxiv.org/html/2205.14953) | Sequential autoregressive joint-action learning is established. A generic categorical joint selector suffices for this finite action set; a Transformer or sequential decoder needs a distinct contribution and comparator before purchase. |
| [Arribas, Cholvi and Mancuso, 2022, §§V–VI](https://arxiv.org/html/2205.12656) | HoRR/PHeRR explicitly schedule replacement and recharge for persistent aerial locations. Fixed locations, fleet sizing and charging assumptions differ from the native moving-user/nonadditive service problem; they supply ordinary rotation alternatives, not directly applicable optimality. |
| [Bouček and Flídr, 2024, §II](https://arxiv.org/html/2407.01084) | SoC prediction, mission waypoints and A* search already support battery-management detours. Native charging is not battery swapping; replacing it with that paper's system would violate this comparison. Its reasoning strengthens the ordinary planning alternative. |
| [Rastgoftar, July 2026 preprint, §§I–II/V](https://arxiv.org/html/2607.15583) | Cyclic worker replacement, fixed anchors and optimised replacement positions already appear in a non-RL surveillance controller. Its bounded-LTL/coverage assumptions and reference synthesis do not establish native S7 service or return safety; fixed anchors plus rotation is not itself new. |
| [Residual Policy Learning, 2018](https://arxiv.org/abs/1812.06298); [PPO, 2017, surrogate objective](https://arxiv.org/abs/1707.06347) | Conventional RL can improve a supplied controller and optimise sampled policies. Here the residual is in candidate logits, not additive motor actions. Neither paper guarantees a finite-data increment on this shielded partially observed host. |

**RECORDED/ordinary:** residual learning, PPO, bounded options, rollout scheduling,
replacement and assignment. **TRIED here:** the old move/hold Q package and the
B04/B05 scoring packages, with their original results. **New to the inspected
native studies, not established literature novelty:** this fixed-H1 temporary
support/return interface and its matched L−O comparison under the live shield.
No credit, task-allocation or long-horizon algorithmic originality claim is made.

### Predictions, competing explanations and native reading

The proposed learned-value story predicts both (i) realised visits that sometimes
maintain delivered service while a source departs, followed by donor release and
resumption, and (ii) a complete L−O improvement in QoS and original J without a
material risk deterioration. A policy that only issues support commands, changes
model scores, raises arrival rate or protects a departing region while harming
the donor's region has not satisfied that story.

The strongest simpler explanation is that ordinary joint rollout already captures
the useful geometry/energy tradeoff and the action opportunity, leaving little
increment worth learning. Additional alternatives have different observations:

- Few eligible donors or mostly guard-stopped/expired visits would constrain this
  action interface's realised opportunity; it would not diagnose a bad neural
  optimiser or all possible support libraries. Read opportunity counts and actual
  movement in the complete experiment, not as a new preliminary probe.
- Frequent executed visits with O gains over P but no L−O gain would retain an
  ordinary package contribution and weaken this learned increment.
- Higher local service with higher return costs, delayed charging or donor-region
  losses would support displacement of cost rather than complete usefulness.
- L−O gains could be learned score calibration, compensation for the surrogate
  initialisation/static users, later consequences or visitation effects. The three
  arms would not identify a temporal-credit mechanism or residual architecture
  advantage. Those would need a separately useful comparison, not a fourth arm
  added automatically here.
- Incomplete technical execution is missing evidence. A fully observed negative
  comparison is adverse evidence. Neither justifies automatic retries or tuning.

Log each boundary's event/candidate/mask/scores/chosen probability and H1/base
targets, plus actual donor displacement, arrival, release reason, guard stops
and shield takeover. Process summaries include opportunity/selection/execution
counts, donor diversion and resumption lag, and QoS around **all** eligible
departure events, including unselected, failed-arrival and censored visits.
These arm-dependent events/windows are descriptive mediators, not randomized
subgroup effects or extra independent replicates. Do not manufacture service
ownership from geometric user regions: native access/backhaul routing decides it.

### A complete first comparison if this design were selected later

| Arm/exposure | Proposed endpoint and rights |
| --- | --- |
| L, one exploratory fit | 64 new H3000 worlds/at most 192k native steps as above; one fixed final checkpoint. No intermediate evaluation, tuning sweep or selection by validation return. |
| O, zero fits | Same information/model/library/refresh/execution; one fixed 60-step scorer, no tuning on final worlds. It receives no fewer model calls or shorter horizon than L. |
| P, zero fits | Exact retained B04 five_ten complete controller under its historical guard/shield and ten-step rules, evaluated anew on the common panel; smaller library/scorer cost explicitly reported. |
| Final panel | Each arm on the same 32 genuinely new H3000 worlds, at most 288k native steps. No old B02/B04/B05 or 957001–957032 world is called unseen. Exact world, fit and policy-RNG seeds would be reserved/scanned before any future declaration, not invented or registered by this design. |

Total template: one started training instance and at most 160 episodes/480k
native steps. This is not 32 training replications and not a universal one-fit
limit. Training/tuning rights differ in the intended way: L receives real
experience/optimisation; O is a fixed model-based rule. Thus L−O asks whether that
extra learned package is useful at its full cost, not information-free causality.
No model rollout labels are fed into PPO targets. All nominal model transitions
are additional work, distinct from the 480k native interaction count.

Primary estimand: paired **complete QoS sum/3000 and raw native J for L−O**,
conditional on this fitted instance and its stated policy sampling scheme.
L−P is the secondary competence contrast; O−P prices ordinary package usefulness.
Also report QoS/actual step, episode length/terminal type and throughput. Keep
naturally early-terminated worlds; no padding of their trajectories or replacement.
The horizon-normalised service denominator exposes lost remaining service without
changing the environment's reward. Pair on verified common initial/exogenous
inputs/prefixes, not matching seed numbers alone. Report all 32 signed differences,
paired t31 descriptive intervals and the n=1 training limitation.

A concrete prospective usefulness recommendation is mean L−O and L−P QoS/3000
at least +.01, and positive raw J differences, subject to the risk branch below.
The .01 is a proposed use threshold (0.3 demand-normalised full-user equivalents
per step with 30 users), not an inherited B02 gate, observed effect or claim of
precision. A later different choice must precede data; no post-result lowering.
Positive conditional effects would justify pricing independent training replication,
not confirmation or adoption. An empirical learning claim still needs at least
three independent training seeds and a prospective claim/evaluation contract.

Report native capped/uncapped return cost, minimum battery for every world and
mean of the eight lowest world minima, fixed 10% reserve exposure, negative-margin
exposure, native 2% service cutoff/depletion events, zero-service worlds/steps,
charging and waiting with censoring, and worst per-world differences. Additional
cutoff/depletion/whole-world zero-service outcomes, a worse mean reserve exposure
or worse lowest-eight battery mean are explicit **tradeoff/no-adoption** outcomes
even if mean service/J passes. All other adverse worlds and intervals remain
visible; zero events do not establish safety or equivalence. No rescue success
criterion based on lower compute is added.

If O improves but L adds no useful increment, retain only the conditional ordinary
asset if its own tails permit that use. If neither clears the complete utility
comparison, end this package. Mixed endpoints/risks are a tradeoff; intervals
crossing zero are uncertain, not equivalent. An incomplete panel is neither a
positive nor a completed scientific negative, and no automatic retry is included.

### Complete cost of the proposed comparison, and current design cost

Counts below are configuration arithmetic, **not new scoring, profiling or a
simulation experiment**. Full-length worlds have 300 real decision boundaries.
The 64 training + 32 L evaluation + 32 O evaluation worlds yield at most 38,400
scored boundaries. With at most nine candidates and 60 primitive prediction
steps each, the nominal rollout budget is **20,736,000 model-step evaluations**
plus model construction and any initial routing snapshots. Active visits and
no-opportunity states reduce this bound; their prevalence is not known. At
boundaries with only one action the common scorer can be skipped by both arms,
using a missing-score mask, because no ranking is possible.

| Work | What is known and unknown |
| --- | --- |
| Design now | 0 started fits, 0 native/environment/model rollout steps, 0 experiments. Source/primary-literature reads, notebook writing and one focused independent design review have nonzero unmetered CPU/agent/token and elapsed cost; no total stopwatch/accounting claim. |
| Native exposure if run | At most 192k training + 288k evaluation steps; imports, simulator evolution and recording are additional to optimiser work. 64 training worlds are proposed exposure, not demonstrated sufficiency. |
| Learning if run | One actor/critic instance, at most 384 optimizer updates/76,800 segment exposures; training-time actor inference and common scorer calls included, not the old B02 39.36-second fit. Actual CPU/GPU wall, RSS and convergence unknown. |
| Ordinary and shared inference | Up to 20.736M **full model steps**, each with radio/routing, energy, guard and charging, plus legal-state reconstruction. This is not 20.736M cheap neural calls. Holding users fixed saves stochastic motion but does not remove service computation. |
| Numerical scale only | Earlier B02 planning notes cited technical static-snapshot timings of 8.1–13.4 ms; multiplying that *different unit* by 20.736M gives 46.656–77.184 worker-hours. This is a sensitivity illustration, **not a measured forecast price or bound**: full model steps, caching, opportunity frequency, node and concurrency differ. It nevertheless exposes why 480k native steps alone is an incomplete quote. |
| Historical anchors | B02 complete runner 3.86090 h, worker CPU 7.67307 h, fit 39.356 s, 351,671 service snapshots; B05 54.802 min acceptance-to-exit, 3.60844 worker CPU h and 131,812 snapshots. Neither can be multiplied into a reliable price for this new model. |
| P | 32 new evaluation worlds; at most 182,400 B04 static snapshots (32×300×19), in addition to its native steps. Its smaller computation is reported rather than matched with dummy work. |
| Storage/engineering/readback | Needed: a legal-state model constructor, exact option state machine, data/learner/evaluator integration, numerical/RNG checks, independent engineering review if implementation is later selected, hashes/compact outputs and one canonical raw copy. New wall/CPU, storage and repair costs are unknown. Existing B02's ~307.4 MB does not price 60-step forecast traces; storing every forecast state would be unnecessary bulk. |
| Node and failures | No reservation/admission now. Any later result work prefers configured wsl_4070 with fresh resource checks; old local_linux rates are not that node's quote. Known prior technical failures remain unresolved evidence, neither proof of an inevitable failure nor a license for a diagnostic/retry programme. |

Algorithm-intrinsic prediction accounts for the 60-step candidate rollouts; an
exact counterfactual suffix, full donor combinatorics, tuning grid or calibration
probe is **not** added as verification. A coarser ordinary predictor could lower
this price, but would be a different design whose adequacy/estimand must be stated;
it cannot secretly weaken the comparator after the learned arm is chosen.

### Provisional investment judgment and focused review question

The design is technically expressible and addresses an untested action. It does
not yet supply an independently motivated new learning mechanism; its possible
value is a conventional residual learner's complete conditional utility. The
ordinary forecast handles much of the conjectured short diversion/recovery
effect, while substantial additional model work, surrogate construction and
finite policy variance remain. The old completed negative lowers the attraction
of another generic score-learning package without proving this one will fail.

My provisional choice is **do not purchase this concrete L/O/P package now**.
That is an opportunity-cost judgment about this proposal, not a requirement for
measured headroom, novelty, a positive toy or diagnosed old failure before any
future learning work. A cheaper O, additional donor search, alternative residual,
or a diagnostic of eligible events is not automatically selected as a successor.
The strongest reason to disagree is that the new executable support decision and
the direct matched native comparison could be informative enough to warrant this
cost even with a conventional learner. The focused independent reviewer is asked
to decide precisely that issue and challenge the feasibility/cost reasoning,
reusing the completed portfolio question-selection review rather than re-auditing
the four old directions.

Claude's service-adaptive anchor/spatial-deployment question remains independently
owned. This design fixes H1 generation/matching and lets one member make a finite
visit to an observed departure position. There is indirect trajectory-induced
H1 rematching at later clocks, already disclosed above, but no learned final
anchor or assignment. If Claude's actual intervention becomes that same finite
visit/comparator, the scientific objects overlap and Root's coordination should
resolve ownership; this notebook does not change Claude's records or contact it.
No current evidence requires reviving SCC/T-prime or a host-wide credit exclusion.

### Independent scientific review — completed 2026-09-28 UTC

Reviewer: registered `hmasd-research-critic`, internal bounded task
`/root/handoff_design_review`, `fork_turns="none"`. This is the one focused review
of this concrete design/investment decision; the portfolio review above already
covered question selection. The full substantive answer follows, with raw-record
links made repository-relative and code links pinned to the inspected source.
Its later retransmission after context compaction was retrieval, not a second
review or a new experimental operation.

**Recommendation: decline this concrete L/O/P investment now, while retaining temporary support visits as an untested opportunity.** The design is scientifically interpretable and technically expressible. Its limited new discrimination does not currently justify constructing the surrogate simulator and paying its repeated search cost alongside PPO. This is an investment judgment, not evidence that learning or handoff cannot help.

No DM/Root conversation was inherited. The assignment disclosed the proposed package and provisional decline, so this was a separate-context review, not a blinded one. I reconstructed the source constraints and native outputs before reading the full notebook. The inspected interfaces remain unchanged from `754d5d34d…` at current main `b4479693a`. No implementation or experimental work was performed.

The completed evidence supports the following reading:

| Comparison | Native observation | Consequence |
| --- | --- | --- |
| B04 P−H_central@10 | QoS +.010578; J +34.736, with adverse worlds | Ordinary transit decisions already have demonstrated conditional value. |
| B05 five_ten−one_step | QoS +.016071; J +35.808 | Temporal prediction helps on this panel, but world 28092823 gained service while losing 260.945 J and increasing reserve exposure by .162792. |
| B02 L−P | QoS −.016488; J −55.389 | The completed offline hold-learning package was adverse. World 29102732 lost 363.316 J with reserve exposure +.147333. This does not diagnose why it failed. |

These readings come directly from the [B04 summary](../../../../runs/energy_relay_availability/b04_transit_hold_a01/summary.json), [B05 summary](../../../../runs/energy_relay_availability/b05_one_step_comparator_a01/summary.json), and [B02 native records](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/summary.json). The failed SET/PPO comparisons remain missing endpoints.

The proposed action genuinely differs from old B02. B04 disables discretionary holds whenever any shield mode is active; it never tested another eligible member visiting the departure position. Preserving H1’s generator, matching rule and private continuation memory is feasible. The notebook correctly distinguishes that invariant from identical future assignments: actual movement changes later matching distances and modes.

The interface nevertheless needs a few explicit choices before becoming executable:

- **Events:** accept the author’s correction of one live event per source, with return entry replacing its transit event and cancelling support tied to the old event. Also specify whether between-clock entries are latched or detected from successive clock samples, including entry-and-release between samples. Otherwise opportunity counts and the nine-candidate bound are ambiguous.
- **Model initialization:** fresh association/routing is an approximation to native history. Native service association uses previous serving sets, and the guard uses current dependent routes. Reward initialization also requires an explicit treatment of graph potential and episode-level `cutoff_event_seen`/`depletion_event_seen`; these are not ordinary reset defaults at an arbitrary decision boundary. These are bounded implementation specifications, not reasons to demand another diagnostic programme.
- **Execution:** eligible means a lawful attempted diversion. A dock-zero donor lacks the return-action guard exemption and can remain blocked until expiry. The notebook correctly retains this possibility. Sources are the [native guard](https://github.com/CartmanFatass/My-paper-code/blob/754d5d34d905a81b58b78e69ae85b8a07cb19aad/envs/pettingzoo/relay/energy_aware.py#L2169), [route-dependent checks](https://github.com/CartmanFatass/My-paper-code/blob/754d5d34d905a81b58b78e69ae85b8a07cb19aad/envs/pettingzoo/relay/routed_core.py#L3294), and [safety-event accounting](https://github.com/CartmanFatass/My-paper-code/blob/754d5d34d905a81b58b78e69ae85b8a07cb19aad/envs/pettingzoo/relay/energy_aware.py#L677).

O is a competent primary comparator: it receives the same finite library and prices joint service, diversion, energy and charging consequences. It is not an established optimum. In particular, **60 steps do not cover complete donor recovery**: a 900 m outbound trip can take 30 steps, followed by ten-step dwell, leaving only twenty forecast steps for resuming a potentially distant H1 target. Static users and reconstructed routes leave further error. Learning could improve expected choices under these limitations; O’s strength does not establish saturation.

Ordinary replacement scheduling is also substantive prior art, but its assumptions differ: HoRR/HeRR dispatch backups before departure and control replacement timing. This proposal reacts to observed departure while preserving the shield, so it cannot inherit continuous-coverage guarantees. [Original scheduling algorithms](https://arxiv.org/html/2205.12656)

The strongest additional simpler alternative is **ordinary randomized score selection**. L at zero residual samples `softmax(s/.02)`; O takes deterministic argmax. Therefore an eventual L−O gain would not by itself establish that PPO updates helped. It could include a benefit from stochastic selection. The notebook’s complete-package interpretation remains valid, but “learned increment” needs this qualification.

If a future decision specifically targets improvement attributable to the trained residual, one economical prospective correction is deterministic argmax evaluation for both L and O, with identical tie ordering. Zero residual would then reproduce O without buying a fourth evaluation arm. Keeping sampled evaluation is also legitimate if the claim remains the trained stochastic package’s utility. Neither correction selects a run now. The original residual-learning construction preserves its supplied controller at zero residual; this proposal preserves its soft version instead. [Residual Policy Learning, §IV](https://arxiv.org/html/1812.06298v2)

The learning specification is otherwise coherent: actual on-policy rewards, finite-horizon zero continuation, masked categorical actions and conventional PPO. There is no evidence that 64 training worlds suffice, and no basis to diagnose a later negative as inadequate data or optimization automatically. PPO’s clipped surrogate supplies an optimization method, not a guarantee on this partially observed host. [PPO, §§3–5](https://arxiv.org/pdf/1707.06347)

The proposed complete observation would change decisions:

- L clears the declared service/J criteria against O and P without the risk tradeoff: conditional package usefulness, sufficient to price independent training replication.
- O improves over P while L adds no useful increment: retain ordinary scheduling only if its tails and full cost permit use.
- Neither package clears the complete comparison: stop this package, without generalizing to all support libraries.
- Few executed visits constrain this interface’s opportunity; technical failure supplies missing evidence.

Whole-world endpoints, horizon-normalized service and adverse tails are appropriate. Event-window readouts remain descriptive because policies change the events themselves. Thirty-two worlds estimate conditional deployment variation for one fitted instance; they are not independent training replications. The strict risk branch is a prospective use rule, not proof that every small adverse point estimate reflects population harm.

Cost arithmetic is consistent: at most **480k native steps, one fit, 384 optimizer updates, 76,800 segment exposures, 20.736M shared forecast steps**, plus P’s at-most 182,400 snapshots. The forecast figure is a loose ceiling; sparse opportunities and active visits can reduce it substantially. The 46.7–77.2 worker-hour sensitivity uses a different unit and must not become a price or lower bound. Actual model occupancy, construction, storage, integration and readback costs remain unknown. Historical B02 cost—3.861 hours elapsed, 7.673 worker CPU hours, only 39.36 seconds fitting—shows why optimizer cost alone is misleading.

The substantive reason to decline is the combination: L retains all of O’s planning cost, introduces substantial new integration work, and offers a narrow conditional test of residual correction whose positive result still admits simpler explanations. Its conventionality alone would not justify rejection, and the upper-bound cost alone would not either. I select no preliminary probe, cheaper replacement or repair programme. If the question later becomes worth purchasing, the proposed complete native comparison is a defensible starting observation after the stated specifications are resolved.

**MATERIAL_DISSENT: no — I support declining this exact new investment. Preserve the stochastic-comparator limitation, incomplete recovery horizon and explicit model/event semantics; none authorizes implementation or a run.**

### DM disposition — final design corrections and decline this investment

<a id="final-design-disposition"></a>

**Decision: decline this concrete residual-PPO/rolling-scheduler/P investment;
the direction is reserve.** The bounded design assignment is complete. There is
no accepted operation, active worker, unread consultation, selected next probe,
retry, fit or pending approval dependency. Temporary support visits remain
untested; this is not an empirical negative for handoff or a general learning
impossibility. I adopt the review, including the following explicit design
corrections. They supersede the corresponding proposal text above while
preserving that text and the review as the decision record.

1. **Match the deployed selection rule.** At evaluation both L and O use
   deterministic argmax over exactly the same valid candidates, with identical
   no-handoff/release-first then source/donor index ordering for exact ties.
   Compute the shared base logit once in float64 as
   `b = (predicted_native_reward_sum / actual_forecast_horizon) / 0.02`.
   O ranks `b`; L ranks `b + float64(f_theta)`. Do not rank unnormalised sums
   in one arm and rounded logits in the other. Thus an exactly zero residual
   reproduces O's choice, including arithmetic/ties; there is no epsilon tie
   adjustment. The actor still samples its masked categorical policy during
   on-policy training. The formerly proposed sampled **evaluation** and its
   policy-RNG panel are withdrawn prospectively, before any exposure. Counts
   are unchanged and no fourth arm is added. This removes randomized versus
   deterministic deployment as the L−O explanation; it does not isolate a new
   architecture, credit mechanism or universal value of PPO. The conditional
   deployment variation is now across the 32 worlds for one frozen fitted
   instance with deterministic selection.
2. **Fix event semantics.** Keep at most one live event per source. Detect
   return entry/release from effective modes sampled at successive ten-step
   clocks, using a separate previous-clock mask; H1 still receives the actual
   previous primitive-step shield mask. An entry followed by release entirely
   between two clocks creates no event. An entry that remains visible is
   registered at the next clock's observed xy. Return entry replaces any live
   transit event for that source and cancels a visit tied to that old event;
   return has priority if both triggers coincide. A transit latch starts False
   (ready), becomes True on the >300 m event, and rearms only at a sampled
   non-returning, valid-H1-target distance ≤30 m. Expiry alone does not rearm it.
   Return release and transit completion end source events at sampled clocks;
   donor ineligibility, arrival/dwell completion and the fixed 60-step expiry
   are checked every primitive step. These are ordinary deterministic option
   rules, not additional planning calls. Eight sources still imply at most
   eight source/donor candidates plus no-handoff; an active visit has only
   continue/release. The sampled event definition may miss short departures.
3. **Fix reward-state reconstruction.** The shared model begins with fresh
   legal-geometry association/routing and computes its initial graph potential
   from that reconstructed state using the native graph-potential function.
   It does not take `current_graph_potential` from private live state and does
   not silently set it to zero at every arbitrary boundary. Carry that model
   potential between predicted steps. Apply the native zero-next-potential
   rule only on a predicted actual episode end, not merely because the
   60-step planning horizon ends. Maintain two observed-history safety latches
   from reset: initially False, then update after each real primitive-step
   observation. Under the frozen S2 with no injected failures, observed
   unavailability supplies the cutoff latch; decoded battery ≤0 supplies the
   depletion latch. Initialize each forecast's once-per-episode safety flags
   from those common latches and update them by the native model equations
   thereafter. This uses legal own-energy history, not extra user snapshots
   or hidden event flags. Float32 battery reconstruction and missing native
   association/potential history remain approximations; no claim of exact
   live-state equivalence is made. All other observable charging/target/wait
   records and configuration follow the declared reconstruction above.
4. **Limit the recovery statement.** O prices only the recovery portion that
   falls inside its 60-step window. It may miss important later donor costs
   or gains; no horizon extension, learned terminal value or preliminary
   headroom measurement is selected. This limitation is a possible reason for
   learned residual usefulness, not evidence that it will occur. Similarly,
   eligibility permits an attempt; it does not certify guard-passing motion.

After these corrections the case for declining is still the joint cost/use
judgment: substantial new legal-state simulator and option integration; every
learned decision retains the ordinary rollout search; and the proposed learning
contribution is a conditional residual correction with no independently grounded
new mechanism. A successful complete native comparison could be useful, but its
current expected scientific discrimination does not justify buying this package.
This is not a novelty requirement for experiments, an assertion that O has solved
the host, or a rejection derived from the 20.736M ceiling alone. Sparse eligible
events could make actual inference far cheaper. No cheaper scorer, randomised
ordinary arm, diagnostic, alternative learner or donor-library expansion is
automatically selected to rescue the investment.

The hypothetical complete comparison and outcome-dependent decisions above are
retained as a concrete alternative, **not a launch contract**. Native QoS/J,
return penalties, all adverse worlds and risk tails remain the use criterion;
small negative risk estimates trigger the proposed conservative use rule without
establishing population harm. No seeds, source snapshot, resources or admission
were reserved. One exploratory fit would remain one training instance, and
positive conditional usefulness would only justify pricing independent training
replication. Historical B02/B04/B05 and technical failures retain their original
endpoints and scientific limits.

The peer's newly published `b4479693a` [reasoning-phase candidate](https://github.com/CartmanFatass/My-paper-code/blob/b4479693a/docs/research/candidates/energy_relay_benchmark/NOTES.md)
changes final goal generation to relational entity-pointer decoding and learned
low-level goal execution. This design preserves H1 generation/matching and only
substitutes one finite support waypoint. That is the actual intervention boundary;
their calendar phases need not be disjoint, because an initial H1 transit can
occur before the first shield entry. This observation neither endorses the peer's
mechanism claims nor changes its experiment, notebook, ownership or Pro request.
Root's shared project plan and routing remain Root-owned.

The independent critic supplied the distinct challenge needed at this selection;
there is no unresolved material disagreement or additional Pro expertise sought
for this declined conventional package. No Pro send is made. This is not a
standing exclusion of Pro for future questions.

**Actual incremental research execution remains 0 fits, 0 result episodes,
0 native steps and 0 nominal rollout steps.** Reading/writing/review and metadata
checks used nonzero unmetered resources. No experimental code, scratch dataset,
model checkpoint or bulk runner output was created, so there is no new bulk
cleanup or disk-reclamation claim. Publication checks concern only document
links, source identities, cost arithmetic and the owned index change.

For the shared logit in correction 1, `actual_forecast_horizon` means the
**common requested horizon `min(60, 3000 - current_step)` for all candidates**.
A predicted natural termination stops that candidate's transitions and reward
sum, but does not shorten this denominator. Thus horizon normalisation cannot
turn early termination into a higher per-surviving-step score or change the
ordinary sum-ranking objective; the last real episode window alone shortens the
common horizon. No extra post-terminal model steps are generated.
