"""One admitted paid-row solve, with a separate scalar/numerical audit."""
from copy import deepcopy
import json
import math
import platform
import re
import time

import numpy as np

from experiments.candidates.uav_fleet_transmission.b03.reader import checked_path, load_arrays, load_decisions
from experiments.candidates.uav_fleet_transmission.study import artifact, process_resources, write_json
from .contract import PAID_RAW, PAID_SUMMARY, fixed_config, source_bindings
from .learning import ARTIFACT_SCHEMA, FEATURE_NAMES, PENALTY, extract_paid_rows, fit_rows


def scalar_features(report, old_mask, candidates, stay):
    """Independent scalar feature arithmetic; no scorer, host, or learned call."""
    if np.asarray(report).shape != (133,) or np.asarray(report).dtype != np.float32:
        raise ValueError("feature audit requires the original public FP32 report")
    p = [[float(report[3*i])*1000, float(report[3*i+1])*1000,
          float(report[3*i+2])*100+50] for i in range(8)]
    users = [[float(report[32+2*u])*1000, float(report[33+2*u])*1000, 0.] for u in range(50)]

    def nearest(positions, mask):
        active = [i for i in range(8) if mask & (1 << i)]
        return [min(math.dist(user, positions[i]) for i in active) if active else 2000. for user in users]

    current = nearest(p, old_mask)
    rows = []
    for c in candidates:
        member, mask, destination = c["member"], c["predicted_mask"], c["predicted_destination"]
        other = [i for i in range(8) if i != member and mask & (1 << i)]
        crowding = min((math.dist(destination[member], destination[i]) for i in other), default=2000.)
        strict = sum(math.dist(u, destination[member]) < min(
            (math.dist(u, destination[i]) for i in other), default=math.inf) for u in users) / 50 if mask & (1 << member) else 0.
        changes = [after - before for after, before in zip(nearest(destination, mask), current)]
        mean = math.fsum(changes) / 50
        sd = math.sqrt(math.fsum((x-mean)**2 for x in changes) / 50)
        rows.append([(c["predicted_total_J"]-460*stay["J"])/500,
                     (c["predicted_total_served"]-460*stay["served"])/25000,
                     c["tail_score"]["quality"]-stay["quality"], c["duration"]/40,
                     c["path"]/1000, p[member][2]/150, crowding/1000, strict,
                     mean/1000, sd/1000, old_mask.bit_count()/8, mask.bit_count()/8])
    return np.asarray(rows, dtype=np.float64).reshape(-1, 12)


def logical_manifest(value):
    """Machine/snapshot absolute paths are provenance, not distinct training rows."""
    value = deepcopy(value)
    value["summary"].pop("path", None)
    for reference in value["references"]:
        reference.pop("resolved_path", None)
    return value


def audit_training_data(data):
    expected = extract_paid_rows(PAID_SUMMARY, PAID_RAW)
    if data["rows"] != expected["rows"] or logical_manifest(data["manifest"]) != logical_manifest(expected["manifest"]):
        raise ValueError("saved training rows or paid source bindings differ")
    summary = json.loads(PAID_SUMMARY.read_text())
    errors = []
    for episode in (e for e in summary["episodes"] if e["arm"] == "T"):
        trace = load_decisions(PAID_RAW.parent / episode["decisions"]["path"])
        decision = trace[40]
        branches = episode["continuation"]["branches"]
        stay = next(b for b in episode["model_branches"] if b["id"] == "stay")
        report = load_arrays(PAID_RAW.parent / stay["raw"]["path"])["reports"][0]
        champions = [b for b in branches if b["id"] != "stay"]
        features = scalar_features(report, decision["old_mask"],
                                   [b["stationary_candidate"] for b in champions], decision["option"]["stay_score"])
        for index, branch in enumerate(champions):
            row = next(r for r in data["rows"] if (r["world_id"], r["branch_id"]) == (episode["world_id"], branch["id"]))
            error = float(np.max(np.abs(np.asarray(row["features"])-features[index])))
            errors.append(error)
            target = (branch["summary"]["total_J"]-stay["summary"]["total_J"])/500-features[index, 0]
            if error > 1e-12 or abs(row["target"]-target) > 1e-12:
                raise ValueError("independent scalar paid feature/target audit differs")
    return {"rows": 58, "worlds": 16, "references": len(data["manifest"]["references"]),
            "maximum_scalar_feature_error": max(errors), "new_scorer_requests": 0, "new_native_steps": 0}


def audit_solution(data, fitted, *, resolve=True):
    """Verify by scalar scaling and augmented least squares, not a second fit choice."""
    rows = data["rows"]
    x = np.asarray([r["features"] for r in rows], dtype=np.float64)
    y = np.asarray([r["target"] for r in rows], dtype=np.float64)
    counts = {w: sum(r["world_id"] == w for r in rows) for w in data["manifest"]["world_ids"]}
    weights = np.asarray([1/(16*counts[r["world_id"]]) for r in rows])
    mean = np.asarray([math.fsum(weights[i]*x[i,j] for i in range(58)) for j in range(12)])
    constant = np.all(x == x[0], axis=0)
    mean[constant] = x[0, constant]
    scales = np.asarray([math.sqrt(math.fsum(weights[i]*(x[i,j]-mean[j])**2 for i in range(58))) for j in range(12)])
    scales[(scales == 0) | constant] = 1.
    if (fitted["schema"] != ARTIFACT_SCHEMA or fitted["penalty"] != PENALTY
            or fitted["feature_names"] != list(FEATURE_NAMES)
            or logical_manifest(fitted["source_manifest"]) != logical_manifest(data["manifest"])
            or fitted["row_identities"] != [{k: r[k] for k in ("world_id", "branch_id", "source")} for r in rows]):
        raise ValueError("fitted objective/lineage differs")
    for name, expected in (("means", mean), ("scales", scales), ("weights", weights)):
        if not np.allclose(fitted[name], expected, rtol=1e-12, atol=1e-12):
            raise ValueError("independent fitted scaler/weights differ: " + name)
    design = np.column_stack((np.ones(58), (x-mean)/scales))
    augmented = np.vstack((np.sqrt(weights)[:, None]*design, math.sqrt(PENALTY)*np.eye(13)))
    target = np.concatenate((np.sqrt(weights)*y, np.zeros(13)))
    beta = np.asarray(fitted["beta"], dtype=np.float64)
    if resolve:
        expected, _, rank, _ = np.linalg.lstsq(augmented, target, rcond=None)
    else:
        # Evaluation checks the fixed normal equation only; positive ridge
        # already makes the13-column system full rank. No additional solve.
        expected, rank = beta, 13
    gradient = design.T @ (weights*(design@beta-y)) + PENALTY*beta
    if (beta.shape != (13,) or not np.isfinite(beta).all() or rank != 13
            or not np.allclose(beta, expected, rtol=1e-12, atol=1e-12)
            or np.max(np.abs(gradient)) > 1e-12):
        raise ValueError("independent ridge equation/solution audit differs")
    prediction = design@beta
    mse = float(np.sum(weights*(prediction-y)**2))
    diagnostics = fitted["diagnostics"]
    checks = {"weight_sum": float(weights.sum()), "weighted_mse": mse,
              "zero_beta_weighted_mse": float(np.sum(weights*y*y)),
              "penalty_value": float(PENALTY*(beta@beta)),
              "objective": mse+float(PENALTY*(beta@beta)),
              "coefficient_movement_l2": float(np.linalg.norm(beta)),
              "prediction_movement_rms": float(np.sqrt(np.sum(weights*prediction**2))),
              "system_condition": float(np.linalg.cond(design.T@(weights[:,None]*design)+PENALTY*np.eye(13)))}
    if (diagnostics["solve_count"] != 1 or diagnostics["constant_columns"] != np.flatnonzero(constant).tolist()
            or any(not math.isclose(diagnostics[k], v, rel_tol=1e-11, abs_tol=1e-12) for k,v in checks.items())):
        raise ValueError("fitted diagnostics differ")
    return {"rank": int(rank), "verification_lstsq_solves": int(resolve), "new_scientific_fits": 0,
            "maximum_beta_error": float(np.max(np.abs(beta-expected))) if resolve else None,
            "maximum_normal_equation_residual": float(np.max(np.abs(gradient))), "diagnostics": checks}


def validate_operation(summary, out, phase, fit_sha256=None):
    config = summary["config"]
    expected = fixed_config(phase, fit_sha256)
    if (any(config.get(k) != v for k,v in expected.items())
            or set(config) != set(expected) | {"launch_sha", "admission_command_sha256", "versions"}
            or not re.fullmatch(r"[0-9a-f]{40}", summary["launch_sha"])
            or summary["launch_sha"] != config["launch_sha"]
            or not re.fullmatch(r"[0-9a-f]{64}", config["admission_command_sha256"])):
        raise ValueError("fixed source/configuration/admission identity differs")
    path = checked_path(out, summary["config_artifact"])
    if path != out/"config.json" or json.loads(path.read_text()) != config:
        raise ValueError("bound saved configuration differs")
    manifest = json.loads((out/"launch-manifest.json").read_text())
    if (manifest.get("acceptance") != "accepted" or manifest.get("sha") != summary["launch_sha"]
            or manifest.get("direction") != config["direction"]
            or manifest.get("command_sha256") != config["admission_command_sha256"]):
        raise ValueError("accepted launch manifest differs")


def run_fit(out, launch_sha, admission):
    wall, cpu = time.perf_counter(), time.process_time()
    config = dict(fixed_config("fit"), launch_sha=launch_sha,
                  admission_command_sha256=admission["command_sha256"],
                  versions={"python": platform.python_version(), "numpy": np.__version__})
    out.mkdir(parents=True, exist_ok=True)
    if any((out/name).exists() for name in ("summary.json", "config.json", "ranker.json", "training_rows.json", "reading.json")):
        raise FileExistsError("existing B06 fit attempt; no implicit refit")
    write_json(out/"config.json", config)
    summary = {"launch_sha": launch_sha, "config": config, "config_artifact": artifact(out/"config.json", out),
               "status": "extracting", "new_fits": 0, "updates": 0, "new_native_steps": 0,
               "new_scorer_requests": 0, "new_training_acquisition": 0}
    write_json(out/"summary.json", summary)
    try:
        ec, ew = time.process_time(), time.perf_counter()
        data = extract_paid_rows(PAID_SUMMARY, PAID_RAW)
        summary["extraction_timing"] = {"cpu_seconds": time.process_time()-ec, "wall_seconds": time.perf_counter()-ew}
        write_json(out/"training_rows.json", data)
        summary["training_rows"] = artifact(out/"training_rows.json", out)
        summary["status"], summary["new_fits"] = "fitting", 1
        write_json(out/"summary.json", summary)
        fc, fw = time.process_time(), time.perf_counter()
        fitted = fit_rows(data)
        summary["fit_kernel_timing"] = {"cpu_seconds": time.process_time()-fc, "wall_seconds": time.perf_counter()-fw}
        write_json(out/"ranker.json", fitted)
        summary["ranker"] = artifact(out/"ranker.json", out)
        summary["status"] = "collected"
        summary["worker_timing"] = {"cpu_seconds": time.process_time()-cpu, "wall_seconds": time.perf_counter()-wall}
        write_json(out/"summary.json", summary)
        validate_operation(summary, out, "fit")
        rc, rw = time.process_time(), time.perf_counter()
        reading = {"status": "complete", "source_sha": launch_sha, "ranker": summary["ranker"],
                   "training_rows": summary["training_rows"], "data_audit": audit_training_data(data),
                   "numerical_audit": audit_solution(data, fitted)}
        if source_bindings() != config["source_bindings"]:
            raise ValueError("source inputs changed during fit")
        reading["timing"] = {"cpu_seconds": time.process_time()-rc, "wall_seconds": time.perf_counter()-rw}
        write_json(out/"reading.json", reading)
        summary["reading"], summary["status"] = artifact(out/"reading.json", out), "complete"
        summary["total_timing"] = {"cpu_seconds": time.process_time()-cpu, "wall_seconds": time.perf_counter()-wall,
                                   "process_resources": process_resources()}
        write_json(out/"summary.json", summary)
        return summary
    except BaseException as exc:
        summary["failure_stage"] = summary["status"]
        summary["status"], summary["error"] = "failed", f"{type(exc).__name__}: {exc}"
        summary["failed_timing"] = {"cpu_seconds": time.process_time()-cpu, "wall_seconds": time.perf_counter()-wall}
        write_json(out/"summary.json", summary)
        raise
