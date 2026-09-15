# FOLR entity-history B03 — result evidence

Object FOLR_ENTITY_HISTORY_B03_781501, exploratory B. The frozen
[science card](FOLR_ENTITY_HISTORY_B03_SCIENCE_CARD_20260914.md) selected one fresh
fit per arm, training781501/evaluation1781501. Exact execution source is
b257dcb1d7578a057afa9b4bdd7c7ff74ad8e24f. Both detached invocations finished exit0;
all selected endpoints are complete and technically accepted. No empirical retry,
checkpoint choice, extra panel or unselected third block occurred.

## Rule and actual outcome

The frozen rule is strict BANK-minus-Generic>+1: BANK_ABOVE_MEI; inclusive[-1,+1]:
WITHIN_MEI retaining sign; strict<-1: GENERIC_ABOVE_MEI. Actual d_B03=-6.63671875,
so the result is **GENERIC_ABOVE_MEI**. The gap favoring Generic is6.63671875;
its excess beyond the declared MEI1 is5.63671875. MEI is a practical return scale,
not a significance, equivalence or competence threshold.

| Endpoint | Generic64 | BANK16 |
| --- | ---: | ---: |
| Final mean native return | 4.9259375 | -1.7107812500000006 |
| Conditional episode sample SD | 8.014662295605376 | 2.7730425058360044 |
| Conditional episode SE | 0.7084027572678379 | 0.24510464504939686 |
| Minimum / maximum | -11.67 / 24.26 | -10.14 / 7.56 |
| Negative final episodes | 40 / 128 | 97 / 128 |
| Fresh fitted policies | 1 | 1 |
| Training episodes / native ticks | 5000 / 100000 | 5000 / 100000 |
| RMSprop optimizer updates | 4969 | 4969 |
| Final greedy episodes / native ticks | 128 / 2560 | 128 / 2560 |
| Actor named parameters | 103173 | 89573 |
| Complete native invocation wall (s) | 2005.71 | 1774.14 |
| Native user / system CPU (s) | 1859.24 / 143.95 | 1347.24 / 425.63 |
| Peak RSS (KiB) | 767384 | 751632 |

Total2fits/205120native ticks/9938optimizer updates/256final episodes. CPU FP32,
Torch intra/inter1/1; easy Traffic Junction H20/five slots/vision1/native reward,
actions and transitions; equal legal information; full-episode replay32 and unchanged
learner. Generic ran first and was fully collected before the already selected BANK.
BANK used Generic summary SHA256
d1b46eac0487632de92ba33e22d029a64882e66633b7418f2d50b2c01fe4e2ec
for pair publication only. It used no Generic checkpoint or learned state.

Every array is finite with declared lengths. One weights-only CPU checkpoint read
per arm verifies arm,4969updates and finite FP32 actor/mixer/targets without actor
construction, RNG sampling or new learning/evaluation. Fresh memory admission passed
immediately before each arm with at least4GiB physical/effective headroom.
[GENERIC_COLLECTION.json](entity_history_b03_781501/GENERIC_COLLECTION.json) and
[BANK_COLLECTION.json](entity_history_b03_781501/BANK_COLLECTION.json) preserve full
member manifests, native timings and checks. The original summaries, complete
checkpoints and supervisor logs are in the published GENERIC_RAW.tar.gz and
BANK_RAW.tar.gz. Archive SHA256s are respectively
5ca1b84e5f262eea476b1219b7284840b029cdee97947af73a73666b525bfb04 and
cbfb535cda8dca062e37737e336fd84f8a7b5c0f15d0cc935ebcbb7650a0ca10.
All copied archive/member hashes were verified; no raw observation is excluded.

## Recalculation, units and historical comparison

The short accepted B02 descriptive analyzer was reused with B03 identity/seed and
exact-source checks. Python statistics independently matches native panels and the
frozen rule. The scientific-tools run summarizer receives one already aggregated
policy endpoint per arm, without --paired, and reports n=1 with across-run SD absent.
The full [RESULT_SUMMARY.json](entity_history_b03_781501/RESULT_SUMMARY.json),
[analysis receipt](entity_history_b03_781501/ANALYSIS_RUN.json) and
[run-level summary](entity_history_b03_781501/RUN_LEVEL_SUMMARY.json) preserve this.
The [figure](entity_history_b03_781501/RESULT_FIGURE.png) was visually checked: fixed
non-overlapping100-episode training windows and all128 final returns per arm.
Both training traces improve from early values. Generic continues rising late;
BANK's displayed late windows are flatter. These exploration-policy windows do not
establish convergence, greedy training-time return or longer-learning rankings.

| Complete prospective block | Generic mean | BANK mean | BANK minus Generic | Rule |
| --- | ---: | ---: | ---: | --- |
| B02: train781401/eval1781401 | -0.65296875 | -5.483828125 | -4.830859375 | GENERIC_ABOVE_MEI |
| B03: train781501/eval1781501 | 4.9259375 | -1.71078125 | -6.63671875 | GENERIC_ABOVE_MEI |

These are two separately selected complete learning-and-evaluation realizations;
they do not isolate pure training variance because both seeds change. No episode
pooling, paired-episode SE, meta-estimate, training-population interval or stable
ranking is claimed. Improved absolute scores across the blocks are realization
observations, not an intervention effect. E still has a missing fresh comparison;
F remains its separate outcome-informed fixed-BANK reference-use result. E and F
share one older BANK fit and are not two BANK training replications. All earlier
negative scalar/typed evidence and stopped-family boundaries remain.

## Prediction, costs and deviations

DM predicted GENERIC_ABOVE_MEI with low confidence; the frozen branch matches.
Owner prediction was not taken (unattended); fresh owner-console review read returned
no entry. This does not score a fabricated owner prediction or estimate calibration.

Complete native walls sum3779.85s; aggregate native CPU3776.06s. Supervisor study
elapsed is4424s (08:24:20Z to09:38:04Z), with644s inter-arm gap, measured to integer
seconds. Native GNU time remains primary per-invocation timing. Runner-reported
walls1943.733741/1708.923375s exclude some surrounding work; Monitor uptimes are
observation ages and are not invocation duration. No speed comparison follows.
Collection plus descriptive analysis measured8.968s in selected non-overlapping
windows; prior preparation, focused-test, launch and observation windows remain in
receipts, while total support/provider costs remain UNKNOWN. E3557.28+F2159.85+
B023041.46+B033779.85=12538.44known native seconds, not the entire direction cost.
No accounting reset or full combined-plan compliance is claimed. Actual native work
is below the DM7200s native plan; that plan is neither owner cap nor scientific gate.

The initial sparse-checkout launch-script lazy-fetch helper failed before any
supervisor acceptance, admission or training. Its owned process group was reconciled
and removed, and exact committed scripts were then staged through configured login
Git. This was not a scientific retry. The initial Monitor prematurely finalized three
turns during Generic; the same live handle was transferred to a recovery Monitor,
which actually observed Generic and BANK to terminal and delivered both. These
operational failures and unknown support costs are retained in EXECUTION.json and
its receipts. They did not alter seeds, science exposure, primary or source.

## Accepted claim and next scientific consequence

B03 adds a second adverse complete observation against the intact replacement-style
BANK16 package at this exact equally informed H20/5000 endpoint. It strengthens the
case against repeating that unchanged prototype as the default development action.
It does not identify the cause, establish universal memory harm, Generic sufficiency,
matched capacity, tuned headroom, optimality, convergence, population superiority,
transfer, C-BENCH, UAV or original-CAMA equivalence. No direction PARK follows from
this result alone. The [DM intake](FOLR_ENTITY_HISTORY_B03_INTAKE_20260914.md) develops
a concrete alternative and strongest counterarguments for independent review.
