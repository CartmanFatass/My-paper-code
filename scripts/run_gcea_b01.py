"""Admitted entry for the fixed GCEA B01 O/P/E comparison."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    from experiments.candidates.goal_conditioned_entity_aggregation.b01.runner import parse_args, run_admitted
    from scripts.hmasd_admission import require_admission

    args = parse_args(argv)
    admission = require_admission(__file__, direction="goal_conditioned_entity_aggregation")
    return run_admitted(args, admission)


if __name__ == "__main__":
    raise SystemExit(main())
