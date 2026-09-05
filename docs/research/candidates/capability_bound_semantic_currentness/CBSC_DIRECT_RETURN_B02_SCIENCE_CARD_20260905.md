Claim: at a fixed recurrent-PPO budget, STRUCT currentness may improve native held-out episode return over same-information RAW on the existing dynamic cache host.
Binding structure: systems / information flow. The task concerns one controller's partial observation of changing receiver-addressed ownership/content/capability; it does not contain multiple co-adapting learners.

# CBSC direct-return B02 science card

Date: 2026-09-05. Object: **CBSC-DIRECT-RETURN-B02**, B/EXPLORE.
Authority: complete direction Convergence Pro selection, recorded in
CBSC_DIRECT_RETURN_B02_PRO_INTAKE_20260905.md and its exact response archive.
This is a new same-mechanism object, not a mechanism recast, old B1 completion,
a continuation of the ended publication repair, or rehabilitation of r05.

## Question, comparator and primary observable

Train fresh STRUCT-CURRENTNESS-GRU and RAW-GRU at seed **21203**.
RAW retains its complete public primitive stream and existing generic four-byte
FIFO adapter. Both use the same host, recurrent model and optimizer. Every
STRUCT feature is a deterministic function of RAW's public history: RAW is the
containing information null, even if a finite-budget network does not learn it.

At checkpoint update 48, for evaluation episode e in 0..31, compute
d_e = native_return(STRUCT,48,e) - native_return(RAW,48,e).
The primary measurement is the mean of all 32 d_e. Preserve every d_e, both
absolute returns and four checkpoint curves. No best-checkpoint/episode/metric
selection, early stopping or arm-specific tuning is allowed.

Use the same fixed stochastic environment panel at updates 0,12,24,48.
Evaluation is greedy, adaptation-free, and recurrent state resets per episode.
Randomly generated environments do not imply stochastic evaluation actions.
Intermediate checkpoints describe learning and are not alternate endpoints.

Keep same-tape ALWAYS_REFRESH and ALWAYS_SAFE native returns and RAW action
distribution as competence context. Weak RAW narrows the interpretation;
it does not restore an 80%-support/whole-table acceptance predicate.

## Host, information and protected semantics

Host: CBSC-DYNAMIC-CACHE-2R-1C-v1, two receiver environment entities and one
learning controller, 24 opportunities and 152 primitive transitions per episode.
Trace: public OWNER/semantic changes -> target-specific owner/epoch registers ->
identical primitive history -> native SERVE/REFRESH/SAFE_FALLBACK choices ->
real recurrent PPO updates -> held-out native return.

Keep existing event probabilities/order, full public learner projection,
STRUCT/RAW adapter behavior, masks, recurrence, delayed settlement and reward.
Active-valid SERVE=1, active-invalid SERVE=-0.30, active REFRESH=-0.40 at
decision +1 at settlement, active SAFE=0.20. Inactive rewards are respectively
-0.10, -0.40, 0. Nondecision positions keep forced WAIT.
Evaluator truth, validity, hidden state, oracle actions, future facts and
reward-derived features must not enter policy observations.

Reuse CPU FP32 CommonRecurrentActorCritic: 168 inputs -> Linear128/ReLU ->
GRU128 -> actor4/value1, 121,349 parameters. Adapter input columns retain
existing zero initialization. Same seed gives matched initialization.
Keep existing PPOConfig: gamma1, GAE0.95, clip0.20, value coefficient0.50,
entropy0.01, Adam LR3e-4/betas0.9,0.999/epsilon1e-8/weight_decay0,
global gradient cap0.5, full-episode BPTT. No auxiliary loss or imitation.

The allowed substrate RNG namespace is B1_RUN with seed21203. Use it unchanged
for environment/action/minibatch addresses, identically across the two arms,
while declaring CBSC-DIRECT-RETURN-B02 and fresh output paths in outer metadata.
Existing strict checkpoint payload/object identity stays unchanged. New scientific
object metadata belongs outside that payload. No old model/optimizer/checkpoint
or old failed-output selection is used. No host/address/token change is selected.
New scientific output root is
temp/directions/capability_bound_semantic_currentness/exp/cbsc_direct_return_b02_seed21203_<launchsha>/
with separate RAW/STRUCT outputs; the corresponding engineering fixture uses
temp/directions/capability_bound_semantic_currentness/test/cbsc_direct_return_b02_<launchsha>/.
CM records exact paths/task names after source is committed. Existing roots are
read-only; no evidence deletion or external communication side effect belongs to this card.

## Actual work and dominant factors

Each arm trains 48 updates, eight fresh episodes per update. Update index u=0..47
uses TRAIN episode IDs8*u ..8*u+7. Each update has four epochs and four
two-episode minibatches, hence16 actual Adam steps. Repeating0..7 is not48rollouts.

| Quantity | Per arm | Two arms |
| --- | ---: | ---: |
| Training episode executions | 384 | 768 |
| Training transitions | 58368 | 116736 |
| Training decisions | 9216 | 18432 |
| Rollout updates | 48 | 96 |
| Adam steps | 768 | 1536 |
| Evaluation episode executions | 128 | 256 |
| Evaluation transitions | 19456 | 38912 |
| Train+evaluation transitions | 77824 | 155648 |

These are execution counts, not independent samples: there is exactly **one
paired independent training seed**, and the four checkpoints reuse32 stochastic
environment roots. Two deterministic context policies score the same32 tapes
once in the RAW invocation:64 ledger-scoring passes, not new training or world
population. The computed count artifact is CBSC_DIRECT_RETURN_B02_COUNTS_20260905.json.

Intrinsic work is2 arms *1 seed *48 updates *8 episodes and2*1*4*32 evaluation
executions; PPO performs2*48*4*4 optimizer steps. There is no policy-class search,
candidate-trajectory search, exact upper, support census or replanning prerequisite.
The old B1 scheduled training/evaluation transition count is7.5times this count;
that is only a count comparison, not a runtime or total-publication saving.

## Measurement and source assignment to CM

Own one thin module:
experiments/candidates/capability_bound_semantic_currentness/direct_return_b02.py;
one thin runner: scripts/run_cbsc_direct_return_b02.py;
one focused integration test:
tests/experiments/candidates/capability_bound_semantic_currentness_omrc_b01/test_direct_return_b02.py.
Existing omrc_b01 source, old attempts and shared surfaces are read-only.
CM may reuse its existing implementer/reviewer path; it owns source and runtime
acceptance, while DM owns interpretation and Root integration.

Use actual DynamicHost.build_stochastic -> EpisodeTape;
engine._project_panel -> observations/work;
engine._rollout_from_panel -> EpisodeRollout/evidence/uniform digest;
RecurrentPPOTrainer.train_rollout -> actual loss records/counters;
engine._evaluate_heldout -> action-name records/state checks;
Action[name] conversion -> evaluator.evaluate_episode on the same tape.
That evaluator's return is a record with numerator/denominator/float display,
not a scalar returned by the held-out helper. Do not use build_b0_panel.

Generate primary measurements during evaluation, then save/read them back.
Retain episode identities and24 chosen actions, checkpoint states at0/12/24/48,
actual update/transition/evaluation counts, actual losses/work per update,
configuration/source/seed/RNG-namespace metadata and initial/final parameter
movement. Sum both decision and settlement ledger contributions. Write the
32 paired differences/mean and both four-point curves during the second arm's
bounded call after reading the first arm's identity-bound result.

This path does not use b1_metrics_production, b1_metrics_rehydrate, replay workers,
the old fifteen-table transaction, full historical truth/support reconstruction,
or all intermediate arrays. PI/DERANGED, motifs/twins, AUC selection and their
mechanism-specific conclusions are outside the object. Existing native Fraction
arithmetic can remain; no universal extreme tolerance is introduced.

## Single changed-path verification and shared risk

The selected unique new focused integration check covers both arms, real host,
public-only projection, legal actions, one eight-episode PPO update, real
parameter movement/counters, action-name conversion, chosen-action native
decision+settlement sum, output writing and readback.

Use engineering seed21201 in B1_RUN, TRAIN0..7, one EVAL_STOCHASTIC episode0,
evaluated at updates0and1 for each arm. It yields32 Adam steps,2432 training
and608 learned-evaluation transitions (3040 total), recorded separately as
engineering exposure. Context-policy scoring verifies delayed REFRESH reward
on the same tape, with no extra environment search. It is not a new scientific
seed or exposure-proof experiment.

Existing host/token/addressing code is still a required dependency. The old
SIGSEGV and different TypeError do not establish its correctness or its failure
on the new route. If this focused path exposes a primary-relevant defect, return
that exact dependency and its measurement impact; do not silently rewrite the
host/interpreter or reproduce old failures as a ritual. This is one focused
check, not another smoke for every launch/checkpoint.

Prior charged focused/offline time remains124.49/300seconds. The new complete
check has at most175seconds including2seconds kill grace (timeout173seconds),
within the175.51seconds actual remaining allowance. Charge its actual wall to
the same directory account; no renamed directory or unused old budget resets it.
If required coverage cannot complete, return the concrete coverage/budget gap.

## Execution, resources and stopping

Formal execution order: RAW then STRUCT, at most one complete invocation per
arm. This order is fixed before either outcome and is not selection by result.
Each complete arm invocation has a **600second wall cap including startup,
admission/host construction, training, four evaluations, checkpoint/result
publication/readback, pair summary in the second arm, and termination grace**.
Use an outer bound whose timeout plus grace does not exceed600seconds.
Do not move pair analysis to an uncharged later script.

New complete runtime is unknown. Source-backed law:
startup + host generation + sum48(rollout/update) + sum4(eval32) +
checkpoint/publication/readback + pairing(second arm) + finish/grace.
Old333.27086seconds is a historical training-slice+replay componentwise envelope,
not the new complete forecast. No C++/GPU/parallel saving is measured or assumed.

Node: configured wsl_4070, /home/wu/.venvs/hmasd/bin/python, CPU FP32,
one scientific process and one Torch compute thread; numeric library threading
is kept at the existing single-thread execution design. No GPU use or node
migration is selected. Commit/push and Root integration precede execution on
an exact-source detached worktree; normal doc-only integration does not change
source identity. Every actual invocation has fresh physical/effective available
memory>=4GiB on that node, immediately before model/RNG/results, joined to
the runner in the configured detached agent-task command. CM sends accepted
handles directly to the current shared tracker and this DM.

Scope machinery: **none**. No new worker pool, resumability, service, registry,
provenance guard or standing profiler. Ordinary <=2000 new non-test lines and
<=600 runner lines apply;30% is a review signal. Old A174/D429 and evidence stay
unchanged. A claim-dependent runtime correctness check is not a generic gate.

End at complete result intake or a concrete primary-path failure, necessary
dependency/budget gap or complete-invocation cap. No automatic retry, extra
seed, training extension or fourth old formal publication. If either endpoint,
pair identity or truthful native reward is absent, the paired performance
conclusion is unavailable; independently trustworthy narrower observations
remain reportable. Optional resource gaps alone limit resource claims.

## Exposure, prediction, MEI and interpretation

Machine exposure line: consultation ran zero new optimizer steps. Existing B0
after16 Adam steps moved1.5308%..1.5884% of initial parameter L2. This supports
ability to move, not linear displacement or performance at768steps. Formal
initial/final movement and actual counters are reported by each arm.

Headroom: matched tuned-generic/upper record absent (HC-M/mismatched historical
assets), not zero and not a prerequisite.
MEI: **0.25 native return per episode**, about1.04% of theoretical maximum24.
It is a practical threshold for considering more independent training, not a
significance rule or fraction of measured headroom.

DM prediction: weakly expect a positive difference exceeding0.25 by update48,
with low confidence because RAW contains the information and LR01 was mixed.
Alternative: competent RAW matches/exceeds STRUCT, or poor RAW makes any gap
comparator-limited. Owner prediction: not taken (unattended). Unscored at freeze.

Above MEI with trustworthy training, pairing and reward suggests keeping this
comparison for one or two fresh training seeds; those calls are not selected
now. Small, adverse or comparator-limited outcomes stay visible and can justify
only a specific next B. A negative inside the MEI must still be reported as
negative. No all-positive-seed, statistical-significance or mechanism-localization
requirement precedes a bounded follow-up recommendation.

Claim ceiling: one local finite-budget paired-seed native performance observation.
No stable/cross-seed superiority, semantic specificity, PI/DERANGED exclusion,
representation necessity, multi-agent coordination, roster/partner co-adaptation,
UAV transfer, exact support statement or restoration of old B1/r05 validity.
