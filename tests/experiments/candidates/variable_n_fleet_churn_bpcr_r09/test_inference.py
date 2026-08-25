from fractions import Fraction

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.inference import (
    complementary_subset_interval,
    inference_contract,
    studentized_tail_count,
)


def test_frozen_inference_counts_and_coverage() -> None:
    contract = inference_contract()
    assert contract["all_coordinate_partition_visits"] == 2_949_120
    assert contract["all_subset_mean_constructions"] == 5_898_060
    assert contract["exact_rational_comparison_ceiling"] == 79_626_150
    assert contract["joint_coverage_lower_bound"] == Fraction(31180, 32768)


def test_constant_rows_have_closed_singleton_interval_and_inclusive_tail() -> None:
    values = (0.125,) * 16
    interval = complementary_subset_interval(values, 12)
    assert interval.lower == interval.upper == Fraction(1, 8)
    assert interval.q == 28
    assert studentized_tail_count(values, Fraction(1, 8)) == 65536
