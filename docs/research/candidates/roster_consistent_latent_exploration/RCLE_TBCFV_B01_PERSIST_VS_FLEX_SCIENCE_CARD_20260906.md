Claim: On the frozen TBCFV rotating-perimeter host at a small fixed learning budget, the persistent common-plan package may recover service after an unseen-roster active-continuation membership change faster than the same-information strictly containing FLEX package.
Binding MARL structure: agent-count change and coordination recovery after a roster change; one shared parameter vector across rosters, no per-N head, public state only.

# RCLE TBCFV B01 persist-vs-flex — science card

Date 2026-09-06; object `RCLE-TBCFV-B01-PERSIST-VS-FLEX`; **B / EXPLORE**; the first empirical
object on TBCFV. Selected by the complete first-binding Innovator response
(`pro_packets/20260906_tbcfv_first_b_innovator_r02/archive/RESPONSE.md`, commit `35e3b7b14`),
**PRO_FINAL**, intake `RCLE_TBCFV_FIRST_B_INNOVATOR_INTAKE_20260906.md`. The Claude research hub
(Root and DM) freezes this card under the owner's standing unattended delegation. No empirical
outcome has been observed; TBCFV has never been built or executed on any node. The definition
card `RCLE_TARGET_BOUND_COMMITMENT_FRAGMENTATION_VALUE_SCIENCE_CARD.md` stays definition-only;
this card authorizes one bounded first pair, not the five-arm twenty-block program.

## 1. Question and ceiling

Under the definition card's host and training law, from identical initialization and identical
small training exposure, does `C1P1-COMMON-PERSISTENT` recover service after an active-continuation
roster change faster than `FLEX-REKEY`, which strictly contains it? The comparison is
exploratory: one paired training seed, two arms, four development-scale quantities. Its ceiling
is a preliminary performance signal or counterexample on this frozen toy, this budget, this
training instance and these held-out cells. It establishes no competence against a tuned generic
baseline, no headroom, no commonality/persistence attribution, no fragmentation mediation, no
stable superiority, no C-level simultaneous inference, and nothing about arbitrary N, variable
k, UAV simulation or deployment. Predecessor-host B1/B2/CPC polarity does not transfer and is
not reopened. `H_A1` stays unidentified.

## 2. Host, arms, training law

Host exactly as the definition card §"Frozen physical host": 120 sectors, six service beacons,
H=64, membership boundary t_c=24, six always-legal beacon claims, `MOVE-TO-CLAIM` decoder,
exogenous roster process paired across arms. Training cells per update: `6→6, 10→10, 6→10,
10→6` × `ACTIVE_CONTINUATION, NEW_EPOCH`, eight episodes each (64 per update). Held-out cells:
`8→8, 12→12, 8→12, 12→8` × the two event conditions; no gradient, tuning, normalization
re-estimate or model selection touches them.

Arms: exactly two learned arms, `C1P1-COMMON-PERSISTENT` (treatment: one common plan z drawn
per epoch, retained through an active membership event) and `FLEX-REKEY` (comparator: identical
before the boundary; at an active event may apply the common and agent-specific update heads).
Both allocate the 26,161-scalar maximum architecture; FLEX's two final update-head layers start
at exactly zero and train; the treatment hard-masks them. Containment is policy-functional, not
optimizer-trajectory equality (definition card §"Frozen learned arms"). No other learned or
scripted arm trains.

Training law unchanged (definition card §"Training, matching, and checkpoint law"): joint loss
`L = −(1/64) Σ_b stop(Y_b − β_(arm,cell)) · (ℓ_z(b) + ℓ_a(b))`, stopped plan draws, score-function
manager gradient, actor log-probabilities, one backward per block, plain SGD with the fixed
whole-tensor step (`g_update = 0.05 g/‖g‖` if nonzero, `θ ← θ − 0.01 g_update`, norm 0.0005),
eight stopped per-cell baselines per arm updated `0.95/0.05` strictly after the parameter update.
There is no optimizer state, momentum, weight decay, clipping, entropy, auxiliary reward,
return normalization, curriculum, replay, early stopping or checkpoint selection, and none is
added. The DM's earlier "separate optimizer/normalization state" means only the baselines.

## 3. Seed, pairing and exposure

One paired training seed **17**. Its root key is the SHA256 of the ASCII string
`RCLE-TBCFV-B01-PERSIST-VS-FLEX/seed/17`; the block digest and every semantic coordinate are
derived from it by the implementation's existing derivation (`_derive_block_digest` and
`SemanticRNG` in the TBCFV tree) with block index 0, exactly as the CM record documents. Both
arms copy the identical initial common tensor (definition card initialization law); initial
positions, roster arrivals/departures, epoch offsets, beacon/demand variables and evaluation
scenarios are identical across arms; common plan draws and actor inverse-CDF draws are paired
where the laws coincide; states are not forced equal after divergence. The arm name selects no
RNG substream.

Each arm trains **200 complete updates × 64 episodes = 12,800 training episodes (819,200
environment ticks)**, at most 200 backward/parameter-update calls, and evaluates the update-200
parameters only, on **256 episodes per held-out cell (2,048 per arm, 131,072 ticks)**. The two
arm runs form one paired training replicate. Record: completed updates, zero-update incidence,
actual nonzero-update count, initial parameter norm and final displacement (the mechanical path
bound 200 × 0.0005 = 0.1 is an upper bound, never a displacement), per-update training-episode
Y summary per cell and overall (all 200 kept; display points every 25), episode counts per
cell, τ=40 fractions and failure codes. Nominal counts do not replace observations.

## 4. Evaluation, primary measurement and reference row

Per episode, exactly the definition card's endpoints: `u_t` normalized unserved demand;
`τ = min{h ∈ 0..36 : u_(24+h) = … = u_(24+h+3) = 0}`, else 40 (a bounded recovery score with a
failure code, not an uncensored mean); `U = (1/40) Σ_(t=24)^63 u_t`; `Y = 1 − (1/64) Σ u_t`;
`F` may be reported descriptively. Intention-to-treat over every assigned scenario; no episode,
agent or interval is excluded for any reason.

**Primary comparison: τ on the two ACTIVE_CONTINUATION held-out paths `8→12` and `12→8`, equal
weight.** For each path publish both arm means, the difference `FLEX − treatment` (positive
favours the treatment), and the τ=40 fraction; the primary summary `Δτ_B01` is the arithmetic
mean of the two path differences. Companion: `U` and `40U` (cumulative normalized unserved
demand, not raw service units) on the same two paths; τ, U and Y on all eight held-out cells
with the eight-cell mean as a declared secondary description. NEW_EPOCH cells are not a pure
"erase plan identity" contrast. Within-seed uncertainty: cell-stratified, paired-scenario Monte
Carlo standard errors or descriptive intervals with existing NumPy; no seed-level inference, no
t-test or episode bootstrap presented as stable superiority.

**Zero-learner reference row `INDEPENDENT-NEAREST`** (definition card §"Treatment-independent
opportunity and competence prerequisites": every agent claims the nearest current beacon, ties
to the lower beacon index, no plan latent): evaluated once on the same 2,048 held-out scenarios,
no training, no parameter search, no script change after learning results are seen; one row
plus eight-cell detail. It gives an interpretable non-coordinated level of τ and U to
distinguish saturated arms from a small relative difference. It is not a tuned generic baseline
and does not fill A1's upper/generic pair; its cost is not "seconds" until measured.

## 5. Interpretation and predictions on record

**MEI: τ 4 physical ticks (10 % of the post-boundary window, one claim period) and U absolute
0.05** (two normalized unserved ticks in the 40-tick window). Interpretive scales for this
object, not significance thresholds; not the original C's 0.02 non-inferiority margin or its
72-tail rule. Reading rule:

| Observation | Current change | Not inferred |
| --- | --- | --- |
| `Δτ_B01` ≈ +4 or more favouring the treatment and no U loss reaching its MEI | keep this finite-budget package as a candidate worth one independent paired seed; show each path and any smaller U loss | stable superiority, non-inferiority, competence, a commonality/persistence mechanism |
| `Δτ_B01` ≈ −4 or worse, or a material U loss for the treatment | less support for restricting FLEX at this budget; a clear adverse result may also merit one replicate | closing RCLE; "persistent state has no value" at any N or budget |
| inside τ ±4 and U ±0.05 | no material difference claimed; learning amount, censoring and seed uncertainty are judged first | equivalence, zero effect, the original C's no-material branch |
| paths disagree, τ/U trade off, errors span the MEI, or τ almost all 40 | mixed/undecided; U and curves keep their own meaning | a post-hoc winning path, switching to U as primary, dropping failed episodes |
| primary comparison damaged | only independently trustworthy narrower facts and technical counts | any algorithmic polarity |

Default follow-up for a credible, clearly comparable pair: one new independent paired training
seed as a separately recorded investment (one or two by cost and observed variability); no
running until positive, no evaluation episodes in place of training seeds; a changed budget or
algorithm is a new outcome-informed B. Direct counter-evidence: FLEX recovering as fast or
faster, or a treatment recovery gain paired with a material cumulative unserved loss.

Node's prospective judgement (recorded): both arms may barely learn at 200 fixed-norm updates
(path bound 0.1); low exposure, optimization difficulty and saturated recovery remain live
explanations if neither arm improves. DM primary prediction: inside-MEI on `Δτ_B01`
(|Δτ_B01| < 4) with both arms' τ=40 fractions above 0.5 on the active paths, because the fixed
0.0005 step and 200 updates move the 26,161-scalar policy little from a uniform-ish six-way
claim distribution. Competing prediction: the persistent plan yields `Δτ_B01` ≥ +4 on at least
one active path because a retained z keeps survivors' claims coherent for the first
post-boundary claim clock while FLEX's freshly trainable heads inject noise. Owner prediction:
**not taken (unattended)** unless filled through the owner console.

## 6. Whole cost, route and stop

Design counts (not exposure): two arms 29,696 episodes (1,900,544 ticks) + reference 2,048
episodes (131,072 ticks) = 31,744 episodes, 2,031,616 ticks; ≤ 400 backward/update calls in
total; 25,600 training episodes are 0.5 % of the full card's 5,120,000. No credible numeric wall
projection exists; A1's fifteen minutes and the predecessor's forty-five are declared bounds;
scripted-episode timing covers no learned forward, graph retention, backward or model output
and is never multiplied into a per-arm cost law.

**Hard cap: 2,700 s per arm and training seed for the complete logical invocation** (import,
initialization, 200 updates, final evaluation, required checks, publication; no phase split,
resume or clock reset), **and 5,400 s cumulative execution wall for the whole first pair**,
including the one shared native build actually paid, the executability measurement, required
checks, the reference row and merged publication, each charged once where it belongs. The study
reports the elapsed critical path and the sum of invocation walls. If a credible projection
exceeds the cap, the design is not launched; before any real learning the DM may record one
symmetric reduction of updates or evaluation episodes and restate the question; 200/256 is the
baseline, not a menu. The first real training block gives its own wall and is charged to the B;
a run found infeasible mid-way stops as a technical stop.

Route: remote-first on the declared node from exact committed and pushed source with detached
supervision and a fresh physical/effective memory admission ≥ 4 GiB immediately before each
invocation; single CPU thread, existing dtype (float64 native, model as implemented), no device,
precision, RNG, batch/update or multi-process change. **Host portability is an open engineering
fact**: the TBCFV native backend (`native_backend.py`) is built through an MSVC/`vcvars64.bat`
pipeline and loaded by ctypes, with no Linux branch; the first build on the node is part of the
CM preparation (§7) and may fail. A local Windows fallback is permitted only under AGENTS §5
(portability established before question-relevant output, no remote process accepted, fresh
local admission) and is recorded as such; it changes no claim meaning.

Stops: native build failure, executability error or overrun (> 300 s or > 64 episodes),
admission failure, or adaptation beyond ordinary budgets stop the launch attempt with logs,
counts and a concrete gap; no claim about learning, no automatic second A, host change, dtype
change, retry or seed replacement. Once real learning runs: cap reached, non-finite primary,
wrong reward/information/event order, missing arm, asymmetric training exposure or held-out
adaptation forbid the complete comparison; a damaged first arm does not spend the remainder on
the second; a damaged second arm keeps the first arm's facts; technical stops carry no
polarity; a missing reference row or telemetry degrades descriptively only.

## 7. Launch preparation and bounded engineering handoff

**Engineering-scope §4 declaration: none of its default-prohibited machinery is needed**; in
particular the thin entry adds no registry, validator, guard, lease, certificate, worker pool,
retry or telemetry beyond wall/RSS/CPU. CM objective:
`RCLE_TBCFV_B01_CM_OBJECTIVE_20260906.md`. Owned by CM: a new attempt directory
`experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/` (thin two-arm
single-seed entry that calls the existing `initialize_block_models`, `execute_training_update`,
`execute_learned_batch`, `execute_scripted_batch`, `exact_advantage_loss`,
`apply_registered_block_update` and a minimal block authority derived from the seed law above,
never `execute_full_panel`, the frontier/publish chain, the preactivity chains or the 20-block
materialization), `scripts/run_rcle_tbcfv_b01.py` (≤ 600 lines), its focused tests, the CM
record, and one bounded portability change inside `native_backend.py` (a Linux compiler branch
with the same source, ABI and flags semantics) reviewed independently. Preparation: first
native build on the node; **one zero-learner scripted executability/cost measurement ≤ 300 s,
≤ 8 cells × one 8-episode batch (≤ 64 episodes, 4,096 ticks) on preparation scenarios separate
from the final held-out panel**, recorded as non-learning host exposure; one focused check of
real return, t_c event/claim/motion order, τ's four-tick and 40 coding, both arms' initial
correspondence and FLEX's gradient path through the update heads, the joint 64-episode update,
and readable output, reusing the existing TBCFV tests (`test_native_host.py` oracle
conformance on the node establishes portability of the build). Budgets: ≤ 2,000 new source
lines, five-minute research tests; the 30 % ratio is a review signal.

Output root `temp/directions/roster_consistent_latent_exploration/exp/tbcfv_b01_20260906/`
with `build/`, `executability/`, `c1p1/`, `flex/`, `reference/` and adjacent admission
receipts; keep per-update curves, final parameters, per-cell τ/U/Y per scenario, τ=40 counts,
failure codes, actual counts and wall/RSS/CPU witnesses; no full trajectories. CM freezes
argv/cwd/node/launch sha before launch; the operator launches; DM interprets; Root integrates.
The complete Pro decision selects this comparison, not source acceptance; the four §11.4
conditions remain the only launch gate.

scope: none
