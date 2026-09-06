"""Run the frozen B01 deployment-mode evaluation or its one non-target engineering check."""

from time import perf_counter

STARTED = perf_counter()

import argparse
import os
from pathlib import Path
import sys

for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def build_config(profile):
    """Card defaults; the check profile differs only in namespace, masters, panel size and cap."""
    check = profile == "engineering-check"
    return dict(profile=profile,
                namespace="VNFC-N7-B01-DEPLOYMENT-MODE-CHECK-20260905" if check
                          else "VNFC-N7-B01-DEPLOYMENT-MODE-20260905",
                world_seed=2026090595 if check else 2026090505,
                action_seed=2026090596 if check else 2026090506,
                episodes=2 if check else 64, wall_cap=300 if check else 180,
                reference_namespace="VNFC-N7-DIRECT-RETURN-B01-20260905",
                reference_record="b01_formal_20260905_02", reference_arm="MAPR",
                reference_eval_seed=2026090502, reference_episodes=64, reference_round=64)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("formal", "engineering-check"), default="formal")
    parser.add_argument("--checkpoint-root", type=Path, required=True,
                        help="directory holding <record>/checkpoints/<ARM>_final.pt for the four frozen policies")
    parser.add_argument("--b01-reference", type=Path,
                        help="recorded B01 formal02 evaluation_episodes.json; required by the check profile")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args(argv)
    if args.profile == "engineering-check" and args.b01_reference is None:
        parser.error("the engineering-check profile requires --b01-reference")
    config = build_config(args.profile)
    from experiments.candidates.variable_n_fleet_churn_n7_direct_b01.deployment_mode import run
    final = run(config, args.out, args.launch_sha, STARTED, args.checkpoint_root, args.b01_reference)
    return 0 if final["within_wall_cap"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
