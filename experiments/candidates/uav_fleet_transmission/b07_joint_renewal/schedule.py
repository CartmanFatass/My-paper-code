"""Preconfigured private clocks and evaluator-only clipped-hold exposure."""
from numbers import Integral
import numpy as np

from .contract import LOW, HIGH


def query_due(tick, phase):
    if (isinstance(tick, (bool, np.bool_)) or not isinstance(tick, Integral) or tick < 0
            or isinstance(phase, (bool, np.bool_)) or not isinstance(phase, Integral) or phase not in range(4)):
        raise ValueError("invalid actual tick or phase")
    return bool(tick == 0 or (tick >= 4 + phase and (tick - phase) % 4 == 0))


def hold_ticks(tick, phase, horizon):
    if type(horizon) is not int or horizon < 8 or horizon % 4 or tick >= horizon or not query_due(tick, phase):
        raise ValueError("a hold starts only at a scheduled in-mission decision")
    return int(min(4 + phase if tick == 0 else 4, horizon - tick))


def physical_hold_changed(position, previous_command, next_command, ticks):
    """Any clipped path difference before the next own query, without radio queries."""
    if type(ticks) is not int or ticks <= 0:
        raise ValueError("positive integer hold required")
    previous = np.array(position, dtype=np.float64, copy=True)
    replacement = previous.copy()
    old_step = 30. * np.asarray(previous_command, dtype=np.float64)
    new_step = 30. * np.asarray(next_command, dtype=np.float64)
    changed = False
    for _ in range(ticks):
        previous = np.clip(previous + old_step, LOW, HIGH)
        replacement = np.clip(replacement + new_step, LOW, HIGH)
        changed |= not np.array_equal(previous, replacement)
    return bool(changed)
