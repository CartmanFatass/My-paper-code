from __future__ import annotations

import os
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from .allocator import frozen_bids, handoff_bids, sp_rda, zero_bids
from .config import EXECUTABLE_ARMS, REGISTERED
from .evaluation import execute_arm
from .experiment import run_stage1
from .generator import World
from .models import SetBidActorCritic, deterministic_adaptive_leases, parameter_counts, pressure_vector, structural_edge_mask
from .rng import opaque_handle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VNFC-B3 v6 registered Stage-1 SP-RDA runner")
    parser.add_argument("--output-root", type=Path,
                        default=Path("artifacts/variable_n_fleet_churn/vnfc_b3_registered"))
    parser.add_argument("--result", type=Path,
                        default=Path("docs/research/candidates/variable_n_fleet_churn/VNFC_B3_STAGE1_RESULT.json"))
    parser.add_argument("--execute-stage1", action="store_true", help="launch exact complete v6 Stage 1")
    parser.add_argument("--validate-only", action="store_true", help="proof-sized no-training conformance probe")
    parser.add_argument("--describe", action="store_true", help="print frozen v6 manifest without compute")
    return parser


def _validation_world() -> World:
    n = 15
    handles = tuple(opaque_handle(0, "validation-only", 0, i // 3, i % 3) for i in range(n))
    capacities = np.tile(np.asarray([[.24, .08, .04], [.08, .24, .04], [.08, .04, .24]]), (5, 1))
    return World(0, "validation-only", 2, 0, 0, (12, 15), "FIXED_MASS", "COUPLED", "SWITCH_REQUIRED",
                 handles, capacities, np.ones(3), {h: i % 3 for i, h in enumerate(handles[:12])},
                 frozenset(handles[12:]), {h: i for i, h in enumerate(handles)}, {})


def validate_only() -> dict:
    torch.manual_seed(1); torch.set_num_threads(1)
    model = SetBidActorCritic().eval(); world = _validation_world(); order = list(range(world.n))
    arm_reports = {}
    for arm in EXECUTABLE_ARMS:
        outcome, counters, _, _, learned = execute_arm(model, world, arm, order, measure_outcome=False, record_timing=False)
        arm_reports[arm] = {"addressed_agents": len(outcome["assignment"]), "counters": counters,
                            "learned_forward_counts": learned}
    handles, agents, tasks, _ = world.observation(order)
    capacities = torch.from_numpy(world.capacities.astype(np.float32)); demand = torch.from_numpy(world.demand.astype(np.float32))
    previous = torch.from_numpy(agents[:, 3:7]); rho = pressure_vector(capacities, demand)
    with torch.no_grad():
        initial = model(torch.from_numpy(agents), torch.from_numpy(tasks), torch.from_numpy(world.observation(order)[3]))
    leases = deterministic_adaptive_leases(initial.lease_probabilities, previous)
    mask = structural_edge_mask(capacities, demand, previous, leases)
    return {"manifest": REGISTERED.manifest(), "parameter_counts": parameter_counts(model),
            "arms": arm_reports, "pressure_finite": bool(torch.isfinite(rho).all()),
            "adaptive_lease_count": int(leases.sum()), "adaptive_structural_edges": int(mask.sum()),
            "common_initial_tensor_state": "single registered initialization function",
            "stage2_compute_launched": False}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.execute_stage1:
        result = run_stage1(args.output_root, args.result)
        print(json.dumps({"result": str(args.result), "stage2_released": result["analysis"]["stage2_released"]}, indent=2))
        return 0
    if args.validate_only:
        print(json.dumps(validate_only(), indent=2, sort_keys=True)); return 0
    print(json.dumps(REGISTERED.manifest(), indent=2, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
