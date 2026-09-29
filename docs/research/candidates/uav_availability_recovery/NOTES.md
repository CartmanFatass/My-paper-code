# UAV Availability Recovery

## 2026-09-29 - B01 prospective complete reserve-control comparison

Native DM `/root/dm_availability_recovery`, parent `/root` in session
`01a0e560-4333-7b03-8ff3-759a4add1d9a`; authoring shared main at
`/home/fires/hmasd-wsl`. This direction owns its implementation, matching tests,
notebook, runs and scratch. Root is publishing the initial index and controls;
no result execution precedes an active assigned row and published exact inputs.
There are no inherited live operations. The current owner pause is lifted in
RESEARCH; paused FSD/PPC, frozen G33 and Claude's directions remain separately owned.

### Question, evidence and prediction

Can joint control of two reserves during one temporary primary UAV outage and
return improve complete native service beyond competent ordinary reassignment?
This is a centralized control-package and empirical coordination comparison,
not a new MARL algorithm, a private-memory claim, general churn, or faster-response
claim. The decision coupling is physical: reserves can supply access or backhaul,
interfere, duplicate service and incur travel/guard costs together. Experience may
learn a useful joint choice despite the ordinary forecast's approximate trajectories
and association. The competing prediction is that same-information finite planning
already supplies the useful adaptation, or neither new package beats inherited S.

Read published main `fed55fd0ef329f8fac55dfdf3faeac46158fc1d4`, RESEARCH topics
[1](../../RESEARCH.md#1-rl-研究的是交互后果不是组件名称),
[2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练) and
[3](../../RESEARCH.md#3-marl-增加的是联合行为和信息结构), plus the
[archive re-entry review](../../archive/2026-09-29/RESEARCH-archive-reentry-review.md).
Their concrete effects are to retain native service and graph-potential reward
separately, give the ordinary planner every information addition, preserve actual
two-reserve joint choices, and make no private-history inference from lifecycle
events. G0 publicly exposes current team geometry/service, assignment ownership
and lifecycle events. This is not a missing-information experiment.

Contrary evidence stays consequential. The original
[N7 B01 two-seed intake](../variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_TWO_SEED_RESULT_INTAKE_20260905.md)
contains two real learning pairs, with both learned arms below BCRH; its intake
does not by itself prove information equality. S4 availability B02 removed
observed replanning lag but mean QoS changed -0.013172 and J -29.686, with wide
uncertainty ([original reading](../energy_relay_availability/NOTES.md#2026-09-27--independent-scientific-review-retain-clock30-and-end-current-timing-investment)).
Neither is untouched opportunity or universal rejection. G0 temporary return is
distinct from N7 permanent loss, static count interpolation, partner adaptation,
Milan restoration and Claude's coupled-host/D1-prime work. No novelty claim is made.

Root's question construction and one focused independent ResearchCritic review
selected this complete three-fit study. Root reports MATERIAL_DISSENT:no after
four adopted corrections: truncate P forecasts at H500; update shadow S every
native step; construct P only from public state rather than deepcopy G0; preserve
native PBRS gamma 0.99. The full published selection/review will be linked when
Root's initial publication is available. This applicable selection review is
reused; independent engineering review will cover the actual executable change.

### Host and information contract

Reuse `UAVSourceIdentifiabilityEnv` from `ha_ctse_process/uav_g0_environment.py`,
`make_episode_source`/`actions_toward_targets` from `uav_g0_geometry.py`, and
`SameInformationController` from `uav_g0_controllers.py`, inspected at the above SHA.
Do not run the old proof-only G0 entry or inherit its oracle gates and endpoint.
Native S7-S1 has 8 UAVs, 30 static users, H500, altitude 50 m, battery/charging/
random failure off. One of six primaries is unavailable from O in 180..220 for
D in 80..100. Motion, radio and service are disabled while absent. Return uses
the unchanged position and a new opaque lifecycle handle. Two reserves remain.

All arms use public current roster positions/velocities/availability, service,
association, registered base/primary/gate/stage geometry, issued assignments,
public lifecycle mapping, observed absence age, physical clock and remaining H.
Association rows are explicitly aligned with the anonymous roster. The L/P
deployment contract additionally supplies all 30 static user XY pairs once per
episode, represented in float32 (240 payload bytes before metadata). These are
the simulator's actual coordinates at that precision, a declared centralized
telemetry/acquisition assumption; this study does not identify their acquisition
value or claim they are free information. P receives the same represented map
that enters L's input. Actor and critic share this information. No episode ID,
RNG state, realized future O/D/service, private ledger or oracle branch is passed.
Both know the duration law; while absent at age a, D is uniform on
`max(80,a+1)..100`. After observed return the active probability is one.

The boundary adapter may read source geometry/initial issued ownership and raw
environment public fields, but not future event fields for action selection.
Source O/D are read only for completed-output windows. Opaque handles are state
keys, not numerical features. Stable feature rows use public original assignments,
and rejoin updates the public old-to-new handle map. This is not physical-slot
identity inference.

### Frozen arms and commands

All arms use S before the first observed leave. Other primaries retain inherited
target tracking throughout; the returned primary retains its original target.
After leave, L and P command the two reserves jointly at leave, rejoin and
absolute ten-step clocks, deduplicating coincident events. Each reserve chooses
one of own-stage, vacated-primary, inward-gate, or hold-current: 16 categorical
joint outputs, joint index `4 * reserve0_choice + reserve1_choice`. Hold captures
the actual decision-boundary position. Commands persist until the next allowed
decision. Every step uses the same `actions_toward_targets` and native guard;
there is no residual cap, BC or unrestricted fleet reassignment.

- S is original SameInformationController, including nearest-reserve dispatch,
  gate return and per-step readiness. It is a secondary reference with its
  disclosed cadence advantage after return.
- P scores all 16 commands with isolated public native radio/routing/delivered-QoS
  snapshots. Nominal tracking forecasts +10/+40/+80/+120, weights 10/30/40/40,
  averaged over active/absent branches under the lawful return posterior. Cut
  intervals at remaining H500, including partial final weights; no value beyond
  H is scored. Include S's current command and both-hold. Ties prefer the S
  incumbent, then lower total travel, then categorical index. Replan from actual
  state. Shadow S updates `target_map` on P's actual trajectory every native
  step, even though P only issues commands at allowed clocks. The forecast
  deliberately approximates future guard and association behavior; retain
  predicted versus realized service and requested/executed actions.
- L is a central 2x128 tanh MLP with 16 logits and a value head, no RNN. Inputs
  are fixed-normalized public geometry, service, association, map, lifecycle age,
  assignments and time. No running normalizer sees evaluation data. Commands
  are sampled in training and argmax at final evaluation.

`step_dense` records completed step t while returning boundary events for t+1.
Consume each event exactly once before the next decision. Read completed-step
native J from `last_constrained_reward_metrics['scenario7_reward']`; returned
boundary availability must not retrospectively change that reward. Native
`reward_discount_gamma=0.99` remains untouched. Learner gamma=1 is the separate
finite-horizon macro-return choice; lambda=.95 applies to actual macro intervals.
Only intervals following an L decision enter PPO. The forced S prefix is measured
but supplies no actor or critic update rows. At H500 this finite-horizon learner
uses zero terminal value rather than continuing beyond its stated objective.

### Exposure, reading and cost

Three fresh fits, seeds 2026092911/2026092912/2026092913; each 512 complete H500
episodes, with distinct deterministic training world streams excluding evaluation
IDs. Per fit: 32 collections x16 complete episodes; four PPO epochs x4 minibatches
per collection =512 optimizer updates, 1,536 in the batch. Adam lr3e-4, clipping
.2, entropy coefficient .01, value coefficient .5, gradient norm cap .5,
gamma1/lambda.95; macro rewards are the actual sums of native step rewards.
No tuning panel, predictor fit, extra seed/arm/factorial or automatic rerun.
Save initialization and final weights plus native curves. Final only, with no
selected checkpoint or extra initialization evaluation panel.

Evaluate deterministic final L from all three fits plus P and S on the same
64 fresh sources 2026093001..2026093064: 320 complete episodes,160,000 steps.
Evaluate one common no-event S reference on those 64 sources:32,000 steps.
All policies would stay S in no-event episodes, so the reference is shared rather
than repeating five identical no-event panels. Training is768,000 native steps.
Total:3 fits,1,920 complete episodes,960,000 steps. Construct each evaluation
source once and reuse its immutable exogenous data across arms. With1,536 training
and64 evaluation source constructions, each invoking assignment twice, the source
path enumerates `1600 * 2 * 8! = 129024000` assignment candidates.
P's pre-truncation upper work is `64 * 33 * 16 * 4 * 2 = 270336` native service
snapshots; identical branches and truncated horizons may reduce it. These are
algorithm work, not free reasoning or environment interaction steps.

Primary readings: complete H500 native J sum and QoS/step, L-P per training seed.
Also read L-S, P-S and all no-event losses. Retain graph_potential_delta (J is not
QoS plus a constant), weakest-hotspot service, J_event and event deficit,
catastrophe streaks, pre/absence/rejoin/post windows, guard counts, path length,
joint choices, policy entropy and adverse worlds. Three training instances are
the inference units;64 common worlds give conditional paired estimates, not64
training replications. Report per-seed means and descriptive paired world t95
intervals; any cross-seed interval is a visibly small-n t2 description. No
equivalence, stable ranking or general safety follows from uncertainty across zero.

L above both P and S in complete J and QoS supports this conditional learned
package; it does not identify map value, private memory, architecture or optimal
coordination. P above S while L does not beat P preserves an ordinary capability.
L above P but below S does not support adoption. Event-only gains or faster
response without complete net benefit are not success. Nonactivation, native
guard suppression and technical missingness are separate readings. No post-result
fault strengthening or enlarged action set follows automatically. This first
fixed study is exploratory package evidence; broader confirmation needs its own
actual claim and applicable fixed-plan scientific review.

Prospective node: wsl_4070, configured Python `/home/wu/.venvs/hmasd/bin/python`,
one worker with one numeric thread, CPU; GPU unnecessary. Fresh actual admission
is required for the result launch. G0's rate is unknown. S4's measured5,377CPU-s/
192k steps suggests only a rough7.47CPU-hour anchor for960k steps, with different
learning, snapshots, initialization, compile and readback costs additional.
Root's14-28 agent-hour engineering estimate is conjectural, not a hard allowance
or runtime promise. Record actual full-process wall/CPU/RSS and fit walls.
Historical native/CPython crashes remain unexplained and distinct from negative
science; a terminal failure never restarts automatically.

### L0 implementation scope

Deliver one new direction runner plus public reserve-command adapter, finite
ordinary planner, categorical PPO and compact reader. Own only
`experiments/candidates/uav_availability_recovery/`, matching tests, this notebook,
`runs/uav_availability_recovery/` and `temp/directions/uav_availability_recovery/`.
No shared-core edits are planned. CLI must call admission before creating result
outputs, environments or learners, and match the published launch SHA. Preserve
all native host, reward, RNG, guard and frozen exposure semantics above.

One bounded Implementer owns only `predictor.py` and `test_predictor.py`: construct
native service snapshots from a typed public payload and score the fixed16 joint
commands at truncated weighted horizons, with lawful return probabilities and
incumbent/travel ties. DM owns control, learning, runner, reading and other tests;
the helper has no index/NOTES/shared-file write ownership, no launches and no
children. Snapshot input consists only of public current arrays/geometry/map,
targets, active mask, clock/age and observed event owner; no live G0 env/source or
ledger enters predictor code. Its active/absent forecast is an explicitly nominal
branch approximation, not exact suffix replay. Use inherited native radio,
association/routing/delivery functions on an isolated S7-S1 instance rebuilt from
that public state; never deepcopy a live G0 environment. Reset snapshot association
state so no source-private serving history enters. Count every native snapshot.

Focused checks must cover public-input isolation, float32 map reaching L/P,
association/roster alignment, all16 joint choices, persistent hold, event/clock
deduplication and consecutive shadow-S readiness. Check truncated weights and
posterior support, native snapshot service reconciliation, no live RNG/state
mutation, reward/boundary ordering, native gamma .99 versus learner gamma1,
finite-horizon macro sums/GAE, forced-prefix exclusion, three independent streams,
optimizer counts and final-only evaluation. Engineering tests use explicit mock
admission and pytest-owned scratch, never final evaluation IDs or result launches.
Independent engineering review covers high-risk numerical/info/identity paths.
Stop dependent implementation if actual source contradicts the question or
comparator and return the evidence to Root; ordinary in-scope fixes need no ACK.

### Selected advice and implemented details

Root published the complete [Oracle, independent review and disposition](../../archive/2026-09-29/RESEARCH-availability-expansion-selection.md)
at `47e8c3cdc`; DM read the whole answer and adopts all four corrections. No core
premise or comparator was contradicted by source reconstruction. The current row
is exploring with exact launch lead `Codex DM (native child)`. Root owns the
initial remote canonical-control synchronization; this is not a per-fit approval.

The bounded Implementer's public predictor returned with12 focused passing
checks. DM read both files and accepted the implementation subject to integration
and independent engineering review. P's active branch nominally lets the returned
owner move from the current boundary, while the absent branch leaves it frozen;
the lawful posterior mixes the sparse endpoint predictions. This approximates
return-time trajectories in addition to future guards and association. Its native
service env contains public arrays, static S7-S1 configuration and a local public
availability mask, never a G0 source or event ledger. Uncomputed zero-weight branch
readings are explicitly null rather than imputed service. Near-exact score ties
use fixed tolerance1e-10, then S incumbent, reserve travel and category index.

The496 normalized L features contain the actual float32 map and the same public
S-incumbent category, as well as current public telemetry and issued targets.
The absence-age field freezes at the observed duration after return; while absent
it is exactly current clock minus observed leave clock. Both roles can use the
public clock. Categorical aliases remain possible at reached targets and are
not removed from the16-output sampling law. PPO uses orthogonal initialization,
Adam's standard epsilon, shared two-layer tanh body, actor output gain .01 and
value gain1. The value loss is half mean squared error with coefficient .5;
advantages normalize over each16-episode collection. Four equal-as-possible
minibatches retain every tail row once per epoch. Separate streams address
world generation, policy sampling and minibatch permutations. No learned prefix
rows and no evaluation normalization updates are introduced.

Forecast diagnostics compare the nominal service at future boundary t+h to the
latest completed native-step service, from step t+h-1. At a lifecycle boundary
these can have different availability; every prediction labels these clocks and
whether an event lies exactly there. Errors also include subsequent replanning.
They diagnose the deployed sparse forecast and are not calibrated exact-suffix
errors. No extra native or counterfactual panel is added to obtain them.

Initial integration checks exposed a feature-size arithmetic typo (596 instead
of496) and a missing scientific-venv PATH entry for ninja before complete native
tests ran. Both were corrected without a result launch or environment install.
The subsequent19-check suite passed in46.01s, including complete500-step S,
hold-policy and P paths on engineering world91723, native reward/availability
timing and per-step S readiness. No final evaluation world was used. A separate
engineering review and saved-output-reader checks are in progress; these are
correctness work, not a positive scientific screening gate.

### Engineering acceptance and inherited-host description correction

Registered independent Reviewer `/root/dm_availability_recovery/b01_engineering_review`
read the contract and actual files in a separate context (`fork_turns=none`). It
independently ran15 focused tests and the event-window equivalence test. DM's
final complete suite passed22 tests in42.53s, covering full native S/L/P paths,
saved-reader reconstruction and corruption detection. A near-zero motion issue
found by the independent reader fixture was repaired in predictor/readback:
native horizontal norm<=1e-8 means exactly zero velocity. Real execution already
used the native transducer. The Reviewer inspected that repair and the final
forecast clock labels and reports no remaining material defect in the new code.
Its initial event-window suspicion was explicitly withdrawn after reading
`RECOVERY_WINDOW_EXTENSION=59`; both native and new windows are [O,R+60).

The Reviewer did identify a real **inherited source-description correction**.
The earlier prospective phrase "radio ... disabled" is too strong if it means
all radio emission/interference is removed. `routed_core.py` passes all eight
positions to the native radio batch; `uav_geometry_backend.cpp` includes each
other UAV's geometric interference, with nonzero FDMA leakage (`aclr_db=45`).
Unavailable transmitter rows, link endpoints and delivered service are masked,
and motion is disabled, but its geometric interference contribution remains.
The public P model inherits that same behavior. A dedicated fixed-geometry
availability-toggle test passed in3.46s: active-row SINR is exactly unchanged,
while the unavailable row has zero access service. This is a source-correctness
fixture, not an extra result panel or a physical-removal counterfactual.

DM promptly returned this contradicted literal premise to Root with the source
evidence and recommends retaining the native service/routing-availability
question with this limitation disclosed. Root is consulting the same independent
scientific reviewer only on its implication. No core physics, arms, duration,
seeds or action set changed; no result launch has occurred. This narrow premise
is being resolved before launch. Engineering acceptance is not scientific
acceptance of a changed host description. G0 environment/geometry/controllers,
native reward/routed core and C++ radio bytes remain unchanged from `fed55fd0e`.

The final launch-contract check found that the admission validator requires a
literal direction string in the guarded call, not the equal-valued module
constant. `runner.py` now passes `direction="uav_availability_recovery"` literally;
the new regression invokes the actual launcher AST validator. This and the
existing missing-admission check pass (2 tests, 1.92s). The same independent
engineering Reviewer inspected this narrow delta and found no material issue;
DM accepts it. Admission still precedes all output and scientific side effects.
Normal remote `git fetch --no-tags origin main` made no progress and exited124
at its35s timeout, before any launch or claim. Exact published-source objects
will be transferred over SSH if needed, without changing canonical sparse
selection, existing dirty outputs or accepted workers.

### Scoped scientific review: native interference correction

Root returned the same independent scientific Reviewer's complete focused answer
below. This was a source-grounded implication review, not a repeated selection
round or an empirical panel.

> **Retain, With Corrected Host Scope**
> The source confirms the contradiction. `envs/pettingzoo/relay/routed_core.py:2728` passes all eight positions into the radio calculation without an availability mask. The C++ interference loops (`envs/pettingzoo/native/uav_geometry_backend.cpp:299`) retain the unavailable UAV's contribution wherever the distance condition permits. Its desired-service SINR row is masked afterward; routing endpoints and motion are separately disabled.
>
> Our earlier "no radio" wording was too strong. Describe G0 as:
> Temporary motion, service and routing unavailability, with the unavailable UAV's position retained in the native interference model. This is not physical removal or complete transmitter shutdown.
>
> This changes the physical interpretation, not the selected comparison's usefulness. Removing a service/relay endpoint still creates a vacancy and changes useful connectivity. Joint reserve placement can still trade vacancy repair against relay support and subsequent return. P's public snapshot model preserves the same interference law, so this discovery does not give L an information or physics advantage.
>
> However, retained interference does not simply cancel between arms: reserve movements change receivers, desired links and routing. It could alter which deployment is beneficial. Therefore, any gain supports the complete controller package under this native unavailability model, not a pure backhaul-connectivity mechanism or effectiveness under a real transmitter outage. The45dB leakage attenuation alone does not establish negligible influence.
>
> Keep the planned fits, arms and endpoints unchanged. Correct the notebook and eventual result wording; retain the proposed correctness fixture establishing service exclusion alongside persistent native interference. No shared-core alteration, additional arm or preliminary scientific study is warranted by this fact alone.
>
> I checked the access, air-link and base-link interference paths, G0 masks and P's public snapshot construction. I did not measure interference magnitude or run a model.
>
> **MATERIAL_DISSENT:no.** Retain the study with the explicit host correction; exclude full-radio-outage and physical-removal claims.

Root adopts that disposition; DM accepts the changed physical interpretation and
the unchanged comparison. There is no remaining scientific hold. The fixed
geometry toggle fixture is retained; it measures service exclusion and active-row
SINR invariance to the availability toggle, not the magnitude or cross-arm
irrelevance of retained interference. Earlier literal radio-off wording is
superseded by this entry. No pure-backhaul attribution or real-transmitter-outage
claim will follow the planned native package comparison.

### Execution destination before any acceptance

The complete source/contract is published at
`a46eea11b48018e3d58699f829bd8107a472f30c`. Preferred `wsl_4070` remains reachable
over SSH, but direct origin reads are unavailable: the fetch timed out at35s,
then `git ls-remote --heads origin refs/heads/main` timed out at20s and again
after a full65s allowance, all exit124 with no output. An SSH delta bundle of the
already-published commit imported successfully and moved only `origin/main` from
`570fd4564` to `a46eea11b`; canonical HEAD stayed570fd4564. Its automatic Git
maintenance reported an existing gc.log / missing-tree-object problem; this was
not repaired or converted into a scientific failure. Canonical sparse selection
and all five pre-existing dirty launch-status hashes are unchanged. Root retains
canonical-control synchronization ownership.

No remote launcher was invoked: zero claims, accepted workers, fits or result
steps exist for this study on that node. Because the fresh published-control
query cannot complete there, DM selects the configured **local_linux** fallback,
one CPU worker with one numeric thread, using
`/home/fires/.venvs/hmasd-linux-cpu/bin/python` and normal fresh actual-node
admission. This changes the prospective runtime environment, not a running
operation or the frozen scientific exposure. All3 fit seeds,1536 training worlds,
64 evaluation worlds, native H500,1536 optimizer updates and960000 steps remain
fixed. Actual Python/NumPy/Torch versions and native timings will be recorded;
no universal cross-host bit-equality or unmeasured runtime prediction is claimed.
The prior native crash evidence still applies as a technical-risk constraint,
and no automatic replacement run is authorized. Final output will be
`runs/uav_availability_recovery/b01_joint_reserve_a01/` on the admitted local node.

### Accepted B01 operation and observation

The local kernel accepted B01 at2026-09-29T15:07:31Z. The canonical recovery
identity is the [native manifest](../../../../runs/uav_availability_recovery/b01_joint_reserve_a01/launch-manifest.json),
with [actual-node preflight](../../../../runs/uav_availability_recovery/b01_joint_reserve_a01/admission-preflight.json)
and [fixed runtime config](../../../../runs/uav_availability_recovery/b01_joint_reserve_a01/config.json).
The fresh memory reading was10,240,045,056 available bytes against a4GiB floor.
The runtime is Python3.10.20, NumPy1.26.3 and Torch2.7.0+cpu. No remote attempt
was accepted and no worker was migrated. Source publication's push reported a
ref-lock conflict, but a fresh direct origin lookup confirmed the exact commit
`b60b71e00d3b3b1c420cbff3b3bf03a805f4c14a` was already published; the kernel
then independently verified the current published controls and source.

`tools/hmasd_wait.py` generation1 observes that same native operation using the
direction-owned request in `temp/directions/uav_availability_recovery/`.
First drain at15:08:03Z confirms consistent accepted identity, live supervisor
and live scientific runner, with no exit witness yet. The native DM child stays
active through deterministic waits and same-handle drain/rearm. Registration
does not imply a future unloaded-child wake, and launch acceptance is not a
scientifically read result. No scope or exposure change is made during collection.

Both now-unused `source-transfer/a46eea11b.bundle` scratch containers were deleted
after import, one locally and one on the configured remote. Allocated usage fell
from217,088 bytes to zero for each exact container, reclaiming434,176 bytes in
total across the two hosts. Both targets are verified absent. No required source,
raw scientific evidence, canonical control, other direction file or process was
removed; published source objects remain in Git.

At the first1500s checkpoint the same runner remains healthy:118 complete episodes
of fit1 at about27.8min elapsed, one native thread,461,532KiB RSS and92.6% process
CPU. This is an initial workload-specific rate, not a completion-time promise or
permission to change exposure. The observer's App wake returned exit1 with the
known unloaded-child queue rejection (`-32600`); process observation itself was
successful and consistent. The still-active DM turn drained checkpoint
`ebe3f0c9d7397378618fb27c` and rearmed the same operation from generation1 to2.
No worker was restarted or duplicated. Later unchanged checkpoints remain in the
same deterministic observer's state and are consolidated at readback.

The17:16Z checkpoint retains the same accepted worker. Fit2026092911 completed
all512 episodes /256000 native steps /512 optimizer updates in6398.206s wall
and6224.749s CPU (1.73 CPU-h); source construction used59.021s wall. Fit2 had143
completed episodes when inspected. Evaluation had not started. These are
collection and cost facts only, not an outcome-based intervention or result
verdict. Generations2 through5 each observed a consistent live operation, met
the same queue-delivery rejection, and were consumed/rearmed; generation6 is
active. The frozen exposure and worker are unchanged.

<a id="b01-complete-native-reading"></a>
### B01 complete native reading, 2026-09-29

The same accepted worker exited0 at20:50:40Z. Observer generations1 through13
delivered consistent live checkpoints; generation14 observed a valid terminal
witness and absent runner/supervisor. Every App queue delivery encountered the
documented `-32600` child limitation; the active DM drained and rearmed the same
handle, never a replacement worker. Terminal event `0f67513c6d29d4a75ea04703`
was consumed into generation15, then observation was stopped with work unchanged.
See the [OS exit witness](../../../../runs/uav_availability_recovery/b01_joint_reserve_a01/process-exit.json),
[summary](../../../../runs/uav_availability_recovery/b01_joint_reserve_a01/summary.json),
[per-world reading](../../../../runs/uav_availability_recovery/b01_joint_reserve_a01/perworld.json)
and [curves](../../../../runs/uav_availability_recovery/b01_joint_reserve_a01/curves.json).

The published `read_saved.py` completed over all1932 manifest-listed files,
41,049,062 bytes, with maximum native/accounting reconstruction error3.55e-15.
It verified1536 training and384 evaluation episodes,960000 native steps,
1536 optimizer updates, disjoint training/evaluation world addresses,320 exact
pre-event comparisons, source identity, macro interval sums, native gamma.99 and
the planned availability/decision clocks. All three checkpoint optimizer counts
are512, with parameter displacement norms5.082366 /5.293719 /4.904813. This is
verified complete collection, not technical missingness or an inactive optimizer.
The [reader result](../../../../runs/uav_availability_recovery/b01_joint_reserve_a01/reading.json)
does not itself decide scientific usefulness.

The complete primary native means are:

| Final arm | Native J | Mean QoS | J minus P | QoS minus P | J minus S | G0 event catastrophe worlds |
|---|---:|---:|---:|---:|---:|---:|
| L, seed2026092911 | 484.704855 | .981389710 | -8.967013 | -.017934025 | -8.888627 | 41/64 |
| L, seed2026092912 | 484.704855 | .981389710 | -8.967013 | -.017934025 | -8.888627 | 41/64 |
| L, seed2026092913 | 494.010000 | 1.000000000 | +.338132 | +.000676265 | +.416518 | 0/64 |
| P | 493.671868 | .999323735 | 0 | 0 | +.078385 | 14/64 |
| S | 493.593482 | .999166964 | -.078385 | -.000156771 | 0 | 16/64 |
| Shared no-event S reference | 494.010000 | 1.000000000 | reference only | reference only | reference only | 0/64 |

Across the three independent training units, mean L-P is -5.865298 J /
-.011730595 QoS; descriptive df2 intervals are [-19.210900,+7.480305] and
[-.038421801,+.014960610]. Mean L-S is -5.786912 J /-.011573824 QoS with
similarly unresolved df2 uncertainty. Two fits are worse than both ordinary
arms in every evaluation world. Their worst L-P loss is world2026093011:
-18.668012 J /-.037336025 QoS. The positive third fit improves24 worlds and
ties40 against P; it improves27 and ties37 against S, with no adverse world.
Its conditional-world L-P J interval is [.213288,.462977], not an interval over
independent training. These mixed fits neither establish equivalence nor a
population-wide inferiority theorem. They do not support adopting this learned
recipe or retrospectively selecting its best seed as a confirmed recipe.

P improves S in exactly3 worlds (2026093042/3052/3064), with J differences
1.75 /2.60 /.666667, and ties the other61. Its mean J difference+.078385 has
conditional t63 interval[-.020504,+.177275]; QoS difference+.000156771 has
interval[-.000041008,+.000354549]. Preserve that limited ordinary benefit and
two fewer registered event catastrophes, without calling P/S equivalent or a
stable material ranking. Deployment computation is not included in native J.

#### What the controllers actually did

Each L/P endpoint made2007 event/t10 decisions over the64 worlds. Seeds11 and12
selected category5, `(vacancy,vacancy)`, at every decision; their positions,
native metrics, user rates, targets, requested actions and executed velocities
are exactly equal in all64 worlds despite distinct fitted parameters. Seed13
selected category3, `(own_stage,hold_current)`, at every decision. This is a
constant deployed command, not observed state-responsive joint recovery.

For seed13, all64 complete position and executed-velocity trajectories are
exactly equal to the no-event S reference, and all native metric arrays are
exactly equal too. After the observed leave, total reserve path length is0 in
every world. The event is real: active masks differ from no-event in5703
member-step entries; delivered user rates differ (up to9Mbps), but remain enough
for native QoS1 and weakest-hotspot service1 at every step. Targets/requested
actions can differ below3e-7m /1e-8 due hold capture and the native near-zero
motion threshold, so command-byte equality is not asserted. This is a native
stationary-service witness under the selected law, not a radio-off simulation,
an absent event, or an added no-dispatch evaluation arm. Its realized constant
action sequence is implementable without learned state conditioning on these
observed worlds; generalization outside them is not established.

The planner's recorded scores illuminate its limitation. Category3(stage,hold)
and category15(both hold) tie the maximum at all2007 decisions. The selected
score is always1; all16 candidates tie at1554 decisions. S's incumbent is among
the maxima at1973 decisions, and P differs from it only34 times. Incumbent-first
tie-breaking selects greater nominal travel than the minimum tied candidate
at1745 decisions, including60 of64 first-leave decisions. These are actual
recorded public forecasts, not extra native rescores. They weaken the premise
that this expensive ordinary comparison excludes a simple non-dispatch account
of the positive learned endpoint. They do not establish the performance of a
new travel-first planner, which was not run.

P's7196 selected endpoint comparisons have mean prediction-minus-realized error
.000870459 and RMSE.00625270. These use the declared boundary/completed-step
clock difference and include subsequent replanning, so they are not exact-suffix
calibration estimates. Small mean forecast error does not erase the tie-rule
failure or establish decision value.

#### Complete service and tails

Pre-event native QoS and weakest-hotspot service equal1 for every arm. Mean QoS
in absence /rejoin60 /post windows is:

| Arm | Absence | Rejoin60 | Post |
|---|---:|---:|---:|
| L11 and L12 | .992199440 | .959201821 | .959162884 |
| L13 | 1 | 1 | 1 |
| P | .996689799 | .999238281 | 1 |
| S | .995953322 | .999118924 | 1 |

For L11/L12, weakest-hotspot service in those windows averages .860783 /
.463255 /.462500; the complete mean is .748878, and the maximum complete
below.6 streak is292 steps (event-window maximum127). P and S have complete
weakest-service means .991869 and .989988, maximum below.6 streaks34 and39.
The G0 event catastrophe is the registered below.6 streak lasting at least10,
not a physical safety certificate. J_event means are .726213 for L11/L12,
1 for L13, .975698 for P and .970025 for S. No-event J_event1 /deficit0 retain
their inherited normalization and are not the proof of stationary service;
the actual per-step native arrays provide that proof on this panel.

Native backhaul-guard blocked-action means per episode are456.1875 for L11/L12,
0 for L13,11.359375 for P and12.75 for S. Reserve motion-modified row totals
are27517 for each bad L endpoint,103 for L13/no-event,1224 for P and1277 for S;
motion modifications are not interchangeable with guard blocks. The bad L
endpoints still travel5091.459m after leave on average, versus4398.429m for P,
4584.117m for S and0 for L13. Thus action application and harmful native motion
occurred; neither blanket nonactivation nor complete guard suppression explains
away the adverse result. The data do not isolate interference, routing,
association or guard mediation as the unique cause.

The retained native graph-potential delta sum happens to be exactly -5.99 in
every evaluated episode, so J differences on this panel equal500 times mean-QoS
differences. This is an observed panel property, not a changed native reward or
a general J=QoS identity. Return penalties, cutoff and depletion are zero under
the selected battery-off host, not evidence for battery-risk robustness.

Training sampled the full action library and all fitted parameters moved. The
final policies retain substantial categorical entropy (evaluation means2.436 /
2.644 /2.343 nats); deterministic decoding nevertheless selects one category per
fit everywhere. The first/last64 training-episode mean J is492.734/491.606,
493.397/492.585 and492.802/493.666 respectively. Those are different training
worlds, not matched initial/final evaluation. The curves support finite-fit
unreliability, not a diagnosis that more training, rescaling or another head
would necessarily repair it.

Actual runner cost is20586.016s wall (5.718h),20408.955 CPU-s (5.669h), with
peak RSS468100KiB for the single scientific worker. Three fitting CPU costs are
6224.749 /4771.545 /5041.922s. P used121856 native radio/service snapshots,
below270336's declared upper bound; its64 episode evaluations used1370.725 CPU-s
versus591.683 for S, with773.882s planner wall time included. Source initialization
retains the full1600 constructions and129024000 assignment-candidate count.
Engineering/review and saved-reader CPU/wall were not separately metered and are
not imputed as zero. There were no failures, missing cells, extra fits, diagnostic
native worlds or retries in B01.

A separate-context registered Scientific Reviewer is independently reconstructing
the completed evidence. DM's provisional judgment is to retain the stationary
capability and adverse seed-specific behavior, reject learned-recipe adoption,
and stop additional investment in this exact native recipe. The full review and
resolved next-action choice follow below; no successor is being launched.

### Independent scientific reading and resolved investment

Registered Reviewer `/root/dm_availability_recovery/b01_scientific_reading`
received the actual question, fixed inputs, original positive/adverse sources
and completed outputs in a fresh context (`fork_turns=none`), without this DM's
interpretation. It reconstructed the decisive results before reading the old
selection advice. Its complete returned answer is retained here:

> Recommend **retaining the conditional positive and simple non-dispatch behavior, stopping further B01 learning or planner refinement, and keeping the broader recovery question in reserve**. The complete result weakens the premise that this G0 task needs adaptive reserve deployment.
>
> No DM/Root conversation or proposed result explanation was supplied. I reconstructed the endpoints and decisive behaviors before reading the archived Oracle/reviewer recommendations. General memory guidance was injected; the targeted memory search found no relevant entry.
>
> I independently checked the frozen source `b60b71e00d3b3b1c420cbff3b3bf03a805f4c14a`, launch/exit/configuration, all **384 evaluation NPZ files**, their hashes, source geometry/map bindings, native service reconstruction, actual availability masks, and consequential contrasts. I also checked all training episode records and curves, six sampled training trajectories, and all six initialization/final checkpoints. Each fit has512 optimizer updates and distinct parameter movement; training worlds are disjoint and exclude evaluation worlds. The DM's broader1,932-file verification remains its complete reading.
>
> The observed complete endpoints are:
>
> | Controller | Native J | Mean QoS | Weakest-hotspot service | Event catastrophes |
> |---|---:|---:|---:|---:|
> | S | 493.593482 | .999166964 | .9899875 | 16/64 |
> | P | 493.671868 | .999323735 | .9918688 | 14/64 |
> | L seed2026092911 | 484.704855 | .981389710 | .7488781 | 41/64 |
> | L seed2026092912 | 484.704855 | .981389710 | .7488781 | 41/64 |
> | L seed2026092913 | 494.010000 | 1.000000000 | 1.0000000 | 0/64 |
>
> Fits11 and12 lose to P and S in **every world**. Each L-P mean is -8.967013 J and -.017934025 QoS. Fit13 genuinely exceeds P on24 worlds, ties on40, and never loses; its means are +.338132 J and +.000676265 QoS. It also exceeds S on27 worlds. Preserve that positive rather than describing all learning as ineffective.
>
> Across the three training units, however, mean L-P is -5.865298 J and -.011730595 QoS. The descriptive t2 J interval is [-19.210900,+7.480305]. This neither establishes a stable learning advantage nor equivalence. The64 common worlds are conditional evaluations, not additional training replications.
>
> The decisive diagnosis comes from actual choices:
>
> - Fits11/12 issue **category5, both reserves toward the vacancy**, at all2,007 evaluated decisions each. Their native metric trajectories coincide. These are active adverse interventions: mean reserve travel is5,112.72m and guard blocks456.19, versus P's4,419.69m and11.36. Loss persists after recovery: post-window QoS is .95916 and weakest service .4625, while P/S recover to1. Guard suppression alone does not identify the causal mechanism.
> - Fit13 issues **category3, own-stage/hold-current**, at all2,007 decisions. It makes zero reserve movement after onset. Every world's positions and native metric arrays equal the no-event S trajectory, despite the genuine unavailable member having zero association and motion during its absence. Actual service arrays confirm the positive; it is not inferred from the no-event `J_event=1` normalization.
> - Training exposed every category hundreds or thousands of times per fit, with approximately16,000 macro decisions each. Sparse category exposure is therefore not the explanation. High sampled entropy alongside constant deterministic outputs is consequential, but it does not identify an optimizer or decoding repair. Without initialization evaluation, parameter movement cannot establish that fit13's endpoint improved over its own initial policy.
>
> The strongest simpler explanation is **sufficient service without dispatch, combined with harmful discretionary movement**. The positive endpoint realizes a constant ordinary command on the entire evaluated panel. It supports a useful capability and a simpler future comparator; it does not demonstrate a need for state-dependent learned recovery.
>
> P's saved predictions reinforce this interpretation. Category3 and both-hold tie for its best score at **all2,007 decisions**. All16 scores tie at1,554 decisions; its incumbent-first rule chooses S's command1,973 times. Only34 choices depart from that incumbent, across four worlds, and complete P-S gains occur in just three. P-S is +.078385 J, with descriptive interval[-.020504,+.177275]. Thus ordinary forecasting has specific useful cases, but these data do not warrant default replacement of S or additional planner investment. A small forecast error also cannot validate its ranking or transient service predictions.
>
> Native reward accounting remains intact. On this particular panel every graph-potential sum is -5.99, so the observed J differences equal cumulative QoS differences. That is an empirical property of these trajectories, not a general policy-independent PBRS identity.
>
> The prior constructive prediction concerned useful joint placement and return. B01 instead shows that retained placement already satisfies the native service objective across all sampled events, while repeated joint dispatch can worsen both recovery and the remaining horizon. The original exploratory purchase was reasonable under its stated uncertainty; its result now changes the investment case. The S4 timing result and both N7 learning pairs remain relevant contrary evidence, not pooled replications or proof of a common failure cause. I checked their original summary/episode outputs; I did not reopen their full native trajectories.
>
> Retain the checkpoints, native positive/adverse evidence, simple stage/hold behavior, and P's specific improvements. Update the directly affected shared understanding: **observed member unavailability does not itself establish consequential service-recovery demand; executed response can be the source of loss**. Private memory, map value, broader churn and decentralized learning remain untested. The unavailable position's interference remains part of this host and does not cancel across moving controllers.
>
> Actual scientific cost was **960,000 native steps, three fits,121,856 planner snapshots,5.718 worker wall-hours and5.669 CPU-hours**. Fits consumed4.504 wall-hours; the remaining worker work consumed1.214 hours. P's planner alone used773.88 seconds. Peak worker RSS was468,100KiB. Engineering, remote-query failures, publication and review are additional and incompletely measured; deployment telemetry/acquisition cost remains unmeasured.
>
> The smallest useful complete observation at this boundary was the saved-data reconstruction above, now completed with zero new fits or native evaluations. I recommend no confirmation panel, extra seed, fault strengthening or automatic optimizer repair. Another identical fit could test recurrence, but it would not address the missing need for adaptive deployment demonstrated here.
>
> A constructive re-entry remains possible when a concrete deployment contract makes conditional reserve choices worth studying. Its comparison should retain the simple non-dispatch alternative and give ordinary control any added information/resources. If that simple controller remains sufficient, simplify; if ordinary conditional deployment helps, retain that capability; if learned control adds complete benefit beyond both, reconsider learning investment. No such new contract or sufficiently consequential adoption decision is currently supplied, so reserve/idle is justified without declaring availability recovery exhausted.
>
> **MATERIAL_DISSENT: no** against completing and publishing B01 and ending this recipe's investment. The direct evidence does object to promoting the single positive fit into a reliable learned-coordination claim or treating further fits as the default next action.

DM accepts the evidence reconstruction and recommendation, including the limit
on claiming learning progress without initial-policy evaluation. No separate Pro
round is added: this independent source-level review resolves the current
interpretation and investment choice without an unresolved expertise gap.

**Resolved choice: retain the useful behavior and evidence, end investment in the
exact B01 recipe, place the broader question in reserve/idle.** No additional fit,
confirmation panel, planner repair, stronger event or enlarged action set is
selected. The observation that changes the explanation is not merely a negative
average: one evaluated stationary endpoint preserves the complete service ceiling
under all64 actual events, while the failed learned endpoints and ordinary
dispatch introduce avoidable losses. P's small improvements remain a real
conditional ordinary capability, but its incumbent tie rule does not exclude the
simpler non-dispatch alternative. Keep the positive seed13 endpoint as a
conditional capability witness, not a post-hoc validated default or proof that
its optimization improved its own initialization.

The distinctions guiding this stop are:

- **Task opportunity:** the selected native event is real, but adaptive reserve
  deployment is not shown necessary for service on this panel. Retained placement
  already meets the registered demand despite endpoint loss.
- **Representation:** the16-command interface contains a useful stationary
  response. No representation impossibility, new MARL method, private-memory
  need or identified map benefit follows from B01.
- **Finite learning:** three complete fits yield two adverse constant dispatch
  endpoints and one useful constant non-dispatch endpoint. Full support exposure
  and parameter movement distinguish this from no training, but do not diagnose
  a successful optimization repair or broader unlearnability.
- **Complete-package use:** the learned recipe has not earned adoption over P/S;
  P's extra computation has not earned default adoption over S. Preserve the
  stationary witness and all contrary outcomes rather than treating failed
  adoption as absence of every useful capability.

The cheapest useful next observation was the completed saved-data reconstruction,
which directly changed the decision without another model run. Identical repeats
would price recurrence rather than resolve the missing adaptive-deployment need;
changing ties or optimizing PPO on this ceiling-level host would not by itself
make the parent question consequential. Broader recovery remains open. Re-entry
would require a concrete justified deployment contract and a useful choice
between stationary, competent ordinary conditional, and learned reserve control,
with any new information/resource granted to the ordinary comparator as well.
That is a possible future question for Root's allocation, not a demanded positive
pilot, an owner-approval dependency or a presently selected experiment. Current
state is idle with no producer. The S4/N7 adverse evidence, inherited radio scope,
and untouched Claude/paused-direction boundaries remain intact.
