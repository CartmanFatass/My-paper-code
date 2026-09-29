#!/usr/bin/env python3
"""b01 cell 0 static gate and closed-loop ordinary references (coupled_host_joint_skills_stage1).

Zero fits.  For each world seed: ``make_host(world, area_size)``; static placement searches
``P_relay`` (A2A allowed) and ``P_flat`` (A2A disabled in the evaluator), same budget and the
same k-means candidates; closed-loop execution of both targets from the world's initial
positions (straight-line flight at max_speed, host contract env with A2A enabled); stationary
and uniform-random floors.  Writes ``worlds/<world>.json`` per world and ``summary.json``
with G = mean(P_relay - P_flat) on the static contract reward, G_C on static backhauled
coverage, closed-loop means of the four references, evaluations used, wall and process CPU
seconds.

Deterministic derivations (no additional seed): planner rng for both searches =
``numpy.random.default_rng(world)`` (fresh instance per search, so the candidates are equal);
random-floor rng = ``numpy.random.default_rng([world, 1])``.

Admission (``scripts/hmasd_launch.py``) precedes every environment import and every output.
``--smoke-no-admission`` exists only for engineering smoke runs: it is refused unless every
world lies outside the declared dev (1000-1031) and hold-out (2000-2031) panels and ``--out``
resolves under this checkout's ``temp/``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIRECTION = "coupled_host_joint_skills_stage1"
DECLARED_PANELS = (range(1000, 1032), range(2000, 2032))
SCIENTIFIC_OUTPUTS = ("summary.json", "worlds")
GATE_THRESHOLD_DECLARED = 0.05
REFERENCES = ("closed_loop_relay", "closed_loop_flat", "stationary_floor", "random_floor")
READERS = ("contract_reward", "coverage_backhauled", "frontend_capacity_with_path_mbps",
           "mean_relays_per_routed_uav")


def parse_worlds(tokens: list[str]) -> list[int]:
    worlds: list[int] = []
    for token in tokens:
        for part in str(token).split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                low, high = part.split("-", 1)
                low_i, high_i = int(low), int(high)
                if high_i < low_i:
                    raise ValueError(f"empty world range {part!r}")
                worlds.extend(range(low_i, high_i + 1))
            else:
                worlds.append(int(part))
    if not worlds:
        raise ValueError("no worlds given")
    if len(set(worlds)) != len(worlds):
        raise ValueError("a world seed is repeated")
    return worlds


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_gate.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--worlds", nargs="+", default=["1000-1031"],
                        help="world (reset) seeds: integers and inclusive ranges a-b")
    parser.add_argument("--area-size", type=int, default=5000)
    parser.add_argument("--budget", type=int, default=3000,
                        help="static evaluations per search (candidates included)")
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting existing scientific outputs in --out")
    parser.add_argument("--smoke-no-admission", action="store_true",
                        help="engineering smoke only: non-panel worlds and --out under temp/")
    return parser


def _git(*arguments: str) -> str | None:
    try:
        completed = subprocess.run(["git", "-C", str(ROOT), *arguments], check=True,
                                   capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def _cpu_seconds() -> dict[str, float]:
    """Process CPU (user+sys) of this runner and of its reaped children, in seconds."""
    own = resource.getrusage(resource.RUSAGE_SELF)
    kids = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "self_user_s": float(own.ru_utime),
        "self_sys_s": float(own.ru_stime),
        "children_user_s": float(kids.ru_utime),
        "children_sys_s": float(kids.ru_stime),
        "total_s": float(own.ru_utime + own.ru_stime + kids.ru_utime + kids.ru_stime),
        "peak_rss_kib": int(own.ru_maxrss),
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def jsonable(value: Any) -> Any:
    """Plain JSON: numpy -> python, non-finite floats -> None, tuples -> lists."""
    try:
        import numpy as np
    except ImportError:  # pragma: no cover
        np = None
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if np is not None and isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if np is not None and isinstance(value, np.generic):
        return jsonable(value.item())
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Path):
        return str(value)
    return str(value)


def write_json(path: Path, payload: Any, indent: int | None = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    separators = None if indent is not None else (",", ":")
    temporary.write_text(json.dumps(jsonable(payload), indent=indent, separators=separators,
                                    allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _smoke_refusal(worlds: list[int], out: Path) -> str | None:
    panel = [w for w in worlds if any(w in r for r in DECLARED_PANELS)]
    if panel:
        return f"--smoke-no-admission refuses declared panel worlds {panel}"
    temp_root = (ROOT / "temp").resolve()
    resolved = out.resolve()
    if resolved != temp_root and temp_root not in resolved.parents:
        return f"--smoke-no-admission needs --out under {temp_root}"
    return None


def _mean_sd(values: list[float]) -> dict[str, Any]:
    import numpy as np

    array = np.asarray(values, dtype=float)
    return {
        "n": int(array.size),
        "mean": float(array.mean()) if array.size else None,
        "sd": float(array.std(ddof=1)) if array.size > 1 else None,
        "min": float(array.min()) if array.size else None,
        "max": float(array.max()) if array.size else None,
    }


def _timed(function, *args, **kwargs):
    cpu0 = _cpu_seconds()["total_s"]
    wall0 = time.perf_counter()
    value = function(*args, **kwargs)
    return value, {"wall_s": time.perf_counter() - wall0, "cpu_s": _cpu_seconds()["total_s"] - cpu0}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        worlds = parse_worlds(args.worlds)
    except ValueError as exc:
        parser.error(str(exc))
    if args.budget < 3:
        parser.error("--budget must be >= 3 (the k-means candidates)")

    if args.smoke_no_admission:
        refusal = _smoke_refusal(worlds, Path(args.out))
        if refusal:
            print(f"error: {refusal}", file=sys.stderr)
            return 2
        admission: Any = "skipped (engineering smoke: non-panel worlds, temp output)"
    else:
        # Admission precedes environment imports and any output.
        from scripts.hmasd_admission import require_admission

        admission = dict(require_admission(__file__, direction="coupled_host_joint_skills_stage1"))

    started_utc = _utc_now()
    started = time.perf_counter()

    import numpy as np

    from experiments.candidates.coupled_host_joint_skills_stage1.host import (
        HOST_CONTRACT_KWARGS,
        make_host,
    )
    from experiments.candidates.coupled_host_joint_skills_stage1.planner import (
        closed_loop_execute,
        random_floor,
        search_placement,
        stationary_floor,
    )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)  # the launcher pre-creates the output root
    existing = [name for name in SCIENTIFIC_OUTPUTS if (out / name).exists()]
    if existing and not args.force:
        print(f"error: {out} already holds scientific output {existing}; pass --force",
              file=sys.stderr)
        return 2

    rows: list[dict[str, Any]] = []
    denominator = None
    for world in worlds:
        world_cpu0 = _cpu_seconds()["total_s"]
        world_wall0 = time.perf_counter()
        env = make_host(world, area_size=args.area_size)
        denominator = env.contract_denominator_bps
        initial = env.uav_positions.copy()

        relay, t_relay = _timed(search_placement, env, True, args.budget,
                                np.random.default_rng(world))
        flat, t_flat = _timed(search_placement, env, False, args.budget,
                              np.random.default_rng(world))
        if flat.max_uav_connections_seen != 0:
            print(f"error: world {world}: P_flat evaluation formed UAV-UAV links",
                  file=sys.stderr)
            return 3
        references: dict[str, Any] = {}
        timing: dict[str, Any] = {"search_relay": t_relay, "search_flat": t_flat}
        references["closed_loop_relay"], timing["closed_loop_relay"] = _timed(
            closed_loop_execute, env, relay.positions_xyz)
        references["closed_loop_flat"], timing["closed_loop_flat"] = _timed(
            closed_loop_execute, env, flat.positions_xyz)
        references["stationary_floor"], timing["stationary_floor"] = _timed(
            stationary_floor, env)
        references["random_floor"], timing["random_floor"] = _timed(
            random_floor, env, np.random.default_rng([world, 1]))
        timing["world_total"] = {"wall_s": time.perf_counter() - world_wall0,
                                 "cpu_s": _cpu_seconds()["total_s"] - world_cpu0}

        row = {
            "world": int(world),
            "area_size": int(args.area_size),
            "initial_positions_xyz": initial.tolist(),
            "user_positions_xy": np.asarray(env.user_positions).tolist(),
            "static": {"P_relay": relay.to_json(), "P_flat": flat.to_json()},
            "G_world": relay.contract_reward - flat.contract_reward,
            "G_C_world": relay.coverage_backhauled - flat.coverage_backhauled,
            "closed_loop": references,
            "timing": timing,
        }
        write_json(out / "worlds" / f"{int(world)}.json", row, indent=None)
        rows.append(row)
        print(f"world={world} G={row['G_world']:+.4f} G_C={row['G_C_world']:+.4f} "
              f"evals={relay.evaluations}/{flat.evaluations} "
              f"wall={timing['world_total']['wall_s']:.1f}s", flush=True)

    closed_loop_summary: dict[str, Any] = {}
    for reference in REFERENCES:
        entry: dict[str, Any] = {}
        for reader in READERS:
            for window in ("mean_all", "mean_final100"):
                key = f"{reader}_{window}"
                entry[key] = _mean_sd([row["closed_loop"][reference][key] for row in rows])
        entry["final_far_cluster_backhauled_share"] = _mean_sd(
            [row["closed_loop"][reference]["final"]["far_cluster_backhauled_share"] for row in rows])
        entry["final_coverage_backhauled"] = _mean_sd(
            [row["closed_loop"][reference]["final"]["coverage_backhauled"] for row in rows])
        if reference.startswith("closed_loop"):
            entry["arrival_step"] = _mean_sd(
                [row["closed_loop"][reference]["arrival_step"] for row in rows
                 if row["closed_loop"][reference]["arrival_step"] is not None])
            entry["not_arrived_worlds"] = [
                row["world"] for row in rows if row["closed_loop"][reference]["arrival_step"] is None]
        closed_loop_summary[reference] = entry

    def timing_stats(component: str) -> dict[str, Any]:
        return {"wall_s": _mean_sd([row["timing"][component]["wall_s"] for row in rows]),
                "cpu_s": _mean_sd([row["timing"][component]["cpu_s"] for row in rows])}

    summary: dict[str, Any] = {
        "tool": "coupled_host_joint_skills_stage1.run_gate",
        "direction": DIRECTION,
        "admission": admission,
        "launch_sha": (admission.get("sha") if isinstance(admission, dict) else None),
        "git_head": _git("rev-parse", "HEAD"),
        "training_fits_performed": 0,
        "worlds": worlds,
        "area_size": int(args.area_size),
        "budget": int(args.budget),
        "host_contract_kwargs": HOST_CONTRACT_KWARGS,
        "contract_denominator_bps": denominator,
        "rng_derivations": {
            "planner": "numpy.random.default_rng(world), fresh instance for each search",
            "random_floor": "numpy.random.default_rng([world, 1])",
        },
        "closed_loop_env": "host contract (a2a_enabled=True) for every reference, incl. P_flat",
        "closed_loop_assignment": "min_makespan permutation of targets to UAVs",
        "gate_threshold_declared": GATE_THRESHOLD_DECLARED,
        "G": _mean_sd([row["G_world"] for row in rows]),
        "G_C": _mean_sd([row["G_C_world"] for row in rows]),
        "static": {
            name: {
                "contract_reward": _mean_sd([row["static"][name]["contract_reward"] for row in rows]),
                "coverage_backhauled": _mean_sd(
                    [row["static"][name]["coverage_backhauled"] for row in rows]),
                "evaluations": _mean_sd([row["static"][name]["evaluations"] for row in rows]),
                "converged_worlds": sum(bool(row["static"][name]["converged"]) for row in rows),
                "start_candidate_k": [row["static"][name]["start_candidate_k"] for row in rows],
            }
            for name in ("P_relay", "P_flat")
        },
        "closed_loop": closed_loop_summary,
        "timing_per_world": {component: timing_stats(component) for component in (
            "search_relay", "search_flat", "closed_loop_relay", "closed_loop_flat",
            "stationary_floor", "random_floor", "world_total")},
        "cpu_seconds": _cpu_seconds(),
        "interpreter": {
            "executable": sys.executable,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "host": platform.node(),
        },
        "arguments": sys.argv[1:] if argv is None else list(argv),
        "start_utc": started_utc,
        "end_utc": _utc_now(),
        "wall_clock_s": time.perf_counter() - started,
    }
    write_json(out / "summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
