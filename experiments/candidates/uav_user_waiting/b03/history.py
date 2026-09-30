"""Running modeled maxima on the unchanged atomic executed settlement path."""

from dataclasses import dataclass, field

import numpy as np

from experiments.candidates.uav_user_waiting.b01.history import (
    ExecutionHistory as PreviousExecutionHistory, ServiceHistory as PreviousHistory,
)


@dataclass
class ServiceHistory(PreviousHistory):
    maximum: np.ndarray = field(default_factory=lambda: np.zeros(50, np.int64))

    def copy(self):
        return ServiceHistory(self.start_tick, self.last.copy(), self.windows.copy(),
                              self.burden.copy(), self.maximum.copy())

    def update(self, tick, served):
        result = super().update(tick, served)
        self.maximum = np.maximum(self.maximum, np.int64(tick) - self.last)
        return result


class ExecutionHistory(PreviousExecutionHistory):
    def __init__(self, sites):
        super().__init__(sites)
        self.history = ServiceHistory()
