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
