"""R03 calibration and its fixed E01 assessment; no full census entry point."""

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

_ENTRY_TIME = perf_counter()

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.variable_n_fleet_churn_causal_headroom.calibration import (
    project, serialization_probe, synthetic_solver_probe,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("calibration", "toy", "e01", "e01-smoke"), required=True)
    parser.add_argument("--seed", type=int, default=2026090311)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode.startswith("e01"):
        return run_e01(args)
    start = perf_counter()
    if args.mode == "toy":
        native = {"scores": [{"seconds": .001, "candidate_count": 1, "agreement": True}],
                  "ticks": {"seconds": .00001, "count": 1},
                  "prehistory": {"seconds": .001, "calls": 1}}
    else:
        from experiments.candidates.variable_n_fleet_churn_causal_headroom.native_backend import calibrate_native
        native = calibrate_native()
    solver = synthetic_solver_probe(args.mode == "toy")
    serialization = serialization_probe(args.mode == "toy")
    projection = project(native, solver, serialization)
    summary = {
        "object": "VNFC-CONTROLLER-HEADROOM-A-RECON-CAUSAL-ONE-DEVIATION-R03",
        "mode": args.mode, "launch_sha": args.launch_sha,
        "fixed_panel_seed_metadata_only": args.seed,
        "native": native, "synthetic_solver": solver,
        "synthetic_serialization": serialization, "projection": projection,
        "new_rng_draws": 0, "models": 0, "optimizer_updates": 0,
        "training_transitions": 0, "checkpoints": 0,
        "native_panel_worlds": 0, "native_candidate_endpoints": 0,
        "scientific_result": False, "full_census_implemented": False,
        "wall_seconds": perf_counter() - start,
    }
    if sys.platform.startswith("linux"):
        import resource
        summary["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    else:
        summary["peak_rss_bytes"] = None
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": projection["status"], "projected_seconds": projection["projected_seconds"],
                      "summary": str(args.out / "summary.json")}))
    return 0 if all(row["agreement"] for row in native["scores"]) and summary["wall_seconds"] < 60 else 1


def run_e01(args):
    import resource
    from experiments.candidates.variable_n_fleet_churn_causal_headroom.e01 import (
        assess, assess_smoke, publish, stamp,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    result = assess(args.out) if args.mode == "e01" else assess_smoke(args.out)
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    summary = dict(
        object="VNFC-R03-EXACT-BATCH-FEASIBILITY-E01", mode=args.mode,
        launch_sha=args.launch_sha, fixed_panel_seed_metadata_only=args.seed,
        result=result, scientific_result=False, full_census_implemented=False,
        native_target_worlds=0, new_rng_draws=0, models=0, optimizer_updates=0,
        training_transitions=0, checkpoints=0,
        peak_rss_main_bytes=own.ru_maxrss * 1024,
        peak_rss_largest_child_bytes=children.ru_maxrss * 1024,
        rss_scope="separate process peaks, not concurrent summed memory",
        inner_wall_before_summary=perf_counter() - _ENTRY_TIME,
        aggregate_cpu_before_summary=stamp()[1],
        cost_scope="process CPU includes compiler children; external GNU time is whole-invocation wall/CPU authority",
    )
    summary_publication = publish(args.out / "summary.json", summary)
    # These finite final readings follow the actual summary write and readback.
    # The enclosing OS timing additionally covers interpreter startup and exit.
    wall, cpu = perf_counter() - _ENTRY_TIME, stamp()[1]
    within_caps = wall <= 60 and cpu <= 300
    projected = result.get("projection", {}).get("projected_wall_seconds")
    print(json.dumps(dict(summary=str(args.out / "summary.json"),
                          summary_publication=summary_publication,
                          inner_complete_wall_seconds=wall, aggregate_cpu_seconds=cpu,
                          measured_inner_caps=within_caps, projected_wall_seconds=projected,
                          outer_cost_required=True)))
    return 0 if within_caps and (projected is None or projected < 2700) else 1


if __name__ == "__main__":
    raise SystemExit(main())
