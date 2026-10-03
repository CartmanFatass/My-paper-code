"""Fixed study identities and byte-bound inputs; no import-time effects."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform

DIRECTION = "typed_joint_skill_decision"
OBJECT_ID = "typed_two_stage_value_b08"
TAG = "b08_two_stage_value_a01"
SEED = 26100388
NAMESPACE = (261003, 88)
TRAIN_IDS = tuple(range(108801000, 108801128))
FINAL_IDS = tuple(range(108802000, 108802032))
FIT_LABELS = (108803001, 108803002, 108803003)
ARMS = ("G2", "A2", "K2-C", "K2-S", "L2-s0", "L2-s1", "L2-s2")
BOOTSTRAP_SEED = 108809991
BOOTSTRAP_REPLICATES = 10000
CHECKPOINTS = tuple(range(0, 2049, 256))
CPU_LIMIT_SECONDS = 52 * 3600
WALL_LIMIT_SECONDS = 72 * 3600
DISK_LIMIT_BYTES = 16 * 1024**3
CEILINGS = {
    "native_transitions": 120620,
    "native_snapshots": 120979,
    "new_fits": 3,
    "optimizer_updates": 6144,
    "worker_model_ticks": 7170440,
    "worker_logical_requests": 1936468853,
    "stationary_banks": 2373,
    "stationary_candidate_rows": 1661100,
    "candidate_transit_ticks": 66444000,
    "training_menu_presentations": 98304,
    "training_candidate_presentations": 786432,
    "training_pair_presentations": 2752512,
    "recorded_forward_menus": 3555,
    "functional_reader_forward_menus": 7110,
}
REPO = Path(__file__).resolve().parents[4]
WORLD_PATH = Path(__file__).with_name("worlds.json")
INPUT_PATH = Path("docs/research/candidates/typed_joint_skill_decision/B08_INPUT.json")
OWN_NAMES = ("__init__.py", "contract.py", "evidence.py", "planner.py", "features.py",
             "model.py", "functional.py", "learning.py", "execution.py", "reader.py", "run.py", "worlds.json")
OWN_PATHS = tuple(f"experiments/candidates/{DIRECTION}/b08_two_stage_value/{name}" for name in OWN_NAMES)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def binding(path, base=REPO):
    path, base = Path(path), Path(base)
    return {"path": path.relative_to(base).as_posix(), "bytes": path.stat().st_size,
            "sha256": sha256(path)}


def addressed_seed(label, stream, *suffix):
    import numpy as np
    return int(np.random.SeedSequence([*NAMESPACE, int(label), int(stream), *suffix])
               .generate_state(1, dtype=np.uint32)[0])


def generate_world_input():
    """Pure, prospective input generation, invoked once before publication."""
    import numpy as np
    records = []
    for world_id in (*TRAIN_IDS, *FINAL_IDS):
        us, vs = addressed_seed(world_id, 1), addressed_seed(world_id, 2)
        ur, vr = np.random.RandomState(us), np.random.RandomState(vs)
        users = np.asarray([[ur.uniform(0, 1000), ur.uniform(0, 1000)] for _ in range(50)], dtype="<f8")
        fleet = np.asarray([[vr.uniform(0, 1000), vr.uniform(0, 1000), vr.uniform(50, 150)]
                            for _ in range(8)], dtype="<f8")
        records.append({"world_id": world_id, "user_seed": us, "uav_seed": vs,
                        "runtime_seed": addressed_seed(world_id, 3, 8),
                        "user_positions": users.tolist(), "uav_positions": fleet.tolist(),
                        "user_sha256": hashlib.sha256(users.tobytes()).hexdigest(),
                        "uav_sha256": hashlib.sha256(fleet.tobytes()).hexdigest()})
    return {"namespace": list(NAMESPACE), "worlds": records,
            "fits": [{"fit_id": i, "label": label,
                      "init_seed": addressed_seed(label, 10),
                      "permutation_seed": addressed_seed(label, 11)}
                     for i, label in enumerate(FIT_LABELS)]}


def load_world_input():
    """Read committed arrays; never regenerate fresh worlds inside the learner."""
    import numpy as np
    value = json.loads(WORLD_PATH.read_text())
    if value["namespace"] != list(NAMESPACE) or [r["world_id"] for r in value["worlds"]] != [*TRAIN_IDS, *FINAL_IDS]:
        raise ValueError("bound world namespace/order differs")
    for row in value["worlds"]:
        for name, shape, hash_name in (("user_positions", (50, 2), "user_sha256"),
                                      ("uav_positions", (8, 3), "uav_sha256")):
            a = np.asarray(row[name], dtype="<f8")
            if a.shape != shape or not np.isfinite(a).all() or hashlib.sha256(a.tobytes()).hexdigest() != row[hash_name]:
                raise ValueError("bound initial array differs")
        if any(type(row[key]) is not int for key in ("world_id", "user_seed", "uav_seed", "runtime_seed")):
            raise ValueError("bound RNG identity is not an integer")
        if (row["user_seed"] != addressed_seed(row["world_id"], 1)
                or row["uav_seed"] != addressed_seed(row["world_id"], 2)
                or row["runtime_seed"] != addressed_seed(row["world_id"], 3, 8)):
            raise ValueError("bound world RNG address differs")
    if [r["fit_id"] for r in value["fits"]] != [0, 1, 2] or [r["label"] for r in value["fits"]] != list(FIT_LABELS):
        raise ValueError("fixed fit order/labels differ")
    for fit in value["fits"]:
        if fit["init_seed"] != addressed_seed(fit["label"], 10) or fit["permutation_seed"] != addressed_seed(fit["label"], 11):
            raise ValueError("bound fit RNG address differs")
    return value


def scene(record):
    import numpy as np
    from experiments.candidates.uav_fleet_transmission.host import MatchedWorld
    users = np.asarray(record["user_positions"], dtype=np.float64)
    fleet = np.asarray(record["uav_positions"], dtype=np.float64)
    users.setflags(write=False)
    fleet.setflags(write=False)
    return MatchedWorld(record["world_id"], record["user_seed"], record["uav_seed"], users, fleet)


def runtime():
    import numpy as np
    import torch
    return {"python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
            "torch_config_sha256": hashlib.sha256(torch.__config__.show().encode()).hexdigest(),
            "device": "cpu", "numeric_threads": 1}


def fixed_scope():
    return {"object_id": OBJECT_ID, "direction": DIRECTION, "seed": SEED,
            "namespace": list(NAMESPACE), "train_ids": list(TRAIN_IDS), "final_ids": list(FINAL_IDS),
            "arms": list(ARMS), "audits": [{"arm": arm, "world_id": FINAL_IDS[0]} for arm in ARMS],
            "checkpoints": list(CHECKPOINTS), "ceilings": CEILINGS,
            "limits": {"cpu_seconds": CPU_LIMIT_SECONDS, "wall_seconds": WALL_LIMIT_SECONDS,
                       "normal_allocated_bytes": DISK_LIMIT_BYTES},
            "host": {"n": 8, "users": 50, "horizon": 500, "cadence": 10, "opportunities": [40, 120]},
            "learning": {"parameter_count": 10272, "fits": 3, "worlds": 128, "epochs": 256,
                         "batch_menus": 16, "updates": 2048, "loss": "uniform_world_all_pair_difference",
                         "target_scale": 100.0 / 460.0, "optimizer": "Adam", "lr": .001,
                         "betas": [.9, .999], "eps": 1e-8, "weight_decay": 0.0, "gradient_clip": 1.0},
            "bootstrap": {"seed": BOOTSTRAP_SEED, "replicates": BOOTSTRAP_REPLICATES},
            "failure_rule": "first formal request/admission/worker/reader failure stops; no automatic retry"}


def validate_input(path, expected_sha):
    path = Path(path)
    if sha256(path) != expected_sha:
        raise ValueError("input-manifest hash mismatch")
    value = json.loads(path.read_text())
    if value["scope"] != fixed_scope() or value["runtime"] != runtime():
        raise ValueError("fixed scope or bound numerical runtime differs")
    if not set(OWN_PATHS).issubset(value["sources"]):
        raise ValueError("own executable/source binding is incomplete")
    if any(value["sources"].get(key) != expected for key, expected in value["frozen_sources"].items()):
        raise ValueError("an inherited frozen source binding changed")
    for relative, expected in value["sources"].items():
        target = (REPO / relative).resolve()
        if not target.is_relative_to(REPO) or binding(target) != dict(expected, path=relative):
            raise ValueError(f"source/input bytes differ: {relative}")
    if value["world_input"] != binding(WORLD_PATH):
        raise ValueError("world-input binding differs")
    load_world_input()
    return value
