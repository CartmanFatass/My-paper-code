"""Direction-owned static S1 worlds and native transmitter activation."""

from dataclasses import dataclass
from numbers import Integral

import numpy as np

from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.uav_env import MultiUAVEnv

WORLD_IDS = tuple(range(29310000, 29310016))
N_USERS = 50
MAX_UAVS = 8


def _integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    return int(value)


def _seed(world_id, stream, *suffix):
    world_id = _integer(world_id, "world_id")
    if world_id not in WORLD_IDS:
        raise ValueError("world_id outside the declared panel")
    return int(np.random.SeedSequence([260930, 14, world_id, stream, *suffix])
               .generate_state(1, dtype=np.uint32)[0])


def runtime_seed(world_id, n_uavs):
    n_uavs = _integer(n_uavs, "n_uavs")
    if n_uavs not in (4, 8):
        raise ValueError("the fleet panel supports N4 and N8")
    return _seed(world_id, 3, n_uavs)


@dataclass(frozen=True)
class MatchedWorld:
    world_id: int
    user_seed: int
    uav_seed: int
    user_positions: np.ndarray
    uav_positions: np.ndarray


def world(world_id):
    """Draw member-major independent streams without consulting any outcome."""
    user_seed, uav_seed = _seed(world_id, 1), _seed(world_id, 2)
    user_rng, uav_rng = np.random.RandomState(user_seed), np.random.RandomState(uav_seed)
    users = np.empty((N_USERS, 2), dtype=np.float64)
    uavs = np.empty((MAX_UAVS, 3), dtype=np.float64)
    for row in users:
        row[:] = [user_rng.uniform(0, 1000), user_rng.uniform(0, 1000)]
    for row in uavs:
        row[:] = [uav_rng.uniform(0, 1000), uav_rng.uniform(0, 1000),
                  uav_rng.uniform(50, 150)]
    users.setflags(write=False)
    uavs.setflags(write=False)
    return MatchedWorld(int(world_id), user_seed, uav_seed, users, uavs)


def mask_bits(mask, n_uavs):
    mask = _integer(mask, "mask")
    if not 1 <= mask < 1 << n_uavs:
        raise ValueError("mask must be a nonempty fleet bitmask")
    return (mask & (1 << np.arange(n_uavs))) != 0


def mask_integer(mask):
    mask = np.asarray(mask)
    if mask.dtype != np.dtype(bool) or mask.ndim != 1:
        raise ValueError("mask must be a one-dimensional boolean array")
    return int(np.sum(mask.astype(np.int64) * (1 << np.arange(mask.size))))


class FleetS1(UAVBaseStationEnv):
    """S1 with all physical UAVs retained when a transmitter is silent."""

    def __init__(self, n_uavs, world_id, horizon=500):
        n_uavs, horizon = _integer(n_uavs, "n_uavs"), _integer(horizon, "horizon")
        if n_uavs not in (4, 8) or horizon <= 0:
            raise ValueError("requires N4/N8 and a positive horizon")
        self.matched_world = world(world_id)
        self._matched_reset_ready = False
        super().__init__(n_uavs=n_uavs, n_users=N_USERS, max_steps=horizon,
                         user_distribution="uniform", channel_model="free_space",
                         seed=self.matched_world.user_seed, min_sinr=0,
                         max_connections=10)
        self.enable_transmitter_mask = True
        self._matched_reset_ready = True
        self.reset()

    def _update_channel_state(self, reuse_physical_channel=False):
        # Scenario1's override predates the generic mask setter's keyword.
        # The generic paths use the same native assignment and observations.
        if self.channel_backend == "reference":
            MultiUAVEnv._update_channel_state_reference(self, reuse_physical_channel)
        else:
            self._update_channel_state_vectorized(reuse_physical_channel)

    def reset(self, seed=None, options=None):
        native_seed = self.matched_world.user_seed if seed is None else seed
        observations, infos = super().reset(seed=native_seed, options=options)
        if self._matched_reset_ready:
            np.copyto(self.user_positions, self.matched_world.user_positions)
            np.copyto(self.uav_positions, self.matched_world.uav_positions[:self.n_uavs])
            self._begin_path_loss_step()
            self._update_channel_state()
            observations = {agent: self._get_observation(agent) for agent in self.agents}
        return observations, infos
