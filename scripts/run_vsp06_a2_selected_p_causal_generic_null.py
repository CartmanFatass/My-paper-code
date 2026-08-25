"""Run the registered VSP06-A2 selected-P causal/generic-null audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.vsp_06_mssr.selected_p_causal_generic_null import (
    PUBLIC_LOCATORS,
    registered_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Execute exactly one deterministic ten-call VSP06-A2 production-"
            "kernel causal/null audit from the accepted public A1 witness."
        )
    )
    parser.add_argument(
        "--a1-witness",
        type=Path,
        default=REPOSITORY_ROOT / PUBLIC_LOCATORS["a1_witness"],
        help="accepted public VSP06-A1 matched-support witness JSON",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="indent the JSON output",
    )
    args = parser.parse_args()
    witness = json.loads(args.a1_witness.read_text(encoding="utf-8"))
    result = registered_audit(witness)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
