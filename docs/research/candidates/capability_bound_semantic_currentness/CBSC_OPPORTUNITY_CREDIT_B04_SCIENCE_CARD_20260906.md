Claim: one paired training run tests whether STRUCT improves fixed-endpoint native return beyond same-information RAW when both learn from sampled opportunity returns.
Binding structure: systems / information flow.

# CBSC-OPPORTUNITY-CREDIT-B04 — selected B/EXPLORE card

Frozen 2026-09-06 PDT under the complete Convergence decision at
`d3222ccb53f4986320f0015960ea997dccd8e856`, archived in
`pro_packets/20260906_opportunity_credit_convergence/archive/RESPONSE.md`.
Decision intake: `CBSC_OPPORTUNITY_CREDIT_B04_CONVERGENCE_INTAKE_20260906.md`.
This is an outcome-informed new learning package under the existing mechanism,
not a recast or a repeat of the paused unchanged 48-update family. B02/B03
remain two valid zero comparisons. Only this card selects the new execution.

This host has one learning controller and two receiver environment entities.
Its public-history currentness is an information-flow inspiration for multi-agent
partial observability; it does not itself measure multi-agent learning,
other-agent non-stationarity, roster changes or partner co-adaptation.

## Question, motivation and primary observable

Does local sampled credit permit a useful STRUCT-versus-RAW return difference,
and do the resulting policies exceed a simple public-request rule? The host's
actions change neither later state nor later recurrent inputs. This motivates
trying a shorter return-prediction target without claiming that GAE caused the
old all-REFRESH plateau or that variance must decrease. The changed component
is a coherent target/critic-supervision package; its parts are not separately
identified by this comparison.

At update 48, primary `d_e = R_STRUCT,e - R_RAW,e` for every evaluation
episode e=0..31; primary estimate is the mean of all 32 d_e. Retain all signed
differences, both absolute returns, and both checkpoints. There is one paired
independent training seed, not 32 independent trained pairs. No best-checkpoint,
episode, metric or seed selection, early stop, or arm-specific tuning.

## Selected learner and credit target

Two arms: existing RAW-GRU (full public stream plus generic FIFO) and
STRUCT-CURRENTNESS-GRU (the same stream plus the existing currentness adapter).
RAW contains the information used by STRUCT; it is not an already tuned optimum.
All STRUCT features remain deterministic functions of the public history.

For each eight-episode rollout and decision `t=12+6*q`, q=0..23:

1. `G[e,q] = stop_gradient(reward[e,t] + reward[e,t+1])`, using only the
   actual sampled action's FP32 decision and settlement rewards.
2. `A[e,q] = G[e,q] - stop_gradient(old_value[e,t])`.
3. Normalize A once over all 192 decisions: `(A-mean(A))/(sqrt(mean((A-mean(A))**2))+1e-8)`.
   Epsilon is outside the square root. Keep targets and normalized advantages
   fixed for all four PPO epochs, not recomputed per episode/minibatch.
4. Use the existing decision-only clipped PPO actor objective. Fit the scalar
   value head to **unnormalized G**, using mean squared error only over the
   48 decision rows in each two-episode minibatch. Nondecision output rows do
   not contribute directly to value loss. Total loss is actor +0.50 value
   -0.01 decision entropy. No value clipping or auxiliary loss.

There is no future-opportunity bootstrap in this target; old GAE lambda is not
used. Do not substitute old lambda=0 or gamma=0. The full 152-token recurrent
unroll and full episode BPTT remain; do not terminate/reset/detach at opportunity
boundaries. Earlier public events still influence later decisions through
recurrence. Final-opportunity settlement is included. Unchosen ledger rewards,
VALID, hidden state, oracle actions, full Q or teacher targets never enter learning.

Preserve the existing 168→Linear128/ReLU→GRU128→actor4/value1 model with
121,349 parameters, original adapter-column zero initialization, CPU FP32,
gamma-one native objective, PPO clip0.20, entropy0.01, Adam LR3e-4,
betas(0.9,0.999), epsilon1e-8, weight_decay0 and global gradient cap0.5.
Keep four epochs × four two-episode minibatches, original Adam order and common
action-uniform/minibatch addressing. Both arms use the new target; never compare
new-target STRUCT with old-GAE RAW. No extra update, replay or imitation.

## Host, information, RNG and evaluation

Use unchanged CBSC-DYNAMIC-CACHE-2R-1C-v1: 24 opportunities, 152 primitive
transitions, existing public event probabilities/order, masks, body/capability
semantics, RAW/STRUCT adapters and delayed settlement. Preserve the native
decision-plus-settlement ledger. Actions do not persistently modify cache.
The environment's evaluator truth remains separate from the public learner view.

Trace: public OWNER/semantic events → receiver-specific history → existing
RAW/STRUCT public adapters → SERVE/REFRESH/SAFE_FALLBACK → the chosen action's
local reward target → real recurrent policy updates → complete held-out return.
One controller acts; receivers, carriers and body slots are environment entities.

Formal seed **21217**, from fresh model and Adam states. Reuse the existing
B1_RUN RNG namespace with that new seed for all exogenous histories, action
uniforms and minibatch order, identically across arms. New B04 outer identity,
output root and honest target/checkpoint metadata are mandatory; old B02/B03
behavior, records and checkpoint meaning remain unchanged. Do not load an old
trained state or label the new learner as unchanged B01 GAE.

Each arm trains 48 eight-episode rollouts, fresh TRAIN IDs0..383 exactly once.
Evaluate only updates **0 and48**, each on EVAL_STOCHASTIC IDs0..31, separate
from TRAIN and identical within the pair. Greedy, adaptation-free evaluation
resets recurrent state per episode. Action realizations may differ across arms;
pairing means common random sources, not forced identical actions.

In RAW's full invocation, score three rules once on the same32 tapes:
ALWAYS_REFRESH, ALWAYS_SAFE and **REQUEST_ONLY**. REQUEST_ONLY chooses REFRESH
if the public decision token's request_active flag is true, else SAFE_FALLBACK.
The public rule chooses its action before evaluator scoring; it never reads
VALID/state/future facts and supplies no labels to the learner. STRUCT reuses
these same-tape records. Publish every endpoint `R_arm-R_REQUEST_ONLY` and its
mean as interpretation context. The old inferred12.1875/12.1125 rule scores
are historical arithmetic, never this new seed's baseline.

Save per-episode24 chosen actions, decision/settlement contributions, native
returns, all endpoint paired differences, both checkpoint states, true model/
optimizer/counters, update loss records and actual sampled training-action
counts. Publish/read back initial and final parameter norms/displacement,
exposure, seed/RNG, target/value-supervision definition and source metadata.
Existing direct evaluation is the reference path; no old fifteen-table replay,
motif/twin census or full intermediate array publication is required.

## Exposure, cost and execution

Machine calculations: `pro_packets/20260906_opportunity_credit_convergence/EXPOSURE_AND_COST.json`
(the proposed values in that historical input are now selected unchanged by Pro).

| Quantity | Per formal arm | Paired total |
| --- | ---: | ---: |
| Training episodes | 384 | 768 |
| Training transitions / decisions | 58368 / 9216 | 116736 / 18432 |
| Rollout updates / Adam steps | 48 / 768 | 96 / 1536 |
| Evaluation executions / transitions | 64 / 9728 | 128 / 19456 |
| Train plus evaluation transitions | 68096 | 136192 |

Dominant work:2 arms×1 seed×48 rollouts×8 episodes, 2×48×4×4 Adam steps,
and2×2 checkpoints×32 evaluations, with152 transitions per episode. The three
fixed rules add96 existing-tape ledger passes/2304 action scores once in RAW;
no new worlds or learners. No nested policy/trajectory/controller search.

Complete cost law: startup/admission + host + sum48(project8/rollout8/PPO4×4)
+sum2(eval32/checkpoint) + RAW context + publication/readback + STRUCT pairing
+termination grace. Old complete walls were RAW/STRUCT79.69/90.78s (B02) and
59.53/58.67s (B03). Planning scenarios159.38/181.56s are twice the larger old
same-arm wall; new implementation cost remains unmeasured, not a guarantee.

Run **RAW then STRUCT**, at most one full formal invocation per arm, each
**600 seconds including all phases and termination grace**. RAW's score does
not determine whether the selected STRUCT runs; primary integrity does. Pair
analysis belongs inside STRUCT's full cap, not an uncharged third invocation.

Use current remote_first route wsl_4070, `/home/wu/.venvs/hmasd/bin/python`,
CPU FP32, one scientific process and one Torch compute thread with existing
numeric-library thread limits. No GPU, dtype, interpreter or parallelism change.
Commit/push exact source, obtain Root integration, then run detached under the
configured agent-task supervisor. Each actual engineering/formal call must join
fresh physical/effective available memory>=4GiB admission immediately to the
runner. Send accepted handles to the independent monitor per current config
and EXPERIMENT_MONITOR.md; CM retains technical collection and DM science.

Exposure line: this consultation ran zero new learner/evaluation calls.
Existing four formal arms moved18.6828676061%–20.3270553056% of initial parameter
L2 after768Adam steps. This demonstrates available weight movement, not new
target performance or a linear displacement forecast. Actual B04 movement
and counts must be reported, with no separate exposure-proof experiment.

## Single selected engineering check and scope

Engineering seed **21211**, two arms, one real8-episode rollout/16Adam steps
per arm; one EVAL_STOCHASTIC tape at updates0/1 per arm. Total32Adam,
2432 training transitions and608 evaluation transitions (**3040 total**).
One complete engineering invocation, **60s including imports, admission,
learner/evaluator, snapshots/publication readback and grace**. No performance
threshold. No additional model/host execution outside this selected check or
the two formal calls. Ordinary pure static checks do not create a new allowance.

Within that check use small constructed reward/value arrays plus the real path
to cover local G/A, fixed rollout targets, unnormalized decision-only value
regression, chosen-action reward, public REQUEST_ONLY, pairing and output readback.
Changing future rewards with fixed old values must leave earlier **unnormalized**
G/A unchanged; normalized values can change through the shared batch statistics.
Nondecision values have no direct value-loss term, but history/shared-parameter
gradients need not be zero. Include delayed REFRESH settlement and final q=23.
Use dtype/scale-appropriate checks, without global1e-12 or cross-platform replay.

Opening directory focused account: **132.15/300s**; charge this one check's
actual wall and necessary short checks to the same account. No budget reset,
repeated simulation smoke or automatic result-bearing retry. CM performs the
bounded implementation directly, with independent review of the new credit,
information, reward, comparison and primary-output boundaries. Check success
does not establish mechanism value.

Engineering-scope §4 needs: **none**. Reuse ordinary learner snapshots without
new recovery/resume orchestration, generic factories, registries, provenance
guards, workers, telemetry service or profiler. Ordinary<=2000 new non-test
source lines and<=600 runner lines apply;30% is a review signal. Old B1 repair
exceptions do not transfer. CM may use a small explicit B04 snapshot record
to state the changed target truthfully; never falsify/bypass old frozen metadata.

## Prediction, MEI, reading rule and stopping

Headroom: matched tuned same-information generic/upper record is absent, not
zero. Existing exact/LR01 assets do not match this online host/budget; REQUEST_ONLY
is a useful public-information null, not tuned headroom or an optimality claim.
MEI: **0.25 native episode return** (about1.04% of the theoretical maximum24),
chosen as the same practical follow-up scale as B02/B03, not a significance test.

DM prediction: weakly expect improved handling of public request activity,
with STRUCT-minus-RAW still inside MEI. Confidence is low; neither owner/epoch
conditioning nor variance reduction is established. Owner prediction:
**not taken (unattended)** at freeze; check any later reply at intake.

Reading rule: a positive STRUCT gap aboveMEI with trustworthy native performance
can motivate one or two new independent seeds, not authorize them now. Retain a
true gap if RAW remains below REQUEST_ONLY but call the comparison limited;
do not call it currentness value. Equality to REQUEST_ONLY alone does not prove
identical actions. If both arms beat that rule with little representation gap,
report shared local performance; other public features/generic conditioning
remain explanations. Zero, adverse, unchanged all-REFRESH or below-rule outcomes
remain visible, and negative insideMEI remains negative. More SERVE/entropy or
weight movement without native gain is not performance value.

End at full pair intake or a concrete target/information/reward/training/pairing
primary defect, necessary coverage/interface/scope gap or complete cap. Preserve
narrow trustworthy facts; do not fill a missing pair with zero. Optional missing
resource telemetry alone marks resources_unmeasured and limits resource claims.
No automatic formal/check retry, extra seed,192updates, changed host/hyperparameter
or new search. Ordinary static fixes retain their existing authority.

Claim ceiling: one local paired-seed performance observation inside this new
credit package. No stable superiority/equivalence, semantic specificity,
PI/DERANGED/generic-conditioning exclusion, causal effect of replacing GAE,
separate target-horizon/value-mask effects, or general MARL/roster/UAV claim.
No pooling of old and new objects as three same-algorithm seeds; old B1/r05
quarantine and historical SIGSEGV/TypeError causes remain unchanged.
