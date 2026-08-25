"""One-shot artifact lifecycle for EOCIV-B7."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.eociv_lite.one_step_root_partition_frozen_history import (
    analyze_phase,
    create_claim,
    evaluate_phase,
    run_lifecycle,
    train_phase,
    validate_result,
)


def _print(value: object) -> None:
    print(json.dumps(value, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "EOCIV-B7 isolated one-shot lifecycle. A registered full must use a fresh "
            "empty root and may be invoked exactly once by CPM."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)

    claim = commands.add_parser("claim", help="bind one fresh isolated run root")
    claim.add_argument("--root", type=Path, required=True)
    claim.add_argument("--source-revision", required=True)
    claim.add_argument("--run-id", required=True)
    claim.add_argument("--technical-only", action="store_true")

    for name in ("train", "evaluate", "analyze"):
        phase = commands.add_parser(name)
        phase.add_argument("--root", type=Path, required=True)

    validate = commands.add_parser("validate")
    validate.add_argument("--root", type=Path, required=True)
    validate.add_argument("--require-full", action="store_true")

    lifecycle = commands.add_parser(
        "lifecycle",
        help="claim, train, evaluate, analyze and validate one fresh root",
    )
    lifecycle.add_argument("--root", type=Path, required=True)
    lifecycle.add_argument("--source-revision", required=True)
    lifecycle.add_argument("--run-id", required=True)
    lifecycle.add_argument("--technical-only", action="store_true")

    arguments = parser.parse_args()
    torch.set_num_threads(1)
    if arguments.command == "claim":
        value = create_claim(
            arguments.root,
            source_revision=arguments.source_revision,
            run_id=arguments.run_id,
            technical_only=bool(arguments.technical_only),
        )
    elif arguments.command == "train":
        value = train_phase(arguments.root)
    elif arguments.command == "evaluate":
        value = evaluate_phase(arguments.root)
    elif arguments.command == "analyze":
        value = analyze_phase(arguments.root)
    elif arguments.command == "validate":
        value = validate_result(arguments.root, require_full=bool(arguments.require_full))
    else:
        value = run_lifecycle(
            arguments.root,
            source_revision=arguments.source_revision,
            run_id=arguments.run_id,
            technical_only=bool(arguments.technical_only),
        )
    _print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
