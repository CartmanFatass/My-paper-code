"""Validate a prepared activity cache and report its provenance and quality.

The checks are the ones that decide whether the cache may be used as evidence:

* the completion marker exists and its content hash matches the arrays,
* every declared per-file SHA-256 still matches on disk,
* the splits are complete UTC dates and do not overlap,
* the reference scale was fitted on the training split only, and is positive,
* the cache states, permanently, whether it holds real activity data.

The report's ``verdict`` is ``VALID`` only when all of those hold.  It separately reports
``is_real_activity_data``: a structurally valid fixture-derived cache is still not real
data, and the report says so rather than letting the distinction be lost downstream.

Usage::

    python scripts/uav_service_restoration/validate_dataset.py --dataset <cache_dir>
    python scripts/uav_service_restoration/validate_dataset.py --dataset <cache_dir> \
        --config configs/uav_service_restoration/milan_site_outage.json --sample-episodes 3
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from _cli import (  # noqa: E402
    EXIT_DATA,
    EXIT_OK,
    CliError,
    emit,
    require_existing_dir,
    require_existing_file,
    run,
)

from envs.uav_service_restoration.config import SourceConfig, load_config  # noqa: E402
from envs.uav_service_restoration.demand import (  # noqa: E402
    COMPLETION_MARKER,
    PREPARED_SCHEMA_VERSION,
    DemandDataError,
    PreparedDatasetDemandSource,
)


def _split_report(root: Path) -> dict[str, Any]:
    payload = json.loads((root / "splits.json").read_text(encoding="utf-8"))
    splits = payload["splits"]
    dates = {name: list(values) for name, values in splits.items()}
    overlaps: dict[str, list[str]] = {}
    names = sorted(dates)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            shared = sorted(set(dates[left]) & set(dates[right]))
            if shared:
                overlaps[f"{left}|{right}"] = shared
    return {
        "rule": payload.get("rule"),
        "n_dates": {name: len(values) for name, values in dates.items()},
        "dates": dates,
        "overlaps": overlaps,
        "disjoint": not overlaps,
        "train_is_non_empty": bool(dates.get("train")),
    }


def _sample_episodes(
    source: PreparedDatasetDemandSource,
    split: str,
    duration_s: float,
    count: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(np.random.SeedSequence(seed))
    sampled: list[dict[str, Any]] = []
    for _ in range(count):
        episode = source.sample_episode(split, rng, duration_s=duration_s)
        frame = source.read_interval(episode, episode.start_utc_ms)
        sampled.append(
            {
                "episode_id": episode.episode_id,
                "split": episode.split,
                "start_utc_ms": int(episode.start_utc_ms),
                "end_utc_ms": int(episode.end_utc_ms),
                "first_interval_offered_mbps_total": float(frame.demand_mbps.sum()),
                "first_interval_observed_fraction": float(frame.observed_mask.mean()),
            }
        )
    return {"split": split, "duration_s": float(duration_s), "episodes": sampled}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate_dataset.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dataset", required=True, help="the prepared cache directory")
    parser.add_argument(
        "--config",
        default=None,
        help=(
            "an environment configuration to check the cache against; without it the "
            "cache is validated structurally only"
        ),
    )
    parser.add_argument(
        "--sample-episodes",
        type=int,
        default=0,
        help="draw this many episodes from --config's split as an end-to-end check",
    )
    parser.add_argument("--seed", type=int, default=0, help="episode sampling seed")
    parser.add_argument(
        "--skip-hash-verification",
        action="store_true",
        help="skip per-file SHA-256 verification (fast, and a weaker verdict)",
    )
    parser.add_argument("--output", default=None, help="also write the report here")
    parser.add_argument(
        "--force", action="store_true", help="overwrite an existing --output file"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.sample_episodes < 0:
        raise CliError("--sample-episodes must not be negative", 2)
    if args.sample_episodes and args.config is None:
        raise CliError("--sample-episodes requires --config, which names the split", 2)

    root = require_existing_dir(args.dataset, "prepared dataset")
    for required in (COMPLETION_MARKER, "metadata.json", "splits.json", "quality_report.json"):
        if not (root / required).is_file():
            raise CliError(
                f"{root} is not a complete prepared cache: {required} is missing. "
                "Re-run prepare_milan.py into a new directory.",
                EXIT_DATA,
            )

    # Structural validation needs a source configuration but no simulation scale: the
    # placeholder below is never used to produce demand, only to open the cache.
    source_config = SourceConfig(
        kind="prepared_dataset", demand_scale_mbps=1.0, dataset_root=str(root)
    )
    env_config = None
    if args.config is not None:
        config_path = require_existing_file(args.config, "environment configuration")
        env_config = load_config(str(config_path))
        source_config = env_config.source

    verify = not bool(args.skip_hash_verification)
    try:
        source = PreparedDatasetDemandSource(
            source_config, dataset_root=str(root), verify_hashes=verify
        )
    except DemandDataError as error:
        emit(
            {
                "tool": "validate_dataset",
                "dataset_root": str(root),
                "verdict": "INVALID",
                "reason": str(error),
                "hash_verification_performed": verify,
            },
            args.output,
            force=bool(args.force),
        )
        return EXIT_DATA

    metadata = source.metadata()
    splits = _split_report(root)
    quality = source.quality_report()
    marker = json.loads((root / COMPLETION_MARKER).read_text(encoding="utf-8"))

    checks = {
        "completion_marker_present": True,
        "schema_version_matches_reader": (
            str(marker.get("schema_version")) == PREPARED_SCHEMA_VERSION
        ),
        "content_hash_matches_marker": str(marker.get("content_sha256")) == metadata.dataset_hash,
        "per_file_hashes_verified": verify,
        "splits_disjoint": splits["disjoint"],
        "train_split_non_empty": splits["train_is_non_empty"],
        "reference_scale_positive": float(source.reference_scale()) > 0.0,
    }
    verdict = "VALID" if all(checks.values()) else "INVALID"

    report: dict[str, Any] = {
        "tool": "validate_dataset",
        "dataset_root": str(root),
        "verdict": verdict,
        "checks": checks,
        "is_real_activity_data": bool(metadata.is_real_activity_data),
        "data_status": (
            "REAL_ACTIVITY_DATA" if metadata.is_real_activity_data else "NOT_REAL_DATA"
        ),
        "provenance": {
            "kind": metadata.kind,
            "schema_version": metadata.schema_version,
            "description": metadata.description,
            "source_url": metadata.source_url,
            "license_note": metadata.license_note,
            "dataset_hash": metadata.dataset_hash,
            "interval_duration_s": metadata.interval_duration_s,
            "activity_reference_scale": float(source.reference_scale()),
            "n_cells": int(source.n_cells()),
        },
        "splits": splits,
        "quality_report": quality,
    }
    if env_config is not None:
        report["configuration"] = {
            "path": str(args.config),
            "environment_id": env_config.environment_id,
            "source_kind": env_config.source.kind,
            "split": env_config.source.split,
            "demand_scale_mbps": env_config.source.demand_scale_mbps,
            "max_demand_points": env_config.source.max_demand_points,
            "cache_has_more_cells_than_max_demand_points": (
                int(source.n_cells()) > int(env_config.source.max_demand_points)
            ),
            "on_entity_limit_exceeded": env_config.observations.on_entity_limit_exceeded,
        }
        if args.sample_episodes:
            report["episode_sampling"] = _sample_episodes(
                source,
                env_config.source.split,
                float(env_config.episode.duration_s),
                int(args.sample_episodes),
                int(args.seed),
            )

    emit(report, args.output, force=bool(args.force))
    return EXIT_OK if verdict == "VALID" else EXIT_DATA


if __name__ == "__main__":
    raise SystemExit(run(main))
