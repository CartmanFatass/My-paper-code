"""Production CLI for frozen UCOPE-B2 train/evaluate/analyze."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.endogenous_paid_count_acquisition import (  # noqa: E402
    SOURCE_PATHS,
    analyze,
    evaluate,
    train,
    validate_evaluation,
    validate_result,
    validate_train,
)


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=PROJECT_ROOT, check=True, capture_output=True,
        text=True, encoding="utf-8",
    )
    return completed.stdout.strip()


def _require_frozen_clean_source(source_commit: str) -> None:
    if _git("rev-parse", "HEAD") != source_commit:
        raise ValueError("declared source commit is not current HEAD")
    tracked = set(_git("ls-files", "--", *SOURCE_PATHS).splitlines())
    if tracked != set(SOURCE_PATHS):
        raise ValueError(f"claim-bearing source paths untracked or absent: {sorted(set(SOURCE_PATHS) - tracked)}")
    status = _git("status", "--porcelain=v1", "--", *SOURCE_PATHS)
    if status:
        raise ValueError(f"claim-bearing source differs from HEAD: {status}")


def _require_retained_phase_source(output_root: str) -> None:
    summary = json.loads((Path(output_root) / "train_summary.json").read_text(encoding="utf-8"))
    if summary.get("technical_only") is not True:
        _require_frozen_clean_source(str(summary["source_commit"]))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    train_parser = commands.add_parser("train", help="freeze tapes and train twelve final-only controllers")
    train_parser.add_argument("--output-root", required=True)
    train_parser.add_argument("--source-commit", required=True)
    train_parser.add_argument("--run-id", required=True)
    train_parser.add_argument("--technical-smoke", action="store_true")
    evaluate_parser = commands.add_parser("evaluate", help="execute exact five-transition panels")
    evaluate_parser.add_argument("--output-root", required=True)
    analyze_parser = commands.add_parser("analyze", help="derive registered metrics and branch")
    analyze_parser.add_argument("--output-root", required=True)
    analyze_parser.add_argument("--result")
    for name in ("validate-train", "validate-evaluate"):
        child = commands.add_parser(name)
        child.add_argument("--output-root", required=True)
        mode = child.add_mutually_exclusive_group()
        mode.add_argument("--require-full", action="store_true")
        mode.add_argument("--require-technical", action="store_true")
    result_parser = commands.add_parser("validate-result")
    result_parser.add_argument("--result", required=True)
    result_parser.add_argument("--output-root")
    mode = result_parser.add_mutually_exclusive_group()
    mode.add_argument("--require-full", action="store_true")
    mode.add_argument("--require-technical", action="store_true")
    return parser


def _mode(arguments: argparse.Namespace) -> bool | None:
    if getattr(arguments, "require_full", False):
        return True
    if getattr(arguments, "require_technical", False):
        return False
    return None


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command == "train":
        if not arguments.technical_smoke:
            _require_frozen_clean_source(arguments.source_commit)
        value = train(output_root=arguments.output_root, source_commit=arguments.source_commit, run_id=arguments.run_id, technical_smoke=bool(arguments.technical_smoke))
    elif arguments.command == "evaluate":
        _require_retained_phase_source(arguments.output_root)
        value = evaluate(output_root=arguments.output_root)
    elif arguments.command == "analyze":
        _require_retained_phase_source(arguments.output_root)
        value = analyze(output_root=arguments.output_root, result_path=arguments.result)
    elif arguments.command == "validate-train":
        value = validate_train(arguments.output_root, require_full=_mode(arguments))
    elif arguments.command == "validate-evaluate":
        value = validate_evaluation(arguments.output_root, require_full=_mode(arguments))
    else:
        value = validate_result(arguments.result, require_full=_mode(arguments), output_root=arguments.output_root)
    print(json.dumps({
        "command": arguments.command,
        "status": "COMPLETE",
        "artifact_kind": value.get("artifact_kind"),
        "technical_only": value.get("technical_only"),
        "scientific_terminal_admitted": value.get("scientific_terminal_admitted"),
        "branch": value.get("branch"),
        "activity_counts": value.get("activity_counts"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
