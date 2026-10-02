"""Frozen E/B purchase and byte-only C/H/H_T reference bindings."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.contract import (
    ROOT, HORIZON, identity, sha256, array_digest, equal, sum_counts, telemetry,
    write_json, source_binding as b10_source_binding,
)

DIRECTION = "uav_fleet_transmission"
OBJECT = "fleet-b12-energy-leximin-assignment-v1"
SEED_ROOT = 29910000
WORLD_SEEDS = tuple(range(29910001, 29910033))
ENGINEERING_SEEDS = (29910091, 29910092)
ARMS = ("E", "B")
COMPARISON_ARMS = ("C", "H_A", "H_T", "E", "B")
CONTRASTS = (("B", "E"), ("E", "C"), ("B", "C"), ("E", "H_A"),
             ("B", "H_A"), ("E", "H_T"), ("B", "H_T"))
CPU_REVIEW_SECONDS = 21600.0
COST_ENVELOPE = dict(native_steps=204000, native_resets=68, native_constructions=136,
    permutation_criteria=9830880, flight_slack_edges=491376, target_returns=81936,
    arithmetic_reference_ticks=9072, public_power_arguments=4581048,
    private_models=0, old_nominal_ticks=0, rf_samples=0, tracker_updates=0, fits=0)


def jobs(phase):
    if phase not in ("engineering", "scientific"):
        raise ValueError("unknown B12 phase")
    seeds = ENGINEERING_SEEDS if phase == "engineering" else WORLD_SEEDS
    result = []
    for index, seed in enumerate(seeds):
        arms = ARMS if index % 2 == 0 else ARMS[::-1]
        result.extend(dict(job_key=f"{seed}/{arm}", seed=seed, arm=arm, limit=HORIZON)
                      for arm in arms)
    return result


def expected_counts(arm, length):
    if arm not in ARMS:
        raise ValueError("only new E/B calls belong to B12")
    plans = (length + 29) // 30
    return dict(proposals=length, plans=plans, canonicalizations=plans, associations=0)


def source_binding(root=ROOT):
    root = Path(root)
    result = b10_source_binding(root)
    names = set(result["files"])
    folder = root / "experiments/candidates/uav_fleet_transmission/b12_resource_assignment"
    names.update(str(p.relative_to(root)) for p in folder.glob("*.py"))
    names.add(str((folder / "references.json").relative_to(root)))
    tests = root / "tests/experiments/candidates/uav_fleet_transmission/b12_resource_assignment"
    names.update(str(p.relative_to(root)) for p in tests.glob("*.py"))
    result["files"] = {name: sha256(root / name) for name in sorted(names)}
    result["construction_contract_sha"] = "6fc708f745de10c5b9dcaf0e93fc6ff9dab161bc"
    result["selection_l0_sha"] = "ded373e8a73f936e2467b100b7ed00837662a688"
    return result


def reference_root_for_output(out):
    out = Path(out).resolve()
    if out.parent.name != DIRECTION or out.parent.parent.name != "runs":
        raise ValueError("reference locator requires canonical direction output")
    return out.parent.parent.parent


def reference_evidence(reference_root, phase, *, verify_raw=True, verify_sources=True):
    """Hash/read saved evidence only, never import or execute an old controller."""
    root = Path(reference_root).resolve()
    descriptors = json.loads(Path(__file__).with_name("references.json").read_text())[phase]
    rows, groups = [], []
    source_verified = {}
    current = b10_source_binding()
    for descriptor in descriptors:
        folder = root / descriptor["run"]
        for name, expected in descriptor["compact"].items():
            found = identity(folder / name)
            if any(found[k] != expected[k] for k in ("sha256", "bytes")):
                raise AssertionError("frozen compact identity differs: " + str(folder / name))
        config = json.loads((folder / "config.json").read_text())
        reading = json.loads((folder / "reading.json").read_text())
        if config["launch_sha"] != descriptor["launch_sha"] or reading["status"] != "VERIFIED":
            raise AssertionError("frozen source/complete-reader identity differs")
        # Only the still-imported B10/native dependencies must match current bytes.
        if any(config["source_binding"]["files"].get(k) != v for k, v in current["files"].items()):
            raise AssertionError("live native/C dependencies differ from the frozen reference")
        if verify_sources:
            for name, expected in config["source_binding"]["files"].items():
                key = descriptor["launch_sha"] + ":" + name
                if key not in source_verified:
                    data = subprocess.check_output(["git", "show", key], cwd=ROOT)
                    source_verified[key] = hashlib.sha256(data).hexdigest()
                if source_verified[key] != expected:
                    raise AssertionError("frozen Git source digest differs: " + key)
        if phase == "engineering" and "C" in descriptor["arms"] and not reading["exact_native_reference_C"]:
            raise AssertionError("old C/REFERENCE engineering identity incomplete")
        selected = [r for r in json.loads((folder / "perworld.json").read_text())
                    if r["arm"] in descriptor["arms"]]
        expected_pairs = {(j["seed"], a) for j in jobs(phase) for a in descriptor["arms"]}
        if len(selected) != len(expected_pairs) or {(r["seed"], r["arm"]) for r in selected} != expected_pairs:
            raise AssertionError("frozen reference panel differs")
        for row in selected:
            if row["status"] != "completed" or row["actual_length"] != HORIZON:
                raise AssertionError("reference mission is incomplete")
            path = (folder / row["raw"]["path"]).resolve()
            if not path.is_relative_to((folder / "raw").resolve()):
                raise AssertionError("frozen raw escaped its canonical directory")
            if verify_raw:
                found = identity(path)
                if any(found[k] != row["raw"][k] for k in ("sha256", "bytes")):
                    raise AssertionError("frozen raw bytes differ: " + str(path))
            rows.append(row | {"reference_directory": str(folder),
                               "reference_source_sha": descriptor["launch_sha"]})
        groups.append(dict(directory=str(folder), descriptor=descriptor))
    return dict(root=str(root), phase=phase, groups=groups, rows=rows,
                new_controller_calls=0, new_model_calls=0, new_native_calls=0)
