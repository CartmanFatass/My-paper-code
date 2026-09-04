"""One-shot CLI for FOLR-B3 calibrated partner-writer stale-load routing."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.folr_core.partner_writer_stale_load_routing import (
    analyze,
    evaluate,
    summarize_artifacts,
    train,
    validate_evaluation,
    validate_result,
    validate_train,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    child = sub.add_parser("train", help="freeze phase P, calibrate, and train phase R only if admitted")
    child.add_argument("--output-root", required=True)
    child.add_argument("--source-commit", required=True)
    child.add_argument("--run-id", required=True)
    child.add_argument("--technical-only", action="store_true")
    child = sub.add_parser("evaluate", help="evaluate final-only phase-R checkpoints, if phase R ran")
    child.add_argument("--output-root", required=True)
    child = sub.add_parser("analyze", help="derive the frozen branch from retained evidence")
    child.add_argument("--output-root", required=True)
    child.add_argument("--result")
    for name in ("validate-train", "validate-evaluate"):
        child = sub.add_parser(name)
        child.add_argument("--output-root", required=True)
        mode = child.add_mutually_exclusive_group()
        mode.add_argument("--require-full", action="store_true")
        mode.add_argument("--require-technical", action="store_true")
    child = sub.add_parser("validate-result")
    child.add_argument("--result", required=True)
    child.add_argument("--output-root", required=True)
    mode = child.add_mutually_exclusive_group()
    mode.add_argument("--require-full", action="store_true")
    mode.add_argument("--require-technical", action="store_true")
    child = sub.add_parser("summarize")
    child.add_argument("--output-root", required=True)
    return parser


def _mode(args: argparse.Namespace) -> bool | None:
    if getattr(args, "require_full", False):
        return True
    if getattr(args, "require_technical", False):
        return False
    return None


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "train":
        value = train(output_root=args.output_root, source_commit=args.source_commit, run_id=args.run_id, technical_only=args.technical_only)
    elif args.command == "evaluate":
        value = evaluate(output_root=args.output_root)
    elif args.command == "analyze":
        value = analyze(output_root=args.output_root, result_path=args.result)
    elif args.command == "validate-train":
        value = validate_train(args.output_root, require_full=_mode(args))
    elif args.command == "validate-evaluate":
        value = validate_evaluation(args.output_root, require_full=_mode(args))
    elif args.command == "validate-result":
        value = validate_result(args.result, output_root=args.output_root, require_full=_mode(args))
    else:
        value = summarize_artifacts(args.output_root)
    print(value.get("artifact_kind", value.get("decision", "OK")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

