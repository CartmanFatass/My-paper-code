# Iteration 33: G43 DB-norm schedule formal result

## Execution boundary

- assignment: `CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_FORMAL_ITERATION_33`
- environment: toy env (`ContinuousRosterToyBatch_CPU_CPP`), not UAV
- execution source commit: `bb42840ab1479abde7f3485006bfbbee981a73cf`
- aligned source commit: `45e16f71d171228135b6444bee1678b157d79abe`
- alignment stage: `889c0b4e3d68a8d74f811ae9ecfe7b5213abfa76`
- formal run: `logs/formal_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_cpu_20260727_bb42840_r1`
- backend: CPU C++ toy backend required; Python fallback false

## Mechanical runtime facts

Train, evaluate and analyze all exited zero. The three required manifests report
`status=COMPLETE`, `formal=true`, and `operational_valid=true`. The frozen
inventory is 3 replicates, 2 arms, 72 evaluation cells, 230400 training
transitions, 165888 evaluation transitions, 396288 total real transitions,
1200 optimizer steps, 48 episodes per cell and 10000 bootstrap resamples.
`K_search=0` and hypothetical transitions are zero; checkpoint selection is
final-only.

## External Pro disposition fields

The exact raw response and mechanical intake are archived at:

- [21_PRO_OPEN_RAW.md](../external-review/rounds/20260727_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_formal_result_review/21_PRO_OPEN_RAW.md)
- [50_MECHANICAL_INTAKE_RECORD.md](../external-review/rounds/20260727_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_formal_result_review/50_MECHANICAL_INTAKE_RECORD.md)

The response explicitly records:

```text
formal_disposition=EQUAL_MEAN_RAW_SUM_SUFFICIENT_G43
scientific_disposition=SUPPORTED_RETAINED_FIXED_EQUAL_MEAN_NO_SHADOW_POST_ANCHOR_G31_COMPOSITION_G43
valid_result_disposition=CONTINUE
conclusion_bearing_iterations_consumed=33
iterations_remaining=4
next_action=CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_DESIGN_ASSERTION_AUDIT
```

The reported comparison is mechanically preserved as
`DBNORM-minus-MEAN pooled CI95=[-0.01122548,-0.00215076,0.00407002]`, with
capacity-6/8/12 UCBs `0.00359780|0.00473064|0.00379189`. This report records
the External Pro fields without adding an operator interpretation, broadening
the claim, or authorizing compute for G44.
