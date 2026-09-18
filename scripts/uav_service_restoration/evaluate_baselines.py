"""Evaluate the non-learning diagnostic controllers with the counterfactual evaluator.

Forward-only: every rollout runs the environment with a fixed rule and takes no optimizer
step.  For each episode the evaluator recomputes two policy-independent references over the
identical exogenous world - the healthy no-UAV trace and the failed no-UAV trace - derives
the affected demand set from their gap, and reports a recovery verdict with its censoring
reason.

What the numbers are for: they characterise the *environment*, showing that the scenario
has headroom and that the evaluator separates a controller that moves toward live backhaul
from one that does not.  These controllers are not tuned and are not a research baseline.

Usage::

    python scripts/uav_service_restoration/evaluate_baselines.py \
        --config configs/uav_service_restoration/smoke_fixture.json --episodes 3
    python scripts/uav_service_restoration/evaluate_baselines.py \
        --config configs/uav_service_restoration/milan_site_outage.json \
        --dataset <cache_dir> --episodes-file <heldout_episode_ids.json>
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any

import numpy as np

from _cli import (  # noqa: E402
    EXIT_OK,
    CliError,
    emit,
    require_existing_file,
    run,
)

from envs.uav_service_restoration.adapter import make_parallel_env  # noqa: E402
from envs.uav_service_restoration.baselines import (  # noqa: E402
    CONTROLLER_NAMES,
    build_controller,
)
from envs.uav_service_restoration.config import load_config  # noqa: E402
from envs.uav_service_restoration.evaluation import rollout_controller  # noqa: E402


def _episode_seeds(args: argparse.Namespace) -> tuple[list[int], str]:
    """Resolve the episode seed list, from a file when one is given."""

    if args.episodes_file is not None:
        path = require_existing_file(args.episodes_file, "episode list")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            values = payload.get("episode_seeds", payload.get("seeds"))
            if values is None:
                raise CliError(
                    f"{path} must hold a list, or an object with 'episode_seeds'", 2
                )
        else:
            values = payload
        if not isinstance(values, list) or not values:
            raise CliError(f"{path} holds no episode seeds", 2)
        try:
            seeds = [int(value) for value in values]
        except (TypeError, ValueError) as error:
            raise CliError(f"{path} holds a non-integer episode seed: {error}", 2) from error
        return seeds, f"episodes-file:{path}"
    base = int(args.seed)
    return [base + index for index in range(int(args.episodes))], f"seed:{base}+index"


def _aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-controller summary across episodes.

    Recovery times are reported with their censored count, never averaged over censored
    episodes as if they were zero.
    """

    satisfaction = np.asarray(
        [record["references"]["controller_satisfaction"] for record in records], dtype=np.float64
    )
    restored = np.asarray(
        [record["recovery"]["fraction_of_lost_service_restored"] for record in records],
        dtype=np.float64,
    )
    times = [
        record["recovery"]["time_to_recovery_s"]
        for record in records
        if record["recovery"].get("time_to_recovery_s") is not None
    ]
    censored = [
        record["recovery"].get("censoring_reason")
        for record in records
        if record["recovery"].get("censored")
    ]
    not_applicable = sum(1 for record in records if not record["recovery"].get("applicable"))
    return {
        "n_episodes": len(records),
        "controller_satisfaction_mean": float(np.nanmean(satisfaction)) if satisfaction.size else None,
        "controller_satisfaction_min": float(np.nanmin(satisfaction)) if satisfaction.size else None,
        "controller_satisfaction_max": float(np.nanmax(satisfaction)) if satisfaction.size else None,
        "fraction_of_lost_service_restored_mean": (
            float(np.nanmean(restored)) if restored.size else None
        ),
        "n_recovered": len(times),
        "time_to_recovery_s_mean_over_recovered": (
            float(np.mean(times)) if times else None
        ),
        "n_censored": len(censored),
        "censoring_reasons": {
            reason: censored.count(reason) for reason in sorted(set(censored) - {None})
        },
        "n_not_applicable": not_applicable,
        "aggregation_rule": (
            "means are over episodes; a censored episode contributes no recovery time and "
            "is never counted as a recovery of zero seconds"
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evaluate_baselines.py",
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
        "--controllers",
        nargs="+",
        default=list(CONTROLLER_NAMES),
        choices=list(CONTROLLER_NAMES),
        help="which diagnostic controllers to run (default: all)",
    )
    parser.add_argument(
        "--episodes", type=int, default=1, help="number of episodes per controller"
    )
    parser.add_argument(
        "--episodes-file",
        default=None,
        help=(
            "JSON list of episode seeds, or an object with 'episode_seeds'; overrides "
            "--episodes and --seed so a held-out set is reproducible"
        ),
    )
    parser.add_argument("--seed", type=int, default=0, help="first episode seed")
    parser.add_argument(
        "--controller-seed",
        type=int,
        default=0,
        help="seed for the stochastic controllers (independent of the episode seed)",
    )
    parser.add_argument(
        "--per-episode",
        action="store_true",
        help="include the full per-episode records, not only the aggregate",
    )
    parser.add_argument("--output", default=None, help="also write the report here")
    parser.add_argument(
        "--force", action="store_true", help="overwrite an existing --output file"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.episodes <= 0:
        raise CliError("--episodes must be positive", 2)

    config_path = require_existing_file(args.config, "environment configuration")
    config = load_config(str(config_path))
    if (
        config.source.kind != "synthetic_fixture"
        and args.dataset is None
        and not config.source.dataset_root
    ):
        raise CliError(
            f"source.kind={config.source.kind!r} needs a prepared cache: pass --dataset "
            "or set source.dataset_root. There is no synthetic fallback.",
            2,
        )

    seeds, seed_provenance = _episode_seeds(args)
    started = time.perf_counter()

    results: dict[str, Any] = {}
    per_episode: dict[str, list[dict[str, Any]]] = {}
    data_status: str | None = None
    for name in args.controllers:
        records: list[dict[str, Any]] = []
        for seed in seeds:
            env = make_parallel_env(config, dataset_root=args.dataset, seed=seed)
            controller = build_controller(name, config, seed=int(args.controller_seed))
            record = rollout_controller(env, controller, seed=seed)
            record["episode_seed"] = int(seed)
            records.append(record)
            status = (
                "REAL_ACTIVITY_DATA"
                if record["episode"]["is_real_activity_data"]
                else "NOT_REAL_DATA"
            )
            if data_status is not None and status != data_status:
                raise CliError("episodes mixed real and non-real data provenance", 4)
            data_status = status
        results[name] = _aggregate(records)
        per_episode[name] = records
    elapsed = time.perf_counter() - started

    report: dict[str, Any] = {
        "tool": "evaluate_baselines",
        "config": str(config_path),
        "environment_id": config.environment_id,
        "training_fits_performed": 0,
        "optimizer_updates": 0,
        "information_condition": config.observations.mode,
        "data_status": data_status,
        "episode_seeds": seeds,
        "episode_seed_provenance": seed_provenance,
        "controller_seed": int(args.controller_seed),
        "recovery_definition": {
            "recovery_fraction_rho": config.evaluation.recovery_fraction_rho,
            "recovery_sustain_s": config.evaluation.recovery_sustain_s,
            "affected_set_rule": (
                "demand points whose delivered volume is strictly lower in the failed "
                "no-UAV reference than in the healthy no-UAV reference; independent of "
                "the evaluated controller"
            ),
        },
        "controllers": results,
        "wall_clock_s": float(elapsed),
        "interpretation_note": (
            "These controllers characterise the environment and the evaluator. They are "
            "untuned rules, not a research baseline, and a single configuration is not "
            "evidence about any algorithm."
        ),
    }
    if args.per_episode:
        report["per_episode"] = per_episode

    emit(report, args.output, force=bool(args.force))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(run(main))
