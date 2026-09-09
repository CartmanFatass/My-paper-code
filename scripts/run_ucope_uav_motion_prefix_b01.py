"""One prospective UAV pair, one synthetic fixture, or read-only aggregation."""
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
from experiments.candidates.ucope.uav_motion_prefix_b01.study import (
    Config, aggregate, declared_masters, run_pair, write_summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--engineering-fixture", action="store_true")
    mode.add_argument("--aggregate", nargs=2, metavar="SUMMARY")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--pair", choices=("p21", "p24", "b02", "b03", "b04", "renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02"), default="p21")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.pair in ("b03", "b04", "renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02") and args.aggregate:
        parser.error(f"{args.pair.upper()} has one training pair and no multi-pair aggregate")
    if args.engineering_fixture and args.pair == "p24":
        parser.error("engineering fixture requires p21, b02, b03, b04, renewal_b01, renewal_b02 or renewal_b03 or renewal_frozen_b01 or renewal_fixed_b01 or renewal_fixed_b02 with seed 9001")
    if args.aggregate:
        if args.seed is not None:
            parser.error("aggregation does not take a seed")
        summary = aggregate([json.loads(Path(p).read_text(encoding="utf-8")) for p in args.aggregate], args.pair)
        args.out.mkdir(parents=True, exist_ok=True)
        write_summary(args.out / "summary.json", summary)
    else:
        expected = (9001,) if args.engineering_fixture else declared_masters(args.pair)
        if args.seed not in expected:
            parser.error(f"this mode requires --seed in {expected}")
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        config = (Config.engineering(args.seed, args.pair) if args.engineering_fixture
                  else Config(args.seed, pair=args.pair))
        summary = run_pair(config, args.out, WHOLE_START)
    print(json.dumps({"mode": summary["mode"], "status": summary.get("status"),
                      "primary": summary["primary"], "counts": summary.get("counts")}, allow_nan=False))
    return 0 if summary.get("status", "COMPLETE") in ("COMPLETE", "PRIMARY_COMPLETE_WITH_LIMITS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
