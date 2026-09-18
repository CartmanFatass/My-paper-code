"""Prepare a read-only activity cache from raw Milan files.

This is the only tool that writes a dataset.  It refuses an existing output directory, so
a cache another process may be reading is never overwritten, and it writes its completion
marker last, so a reader that sees the marker knows every array is complete.

It will not fabricate data, and it will not guess provenance: exactly one of
``--real-data`` and ``--not-real-data`` is required.  ``--not-real-data`` prepares a cache
from a self-authored fixture for testing; that cache is permanently marked
``is_real_activity_data: false`` and a ``milan_activity`` configuration refuses to open it.

Run ``inspect_data.py`` first and confirm the column mapping against the version you
downloaded.  The publisher's licence governs the raw data and the cache; it is separate
from this repository's code licence, and neither raw files nor caches belong in Git.

Usage::

    python scripts/uav_service_restoration/prepare_milan.py \
        --input <raw_file> [<raw_file> ...] --grid <milano-grid.geojson> \
        --config configs/uav_service_restoration/preprocess_milan_reference.json \
        --output <new_cache_dir>
"""

from __future__ import annotations

import argparse
from pathlib import Path

from _cli import (  # noqa: E402
    EXIT_OK,
    CliError,
    emit,
    require_existing_file,
    run,
)

from envs.uav_service_restoration.preprocess_milan import (  # noqa: E402
    load_preprocess_config,
    prepare_milan_dataset,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prepare_milan.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        required=True,
        nargs="+",
        help="one or more raw activity files; duplicate paths are refused",
    )
    parser.add_argument("--grid", required=True, help="the matching grid file")
    parser.add_argument(
        "--config", required=True, help="preprocessing configuration (strict JSON)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="a NEW directory for the cache; an existing directory is refused",
    )
    provenance = parser.add_mutually_exclusive_group(required=True)
    provenance.add_argument(
        "--real-data",
        action="store_true",
        help=(
            "assert that --input holds genuine published activity records; the cache is "
            "then marked is_real_activity_data and may back a milan_activity run"
        ),
    )
    provenance.add_argument(
        "--not-real-data",
        action="store_true",
        help=(
            "mark the cache as NOT real activity data (fixture-derived input); a "
            "milan_activity configuration will then refuse to open it"
        ),
    )
    parser.add_argument(
        "--report", default=None, help="also write the returned metadata here"
    )
    parser.add_argument(
        "--force", action="store_true", help="overwrite an existing --report file"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    resolved_inputs = [require_existing_file(path, "raw activity file") for path in args.input]
    seen: set[Path] = set()
    for path in resolved_inputs:
        key = path.resolve()
        if key in seen:
            raise CliError(f"duplicate input file: {path}; records are never double-counted", 2)
        seen.add(key)

    grid_path = require_existing_file(args.grid, "grid file")
    config_path = require_existing_file(args.config, "preprocessing configuration")
    output_root = Path(args.output)
    if output_root.exists():
        raise CliError(
            f"{output_root} already exists; write into a new directory so a cache in "
            "use is never overwritten",
            2,
        )

    config = load_preprocess_config(config_path)
    # The provenance claim is never a default: one of the two flags is required, so a
    # fixture-derived cache can never be stamped as real activity data by omission.
    is_real = bool(args.real_data)
    metadata = prepare_milan_dataset(
        resolved_inputs,
        grid_path,
        config,
        output_root,
        is_real_activity_data=is_real,
        kind="milan_activity" if is_real else "prepared_dataset",
    )
    emit(
        {
            "tool": "prepare_milan",
            "output_root": str(output_root),
            "is_real_activity_data": is_real,
            "n_input_files": len(resolved_inputs),
            "metadata": metadata,
            "next_step": (
                "python scripts/uav_service_restoration/validate_dataset.py --dataset "
                f"{output_root}"
            ),
        },
        args.report,
        force=bool(args.force),
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(run(main))
