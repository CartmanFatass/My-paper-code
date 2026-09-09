#!/usr/bin/env python3
"""Entry point for the engineering-only MGTAP B01 adapter."""

import time
PROCESS_START = time.monotonic()

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.runner import main


if __name__ == "__main__":
    raise SystemExit(main(process_start=PROCESS_START))
