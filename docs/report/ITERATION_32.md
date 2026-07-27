# 第32轮：G42 scale-matched raw-sum formal result

## 运行边界

- assignment: `CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_FORMAL_ITERATION_32`
- environment: toy env (`ContinuousRosterToyBatch_CPU_CPP`), not UAV
- execution source commit: `a6c3c2971ee74e76a453995c3a7c12627bb8f02c`
- aligned source commit: `6b8ea82d8fdbc76c14a414ff2b042a126f945dfb`
- alignment stage: `309858dca06af66f13857f94773bcef37527d821`
- formal run: `logs/formal_continuous_roster_native_six_g31_direction_balance_attribution_g42_cpu_20260727_a6c3c29_r1`
- backend: CPU C++ toy backend required; Python fallback false

## 机械运行事实

Train, evaluate and analyze all exited zero. The three required manifests report
`status=COMPLETE`, `formal=true`, and `operational_valid=true` with no operational
errors. The frozen inventory is 3 replicates, 2 arms, 72 evaluation cells,
230400 training transitions, 165888 evaluation transitions, 396288 total real
transitions, 1200 optimizer steps, 48 episodes per cell and 10000 bootstrap
resamples. `K_search=0` and hypothetical transitions are zero; checkpoint
selection is final-only.

## External Pro 原样裁决字段

The exact raw response and mechanical intake are archived at:

- [21_PRO_OPEN_RAW.md](../external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_formal_result_review_a6c3c29/21_PRO_OPEN_RAW.md)
- [50_MECHANICAL_INTAKE_RECORD.md](../external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_formal_result_review_a6c3c29/50_MECHANICAL_INTAKE_RECORD.md)

The response explicitly records:

```text
formal_disposition=SCALE_MATCHED_NO_DIRECTION_BALANCE_SUFFICIENT_G42
scientific_disposition=SUPPORTED_RETAINED_SCALE_MATCHED_RAW_SUM_POST_ANCHOR_G31_COMPOSITION_G42
valid_result_disposition=CONTINUE
conclusion_bearing_iterations_consumed=32
iterations_remaining=5
next_action=CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_DESIGN_ASSERTION_AUDIT
```

This report records the External Pro fields mechanically; the next action is a
zero-compute G43 design assertion audit. It does not broaden the claim beyond
the stated G42 boundary or reactivate G33/UAV work.
