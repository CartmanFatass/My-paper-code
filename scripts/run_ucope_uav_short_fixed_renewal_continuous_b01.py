"""One continuous short fixed or learned renewal study or engineering fixture."""
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
from experiments.candidates.ucope.uav_short_fixed_renewal_continuous_b01.study import Config, LEARNED_SELECTOR, SELECTOR, run_pair


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair", choices=(SELECTOR, LEARNED_SELECTOR), default=SELECTOR)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--engineering-fixture", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    learned = args.pair == LEARNED_SELECTOR
    expected = (9002,) if learned and args.engineering_fixture else \
               (8701,) if learned else (9001,) if args.engineering_fixture else (8601, 8602)
    if args.seed not in expected:
        parser.error("seed does not match the selected study and fixture mode")
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    config = Config.learned(args.engineering_fixture) if learned else \
             Config.engineering() if args.engineering_fixture else Config(args.seed)
    result = run_pair(config, args.out, WHOLE_START)
    print(json.dumps(dict(mode=result["mode"], status=result["status"], primary=result["primary"], counts=result["counts"]), allow_nan=False))
    return 0 if result["status"] in ("COMPLETE", "PRIMARY_COMPLETE_WITH_LIMITS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
