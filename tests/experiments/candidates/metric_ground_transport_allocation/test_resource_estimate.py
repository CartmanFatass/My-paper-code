from __future__ import annotations

import inspect
import math
from pathlib import Path

import numpy as np

from experiments.candidates.metric_ground_transport_allocation import resource_estimate


def test_current_authority_workload_is_frozen() -> None:
    assert resource_estimate.WORKLOAD == {
        "gate_training_units": 24_576,
        "validation_panel_units": 192,
        "conditional_conclusion_training_units": 32_768,
        "conditional_base_plus_replay_units": 64,
        "conditional_packet_writes": 16,
    }
    assert resource_estimate.STATIC_PACKET_BYTES == 110_000_000
    assert resource_estimate.STATIC_SIXTEEN_PACKET_BYTES == 1_760_000_000


def test_module_has_no_registered_mgtap_import_or_optimizer() -> None:
    source = inspect.getsource(resource_estimate)
    forbidden_imports = (
        "from .run import",
        "from .trainer import",
        "from .evaluation import",
        "from .analysis import",
        "from .rng import",
        "from .artifacts import",
    )
    assert all(token not in source for token in forbidden_imports)
    assert "torch.optim" not in source


def test_authority_refs_match_current_revision_four_checkout() -> None:
    root = Path.cwd()
    refs = resource_estimate._validate_authority(root)
    assert {ref["label"] for ref in refs} == set(resource_estimate.AUTHORITY_REFS)


def test_hand_written_compute_fixtures_are_finite_and_repeatable() -> None:
    resource_estimate._training_fixture()
    resource_estimate._validation_panel_fixture()
    resource_estimate._base_plus_replay_fixture()


def test_packet_fixture_is_typed_numeric_and_has_expected_row_shape() -> None:
    arrays = resource_estimate._packet_arrays(rows=8)
    assert {array.dtype for array in arrays.values()} == {
        np.dtype("int8"),
        np.dtype("int16"),
        np.dtype("int32"),
        np.dtype("float64"),
    }
    assert all(array.shape[0] == 8 for array in arrays.values())
    assert all(np.all(np.isfinite(array)) for array in arrays.values())


def test_projection_uses_exact_conditional_counts() -> None:
    timing = {
        "central_wall_seconds_per_unit": 1.0,
        "observed_max_wall_seconds_per_unit": 2.0,
        "central_cpu_seconds_per_unit": 3.0,
        "observed_max_cpu_seconds_per_unit": 4.0,
    }
    common = {
        "wall_seconds": 5.0,
        "cpu_seconds": 6.0,
        "complete_common_tree_bytes": 100,
    }
    packet = {
        "write_wall_seconds": 7.0,
        "read_access_wall_seconds": 8.0,
        "write_cpu_seconds": 9.0,
        "read_access_cpu_seconds": 10.0,
        "compressed_bytes": 1_000,
    }
    projection = resource_estimate._project(
        0.5,
        0.25,
        timing,
        timing,
        timing,
        common,
        packet,
        1_024,
        2_048,
    )
    expected_gate_wall = 0.5 + 24_576 + 192 + 5.0
    expected_all_wall = expected_gate_wall + 32_768 + 64 + 16 * 15.0
    assert projection["gate_only"]["central_wall_seconds"] == expected_gate_wall
    assert projection["all_pass"]["central_wall_seconds"] == expected_all_wall
    assert projection["gate_only"]["central_peak_rss_bytes"] == 1_024
    assert projection["all_pass"]["central_peak_rss_bytes"] == 2_048
    assert math.isfinite(projection["all_pass"]["conservative_upper_cpu_seconds"])


def test_process_and_capacity_observers_return_positive_bytes() -> None:
    current, peak = resource_estimate._process_memory_bytes()
    total, available = resource_estimate._physical_memory_bytes()
    assert 0 < current <= peak
    assert 0 < available <= total
