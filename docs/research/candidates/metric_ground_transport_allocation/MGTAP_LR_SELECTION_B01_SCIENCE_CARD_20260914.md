# MGTAP-LR-SELECTION-B01 — finite symmetric LR selection and fresh holdout

Claim under study: a finitely selected COND learning procedure may provide useful local native return against an equally selected DENSE procedure.
Binding structure: systems / information flow; both actors use the same legal local information in a partially observed multi-UAV task.

Status: prospective B/EXPLORE protocol selected by DM at the 2026-09-14 reentry.
The complete runner is implemented and technically accepted after independent review.
The single exact-source programme completed on2026-09-14. Its frozen rule reads
COND_ABOVE_MEI; see [complete result intake](MGTAP_LR_SELECTION_B01_INTAKE_20260914.md)
and [actual launch facts](reentry_20260914/LAUNCH.md). The prospective contract below is unchanged.
No old frozen invocation is resumed. The current development decision is in
[DM reentry intake](reentry_20260914/DM_REENTRY_INTAKE.md).

## 1. Question, comparator and claim

After equal finite learning-rate selection opportunities, does selected mean-COND
supply a useful local holdout contrast against selected intact-DENSE, sufficient
to justify continued work on an optional COND implementation branch?

These are TWO COMPLETE SELECTION-AND-LEARNING PROCEDURES, not a pure geometry
effect or a causal estimate of tuning gain. Each has three candidate fits and
one fresh selected fit. Without an additional untuned holdout comparator, the
effect of tuning itself is not identified. No such extra comparator is selected.

The alternative is an unchanged two-fit recurrence, or continued PARK.
The new question costs four times as many fits as that recurrence. The earlier
toy's scalar-setting sensitivity makes this concrete choice worth a bounded
investigation in DM judgment; it neither proves the native cause nor mandates
tuning as a universal prerequisite. Native tuned headroom remains unmeasured.

## 2. Protected native learning semantics

Reuse the accepted five-UAV/fifty-uniform-user, free-space/no-shadowing H256 law;
original team reward sum divided by256; raw108 legal local actor information;
private GRU64; training-only critic information; primitive sampled velocity;
mean visible-partner query and separate masked-partner sum for COND;
intact DENSE raw/nonlinear paths; recurrent PPO agent_compound ratios, chunk32,
two complete episodes per rollout, four full-rollout epochs, entropy coefficient0.01,
joint actor/critic gradient clipping0.5, and original Adam settings except LR.
CPU FP32, one Torch thread. No topology, reward, information or policy interface change.

Fixed inherited source before this work: 1c5887704d42bd97db0835501338b657850ac352.
The early256 B02 launch source8744085c293288e2c178fbc6d2a97ae9ca053c43 is provenance,
not this new launch SHA. Keep frozen modules unchanged; create a direction-local runner
using the accepted factory/collector/update. At actual launch bind this new complete
runner and card to their own published SHA.

## 3. Selection, randomization and final estimand

Learning-rate candidates, also exact-tie preference order:
base=3e-4, slow=1e-4, fast=1e-3. All other Adam parameters unchanged:
betas=(0.9,0.999), eps=1e-8, weight_decay=0, amsgrad/foreach/fused=False.

Selection master8251: run all three candidates for BOTH arms, 256 training episodes
and32 validation episodes per candidate/arm. Each candidate starts from the same
master's corresponding arm initialization with a NEW optimizer and NEW arm-owned
RNG instances. Use base/slow/fast candidate order, COND then DENSE within each candidate.
Matched reset addresses do not require identical learned trajectories.

Select each arm independently by its own highest mean validation J, with the stated
exact-tie rule. Save every candidate score, model, training/validation record and
the selected configuration. Publish and hash the selection record BEFORE holdout
fitting begins. No choosing the arm difference, manual override, dropped losing
candidate or extra selection world. A missing/damaged required candidate yields
INCOMPLETE for this full procedure, not a replacement search or a polarity.

Holdout master8252: construct a completely new matched pair and fresh optimizers/RNGs,
fit each selected configuration for256 episodes, and evaluate its sole32 final worlds.
Do not transfer selection weights or use holdout values to alter selected rates.

For master s, base=100000*s. Training episode e uses reset base+1000+e,
private persistent velocity stream base+21 and dummy duration stream base+4000+e.
Evaluation episode e uses reset base+2000+e, velocity base+3000+e and dummy duration
base+5000+e. Stage masters and evaluation roles are disjoint. The executable
[protocol](../../../../experiments/candidates/metric_ground_transport_allocation/mgtap_lr_selection_b01/protocol.py)
rejects wrong stage/master/rate/endpoint/addresses, duplicates and missing panels.

Primary: ordered mean of32 holdout (J_COND,e − J_DENSE,e), conditional paired-world
SE reported separately. MEI=0.01 J is the inherited local development scale:
strict >+0.01 COND_ABOVE_MEI; strict <−0.01 COND_ADVERSE; inclusive band INSIDE_MEI.
All signs and worlds are retained. No branch is assigned to the selection maximum
or a pool containing old results.

There is one selection training master and ONE fresh final learning pair.
The six selection fits are correlated candidates, not six independent programme
replications;32 final worlds are not32 training seeds. This programme itself was
selected after prior outcomes. It cannot estimate training or selection-population
uncertainty, stable ordering, learning curves, sample efficiency or a unique mechanism.
No cross-master covariance decomposition is claimed.

## 4. Work and resource plan

[Machine-computed exposure](reentry_20260914/PLANNED_EXPOSURE.json) comes from the
protocol constants, without a simulation:

| Stage | Fits | Training episodes | Evaluation episodes | Team ticks | Adam calls |
| --- | ---: | ---: | ---: | ---: | ---: |
| Selection | 6 | 1536 | 192 validation | 442368 | 3072 |
| Holdout | 2 | 512 | 64 final | 147456 | 1024 |
| Total | 8 | 2048 | 256 | 589824 | 4096 |

Per fit:65536 training +8192 evaluation team ticks,128 rollouts and512 Adam calls.
Total actor collection/evaluation/replay uses:13434880;1024 total rollout updates
are not1024 optimizer calls. Only the three LR candidates are nested; no trajectory,
controller, solver or checkpoint search.

DM native working estimate: roughly15–30 minutes, UNMEASURED. The old two-pair
378.77s sum is a sizing anchor only, not a new hard budget or total-cost guarantee.
Plan serial CPU/thread1 on the existing execution node, at least4GiB physical AND effective available admission
headroom and no interference with RCLE/FOLR. Fresh actual-node admission precedes
any invocation; memory and runtime are measured rather than guaranteed by old RSS.

Ordinary technical watchdog plan:1800s per fit and14400s for the full serial study.
These are DM-adjustable operational watchdogs, not owner caps or scientific endpoints.
No extra paid capacity or cross-direction resource reassignment is authorized.
Support, provider, lifecycle total and aggregate CPU remain UNKNOWN; record actual
startup/review/staging/collection/retention work once. Keep all technical partials.

Engineering-scope §4 items needed by this object: the two-stage serial selection/holdout
sequence measures the selected procedure; complete evaluation-panel checks bind the
actual primary to its selected arm/rate/master/endpoint; and a saved selection JSON
with its byte hash records which rates were fixed before holdout fitting. These are
scientific measurement/persistence needs, not security guarantees, external approval
or generic provenance gates. No resume/retry service, lease, new supervisor, worker
pool, additional telemetry or general-purpose schema framework is selected. The
4GiB line corrects the draft's2GiB planning text to current AGENTS §7 before any launch;
it changes no scientific exposure and claims no admission has occurred.

## 5. Prediction, decisions and verification

DM leading prediction: the fresh selected-program contrast is inside the local MEI
band or adverse, rather than a reliably positive COND advantage. There is no calibrated
probability forecast; owner prediction not solicited and no reply invented.

A useful positive holdout would favor retaining selected COND as an actively developed,
bounded-use optional branch; it does not promote shared defaults or prove recurrence.
Inside/adverse results weaken that option and favor PARK or a separately justified
modification, based on all signed results and costs. No automatic replacement seed,
grid expansion, endpoint extension or successor follows any branch.
Damage produces INCOMPLETE, not a scientific COND loss.

Verification targets the NEW selection boundary, candidate opportunities, fresh
initialization/optimizer/RNG ownership, stage/address segregation, learner movement,
real exposure, all retained panels and closed primary. Reuse accepted unchanged
semantics rather than replaying all historical science. Independent review of the
completed runner/changed behavior is recorded in [engineering acceptance](reentry_20260914/ENGINEERING.md).
The new [scientific design review intake](pro_packets/20260914_lr_selection_design_review/INTAKE.md)
retains its implementation dependencies and inference limits. Neither review is an
actual-node admission, launch receipt or native scientific observation.

DM owns implementation, review response, technical acceptance, launch and intake.
Under the later OWNER Portfolio authority correction, direction-level continuation,
recast, PARK/CLOSE or reopening is reported with full evidence and alternatives to
Portfolio for final interpretation. Ordinary work on this selected object needs
no per-experiment approval. Direction Pro remains its independent scientific Reviewer;
the already-dispatched design question is preserved at its exact earlier input version.
