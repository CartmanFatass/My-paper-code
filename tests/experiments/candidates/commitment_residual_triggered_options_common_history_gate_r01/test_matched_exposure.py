import numpy as np
import pytest

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    Budget, PanelRow, Representation, RowKey, Split,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.training import train_one_path
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.packets import PacketDataset


def _row(index: int) -> PanelRow:
    return PanelRow(
        RowKey(0, Split.TRAIN, "K8", index, 60, 0), 0.25, 4,
        np.ones((2 + index, 42), dtype=np.float32), np.zeros(8, dtype=np.float32),
        np.zeros(8, dtype=np.float32), np.eye(8, dtype=np.float32),
        np.ones(8, dtype=bool), np.arange(8, dtype=np.float64), 0, ("tape", index),
    )


def test_short_snapshot_continues_to_long_with_matched_work() -> None:
    rows = (_row(0), _row(1))
    order = np.resize(np.asarray((1, 0), dtype=np.int64), 2 * 64)
    packets = PacketDataset(tuple(row.key.text for row in rows), np.zeros((2, 52), dtype=np.float32))
    raw = train_one_path(
        rows, packets, replicate=0, representation=Representation.RAW,
        order=order, short_updates=1, long_updates=2,
    )
    true = train_one_path(
        rows, packets, replicate=0, representation=Representation.TRUE_RESIDUAL,
        order=order, short_updates=1, long_updates=2,
    )
    deranged = train_one_path(
        rows, packets, replicate=0, representation=Representation.CALIBRATED_DERANGEMENT,
        order=order, short_updates=1, long_updates=2,
    )
    assert raw.audits[Budget.SHORT].processed_examples == 64
    assert raw.audits[Budget.LONG].processed_examples == 128
    assert raw.audits[Budget.SHORT].initialization_state == true.audits[Budget.SHORT].initialization_state
    assert raw.audits[Budget.LONG].order == true.audits[Budget.LONG].order
    assert raw.final_parameters == true.final_parameters
    assert deranged.audits[Budget.LONG].logical_work == 128
    assert deranged.audits[Budget.LONG].initialization_state == raw.audits[Budget.LONG].initialization_state


def test_training_refuses_packet_row_permutation() -> None:
    rows = (_row(0), _row(1))
    packets = PacketDataset(
        tuple(row.key.text for row in reversed(rows)), np.zeros((2, 52), dtype=np.float32)
    )
    with pytest.raises(ValueError, match="row-key order"):
        train_one_path(
            rows, packets, replicate=0, representation=Representation.RAW,
            order=np.resize(np.asarray((0, 1), dtype=np.int64), 64),
            short_updates=1, long_updates=1,
        )
