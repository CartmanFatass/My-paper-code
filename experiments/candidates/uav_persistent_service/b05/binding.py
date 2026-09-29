"""Exact source and original R artifact bindings for the two complete panels."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from experiments.candidates.uav_persistent_service.b04.binding import (
    bind_source, sha256_file, verified_path, verify_raw_identity,
)
from .readout import HORIZON, PANELS, SEEDS, continuity_readings, recovery_readings


ROOT = Path("/home/wu/projects/HMASD/runs/uav_persistent_service")
ORIGINALS = {
    "original": {"tag": "b04_original_worlds_a01",
                 "source": "7bc0157f32caa8a1c29eb61e2ff483c6787b5f3e",
                 "manifest": "543146bb0193722de253d3d24a6bd16e77ec62ff967367555a83fed62c7b4442",
                 "artifacts": 29},
    "reassignment": {"tag": "b03_reassignment_a01",
                     "source": "a4bd3b5eccef6e83a71c00fdbb8eccd6ecaf5c67",
                     "manifest": "f8eb32c1e53178c508aee5c8394724ac05cda8282aeaf45c702598360bf0482b",
                     "artifacts": 75},
}


def verify_original_manifest(root: Path, specification: dict) -> dict:
    path = root/"manifest.json"
    if path.is_symlink() or sha256_file(path) != specification["manifest"]:
        raise ValueError("original R manifest identity differs")
    manifest = json.loads(path.read_text())
    artifacts = manifest["artifacts"]
    if (manifest["launch_sha"] != specification["source"]
            or len(artifacts) != specification["artifacts"]
            or manifest["storage_bytes"] != sum(item["bytes"] for item in artifacts.values())):
        raise ValueError("original manifest source/count/bytes differ")
    for name, item in artifacts.items():
        verified_path(root, name, item["sha256"], item["bytes"])
    return manifest


def bind_controls(root: Path = ROOT) -> tuple[dict[int, dict], dict]:
    controls, evidence, effective = {}, {}, None
    for panel, spec in ORIGINALS.items():
        old_root = root/spec["tag"]
        manifest = verify_original_manifest(old_root, spec)
        artifacts = manifest["artifacts"]
        config = json.loads((old_root/"config.json").read_text())
        summary = json.loads((old_root/"summary.json").read_text())
        rows = json.loads((old_root/"perworld.json").read_text())
        selected = [row for row in rows if row["arm"] == "R"]
        if (config["launch_sha"] != spec["source"] or config["horizon"] != HORIZON
                or tuple(config["seeds"]) != PANELS[panel]
                or config["shield"] != {"enter_margin": 0.0, "exit_margin": .05}
                or summary["status"] != "complete" or summary["launch_sha"] != spec["source"]
                or len(selected) != 8 or {row["seed"] for row in selected} != set(PANELS[panel])):
            raise ValueError("original R configuration or full result differs")
        identities = []
        for row in selected:
            seed = row["seed"]
            if (row["status"] != "completed" or row["actual_length"] != HORIZON
                    or row["job_key"] != f"R/{seed}"):
                raise ValueError("original R endpoint identity differs")
            for field in ("raw", "decisions"):
                record = artifacts[row[f"{field}_path"]]
                if row[f"{field}_sha256"] != record["sha256"]:
                    raise ValueError("original row and manifest artifact disagree")
            if row["raw_bytes"] != artifacts[row["raw_path"]]["bytes"]:
                raise ValueError("original raw size differs")
            if effective is None:
                effective = row["effective_config"]
            elif effective != row["effective_config"]:
                raise ValueError("original R effective configurations disagree")
            decisions = json.loads((old_root/row["decisions_path"]).read_text())
            with np.load(old_root/row["raw_path"], allow_pickle=False) as raw:
                verify_raw_identity(raw, row)
                extra = continuity_readings(raw) | recovery_readings(raw, decisions["events"])
            controls[seed] = row | extra | {"control_root": str(old_root)}
            identities.append({key: row[key] for key in (
                "seed", "arm", "job_key", "actual_length", "raw_path", "raw_sha256", "raw_bytes",
                "decisions_path", "decisions_sha256", "initial_state_sha256", "ground_bs_sha256",
                "user_xy_trace_sha256", "rng_state_stream_sha256")})
        evidence[panel] = {"root": str(old_root), "source_sha": spec["source"],
                           "manifest_sha256": spec["manifest"], "verified_artifacts": len(artifacts),
                           "verified_bytes": manifest["storage_bytes"], "rows": identities}
    if set(controls) != set(SEEDS):
        raise ValueError("missing/duplicate original R controls")
    return controls, {"panels": evidence, "effective_config": effective,
                      "reuse_scope": "exact R only; original P/O_H retained but not compared anew"}


def verify_pair(out: Path, row: dict, control: dict) -> dict:
    seed = int(row["seed"])
    try:
        if row["arm"] != "S" or row["job_key"] != f"S/{seed}" or control["seed"] != seed:
            raise ValueError("new/control row identity differs")
        if (row["effective_config"] != control["effective_config"]
                or any(not control.get(field) or row.get(field) != control[field]
                       for field in ("initial_state_sha256", "ground_bs_sha256"))):
            raise ValueError("new/control config or initial world differs")
        path = verified_path(out, row["raw_path"], row["raw_sha256"], row["raw_bytes"])
        verified_path(out, row["decisions_path"], row["decisions_sha256"])
        old_path = verified_path(Path(control["control_root"]), control["raw_path"],
                                 control["raw_sha256"], control["raw_bytes"])
        with np.load(path, allow_pickle=False) as raw:
            new = verify_raw_identity(raw, row)
            new_battery = raw["initial_native_battery"].copy()
        with np.load(old_path, allow_pickle=False) as raw:
            old = verify_raw_identity(raw, control)
            old_battery = raw["initial_native_battery"].copy()
        prefix = min(row["actual_length"], control["actual_length"])+1
        if (not np.array_equal(new[0][:prefix], old[0][:prefix])
                or not np.array_equal(new[1][:prefix], old[1][:prefix])
                or not np.array_equal(new_battery, old_battery)):
            raise ValueError("complete common-prefix exogenous or initial battery arrays differ")
        full = row["actual_length"] == control["actual_length"]
        if full and any(row.get(field) != control.get(field)
                        for field in ("user_xy_trace_sha256", "rng_state_stream_sha256")):
            raise ValueError("full exogenous stream digests disagree")
        return {"status": "verified", "seed": seed, "prefix_states": prefix,
                "equal_length": full, "users_equal": True, "rng_equal": True,
                "initial_battery_equal": True}
    except (OSError, KeyError, TypeError, ValueError) as error:
        return {"status": "failed", "seed": seed, "error": f"{type(error).__name__}: {error}"}
