#!/usr/bin/env python3
"""One declared metered finite-check invocation; no native or RF environment."""
import argparse
import json
import os
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError("existing check attempt is immutable; do not silently repeat it")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    wall = time.perf_counter()
    from experiments.candidates.uav_fleet_transmission.b12_resource_assignment.contract import OBJECT, source_binding, write_json
    from experiments.candidates.uav_fleet_transmission.b12_resource_assignment.controller import TOTALS
    import pytest
    TOTALS.clear()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    status = pytest.main(["-q", "-s", "--maxfail=1", "--junitxml=" + str(args.out.with_suffix(".xml")),
                         "tests/experiments/candidates/uav_fleet_transmission/b12_resource_assignment"])
    cpu = time.process_time()
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu += children.ru_utime + children.ru_stime
    counts = dict(TOTALS)
    result = dict(object=OBJECT, status="passed" if status == 0 else "failed", exit_code=int(status),
        source_binding=source_binding(), counts=counts, cpu_seconds=cpu, wall_seconds=time.perf_counter()-wall,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        native_steps=0, native_resets=0, native_constructions=0, private_models=0, rf_calls=0, fits=0,
        cost_scope="one process startup/import plus finite actual/mock/failed checks and reaped children")
    write_json(args.out, result)
    return int(status)


if __name__ == "__main__":
    raise SystemExit(main())
