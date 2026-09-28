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

## 2026-09-28 - B01 direct native-J learning selected; fixed design and L0

Root selected the single integrated study after the [complete independent review](../../archive/2026-09-28/RESEARCH-expanded-native-dm-review.md).
The dedicated Reviewer reconstructed original evidence in its separate context,
recommended direct learning to test whether experience values the downstream
service consequence of sensing, and returned `MATERIAL_DISSENT: no` on the final
comparison. It specifically requires finite-H3000 returns and rejects a separate
rule-positive prerequisite. The DM read the complete review and adopts it. The
old H/P/A-only proposal remains above as selection history and will not run.

Freeze tag `b01_native_j_a01`: one CPU FP32 SB3 PPO fit, policy seed **28130001**.
Training initial worlds **28132001-28132160** occur exactly once, assigned in
round-robin order to four vector environments, 40 episodes per lane. Evaluation
worlds **28133001-28133016**, disjoint from training, are common to **L0, L1, H,
P, A**. L0 is the saved initialization, L1 the fixed 480k-step endpoint; both
evaluate deterministic categorical argmax. H/P/A are deterministic. There is no
checkpoint selection, calibration panel, tuning, extension or automatic retry.
This remains one fit / 160 complete training episodes / 16000 macro decisions,
followed by 80 complete evaluation episodes / 240000 native transitions, total
at most 720000 native transitions. Seed searches found no prior use of this exact
seed family in the inspected candidate records/sources/configuration outputs.

The native host is unchanged S7-S2/H3000. Each macro action lasts exactly 30
native steps unless native termination occurs sooner. Its reward is the actual
unscaled sum of the native team rewards in that interval. PPO gamma=1.0,
GAE lambda=.95, learning rate=.0003, clip=.2, value coefficient=.5, entropy
coefficient=.01, max gradient norm=.5, no target-KL early exit and no schedules.
Use SB3 MlpPolicy with separate [128,128] tanh policy/value networks, its ordinary
orthogonal initialization and advantage normalization, no reward/observation
running normalization and CPU device. Four environments x 100 macro steps per
rollout, batch size 100, 10 epochs, 40 rollouts yield **1600 optimizer steps**.
Record actual counts, parameter movement, losses and the training curves. There
is no recurrent hidden state; ordinary explicit map/BS memory is reset per world.

The finite scientific endpoint is terminal for learning, even when the native
environment calls it a truncation. Preserve that native flag in records but
return `terminated=True, truncated=False` from the macro wrapper at H3000; SB3
must never set `TimeLimit.truncated=True` or add a value beyond the endpoint.
At the last episode's vector auto-reset, return a nonstepped final observation
and refuse any later step, so the library cannot expose a 161st training world.
Early native termination is preserved and must make the fixed complete-exposure
contract incomplete; it does not silently fill the budget with new episodes.

### Policy family and exact implementation choices

All arms use canonical legal H1 planning, permanent once-legally-seen BS memory,
the existing 6-service/2-relay target generation, Hungarian assignment and H1
speed/altitude. Keep nominal H1 target history separate from a scout override.
At each 30-step boundary, at most one available service-assigned UAV may scout;
protect relay assignments, choose the largest legal return margin with lower
index ties, and require margin > .20, a known legal BS and 6-29 canonical current
user detections. Otherwise all requests execute H. The common native shield and
guard retain final authority. A request outside the discrete action range is an
error; a legal request in an ineligible state maps to H and is counted. PPO stores
the requested action/log probability, not a substituted action. Many-to-one
fallback is part of the environment response, not a post-hoc loss mask.

The common action library is **0=ordinary service, 1-256=one scout to a public
500 m cell center of the full 8000 m arena**, ordered x then y. This public full
arena library includes later user migration and avoids hard-coding initial
support as permanent knowledge. The search approximation places .8 of prior mass
uniformly over central [2000,6000]^2 and .2 over the known opposite remote-corner
square; mix 5% uniform whole-arena mass for later demand movement. This floor is
a predeclared heuristic, not an inferred probability calibration.

Use a 250 m survey grid (32 x 32). At each common plan, compute full-cell sensing
containment using each legal UAV position, 1500 m 3-D range, 1.5 m user height and
the cell half-diagonal. Store each cell's most conservative guaranteed visibility
expiry from its clearance divided by the public 3 m/s user-speed bound. This is
survey freshness, not proof that the cell was empty or an identified user map.
A scores prior mass stale by predicted arrival inside each target footprint,
divided by one plus travel seconds; 300 m continuation-distance hysteresis and
lower action-index ties. Zero positive new mass selects H. P follows a fixed
nearest-neighbour tour of the same public waypoint library, prioritizing the
central/remote-support points before its uniform-floor points; skip reached or
currently sensed waypoints, cycle after a completed tour. Both reselect only on
the common 30-step clock. This fixes 30-step commitments within the previously
proposed at-most-90 bound, without another decision frequency.

L receives the current legal observation array and explicit common BS/survey,
candidate-prior/geometry, eligibility and nominal-target features. No privileged
state, latent world coordinate, real user ID, future RNG, training label or A-score
residual enters the actor or critic. Features can expose the ordinary geometric
quantities used by A/P; L directly selects an action from the entire common library.

### L0 ownership, checks and reading

One bounded Implementer owns only
`experiments/candidates/uav_active_sensing/controllers.py` and
`tests/experiments/candidates/uav_active_sensing/test_controllers.py`: the common
legal-memory controller, finite action behavior, H/P/A selectors, features and
evaluator adapter. It reads this L0 and nearest AGENTS, writes no shared file or
notebook, mutates no Git index, runs no result panel and spawns no helper. It is
not alone in the shared checkout and must preserve other authors' work.
The DM owns all remaining direction files: macro Gym wrapper, SB3 training,
evaluation/readout, admitted entrypoint, records and their tests. No shared
learner/environment change or copied core is planned.

Focused checks cover legal-source poisoning/isolation, original canonical H_BS
action parity, survey boundary/age/reset, candidate bounds, relay protection,
eligibility/fallback, exact macro reward/native counts, terminal bootstrap,
complete and exhausted seed schedules, SB3 save/load and deterministic action
identity, numerical/RNG preservation with observer off/on, update count and
failed/incomplete publication. Use short nonpanel worlds only for wiring tests;
record their exposure separately. Independent engineering review covers this
actual executable diff before acceptance and launch. The DM accepts the helper
diff and its checks rather than treating helper completion as review.

Primary comparisons are L1-L0 and L1-A in native J and QoS, with L1-P and L1-H
retained to ensure a weak hand rule is not the sole reference. A/P-H and A-P retain
the original ordinary-search question inside this same fixed evaluation. Read
all native risk components, minimum battery, 10% reserve exposure, throughput,
zero-service worlds, discovery/current visibility and actual travel; uncertainty
is descriptive paired-world t95 for this **one trained instance**, not learning
replication. A gain only in discovery, proxy scores or training reward does not
establish useful deployment. No sign or interval automatically purchases another
fit; independent scientific interpretation at the result boundary will resolve
keep/revise/stop with the complete adverse evidence and measured costs.

### Implementation and nonpanel checks

The bounded Implementer delivered only the two assigned controller/test files;
the DM read and accepted that diff. Actor and critic use the same finite 5509
features: 8 x 365 legal observation values, legal BS flag/xy, 1024 survey freshness
values, 1024 public prior masses, 256 candidate xy pairs, eligibility, eight-way
scout indicator, sixteen nominal target coordinates, and the public step/3000
finite-horizon clock. The time feature makes the declared finite objective
available to both networks; it carries no simulator-only source. Nominal H1
history remains separate from the executed scout override.

The DM implemented a direction-local Gym macro adapter, ordinary SB3 PPO fit,
fixed post-fit evaluation, one-way truth observer and failure-preserving readout.
The native stepping path reuses production shield and original native metric
checks. It stores complete native reward/risk traces and macro requested/executed
actions. Four spawned processes isolate training-world RNGs from the learner;
world resets use the fixed world list rather than SB3's policy-seed reset list.
Each completed rollout is checked for all four H3000 ends, exact float32 storage
of unscaled native macro rewards, and unmodified requested categorical actions.
Only initialization and fixed endpoint are saved. Worker CPU/RSS and parent
wall/CPU are recorded separately; missing/early/failed work cannot yield complete
contrasts or start replacement worlds.

Local SB3 is 2.6.0. Two full focused runs passed **19 tests in 22.50 s and
22.47 s**; each exposed 480 nonpanel native steps and one short engineering PPO
optimizer update. The second uses the production TrainingAudit callback. They
cover real-native H_BS action/reward/metric parity, observer-off/on trace and RNG
identity, four subprocess seed schedules, terminal non-bootstrap with a nonzero
critic, exhausted auto-reset, saved-policy identity, failure readout and admission
before scientific effects. Test seeds are only 28139001/002 and 28139101-104;
none are training/evaluation seeds. This is wiring verification, not a research
fit or performance panel. Pytest cleaned its owned scratch.

The independent engineering Reviewer found a real L0 deviation: survey expiry
was updated at every primitive act, although the declared survey clock is 30.
The DM split that path: legal BS/own-position refresh remains every primitive
step, survey only updates in prepare at plan boundaries. A transient between-
boundary footprint regression now checks this distinction; the controller-only
suite passed **13 tests in 4.10 s**, no native steps. The correction changes no
accepted run because no result operation has been launched. Full independent
review is ongoing; no scientific result or engineering acceptance is claimed yet.

### Engineering acceptance and publication

The independent Reviewer found a second, higher-risk seed-contract deviation:
native BS geometry is initialized in the environment constructor and is not
resampled by reset(seed). Reusing one native object per training lane would have
made later world labels share the first world's BS. The DM now closes and
reconstructs the native environment for **every** non-exhausted scheduled world,
matching the existing evaluator. The last automatic reset still constructs
nothing. A two-world regression compares the second initial observation, BS,
native rewards and metrics with an independently constructed H_BS world under
the same nonpanel seed. It passed locally (1 test, 8.42 s, 90 native steps).

The separate Reviewer independently reran both repaired regressions: **2 passed
in 7.64 s, 90 nonpanel native steps, zero optimizer updates**. Its final finding
is "No material finding remains in the current eight-file implementation."
It traced legal actor/critic information, requested-action/log-probability storage,
finite-terminal bootstrap exclusion, complete rollout and optimizer counts,
checkpoint hash/fingerprint restoration, native shield/reward identity, one-way
observer effects and suppression of incomplete contrasts. It did not execute a
production panel or full fit; runtime success remains to be observed.

The DM accepted these repairs and the independent review. The final full suite
passed **21 tests in 32.71 s**, including 570 nonpanel native steps and one short
PPO engineering optimizer update. Total recorded verification exposure is
**1710 nonpanel native transitions and three one-update engineering PPO checks**,
separate from the one planned result-bearing fit. No training/evaluation panel
seed has been exposed. Pytest again removed its owned scratch. The target node
also reports SB3 **2.6.0**, Torch **2.7.0+cu118**; the declared learner remains CPU
FP32. No dependency was installed or shared learner changed.

Publish the exact direction inputs and this own ACTIVE/exploring row, then use
the configured wsl_4070 detached admission path with tag `b01_native_j_a01` and
four single-thread evaluation workers. Actual memory admission, not the old
estimate, determines when this may run. Preserve the accepted original handle;
no retry, new fit, new seed or budget extension follows from this acceptance.
Root has observed that App queue cannot wake an unloaded native child. This DM
therefore remains in its native turn, using deterministic same-handle waiting
and checkpoint rearming until collection and scientific reading, rather than
ending after observer registration or changing the observation target.

### 2026-09-28 - B01 native operation accepted

Exact published source is **38b7f132af8e26b851826f2e3db90a5fb5fb1a06**.
The configured wsl_4070 supervisor accepted the request and the native admission
kernel accepted this single operation at **04:26:06 UTC**. The authoritative
[manifest](../../../../runs/uav_active_sensing/b01_native_j_a01/launch-manifest.json)
pins the operation, runner/supervisor identities and immutable source snapshot;
the [actual-node preflight](../../../../runs/uav_active_sensing/b01_native_j_a01/admission-preflight.json)
measured **13,499,113,472** available physical/effective bytes against the
4,294,967,296-byte floor. Initial status and detached observation both report
accepted/running, consistent identities, no exit witness and zero probe errors.
This is an accepted training/collection operation, **not a read result**.

The same-handle observer is generation 1 at
`/home/fires/.local/state/hmasd-wait/01a0e600-4fa1-7060-91f0-ae8e132f0732`,
job `b01_native_j_a01`, with a 1500-second checkpoint window and 60-second
read-only status probes. Its first drain at 04:27:53 UTC adopted the accepted
manifest. Preserve this reference and rearm checkpoints without a worker restart;
the DM keeps its native turn active through deterministic waits.

Only this direction's published ACTIVE row was added to the dirty remote
canonical index under its writer lock. Other text, pause, sparse selection and
outputs were preserved. One incorrectly quoted prelaunch SSH synchronization
attempt failed before finding the lock/repository and made no change; corrected
quoting then fetched and synchronized the one row. The node still reports its
pre-existing Git GC bad-tree warning `9e40125ee3e24973b69754649226d18847b45862`;
no unrelated repair was attempted. Published-source snapshot creation and native
admission succeeded. No scientific retry or alternate operation was launched.

At the first observer checkpoint, the original native operation was still
running with consistent identities and zero probe errors (latest observation
05:05:27 UTC). App wake delivery failed with the known native-child error
`unloaded spawned sub-agents (code -32600)`; no delivery to Root is inferred.
The still-active DM read and consumed checkpoint event
`ebe3f0c9d7397378618fb27c`, then rearmed the same manifest as generation 2 for
1500 seconds. No worker, episode, policy fit or scientific budget was restarted.

During accepted collection Root supplied the independently owned six-program B
readback: 192/192 complete, with large true-BS consequences and some worlds that
never legally reveal BS. This is cross-question context, not this panel's
denominator or a reason to change its accepted inputs. The present gate requires
already-known legal BS and therefore **does not test initial BS discovery**.
The complete reading will report this fixed panel's own known-BS-at-decision,
eligible and executed-scout counts, separating lack of activation from active
programs with no service/J gain. Any trajectory-dependent exposure breakdown is
descriptive, not a causally identified pre-treatment subgroup. No gate, seed,
training horizon or evaluation panel changes; initial BS inference/acquisition is
a separate Root-owned question-selection decision.

The second checkpoint retained running/consistent identities and zero probe
errors (05:34:56 UTC). The DM consumed event `71732bee4ad65d0a6c81e531` and
rearmed the same manifest as generation 3, again without restarting work. The
known App queue rejection recurred; long deterministic waits and native return
remain the observation path, not an inferred delivery.

## 2026-09-28 - B01 complete: limited activation and no established learned increment

The original operation exited 0 at 05:41:06 UTC. Generation 3 observed READY at
05:42:01 with consistent identities, absent runner/supervisor and a valid native
exit witness. The DM consumed event `0fe49ad60a20bed9f2457a79`, advanced to
generation 4 with no live job, and stopped observation. The native child remained
active through collection; the known rejected App wake was not treated as a
delivery or an invitation to relaunch. No worker or scientific request restarted.

All declared work is complete: **one fit, 160 H3000 training worlds / 480000
native steps / 16000 macro decisions / 40 rollouts / 1600 optimizer steps**,
plus **80 H3000 evaluation worlds / 240000 native steps**, total **720000**.
There are no missing, failed, unstarted or partial scientific jobs. Each native
episode ends only at step 3000 with the original truncation flag. All stored
macro rewards match the true native sums, requested actions are preserved in
PPO storage, and all learning ends are finite terminals without TimeLimit
bootstrap. The last auto-reset exposed no extra world.

The post-run, read-only [integrity reader](../../../../experiments/candidates/uav_active_sensing/inspect_result.py)
verified all **340 manifest-listed files** by size and SHA256, all 240 native
traces and their native J/metric/battery/reserve aggregates, exact seed schedules,
macro clocks and fallback counts, and all rollout/update audits. This adds no
simulator transition, policy call or learner update. The separate engineering
Reviewer independently checked the canonical traces, macro reward slices,
rollout episode identities/aggregates and eligibility/fallback mappings; it
returned **no material finding** for reader digest `761768f5...f61112`.
"Exact H path" below means equality of the six recorded arrays own_xyz,
target_xy, mode, reward, metrics and ends, not equality of every hidden state.

Primary compact evidence is the [summary](../../../../runs/uav_active_sensing/b01_native_j_a01/summary.json),
[all worlds](../../../../runs/uav_active_sensing/b01_native_j_a01/perworld.json),
[frozen config](../../../../runs/uav_active_sensing/b01_native_j_a01/config.json),
[training](../../../../runs/uav_active_sensing/b01_native_j_a01/training.json),
[reading](../../../../runs/uav_active_sensing/b01_native_j_a01/reading.json),
[manifest](../../../../runs/uav_active_sensing/b01_native_j_a01/manifest.json),
[native exit](../../../../runs/uav_active_sensing/b01_native_j_a01/process-exit.json) and
[terminal status](../../../../runs/uav_active_sensing/b01_native_j_a01/terminal-status.json).
Frozen input SHA remains `38b7f132af8e26b851826f2e3db90a5fb5fb1a06`.
Manifest SHA256 is
`1b23004235f12f44313201f25d13ddf1dbe00a9c89bba11dadd5531f2fa2d414`;
listed artifacts total **123412058 bytes**. Every evaluation world is now exposed
development evidence; no holdout or independent learning replication is implied.

### Complete native outcomes and adverse worlds

All figures below are equally weighted over the same 16 initial evaluation
worlds. Return cost is native cost per step (raw and capped coincide in this
panel); battery is the mean of per-world episode minima, not a safety guarantee.
All 80 episodes have zero cutoff/depletion events and nonzero complete service.

| Arm | Mean J | QoS/step | Return cost/step | Mean minimum battery | Below-10% UAV-step share | Team travel m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H | 1587.410677 | .574956395 | .017824169 | .088266455 | .053645833 | 147176.096 |
| L0 | 1597.307093 | .575528737 | .016459640 | .088953641 | .049419271 | 150284.784 |
| L1 | 1587.520643 | .576140511 | .018396481 | .087503609 | .057776042 | 148985.398 |
| P | 1584.600858 | .581478318 | .021550769 | .086525535 | .063565104 | 148219.765 |
| A | 1616.785128 | .583861650 | .017378196 | .087873697 | .054278646 | 146891.286 |

Intervals are the predeclared nominal paired t95 over 16 world differences,
conditional on this single trained policy instance, without multiplicity
adjustment. They are not training-seed intervals, equivalence tests or a
confirmation rule. Ten exact-zero worlds remain in each comparison.

| Contrast | Delta J [t95] | J + / - / = | Delta QoS [t95] | QoS + / - / = |
| --- | --- | --- | --- | --- |
| L1-L0 | -9.786449 [-34.249434, 14.676535] | 2 / 4 / 10 | .000611774 [-.010125957, .011349504] | 3 / 3 / 10 |
| L1-A | -29.264485 [-63.432953, 4.903984] | 1 / 5 / 10 | -.007721139 [-.017412734, .001970456] | 1 / 5 / 10 |
| L1-H | .109966 [-26.258341, 26.478274] | 3 / 3 / 10 | .001184116 [-.011523010, .013891242] | 3 / 3 / 10 |
| L1-P | 2.919785 [-37.459051, 43.298622] | 3 / 3 / 10 | -.005337807 [-.017374637, .006699024] | 2 / 4 / 10 |
| A-H | 29.374451 [-.786291, 59.535193] | 5 / 1 / 10 | .008905255 [-.001837613, .019648123] | 4 / 2 / 10 |
| P-H | -2.809819 [-65.264048, 59.644410] | 3 / 3 / 10 | .006521923 [-.010653069, .023696914] | 4 / 2 / 10 |
| A-P | 32.184270 [-30.623412, 94.991952] | 3 / 3 / 10 | .002383332 [-.009916511, .014683175] | 3 / 3 / 10 |

Every nonzero-world contrast is retained, rather than displaying only favorable
worlds. The other ten world IDs are listed in the activation section and all
seven differences below are exactly zero there.

Native J differences:

| World | L1-L0 | L1-A | L1-H | L1-P | A-H | P-H | A-P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 28133003 | 64.461 | -52.697 | 12.767 | 24.272 | 65.464 | -11.504 | 76.969 |
| 28133005 | -73.606 | -118.024 | -78.697 | 112.643 | 39.328 | -191.340 | 230.668 |
| 28133006 | 8.484 | -35.535 | 147.753 | -149.946 | 183.289 | 297.699 | -114.411 |
| 28133008 | -2.529 | -119.069 | -32.620 | -125.456 | 86.449 | 92.836 | -6.387 |
| 28133013 | -0.112 | 57.038 | 32.642 | -1.256 | -24.396 | 33.898 | -58.294 |
| 28133015 | -153.281 | -199.944 | -80.086 | 186.459 | 119.858 | -266.545 | 386.403 |

QoS/step differences:

| World | L1-L0 | L1-A | L1-H | L1-P | A-H | P-H | A-P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 28133003 | 0.066515 | -0.001988 | 0.049302 | 0.018710 | 0.051290 | 0.030592 | 0.020698 |
| 28133005 | -0.024599 | -0.039656 | -0.027340 | 0.035756 | 0.012316 | -0.063097 | 0.075412 |
| 28133006 | 0.002303 | -0.011856 | 0.049548 | -0.051920 | 0.061404 | 0.101468 | -0.040064 |
| 28133008 | -0.002037 | -0.039046 | -0.011562 | -0.041176 | 0.027483 | 0.029613 | -0.002130 |
| 28133013 | 0.000134 | 0.017624 | 0.010686 | -0.001069 | -0.006938 | 0.011755 | -0.018693 |
| 28133015 | -0.032528 | -0.048616 | -0.051687 | -0.045706 | -0.003071 | -0.005981 | 0.002910 |

The average L1-L0 QoS change is near zero while return cost increases .001936841
and reserve exposure increases .008356771. L1-H increases return cost .000572312
and travel 1809.302 m on average; L1-A travels 2094.112 m farther and has higher
cost .001018285. These are complete realized differences, not additive causal
cost estimates for a single sensing decision.

Risk remains concrete even where J improves. In world 28133003, L1-H improves
QoS .049302 but raises cost .022523, lowers minimum battery .101187 -> .084140
and introduces .097958 below-reserve exposure. A-H in that world improves
QoS/J while also raising cost .014734 and lowering battery to .087727.
World 28133015 has L1-L0 J -153.281, QoS -.032528 and cost +.009283.
Its P-H J is -266.545 and P cost .069139, battery .071310 and reserve share
.182958, the panel's maximum. A-H there raises J 119.858 but lowers QoS .003071;
reduced return penalty contributes to J and does not restore the service loss.
A's world 28133013 loses both J and QoS while raising cost.

The common minimum-battery world is **28133011**, .063304986 for every arm:
cost .065457465, reserve share .1585, QoS .360759438 and J 659.154793. It never
activates scouting, so this is an inherited ordinary-control tail, not an active
sensing treatment effect. Zero cutoff/depletion does not establish safety,
sustainable cycling or absence of these low-reserve consequences.

### Opportunity, exposure and actual learned behavior

In this panel **10/16 worlds have no known legal BS at any macro decision through
t2970**: 28133001, 002, 004, 007, 009, 010, 011, 012, 014 and 016 (each suffix
completes the same 28133 prefix). They have zero eligible/scout plans in every
arm and each intervening arm's six recorded native arrays equal H exactly.
This is a decision-time statement, not a primitive-by-primitive proof of no BS
sighting in the final 29 steps. There is no known-BS-but-never-eligible world.
The six active worlds are 28133003/005/006/008/013/015. The common first known-BS
plan is t0 in 003/005/006/015, t30 in 013 and t1530 in 008; first eligibility is
t90 except t150 in 015 and t1530 in 008. They are descriptive trajectory groups,
not a new randomized estimand, and were not selected for extra evaluation.

Total eligible plans are H 125, L0 118, L1 93, P 68 and A 68 out of 1600 per
arm. H always selects service. L0 and L1 request scouting at **all 1600 decisions**;
ineligible requests fall back to H, so their executed scout totals are 118/93.
Neither saved deterministic learned arm requests ordinary service at any eligible
decision. P/A execute 68 scouts each and explicitly request H when ineligible.
Changing later eligibility counts is a consequence of changed paths, not an
independent reduction in exploration cost.

All arms in all 16 worlds eventually discover all 30 users, so final unique-user
count is saturated. H/A mean current visibility is 20.920208/21.283708 users;
A-H is +.363500 [.039758, .687242] and is positive in every active world.
P-H is +.267542 [.018040, .517044], also six positive active worlds. L1-H is
-.000041667 [-.271756, .271672]. A reaches all users earlier than H in
003/005/006/015, ties in 008/013; this is still not a mediation estimate.
Earlier or more sustained visibility can coexist with loss, e.g. A's active
013 loses service/J, and 015 gains J while losing service.

Training has **1129 eligible macros / 16000 (7.05625%)**, in 54/160 worlds.
Of those eligible choices, only **7 requested service** and 1122 requested a
scout target. This is observed exposure under the flat 257-action categorical
parameterization, not a claim that 480k native steps were missing. It is not
a balanced empirical comparison of serving versus probing. Ineligible choices
still legitimately contribute to the declared PPO objective through the common
fallback environment; they were not retrospectively masked.

The actor changed (L2 .344535, max absolute .011171); the critic changed
(L2 13.622107). All 1600 optimizer steps occurred and initial/endpoint checkpoint
hashes differ. Approximate KL at first/last update is .00007747/.00011463,
clip fraction zero at both, and entropy magnitude 5.549060 -> 5.545068, close
to log(257)=5.549076. Thus the training distribution remained close to high
entropy at those audits; a deterministic argmax concentration is not evidence
of a sharply concentrated stochastic policy. L1's 93 executed actions use
only action223 (84 times) and action138 (9 times), public xy (6750,7250) and
(4250,4750). There is no established learned "when to sense" behavior in this
fixed deployment mode; the changed target selection did not establish the
primary complete-value increment.

Mean training J over successive ten-rollout blocks is 1803.671, 1703.150,
1864.453 and 1652.975 (QoS .645220, .623360, .666488, .601956). These use
different worlds, not a matched learning-gain curve. Critic explained variance
-.000499 -> .212176 and value loss 128464.85 -> 108888.51 do not substitute for
the unfavorable/uncertain fixed endpoint comparisons.

### Total cost and interpretation context

Scientific runner wall time was **4370.938878 s = 72.848981 minutes =
1.214150 node-hours**. Training parent wall was 3071.582454 s; four training
workers used 11479.745580 summed CPU seconds and 12274.176649 summed wall seconds.
Evaluation workers used 5302.002193 summed CPU seconds and 5137.962307 summed
wall seconds. Parent CPU across the batch was 28.294755 s, including its training
portion, so measured parent-plus-workers CPU totals 16810.042528 s (4.669456 h).
These are scopes of measurements, not simultaneous utilization or method-speed
claims. Parent peak RSS was 673064 KiB; maximum individual training-worker peak
was 516748 KiB. Native J does not price learner or planner computation.
Implementation, the previously recorded 1710 nonpanel native verification steps
and three one-update wiring checks, independent reviews, collection and
publication cost additional time not fully metered; they are not zero cost.

Before choosing the result disposition, the DM refreshed published RESEARCH
topics 2 and 8 and read the adjacent B01 information-value complete result and
independent diagnosis. The same canonical ordinary control makes BS knowledge
an actionable input, but its 17/32 never-seen count is not ours. Our deliberate
known-BS gate excludes initial BS acquisition, so the present lack of activation
does not refute that remaining opportunity. The original central-local gap
remains a package difference, not a recovered information percentage. Earlier
finite-model and spatial-generalization negatives still constrain only their
particular programs; no old route is reopened by this result.

### Independent scientific reading and DM disposition

The registered ResearchCritic `interpret_result` received no inherited DM/Root
conversation. The assignment, index navigation and frozen notebook disclosed
the selected approach, so this was independent-context rather than blinded
review. It reconstructed results before reading the prior review body,
independently checked all 80 evaluation NPZ hashes, lengths, native J sums,
reserve exposures and plan records, and read all 16000 training macros, 40
rollout/update records and 160 training episode summaries. It did not repeat
the complete engineering audit. Its J table used J/step; all J differences in
the preceding DM tables are totals over exactly 3000 steps.

The review returned **MATERIAL_DISSENT: no** and recommended stopping the
unchanged 257-action PPO recipe, keeping H as the ordinary anchor and A as a
conditional exploratory asset, without automatic replication or confirmation.
It stressed that 548/1600 known-BS decisions per arm and only six affected
worlds combine real intervention with substantial nonactivation. Sparse
service exposure and near-maximal entropy make ordinary finite exploration
and optimization difficulty the strongest simple explanation. Large value
losses under global gradient clipping are another plausible contributor;
there are no gradient measurements identifying that as the cause. Neither
the decreased eligible count nor concentrated deterministic argmax choices
demonstrate learned restraint or a concentrated sampling policy.

The critic also identified training outcomes that must not be hidden behind
the evaluation panel's lack of zero-service worlds. DM verification of all
160 training episode summaries confirms zero service in **28132037** (J
-285.869855, minimum battery .070677614, reserve share .125791667) and
**28132124** (J -638.162655, minimum battery .053775653, reserve .200333333).
Training world **28132042** has the lowest battery .039612527 and largest
reserve exposure .263625, QoS .384949270, J 136.930116 and mean return cost
.171133477. All training episodes also have zero cutoff/depletion events.
These are adverse training exposures, not extra endpoint evaluation units.

The review distinguishes four judgments. There is some ordinary sensing
opportunity on these trajectories, but ordinary H already discovers all 30
users by t895 in every world. The legal action library includes service and
scouting; it does not establish feature sufficiency. The adverse finite
learning recipe does not identify a general inability to learn information
value. The complete L1 package has earned no deployment preference; A's
positive mean remains heterogeneous, risk-bearing and uncertain. Changes in
deployment, backhaul and energy prevent interpreting the differences as a
pure information mediator. The prior choice to test direct native learning
without a positive rule screen was reasonable and remains part of the record.

Its strongest unselected repair is a balanced service/scout parameterization:
predict much more eligible service experience, then improved complete native
utility if that scarcity mattered. That would be a new learning-package
experiment, not proof of this failure's cause. The review does not prefer
another fit-plus-panel cost to the already identified initial-BS question.
It declines an unchanged extra seed, a larger evaluation panel bought only to
narrow these intervals, and automatic A confirmation. It instead recommends
Root's existing ordinary legal station-prior BS estimate versus H_BS proposal:
32 fresh common worlds / 64 H3000 episodes / 192k native transitions / 0 fits,
approximately 20-25 node minutes by the other direction's measured rate plus
engineering/readback. Jitter, clipping and separation prevent exact BS
reconstruction. This proposal is outside the present known-BS sensing study;
no arm, seed, estimator implementation or launch has been added here.

**DM disposition: adopt the diagnosis and stop unchanged-selector investment.**
The primary predicted complete learning increment is not established: L1-L0
and L1-A J means are negative, while QoS/J uncertainty and losses remain.
Ordinary A demonstrates extra visibility and some useful realized trajectories,
not an established population advantage, dominance over P or pure information
mechanism. Keep its controller as a conditional asset and retain every loss.
The parent question remains open, but the next purchase should not be an
unreasoned seed, longer fit or expanding gate on this exposed batch. Direction
state becomes **reserve**, with no active operation or selected successor.
Return initial-BS inference/acquisition as the concrete next-question
recommendation to Root, which owns cross-question allocation; no owner/Root
approval is pending for publication or collection.

### Durable evidence and retirement boundary

After both independent helpers completed their reads, a fresh same-handle
status check at 06:19:19 UTC again confirmed exit 0, absent runner/supervisor
and consistent identities. The unique bulk evidence was moved, not copied,
from the sparse canonical checkout to:

`hmasd-wsl-node:/home/wu/hmasd-artifacts/uav_active_sensing/b01_native_j_a01/`

That is now the canonical location for all 240 NPZ traces, all training macro
records and the actual initial/endpoint checkpoints. The original manifest
and compact metadata accompany them; original native claim/status/summary
files remain at the launch output path for recovery and duplicate prevention.
The unchanged read-only reader reverified all 340 listed sizes/hashes and
reconstructed the identical scientific reading at the durable location.
Allocated durable directory size is 124407808 bytes; listed content size is
123412058 bytes. Relocation itself is not claimed as disk reclamation.

Small source, regression tests, integrity reader and compact original
per-world/rollout/update records are retained as the reproducible legal-sensing
and finite-native-J reference. No peer imports, active worker or scientific
helper consumes the disposable launch source. The maintained exact-target
collector initially refused protected `/proc/660/cwd`; its supported
`--sudo-process-scan` read-only preview then found the snapshot eligible.
Publish these results before applying exact source/scratch reclamation; do not
delete the durable raw evidence, checkpoints, native claim or status records.

Publication **27b21ea90b57c91bafdd907b3ec89e5349e0fb4f** contains the full
result, compact original readings, independent dispositions and own RESEARCH
standing/shared information topic. The subsequent supported exact-target GC
rechecked the accepted operation under its lock and removed
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/4d37977a05ce465389ad5b322bcdbedd`.
It was **799772672 allocated bytes** before removal and is now absent from
both the filesystem and Git worktree registration. The native claim remains.
The durable evidence directory remains unchanged at 124407808 allocated bytes.

Also deleted the completed observer request directory
`temp/directions/uav_active_sensing/` (8192 allocated bytes),
`experiments/candidates/uav_active_sensing/__pycache__/` (73728), and
`tests/experiments/candidates/uav_active_sensing/__pycache__/` (77824), after
confirming the observer and both reviewers were done. All three exact targets
are absent. Total **measured cleanup-target allocation decreased 799932416
bytes** across the source snapshot and these local targets. This is not a
claim about concurrent whole-filesystem free space; output relocation itself
was not counted as reclaimed space. The initial `rm -rf` command was rejected
before effects by the shell tool's force-removal restriction; ordinary exact
`rm -r` succeeded, without force or bypass. No deletion blocker remains.
Retained bulk is the one necessary evidence copy; compact status/summary
copies at the original output path preserve native recovery. No full-tree
backup, tarball, extra source copy, peer edit or new result operation was made.
