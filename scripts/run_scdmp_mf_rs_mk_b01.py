"""Preflight-only CLI for the current SCDMP B01 engineering milestone."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.runner import (
    preflight_only,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-only", action="store_true", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    args = parser.parse_args()
    value = preflight_only(
        receipt=args.receipt,
        result_root=args.result_root,
        command_runner=subprocess.run,
    )
    print(f"passed={str(value.passed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
