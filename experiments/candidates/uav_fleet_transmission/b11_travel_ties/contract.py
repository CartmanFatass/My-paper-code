"""Fixed B11 panel, full incremental price, and frozen B10 reference identities."""
from __future__ import annotations
import json
from pathlib import Path
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.contract import (
    ROOT, HORIZON, SAMPLES, identity, sha256, array_digest, equal, sum_counts,
    telemetry, write_json, source_binding as b10_source_binding,
    expected_counts as b10_expected_counts,
)
DIRECTION = "uav_fleet_transmission"
OBJECT = "fleet-b11-literal-score-travel-ties-v1"
SEED_ROOT = 29910000
WORLD_SEEDS = tuple(range(29910001, 29910033))
ENGINEERING_SEEDS = (29910091, 29910092)
ARMS = ("H_T",)
COMPARISON_ARMS = ("C", "H_A", "H_T")
CPU_REVIEW_SECONDS = 14400.0
COST_ENVELOPE = dict(native_steps=102000, native_resets=34, native_constructions=68,
    candidate_forecasts=109376, nominal_ticks=3281280, rf_samples=328128,
    private_models=80, fits=0)


def jobs(phase):
    if phase not in ("engineering", "scientific"):
        raise ValueError("unknown B11 phase")
    seeds = ENGINEERING_SEEDS if phase == "engineering" else WORLD_SEEDS
    return [dict(job_key=f"{seed}/H_T", seed=seed, arm="H_T", limit=HORIZON) for seed in seeds]


def expected_counts(arm, length):
    if arm != "H_T":
        raise ValueError("only new H_T calls belong to B11")
    return b10_expected_counts("H_A", length)


def source_binding(root=ROOT):
    root=Path(root)
    result=b10_source_binding(root)
    names=set(result["files"])
    folder=root/"experiments/candidates/uav_fleet_transmission/b11_travel_ties"
    names.update(str(p.relative_to(root)) for p in folder.glob("*.py"))
    names.add(str((folder/"references.json").relative_to(root)))
    result["files"]={name:sha256(root/name) for name in sorted(names)}
    result["construction_contract_sha"]="95ecc08021c0f0a3fffd1efe94323fb77ff31f24"
    return result


def reference_evidence(reference_root, phase, *, verify_raw=True):
    """Read/hash only: no comparator controller, nominal model, native or RNG call."""
    root=Path(reference_root).resolve()
    descriptor=json.loads(Path(__file__).with_name("references.json").read_text())[phase]
    folder=root/descriptor["run"]
    for name, expected in descriptor["compact"].items():
        actual=identity(folder/name)
        if any(actual[key]!=expected[key] for key in ("sha256","bytes")):
            raise AssertionError("frozen B10 compact identity differs: "+name)
    config=json.loads((folder/"config.json").read_text())
    reading=json.loads((folder/"reading.json").read_text())
    if config["launch_sha"]!=descriptor["launch_sha"] or reading["status"]!="VERIFIED":
        raise AssertionError("frozen reference source or complete reader differs")
    current=b10_source_binding()
    if config["source_binding"]!=current:
        raise AssertionError("imported B10 dependencies differ from actual frozen references")
    if phase=="engineering" and not reading["exact_native_reference_C"]:
        raise AssertionError("old C=REFERENCE engineering evidence incomplete")
    rows=[r for r in json.loads((folder/"perworld.json").read_text()) if r["arm"] in ("C","H_A")]
    expected={(j["seed"],a) for j in jobs(phase) for a in ("C","H_A")}
    if len(rows)!=len(expected) or {(r["seed"],r["arm"]) for r in rows}!=expected:
        raise AssertionError("reference panel does not match exposed B11 worlds")
    for row in rows:
        if row["status"]!="completed" or row["actual_length"]!=HORIZON:
            raise AssertionError("reference is not a complete original mission")
        path=(folder/row["raw"]["path"]).resolve()
        if not path.is_relative_to((folder/"raw").resolve()):
            raise AssertionError("reference raw escaped canonical evidence")
        if verify_raw:
            actual=identity(path)
            if any(actual[k]!=row["raw"][k] for k in ("sha256","bytes")):
                raise AssertionError("frozen raw reference changed: "+str(path))
    return dict(root=str(root),directory=str(folder),phase=phase,
                descriptor=descriptor,rows=rows,raw_hashes_verified=bool(verify_raw),
                new_controller_calls=0,new_model_calls=0,new_native_calls=0)
