"""One-transition coordinate anchor, computed only from private observations."""
import numpy as np

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import own_positions


class Binding:
    def __init__(self):
        self.anchor = np.zeros((5, 2), dtype=np.float64)
        self.valid = np.zeros(5, dtype=bool)
        self.sinr = np.zeros(5, dtype=np.float64)
        self.previous_position = None

    def observe(self, obs, proposal):
        # Conversion before addition preserves float64 arithmetic over FP32 bytes.
        obs64 = np.asarray(obs, dtype=np.float32).astype(np.float64)
        rows = obs64[:, 3:63].reshape(5, 20, 3)
        visible = rows[:, :, 2] > 0
        count = visible.sum(1)
        coords = obs64[:, None, :2] + rows[:, :, :2]
        position = own_positions(obs)
        displacement = (np.zeros((5, 3)) if self.previous_position is None
                        else (position - self.previous_position) / 30)
        retrace = np.clip(-displacement, -1, 1)
        distance = np.max(np.abs(coords - self.anchor[:, None]), axis=-1)
        near = visible & (distance <= 2e-6)
        absent = ~near.any(1)
        loss = self.valid & absent & (count >= 1) & (count <= 19)
        relative = np.where(self.valid[:, None], self.anchor - obs64[:, :2], 0)
        away = -(np.asarray(proposal)[:, :2] * relative).sum(1)
        away = np.where(self.valid, away, 0)
        opportunity = loss & (away > 0)
        z = np.column_stack((self.valid, count / 20, loss, relative,
                             np.where(self.valid, self.sinr, 0), displacement, retrace, away))

        # First observed minimum, then intrinsic ambiguity in the CURRENT list.
        selected = np.where(visible, rows[:, :, 2], np.inf).argmin(1)
        next_anchor = coords[np.arange(5), selected]
        next_distance = np.max(np.abs(coords - next_anchor[:, None]), axis=-1)
        next_valid = (count > 0) & ((visible & (next_distance <= 2e-6)).sum(1) == 1)
        self.anchor = next_anchor
        self.valid = next_valid
        self.sinr = rows[np.arange(5), selected, 2]
        self.previous_position = position.copy()
        return z.astype(np.float32), opportunity, retrace.astype(np.float32)
