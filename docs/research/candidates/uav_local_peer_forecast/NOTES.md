# Lawful local peer-motion forecasting

<a id="design-scope-20260930"></a>
## 2026-09-30 — Assigned question and design scope

Root assigned the new native DM `/root/dm_local_peer_forecast` the scientific
design question: can lawful anticipation of currently visible teammate motion
improve competent decentralized `LocalController(history=False)` under the same
N5, all-on, H256, 27-command, four-tick commitment contract? Root registered the
active direction and actual Astra Max runtime at
`062d04bc8b3e07c534e72facebe7f27b62d604d4`. This assignment has **0 new fits,
0 native evaluation, and no selected result implementation or launch**. The
deliverable is a source-grounded complete prospective comparison and its full
cost for Root's investment choice. No CLAIM or confirmation is selected.

The consequential unknown is whether observed previous motion predicts a useful
part of the *next jointly chosen command block*. Estimating a past velocity is
not the same as knowing that command. The intended first contribution is a
conditional ordinary-control capability or empirical boundary on this host,
not a new prediction algorithm, a necessary-learning claim, or an obligation to
obtain a positive result. Root's existing separate-context Oracle
`/root/deep_report_review` owns the ongoing independent construction/challenge;
this DM owns actual interface feasibility, prospective law, comparison and cost.
No second ideation/critic round or Pro send is commissioned here.

Ownership is limited to this direction's implementation/tests, this notebook,
future runs and scratch paths on shared main. The existing local-C development,
local-C inheritance, N8 silent-repositioning and Claude studies retain their
writers, interfaces and accepted inputs. Root's actual selected scope permits
design and source reading; no native operation has been adopted or created.

### Published background used in this design

Read current published RESEARCH at `062d04bc8b3e07c534e72facebe7f27b62d604d4`:
[topic 2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练),
[topic 5](../../RESEARCH.md#5-技能和异步性是组织决策的方式其收益需要证据), and
[topic 8](../../RESEARCH.md#8-数学信息与博弈结构怎样帮助dm选择实验).
Topic 2 supplies competent C and the adverse local-history results: lawful
history or activated decisions do not by themselves establish complete value.
It keeps absent-user caching out of this intervention. Topic 5 retains the
message-content B04 forecasting capability alongside its native losses; more
accurate forecasts do not establish beneficial coordination. Topic 8 locates
the proposed intervention in a legal history-dependent policy's approximate
transition model, with endogenous simultaneous teammate actions still unknown.
It motivates reading complete native J/service and action exposure together.

The original Oracle proposal is preserved in
[the completed fourth-question review](../../archive/2026-09-30/RESEARCH-silent-reserve-repositioning.md#full-independent-oracle-answer),
source `7bb778764d4de030179f9b4d06681c35073fb372`. Its two-program cost of
16,384 native steps and 2,211,840 model ticks is only the candidate-own-motion
count; association, peer power, reading and engineering were explicitly not
priced. The present design must complete that accounting before investment.

The actual C contract and prior selection are also documented in
[ordinary-parent design](../uav_parent_adaptation/NOTES.md#ordinary-parent-design-20260930).
This direction does not inherit that learner or its three selected fits. The
completed waiting B02 [reading](../uav_user_waiting/NOTES.md#b02-complete-reading)
is a different registered-map, delayed-service-history host; its accurate
98-tick adverse witness neither diagnoses missing history here nor refutes
anticipation generally.

### Initial source reconstruction

Sources read through CodeGraph and the uncovered exact method ranges:
`experiments/candidates/uav_local_history/b01/controller.py`,
`experiments/candidates/uav_local_history/b01/study.py`,
`experiments/candidates/ucope/uav_motion_prefix_b01/environment.py`,
`envs/pettingzoo/uav_env.py`, and `envs/pettingzoo/uav_radio.py`.
No source file has been edited or executed for a result.

C receives only a copied 104-value local row plus the primitive clock; it scores
27 own trajectories of four componentwise-clipped ticks, takes the first maximum
in squared-command-norm/lexicographic order, and uses its private ten-waypoint
sweep when every predicted service count is zero. All five actors replan at
the same `t % 4 == 0`; intervening observations are available but cannot change
the held command. The current native radio has 3 dB eligibility, capacity 10,
23 dBm transmit power, -80 dBm noise and 2 GHz free-space propagation. Native
J is `.7*served/50 + .3*connected_quality`, without an altitude term or message
fee. Current C's proxy sees only its visible-user subset and visible peers.

Peer rows are anonymous relative xyz plus normalized SINR, zero padded to ten;
at N5 there are at most four actual peers. Native `_local_uav_entries(i)` sorts
row `uav_sinr_matrix[i]` descending, stable at ties, with threshold 3 dB. The
matrix is **[sender, receiver]**: the row is own transmitter to peer receiver
SINR. It is not a set of signals received at a single receiver, and the usual
one-decodable-transmitter argument therefore does not limit it to one peer.
Row rank is not an identity. Recover each peer's absolute position from the
same row's own position before temporal differencing; relative differencing
without own-motion correction is invalid.

At a decision boundary the displacement from `t-1` to `t` was generated by the
previous block. Every peer selects a new block simultaneously. Neither the
known physical transition nor correct association makes old-velocity
extrapolation a known future trajectory. New/missing peers, ambiguous
association and boundary-clipped motion need a fixed fallback law. The full
contract, predicted outcomes and costs are developed below before selection.

<a id="lawful-interface-20260930"></a>
## 2026-09-30 — Exact local interface and forecast feasibility

The following are source facts and a proposed lawful implementation contract,
not a result or selected code task. At the published registration revision
`062d04bc8b3e07c534e72facebe7f27b62d604d4`, the relevant Git blobs are:

| Source | Git blob |
| --- | --- |
| `experiments/candidates/uav_local_history/b01/controller.py` | `9c98f540f74e4d4605dce84a797e6b932cd9cb50` |
| `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py` | `4b59281bfb76245dd3283fe860327e35463c2b26` |
| `envs/pettingzoo/uav_env.py` | `1e67c3a56fc1824db968485366dadcc54c7d8125` |
| `envs/pettingzoo/uav_radio.py` | `cf7cdbf3562e78e41bc06d32f733e806d7190313` |
| `envs/pettingzoo/env_adapter.py` | `58da35c3263e00319d90b93169a6d14b0f7e5bda` |

C and the factory retain the old B01 bytes, but native radio extraction and
transmitter masking were added after B01. Bind the current all-on source for
every new arm, verify its exercised semantics during engineering, and do not
call the historical score a reproduction on identical environment bytes.

### Observation, clock and physical law

The factory sets five UAVs, 50 static uniform users, 1,000 m square, altitude
50–150 m, component speed 30 m per one-second tick, H256, free space, no
shadowing, no FDMA, no paper reward and no enabled transmitter mask. All radios
stay on. An action is a three-vector in `{-1,0,1}^3`; diagonal speed is not
Euclidean-normalized. The environment adds `30*command` on every coordinate,
clips x/y to [0,1000] and z to [50,150], then recomputes radio, connections and
reward. There is no acceleration, collision, battery, message, service-ACK,
altitude-penalty or travel-cost term in this contract. Movement is nevertheless
a reported physical consequence, not free energy or a safety result.

The 104-entry FP32 row is:

| Entries | Lawful content |
| --- | --- |
| `[0:3]` | Own x/1000, y/1000, (z−50)/100. |
| `[3:63]` | 20 anonymous user triples: relative x/1000, y/1000, clip((current own-link SINR+10)/50,0,1). |
| `[63:103]` | 10 anonymous peer quadruples: relative x/1000, y/1000, z/100, clip((outbound peer-link SINR+10)/50,0,1). |
| `[103]` | Current primitive tick / 256. |

Both lists include links with native SINR at least 3 dB, sort descending by
SINR and retain native stable index order at an exact tie. Users are capped at
20, peers at ten (at most four exist here); absent rows are all zero. A positive
last field identifies a populated row because eligible SINR is above the
normalization floor. Row rank can change at every tick and is not an ID.
The peer SINR field supplies visibility/ranking, not velocity, a command, or
another actor's private state. The policy never receives native entity-index
lists, `state_info`, the environment, evaluator associations, or another UAV's
observation. The evaluator may use those only after recording the action.

Five fresh private policy instances are constructed at each reset. The collector
supplies consecutive integer clocks 0..255, one copied row per actor per tick;
the clock matches row[103]. Duplicate/skipped clocks are an interface error,
not an invitation to extrapolate through missing time. Terminal row t=256 is
recorded for checking but causes no new action. At t=0,4,...,252 all five actors
select simultaneously from their own pre-step data. The selected vector is
held on the following four native transitions; observations at interior ticks
may update private history but never interrupt the command. No decision sees
the current round's other commands.

### C's actual decision, calibration and limits

C replaces its current user list each tick. It has no absent-user geometry.
Its persistent behavioral state is its own held command and sweep-waypoint
index; the ten waypoint coordinates and physical radio parameters are known
algorithmic knowledge. At each decision, C predicts all 27 own commands for
four ticks by repeated componentwise clipping. Commands are ordered first by
squared norm and then by the `(x,y,z)` tuple. It averages the four modeled
`.7*served/50 + .3*quality` values and picks the first maximum in that order.
Model service uses the current visible users only, eligibility 3 dB and top-ten
links per modeled transmitter; quality is clipped `(SINR−3)/30` averaged over
those selected links. Because 3 dB is greater than 0 dB and all denominators
include the other active transmitters, two modeled transmitters cannot both
meet threshold for the same user. The local cap rule therefore has no
double-assignment problem within that subset. It still omits users visible
only to other actors, their capacity occupancy, and undiscovered users.

For each current user u, let `P0(u)` be own current power and `Pj(u)` the current
power from each visible peer. C infers an aggregate unseen-peer term

`U(u) = max(P0(u)/10**(SINR_obs(u)/10) − sum_j Pj(u) − noise, 0)`

when fewer than four peers are visible, and sets U=0 when all four are visible.
This uses the current observed user SINR, with power in mW and noise `1e-8` mW.
It is not a reconstructed hidden-peer position or identity. C holds U fixed at
each static user during the four predictions. For each future candidate it
uses own candidate power plus visible peers' modeled powers and this same U;
the denominator for a modeled transmitter is the sum of *other* modeled
transmitter powers + U + noise. The known visible contribution must be
subtracted once when calibrating U, then included once at its forecast location.
Do not freeze total interference and add predicted peers a second time, or
recalibrate U at candidate locations in a way that cancels the intervention.

For a moving-peer proposal, all current calibration remains exactly C's. Only
the future positions/powers of qualifying currently visible peers change.
Unseen interference is still constant, unknown users remain absent, and peers'
responses to our hypothetical candidate action are not simulated. Forecasting
geometry can improve or worsen this incomplete local score; it is not global
J prediction or a joint best response. If all candidate modeled service counts
are zero, preserve C's sweep: initialize to the nearest waypoint, advance one
cyclic waypoint when within 60 m, and choose the command whose four-tick endpoint
is nearest that waypoint at altitude 50 m. Both distance ties and score ties use
the existing first-index rules. The waypoint mutates once per actual fallback
decision, never from a diagnostic scorer.

### Anonymous two-frame association and numerical invariants

At every tick decode each populated peer into absolute xyz using the *same*
row's own xyz and scales `(1000,1000,100)`. For current row a and previous-tick
row b, form the componentwise gate
`all(abs(xyz_t[a]−xyz_(t−1)[b]) <= 30.001 m)`.
Accept a pair only when its row and column each contain exactly one feasible
pair. This deliberately abstains on ambiguity rather than solving a forced
nearest-neighbor assignment. It is invariant to row permutations, including
SINR sorting changes, and never uses SINR rank as identity. At N5 this is at
most 16 candidate pairs per adjacent-frame update.

For an accepted pair, let delta be the own-corrected one-tick displacement,
replace each component with absolute value below .001 m by zero, and clip each
remaining component to [-30,30] m. The .001 m tolerance is numerical protection
for FP32 coordinate reconstruction, not a data-tuned motion threshold. A pair
is moving only if its resulting vector is nonzero. Startup, new appearance,
ambiguous association or an absent immediately preceding observation gives
zero velocity. Missing peers are removed from the represented set immediately;
there is no extrapolated invisible track or resurrection from older history.
They remain part of the aggregate U term at current users. A reappearing peer
starts without a velocity unless a unique immediately preceding pair exists.
Reset clears frames, clock, counters, held command and waypoint together.

For a moving peer and a prospectively fixed forecast direction, advance four
times by the forecast displacement with the same componentwise native bounds.
Its actual prior command cannot in general be recovered from a clipped last
displacement. At a renewal even a correctly recovered old command would not
reveal the new command. Do not infer a target, full policy input, commitment or
stationary hidden agents from these two frames.

**Exact inactive behavior matters.** If every peer has zero/default velocity,
use C's unmodified stationary scoring path and unmodified decoded coordinates.
Blind clipping of a stationary FP32-derived coordinate can change C by tiny
roundoff near a boundary. In a mixed set, retain C's present power for each
stationary peer column and clip/recompute only moving peer columns. At n=0
both policies take C's identical empty-score/sweep path. Association history
still updates, but neither an unmatched peer nor a no-user event is a scored
forecast intervention. These invariants are proposed focused engineering
checks, not a positive-result or native-pilot requirement.

### Why better geometry is not yet a value claim

At a renewal, `delta_(t−1,t)` describes the old command block. For an unclipped
peer, a continuing command would make constant velocity accurate; a stopped
command makes stationarity accurate; a reversed command makes persistence err
by `2*k*delta` at lead k while stationarity errs by `k*delta`. This elementary
counterexample changes the forecast comparison before any new outcomes. Native
clipping and private local decisions further complicate it. It does not prove
which branch C or a new forecast policy takes, or whether those position errors
change the chosen own command.

The primary local-library bridge read here is **MARL-0016**, Wu et al.,
*Models as Agents* (AAAI 2023), structured primary text
`/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0016.json`, PDF
`/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0016.pdf`, pp. 2–4.
**DIRECT:** their model-learning formulation conditions on joint observation
and action, assumes that joint input suffices for next joint observation/reward,
and discusses prediction errors interacting with the current joint policy.
**INFERENCE for this design:** those assumptions cannot supply the missing
teammate inputs or new commands to our single-row actor; changing all actors'
forecasts changes the trajectories being predicted. Their framework motivates
checking complete behavior, not importing a return guarantee, MAG machinery or
extra information. No novelty claim is based on a library search miss. Root's
existing Oracle is completing the broader three-store and primary-web reading
for this same selection, without another delegated review here.

<a id="development-evidence-20260930"></a>
## 2026-09-30 — The inherited evidence changes the forecast hypothesis

The existing Oracle independently read all 32 original C trajectories in
`runs/uav_local_history/b01_censor_search_a01/raw/`, verifying each against
the original summary-bound SHA256. This is read-only development evidence from
already paid episodes, **not a V or R native evaluation**. The full independent
selection answer and its source locator are retained below when returned.
The final numbers use the exact .001 m snap and [-30,30] component clipping;
an earlier preliminary tally of 161 CV-worse pairs used different endpoint
arithmetic and is superseded by 160. No new score was used to choose a forecast.

Across 10,240 C decision-agent events there were 1,616 with a visible peer:
8,624 had none, 1,613 had one and three had two. At decision boundaries the
mutually unique adjacent-frame gate accepted 1,345 peer pairs in 1,342 events;
all were truth-correct in the evaluator audit. This demonstrates feasibility
on those old traces, not a general anonymous-association guarantee. Of those
pairs, 242 moved; only 241 decision events had a moving pair. Only **109
events also had current users**, the necessary direct opportunity for changing
C's radio score. Those events span 20/32 worlds, with 64 concentrated in
worlds 07 and 22. Unknown peer and visibility patterns on the new policy's
own paths remain unknown.

The four-tick location-error reading supplied by the Oracle is adverse to the
original persistence rationale: over all 1,345 pairs, stationarity is 14.218548 m
and clipped CV is 19.044305 m; over the 242 moving pairs, 74.865924 versus
101.686762 m. The decision-relevant 109-event slice is more adverse:
**78.932324 m stationary versus 139.200707 m CV**, with 15 CV-better and
91 CV-worse pairs. Only nine preserve the previous command, ten next stop and
**68 exactly reverse it**. These descriptive old-trajectory quantities are not
native control effects; their exact error aggregation and remaining patterns
belong to the full Oracle answer, not an invented population confidence interval.

This changes the constructive conjecture from unqualified persistence to
**anticipation of synchronous reactive reversal**. C's four-tick greedy update
can overshoot a useful configuration, and its next block can reverse. That is
a plausible explanation of the observed pattern, not a diagnosed cause of
every reversal or a rule guaranteed by the source. A fixed reversal forecast
has an opposite falsifiable prediction to CV. All five actors adopting either
forecast can alter or destroy the old C pattern, which is precisely why a
complete native comparison is still informative and an offline accuracy
screen cannot decide deployment value.

The same independent review therefore revises its earlier provisional C/V
recommendation to **one C/V/R complete comparison**, with C primary, V the
ordinary persistence control and R the reversal conjecture. This is not an
after-result sign sweep: the old 32 C worlds are explicit selection exposure,
the new panel is fixed before its outcomes, and both competing forecasts are
retained rather than choosing the best sign afterward. No interpolation grid,
learned predictor, online fit or extra pilot is proposed.

The earlier message-content B04 adverse is retained at its actual scope:
[complete reading](../uav_message_content/NOTES.md#b04-complete-reading), source
`7bb6d2f8eedecd7479fc4cb830467b8c6601a5ec`. Its learned forecasts of the sender's
own future endpoint used a 40-byte delayed RR channel, private GRU/current
policy-center inputs, primitive control and co-adapting PPO. Its qualified
ordinary comparator kept the known sampled first command then persisted the
policy-center command; sampled-command-only persistence was much worse.
Learned horizontal error improved in every continuation, yet F−O mean J/service
was −.009810/−.720988 with mixed continuation signs and wide intervals.
This makes competent ordinary prediction and full native reading essential,
but it neither measures two-frame anonymous peer prediction nor proves that
the proposed R is useful or that learning should repair CV.

Root also supplied a **provisional** new local-C inheritance result during
design: final sampled policy reportedly improves mean J/service over C, while
memoized C is faster and the independent result disposition is still pending.
No checkpoint, result comparison or new learning work is inherited here. That
capability may alter Root's portfolio priority after its full publication; it
does not replace unchanged C for this component/package question or justify
adding an unreviewed learned arm to the fixed proposal.

<a id="complete-proposal-20260930"></a>
## 2026-09-30 — Complete prospective C/V/R comparison for investment choice

**Recommendation under the single independent review:** a small complete
ordinary-policy comparison is defensible despite the adverse persistence
evidence, provided implementation remains local and the conclusions remain
conditional. Root has selected design work only; the following is a fixed
proposal, **not launch authority or a started batch**. Independent advice,
the DM's final disposition and publication are recorded below. A later result
selection must preserve this exposure or append an explicit changed proposal
before implementation/execution. There is no training component or CLAIM.

### Three complete decentralized programs

| Program | Peer forecast used in C's otherwise unchanged four-tick score |
| --- | --- |
| **C** | Original `LocalController(history=False)`, visible peers stationary. |
| **V** | Qualified adjacent-frame displacement `+delta`, constant for the next four ticks with sequential native clipping; zero/default peers retain the exact C path. |
| **R** | Qualified adjacent-frame displacement `−delta` at the simultaneous renewal, constant for the next four ticks with sequential native clipping; all qualification and inactive behavior identical to V. |

R is a phase-aware ordinary reversal conjecture, not a prediction of a disclosed
peer command. Its sign is fixed for the study. All five UAVs use that arm's
program, each with private state. Both V and R update the same two-frame local
history on all primitive ticks; the signed forecast affects scoring only at
the common renewal. They use no higher cadence, additional users, messages,
hidden history, future labels, training critic or evaluator truth. C is allowed
the same native observations at the same cadence; V/R differ by using lawful
past observations that C currently discards. This is better use of the same
observation contract, not identical representation or inference cost.

C is a competent relevant ordinary comparator: full 27-command, four-tick
radio planning with current-SINR calibration and its sweep fallback. It is
stronger than a stationary *actor*, one-step/no-radio rule, or zero-action
baseline. V is the natural ordinary motion-persistence control for R, and the
old source/data make its contrary prediction consequential. Registered-map
radio activation and public-global-state N8 C/E/J have different rights and
objectives. Local-history H is a paid conditional capability with mixed means
and tail losses, not an established universally stronger current-state method;
adding its absent-user map would confound the present increment. The new
ordinary-C learner and inherited neural asset are separate complete learning
investments, not mandatory new arms here. No third forecast module, arbitrary
shrinkage grid, robust reachable-set enumeration or learned dynamics is needed
to answer this finite question. Such alternatives remain separate investments
if a future useful observation actually motivates them.

The proposed evaluator uses **32 fresh matched worlds, seeds 29401000 through
29401031 inclusive**, one H256 episode per program and seed. A literal-number
search of current direction notes/code and run config/summary files found no
existing use of this seed range; actual initialized arrays must still be
checked for within-world equality and between-world distinctness. Each seed
is reset separately in each arm. Execute worlds in ascending order and rotate
the complete order `(C,V,R)`, `(V,R,C)`, `(R,C,V)` by world index modulo three.
One factory construction may precede 96 explicit episode resets; its unscored
reset is charged separately. All episodes stop at H256, with no checkpoint,
endpoint, world replacement, tuning split or post-outcome arm selection.
Three-way identical initial geometry and four-tick native prefixes are required
by the law. Technical failure retains incurred work and missing status; it is
not a negative/zero cell or authority for automatic retry.

### Constructive prediction, native reading and alternatives

The constructive prediction has two separate parts. On decision events with
current users and a moving, unambiguously associated peer, R should better
represent the next block than V when the old C-like reversal pattern survives.
Its changed interference/service ranking may then avoid a harmful own motion
or choose a useful one, improving **full-episode native J and service over C**.
The old data make persistence a credible adverse alternative rather than an
owed improvement. They do not establish the frequency, accuracy or relevance
of reversal on any new arm's endogenous trajectory.

Read R−C as the primary forecast-package comparison, V−C as the ordinary
persistence comparison, and R−V as the difference between these competing
lawful hypotheses. For each retain the complete 32 signed world differences,
mean, median, min/max and positive/negative/exact-equality counts. Give
descriptive paired two-sided t95 intervals with df31 for full-episode mean J
and served users/tick, with worlds as the units for these fixed deterministic
programs. These are exploratory distribution summaries, not training
replications, multiplicity-adjusted confirmation, equivalence or calibrated
posterior confidence. No result is selected by whichever contrast or metric
looks best.

Always retain full-episode connected quality, per-world minimum and p10 service,
zero-service ticks and longest zero-service streak, mean per-UAV path length,
altitude/boundary exposure and actor/model/reader costs. These characterize
tradeoffs; they are not an invented physical-safety requirement or post-hoc
adoption gate. A joint favorable J/service mean can preserve a conditional
capability, with its uncertainty and every adverse world; it does not authorize
a default policy, another panel or a learning fit. No universal minimum effect
or confirmation decision is invented for this exploratory comparison.

Keep the following outcome implications prospective:

- **R improves C and V in complete J/service:** retain the measured conditional
  ordinary anticipation capability. Reversal-consistent error/exposure helps
  explain it but does not prove mediation, global dynamics identification or
  a need for learning. Root may separately consider a consequential extension.
- **V improves C while R fails:** preserve persistence's actual native value
  despite the adverse old slice; the development reversal conjecture did not
  transfer to this complete deployment comparison.
- **Both improve C:** keep both complete capabilities and their cost/tail
  differences. This does not isolate forecast accuracy rather than altered
  exploration/closed-loop trajectories as the cause.
- **R exceeds V but fails against C, or either trades J against service/tails:**
  report the narrower prediction or task tradeoff; do not rename a relative
  win as complete improvement or discard adverse components.
- **Lower forecast error, changed rankings/actions, but no native gain:**
  weaken the proposed conversion from geometry to complete use. Do not
  automatically fit a predictor or repair calibration/association merely
  because the package lost.
- **Sparse or no scored/action exposure:** retain the whole panel and the paid
  work. This limits this policy's opportunity under this fixed host; it is not
  evidence that actively used anticipation is harmful or that MARL prediction
  is impossible. Do not filter to active worlds or append an opportunity hunt.
- **Broadly adverse or uncertain complete outcomes:** retain signed evidence
  and end this fixed batch. The broader question is unresolved; another
  investment would need a new discriminating reason and comparison, not a
  renamed sign, threshold or seed search.

### Saved-data reader and separation from actor computation

The worker stores one compressed trajectory per arm/world with all local rows
including terminal observations, actual commands and positions, initial static
users, native reward/service/quality, selected candidate indices and scores,
pre/post navigation state, and association/motion/fallback/counter telemetry.
Native connection or served-user telemetry is evaluator data only. Hash all
raw artifacts and bind them to the compact config, source manifest, summary and
status. Full arrays stay in the one durable run `raw/` location; compact
per-world results, counts, signed contrasts, source identity and reader output
are published in Git. No second evidence copy or neural checkpoint is needed.

An independent pure saved-data reader must reconstruct initial pairing, all
native movement and clipping, held clocks, radio/visibility/sorting, connections,
J/service/Q and the local input contract. It independently reconstructs each
program's actual association, qualification, future power, score, selection,
fallback and waypoint evolution. It must not call the candidate scorer as its
proof. Scalar reference cases and declared vectorized arithmetic are appropriate;
there is no new native environment step, suffix replay or evaluator policy call.

On every V/R decision, additionally compute **stationary C scores on that exact
local input and that actual program's entering waypoint state**, without
mutating either policy. The alternate fallback may calculate its own tentative
waypoint solely for that choice, then discard it. This answers whether the
forecast changes the current ranking/action, not what a separately running C
would have done after a different history. Report score-vector perturbation,
argmax/selected-index disagreement and whether the two held commands produce
different physical four-tick own paths. Distinguish command aliases caused by
native clipping. Evaluator truth may check that last physical mapping but
never choose or gate the live action. No extra V↔R scoring branch is needed;
the complete R−V panel already buys that package contrast.

For each program's recorded path, compute stationary, +delta and −delta
position-error shadows at each lead 1..4 for the currently visible peer rows.
Report all rows and the fixed nested descriptive slices: uniquely matched,
moving matched, moving matched with current users, and actual score/action
changes. Report missing/ambiguous/default rates and evaluator-checked accepted
association errors. Future identities/positions are used solely to score these
saved predictions after the episode; never to validate a live match or select
the forecast. Native joint command persistence, stop and exact reversal are
also offline descriptions, not lawful policy inputs or causal explanation.
No native endpoint is conditioned on these future-defined slices.

Within the reader, reuse a decision's own 27 trajectories, own powers and
current calibration between the actual and stationary score. This is declared
verification reuse, not a deployment speedup. The worker makes **no online
stationary shadow call**. Report controller-only CPU plus complete process
CPU/wall/RSS/I/O separately from independent reading and engineering. C's known
exact memoization and the current inheritance study are stronger ordinary
compute alternatives; comparison to unmodified C here supports no fastest-
controller or amortization claim. There is no outcome-driven caching rewrite.

### Full prospective cost, not only a zero-fit label

Let D = 32 worlds × 5 actors × 64 renewals = 10,240 decisions per program;
each program ingests 40,960 rows. At a decision let n≤20 be current users,
p≤4 visible peers and m≤p qualifying moving peers. These formulas count
requested work before any declared exact reuse, not measured runtime:

| Worker work | Fixed count or conservative ceiling |
| --- | ---: |
| Started fits / optimizer calls / new training labels | 0 / 0 / 0 |
| Complete episodes / native team steps | 96 / 24,576 |
| Actor row ingests / actual rankings | 122,880 / 30,720 |
| Own candidate trajectories / candidate model ticks | 829,440 / 3,317,760 |
| Adjacent-frame updates in V and R | 81,600 |
| Pair gates in V and R, each testing three coordinates | ≤1,305,600 |
| Extra moving-peer propagated ticks in V and R | ≤322,560 |
| Own candidate + current setup powers, sum of `(108+1+p)*n` | ≤69,427,200 |
| Extra moving-peer powers, sum of `4*m*n` outside t=0 | ≤6,451,200 |
| **Total controller station–user power values** | **≤75,878,400** |
| Logical candidate SINR values, sum of `108*(1+p)*n` | ≤331,776,000 |
| Logical transmitter/user-list sorts, each of length ≤20 | ≤16,588,800 |
| Native episode-initial + post-step radio states | 24,672 |
| Constructor's additional unscored radio state | 1 |
| Native dense link/path-loss/power slots, `(250+25)` per state | 6,785,075 |
| **Controller + native power-slot ceiling** | **82,663,475** |

The extra peer bound excludes each episode's startup renewal, where no temporal
pair can exist: `2*32*5*63*4*4` propagated peer ticks. Zero velocities and n=0
need no new peer powers. Native dense calculations include the five diagonal
UAV matrix placeholders that the implementation computes before zeroing;
there are only 20 physically nonself directed peer links. Thus 96×257×270 =
6,661,440 is the physical nonself link count, while 6,784,800 is the scored/reset
dense-slot count. The constructor adds 275 dense slots. These slot counts do
not mean the two matrices consume identical CPU work. Native radio reductions,
greedy assignment, observations, copies, imports, initialization, compression
and summary writes are all part of measured worker cost, not omitted work.

The independent reader reconstructs 30,720 actual rankings plus 20,480
stationary C shadows on V/R paths: **51,200 score requests and 5,529,600 logical
candidate model ticks**. It may share own trajectory/power/calibration *inside
one recorded decision* between its actual and stationary branch. With that
declared reuse it needs no more than the worker's 75,878,400 controller power
values plus 6,784,800 native reconstruction slots, or **82,663,200** power slots.
Its logical scored SINR ceiling is 552,960,000, with up to 27,648,000 list sorts;
score reductions still run for the extra shadow branch even when powers reuse.
If implementation does not realize that reuse, the excess work must be counted,
not silently reported at the lower figure. No cross-program actor cache is
credited as deployment saving.

Reader history reconstruction for all three programs entails at most 1,958,400
pair gates. Stationary/V/R per-lead position-error shadows add at most 1,474,560
three-coordinate comparisons across all currently visible decision peers;
they add no radio ranking or native transition. Hash verification, association
truth audit, count reconstruction, all 32 paired differences and raw-file I/O
are included in measured reader CPU/wall separately. This is finite complete
verification rather than exhaustive joint-action or suffix replay.

For scale, the *old* local-linux C/H B01 worker used 30.341465 s wall,
29.774803 s CPU and 127,568 KiB process-lifetime peak RSS for 64 episodes;
the 32 C episode walls sum to 12.673379 s. The old C counters report
1,105,920 model ticks, 4,491,288 candidate and 45,323 setup link powers,
far below the worst-case n/p ceilings because its actual local sets were small.
Sources: original [summary](../../../../runs/uav_local_history/b01_censor_search_a01/summary.json)
and [full reading](../uav_local_history/NOTES.md#2026-09-29---b01-complete-reading).
This motivates a provisional **1–5 CPU minutes for the new worker and a separate
1–5 CPU minutes for the reader**, not a measured cross-node speed, a deadline
or a scientific stopping rule. Current code, source/node load and larger
telemetry can change those estimates. One-thread NumPy/BLAS and no GPU are
adequate; prefer configured wsl_4070 when an actual selected launch is admitted.
The configured interpreter, current source publication and fresh node memory
admission must be used then, not borrowed from this design-time reading.

Engineering is the dominant investment: provisionally **2–4 hours** for the
local controller/collector, independent pure reader and focused checks, plus
**.5–1.5 hours** of independent executable review/repairs. These are planning
estimates, not a time allowance or a promise of completion. Core scorer arrays
are at most 27×4×5×20 values per actor decision; process/reader peak RSS remains
unmeasured. Record actual phase wall/CPU, RSS scope, raw bytes and import/build
cost instead of extrapolating a universal fit rate. Dense raw observations,
positions, commands and all candidate score/service vectors are about 69 MB
before association/native telemetry; provisionally reserve 150 MB uncompressed
per complete panel, with compression measured afterward. This is not a
permission to truncate promised evidence at a byte limit.

The full proposed worker-plus-reader ceiling is 165,326,675 power slots, with
8,847,360 scored candidate model ticks across live control and verification.
It is not all native environment work and not all policy deployment work;
keep those scopes separate. The total expected compute is small compared with
implementation/reading, so an expanding general tracker, dynamics learner or
replay framework would defeat the reason for choosing this bounded experiment.

### Future bounded engineering scope if Root selects the experiment

No code is authored by this design assignment. The prospective L0 is one
verifiable behavior change: replace only currently visible moving-peer future
powers inside C's legal four-tick score according to the fixed +delta/−delta
laws; preserve C itself, all host/actor/control semantics and inactive parity.
New entrypoints/helpers/tests belong only under this direction's assigned
`experiments/candidates/uav_local_peer_forecast/` and matching test paths.
Import the published C constants/behavior and factory rather than modifying
the other directions' shared inputs or copying an entire learner. The new
runner, pure reader and fixed invocation are bound/published before any launch.

Meaningful focused checks would cover own-motion correction, row permutations,
ambiguity/new/missing/reappearing peers, reset/clock isolation, exact zero/default
parity, mixed moving/stationary near-boundary coordinates, scalar radio residual
calibration, four native clips including altitude and diagonal motion, score
ties, fallback/waypoint mutation, four-tick hold and source/actor leakage. All
stationary modes must agree with original C at the action/score level on the
same legal fixtures. Verify the current all-on host path and independent reader
against original formulas without creating a positive native pilot. Tests own
their scratch through the repository's normal fixtures.

The scorer, collector and reader affect scientific meaning and therefore need
one independent high-risk engineering review after implementation. This does
not repeat the present scientific selection review. Exact published inputs,
active direction/lead/pause, actual-node resource admission and accepted-handle
observation govern any later result run. This design has no such handle,
worker, queue, observer, fit or native exposure to recover or duplicate.

<a id="selected-study-20260930"></a>
## 2026-09-30 16:08 UTC — Root selection and final prospective corrections

After reading this complete proposal and the full independent Oracle answer,
Root **selected the single C/V/R result study** and assigned this same DM
implementation, independent executable review, exact-input publication, native
admission, same-handle observation, complete reading, independent scientific
diagnosis, publication and measured cleanup. No further per-run Root ACK is
required. This supersedes the earlier design-only limit prospectively; no native
work, fit or code result has yet occurred at this selection boundary.

The fixed study remains 32 fresh seeds 29401000..29401031, 96 H256 episodes,
24,576 native steps, zero fits/optimizer calls/new training labels, and the exact
legal C/V/R laws above. **Primary: R−C full-episode mean native J**. J is the
mean of 256 team rewards (the sum of the five per-agent reward fields), each
`.7*served/50+.3*connected_quality`; mean service is connected users per native
tick. Preserve signed service, R−V and V−C, all complete adverse/tail/cost
outcomes and the declared same-path prediction/action diagnostics. This is the
value of minimal legal motion history across synchronized renewals, not a
best-use claim over the inherited sampled neural policy or forecast learning.

The final pre-exposure corrections are:

- Use all **six** arm orders, cycling by ascending world index modulo six:
  `(C,V,R)`, `(C,R,V)`, `(V,C,R)`, `(V,R,C)`, `(R,C,V)`, `(R,V,C)`.
  This replaces the provisional three-order rotation, without changing any
  episode, seed, endpoint or policy.
- The Oracle's final clipped CV four-tick error values are **19.044302 m** over
  all 1,345 matched pairs and **101.686747 m** over the 242 moving pairs;
  the 109-event relevant-slice value **139.200707 m** is unchanged. Preserve
  the final answer's error aggregation and all adverse facts below. The earlier
  19.044305/101.686762 values above are preliminary arithmetic, not additional
  measurements or selection evidence.
- Use the Oracle's more conservative **1.5–7.5 CPU-minute estimate each for
  worker and reader**. These are planning estimates, never caps or a change to
  the fixed scientific stopping rule. Actual costs are measured by phase.

The own-direction row will be published with this selection. Root will update
the cross-direction plan afterward, avoiding concurrent writes to that shared
section. Other active C studies, N8 work and all owner pauses/Claude ownership
remain unchanged. The existing independent answer is the applicable selection
review; no new selection quorum or Pro send is needed. The full answer and
this DM's substantive response are retained next before implementation.

<a id="full-independent-selection-answer-20260930"></a>
### Full independent Oracle answer (verbatim native return)

I recommend **revising the proposal to one fixed C/V/R comparison**, with zero fits. The useful question is whether anticipating motion across synchronized command renewals improves competent local planning. The retained evidence supports testing opposite forecasts; it does not support assuming velocity persistence is accurate.

This remains a design recommendation. Root selects the investment; the DM owns the final declaration, implementation, checks and native admission.

I formed the initial reading from the controller, environment and retained trajectories before considering the DM’s proposed explanation. This is the existing separate-context review, with earlier applicable source readings reused.

**What the original evidence establishes**

I checked all 32 original C trajectory hashes against the [B01 summary](/home/fires/hmasd-wsl/runs/uav_local_history/b01_censor_search_a01/summary.json), source `9327837445025d756d823eeb6e39f50ac90293ad`, and reconstructed peer visibility and adjacent-frame association directly from saved observations.

| Decision-relevant exposure | Count |
|---|---:|
| Agent decisions | 10,240 |
| At least one visible peer | 1,616 |
| Uniquely associated adjacent-frame peer pairs | 1,345 |
| Moving associated pairs | 242 |
| Decisions with both a moving associated peer and current users | **109** |

All 1,345 associations matched the evaluator’s physical identity. That establishes feasibility on these traces, not a general identity guarantee. The 109 potentially consequential decisions occurred in 20 worlds; 64 were concentrated in worlds 07 and 22. They are opportunities to change the local score, not demonstrated changes of action.

The following errors use the proposed clipped velocity law:

| Old C trajectory subset | Stationary forecast | Velocity persistence |
|---|---:|---:|
| All 1,345 associated pairs | 14.218548 m | 19.044302 m |
| 242 moving pairs | 74.865924 m | 101.686747 m |
| 109 moving pairs with current users | **78.932324 m** | **139.200707 m** |

The statistic is the arithmetic mean of Euclidean position error over leads 1–4, then the unweighted mean across eligible peer pairs. It is **not RMS error**. In the consequential 109-pair subset, persistence was better in 15 cases and worse in 91, using a `1e-4 m` comparison tolerance.

At those decisions, nine peers retained their previous command, ten stopped, and **68 exactly reversed their command**. This materially weakens the original persistence rationale and supplies a concrete opposing conjecture.

For reproducibility, the retained inputs are `raw/C_29091000.npz` through `raw/C_29091031.npz` under the linked run. The summary SHA256 is `6506e9692d0310b0538fcd4457fbbed7c8a63ae335a1c41c1c533aa939ec0abd`. I decoded absolute peer positions from own position plus relative coordinates, applied the association and velocity rules below, and used evaluator identity only to locate subsequent recorded positions. No policy scoring, native transition or fit was added. Preliminary figures `19.044305`, `101.686762` and 161 worse pairs are superseded by the precisely clipped readings above.

**The revised comparison**

Keep the current N5, all-on, H256 host, 50 static uniform users, lawful local observations, 27 commands and simultaneous four-tick commitments. Use the DM’s proposed fresh seeds `29401000…29401031`, with all three programs on every world and all five teammates using the same program. Rotate the six possible arm orders across worlds.

1. **C:** unchanged `LocalController(history=False)`.
2. **V:** C with qualifying currently visible peers propagated using their last observed displacement.
3. **R:** the identical intervention using the **negative** of that displacement.

R is a development-informed conjecture about renewal behavior. It is neither an identified physical law nor a new prediction algorithm. The 32 inspected C worlds remain explicit selection exposure.

The exact lawful interface matters:

- Peer rows are anonymous and sorted by **outgoing own-transmitter→peer-receiver SINR**. They are not stable identities, and visibility is not restricted to one peer.
- Correct for own movement before differencing. Match adjacent frames only, accepting a pair when the componentwise `≤30.001 m` gate has exactly one feasible entry in its row and column.
- Snap displacement components with magnitude below `.001 m` to zero, then clip to `[-30,30]`. Startup, ambiguity and missing continuity give zero velocity. No invisible-track continuation or resurrection.
- Propagate moving peers through four successive native boundary clips. R negates the inferred displacement; it does not recover or negate a hidden command.
- Preserve C’s current observed-user set, unknown-interference calibration, objective, command order, ties and sweep navigation. Replace only future powers of moving visible peers. Recalibrating unknown interference at forecast positions, or counting visible interference twice, would change the experiment.
- When no qualifying peer moves, use C’s exact stationary path. In mixed cases, retain C’s existing powers for stationary peers. Clipping their reconstructed coordinates unnecessarily can introduce numerical action differences.
- Interior observations update private frames but cannot interrupt the held command. No actor receives another actor’s current command, private observation, identity, evaluator truth or future observation.

These semantics agree with the current [DM notebook](/home/fires/hmasd-wsl/docs/research/candidates/uav_local_peer_forecast/NOTES.md) and the [original controller](/home/fires/hmasd-wsl/experiments/candidates/uav_local_history/b01/controller.py). Controller and factory bytes remain unchanged from B01, but the environment subsequently acquired radio extraction and masking support. Bind and check the **current all-on implementation**; do not describe the new environment as byte-identical to the old launch.

**The strongest objection and the constructive prediction**

All agents choose new commands precisely when the forecast extrapolates the old block. Moreover, installing R changes the behavior R is supposed to predict.

A simple counterexample explains the danger. In a two-location coordination problem, simultaneous best responses can alternate together between locations. Reversal perfectly predicts that old policy’s next move. If both controllers instead respond to predicted reversals, they may remain together and retain poor coordination. Accurate prediction on old trajectories therefore need not produce useful intervention.

For this host, overshoot followed by reactive correction is a plausible explanation of the observed reversals. It remains an inference: clipping, changing visibility, user geometry and teammate responses could also contribute.

The constructive R hypothesis is that enough renewal reversals remain predictable under use for R to improve action ranking and complete native J/service relative to both stationary C and ordinary V. The serious alternatives are:

- Stationary C is already adequate at most consequential decisions.
- Forecasts change too few executed choices to matter.
- R’s installation destroys the old reversal pattern.
- Forecasts change actions but worsen the incomplete local objective’s relationship to native team service.

This makes the complete three-program observation worthwhile. A third interpolation, learned predictor, centralized simulator or preparatory positive pilot is unnecessary.

**Read the result as follows**

Declare **R−C native mean J** as primary, with R−V and V−C and their service consequences reported alongside it. Preserve all 32 paired worlds, uncertainty across worlds, quality, minimum and lower-tail service, zero-service ticks, path length, boundaries and actual computation. These are fixed-program world comparisons, not independent learning replications.

The reader should reconstruct actual rankings and, on V/R trajectories, compute a nonmutating stationary-C shadow using the actual entering navigation state. Separate:

`eligible observation → moving forecast → changed scores → changed argmax → changed physical four-tick trajectory`.

Compute C/V/R position-error shadows on the **same recorded trajectories**, by lead. Do not compare errors collected under different policies as though their target distributions matched. Following a currently visible peer through later censoring is permissible for evaluator error measurement only.

The consequential branches are:

- **R improves J and service over C and V:** retain a conditional useful control capability. Lower same-path forecast error supports the anticipation account; benefit without that improvement supports the package, with mechanism unresolved.
- **R beats C but not V:** the ordinary persistence alternative is sufficient for the observed improvement; the reversal-specific claim fails.
- **V benefits while R fails:** preserve V’s positive result and reject the tested reversal recipe. Do not rename this an R success.
- **Forecasts activate and worsen native outcomes:** evidence against these deployed interventions, with no automatic predictor fit or sign/weight search.
- **Sparse activation or few physical action changes:** limited exposure to the mechanism, rather than evidence that active anticipation is harmful.
- **Mixed or unresolved native effects:** retain the tradeoff or uncertainty. Do not increase worlds, change gates or densify encounters after seeing outcomes.

No outcome automatically buys confirmation or learning.

**Complete prospective cost**

The revised panel contains **96 episodes, 24,576 native steps, zero fits and zero optimizer updates**.

| Work | Declared count or ceiling |
|---|---:|
| Actor ingests | 122,880 |
| Deployed rankings | 30,720 |
| Own candidate trajectories | 829,440 |
| Own candidate model ticks | 3,317,760 |
| Adjacent-frame pair gates, V and R | ≤1,305,600 |
| Moving-peer prediction ticks | ≤322,560 |
| Controller power evaluations | ≤75,878,400 |
| Native dense link/power slots, including constructor reset | 6,785,075 |
| **Worker combined slot ceiling** | **82,663,475** |
| Reader rankings, including C shadows | 51,200 |
| Reader logical scored model ticks | 5,529,600 |
| **Reader combined unique-slot ceiling with declared reuse** | **82,663,200** |

Dense native accounting includes five diagonal placeholders per state; the distinct nonself physical-link count should also remain available. Logical score counts, unique power evaluations and CPU time are different quantities. Reuse within the reader does not reduce deployment cost.

The original C/H worker used about 30.34 wall seconds and 29.77 process CPU seconds; C’s 32 episodes used 12.67 wall seconds. Those are evidence about an earlier implementation and machine, not a runtime promise. Scaling the DM’s planning estimates suggests roughly **1.5–7.5 CPU minutes each for worker and reader**, plus **2–4 hours implementation/reader work and 0.5–1.5 hours engineering review**. These are provisional estimates, not caps. Actual memory, retained diagnostic volume, caching behavior and supervision cost remain implementation/admission facts to report.

**Literature and newly arrived evidence**

The three-store search supplies useful boundaries, not a novelty verdict:

- New-libs **B03**, Oliehoek–Amato, author preprint pp.34–35, formalizes policies using each agent’s own history. It does not make this two-frame summary sufficient. [Primary preprint](https://www.fransoliehoek.net/docs/OliehoekAmato16book.pdf)
- Inst-sci **MARL-0016**, *Models as Agents*, pp.2–4, explicitly involves joint observation/action information and interacting model/policy errors. Its guarantee does not transfer to our single-row forecast. [Local primary JSON](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0016.json), [AAAI paper](https://ojs.aaai.org/index.php/AAAI/article/download/26241/26013)
- My-lib **iclr-2023-virtual-11586**, Palenicek et al., pp.1–6, empirically separates dynamics accuracy from value-expansion benefit on its continuous-control tasks. This is a methodological analogy, not a result about these UAV controllers. [Local PDF](/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/iclr-2023/iclr-2023-virtual-11586/arxiv-2303.03955.pdf), [primary v1](https://arxiv.org/pdf/2303.03955v1)

Earlier B04’s improved learned endpoint forecasts and adverse F−O native means remain relevant contrary evidence. Its delayed sender messages, private recurrent inputs and co-adapting training differ materially from anonymous local peer forecasting; it neither refutes this comparison nor warrants learned repair.

The new inherited sampled policy is a more substantial constructive opportunity than an untested forecast. I directly checked all **96 C/greedy/sampled evaluation artifacts** at source `e945483b8`: hashes, paired initial arrays, all-on masks, clipped motion and native reductions from saved SINR/connections. Sampled−C reproduces **J +.046566 and service +3.352905**, with 26/32 positive worlds for each, alongside **mean episode-minimum service −.78125**. Memoized C has lower query CPU cost. I did not repeat its training, actor-forward or RNG audit; its assigned result review owns those remaining checks.

That evidence strengthens the case for developing the inherited asset. It does not establish a stochastic coordination mechanism. C remains the proper attribution comparator here, while C/V/R cannot establish superiority to the best available learned asset. An S arm is unnecessary for this bounded question; a later best-use claim would require the appropriate matched comparison.

The supported contribution is a conditional empirical answer about using minimal lawful motion history in cooperative planning. The additional R arm costs 8,192 native steps and tests an opposing, evidence-motivated prediction. That is a sufficient reason for this finite comparison; maintaining four active DMs is not.

**MATERIAL_DISSENT: no — for the revised, bounded C/V/R comparison above. Training, broad forecasting claims and superiority to the inherited sampled policy are unsupported by this recommendation.**

### DM disposition and implementation handoff

Read the whole answer. Adopt C/V/R, the six fixed orders, exact inactive parity,
the primary R−C J contrast and all mandatory adverse/cost readings. The error
statistic is mean Euclidean error across four leads then pairs, not RMS; the
prospective reader reports it plus per-lead values on each same recorded path.
The independent review changed the core constructive hypothesis and the finite
comparison before native exposure. No material dissent remains to self-clear.
The observed reversals support a test of R; they do not imply that R predicts
its own coupled deployment dynamics. The coordination counterexample and the
inherited sampled policy's distinct useful capability prevent a broad forecast
or best-use claim even if R−C is positive. The old 32 C worlds are development
selection exposure, not part of the fresh panel.

The single bounded implementation task now proceeds from the L0 above. Its
writer owns only new direction implementation/tests, with no NOTES, RESEARCH,
shared source or Git index permission; the DM reviews/accepts and publishes.
The implementation includes the live controller, guarded fixed collector and
independent saved-data reader for this one comparison. It selects no new
science, arm, fit, world or native pilot. A separate engineering Reviewer checks
the resulting numerical, information, state and reader behavior before launch.

### 2026-09-30 — Primary-passage verification during implementation

Personally checked new-libs B03 against Oliehoek–Amato's
[author preprint](https://www.fransoliehoek.net/docs/OliehoekAmato16book.pdf),
printed pp.34–37 (PDF pages40–43), §3.2–3.3. Policies use an agent's own
history; the general local history does not become a sufficient Markov state
merely by retaining two frames. Their multiagent-belief discussion additionally
depends on assumptions about other agents' future policies. These passages
support the declared legal-input boundary and the deployment-coupling caveat,
not sufficiency or value of the selected displacement statistic. The fixed
C/V/R design and its predictions remain unchanged. The catalogue's absent
local B03 PDF was not treated as read; this verification used the original
author-hosted source.

### 2026-09-30 16:43 UTC — Engineering review and correctness exposure

The implementation handoff contains the direction controller, collector,
independent reader, guarded runner, package initializer and focused tests.
The DM found and repaired two issues before result launch: delegated inactive
C decisions originally overwrote cumulative moving-peer work counters, and
the new runner originally rejected the launcher's correctly precreated output
directory. Regression checks now preserve exact inactive actions/scores while
retaining cumulative work, and permit launcher metadata while refusing prior
scientific outputs. Timing now starts before scientific imports, whose measured
scope is separate from native factory construction.

Independent engineering review passed the current 22 checks and 300 additional
in-memory C/V/R rankings (maximum score difference 1.11e-16 with matching choices
and navigation). It found one remaining P2: a late reader verification failure
would lose completed/partial reader work counts. The same Implementer is adding
incremental failed-reader accounting and a late-failure regression; launch waits
for that correction and focused review, not a second scientific selection.

The DM additionally found **selected-world correctness exposure**: test fixtures
used seed29401000's initial geometry with a pure, independent-radio `SavedFixture`
for eight transitions per C/V/R arm and an injected R failure after three
returned transitions. These were not native environment constructor/reset/step
calls, but they did compute policy choices and model outcomes for the first
selected world's prefix. Do not describe that prefix as unseen. The C/V/R
programs, scientific comparison, primary and panel were already fixed before
these checks; no outcome-based scientific selection or policy revision followed.
The correction replaces test geometry with a handcrafted test fixture and
identity7; **production seeds remain 29401000..29401031**.

The Implementer's audited two test invocations were 20passed/0.89s and
22passed/0.47s. Each incurred 27 returned/28 attempted pure fixture transitions,
140 actor ingests and35 live rankings (3,780 logical model ticks): together
54 returned/56 attempted transitions,280 ingests,70 rankings/7,560 model ticks.
The Reviewer's one 22-test invocation incurred the same fixture prefix once,
bringing known selected-prefix correctness totals to **81 returned/84 attempted
pure transitions,420 ingests,105 rankings/11,340 logical model ticks**, all on the
same seed and with zero native environment steps. Repeated saved-data corruption
checks add verification work whose exact counters were not retained in normal
test scratch; these totals are therefore not complete engineering cost. No
numeric scientific endpoint was printed by the checks. The fixed complete panel
remains the result experiment; its provenance will retain this exposure rather
than silently replacing a seed or claiming pristine freshness for all32 worlds.

The Reviewer's additional300 rankings used `RandomState(913)` only to construct
100 independent synthetic local rows, each scored under C/V/R; they used no
selected seed, initial-world generator, native transition or collected path.
This adds300 live and300 independent reader rankings,32,400 logical model
ticks on each side. The Implementer's clean and final-counter checks alone
add at least200 reader score requests/21,600 logical ticks over its two earlier
test invocations; other corruption checks remain incompletely metered.

### Fixed execution and retention details

Use the configured `wsl_4070` node, canonical checkout
`/home/wu/projects/HMASD`, configured
`/home/wu/.venvs/hmasd-gcc-31021/bin/python`, one NumPy/BLAS thread and no GPU.
The current native control launcher and compute configuration already match
published authoring-source bytes. Synchronize only this direction's published
active row into its live canonical RESEARCH (preserving other direction edits),
fetch the exact published source, then request a retained launcher snapshot.
There is no accepted operation to migrate or retry.

The new tag is `runs/uav_local_peer_forecast/b01_cv_reversal_a01`. The frozen
scientific argv is
`experiments/candidates/uav_local_peer_forecast/run.py --seed 29401000 --launch-sha <published-source-sha> --out runs/uav_local_peer_forecast/b01_cv_reversal_a01`.
The launcher receives that same full SHA, direction `uav_local_peer_forecast`,
lead `Codex DM (native child)`, node `wsl_4070`, source root above and `--snapshot`.
It must freshly admit actual-node memory and current pause/lead/publication.
The admitted process completes the fixed worker and then its full independent
saved-data reader; it never retries a failed worker. Arm `tools/hmasd_wait.py`
on the one accepted status handle and keep this native DM turn active through
complete reading. A technical reader failure preserves accepted worker outputs
and incurred counts; it does not authorize new native episodes.

Keep the single bulk `raw/` copy under that canonical node/tag. Collect only
compact configuration, summary/reading, worker/reader/terminal status and native
admission/process records locally for Git publication; use the recorded raw
byte counts and hashes for direct node readback. No duplicate bulk collection
or backup chain is needed. After terminal verification and scientific reading,
check live consumers and use maintained snapshot GC on this exact accepted
snapshot, recording actual targets and net allocated bytes reclaimed.

### 2026-09-30 16:51 UTC — Executable acceptance

Independent Reviewer rechecked the repaired incremental reader accounting and
both failure entrypoints: **no material finding remains**. Its final full suite
passed27 tests in0.66s, including late score/counter failure and interrupted
arithmetic. The DM independently ran the final full suite:27passed/0.70s;
syntax and whitespace checks passed. Current fixtures contain no selected-seed
literal or call to `initial_geometry`; their geometry is handcrafted. The
Implementer's final tests were27passed/0.75s and focused5passed/0.97s.
These test times are support checks, not native result runtime. Exact total
engineering CPU and labor are not metered.

The DM accepts the six-file diff against the frozen L0, including original-C
reuse, anonymous local history, inactive/mixed numerical behavior, guarded
collector, partial-failure evidence and independently implemented saved-data
formulas. No shared controller/environment source was changed, no fit/native
experiment has run, and no scientific design revision resulted from the
engineering repairs. Target-node numerical behavior and the complete panel
remain to be observed. Publish these inputs before requesting admission.

### 2026-09-30 17:01 UTC — Accepted native operation and observation

Inputs were published and verified at
`13da38312ab6ab4af9dc94c160955b01b479a37d`. A first direct-shell Git fetch on the
node waited without completing; its own HTTPS helper was stopped before any
control write, snapshot, claim or runner effect. Repeating only source/control
synchronization through the configured `zsh -lic` network environment succeeded.
The preexisting automatic-GC warning about missing historical tree
`dfe82c9813ee82191abb8385cc12a6886fd0a77b` was preserved; no shared Git repair
or broad cleanup was attempted. Only the owned active row was inserted in
live canonical RESEARCH; other dirty controls/outputs were preserved.

Supervisor `peer-cvr-b01-a01-20260930` submitted the single launch and ended
exit0 after returning native acceptance at **2026-09-30T17:01:17.298181Z**.
The [manifest](../../../../runs/uav_local_peer_forecast/b01_cv_reversal_a01/launch-manifest.json)
and [fresh admission](../../../../runs/uav_local_peer_forecast/b01_cv_reversal_a01/admission-preflight.json)
bind source, current control observation, command and actual node resources.
Operation:
`/home/wu/projects/HMASD/.git/hmasd-admission/1c0fd47795a240ff32a35fa8b2242bc8a06cbba6930c2ae32e28be193cc47be4.json`.
Snapshot:
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/c3b7702e04984830ab4355b038174722`.
RunnerPID1140807 and native supervisorPID1140806 are recorded identities, not
relaunch instructions. Source remains the published SHA above despite later
main/control publication.

`tools/hmasd_wait.py` registered generation1 with600-second checkpoint window,
30-second status interval and25-second probe timeout, observing that exact
operation. The first drain directly observed accepted/running native identities
and consistent records at17:01:42UTC. This native DM stays active through
collection and interpretation; registration or launcher acceptance is not a
scientific result boundary. The worker and reader are one accepted process.

<a id="b01-complete-reading"></a>
## 2026-09-30 — B01 complete result reading

The same operation exited0 with a valid witness at17:02:22UTC; the deterministic
observer recorded READY/consistent terminal facts at17:02:24UTC. Native-child
queue delivery was rejected by the runtime, as anticipated; the active DM
drained the event directly, consumed it in generation2 and stopped the finished
observer without restarting the worker. All96 episodes and the independent
full reader completed at the original source13da38312. The summary and reading
are [run records](../../../../runs/uav_local_peer_forecast/b01_cv_reversal_a01/summary.json)
and [full reading](../../../../runs/uav_local_peer_forecast/b01_cv_reversal_a01/reading.json).
Summary SHA256 `0545b3fd02c375ac573c856418d212acdea7e52ab39b2c8ee7663bfb1b77641d`;
reading SHA256 `fdc6012b80d9e0ef72d0105319e974f0e56f0176433aa11694412bf63bd0bb9e`.
The DM verified all summary-linked compact hashes, all10 source-manifest files,
and directly on the canonical node all96 raw hashes/byte counts:7,215,902bytes
at the declared single raw location. No bulk duplicate was collected.

Before the continuation judgment, read the relevant published RESEARCH at
`6307afcc1e789b419c062491a9d45dce6b0691ab`: §2's local-history C/H and newly
completed ordinary C-prior I evidence, plus §5's delayed future-motion B04.
They preserve the distinction between lawful history, prediction accuracy,
actual decisions and complete use. Ordinary I's new conditional positive
strengthens the simpler alternative of changing behavior around competent C;
cross-panel magnitudes do not rank it against V/R here. The inherited sampled
asset remains another capability, not this component comparison's attribution
baseline. These readings give no reason to buy a predictor fit automatically.

### Complete native endpoints and contrary outcomes

| Program | Mean native J | Users/tick | Mean within-episode service-p10 | Mean episode minimum | Mean path m/UAV |
| --- | ---: | ---: | ---: | ---: | ---: |
| C | .332121330 | 19.634033 | 18.984375 | 11.3125 | 2205.271 |
| V | .336812229 | 19.925903 | 19.375000 | 11.3125 | 2409.165 |
| R | .330925842 | 19.527954 | 18.984375 | 11.3125 | 2274.776 |

The fixed paired t95 intervals are descriptive across32 worlds, df31, with no
filtering, resampling choice or outcome-dependent panel extension:

| Contrast | Mean delta J [t95] | Mean delta users/tick [t95] | J positive/negative/exactly same worlds |
| --- | --- | --- | --- |
| **R−C primary** | **−.001195487 [−.003726104,+.001335129]** | **−.106079 [−.312271,+.100113]** | 4/4/24 |
| V−C | +.004690899 [−.002234368,+.011616165] | +.291870 [−.184840,+.768581] | 4/1/27 |
| R−V | −.005886386 [−.013004277,+.001231504] | −.397949 [−.910936,+.115038] | 4/7/21 |

The primary constructive R prediction is not established. R−C service improves
in3 and falls in5 worlds, with24 equal; its small quality increase+.000965400
does not offset the mean service loss. V's positive J/service point estimate is
preserved, not promoted to reliable superiority. All program/world minima are
identical and all96 episodes have zero zero-service ticks; this does not measure
individual-user continuity or physical safety.

Preserve concrete strong positive and adverse outcomes. V−C in29401002 is
+.097783118J/+6.550781 users, with service-p10+6 and path+3703.971m/UAV;
29401012 and29401017 also gain+2.828125/+1.585938 users. V loses
−.017340924J/−1.855469 users in29401026, with service-p10−2. R's largest
J gain is29401002 (+.002732434), but its service there is−.019531;
29401006 loses−.039539521J/−3.238281 users, service-p10−2 and
path+1774.880m/UAV. R−C mean service-p10 is exactly0 because one−2 and
one+2 offset; V−C is+.390625, not a uniform tail improvement. Mean path
increases are+203.894m/UAV forV and+69.505m/UAV forR. Mean xy-boundary
exposure rises7.875/7.21875 UAV-ticks; mean altitude rises .019531/.058594m.
There is no altitude penalty or energy model in this native J, so neither
height nor path changes are to be renamed energy/safety outcomes.

The DM separately compared saved commands, full positions, local observations,
J/service/quality arrays: V/C are exactly identical in27 worlds, R/C in24,
R/V in21. This is a trajectory fact, not merely equality of rounded endpoints.
The earlier seed29401000 correctness-prefix exposure remains declared above;
all32 original worlds are retained without deletion or replacement.

### Information, prediction and actual decision exposure

All122,880 actor ingests,30,720 deployed rankings and3,317,760 own candidate
model ticks occurred. The complete reader made51,200 rankings including20,480
stationary-C shadows, sharing powers only within each decision. It reconstructed
all24,672 saved native states, all radio/observation/assignment/reward/movement,
all actual controller scores/selections/navigation/holds, and the declared
same-path predictions. No actor received evaluator identity, truth, other
observations, current teammate commands or future information.

| Actual recorded policy | Moving-peer + current-user decisions | Changed score vectors | Changed argmax / command / physical path | Worlds with physical changes |
| --- | ---: | ---: | ---: | ---: |
| C | 202 | 0 (self reference) | 0 | 0 |
| V | 207 | 206 | 5 / 5 / 5 | 5 |
| R | 202 | 202 | 9 / 9 / 9 | 8 |

Each program has10,240 decisions. Thus score perturbations usually leave the
decision unchanged; 14 total altered commands are all physically distinct,
with no clipping alias. This is sparse decision use, not nonactivation of the
tracker or scorer. The full reader found22,539 accepted adjacent-frame matches
across all paths with zero evaluator-identity errors and zero ambiguous rows;
809 visible rows lacked a match. These finite traces validate observed
associations, not a universal association guarantee. All worker calibration
discrepancy counters are0. No association/calibration defect has been identified
as a reason for another repair.

The following errors are arithmetic mean Euclidean meters over leads1–4 then
eligible pairs, always comparing all three forecasts **on the same recorded
path**. They are not RMS and are not causal outcome conditioning:

| Recorded policy; fixed slice | Peer pairs | Stationary C forecast | V forecast | R forecast |
| --- | ---: | ---: | ---: | ---: |
| C; moving matched + users | 203 | 68.574035 | 108.916915 | 24.919163 |
| V; moving matched + users | 208 | 71.008630 | 109.130302 | 28.188739 |
| R; moving matched + users | 203 | 69.738419 | 109.167159 | 29.025438 |
| V; actual physical-change slice | 5 | 45.000008 | 64.571250 | 96.213203 |
| R; actual physical-change slice | 10 | 43.072018 | 71.210592 | 76.170357 |

Peer-pair and decision denominators differ when multiple peers are visible.
The last two slices were prospectively declared descriptive diagnostics; they
do not identify the effect of a forecast error or a counterfactual C continuation.
Reversal still predicts geometry better on the broad moving+users slice even
under R deployment. Its nine consequential choices do not inherit that error
advantage: on their ten peer pairs, R's error is higher than stationary C's.
Conversely, V has four beneficial complete worlds despite worse broad errors.
Thus neither the old-reversal premise disappearing everywhere nor aggregate
accuracy translating automatically into native value fits these observations.
The simplest supported change in explanation is that most model changes leave
competent C's ranking winner intact, while rare changed choices can change the
subsequent path substantially. This does not identify which local error or
longer-horizon consequence caused any specific native gain/loss.

### Complete measured cost and provisional continuation judgment

The study used96 complete episodes/24,576 native steps,0fits/updates/new
training labels, one constructor/unscored reset and96 explicit scored resets.
Worker counts are13,208,570 controller power values (only3,300 additional
moving-peer values) plus6,785,075 native dense slots =19,993,645 total.
The reader uses19,993,370 combined slots; both are well below their prospective
ceilings. Dense diagonal placeholders remain charged; physical nonself native
links total6,661,710 including the constructor reset.

Worker wall/CPU were28.822213/30.244984s; full reader32.234286/33.959248s;
complete process61.084482 wall/64.233721 CPU seconds with peakRSS78,320KiB
(process-lifetime Linux scope). Imports and native factory are included; their
separate wall/CPU values are .042313/.044559s and .217704/.229393s.
Measured C/V/R actor CPU over32 episodes is3.314114/5.356443/5.426546s;
V/R cost about1.62/1.64 times C here. No deadline or fastest-controller claim
was tested; known exact memoization is an additional ordinary compute option.
The DM's final raw-hash/trajectory-identity pass added .161206wall/.668323CPU
seconds excluding imports/SSH. Engineering, Git/network synchronization,
admission/snapshot, transfer and scientific review remain additional support;
the earlier correctly disclosed test exposure is not folded into native steps.

**DM initial disposition, pending independent scientific diagnosis:** retain C,
the exact V positive/adverse witnesses and R's geometric prediction capability,
but do not adopt R or claim V superiority. The selected reversal recipe has
not converted its broad accuracy advantage into useful complete mean value.
Sparse physical use limits an active-anticipation harm claim;0fits says nothing
about forecast learnability. Decline automatic sign/weight/gate tuning, learner
fitting, encounter densification or a new panel merely to shrink these intervals.
A fresh fixed-program replication could test recurrence of V's rare gains,
but it would still need an actual deployment choice to change and competent
ordinary alternatives. No new operation is selected while the separate-context
ResearchCritic reconstructs these facts and recommends the bounded next action
or justified stop. This is an unresolved broader prediction/control question,
not an empirical impossibility or a technical failure.

<a id="b01-independent-diagnosis"></a>
## 2026-09-30 — Independent scientific diagnosis and resolved disposition

The dedicated ResearchCritic ran in a separate context with no inherited DM or
Root conversation. It reconstructed the frozen protocol, source and native
evidence before reading the original Oracle answer and proponents' interpretations.
Its completed substantive recommendation follows. No new native episode or fit
was launched for this review.

### Independent review

**Recommend revising the explanation and stopping further investment in this
fixed C/V/R recipe.** Retain C as the component reference, V's conditional
capability, and every adverse result. The reviewer agrees with the DM's proposed
disposition. No additional fit, replication or Pro consultation is warranted by
this result alone.

The reviewer independently checked all 96 raw hashes; all 32 distinct initialized
geometries; three-arm pairing and identical first four ticks; native movement;
reward/service/quality reductions; and every signed J/service contrast and
declared interval. Maximum reward-formula discrepancy was 1.67e-16. It also
independently reconstructed the relevant same-path forecast errors. All 10 current
source files matched launch 13da38312ab6ab4af9dc94c160955b01b479a37d. The existing
full reader completed successfully; the critic did not repeat its complete
controller/physics reconstruction or the engineering suite.

The complete comparisons in the preceding reading are exploratory fixed-program
comparisons across worlds. They establish neither equivalence nor a reliable
population ranking. The recorded correctness exposure to seed 29401000's prefix
remains provenance; all 32 worlds remain in the frozen reading.

These raw witnesses are consequential. Actors are **zero-indexed**. Error is
mean Euclidean error over the next four leads for the moving visible peer at
the first differing decision.

| Program/world | First differing tick/actor | Stationary / used forecast error, m | First changed block delta J | Complete delta J / users per tick |
| --- | --- | ---: | ---: | ---: |
| R29401006 | t4 / actor 1 | 75.000 / .000011 | +.026952 | −.039540 / −3.238281 |
| V29401002 | t8 / actor 2 | .000020 / 75.000020 | −.002285 | +.097783 / +6.550781 |
| V29401012 | t8 / actor 4 | .000001 / 105.110526 | −.023468 | +.038055 / +2.828125 |
| V29401017 | t4 / actor 1 | 75.000004 / .000016 | −.011377 | +.028682 / +1.585938 |
| V29401026 | t16 / actor 4 | 75.000005 / .000017 | −.007569 | −.017341 / −1.855469 |

For each row, the two complete programs have identical observed prefixes through
the decision input:

- **R29401006:** actor 1 moves left instead of holding. Peer 0 actually reverses
  its horizontal motion, making R almost exact. Initial service improves from
  C's `[5,6,7,7]` to `[5,9,9,8]`, but during ticks 64–255 C averages 18 served
  and R 14.25. Full-episode service p10 falls 2; mean path increases 1774.880m/UAV.
- **V29401002:** actor 2 chooses `(1,1,1)` instead of `(0,−1,0)`. Peer 1 stops,
  so stationary prediction is accurate. Subsequent service nevertheless improves:
  ticks 64–255 average 22.0625 versus C 15. Actor 2's observed-user count averages 6.62
  versus C 0. Service p10 rises 6, with 3703.971m/UAV extra path.
- **V29401012:** actor 4 chooses `(1,1,1)` instead of holding while peer 3 stops.
  Late service becomes 20.25 versus 17.125; p10 rises 3 and path increases 1511.675m/UAV.
- **V29401017:** actor 1 chooses `(1,−1,1)` instead of `(−1,0,0)`. Persistence
  accurately predicts peer 2. Despite the initial loss, late service becomes 19.875
  versus 18; p10 rises 1 and path increases 1562.562m/UAV.
- **V29401026:** actor 4 holds instead of moving left while peer 0 continues left.
  Only four ticks have different team commands, but the positional consequence
  persists: subsequent service settles at 10 versus 12. Service p10 falls 2.

These are **observed matched-program contrasts**, including subsequent coupled
responses. Forecast errors describe the recorded paths. They are not evaluations
of arbitrary alternative suffixes, proofs of mediation, or evidence that the
same intervention would help another world.

The supported diagnosis is more specific than “accuracy does not guarantee reward”:

1. **The reversal representation prediction survives deployment.** On R's 203
   moving-peer pairs with current users, errors are C 69.738 m, V 109.167 m and
   R 29.025 m; 149 next commands exactly reverse. Corresponding reversal advantages
   also remain on C and V paths. Destruction of the old reversal pattern is a
   weak explanation of this result.
2. **Consequential choice exposure is sparse.** V has 207 eligible decisions and
   206 score changes, producing five physical changes. R has 202 eligible
   decisions/score changes, producing nine physical changes. Each denominator
   is 10240 actor decisions; eligible events occur in 22 worlds. This is substantial
   nonconsequential scoring alongside sparse executed intervention, not universal
   nonactivation. R29401006 and V29401026 are active adverse witnesses.
3. **Average geometric accuracy poorly targets the decisions that determine
   complete value.** On R's action-changing slice, stationary error is 43.072 m
   versus R 76.170 m across ten peer pairs. That selected slice is descriptive.
   More decisively, accurate forecasts can improve the first block and harm the
   episode, while inaccurate forecasts can harm the block and improve the episode.
4. **The strongest simpler explanation is trajectory redirection under competent,
   short-horizon local planning.** Different early choices change later visibility,
   interference and configurations. Raw service and observation traces support
   this account, but do not isolate discovery, invisible interference, horizon
   truncation or coupled responses as its sole cause. Tracking failure is
   unsupported here; learnability was not tested.

V's strongest useful positive is a sparse, lawful intervention that sometimes
reaches substantially better complete trajectories, with both inaccurate and
accurate forecasts among its gains. Preserve that capability. Also retain R's
three small joint J/service gains and its quality/service tradeoff in 29401002;
its adverse mean is not universal failure.

The newly available ordinary I policy strengthens the competing explanation
without empirically ranking I against V. The critic checked its policy/source
reading, declared block results, and paired positive/adverse raw witnesses:
30300109 gives +.234261 J/+16.488281 service;30300220 gives −.093560/−7.039063.
Its overall +.023721 J/+1.709106 service comes with greater travel and worse
within-episode service p10. This demonstrates useful ordinary perturbation
without a forecast. It does not establish that randomization explains V's gains
or that I dominates V. [I reading](../../../../runs/uav_parent_adaptation/b03_c_prior_a01/reading.json).

**The stopping recommendation is an investment judgment, not a family-wide
impossibility claim.** An unchanged V replication could test recurrence but
would leave the ordinary-perturbation explanation largely unresolved. The
reviewer would not allocate it now. No further observation is needed to publish
this study and end the fixed-sign recipe.

If a later decision specifically concerns using V, a worthwhile complete
observation would compare fixed V, C and the competent ordinary stochastic
alternative on prospectively matched worlds, preserving service continuity
and movement costs. Recurrent V−C gains would support package recurrence;
an advantageous matched V-versus-ordinary tradeoff could support use; mixed
or adverse recurrence would weaken expansion. None alone proves forecast
mediation. A reasoned, costed successor conjecture is sufficient: do not require
a complete downstream causal diagnosis before allowing future exploration.

The critic independently agreed with the preceding measured native/worker/reader
cost. One additional reviewer arithmetic pass cost 34.417 wall/36.105 CPU seconds,
with zero native transitions or fits. Engineering and total support cost remain
incompletely metered. No live review process or snapshot/scratch consumer remains;
preserve the sole raw evidence copy, with no continued snapshot retention needed.

**MATERIAL_DISSENT: no.** The reviewer supports this fixed-recipe stop and
retention of V's conditional capability, grounded in verified sparse interventions,
positive/adverse trajectories and the failed primary improvement prediction.

### DM resolution and next condition

Accept the independent diagnosis and recommendation. The initial explanation
is sharpened by the first-block/full-episode reversals above: poor error on the
aggregate action-changing slice cannot by itself explain R's large loss, whose
first forecast is nearly exact and initially beneficial. Likewise V's gains
do not depend uniformly on forecast correctness or initial reward improvement.
The empirically supported account is sparse trajectory redirection; the exact
roles of later discovery, interference and coupled responses remain unresolved.

**Keep:** competent C as the matched component reference; frozen C/V/R code and
independent reader; V's conditional positive/adverse trajectories; R's improved
geometric prediction and all small positive/adverse endpoints; the complete
raw/compact evidence and disclosed prefix exposure. **Stop:** the unchanged
fixed-sign recipe and automatic sign/weight/gate tuning, fitting or panel
extension. Neither R adoption nor reliable V superiority is established.
Task opportunity, lawful representation, learnability and complete-package
value remain distinct; no forecast learner was fitted.

Place the direction in **reserve**, idle with no accepted producer or pending
scientific dependency. The assigned one-panel boundary is complete. Return the
evidence and this choice to Root for cross-question allocation; do not silently
start a successor. A concrete re-entry condition is an actual V-use decision
or a materially different, reasoned and costed anticipation/control conjecture
with an applicable independent selection review. An eventual complete comparison
should preserve C and competent ordinary same-resource alternatives such as I;
no proof of mediation, exhaustive suffix replay or successful toy is an admission
gate. A future proposal is optional, not owed by the still-open parent question.
No additional Pro consultation supplies a distinct unresolved role at this
decision; the evidence-first ResearchCritic review is adequate and uncontested.
