# R26-G1a Individual-Skill Behavior Screen

- Checkpoint: `r29_t10_probe_only_seed29031_final`
- Gate: **PASS**
- Rows: 6086

## Split

- Train rows: 3774; Train resets: `[1, 2, 3, 4, 9, 10, 11, 12, 13, 14, 15, 16, 19, 22, 26, 28, 30, 31, 33, 34, 35, 36, 37, 38, 40, 41, 43, 44, 46, 47, 48, 50, 51, 52, 53, 56, 57, 59, 60, 61]`
- Validation rows: 1176; Validation resets: `[6, 20, 21, 23, 24, 27, 29, 42, 45, 55, 62, 63]`
- Test rows: 1136; Test resets: `[0, 5, 7, 8, 17, 18, 25, 32, 39, 49, 54, 58]`
- Valid-pre comparison rows: train=3534, validation=1104, test=1064

## Baselines

- Label counts: `[1592, 1400, 1436, 1658]`
- Normalized label entropy: 0.998223
- Maximum label fraction: 0.272429
- Majority accuracy: 0.272887

## Thresholds

| threshold | pre-registered value |
| --- | ---: |
| normalized_label_entropy_min | `0.8` |
| accuracy_gain_min | `0.05` |
| matched_null_difference | `> 0.0` |
| matched_null_bootstrap_lower | `> 0.0` |
| overfit_train_minus_test_accuracy | `> 0.20` |
| early_stop_min_delta | `0.0001` |

## Primary differences

| metric | value | Bootstrap 95% CI |
| --- | ---: | ---: |
| full_minus_prior_accuracy | 0.073063 | [0.044444, 0.108793] |
| behavior_post_minus_pre_accuracy | 0.061090 | [0.028264, 0.094050] |

## Matched nulls

| null | real-minus-null accuracy | Bootstrap 95% CI | unchanged fraction |
| --- | ---: | ---: | ---: |
| agent_matched | 0.098592 | [0.068162, 0.133964] | 0.251561 |
| duration_matched | 0.106514 | [0.072137, 0.142977] | 0.257312 |
| agent_duration_matched | 0.108275 | [0.062886, 0.154469] | 0.261748 |

## Variant scores

| variant | kind | unchanged | best step | test accuracy | macro-F1 | cross-entropy | train-test gap |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| real | behavior | 1.000000 | 25 | 0.352113 | 0.348151 | 1.347057 | 0.094893 |
| real | prior | 1.000000 | 5 | 0.279930 | 0.180022 | 1.382039 | 0.027172 |
| real | full | 1.000000 | 25 | 0.352993 | 0.338483 | 1.354317 | 0.082354 |
| shuffled | behavior | 0.253697 | 5 | 0.257042 | 0.147325 | 1.388002 | 0.043435 |
| fake_marginal | behavior | 0.246467 | 10 | 0.254401 | 0.164859 | 1.391557 | 0.060119 |
| agent_matched | behavior | 0.251561 | 5 | 0.253521 | 0.125927 | 1.388396 | 0.041391 |
| duration_matched | behavior | 0.257312 | 5 | 0.245599 | 0.118405 | 1.390698 | 0.053024 |
| agent_duration_matched | behavior | 0.261748 | 5 | 0.243838 | 0.117837 | 1.389791 | 0.047365 |
| pre_only | behavior | 1.000000 | 5 | 0.278195 | 0.211780 | 1.384538 | 0.029954 |
| action_only | behavior | 1.000000 | 35 | 0.380282 | 0.370143 | 1.313018 | 0.015850 |
| effect_only | behavior | 1.000000 | 5 | 0.278169 | 0.172713 | 1.383911 | 0.022573 |
| context_only | prior | 1.000000 | 5 | 0.279930 | 0.180022 | 1.382039 | 0.027172 |

## Gate reasons

- all five pre-registered checkpoint gates pass
