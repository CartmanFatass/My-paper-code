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
