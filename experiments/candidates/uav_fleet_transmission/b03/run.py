"""Admission-guarded fixed N8 C/R/T B03 entrypoint."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args(argv)
    from scripts.hmasd_admission import require_admission
    accepted = require_admission(__file__, direction="uav_fleet_transmission")
    if accepted["sha"] != args.launch_sha:
        raise ValueError("source SHA differs from accepted operation")
    from experiments.candidates.uav_fleet_transmission.b03.study import run_study
    run_study(args.out.resolve(), args.launch_sha, accepted)


if __name__ == "__main__":
    main()
