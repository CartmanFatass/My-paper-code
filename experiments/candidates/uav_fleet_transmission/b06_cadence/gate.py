"""Lawful local-count scheduler, with no actor or evaluator access."""
from numbers import Integral
import numpy as np


def own_count(row):
    row = np.asarray(row)
    if row.shape != (104,) or row.dtype != np.float32 or not np.isfinite(row).all():
        raise ValueError("gate requires one finite original FP32 observation")
    return min(10, int(np.count_nonzero(row[3:63].reshape(20, 3)[:, 2] > 0.)))


class Cadence:
    """One agent's original-block clock; E observes every tick, including spent ones."""
    def __init__(self, mode):
        if mode not in ("H4", "E", "H1"):
            raise ValueError("unknown cadence")
        self.mode, self.next_tick, self.previous, self.used = mode, 0, None, False

    def step(self, row, tick):
        if isinstance(tick, (bool, np.bool_)) or not isinstance(tick, Integral) or tick != self.next_tick:
            raise ValueError("cadence requires consecutive native ticks beginning at zero")
        self.next_tick += 1
        boundary = tick % 4 == 0
        q, loss, available = -1, False, False
        if self.mode == "E":
            q = own_count(row)
            loss = self.previous is not None and q < self.previous
            if boundary:
                self.used = False
            available = not boundary and not self.used
            extra = bool(loss and available)
            if extra:
                self.used = True
            self.previous = q
        else:
            extra = False
        query = bool(boundary or extra or self.mode == "H1")
        return dict(query=query, count=q, loss=bool(loss), available=bool(available),
                    extra=extra, used=bool(self.used),
                    kind=0 if boundary else 1 if extra else 2 if query else -1)


def remaining_motion_changed(position, old_command, new_command, tick):
    """Compare clipped command paths until the ORIGINAL boundary, without a model query."""
    old, new = np.asarray(position, dtype=np.float64).copy(), np.asarray(position, dtype=np.float64).copy()
    previous, replacement = np.asarray(old_command, dtype=np.float64), np.asarray(new_command, dtype=np.float64)
    changed = False
    for _ in range(4 - tick % 4):
        old = np.clip(old + 30. * previous, (0., 0., 50.), (1000., 1000., 150.))
        new = np.clip(new + 30. * replacement, (0., 0., 50.), (1000., 1000., 150.))
        changed |= not np.array_equal(old, new)
    return bool(changed)
