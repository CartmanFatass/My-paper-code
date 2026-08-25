from __future__ import annotations

from types import SimpleNamespace

from tools.benchmarks import benchmark_uav_cpp_backend as benchmark


def test_geometry_matrix_covers_required_batch_widths(monkeypatch) -> None:
    monkeypatch.setattr(benchmark, "load_uav_cpp_backend", lambda: SimpleNamespace())
    monkeypatch.setattr(
        benchmark,
        "run_benchmark",
        lambda *, batch_size, repeats, iterations, seed: {
            "workload": {"batch": batch_size},
            "repeats": repeats,
            "iterations": iterations,
            "seed": seed,
            "accepted": True,
        },
    )
    result = benchmark.run_geometry_batch_matrix(
        batch_sizes=(1, 8, 32), repeats=5, iterations=3, seed=7
    )
    assert result["schema"] == "hmasd.uav_cpp_geometry_batch_matrix.v1"
    assert result["batch_sizes"] == [1, 8, 32]
    assert result["native_scope"] == "geometry_only_not_full_reset_step"
    assert result["steady_measurement_excludes_process_cold_preflight"] is True
    assert [row["workload"]["batch"] for row in result["results"]] == [1, 8, 32]
    assert result["accepted"] is True


def test_radio_matrix_covers_both_consumer_interference_laws(monkeypatch) -> None:
    monkeypatch.setattr(benchmark, "load_uav_cpp_backend", lambda: SimpleNamespace())
    monkeypatch.setattr(
        benchmark,
        "_radio_kwargs",
        lambda _seed, width, excluded: {"width": width, "excluded": excluded},
    )
    result_type = SimpleNamespace(
        access_sinr=0,
        air_sinr=0,
        uav_to_base_sinr=0,
        base_to_uav_sinr=0,
    )
    monkeypatch.setattr(
        benchmark, "compute_radio_reference_batch", lambda **_kwargs: result_type
    )
    monkeypatch.setattr(benchmark, "compute_radio_batch", lambda **_kwargs: result_type)
    monkeypatch.setattr(benchmark, "_radio_equal", lambda _left, _right: True)
    result = benchmark.run_radio_batch_matrix(
        batch_sizes=(1, 8, 32), repeats=1, iterations=1, seed=7
    )
    assert result["batch_sizes"] == [1, 8, 32]
    assert [(row["consumer_law"], row["batch"]) for row in result["results"]] == [
        ("routed_energy", 1),
        ("routed_energy", 8),
        ("routed_energy", 32),
        ("forced", 1),
        ("forced", 8),
        ("forced", 32),
    ]


def test_complete_batch_contract_exposes_nonbatched_environment_gap(monkeypatch) -> None:
    monkeypatch.setattr(
        benchmark,
        "_run_complete_reset_step_batch",
        lambda *, workload, batch_size, repeats, seed: {
            "workload": workload,
            "batch": batch_size,
            "samples": repeats,
            "seed": seed,
            "speedup": 1.1,
            "payload_internal_rng_exact": True,
        },
    )
    result = benchmark.run_complete_reset_step_batch_benchmark(
        batch_sizes=(1, 8, 32), repeats=3, seed=7
    )
    assert result["full_environment_batched_cpp"] is False
    assert result["native_numeric_batch_width_per_consumer"] == 1
    assert result["consumer_batch_execution"] == "python_sequential_environment_instances"
    assert len(result["results"]) == 9
    assert result["accepted"] is True
