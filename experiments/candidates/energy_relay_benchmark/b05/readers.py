"""Readers of ``b05_canonical_frame_a01`` (zero episodes): b04's deployment readers plus the b05 additions.

Inputs are B05 panel runs (``panels/<name>.json`` + ``traces/<name>.npz`` written by
``b05/evaluation.py``) and reference panels without traces (a B01/B02 ``panels/*.json`` with
``worlds`` rows, or b04 Block 2 ``paired_rotation.json`` whose ``local_id_rows`` are read).

Per traced panel (reused from ``b04/deployment_readers.py``): legacy and stratified headings
(``by_corner``), first service with the -1 fix (all-worlds denominator, censoring, served within
60/120, and the no-access-user-at-t = 0 subgroup keyed by seed from the panel rows'
``users_in_access_range_t0`` or an ``--access`` b04 ``conditions.json``), speed saturation.
Added here:

* ``inward``: net inward displacement per UAV over the first ``INWARD_STEPS`` steps = projection
  of xy[100] - xy[0] onto the unit vector from xy[0] to the arena centre (4000, 4000) m; median,
  IQR, mean and n per spawn corner and pooled.
* ``decomposition``: per UAV-step t < window (``DECOMPOSITION_WINDOW`` and the full trace):
  |raw proposal xy| (C_SW_FULL: before rescaling), |post-shield action xy|, actual horizontal
  displacement |xy[t+1] - xy[t]| (m); strata normal mode (shield off at t) / all, free space (not
  within ``WALL_M`` of a wall at t) / at wall; plus the shares of saturated actual displacement
  (>= 29 m, b04's threshold) and of post-shield |a_xy| >= 1.
* ``persistence``: circular resultant length R of the step headings (actual displacement >= 1 m)
  in consecutive non-overlapping ``PERSISTENCE_STEPS``-step windows per UAV within the window,
  windows with >= 2 moving steps; all windows and windows wholly in normal mode.
* ``pairs``: per named pair A:B, per-world A - B on the paired metrics with paired SE, overall
  and by spawn corner, the boundary shares (normal mode) of both sides by corner, and the worlds
  where A's QoS/step is below B's.  Corners come from any trace holding the seed (spawn corner is
  a world property: team-mean reset xy against the area centre, as b04 ``headings``).

Every source is recorded with its path and sha256; the reader draws no random number.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np

from ..b04 import deployment_readers as dr

AREA_M = dr.DEFAULT_AREA_M
CENTRE_M = (AREA_M / 2.0, AREA_M / 2.0)
WALL_M = dr.DEFAULT_WALL_M
INWARD_STEPS = 100
DECOMPOSITION_WINDOW = dr.SPEED_WINDOW          # 1000, b04's speed window; full trace also read
PERSISTENCE_STEPS = 10
MOVE_M = dr.DEFAULT_MOVE_M
SATURATION_M = dr.SPEED_SATURATION_M
CORNERS = ("W,S", "W,N", "E,S", "E,N")
PAIRED_METRICS = ("qos_per_step", "raw_native_J", "return_constraint_cost_sum",
                  "episode_minimum_battery_ratio", "boundary_share_normal_mode",
                  "first_service_step")


def corner_label(xyz, area_m: float = AREA_M) -> str:
    """Spawn corner of one world from its trace own_xyz [T, n, 3] (team mean at t = 0)."""
    centre = np.asarray(xyz, dtype=np.float64)[0, :, :2].mean(axis=0)
    return f"{'E' if centre[0] > area_m / 2.0 else 'W'},{'N' if centre[1] > area_m / 2.0 else 'S'}"


def load_trace(path) -> list[dict[str, Any]]:
    """b04 ``load_worlds`` rows (seed, xyz, qos) + mode and the b05 arrays when present."""
    worlds = dr.load_worlds(path)
    modes = dr.load_modes(path)
    archive = np.load(path)
    indices = sorted({key.split("_")[1] for key in archive.files if key.endswith("_own_xyz")}, key=int)
    for world, mode, index in zip(worlds, modes, indices, strict=True):
        world["mode"] = mode
        for key in ("proposal", "submitted", "proposal_raw", "frame", "users_in_access_range_t0"):
            name = f"world_{index}_{key}"
            if name in archive.files:
                world[key] = np.asarray(archive[name])
        world["corner"] = corner_label(world["xyz"])
    return worlds


def _quantiles(values) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {"n": 0, "median": None, "q25": None, "q75": None, "mean": None}
    q25, median, q75 = np.percentile(values, [25, 50, 75])
    return {"n": int(values.size), "median": round(float(median), 4), "q25": round(float(q25), 4),
            "q75": round(float(q75), 4), "mean": round(float(values.mean()), 4)}


def _by_corner(worlds, per_world) -> dict[str, Any]:
    """{pooled, by_corner} of ``_quantiles`` over the concatenated per-world value arrays."""
    pooled = [np.ravel(per_world(w)) for w in worlds]
    result = {"pooled": _quantiles(np.concatenate(pooled) if pooled else [])}
    result["by_corner"] = {}
    for corner in CORNERS:
        chosen = [np.ravel(per_world(w)) for w in worlds if w["corner"] == corner]
        if chosen:
            result["by_corner"][corner] = {"worlds": len(chosen), **_quantiles(np.concatenate(chosen))}
    return result


def inward_displacement(xyz, steps: int = INWARD_STEPS, centre=CENTRE_M) -> np.ndarray:
    """Per UAV: (xy[steps] - xy[0]) . unit(centre - xy[0]) in metres (0 where xy[0] is the centre)."""
    xy = np.asarray(xyz, dtype=np.float64)[:, :, :2]
    last = min(int(steps), xy.shape[0] - 1)
    displacement = xy[last] - xy[0]
    toward = np.asarray(centre, dtype=np.float64) - xy[0]
    distance = np.linalg.norm(toward, axis=-1)
    unit = np.divide(toward, distance[:, None], out=np.zeros_like(toward), where=distance[:, None] > 0)
    return np.sum(displacement * unit, axis=-1)


def inward_summary(worlds, steps: int = INWARD_STEPS) -> dict[str, Any]:
    return {"steps": int(steps), "centre_m": list(CENTRE_M), "unit": "m per UAV",
            **_by_corner(worlds, lambda w: inward_displacement(w["xyz"], steps))}


def _step_arrays(world, window: int | None):
    """Per UAV-step arrays for t < min(window, T - 1): raw, shielded, actual, normal, free."""
    xy = np.asarray(world["xyz"], dtype=np.float64)[:, :, :2]
    steps = xy.shape[0] - 1 if window is None else min(int(window), xy.shape[0] - 1)
    raw_source = world.get("proposal_raw", world.get("proposal"))
    raw = (np.linalg.norm(np.asarray(raw_source, dtype=np.float64)[:steps, :, :2], axis=-1)
           if raw_source is not None else None)
    shielded = (np.linalg.norm(np.asarray(world["submitted"], dtype=np.float64)[:steps, :, :2], axis=-1)
                if "submitted" in world else None)
    actual = np.linalg.norm(xy[1:steps + 1] - xy[:steps], axis=-1)
    position = xy[:steps]
    at_wall = ((position[..., 0] <= WALL_M) | (position[..., 0] >= AREA_M - WALL_M)
               | (position[..., 1] <= WALL_M) | (position[..., 1] >= AREA_M - WALL_M))
    normal = ~np.asarray(world["mode"][:steps], dtype=bool)
    return raw, shielded, actual, normal, ~at_wall


def decomposition(worlds, window: int | None = DECOMPOSITION_WINDOW) -> dict[str, Any]:
    """Raw proposal -> post-shield action -> actual displacement magnitudes by stratum and corner."""
    strata = {"normal_free": lambda n, f: n & f, "normal_wall": lambda n, f: n & ~f,
              "all_free": lambda n, f: f, "all_wall": lambda n, f: ~f, "all": lambda n, f: n | ~n}

    def block(chosen):
        out = {}
        for label, select in strata.items():
            raw_values, shielded_values, actual_values = [], [], []
            for world in chosen:
                raw, shielded, actual, normal, free = _step_arrays(world, window)
                mask = select(normal, free)
                actual_values.append(actual[mask])
                if raw is not None:
                    raw_values.append(raw[mask])
                if shielded is not None:
                    shielded_values.append(shielded[mask])
            actual_all = np.concatenate(actual_values) if actual_values else np.zeros(0)
            shielded_all = np.concatenate(shielded_values) if shielded_values else np.zeros(0)
            out[label] = {
                "uav_steps": int(actual_all.size),
                "raw_proposal_norm": _quantiles(np.concatenate(raw_values)) if raw_values else None,
                "post_shield_norm": _quantiles(shielded_all) if shielded_values else None,
                "actual_displacement_m": _quantiles(actual_all),
                "actual_saturated_share": (round(float(np.mean(actual_all >= SATURATION_M)), 4)
                                           if actual_all.size else None),
                "post_shield_unit_norm_share": (round(float(np.mean(shielded_all >= 1.0)), 4)
                                                if shielded_all.size else None)}
        return out

    result = {"window": window, "wall_m": WALL_M, "saturation_m": SATURATION_M,
              "raw_source": "proposal_raw when present (C_SW_FULL), else proposal",
              "pooled": block(worlds), "by_corner": {}}
    for corner in CORNERS:
        chosen = [w for w in worlds if w["corner"] == corner]
        if chosen:
            result["by_corner"][corner] = {"worlds": len(chosen), **block(chosen)}
    return result


def persistence_values(world, window: int | None = DECOMPOSITION_WINDOW,
                       length: int = PERSISTENCE_STEPS, move_m: float = MOVE_M):
    """(R over all windows, R over windows wholly in normal mode) for one world, per UAV x window."""
    xy = np.asarray(world["xyz"], dtype=np.float64)[:, :, :2]
    steps = xy.shape[0] - 1 if window is None else min(int(window), xy.shape[0] - 1)
    delta = xy[1:steps + 1] - xy[:steps]
    speed = np.linalg.norm(delta, axis=-1)
    normal = ~np.asarray(world["mode"][:steps], dtype=bool)
    every, normal_only = [], []
    for start in range(0, steps - length + 1, length):
        chunk, moving = delta[start:start + length], speed[start:start + length] >= move_m
        for agent in range(xy.shape[1]):
            keep = moving[:, agent]
            if keep.sum() < 2:
                continue
            unit = chunk[keep, agent] / speed[start:start + length][keep, agent][:, None]
            r = float(np.linalg.norm(unit.mean(axis=0)))
            every.append(r)
            if normal[start:start + length, agent].all():
                normal_only.append(r)
    return np.asarray(every), np.asarray(normal_only)


def persistence_summary(worlds, window: int | None = DECOMPOSITION_WINDOW,
                        length: int = PERSISTENCE_STEPS) -> dict[str, Any]:
    cache = {id(w): persistence_values(w, window, length) for w in worlds}
    return {"window": window, "window_steps": int(length), "move_m": MOVE_M,
            "all_windows": _by_corner(worlds, lambda w: cache[id(w)][0]),
            "normal_mode_windows": _by_corner(worlds, lambda w: cache[id(w)][1])}


def load_rows(path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "worlds" in payload and isinstance(payload["worlds"], list):
        return payload["worlds"]
    if isinstance(payload, dict) and "local_id_rows" in payload:
        return payload["local_id_rows"]
    raise ValueError(f"{path}: neither a panel (worlds rows) nor a Block 2 paired_rotation.json")


def _paired_stats(differences) -> dict[str, Any]:
    diff = np.asarray(differences, dtype=np.float64)
    return {"n": int(diff.size), "mean": float(diff.mean()) if diff.size else None,
            "paired_se": float(diff.std(ddof=1) / np.sqrt(diff.size)) if diff.size > 1 else None,
            "positive": int((diff > 0).sum()), "negative": int((diff < 0).sum()),
            "zero": int((diff == 0).sum())}


def paired(rows_a, rows_b, corners: dict[int, str]) -> dict[str, Any]:
    """A - B per world on ``PAIRED_METRICS`` (worlds where both sides have the value), overall and
    by corner; boundary shares by corner; worlds where A's QoS/step < B's."""
    by_a = {int(r["seed"]): r for r in rows_a if not r.get("failed")}
    by_b = {int(r["seed"]): r for r in rows_b if not r.get("failed")}
    seeds = sorted(set(by_a) & set(by_b))
    result: dict[str, Any] = {"paired_worlds": len(seeds), "only_a": sorted(set(by_a) - set(by_b)),
                              "only_b": sorted(set(by_b) - set(by_a)), "metrics": {}}
    for metric in PAIRED_METRICS:
        usable = [s for s in seeds if by_a[s].get(metric) is not None and by_b[s].get(metric) is not None]
        diffs = {s: float(by_a[s][metric]) - float(by_b[s][metric]) for s in usable}
        block = {"overall": _paired_stats(list(diffs.values())), "by_corner": {},
                 "differences": {str(s): d for s, d in diffs.items()}}
        for corner in (*CORNERS, "unknown"):
            chosen = [d for s, d in diffs.items() if corners.get(s, "unknown") == corner]
            if chosen:
                block["by_corner"][corner] = _paired_stats(chosen)
        result["metrics"][metric] = block
    shares = {}
    for label, by in (("a", by_a), ("b", by_b)):
        shares[label] = {}
        for corner in (*CORNERS, "unknown"):
            values = [by[s]["boundary_share_normal_mode"] for s in seeds
                      if corners.get(s, "unknown") == corner
                      and by[s].get("boundary_share_normal_mode") is not None]
            if values:
                shares[label][corner] = {"n": len(values), "mean": float(np.mean(values))}
    result["boundary_share_normal_mode_by_corner"] = shares
    qos = result["metrics"]["qos_per_step"]["differences"]
    result["worlds_a_below_b_qos"] = sorted(int(s) for s, d in qos.items() if d < 0)
    return result


def _sha256(path) -> str:
    return dr.sha256_of(path)


def _git_head():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[4],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:   # pragma: no cover
        return None


def trace_of(panel_path) -> Path:
    panel_path = Path(panel_path)
    return panel_path.parent.parent / "traces" / (panel_path.stem + ".npz")


def read_panel(panel_path, access: dict[int, int] | None = None):
    """(readings, worlds) of one traced B05 panel."""
    rows = load_rows(panel_path)
    worlds = load_trace(trace_of(panel_path))
    access_rows = {int(r["seed"]): int(r["users_in_access_range_t0"]) for r in rows
                   if r.get("users_in_access_range_t0") is not None}
    access_used = access_rows or access
    return {
        "worlds": len(worlds), "seeds": [w["seed"] for w in worlds],
        "corners": {str(w["seed"]): w["corner"] for w in worlds},
        "frames": {str(r["seed"]): r.get("frame") for r in rows},
        "heading": {"legacy": dr.heading_summary(worlds),
                    "stratified": dr.stratified_heading_summary(worlds)},
        "first_service": dr.first_service_summary(worlds),
        "first_service_conditional": (
            dr.conditional_first_service(worlds, access_used) if access_used
            else {"reason": "no users_in_access_range_t0 in the panel rows and no --access file"}),
        "first_service_access_source": ("panel rows" if access_rows else
                                        "--access conditions.json" if access else None),
        "speed_saturation": dr.speed_saturation(worlds, [w["mode"] for w in worlds]),
        "inward": inward_summary(worlds),
        "decomposition": {"window": decomposition(worlds, DECOMPOSITION_WINDOW),
                          "full": decomposition(worlds, None)},
        "persistence": {"window": persistence_summary(worlds, DECOMPOSITION_WINDOW),
                        "full": persistence_summary(worlds, None)},
    }, worlds


def load_access(path) -> dict[int, int]:
    worlds = json.loads(Path(path).read_text(encoding="utf-8"))["worlds"]
    return {int(seed): int(row["users_in_access_range_t0"]) for seed, row in worlds.items()}


def read(out, *, panels: dict[str, str], references: dict[str, str] | None = None,
         pairs: dict[str, tuple[str, str]] | None = None, access_path: str | None = None,
         argv=None) -> dict[str, Any]:
    """``readers.json`` + ``manifest.json`` under ``out`` (refuses to overwrite)."""
    out = Path(out)
    if (out / "readers.json").exists() or (out / "manifest.json").exists():
        raise FileExistsError(f"reader output already exists: {out}")
    references = dict(references or {})
    pairs = dict(pairs or {})
    overlap = set(panels) & set(references)
    if overlap:
        raise ValueError(f"labels used twice: {sorted(overlap)}")
    access = load_access(access_path) if access_path else None
    sources, per_panel, rows, corners = {}, {}, {}, {}
    for label, path in panels.items():
        reading, worlds = read_panel(path, access)
        per_panel[label] = reading
        rows[label] = load_rows(path)
        for world in worlds:
            corners.setdefault(int(world["seed"]), world["corner"])
        trace = trace_of(path)
        sources[label] = {"panel": str(path), "panel_sha256": _sha256(path),
                          "trace": str(trace), "trace_sha256": _sha256(trace)}
    for label, path in references.items():
        rows[label] = load_rows(path)
        sources[label] = {"reference": str(path), "sha256": _sha256(path), "traced": False}
    pair_out = {}
    for name, (a, b) in pairs.items():
        if a not in rows or b not in rows:
            raise ValueError(f"pair {name}: unknown label {a if a not in rows else b}")
        pair_out[name] = {"a": a, "b": b, "a_source": sources[a], "b_source": sources[b],
                          **paired(rows[a], rows[b], corners)}
    payload = {"panels": per_panel, "pairs": pair_out,
               "parameters": {"area_m": AREA_M, "centre_m": list(CENTRE_M), "wall_m": WALL_M,
                              "inward_steps": INWARD_STEPS,
                              "decomposition_window": DECOMPOSITION_WINDOW,
                              "persistence_steps": PERSISTENCE_STEPS, "move_m": MOVE_M,
                              "saturation_m": SATURATION_M, "paired_metrics": list(PAIRED_METRICS)},
               "corner_rule": "team-mean own xy at t = 0 against area/2 (b04 headings)",
               "b04_corner_codes": ("heading.stratified by_corner keys are b04's '<east><north>' "
                                    "codes: 00 = W,S; 01 = W,N; 10 = E,S; 11 = E,N")}
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "readers.json", "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, sort_keys=True, default=_json_default)
    manifest = {"kind": "derived_reading_of_b05_panels", "new_episodes": 0, "fits": 0,
                "reader": "experiments/candidates/energy_relay_benchmark/b05/readers.py",
                "git_head": _git_head(), "argv": list(argv) if argv is not None else None,
                "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "access": ({"path": str(access_path), "sha256": _sha256(access_path)}
                           if access_path else None),
                "sources": sources, "readers_json_sha256": _sha256(out / "readers.json")}
    with open(out / "manifest.json", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=1, sort_keys=True)
    return payload


def _json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"not JSON serialisable: {type(value).__name__}")
