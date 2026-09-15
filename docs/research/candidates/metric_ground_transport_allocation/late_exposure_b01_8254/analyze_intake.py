"""Data-only intake of the sole8254 native run; no environment/model construction."""
import csv
import json
import math
from pathlib import Path
import re
import statistics

import torch

from experiments.candidates.metric_ground_transport_allocation.mgtap_late_exposure_b01 import protocol as p

ROOT = Path("temp/directions/metric_ground_transport_allocation/exp/late_exposure_b01_8254_20260914")
OUT = Path(__file__).parent
SOURCE = "90f835e10357fbbf465cc5d500a93f1e2d4ab226"


def main():
    summary = json.loads((ROOT / "summary.json").read_text())
    rows = [json.loads(line) for line in (ROOT / "episodes.jsonl").read_text().splitlines()]
    rolls = [json.loads(line) for line in (ROOT / "rollouts.jsonl").read_text().splitlines()]
    assert summary["launch_sha"] == SOURCE and summary["master"] == p.MASTER
    assert summary["status"] == "COMPLETE" and not summary["limits"] and not summary["partial_fits"]
    assert len(rows) == 1152 and len(rolls) == 512 and len(summary["fits"]) == 2
    checkpoint_facts = []
    for arm in p.ARMS:
        train = [r for r in rows if r["arm"] == arm and r["phase"] == "train"]
        assert len(train) == 512 and [r["episode"] for r in train] == list(range(512))
        arm_rows = [r for r in rows if r["arm"] == arm]
        for row in arm_rows:
            assert row["object"] == p.OBJECT and row["pair_master"] == p.MASTER
            assert row["learning_rate"] == p.LEARNING_RATE and row["steps"] == 256 and math.isfinite(row["J"])
            assert all(row[k] == v for k, v in p.randomization(row["phase"], row["episode"]).items())
        arm_rolls = [r for r in rolls if r["arm"] == arm]
        assert [r["rollout"] for r in arm_rolls] == list(range(256))
        assert all(r["optimizer_steps"] == 4 and len(r["epochs"]) == 4 for r in arm_rolls)
        fit = next(f for f in summary["fits"] if f["arm"] == arm)
        assert fit["fit_complete"] and not fit["limits"]
        assert fit["counts"]["optimizer_steps"] == sum(r["optimizer_steps"] for r in arm_rolls) == 1024
        assert fit["counts"]["train_team_steps"] == 131072 and fit["counts"]["eval_team_steps"] == 16384
        for endpoint in fit["endpoints"]:
            ep = endpoint["train_endpoint"]
            assert math.isfinite(endpoint["exposure"]["total"]["displacement"])
            assert endpoint["exposure"]["total"]["displacement"] > 0
            checkpoint = torch.load(ROOT / endpoint["checkpoint"], weights_only=True, map_location="cpu")
            assert (checkpoint["object"], checkpoint["pair_master"], checkpoint["arm"], checkpoint["train_endpoint"]) == (p.OBJECT, p.MASTER, arm, ep)
            steps = sorted({int(v["step"].item()) for v in checkpoint["optimizer"]["state"].values()})
            assert steps == [ep * 2]
            assert all(g["lr"] == 1e-4 for g in checkpoint["optimizer"]["param_groups"])
            checkpoint_facts.append({"arm": arm, "endpoint": ep, "adam_step_values": steps,
                                     "total_displacement": endpoint["exposure"]["total"]["displacement"]})
    primary = p.primary(rows)
    assert primary == summary["primary"]
    log = (ROOT / "supervisor" / "task.log").read_text()
    wall = float(re.search(r"MGTAP_COMPLETE_COMMAND_WALL_SECONDS=([0-9.]+)", log).group(1))
    rss = int(re.search(r"MGTAP_COMPLETE_COMMAND_PEAK_RSS_KIB=(\d+)", log).group(1))
    exit_code = int(re.search(r"MGTAP_COMPLETE_COMMAND_EXIT=(\d+)", log).group(1))
    assert exit_code == 0
    panels = {}
    for endpoint, panel in primary["panels"].items():
        d = panel["COND_minus_DENSE"]["differences"]
        panels[endpoint] = {"mean_J_by_arm": {a: statistics.mean(panel["J"][a]) for a in p.ARMS},
                            "delta_J": statistics.mean(d), "conditional_world_se": statistics.stdev(d) / math.sqrt(32),
                            "positive_worlds": sum(x > 0 for x in d), "negative_worlds": sum(x < 0 for x in d),
                            "zero_worlds": sum(x == 0 for x in d), "reading": panel["reading"]}
    result = {"object": p.OBJECT, "source_sha": SOURCE, "master": p.MASTER, "primary": primary,
              "panel_summary": panels, "checkpoint_facts": checkpoint_facts,
              "independent_training_pairs": 1, "training_run_sd": None,
              "raw_episode_rows": len(rows), "raw_rollout_rows": len(rolls),
              "actual_team_ticks": sum(r["steps"] for r in rows), "actual_adam_calls": sum(r["optimizer_steps"] for r in rolls),
              "whole_command_wall_seconds": wall, "peak_rss_kib": rss, "exit_code": exit_code,
              "fit_body_seconds": {f["arm"]: f["fit_body_wall"] for f in summary["fits"]},
              "cost_limit": "full support/provider/engineering/lifetime/aggregate CPU UNKNOWN; body scopes are nested",
              "checks": "all raw rows/addresses/counts, both endpoint reductions, actual checkpoint Adam step continuity and displacement; no new learner/environment exposure"}
    (OUT / "ANALYSIS.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    (OUT / "RUN_SUMMARY.json").write_bytes((ROOT / "summary.json").read_bytes())
    with (OUT / "PAIRED_SCORES.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["endpoint", "episode", "COND_J", "DENSE_J", "COND_minus_DENSE"])
        for endpoint, panel in primary["panels"].items():
            for e, d in enumerate(panel["COND_minus_DENSE"]["differences"]):
                w.writerow([endpoint, e, panel["J"]["COND"][e], panel["J"]["DENSE"][e], d])
    with (OUT / "FINAL_RUN_SCORES.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "seed", "arm", "score"])
        for arm, score in panels["512"]["mean_J_by_arm"].items():
            w.writerow([p.OBJECT, p.MASTER, arm, score])
    print(json.dumps({k: v for k, v in result.items() if k != "primary"}, indent=2))


if __name__ == "__main__":
    main()
