"""Fresh bound B04 worlds; unchanged native N8 fleet physics."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import numpy as np

from ..host import MatchedWorld
from ..b02.host import make_env

WORLD_IDS = tuple(range(29497000, 29497016))
WORLD_FILE = Path(__file__).with_name("worlds.json")
SEED_NAMESPACE = (260930, 97)


def seed(world_id, stream, *suffix):
    if type(world_id) is not int or world_id not in WORLD_IDS:
        raise ValueError("world outside the fixed B04 panel")
    return int(np.random.SeedSequence([*SEED_NAMESPACE, world_id, stream, *suffix])
               .generate_state(1, dtype=np.uint32)[0])


def world(world_id):
    user_seed, uav_seed = seed(world_id, 1), seed(world_id, 2)
    users_rng, fleet_rng = np.random.RandomState(user_seed), np.random.RandomState(uav_seed)
    users = np.asarray([[users_rng.uniform(0, 1000), users_rng.uniform(0, 1000)]
                        for _ in range(50)])
    fleet = np.asarray([[fleet_rng.uniform(0, 1000), fleet_rng.uniform(0, 1000),
                         fleet_rng.uniform(50, 150)] for _ in range(8)])
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
    scenes = {world_id: world(world_id) for world_id in WORLD_IDS}
    expected = {"address": list(SEED_NAMESPACE),
                "worlds": [world_record(scenes[world_id]) for world_id in WORLD_IDS]}
    if payload != expected:
        raise ValueError("committed initial arrays differ from declared RNG addresses")
    return scenes
