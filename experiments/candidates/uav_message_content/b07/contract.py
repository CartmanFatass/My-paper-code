"""Fixed scientific dimensions and compact evidence helpers."""

import hashlib
import json
import os
from pathlib import Path

SEEDS = (19811, 19812, 19813)
METRICS = ("unit", "inverse_sd")
PROGRAMS = ("fullD", "fullB", "O1", "O2", "O3", "L1", "L2", "L3")
HORIZON, AGENTS, USERS, CENTERS = 256, 5, 50, 256
FIELDS = (0, 1, 2, 3, 4, 6)
D_SHA = "1a0de628a6c324a5cd0c69f4857b37b4bc1f47c51dc80d2a9a233e7ee7f69840"
B_SHA = "34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2"
DATA_SHA = "a0eaac8dea65434625b9a6778b7b7f147b1698de68a137b622b93a2f3fb04311"
SUMMARY_SHA = "c642411146305d20716bec3f9fba510e8021adf9076876079799141b637e2211"
EXPECTED = dict(fits_started=12, fits_completed=12, adam_updates=720,
                fit_actor_rows=3686400, dev_actor_rows=122880, binding_actor_rows=40960,
                native_actor_rows=327680, reader_actor_rows=327680,
                native_steps=65536, native_episodes=256, reader_steps=65536,
                motion_vectors=327680, packets=65536, beacon_bytes=131072,
                packet_bytes=573440, nearest_center_comparisons=475004928,
                policy_updates=0, critic_calls=0, gpu_calls=0, new_teacher_labels=0)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=sha256(path), bytes=path.stat().st_size)


def verify_artifact(record):
    path = Path(record["path"])
    require(path.is_absolute() and not path.is_symlink() and path.is_file(), "artifact path invalid")
    require(path.stat().st_size == record["bytes"] and sha256(path) == record["sha256"],
            f"artifact identity mismatch: {path}")
    return path


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def increment(counts, key, value=1):
    counts[key] = counts.get(key, 0) + int(value)
