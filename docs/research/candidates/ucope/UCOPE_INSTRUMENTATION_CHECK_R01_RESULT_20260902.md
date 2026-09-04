# UCOPE-A-INSTRUMENTATION-TAIL-AGREEMENT-COMPETENCE-CHECK-R01 — result

- Direction: `ucope`
- Object id: `UCOPE-A-INSTRUMENTATION-TAIL-AGREEMENT-COMPETENCE-CHECK-R01`
- Evidence class: **A/RECON — instrumentation check** (outcome-free; no polarity; consumes no
  B object)
- Card (written first): `docs/research/candidates/ucope/UCOPE_INSTRUMENTATION_CHECK_R01_CARD_20260902.md`
- Check: `tests/experiments/candidates/ucope/test_instrumentation_check_r01.py`
- Date: 2026-09-02
- Interpreter: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` (Python 3.10.20, torch 2.7.0+cpu)

## 1. Command and outcome

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
  tests/experiments/candidates/ucope/test_instrumentation_check_r01.py \
  --basetemp C:/Projects/HMASD/temp/directions/ucope/test/instrumentation_check_r01g
```

`77 passed in 36.85s` — **the check PASSES.** No measurement was shown defective, so no dated
note is added to the R01 rung-1 or rung-2 result documents, and no runner fix was required.

## 2. Pass / fail per measurement

| # | Measurement | Verdict | Deciding numbers |
| --- | --- | --- | --- |
| M0 | The check's independent reference reproduces `oracle.py` exactly | **PASS** | exact `Fraction` equality on `tail_return` (18 values), on all 56 count masses and beliefs, and on all 8 oracle rows |
| M1a | Tail agreement, true value **0**, both arms | **PASS** | always-period-8 policy: per-context agreement `0` in all 8 contexts; recorded `minimum_tail_agreement == 0.0` |
| M1b | Tail agreement, true value **1**, both arms | **PASS** | exact-oracle beta `(0.31, 0.60, 1.35, -1.08, -0.891)`: agreement `1` in all 8 contexts; recorded `1.0` |
| M1c | Tail agreement, intermediate values, both arms | **PASS** | always-4 → `5306040/128000000 = 0.041453`; belief-threshold policy → `66653020/128000000 = 0.520727` (per-context `79071420/128000000 = 0.617745` at `LINKED-p13_20-*`, `1` on `SEVERED`); every recorded value matches the reference to `<= 1e-12` |
| M1d | An exactly-`1/2` level is unattainable | **PASS (claim proved, not assumed)** | exhaustive enumeration of all `2^7 = 128` subsets of the seven count masses, for each of the four `LINKED` contexts: `1/2` is in none of them |
| M1e | The frozen 5-term basis can represent the true tail value | **PASS** | max |basis value − exact expected tail return| over all 224 (context, count, period) points `< 1e-6` (fp32 only) |
| M2a | The competence predicate can fire — positive control, both arms | **PASS** | exactly-optimal root+tail: `competence_pass True`, `max_regret 0.0`, `minimum_tail_agreement 1.0`, `oracle_root_match True`, root vector `= {7 x IMMEDIATE, PROBE at LINKED-p17_20-c9_100}` |
| M2b | Root scores reproduce the oracle's own values | **PASS** | every `PROBE` and `IMMEDIATE:k` score within `1e-6` of `build_oracle()`; so `max_regret = 0` is a true zero |
| M2c | All four reported components vs the reference, 12 synthetic policies × 2 arms | **PASS** | `root_actions`, `oracle_root_match` exact; `max_regret`, `minimum_tail_agreement` to `<= 1e-12`; `competence_pass` identical |
| M2d | Component isolation — wrong root only | **PASS** | perfect tail + always-`IMMEDIATE:4` root: agreement stays `1.0`, `oracle_root_match` flips to `False`, `competence_pass False`, `max_regret = 0.02143710125` (the target context's `probe_value − baseline`) |
| M2e | Exact (`Fraction`) predicate vs float predicate | **PASS** | `validate_policy_evaluation` accepts every synthetic row and agrees on `competence_pass` |
| M2f | The two arms are the same function when the FLEX residual is zero | **PASS** | identical `tail_periods`, `root_selected_labels`, `minimum_tail_agreement`, `max_regret`, `competence_pass` for all 6 tail policies |
| M2g | The FLEX residual is actually read | **PASS** | a constant residual of `0.25` shifts every root and tail score by `0.25` (`< 1e-5`) and changes no choice |
| M3a | Displacement arithmetic vs hand computation | **PASS** | 24 rows, all six fields to `<= 1e-12` against an independent recomputation using the same FP32-then-FP64 order |
| M3b | FLEX residual **inside** the aggregate, **outside** the beta line | **PASS** | residual-only move of `0.5`: `parameter_displacement_l2 = 0.5`, `beta_displacement_l2 = 0.0`, `beta_max_abs_coordinate_move = 0.0`, `learner_can_move_in_its_budget = False` |
| M3c | The initialisation scale is arm-dependent | **PASS** | tail stage, seed `…fresh-00` fold 0: FLEX `9.102437056195274` over 4,870 coordinates, BC `1.5502197353913905` over 5 coordinates; ratio `5.87` |
| M3d | The **published** exposure lines recompute from the published checkpoints | **PASS** | all 24 rows of rung 1 and all 24 of rung 2, four fields each, to `<= 1e-12` |
| M4a-i | Period 8 is never oracle-optimal | **PASS** | `value(6,b) − value(8,b) = 1/125 + 6b/25 > 0` on `[0,1]`; checked on all 29 beliefs this host can present and on a 101-point grid |
| M4a-ii | `SEVERED` agreement is all-or-nothing | **PASS** | belief `= 1/2` for all 7 counts; `optimal_tail(1/2) = 4`; constant-period agreement `= 1` iff period `= 4`, else `0` |
| M4a-iii | The published BC zeros recompute | **PASS** | all 24 + 30 BC rows: the independent reference reproduces `minimum_tail_agreement`, `max_regret`, `oracle_root_match` and `root_actions` exactly; BC selected only periods `{2, 8}`; `SEVERED` agreement `0` in every row |
| M4a-iv | The recorded BC tail scores **are** the frozen 5-term model, far from the oracle | **PASS** | least-squares recovery from each row's own 224 recorded scores: residual `< 1.9e-7` (fp32); `max abs(beta − beta*) > 0.5` for every policy; the recovered argmax equals the recorded `tail_periods` at every one of the 56 (context, count) cells |
| M4b-i | FT checkpoints share one tail model (unit scale, real training) | **PASS** | ASSESS config: `FT-XF-BC` and `FT-XF-FLEX` produce 1 distinct tail state across their 2 checkpoints; `MT-XF-FLEX` produces 2 |
| M4b-ii | …and on the published rungs | **PASS** | for all 12 (arm, seed, fold) groups at each rung, `tail_periods`, `tail_scores` and `minimum_tail_agreement` are byte-identical across every checkpoint |

## 3. Defects found

**None.** No `file:line` defect is reported, because no measurement failed. The R01 published
records and documents are unchanged.

Two design facts were established that are *not* defects but do bear on how the R01 numbers
may be read; both are recorded here and are what motivates R02's per-arm rule:

1. `minimum_tail_agreement` is a **minimum over the eight contexts**
   (`experiments/candidates/ucope/competence_first_scout_r01/evaluation.py:123`), and four of
   those eight contexts are `SEVERED`, where the belief is `1/2` for every count. On those
   contexts the agreement can only be `0` or `1`. A recorded `0.000000` therefore carries much
   less information than a continuous score would: it says "this policy does not select period
   4 at belief 1/2", nothing more.
2. `exposure_line` reads **the whole `state_dict()`** for
   `parameter_displacement_l2` / `initialisation_scale_l2`
   (`scripts/run_ucope_exposure_ladder_rung1.py:395`) — for `FT-XF-FLEX` that is `beta` plus
   `residual.{0,2,4}.{weight,bias}`, 4,870 tail coordinates against BC's 5 — and reads **only
   `state_dict()["beta"]`** for `beta_displacement_l2`, `beta_initialisation_l2` and
   `beta_max_abs_coordinate_move` (`:400`, `:410`–`:412`). The R01 reading rule's `m` is the
   minimum of `beta_max_abs_coordinate_move` over **all 24 rows of both arms**, so it excludes
   FLEX's residual and lets whichever arm has the smaller beta motion decide the branch alone.

## 4. What the ladder's recorded competence observations do and do not mean

**Do mean.** `competence_pass`, `max_regret`, `minimum_tail_agreement` and `oracle_root_match`
as recorded at both rungs are correct measurements of the policies that were trained. The
predicate is not stuck at `False`: given exactly-optimal coefficients it returns `True` on both
arms, with `max_regret 0.0` and `minimum_tail_agreement 1.0`. `0/12 competent` at rung 1 and
`0/12` at rung 2 are statements about those learners on this host, at this criterion.

**Anomaly (a) explained.** `FT-XF-BC`'s `0.000000` is a property of the learned policies. Every
published BC tail model is the frozen 5-term Bellman function (recovered to fp32 residual from
its own recorded scores) with coefficients far from the exactly-representable optimum
`(0.31, 0.60, 1.35, -1.08, -0.891)`; its argmax over `K_eval = {2,4,6,8}` lands only on the
endpoints 2 and 8 at every belief the host presents. Period 8 is never optimal at any belief,
and period 4 — the unique optimum at belief `1/2` — is never selected, so the four `SEVERED`
contexts score exactly 0 and the minimum is exactly 0. The BC basis **can** represent the true
tail value exactly, so this is a learning outcome, not a representational or instrumentation
artefact.

**Anomaly (b) explained.** For every `FT-*` arm, `training.train_policy` completes the entire
tail loop before the first root update
(`experiments/candidates/ucope/competence_first_scout_r01/training.py:226`) and never touches
the tail module again during the root loop (`:232`–`:234`); checkpoints are taken only at root
milestones. The tail model at every checkpoint of one policy is therefore byte-identical, so
tail agreement — which depends only on the tail model — is necessarily constant across a
policy's checkpoints. This holds for both FT arms (it holds for BC too, at the value 0) and is
demonstrated at unit scale against the `MT-XF-FLEX` control, whose interleaved clock does
change the tail between checkpoints.

**Do not mean.** Nothing here makes `FT-XF-BC` competent, changes any published branch, or
licenses any claim beyond R01's stated ceiling. In particular a constant `minimum_tail_agreement`
across checkpoints is **not** evidence that the tail stopped learning within its own loop — the
instrument simply cannot see inside the tail loop, because no checkpoint is taken there. Any
question about tail-loop dynamics needs a different object with tail-side checkpoints.

## 5. Deviations

1. **The `1/2` level was substituted.** The card asked for true agreement levels
   `{0, 1/2, 1, intermediate}`. An exactly-`1/2` true agreement is unattainable on this frozen
   host: the seven count masses are binomial and no subset sums to `1/2`. The check proves that
   by exhaustive enumeration rather than asserting it, and substitutes the closest attainable
   recorded minimum, `0.520727`, together with `0.041453` and the exact `0` and `1` levels. The
   complementary per-context value `0.479273` (the same distance from `1/2` on the other side)
   is not attainable as a *minimum*, because a policy scoring it on a `LINKED` context
   necessarily scores `0` on the `SEVERED` contexts.
2. **The convexity hypothesis for anomaly (a) was wrong and was replaced before the run
   concluded.** A first draft asserted that BC's learned tail value is convex in `k` (which
   would force endpoint selection). The published second differences are negative
   (e.g. `−0.0563` at rung 1), so the learned surface is concave. The check now recovers each
   BC policy's actual coefficients from its own recorded scores and shows the argmax lands on
   an endpoint for a different, verified reason — the slope term is far from the optimum. This
   replacement was made in the check's code before the reported result; it is recorded here
   because a hypothesis stated in the card's §2 was falsified by the check itself.
3. Two rows of the check read the untracked published run directories (M3d, M4a-iii/iv, M4b-ii).
   They read only the fields `validate_policy_evaluation` and `validate_complete` already read,
   and they skip cleanly if those directories are absent.

## 6. Not verified

- Nothing is claimed about *why* the learners land where they do — objective, target package,
  conditioning, fold coupling and seed instability are all untouched by this object.
- The check does not evaluate the whitening discriminator's instrumentation; that object is
  held by the owner and was not read or run.
- The `MT-XF-FLEX` arm appears only as a sensitivity control at ASSESS scale; no claim is made
  about it.
- The check does not test the sampled-evaluation diagnostics, the host, the RNG contract, the
  checkpoint format or the resource telemetry; those are covered by the existing suites.
