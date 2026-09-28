# UAV active sensing

## 2026-09-28 - Native question assignment and prospective comparison

Direction lead: `Codex DM (native child)`, native address
`/root/dm_active_sensing`, assigned by Root `/root` in task
`01a0e560-4333-7b03-8ff3-759a4add1d9a`. Author on shared `main` at
`/home/fires/hmasd-wsl`, owning only this direction's implementation, tests,
notebook, runs and scratch. Root commissions one combined independent scientific
review for the new questions. No duplicate critic is requested here. This entry
is a proposal for that review; no result launch is selected before its disposition.
Current cost: 0 fits, 0 native transitions, 0 evaluations. No historical accepted
operation was restarted or inherited. The global pause is lifted; PPC/FSD holds
and G33's frozen identity remain outside this question.

### Question, inherited evidence and actionable uncertainty

Can deliberate travel to obtain observations improve complete service under S7's
existing legal pooled-observation contract, beyond ordinary service deployment
and a competent geographical search prior? The intended contribution is empirical
understanding and possibly a useful ordinary controller. This first study claims
no new learning algorithm, optimal information value or decentralised execution.

Published background inspected at `origin/main`
`6dfbc9731e911de00d76d2b812063a741a4a0dfb`: [RESEARCH topics 2, 6 and
8](../../RESEARCH.md#研究背景与共享认识). The static-BS/current-demand distinction
requires ordinary BS memory in every arm. The adverse event-replanning result
means faster observation refresh is not presumed useful. The information-value
discussion requires complete native outcomes, since acquiring information also
changes travel, backhaul and energy. The finite-model B01/B02 findings concern a
different small host and sparse task completions; they discourage crediting a
proxy improvement as native benefit, not testing native sensing. The old spatial
mixture-training failures do not address active observation choice. No former
particle-budget or training-mixture route is reopened.

Original evidence read: benchmark B01 `b01_ref_a02`, source `e1fdbe72f`, its
[complete reading and later corrections](../energy_relay_benchmark/NOTES.md#2026-09-26--b01-result-read-by-the-pre-registered-branches-operation-02f762d2-tag-b01_ref_a02),
and [the reconstructed information contract](../uav_information_value/NOTES.md#actual-information-and-decision-contract).
B01 completed 540 H3000 episodes, 1.62M native steps, 0 fits, 6197 seconds
runner wall; its superseded attempt adds about an hour, reported there as about
two node hours overall. Production H_central/H_local QoS is .774024/.596939 and
native J is 2281.887/1628.446. H_local had one zero-service world and much larger
return cost (65.9 versus 4.8), although no cutoff/depletion. H1 was selected on
eight central development worlds, not separately tuned for local input. The .177
QoS difference contains input ordering, clustering and fallback behavior and is
not pure information headroom. The later B01 corrections withdraw the station-
prior causal reading and qualify the exit-width and risk interpretations.

Relevant source facts, verified directly:

- `configs/config_1.py` and native `make_eval_config` select S7-S2, 8 UAVs,
  30 users, 8000 m square, H3000, RPGM speed at most 3 m/s, 5 initial clusters.
  Four cluster centers are uniform in the central [2000,6000]^2 region; one
  remote cluster is near the corner opposite the actual BS. The exact remote
  corner becomes a legal distributional prior only after the BS is legally
  known. Before that, all four corners remain possible. The controller must
  never obtain the world's true unknown cluster coordinates, target velocities,
  memberships or future random draws.
- `local_view.py::_get_local_users` uses a 1500 m three-dimensional radius.
  At 100 m UAV height the horizontal radius for 1.5 m users is about 1496.8 m.
  All 30 users fit in the 30 anonymous, distance-sorted slots; slot identity
  does not persist. Pooling all eight legal observations is permitted by the
  existing reference contract. This is a central pooled controller, not eight
  independently informed actors.
- `routed_core.py` rebuilds the BS cache from current visibility; the one BS is
  static within the episode. Every arm retains a BS once legally seen and clears
  it on reset. This is common competence, not the experimental intervention.
- Station records and all UAV positions/batteries are always in the energy
  suffix. Station 1 is a noisy initial demand-mean anchor, with up to 960 m
  component-wise jitter plus clipping/separation. It is not a true demand map.
- H1 replans each 30 steps, supplies six service centroids and two relay points,
  assigns with distance/hysteresis, flies at 100 m and at most 30 m/s, and keeps
  the native return shield and backhaul guard. With at least six current legal
  users and a BS, no UAV is left for its station-1 ring search. Thus one observed
  cluster can in principle consume the full service allocation while another
  remains unseen. This is a possible failure mode, not its measured frequency.

The central region's 4 km side and the remote cluster leave plausible actionable
uncertainty despite the relatively large sensor. Eight UAVs can also discover
much of it incidentally while serving; that is the strongest explanation against
a dedicated scout. No new diagnostic episode is required before a useful complete
policy comparison. Existing result panels are development knowledge, never fresh
test evidence for this direction.

### Recommended first complete comparison

Recommend a single exploratory S2/H3000, zero-fit comparison on **16 fresh paired
initial world seeds**, three fixed programs (48 episodes, at most 144000 team
transitions). Fix seeds and the executable policies after the combined review,
before any result exposure. Keep the original environment, observation delivery,
native rewards, demand, faults, shield and guard. No oracle controller is needed:
the information-value DM separately measures privileged-source consequences.

| Program | Complete policy | Intended reading |
| --- | --- | --- |
| H | Ordinary legal H1 deployment with common static-BS memory and the existing station-ring fallback | Capable no-dedicated-scout service anchor; it already searches when too few targets exist |
| P | H plus at most one service UAV assigned to a deterministic, public-prior geographical patrol; discoveries feed the ordinary service planner | Strong ordinary search/deployment alternative, not random motion |
| A | Same scout resources, candidate geography and service planner as P; choose scout visits using actual legal sensing footprints and their age | Increment of feedback-directed active acquisition over ordinary prior search |

All three assimilate the same delivered legal observations and share exactly the
same static-BS memory code. A and P share ordinary survey history, but P's waypoint
order is fixed by its geographical sweep rather than scoring remaining uncertainty.
There is no anonymous user tracker in this proposal. Current detections retain
priority; ordinary deployment is replanned after every visit from current input.
No hidden truth, future target or simulator RNG is passed to a controller.

The bounded policy family proposed for review is a one-scout geographical search.
Both P/A preserve the two H1 relay assignments. They can repurpose at most one
available service-assigned UAV, chosen by highest legal return-energy margin,
with deterministic index ties, only while that margin exceeds .20. The scout
uses the same primitive speed/altitude and can be overridden by the same native
shield/guard. No low-margin UAV is forced to continue a search. When all 30 users
are currently observed, all available UAVs return to ordinary deployment.

Candidate search geography comes from a fixed 500 m lattice over the public
central-demand region and the possible remote-corner support. The whole-map
position law is known, but exact world coordinates are not. A simple public
prior puts 4/5 of mass over the central region and 1/5 over the remote support;
it is explicitly a search approximation, not an exact posterior for moving RPGM
users. A never assumes that the initial support remains a hard support at later
times. Already observed areas supply negative evidence only after accounting for
the finite radius and elapsed time: a past empty footprint shrinks at 3 m per
elapsed step before being treated as still cleared. The implementation must use
complete-cell containment, not a center-only claim that a square was fully seen.
This needs no true user IDs or cross-time slot association.

P's deterministic nearest-neighbour tour visits this same finite geography, with
a visit counted only after its waypoint is within sensing radius; completed tours
cycle to accommodate mobility. A instead chooses the waypoint with the largest
public-prior mass outside the current/remaining cleared footprints per planned
travel time, with travel-distance ties and prior-target hysteresis. The basic H1
service target remains a candidate; search commitments are bounded to at most
90 steps and are revisited on the common 30-step plan clock. A new detection is
immediately available to ordinary replanning in both P/A. No extra observation
call, reward bonus or private measurement is added. Exact selection/hysteresis
and fallback arithmetic must be fixed in L0 after scientific review; none is to
be tuned on the result panel.

This is a complete policy-family comparison, not an exact Bayes-adaptive planner.
An information-theoretic calculation is not used as a surrogate endpoint. A's
proposal criterion values information coverage, while P supplies the ordinary
geographical search alternative; service, radio paths and energy determine whether
either actually pays. If the review regards this family as too weak or the proxy
as insufficiently connected to service, revise now or decline it before exposure.

### Contrasts, predictions and what can be distinguished

Primary policy contrast **A-H**: net native use of deliberate adaptive sensing
under equal legal information rights and ordinary static memory. Companion
contrasts **P-H** and **A-P** distinguish a general geographical-search improvement
from the usefulness of directing that search with legal observation history.
These are total consequences of fixed closed-loop programs; identical reset seeds
do not fix later states, routing, sensor footprints or random-number consumption.
They do not isolate a pure information mediator from the physical consequences
of travel, nor identify the optimal value of information. A positive result would
support this active-search package, with that limit explicit.

Working prediction: A reduces the duration of missing current demand, increases
legal discovery of previously uncovered demand and improves complete QoS/J over H;
feedback-directed scheduling may reduce wasted travel versus P. The opposing
prediction is that ordinary service motion plus the public-prior patrol reveals
enough, and allocating a scarce service UAV to discovery adds travel/backhaul cost
without useful service. The intermediate and native parts are separately testable.

Read native QoS/actual step and native J together, plus delivered throughput,
return-cost components, minimum battery, reserve exposure, cutoff/depletion,
zero-service worlds, complete duration and termination. Evaluator-only truth may
label first discovery, number of current users in the sensor union, first time all
30 have been discovered, and discovery ages. These diagnostics must be in a
one-way observer and never select actions. Report actual horizontal distance,
scout decisions/steps, fulfilled/guard-blocked visits and service lost/gained on
the complete trajectories. Discovery alone is not utility, and no-failure counts
do not establish safety.

- If A/P both improve H but A-P is small or unresolved, ordinary systematic
  search is sufficient for the observed improvement; adaptive sensing has not
  earned its added machinery.
- If A improves native service/J over both while producing useful additional
  observations at measured travel/risk cost, retain conditional evidence for its
  complete package. Do not call the correlational process reading causal VoI.
- If A finds more demand but does not improve complete utility, the acquisition
  mechanism activated without paying for itself; more search is not an automatic
  repair. If scout activation is absent, read nonactivation, not failed sensing.
- Mixed world signs, risk tails, wide intervals or a technically incomplete panel
  remain explicit. No outcome triggers an extra seed, tuning sweep, neural fit,
  longer horizon or renamed retry. The broader active-sensing question may remain
  open even when this bounded investment ends.

Use per-world paired signed differences with descriptive paired uncertainty and
all losses preserved. The independent unit is the initial world for these fixed
programs, not a step or repeated scout visit. This is exploratory, with no
equivalence claim, confirmation or learning-seed claim.

### Full cost, implementation boundary and next action

Prospective dominant work: 3 x 16 x H3000 = at most 144000 native transitions;
at most 4800 ordinary H1 plans; 96000 primitive-step survey updates across P/A;
at most 3200 finite waypoint decisions, with candidate count bounded by the
published lattice. No simulated suffix trees, optimization, parameter fitting,
extra evaluation panel or training is proposed. A compact 32 x 32 survey grid
would entail at most 8 x 1024 containment checks per update, about 786 million
small geometric checks across both scout arms before vectorization. This is
real algorithm cost, not free because fits are zero; lower-resolution bookkeeping
or updating only on the 30-step clock can be chosen before implementation if its
semantics are stated. Do not claim a speedup before measuring the complete path.

Availability B01's 128 episodes took about 46 runner minutes with four workers;
48 episodes alone would scale to about 17 minutes before this policy/observer
cost and contention. Initial node estimate **30-60 minutes**, not a hard scientific
limit or measured runtime. Engineering, independent executable review and reading
are additional; exact wall/CPU/RSS will be reported. Prefer configured `wsl_4070`
with actual admission at launch. Node admission is unnecessary for this reasoning.

Next action: Root's combined Scientific Reviewer challenges this actual comparison
and the parent question. Then record the resolved policy, exact seeds and concise
L0; implement on owned paths, use focused leakage/RNG/native-evaluator checks and
independent engineering review, publish exact inputs and only then admit the
single complete batch. No worker/observer/accepted handle exists yet. No cleanup
target has been created and no reclaimed disk bytes are claimed.

### Pre-review implementation refinement and source-cost correction

The complete original benchmark record reports 6197 s for the completed B01 and
about two node hours including its superseded operation. The sentence above that
adds "about an hour" should not be used to recompute that total: it inherited an
earlier estimate beside later stop times. Retain the measured complete-operation
wall and report the superseded-attempt cost as historically approximate.

The proposed scout activates only after a legal BS sighting and when the current
canonical user count is at least six but below thirty. The existing H1 ring
continues to handle initial deployment with too few detections. This isolates the
specific question of searching beyond an already acquired service cluster and
avoids spending this study on initial BS discovery, which is outside its intended
increment. Both P/A use the same activation rule and ordinary BS memory. Losing
eligibility, shield control or the legal .20 return margin ends the commitment at
the next common replan. No truth-based eligibility or hidden count is permitted.

Use the common 30-step replan clock for survey-grid assimilation and waypoint
choice, not a new primitive-step memory update. A missed between-replan footprint
is deliberately not inferred; this is a conservative ordinary survey history.
Grid containment uses the actual 3-D sensing radius projected to the ground and
the maximum cell-corner distance. Previous surveyed footprints are evidence that
their then-present users were exposed, not that every such cell was empty. Any
claim about empty space must distinguish positive detections and use the 3 m/s
motion bound. The search approximation can instead score observation freshness
without asserting an exact count posterior. All eligibility, map and target
formulas still go to the same pending independent scientific review.

Revised dominant map cost: at most 3200 P/A replan updates, each at most 8 x 1024
geometric checks, or 26.2M checks total; at most 3200 finite waypoint choices.
The earlier 786M primitive-update option is declined before implementation, not a
measured optimization. Native exposure remains exactly the proposed 48 episodes /
144k transitions / 0 fits. No new pilot, tuning or hidden scenario tree is added.

Reusable implementation inputs already exist: the published
`uav_information_value.controllers.SourceController("H_BS")` and its
`PointSetHeuristic` implement canonical sort-then-merge legal input, the ordinary
planner and static BS memory. Thus H here means this canonical legal program,
not universal identity to historical H_local. The original evaluator's
`observer.on_step(...)` can collect truth-only discovery/geometry after each
native transition without a core edit. The future direction controller must not
retain the raw environment or consume `state`; poison-state/absent-env tests and
observer-off/on native replay will check this separation. Any new dependency on
this shared published candidate asset will be named before cleanup; another
direction's source or tests will not be edited.

### Direct learning alternative supplied to Root's same review

Root reports that the independent Reviewer provisionally supports H/P/A as a
narrow ordinary sensing-policy comparison and is also considering direct native-
return learning. A zero-fit comparison is **not** a prerequisite for learning.
No second active study or automatic conditional follow-on is selected.

A feasible direct object is a finite sensing/deployment selector: every 30 native
steps it chooses ordinary H1 service or a scout target from the same public
candidate geometry and one-scout resource/safety constraints used by P/A. It
consumes current pooled legal observations, ordinary BS/survey memory and legal
candidate features; actor and critic have the same information. The learner
chooses the target without adding a tiny residual to A's hand score. H1 remains
the common motion/relay/service asset, not a teacher label or privileged feature.
The objective is the sum of native rewards over the actual 30-step macro interval;
gamma=1 at macro time matches the finite H3000 native J objective. No intrinsic
information reward, true user labels, counterfactual simulator suffix or unseen
RPGM target is introduced. Episode truncation at the scientific horizon must
terminate the finite-horizon return rather than bootstrap beyond H3000.

Stable-Baselines3 is already installed in both configured scientific interpreters
(read-only module-spec checks on local_linux and wsl_4070); sb3_contrib is absent.
A direction-local Gym wrapper around the existing native stepping/shield contract
can therefore reuse ordinary PPO. This is feasibility, not validation: seed
binding, inactive choices, macro reward/time accounting, observation memory,
terminal/bootstrap semantics, reset isolation and the actual native evaluator
still require implementation checks and independent engineering review.

Suggested smallest useful learning comparison: **one 480000-native-step fit**,
160 complete H3000 training episodes / 16000 macro decisions, four environments,
100 macro steps per environment per rollout, 40 rollout updates, 10 epochs with
four 100-example minibatches: 1600 optimizer steps. Read its fixed endpoint and
its initialization on the same 16 fresh evaluation worlds as H/P/A: five fixed
evaluated programs x 16 x H3000 = 80 episodes / 240000 evaluation steps. Total
prospective native exposure is **720000 transitions**, 1 fit, no panel extension
or best-checkpoint selection. The one fit is exploratory; evaluation worlds are
not independent training replicates. The precise seeds, action library and PPO
parameters would be fixed prospectively if this alternative is chosen.

Scaling only native episodes from the existing 128-episode/46-minute reference
suggests about 86 minutes before training/feature overhead, contention and
readback. A conservative first total-node estimate is **2-4 hours**, with actual
training throughput unmeasured and engineering/review additional. This is more
expensive than H/P/A alone but directly answers a different consequential question:
whether native return can learn when and where sensing is worthwhile. The DM's
recommendation to Root is conditional on that scientific objective, not on a
prior toy, geometry probe or positive H/P/A result. Root's same independent review
will select one first study; neither alternative is launched by this entry.
