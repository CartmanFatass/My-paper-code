# Energy relay imitation

Lead runtime: `Codex DM (independent session)`. Direct DM task
`01a0e0f8-4e3f-70f1-802f-4bf4c2348221`, host `local`, authoring on shared
`main` at `/home/fires/hmasd-wsl`. The operating constitution is the authority.
This notebook is append-only; the DM owns its writing.

## 2026-09-27 — question adoption and B01 reconstruction

The owner-assigned question is whether ordinary demonstration learning, under explicit
lawful information rights, yields useful native closed-loop S7 deployment, and when a
teacher/student visitation difference warrants further study. This takes only the unexecuted
D4 successor from `energy_relay_baselines`. D1's prepared independent SET fits, DM2's accepted
136-episode diagnostic batch, and Claude's accepted resumed SET study and final reading remain
with their owners. No operation is inherited, restarted or duplicated. Initial RESEARCH
registration is being published by Root; preparation can proceed before that registration,
but result execution must see this direction actively assigned to this runtime.

Evidence used: [corrected source report](../../../inbox/2026-09-27-energy-relay-benchmark-report-and-directions-for-codex.md)
(correction `003d4d369`), [benchmark notebook](../energy_relay_benchmark/NOTES.md),
and [current shared background](../../RESEARCH.md), inspected on main at
`eda9fae045607dc6e59133fb1bab8f1569744e08`. The c04 public reading is .406/.404
QoS per step (deterministic/sampled), improving from c03, on one recovered training instance.
Thus the original c03 plateau story is not a premise of this study. H_local's earlier .597
and J 1628 are development context, not outcomes on this study's new worlds. H_local pools
the eight UAVs' legal observations in one planner. It is not eight independent local actors.
Its service and return-risk outcomes must be read together.

The shared service/risk topic changes the design: shield-driven visits can themselves produce
service, energy recovery does not imply complete service gain, and a proxy fit does not establish
native utility. Therefore retain the common production shield, teacher and same-model
initialisation, full native J/QoS/return risk, pre-entry/post-input phases, and adverse worlds.
The representation/learning topic precludes treating BC success or failure as a capacity bound:
SET receives current own observations plus a k=10 held central state/joint-observation snapshot;
H_local's current pooled observations and planner history are a different information structure.

Root's completed independent ResearchCritic recommendation was supplied in the assignment:
`MATERIAL_DISSENT: no` on separating this question; begin with BC-only closed-loop deployment,
not automatic long RL or a representation-ceiling claim. Reuse that question-level review.
The suggested first comparison is fresh 32 H_local demonstration episodes, one fixed-budget
SET actor BC fit, and teacher/initial/final policies each on the same 32 separate development
worlds: 128 environment episodes, at most 384,000 team transitions. These are proposal counts,
not an accepted launch. The executable protocol below will bind training and data semantics
before publication and admission; any material scientific change needs targeted review.
No distinct Pro expertise or unresolved disagreement currently justifies another consultation.

Neither this DM nor its helpers may read, enumerate or use the contents of
`runs/energy_relay_benchmark/b02_holdout_refs_a01`. Seeds 957001–957032 are excluded
from all collection, fitting, evaluation and tests. Later disclosure would not make those
worlds a fresh test set. Tests use short, unrelated fixture worlds, never scientific panels.

Current scientific execution: 0 fits, 0 collection/evaluation episodes. The existing published
optional evaluator observer (`ef5c35b77`) is sufficient for new teacher inputs/actions;
DM2 remains the only writer of that shared interface. No shared host fork is planned.

### B01 intended reading and cost boundary

BC closed-loop service/J improvement with its risk costs supports a supervised starting
point for this training instance. Good offline imitation together with poor closed-loop
deployment increases the interest of visitation/feedback effects but does not uniquely diagnose
them; teacher-world generalisation, information cadence and optimisation remain distinguishable
limitations. Poor offline and online outcomes do not show a representation limit. Mixed
service/risk outcomes remain conflicts, and early terminations or failed worlds are retained.
No result automatically buys 1.2M RL, DAgger, extra seeds or checkpoint selection.

Environment work is bounded by 32 × 3000 collection plus 3 × 32 × 3000 evaluation steps.
Older 8-worker evaluation timings suggest tens of minutes, not a reliable current quote under
contention. BC replay/updates, complete input storage, engineering and offline diagnostics
will be explicitly counted in the frozen protocol. Fit wall, batch wall and worker RSS scope
will be measured; unmeasured quantities remain unknown. Bulk outputs stay in one durable
direction run location with hashes, while compact identity/config/summary/status are published.

## 2026-09-27 — B01 prospective protocol and L0 implementation scope

**Comparison fixed before data.** Fresh demonstration worlds 967001–967032; separate new
development evaluation worlds 968001–968032. Model initialisation seed 929031; episode-order
RNG 929032. All 32 demonstrations are training data, no checkpoint selection or tuning split.
Evaluate H_local, that same model's saved initialisation, and the final BC endpoint on all
32 evaluation worlds, deterministically. This is one exploratory training instance, not
confirmation and not comparison against Claude's separately trained instance. No stochastic
policy claim is attempted: BC fits the deterministic proposal, not its action variance.

All environment work uses the existing S7-S2/H3000, 8 UAVs, production shield enter 0/exit .05,
native backhaul guard, reward (lambda_return=2, lambda_e=1), charging allocation and termination.
Use `HeuristicParams(information="local")` unchanged (six service targets, 100m altitude,
30m/s cruise, replan 30, station-ring search). Teacher inputs are pooled legal observations and
its retained planner state. SET retains the published central snapshot model, n_Z=n_z=1 and
k=10. Its actor sees current own observation, held central state and held joint observations,
and ego index; central state is privileged information, explicitly granted here. This is not
a matched-information teacher/student representation comparison. No critic or RL update occurs.

Collect pre-step raw observations, central state, teacher proposal, submitted shield action,
and native trace/episode endings through the published observer seam. This records complete
legal inputs and the granted central input. No additional actor forward, RNG draw or controller
step is made by observation. Preserve proposal and submission as distinct arrays. The target is
the teacher's pre-shield proposal at every real transition, including shield-active steps.
Never train against the submitted action. The student receives the same production shield at
deployment. Full raw state may be stored once per step for simplicity; no duplicate t+1 copy
is needed because replay uses only pre-step fields.

**One BC fit, fixed horizon.** Ten epochs over the 32 complete demonstration sequences;
shuffle episode order with the declared independent NumPy RNG each epoch, batch four episodes
(32 episode-agent trajectories), keep primitive-time order. TBPTT chunks of 128 steps retain
student recurrent values across chunks and detach only the graph; zero hidden only at episode
start and mask padding/terminal tails. Updating each chunk means carried hidden values were
produced with the preceding parameters; this declared ordinary TBPTT approximation is not
claimed to be full-episode exact-gradient training. Hold central inputs at episode steps
0,10,20,..., using the same normalisation-off and no-affine contract as SET. Input reconstruction
must match the actual online actor call on a short unrelated native fixture across t=10.

Regress the actual native `R_Actor.forward(..., deterministic=True)` action, whose effective
S7 config uses `tanh_gaussian`, to proposal using mean squared error over valid agents, action
dimensions and steps. Do not bypass tanh with raw Gaussian means. Reuse the native actor Adam
optimizer, learning rate 1e-4, weight decay 0 and max_grad_norm from the unchanged SET config;
no schedules. Logstd gets no loss/update and must remain equal to initialisation; critic,
coordinator, normalisers and other modules stay unchanged. Record actor parameter movement,
actual optimizer steps and gradient finite checks. At H3000 this is at most 1,920 updates and
7,680,000 agent-transition loss exposures; shorter real episodes reduce work, never acquire
replacement worlds. The final tenth-epoch checkpoint is the only trained endpoint.

**Fixed diagnostics, never selection.** Read initial/final deterministic MSE (overall and
per action dimension) by complete recurrent replay on demonstration sequences and on the
separate teacher evaluation trajectories. Replay uses zero episode-start states and fixed
weights; no parameter update or reset at chunk boundaries. This is at most another 3,072,000
agent-transition forward exposures (2 policies × 64 teacher episodes × 3000 × 8).
Teacher-evaluation inputs are collected only after fitting and never enter training, statistics
normalisation or hyperparameter choice. Their offline error distinguishes simple failure to
generalise to other teacher worlds from a training-data-only fit. Good offline error still
does not uniquely identify closed-loop distribution shift as the cause of any deployment loss.

Primary reading is per-world native QoS/step and raw J, BC minus its own initialisation, with
teacher beside both. Retain return cost, cutoff/depletion, episode minimum battery and its
world lower tail, charging input, shield mode/entries, first-service and phase measures,
zero-service worlds, actual length and termination type. Publish every world and paired signed
difference; world SE/descriptive intervals are conditional on this one training instance,
never a training-population n. Service gain with worse risk is reported as a conflict. Use
the old .03 QoS scale only as descriptive context, not a confirmation threshold or a selection
rule. A failed world is recorded and prevents a complete-panel verdict; no silent drop/retry.

**Execution/cost.** One sequential admitted batch: collection → one fit → teacher/init/final
evaluation and fixed replay readings. Collection/evaluation upper bound 128 episodes/384k
environment transitions; evaluation has zero optimizer updates. CPU environment workers four,
one Torch/BLAS thread each; fit on configured wsl_4070 CUDA with one Torch thread, TF32 off.
No environment evaluator runs concurrently with the BC fit inside this batch. Expected wall
is approximately 45–90 minutes of environment work at four workers under current contention;
BC/replay wall is unmeasured, provisionally tens of minutes, not promised half-hour completion.
The exact byte footprint is derived from runtime dimensions, with at most four episodes loaded
for training at once. Estimate order 1–2 GB uncompressed inputs plus native traces and two
checkpoints; compressed byte counts and process peak RSS will be measured. Scientific budget
does not change if this engineering estimate is exceeded. No wall-based scientific endpoint.

**L0.** Implement only `experiments/candidates/energy_relay_imitation/b01/` plus its admitted
runner `experiments/candidates/energy_relay_imitation/run_b01.py` and mirrored owned tests.
Reuse benchmark B01 evaluator/observer, feedback, heuristic and B02 config/checkpoint interfaces;
do not edit shared evaluator, learner, trainer, another direction, NOTES, or Git from helpers.
Deliver the above complete collection/training/evaluation/readout with compact config, status,
per-world summary, progress and telemetry. Bulk per-world NPZ/checkpoints live under the run's
`raw/`/`checkpoints/` with byte count and SHA256 in existing metadata; do not shuttle bulk arrays
through the process pool or retain duplicate copies. Admission precedes output creation or
scientific imports/effects, and SHA must match. Native model saving plus B01-compatible record
must support exact fingerprint-checked loading of init and final checkpoints. A scientific
exception records stage and counts and stops; no resume/retry switch.

Checks cover input cadence and live actor parity (including actual tanh action), recurrent
chunk continuity/reset, padding and early terminal masking, finite regression gradients and
actor-only movement, unchanged logstd/critic/normaliser, checkpoint roundtrip, disjoint fixed
worlds and forbidden holdout, failed-world retention, and admission ordering. Short unrelated
native fixture seed 41/H12 may cross the t=10 boundary; it is a correctness test, not a panel.
Use pytest-owned scratch under this direction. Independent high-risk engineering review is
required before source acceptance; scientific question-level review above remains applicable.
Stop at a real semantics conflict or test failure and return facts. No extra fit/seed/arm/RL,
no test execution of the actual scientific panels, and no downstream automatic study.

### Registration, full review and engineering preparation

Main `4220ecd4f` now publishes this direction as exploring with the exact lead runtime above
and this task's address. The DM read the complete [independent expansion review and Root
adoption](../../archive/2026-09-27/RESEARCH-four-dm-expansion.md#four-dm-expansion-review),
including its retained dissent against capacity-bound interpretation and automatic long RL.
Its scientific comparison is unchanged by the concrete BC budget above. No Root ACK is needed.

Bounded read-only Scout reconstructed the published source interface. Its initial inference
from the generic Gaussian default was incorrect; the DM checked `Config('S7-S2')` and the
Scout corrected it to effective `tanh_gaussian` before implementation. The protocol uses the
actual bounded deterministic actor output, and a native parity test protects that distinction.
An Implementer owns only this direction's candidate and mirrored test directories; the DM
retains this notebook and acceptance. No helper has touched the sealed data.

Read-only actual-node preparation observed `LAPTOP-U9TDKC8A`, 16,568,721,408 physical bytes,
14,068,523,008 available bytes, GPU 7,658 MiB free, with Claude's resumed training process
still present. This is a feasibility observation, not launch admission or a reservation.
The eventual launcher must obtain a fresh memory check immediately before its child handshake.

Before any data, refine the fixed offline diagnostic to report MSE separately on shield-active
and shield-inactive agent-steps (using the existing native mode trace), alongside overall and
per-dimension values. This adds no forward or label/fit exposure and changes no training weight;
it prevents many simple shield-time proposals from masking poor free-deployment imitation.

### Engineering review and newly published background (before scientific execution)

The DM read the implementer's complete collector/replay/fit/checkpoint/evaluator diff and
focused checks. An independent `hmasd-reviewer`, in a separate context, traced the same path
and independently passed the original seven CPU checks (9.24s). It found no additional
material learner, information-flow, RNG or checkpoint issue, but retained three implementation
findings: native launch metadata/atomic temporary files must coexist with the candidate output
guard (P1); failed-world work must not be represented as an exact zero and native completion
facts must survive persistence failure (P2); promised BLAS/OpenMP thread caps must be set before
scientific imports and inherited by workers (P2). The DM accepted all three for repair and
targeted regression checks. No failed scientific launch was incurred; full CUDA/H3000 behavior
is not yet empirically verified by these short CPU correctness fixtures.

Relevant current background changed at `27b796888`: DM2's frozen c00/c03 CPU path comparison
matches the recorded collector/evaluator path; lower sampled wall occupancy did not supply
meaningful mean J gain and worsened risk. This reinforces retaining native service/risk rather
than a wall/saturation proxy. The present BC comparison and deterministic-action scope remain
unchanged: it fits a point proposal and makes no statement about its untrained sampling variance.
The shared optional evaluator seam remains published after DM2 retired its one-off runner;
this candidate imports only the retained benchmark interfaces, not deleted diagnostic runners.

### Prospective execution-resource amendment, 2026-09-27 UTC

Before any scientific launch/data, reduce environment collection/evaluation workers from four
to **two**, retaining one Torch/BLAS thread each. The four-episode BC minibatch, all worlds,
seeds, epochs, update/exposure bounds, action modes and CUDA fitting are unchanged. Each world
is rebuilt independently with its fixed seed and output path; completion order is sorted out
of the readout. This is resource topology, not a new scientific comparator or exposure.

Actual-node read-only measurement found 6,576,672,768 available bytes while Claude training,
its separate eight-worker c05 evaluation, DM1's fresh training and DM4's four-worker S4 panel
were active. That is four concurrent result-bearing operations before ours, conservatively
counting the training and its separate evaluation. Existing learned evaluation workers showed
roughly 0.7–0.8 GB RSS each, and reference workers roughly 0.5 GB. Two of our workers leave a
more credible margin above the configured 4 GiB memory floor; four would be too close under
these conditions. The launcher still performs fresh actual-node admission. Supersede the
earlier 45–90 minute environment estimate with approximately **90–180 minutes** under current
contention, plus unmeasured BC/replay and preparation. This is an estimate, not a stopping rule.

The reviewer additionally identified `ProcessPoolExecutor.submit` failing after some worlds
are already submitted. The accepted repair stops dispatch, preserves the rejected job as
unattempted and submission failure, and drains/account existing futures before returning an
incomplete panel. No accepted world is restarted. Together with unknown failed-world work
bounds this prevents completed or partially executed work disappearing from a failed reading.

### Engineering acceptance before source publication

Final owned candidate suite: **20 passed in 9.29s** (Implementer). Independent Reviewer
verified the substantive input/recurrent/actor/checkpoint path, the repair regressions
(13 passed, 5 deselected in 3.52s), then the final submit-rejection regressions
(2 passed, 18 deselected in 3.91s). Its final disposition: all findings closed; no material
engineering issue or residual launch blocker. Reviewed `study.py` SHA256:
`554222132dde143467219a3f1bd6bb04e0c4904e7b10f6b1ce3381c975425654`.
It also confirmed two environment workers change only concurrency, not the four-episode fit
group, seeds, exposure, policy mode or sorted reading. The DM read and accepts this version.
All checks were CPU/native-short-fixture or mocked-failure checks, not full CUDA/H3000 science.
Actual scientific work still 0 fits and 0 panel episodes before the accepted launch below.

### 2026-09-27 — B01 accepted; same-operation observation

The native kernel accepted the fixed B01 batch at 04:45:34 UTC. The
[manifest](../../../../runs/energy_relay_imitation/b01_bc_a01/launch-manifest.json)
is the authoritative command/source/process/claim record; the
[observed status](../../../../runs/energy_relay_imitation/b01_bc_a01/status-observed.json)
confirmed the recorded runner and supervisor alive and consistent, without an exit witness.
The [actual-node receipt](../../../../runs/energy_relay_imitation/b01_bc_a01/admission-preflight.json)
measured 10,244,784,128 available bytes against the 4 GiB floor. Three other admitted
result operations were alive immediately before submission; this batch makes four under the
owner ceiling of five. The fixed two-worker resource amendment above remains in force.

Remote main fetch succeeded, but whole-checkout fast-forward was refused because another
live direction was writing its tracked summary. That output was preserved. The canonical
pause/state/lead already agreed with fresh published main, and compute config, launcher and
snapshot implementation bytes matched it. The kernel therefore used the published immutable
source through its ordinary snapshot path; no control file, source input or other live run was
rewritten to bypass admission. Non-login Git reads had stalled on missing-object network
fetches; using the configured login network shell resolved that transport issue. Only this
session's verified stalled Git helper was terminated, never a scientific process.

Manifest and preflight were copied and SHA256-verified against the node. Scientific bulk
remains at the manifest output root; acceptance is not a result. Observe this same operation
with the native waiter, then collect, verify and read its terminal artifacts. No resend,
restart, automatic fit extension or new seed is authorized by a checkpoint or wait failure.

## 2026-09-27 — B01 complete: partial mean gain, adverse worlds and nonuniform imitation

### Terminal evidence, integrity and actual cost

The accepted operation exited normally with code 0 at 06:17:40 UTC. The
[terminal status](../../../../runs/energy_relay_imitation/b01_bc_a01/status-terminal.json)
and [exit witness](../../../../runs/energy_relay_imitation/b01_bc_a01/process-exit.json)
agree with its original identity. The [complete summary](../../../../runs/energy_relay_imitation/b01_bc_a01/summary.json)
contains every native world and paired difference; [config](../../../../runs/energy_relay_imitation/b01_bc_a01/config.json),
[progress](../../../../runs/energy_relay_imitation/b01_bc_a01/progress.jsonl) and the two checkpoint
records preserve the fixed execution. No failed world, early termination, dropped world or retry:
all 128 episodes ended at H3000 by native truncation, exactly **384,000 environment transitions**.
One fit completed ten epochs, **1,920 updates / 7,680,000 agent-transition loss exposures**;
the four fixed offline readings used **3,072,000 further agent-transition forwards**, no updates.

The DM independently verified all **128 NPZ files and two full checkpoints** against their
recorded SHA256 and byte counts, checked per-world JSON equality with the summary, and rescored
every native reward/metric sum and ending from raw arrays. Teacher input shapes/finite values,
offline stratum counts and weighted MSE aggregation agree. Every shield-inactive teacher
proposal equals the submitted action; all 573,945 shield-active agent-steps across both teacher
panels changed the proposal on submission. These remain distinct recorded actions.
Only 14 actor state tensors changed between actual checkpoints; logstd and all critic tensors,
coordinator, value normalisers and their non-actor optimizers stayed unchanged. Actor optimizer
steps are 1,920 throughout its populated state. Runtime finite-gradient checks passed and actor
parameter L2 movement was 9.95421. See [artifact verification](../../../../runs/energy_relay_imitation/b01_bc_a01/artifact-verification.json)
and [raw/checkpoint verification](../../../../runs/energy_relay_imitation/b01_bc_a01/native-verification.json).
This verification used no additional fit, environment episode or actor forward.

Study wall was **5,374.94 s / 89.58 min**, including **328.26 s / 5.47 min** fitting. Collection,
teacher, initial and final evaluation panels respectively took 1,499.71 / 1,064.05 / 1,017.78 /
1,262.91 s; preparation/import, transport and this reading are not silently included as measured
study time. Admission-to-exit was approximately 92.11 min. Reported parent/maximum-child/world-worker
peak RSS was 1,441,020 KiB; this is not simultaneous aggregate memory across processes or the node.
All bulk files total 614,544,233 logical bytes / 614,830,080 allocated bytes. The canonical
retained bulk location is `wsl_4070:/home/wu/projects/HMASD/runs/energy_relay_imitation/b01_bc_a01/`;
relative paths, sizes and hashes are in the summary. Only compact outputs were collected locally.
The [stderr](../../../../runs/energy_relay_imitation/b01_bc_a01/stderr.log) contains the existing
singleton skill-logit standard-deviation diagnostics and notices that inactive discriminator
buffers were not saved; it contains no scientific exception. The native metric and parameter
checks above, rather than a clean-looking log, support technical completion.

### Native reading, including all adverse outcomes

The fixed development-world comparison is conditional on **one training instance**. The DM
recomputed the aggregates and paired SEs independently in [reading.json](../../../../runs/energy_relay_imitation/b01_bc_a01/reading.json).
No new threshold, selected checkpoint or selected world was introduced.

| Full H3000 world mean | H_local teacher | Actual initialisation | Final BC |
| --- | ---: | ---: | ---: |
| QoS per step | .580086 | .217423 | .266972 |
| Raw native J | 1532.730 | 617.416 | 756.935 |
| Raw return-constraint cost sum | 88.5065 | 4.5715 | 8.4036 |
| Episode minimum battery ratio | .083022 | .098560 | .099197 |
| Charger input Wh | 367.526 | 174.479 | 214.557 |
| Shield-active UAV-step fraction | .378426 | .184805 | .306353 |
| Shield entry count | 42.1875 | 48.7813 | 108.6563 |
| Guard blocked actions | 2732.06 | 736.81 | 3855.34 |
| Boundary fraction in normal mode | 0 | .160116 | .589672 |
| Altitude-floor fraction in normal mode | .019421 | .988460 | .022514 |
| Zero-service worlds | 0/32 | 1/32 | 5/32 |

BC minus its own initialisation is **+.0495489 QoS/step** (world SE .0309238; descriptive
mean ± 1.96 SE = [−.0110616, +.1101595]) and **+139.5188 J** (SE 93.1461;
[−43.0476, +322.0852]). These intervals describe world variation conditional on the one fit,
not training-population uncertainty or equivalence. QoS signs are **16 positive / 1 zero / 15
negative**; J signs are **15 positive / 17 negative**. The same mean gain therefore does not
make this a reliably improved deployment policy. The worst paired world, **968024**, loses
**.247244 QoS/step and 735.070 J** and becomes zero-service. The largest gain, 968027, adds
.399625 QoS/step and 1192.861 J. All 15 service-loss and 17 J-loss world IDs/differences are
retained in reading.json, with every original world in summary.json.

Final zero-service worlds are **968005, 968006, 968016, 968021 and 968024**; initialisation was
zero only in 968006, so four new zero-service cases coexist with the positive mean. Return cost
increases by **3.83207** on average (SE 2.72436), with increases in **23/32** worlds; 968026
has the largest increase, +51.0335, alongside a .0186788 decline in minimum battery. Mean
minimum battery rises only .0006373 while **17/32** minima fall. The final lower tail begins
.079835 (968020), .082480 (968026), .085798 (968007), versus initial panel minimum .085256.
All three evaluation panels have zero cutoff/depletion events and penalties; this does not
erase the measured return-risk conflict or establish safety.

Teacher-minus-BC QoS is .313114 on average; BC beats teacher QoS in only 968031 and J in
968001/968031. The teacher also carries much larger average return cost and a lower battery
tail, so it is an opportunity comparator with costs, not a risk-free optimum or a matched
information capacity bound. No ranking against Claude's separately trained policy is inferred.

Policy-dependent phase means are retained descriptively: initial→BC pre-entry QoS .080361→
.161933, entry-to-input .224142→.265221, post-input .375771→.362486. These are different
policy-induced windows, not matched causal phases. First-service means among served worlds
are 533.45 steps (31 worlds) and 146.74 (27 worlds); excluding the five BC never-served worlds
would falsely turn that conditional mean into universal service acceleration. The increased
normal-mode boundary occupancy and shield entry/block counts are adverse process observations,
not by themselves a causal diagnosis.

### Fixed offline reading: the overall decrease masks a worsened control stratum

| Proposal MSE, initial → BC | Demonstration trajectories | Separate teacher-evaluation trajectories |
| --- | ---: | ---: |
| Overall | .178120 → .091954 | .176313 → .101468 |
| Shield inactive | .126592 → .132997 | .122161 → .148999 |
| Shield active | .266271 → .021739 | .265258 → .023397 |

The held-out teacher-trajectory action-dimension MSEs (horizontal x/y, vertical, docking) are
**[.147891, .155600, .401746, .0000136] → [.166568, .175979, .062177, .001148]**.
The vertical coordinate improves sharply while the other three worsen. On shield-inactive
held-out agent-steps every dimension worsens, including vertical .044374→.092608. The same
inactive-stratum total error also worsens on demonstrations, so the native weakness is not
adequately described as a well-fitted control rule that only fails on unseen visited states.

Shield-active steps are 36.8898% of demonstration and 37.8426% of teacher-evaluation agent-steps.
In the latter panel, their weighted MSE change is −.0915263 while shield-inactive change
contributes **+.0166815**, yielding the overall −.0748448. The analogous demonstration
contributions are −.0902074 and +.0040417. Thus the aggregate improvement does not establish
successful imitation of the student-controlled phase. It motivates distinguishing loss
allocation/finite optimisation and information/history mismatch from visitation effects;
none is uniquely identified by this completed comparison. Scientific review and the DM's
investment disposition follow below.

### Independent scientific review and DM disposition

Scientific Reviewer `bc_scientific_review` used the registered ResearchCritic role in a fresh
context without inherited DM/Root turns. It reconstructed the prospective protocol and full
native outputs before reading the shared interpretation, independently checked collected-file
hashes and aggregates, and explicitly distinguished its reading of the DM's remote verification
receipts from personally reopening the bulk files. The excluded holdout was not inspected.
Its substantive review is preserved here; the repeated numerical tables are given above.

The review supports a heterogeneous positive mean BC change for this saved initialisation,
not reliable deployment benefit, successful teacher-policy compression, or a visitation-shift
diagnosis. It additionally checked the paired medians: QoS +.002447, J −9.055. Its strongest
simpler explanation is partial acquisition of a height-control habit with poor allocation of
finite fitting effort across consequential parts of the teacher policy. Teacher altitude control
toward 100 m, the vertical-error decrease and the normal-mode altitude-floor reduction support
that candidate explanation, while horizontal errors and boundary occupancy worsen. This is a
supported diagnostic hypothesis, not an identified altitude-mediated causal effect.

The frozen shield replaces all four proposal coordinates while active. Supervising those
teacher proposals was exactly the B01 contract, not an implementation violation. Much of the
measured fitting success therefore concerns proposals that do not directly determine the
executed action at that step. Competition from these supervised examples is a modifiable
candidate contributor, but they may still help near release or through recurrent representations;
removing them could help or hurt. The fact that inactive-stratum error worsens even on training
demonstrations gives finite fitting/objective alignment priority over a pure unseen-visitation
story. Information/history mismatch and new-teacher-world generalisation remain alternatives.
Neither the pooled teacher gap nor central input availability is a matched capacity bound.

The reviewer recommends **one prospectively fixed loss-mask comparison**, starting from the
saved B01 initialisation and retained demonstrations. Keep the order, ten epochs, optimizer,
recurrent processing, input cadence and action interface; retain every step for recurrence,
but remove direct action-regression loss where the production shield replaces the proposal.
Freeze loss normalisation and empty-mask handling. Reuse existing teacher/initial/B01 endpoint
readings on the same 32 development worlds and evaluate only the new endpoint. This is exposed-data
exploration, not replication. Do not add an altitude-only control, extra seeds, rollout aggregation,
RL, DAgger or confirmation as an automatic bundle.

The discriminating prediction is joint: better inactive-stratum imitation on both teacher
panels **and** better complete native deployment than all-transition BC. If both improve,
retain a useful conditional objective intervention without claiming it explains the whole gap.
If inactive imitation improves but native deployment does not, reduce the usefulness assigned
to teacher-distribution MSE and reconsider visitation/feedback without automatically selecting
DAgger. If even training-stratum error does not improve, weaken loss competition rather than
buy more epochs or architecture to rescue it. Service improvement accompanied by worse risk
or additional zero-service failures remains a conflict.

The review's incremental budget is one fit, unchanged full recurrent forward exposure,
4,846,860 unmasked training agent-step exposures, 32 native episodes / at most 96,000 environment
transitions, and 1,536,000 offline replay agent-step exposures. B01 provides 5.47 min fitting and
21.05 min final-evaluation references, with revised-fit/replay/engineering/contending-node costs
not guaranteed by those timings. End-to-end policy latency and aggregate CPU/GPU occupancy
were not fully measured; no computational advantage over H_local is demonstrated.

**MATERIAL_DISSENT: no** — the review's supported object is publication of completed exploratory
B01 within its fixed BC-only scope. No competing post-result investment was supplied; the
review recommends the single new loss-mask comparison and does not itself authorise execution.

**DM decision.** Accept the reconstructed reading and this narrow continuation under the existing
delegated imitation question. B01 is complete and immutable; do not promote its endpoint to a
reliable deployment baseline or purchase an unchanged extra seed. Select B02 below as a distinct
prospective intervention that separates an observed supervision mismatch from a pure visitation
account. This is a scientific choice from new evidence and review, not a waiter-triggered extension
of B01. No unresolved material dissent or distinct Pro benefit remains; no extra Pro round is owed.
The direction retains its question and records the adverse evidence. No result of B02 automatically
authorises another fit, RL, DAgger, hyperparameter sweep or confirmation.

### B01 source and scratch retirement

Compact outputs were collected with matching hashes. The native collector initially refused
because the DM's checkpoint-inspection import had created two `configs/__pycache__` files in the
snapshot; those exact timestamp-verified disposable files were removed. A second refusal concerned
protected process `/proc/660/cwd`; the documented passwordless read-only process scan resolved it.
The collector then previewed and removed only this terminal operation's source snapshot, with
claim/manifest/exit and all 130 bulk artifacts preserved outside it. Refusals and collector receipts
are retained. [Measured cleanup](../../../../runs/energy_relay_imitation/b01_bc_a01/cleanup.json)
confirms source directory and Git registration gone, allocated bytes **796,762,112 → 0** on the
node, approximately 759.85 MiB freed. No backup or duplicate bulk copy was created. Local request
scratch was also removed; the separately measured final empty-directory cleanup freed 8,192 bytes,
without inventing a total for the earlier request-file deletion. The needed B01 implementation
and tests remain for the selected B02 reuse. Native observation was consumed and stopped after
terminal collection; it has no remaining B01 work to wake or restart.

## 2026-09-27 — B02 prospective loss-mask comparison and L0

**Question and intervention.** Does omitting direct proposal loss during production-shield
takeover improve both actionable teacher imitation and complete native deployment, conditional
on the same B01 demonstrations and actual initialisation? B01's aggregate fit gain together with
worse inactive-stratum training/evaluation MSE motivates this question. The independent review
above supplies the section-5 scientific scrutiny. The current learning/service-risk background
requires native J/QoS/risk and adverse worlds alongside the stratum diagnostic, not an MSE gate.

**Fixed inputs and information.** Read only the retained B01 root
`/home/wu/projects/HMASD/runs/energy_relay_imitation/b01_bc_a01` on wsl_4070. Pin B01 source
`b8cf9d3aace3ac4b386d03190b5a6310ee90acae` and completed summary SHA256
`ab6c8a3bcaa138434843b70915e7e0bb755551cefd8e673f1a18b2cfb760421e`.
The actual initial checkpoint SHA256 is
`360ab5575f69fe08a5025d61421d0cf51bf1d8702a7b17802b9f94dbe8334b88`, fingerprint
`cb5c15e6d6fbf4e35affb0e33dd9f59915856e5167b8b6a474825324b85cb701`.
Validate the summary, corresponding record and every used raw-input hash before fitting/replay;
refuse missing or mismatched inputs rather than regenerate or silently substitute them. Record
absolute source locators and digests in B02 output, without copying initial checkpoint or raw data.
Use the same 32 demonstration worlds 967001–032 and existing 32 teacher-evaluation trajectories
968001–032. Preserve the granted SET central snapshot, k=10 cadence, actual deterministic tanh
head and recurrent contract. Forbidden worlds 957001–032 remain excluded. The 968001–032 panel
is now exposed development data, never renamed a new test or training replicate.

**Exactly one new fit.** Load the saved initial checkpoint, including its zero-step actor optimizer,
into the same B01 model/config; verify the fingerprint. Retain seed 929031, order RNG 929032,
ten epochs, four-episode groups, TBPTT128, learning rate 1e-4, clipping .5, weight decay 0,
no scheduler, TF32 off and single-thread library caps. Keep actor-only optimisation and unchanged
logstd/critic/coordinator/normalisers. Every real step still participates in chronological actor
forward and recurrent state propagation. Define direct loss weight as valid padding mask times
`not recorded_shield_active`, then divide summed squared error by the selected agent-step count
times four action dimensions. This selected-coordinate mean is part of the intervention.
Keep teacher proposals as targets, never submitted actions. Active steps can still influence
future inactive outputs through the recurrent graph within a chunk; the claim is removal of
their direct loss, not removal of all gradients or history associated with those steps.

If a chunk has no selected elements, advance/carry and detach hidden state normally, clear
gradients and skip its optimizer step; do not replace the chunk, accumulate extra updates or
change sequence order. At most 1,920 updates, exactly 7,680,000 full recurrent training agent-step
forwards and 4,846,860 selected loss exposures for these complete fixed data. Report actual
updates, skipped chunks, both exposure counts, finite checks and module invariance.

**One endpoint and complete reading.** Save only the new final checkpoint. Run it deterministically
on the same 32 development worlds, H3000/S7-S2/eight UAVs/production shield, with two environment
workers and one thread each. No new teacher collection and no rerun of B01 initial/final policies.
The primary new comparison is revised-minus-B01-BC, with teacher and actual initialisation retained
from their immutable records. Report every world and signed QoS/J/risk difference, zero-service,
minimum-battery tail, cutoff/depletion, charging, shield/guard and phase diagnostics with the same
censoring/conditional-window caveats. Do not silently drop failed worlds or infer a complete
panel after failure. Replay the new endpoint, with frozen weights and complete recurrent state,
on both existing teacher panels; report overall/per-dimension/active/inactive MSE. Exactly
1,536,000 additional offline agent-step forwards, no checkpoint selection or fit on evaluation data.

The joint prediction and all four outcome branches are those in the review above. Relative
native improvements with risk/failure conflicts remain conflicts; offline improvement alone
does not establish utility or a unique mechanism. This conditional paired intervention is not
confirmation, not an independent training seed and not a policy-class capacity test.

**Cost and execution.** One sequential admitted batch: validated retained inputs → one fit →
32 final-policy episodes (maximum 96,000 environment transitions) → two offline replays → reading.
Reference fit/evaluation wall is 5.47 + 21.05 min; allow approximately **30–45 minutes** compute
including replay/imports under comparable contention, with engineering, review, transport and
interpretation additional and actual times recorded. Wall is an estimate, not a stopping rule.
Measured B01 process peaks suggest roughly 1.4 GiB per heavy process, not a concurrent node total;
fresh node memory/concurrency admission still applies. New bulk is one final checkpoint plus
32 trajectory files; retain one canonical run copy and compact Git records. No additional node
or resource reservation follows from this plan. B02 scientific work is **0 fits / 0 episodes**
until exact-source publication, independent engineering acceptance and native admission.

**Bounded implementation L0.** The Implementer owns only new
`experiments/candidates/energy_relay_imitation/b02/`, `run_b02.py` in that direction and mirrored
tests, plus a narrow backwards-compatible B01 helper parameterisation if necessary to reuse
fit/replay/failure handling. Preserve B01 defaults and its frozen meanings; no shared evaluator,
learner or other direction edits. Prefer reuse over a second copy of the complete B01 framework.
The admitted entry must check admission/source identity before scientific effects and pin external
inputs. Preserve the repaired metadata coexistence, thread caps, failed-work accounting and
pool-submission handling. Tests exercise masked-loss behaviour, recurrent continuation through
masked steps, empty masks, immutable-input rejection, counts/checkpoints and B01 compatibility
using synthetic/short unrelated fixtures only. No actual scientific panel in tests. The helper
does no Git mutations, NOTES edits or science launch; it returns code, checks and limitations.
The DM accepts only after the independent Engineering Reviewer closes material issues.

Implementation binding clarification, before B02 execution: the launcher deliberately maps
absolute CLI inputs beneath the author checkout into the immutable source snapshot. Therefore
the fixed external B01 artifact root and digests above live in committed B02 candidate code,
and its production entry exposes no root override. It resolves/validates that declared root
after admission and records the locator/digests in config. Isolated tests may pass a fixture
root to the internal batch helper. No launcher exception, generic-summary alias, symlink,
extra bulk copy or changed scientific input is introduced.
