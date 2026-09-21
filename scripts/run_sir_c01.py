#!/usr/bin/env python3
"""Admitted entry for the fixed, prospective skill-information-refresh C01."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, default=73141)
    args = parser.parse_args()
    if args.seed < 0 or len(args.launch_sha) != 40 or any(c not in "0123456789abcdef" for c in args.launch_sha):
        parser.error("seed must be nonnegative and launch-sha must be a full lowercase Git SHA")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="skill_information_refresh")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("scientific launch SHA differs from admitted SHA")
    from experiments.candidates.skill_information_refresh.c01.study import Config, run_study
    return run_study(args.out, args.launch_sha, Config(seed=args.seed))


if __name__ == "__main__":
    main()
