import numpy as np
import pytest

from scripts.analyze_r38_cts_access import (
    decide_result,
    paired_bootstrap_ci,
    require_nonnegative_integer,
    validate_policy_rows,
    validate_zero_count_fields,
)


def test_paired_bootstrap_uses_episode_differences():
    mappo = np.ones(256, dtype=np.float64)
    random = np.zeros(256, dtype=np.float64)
    estimate, lower, upper = paired_bootstrap_ci(
        mappo, random, repetitions=10_000, seed=59_031
    )
    assert (estimate, lower, upper) == (1.0, 1.0, 1.0)


def test_decision_checks_implementation_before_science():
    assert decide_result(False, True, True) == "INVALID_R38_IMPLEMENTATION"
    assert decide_result(True, False, True) == "FAIL_R38_CTS_ACCESS"
    assert decide_result(True, True, False) == "FAIL_R38_CTS_ACCESS"
    assert decide_result(True, True, True) == "PASS_R38_CTS_ACCESS"


@pytest.mark.parametrize("value", (-1.0, 0.5, np.nan, np.inf, "1.5"))
def test_nonnegative_integer_rejects_fractional_negative_and_nonfinite(value):
    with pytest.raises(ValueError, match="finite nonnegative integer"):
        require_nonnegative_integer(value, field="evidence")


def test_zero_count_validator_rejects_each_field_without_cancellation():
    rows = [
        {"r30_high_rows": 1.0, "r30_decision_rows": 0.0, "process_segments": 0.0},
        {"r30_high_rows": -1.0, "r30_decision_rows": 0.5, "process_segments": 2.0},
    ]
    reasons = []
    totals = validate_zero_count_fields(
        rows,
        ("r30_high_rows", "r30_decision_rows", "process_segments"),
        label="training updates",
        reasons=reasons,
    )
    assert totals == {
        "r30_high_rows": 1,
        "r30_decision_rows": 0,
        "process_segments": 2,
    }
    assert any("r30_high_rows=1 != 0" in reason for reason in reasons)
    assert any("r30_high_rows" in reason and "finite nonnegative integer" in reason for reason in reasons)
    assert any("r30_decision_rows" in reason and "finite nonnegative integer" in reason for reason in reasons)
    assert any("process_segments=2 != 0" in reason for reason in reasons)


def test_policy_validation_rejects_fractional_success_length():
    row = {
        "episode": 0.0,
        "reset_seed": 139_031.0,
        "reward": 1.0,
        "length": 3.5,
        "terminated_flag": 1.0,
        "truncated_flag": 0.0,
        "r38_short_duty_complete": 1.0,
        "r38_long_duty_complete": 1.0,
        "r38_full_cycle_success": 1.0,
        "r38_anchor_streak_max": 40.0,
        "r38_shuttle_stage_max": 4.0,
        "r38_sparse_reward": 1.0,
    }
    reasons = []

    audit = validate_policy_rows(
        [row], tuple(row), "MAPPO evaluation", reasons, mappo=False
    )

    assert audit["terminal_semantics_valid"] is False
    assert any(
        "length must be a finite nonnegative integer" in reason
        for reason in reasons
    )
