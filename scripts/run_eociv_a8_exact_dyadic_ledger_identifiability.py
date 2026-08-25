#!/usr/bin/env python3
"""One-shot entry point for the zero-runtime EOCIV-A8 source audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


RUNNER_RELATIVE_PATH = "scripts/run_eociv_a8_exact_dyadic_ledger_identifiability.py"
CORE_RELATIVE_PATH = "experiments/candidates/eociv_lite/exact_dyadic_ledger_identifiability.py"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run exactly one EOCIV-A8 source/interface audit. The command parses "
            "source and manifests only; it performs no environment or learner work."
        )
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    source_root = args.source_root.resolve()
    resolved_entries = []
    for entry in sys.path:
        try:
            if Path(entry).resolve() == source_root:
                continue
        except (OSError, RuntimeError):
            pass
        resolved_entries.append(entry)
    sys.path[:] = [str(source_root), *resolved_entries]
    from experiments.candidates.eociv_lite.exact_dyadic_ledger_identifiability import (
        run_audit,
    )

    result = run_audit(
        source_root=source_root,
        expected_commit=args.expected_source_commit,
        payload_path=args.payload.resolve(),
        output_path=args.output.resolve(),
        cwd=Path.cwd(),
        core_relative_path=CORE_RELATIVE_PATH,
        runner_relative_path=RUNNER_RELATIVE_PATH,
        runtime_runner_file=Path(__file__),
    )
    print(
        json.dumps(
            {
                "treatment_id": result["treatment_id"],
                "terminal_branch": result["terminal_branch"],
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
