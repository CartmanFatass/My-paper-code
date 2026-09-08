"""Run the fixed B01 chain, or its explicitly labelled engineering fixture."""
import time

STARTED_AT = time.monotonic()

import argparse
import json
import sys
from pathlib import Path

import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.vsp_02.teammate_policy_change_b01.study import StudyConfig, run_study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--seed', type=int, default=1103)
    parser.add_argument('--engineering-fixture', action='store_true')
    args = parser.parse_args()
    summary = run_study(StudyConfig(args.seed, args.engineering_fixture), args.out,
                        started_at=STARTED_AT)
    print(json.dumps({key: summary[key] for key in ('run_kind', 'status', 'counts', 'wall_seconds')}))
    return 0 if summary['status'] == 'COMPLETE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
