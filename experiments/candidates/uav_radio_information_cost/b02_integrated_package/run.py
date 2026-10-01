#!/usr/bin/env python3
"""Admitted literal U32_FULL/P_PRIOR main purchase."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))


def main(argv=None):
    from experiments.candidates.uav_radio_information_cost.b02_integrated_package.entry import parse, execute
    args, started = parse("run",argv)
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_radio_information_cost")
    return execute("run",args,admission,started)


if __name__ == "__main__":
    if main()["status"] != "COMPLETE":
        raise SystemExit(1)
