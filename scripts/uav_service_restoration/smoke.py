"""Forward-only smoke run of ``uav_service_restoration_v0``.  No optimizer, no gradients.

This is the command that needs no download: point it at ``smoke_fixture.json``, which is
self-contained and explicitly NOT real data.  It steps the environment through the shared
adapter route, checks the PettingZoo Parallel API, and reports observation and state
dimensions, scheduler status counts, timing, and the episode summary.

It performs no training fit and takes no optimizer step.  ``--config`` is mandatory: a
fixture is never a hidden default.

Usage::

    python scripts/uav_service_restoration/smoke.py \
        --config configs/uav_service_restoration/smoke_fixture.json --steps 32
"""

from __future__ import annotations

import argparse
import contextlib
import io
import time
from collections import Counter
from typing import Any

import numpy as np

from _cli import (  # noqa: E402
    EXIT_OK,
    CliError,
    emit,
    require_existing_file,
    run,
)

from envs.uav_service_restoration.adapter import (  # noqa: E402
    make_array_env,
    make_parallel_env,
)
from envs.uav_service_restoration.config import load_config  # noqa: E402


def _api_test(config: Any, dataset_root: str | None) -> dict[str, Any]:
    """Run PettingZoo's own Parallel API test on a fresh environment."""

    try:
        from pettingzoo.test import parallel_api_test
    except ImportError as error:  # pragma: no cover - dependency is present in this env
        return {"performed": False, "reason": f"pettingzoo.test unavailable: {error}"}
    env = make_parallel_env(config, dataset_root=dataset_root, seed=int(config.seed))
    cycles = max(1, int(round(config.episode.duration_s / config.episode.decision_dt_s)))
    # parallel_api_test prints to stdout; capture it so this tool's stdout stays valid JSON.
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        parallel_api_test(env, num_cycles=cycles)
    return {
        "performed": True,
        "num_cycles": cycles,
        "output": captured.getvalue().strip().splitlines(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smoke.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config", required=True, help="environment configuration (no default)"
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="prepared cache root, overriding the configuration's dataset_root",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help="decision steps to take (default: one full episode)",
    )
    parser.add_argument("--seed", type=int, default=None, help="episode seed")
    parser.add_argument(
        "--policy",
        choices=("zero", "random"),
        default="zero",
        help="action source for the smoke run; both are non-learning (default: zero)",
    )
    parser.add_argument(
        "--skip-api-test",
        action="store_true",
        help="skip PettingZoo's parallel_api_test (which re-runs a full episode)",
    )
    parser.add_argument("--output", default=None, help="also write the report here")
    parser.add_argument(
        "--force", action="store_true", help="overwrite an existing --output file"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.steps is not None and args.steps <= 0:
        raise CliError("--steps must be positive", 2)

    config_path = require_existing_file(args.config, "environment configuration")
    config = load_config(str(config_path))
    if config.source.kind != "synthetic_fixture" and args.dataset is None and not config.source.dataset_root:
        raise CliError(
            f"source.kind={config.source.kind!r} needs a prepared cache: pass --dataset "
            "or set source.dataset_root. There is no synthetic fallback.",
            2,
        )

    seed = int(config.seed if args.seed is None else args.seed)
    adapter = make_array_env(config, dataset_root=args.dataset, seed=seed)
    env = adapter.env  # the shared adapter keeps the Parallel environment on .env

    started = time.perf_counter()
    observations, info = adapter.reset(seed=seed)
    n_steps = int(config.episode.duration_s / config.episode.decision_dt_s)
    if args.steps is not None:
        n_steps = min(n_steps, int(args.steps))

    rng = np.random.default_rng(np.random.SeedSequence(seed))
    statuses: Counter[str] = Counter()
    rewards: list[float] = []
    taken = 0
    terminated = truncated = False
    for _ in range(n_steps):
        if args.policy == "random":
            actions = rng.uniform(-1.0, 1.0, size=observations.shape[0] * 3).reshape(-1, 3)
            actions = actions.astype(np.float32)
        else:
            actions = np.zeros((observations.shape[0], 3), dtype=np.float32)
        observations, reward, terminated, truncated, info = adapter.step(actions)
        rewards.append(float(reward))
        taken += 1
        # The scheduler status is an execution fact, not policy information, so it is
        # read from the diagnostic channel rather than from the observation.
        status = env.get_privileged_diagnostics().get("scheduler_status")
        if status is not None:
            statuses[str(getattr(status, "value", status))] += 1
        if terminated or truncated:
            break
    elapsed = time.perf_counter() - started

    summary = env.episode_summary()
    report: dict[str, Any] = {
        "tool": "smoke",
        "config": str(config_path),
        "environment_id": config.environment_id,
        "schema_version": config.schema_version,
        "training_fits_performed": 0,
        "optimizer_updates": 0,
        "policy": args.policy,
        "seed": seed,
        "shapes": {
            "n_agents": int(observations.shape[0]),
            "obs_dim": int(adapter.obs_dim),
            "state_dim": int(adapter.state_dim),
            "action_dim": 3,
            "n_demand_points": int(env.demand_layout.positions_m.shape[0]),
        },
        "stepping": {
            "decision_steps_taken": taken,
            "decision_steps_in_episode": int(
                config.episode.duration_s / config.episode.decision_dt_s
            ),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "physical_time_s": float(env.physical_time_s),
            "wall_clock_s": float(elapsed),
            "wall_clock_s_per_decision_step": float(elapsed / taken) if taken else None,
        },
        "reward": {
            "sum": float(np.sum(rewards)) if rewards else 0.0,
            "mean": float(np.mean(rewards)) if rewards else None,
            "min": float(np.min(rewards)) if rewards else None,
            "max": float(np.max(rewards)) if rewards else None,
        },
        "scheduler_status_counts": dict(statuses),
        "episode_summary": summary,
        "data_status": (
            "REAL_ACTIVITY_DATA"
            if env.get_privileged_diagnostics()["source_metadata"]["is_real_activity_data"]
            else "NOT_REAL_DATA"
        ),
        "calibration_summary": config.calibration_summary(),
    }
    report["api_test"] = (
        {"performed": False, "reason": "--skip-api-test"}
        if args.skip_api_test
        else _api_test(config, args.dataset)
    )

    emit(report, args.output, force=bool(args.force))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(run(main))
