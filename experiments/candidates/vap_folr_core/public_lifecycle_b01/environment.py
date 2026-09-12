"""Completed native lifecycle metadata; no additional simulator/RNG calls."""
import numpy as np

from .native_env import Entity_Traffic_Junction_Env


class LifecycleEnv(Entity_Traffic_Junction_Env):
    def reset(self, **kwargs):
        result = super().reset(**kwargs)
        self.birth = self.entity_mask == 0
        self.departure = np.zeros(self.ncar, dtype=bool)
        self.continuation = np.zeros(self.ncar, dtype=bool)
        self.event = False
        return result

    def _remove_car(self, id):
        # Native collision code can call removal on an inactive slot too.
        # Record only a real departure, but ALWAYS execute native side effects.
        self.departure[id] |= self.entity_mask[id] == 0
        super()._remove_car(id)

    def _add_car(self):
        inactive_before = self.entity_mask.astype(bool).copy()
        super()._add_car()
        self.birth |= inactive_before & (self.entity_mask == 0)

    def step(self, action):
        before = self.entity_mask == 0
        self.birth = np.zeros(self.ncar, dtype=bool)
        self.departure = np.zeros(self.ncar, dtype=bool)
        result = super().step(action)
        after = self.entity_mask == 0
        self.continuation = before & after & ~self.departure & ~self.birth
        self.event = bool(np.any(self.departure | self.birth))
        return result

    def observation(self, previous_actions):
        obs_mask, entity_mask = self.get_masks()
        previous = np.eye(self.n_actions, dtype=np.float32)[previous_actions]
        previous *= self.continuation[:, None]
        return {
            'entities': np.asarray(self.get_entities(), dtype=np.float32),
            'obs_mask': np.asarray(obs_mask, dtype=bool),
            'entity_mask': np.asarray(entity_mask, dtype=bool),
            'birth': self.birth.copy(),
            'continuation': self.continuation.copy(),
            'event': np.asarray(self.event),
            'previous_action': previous,
        }


def count_transition(env, arm):
    # Called after a real transition; terminal events have no next native action.
    eligible = int(np.sum(env.continuation)) if env.t < env.max_steps else 0
    opportunities = eligible if env.event else 0
    return {
        'births': int(env.birth.sum()),
        'departures': int(env.departure.sum()),
        'survivor_opportunities': opportunities,
        'eligible_survivor_opportunities': eligible,
        'survivor_resets': opportunities if arm == 'EVENT' else 0,
        'survivor_attenuations': opportunities if arm in ['HALF_EVENT', 'LEARNED_EVENT'] else 0,
    }
