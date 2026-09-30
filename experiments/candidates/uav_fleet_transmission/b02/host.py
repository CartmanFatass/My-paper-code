"""Fresh B02 world identities; unchanged native B01 fleet physics."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import numpy as np

from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from experiments.candidates.agent_count_generalization.adapter import CountAdapter
from ..host import FleetS1, MatchedWorld

WORLD_IDS = tuple(range(29324000, 29324016))
WORLD_FILE = Path(__file__).with_name("worlds.json")


def seed(world_id, stream, *suffix):
    if type(world_id) is not int or world_id not in WORLD_IDS:
        raise ValueError("world outside the fixed B02 panel")
    return int(np.random.SeedSequence([260930, 24, world_id, stream, *suffix])
               .generate_state(1, dtype=np.uint32)[0])


def world(world_id):
    user_seed, uav_seed = seed(world_id, 1), seed(world_id, 2)
    u, v = np.random.RandomState(user_seed), np.random.RandomState(uav_seed)
    users = np.asarray([[u.uniform(0, 1000), u.uniform(0, 1000)] for _ in range(50)])
    fleet = np.asarray([[v.uniform(0, 1000), v.uniform(0, 1000), v.uniform(50, 150)]
                        for _ in range(8)])
    users.setflags(write=False)
    fleet.setflags(write=False)
    return MatchedWorld(world_id, user_seed, uav_seed, users, fleet)


def world_record(scene):
    result = asdict(scene)
    for field in ("user_positions", "uav_positions"):
        values = getattr(scene, field)
        result[field] = values.tolist()
        result[field + "_sha256_le_f64"] = hashlib.sha256(values.astype("<f8").tobytes()).hexdigest()
    result["runtime_seed"] = seed(scene.world_id, 3, 8)
    return result


def bound_worlds():
    payload = json.loads(WORLD_FILE.read_text())
    expected = {"address": [260930, 24], "worlds": [world_record(world(w)) for w in WORLD_IDS]}
    if payload != expected:
        raise ValueError("committed initial arrays differ from declared RNG addresses")
    return {w: world(w) for w in WORLD_IDS}


class RepositionS1(FleetS1):
    def __init__(self, scene, horizon=500):
        if scene.user_positions.shape != (50, 2) or scene.uav_positions.shape != (8, 3):
            raise ValueError("requires one static 50-user/N8 world")
        self.matched_world = scene
        self._matched_reset_ready = False
        UAVBaseStationEnv.__init__(self, n_uavs=8, n_users=50, max_steps=horizon,
            user_distribution="uniform", channel_model="free_space", seed=scene.user_seed,
            min_sinr=0, max_connections=10)
        self.enable_transmitter_mask = True
        self._matched_reset_ready = True
        self.reset()


def make_env(scene, horizon, runtime_seed):
    return CountAdapter(ParallelToArrayAdapter(RepositionS1(scene, horizon), seed=runtime_seed))
