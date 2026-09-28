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
