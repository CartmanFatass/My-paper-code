"""Published B02 population, immutable inherited bytes and complete work ceilings."""
import json
from pathlib import Path

from experiments.candidates.uav_planning_opportunity_timing.b01.inputs import (
    SOURCE_PATHS as INHERITED_PATHS, artifact, checked_file, json_record, load_arrays,
    load_catalog, load_trace, payload_binding, record_bytes, same_array, same_payload,
    same_record, sha256, write_json,
)
from experiments.candidates.uav_fleet_transmission.b04.study import episode_costs as inherited_costs
from .host import ALL_WORLD_IDS, AUDIT_WORLD, WORLD_IDS, WORLD_FILE

ROOT = Path(__file__).resolve().parents[4]
DIRECTION = "uav_planning_opportunity_timing"
OBJECT_ID = "planning_opportunity_timing_b02"
ARMS = ("A2", "A_E", "G_E4", "A_E4")
SEED = 29524000
BOOTSTRAP_SEED = 29524991
CONTRASTS = (("A_E4", "A_E"), ("A_E4", "G_E4"), ("G_E4", "A_E"),
             ("A_E4", "A2"), ("G_E4", "A2"), ("A_E", "A2"))
_LIMIT_KEYS = ("worker_state_mask_requests", "model_physical_transitions", "stationary_banks",
               "stationary_candidate_rows", "candidate_transit_ticks", "model_branches",
               "segment_certificates")
ARM_LIMITS = {arm: dict(zip(_LIMIT_KEYS, values)) for arm, values in (
    ("A2", (8351156, 31040, 10, 7000, 280000, 80, 88)),
    ("A_E", (9437556, 35520, 10, 7000, 280000, 80, 88)),
    ("G_E4", (3855642, 14240, 4, 2800, 112000, 32, 32)),
    ("A_E4", (25621722, 97040, 28, 19600, 784000, 224, 248)),
)}
WORKER_LIMITS = {key: 17 * sum(row[key] for row in ARM_LIMITS.values()) for key in _LIMIT_KEYS}
RESOURCE_LIMITS = {"aggregate_metered_cpu_seconds": 86400, "operation_wall_seconds": 172800,
                   "allocated_bytes": 12 * 1024**3, "finalization_cpu_reserve_seconds": 600,
                   "finalization_wall_reserve_seconds": 1200, "allocation_reserve_bytes": 128 * 1024**2}
MOCK_LIMITS = {"cpu_seconds": 1800, "wall_seconds": 7200}
OWN_NAMES = ("__init__.py", "host.py", "inputs.py", "option.py", "segment.py", "controller.py",
             "meter.py", "study.py", "reader.py", "run.py", "worlds.json", "preparation.json",
             "frozen-bindings.json")
SOURCE_PATHS = tuple(dict.fromkeys((*INHERITED_PATHS,
    *(f"experiments/candidates/{DIRECTION}/b02/{name}" for name in OWN_NAMES))))


def mission_order():
    return ([("audit", AUDIT_WORLD, arm) for arm in ARMS]
            + [("result", w, ARMS[(i + k) % 4]) for i, w in enumerate(WORLD_IDS) for k in range(4)])


def source_bindings():
    inherited = json.loads(Path(__file__).with_name("frozen-bindings.json").read_text())
    if set(inherited["source_bindings"]) != set(INHERITED_PATHS):
        raise ValueError("inherited55-source closure changed")
    current = {name: artifact(ROOT / name, ROOT) for name in SOURCE_PATHS}
    for name, expected in inherited["source_bindings"].items():
        same_record(current[name], expected, f"frozen inherited source/{name}")
    return current, inherited["source_sha"]


def fixed_config():
    preparation = json.loads(Path(__file__).with_name("preparation.json").read_text())
    bindings, inherited_sha = source_bindings()
    return {"direction": DIRECTION, "object_id": OBJECT_ID, "n": 8, "horizon": 500,
        "arms": list(ARMS), "world_ids": list(WORLD_IDS), "audit_world": AUDIT_WORLD,
        "mission_order": [list(row) for row in mission_order()], "seed": SEED,
        "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_replicates": 10000,
        "source_bindings": bindings, "frozen_inherited_source_sha": inherited_sha,
        "world_file": artifact(WORLD_FILE, ROOT), "preparation": preparation,
        "new_fits": 0, "updates": 0, "new_teacher_labels": 0, "native_steps": 34000,
        "actual_opportunities": 204, "worker_limits": WORKER_LIMITS, "arm_limits": ARM_LIMITS,
        "resource_limits": RESOURCE_LIMITS, "mock_limits": MOCK_LIMITS,
        "worker_reuse": True, "reader_reuse": False,
        "rule": "A2/A_E frozen; G_E4/A_E4 four actual choices from40, then stay+10 or commanded arrival+10;"
                " dispatch before C/E; A_E4 choices1..3 foresee one ordinary next, choice4 ordinary",
        "forecast_scope": "G_E4 choices1..3 and A_E4 choices1..2 stop before next actual selection;"
                          " A_E4 choice3 complete tail plus next-choice prefix; all other choices complete tail",
        "evidence_identity": "phase/world/arm raw folder plus ordinal/current clock/candidate/next clock/segment ID;"
                             " A_E4 ae/first scope is unchanged B01 opportunity1",
        "failure_policy": "first formal request/admission/worker/reader/resource failure closes purchase; no retry/resume",
        "primary": "A_E4-A_E", "matched_rights": "A_E4-G_E4",
        "contrasts": [a + "-" + b for a, b in CONTRASTS],
        "reading_order": "four worker missions then four full readings, audit world first then each result world"}


def episode_costs(catalog, native_counts, position_predictions):
    return {**inherited_costs(catalog, native_counts, position_predictions),
            "segment_certificates": len(catalog["segments"])}


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
