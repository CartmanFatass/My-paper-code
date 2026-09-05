# N3 DISH B01 C04 — complete three-seed result evidence

Date: 2026-09-04 PDT. Object `DISH-FIRST-TRIGGER-SOURCE-SCOUT-B01`, **B / EXPLORE**.
Result: **FTS-B0 — TRIGGER_SUPPORT_INSUFFICIENT**. All three original seeds are valid;
none exposes a source comparison. A/B have no consumption state.

## E0 — question, rule and bounded reading

The card asks whether prepared SHADOW state improves 100-tick recovery over incumbent COPY
after the first application-valid owner handover, with RETAIN as the shell-matched remap control.
The card's usable-support rule is: "A seed has **usable trigger support** when at least four
of sixteen rows trigger and the triggered set contains both packages."

The aggregate instruction is "Apply the following branches in order to three complete seed
summaries:". All three are now complete. Its first branch applies verbatim:

> **`FTS-B0 — TRIGGER_SUPPORT_INSUFFICIENT`.** Fewer than two seeds have usable trigger support.
> Reading: this budget/panel did not expose enough first-valid opportunities to compare sources.

There are **zero usable seeds out of three**, with **zero triggered rows out of 48**. The DM
independently recomputed the support predicates from original rows and ran the existing
`classify_three_seed_result` reducer over the three original estimand dictionaries; it returns
`FTS-B0`. No later ordered branch is reached. Raw zero differences and `shadow_nonharm=true`
are empty-support defaults, not sampled equality or observed nonharm. The five-service-tick
descriptive MEI is unidentifiable. This is a fixed-budget/panel trigger-support observation,
not a source-value negative, natural prevalence estimate, family closure or N3 disposition.

## Counts and exposure

| Quantity | Seed 11 | Seed 29 | Seed 47 |
| --- | ---: | ---: | ---: |
| Native training transitions | 262,144 | 262,144 | 262,144 |
| Learner updates / optimizer steps | 64 / 2,048 | 64 / 2,048 | 64 / 2,048 |
| Distinct declared panel rows / triggered | 16 / 0 | 16 / 0 | 16 / 0 |
| Prefix ticks / branch consequence ticks | 19,200 / 0 | 19,200 / 0 | 19,200 / 0 |
| Initial parameter norm | 38.19731474061207 | 38.286447586375616 | 38.193747358754344 |
| Final parameter norm | 41.78517869974931 | 41.81658102299228 | 41.7205655228189 |
| Relative total L2 displacement | 0.42465718774783356 | 0.419585027483137 | 0.4196544358013136 |
| Raw maximum per-tensor displacement ratio | 1.2535341627432597e300 | 1.0764195675299437e300 | 1.1524722211249414e300 |
| Runner wall seconds | 1068.1102725170058 | 977.5005878610027 | 995.6141687410054 |
| Logged supervisor wall seconds | 1099 | 1017 | 1040 |
| Peak RSS bytes | 628,801,536 | 628,461,568 | 640,073,728 |

Total actual learner work is **786,432 transitions, 192 updates and 6,144 optimizer steps**;
evaluation is **57,600 prefix ticks, zero branch ticks**. Rows within a seed are paired
conditions, not independent learner replicates. Every checkpoint has 50 finite model tensors,
36 finite optimizer states at step 2,048 and update 64. Actor/snapshot/critic Welford counts
are 1,048,576 / 0 / 262,144 per seed. Checkpoints are 2,070,711 bytes each.

CM recomputed each final norm exactly from the retained checkpoint. Initial norms and total
displacements are original runner observations: initial checkpoint bytes were not separately
published. The huge finite per-tensor ratios use `max(initial_tensor_norm,1e-300)` for initially
zero tensors. They remain visible with this zero-reference limitation and are not meaningful
percentages or nonfinite learner failures. No metric was changed after observation.

## Receipts, artifacts and resource accounting

All runs use source **`e0541d0cb3e9e63731c72f4dacb10b44d268fd39`**, CPU FP32 learner,
float64 native physics, one Torch thread and unchanged carded RNG/training/evaluation semantics.
Node `wsl_4070`; cwd `/home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c`.
Tasks are `dish_b01_c04_seed11_e0541d0c_a1`, `dish_b01_c04_seed29_e0541d0c_a1` and
`dish_b01_c04_seed47_e0541d0c_a1`, each terminal with existing exit witness 0.

| Seed | Fresh admission UTC | Physical and effective available bytes | Start / terminal UTC |
| --- | --- | ---: | --- |
| 11 | 2026-09-05T00:12:03.356900Z | 12,531,122,176 | 00:12:03 / 00:30:22 |
| 29 | 2026-09-05T00:47:14.317386Z | 15,432,970,240 | 00:47:14 / 01:04:11 |
| 47 | 2026-09-05T01:12:59.650750Z | 13,040,766,976 | 01:12:59 / 01:30:19 |

Every admission has both floor flags and `passed=true`, no failure reason, and a 4,294,967,296
byte floor. Each is adjacent to its one scientific invocation. Start admission is not runtime
telemetry. All three report measured wall/RSS; scratch is unmeasured. Actual aggregate runner
cost is **3041.225029119014 seconds (50.6871 minutes)**; logged supervisor cost is **3156 seconds**.
The total is charged once to the direction. Conservatively each source arm receives the full
seed cost for its comparison; no seed exceeds the frozen 1474.544745605439-second projection
or 1800-second cap. Tracker observation uptime after termination is not execution duration.

Remote originals are under cwd-relative
`temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed{11,29,47}_a1/`
(`summary.json`, `checkpoint.pt`), with sibling `seed{11,29,47}_a1_admission.json` receipts.
Supervisor witnesses remain in `/home/wu/.agent-tasks/<task>/`. Collected originals, logs and
wrappers are in the same relative root of `C:/Projects/HMASD-worktrees/cm-n3-dish-c04-20260904`.

Tracked `N3_DISH_B01_C04_SEED{11,29,47}_SUMMARY_20260904.json` files are byte-identical to
original summaries. Their collection records are the corresponding `..._COLLECTION_...md`:
seed 11 at `17018ec74592c0b29254006006fac03f951e22c5`, seed 29 at
`da86d9126ebf15a87cd16bde68dbe623082b855c`, seed 47 at
`4320f13a9cbde49109410f3677eb8ec21ddec4c9`.

## What was checked, deviations and remaining engineering limits

DM parsed original summaries/receipts, checked their equality to tracked bytes, reconstructed
each exact package x schedule x speed x slot product, checked all row and work counts, and
recomputed usable support and the ordered rule. CM collected existing artifacts and checked
checkpoint finiteness, counters and final norms without rerunning learners or evaluation.
The card explicitly admits no-trigger rows; absent conditional fork receipts and metrics are
not incomplete instrumentation on those rows.

No scientific, numerical, RNG, checkpoint or side-effect deviation was found. The accepted
C04 correction changed launcher quoting and one proven overly broad action-equality test only;
production precision and action laws stayed fixed. Scope section-4 additions: none. The
accepted implementation remained within section-5 budgets (+1198 non-test lines, runner 118,
orchestration 274/1198 = 22.9%). Full automated `_run` publication-path coverage remains open,
although real learner-to-no-trigger publication completed three times. A real triggered
scientific branch has still not been observed. These limits do not create source polarity.

## Prediction, support, contradiction and next discriminator

The original DM prediction **FTS-B0** is correct on this complete object. The conditional
FTS-BC prediction was not tested. Owner prediction: **not taken (unattended)**; no outstanding
owner instruction was returned at intake. No tuned same-information B01 headroom is available.

Strongest support is complete non-exposure over the exact panel at three independently trained,
finite and measurably displaced checkpoints. The strongest limit against a mechanism negative
is that the source intervention never acted. Proposal competence, preparation/delivery support,
application eligibility and physical/terminal opportunity remain unresolved; prefix length
alone does not establish live opportunities. Useful shadow state, generic-copy sufficiency,
replay/replan containment and training co-adaptation all remain live.

The smallest next discriminator is A/RECON measurement of the unchanged seed-11 checkpoint's
original sixteen prefix rows, recording where the handover chain stops. This diagnoses one
retained path; it cannot establish a source effect or replace a new B comparison.
