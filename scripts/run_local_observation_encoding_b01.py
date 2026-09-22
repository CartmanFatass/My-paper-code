"""Admitted command-line entry for local-observation-encoding B01."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.local_observation_encoding.b01 import parse_args, plan_guard, run_admitted
from scripts.hmasd_admission import require_admission


def main(argv=None):
    args = parse_args(argv)
    # Refuse an out-of-plan arm/seed before spending the single-use admission.
    plan_guard(args.arm, args.seed)
    admission = require_admission(__file__, direction="local_observation_encoding")
    return run_admitted(args, admission)


if __name__ == "__main__":
    raise SystemExit(main())
