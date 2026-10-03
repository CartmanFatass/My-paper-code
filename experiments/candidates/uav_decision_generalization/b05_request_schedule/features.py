"""Fixed 303-column action features, retaining canonical float64 G values."""
import numpy as np

from .contract import FEATURE_COUNT, HORIZON
from .task import _array, candidate_slots

# Slice names are explicit for consumers and independent feature reconstruction.
FEATURE_SLICES = {
    "users": slice(0, 100), "rates": slice(100, 104),
    "positions": slice(104, 122), "ack": slice(122, 172),
    "counts": slice(172, 176), "progress": slice(176, 180),
    "pairs": slice(180, 198), "active_slots": slice(198, 246),
    "candidate_slots": slice(246, 294), "action": slice(294, 298),
    "time": slice(298, 299), "g_values": slice(299, 303),
}


def candidate_features(state, g_costs):
    raw = _array(g_costs, np.float64, (4,), "G costs")
    candidates = candidate_slots(state)
    positions = state.positions.copy()
    positions[:, :2] /= 5000.0
    positions[:, 2] = (positions[:, 2] - 50.0) / 100.0
    pair_membership = np.zeros((6, 3), dtype=np.float64)
    for pair_index, pair in enumerate(state.pairs):
        pair_membership[list(pair), pair_index] = 1.0
    common = np.concatenate((state.users.ravel() / 5000.0, state.probabilities,
                             positions.ravel(), state.ack, state.counts / 48.0,
                             state.progress / 20.0, pair_membership.ravel(),
                             np.eye(8)[state.active_slots].ravel()))
    features = np.concatenate((np.tile(common, (4, 1)),
                               np.eye(8)[candidates].reshape(4, 48), np.eye(4),
                               np.full((4, 1), state.tick / HORIZON),
                               np.tile(raw / HORIZON, (4, 1))), axis=1).astype(np.float32)
    assert features.shape == (4, FEATURE_COUNT)
    return features, raw
