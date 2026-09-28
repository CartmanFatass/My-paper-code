# UAV whole-fleet service and energy coordination

## 2026-09-28 UTC - first question-selection return

This is the new native DM's bounded reasoning/design assignment from Root
`01a0e560-4333-7b03-8ff3-759a4add1d9a`, child `/root/dm_energy_coordination`.
The current published control is `9fb1cf301cf41beb9aa6c37ced1a1d46b4bc06a3`:
owner pause lifted, direction exploring, lead `Codex DM (native child)`.
No old DM, accepted operation or experiment is inherited. This entry contains
**0 started fits, 0 optimizer updates, 0 new native episodes/transitions, and
0 executed model/simulation steps**. Reading/design time is real and unmeasured.
There is no result handle. Root's already assigned independent ResearchCritic
will cover this selection; no duplicate critic or ceremonial Pro request was made.

### Question and changed premise

Can coordinated choices of the entire fleet's service locations, return,
charging and redeployment improve complete native service/risk value beyond
competent independent planning? The intended first contribution is empirical
task understanding and possibly a useful ordinary control package. It is not
yet a learning-method claim or a claim that coordination is absent from H1.

The native task has meaningful coupling, but **charging is not a communication
blackout**. The better conjecture is that independently attractive trajectories
can jointly remove a useful relay geometry, duplicate service, or concentrate
future charging demand. Conditioning choices on the other newly selected plans
could avoid these conflicts. The strongest competing explanation is that good
ordinary spatial deployment plus local return feedback already absorbs most
useful structure; charging stations themselves can support service, and the
native battery-priority allocator already supplies useful balancing. More
coordination could add forecast error, travel and low-battery tails instead.

This uses current [RESEARCH topics 1, 3, 6 and 8](../../RESEARCH.md#研究背景与共享认识)
at the published revision above. Their concrete design consequences are: compare
complete native packages; give the ordinary comparator the same information,
goals and recharge choices; distinguish task opportunity from learning; retain
adverse worlds and price the nested search. No favorable headroom calculation,
toy pass or complete mechanism proof is required before a useful experiment.

### Native facts that constrain the explanation

All source passages below were read on main at `9fb1cf301`; these inspected files
have no diff from the earlier published `dbdc519bd` during this task. Function
names identify the passages. These are source facts, not new empirical results.

- [Energy environment](https://github.com/CartmanFatass/My-paper-code/blob/9fb1cf301cf41beb9aa6c37ced1a1d46b4bc06a3/envs/pettingzoo/relay/energy_aware.py),
  `_communication_unavailable_mask`, `_is_uav_unavailable`: availability is lost
  through failure or battery at/below service cutoff. Charging, returning and a
  dock request do not themselves disable radio service. An energy mode is not a
  removed roster member or an absent service asset.
- In the same file, `_calculate_end_to_end_user_rates` divides an UAV's access
  bandwidth among its connected users, scales its rates by its backhaul
  bottleneck, and takes the maximum delivered rate over UAVs for each user.
  Redundant coverage need not add service; a relay can enable several other
  UAVs. The implementation does not debit a shared edge's residual capacity for
  every downstream flow here. Do not import an unimplemented packet queue or
  flow-conservation bottleneck into the explanation.
- `_charging_station_anchor_points` places the two station priors near a
  BS/service relay point and the initial service center, with randomized jitter.
  Station proximity is therefore also a deployment prior. Station occupancy is
  not pure lost-service time.
- `_apply_energy_dynamics`, `_charging_candidates_by_station` and
  `_select_charging_uavs` consume physical energy before input; eligibility
  requires a dock request, actual speed at most 1 m/s and distance at most 20 m.
  With production capacities `(1, 1)`, selection sorts by battery, then negative
  wait age, then index on every tick. There is no switching setup loss, native
  reservation action, selectable slot owner or first-come-first-served queue.
- `_prepare_energy_actions` accepts continuous xyz movement and a dock bit;
  requested docking selects the **nearest** station at that tick. Inside 160 m,
  docking uses its own horizontal/vertical caps. A policy cannot set a station
  index by writing an action coordinate. `_apply_backhaul_action_guard` allows
  a station-directed requested move to bypass the ordinary topology guard;
  ordinary service moves can still be blocked. Native guard, limp-home and
  depletion therefore remain part of every actual policy's consequences.
- `_raw_return_energy_margins` uses current three-dimensional distance to the
  nearest station, low-speed horizontal power and a 0.10 reserve. The reward
  uses the team's **worst** negative margin, scaled and capped, not a sum of
  independent battery penalties. Geometry, station choice through movement,
  and energy are coupled even before a physical cutoff.
- [Production feedback](https://github.com/CartmanFatass/My-paper-code/blob/9fb1cf301cf41beb9aa6c37ced1a1d46b4bc06a3/experiments/candidates/energy_relay_benchmark/b01/feedback.py)
  enters at decoded margin <=0 and leaves at >=0.05. It can leave before charging
  if geometry raises the margin. More entries, exits or input episodes are not
  necessarily more completed useful energy cycles.
- [H1](https://github.com/CartmanFatass/My-paper-code/blob/9fb1cf301cf41beb9aa6c37ced1a1d46b4bc06a3/experiments/candidates/energy_relay_benchmark/b01/heuristic.py)
  already pools information, creates service/relay targets, and uses Hungarian
  assignment with 300 m continuation hysteresis. `H_local` is also a pooled
  planner, not eight independent local actors. Its central variant gets current
  full user/BS xy; the [observation decoder](https://github.com/CartmanFatass/My-paper-code/blob/9fb1cf301cf41beb9aa6c37ced1a1d46b4bc06a3/experiments/candidates/energy_relay_benchmark/b01/observation.py)
  supplies all UAV energy/geometry records and station records even outside the
  local user-observation radius. Information and planning must not be conflated.

The simple mathematical reason is nonseparability: team delivered service is a
max over members after access/backhaul restrictions, risk is a max over deficits,
and at most one eligible member per station receives input. In general, changing
two member plans together does not equal the sum of their separate changes.
This locates an opportunity; it neither proves that the opportunity is large nor
that a particular finite planner will use it.

### Inherited evidence and what it rules out

| Original evidence | Retained reading and effect on this design |
| --- | --- |
| [Service B07](../uav_service_auxiliary/NOTES.md#2026-09-24--b07-complete-native-h3000-feedback-restores-energy-with-material-service-loss-worlds), input `47d56c9bc` | F restores physical energy and removes observed cutoff/depletion in those panels; 78/80 worlds have finite same-member recovery followed by team service. Individual service attribution is absent, 502 input-bearing intervals remain unfinished, and large service losses survive. Use real complete service/risk, not a recovery counter. |
| [B09](../uav_service_auxiliary/NOTES.md#2026-09-24--b09-complete-both-arms-learn-service-feedback-training-adds-no-mean-endpoint-gain), input `e5e53534c` | Both new arms learn service; A-N endpoint QoS/step is -0.027188074 and J -82.166591 in one matched pair. Feedback-aware training is not an established repair. No retuning or relabeling of that package is proposed. |
| [B10](../uav_service_auxiliary/NOTES.md#2026-09-25--b10-complete-continuity-improves-recovery-counts-but-worsens-j-and-waiting-risk), input `3be662f4a`; [B11](../uav_service_auxiliary/NOTES.md#2026-09-25--b11-complete-guarded-continuity-changes-recovery-but-adds-no-mean-complete-utility), input `529df1b9e` | More continuous input/recovery failed to add mean complete utility; B11 J -3.347054, QoS -0.000472718, longer waits and lower minima. Keep the native allocator. These do not refute service-aware trajectory coordination or prove O optimal. |
| [Availability B04/B05](../energy_relay_availability/NOTES.md#2026-09-27--complete-native-b05-reading), inputs `025350669` / `754d5d34d` | Ordinary movement timing has conditional usefulness. B05 QoS +0.01607076 and J +35.80811 coexist with world 28092823's J -260.94523 and 16.279% reserve exposure. The B04 planner falls back whenever any shield mode is active; it did not test coordinated cycle decisions. Retain an ordinary competence reference and all risk tails. |
| [Cooperative B02](../uav_cooperative_planning/NOTES.md#2026-09-27--complete-native-b02-reading), input `9f72afd22` | One active value-learning package loses QoS/J to P, selecting 4,575 holds in 4,582 windows. That behavior does not identify a long-horizon, credit, information or learning impossibility. Do not rescue it with another fit. |
| [Transit-handoff final disposition](../uav_transit_handoff/NOTES.md#final-design-disposition) | A residual-PPO plus ordinary rolling-search design was declined at 0 fits/0 result steps on value/cost. Temporary handoff remains untested. Its 20.736M proposed full model steps are neither an observed cost nor empirical negative evidence. |

Prior technical missing endpoints, including B08 and the newer ordinary SET
attempts, stay technically missing. They provide no negative ranking here.
The new question is not a renamed threshold, slot-continuity, value-hold or
handoff-residual retry.

### One concrete comparison worth considering

**Recommendation to the first selection review:** prefer a bounded ordinary
coordination comparison to another learner or local recovery repair. The
primary comparison is sequential joint-plan conditioning **C** versus a strong
independent rollout controller **I**. Include **H**, unchanged H_central+F at a
30-step clock, as a cheap secondary competence reference in the same complete
worlds. C-I is the selected question; H prevents an apparent gain over a newly
weak comparator from being promoted as useful control. This is a design for
review, not a launch declaration or authorization to implement in this turn.

**Common task and interface.** Native S7-S2, eight UAVs, 30 users, H3000, original
reward, termination, mobility, radio, charging allocator and backhaul guard.
Production F runs every primitive step in all arms. I and C may submit early
return, continue charging or redeploy once F permits service proposals; F is a
common emergency override, not the normal cycle scheduler. They choose all
members' goals every 30 real steps from reset onward. There is no fixed-H1
assignment, single-donor limit, pre-entry exclusion or one-event-only action.

Both primary arms receive identical current central user/BS xy at that clock,
the pooled current legal observations, and their own past goals/modes. Between
clocks they receive the legal fields needed for goal tracking and F, with no new
central user query. No raw simulator state, actual future user motion, hidden
association history, RNG or future failure is supplied. This explicitly tests
central-snapshot control; it does not answer the other DM's lawful-information
question or establish decentralized deployability. There is no actor/critic or
training asymmetry: both arms have zero learned parameters and zero fits.

**Broad common goal library.** At each clock form six current user centroids,
the two ordinary H1 relay points, the six BS-to-centroid midpoints, and the two
charging-station positions: at most 16 shared sites. Each member can also keep
its incumbent goal or hold its current location, giving at most 18 candidates.
Ordinary service/relay sites use 100 m; station sites use station height. No
quota assigns six members to service or two to relay, and no Hungarian mapping
is frozen across candidates. All available members can choose any site.
Coincident candidates use a deterministic first-occurrence rule.

The primitive executor follows capped movement toward the chosen site. A station
goal requests docking only when that goal's station is the currently nearest
valid station; otherwise it travels with dock bit zero and remains subject to
the ordinary guard. The native nearest-station rule and F can still defeat this
intention. A held station goal continues requesting input; a later clock may
select service again. There is no reserved slot, forced charging continuity,
teleportation, guaranteed arrival, special service while charging, or changed
station allocator. Return/charge/redeployment duration emerges from this common
closed loop. This finite goal catalog is a restriction, not the full continuous
policy class or an upper bound on attainable service.

**Shared approximate forecast.** Rank a complete team goal vector by a 300-step
nominal forecast, truncated at the true remaining horizon. Users stay at their
current observed positions. Reconstruct physical state from allowed fields;
never deepcopy hidden live state. Propagate nominal motion, F, native power,
docking eligibility and native battery-priority input at one-second resolution.
At six evenly spaced points, recompute native radio/routing/service on the
predicted geometry with fresh association, then quadrature-weight QoS over the
forecast. Subtract the integrated native capped return penalty and once-only
cutoff/depletion event terms. The scoring surrogate omits PBRS; actual J retains
the original PBRS and is read separately. No learned terminal value is added.

This deliberately does not run the whole native environment at every model
tick. It omits evolving association history and predictive backhaul-guard
interventions, and freezes users; those are material approximations shared by I
and C, not claims of exact model access. Actual guard/motion discrepancies must
be retained. Charging members stay radio-available in the model above cutoff.
A 300-step forecast may end before a recovery cycle finishes; the **evaluation**
is a complete H3000 policy comparison, not a guarantee that every forecast sees
a completed cycle. Extending the horizon after scores is not part of this study.

**Competent independent arm I.** First score the carried-forward goal vector
and a fresh ordinary H1+F vector; use the better as a common-form incumbent b.
For every UAV independently, score all its candidate replacements while other
members keep b. Each UAV therefore prices whole predicted team service, native
station competition and worst-member risk, not just distance or its own energy.
Assemble the independently chosen goals and score that complete vector once.
Execute the best-scoring vector among b, this simultaneous combination, and the
best single-member replacement already scored. This joint veto/fallback avoids
knowingly deploying a bad simultaneous combination. It is a strong ordinary
independent-improvement planner with a central safeguard, not strictly local
information control or an entirely uncoordinated straw comparator.

**Coordinated arm C.** Start with the same incumbent construction. Make one
agent-by-agent sweep through the same candidate library, incorporating each
accepted goal into the vector used to score the next member. Use a cyclic order
starting at `(clock_index mod 8)` and incumbent-first strict float64 comparisons
for ties. No repeated sweeps, subset enumeration or horizon search is hidden.
Earlier members' new intentions are the only added planning dependency. Both
arms have broad cycle freedom; this is not a small learned correction to I.

One C sweep is ordinary rollout/coordinate planning, not a novel algorithm.
[Bertsekas, arXiv:1910.00120v3](https://arxiv.org/pdf/1910.00120), section 2,
equation (2.1), constructs component decisions using previously improved
components and remaining base-policy components; section 1.2 explains the
linear rather than Cartesian-product action-search count. This is the useful
method bridge. Its exact cost-to-go improvement statement does not certify our
partial reconstructed state, sparse service forecast or complete native gain.
The scientific object here is the task consequence of the two declared packages.

### Predictions and what the outcomes change

The conjecture predicts that C changes meaningful joint trajectories, with less
duplicated service or damaging simultaneous departures/charging concentration,
and improves complete QoS and native J over I. Those process descriptions are
not alternative success endpoints. I already has the same model, lookahead,
energy information, action library and global veto, so a gain cannot simply be
called extra sensing or a newly permitted return action. Serial computation,
cyclic order and changed visited states still belong to C's package.

Read per-world H3000 cumulative/mean QoS, raw native J and its components,
return-cost sum, minimum battery, fraction at/below 10% reserve, cutoff/depletion,
long service gaps, energy consumed/input, and every signed loss. Use planned-
window service with the original termination accounting; report actual length.
Retain modes, requested/executed actions, chosen sites and guard interventions
to check whether the intended control happened. Fixed 0-1000/1000-2000/2000-3000
service/risk summaries can describe timing without selecting endogenous event
windows or attributing team service to one recharged member.

- C improves QoS/J over I and remains competitive with H, without important
  observed risk damage: retain conditional ordinary coordination usefulness;
  consider replication only if that use merits it. No learning necessity follows.
- C improves over I but both are worse than H: a new-planner limitation remains;
  do not promote a weak-baseline victory as useful energy coordination.
- Predicted scores/conflict counters improve but complete QoS/J do not, or severe
  reserve/service tails worsen: the proposed coupling-aware forecast package
  has not earned use. Do not automatically increase horizon, retune a threshold
  or buy a neural correction. Reconsider the question using the adverse result.
- Small or mixed differences: limited discrimination, not equivalence or proof
  that the native task lacks coordination opportunities. A positive difference
  mainly before actual recovery supports spatial planning, not an energy-cycle
  mechanism. The broader energy attribution remains unresolved.
- Missing/failed implementation or episodes: technical incompleteness, never a
  coordination-negative result or an automatic retry.

### Dominant prospective cost and investment boundary

The smallest proposed complete exploratory panel is **8 new paired initialized
worlds x I/C/H x H3000 = 24 episodes, at most 72,000 native team transitions**,
0 fits and 0 optimizer updates. World seeds and the exact execution contract
would be fixed prospectively after the selection review; none is executed or
reserved here. Eight worlds are for a rough fixed-policy use decision, not
confirmation, tail safety, equivalence or a learned-population estimate. No
additional panel or fit follows automatically.

There are at most 100 real planning clocks per world. At 18 candidates/member,
I has at most `2 + 8*18 + 1 = 147` complete-vector scores per clock; C at most
`2 + 8*18 = 146`. Best-single scores are reused. This gives at most **234,400
nominal team plans**, **70,320,000 reduced one-second physical team updates**
(562,560,000 member updates), and **1,406,400 native radio/routing/service
snapshot calls**, plus H's ordinary k-means/assignment. Horizon truncation,
unavailable members and duplicate candidates can reduce these bounds; they
must not be advertised as measured savings. Each snapshot contains its own
radio, association and route computation; it is not one scalar FLOP.

For scale, B04 used 85,462 service snapshots in P's 32-world panel, with total
two-arm worker wall 11,821 s; B02's H/P panels measured about 4,241/5,622 worker
seconds with 86,602 P snapshots. Taking the latter *whole-panel difference*
over snapshots gives roughly 0.016 worker-second/snapshot, hence about **6.2
worker-hours for 1.406M snapshots alone**. This is an illustrative extrapolation,
not an isolated kernel benchmark or runtime promise: trajectories, model object
construction, machines and concurrency differ. Native evaluation, 70.3M physical
updates, data recording, engineering, checks/review and readback are additional.
The future physical kernel's runtime/RSS are **unknown**, not zero. There is no
new profiling rollout or mandatory chain of headroom diagnostics in this return.

The full model rollout alternative would execute radio/routing at each of the
70.3M model steps and is not the proposed study. An exhaustive 18^8 joint-goal
search is also not proposed. A new learner adds training, exposure and variance
without first resolving this ordinary-use comparison; it is not selected merely
because the previous learned package failed. Conversely, if the physical
forecast cannot be implemented compactly and honestly within the known cost
scale, declining this package is preferable to quietly expanding the study.

My first-return recommendation is **retain this single ordinary comparison as
the concrete option for independent selection review**, with the approximation
and several-worker-hour cost central to that decision. It is more consequential
than changing a shield threshold: every member can reallocate service and energy
goals over the entire episode. It is not yet evidence that the comparison merits
an expensive implementation or that the task needs a new MARL architecture.
Root may choose implementation, a material reframe or idle after integrating the
already assigned scientific review. This is the assigned substantive boundary,
not a per-run approval requirement.

### Ownership, shared dependencies and current state

This direction owns only its five assigned direction directories. Any eventual
implementation would use those paths and read existing shared environment,
observation, feedback and ordinary-controller helpers; no peer notebook or
learner modification is required by this design. The reconstructed forecast
and controller would be new direction code requiring focused numerical/
information review if selected, not an unsolicited shared environment change.

Claude's active estimand is a learned relational goal decoder for deployment
before first shield entry. This option tests ordinary joint-plan conditioning
against independent full-cycle planning; it uses no Claude learner, decoder
training or pre-entry ablation. Early deployment can change in both arms because
it is part of the whole service-energy policy. That shared phase alone is not
duplication. Root's committed scope message is the coordination route; this DM
sends no App or Claude message and makes no claim the peer has read/agreed.

Current state is **design return, no active result operation**. Independent
selection review and Root's cross-question choice are the actual next tasks.
No implementation, diagnostic, training, simulation, evaluation or repair batch
was started. There are no generated scratch/bulk targets to retire and no disk
reclamation claim. No shared-background empirical claim changes on this reading
alone; the native semantic corrections and their design effect are recorded here.

### First-return cost correction - choose analytical itineraries

Root asked whether a simpler complete ordinary policy could retain the decisive
coupling without purchasing the 300-step physical branch simulation. It can.
**I decline implementation of the one-second branch model described above and
recommend the following coarser I/C/H comparison instead.** This is one revised
option, not two implementations, a preliminary headroom test, or a promise to
repair the detailed model later. The original alternative and its full cost
remain above as the reason for this choice. No result was observed between them.

Keep the task, common information, 18-candidate goal freedom, native primitive
executor/F, independent joint veto, sequential sweep and native endpoints.
For I/C use a **60-step real decision clock**, a **600-step analytical itinerary**,
and service/risk readings at nominal times **200, 400 and 600** (truncate and
partition the remaining horizon into three equal intervals near episode end).
H remains the established H_central+F at its 30-step clock, explicitly a
secondary complete competence reference, not a timing-matched causal control.

Each service/relay goal has one nominal service-return-recharge-redeployment
itinerary. Estimate capped outer flight and final docking times from geometry,
using their separate horizontal/vertical speeds and native power at those
nominal velocities. At the service goal estimate the dwell until the native
zero-margin return trigger from predicted arrival battery and hover power.
Estimate travel to its nearest station, input until the production release
margin, and travel back to the chosen goal. An already active F mode begins in
its corresponding return phase. A station goal goes to that station and stays
there in the forecast; the next real decision can choose redeployment freely.
A hold goal uses the same energy-cycle estimate at its current geometry.

This is a phase-duration estimate, not integration of the actual future F path:
triggering during travel, guard intervention, docking geometry and another
later cycle can differ. Include only **one predicted return visit per UAV**;
after its predicted redeployment, project continued goal service/energy to the
forecast end. Read subsequent margin deficits rather than silently granting a
second recharge. Real execution always replans from observations and can have
arbitrarily many native returns. This approximation limits the package reading;
it does not truncate actual H3000 collection or declare an unfinished cycle done.

Couple the itineraries at each station with an analytical fluid approximation to
the existing lowest-battery allocator: predicted arrivals join that station's
eligible group, the lowest stored-energy level receives the station's fixed
power, and tied lowest levels share it until the next level/arrival/release
event. Subtract hover consumption from **all** eligible members, including those
not receiving input. Production capacity remains one charging stream per site;
there is no extra energy, exclusive reservation, zero-cost wait or session setup
penalty. Continuous sharing approximates the discrete tick priority, and gives
no native allocation guarantee. This can be evaluated at phase and energy-level
crossing events instead of 600 one-second radio/physical transitions.

At each of the three sample times, put every predicted UAV at its corresponding
travel/service/charging position and battery; compute native joint radio/routing
and delivered QoS with fresh association. A charging member remains in the radio
graph above cutoff. Rank by the three-interval quadrature of QoS minus native
capped worst-member return penalty, with predicted once-only cutoff/depletion
penalties; actual J still uses its unchanged native definition and PBRS.
No extra terminal battery value, charge bonus or service-blackout mask is added.
This retains the decisive **joint geometry, duplicate service, worst-member risk
and finite shared charging power**. It gives up tick-accurate cycle forecasting,
not the ability to choose any fleet member's service/energy goal.

I and C get the same analytical model. Independent I still scores complete joint
itineraries for each unilateral change and rejects an adverse combined vector;
C conditions later choices on accepted earlier itineraries. The added C question
is therefore whether these new joint intentions have complete native usefulness,
not whether one side knows about stations or can plan a recharge. Both can change
early deployment. Purely better geometry, conservative energy estimates and
forecast exploitation remain distinct possible explanations for a C-I result.

The proposed **8 fresh worlds x 3 arms x H3000** still costs at most **72,000 native
transitions, 0 fits**. At most 50 real I/C clocks per world yield **117,200 nominal
team plans and 351,600 radio/routing/service snapshots**. Each analytical plan has
at most six phase boundaries per member (48 across the eight-member fleet), plus
the charging groups' energy-level crossing calculations; those station solves
and geometry/power evaluations are additional computation. There is no hidden
600-tick inner environment rollout. The earlier measured-panel scaling gives
about **1.6 worker-hours for service snapshots alone**, not the total job or a
runtime guarantee. Native evaluation, event calculations, model construction,
engineering/review/readback and storage are additional; their wall/RSS remain
unknown. The full model's 70.3M physical updates are **declined prospective work**,
not cost already spent or a later mandatory repair.

This choice buys one direct complete observation with the native couplings
present, at a substantially smaller explicit model-query count. If C only beats
I because both coarse planners are weak against H, or if model improvement fails
to survive real guard/energy dynamics, the programme learns that this ordinary
coordination package has not earned more investment. No large model refinement
or learned residual is thereby selected. A useful native C-I/H result would
justify considering replication or a new substantive learning question; it
would not establish a recharge mechanism or a novel rollout method. The eight
worlds cannot establish tail safety or equivalence. This **analytical I/C/H option**
is the single final recommendation at the assigned first-return boundary, pending
Root's integration with the existing independent scientific review. Exact phase
formulas and correctness checks belong in its L0 only if that work is selected.

### Root selection at this boundary

Root selected the final **analytical-itinerary I/C/H** option through native
parent communication after the common independent scientific review. The larger
one-second branch model remains declined. The selected substantive comparison is
**sequentially conditioned improvement versus simultaneous improvement with a
joint veto**, not coordination versus no coordination. H remains the ordinary
competence anchor. I's central safeguard is part of a competent comparator,
not something to remove to make the contrast cleaner.

The selected scope remains eight fresh worlds, three programs, H3000, at most
72,000 native steps, zero fits, shared I/C analytical model and 60-step clock,
with the stated 117,200-plan/351,600-snapshot bounds and additional actual costs
recorded. No extra sweep, learned model, larger forecast repair or added panel
is selected. Engineering review must examine the physical approximations,
information, numerical behavior and event solver if implemented.

Root reports that the completed independent review retains this question and
supports the event-based cost simplification. Its full record is being published
at `docs/research/archive/2026-09-28/RESEARCH-native-dm-question-review.md`; that
file was not yet present at this writing, so this is the native decision record,
not a claim that this DM has read the unpublished review text. Read that existing
review on the next substantive continuation; no second review is requested for
the unchanged question. Root explicitly kept the current task at **publish this
first return, then stop** and will assign implementation/execution through a
native follow-up. No implementation or result operation began here.

## 2026-09-28 - B01 implementation and fixed execution scope

Root's native follow-up now assigns the selected comparison end to end. I read
the complete independent review and disposition at `d8e53285b`,
`docs/research/archive/2026-09-28/RESEARCH-native-dm-question-review.md`. It retains
the I/C question, corrects the coordination-versus-independence interpretation,
and favors event integration; it does not validate the formulas below. No new
scientific review is needed for this unchanged selection. Current RESEARCH
assigns this active direction to `Codex DM (native child)`; owner pause is lifted.
The existing background and adverse evidence above remain the design constraints.

### B01 L0: analytical forecast, controller and evaluator

Implement only this direction's experiment/tests/records. Reuse the existing
S7-S2 configuration, legal decoders, ordinary H1, production F and deterministic
`energy_relay_benchmark.b01.evaluation.evaluate_world`. No shared simulator,
reward, physics, guard, charging rule, learner or peer source modification.
Independent engineering review must cover the event solver, information boundary,
numerics, search contract and admission-before-effects path before result launch.

Fixed batch `b01_analytical_coordination_a01`: worlds **31092801--31092808**, arms
**H, I, C**, each native H3000. These are new initialized world seeds, not a new
training lineage. The seed list is to be checked against published run contracts
before launch. At most 24 episodes / 72,000 team transitions; zero fits/updates.
No preliminary scientific rollout, exposed seed selection, extra horizon/sweep,
post-result panel extension or implicit retry is included. Correctness fixtures
use separate test seeds and short mocked/native contracts, not result endpoints.

The model API takes immutable float64 legal UAV positions/batteries, decoded
station positions, current effective production-F modes, chosen goal coordinates
and station IDs, and public fixed S2 constants. All current user/BS xy enter a
separate native snapshot scorer only at real 60-step planning clocks. Forecast
construction receives neither the live environment nor hidden RNG, association,
user motion/waypoints or pending event state. A fresh model environment built
from fixed config supplies native radio/demand/power functions; each snapshot
overwrites all geometric/battery inputs and resets association/cache state.

Nominal motion is a straight segment with duration
`max(horizontal_distance / horizontal_cap, abs(dz) / vertical_cap)`; its constant
velocity supplies native power and its position is linearly interpolated. This
differs from the executor's separate axis completion, an explicit approximation.
Station travel has an outer segment ending on the 160 m approach sphere and a
docking segment ending on the 20 m capture sphere, with caps (30,5) then (3,1)
m/s. Starting inside either sphere omits that segment. The final capture point,
not a teleport to station centre, is the charge and release position. Return
margin uses nearest 3-D station distance and native `P(3,0) / (3600*3*160)` per
metre, less reserve 0.1. A service-goal itinerary first flies to its goal, dwells
`max(0, arrival_Wh - required_return_Wh - 16) / hover_Wh_per_s`, returns to the
nearest station, charges to the production release margin .05 at the capture
point, then flies back to the chosen goal and dwells. Effective F at the planning
instant skips initial service travel/dwell and returns from the observed position.
Triggering during nominal outbound flight is not simulated. Motion stops at an
analytically predicted zero battery; a member depleted before arrival cannot
receive remote charge. Only one station visit is granted. Redeployment may again
accrue deficits but earns no second model recharge.

A station goal flies to its selected station and remains eligible there through
the forecast. If F is already active, its native nearest station takes precedence
and the model stays there until the next real replan; this avoids inventing a
second predicted visit. The real policy can change its station/deployment choice
at every subsequent clock. A service goal for an F-active member still redeploys
after release. Current hold is a normal service goal at observed xyz. The real
executor requests docking only when its selected station is presently nearest;
F and the native guard retain their actual authority every primitive step.

The station solver uses only arrival, lowest-energy equalization, release,
zero/full-energy and requested sample/end events. All eligible members consume
hover energy, even while waiting. The single 1000 W stream is split among tied
lowest stored-Wh members until the next event. Stored energy is clipped at zero
and capacity; record power input, consumption and floor clipping separately so
energy conservation is testable. Full permanent residents may absorb only their
hover loss when all contenders are full; no excess input is banked. Charging
members remain radio-available above cutoff. Fluid sharing is not the actual
discrete battery/wait/index tie rule and is not represented as an exact queue.
An event-iteration safety limit fails visibly rather than adding ticks or changing
policy. Physical trajectories are piecewise analytical, never 600 hidden steps.

Sample at three equal interval right endpoints over `min(600, remaining_steps)`.
Plan score is interval width times the sum of snapshot
`QoS - 2*min(1, max(0,-min_margin)/.05)`, minus predicted new cutoff/depletion
counts times 5/10. Detect crossings over segments/events, not only the three
samples. Once-only masks are reconstructed from the controller's own previously
observed legal batteries (including reset), never read from hidden reward state.
No PBRS or terminal-energy bonus enters this score; actual J/PBRS are unchanged.

Incumbent is the strictly better of carried goals and fresh ordinary H1+F goals,
with carried first on exact ties; reset carries H1 goals. The H1 reference keeps
its own ordinary assignment memory. All members retain the at-most-18 goal
options, including active F members' later deployment. I computes unilateral
improvements against the fixed incumbent, then scores the assembled plan once
and chooses best of incumbent, assembled and best single change. C uses one
cyclic-order sequential sweep; strict float64 improvements, incumbent-first ties.
No extra polish. Per-clock upper bounds remain I147 / C146 (including the two
incumbent scores), at most 117,200 plans / 351,600 snapshots for the full batch.
Cache identical whole-plan scores within a clock only; record both requested
scoring calls and actual model evaluations. H is unmodified H1 central @30+F.

Checks will cover closed-form travel/energy, capture geometry, fluid arrivals/
equalization/release/saturation/floor behavior and power conservation, cutoff
crossings, no extra model visit, strict ties/search conditioning and bounds,
legal snapshot isolation, native charge radio availability, deterministic seeded
pairing, step-clock/action tracing, and admission-before-result effects. The
runner will hash initial state, exogenous users and environment RNG to check
paired worlds, retain all failures without automatic retry, and write compact
per-world/paired endpoints plus hashed bulk traces. Report J and every native
reward component, QoS/service and fixed 1000-step bins, signed loss worlds,
return-risk, battery/reserve/cutoff/depletion, long service gaps, energy input/
consumption, guard/mode behavior, model discrepancy, and wall/CPU/RSS/query/event
cost. H comparisons are competence checks, not clock-matched causal estimates.

Full cost remains unknown before implementation: historical snapshot scaling
does not include the station solver, native steps, checks/review/readback or
storage. These are recorded actual work, not free because fit count is zero.
Material formula/implementation failure will be returned to Root as such, not
silently replaced with the declined primitive simulation or a new study.

### B01 engineering acceptance and launch choice

The bounded implementation is complete in `experiments/candidates/
uav_energy_coordination/` with focused tests in its matching test directory.
The two named Implementer helpers supplied only the pure itinerary solver and
the fixed runner/readout; I read and accepted their code and checks. The DM
implemented the controller, information-isolated native scorer and integration
checks. No shared environment/controller/evaluator file was edited.

The independent `hmasd-reviewer` `/root/dm_energy_coordination/engineering_review`
(fresh context, read-only) traced the native consumers, event solver, information
boundary, search and launch contract. It found two material evidence-accounting
defects before result execution: failed worlds' retained completed-clock costs
were omitted from batch totals, and later failures could lose already collected
native reward/metric/battery evidence. Both are repaired. Totals include known
failed-world work and label unknown in-progress work; a read-only observer keeps
native readings across planner exceptions, and returned evaluator arrays survive
downstream readout failures. Focused regressions cover both. The final reviewer
return reports **no material finding remains**; it does not certify forecast
accuracy or accept a scientific result.

Final full owned suite: **29 passed in 12.78 s** using the configured Linux CPU
interpreter with numeric threads 1. Independent checks included the earlier full
26-test suite (12.37 s), the cost regression (2.83 s), and both final preservation
regressions (3.59 s). The reviewer also checked 1,000 synthetic in-memory
analytical fleets for conservation/event progress; those are numerical checks,
not native episodes or study results. Our tests include 25 additional synthetic
fleets, closed-form travel/charging cases, and six-step native H/I/C episodes on
the separate correctness seed 70192. Those short integration checks were repeated
during development/review, not used for performance selection. Test suites also
construct/reset native fixtures and make snapshot calls, so these listed test
durations are not a zero-cost preparation claim. All 14 remaining warnings are
imported Matplotlib/Pyparsing deprecations. A temporary test-insertion NameError
was fixed before the final pass. No scientific fit or result-world rollout has
started; the 24-world batch and its bounds are unchanged.

Choose the owner-prioritized configured `wsl_4070` node, **2 workers, one numeric
thread each**, CPU native environment calculation. A read-only preparation check
found the correct host and 15,646,273,536 available bytes with no scientific
worker listed; native admission will take a fresh measurement, not reuse this
reading. Actual full runtime, simultaneous memory peak and raw storage remain
unknown; the runner records invocation/summed-worker wall, CPU, process RSS,
actual native transitions, plans/snapshots/events/phases and trace bytes/hashes.
Engineering/source-reading wall outside the listed checks is unmeasured, not
zero. The remote canonical checkout contains other directions' modified records
and an older main. Root explicitly directs insertion of only our already
published operative row under the remote writer lock, preserving its dirty
RESEARCH, outputs and sparse selection; no shared-tree merge/reset is needed.
The actual run uses the exact published source in the native launcher's immutable
snapshot. Publication and admission/acceptance are still separate facts.

### B01 accepted - same-operation collection pending

Published source **`e663b53c7ea3f52983365ed9c3ce044bc4ccf699`** was fetched on
`wsl_4070`. The remote operative row was inserted under its writer lock; the
existing information-value row and other dirty records were untouched. A patch
without trailing context required git's explicit no-trailing-context mode; its
rejected checks/applications changed nothing. The known remote zsh startup
diagnostics and Git auto-GC bad-tree warning were observed separately from the
successful fetch and admission. No shared-tree merge/reset or sparse change.

One configured-supervisor request `uec-b01-analytical-a01` invoked the native
launcher. Outer exit0 means submission completion only. Native admission accepted
**2026-09-28 03:37:23 UTC**, exact source above, seed31092801, workers2, threads1,
output `runs/uav_energy_coordination/b01_analytical_coordination_a01`. Fresh
`/proc/meminfo` measured **13,292,367,872 available bytes** against the
**4,294,967,296-byte floor**, with no failure reasons. Collected compact records:
[manifest](../../../../runs/uav_energy_coordination/b01_analytical_coordination_a01/launch-manifest.json),
[launch status](../../../../runs/uav_energy_coordination/b01_analytical_coordination_a01/launch-status.json),
[preflight](../../../../runs/uav_energy_coordination/b01_analytical_coordination_a01/admission-preflight.json).
Same-node operation reference:
`/home/wu/projects/HMASD/.git/hmasd-admission/70d1d7a565a02f1601e443ecac730b2fe43a04e72a7bf0fcb7cdf5bd82f267a9.json`.
Source snapshot: `.git/hmasd-launch-sources/7ea7d7d869b94ac5aba9f7ff532c6590`.
At **03:38:36 UTC** runner859694 and supervisor859693 were running with matching
Linux identities and consistent records; no exit witness existed. No scientific
endpoint has been read or accepted.

The next action is `tools/hmasd_wait.py` on that exact operation via
`temp/directions/uav_energy_coordination/b01-wait-request.json`. The actual owning
native-child Codex UUID is `01a0e5d9-7595-7010-b974-4dc802d1b7d8`; Root parent and
lead stay unchanged. Collection, interpretation and publication remain this DM's
task. A checkpoint rearms observation, never the worker; acceptance authorizes
no retry, replacement world, extension or additional study.

Local helpers/tests had finished before removing only the direction's experiment
`__pycache__`, `b01/__pycache__` and matching test `__pycache__`. The tool first
rejected `rm -rf`; targeted `.pyc` deletion and empty-directory removal succeeded.
Allocated usage across the two owned code/test trees fell from **393,216** to
**139,264 bytes**, net **253,952 bytes reclaimed**; all three targets are gone.
Required source/tests remain, as do the live native snapshot and unique output.
This preparation cleanup does not retire the active result operation.

## 2026-09-28 - B01 complete: useful ordinary package, no sequential increment

### Original operation and evidence

The original accepted operation ended **2026-09-28 04:11:46.357294 UTC**, exit0,
with a valid native exit witness, absent runner/supervisor and consistent records.
There was no restart, retry, replacement, extension or additional result rollout.
All **24/24 episodes reached the declared H3000 truncation**, exactly **72,000
native team transitions**, **0 fits / 0 optimizer updates**. No failed, missing,
unreconciled, cancelled or orphan result exists. Source remains
`e663b53c7ea3f52983365ed9c3ce044bc4ccf699`; acceptance was published in `762d288e5`.

Compact evidence: [config](../../../../runs/uav_energy_coordination/b01_analytical_coordination_a01/config.json),
[summary](../../../../runs/uav_energy_coordination/b01_analytical_coordination_a01/summary.json),
[all worlds](../../../../runs/uav_energy_coordination/b01_analytical_coordination_a01/perworld.json),
[content manifest](../../../../runs/uav_energy_coordination/b01_analytical_coordination_a01/manifest.json),
[exit witness](../../../../runs/uav_energy_coordination/b01_analytical_coordination_a01/process-exit.json),
[terminal status](../../../../runs/uav_energy_coordination/b01_analytical_coordination_a01/terminal-status.json).
The one required bulk copy remains at `wsl_4070`:
`/home/wu/projects/HMASD/runs/uav_energy_coordination/b01_analytical_coordination_a01/raw/`.
All **51 manifest-listed files** passed byte-count and SHA256 verification there;
the three collected compact scientific files match the same hashes locally.
The 48 raw files (24 NPZ plus 24 final progress records) total **56,078,638 bytes**;
manifest-listed raw plus compact scientific artifacts total **56,404,388 bytes**.
Manifest SHA256: `cd6f9cecc862f6921bd4dd99828d350ac1306997b6b58b4c5ba5da6d14b301bf`.
No bulk copy was added to Git or duplicated locally.

I read all 24 original NPZ files: native metrics/J, per-UAV energy totals,
terminal flags, planner costs/bounds and all 60-step decision clocks reconcile
with the compact rows. Complete raw user trajectories are equal within each of
the eight triples; recorded initial-state and RNG-stream hashes also agree 8/8.
The first post-hoc checker wrongly required bitwise reward equality: its maximum
observer/evaluator difference is **2.22e-16**, within the already frozen 1e-12
check. Battery decode differs by at most **2.9802241e-8**, within its frozen 3e-8
float32 bound. This was a readback-check error, not a failed native run, changed
input, tolerance revision or reason to repeat any world. All 14 native reward
metrics are exactly equal between the independent recorder and evaluator.

The observer was genuinely directed to child UUID
`01a0e5d9-7595-7010-b974-4dc802d1b7d8`, not Root. Its actual terminal wake
`847b1e9c-5a54-494f-a633-f4ef90560b06` failed with exit1 / `-32600`:
`direct app-server input is not allowed for unloaded spawned sub-agents`.
Thus registration did not establish automatic native-child continuation. After
Root's explicit continuation, this native turn waited and drained the same state;
READY event `baca624e003bae02bd9ea501` was consumed at generation2 and observation
was stopped. No target was rebound and no worker was relaunched. There is now no
active result producer, unread terminal event or collection dependency.

### Native outcomes and adverse worlds

All numbers below concern the fixed programs on eight initialized worlds, not
training replications, confirmation, or independent support from correlated
service/reward endpoints. Intervals are the declared descriptive paired t7
intervals. H remains the competence reference, not a timing-isolated control.

| Mean endpoint | H | I | C |
| --- | ---: | ---: | ---: |
| QoS/step | .769472137 | .814832456 | .800917362 |
| Native J | 2265.841194 | 2411.084022 | 2368.485910 |
| Delivered megabits | 69252.492290 | 73334.921067 | 72082.562592 |
| Return-cost sum | 6.045521 | 1.458323 | 1.885357 |
| Episode minimum battery ratio | .100412196 | .103327944 | .105099009 |
| UAV-step fraction at/below 10% reserve | .011041667 | .001000000 | .001536458 |
| Input Wh | 378.680556 | 449.662663 | 487.428368 |
| Consumed Wh | 1355.019309 | 1366.684520 | 1421.456553 |
| F-mode UAV-steps | 8257.125 | 4537.125 | 5968.250 |
| Guard-blocked actions | 858.875 | 1904.875 | 1203.250 |

| Contrast | QoS/step difference [t7 interval] | Native J difference [t7 interval] | Joint service/J wins/losses |
| --- | --- | --- | --- |
| I-H | +.045360320 [.015276119, .075444521] | +145.242828 [49.830363, 240.655292] | 8/0 |
| C-H | +.031445226 [.002383963, .060506488] | +102.644716 [7.834126, 197.455306] | 6/2 |
| C-I | -.013915094 [-.044648208, .016818020] | -42.598112 [-135.020718, 49.824494] | 3/5 |

I-H J decomposes into **+136.080959** cumulative QoS, **+9.174396** from the
unchanged coefficient2 return penalty, and **-.012527** shaping difference.
C-I decomposes into **-41.745283** QoS, **-.854068** return penalty and **+.001239**
shaping. All cutoff/depletion counts, penalties and cutoff-step exposures are
zero. These are primarily service changes, not a shaping-score improvement.

Every C-I primary world is retained here; seed suffixes complete `310928xx`:

| Suffix | QoS/step difference | J difference |
| --- | ---: | ---: |
| 01 | +.037404343 | +111.783269 |
| 02 | +.017332897 | +50.725859 |
| 03 | -.074271999 | -224.616478 |
| 04 | -.049291034 | -148.649315 |
| 05 | -.013167826 | -47.860198 |
| 06 | -.013936030 | -36.332942 |
| 07 | -.028638694 | -85.319155 |
| 08 | +.013247591 | +39.484066 |

C-H loses in **04/07**, respectively QoS **-.018989655 / -.026053564** and
J **-58.571159 / -78.741937**. I-H's smallest J gain is **+6.577218** in07,
largest **+333.793688** in03. This does not make C's increment useful merely
because C's mean remains above H.

Risk is not uniformly improved. Both I and C increase return-cost/step versus H
in **03/04/06/07**. C increases it versus I in **01/02/03/04/05/08**; its mean
increment is **+.000142345**, while I-H and C-H means are **-.001529066** and
**-.001386721**. Their intervals all cross zero. I lowers minimum battery versus
H in01/02/03/06/07 despite its favorable average, and creates reserve breaches in
**06** (minimum **.098111190**, **.791667%** UAV-steps) and **07** (minimum
**.099598816**, **.008333%**), where H had none. C versus I creates the adverse
**05** tail: minimum **.097327669** versus **.114689842**, **1.229167%** reserve
exposure versus zero, and a below-half-service gap of **187** versus **176**
steps. C also acquires another >=60-step low-service spell in03. Worst observed
minimum batteries are H **.091435980**, I **.098111190**, C **.097327669**.
No zero event counts, mean improvement or eight-world panel establish safety,
risk dominance or a reserve invariant.

All zero-QoS gaps are the shared startup prefixes in03/05/06 (**13/68/78** steps);
there is no later zero-QoS spell. Fixed-bin mean QoS preserves later service:

| Native step bin | H | I | C |
| --- | ---: | ---: | ---: |
| 0-1000 | .791042055 | .818690938 | .814624041 |
| 1000-2000 | .826998719 | .870725268 | .869096554 |
| 2000-3000 | .690375635 | .755081163 | .719031491 |

C-I J differences by those bins are **-4.066881, -2.428419, -36.102812**.
I's package gain is not confined to initial deployment; neither these bins nor
the initial/input-relative phase summaries isolate why it occurs.

Charging and movement qualify the apparent recovery story. I and C charge
before the first F entry in **7/8** and **5/8** worlds, H in none. Mean first
input is H1572.625, I831.250, C997.500; mean waiting UAV-steps are
H5264.250, I3053.375, C3848.750. Mean charging UAV-steps are H1363.250,
I1680.375, C1781.875. Charging radio availability and native priority allocation
were unchanged. C consumes **more than I in every world**, mean **+54.772033 Wh**, and the
independent raw reading finds more travel and a lower time-averaged fleet-minimum
battery in every world. More charging input has not supplied a C-I service gain.
Mean input-minus-consumption stays negative: **H -976.338753, I -917.021857,
C -934.028185 Wh**. H3000 completion is not indefinitely sustainable cycling.

The model/choice trace is active, not an all-hold result: I/C record positive
selected-versus-incumbent model gains in **284/400** and **269/400** clocks.
Held-itinerary versus later replanning QoS discrepancies average **+.116990**
and **+.134238**, with mean position discrepancies **732.7/872.5 m** and mean
absolute battery discrepancies **.040865/.050453**. These deliberately compare
different future action paths. They do not validate forecast accuracy, identify
forecast error as C's causal failure, or justify the declined physical model.

### Full cost

The native accepted-to-exit interval was **2063.284066 s**; runner invocation
elapsed **2016.511271 s (33.61 min)**. Summed worker wall was **3980.410978 s
(66.34 min)**; summed worker CPU **4066.021775 s (67.77 min)**, parent CPU
**.304824 s**. Two workers each used one numeric thread. Maximum measured worker
RSS was **561,840 KiB**, parent peak **477,564 KiB**; neither is a simultaneous
node memory peak. No worker resource row is missing.

| Work | I | C | Total |
| --- | ---: | ---: | ---: |
| Score requests | 57,788 | 57,360 | 115,148 |
| Actual model evaluations | 54,435 | 54,146 | 108,581 |
| Native routing/service snapshots | 163,305 | 162,438 | 325,743 |
| Station events | 1,072,661 | 1,046,972 | 2,119,633 |
| Analytical phases | 1,295,643 | 1,256,947 | 2,552,590 |
| Planner wall seconds | 947.868896 | 945.740576 | 1893.609472 |

These remain inside the declared 117,200/351,600 plan/snapshot bounds; no
primitive-step forecast was run. Planner wall is already included in worker wall,
not extra additive runtime. Mean worker wall/world is **H85.519, I206.665,
C205.367 s**. Native J does not price this computational increment. The 72k
native evaluation steps, scorer snapshots, event work, artifact bytes and measured
checks above are all real costs despite zero fits. Implementation, repeated
development checks outside the listed durations, review, publication and readback
add partly unmetered work; no end-to-end wall or simultaneous-memory claim is made.

### Independent reading and DM disposition

Registered `hmasd-research-critic` `/root/dm_energy_coordination/result_critic`
reviewed in a separate context without DM/Root conversation inheritance. The
assignment disclosed completion and interpretation boundaries; navigation exposed
allocation summaries, so this was independent evidence-first review, not blinded
review. It reconstructed the new result before reading prior explanations and
Root's disposition, inspected all24 original NPZ files, and independently
reproduced **120** J/QoS/energy/minimum-battery scalars exactly. It read the original
supporting/adverse studies rather than treating adviser agreement as evidence.

Its substantive recommendation is **revise**: retain I as a promising ordinary
package, end investment in the unchanged sequential C recipe, and consider one
fresh comparison against the already useful ordinary P (`five_ten` transit hold).
It reports **no material dissent** relative to the frozen exploratory reading and
absence of a selected follow-on. It explicitly opposes an expanded claim that
sequential conditioning or recharge coordination has demonstrated useful benefit.

I adopt that reading. The prediction that C's sequential conditioning improves
complete native utility has weakened, not merely suffered a technical omission.
The descriptive interval still permits a positive population increment; the
observed losses and universally higher consumption nevertheless give no earned
reason to invest in unchanged C, automatic parameter rescue, a larger physical
model or a learning residual. The parent question is not refuted: both analytical
packages have useful conditional H comparisons, and I's all-world gains provide
a credible ordinary control opportunity on this panel.

The identified structure is shared service/routing, worst-member return risk and
station capacity. **Which coupling produced useful incremental coordination is
still unresolved.** I already uses joint scoring and a joint veto. C-I measures a
finite sequential versus simultaneous improvement procedure, not coordination
versus no coordination. I-H also changes target choices, model/computation,
execution and cadence (60 versus30). Ordinary flexible spatial deployment and
guard-aware execution, with the host's own battery-priority allocator providing
balancing, remains a strong simpler explanation; this is a hypothesis, not an
established causal diagnosis. No representation requirement, learning advantage,
learnability limit, accurate anticipation or real-world safety claim follows.

This revises rather than erases the background. B07 showed recovery with major
service-loss worlds; B09-B11 did not turn more charging continuity into complete
usefulness. Availability B04/B05 retained ordinary finite-planning value and risk
tails. Cooperative B02's learned package lost without diagnosing general planning
failure; the declined transit-handoff design was never an empirical negative.
B01 now adds a complete ordinary package opportunity but no demonstrated C-I
increment. It does not reopen those old fits or require learning as a contribution.

For Root's next allocation, the critic's strongest proposed comparison is frozen
**I versus existing P**, eight fresh paired S2/H3000 worlds, **16 episodes / 48k
steps / 0 fits**, retaining each complete program's actual cadence. It would ask
whether I is worth reusing beyond another demonstrated ordinary option, not
identify recharge causality. Positive service/J with acceptable observed risk
and compute would retain I as the stronger conditional reference; P matching or
winning would favor the simpler package; mixed/uncertain outcomes need not buy
an extension. Historical workload references are I's **27.6 worker-minutes** here
and about **28.8** for P on a different execution context, not a runtime promise.
Integration, matched-node cost and prospective practical acceptance criteria would
still need specification. **This is a recommendation, not a selected study or
launch authority.** No new comparison, fit, horizon, panel expansion or model
repair is active. B01 is fully read; retain the useful I/C/H reference code and
negative comparator, with the wider question reserved for Root's next assignment.

### Retirement and measured cleanup

After local compact verification, full raw checks and checking the reviewer's
consumers, the configured snapshot collector preview initially refused `/proc/660/cwd`
inspection. The documented existing passwordless, read-only `--sudo-process-scan`
resolved that concrete check. Preview then found the exact snapshot eligible;
apply under the remote writer lock removed only
`.git/hmasd-launch-sources/7ea7d7d869b94ac5aba9f7ff532c6590`, with terminal identities,
durable source reachability and retained external output verified. Allocated
snapshot bytes fell from **799,256,576 to0**; absence was checked.

Removed all three local disposable files (`verify_collected_b01.py`,
`remote-operative-row.patch`, `b01-wait-request.json`) and their empty owned temp
directory, **20,480 to0 bytes**, plus the remote applied patch and its empty
owned temp directory, **8,192 to0 bytes**. The local empty stdout/stderr collection
copies were removed too (zero allocated file bytes); original empty logs remain
with the run. This closure reclaimed **799,285,248 allocated bytes**; including
the already recorded preparation bytecode cleanup, B01 reclaimed **799,539,200
bytes**. No cleanup blocker or redundant snapshot remains for this operation.
Required unique raw evidence, compact records, native claim and published source
identity remain; no backup chain or whole-tree retention was created.

## 2026-09-28 - B02 selected: frozen I versus the existing P package

Root has now selected the next observation recommended in the completed B01
independent review: **I versus existing five_ten transit-hold P**, eight fresh
common S2/H3000 worlds. The question is whether I earns reuse beyond another
ordinary package with demonstrated usefulness, not whether recharge coordination
or accurate anticipation causes an advantage. The prior applicable independent
scientific review covers this choice; no duplicate review or new Pro gate is
added. B01's positive I-H comparison, adverse C-I comparison, all reserve tails
and full costs remain constraints. Current RESEARCH's ordinary-planning and B01
background directly motivates the stronger comparator. The different-world
radio-placement result mentioned by Root cannot rank these programs and supplies
no reason to change this comparison or add an arm.

### Exact programs and information

I calls the unmodified `b01.controller.AnalyticalController("I", env, config)`
from the B01 source `e663b53c7ea3f52983365ed9c3ce044bc4ccf699`. The controller and
itinerary Git blobs remain `fa53cea6ae82bb65f101f1f78190b3c44ae45ada` and
`2167405986ec9059703cd9516ca91f52842d8b0a`: 60-step actual replanning, incumbent
comparison, simultaneous unilateral proposals, assembled-plan joint veto and
fallback, unchanged 600-second analytical itinerary and all native feedback.
No parameter, target library, energy formula, risk term or ordering is repaired.

P calls `experiments.candidates.energy_relay_availability.b04.transit_hold.
TransitHoldController(env)`, the original B04 five_ten controller published at
`025350669bc5e8ab99fc71954f749ae47a6853e9`. B05 source
`754d5d34d905a81b58b78e69ae85b8a07cb19aad` reuses it; its Git blob is still exactly
`3750fff9b8109c213eab3e2fe8eec55d6160806d`. The common heuristic, observation,
feedback and evaluator files also have no diff from that B04 version. The retired
cooperative B02 source `9f72afd2223baccd9ed554b0ef86bcbe5277afb5` documented use of
the same P, not a new optimizer to reconstruct. The read-only named Scout traced
these identities and the nested cost; I checked the actual integration APIs.

P preserves H1 central target assignment, continuation memory, vertical behavior
and **10-step actual cadence**. Its candidate set is the all-move baseline plus
one horizontal hold for each movable assigned member, at most nine plans. Any
current F mode, legal return margin at/below the production entry threshold, or
absence of a movable member triggers the original all-move fallback with no
scorer calls. Active plans maximize `(q0 + 2*q5 + q10)/4`, with the original
strict ordering and tie rules. Positions at5/10 are closed-form projections;
there is no forecast `env.step`, energy propagation, charging schedule or return
penalty in P's score. Production F still acts on every actual primitive step.

Both receive current central user/BS xy only on their own replanning clocks and
legal own observations each tick. P's scorer deep-copies the live environment,
overwrites positions and batteries from those declared facts, resets association
and geometry/communication caches, then uses native radio/routing/delivery.
I's scorer installs declared facts into its separately reset fixed-config model.
Thus cadence, model knowledge/construction, action choices and computational work
are deliberately **not matched**. These are compatible complete native packages,
not mechanism controls or an information-value decomposition. The source audit
found neither identical controls nor a task incompatibility requiring a scope
change; these concrete differences were returned to Root before integration.

### Fixed comparison, cost and reading

Batch `b02_i_vs_p_a01` has seeds **41092801..41092808**, ordered by seed and then
I/P: **16 episodes, at most48,000 native team transitions, 0 fits/updates**. A
repository search found no prior use of this block in source, notebooks or run
JSON. These are new initialized worlds, not a refill or replay of B01. Native
S2 physics/reward/guard/charging and H3000 termination remain unchanged. No C,
extra panel, cadence matching, horizon search, policy repair or fit is selected.

I has at most **58,800 score requests / 176,400 routing-service snapshots** for
eight worlds. P has at most300 clocks/world. An active P clock uses one shared
q0 plus two snapshots per candidate, at most **19**, including q0. Hence P's
bound is **21,600 candidate-plan scores + 2,400 shared-q0 snapshots**, totaling
**45,600 native service/routing snapshots** across eight worlds. Each snapshot
calls native route construction once; combined snapshot bound is **222,000**.
Fall-back clocks may use none. Both programs have **zero primitive forecast
environment steps**; I has event/phase work, while P has closed-form projected
positions and repeated environment deep copies. Those operations are not free
because they are not fits or native transitions. Do not multiply P's5/10 labels
into fictitious simulated steps or omit q0 from its cost.

Record per-arm/controller wall, decision-tick wall, invocation/summed worker
wall, worker/parent CPU and scoped peak RSS, native transitions, score requests,
actual model evaluations, scorer/routing calls, P baseline/projection counts,
I events/phases, input/trace bytes and all extra engineering/readback cost. I's
27.6 and P's approximately28.8 worker-minutes for eight worlds are historical
workload anchors from different contexts, not a runtime guarantee or cost match.
Use the configured actual node with two workers and one numeric thread, subject
to fresh runner-side admission. No synthetic runtime ceiling or extra fit
allowance is inferred from the workload estimate.

Primary signed comparison is **I-P** for full native J and QoS/step. Retain every
world and all native reward components, delivered service, fixed1000-step bins,
return costs, minimum battery, reserve/cutoff/depletion exposures and events,
service gaps, input/consumed energy, feedback/guard behavior and computational
cost. Pair initial-state, full exogenous-user trajectory and live RNG digests;
only eight complete verified pairs receive descriptive t7 intervals. Missing or
failed work is technical missingness, not a negative package result or permission
to replace a seed. A failure stops new submissions while accepted pending work
is collected; no automatic retry or continuation.

Read gains and risk/compute separately; there is no new utility scalar pricing
computation and no confirmation threshold. Positive average service/J with new
cutoff/depletion, reserve exposure or worsened adverse tails does not establish
default replacement or risk dominance. If I supplies useful native gains with
an acceptable observed tradeoff, retain it as a conditional ordinary reference;
P matching/winning can favor the simpler package. Mixed gains/risks or broad
uncertainty can end the investment without expanding seeds or tuning. A mean
from another panel is never subtracted to answer this comparison. No possible
outcome identifies the contribution of recharge coordination by itself.

### B02 L0: minimal adapters and two-arm collection

Own only `experiments/candidates/uav_energy_coordination/b02/`, `run_b02.py`,
matching `tests/experiments/candidates/uav_energy_coordination/b02/`, and existing
direction records/scratch. A narrow exception within our owned B01 reader permits
explicit arms/contrasts/interpretation arguments with unchanged B01 defaults;
test that its original output is preserved. Do not edit either frozen controller,
the itinerary, P's paths or any shared native code.

A direction-local `FrozenController(arm, env, config)` forwards proposals/reset
and exposes the base's targets/plan-input steps. It only reads existing counters
and records wall time; no new score, environment step, RNG call, actor input or
action modification. API: `decision_arrays()` for partial evidence,
`validate_trace(length)` for complete decision arrays, `costs` for current known
work, `close()` for the existing I scorer. P decision arrays reuse B05's existing
serializer with `transit_` rather than `planner_` names, avoiding confusion with
I's three-point itinerary arrays. Keep all P fallbacks/candidates/q0/q5/q10 and
near-tie readings. I uses the existing decision validation. Actual source hashes
and original identities go into config.

The new entry requires native admission before runner effects, fixed seed block,
source SHA, threads and job plan. Reuse the existing evaluator, production F,
read-only native failure-preserving observer, bounded submission and manifest
utilities. Retain native data and completed-clock/known cost after failures,
mark unknown in-progress work, collect pending accepted jobs, and never retry.
Raw evidence stays on the configured node; compact records are published.

Focused checks: I/P adapters return the same native actions and seeded trajectories
as their unwrapped originals on separate correctness fixtures, reset/clock/RNG
and source identities, P q0-inclusive accounting/fallback bounds, two-arm complete
pairing and adverse reads, default B01 reader regression, admission before effects,
and partial-native/cost preservation. No study seed is used in checks or policy
selection. Independent engineering review examines the adapter/counters and
execution/readout contract; the scientific reviewer is not repeated for this
unchanged selected question. Publish exact inputs before admission, retain the
same native handle, and remain in this native turn for deterministic long waits
because the detached queue cannot be assumed to resume an unloaded native child.
