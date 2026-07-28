# D7.S normalizer autopsy

This script analyzes the SCALAR quantities recorded by the executed R3 code, conditional on the correctness of that execution path. It is not itself a second validation of the environment trajectories.

Input artifact: `logs/d7s_audit_2_30289161086/pooled/d7_s_event_aligned.json` (sha256 `b087e67cfb799000...`)
Bootstrap: iters=10000 seed=2026072601 quick_dev_run=False

## Sentinel (Modification 2)

| condition | ok | detail |
|---|---|---|
| artifact_hash | True | matches frozen reference |
| contract_and_procedure | True | contract_id='D7_S_EVENT_ALIGNED_SOURCE_AUDIT' (expected 'D7_S_EVENT_ALIGNED_SOURCE_AUDIT'), procedure_version='d7s_event_aligned_v1' (expected 'd7s_event_aligned_v1') |
| topology_seeds | True | expected [20260726, 20260727, 20260728, 20260729, 20260730, 20260731, 20260732, 20260733], got [20260726, 20260727, 20260728, 20260729, 20260730, 20260731, 20260732, 20260733] |
| smoke_false | True | smoke=False |
| topology_units_shape | True | all four collections present on every topology |
| bounds_reproduction | True | all six bounds reproduced within tolerance |

## Section A -- standalone distributions

| quantity | point | 5th pct | 95th pct | min | max | +/-/0 |
|---|---|---|---|---|---|---|
| artifact-derived B_stable | 0.180139 | -0.077367 | 0.416071 | -0.495793 | 0.534832 | 5/1/2 |
| artifact-derived B_flex | 4.288854 | -8.648833 | 14.102587 | -17.147505 | 19.027850 | 6/2/0 |
| artifact-derived U*_stable | 1.254074 | -2.203652 | 7.186347 | -5.205364 | 14.042137 | 4/4/0 |
| artifact-derived U*_flex | -4.122402 | -13.827640 | 3.371472 | -30.069646 | 7.395372 | 3/5/0 |

## Evidence matrix

| explanation | verdict |
|---|---|
| N1_signed_normalizer_failure | compatible |
| N2_opposite_source_direction | not resolved |
| N3_component_cancellation | UNDISCRIMINATED_FROM_STORED_ARTIFACT |
| N4_topology_heterogeneity | material |
| N5_comparator_scale_mismatch | raised |
| selection_instability | moderate |

Do not force exactly one explanation to win (Modification 4).

## R4 recommendations (non-binding, Modification 6)

- a normalizer scale better matched to the focal one-Delta intervention (N5 raised)
- stratify or expand by topology before re-attempting a pooled normalizer (N4 material)

The final R4 freeze or carrier retirement remains a scientific disposition at the next review boundary; this script does not decide it.
