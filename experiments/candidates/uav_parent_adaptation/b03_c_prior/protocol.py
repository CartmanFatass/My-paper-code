"""Frozen allocation and compact artifact helpers; no scientific CLI variants."""

import hashlib
import json
from pathlib import Path
import resource
import time

MASTERS = (303031, 303032, 303033)
TRAIN_EPISODES = 512
EVAL_WORLDS = 32
HORIZON = 256
HOLD = 4
ARMS = ("C", "I", "Lg", "Ls")
OBJECT = "UAV-PARENT-ADAPTATION-B03-C-PRIOR"


def train_world(block, episode):
    return 30310000 + 1000 * block + episode


def eval_world(block, world):
    return 30300000 + 100 * block + world


def expected_counts():
    return dict(fits=3, train_episodes=1536, eval_episodes=384,
                native_step_calls=491520, team_steps=491520,
                train_team_steps=393216, eval_team_steps=98304,
                explicit_resets=1920, ppo_rollouts=768,
                actor_optimizer_steps=3072, critic_optimizer_steps=3072,
                train_actor_rows=491520, train_critic_rows=98304,
                eval_actor_rows=92160, identity_shadow_rows=30720,
                actor_replay_rows=1966080, critic_replay_rows=393216,
                c_ingests=2457600, c_decisions=614400,
                c_trajectories=16588800, c_model_ticks=66355200)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def identity(path, base=None):
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return dict(path=str(path.relative_to(base) if base is not None else path),
                bytes=path.stat().st_size, sha256=h.hexdigest())


def clock():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return time.perf_counter(), usage.ru_utime + usage.ru_stime


def elapsed(start):
    now = clock()
    return dict(wall_seconds=now[0] - start[0], cpu_seconds=now[1] - start[1],
                process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
