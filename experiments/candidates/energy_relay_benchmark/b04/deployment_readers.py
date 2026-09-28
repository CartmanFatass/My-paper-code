"""Zero-fit readers of existing S7 evaluation traces for the deployment (pre-entry) window.

Reasoning phase of `energy_relay_benchmark` (2026-09-27): these readers open trace ``.npz`` files
already written by the b01/b02 evaluators (keys ``world_<i>_own_xyz`` [T, n, 3],
``world_<i>_qos`` [T], ``world_<i>_seed``) and derive descriptive statistics.  No environment,
no model, no new episode is created; the manifest records every source file with its sha256.

blob statistics (per world, then mean/sd/min/max over worlds)
  spread_t0            mean pairwise horizontal distance at step 0 (m)
  spread_<W>, hull_<W>  mean over the first W steps of the mean / max pairwise distance (m)
  cohere_<W>           share of the first W steps whose moving UAVs (>= move_m) have a mean pairwise
                       velocity cosine above the threshold (the team moves as one blob)
  first_qos            first step with qos > 0 (-1 when never)

heading statistics (per policy)
  heading of each UAV = angle of its net horizontal displacement over the first H steps
  R_map[i]             mean resultant length of UAV i's heading across worlds in the MAP frame
                       (1: the same absolute heading in every world; ~0: heading varies by world)
  R_spawnrel[i]        the same after mirroring each world so its spawn corner is the lower-left
                       corner (a proxy frame for "conditioned on the spawn geometry")
  mean_heading_map_deg / mean_heading_spawnrel_deg   circular means per UAV
  wall_share           share of UAV-steps within wall_m of the E / W / S / N wall, and none, over
                       the first wall_window steps
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import subprocess
import time

import numpy as np

DEFAULT_WINDOWS = (100, 300, 1000)
DEFAULT_HEADING_STEPS = 100
DEFAULT_AREA_M = 8000.0
DEFAULT_WALL_M = 60.0
DEFAULT_WALL_WINDOW = 1000
DEFAULT_MOVE_M = 1.0
DEFAULT_COHERENCE_COSINE = 0.8
WALL_LABELS = ("E", "W", "S", "N", "none")


def load_worlds(path):
    """Return [{seed, xyz [T, n, 3], qos [T]}] for one trace file, in world-index order."""
    archive = np.load(path)
    indices = sorted({key.split("_")[1] for key in archive.files if key.endswith("_own_xyz")}, key=int)
    worlds = []
    for index in indices:
        seed_key = f"world_{index}_seed"
        worlds.append({
            "seed": int(archive[seed_key]) if seed_key in archive.files else -1,
            "xyz": np.asarray(archive[f"world_{index}_own_xyz"], dtype=np.float64),
            "qos": np.asarray(archive[f"world_{index}_qos"], dtype=np.float64),
        })
    return worlds


def pairwise_distances(xy):
    """Upper-triangle pairwise Euclidean distances of xy [n, 2]."""
    delta = xy[:, None, :] - xy[None, :, :]
    distance = np.sqrt((delta * delta).sum(-1))
    upper = np.triu_indices(xy.shape[0], 1)
    return distance[upper]


def coherence(velocity, move_m=DEFAULT_MOVE_M):
    """Mean pairwise cosine among UAVs that moved at least move_m; nan with fewer than two movers."""
    speed = np.linalg.norm(velocity, axis=-1)
    moving = speed >= move_m
    if moving.sum() < 2:
        return float("nan")
    unit = velocity[moving] / speed[moving][:, None]
    cosine = unit @ unit.T
    upper = np.triu_indices(unit.shape[0], 1)
    return float(cosine[upper].mean())


def first_positive(qos):
    positive = np.flatnonzero(qos > 0)
    return int(positive[0]) if positive.size else -1


def blob_row(world, windows=DEFAULT_WINDOWS, move_m=DEFAULT_MOVE_M, cosine=DEFAULT_COHERENCE_COSINE):
    xyz, qos = world["xyz"], world["qos"]
    xy = xyz[:, :, :2]
    velocity = np.diff(xy, axis=0)
    row = {"seed": world["seed"], "first_qos": first_positive(qos),
           "spread_t0": float(pairwise_distances(xy[0]).mean())}
    for window in windows:
        steps = min(int(window), xy.shape[0])
        distances = [pairwise_distances(xy[t]) for t in range(steps)]
        row[f"spread_{window}"] = float(np.mean([d.mean() for d in distances]))
        row[f"hull_{window}"] = float(np.mean([d.max() for d in distances]))
        coherent = np.array([coherence(velocity[t], move_m) for t in range(min(steps, velocity.shape[0]))])
        finite = np.isfinite(coherent)
        row[f"cohere_{window}"] = float(np.mean(coherent[finite] > cosine)) if finite.any() else float("nan")
    return row


def summarise(rows, skip=("seed",)):
    summary = {}
    for key in rows[0]:
        if key in skip:
            continue
        values = np.array([row[key] for row in rows], dtype=float)
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            summary[key] = {"mean": None, "sd": None, "min": None, "max": None, "n": 0}
            continue
        summary[key] = {
            "mean": round(float(finite.mean()), 3),
            "sd": round(float(finite.std(ddof=1)), 3) if finite.size > 1 else None,
            "min": round(float(finite.min()), 3),
            "max": round(float(finite.max()), 3),
            "n": int(finite.size),
        }
    return summary


def headings(worlds, steps=DEFAULT_HEADING_STEPS, area_m=DEFAULT_AREA_M):
    """Map-frame heading angles [W, n] and spawn-corner flags [W, 2] (east half, north half)."""
    angles, corners = [], []
    for world in worlds:
        xy = world["xyz"][:, :, :2]
        last = min(int(steps), xy.shape[0] - 1)
        displacement = xy[last] - xy[0]
        angles.append(np.arctan2(displacement[:, 1], displacement[:, 0]))
        centre = xy[0].mean(0)
        corners.append((int(centre[0] > area_m / 2.0), int(centre[1] > area_m / 2.0)))
    return np.array(angles), np.array(corners, dtype=int)


def mirror_to_spawn_frame(angles, corners):
    """Mirror x when spawned on the east half and y when on the north half."""
    vectors = np.stack([np.cos(angles), np.sin(angles)], -1)
    vectors[:, :, 0] *= np.where(corners[:, 0][:, None] == 1, -1.0, 1.0)
    vectors[:, :, 1] *= np.where(corners[:, 1][:, None] == 1, -1.0, 1.0)
    return np.arctan2(vectors[..., 1], vectors[..., 0])


def resultant_length(angles):
    return np.abs(np.exp(1j * angles).mean(0))


def mean_angle_deg(angles):
    return np.degrees(np.angle(np.exp(1j * angles).mean(0)))


def wall_shares(worlds, area_m=DEFAULT_AREA_M, wall_m=DEFAULT_WALL_M, window=DEFAULT_WALL_WINDOW):
    counts = np.zeros(5)
    total = 0
    for world in worlds:
        xy = world["xyz"][:int(window), :, :2]
        east = xy[..., 0] >= area_m - wall_m
        west = xy[..., 0] <= wall_m
        south = xy[..., 1] <= wall_m
        north = xy[..., 1] >= area_m - wall_m
        counts += [east.sum(), west.sum(), south.sum(), north.sum(), (~(east | west | south | north)).sum()]
        total += xy.shape[0] * xy.shape[1]
    return {label: round(float(count / total), 4) for label, count in zip(WALL_LABELS, counts)}


def heading_summary(worlds, steps=DEFAULT_HEADING_STEPS, area_m=DEFAULT_AREA_M,
                    wall_m=DEFAULT_WALL_M, wall_window=DEFAULT_WALL_WINDOW):
    angles, corners = headings(worlds, steps, area_m)
    relative = mirror_to_spawn_frame(angles, corners)
    r_map, r_rel = resultant_length(angles), resultant_length(relative)
    return {
        "worlds": int(angles.shape[0]),
        "heading_steps": int(steps),
        "spawn_corners_present": sorted({f"{e}{n}" for e, n in corners.tolist()}),
        "R_map_per_agent": [round(float(x), 3) for x in r_map],
        "R_map_mean": round(float(r_map.mean()), 3),
        "R_spawnrel_per_agent": [round(float(x), 3) for x in r_rel],
        "R_spawnrel_mean": round(float(r_rel.mean()), 3),
        "mean_heading_map_deg": [round(float(x), 1) for x in mean_angle_deg(angles)],
        "mean_heading_spawnrel_deg": [round(float(x), 1) for x in mean_angle_deg(relative)],
        "wall_share": wall_shares(worlds, area_m, wall_m, wall_window),
    }


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_group(files, windows=DEFAULT_WINDOWS, heading_steps=DEFAULT_HEADING_STEPS,
               area_m=DEFAULT_AREA_M, wall_m=DEFAULT_WALL_M, wall_window=DEFAULT_WALL_WINDOW,
               move_m=DEFAULT_MOVE_M, cosine=DEFAULT_COHERENCE_COSINE):
    worlds, sources = [], []
    for path in files:
        loaded = load_worlds(path)
        worlds.extend(loaded)
        sources.append({"path": path, "sha256": sha256_of(path), "bytes": os.path.getsize(path),
                        "worlds": len(loaded), "seeds": [w["seed"] for w in loaded]})
    rows = [blob_row(w, windows, move_m, cosine) for w in worlds]
    blob = {"worlds": len(rows), "seeds": [r["seed"] for r in rows], "summary": summarise(rows), "rows": rows}
    heading = heading_summary(worlds, heading_steps, area_m, wall_m, wall_window)
    return {"sources": sources, "blob": blob, "heading": heading}


def _git_head():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # pragma: no cover - git is optional for the reading itself
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--group", action="append", required=True, metavar="NAME=GLOB",
                        help="named trace group; the glob is expanded recursively (repeatable)")
    parser.add_argument("--out", required=True, help="output directory for the JSON records")
    parser.add_argument("--windows", default=",".join(map(str, DEFAULT_WINDOWS)))
    parser.add_argument("--heading-steps", type=int, default=DEFAULT_HEADING_STEPS)
    parser.add_argument("--area-m", type=float, default=DEFAULT_AREA_M)
    parser.add_argument("--wall-m", type=float, default=DEFAULT_WALL_M)
    parser.add_argument("--wall-window", type=int, default=DEFAULT_WALL_WINDOW)
    parser.add_argument("--move-m", type=float, default=DEFAULT_MOVE_M)
    parser.add_argument("--coherence-cosine", type=float, default=DEFAULT_COHERENCE_COSINE)
    args = parser.parse_args(argv)
    windows = tuple(int(x) for x in args.windows.split(",") if x)
    parameters = {"windows": windows, "heading_steps": args.heading_steps, "area_m": args.area_m,
                  "wall_m": args.wall_m, "wall_window": args.wall_window, "move_m": args.move_m,
                  "coherence_cosine": args.coherence_cosine}
    os.makedirs(args.out, exist_ok=True)
    blob_out, heading_out, manifest_groups = {}, {}, {}
    for item in args.group:
        name, pattern = item.split("=", 1)
        files = sorted(glob.glob(pattern, recursive=True))
        if not files:
            raise SystemExit(f"group {name}: no file matches {pattern}")
        result = read_group(files, windows, args.heading_steps, args.area_m, args.wall_m,
                            args.wall_window, args.move_m, args.coherence_cosine)
        blob_out[name] = result["blob"]
        heading_out[name] = result["heading"]
        manifest_groups[name] = {"pattern": pattern, "sources": result["sources"]}
        b, h = result["blob"]["summary"], result["heading"]
        print(f"{name:14s} n={result['blob']['worlds']:3d} spread_t0 {b['spread_t0']['mean']:6.0f} "
              + " ".join(f"spread_{w} {b[f'spread_{w}']['mean']:6.0f}" for w in windows)
              + f" | cohere_{windows[0]} {b[f'cohere_{windows[0]}']['mean']} | first_qos {b['first_qos']['mean']}"
              + f" | R_map {h['R_map_mean']:.2f} R_spawnrel {h['R_spawnrel_mean']:.2f} | walls {h['wall_share']}")
    manifest = {"kind": "derived_reading_of_existing_traces", "launcher": None, "new_episodes": 0,
                "reader": "experiments/candidates/energy_relay_benchmark/b04/deployment_readers.py",
                "git_head": _git_head(), "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "parameters": parameters, "groups": manifest_groups}
    for filename, payload in (("blob_stat.json", blob_out), ("heading_stat.json", heading_out),
                              ("manifest.json", manifest)):
        with open(os.path.join(args.out, filename), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1, sort_keys=True)
    return 0



# ---------------------------------------------------------------------------------------------
# Block 0 of b04_geometry_probe_a01 (NOTES 2026-09-28, entry 2).  Additive: every function and
# output above is unchanged, so b04_deployment_reading_a01 stays reproducible with ``main``.
# ---------------------------------------------------------------------------------------------

FIRST_SERVICE_WINDOWS = (60, 120)       # served within W  <=>  first step with qos > 0 is <= W
MIN_NET_DISPLACEMENT_M = 30.0
SPEED_SATURATION_M = 29.0
SPEED_WINDOW = 1000
BLOCK0_GROUPS = (   # b04_deployment_reading_a01's groups + c02 (traces exist, never read)
    ("H_central", "runs/energy_relay_benchmark/b01_ref_a02/grid/traces/H1_e0.00_x0.05.npz"),
    ("H_local", "runs/energy_relay_benchmark/b01_ref_a02/reference/traces/Hlocal_e0.00_x0.05.npz"),
    ("N_init_953", "runs/energy_relay_benchmark/b01_ref_a02/null/traces/N_e0.00_x0.05.npz"),
    ("SET_c00_det", "runs/energy_relay_benchmark/b02_s1_eval_c00_a01/**/traces/L_c00_deterministic_*.npz"),
    ("SET_c01_det", "runs/energy_relay_benchmark/b02_s1_eval_c01_a01/**/traces/L_c01_deterministic_*.npz"),
    ("SET_c02_det", "runs/energy_relay_benchmark/b02_s1_eval_c02_a01/**/traces/L_c02_deterministic_*.npz"),
    ("SET_c03_det", "runs/energy_relay_benchmark/b02_s1_eval_c03_a01/**/traces/L_c03_deterministic_*.npz"),
    ("SET_c06_det", "runs/energy_relay_benchmark/b02_s1_eval_c06_a01/**/traces/L_c06_deterministic_*.npz"),
    ("SET_c06_stoch", "runs/energy_relay_benchmark/b02_s1_eval_c06_a01/**/traces/L_c06_stochastic_*.npz"),
)


def load_modes(path):
    """Shield mode [T, n] per world (trace key ``world_<i>_mode``), in world-index order."""
    archive = np.load(path)
    indices = sorted({key.split("_")[1] for key in archive.files if key.endswith("_own_xyz")}, key=int)
    return [np.asarray(archive[f"world_{index}_mode"]) > 0.5 for index in indices]


def _count_share(count, served, total):
    return {"count": int(count), "share_of_served": (round(count / served, 4) if served else None),
            "share_of_all": (round(count / total, 4) if total else None)}


def first_service_summary(worlds, windows=FIRST_SERVICE_WINDOWS):
    """First service with the -1 fix: never-served count, mean over served worlds, window counts
    (first step <= W) and the censored mean (a miss counts as the trace horizon)."""
    first = np.array([first_positive(w["qos"]) for w in worlds], dtype=np.int64)
    horizon = np.array([len(w["qos"]) for w in worlds], dtype=np.int64)
    served = first >= 0
    total, n_served = int(first.size), int(served.sum())
    result = {"worlds": total, "never_served": total - n_served, "served": n_served,
              "mean_served": round(float(first[served].mean()), 3) if n_served else None,
              "censored_mean": round(float(np.where(served, first, horizon).mean()), 3) if total else None,
              "horizon": sorted(set(horizon.tolist())), "window_rule": "first_step <= W"}
    for window in windows:
        result[f"served_within_{window}"] = _count_share(int((served & (first <= window)).sum()),
                                                         n_served, total)
    return result


def conditional_first_service(worlds, access, windows=FIRST_SERVICE_WINDOWS):
    """``first_service_summary`` over the worlds whose seed has no user in actual access range at
    t = 0 (``access``: seed -> users in range, from Block 1's ID reset)."""
    joined = [w for w in worlds if w["seed"] in access]
    empty = [w for w in joined if access[w["seed"]] == 0]
    return {"joined_worlds": len(joined), "no_user_in_access_range_t0_worlds": len(empty),
            "no_user_in_access_range_t0": first_service_summary(empty, windows) if empty else None}


def _unit_mean_angle(vectors):
    """Circular mean angle of the non-zero rows of vectors [k, 2]; nan when there is none."""
    norms = np.linalg.norm(vectors, axis=-1)
    keep = norms > 0
    if not keep.any():
        return float("nan")
    unit = vectors[keep] / norms[keep][:, None]
    return float(np.arctan2(unit[:, 1].mean(), unit[:, 0].mean()))


def heading_samples(worlds, steps=DEFAULT_HEADING_STEPS, area_m=DEFAULT_AREA_M, wall_m=DEFAULT_WALL_M,
                    min_displacement_m=MIN_NET_DISPLACEMENT_M, move_m=DEFAULT_MOVE_M):
    """Per (world, agent): net and step-wise-mean headings over the first ``steps`` steps and over
    the pre-first-wall-contact part of that window; nan where excluded (net displacement below
    ``min_displacement_m``, or no pre-contact step)."""
    keys = ("net", "stepwise", "net_prewall", "stepwise_prewall")
    out = {key: [] for key in keys}
    corners = []
    for world in worlds:
        xy = world["xyz"][:, :, :2]
        last = min(int(steps), xy.shape[0] - 1)
        centre = xy[0].mean(0)
        corners.append((int(centre[0] > area_m / 2.0), int(centre[1] > area_m / 2.0)))
        near = ((xy[..., 0] <= wall_m) | (xy[..., 0] >= area_m - wall_m)
                | (xy[..., 1] <= wall_m) | (xy[..., 1] >= area_m - wall_m))
        rows = {key: [] for key in keys}
        for agent in range(xy.shape[1]):
            contact = np.flatnonzero(near[:, agent])
            for suffix, end in (("", last), ("_prewall", min(last, int(contact[0]) - 1)
                                             if contact.size else last)):
                net = xy[end, agent] - xy[0, agent] if end > 0 else np.zeros(2)
                velocity = np.diff(xy[:end + 1, agent], axis=0) if end > 0 else np.zeros((0, 2))
                velocity = velocity[np.linalg.norm(velocity, axis=-1) >= move_m]
                excluded = end <= 0 or float(np.linalg.norm(net)) < min_displacement_m
                rows["net" + suffix].append(float("nan") if excluded
                                            else float(np.arctan2(net[1], net[0])))
                rows["stepwise" + suffix].append(float("nan") if excluded
                                                 else _unit_mean_angle(velocity))
        for key in keys:
            out[key].append(rows[key])
    return {key: np.array(value, dtype=np.float64) for key, value in out.items()}, np.array(corners, dtype=int)


def _stratum(angles, corners, mask):
    """R_map / R_spawnrel / circular means / n over the finite angles selected by mask [W, n]."""
    relative = mirror_to_spawn_frame(angles, corners)
    keep = mask & np.isfinite(angles)
    n = int(keep.sum())
    if n == 0:
        return {"n": 0, "R_map": None, "R_spawnrel": None, "mean_map_deg": None, "mean_spawnrel_deg": None}
    a, r = np.exp(1j * angles[keep]).mean(), np.exp(1j * relative[keep]).mean()
    return {"n": n, "R_map": round(float(abs(a)), 3), "R_spawnrel": round(float(abs(r)), 3),
            "mean_map_deg": round(float(np.degrees(np.angle(a))), 1),
            "mean_spawnrel_deg": round(float(np.degrees(np.angle(r))), 1)}


def _corner_equal_weight(angles, corners):
    """Resultant of the equal-weight mean of per-corner mean unit vectors (map and spawn frame)."""
    relative = mirror_to_spawn_frame(angles, corners)
    labels = [f"{e}{n}" for e, n in corners.tolist()]
    means_map, means_rel = [], []
    for label in sorted(set(labels)):
        rows = np.array([lab == label for lab in labels])
        values = angles[rows]
        finite = np.isfinite(values)
        if finite.any():
            means_map.append(np.exp(1j * values[finite]).mean())
            means_rel.append(np.exp(1j * relative[rows][finite]).mean())
    if not means_map:
        return {"corners": 0, "R_map": None, "R_spawnrel": None}
    return {"corners": len(means_map), "R_map": round(float(abs(np.mean(means_map))), 3),
            "R_spawnrel": round(float(abs(np.mean(means_rel))), 3)}


def stratified_heading_summary(worlds, **kwargs):
    """Headings per stratum: all, spawn corner (each and equal-weight), agent index (= spawn slot),
    pre-first-wall-contact (all and per index); net-displacement and step-wise-mean headings."""
    samples, corners = heading_samples(worlds, **kwargs)
    labels = np.array([f"{e}{n}" for e, n in corners.tolist()])
    everything = np.ones(samples["net"].shape, dtype=bool)
    result = {"worlds": int(len(worlds)), "min_net_displacement_m": kwargs.get(
        "min_displacement_m", MIN_NET_DISPLACEMENT_M)}
    for kind in ("net", "stepwise"):
        angles, prewall = samples[kind], samples[kind + "_prewall"]
        n_agents = angles.shape[1]
        by_index = {}
        for agent in range(n_agents):
            column = np.zeros_like(everything)
            column[:, agent] = True
            by_index[str(agent)] = _stratum(angles, corners, column)
        prewall_index = {}
        for agent in range(n_agents):
            column = np.zeros_like(everything)
            column[:, agent] = True
            prewall_index[str(agent)] = _stratum(prewall, corners, column)
        result[kind] = {
            "all": _stratum(angles, corners, everything),
            "excluded": int((~np.isfinite(angles)).sum()),
            "by_corner": {label: _stratum(angles, corners, (labels == label)[:, None] & everything)
                          for label in sorted(set(labels.tolist()))},
            "corner_equal_weight": _corner_equal_weight(angles, corners),
            "by_index": by_index,
            "pre_wall_contact": {"all": _stratum(prewall, corners, everything),
                                 "excluded": int((~np.isfinite(prewall)).sum()),
                                 "by_index": prewall_index},
        }
    return result


def speed_saturation(worlds, modes, threshold_m=SPEED_SATURATION_M, window=SPEED_WINDOW):
    """Share of normal-mode UAV-steps (shield mode False at step t) whose horizontal displacement
    xy[t+1] - xy[t] is >= threshold_m, over the first ``window`` steps."""
    saturated = normal = 0
    for world, mode in zip(worlds, modes):
        xy = world["xyz"][:, :, :2]
        steps = min(int(window), xy.shape[0] - 1)
        speed = np.linalg.norm(xy[1:steps + 1] - xy[:steps], axis=-1)
        free = ~np.asarray(mode[:steps], dtype=bool)
        normal += int(free.sum())
        saturated += int((free & (speed >= threshold_m)).sum())
    return {"normal_uav_steps": normal, "saturated_uav_steps": saturated,
            "share": round(saturated / normal, 4) if normal else None,
            "threshold_m": float(threshold_m), "window": int(window)}


def block0(out, groups=BLOCK0_GROUPS, access=None, root="."):
    """Block 0 records: ``blob_stat.json`` (legacy blob reading, ``first_qos`` marked, plus the
    fixed first-service reading), ``heading_stat.json`` (legacy + stratified) and
    ``speed_stat.json``.  ``access``: seed -> users in actual access range at t = 0, or None."""
    os.makedirs(out, exist_ok=True)
    blob_out, heading_out, speed_out, sources = {}, {}, {}, {}
    for name, pattern in groups:
        files = sorted(glob.glob(os.path.join(root, pattern), recursive=True))
        if not files:
            raise FileNotFoundError(f"group {name}: no file matches {pattern}")
        result = read_group(files)
        worlds = [w for path in files for w in load_worlds(path)]
        modes = [m for path in files for m in load_modes(path)]
        blob = result["blob"]
        blob["summary"]["first_qos"]["legacy_minus_one_in_mean"] = True
        blob["first_service"] = first_service_summary(worlds)
        blob["first_service_conditional"] = (
            conditional_first_service(worlds, access) if access is not None
            else {"reason": "Block 1 conditions.json (users_in_access_range_t0) not available"})
        blob_out[name] = blob
        heading_out[name] = {"legacy": result["heading"], "stratified": stratified_heading_summary(worlds)}
        speed_out[name] = speed_saturation(worlds, modes)
        sources[name] = {"pattern": pattern, "sources": result["sources"]}
    for filename, payload in (("blob_stat.json", blob_out), ("heading_stat.json", heading_out),
                              ("speed_stat.json", speed_out)):
        with open(os.path.join(out, filename), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1, sort_keys=True)
    return sources


if __name__ == "__main__":
    raise SystemExit(main())
