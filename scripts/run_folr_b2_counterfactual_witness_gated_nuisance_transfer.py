"""Production CLI for frozen FOLR-B2 train -> evaluate -> analyze."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.folr_core.counterfactual_witness_gated_nuisance_transfer import (  # noqa: E402
    analyze,
    evaluate,
    train,
    validate_evaluation,
    validate_result,
    validate_train,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    train_parser = sub.add_parser("train", help="freeze the exact manifest and train final actors")
    train_parser.add_argument("--output-root", required=True)
    train_parser.add_argument("--source-commit", required=True)
    train_parser.add_argument("--run-id", required=True)
    train_parser.add_argument("--technical-smoke", action="store_true")
    evaluate_parser = sub.add_parser("evaluate", help="evaluate all final-only checkpoints")
    evaluate_parser.add_argument("--output-root", required=True)
    analyze_parser = sub.add_parser("analyze", help="materialize paired tables and frozen branch")
    analyze_parser.add_argument("--output-root", required=True)
    analyze_parser.add_argument("--result")
    for name in ("validate-train", "validate-evaluate"):
        child = sub.add_parser(name)
        child.add_argument("--output-root", required=True)
        mode = child.add_mutually_exclusive_group()
        mode.add_argument("--require-full", action="store_true")
        mode.add_argument("--require-technical", action="store_true")
    result = sub.add_parser("validate-result")
    result.add_argument("--result", required=True)
    result.add_argument(
        "--output-root",
        help="canonical run root; required when --result is outside that root",
    )
    mode = result.add_mutually_exclusive_group()
    mode.add_argument("--require-full", action="store_true")
    mode.add_argument("--require-technical", action="store_true")
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
        value = train(
            output_root=args.output_root,
            source_commit=args.source_commit,
            run_id=args.run_id,
            technical_smoke=bool(args.technical_smoke),
        )
    elif args.command == "evaluate":
        value = evaluate(output_root=args.output_root)
    elif args.command == "analyze":
        value = analyze(output_root=args.output_root, result_path=args.result)
    elif args.command == "validate-train":
        value = validate_train(args.output_root, require_full=_mode(args))
    elif args.command == "validate-evaluate":
        value = validate_evaluation(args.output_root, require_full=_mode(args))
    else:
        value = validate_result(
            args.result,
            require_full=_mode(args),
            output_root=args.output_root,
        )
    print(
        json.dumps(
            {
                "command": args.command,
                "status": "COMPLETE",
                "artifact_kind": value.get("artifact_kind"),
                "technical_only": value.get("technical_only"),
                "scientific_terminal_admitted": value.get("scientific_terminal_admitted"),
                "decision": value.get("decision"),
                "activity_counts": value.get("activity_counts"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
