"""25-step rollout bit-digest, per docs/project/HANDOFF_CPP_MIGRATION.md.

Hashes the raw bytes (no rounding) of sinr_matrix, connections,
user_serving_uav, uav_positions, user_positions, uav_battery_ratios each step.

Usage: python digest.py <repo_root> [--native] [--steps N] [--seed S]
"""
from __future__ import annotations

import argparse
import hashlib
import sys

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root")
    parser.add_argument("--native", action="store_true")
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--seed", type=int, default=20260725)
    args = parser.parse_args()

    sys.path.insert(0, args.repo_root)
    sys.path.insert(0, args.repo_root + "/scripts")
    import audit_d7_s_event_aligned as audit

    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(config, topology_seed=args.seed)
    env = audit.build_pinned_env(
        config, episode_seed=args.seed, coords=coords, coord_hash=coord_hash,
        energy_stage="S3", user_world_seed=args.seed)
    env.use_native_geometry = bool(args.native)

    digest = hashlib.sha256()
    for _ in range(args.steps):
        actions = {}
        for name in env.agents:
            space = env.action_space(name)
            actions[name] = np.zeros(space.shape, dtype=space.dtype)
        env.step(actions)
        for field in ("sinr_matrix", "connections", "user_serving_uav",
                      "uav_positions", "user_positions", "uav_battery_ratios"):
            digest.update(np.ascontiguousarray(np.asarray(getattr(env, field))).tobytes())
    print(digest.hexdigest())


if __name__ == "__main__":
    main()
