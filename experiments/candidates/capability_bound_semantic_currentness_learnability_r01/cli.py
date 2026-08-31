"""Result-blind describe/preflight and fenced production entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .contract import PRODUCTION_BLOCKER, READY_FOR_PRODUCTION, describe
from .preflight import run_preflight
from .production import run_registered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="capability_bound_semantic_currentness_learnability_r01")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("describe", help="emit result-blind frozen contract identity")
    commands.add_parser("preflight", help="run result-blind complete static audits")
    run = commands.add_parser("run", help="run the sole production object when scientifically ready")
    run.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help=(
            "legacy name for the create-only terminal result path; "
            "this command reads no manifest file"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "describe":
        print(json.dumps(describe(), sort_keys=True, separators=(",", ":")))
        return 0
    if args.command == "preflight":
        payload = run_preflight()
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return 0 if payload["valid"] else 2
    if not READY_FOR_PRODUCTION:
        raise RuntimeError(f"CBSC-LR01 production is fenced: {PRODUCTION_BLOCKER}")
    published = run_registered(args.manifest)
    print(str(published))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = ["build_parser", "main"]
