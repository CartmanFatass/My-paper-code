"""Fixed B01 addresses and source identities. No constructors or result effects."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from experiments.candidates.uav_fleet_transmission.b10_service_assignment.contract import (
    ROOT, HORIZON, identity, sha256, equal, array_digest, sum_counts, telemetry,
    write_json, json_value, source_binding as retained_binding,
)

DIRECTION = "uav_service_resource_control"
OBJECT = "service-resource-b01-finite-native-selector-v1"
THETAS = (0., .10, .20, .30)
ORDINARY = ("C", "H_T", "T_0", "T_10", "T_20", "T_30")
DEV_WORLDS = tuple(range(40034001, 40034017))
FINAL_WORLDS = tuple(range(40035001, 40035033))
FIT_SEEDS = tuple(dict(init_seed=51030000 + k, exploration_seed=52030000 + k,
                      replay_seed=53030000 + k) for k in (11, 22, 33))
CPU_LIMIT = 75 * 3600.
WALL_LIMIT = 96 * 3600.
BYTE_LIMIT = 32 * 1024**3


def clean(value):
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def diagnostic_bytes(value):
    return np.frombuffer(json.dumps(clean(value), sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode(), dtype=np.uint8).copy()


def ordinary_program(label):
    if label in ("C", "H_T"):
        return dict(program=label)
    if label in ORDINARY[2:]:
        return dict(program="T", theta=THETAS[ORDINARY.index(label)-2])
    raise ValueError("undeclared ordinary label")


def job(phase, seed, label, **program):
    return dict(job_key=f"{phase}/{seed}/{label}", phase=phase, seed=int(seed),
                arm=label, limit=HORIZON, **program)


def audit_jobs():
    return [job("audit", 40039001, p, program=p) for p in
            ("C", "forced_C", "H_T", "forced_H_T")] + [
        job("audit", 40039002, f"alternating_{p}", program="alternating", initial_parity=p)
        for p in (0, 1)]


def training_jobs(fit):
    if fit not in range(3):
        raise ValueError("fit must be0,1,2")
    return [job("train", 40031001 + 1000*fit + index, f"L{fit}", program="SELECTOR",
                fit=fit, episode_index=index) for index in range(128)]


def calibration_jobs():
    return [job("calibration", seed, arm, **ordinary_program(arm))
            for seed in DEV_WORLDS for arm in ORDINARY]


def final_jobs(selected):
    if selected not in ORDINARY:
        raise ValueError("T* must be a calibrated ordinary program")
    arms = ("C", "H_T") + (() if selected in ("C", "H_T") else ("T_star",)) + ("L0", "L1", "L2")
    result = []
    for index, seed in enumerate(FINAL_WORLDS):
        shift = index % len(arms)
        for arm in arms[shift:] + arms[:shift]:
            program = (dict(program="SELECTOR", fit=int(arm[1]), episode_index=index)
                       if arm.startswith("L") else ordinary_program(selected if arm == "T_star" else arm))
            result.append(job("final", seed, arm, **program))
    return result


def select_ordinary(rows):
    expected = calibration_jobs()
    by_key = {r["job_key"]: r for r in rows}
    if len(rows) != len(expected) or len(by_key) != len(rows):
        raise ValueError("calibration completeness/uniqueness failure")
    for spec in expected:
        row = by_key[spec["job_key"]]
        if row["status"] != "completed" or any(row[k] != v for k, v in spec.items()):
            raise ValueError("calibration identity/failure")
    means = {arm: math.fsum(by_key[f"calibration/{seed}/{arm}"]["J_total"]
                           for seed in DEV_WORLDS)/len(DEV_WORLDS) for arm in ORDINARY}
    if not all(math.isfinite(v) for v in means.values()):
        raise ValueError("nonfinite calibration result")
    selected = max(ORDINARY, key=lambda arm: means[arm])  # first exact maximum
    return dict(selected=selected, program=ordinary_program(selected), means=means,
                tie_order=list(ORDINARY), source_worlds=list(DEV_WORLDS),
                final_identity_alias=selected if selected in ("C", "H_T") else None)


def expected_counts(program, length):
    plans = (length + 29)//30
    tracked = program != "C"
    return dict(proposals=length, plans=plans, canonicalizations=plans + (length if tracked else 0),
                associations=length if tracked else 0)


def source_binding(root=ROOT):
    root = Path(root)
    result = retained_binding(root)
    names = set(result["files"])
    for directory in ("experiments/candidates/uav_fleet_transmission/b11_travel_ties",
                      "experiments/candidates/uav_fleet_transmission/b12_resource_assignment",
                      "experiments/candidates/uav_service_resource_control/b01_native_selector"):
        names.update(str(path.relative_to(root)) for path in (root/directory).glob("*.py"))
    names.update((".codex/hmasd-compute.toml", "scripts/hmasd_launch.py",
                  "scripts/hmasd_admission.py"))
    result["files"] = {name: sha256(root/name) for name in sorted(names)}
    result["source_contract_sha"] = "fa5b7fb85e1e06df53fc3e34ec0e7e8f5529d547"
    result["whole_purchase_selection_sha"] = "a85b6ded1cca75fb035334eb177b812804b5f7c2"
    return result
