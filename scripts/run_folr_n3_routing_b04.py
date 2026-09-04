"""N3/FOLR B04: paired reward-learning curves on the unchanged B3 host."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def result_rule(differences: list[float]) -> dict:
    mean = sum(differences) / len(differences)
    if mean >= 0.05 and sum(x > 0 for x in differences) >= 2:
        branch = "B04_TYPED_SIGNAL"
    elif mean <= -0.05 and sum(x < 0 for x in differences) >= 2:
        branch = "B04_GENERIC_SIGNAL"
    elif abs(mean) < 0.05:
        branch = "B04_WITHIN_MEI"
    else:
        branch = "B04_HETEROGENEOUS"
    return {"branch": branch, "mean_stale_auc_difference": mean,
            "seed_stale_auc_differences": differences, "mei": 0.05}


def expected_counts(seeds: int, updates: int, batch_size: int,
                    eval_episodes: int, eval_every: int) -> dict:
    points = len(range(0, updates + 1, eval_every))
    if updates % eval_every:
        points += 1
    writer_train = seeds * updates * batch_size
    routing_train = 3 * writer_train
    writer_eval = seeds * points * eval_episodes
    routing_eval = 3 * seeds * points * 2 * eval_episodes
    latch_eval = seeds * 2 * eval_episodes
    episodes = writer_train + routing_train + writer_eval + routing_eval + latch_eval
    return {"writer_training_episodes": writer_train,
            "routing_training_episodes": routing_train,
            "training_episodes": writer_train + routing_train,
            "writer_updates": seeds * updates,
            "routing_updates": 3 * seeds * updates,
            "learner_updates": 4 * seeds * updates,
            "writer_evaluation_episodes": writer_eval,
            "routing_evaluation_episodes": routing_eval,
            "latch_evaluation_episodes": latch_eval,
            "evaluation_episodes": writer_eval + routing_eval + latch_eval,
            "complete_episodes": episodes, "primitive_transitions": 3 * episodes}


def cost_projection(coefficients: dict) -> dict:
    """Full three-seed costs; every routing arm pays the entire shared writer."""
    costs = {}
    for phase in ("WRITER", "TYPED", "GENERIC", "RESET"):
        c = coefficients[phase]
        eval_count = 6912 if phase == "WRITER" else 13824
        costs[phase] = (24576 * c["seconds_per_train_episode"]
                        + eval_count * c["seconds_per_eval_episode"])
    latch = 1536 * coefficients["LATCH"]["seconds_per_eval_episode"]
    charged = {arm: costs["WRITER"] + costs[arm]
               for arm in ("TYPED", "GENERIC", "RESET")}
    return {"cost_law": "train_episodes * seconds_per_train_episode + eval_episodes * seconds_per_eval_episode",
            "coefficients": coefficients, "three_seed_phase_seconds": costs,
            "three_seed_routing_arm_seconds_with_full_shared_writer": charged,
            "three_seed_latch_seconds": latch,
            "total_seconds": sum(costs.values()) + latch,
            "per_phase_or_charged_arm_cap_seconds": 600,
            "full_invocation_cap_seconds": 2400}


def exposure_line() -> dict:
    writer_rms = (2 / 6) ** 0.5
    router_rms = (2 / 12) ** 0.5
    return {"updates_per_learner": 128, "Adam_lr": 0.025,
            "nominal_coordinate_path": 128 * 0.025,
            "writer_min_nonzero_Xavier_RMS": writer_rms,
            "writer_nominal_ratio": 128 * 0.025 / writer_rms,
            "router_min_nonzero_Xavier_RMS": router_rms,
            "router_nominal_ratio": 128 * 0.025 / router_rms,
            "meaning": "Nominal learning-rate path, not a realized displacement bound."}


def summarize(seed_results: list[dict], *, configuration: dict, launch_sha: str,
              wall_seconds: float, peak_rss_bytes: int | None) -> dict:
    differences = [r["arms"]["TYPED"]["auc"]["STALE_LOAD"]
                   - r["arms"]["GENERIC"]["auc"]["STALE_LOAD"] for r in seed_results]
    means = {arm: sum(r["arms"][arm]["final"]["STALE_LOAD"]["return"]
                     for r in seed_results) / len(seed_results)
             for arm in ("TYPED", "GENERIC", "RESET")}
    writer_mean = sum(r["writer"]["final"]["CALIBRATION"]["return"]
                      for r in seed_results) / len(seed_results)
    latch_mean = sum(r["latch"]["final"]["STALE_LOAD"]["return"]
                     for r in seed_results) / len(seed_results)
    coefficients = {}
    totals = {"train_episodes": 0, "eval_episodes": 0, "updates": 0,
              "primitive_transitions": 0}
    for phase in ("WRITER", "TYPED", "GENERIC", "RESET", "LATCH"):
        entries = [r["writer"] if phase == "WRITER" else r["latch"]
                   if phase == "LATCH" else r["arms"][phase] for r in seed_results]
        train_n = sum(p["counts"]["train_episodes"] for p in entries)
        eval_n = sum(p["counts"]["eval_episodes"] for p in entries)
        coefficients[phase] = {
            "seconds_per_train_episode": sum(p["wall_seconds"]["train"] for p in entries) / train_n if train_n else 0.0,
            "seconds_per_eval_episode": sum(p["wall_seconds"]["evaluation"] for p in entries) / eval_n,
        }
        for key in totals:
            totals[key] += sum(p["counts"][key] for p in entries)
    totals["complete_episodes"] = totals["train_episodes"] + totals["eval_episodes"]
    rule = result_rule(differences)
    if configuration["technical_only"]:
        rule["interpretation"] = "Technical smoke only; this is not the full B04 result."
    return {
        "object": "N3-FOLR-ROUTING-B04", "launch_sha": launch_sha,
        "configuration": configuration, "exposure": exposure_line(),
        "seed_results": seed_results, "counts": totals,
        "seed_comparisons": [{"seed": r["seed"], "regimes": {
            regime: {"typed_minus_generic_auc": r["arms"]["TYPED"]["auc"][regime] - r["arms"]["GENERIC"]["auc"][regime],
                     "typed_minus_generic_final_return": r["arms"]["TYPED"]["final"][regime]["return"] - r["arms"]["GENERIC"]["final"][regime]["return"]}
            for regime in ("CLEAN", "STALE_LOAD")}} for r in seed_results],
        "expected_counts": expected_counts(len(seed_results), configuration["updates"],
                                            configuration["batch_size"], configuration["eval_episodes"],
                                            configuration["eval_every"]),
        "result_rule": rule,
        "descriptive_flags": {"writer_weak": writer_mean < 0.90,
                              "simple_control_headroom": latch_mean - max(means["TYPED"], means["GENERIC"]) >= 0.05,
                              "mean_final_writer_return": writer_mean,
                              "mean_final_latch_stale_return": latch_mean,
                              "mean_final_stale_return_by_arm": means},
        "optimization_cost_note": "LATCH has zero receiver updates and reuses the paid writer; learned routing arms each have their own updates.",
        "cost_projection": cost_projection(coefficients),
        "resources": {"wall_seconds": wall_seconds, "peak_rss_bytes": peak_rss_bytes,
                      "status": "measured" if peak_rss_bytes is not None else "resources_unmeasured"},
        "publication_coverage": "The technical smoke invokes this same final summary and JSONL/checkpoint publication path; full training constants remain prospective until the full invocation completes.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[96041, 96042, 96043])
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    import torch
    from experiments.candidates.vap_folr_core.n3_routing_b04.learning import run_seed

    torch.set_num_threads(1)
    torch.set_default_dtype(torch.float32)
    configuration = {"seeds": args.seeds, "updates": 2 if args.smoke else 128,
                     "batch_size": 64, "eval_episodes": 256,
                     "eval_every": 1 if args.smoke else 16,
                     "technical_only": args.smoke, "device": "cpu", "dtype": "float32",
                     "learning_rate": 0.025, "torch_threads": 1,
                     "rng": "Explicit seed namespaces; paired routing initialization, data and action uniforms; fixed separate evaluation tapes."}
    launch_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    args.output_root.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    results = []
    for seed in args.seeds:
        result = run_seed(seed, updates=configuration["updates"], batch_size=64,
                          eval_episodes=configuration["eval_episodes"],
                          eval_every=configuration["eval_every"], output_root=args.output_root)
        results.append(result)
        print(json.dumps({"completed_seed": seed, "wall_seconds": time.perf_counter() - started}), flush=True)
    peak_rss = None
    if sys.platform != "win32":
        import resource
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    summary = summarize(results, configuration=configuration, launch_sha=launch_sha,
                        wall_seconds=time.perf_counter() - started, peak_rss_bytes=peak_rss)
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": str(args.output_root / "summary.json"), "counts": summary["counts"],
                      "cost_projection": summary["cost_projection"]}), flush=True)


if __name__ == "__main__":
    main()
