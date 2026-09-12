"""Public episode capabilities act only at the native physical integration boundary."""
import numpy as np

from envs.pettingzoo.uav_env import MultiUAVEnv
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real


CAPABILITIES = np.array([.5, .75, 1., 1.25, 1.5], dtype=np.float32)


class HeterogeneousUAVEnv(MultiUAVEnv):
    def reset(self, seed=None, options=None):
        observations, infos = super().reset(seed=seed, options=options)
        # A separate exogenous domain leaves native placement/channel RNG untouched.
        rng = np.random.default_rng([int(self.seed_val), 37])
        self.capabilities = rng.permutation(CAPABILITIES)
        return observations, infos

    def step(self, actions):
        # The base consumes these values only in action * max_speed * time_step,
        # before clipping physical positions. Do not change the caller's proposals
        # or feed scaled physical velocities back as normalized command history.
        physical_inputs = {
            agent: np.asarray(command) * self.capabilities[self.possible_agents.index(agent)]
            for agent, command in actions.items()
        }
        return super().step(physical_inputs)


class CapabilityAdapter:
    def __init__(self, seed):
        self.base = make_real(seed, base_class=HeterogeneousUAVEnv)
        self.env = self.base.env

    def augment(self, observations):
        public = np.broadcast_to(self.env.capabilities, (5, 5))
        return np.concatenate((observations, public, np.eye(5, dtype=np.float32)),
                              axis=-1).astype(np.float32)

    def reset(self, seed=None):
        observations, info = self.base.reset(seed=seed)
        return self.augment(observations), info

    def step(self, actions):
        observations, reward, terminated, truncated, info = self.base.step(actions)
        return self.augment(observations), reward, terminated, truncated, info
