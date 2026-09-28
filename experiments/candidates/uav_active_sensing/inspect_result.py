"""Read-only, post-run integrity and activation reading; no simulator or learner calls."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np


def read_json(path):
    return json.loads(path.read_text())


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def close(left, right):
    if not np.allclose(left, right, rtol=1e-10, atol=1e-9):
        raise ValueError(f"native aggregate differs: {left} != {right}")


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1 << 20), b""):
            value.update(data)
    return value.hexdigest()


def trace_check(out, row):
    with np.load(out / row["raw_path"], allow_pickle=False) as raw:
        reward, metrics, ends = raw["reward"], raw["metrics"], raw["ends"]
        fields = list(raw["metric_fields"])
        if (len(reward) != 3000 or row["actual_length"] != 3000
                or ends[:-1].any() or not np.array_equal(ends[-1], [False, True])):
            raise ValueError("incomplete native H3000 trace")
        if not np.isfinite(reward).all() or not np.isfinite(metrics).all():
            raise ValueError("nonfinite native trace")
        col = {field: metrics[:, i] for i, field in enumerate(fields)}
        close(reward, col["qos_satisfaction_ratio"] - 2 * col["return_constraint_cost"]
              - col["cutoff_event_penalty"] - col["depletion_event_penalty"] + col["graph_potential_delta"])
        close(reward.sum(), row["raw_native_J"])
        close(col["qos_satisfaction_ratio"].mean(), row["qos_per_step"])
        close(col["battery_min_ratio"].min(), row["episode_minimum_battery_ratio"])
        close(np.mean(raw["battery"] < .10), row["reserve10_uav_step_fraction"])
        for i, field in enumerate(fields):
            close(metrics[:, i].sum(), row[f"{field}_sum"])
            close(metrics[:, i].mean(), row[f"{field}_per_step"])


def inspect(out):
    started = time.monotonic()
    manifest, config = read_json(out / "manifest.json"), read_json(out / "config.json")
    summary, training = read_json(out / "summary.json"), read_json(out / "training.json")
    rows = read_json(out / "perworld.json")
    if summary["status"] != "complete" or training["status"] != "complete":
        raise ValueError("this reader requires the complete accepted batch")
    for relative, entry in manifest["artifacts"].items():
        path = out / relative
        if path.stat().st_size != entry["bytes"] or digest(path) != entry["sha256"]:
            raise ValueError(f"artifact identity differs: {relative}")
    if summary["actual_native_steps"] != 720000 or training["actual_native_steps"] != 480000:
        raise ValueError("native exposure count differs")
    if {(r["arm"], r["seed"]) for r in rows} != {(r["arm"], r["seed"]) for r in config["jobs"]} or len(rows) != 80:
        raise ValueError("evaluation panel identity differs")
    training_rows, macro_rows = [], []
    for lane in range(4):
        episodes = read_json(out / "training" / f"lane{lane}.episodes.json")
        macros = read_lines(out / "training" / f"lane{lane}.macros.jsonl")
        if [row["seed"] for row in episodes] != config["training_seeds"][lane::4] or len(macros) != 4000:
            raise ValueError("lane seed/exposure schedule differs")
        for index, episode in enumerate(episodes):
            part = macros[index * 100:(index + 1) * 100]
            if ([m["macro_start"] for m in part] != list(range(0, 3000, 30))
                    or any(m["macro_native_steps"] != 30 or m["world_seed"] != episode["seed"]
                           or m["TimeLimit.truncated"] for m in part)):
                raise ValueError("native macro schedule or terminal-bootstrap guard differs")
            close(sum(m["native_reward_sum"] for m in part), episode["raw_native_J"])
        training_rows.extend(episodes)
        macro_rows.extend(macros)
    for row in rows + training_rows:
        trace_check(out, row)
    rollouts, updates = read_lines(out / "training" / "rollouts.jsonl"), read_lines(out / "training" / "updates.jsonl")
    if (len(rollouts) != 40 or [r["optimizer_steps"] for r in updates] != list(range(40, 1601, 40))
            or any(not row["stored_native_rewards_exact_float32"] or not row["stored_requested_actions_exact"]
                   or not row["all_finite_horizon_dones"] for row in rollouts)):
        raise ValueError("complete PPO rollout/update audit differs")
    by_key = {(r["arm"], r["seed"]): r for r in rows}
    gates = []
    for row in rows:
        with np.load(out / row["raw_path"], allow_pickle=False) as raw:
            if not np.array_equal(raw["plan_step"], np.arange(0, 3000, 30)):
                raise ValueError("evaluation macro clock differs")
            known, eligible = raw["plan_bs_known"].astype(bool), raw["plan_eligible"].astype(bool)
            requested, executed = raw["plan_requested"], raw["plan_executed"]
            if np.any((~eligible) & (executed != 0)) or np.any((requested < 0) | (requested > 256)):
                raise ValueError("illegal scout execution or requested action")
            close(eligible.sum(), row["eligible_plans"])
            close(np.count_nonzero(executed), row["executed_scout_plans"])
            close(raw["sense_actual_travel_m"].sum(), row["actual_team_travel_m"])
            close((raw["sense_first_seen_step"] >= 0).sum(), row["discovered_users"])
            base_row = by_key[("H", row["seed"])]
            with np.load(out / base_row["raw_path"], allow_pickle=False) as base:
                identical = all(np.array_equal(raw[key], base[key], equal_nan=True)
                                for key in ("own_xyz", "target_xy", "mode", "reward", "metrics", "ends"))
            gates.append({
                "arm": row["arm"], "seed": row["seed"],
                "known_bs_plans": int(known.sum()),
                "first_known_bs_plan_step": int(raw["plan_step"][known][0]) if known.any() else None,
                "eligible_plans": int(eligible.sum()),
                "first_eligible_plan_step": int(raw["plan_step"][eligible][0]) if eligible.any() else None,
                "eligible_service_requests": int(np.count_nonzero(eligible & (requested == 0))),
                "executed_scout_plans": int(np.count_nonzero(executed)),
                "effective_action_histogram": {str(k): v for k, v in sorted(Counter(map(int, executed)).items())},
                "exact_native_path_equal_H": identical,
                "all_users_first_discovered_step": int(raw["sense_first_seen_step"].max())
                if np.all(raw["sense_first_seen_step"] >= 0) else None,
            })
    arms = {}
    for arm in ("L0", "L1", "H", "P", "A"):
        panel = [r for r in gates if r["arm"] == arm]
        arms[arm] = {
            "no_known_bs_at_any_plan": [r["seed"] for r in panel if not r["known_bs_plans"]],
            "no_eligible_plan": [r["seed"] for r in panel if not r["eligible_plans"]],
            "known_bs_but_no_eligible_plan": [r["seed"] for r in panel if r["known_bs_plans"] and not r["eligible_plans"]],
            "exact_path_equal_H": [r["seed"] for r in panel if r["exact_native_path_equal_H"]],
            "eligible_plans": sum(r["eligible_plans"] for r in panel),
            "eligible_service_requests": sum(r["eligible_service_requests"] for r in panel),
            "executed_scout_plans": sum(r["executed_scout_plans"] for r in panel),
        }
    eligible_train = [m for m in macro_rows if m["choice"]["eligible"]]
    train_activity = {
        "macros": len(macro_rows), "eligible_macros": len(eligible_train),
        "eligible_service_requests": sum(m["choice"]["requested"] == 0 for m in eligible_train),
        "eligible_scout_requests": sum(m["choice"]["requested"] > 0 for m in eligible_train),
        "worlds_with_eligible_macro": len({m["world_seed"] for m in eligible_train}),
        "eligible_action_histogram": {str(k): v for k, v in sorted(Counter(m["choice"]["requested"] for m in eligible_train).items())},
    }
    return {
        "source_sha": manifest["launch_sha"], "status": "verified",
        "manifest_sha256": digest(out / "manifest.json"),
        "artifacts_hashed": len(manifest["artifacts"]), "storage_bytes": manifest["storage_bytes"],
        "native_traces_checked": len(rows) + len(training_rows), "native_steps_checked": 720000,
        "training_activity": train_activity, "arms": arms, "perworld_activation": gates,
        "survey_scope": "BS known at macro decisions through t2970; this is not a first-BS-discovery experiment",
        "training_curve": [{"rollouts": [start + 1, start + 10],
                            "mean_native_J": float(np.mean([v for row in rollouts[start:start + 10] for v in row["native_J"]])),
                            "mean_qos": float(np.mean([v for row in rollouts[start:start + 10] for v in row["qos_per_step"]]))}
                           for start in range(0, 40, 10)],
        "first_update": updates[0], "last_update": updates[-1],
        "reading_wall_seconds": time.monotonic() - started,
    }


if __name__ == "__main__":
    print(json.dumps(inspect(Path(sys.argv[1])), sort_keys=True, allow_nan=False))
