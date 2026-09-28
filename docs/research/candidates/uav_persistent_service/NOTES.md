# UAV persistent service commitments

## 2026-09-28 - Prospective selection: finite service and recharge commitments

This is the fresh native DM's concrete design return to Root, before substantial
implementation or result execution. Root assigned the fleet timing/duration
question after the owner resumed the next round. Current published main is
`858e8cff50c467438d42e9f47fbfef70269a6b1f`, verified against `origin/main`.
The owner pause is lifted; other directions' pauses and accepted operations are
unchanged. The new direction is not yet registered for result execution. Root's
same independent selection critic will review this concrete comparison; this is
the consequential selection boundary, not a per-run approval rule.

**Current work: 0 fits, 0 new native/model transitions, no run handle.** Reading,
one bounded read-only source Scout, literature retrieval, reasoning and authoring
are real but incompletely timed costs. The intended first contribution is useful
complete UAV service and an empirical boundary on finite learned scheduling,
not a new PPO method, decentralized MARL algorithm or indefinite-service theorem.

### Inherited evidence changes the design

The relevant published background is [RESEARCH topics 2, 6, 7 and
8](../../RESEARCH.md#研究背景与共享认识) at the revision above. Its concrete effects
are: retain the strongest compatible ordinary reference; separate central truth
from lawful observations; measure requested and executed decisions; preserve
native service and all risk tails; and distinguish a fitted instance from
independent training replication.

| Original evidence | Binding consequence here |
| --- | --- |
| [Energy B01/B02 complete reading](../uav_energy_coordination/NOTES.md#2026-09-28---b02-complete-i-does-not-earn-reuse-beyond-p), I source `e663b53c7`, P source `025350669`, B02 input `2b66dc512` | I-H was useful, but I-P on eight fresh H3000 pairs was J -136.696 and QoS -.039707, with six joint losses and an intact 728-step terminal outage in I08. More charging was not more net usefulness. Neither the charging mechanism nor a repair was identified. |
| Original I controller and itinerary at `e663b53c7` | Proactive station trips are already tried: every member's library included both station goals; station goals set dock when the selected station was nearest; goals persisted between 60-step replans. Its forecast treated explicit station goals as residents. A new name for that goal search is not a new study. |
| [Cooperative B02](../uav_cooperative_planning/NOTES.md#2026-09-27--complete-native-b02-reading), source `9f72afd2` | One offline learned ranking fit over P's move/hold library lost to P and chose 4575 holds in 4582 active windows. This proposal uses no old checkpoint, replay or value-ranking retry. The old result does not identify an optimization defect. |
| [Unexecuted handoff design and decline](../uav_transit_handoff/NOTES.md#final-design-disposition) | Do not rebuild its costly 60-step native surrogate or attach a residual learner that retains all ordinary search cost. Its decline is not an empirical negative for handoff. |
| [Information B03](../uav_information_value/NOTES.md#2026-09-28---b03-independent-reading-and-comparator-disposition), input `153a87e6`, result `4204bc869` | Lawful P_BS is a stronger conditional reference for compatible lawful-information questions, with binding low-reserve counterexamples. Here choose central current snapshots to preserve exact TransitHold P. P_BS is a different information/action package, not silently this P or a default-safe policy. No deployment-lawfulness claim follows. |
| [Sensing B02](../uav_active_sensing/NOTES.md#2026-09-28---b02-complete-semantic-exposure-without-established-package-value), input `087c8823a`, result `02e676dcd` | 3411 eligible training choices, including 1618 service and 1793 probe choices, did not establish package value. More exposure or parameter movement is not success. No optimizer/entropy/gate repair is inherited. |

Late low-reserve fleets motivate examining temporal availability, but do not
diagnose a charge-cycle defect or establish available sustainable-service gain.
The new difference from I is a declared admission and finite recharge commitment
whose dwell clock survives ordinary replanning, followed by explicit release to
current service planning. This remains a related scheduling approach, not a claim
that charging or persistent goals are new. Conventional dispatch rules are a
serious alternative to learning.

### Native interface and scope

Use frozen S7-S2 physics, eight UAVs, 30 users, original reward, H3000 and
production per-step F `(enter_margin=0, exit_margin=.05)`. Keep native guard,
limp-home, allocator, reward coefficients and world generator unchanged. All
three arms receive current central user/BS xy only at the same original P
10-step refresh, plus the existing legal own/fleet energy and station records.
No user velocity, future trajectory/RNG, hidden association history or privileged
critic input is added. The scheduler decides every 30 steps from the most recent
current snapshot and its own option/energy history.

Source facts checked directly, with a bounded read-only Scout:

- `energy_aware.py:1617-1752`: action is xyz+dock; dock is reissued every step,
  `action[3] > .5`, to the nearest active station in 3D. Outside 160 m xyz remains
  policy controlled; inside it native docking overrides xyz at 3 m/s horizontal
  and 1 m/s vertical. Capture is within 20 m with actual speed at most 1 m/s.
- `energy_aware.py:291-296,1805-1889`: S2 enables charging with capacities `[1,1]`.
  Priority is lowest post-consumption battery, then longer wait, then index.
  There is no station reservation or protected charging slot. At dt=1, 1000 W
  input and 168.49 W hover draw imply nominal net +.231 Wh/step below full charge,
  about .001446 of a 160 Wh battery. Contending arrivals can interrupt it.
- `energy_aware.py:2152-2190`: charging/returning members remain radios above the
  service cutoff unless failed. A genuine dock-directed movement can bypass the
  native topology guard. Other movements still face it.
- Production margin F is external, in
  `experiments/candidates/energy_relay_benchmark/b01/feedback.py`; native limp-home
  acts at battery <=.05. Real F always overrides a voluntary command and retains
  its own mode state. A voluntary commitment cannot release F or reserve power.

The primary bridges narrow, rather than certify, this comparison.
[Asghar et al., section III](https://arxiv.org/html/2303.08935#S3) uses graph visits
and latency constraints with recharge represented in travel costs; native radio
delivery is simultaneous and nonadditive. [Kumar et al., section II](https://arxiv.org/html/2409.00572#S2)
assumes known full-charge/full-operation durations and controllable consecutive
charging slots, excluding ordinary partial charging. Native priority can preempt
each step and no reservation action exists. Their guarantees do not transfer.
The useful bridge is staggered availability under shared energy resources; the
missing coupling is live access/backhaul geometry, moving users and compulsory F.

### Concrete shared commitment interface

The proposed first comparison is deliberately limited to **nearest-station
admission and dwell duration**, with complete service planning continuing around
it. Station rebalancing, learned spatial anchors and peer canonical-frame
training are outside this first study. This restriction is substantive: both
chargers may not be reachable through a useful discretionary schedule.

1. At steps 0,30,..., a choice is `continue service` or `(member i, dwell d)`,
   with `d in {120,300,600}` primitive seconds. At most one new commitment starts
   per clock. Several existing commitments can proceed asynchronously.
2. Member i is eligible when available and not failed, not in effective real F,
   battery is strictly below full, and it has no active commitment. Its nearest
   legal station must have neither an active voluntary commitment nor a current
   real-F member targeting that station. Also require fewer than two active
   voluntary commitments globally. This is a common admission restriction,
   not a native reservation. Later F entry or nearest-station changes can still
   create contention after admission; the two-member global limit remains.
3. Starting stores the nearest station and chosen duration. Command the same
   capped stationward vector/dock primitive as production F while retaining a
   separate commitment state; real F is applied afterward. If nearest station
   changes, follow the current nearest station and record that change. There is
   no policy-controlled station ID or hidden station reassignment authority.
4. First observed geometric arrival within 20 m starts a wall-clock dwell counter. Keep
   requesting dock until d elapsed capture seconds, full battery, or 900 seconds
   since initiation, whichever occurs first. Waiting without charger admission
   consumes dwell time. Leaving capture does not restart the clock. No arrival
   by timeout is a failed-arrival commitment, not a completed recharge. This
   arrival definition is separate from native speed/priority-qualified charging.
5. A release returns the member to the current ordinary service assignment at
   the next 10-step clock. Real F may still prevent departure. Log requested and
   actual release separately. H3000 may censor a commitment; no completion is
   invented. There is no adaptive duration extension or automatic second attempt.
6. Keep commitment assignment availability separate from real F modes. In the
   common L/O wrapper, committed members are omitted from H1 matching and hold
   candidates; only real F activates the inherited fleet-wide all-move fallback.
   The other P rules, clock, target continuation and strict ties are retained.
   In P's short radio projections a committed member remains at its current
   observed position/battery; it is not removed from radio service. This is an
   explicitly shared approximate execution adaptation, not a pure duration
   contrast. The unmodified P arm remains separate. With no commitments the
   wrapper must reproduce historical P exactly.

The actual post-filter command, displacement, dock/capture/charge, early F,
timeout, release and return to service are separate measurements. A valid label
does not imply arrival, charger allocation, useful recharge or service recovery.
The common admission restriction may leave little opportunity; measure this in
the full study rather than impose an activation pilot.

### Arms and ordinary competence

**P:** exact `TransitHoldController` from `025350669`, unchanged 10-step
all-move/one-horizontal-hold candidates and `(q0+2*q5+q10)/4` score, including
every real-F fallback. This is the historical competent ordinary reference,
not a safe optimum and not lawful P_BS.

**O:** a fixed capacity-aware earliest-deadline dispatcher over the complete
shared interface above, with the common commitment-aware P service controller.
For each eligible i, compute remaining service time
`D_i = max(0, margin_i) * 160 * 3600 / p_i`, where `p_i` is the maximum of
168.49 W and its measured positive battery draw over the previous 30 seconds
converted to W; use 168.49 W when that history is unavailable or includes
charging. This is a held-geometry estimate, not a safety certificate. Estimate
station travel tau_i with capped 30/5 m/s motion outside 160 m and 3/1 m/s inside,
using the same decoded xyz and station coordinates.

For a candidate i, the next same-station member's earliest remaining departure
slack is `S_next = min_{k != i}(D_k - tau_k)` over currently free members; use
infinity when absent. Choose the longest d in `{120,300,600}` for which
`tau_i + d <= S_next`; choose 120 when none fits. Dispatch only if
`D_i <= tau_i + d + 30`. Across dispatchable members choose the smallest
`D_i - tau_i`, breaking exact ties by lower observed connection load and index.
Otherwise continue service. Busy stations wait under the common admission mask;
no forecast claims to control later native priority.

O sees fleet energy deadlines, current queue/forced-return occupancy, travel
cost and the next member's competing deadline; it varies dwell duration and
replans from actual history. It uses no fitted parameter and no native future
rollout. It is a competent conventional scheduling candidate, not a proven best
ordinary scheduler. Its held-geometry deadline can be wrong as P moves members,
and its service-aware tie rule is weak. Exact P separately protects against
mistaking a weaker new scheduler for the best available ordinary reference.
The selection critic should challenge this ordinary comparator's adequacy.

**L:** a direct, non-residual on-policy PPO dispatcher over exactly O's interface.
It selects the whole admission/member/duration decision rather than adjusting
O's score. Inputs: current central user/BS positions; decoded own/fleet/station
fields; current P targets; real-F masks; option station/age/arrival/dwell fields;
the preceding 30-second battery history and masks; remaining episode time.
Use fixed physical scales, with no evaluation-fitted normalizer. The critic
gets the same input, not privileged state. Two 128-unit tanh layers per actor
and critic suffice for this bounded exploratory instance.

Factor the distribution into a binary service/dispatch gate, an eligible-member
categorical and a conditional 3-duration categorical. Zero actor output heads
give initial semantic mass .5 to service and .5 to dispatch, independent of
member/option counts; dispatch mass is uniform across eligible members and then
durations. With no eligible member, service has probability one. Training samples
this joint distribution. Evaluation first chooses the binary gate by argmax
(service on exact tie), then member/duration argmax with index/shorter-duration
ties. This is semantic staged argmax, not flattened joint-label argmax. Initial
deterministic L is therefore exactly P; verify that equivalence in correctness
fixtures, so a fourth untrained evaluation arm is unnecessary. Record the actual
gate and conditional probabilities rather than infer preference from counts.

Use maintained SB3 PPO, fresh parameters, gamma=1, lambda=.95, clip=.2, Adam
3e-4, 10 epochs, batch100, entropy0, value coefficient .5, gradient norm .5.
Train on sums of actual original native reward over each 30-step segment,
without shaping, future labels or forecast targets. Finite H3000 has zero
continuation. Forced-choice rows remain for the critic; their gate is fixed.
Retain actual optimizer counts, loss/gradient health, requested-action storage
and actor/critic movement. These checks establish learning ran, not usefulness.

### One complete first comparison and cost

Proposed batch `b01_commitment_a01`: **one fit**, 64 distinct H3000 training
worlds `52092801..52092864`, policy seed `5292801`. Four lanes, 100 macros per
world, 16 complete four-world rollouts, 640 optimizer steps. This is 192,000
native training transitions, 6,400 macro decisions and 64,000 epoch exposures.
Select only the final checkpoint, with no intermediate evaluation or tuning.

Evaluate L, O and exact P once each on 16 common new H3000 worlds
`52192801..52192816`: 48 complete episodes, 144,000 native transitions,
zero new updates. Total is **112 episodes / 336,000 native transitions / one
training instance**. Exact-integer seed search found no earlier occurrence in
current source/notebooks/run JSON. Seed numbers alone do not establish paired
worlds: verify common initial state and exogenous user-trajectory/RNG identity.
No horizon extension, second fit, control arm, grid, replay or retry is included.

All 112 worlds retain P-family service computation at most 300 clocks/world,
with at most 19 native radio snapshots each: **638,400 snapshot calls** is a
loose total ceiling (shared q0 included). Forced modes and ineligible choices
reduce this count. The new O scheduling itself uses finite arithmetic over eight
members, with **zero primitive forecast environment steps** and no extra radio
calls. Neural inference, the real environment, P deep copies/routing, optimizer,
recording and 11,200 total 30-step scheduler clocks are additional actual work.
P itself need not invoke a scheduler, so only 9,600 such clocks are decision
opportunities for L/O; the larger number is an accounting ceiling, not executed
neural inference. Report actual calls and per-arm CPU/wall/RSS.

Historical P cost in Energy B02 was 629.83 worker-seconds for eight worlds,
including 22,249 snapshots. A literal 112-world scaling is about 2.45 worker
hours, not a quote: L/O alter fallback occupancy, four training workers and
optimization change contention, and the upper snapshot count is much larger.
Plan for hours of CPU work, with elapsed wall not yet measured; fresh actual
node admission decides whether configured `wsl_4070` can host four one-thread
training workers while the peer's accepted B05 remains untouched. There is no
GPU requirement or resource reservation now. A smaller admitted process count
would need to preserve the declared data/optimizer schedule, not change fits.

Engineering scope, if selected: a direction-local commitment state machine and
P adapter; ordinary dispatcher; SB3 distribution/macro wrapper; failure-preserving
batch/reader and narrow tests. Reuse shared native evaluator and launch/admission,
not a copied simulator or new launcher. Necessary checks cover no-commit P
identity, real-F precedence, assignment versus F masks, duration/timeout/aliases,
semantic mass and masked likelihoods, native reward storage/finite termination,
RNG/data separation, and adverse/partial records. Independent engineering review
is required for this high-risk executable meaning. Implementation, review,
tests, raw retention and readback have additional unmetered cost; no full-project
runtime price is claimed. No substantive code or fixture has been run yet.

### What the outcomes would change

Primary contrasts are complete **L-O and L-P** in native J and QoS/H3000;
O-P measures the ordinary commitment package. Read all signed world pairs,
descriptive t15 intervals conditional on this one fit, complete native reward
components, fixed 1000-step bins, delivered service, longest service outages,
minimum battery/margin, <=.10 reserve exposure, final 300-step persistent reserve
members, cutoff/depletion, charging input/draw/net storage and computational cost.
No world is dropped because the choice did not activate.

The conjecture predicts meaningful pre-F arrivals, held charging and released
members returning to useful service, together with complete J/service gain.
These process readings can fail separately. A useful exploratory L package
would have mean L-O and L-P QoS >=+.01 and positive native J on this panel,
with uncertainty and every loss disclosed. Additional cutoff/depletion or
terminal zero-service worlds, greater mean reserve exposure, or additional
last-300-step persistent low-reserve members against either reference blocks a
default-use recommendation even if means pass. This is a prospective use rule,
not a claim of statistical safety or a confirmation test.

- L improves over both references with acceptable observed tradeoffs: a finite
  learned package merits pricing independent-fit replication, not confirmation.
  It does not identify a temporal-credit mechanism, novel coordination algorithm
  or learning superiority over all competent ordinary scheduling.
- O improves over P and L adds no useful increment: retain a conditional ordinary
  scheduling asset if tails/cost permit. No automatic PPO repair follows.
- Neither commitment package earns usefulness beyond P: stop this exact package;
  do not rescue it with extra seeds, duration choices or a longer horizon.
- Few admissions, failed arrivals, F takeovers or little useful charge constrain
  this interface's realized opportunity. They are not evidence that PPO was
  inherently incapable or that all scheduling has no value.
- Mixed utility/risk or broad uncertainty may justify no further investment;
  technical incompleteness is missing evidence and never a scientific negative.

### DM recommendation at the selection boundary

**Provisionally select this one direct complete comparison, subject to the shared
selection critic's disposition.** Its scientific value is the real question of
whether finite return admission/dwell commitments improve complete service beyond
P, and whether direct experience adds to a capable inexpensive ordinary schedule.
It avoids the old costly model-search residual while retaining native coupling.
The most consequential objection is O's adequacy: if the critic finds its
deadline/duration rule too weak for the intended learned-increment claim, revise
the comparison or decline the investment; do not silently weaken that claim after
results. Other open premises are actual admission frequency, nearest-station
restriction, F/priority interference and finite learning. These can be read within
the experiment rather than added as prerequisite probes.

The claim is intentionally H3000 and central-information conditional. It neither
reopens the stopped I/C recipe nor establishes sustainability or a diagnosed
energy bottleneck. No peer operation, old DM session or App message is involved.
Root owns the pending question-selection resolution and cross-question plan;
ordinary in-scope execution after selection requires no per-fit acknowledgment.

## 2026-09-28 - Selection correction and accepted implementation scope

Root read the full independent selection review and selected the bounded L/O/P
study **after correcting O**. The material objection to `17ce44bfd` is upheld:
native return margin already deducts reserve and estimated return energy, so
`D=margin*capacity/p` estimates time to F entry, a departure deadline under held
geometry. Ranking by `D-tau` deducted travel twice. The full independent answer
and Root disposition will be linked from Root's published
[current research plan](../../RESEARCH.md#current-research-plan); no duplicate
selection critic, Pro consultation or prerequisite activation study is selected.
The following prospective rules supersede the conflicting O arithmetic above.

### Corrected O, with distinct time meanings

At macro step t let `R=3000-t`. Calculate each free member's departure deadline
`D_i=max(0,margin_i)*160*3600/p_i`, retaining the declared recent-positive-draw
estimate and hover fallback. `tau_in,i` is the nominal time to the nearest
station's capture sphere; use capped straight-vector travel at 30/5 m/s outside
160 m, then 3/1 m/s down to 20 m. Sum those two segment times, rounding the
result upward to whole primitive steps. At/inside 20 m it is zero.

For each free same-station competitor k, its nominal arrival if it waits until
F entry is `A_k=D_k+tau_in,k`. Set `A_next=min A_k`, or infinity when none exists.
This is an approximate station-arrival forecast, not a reservation or a claim
that F will follow that exact future route.

Let `tau_out,i` be upward-rounded travel at ordinary 30/5 m/s from the nominal
capture point on the current stationward line to i's current base H1 target at
100 m height. If already inside capture, use the current point; if no finite
base H1 target is available, O does not initiate for that member at this clock.
This estimates restoration to the current service target; actual post-release
H1 rematching and the topology guard can change it. Add ten seconds for the next
ordinary planning clock. Keep this restoration estimate distinct from occupancy.

For candidate i select the longest `d in {120,300,600}` satisfying both:

`tau_in,i+d <= A_next` (nominal station occupancy ends before the next arrival),

`tau_in,i+d+10+tau_out,i <= R` (nominal restoration within the finite episode).

If none fits, continue service for that candidate. A feasible candidate is
dispatchable only when `D_i < R` and `D_i <= tau_in,i+d+30`. Among dispatchable
members rank **D_i**, then lower observed connection load and index. No `D-tau`
ranking remains. A beyond-horizon departure deadline alone cannot motivate
recharge. The common L/O action rights are unchanged: these tests choose O's
action, not a mask constraining L's permissible choices.

Actual dwell means **elapsed time after first geometric arrival**, including
time waiting for allocation and later time outside capture. Release/full-battery/
900-second timeout and native F precedence stay as declared. A commitment still
alive at the native endpoint is right-censored; the horizon never fabricates
allocated charging, restoration or option completion. The endpoint constraint
is an approximate O rule, not a guarantee, and does not alter native termination.

Correctness cases to retain: another member with `D=600,tau_in=100` has arrival
700; a candidate with `tau_in=100` may choose d600 when the separate restoration
test permits it. Rank D100/tau90 before D110/tau1. With `D>=R`, O stays in service.
Reject a duration that fits occupancy but cannot restore by R; preserve equality
at the restoration boundary. Missing service target yields no ordinary dispatch.
No feasible duration yields service, without silently forcing120. These are
deterministic arithmetic checks, not result-bearing pilot worlds.

### L0 - commitment decisions through the native complete comparison

Deliverable: the exact selected controller/state machine, masked hierarchical
SB3 distribution, finite native macro environment, one fixed training schedule,
three-arm evaluator, compact readout and failure-preserving raw evidence. Own
only this direction's implementation/tests/notebook/runs/scratch plus its narrow
RESEARCH/routing entry after Root's shared plan publication. No shared native
environment, P source, reward, feedback, node control or peer code changes.

The bounded Implementer task owns `controllers.py` and matching controller tests:
one verifiable behavior, dispatch and execute finite commitments without changing
real F or exact no-commit P. It has no index/commit/launch/notebook permission.
The DM owns policy, training, macro/evaluation/reading integration and accepts the
Implementer's diff/checks. Other sessions' current benchmark changes are preserved.

Integration contract: discrete action0 is service; action `1+3*i+j` admits member
i for duration index j. `prepare(observations,modes,step)` occurs at a30-step
boundary, advances observation-only option state, computes/cache the ordinary
P action once for that same primitive step and returns finite float32 features.
The first eight features are the exact eligible-member mask (0/1). Actor and
critic features include only the declared current inputs and maintained history.
`apply_choice(action)` returns a serializable requested/executed decision record;
`propose(observations,state,step,previous_done,modes)` uses that cached step action
or advances ordinary P once, then applies voluntary commands. External production
F is always applied last by the recorder. A newly admitted member leaves H1
matching at the next existing10-step replan, not through an extra hidden call.
Release likewise restores eligibility at the next ordinary replan. Features and
ordinary restoration estimates use the current base H1 target from preparation,
not a temporary horizontal-hold target. All counters distinguish source calls,
macro choices, native steps and actual option events.

Within the common P adapter, true F determines the inherited fleet-wide fallback;
assignment/hold eligibility separately excludes commitments. Committed members
remain in the scorer's radio geometry at current observed position/battery.
No-commit behavior must match the original P action, target memory, snapshot
counts and native trajectory on non-study correctness seeds. Initial staged
deterministic L must likewise match P through the actual evaluator path.

Checks cover the corrected O examples above, option elapsed-time/timeout/full/
terminal semantics, station changes and the global two-commit limit, physical
F priority, meaningful/aliased duration choices, P fallback separation, native
mask/probability/likelihood and sampled-versus-staged decisions, no-eligible
states, final-only checkpoint, exact reward/action storage, finite-horizon zero
continuation, declared seeds/update counts, and complete/adverse/partial output.
Use non-study seeds for bounded correctness fixtures; count their native steps
and optimization wiring work separately from the selected fit. No activation
threshold or positive heuristic result is a gate. Required independent engineering
review follows the executable diff; independent result diagnosis follows complete
raw reading. Keep the one selected fit and64/48 episodes unchanged.

Root published the full independent answer, retained MATERIAL_DISSENT and resolved
selection in [round-three selection](../../archive/2026-09-28/RESEARCH-native-round3-selection.md#decision),
commit `0e9e32168ef7e37cab04e9f46753bb98f636fff8`. I read the complete answer and
adopt the correction above. Ordinary implementation now proceeds under that one
selection; no extra scientific approval or screening condition has been added.
The controller event `assignment_restored` means a finite H1 target is reassigned
while the observed effective F mode is off. Actual travel, connected load and
team service are separate native readings, never inferred from that event name.

## 2026-09-28 - B01 input acceptance and engineering evidence

The bounded Implementer returned `controllers.py` and five controller tests; I
read and accepted the implementation, then integrated the fixed direct PPO,
native macro collector, complete L/O/P batch and readout. Final feature width is
773, including the declared legal energy/station fields and explicit H1-target
validity; actor and critic still share identical current/history inputs. The
source P file remains byte-identical to `025350669`. No native physics, rewards,
guard, allocator, F thresholds or other direction's controller were edited.

The separate registered engineering Reviewer `/root/dm_persistent_service_round3/engineering_review`
read the actual executable path, not only this description. Three P2 findings
were preserved and corrected before launch:

- Pairing digests were initially recorded without suppressing paired conclusions
  on mismatch. Failed/missing pairing now makes the comparison incomplete and
  removes contrasts/practical conclusions while retaining each world's reading.
- Promised gradient health initially had no recorder. A nonmutating optimizer
  pre-step hook now logs finite post-clipping gradient norms/tensor counts;
  successful training must contain 640 such records and 640 actual updates.
- A new passive option reader initially grouped by timestamp, misattributing a
  release followed by same-step readmission. It now groups by chronological event
  indices, preserving release/assignment events before the next start.

The same Reviewer reread all corrections and returned **no material finding
remaining**. Its first independent run passed 11 tests in14.44s, including335
native transitions and one four-step synthetic optimizer update. No repeat
selection critic or new scientific pilot was used. I accept that engineering
disposition, without treating it as evidence of policy usefulness.

The final DM suite is **14 passed in13.92s**, using335 non-study native transitions
and one synthetic four-step update. It covers corrected O arithmetic; exact
no-commit and initial deterministic-L/P execution identity; commitment/F fallback
separation; elapsed/full/timeout/censor semantics; masks/joint likelihood/staged
mode; checkpoint round-trip; native four-process exhaustion; finite zero
continuation; partial output preservation; pairing/risk rejection; gradient
auditing; same-step option attribution; and the actual TrainingAudit callback on
a synthetic100x4 complete rollout with mismatched-storage rejection. The synthetic
callback has zero native transitions/optimizer updates and is not training data.

Across the recorded author/Implementer/Reviewer invocations, at least1525 native
correctness transitions and six four-step synthetic optimizer updates were used.
One interrupted tool handle for the bounded spawn/partial tests lost its terminal
return; it could add up to150 native transitions, but no live test remained after
owner resume. The later exact tests were rerun and passed. An early synthetic
test assertion used a pre-flattening SB3 action-array shape after optimization;
that test-only indexing was fixed (8 other tests had passed). No result-bearing
fit/world was consumed by either issue. Known returned test wall times total
about99seconds, excluding initial helper checks, the interrupted handle and
unmetered reading/implementation/review time. This is not the full engineering cost.

Owner resumed the interrupted task explicitly. Reconciliation found no persistent
service run directory, accepted handle or live worker. The selected scientific
budget remains one fit/112H3000 episodes/336000 native transitions/640 updates.
The primary node currently has ample available memory and only the unchanged peer
B05 GPU operation among result workers; formal fresh launcher admission remains
required. The finite dispatcher uses four single-thread CPU lanes and no GPU.
I will publish exact inputs, synchronize only this direction's canonical control
row if needed, then request the original first launch. This is not a retry.

### Accepted first operation and observation

Inputs `981e935ee336cbdde3f3b69f229019384376ba5f` were committed, pushed and
verified at `origin/main` before execution. Canonical remote policy synchronization
inserted only this direction's exploring row, preserving the existing other-DM
edits. The first control-only fetch without the configured login network shell
stalled; its local SSH process was stopped before using configured `zsh -lic`.
That fetch succeeded. It also emitted an existing auto-GC missing-tree warning
(`9e40125ee3e24973b69754649226d18847b45862`); no peer Git object/GC repair was
attempted. The exact published source snapshot subsequently prepared successfully.

The configured supervisor accepted the one launcher request, then the native
kernel separately admitted the scientific child at2026-09-28T15:54:25Z. The
[manifest](../../../../runs/uav_persistent_service/b01_commitment_a01/launch-manifest.json)
is the authoritative operation/source/process reference, and the
[fresh admission](../../../../runs/uav_persistent_service/b01_commitment_a01/admission-preflight.json)
reported13251149824 available bytes against the4294967296-byte floor. Training
reports one started fit and SB3 2.6.0; this is not a completed result.

The first observer request was refused locally because its SSH executable was
not absolute, before observer registration. Correcting it to `/usr/bin/ssh`
registered the same manifest in `hmasd_wait` generation1, job
`b01_commitment_a01`, 60-second probes and1500-second checkpoint window. Drain
then observed matching live runner/supervisor identities, accepted admission,
consistent records and absent exit witness. State belongs to native child runtime
`01a0e858-d69a-7dc2-b858-08d9438ed121`; registration is not a claim of queue wake.
I remain active, use long deterministic waits and drain/rearm this same handle.
No worker restart, duplicate launch or scientific retry occurred.

## 2026-09-28 - B01 complete: useful ordinary package, unchanged learned deployment

### Completion, collection and scope

The accepted first operation completed with a valid exit-zero witness and absent
runner/supervisor identities. The same deterministic observer produced one
checkpoint and then READY; both App queue attempts returned `-32600` because this
native child was not an independently loaded App thread. I stayed active through
two long native waits, drained and rearmed the same manifest, collected the
terminal facts, consumed READY and stopped observation. The final drain is
generation3, stopped, no pending event or delivery. No replacement worker or
changed scientific input was used. The committed
[terminal status](../../../../runs/uav_persistent_service/b01_commitment_a01/terminal-status.json)
and [observer reading](../../../../runs/uav_persistent_service/b01_commitment_a01/observer-terminal.json)
retain observation separately from failed queue delivery.

One fit completed all64 distinct training H3000 worlds,192000 native steps,
6400 macro choices and640 optimizer updates. All48 planned L/O/P evaluation
episodes completed H3000,144000 native steps. There is no failed, missing,
unstarted or orphan-raw cell, runner error or pairing failure. Initial-state,
user-trajectory, BS and RNG pairing checks pass on all16 evaluation worlds.
The final checkpoint is the only scored learned endpoint; no extra arm, horizon,
fit, rescue evaluation or early-checkpoint selection was added.

I verified every one of294 runner-manifest files,325632466 bytes, against size
and SHA256. Complete reading covered all112 raw trajectories, decision/event
streams, training exposures and640 gradient/update records. Native metrics were
recomputed from every trace, macro rewards compared to native reward sums,
episode lengths and finite endings checked, energy bookkeeping reconstructed,
and option summaries checked against chronological events and native allocation.
The compact [reading](../../../../runs/uav_persistent_service/b01_commitment_a01/reading.json),
[per-world results](../../../../runs/uav_persistent_service/b01_commitment_a01/perworld.json),
[paired summary](../../../../runs/uav_persistent_service/b01_commitment_a01/summary.json)
and [training result](../../../../runs/uav_persistent_service/b01_commitment_a01/training.json)
preserve all worlds and tails, not just the following means.

### Complete package comparison and adverse tails

| Contrast | Native J difference | QoS/H3000 difference | Joint signs |
|---|---:|---:|---|
| O-P | +196.348728 [153.466253,239.231203] | +.062865667 [.049190769,.076540566] | 15 wins,1 loss |
| L-P | 0 [0,0] | 0 [0,0] | 16 exact identities |
| L-O | -196.348728 [-239.231203,-153.466253] | -.062865667 [-.076540566,-.049190769] | 1 win,15 losses |

Intervals are the prospective descriptive paired t15 intervals over16 worlds,
not independent training replications or confirmation. O mean J/QoS is
2497.438199/.843097538; P and L are2301.089471/.780231870. The native arrays
shared by L and P, including proposals, submissions, rewards, trajectories,
guard/shield, battery, charging and service fields, are **bitwise identical in
all16 worlds**. This is stronger than a zero mean or an imprecise difference.

O exceeds the prospective one-percentage-point service and positive-J threshold
against P. Its specified additional-risk block is not triggered on this panel:
no cutoff/depletion in any arm; no O world has native battery at or below.10;
O's lowest battery is.105691988, versus P/L's.093057136. P/L has reserve exposure
in worlds01,06,11,13,16 and mean reserve UAV-step fraction.008119792, versus O0.
Final low-reserve member counts are7 in01/06/13/16 and1 in11 for P/L,0 for O.
**No arm has a member persistently below reserve for the full final300 steps on
this panel.** The motivating historical seven-member persistent tails are not
silently imported into these new worlds. P/L world03 ends in101 zero-service
steps; O03's longest zero spell is12 and no O episode ends at zero service.
O still has outages, including an81-step zero-service spell in world08; neither
zero cutoff nor an untriggered finite risk block certifies safety.
O lengthens the longest below-half-QoS spell in nine worlds (04/05/06/07/09/10/
11/12/16), even though that metric's mean improves. Mean first1000-step QoS is
.813165 for O versus.826905 for P; the largest mean gain occurs in the last1000.

World52192812 is the single joint counterexample: O-P J -41.997854 and
QoS -.014215728, with O2222.745104/.751436438 versus P2264.742959/.765652166.
O/P QoS over successive1000-step bins is .742423/.818205,
.822547/.844899 and .689340/.633852. Later recovery does not repay earlier
loss. O's battery minimum.121276 is higher than P's.101199 and it receives
935.127Wh instead of435.278Wh; more charge and better reserve are not monotone
service improvements. Both have17-step longest zero spells; O/P longest
below-half-service spells are86/81. These time bins are descriptive, not an
isolated causal diagnosis of the loss.

O-P raw return-constraint cost per native step averages -.001292038
[-.002283360,-.000300717], lower in15 worlds but slightly higher in14
(+.000011031). O receives413.182909Wh more charger input on average, has
356.312873Wh better total stored-energy change, and travels36478.433m more;
all16 worlds have each of those positive differences. Mean charger inputs are
801.655131Wh and388.472222Wh. No energy-balance or sustainability claim follows
from this finite, initially charged H3000 comparison.
Every O world still withdraws net stored energy,458.280..773.951Wh, mean608.822Wh.

### Choices, durations, execution and recovery

O has934 eligible macro clocks, makes145 voluntary commitments and retains
service at789 eligible clocks. There are6..11 commitments per world. All145
have an observed arrival, native allocated charging, later assignment restoration
and an actual F-free movement after release.143 later obtain positive connected
load; neither target restoration nor movement alone is called service recovery,
and absent load on two options does not diagnose a relay's lack of contribution.

O selects120/300/600 labels26/38/81 times. Releases are57 elapsed-dwell and88
full-battery, with no timeout or terminal censor. All81 nominal600 options end
full before600;54 still last more than300 elapsed steps. Thus a600 label is not
600 allocated charging steps, and many choices have a nonbinding duration.
Across O options, mean commanded duration is395.883 steps, mean elapsed time
after first observed geometric arrival297.131, mean allocated charging296.683
(range104..585), and mean native eligible waiting.455 (maximum23). Seven
allocation interruptions occur. Mean input82.340Wh, positive net charging
68.454Wh and total option battery change60.759Wh are distinct quantities;
all option battery changes are positive, minimum15.069Wh. There are no real-F
steps/entries during O options, station changes or overwritten dock commands.

Training has2484 genuinely eligible clocks across all64 worlds,1329 eligible
service choices and1155 sampled dispatches, all executed. The three duration
labels occur369/403/383 times, all eight members122..177 times. These observations
establish actual action exposure, not learning success or intended-duration
fidelity. Training option outcomes are735 full releases,352 dwell releases,
67 right censors and one `timeout_no_arrival` label.1142 options receive native
charging;1128 have a decoded observed-arrival event,1084 later restore assignment,
1085 show F-free movement and910 positive connected load. Mean allocation is
148.747 steps, waiting8.866 (maximum465), and there are459 allocation
interruptions. Mean input41.246Wh, positive net charging34.285Wh and option
battery change28.525Wh do not conceal the minimum -14.310Wh battery change.
398 observed options end before the shortest120-step label. This indicates
nonbinding duration in many observed outcomes, not counterfactual equivalence
of all labels; duration remains an actor input affecting future decisions.
No training commitment overlaps real F, changes station or has its command
overwritten. Actual activation and semantic limitations both matter.

The final L retains service at every one of1344 eligible evaluation clocks
(all1600 total clocks include256 forced service choices). Eligible service
probabilities are .518974..609036, mean.600290; the declared staged deterministic
gate therefore produces zero voluntary commitment. Gate entropy mean.672665 and
duration entropy1.097011 are not probability collapse. During training mean
eligible service probability is.550742, from exactly.5 initially to.614706 in
the final rollout;1155 sampled commitments are compatible with an endpoint mode
that never dispatches. Actor/critic L2 movements.100182/4.756783 and640 finite
post-clipping gradients show updates occurred, not why this deployment failed
to improve. No stochastic evaluation or gate/entropy repair is selected.

### Control-affecting arrival-boundary limitation

The compact reader retains17 training options with native allocated charging but
no observed arrival event. Each reaches a minimum decoded legal station distance
of **20.000001907348633m**, just above the controller's exact `<=20` predicate,
while native physical capture permits charging. These are14 full releases,
two terminal censors and one timeout. This is a **control-affecting semantic
limitation**, not just an unfortunate label: first arrival starts the dwell
clock, so missing it can prevent the declared elapsed-dwell release.

The concrete counterexample is training seed52092818, member4,120 label at1590:
it remains committed until2490,900 steps, receives580 allocated charging steps,
and is labelled `timeout_no_arrival`. That label is not evidence of physical
arrival or recharge failure. There are27 total training options without an
observed arrival;17 charged as above, while other cases include horizon limits.
All145 O evaluation options have observed arrivals, and no such mismatch;
L evaluation contains no option. I leave the accepted outputs and source
unchanged, including the misleading label, and explicitly qualify its reading.

Consequently O-P remains a complete comparison of the executed ordinary package;
L-P/L-O remain valid outcomes of this **as-executed** finite training/deployment
package. The intended geometric-arrival duration-learning experiment is
incompletely realized. Real exposure, parameter changes and successful updates
do not repair that missing semantic guarantee. The mismatch is not established
as the cause of L=P; neither a small affected count nor the large timeout permits
an unmeasured counterfactual conclusion. No epsilon patch, retry, replacement
fit or relabelled success is included in this study.

### Total scientific and engineering cost

The scientific cost is1 fit,64 training plus48 evaluation H3000 episodes,
336000 native transitions,6400 training macro transitions,160 PPO epochs and
640 optimizer updates (64000 minibatch sample exposures). Final-only endpoint
evaluation has zero optimizer updates. Actual service-snapshot calls are187205
in training and147394 in evaluation,334599 total, with no primitive forecast
rollouts. O/P evaluation calls are63528/41933; L equals P at41933. More frequent
available-team ordinary scoring after O commitments contributes real computation,
which native J does not charge. O/P summed worker CPU is1824.845/1573.811s,
about15.95% more for O, even though query count is about51.5% higher.

Runner wall is2900.052s (48.334min), of which training is1665.376s. Accepted
launch to the exit witness spans50.852639min including startup. Summed worker
CPU is11341.954s (3.15054h), plus8.130s parent CPU; the largest recorded individual
peak RSS is729020KiB, not aggregate memory. These coexist with the earlier
engineering cost of at least1525 native correctness transitions, up to150 more
from the interrupted handle, six four-step synthetic optimizer updates and the
recorded test/review work. Reading, implementation, failed control fetch,
collection and independent scientific review time were not fully metered.
There is no failed result-bearing fit to omit; the arrival/dwell limitation and
earlier test/transport/queue failures remain explicit costs and limitations.

### Independent scientific reading and DM disposition

The separate-context registered ResearchCritic
`/root/dm_persistent_service_round3/result_review` reconstructed raw evidence
before receiving my proposed interpretation. I supplied the actual question,
selection review, fixed source, original supporting/adverse sources and complete
current artifacts; no DM or Root turn history was inherited. This is independent
reasoning and reconstruction, not a blinded result reading. It performed no fit,
native rollout, edit or shared-index operation. Its full answer follows; the
absolute links identify the files at review time. Bulk paths are subsequently
bound to the canonical retained location in the retention entry below.

#### Full independent answer

**Recommend retaining O as a conditional central-information S7-S2/H3000 reference, stopping this PPO recipe, and purchasing no additional run now.** The DM's proposed disposition is supported, with the duration-control limitation below preserved explicitly.

No DM or Root conversation was inherited. The assignment supplied headline results, and index navigation exposed historical summaries, so this was separate-context review, not blinded review. I reconstructed the current raw evidence before receiving the DM's proposed diagnosis. I verified all 294 manifest files, read all 112 NPZ episodes, checked training choices and updates, and confirmed that P's source blob matches `025350669`. Historical counterevidence was checked through original world records and selected adverse raw pairs. No records, code or experiments were changed.

The complete comparison at source `981e935ee336cbdde3f3b69f229019384376ba5f` supports:

| Contrast | Mean native J difference | Mean QoS difference | Reading |
|---|---:|---:|---|
| O-P | +196.348728 | +.062865667 | Both improve in 15/16 worlds |
| L-P | 0 | 0 | Every common native array is bitwise identical |
| L-O | -196.348728 | -.062865667 | This deployed learned package supplies no increment |

O-P's descriptive paired intervals are `[153.466253,239.231203]` for J and `[.049190769,.076540566]` for QoS. These describe the sampled worlds; they do not provide independent learning replication. [Complete world records](/home/fires/hmasd-wsl/runs/uav_persistent_service/b01_commitment_a01/perworld.json).

O establishes a **measured achievable package increment** over competent P. Its 145 commitments all recorded arrival, charging, release, reassignment and subsequent movement; 143 subsequently recorded connected load. None timed out, remained censored or experienced real-F takeover during commitment. Thus useful discretionary commitment was physically realized. Connected load does not identify an individual member's delivered-service contribution, and zero takeover exposure does not demonstrate robustness to takeover. The comparison jointly changes admission, dwell, assignment availability and resulting service planning; it does not isolate any component.

The favorable means retain consequential limits. World `52192812` loses **41.997854 J and .014215728 QoS**. O lengthens the longest below-half-QoS spell in **nine worlds**, despite improving that metric's mean. Its mean first-1000-step QoS is lower; the largest gain occurs in the last 1000 steps. O has no observed <=10% reserve exposure, cutoff, depletion or terminal-zero-service world, while P has reserve exposure and one terminal-zero-service world. Nevertheless, every O world withdraws net stored energy, between **458 and 774 Wh**. This supports finite usefulness, not sustainability or general safety.

The learning result needs three separate judgments:

- **Opportunity and action interface:** O's result supplies a constructive useful policy within the shared commitment interface. It does not prove that the particular neural representation can recover O, or quantify optimal or learnable headroom.
- **Actual training:** all 64 worlds exposed eligible decisions. Training executed **1,155 commitments across 2,484 eligible clocks**, with 640 optimizer updates and parameter movement. Global nonactivation or an entirely inaccessible action branch cannot explain the paid training exposure.
- **Declared deployment:** L selected service on all **1,344 eligible evaluation clocks**. Its service probability ranged from **.518974 to .609036**, averaging .600290. The declared staged argmax therefore reproduces P even though substantial dispatch probability remains. This explains deployment nonactivation mechanically; it does not establish why training produced those logits. Near-zero critic explained variance and small policy changes are observations, not an identified optimizer failure. [Deployment rule](/home/fires/hmasd-wsl/experiments/candidates/uav_persistent_service/policy.py:38), [training evidence](/home/fires/hmasd-wsl/runs/uav_persistent_service/b01_commitment_a01/training.json).

**The strongest consequential qualification is that the arrival mismatch affects control, not merely event naming.** Of 27 training commitments without a recorded geometric-arrival event, 17 received native charging: 14 ended full, two were censored, and one timed out. Their minimum recorded decoded distance was `20.000001907348633 m`. In world `52092818`, member 4's **120-second choice remained commanded for 900 steps and received 580 allocated charging steps**. Arrival starts the actual dwell-release clock, so this mismatch changes the experienced duration. [Control condition](/home/fires/hmasd-wsl/experiments/candidates/uav_persistent_service/controllers.py:228), [original counterexample](/home/fires/hmasd-wsl/runs/uav_persistent_service/b01_commitment_a01/training/world_52092818.decisions.json).

Accordingly, the complete O-P comparison remains valid; L's as-executed finite package produces unchanged deployment; and the intended geometric-duration learning interpretation remains incomplete. Updates and executed commitments do not repair that semantic gap. All 145 O evaluation commitments recorded arrival, so the observed O benefit does not depend on these missed-arrival cases. Neither their frequency nor the counterexample identifies them as the cause of L=P.

Ordinary stopping rules also reduce duration differentiation: training had **735 full-battery releases**, including 364 with recorded dwell below 120 seconds. O's 81 choices labelled 600 all ended full; its 120 choices all ended by dwell. These are realized exposures, not counterfactual proof that alternative labels would always behave identically.

The earlier evidence remains relevant without becoming a universal failure story. Energy I lost to P on its own panel, including the verified 728-step terminal outage; the old learned move/hold ranking actively changed choices and lost to P. Current L instead leaves deployment unchanged. Those different observations cannot establish one shared learning failure or show that O repaired I's causal defect.

The investment correction is therefore concrete: **retain the ordinary asset and the empirical opportunity; end this learning recipe without stochastic-deployment rescue, detector-patch retry or automatic optimizer tuning.** A repaired detector would define changed execution semantics. The broader learned-scheduling question remains open, but no presently specified follow-up has demonstrated sufficient decision value.

The smallest worthwhile complete observation for the selected question has already been obtained. If a later concrete decision requires recurring O usefulness, a frozen O/P comparison on fresh complete H3000 worlds would address it: repeated gains with acceptable tails would strengthen conditional reuse; adverse or mixed results would narrow that preference. Neither outcome would establish learning capability. This is a contingent comparison, not a recommended run now.

Actual cost was **one fit, 336,000 native steps, 334,599 service snapshots**, 27.76 minutes fit wall and 48.33 minutes runner wall; acceptance-to-exit was 50.85 minutes. Summed worker CPU was **3.151 hours**. O evaluation used **15.95% more CPU** and 51.50% more snapshots than P. Sixteen future O/P pairs have a measured workload anchor of approximately **.944 worker-CPU hours**, before preparation and readback; future elapsed time remains unknown. Engineering, review, transport and publication costs are incompletely timed. Native J does not price those costs.

**MATERIAL_DISSENT: no.** The proposed stop-L/conditional-O disposition matches the direct evidence, provided the control-affecting duration mismatch, adverse service tails and single-training-instance scope remain substantive parts of the retained result.

#### DM disposition

I accept that recommendation and its qualifications. It corrects the tempting
reading of O as optimal/learnable "headroom" to a measured achievable complete
package increment. Native guard/geometry did not exhaust all useful discretionary
control under this exact central-information interface; nevertheless O-P does
not isolate departure timing, occupancy, duration, reassignment or any diagnosed
charge-cycle defect. Its early-service and nine-world below-half-service tails
and universally negative stored-energy balance remain part of the judgment.

The direct learner's actual training was not globally inactive, while its
specified deployment is exactly inactive relative to P. These observations do
not identify why its logits favored service. The control-affecting decoded
arrival error prevents a clean negative conclusion about intended geometric
duration learning; the negative is this one as-executed package. A future detector
change would be new execution semantics, not completion of this already collected
batch, and exposure/update counts cannot substitute for that distinction.

The chosen next action is **stop this PPO recipe; retain O as a conditional
S7-S2/H3000 central-information ordinary reference; put the broader question in
reserve with no new producer**. There is no pending fit, result collection,
external advice or owner-approval dependency. One fit and16 evaluation worlds do
not support confirmation, learning impossibility, decentralized legality, default
safety or sustainable repeated service. Previous I/C, move/hold-learning and
lawful-controller adverse evidence remain binding in their original scopes;
this result neither renames those recipes nor retrospectively diagnoses them.

A concrete future reuse decision could make fresh frozen O/P replication worth
its full cost, and a substantively different learning comparison might be worth
proposing if it changes an unresolved decision. Neither is selected now. A
numerical repair, stochastic evaluation, extra seed/epoch or automatic entropy,
reward or optimizer revision is not this direction's next task by default.
Cross-question proposals return to Root; publication and cleanup below are my
remaining in-scope work. No additional selection critic or Pro round is needed
for this uncontested, independently read disposition.

### Publication, retention and measured cleanup

The complete result, full independent answer and own RESEARCH/background standing
were published and verified at `origin/main` in
`ad55c6e43fdbd38bf78abc42f9e48e762535b357`. Root subsequently read the full answer
and compact records and adopted conditional-O/stop-L, with no additional run.
This acknowledgement was not a prerequisite for my publication or cleanup.

The one canonical bulk copy is now on `wsl_4070` at
`/home/wu/hmasd-artifacts/uav_persistent_service/b01_commitment_a01/`.
Only `raw/`, `training/`, `initial.zip` and `endpoint.zip` were moved there from
the completed native output, without a symlink or changed in-flight binding.
All290 bulk files,324956354 bytes, were reverified against the original runner
manifest. Its SHA256 is
`b351ed14cadb62bf20a7a71c659bc6841c6f9f7ee636f26d05f007a86c9ff7f7`;
bulk relative paths resolve under this canonical root, while the four compact
manifest entries remain in Git and the original native output. Together these
preserve all294 files originally verified. The endpoint is2896988 bytes,
SHA256 `12375027e5a806c3ab205626aaf8401d3f04cfd0f5fc9e1254784a7dc8552493`;
the initial checkpoint is986822 bytes,
SHA256 `c03e59d046e308a20b787abc5a8e403e8d3cae821b8b6638760b025b0154d2a6`.
These two endpoints, training/decision/gradient evidence and all original native
arrays support the specific exposure, unchanged-deployment, ordinary-package
and arrival-mismatch readings. They are not an unselected continuation or a
chain of backups. Compact native claims, manifests, stdout/stderr, exit/status
and scientific summaries remain at the original output path for recovery and
duplicate prevention; claim/manifest/source identities were not rewritten.

Before deletion I checked completed worker/observer status, read-only helper
completion, imports, tests and current entrypoint consumers. No other direction
imports this direction, and no live result or review consumer remained. Useful
ordinary `controllers.py`, native evaluator, passive mechanism/readout code,
constants, checkpoint policy class and controller tests remain on main. The
retained policy class permits reading the exact stored learned checkpoint; it
does not authorize retraining. The ended `batch.py`, `training.py`, `run_b01.py`
and `test_pipeline.py` were removed from the current tree. Their exact executed
versions and all14 input tests remain at
[source981e935ee](https://github.com/CartmanFatass/My-paper-code/tree/981e935ee336cbdde3f3b69f229019384376ba5f/experiments/candidates/uav_persistent_service)
and its matching tests. No detector repair was made. A final import/collection
check collects the five retained controller tests in1.89s; it executes zero
native steps/optimizer updates and does not replace the original14-test run.
There are no references to the retired modules from current executable callers.

Actual deleted targets are the local duplicate `runs/uav_persistent_service/
b01_commitment_a01/{raw,training,initial.zip,endpoint.zip}`, local
`temp/directions/uav_persistent_service/`, the two direction code/test
`__pycache__/` directories, the four retired source/test files above, remote
`/home/wu/projects/HMASD/temp/directions/uav_persistent_service/`, and the
launcher source snapshot
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/014187470de74ecf8da122a04d9baf31`.
The supported exact-snapshot collector first refused because `/proc/660/cwd`
was protected. Retrying its documented read-only process probe with existing
passwordless `--sudo-process-scan` gave an eligible preview; apply rechecked
terminal/source/durable-ref/clean-file conditions and removed only this snapshot.
The refusal is preserved here; it did not require changing any peer process,
claim, output or Git history. The original auto-GC warning was not repaired.

Allocated-byte measurements include the canonical bulk destination, so moving
data is not counted as reclaiming it:

| Host and exact owned scope | Before | After | Net freed |
|---|---:|---:|---:|
| Local code/tests/run/scratch directories | 326852608 | 983040 | 325869568 |
| Remote snapshot/original output/scratch plus new canonical direction directory | 1127063552 | 326430720 | 800632832 |
| Total | 1453916160 | 327413760 | **1126502400** |

All eleven local deleted targets and both remote deletion targets were checked
absent. The canonical bulk store remains intentionally,325681152 allocated
bytes including the new direction directory; compact native output remains
749568 bytes. No blocked cleanup target, open observation, active producer,
unread result, pending advice or selected new experiment remains. Unrelated
writers' source, untracked files and accepted operations were preserved. This
is a measured working/output-filesystem reduction, not a claim about Git object
pack size or total host free space.
