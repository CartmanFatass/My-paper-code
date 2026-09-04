"""Run one B02 pilot or main seed; memory admission is external to this runner."""

import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.candidates.metric_ground_transport_allocation.actor import Actor
from experiments.candidates.metric_ground_transport_allocation.config import ORDERED_PAIRS, LOADS, TRAIN_SIZES
from experiments.candidates.metric_ground_transport_allocation.mgtap_b02_curves.numerical import (
    evaluation_groups, evaluate, oracle_population, training_step,
)
from experiments.candidates.metric_ground_transport_allocation.mgtap_b02_curves.reporting import (
    MAIN_GRID, MAIN_SEEDS, cost_law, curve_point, summarize,
)


def peak_rss_bytes():
    try:
        if sys.platform == "win32":
            import psutil
            return psutil.Process().memory_info().peak_wset
        import resource
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024))
    except (ImportError, AttributeError, OSError):
        return None


def fit_arm(arm, seed, updates, grid, tapes, cap, groups, oracle, out, result):
    started = perf_counter()
    actor = Actor(arm, "INTACT")
    optimizer = torch.optim.SGD(actor.parameters(), lr=0.1, momentum=0.0, weight_decay=0.0)
    trace, parameters, episode_returns, checkpoints = [], [], [], []
    result.update(status="incomplete", updates=0, curve=[])
    update_seconds = evaluation_seconds = path_length = 0.0
    try:
        for update in range(updates + 1):
            if perf_counter() - started >= cap:
                result["status"] = "budget_truncated"
                break
            if update:
                tick = perf_counter()
                row = training_step(actor, optimizer, seed, update)
                elapsed = perf_counter() - tick
                update_seconds += elapsed
                path_length += row["step_displacement_l2"]
                row.update(cumulative_path_l2=path_length, wall_seconds=elapsed)
                trace.append(row)
                result["updates"] = update
            if update in grid:
                if perf_counter() - started >= cap:
                    result["status"] = "budget_truncated"
                    break
                tick = perf_counter()
                values = evaluate(actor, groups, tapes)
                result["curve"].append(curve_point(update, values, oracle))
                parameters.append(actor.parameter_vector())
                episode_returns.append(values)
                checkpoints.append(update)
                evaluation_seconds += perf_counter() - tick
        else:
            result["status"] = "complete" if perf_counter() - started < cap else "budget_truncated"
    finally:
        # Required learner measurements are retained even when an invocation fails.
        (out / f"{arm}_training.json").write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
        np.savez(out / f"{arm}_evaluation.npz", checkpoints=np.asarray(checkpoints, dtype=np.int64),
                 parameters=np.asarray(parameters, dtype=np.float64).reshape(-1, 60),
                 episode_returns=np.asarray(episode_returns, dtype=np.float64).reshape(-1, 2, 12, 2, tapes),
                 sizes=np.asarray(TRAIN_SIZES), pairs=np.asarray(ORDERED_PAIRS), loads=np.asarray(LOADS))
        result.update(
            training_decisions=sum(row["training_decisions"] for row in trace),
            training_agent_steps=sum(row["training_agent_steps"] for row in trace),
            evaluation_episodes=sum(row["evaluation_episodes"] for row in result["curve"]),
            evaluation_decisions=sum(row["evaluation_decisions"] for row in result["curve"]),
            evaluation_agent_steps=sum(row["evaluation_agent_steps"] for row in result["curve"]),
            cumulative_path_l2=path_length,
            update_seconds=update_seconds, evaluation_seconds=evaluation_seconds,
            cost=cost_law(update_seconds, len(trace), evaluation_seconds, len(checkpoints)),
            wall_seconds=perf_counter() - started,
            training_trace=f"{arm}_training.json", evaluation_arrays=f"{arm}_evaluation.npz",
        )


def run(mode, seed, out, oracle_path=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    updates, grid, tapes, cap = {"pilot": (16, (0, 16), 16, 30.0),
                                "main": (256, MAIN_GRID, 16, 100.0),
                                "smoke": (1, (0, 1), 2, 30.0)}[mode]
    summary = {
        "mode": mode, "seed": seed, "status": "incomplete", "branch": None,
        "evidence_class": "B_development" if mode == "pilot" else ("test_only" if mode == "smoke" else "B_explore"),
        "launch_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "argv": sys.argv, "node": platform.node(), "cwd": str(Path.cwd()), "output_root": str(out.resolve()),
        "configuration": {"updates": updates, "grid": list(grid), "evaluation_tapes": tapes,
                          "sizes": list(TRAIN_SIZES), "arms": ["METRIC", "FREE"], "binding": "INTACT",
                          "dtype": "float64", "device": "cpu", "threads": 1, "learning_rate": 0.1,
                          "momentum": 0, "weight_decay": 0, "gradient_clip": 5,
                          "parameters": 60, "init_l2": 0, "max_path_l2": updates * 0.1 * 5,
                          "unit_logit_reference": 1, "arm_cap_seconds": cap},
        "arms": {},
    }
    try:
        setup_started = perf_counter()
        torch.set_num_threads(1)
        oracle = np.load(oracle_path) if oracle_path is not None else oracle_population(setup_started + 60.0)
        groups = evaluation_groups(seed, tapes)
        np.save(out / "oracle_returns.npy", oracle)
        summary["shared_setup_seconds"] = perf_counter() - setup_started
        summary["oracle_source"] = str(Path(oracle_path).resolve()) if oracle_path is not None else "computed_once"
        summary["oracle"] = {"return": float(oracle.mean()), "by_n": {
            str(n): {"return": float(oracle[i].mean()), "by_load": {
                load: float(oracle[i, :, j].mean()) for j, load in enumerate(LOADS)}}
            for i, n in enumerate(TRAIN_SIZES)}}
        if summary["shared_setup_seconds"] >= 60.0:
            raise TimeoutError("B02 shared setup exceeded 60 seconds")
        for arm in ("METRIC", "FREE"):
            summary["arms"][arm] = {}
            fit_arm(arm, seed, updates, grid, tapes, cap, groups, oracle, out, summary["arms"][arm])
        summary["status"] = "complete" if all(a["status"] == "complete" for a in summary["arms"].values()) else "budget_truncated"
    finally:
        summary["wall_seconds"] = perf_counter() - started
        summary["peak_rss_bytes"] = peak_rss_bytes()
        summary["resource_status"] = "measured" if summary["peak_rss_bytes"] is not None else "resources_unmeasured"
        (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("pilot", "main", "smoke", "summarize"), required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, help="Pilot oracle_returns.npy, required for main")
    parser.add_argument("--inputs", type=Path, nargs="+", help="Existing main summary.json files, for offline summarize only")
    args = parser.parse_args()
    if args.mode == "summarize":
        if not args.inputs:
            parser.error("summarize requires --inputs")
        result = summarize([json.loads(path.read_text(encoding="utf-8")) for path in args.inputs])
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    else:
        if args.seed is None:
            parser.error("a run requires --seed")
        if args.mode == "pilot" and args.seed != 1907:
            parser.error("the frozen pilot seed is 1907")
        if args.mode == "main" and args.seed not in MAIN_SEEDS:
            parser.error("the frozen main seeds are 203, 211, 223")
        if args.mode == "main" and args.oracle is None:
            parser.error("main requires --oracle from the pilot")
        result = run(args.mode, args.seed, args.out, args.oracle)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
