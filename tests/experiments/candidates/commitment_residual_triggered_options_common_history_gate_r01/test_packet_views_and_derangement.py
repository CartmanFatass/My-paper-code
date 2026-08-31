import numpy as np
import pytest
import torch

from experiments.candidates.commitment_residual_triggered_options.predictor import (
    CalibrationTable as CitedCalibrationTable, make_packets as cited_make_packets,
    whitened_residual as cited,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    PanelRow, RowKey, Split,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.derangement import (
    DerangementPlan, build_derangement,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.packets import (
    CalibrationTable, PacketDataset, construct_packet_views, raw_packet, residual_packet,
    whitened_residual,
)


def _row(index: int) -> PanelRow:
    legal = np.ones(8, dtype=bool)
    return PanelRow(
        RowKey(0, Split.TRAIN, "K8", index, 60, 0), 0.25, 4,
        np.full((2, 42), index, dtype=np.float32),
        np.linspace(0.0, 0.7, 8, dtype=np.float32) + index,
        np.zeros(8, dtype=np.float32), np.eye(8, dtype=np.float32),
        legal, np.arange(8, dtype=np.float64), 0, ("tape", index),
    )


def test_fp32_triangular_equivalence_and_packet_width() -> None:
    target = np.arange(8, dtype=np.float32) / 3
    mean = np.arange(8, dtype=np.float32) / 7
    factor = np.tril(np.full((8, 8), 0.02, dtype=np.float32)) + np.eye(8, dtype=np.float32)
    actual = whitened_residual(target, mean, factor)
    expected = cited(torch.from_numpy(target), torch.from_numpy(mean), torch.from_numpy(factor)).numpy()
    assert actual.dtype == np.float32
    assert np.array_equal(actual, expected)
    rows = tuple(_row(index) for index in range(4))
    calibration = CalibrationTable(np.sort(np.stack([actual] * 4).T, axis=1))
    views = construct_packet_views(rows, calibration)
    assert views.raw.shape == views.true_residual.shape == (4, 52)
    assert np.all(views.true_residual[:, 24:] == 0.0)

    support = np.sort(np.stack((actual - 0.5, actual, actual + 0.5)).T, axis=1).astype(np.float32)
    ours = CalibrationTable(support)
    cited_table = CitedCalibrationTable(torch.from_numpy(support))
    cited_packets = cited_make_packets(
        torch.from_numpy(target), torch.from_numpy(mean), torch.from_numpy(factor), cited_table,
    )
    assert np.array_equal(raw_packet(target, mean, factor), cited_packets.raw.numpy())
    assert np.array_equal(
        residual_packet(target, mean, factor, ours), cited_packets.explicit.numpy()
    )

    zero = np.zeros(8, dtype=np.float32)
    zero_support = np.zeros((8, 1), dtype=np.float32)
    ours_zero = residual_packet(zero, zero, np.eye(8, dtype=np.float32), CalibrationTable(zero_support))
    cited_zero = cited_make_packets(
        torch.from_numpy(zero), torch.from_numpy(zero), torch.eye(8),
        CitedCalibrationTable(torch.from_numpy(zero_support)),
    ).explicit.numpy()
    assert ours_zero.tobytes(order="C") == cited_zero.tobytes(order="C")


def test_derangement_is_cell_local_fixed_point_free_and_multiset_exact() -> None:
    rows = tuple(_row(index) for index in range(4))
    packets = np.arange(4 * 52, dtype=np.float32).reshape(4, 52)
    source = PacketDataset(tuple(row.key.text for row in rows), packets)
    deranged, plan = build_derangement(rows, source, replicate=0)
    assert all(index != donor for index, donor in enumerate(plan.donor_indices))
    assert sorted(map(tuple, packets)) == sorted(map(tuple, deranged.values))
    restored = DerangementPlan.from_json(plan.to_json())
    assert restored == plan
    assert np.array_equal(restored.apply(rows, source).values, deranged.values)
    tampered = restored.to_json()
    tampered["recipient_keys"][0] = "wrong-row"  # type: ignore[index]
    with pytest.raises(ValueError, match="not bound"):
        DerangementPlan.from_json(tampered).apply(rows, source)


def test_derangement_refuses_singleton_cells() -> None:
    with pytest.raises(ValueError, match="fewer than two"):
        row = _row(0)
        build_derangement(
            (row,), PacketDataset((row.key.text,), np.zeros((1, 52), dtype=np.float32)),
            replicate=0,
        )
