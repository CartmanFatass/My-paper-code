"""One bounded replay of the original 8702 T prefix for failure-location evidence."""
import time
WHOLE_START = time.monotonic()
import os
for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.ucope.uav_short_fixed_renewal_continuous_b01.study import Config, run_pair


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=(8702,), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    result = run_pair(Config.failure_location(seed=args.seed), args.out, WHOLE_START,
                      failure_location=True)
    print(json.dumps(dict(mode=result["mode"], comparison_status=result["status"],
        diagnostic_prefix_complete=result["diagnostic_prefix_complete"],
        failure_context=result.get("failure_context"), counts=result["counts"]), allow_nan=False))
    return 0 if result["diagnostic_prefix_complete"] and not result["limits"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
