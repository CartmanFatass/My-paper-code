import numpy as np

from scripts.analyze_r38_cts_access import decide_result, paired_bootstrap_ci


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
