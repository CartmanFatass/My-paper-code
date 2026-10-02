"""Frozen B10 assignment-only addresses and source-bound utilities; no effects."""
from __future__ import annotations
from pathlib import Path
from experiments.candidates.uav_fleet_transmission.b09_service_prediction.contract import (
    ROOT, HORIZON, MODEL_SEED, SAMPLES, EVENTS, BS_SOURCES, json_value, write_json,
    sha256, identity, array_digest, sum_counts, telemetry, equal,
    source_binding as retained_source_binding,
)
DIRECTION = "uav_fleet_transmission"
OBJECT = "fleet-b10-current-service-assignment-v1"
SEED_ROOT = 29910000
WORLD_SEEDS = tuple(range(29910001, 29910033))
ENGINEERING_SEEDS = (29910091, 29910092)
ARMS = ("C", "H_A", "F_A")
CPU_REVIEW_SECONDS = 12 * 3600.0
COST_ENVELOPE = dict(native_steps=312000, native_resets=104, native_constructions=208,
    candidate_forecasts=218752, nominal_ticks=6562560, rf_samples=656256,
    private_models=160, fits=0)


def jobs(phase):
    if phase == "engineering":
        return [dict(job_key=f"{seed}/{arm}", seed=seed, arm=arm, limit=HORIZON)
                for seed in ENGINEERING_SEEDS for arm in ("REFERENCE", *ARMS)]
    if phase != "scientific":
        raise ValueError("unknown frozen B10 phase")
    result=[]
    for index, seed in enumerate(WORLD_SEEDS):
        shift=index % len(ARMS)
        for arm in ARMS[shift:]+ARMS[:shift]:
            result.append(dict(job_key=f"{seed}/{arm}", seed=seed, arm=arm, limit=HORIZON))
    return result


def source_binding(root=ROOT):
    root=Path(root)
    result=retained_source_binding(root)
    names=set(result["files"])
    names.update(str(path.relative_to(root)) for path in
                 (root/"experiments/candidates/uav_fleet_transmission/b10_service_assignment").glob("*.py"))
    result["files"]={name:sha256(root/name) for name in sorted(names)}
    result["construction_contract_sha"]="72bf27b15d31709dfa4f05e0f485025c7c375c52"
    return result


def expected_counts(arm, length):
    plans=(length+29)//30
    tracked=arm in ("H_A","F_A")
    return dict(proposals=length, plans=plans,
                canonicalizations=plans+(length if tracked else 0),
                associations=length if tracked else 0)
