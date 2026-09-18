"""Capture or compare a short deterministic fingerprint of a legacy scenario route.

This is the non-regression instrument for the ``uav_service_restoration_v0`` work.  It
touches no legacy file: it drives ``ha_ctse_process.env_factory.make_env`` exactly as the
standalone trainer does, with a fixed seed and a fixed action sequence drawn from a local
``numpy.random.Generator``, and hashes what the adapter returns.

Determinism claim: the fingerprint is reproducible on the same machine, the same
interpreter and the same dependency set.  No cross-platform bitwise claim is made.

Usage::

    python scripts/uav_service_restoration/legacy_baseline_fingerprint.py capture \
        --scenario base --seed 12345 --steps 8 --output <path.json>
    python scripts/uav_service_restoration/legacy_baseline_fingerprint.py compare \
        --baseline <path.json>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _hash_array(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(contiguous.dtype).encode("ascii"))
    digest.update(str(contiguous.shape).encode("ascii"))
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _rng_state_hash(env: Any) -> str | None:
    """Hash the environment RNG state when the legacy environment exposes one."""

    for attribute in ("np_random", "rng", "_rng", "_np_random"):
        generator = getattr(env, attribute, None)
        if generator is None:
            continue
        try:
            state = generator.bit_generator.state
        except AttributeError:
            try:
                state = generator.get_state()
            except AttributeError:
                continue
        return hashlib.sha256(
            json.dumps(state, sort_keys=True, default=repr).encode("utf-8")
        ).hexdigest()
    return None


def capture(scenario: str, seed: int, steps: int) -> dict[str, Any]:
    from configs.config_1 import Config
    from ha_ctse_process.env_factory import EnvSpec, make_env

    config = Config()
    env = make_env(config, EnvSpec(scenario=scenario, seed=int(seed)))()
    observations, info = env.reset(seed=int(seed))

    record: dict[str, Any] = {
        "scenario": scenario,
        "seed": int(seed),
        "steps": int(steps),
        "obs_dim": int(env.obs_dim),
        "state_dim": int(env.state_dim),
        "action_dim": int(env.action_dim),
        "n_uavs": int(env.n_uavs),
        "reset_obs_sha256": _hash_array(observations),
        "reset_state_sha256": _hash_array(np.asarray(info["state"], dtype=np.float32)),
        "reset_rng_sha256": _rng_state_hash(env.env),
        "transitions": [],
    }

    action_rng = np.random.default_rng(int(seed) + 991)
    low = np.asarray(env.action_space.low, dtype=np.float64)
    high = np.asarray(env.action_space.high, dtype=np.float64)
    for _ in range(int(steps)):
        action = low + (high - low) * action_rng.random(size=low.shape)
        action = action.astype(np.float32)
        observations, reward, terminated, truncated, info = env.step(action)
        record["transitions"].append(
            {
                "action_sha256": _hash_array(action),
                "obs_sha256": _hash_array(observations),
                "next_state_sha256": _hash_array(
                    np.asarray(info["next_state"], dtype=np.float32)
                ),
                "reward": float(reward),
                "terminated": bool(terminated),
                "truncated": bool(truncated),
                "rng_sha256": _rng_state_hash(env.env),
            }
        )
        if terminated or truncated:
            break
    env.close()
    return record


def _compare(baseline: dict[str, Any], current: dict[str, Any]) -> list[str]:
    differences: list[str] = []
    scalar_keys = [
        "obs_dim",
        "state_dim",
        "action_dim",
        "n_uavs",
        "reset_obs_sha256",
        "reset_state_sha256",
        "reset_rng_sha256",
    ]
    for key in scalar_keys:
        if baseline.get(key) != current.get(key):
            differences.append(f"{key}: baseline={baseline.get(key)!r} current={current.get(key)!r}")
    base_transitions = baseline.get("transitions", [])
    current_transitions = current.get("transitions", [])
    if len(base_transitions) != len(current_transitions):
        differences.append(
            f"transition count: baseline={len(base_transitions)} current={len(current_transitions)}"
        )
    for index, (want, got) in enumerate(zip(base_transitions, current_transitions)):
        for key in sorted(set(want) | set(got)):
            if want.get(key) != got.get(key):
                differences.append(
                    f"transition[{index}].{key}: baseline={want.get(key)!r} current={got.get(key)!r}"
                )
    return differences


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture_parser = subparsers.add_parser("capture", help="Write a fingerprint JSON file")
    capture_parser.add_argument("--scenario", default="base")
    capture_parser.add_argument("--seed", type=int, default=12345)
    capture_parser.add_argument("--steps", type=int, default=8)
    capture_parser.add_argument("--output", required=True, type=Path)

    compare_parser = subparsers.add_parser("compare", help="Recompute and diff a fingerprint")
    compare_parser.add_argument("--baseline", required=True, type=Path)

    args = parser.parse_args(argv)

    if args.command == "capture":
        record = capture(args.scenario, args.seed, args.steps)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
        print(f"wrote {args.output}")
        return 0

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    current = capture(baseline["scenario"], int(baseline["seed"]), int(baseline["steps"]))
    differences = _compare(baseline, current)
    if differences:
        print("LEGACY_FINGERPRINT_DIFFERS")
        for line in differences:
            print(f"  {line}")
        return 1
    print("LEGACY_FINGERPRINT_IDENTICAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
