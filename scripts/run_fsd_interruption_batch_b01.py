"""FSD interruption-by-batch: eight originals and their block-aware B readout.

Renewal and batch are separately bound; the native collector/evaluator is reused.
Ordinary wall plans are not deadlines. No retry, extra endpoint or baseline fit.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import run_fsd_uav_individual_renewal_b01 as shared

OBJECT_ID = "FSD_INTERRUPTION_BATCH_B01"
CARD = "docs/research/candidates/flexible_skill_duration/FSD_INTERRUPTION_BATCH_B01_PROSPECTIVE_CARD_20260914.md"
BLOCKS = {772003: 782003, 772103: 782103}
ARMS = {"D128": ("D0", 128), "D1280": ("D0", 1280), "I128": ("I", 128), "I1280": ("I", 1280)}
WALL_PLANS = {"D128": 900., "D1280": 900., "I128": 1800., "I1280": 1800.}
CONTRASTS = {
    "SI1280": {"I1280": 1., "D1280": -1.},
    "SI128": {"I128": 1., "D128": -1.},
    "MI": {"I1280": .5, "D1280": -.5, "I128": .5, "D128": -.5},
    "MB": {"D1280": .5, "D128": -.5, "I1280": .5, "I128": -.5},
    "INT": {"I1280": 1., "D1280": -1., "I128": -1., "D128": 1.},
    "PKG": {"I1280": 1., "D128": -1.},
}


def make_config(arm, envs, seed):
    renewal, batch = ARMS[arm]
    return shared.make_config(renewal, envs, seed, coordinator_batch_size=batch)


def run_fit(arm, seed, out):
    renewal, batch = ARMS[arm]
    evaluation_seed = BLOCKS[seed]
    summary = shared.base_summary(renewal, training_seed=seed, evaluation_seed=evaluation_seed,
                                  object_id=OBJECT_ID, card=CARD, caps=None)
    summary.update(factorial_arm=arm, block_seed=seed, ordinary_wall_plan_seconds=WALL_PLANS[arm],
                   cost_law="15 * sum_rollout ceil(valid_joint_rows / coordinator_batch_size)",
                   coordinator_batch_size=batch)
    out.mkdir(parents=True, exist_ok=True)
    try:
        shared.write_json(out / "manifest.json", {k: v for k, v in summary.items()
                          if k not in ("status", "failure", "training_rows", "evaluation", "counts")})
        shared.publish(out, summary, "setup")
        envs, learner, theta0, counters = shared.build_learner(
            summary, out, training_seed=seed, coordinator_batch_size=batch)
        shared.collect_training(envs, learner, theta0, counters, summary, out)
        shared.final_evaluation(learner, summary, out, evaluation_seed=evaluation_seed,
                                 coordinator_batch_size=batch)
        summary["status"] = "complete"
        try:
            if shared.sys.platform == "win32":
                import psutil
                summary["peak_rss_bytes"] = int(psutil.Process().memory_info().peak_wset)
            else:
                import resource
                summary["peak_rss_bytes"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss *
                                                (1 if shared.sys.platform == "darwin" else 1024))
        except (ImportError, OSError):
            summary["peak_rss_bytes"] = None
        shared.publish(out, summary, "final")
    except Exception as exc:
        summary["status"], summary["failure"] = "incomplete", f"{type(exc).__name__}: {exc}"
        shared.write_json(out / "summary.json", summary)
    print(json.dumps({"arm": arm, "seed": seed, "status": summary["status"], "failure": summary["failure"]}))
    return 0 if summary["status"] == "complete" else 1


def arm_endpoint(summary):
    """Read a complete card endpoint; failures limit its dependent contrasts only."""
    seed, arm = summary["block_seed"], summary["factorial_arm"]
    renewal, batch = ARMS[arm]
    evaluation_seed = BLOCKS[seed]
    if (summary["object_id"] != OBJECT_ID or summary["card"] != CARD
            or summary["arm"] != renewal or summary["status"] != "complete"
            or summary["training_seed"] != seed or summary["evaluation_seed"] != evaluation_seed):
        raise ValueError("incomplete or wrong arm/block/object")
    counts, endpoint = summary["counts"], summary["evaluation"]
    expected_counts = {
        "model_constructions": 2, "training_starts": 1, "checkpoint_loads": 0,
        "training_transitions": shared.TRAIN_LANES * shared.HORIZON * shared.ROLLOUTS,
        "stored_training_transitions": shared.TRAIN_LANES * shared.HORIZON * shared.ROLLOUTS,
        "training_episodes": shared.TRAIN_LANES * shared.ROLLOUTS, "update_stages": shared.ROLLOUTS,
        "training_agent_step_batches": shared.HORIZON * shared.ROLLOUTS,
        "evaluation_steps": shared.EVAL_LANES * shared.HORIZON,
        "evaluation_agent_step_batches": shared.HORIZON, "evaluation_episodes": shared.EVAL_LANES,
    }
    if any(counts[k] != v for k, v in expected_counts.items()):
        raise ValueError("incomplete training/final exposure")
    if (len(summary["training_rows"]) != shared.ROLLOUTS
            or not all(row["updated"] for row in summary["training_rows"])
            or any(summary["optimizer_calls"][k] <= 0 for k in ("discoverer_actor", "discoverer_critic"))
            or any(summary["evaluation_optimizer_calls"].values())):
        raise ValueError("missing learner updates or evaluator learning")
    for key, lanes, phase_seed in (("learner_config", shared.TRAIN_LANES, seed),
                                    ("evaluation_config", shared.EVAL_LANES, evaluation_seed)):
        config = summary[key]
        expected = {"policy_interruption_mode": "d2", "interruption_cost_c": .25 if renewal == "I" else "Infinity",
                    "interruption_cost_c_Z": "Infinity", "k": 10, "skill_cap_k_max": 10, "team_cap_k_Z": 10,
                    "interruption_delta": 1, "age_feature": "off", "n_Z": 6, "n_z": 6, "n_agents": shared.N_UAVS,
                    "n_users": shared.N_USERS, "num_envs": lanes, "rollout_length": shared.HORIZON,
                    "seed": phase_seed, "coordinator_batch_size": batch}
        if any(config[k] != v for k, v in expected.items()):
            raise ValueError("arm construction mismatch: " + key)
    if (summary["training_lane_seeds"] != list(range(seed, seed + shared.TRAIN_LANES))
            or summary["evaluation_lane_seeds"] != list(range(evaluation_seed, evaluation_seed + shared.EVAL_LANES))
            or endpoint["status"] != "complete" or endpoint["after_update"] != shared.ROLLOUTS
            or endpoint["episode_ids"] != list(range(shared.EVAL_LANES))
            or endpoint["lane_seeds"] != summary["evaluation_lane_seeds"]
            or endpoint["steps_per_lane"] != [shared.HORIZON] * shared.EVAL_LANES
            or endpoint["completed_episodes"] != shared.EVAL_LANES):
        raise ValueError("wrong sole-final endpoint or lane seeds")
    scores = np.asarray(endpoint["native_scores_J"], dtype=np.float64)
    returns = np.asarray(endpoint["returns_U"], dtype=np.float64)
    if scores.shape != (shared.EVAL_LANES,) or returns.shape != scores.shape:
        raise ValueError("missing primary values")
    shared.require_finite((scores, returns), "arm primary")
    if not np.allclose(returns * shared.N_UAVS / shared.HORIZON, scores, rtol=1e-9, atol=1e-9):
        raise ValueError("native return scaling mismatch")
    return scores


def block_statistics(values):
    count = len(values)
    mean = float(np.mean(values)) if count else None
    sd = float(np.std(values, ddof=1)) if count == 2 else None
    se = sd / math.sqrt(count) if sd is not None else None
    # Exactly two planned independent blocks: t(.975,df=1) is a Cauchy quantile.
    half = math.tan(math.pi * .475) * se if se is not None else None
    return {"available_training_blocks": count, "planned_training_blocks": 2, "mean": mean,
            "sample_sd": sd, "se": se, "working_model_95pct_interval":
            [mean - half, mean + half] if half is not None else None,
            "working_model": "iid-normal block contrasts; df=1 with two blocks; assumptions uncheckable, coverage not established"}


def assemble_blocks(summaries):
    supplied = {}
    for summary in summaries:
        key = (summary["block_seed"], summary["factorial_arm"])
        if key[0] not in BLOCKS or key[1] not in ARMS or key in supplied:
            raise ValueError("unselected or duplicate original arm/block")
        supplied[key] = summary
    blocks, contrast_values = [], {name: [] for name in CONTRASTS}
    for seed in BLOCKS:
        endpoints, failures, rows = {}, {}, {}
        for arm in ARMS:
            result = supplied.get((seed, arm))
            if result is None:
                failures[arm] = "not supplied"
                continue
            try:
                endpoints[arm] = arm_endpoint(result)
                rows[arm] = {"J": float(endpoints[arm].mean()), "endpoint_scores_J": endpoints[arm].tolist(),
                             "launch_sha": result["launch_sha"], "counts": result["counts"],
                             "optimizer_calls": result["optimizer_calls"],
                             "wall_seconds_before_publication": result.get("wall_seconds_before_publication"),
                             "peak_rss_bytes": result.get("peak_rss_bytes")}
            except (KeyError, TypeError, ValueError) as exc:
                failures[arm] = str(exc)
        contrasts = {}
        for name, weights in CONTRASTS.items():
            if not all(arm in endpoints for arm in weights):
                contrasts[name] = {"status": "incomplete", "missing_operands": [a for a in weights if a not in endpoints]}
                continue
            operands = [supplied[(seed, arm)] for arm in weights]
            # Unplanned common-config/information differences invalidate only this contrast.
            comparable = []
            for result in operands:
                common = {k: result[k] for k in ("host", "device", "torch_threads", "learner_precision",
                                               "reward_return_precision", "native_score_factor")}
                for phase in ("learner_config", "evaluation_config"):
                    common[phase] = {k: v for k, v in result[phase].items()
                                     if k not in ("interruption_cost_c", "coordinator_batch_size")}
                comparable.append(common)
            if any(other != comparable[0] for other in comparable[1:]):
                contrasts[name] = {"status": "incomplete", "failure": "unplanned comparator difference"}
                continue
            differences = sum(weight * endpoints[arm] for arm, weight in weights.items())
            value = float(differences.mean())
            contrasts[name] = {"status": "complete", "value": value,
                               "conditional_episode_sd": float(differences.std(ddof=1)),
                               "conditional_episode_se": float(differences.std(ddof=1) / math.sqrt(shared.EVAL_LANES))}
            contrast_values[name].append(value)
        blocks.append({"training_seed": seed, "evaluation_seed": BLOCKS[seed], "arms": rows,
                       "missing_or_invalid_arms": failures, "contrasts": contrasts})
    aggregate = {name: block_statistics(values) for name, values in contrast_values.items()}
    primary = dict(aggregate["SI1280"], name="SI1280", mei_J=.01)
    mean = primary["mean"]
    primary["available_mean_reading"] = (None if mean is None else "above_mei" if mean > .01
                                          else "opposite_sign" if mean < -.01 else "small_or_unresolved")
    return {"object_id": OBJECT_ID, "card": CARD, "launch_sha": shared.e0._git("rev-parse", "HEAD"),
            "status": "complete" if all(c["available_training_blocks"] == 2 for c in aggregate.values()) else "incomplete",
            "blocks": blocks, "contrasts": aggregate, "primary": primary,
            "interpretation_limit": "Two independent training blocks, no episode-as-training replication, equivalence or historical pooling."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--arm", choices=tuple(ARMS), required=True)
    fit.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    fit.add_argument("--output-root", type=Path, required=True)
    reduce = sub.add_parser("reduce")
    reduce.add_argument("--summaries", type=Path, nargs="+", required=True)
    reduce.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "fit":
        return run_fit(args.arm, args.seed, args.output_root.resolve())
    result = assemble_blocks([json.loads(p.read_text(encoding="utf-8")) for p in args.summaries])
    result["input_summaries"] = [str(p) for p in args.summaries]
    args.output_root.mkdir(parents=True, exist_ok=True)
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({"status": result["status"], "primary": result["primary"]}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
