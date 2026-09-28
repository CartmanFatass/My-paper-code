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


if __name__ == "__main__":
    raise SystemExit(main())
