"""The selected fresh initial arrays; generation is not a host rollout."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

import numpy as np

WORLD_IDS = tuple(range(29524000, 29524016))
AUDIT_WORLD = 29524900
ALL_WORLD_IDS = (AUDIT_WORLD, *WORLD_IDS)
ADDRESS = (261003, 74)
WORLD_FILE = Path(__file__).with_name("worlds.json")


@dataclass(frozen=True)
class World:
    world_id: int
    user_seed: int
    uav_seed: int
    user_positions: np.ndarray
    uav_positions: np.ndarray


def seed(world_id, stream, *suffix):
    if type(world_id) is not int or world_id not in ALL_WORLD_IDS:
        raise ValueError("world outside the fixed rolling purchase")
    return int(np.random.SeedSequence([*ADDRESS, world_id, stream, *suffix])
               .generate_state(1, dtype=np.uint32)[0])


def world(world_id):
    user_seed, uav_seed = seed(world_id, 1), seed(world_id, 2)
    u, v = np.random.RandomState(user_seed), np.random.RandomState(uav_seed)
    users = np.asarray([[u.uniform(0, 1000), u.uniform(0, 1000)] for _ in range(50)])
    fleet = np.asarray([[v.uniform(0, 1000), v.uniform(0, 1000), v.uniform(50, 150)]
                        for _ in range(8)])
    users.setflags(write=False)
    fleet.setflags(write=False)
    return World(world_id, user_seed, uav_seed, users, fleet)


def world_record(scene):
    row = asdict(scene)
    for field in ("user_positions", "uav_positions"):
        value = getattr(scene, field)
        row[field] = value.tolist()
        row[field + "_sha256_le_f64"] = hashlib.sha256(value.astype("<f8").tobytes()).hexdigest()
    row["runtime_seed"] = seed(scene.world_id, 3, 8)
    return row


def generated_inputs():
    return {"address": list(ADDRESS), "worlds": [world_record(world(w)) for w in ALL_WORLD_IDS]}


def bound_worlds():
    scenes = {w: world(w) for w in ALL_WORLD_IDS}
    expected = {"address": list(ADDRESS), "worlds": [world_record(scenes[w]) for w in ALL_WORLD_IDS]}
    if json.loads(WORLD_FILE.read_text()) != expected:
        raise ValueError("committed arrays differ from the fixed RNG addresses")
    return scenes
