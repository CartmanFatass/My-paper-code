"""Lawful local features and the fixed B01 recurrent policy."""

import numpy as np
import torch
from torch import nn

from experiments.candidates.finite_model_decision_value.b01.host import FRAME


FEATURES = 35


def features(record, calibration_displacements):
    """Encode one copied LocalRecord; no host, belief or future is accepted."""
    moves = np.asarray(calibration_displacements)
    if moves.shape != (record.batch, 4) or not np.isin(moves, (0, 1)).all():
        raise ValueError("four observed binary calibration displacements per context required")

    def payload(value, valid):
        value = np.asarray(value)
        valid = np.asarray(valid, dtype=bool)
        stage = np.eye(3, dtype=np.float32)[value[:, 0]]
        scalars = np.column_stack((value[:, 1] / 7, value[:, 2] / 4,
                                   value[:, 3] / 16, value[:, 4])).astype(np.float32)
        return np.concatenate((stage, scalars), axis=1) * valid[:, None]

    last_valid = record.last_sent_time >= 0
    peer_valid = record.peer_packet_time >= 0
    output = np.concatenate((
        payload(record.own, np.ones(record.batch, dtype=bool)),
        payload(record.last_sent, last_valid),
        payload(record.peer_packet, peer_valid),
        np.column_stack((last_valid, record.last_sent_time / 96,
                         peer_valid, record.peer_packet_time / 96,
                         record.available,
                         np.full(record.batch, record.t / 96),
                         np.full(record.batch, record.t % FRAME / FRAME),
                         np.full(record.batch, record.t % 12 / 12),
                         np.full(record.batch, record.t % 16 / 16),
                         np.full(record.batch, record.agent),
                         moves)).astype(np.float32),
    ), axis=1).astype(np.float32)
    if output.shape != (record.batch, FEATURES) or not np.isfinite(output).all():
        raise AssertionError("invalid lawful feature shape or values")
    return output


class Student(nn.Module):
    def __init__(self):
        super().__init__()
        self.input = nn.Linear(FEATURES, 64)
        self.gru = nn.GRU(64, 64, batch_first=True)
        self.logit = nn.Linear(64, 1)

    def forward(self, sequence, memory=None):
        projected = torch.tanh(self.input(sequence))
        output, memory = self.gru(projected, memory)
        return self.logit(output).squeeze(-1), memory
