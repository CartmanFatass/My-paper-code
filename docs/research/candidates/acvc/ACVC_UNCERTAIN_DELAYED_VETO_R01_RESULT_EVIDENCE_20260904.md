# ACVC uncertain/delayed veto R01 — result evidence

- Direction: `acvc`
- Object: `ACVC-B-EXPLORE-UNCERTAIN-DELAYED-VETO-R01`
- Evidence class and claim ceiling: **B/EXPLORE**; one-seed mechanism signal or
  counterexample on the frozen constructed host only
- Science card:
  [`ACVC_UNCERTAIN_DELAYED_VETO_R01_SCIENCE_CARD_20260904.md`](ACVC_UNCERTAIN_DELAYED_VETO_R01_SCIENCE_CARD_20260904.md)
- Complete machine result:
  [`ACVC_UNCERTAIN_DELAYED_VETO_R01_RESULT_20260904.json`](ACVC_UNCERTAIN_DELAYED_VETO_R01_RESULT_20260904.json)
- Launch commit: `3df33befd84880935cba9ddb7b1f3d3b3650d4f0`
- Base seed: `11`
- Result: **`B2-C / FIXED_RULE_CONTAINS`**

## E0 execution and integrity record

The result-bearing invocation was launched once, after the implementation and cost projection
were committed. Immediately before the invocation,
`scripts/hmasd_resource_preflight.py admit-memory` recorded both physical and effective available
memory as `8,236,081,152` bytes against a `4,294,967,296`-byte floor; both checks passed. The
admission receipt was assessed at `2026-09-04T11:31:16.405943Z`.

The independent process was accepted at `2026-09-04T11:31:16.498Z` as PID `20580`, terminated
normally with exit code `0`, and wrote one `summary.json`. Standard error was empty. Its logical
argument vector was:

```text
scripts/run_acvc_uncertain_delayed_veto_r01.py run
--output-root temp/directions/acvc/exp/uncertain_delayed_veto_r01_20260904
--admission-receipt temp/directions/acvc/exp/uncertain_delayed_veto_r01_20260904_admission.json
--project-cost temp/directions/acvc/exp/uncertain_delayed_veto_r01_20260904_project_cost.json
--seed 11
```

The machine result reports `complete=true`, `result_bearing=true`, `toy=false`, and
`technical_only=false`. Required counts are exact: `128` optimizer updates, `8,192` training
episodes and `98,304` training transitions per learned arm; `4,096` fresh evaluation episodes and
`49,152` evaluation transitions per arm; model-selection exposure is zero. RNG namespace seeds,
ownership, all paired episode returns, regime and field subgroups, action rates, safety and clean
loss, exposure, launch SHA, and resource fields are retained in the linked JSON.

## Cost, resources, and learner exposure

The result-blind projection admitted every arm under its own cap. Projected learned-arm times were
`6.061502 s` for `ACVC-HISTORY-GATE` and `8.030863 s` for `RAW-GRU`, each below `600 s`; the
largest fixed-arm projection was `0.095453 s`, below `120 s`. Actual total arm times were
`5.130695 s`, `2.800952 s`, and `0.015627–0.018844 s` for the fixed arms. Every arm records
`wall_cap_enforced=true`. Whole-process wall time was `8.113134 s`, and measured peak RSS was
`311,377,920` bytes.

Both learners moved materially and had a gradient-bearing update at all `128` updates:

| arm | parameters | initial L2 | displacement L2 | displacement / initial | action entropy |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ACVC-HISTORY-GATE` | 92 | 0.452148 | 4.779539 | 10.570736 | 0.250218 |
| `RAW-GRU` | 516 | 1.090668 | 8.965516 | 8.220204 | 0.270467 |

The frozen exposure admission ratios were `5.661861` and `2.347185`, respectively, above the
required `0.5`. There is therefore no zero-exposure, missing-count, nonfinite, resource, or wall-cap
quarantine condition.

## Direct observations

| arm | mean return | SD | unsafe execute rate | clean opportunity loss | execute / probe / veto |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ACVC-HISTORY-GATE` | 2.528271 | 1.375396 | 0.000000 | 0.600000 | 0.000000 / 1.000000 / 0.000000 |
| `RAW-GRU` | 2.528271 | 1.375396 | 0.000000 | 0.600000 | 0.000000 / 1.000000 / 0.000000 |
| `DET-CF` | 3.392822 | 3.217103 | 0.154433 | 0.388516 | 0.314982 / 0.685018 / 0.000000 |
| `AUTH-PROBE` | 2.633936 | 5.046369 | 0.473401 | 0.213276 | 0.612142 / 0.387858 / 0.000000 |
| `ALWAYS-PROBE` | 2.528271 | 1.375396 | 0.000000 | 0.600000 | 0.000000 / 1.000000 / 0.000000 |
| `ALWAYS-EXECUTE` | 0.641357 | 6.876979 | 1.000000 | 0.000000 | 1.000000 / 0.000000 / 0.000000 |
| `ALWAYS-VETO` | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0.000000 / 0.000000 / 1.000000 |

The fixed decision comparator chosen by the frozen tie rule was `DET-CF`. Both learned arms had
the same return on every paired evaluation episode and exactly matched the reporting-only
`ALWAYS-PROBE` policy. Their calibrated/uninformative regime means were also identical:
`2.518967 / 2.537272`. The structured history state was populated, but neither learner's greedy
action changed with it.

The primary effects were:

```text
Delta_A  = -0.8645507692, paired descriptive 95% interval [-0.9379313332, -0.7911702051]
Delta_G  = -0.8645507692, paired descriptive 95% interval [-0.9379313332, -0.7911702051]
Delta_AG =  0.0000000000, paired descriptive 95% interval [0, 0]
```

Neither learned arm was harm-compatible with `DET-CF`: each reduced unsafe execution but exceeded
the fixed arm's clean-opportunity loss by about `0.211484`, above the frozen `0.05` allowance.

## Frozen rule application

The rule was applied in the registered order. Branch A fails because `Delta_A < 0.25`, the
treatment is not harm-compatible, and it has no advantage over the recurrent comparator. Branch B
fails because `Delta_G < 0.25` and the recurrent comparator is not harm-compatible. Branch C then
holds because neither learned arm exceeds `DET-CF` by `0.10` while harm-compatible. The machine and
DM readings therefore agree on **`B2-C / FIXED_RULE_CONTAINS`**.

## Bounded reading and alternatives

Direct observation supports the following narrow result: on this host, seed, A2C budget, and
initialization, both a structured calibration-history gate and the stronger same-information GRU
converged to indiscriminate probing and were contained by the competent memoryless
confidence/freshness rule. This contradicts the DM prediction of `B2-A`.

The strongest support is the exact paired equality between both learned arms and `ALWAYS-PROBE`,
the `0.864551` return deficit to `DET-CF`, and complete exposure/count records. The strongest live
contradiction is learner competence: this was one seed and both different representations reached
the same conservative local policy despite substantial parameter movement. The result therefore
does not establish that revealed history has no decision value, that no other optimizer can learn
it, or that ACVC is direction-wide negative. It closes at most this host/budget rung. It is not a
technical failure and creates no justification for a result-informed rerun.

## Engineering conformance and deviations

The implementation stayed on the card's isolated research-code surfaces. The final focused suite
passed `8` tests in `14.91 s` after the committed wall-cap correction; independent review found no
material issue. Non-test research code was approximately `856` lines and the runner `69` lines,
within the section 5 budgets. The object requested no engineering-scope section 4 machinery, and
none was added. No scientific, numerical, RNG, checkpoint, side-effect, launch, or result-rule
deviation was observed.

