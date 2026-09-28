#!/usr/bin/env python3
"""B01 readiness runner (uav_restoration_readiness): zero-fit controller rollouts.

For each episode seed x controller: ``make_parallel_env(config, dataset_root, seed)``,
``rollout_controller(env, controller, seed=seed)`` (the environment's own counterfactual
evaluator), then ``episodes/<controller>/<seed>.json`` and one ``summary.json`` with the
``evaluate_baselines._aggregate`` shape per controller plus paired per-seed differences.

Forward-only; no optimizer step.  Admission (``scripts/hmasd_launch.py``) precedes every
environment import and every output.  ``--no-admission`` exists only for the synthetic
fixture test path and is refused for any other source kind.

Episodes run seed-major (all controllers for one seed before the next seed), so a
``--max-wall-s`` stop leaves complete pairs for the seeds already started.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIRECTION = "uav_restoration_readiness"
AVAILABLE_CONTROLLERS = (
    "static_uav",
    "demand_greedy",
    "backhaul_aware_greedy",
    "joint_rolling_lp",
)
DEFAULT_CONTROLLERS = ("static_uav", "backhaul_aware_greedy", "joint_rolling_lp")
INFORMATION_MODES = ("central_delayed_telemetry", "ideal_full_current_demand")
PAIRS = (
    ("joint_rolling_lp", "backhaul_aware_greedy"),
    ("backhaul_aware_greedy", "static_uav"),
)
PAIRED_METRICS = (
    ("controller_satisfaction", ("references", "controller_satisfaction")),
    ("fraction_of_lost_service_restored", ("recovery", "fraction_of_lost_service_restored")),
)
SCIENTIFIC_OUTPUTS = ("summary.json", "episodes")


# ----------------------------------------------------------------------------------------
# Arguments
# ----------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_readiness.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, help="environment configuration JSON")
    parser.add_argument("--dataset", default=None,
                        help="prepared cache root (overrides source.dataset_root)")
    parser.add_argument("--episodes-file", required=True,
                        help="JSON list of episode seeds, or {\"episode_seeds\": [...]}")
    parser.add_argument("--controllers", nargs="+", default=list(DEFAULT_CONTROLLERS),
                        choices=list(AVAILABLE_CONTROLLERS))
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting existing scientific outputs in --out")
    parser.add_argument("--information-mode", default="central_delayed_telemetry",
                        choices=list(INFORMATION_MODES))
    parser.add_argument("--diagnostic-rationale", default=None,
                        help="required with --information-mode ideal_full_current_demand")
    parser.add_argument("--max-wall-s", type=float, default=None,
                        help="do not start a new episode once this wall budget is spent")
    parser.add_argument("--planner-top-k", type=int, default=8)
    parser.add_argument("--planner-max-sweeps", type=int, default=2)
    parser.add_argument("--no-admission", action="store_true",
                        help="fixture test path only: skip launch admission")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.information_mode == "ideal_full_current_demand" and not (
        args.diagnostic_rationale and args.diagnostic_rationale.strip()
    ):
        parser.error("--information-mode ideal_full_current_demand requires "
                     "--diagnostic-rationale TEXT")
    if args.planner_top_k < 1:
        parser.error("--planner-top-k must be >= 1")
    if args.planner_max_sweeps < 0:
        parser.error("--planner-max-sweeps must be >= 0")
    if args.max_wall_s is not None and not args.max_wall_s > 0.0:
        parser.error("--max-wall-s must be positive")
    if len(set(args.controllers)) != len(args.controllers):
        parser.error("--controllers lists a controller twice")
    return args


# ----------------------------------------------------------------------------------------
# Small helpers (no environment imports)
# ----------------------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*arguments: str) -> str | None:
    try:
        completed = subprocess.run(["git", "-C", str(ROOT), *arguments], check=True,
                                   capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(jsonable(payload), indent=2, allow_nan=False) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def load_episode_seeds(path: Path) -> list[int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    values = payload.get("episode_seeds") if isinstance(payload, dict) else payload
    if not isinstance(values, list) or not values:
        raise SystemExit(f"error: {path} holds no episode seeds (list or episode_seeds)")
    seeds: list[int] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise SystemExit(f"error: {path} holds a non-integer episode seed {value!r}")
        seeds.append(int(value))
    if len(set(seeds)) != len(seeds):
        raise SystemExit(f"error: {path} repeats an episode seed")
    return seeds


# ----------------------------------------------------------------------------------------
# Aggregation (same shape as scripts/uav_service_restoration/evaluate_baselines._aggregate)
# ----------------------------------------------------------------------------------------


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Duplicate of ``evaluate_baselines._aggregate`` (that script imports ``_cli`` through a
    path hack, so it is not importable here); a test pins equality on fixture records."""

    import numpy as np

    def _float(value: Any) -> float:
        return float("nan") if value is None else float(value)

    satisfaction = np.asarray(
        [_float(record["references"]["controller_satisfaction"]) for record in records],
        dtype=np.float64,
    )
    restored = np.asarray(
        [_float(record["recovery"]["fraction_of_lost_service_restored"]) for record in records],
        dtype=np.float64,
    )
    times = [
        record["recovery"]["time_to_recovery_s"]
        for record in records
        if record["recovery"].get("time_to_recovery_s") is not None
    ]
    censored = [
        record["recovery"].get("censoring_reason")
        for record in records
        if record["recovery"].get("censored")
    ]
    not_applicable = sum(1 for record in records if not record["recovery"].get("applicable"))
    return {
        "n_episodes": len(records),
        "controller_satisfaction_mean": float(np.nanmean(satisfaction)) if satisfaction.size else None,
        "controller_satisfaction_min": float(np.nanmin(satisfaction)) if satisfaction.size else None,
        "controller_satisfaction_max": float(np.nanmax(satisfaction)) if satisfaction.size else None,
        "fraction_of_lost_service_restored_mean": (
            float(np.nanmean(restored)) if restored.size else None
        ),
        "n_recovered": len(times),
        "time_to_recovery_s_mean_over_recovered": (
            float(np.mean(times)) if times else None
        ),
        "n_censored": len(censored),
        "censoring_reasons": {
            reason: censored.count(reason) for reason in sorted(set(censored) - {None})
        },
        "n_not_applicable": not_applicable,
        "aggregation_rule": (
            "means are over episodes; a censored episode contributes no recovery time and "
            "is never counted as a recovery of zero seconds"
        ),
    }


def _metric(record: dict[str, Any], keys: tuple[str, str]) -> float:
    value = record.get(keys[0], {}).get(keys[1]) if record else None
    return float("nan") if value is None else float(value)


def paired_differences(
    records: dict[str, dict[int, dict[str, Any]]], seeds: list[int]
) -> dict[str, Any]:
    """Per-seed ``a - b`` on each paired metric; seeds where either side is missing or
    non-finite are dropped and counted."""

    out: dict[str, Any] = {}
    for first, second in PAIRS:
        if first not in records or second not in records:
            continue
        pair: dict[str, Any] = {}
        for label, keys in PAIRED_METRICS:
            per_seed: dict[str, float | None] = {}
            values: list[float] = []
            dropped = 0
            for seed in seeds:
                a = records[first].get(seed)
                b = records[second].get(seed)
                if a is None or b is None:
                    continue
                difference = _metric(a, keys) - _metric(b, keys)
                if math.isfinite(difference):
                    per_seed[str(seed)] = difference
                    values.append(difference)
                else:
                    per_seed[str(seed)] = None
                    dropped += 1
            n = len(values)
            mean = sum(values) / n if n else None
            if n >= 2:
                variance = sum((value - mean) ** 2 for value in values) / (n - 1)
                se = math.sqrt(variance) / math.sqrt(n)
            else:
                se = None
            pair[label] = {
                "mean": mean,
                "se": se,
                "n": n,
                "n_positive": sum(1 for value in values if value > 0.0),
                "n_negative": sum(1 for value in values if value < 0.0),
                "n_zero": sum(1 for value in values if value == 0.0),
                "n_dropped_non_finite": dropped,
                "per_seed": per_seed,
                "se_rule": "sample SD (ddof=1) / sqrt(n) over seeds with a finite difference",
            }
        out[f"{first}_minus_{second}"] = pair
    return out


# ----------------------------------------------------------------------------------------
# Rollout plumbing
# ----------------------------------------------------------------------------------------


class _PositionRecorder:
    """Forwards to a controller and records the permitted view's UAV positions per step."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.name = getattr(inner, "name", type(inner).__name__)
        self.positions: list[list[list[float]]] = []

    def reset(self) -> None:
        self.positions = []
        self._inner.reset()

    def act(self, view: dict[str, Any], agents: list[str]) -> Any:
        self.positions.append(view["uav_positions"].tolist())
        return self._inner.act(view, agents)


def _step_series(env: Any, decision_dt_s: float) -> dict[str, Any]:
    """Series available from ``env.accumulator`` after the rollout."""

    import numpy as np

    accumulator = env.accumulator
    starts = [float(item[0]) for item in accumulator.delivered_series_mbps]
    durations = [float(item[1]) for item in accumulator.delivered_series_mbps]
    delivered = (
        np.stack([item[2] for item in accumulator.delivered_series_mbps])
        if accumulator.delivered_series_mbps else np.zeros((0, accumulator.n_demand_points))
    )
    offered = (
        np.stack(accumulator.offered_series_mbps)
        if accumulator.offered_series_mbps else np.zeros((0, accumulator.n_demand_points))
    )
    unmet = np.maximum(offered - delivered, 0.0)
    weights = np.asarray(durations, dtype=np.float64)
    step_index = np.floor(np.asarray(starts, dtype=np.float64) / decision_dt_s + 1e-9).astype(int)
    n_steps = int(step_index.max()) + 1 if step_index.size else 0
    per_step: dict[str, list[list[float]]] = {"offered_mbit": [], "delivered_mbit": [],
                                              "unmet_mbit": []}
    for step in range(n_steps):
        mask = step_index == step
        w = weights[mask][:, None]
        per_step["offered_mbit"].append((offered[mask] * w).sum(axis=0).tolist())
        per_step["delivered_mbit"].append((delivered[mask] * w).sum(axis=0).tolist())
        per_step["unmet_mbit"].append((unmet[mask] * w).sum(axis=0).tolist())
    return {
        "subinterval": {
            "start_s": starts,
            "duration_s": durations,
            "offered_mbps_total": offered.sum(axis=1).tolist(),
            "delivered_mbps_total": delivered.sum(axis=1).tolist(),
            "unmet_mbps_total": unmet.sum(axis=1).tolist(),
        },
        "per_decision_step_per_slot": per_step,
        "series_notes": (
            "subinterval series are slot totals (per-slot rates per subinterval are "
            "aggregated to per-decision-step per-slot volumes to bound file size); UAV "
            "positions are those in the permitted view at each decision start plus the "
            "final position; the accumulator exposes no per-substep positions"
        ),
    }


def _data_status(record: dict[str, Any]) -> str:
    return "REAL_ACTIVITY_DATA" if record["episode"]["is_real_activity_data"] else "NOT_REAL_DATA"


# ----------------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config).resolve()

    if args.no_admission:
        # Fixture test path only.  Read the raw document (no environment import) and refuse
        # any source other than the self-contained synthetic fixture.
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        if raw.get("source", {}).get("kind") != "synthetic_fixture":
            print("error: --no-admission is only for synthetic_fixture configurations",
                  file=sys.stderr)
            return 2
        admission: Any = "skipped (fixture test)"
    else:
        # Admission precedes environment imports and any output.
        from scripts.hmasd_admission import require_admission

        admission = dict(require_admission(__file__, direction="uav_restoration_readiness"))

    started_utc = _utc_now()
    started = time.perf_counter()

    import numpy as np

    from envs.uav_service_restoration.adapter import make_parallel_env
    from envs.uav_service_restoration.baselines import build_controller
    from envs.uav_service_restoration.config import config_from_dict
    from envs.uav_service_restoration.evaluation import rollout_controller
    from experiments.candidates.uav_restoration_readiness.b01.joint_planner import (
        JointRollingLPController,
    )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)  # the launcher pre-creates the output root
    existing = [name for name in SCIENTIFIC_OUTPUTS if (out / name).exists()]
    if existing and not args.force:
        print(f"error: {out} already holds scientific output {existing}; pass --force",
              file=sys.stderr)
        return 2

    # Same loader path as load_config: JSON -> dict -> config_from_dict (validate()).
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    original_mode = payload.get("observations", {}).get("mode", "central_delayed_telemetry")
    payload.setdefault("observations", {})["mode"] = args.information_mode
    config = config_from_dict(payload)
    if (
        config.source.kind != "synthetic_fixture"
        and args.dataset is None
        and not config.source.dataset_root
    ):
        print(f"error: source.kind={config.source.kind!r} needs --dataset or "
              "source.dataset_root", file=sys.stderr)
        return 2

    episodes_path = Path(args.episodes_file).resolve()
    seeds = load_episode_seeds(episodes_path)
    decision_dt = float(config.episode.decision_dt_s)

    def make_controller(name: str) -> Any:
        if name == "joint_rolling_lp":
            return JointRollingLPController(config, top_k=args.planner_top_k,
                                            max_sweeps=args.planner_max_sweeps)
        return build_controller(name, config, seed=0)

    records: dict[str, dict[int, dict[str, Any]]] = {name: {} for name in args.controllers}
    episode_walls: list[dict[str, Any]] = []
    data_status: str | None = None
    stopped_by_budget = False
    not_started: list[dict[str, Any]] = []

    for seed in seeds:
        for name in args.controllers:
            elapsed = time.perf_counter() - started
            if args.max_wall_s is not None and elapsed >= float(args.max_wall_s):
                stopped_by_budget = True
                not_started.append({"controller": name, "seed": int(seed)})
                continue
            env = make_parallel_env(config, dataset_root=args.dataset, seed=seed)
            recorder = _PositionRecorder(make_controller(name))
            episode_started = time.perf_counter()
            record = rollout_controller(env, recorder, seed=seed)
            wall = time.perf_counter() - episode_started
            status = _data_status(record)
            if data_status is not None and status != data_status:
                print("error: episodes mixed real and non-real data provenance",
                      file=sys.stderr)
                return 4
            data_status = status
            record["episode_seed"] = int(seed)
            records[name][int(seed)] = record
            episode: dict[str, Any] = {
                "controller": name,
                "episode_seed": int(seed),
                "wall_s": wall,
                "record": record,
                "series": _step_series(env, decision_dt),
                "uav_positions_per_decision_start": recorder.positions,
                "uav_positions_final": env.uav_positions_m.tolist(),
            }
            inner = recorder._inner
            if isinstance(inner, JointRollingLPController):
                diagnostics = inner.step_diagnostics
                solves = [int(item["n_lp_solves"]) for item in diagnostics]
                planned = [item for item in diagnostics if item["status"] == "planned"]
                episode["planner"] = {
                    "parameters": inner.parameters,
                    "step_diagnostics": diagnostics,
                    "n_lp_solves_total": int(sum(solves)),
                    "n_lp_solves_per_planned_step_mean": (
                        float(np.mean([item["n_lp_solves"] for item in planned]))
                        if planned else None
                    ),
                    "n_lp_solves_per_step_max": int(max(solves)) if solves else 0,
                    "n_lp_failures_total": int(sum(item["n_lp_failures"] for item in diagnostics)),
                    "n_planned_steps": len(planned),
                    "planner_wall_s_total": float(sum(item["wall_s"] for item in diagnostics)),
                }
            write_json(out / "episodes" / name / f"{int(seed)}.json", episode)
            summary_wall = {"controller": name, "episode_seed": int(seed), "wall_s": wall}
            if "planner" in episode:
                summary_wall["n_lp_solves_total"] = episode["planner"]["n_lp_solves_total"]
                summary_wall["n_lp_solves_per_planned_step_mean"] = episode["planner"][
                    "n_lp_solves_per_planned_step_mean"]
                summary_wall["planner_wall_s_total"] = episode["planner"]["planner_wall_s_total"]
            episode_walls.append(summary_wall)
            print(f"{name} seed={seed} wall={wall:.2f}s "
                  f"sat={record['references']['controller_satisfaction']}", flush=True)

    controllers_summary = {
        name: aggregate([records[name][seed] for seed in seeds if seed in records[name]])
        for name in args.controllers
    }
    for name in args.controllers:
        controllers_summary[name]["episode_seeds"] = [
            seed for seed in seeds if seed in records[name]
        ]

    summary: dict[str, Any] = {
        "tool": "uav_restoration_readiness.b01.run_readiness",
        "direction": DIRECTION,
        "admission": admission,
        "launch_sha": (admission.get("sha") if isinstance(admission, dict) else None),
        "git_head": _git("rev-parse", "HEAD"),
        "training_fits_performed": 0,
        "optimizer_updates": 0,
        "config": str(config_path),
        "config_sha256": _sha256(config_path),
        "config_observations_mode_in_file": original_mode,
        "environment_id": config.environment_id,
        "information_condition": config.observations.mode,
        "diagnostic_rationale": args.diagnostic_rationale,
        "information_mode_note": (
            "the controllers read only env.get_current_state(); that mapping carries the "
            "telemetry store in every observations.mode, so the mode changes observation/"
            "state vectors but not what these controllers see"
        ),
        "dataset_root": args.dataset if args.dataset is not None else config.source.dataset_root,
        "data_status": data_status,
        "episodes_file": str(episodes_path),
        "episodes_file_sha256": _sha256(episodes_path),
        "episode_seeds": seeds,
        "controllers_requested": list(args.controllers),
        "planner_parameters": {"top_k": args.planner_top_k,
                               "max_sweeps": args.planner_max_sweeps},
        "controllers": controllers_summary,
        "paired_differences": paired_differences(records, seeds),
        "per_episode_wall": episode_walls,
        "max_wall_s": args.max_wall_s,
        "stopped_by_wall_budget": stopped_by_budget,
        "episodes_not_started": not_started,
        "episode_order": "seed-major: every requested controller for a seed, then the next seed",
        "recovery_definition": {
            "recovery_fraction_rho": config.evaluation.recovery_fraction_rho,
            "recovery_sustain_s": config.evaluation.recovery_sustain_s,
        },
        "interpreter": {
            "executable": sys.executable,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": __import__("scipy").__version__,
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
