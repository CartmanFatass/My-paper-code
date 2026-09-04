from tools.benchmarks import benchmark_variable_roster_low_step_transfer as benchmark


def test_low_step_host_transfer_benchmark_is_bounded_and_oracle_gated():
    result = benchmark.run_benchmark(
        repeats=3,
        iterations=1,
        rows=5,
        environments=2,
        device="cpu",
    )
    assert (
        result["schema"]
        == "hmasd.variable_roster_low_step_host_transfer_benchmark.v1"
    )
    assert result["bounded_workload"] is True
    assert result["oracle_equal"] is True
    assert result["legacy_median_seconds"] > 0.0
    assert result["packed_median_seconds"] > 0.0
    assert result["production_default"] == "legacy"
    assert result["promotion_allowed"] is False
