"""Immutable identities and finite work ceilings for the selected whole study."""
import json
from pathlib import Path

from experiments.candidates.uav_fleet_transmission.b04.study import SOURCE_PATHS as FROZEN_PATHS
from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse.inputs import (
    artifact, checked_file, json_record, load_arrays, load_catalog, load_trace,
    payload_binding, record_bytes, same_array, same_payload, same_record, sha256)
from .host import ALL_WORLD_IDS, AUDIT_WORLD, WORLD_IDS, WORLD_FILE

ROOT = Path(__file__).resolve().parents[4]
DIRECTION = "uav_planning_opportunity_timing"
OBJECT_ID = "planning_opportunity_timing_b01"
ARMS = ("G2", "A2", "G_E", "A_E")
SEED = 29523000
BOOTSTRAP_SEED = 29523991
ARM_LIMITS = {
    "G2": {"worker_state_mask_requests": 1891196, "model_physical_transitions": 6720},
    "A2": {"worker_state_mask_requests": 8351156, "model_physical_transitions": 31040},
    "G_E": {"worker_state_mask_requests": 2026996, "model_physical_transitions": 7280},
    "A_E": {"worker_state_mask_requests": 9437556, "model_physical_transitions": 35520},
}
WORKER_LIMITS = {"worker_state_mask_requests": 369017368, "model_physical_transitions": 1369520,
                 "stationary_banks": 408, "stationary_candidate_rows": 285600,
                 "candidate_transit_ticks": 11424000, "model_branches": 3264}
RESOURCE_LIMITS = {"aggregate_metered_cpu_seconds": 72000, "operation_wall_seconds": 172800,
                   "allocated_bytes": 10 * 1024**3, "finalization_cpu_reserve_seconds": 300,
                   "finalization_wall_reserve_seconds": 600, "allocation_reserve_bytes": 64 * 1024**2}
OWN_NAMES = ("__init__.py", "host.py", "inputs.py", "option.py", "segment.py", "controller.py",
             "evidence.py", "meter.py", "study.py", "reader.py", "run.py", "worlds.json", "preparation.json")
REUSE_NAMES = ("__init__.py", "controller.py", "segment.py", "inputs.py", "reader.py")
SOURCE_PATHS = tuple(dict.fromkeys((*FROZEN_PATHS,
    *(f"experiments/candidates/{DIRECTION}/b01/{name}" for name in OWN_NAMES),
    *(f"experiments/candidates/uav_parent_adaptation/b08_exact_planning_reuse/{name}" for name in REUSE_NAMES),
    "experiments/candidates/uav_parent_adaptation/b06_continuation_amortization/cycle.py",
    "experiments/candidates/uav_planning_opportunity_timing/__init__.py", "scripts/hmasd_admission.py")))


def mission_order():
    result = [("audit", AUDIT_WORLD, arm) for arm in ARMS]
    result.extend(("result", w, ARMS[(i + k) % 4])
                  for i, w in enumerate(WORLD_IDS) for k in range(4))
    return result


def fixed_config():
    preparation = json.loads(Path(__file__).with_name("preparation.json").read_text())
    return {"direction": DIRECTION, "object_id": OBJECT_ID, "n": 8, "horizon": 500,
        "arms": list(ARMS), "world_ids": list(WORLD_IDS), "audit_world": AUDIT_WORLD,
        "mission_order": [list(row) for row in mission_order()], "seed": SEED,
        "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_replicates": 10000,
        "source_bindings": {name: artifact(ROOT / name, ROOT) for name in SOURCE_PATHS},
        "world_file": artifact(WORLD_FILE, ROOT), "preparation": preparation,
        "new_fits": 0, "updates": 0, "native_steps": 34000,
        "worker_limits": WORKER_LIMITS, "arm_limits": ARM_LIMITS, "resource_limits": RESOURCE_LIMITS,
        "worker_reuse": True, "reader_reuse": False,
        "rule": "first at40; G2/A2 second120; G_E/A_E second50 if stay else40+duration+10; dispatch before C/E",
        "failure_policy": "first formal admission/worker/reader failure closes purchase; no retry/resume",
        "primary": "A_E-A2", "secondary": ["G_E-A2", "G_E-G2", "A_E-G_E"],
        "descriptive": ["A2-G2", "A_E-G2"],
        "reading_order": "four worker missions then four full readings, audit world first then each result world"}


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_bytes(json.dumps(value, sort_keys=True, indent=2, allow_nan=False).encode() + b"\n")
    partial.replace(path)


def check_costs(costs, arm):
    for name, limit in ARM_LIMITS[arm].items():
        if type(costs[name]) is not int or not 0 <= costs[name] <= limit:
            raise ValueError(f"declared per-mission ceiling exceeded: {arm}/{name}")


def aggregate_costs(rows):
    totals = {name: sum(row["costs"][name] for row in rows) for name in WORKER_LIMITS}
    for name, value in totals.items():
        if type(value) is not int or not 0 <= value <= WORKER_LIMITS[name]:
            raise ValueError(f"declared whole-study ceiling exceeded: {name}")
    return totals
