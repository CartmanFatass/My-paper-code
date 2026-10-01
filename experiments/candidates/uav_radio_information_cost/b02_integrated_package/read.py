#!/usr/bin/env python3
"""Admitted complete paired main reader; zero new native episodes."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))


def main(argv=None):
    from experiments.candidates.uav_radio_information_cost.b02_integrated_package.entry import main as entry
    return entry(__file__,"read",argv)


if __name__ == "__main__":
    if main()["status"] != "VERIFIED_COMPLETE":
        raise SystemExit(1)
