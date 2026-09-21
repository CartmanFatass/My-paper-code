#!/usr/bin/env python3
"""Admitted entry for the fixed C07 near-commit confirmation."""

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
    args = parser.parse_args()
    valid_sha = (
        len(args.launch_sha) == 40
        and all(character in "0123456789abcdef" for character in args.launch_sha)
    )
    if not valid_sha:
        parser.error("launch-sha must be a full lowercase Git SHA")

    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="skill_information_refresh")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("scientific launch SHA differs from admitted SHA")

    from experiments.candidates.skill_information_refresh.c07.confirm import run_confirmation
    return run_confirmation(args.out, args.launch_sha)


if __name__ == "__main__":
    main()
