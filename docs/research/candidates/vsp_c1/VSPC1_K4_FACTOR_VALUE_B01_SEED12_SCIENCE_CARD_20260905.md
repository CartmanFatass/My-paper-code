Claim tested: Repeating the fixed factorized-versus-generic comparison on two independent training seeds will show whether seed0's local adverse endpoint/AUC is sensitive to training randomness.
Binding structure: (b) temporal abstraction or termination; the same exogenous periods constrain held service actions and their renewal credit.

# VSP-C1 K4 B01 — independent seeds 1 and 2

Class: **B/EXPLORE**. Rung label: `VSPC1-K4-FACTOR-VALUE-B01-SEED12`. This is a bounded seed extension of the same B01 comparison, not a new family, C freeze, new algorithm or rewrite of seed0. The original card and result remain unchanged. Selection is the object-tier [seed0 intake, decision 2](VSPC1_K4_FACTOR_VALUE_B01_INTAKE_20260905.md): `OWNER_DELEGATED` under the standing 2026-09-03 unattended instruction.

## Complete inherited science and exact change

The [original B01 card](VSPC1_K4_FACTOR_VALUE_B01_SCIENCE_CARD_20260905.md), §§1–9, supplies the complete host, population, treatment/comparator, RNG, learner, evaluation, cost/stop and engineering meanings. They are incorporated here in full except the selected training seeds and the follow-up reading rule below. The source behavior actually accepted at `e7e574b4496875f45e1d1b9b41c02cd35cf3684e` is the reuse baseline. Only the runner's seed admission needs to permit **1 and 2** in addition to its historically permitted 0; do not rerun seed0 or alter the algorithm, output identity, model shape, learning rate, schedule, episode weighting or any numerical/RNG path. Summaries still identify the B01 object and their actual seed; this card identifies the new rung explicitly.

Four complete invocations are selected in order: `FACTOR seed1`, `GENERIC seed1`, `FACTOR seed2`, `GENERIC seed2`. They are serial. Each starts a fresh model and optimizer with its own seed; no seed0 checkpoint or trajectory is reused. Within a seed the two arms retain the common exogenous/context and exploration streams; between seeds those streams and initialization are independent under the existing SeedSequence scheme. Existing actual stream assignments become `[s,101]` / `[s,102]`, FACTOR dense/embedding `1000*s+201/202` and GENERIC dense `1000*s+301`. Evaluation is deterministic and consumes no training randomness.

Each arm/seed remains N2, six native steps, `p={2,6}`, `tau={2,4}`, `c={0,1}`, all eight contexts equally weighted. Models remain FACTOR188 / GENERIC191, CPU FP32 with stated Xavier/embedding initialization. Each has 128 cycles of 32 real episodes and exactly 128 full-batch Adam steps at lr0.01, episode-weighted renewal loss and detached pre-update bootstrap. All nine evaluations at updates0,16,...128 use the same actual host and eight contexts. Periods/partner plans/actions are not trained or selected by an extra controller. No held-out corner, new partner, tabular arm, reference evaluation, exact A or tuning sweep is added.

## Question, headroom and predictions

Seed0 has `Delta J=-1/24` and `Delta AUC=-0.0286458333333`; its endpoint difference is one `(p6,tau2,c1)` context. J0 means are both0.5 but initial context policies differ. The new question is training-seed sensitivity of this same finite-budget observation, not a selected-positive-seed search. Single-seed evidence cannot settle whether the action asymmetry or sign is representative; observed total invocation wall was5.71s for a complete pair. This justifies two directly comparable repetitions without first explaining a unique mechanism.

MEI stays descriptive absolute `1/12`, half a service step per six-step task on average; it is no launch, significance or all-positive gate. The new toy's analytic reference is5/6; seed0's untuned GENERIC endpoint was2/3, a diagnostic gap1/6. Tuned headroom is unmeasured and historical A01 remains unavailable. Missing tuning is not a prerequisite for these repetitions. Reuse the exact host/baseline because information, action, population and per-invocation budget match.

DM prediction before new outcomes: some context/sign variation across initialization/training seeds is plausible; GENERIC is predicted to be at least competitive on average, with no reliable FACTOR advantage asserted. No individual sign is required. Owner prediction: **not taken (unattended)**. The public fixed partner still reduces the task to fully observed single-controller control; generic shared features, bilinear optimization, initialization and segment credit remain live alternatives.

## Measurements and reading rule

Report all per-seed endpoint differences, normalized full-curve AUC differences, J0 and learning gains, all nine curves and existing context/period/partner strata. The primary measure remains fixed-update128 native return; full AUC remains prespecified support. No best checkpoint, favorable early window, seed replacement or post-outcome weight change is allowed. Report new seeds1–2 separately, then explicitly label the descriptive three-seed aggregation including the historical seed0 result. The independent unit is the training-seed pair, not a context or checkpoint. Three seeds do not guarantee population superiority/equivalence or sufficient publication uncertainty; no interval is required for this B.

| Observation | B interpretation and next recommendation |
| --- | --- |
| A primary dependency is damaged or a learner does not execute | Preserve the attempt and trustworthy narrower facts; no dependent performance comparison or mechanism polarity. Return the concrete repair requirement, with no automatic replacement seed. |
| The new seeds have mixed signs or the context loss changes | Training randomness materially affects the observed comparison. Keep every result and report instability; no stable benefit/cost conclusion or run-until-positive continuation. |
| The new seeds also favor GENERIC on endpoint/AUC | Stronger but still small-sample local contrary evidence for this parameterization and budget. Do not silently close K4 or claim a universal causal negative-transfer mechanism. |
| The new seeds show a FACTOR endpoint or fixed-AUC benefit | Preserve the contrary seed0 and any opposite metric/strata. This is a limited, seed-dependent signal; no automatic benchmark promotion or further seeds are authorized. |
| Endpoints/curves coincide or differences are small | Report their magnitude and variation without proving equivalence. Decide the value of a specifically named next discriminator from the actual data. |

Above the MEI, a repeated signed effect is a more substantial local signal but still needs a claim proportional to three seeds. Inside it, report the small actual effect without declaring equivalence. Opposite signs narrow claims toward training sensitivity. Any new arm, tuning or larger claim is separately selected after this intake; none is implicit in completing the four invocations.

## Exposure, cost, portability and stop

The [computed count/projection file](VSPC1_K4_FACTOR_VALUE_B01_SEED12_COUNTS_20260905.json) records four invocations ×4,096 training episodes,8,192 renewals,128 optimizer steps,72 evaluation episodes and25,008 total joint steps each: **16,384 training episodes,32,768 renewal transitions,512 optimizer steps,288 evaluation episodes and100,032 complete joint steps**. Model shapes, batch and scoring calls are unchanged; no new nested search is present.

Prospective exposure is the original positive unfrozen Adam budget and initialization scale for each new arm/seed; expected norms4.138510931/3.627569332 and nominal sum(lr)=1.28 remain design arithmetic, not measured movement. Actual norms/displacement and nonzero transition/update/evaluation counts must come from each new invocation. Seed0's actual ratios0.506819673/0.436521756 are reuse evidence that these learners moved in this budget, not substitutes for the new measurements or a minimum-ratio gate.

Each complete arm/seed invocation retains the original **2700-second cap** including imports/init/train/evaluation/checks/publication. Four cap sums are10800 invocation-wall seconds, not an elapsed-study target. Applying the existing exact-shape observed complete unit costs gives conditional projections1.76s per FACTOR and3.95s per GENERIC invocation,11.42s summed for four. Actual runtime/host contention can differ; no speedup ratio, universal overhead multiplier or new calibration is claimed. Directly measure the four complete invocations and distinguish study elapsed, summed wall and aggregate CPU. No additional compute beyond the four selected runs is allocated by the projection.

Keep remote-first configured `wsl_4070`, CPU FP32, one process/compute thread, in-process batch32 and original prospective host portability. Each invocation gets its own immediately adjacent actual-node physical/effective≥4GiB admission before scientific state construction, joined with the exact runner under existing detached `agent-task`. Commit/push accepted source before execution. Local fallback retains the original no-accepted-remote-process/fresh-destination-admission conditions. Do not switch device or migrate a live run.

Stop each invocation at its cap or an actual failure; preserve its observed counts/output. No automatic continuation, rescue seed, extra epoch, model change or rerun is authorized. CM owns technical acceptance and tracker handles; DM owns the complete scientific intake.

## Bounded CM continuation

Reuse `/root/dm_amx_k4_vspc1_design/cm_am_vspc1_b01` and its existing implementer/reviewer as needed. Ownership remains the existing runner/attempt/mirrored tests and CM technical record. Expected source change is only the runner's accepted seed choices; changing a scientific dependency requires a concrete return to DM. Scope §4 additions: **none**. Keep original source/runner/test budgets and single-layer tensor batching; do not add an experiment framework, replay platform, validator or profiler.

Reuse the accepted source/primary-output checks for unchanged behavior. Review the seed-selection diff and verify actual new seed/context/update/evaluation records; a changed permitted seed list does not justify an extra learner/environment smoke or all-history replay. Each selected run exercises the actual primary write/read path within its budget. All four outputs and their complete technical evidence are retained. No ordinary Root/owner approval, Pro round or GitHub capability pilot is a launch condition.
