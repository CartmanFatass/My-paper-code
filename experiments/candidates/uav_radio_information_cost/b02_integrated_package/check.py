#!/usr/bin/env python3
"""Admitted two H8 streams and their full saved-byte reconstruction."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))


def main(argv=None):
    from experiments.candidates.uav_radio_information_cost.b02_integrated_package.entry import main as entry
    return entry(__file__,"check",argv)


if __name__ == "__main__":
    if main()["status"] != "VERIFIED_COMPLETE":
        raise SystemExit(1)
