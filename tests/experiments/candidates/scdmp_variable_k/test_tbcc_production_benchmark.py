from __future__ import annotations

import torch

from tools.benchmarks import benchmark_scdmp_tbcc_r02_production_preactivity as benchmark


def _measurement(wall: float = 1.0, rss: int = 1024) -> dict[str, object]:
    return {
        "wall_seconds": wall,
        "cpu_seconds": wall,
        "peak_rss_bytes": rss,
        "rss_bytes": rss,
        "io_read_bytes": 0,
        "io_write_bytes": 0,
        "cpu_utilization_fraction": 1.0,
        "telemetry_available": True,
        "telemetry_error": None,
    }


def test_exact_chain_and_registered_full_panel_counts() -> None:
    assert benchmark.CHAIN_COVERAGE == (
        "environment",
        "loader",
        "batch",
        "forward_backward",
        "rollout",
        "evaluation",
        "io",
        "resume",
    )
    assert benchmark.PANEL_COUNTS["complete_episodes_or_rollouts"] == 343_296
    assert benchmark.PANEL_COUNTS["complete_allocated_slots"] == 124_959_744
    assert benchmark.PANEL_COUNTS["complete_max_policy_queries"] == 15_829_632
    assert benchmark.PANEL_COUNTS["complete_adamw_steps"] == 129_024
    assert benchmark.PANEL_COUNTS["complete_final_checkpoints"] == 96


def test_abi2_primitive_reward_trace_matches_independent_test_oracle() -> None:
    row = benchmark._primitive_reward_trace()
    assert row["abi_version"] == 2
    assert row["capacity"] == 13
    assert row["count_equals_ticks_advanced"] is True
    assert row["inactive_tail_canonical_zero"] is True
    assert row["oracle_native_reward_equal"] is True
    assert row["maximum_absolute_difference"] <= 2e-14
    assert row["reward_values_exposed"] is False


def test_checkpoint_frontier_gate_result_shapes_are_atomic_and_cold_resumable(tmp_path) -> None:
    payloads = {
        arm: {
            "schema": "TEST_ONLY_TBCC_CHECKPOINT_SHAPE_V1",
            "test_only": True,
            "arm": arm,
            "completed_updates": 0,
            "optimizer": {"step_index": 0},
            "tensor": torch.arange(32, dtype=torch.float32),
        }
        for arm in ("FOUNDATION", "TREAT", "FREE", "SET")
    }
    row = benchmark._io_and_mocked_runner(tmp_path, payloads)
    assert row["mocked_complete_service_calls"] == 99
    assert row["branch_values_exposed"] is False
    assert row["checkpoint_payload_values_exposed"] is False
    assert row["exact_update_generation_count"] == 10_752
    assert row["exact_initial_frontier_count"] == 96
    assert set(row["representative_arm_io"]) == {"FOUNDATION", "TREAT", "FREE", "SET"}
    assert row["generation_storage"]["checkpoint_receipt_update_frontier_bytes_exact"] > 0
    assert row["atomic_create_only"] is True
    assert row["same_coordinate_resume"] is True
    assert row["cold_resume"]["mocked_services_reexecuted"] is False


def test_projection_uses_exact_counts_and_measured_conservative_speedup() -> None:
    widths = [
        {
            "native_transitions_per_second": 1_000_000.0,
            "fixture_oracle": [_measurement()],
            "optimized_native": [_measurement()],
        }
        for _ in benchmark.WIDTHS
    ]
    forwards = [
        {"controllers": {"FOUNDATION": {"batched_rows_per_second": 100_000.0}}}
    ]
    kernels = [
        {"adamw_steps": 12, "measurement": _measurement(0.12)},
        {"adamw_steps": 12, "measurement": _measurement(0.10)},
    ]
    service = {
        "training": {
            "primitive_transitions": 100,
            "policy_rows": 10,
            "adamw_steps": 12,
            "measurement": _measurement(0.01),
        },
        "evaluation_adapters": [
            {
                "primitive_transitions": 100,
                "active_policy_rows": 10,
                "measurement": _measurement(0.01),
            },
            {
                "primitive_transitions": 100,
                "active_policy_rows": 10,
                "measurement": _measurement(0.01),
            },
        ],
        "opportunity": {
            "primitive_transitions": 100,
            "policy_rows": 10,
            "full_stage_pair_count": 768,
            "measurement": _measurement(0.01),
        },
        "serial_analyzer_measurement": _measurement(0.01),
    }
    preflight = {
        "direct_measurement": _measurement(0.01),
        "foreground_cli_measurement": _measurement(0.01),
    }
    arm_storage = {
        arm: {"update_generation_count": 3840 if arm == "FOUNDATION" else 2304, "slot_count": 24}
        for arm in ("FOUNDATION", "TREAT", "FREE", "SET")
    }
    arm_io = {
        arm: {
            "checkpoint_write_measurement": _measurement(0.01),
            "receipt_write_measurement": _measurement(0.01),
            "frontier_chain_write_measurement": _measurement(0.01),
            "full_resume_measurement": _measurement(0.01),
        }
        for arm in arm_storage
    }
    io_row = {
        "mocked_complete_branch_measurement": _measurement(0.01),
        "same_process_resume_measurement": _measurement(0.01),
        "generation_storage": {
            "arms": arm_storage,
            "checkpoint_receipt_update_frontier_bytes_exact": 3_000_000,
        },
        "representative_arm_io": arm_io,
        "final_gate_result_bytes": 4096,
        "installed_manifest_preactivity_bytes": 8192,
        "exact_update_generation_count": 10_752,
        "exact_initial_frontier_count": 96,
    }
    projection = benchmark._projection(
        widths,
        forwards,
        kernels,
        service,
        preflight,
        io_row,
        {"measured_effective_speedup": 2.5},
    )
    assert projection["exact_counts"] == benchmark.PANEL_COUNTS
    assert projection["measured_effective_speedup"] == 2.5
    assert projection["kernel_double_counting"] is False
    assert projection["production_runner_formally_executed"] is False
    assert projection["serial_components_divided_by_thread_speedup"] is False
    assert projection["exact_update_generation_count"] == 10_752
    assert projection["projected_storage_bytes"] == 3_012_288
    assert projection["resource_class_remains_credible"] is True
