"""Admission-guarded fixed N8 T/G2/A2 B04 entrypoint."""
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
    parser.add_argument("--seed", type=int, default=260930)
    args = parser.parse_args(argv)
    if args.seed != 260930:
        raise ValueError("B04 uses only its prospectively bound world namespace")
    from scripts.hmasd_admission import require_admission
    accepted = require_admission(__file__, direction="uav_fleet_transmission")
    if accepted["sha"] != args.launch_sha:
        raise ValueError("source SHA differs from accepted operation")
    from experiments.candidates.uav_fleet_transmission.b04.study import run_study
    run_study(args.out.resolve(), args.launch_sha, accepted)


if __name__ == "__main__":
    main()
