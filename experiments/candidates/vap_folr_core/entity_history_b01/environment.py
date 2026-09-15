"""Truthful public lifecycle and each observer's own sighting bookkeeping."""
import numpy as np

from ..public_lifecycle_b01.environment import LifecycleEnv


class EntityHistoryEnv(LifecycleEnv):
    def reset(self, **kwargs):
        result = super().reset(**kwargs)
        self.seen = np.zeros((5, 5), dtype=bool)
        self.age = np.zeros((5, 5), dtype=np.int16)
        self._observe_boundary()
        return result

    def step(self, action):
        result = super().step(action)
        self._observe_boundary()
        return result

    def _observe_boundary(self):
        # One update per completed primitive transition, never per observation read.
        active = ~self.entity_mask.astype(bool)
        visible = ~np.asarray(self.get_masks()[0], dtype=bool)
        self.visible = visible & active[:, None] & active[None, :]
        carry = self.continuation[:, None] & self.continuation[None, :]
        self.seen &= carry
        self.age = np.where(self.seen, self.age + 1, 0).astype(np.int16)
        self.seen |= self.visible
        self.age[self.visible] = 0

    def observation(self, previous_actions):
        result = super().observation(previous_actions)
        result.update(departure=self.departure.copy(), visible=self.visible.copy(),
                      seen=self.seen.copy(), age=self.age.copy())
        return result
