"""Admission-guarded entry for the fixed complete B01 panel."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args(argv)
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_fleet_transmission")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA differs from accepted source")
    from experiments.candidates.uav_fleet_transmission.study import run_study
    run_study(args.out.resolve(), args.checkpoint_root.resolve(), args.launch_sha, admission)


if __name__ == "__main__":
    main()
