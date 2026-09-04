#!/usr/bin/env python3
"""Create-once CLI for the frozen UCOPE B1-04 odd-support A/RECON audit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.competence_first_scout_r01.support_audit import (  # noqa: E402
    ACCEPTED_BINDING,
    execute_audit_to_output,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--complete-root", required=True)
    parser.add_argument("--admission-receipt", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    execute_audit_to_output(
        args.complete_root,
        args.admission_receipt,
        args.output,
        binding=ACCEPTED_BINDING,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
