"""Inspect a raw Milan activity file and grid **before** preparing a cache.

This tool reads, it never writes a dataset.  Its purpose is to let you verify against the
version you actually downloaded: the column count and order, the timestamp unit and
interval spacing, the country-code dimension, the missing-field convention, and whether
the grid file matches the square ids in the activity file.

Nothing here decides anything on your behalf.  If the declared column mapping does not
match the file, the report says so and ``prepare_milan.py`` will refuse the file rather
than guess.

Usage::

    python scripts/uav_service_restoration/inspect_data.py \
        --input <raw_activity_file> --grid <milano-grid.geojson> \
        --config configs/uav_service_restoration/preprocess_milan_reference.json
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from _cli import (  # noqa: E402  (path setup happens inside _cli)
    EXIT_OK,
    CliError,
    emit,
    require_existing_file,
    run,
)

from envs.uav_service_restoration.preprocess_milan import (  # noqa: E402
    inspect_raw_sample,
    load_preprocess_config,
    read_milano_grid,
    select_region,
    sha256_of_file,
)


def _grid_report(grid_path: Path, config: Any) -> dict[str, Any]:
    grid = read_milano_grid(grid_path, utm_zone=config.utm_zone)
    indices, record = select_region(grid, config.region)
    positions = np.stack(
        [grid.easting_m[indices], grid.northing_m[indices]], axis=1
    )
    report: dict[str, Any] = {
        "path": str(grid_path),
        "sha256": sha256_of_file(grid_path),
        "n_cells_total": int(grid.cell_ids.shape[0]),
        "source_crs": grid.source_crs,
        "projected_crs": f"UTM zone {config.utm_zone}N (WGS84)",
        "square_id_range": [int(grid.cell_ids.min()), int(grid.cell_ids.max())],
        "region_selection": record,
        "n_cells_selected": int(indices.shape[0]),
    }
    if positions.shape[0] >= 2:
        report["selected_extent_m"] = {
            "x": [float(positions[:, 0].min()), float(positions[:, 0].max())],
            "y": [float(positions[:, 1].min()), float(positions[:, 1].max())],
        }
        # Nearest-neighbour spacing: a sanity check that the grid was projected into
        # metres and not stretched.  Milan's grid is nominally 235 m per cell.
        sample = positions[: min(positions.shape[0], 400)]
        deltas = sample[:, None, :] - sample[None, :, :]
        distances = np.sqrt((deltas**2).sum(axis=-1))
        np.fill_diagonal(distances, np.inf)
        nearest = distances.min(axis=1)
        report["nearest_neighbour_spacing_m"] = {
            "min": float(nearest.min()),
            "median": float(np.median(nearest)),
            "max": float(nearest.max()),
            "note": (
                "spacing is measured in the projected frame; a value far from the "
                "documented cell size means the grid or the UTM zone is wrong"
            ),
        }
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inspect_data.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        required=True,
        help="one raw activity file to inspect (a single file, not a directory)",
    )
    parser.add_argument(
        "--grid",
        default=None,
        help="the matching grid file; omitted, the grid checks are skipped",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="preprocessing configuration declaring the column mapping to verify",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=2000,
        help="how many rows of the activity file to sample (default: 2000)",
    )
    parser.add_argument("--output", default=None, help="also write the report here")
    parser.add_argument(
        "--force", action="store_true", help="overwrite an existing --output file"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_rows <= 0:
        raise CliError("--max-rows must be positive", 2)

    config_path = require_existing_file(args.config, "preprocessing configuration")
    input_path = require_existing_file(args.input, "raw activity file")
    config = load_preprocess_config(config_path)

    report: dict[str, Any] = {
        "tool": "inspect_data",
        "verdict_is_advisory": True,
        "declared_column_mapping": {
            "n_columns": config.columns.n_columns,
            "square_id": config.columns.square_id,
            "time_interval_ms": config.columns.time_interval_ms,
            "country_code": config.columns.country_code,
            "internet_activity": config.columns.internet_activity,
            "delimiter": repr(config.columns.delimiter),
            "has_header": config.columns.has_header,
        },
        "declared_activity_field": config.activity_field,
        "declared_interval_duration_ms": int(config.interval_duration_ms),
        "activity": inspect_raw_sample(input_path, config, max_rows=int(args.max_rows)),
    }
    if args.grid is not None:
        grid_path = require_existing_file(args.grid, "grid file")
        report["grid"] = _grid_report(grid_path, config)
        report["activity_square_ids_seen"] = report["activity"]["distinct_square_ids"]
        report["grid_square_id_range"] = report["grid"]["square_id_range"]
    else:
        report["grid"] = "not inspected: --grid was not supplied"

    emit(report, args.output, force=bool(args.force))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(run(main))
