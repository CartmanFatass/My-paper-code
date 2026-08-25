"""Run the zero-activity VSP06-A1 registered source-binding probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.vsp_06_mssr.joint_production_binding import (
    registered_probe,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the registered VSP06-A1 production binding without "
            "executing an environment, policy, learner, trainer, optimizer, "
            "or evaluator."
        )
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="indent the JSON output",
    )
    parser.add_argument(
        "--retained-evidence",
        type=Path,
        help=(
            "optional JSON focused-test evidence; the probe still constructs "
            "fresh production factories and executes no policy"
        ),
    )
    args = parser.parse_args()
    retained = None
    if args.retained_evidence is not None:
        retained = json.loads(args.retained_evidence.read_text(encoding="utf-8"))
    print(
        json.dumps(
            registered_probe(retained),
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
