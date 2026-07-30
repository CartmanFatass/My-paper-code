"""Same-process interleaved benchmark: native off vs on vs null control.

Methodology per HANDOFF_CPP_MIGRATION.md: the box has ~3x thermal swing across
measurement blocks, so cross-process or blocked measurement is unusable. Three
arms run interleaved inside each block with the order flipped per block; the
null arm is a second flag-off env, so its ratio against the first is the noise
floor any claimed speedup must clear.

Usage: python bench_paired.py <repo_root> [--blocks N] [--steps-per-block N]
"""
from __future__ import annotations

import argparse
import sys
import time

import numpy as np


def build(repo_root: str, *, native: bool, seed: int = 20260725):
    import audit_d7_s_event_aligned as audit
    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(config, topology_seed=seed)
    env = audit.build_pinned_env(
        config, episode_seed=seed, coords=coords, coord_hash=coord_hash,
        energy_stage="S3", user_world_seed=seed)
    env.use_native_geometry = bool(native)
    return env


def zero_actions(env):
    actions = {}
    for name in env.agents:
        space = env.action_space(name)
        actions[name] = np.zeros(space.shape, dtype=space.dtype)
    return actions


def run_block(env, steps: int) -> float:
    start = time.perf_counter()
    for _ in range(steps):
        env.step(zero_actions(env))
    return time.perf_counter() - start


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root")
    parser.add_argument("--blocks", type=int, default=8)
    parser.add_argument("--steps-per-block", type=int, default=10)
    args = parser.parse_args()

    sys.path.insert(0, args.repo_root)
    sys.path.insert(0, args.repo_root + "/scripts")

    arms = {
        "off": build(args.repo_root, native=False),
        "on": build(args.repo_root, native=True),
        "null": build(args.repo_root, native=False),
    }
    order = ["off", "on", "null"]
    totals = {k: 0.0 for k in arms}
    # warmup (JIT load, caches, branch predictors)
    for k in order:
        run_block(arms[k], 3)
    for block in range(args.blocks):
        seq = order if block % 2 == 0 else list(reversed(order))
        for k in seq:
            totals[k] += run_block(arms[k], args.steps_per_block)

    n = args.blocks * args.steps_per_block
    for k in order:
        print(f"{k:5s} {totals[k]:.3f}s total  {totals[k]/n*1000:.2f} ms/step")
    print(f"speedup on vs off : {totals['off']/totals['on']:.3f}x")
    print(f"null noise (off/null): {totals['off']/totals['null']:.3f}x")


if __name__ == "__main__":
    main()
