"""Accumulated reconstructed waiting on the frozen causal settlement path."""

from dataclasses import dataclass, field

import numpy as np

from experiments.candidates.uav_radio_activation.b03.protocol import U
from experiments.candidates.uav_registered_service.b01.history import (
    ExecutionHistory as FrozenExecutionHistory,
    ServiceHistory as FrozenServiceHistory,
)


@dataclass
class ServiceHistory(FrozenServiceHistory):
    """Sum post-transition ages, retaining permanent initial-prefix censorship.

    With a late first anchor, the inherited -1 last-service sentinel reconstructs
    age as tick+1 until first observed service. Those numerical burdens are only
    reconstructed values: the missing prefix never becomes complete later.
    """

    burden: np.ndarray = field(default_factory=lambda: np.zeros(U, dtype=np.int64))

    @property
    def burden_unknown(self):
        return self.start_tick > 0

    def copy(self):
        return ServiceHistory(self.start_tick, self.last.copy(), self.windows.copy(),
                              self.burden.copy())

    def update(self, tick, served):
        new_pairs = super().update(tick, served)
        self.burden += np.int64(tick) - self.last
        return new_pairs


class ExecutionHistory(FrozenExecutionHistory):
    """Keep frozen anchors, postmove physics, and atomic executed settlement."""

    def __init__(self, sites):
        super().__init__(sites)
        self.history = ServiceHistory()
