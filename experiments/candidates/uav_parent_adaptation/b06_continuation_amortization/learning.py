"""Lawful public features and the single, fixed B06 residual ridge solve.

This module reads already-paid evidence; it never queries a controller, native
host, radio model or stationary scorer. Artifact extraction is separate from fit.
"""
from copy import deepcopy
import gzip
import hashlib
import io
import json
from numbers import Integral
from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_fleet_transmission.control import decode_public_state


EXPECTED_SUMMARY_SHA256 = "df0d60b900d816bc93fed1855feca1afc9050dc2b719b017a7beb5d159a5cd7d"
WORLD_IDS = tuple(range(29326000, 29326016))
CHAMPION_COUNTS = (3, 4, 4, 4, 3, 4, 4, 4, 3, 3, 3, 4, 4, 3, 4, 4)
FEATURE_NAMES = (
    "stationary_J_advantage", "stationary_served_advantage", "tail_quality_advantage",
    "duration", "path", "current_height", "arrival_other_distance",
    "strict_nearest_fraction", "nearest_distance_change_mean",
    "nearest_distance_change_sd", "old_mask_fraction", "arrival_mask_fraction",
)
PENALTY = 0.1
ARTIFACT_SCHEMA = "b06-residual-ridge-v1"


def _integer(value, name, low, high):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer")
    value = int(value)
    if not low <= value <= high:
        raise ValueError(f"{name} out of range")
    return value


def _finite(value, name):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be finite numeric")
    value = float(value)
    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _positions(value):
    p = np.asarray(value, dtype=np.float64)
    if (p.shape != (8, 3) or not np.isfinite(p).all()
            or np.any(p < [0, 0, 50]) or np.any(p > [1000, 1000, 150])):
        raise ValueError("requires bounded finite eight-member geometry")
    return p


def _active(mask):
    return np.flatnonzero([(mask >> i) & 1 for i in range(8)])


def _nearest(positions, ground_users, mask):
    active = _active(mask)
    if len(active) == 0:
        return np.full(50, 2000.0, dtype=np.float64)
    return np.linalg.norm(ground_users[:, None] - positions[active], axis=2).min(axis=1)


def feature_matrix(public_report, old_mask, candidates, stay_score):
    """Twelve frozen columns, from the quantized report and stationary metadata."""
    if np.asarray(public_report).dtype != np.float32:
        raise ValueError("public report must retain its original FP32 dtype")
    positions, users = decode_public_state(public_report, 8)
    _positions(positions)
    if np.any(users < 0) or np.any(users > 1000):
        raise ValueError("public users outside native bounds")
    old_mask = _integer(old_mask, "old_mask", 0, 255)
    stay = {k: _finite(stay_score[k], f"stay {k}") for k in ("J", "served", "quality")}
    ground = np.column_stack((users, np.zeros(50, dtype=np.float64)))
    current_nearest = _nearest(positions, ground, old_mask)
    rows = []
    for c in candidates:
        member = _integer(c["member"], "member", 0, 7)
        _integer(c["site"], "site", 0, 99)
        mask = _integer(c["predicted_mask"], "predicted_mask", 0, 255)
        arrival = _positions(c["predicted_destination"])
        duration = _integer(c["duration"], "duration", 10, 40)
        if duration % 10:
            raise ValueError("duration must be ten-clock aligned")
        path = _finite(c["path"], "path")
        if path < 0:
            raise ValueError("path must be nonnegative")
        others = _active(mask & ~(1 << member))
        crowding = (float(np.linalg.norm(arrival[others] - arrival[member], axis=1).min())
                    if len(others) else 2000.0)
        arrival_active = _active(mask)
        # Each arrival user/transmitter distance is paid once and reused by both
        # nearest features. Only the distinct transmitter/transmitter crowding
        # pairs above require additional geometry.
        distances = np.linalg.norm(ground[:, None] - arrival[arrival_active], axis=2)
        arrival_nearest = distances.min(axis=1) if len(arrival_active) else np.full(50, 2000.0)
        if mask & (1 << member):
            own_column = int(np.flatnonzero(arrival_active == member)[0])
            own_distance = distances[:, own_column]
            other_distance = (distances[:, arrival_active != member].min(axis=1)
                              if len(others) else np.full(50, np.inf))
            strict_fraction = float(np.mean(own_distance < other_distance))
        else:
            strict_fraction = 0.0
        change = arrival_nearest - current_nearest
        rows.append([
            (_finite(c["predicted_total_J"], "stationary J") - 460 * stay["J"]) / 500,
            (_finite(c["predicted_total_served"], "stationary served") - 460 * stay["served"]) / 25000,
            _finite(c["tail_score"]["quality"], "tail quality") - stay["quality"],
            duration / 40, path / 1000, positions[member, 2] / 150,
            crowding / 1000, strict_fraction, float(change.mean()) / 1000,
            float(change.std(ddof=0)) / 1000, old_mask.bit_count() / 8, mask.bit_count() / 8,
        ])
    result = np.asarray(rows, dtype=np.float64).reshape(-1, 12)
    if not np.isfinite(result).all():
        raise ValueError("feature arithmetic must remain finite")
    return result


def _read_reference(reference, base, manifest, label, *, raw=False):
    """Parse only the bytes whose declared length and digest were verified."""
    path = Path(reference["path"])
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("unsafe artifact reference")
    if raw:
        if path.parts[0] != "raw" or len(path.parts) < 2:
            raise ValueError("expected raw/... artifact reference")
        path = Path(*path.parts[1:])
    base = Path(base).resolve()
    target = (base / path).resolve()
    if not target.is_relative_to(base):
        raise ValueError("artifact reference escapes root")
    payload = target.read_bytes()
    if (len(payload) != reference["bytes"]
            or hashlib.sha256(payload).hexdigest() != reference["sha256"]):
        raise ValueError(f"artifact byte/hash mismatch: {label}")
    manifest.append(dict(label=label, reference=deepcopy(reference), resolved_path=str(target)))
    return payload


def extract_paid_rows(summary_path, raw_root):
    """Extract the immutable 58/16 source, without fitting or querying a model.

    ``raw_root`` is the raw directory itself, not its parent. The returned JSON
    data retains each target/report/stationary source pointer and every T-episode
    artifact reference, including the complete branch raw files and traces.
    """
    summary_path = Path(summary_path).resolve()
    payload = summary_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SUMMARY_SHA256:
        raise ValueError("unbound paid summary hash")
    summary = json.loads(payload)
    spec = summary["config"]["spec"]
    if (summary["status"] != "complete" or spec["world_ids"] != list(WORLD_IDS)
            or (spec["n"], spec["horizon"], spec["option_t"], spec["cadence"]) != (8, 500, 40, 10)):
        raise ValueError("paid source protocol mismatch")
    references = []
    for key in ("config_artifact", "reading"):
        _read_reference(summary[key], summary_path.parent, references, key)
    episodes = [e for e in summary["episodes"] if e["arm"] == "T"]
    if sorted(e["world_id"] for e in episodes) != list(WORLD_IDS):
        raise ValueError("paid world identity mismatch")
    rows = []
    for world, expected_count in zip(WORLD_IDS, CHAMPION_COUNTS):
        e = next(e for e in episodes if e["world_id"] == world)
        prefix = f"world:{world}"
        _read_reference(e["raw"], raw_root, references, prefix + ":native", raw=True)
        trace_bytes = _read_reference(e["decisions"], raw_root, references, prefix + ":trace", raw=True)
        decisions = []
        with gzip.GzipFile(fileobj=io.BytesIO(trace_bytes)) as trace:
            for line_number, line in enumerate(trace):
                decision = json.loads(line)
                if decision["t"] == 40:
                    decisions.append((line_number, decision))
        if len(decisions) != 1:
            raise ValueError("requires exactly one original t40 decision")
        line_number, decision = decisions[0]
        old_mask = _integer(decision["old_mask"], "paid old mask", 1, 255)
        stay_score = decision["option"]["stay_score"]
        _read_reference(e["stationary_candidates"], raw_root, references, prefix + ":stationary", raw=True)
        branches = e["continuation"]["branches"]
        if (e["continuation"]["candidate_count"] != expected_count * 100
                or len(branches) != expected_count + 1
                or len({b["id"] for b in branches}) != len(branches)):
            raise ValueError("paid champion count/identity mismatch")
        artifacts = e["model_branches"]
        if (len(artifacts) != len(branches)
                or {a["id"] for a in artifacts} != {b["id"] for b in branches}):
            raise ValueError("paid branch artifact identity mismatch")
        raw_payloads = {}
        for a in artifacts:
            compact = next(b for b in branches if b["id"] == a["id"])
            if a["summary"] != compact["summary"]:
                raise ValueError("branch target summary mismatch")
            raw_payloads[a["id"]] = _read_reference(
                a["raw"], raw_root, references, prefix + ":model:" + a["id"], raw=True)
            _read_reference(a["decisions"], raw_root, references,
                            prefix + ":model-trace:" + a["id"], raw=True)
        stay_branch = next(b for b in branches if b["id"] == "stay")
        if stay_branch["stationary_candidate"] is not None:
            raise ValueError("stay cannot carry a stationary candidate")
        with np.load(io.BytesIO(raw_payloads["stay"]), allow_pickle=False) as archive:
            reports, times = archive["reports"], archive["report_times"]
            if (reports.shape != (46, 133) or reports.dtype != np.float32
                    or not np.isfinite(reports).all() or times.shape != (46,)
                    or times.dtype != np.int64 or not np.array_equal(times, np.arange(40, 500, 10))
                    or reports[0, -1] != np.float32(40 / 500)):
                raise ValueError("paid report shape/dtype/clock mismatch")
            public_report = reports[0].copy()
        trace_branches = decision["continuation"]["branches"]
        if {b["id"] for b in trace_branches} != {b["id"] for b in branches}:
            raise ValueError("t40 branch identity mismatch")
        candidates = [b for b in branches if b["id"] != "stay"]
        features = feature_matrix(public_report, old_mask,
                                  [b["stationary_candidate"] for b in candidates], stay_score)
        stay_total = _finite(stay_branch["summary"]["total_J"], "model stay J")
        for i, b in enumerate(candidates):
            traced = next(t for t in trace_branches if t["id"] == b["id"])
            if (traced["plan"]["selected"] != b["stationary_candidate"]
                    or traced["summary"] != b["summary"]):
                raise ValueError("t40 stationary/target provenance mismatch")
            a = next(a for a in artifacts if a["id"] == b["id"])
            stay_artifact = next(a for a in artifacts if a["id"] == "stay")
            target = (_finite(b["summary"]["total_J"], "model champion J") - stay_total) / 500 - features[i, 0]
            source = dict(
                report=dict(reference=deepcopy(stay_artifact["raw"]), array="reports", index=0),
                stationary=dict(reference=deepcopy(e["decisions"]), line=line_number, tick=40,
                                branch_id=b["id"], stay_score_path="option.stay_score",
                                candidate_reference=deepcopy(e["stationary_candidates"])),
                target=dict(kind="paid_complete_model_residual", branch_id=b["id"],
                            branch_raw=deepcopy(a["raw"]), stay_raw=deepcopy(stay_artifact["raw"]),
                            branch_summary=deepcopy(b["summary"]), stay_summary=deepcopy(stay_branch["summary"])),
            )
            rows.append(dict(world_id=world, branch_id=b["id"], features=features[i].tolist(),
                             target=float(target), source=source))
    manifest = dict(summary=dict(path=str(summary_path), bytes=len(payload), sha256=digest),
                    source_bindings=deepcopy(summary["config"]["source_bindings"]),
                    references=references, world_ids=list(WORLD_IDS),
                    champion_counts=list(CHAMPION_COUNTS), feature_names=list(FEATURE_NAMES),
                    label_kind="paid_complete_model_residual", row_count=len(rows))
    return dict(rows=rows, manifest=manifest)


def fit_rows(data):
    """One FP64 solve of the fixed equal-world, all-coefficient ridge objective."""
    rows, manifest = data["rows"], data["manifest"]
    if (manifest["summary"]["sha256"] != EXPECTED_SUMMARY_SHA256
            or manifest["world_ids"] != list(WORLD_IDS)
            or manifest["feature_names"] != list(FEATURE_NAMES)
            or manifest["label_kind"] != "paid_complete_model_residual"
            or manifest["row_count"] != 58 or len(rows) != 58):
        raise ValueError("unbound row manifest")
    identities = [(r["world_id"], r["branch_id"]) for r in rows]
    if len(set(identities)) != 58 or any(not r["source"] for r in rows):
        raise ValueError("missing or duplicate row source identity")
    if set(r["world_id"] for r in rows) != set(WORLD_IDS):
        raise ValueError("row world identity mismatch")
    counts = [sum(r["world_id"] == world for r in rows) for world in WORLD_IDS]
    if counts != list(CHAMPION_COUNTS) or manifest["champion_counts"] != counts:
        raise ValueError("row world counts mismatch")
    features = np.asarray([r["features"] for r in rows], dtype=np.float64)
    targets = np.asarray([r["target"] for r in rows], dtype=np.float64)
    if (features.shape != (58, 12) or targets.shape != (58,)
            or not np.isfinite(features).all() or not np.isfinite(targets).all()):
        raise ValueError("invalid finite training rows")
    by_world = dict(zip(WORLD_IDS, counts))
    weights = np.asarray([1 / (16 * by_world[r["world_id"]]) for r in rows], dtype=np.float64)
    means = np.sum(weights[:, None] * features, axis=0)
    constant = np.all(features == features[0], axis=0)
    means[constant] = features[0, constant]
    scales = np.sqrt(np.sum(weights[:, None] * (features - means) ** 2, axis=0))
    scales[(scales == 0) | constant] = 1.0
    standardized = (features - means) / scales
    design = np.column_stack((np.ones(58, dtype=np.float64), standardized))
    gram = design.T @ (weights[:, None] * design)
    system = gram + PENALTY * np.eye(13, dtype=np.float64)
    beta = np.linalg.solve(system, design.T @ (weights * targets))
    if not np.isfinite(beta).all():
        raise ValueError("ridge coefficients must be finite")
    prediction = design @ beta
    mse = float(np.sum(weights * (prediction - targets) ** 2))
    diagnostics = dict(weight_sum=float(weights.sum()), weighted_mse=mse,
                       zero_beta_weighted_mse=float(np.sum(weights * targets ** 2)),
                       penalty_value=float(PENALTY * (beta @ beta)),
                       objective=float(mse + PENALTY * (beta @ beta)),
                       coefficient_movement_l2=float(np.linalg.norm(beta)),
                       prediction_movement_rms=float(np.sqrt(np.sum(weights * prediction ** 2))),
                       system_condition=float(np.linalg.cond(system)),
                       constant_columns=np.flatnonzero(constant).tolist(), solve_count=1)
    return dict(schema=ARTIFACT_SCHEMA, beta=beta.tolist(), means=means.tolist(),
                scales=scales.tolist(), penalty=PENALTY, feature_names=list(FEATURE_NAMES),
                weights=weights.tolist(), row_identities=[dict(world_id=r["world_id"],
                    branch_id=r["branch_id"], source=deepcopy(r["source"])) for r in rows],
                source_manifest=deepcopy(manifest), diagnostics=diagnostics)


def choose_plan(artifact, bank, public_report, old_mask, *, timing=None):
    """Rank frozen member champions; exact zero coefficients delegate to R."""
    if (artifact["schema"] != ARTIFACT_SCHEMA or artifact["penalty"] != PENALTY
            or artifact["feature_names"] != list(FEATURE_NAMES)):
        raise ValueError("ranker artifact contract mismatch")
    beta = np.asarray(artifact["beta"], dtype=np.float64)
    means = np.asarray(artifact["means"], dtype=np.float64)
    scales = np.asarray(artifact["scales"], dtype=np.float64)
    if (beta.shape != (13,) or means.shape != (12,) or scales.shape != (12,)
            or not all(np.isfinite(a).all() for a in (beta, means, scales)) or np.any(scales <= 0)):
        raise ValueError("invalid ranker coefficients/scaler")
    champions, original = bank["champions"], bank["original_R"]
    candidates = [p["selected"] for p in champions]
    fc, fw = time.process_time(), time.perf_counter()
    features = feature_matrix(public_report, old_mask, candidates, original["stay_score"])
    if timing is not None:
        timing.update(feature_cpu_seconds=time.process_time()-fc, feature_wall_seconds=time.perf_counter()-fw)
    ic, iw = time.process_time(), time.perf_counter()
    standardized = (features - means) / scales
    residuals = beta[0] + standardized @ beta[1:]
    advantages = features[:, 0] + residuals
    if not np.isfinite(advantages).all():
        raise ValueError("prediction must remain finite")
    zero = bool(np.all(beta == 0))
    selected = None
    if zero:
        plan = original if original["initiated"] else None
    else:
        if len(champions):
            selected = max(range(len(champions)), key=lambda i: (
                advantages[i], candidates[i]["predicted_total_served"], -candidates[i]["path"],
                -candidates[i]["duration"], -candidates[i]["member"], -candidates[i]["site"]))
            if advantages[selected] <= 0:
                selected = None
        plan = champions[selected] if selected is not None else None
    record = dict(zero_beta_fallback=zero, features=features.tolist(),
                  standardized_features=standardized.tolist(), predicted_residuals=residuals.tolist(),
                  predicted_advantages=advantages.tolist(), selected_index=selected,
                  selected_member=plan["member"] if plan is not None else None,
                  selected_site=plan["site"] if plan is not None else None,
                  initiated=plan is not None,
                  feature_distance_pairs=50*int(old_mask).bit_count()+sum(
                      50*int(c["predicted_mask"]).bit_count()
                      + (int(c["predicted_mask"]) & ~(1 << c["member"])).bit_count() for c in candidates),
                  coefficient_products=13*len(candidates))
    result = deepcopy(plan)
    if timing is not None:
        timing.update(inference_cpu_seconds=time.process_time()-ic, inference_wall_seconds=time.perf_counter()-iw)
    return result, record
