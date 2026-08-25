from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest

from experiments.candidates.metric_ground_transport_allocation import resource_estimate as estimate


def _fabricated_measurements(
    *, wall: list[float] | None = None, cpu: list[float] | None = None
) -> dict[str, object]:
    wall_observations = [0.001, 0.002, 0.003] if wall is None else wall
    cpu_observations = [0.0005, 0.001, 0.0015] if cpu is None else cpu
    timing_units = {
        name: {
            "wall_seconds": list(wall_observations),
            "cpu_seconds": list(cpu_observations),
            "peak_rss_bytes": 2_000_000 + index,
        }
        for index, name in enumerate(estimate._ALL_TIMING_UNITS)
    }
    return {
        "identity": {
            "operating_system": "Linux",
            "kernel_release": "fixture-kernel",
            "kernel_version": "fixture-version",
            "wsl_detected": True,
            "machine": "x86_64",
            "cpu_model": "fixture-cpu",
            "python_version": "3.fixture",
            "python_implementation": "CPython",
            "numpy_version": "fixture",
            "torch_version": "fixture",
            "device": "cpu",
            "processes": 1,
            "intra_op_threads": 4,
            "inter_op_threads": 1,
            "accelerators": 0,
        },
        "cold_imported_process_rss": {
            "peak_rss_bytes": 1_900_000,
            "current_rss_bytes": 1_800_000,
            "proc_high_water_bytes": 1_900_000,
        },
        "measurement_repetitions": 3,
        "timing_units": timing_units,
        "rss_stages_bytes": {
            "cold_imported_process": 1_900_000,
            "actor_autograd": 2_000_000,
            "validation_panel": 2_000_001,
            "base_plus_replay_fit": 2_000_002,
            "four_fit_concatenation": 2_000_003,
            "packet_compression_write": 2_000_004,
            "packet_read_access": 2_000_005,
            "compression": 2_000_006,
            "neutral_table_io": 2_000_007,
            "neutral_metadata_json_io": 2_000_008,
        },
        "storage_bytes": {
            "raw_per_packet_payload_bytes": 110_000_000,
            "compressed_per_packet_bytes": 1_000_000,
            "logical_sixteen_packet_bytes": 16_000_000,
            "raw_source_table_payload_bytes": 312_064,
            "compressed_table_bytes": 200_000,
            "metadata_json_bytes": 1_024,
            "staging_temporary_bytes": 16_201_024,
            "complete_tree_bytes": 16_201_024,
        },
    }


def _fabricated_capacities() -> dict[str, int]:
    return {
        "memory_available_bytes": 16 * 1024**3,
        "disk_available_bytes": 32 * 1024**3,
    }


def test_literal_projection_schema_and_storage_unknowns() -> None:
    report = estimate._build_report(_fabricated_measurements(), _fabricated_capacities())

    assert report["workload"]["counts"] == {
        "gate_training_updates": 24_576,
        "validation_panels": 192,
        "conditional_training_updates": 32_768,
        "base_plus_replay_fit_evaluations": 64,
        "four_fit_concatenations": 16,
        "packet_writes": 16,
        "packet_read_access_units": 16,
        "neutral_table_io_units": 1,
        "neutral_metadata_json_io_units": 1,
    }
    assert report["workload"]["formulas"]["gate_only_wall_and_cpu"] == (
        "24_576 * training_update_unit + 192 * validation_panel_unit"
    )
    assert report["workload"]["formulas"]["all_pass_wall_and_cpu"] == (
        "gate_only + 32_768 * training_update_unit + 64 * base_plus_replay_fit_unit + "
        "16 * four_fit_concatenation_unit + 16 * packet_compression_write_unit + "
        "16 * packet_read_access_unit + 1 * neutral_table_io_unit + "
        "1 * neutral_metadata_json_io_unit"
    )
    assert report["workload"]["fixture_shapes"] == {
        "training_episodes": 48,
        "training_epochs": 2,
        "validation_panel_rows": 1_536,
        "base_plus_replay_rows": 24_576,
        "evaluation_rows_per_fit": 12_288,
        "combined_packet_rows": 49_152,
        "four_fit_members": 4,
        "raw_per_packet_payload_bytes": 110_000_000,
        "source_table_payload_bytes": 312_064,
        "logical_packet_count": 16,
    }

    expected_metric_names = {
        "wall_seconds",
        "cpu_seconds",
        "peak_rss_bytes",
        "temporary_bytes",
        "retained_bytes",
        "process_count",
        "thread_count",
        "accelerator_count",
    }
    for path_name in ("gate_only", "all_pass"):
        metrics = report["paths"][path_name]["metrics"]
        assert set(metrics) == expected_metric_names
        for metric in metrics.values():
            assert set(metric) == {
                "unit",
                "status",
                "central",
                "conservative_upper",
                "reason",
            }

    gate_count = 24_576 + 192
    all_pass_count = gate_count + 32_768 + 64 + 16 + 16 + 16 + 1 + 1
    gate_wall = report["paths"]["gate_only"]["metrics"]["wall_seconds"]
    all_pass_wall = report["paths"]["all_pass"]["metrics"]["wall_seconds"]
    assert gate_wall["status"] == "grounded"
    assert gate_wall["central"] == pytest.approx(gate_count * 0.002)
    assert gate_wall["conservative_upper"] == pytest.approx(gate_count * 0.003 * 1.25)
    assert all_pass_wall["status"] == "grounded"
    assert all_pass_wall["central"] == pytest.approx(all_pass_count * 0.002)
    assert all_pass_wall["conservative_upper"] == pytest.approx(
        all_pass_count * 0.003 * 1.25
    )
    assert report["paths"]["gate_only"]["metrics"]["temporary_bytes"]["status"] == "unknown"
    assert report["paths"]["gate_only"]["metrics"]["temporary_bytes"]["central"] is None
    assert report["paths"]["gate_only"]["metrics"]["retained_bytes"]["conservative_upper"] is None
    assert report["paths"]["gate_only"]["comparisons"]["disk"]["within_safe_available"] is None
    assert report["paths"]["gate_only"]["comparisons"]["disk"]["within_source_envelope"] is None
    assert {item["quantity"] for item in report["unknowns"]} == {
        "gate_only.temporary_bytes",
        "gate_only.retained_bytes",
    }
    assert report["measurements"]["peak_rss_observer"] == {
        "platform": "Linux",
        "source": "resource.getrusage(RUSAGE_SELF).ru_maxrss",
        "native_unit": "KiB",
        "conversion": "integer KiB * 1024 bytes",
    }
    assert report["measurements"]["storage_units"]["compressed_per_packet"]["formula"] == (
        "observed compressed NPZ packet bytes"
    )
    assert report["paths"]["all_pass"]["comparisons"]["disk"]["estimate_formula"] == (
        "max(temporary_bytes.conservative_upper, retained_bytes.conservative_upper)"
    )
    assert report["actions"] == {
        "all_pass_wall_classification": "at_or_below_7200_seconds",
        "all_pass_memory_classification": "within_safe_capacity_and_source_envelope",
        "all_pass_disk_classification": "within_safe_capacity_and_source_envelope",
        "unsafe_memory": {
            "reduction_batching_or_sharding_required": False,
            "approval_route_available": False,
        },
        "later_high_cost_execution": {
            "performance_reasonableness_review_attempt_required": False,
            "explicit_user_approval_required": False,
            "self_authorized": False,
        },
    }


def test_action_classifications_are_literal_and_fail_closed() -> None:
    assert estimate._classify_wall(estimate._metric("seconds", 7_000.0, 7_200.0)) == (
        "at_or_below_7200_seconds"
    )
    assert estimate._classify_wall(estimate._metric("seconds", 7_000.0, 7_200.0001)) == (
        "above_7200_seconds"
    )
    assert estimate._classify_wall(estimate._metric("seconds", None, None)) == "ungrounded"
    assert estimate._classify_memory(
        {"within_safe_available": True, "within_source_envelope": True}
    ) == "within_safe_capacity_and_source_envelope"
    assert estimate._classify_memory(
        {"within_safe_available": False, "within_source_envelope": True}
    ) == "reduction_batching_or_sharding_required"
    assert estimate._classify_memory(
        {"within_safe_available": None, "within_source_envelope": True}
    ) == "ungrounded"


def test_main_creates_canonical_sorted_json_once_without_default_workload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        estimate,
        "_collect_default_measurements",
        lambda temporary_parent: _fabricated_measurements(),
    )
    monkeypatch.setattr(
        estimate,
        "_read_capacities",
        lambda output_parent: _fabricated_capacities(),
    )
    output = tmp_path / "estimate.json"

    assert estimate.main(["--output", str(output)]) == 0
    payload = output.read_bytes()
    document = json.loads(payload)
    assert payload == (
        json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    assert not Path(f"{output}.tmp").exists()
    with pytest.raises(estimate.OutputPathError):
        estimate.main(["--output", str(output)])


def test_output_preflight_refusals(tmp_path: Path) -> None:
    with pytest.raises(estimate.OutputPathError):
        estimate._canonical_output_path("relative.json")
    with pytest.raises(estimate.OutputPathError):
        estimate._canonical_output_path(tmp_path / "estimate.txt")
    with pytest.raises(estimate.OutputPathError):
        estimate._canonical_output_path(f"{tmp_path}/nested/../estimate.json")

    real_parent = tmp_path / "real"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(estimate.OutputPathError):
        estimate._canonical_output_path(linked_parent / "estimate.json")

    fresh = tmp_path / "fresh.json"
    Path(f"{fresh}.tmp").write_text("occupied", encoding="utf-8")
    with pytest.raises(estimate.OutputPathError):
        with estimate._preflight_output(fresh):
            pass
    assert not fresh.exists()


def test_recursive_artifact_firewall_rejects_fields_tokens_and_nonfinite_data() -> None:
    estimate._artifact_firewall({"validation_panel": {"rows": 1_536}})
    refused = (
        {"nested": {"reward": 1.0}},
        {"nested_reward_metric": 1.0},
        {"note": "policy output"},
        {"note": "registered seed"},
        {"nested": [0.0, float("nan")]},
        {"nested": [0.0, float("inf")]},
    )
    for document in refused:
        with pytest.raises(estimate.ArtifactFirewallError):
            estimate._canonical_json_bytes(document)


def test_tiny_guarded_collector_blocks_import_call_and_optimizer_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forbidden_module = next(
        name for name in estimate.FORBIDDEN_MGTAP_MODULES if name.endswith(".trainer")
    )
    with pytest.raises(estimate.CollectionBoundaryError):
        estimate._run_guarded_collection(
            lambda: importlib.import_module(forbidden_module)  # type: ignore[return-value]
        )

    effects: list[str] = []
    fake_run = ModuleType("experiments.candidates.metric_ground_transport_allocation.run")

    def production(path: object) -> None:
        del path
        effects.append("called")

    fake_run.production = production  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, fake_run.__name__, fake_run)
    with pytest.raises(estimate.CollectionBoundaryError):
        estimate._run_guarded_collection(
            lambda: (fake_run.production(None), {})[1]  # type: ignore[attr-defined]
        )
    assert effects == []

    parameter = estimate.torch.nn.Parameter(estimate.torch.tensor([1.0]))
    optimizer = estimate.torch.optim.SGD([parameter], lr=0.5)
    before = parameter.detach().clone()

    def attempt_step() -> dict[str, object]:
        parameter.grad = estimate.torch.ones_like(parameter)
        optimizer.step()
        return {}

    with pytest.raises(estimate.CollectionBoundaryError):
        estimate._run_guarded_collection(attempt_step)
    assert estimate.torch.equal(parameter.detach(), before)
