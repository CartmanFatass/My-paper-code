# R26-G1a Individual-Skill Behavior Screen

- Checkpoint: `r29_t10_real_reward_seed29031_final`
- Gate: **MIXED**
- Rows: 6103

## Split

- Train rows: 3760; Train resets: `[1, 2, 3, 4, 9, 10, 11, 12, 13, 14, 15, 16, 19, 22, 26, 28, 30, 31, 33, 34, 35, 36, 37, 38, 40, 41, 43, 44, 46, 47, 48, 50, 51, 52, 53, 56, 57, 59, 60, 61]`
- Validation rows: 1206; Validation resets: `[6, 20, 21, 23, 24, 27, 29, 42, 45, 55, 62, 63]`
- Test rows: 1137; Test resets: `[0, 5, 7, 8, 17, 18, 25, 32, 39, 49, 54, 58]`
- Valid-pre comparison rows: train=3520, validation=1134, test=1065

## Baselines

- Label counts: `[1696, 1400, 1438, 1569]`
- Normalized label entropy: 0.997911
- Maximum label fraction: 0.277896
- Majority accuracy: 0.259455

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
| full_minus_prior_accuracy | 0.014952 | [-0.003446, 0.034855] |
| behavior_post_minus_pre_accuracy | -0.002817 | [-0.010701, 0.005320] |

## Matched nulls

| null | real-minus-null accuracy | Bootstrap 95% CI | unchanged fraction |
| --- | ---: | ---: | ---: |
| agent_matched | 0.023747 | [-0.002807, 0.050046] | 0.250369 |
| duration_matched | 0.017590 | [-0.006088, 0.038390] | 0.249222 |
| agent_duration_matched | 0.015831 | [-0.012965, 0.043405] | 0.259708 |

## Variant scores

| variant | kind | unchanged | best step | test accuracy | macro-F1 | cross-entropy | train-test gap |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| real | behavior | 1.000000 | 5 | 0.273527 | 0.207376 | 1.375844 | 0.053335 |
| real | prior | 1.000000 | 10 | 0.288478 | 0.206050 | 1.387255 | 0.052745 |
| real | full | 1.000000 | 10 | 0.303430 | 0.268100 | 1.370312 | 0.043644 |
| shuffled | behavior | 0.245945 | 5 | 0.283201 | 0.178754 | 1.388919 | -0.001818 |
| fake_marginal | behavior | 0.252499 | 5 | 0.248901 | 0.160247 | 1.388730 | 0.027695 |
| agent_matched | behavior | 0.250369 | 5 | 0.249780 | 0.150112 | 1.389324 | 0.040379 |
| duration_matched | behavior | 0.249222 | 5 | 0.255937 | 0.128451 | 1.388972 | 0.018531 |
| agent_duration_matched | behavior | 0.259708 | 5 | 0.257696 | 0.168569 | 1.388789 | 0.035123 |
| pre_only | behavior | 1.000000 | 5 | 0.281690 | 0.181400 | 1.386400 | 0.030242 |
| action_only | behavior | 1.000000 | 25 | 0.312225 | 0.298924 | 1.349566 | 0.052403 |
| effect_only | behavior | 1.000000 | 5 | 0.264732 | 0.176425 | 1.387076 | 0.047502 |
| context_only | prior | 1.000000 | 10 | 0.288478 | 0.206050 | 1.387255 | 0.052745 |

## Gate reasons

- full-minus-prior accuracy 0.014952 is below 0.05
- post-minus-pre accuracy -0.002817 is below 0.05
- strongest matched-null bootstrap lower bound -0.012965 is not above zero
