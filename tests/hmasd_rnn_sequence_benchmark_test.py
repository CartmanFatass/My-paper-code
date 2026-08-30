import random

import numpy as np
import pytest
import torch

from tools.benchmarks import benchmark_rnn_sequence_backend as benchmark


def _rng_snapshot():
    return (
        random.getstate(),
        np.random.get_state(),
        torch.get_rng_state().clone(),
    )


def _rng_equal(before, after):
    return (
        before[0] == after[0]
        and before[1][0] == after[1][0]
        and np.array_equal(before[1][1], after[1][1])
        and before[1][2:] == after[1][2:]
        and torch.equal(before[2], after[2])
    )


def test_rnn_sequence_backend_benchmark_is_equivalence_gated_and_rng_preserving():
    before = _rng_snapshot()
    result = benchmark.run_benchmark(
        repeats=31,
        iterations=1,
        timesteps=3,
        batch_size=2,
        input_dim=3,
        hidden_size=4,
        device="cpu",
    )
    assert _rng_equal(before, _rng_snapshot())
    assert result["schema"] == "hmasd.rnn_sequence_backend_benchmark.v1"
    assert result["bounded_workload"] is True
    assert result["numeric_equivalent"] is True
    assert result["numeric_mismatches"] == []
    assert result["rng_preserved"] is True
    assert result["current_production_default"] == "step_reference"
    assert result["production_default_if_gate_fails"] == "step_reference"
    assert result["config"]["repeats"] == 31
    assert result["step_reference_median_seconds"] > 0.0
    assert result["segmented_median_seconds"] > 0.0
    assert len(result["config_fingerprint"]) == 64
    assert len(result["machine_fingerprint"]["sha256"]) == 64
    assert len(result["source_fingerprint"]["sha256"]) == 64


def test_rnn_sequence_backend_benchmark_requires_odd_31_or_more_repeats():
    with pytest.raises(ValueError, match="odd repeats"):
        benchmark.run_benchmark(repeats=30)
    with pytest.raises(ValueError, match="odd repeats"):
        benchmark.run_benchmark(repeats=32)
