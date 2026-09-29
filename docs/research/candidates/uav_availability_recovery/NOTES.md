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
