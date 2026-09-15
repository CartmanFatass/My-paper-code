# TRDL B01 — native result evidence

Class **B/EXPLORE**, complete original pair, source`0874ccfb6102859e5cd7ecfbc4b7d578eab06d91`. Read the [card](TRDL_B01_SCIENCE_CARD_20260914.md), [scientific intake](TRDL_B01_INTAKE_20260914.md), [pair summary](trdl_b01_9601/PAIR_SUMMARY.json), [validation](trdl_b01_9601/VALIDATION.json) and [raw archive](trdl_b01_9601/RAW_RESULTS.zip). This is one matched training instance per method and an outcome from the selected complete packages.

## Reading rule and primary observation

Rule applied verbatim: “`Delta_tail > .01`: Q32_ABOVE_MEI; `-.01 <= Delta_tail <= .01`: INSIDE_MEI; `Delta_tail < -.01`: SCALAR_ABOVE_MEI.” Each arm independently selects its own64 lowest of256 final stochastic J returns, with J=native team reward sum/256. This is not the tail of paired differences.

| Final observable | SCALAR | Q32 | Q32−SCALAR |
| --- | ---: | ---: | ---: |
| Own64-of256 mean J, primary |0.08521000753530991|0.11977347559882232|**+0.034563468063512404**|
| Ordinary256-return mean J |0.14086419139155873|0.19251225542684883|+0.0516480640352901|
| Own64th return threshold |0.1106247841291423|0.15216589320388105|not a primary contrast|

Observed branch **Q32_ABOVE_MEI**. There is no ordinary-mean harm in this panel, although55 of256 matched-reset rows have a lower sampled Q32 return. All512 final observations remain preserved. Those matched rows retain private action randomness and are not independent training replications. No training-population uncertainty is estimable from this pair, and no paired-mean SE or confidence interval is presented as tail uncertainty.

## Actual exposure, learner and technical receipts

Each original completed512 H256 training episodes,256 H256 final-evaluation episodes,768 explicit resets plus one unscored constructor reset,196608 successful team steps and128 sequential nonzero-lr joint Adam calls. Pair totals:1024 training and512 final episodes,393216 scored team ticks,256 joint updates; no retry, extra native smoke, pilot, model selection or additional evaluation. CPU FP32 and Torch compute threads1 were reported by both runners. Independent [source review](TRDL_B01_INDEPENDENT_REVIEW_20260914.md) and [engineering checks](TRDL_B01_ENGINEERING_20260914.md) preceded accepted launches; these are separate from this scientific acceptance.

| Learner movement | SCALAR | Q32 |
| --- | ---: | ---: |
| Trained actor parameters |34902|34902|
| Trained critic parameters |34305|38304|
| Actor L2 displacement / initial norm |1.229894995689392 /12.57728385925293|1.3208191394805908 /12.57728385925293|
| Critic L2 displacement / initial norm |0.5683510899543762 /9.317988395690918|1.1893601417541504 /9.870976448059082|
| Maximum preclip combined gradient norm |0.21656954288482666|0.1387568861246109|

Both actor and critic gradient norms were positive in every logged epoch; all32 own-batch thresholds had three strictly-negative scores. Per-batch eta and scores stayed identical across its four epoch rows. The .5 joint clipping threshold was never reached in these logs: threshold activation therefore does not explain this particular difference. This observation does not isolate representation, prove an adequate critic or remove other target/loss/PPO/fitting differences. First/last critic losses refer to changing batch targets and incomparable loss units, not a matched calibration assessment. The nominal128×.0003=.0384 learning-rate sum was never a displacement bound.

DM validated every raw episode's identity/reset schedule/steps/reward_sum/H, all128 update counters and batch/epoch groups per arm, each own-batch FP32 fourth order statistic and score count, final return vectors versus summaries, independent own-tail reductions, and finite FP32 checkpoint/source/master/arm/update/parameter-count/final-norm facts. Checkpoint loading performed no model construction, native call or optimizer update. The committed pair-publication path and independent recorded-array reduction agree. Technical checks do not establish population efficacy or baseline tuning adequacy.

Native supervisor handles`trdl-b01-9601-scalar` and`trdl-b01-9601-q32` both finished/exit0, tmux inactive, as independently read during collection. SCALAR native log terminates2026-09-15T03:37:39Z, Q32 at03:37:53Z; both supervisor duration198s. Monitor returned terminal events at03:39:17Z and empty active set. Its initial adoption's one-day timestamp error was corrected from actual node time in the [execution intake](trdl_b01_9601/EXECUTION_INTAKE.md); it does not alter any experiment timestamp or measurement.

## Complete costs, retained bytes and limits

| Native whole invocation | SCALAR | Q32 |
| --- | ---: | ---: |
| `/usr/bin/time` wall seconds, including exit |197.99|197.65|
| User / system CPU seconds |196.71 /0.83|196.42 /0.82|
| Peak RSS KiB |655784|655900|
| Training collection wall seconds |123.49519179330673|123.91270945011638|
| Frozen baselines / update wall seconds |0.1884656430920586 /9.628233249182813|0.212580201565288 /9.694596285698935|
| Final evaluation wall seconds |58.8489129160298|57.94614104903303|

Sum of whole-arm wall is**395.64s**, distinct from the approximately212s overlapping supervisor study span. Collection phases include explicit resets; constructor initialization includes its reset, whose separate unit rate remains unmeasured. Final JSON/exit is inside invocation timing even though it follows the runner's closeout timer. No time is excluded from native accounting. These two observed walls are not isolated method-cost experiments or guaranteed future rates; source/support/provider/agent/maintenance costs remain incompletely measured. Focused-test invocation wall is11.8756571s total. No scientific/test/code budget breach occurred; ordinary runtime plans were not hard funding caps.

The647102-byte RAW_RESULTS.zip contains24 transferred files: both complete arm summaries, episode/update rows and checkpoints, adjacent admissions, whole-invocation time files and supervisor records/logs. Archive CRC verification passed; preservation SHA256`e10085a57a9f950a9ec5fed0852b8e7b64041b777a8f4c472735778812ebc8b2`. This post-collection archive checksum preserves evidence; it is not a new runtime provenance gate. [Cleanup inventory](trdl_b01_9601/CLEANUP_INVENTORY.md) retains active/shared authoring, source transport and policy-blocked test scratch until the proper retention/cleanup boundary.

Strongest support is the complete native own-tail increment with positive ordinary-mean difference and nonzero learning. Strongest surviving alternative is finite fitting/optimization or favorable training/action realization against an untuned scalar recipe; a competent scalar conditional W estimator could suffice. Matching tuned host headroom remains absent. This is not exact/unbiased CVaR, stable superiority, scalar-class inadequacy, pure representation/credit cause, expected-return-objective superiority, novelty, safety, transfer or K-axis attribution.
