"""Fixed N8 static S1 worlds, with inherited native transmitter semantics."""
import numpy as np

from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from experiments.candidates.agent_count_generalization.adapter import CountAdapter
from experiments.candidates.agent_count_generalization.runner import preserve_rng
from experiments.candidates.uav_fleet_transmission.host import (
    FleetS1 as _FleetS1, MatchedWorld, _integer, mask_bits, mask_integer,
)

TRAIN_WORLD_IDS = tuple(range(29317000, 29317512))
EVAL_WORLD_IDS = tuple(range(29316000, 29316032))


def _seed(world_id, stream):
    world_id = _integer(world_id, "world_id")
    if world_id not in TRAIN_WORLD_IDS and world_id not in EVAL_WORLD_IDS:
        raise ValueError("world_id outside the declared training/evaluation panels")
    return int(np.random.SeedSequence([260930, 17, world_id, stream])
               .generate_state(1, dtype=np.uint32)[0])


def runtime_seed(world_id):
    return _seed(world_id, 3)


def world(world_id):
    user_seed, uav_seed = _seed(world_id, 1), _seed(world_id, 2)
    user_rng, uav_rng = np.random.RandomState(user_seed), np.random.RandomState(uav_seed)
    users, uavs = np.empty((50, 2)), np.empty((8, 3))
    for row in users:
        row[:] = [user_rng.uniform(0, 1000), user_rng.uniform(0, 1000)]
    for row in uavs:
        row[:] = [uav_rng.uniform(0, 1000), uav_rng.uniform(0, 1000), uav_rng.uniform(50, 150)]
    users.setflags(write=False)
    uavs.setflags(write=False)
    return MatchedWorld(int(world_id), user_seed, uav_seed, users, uavs)


class FleetS1(_FleetS1):
    """Reuse the retained mask/reset methods; fixtures explicitly supply worlds."""

    def __init__(self, world_id, horizon=500, *, world_generator=world):
        horizon = _integer(horizon, "horizon")
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        self.matched_world = world_generator(world_id)
        if (self.matched_world.user_positions.shape != (50, 2)
                or self.matched_world.uav_positions.shape != (8, 3)):
            raise ValueError("requires 50 users and eight physical UAVs")
        self._matched_reset_ready = False
        with preserve_rng():
            UAVBaseStationEnv.__init__(
                self, n_uavs=8, n_users=50, max_steps=horizon,
                user_distribution="uniform", channel_model="free_space",
                seed=self.matched_world.user_seed, min_sinr=0, max_connections=10,
            )
            self.enable_transmitter_mask = True
            self._matched_reset_ready = True
            self.reset()

    def reset(self, seed=None, options=None):
        with preserve_rng():
            return super().reset(seed=seed, options=options)


NativeFleetS1 = FleetS1


def make_env(world_id, horizon=500):
    with preserve_rng():
        return CountAdapter(ParallelToArrayAdapter(
            FleetS1(world_id, horizon), seed=runtime_seed(world_id)))
