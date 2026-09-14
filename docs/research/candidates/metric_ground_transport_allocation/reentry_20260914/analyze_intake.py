"""Read the fixed completed programme; no Torch, models, fitting or new estimand."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import zipfile

from experiments.candidates.metric_ground_transport_allocation.mgtap_lr_selection_b01 import protocol


SOURCE = "2d351d48604396ce478aa900584bd24b3255def5"


def digest(body):
    return hashlib.sha256(body).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def analyze(root, out):
    expected_hashes = json.loads((out / "REMOTE_HASHES.json").read_text())
    assert expected_hashes["launch_sha"] == SOURCE
    members = {name: (root / name).read_bytes() for name in expected_hashes["sha256"]}
    assert all(digest(body) == expected_hashes["sha256"][name]
               for name, body in members.items()), "remote/native byte mismatch"
    summary = json.loads(members["summary.json"])
    rows = [json.loads(line) for line in members["episodes.jsonl"].splitlines()]
    rollouts = [json.loads(line) for line in members["rollouts.jsonl"].splitlines()]
    saved_selection = json.loads(members["selection.json"])
    assert summary["launch_sha"] == SOURCE and summary["status"] == "COMPLETE"
    assert members["supervisor/exit_code"].strip() == b"0"
    assert members["supervisor/status"].strip() == b"finished"
    assert summary["limits"] == [] and summary["completed_fit_count"] == 8
    selected = protocol.select_learning_rates(
        [row for row in rows if row["stage"] == "selection" and row["phase"] == "eval"])
    assert selected == summary["selection"]
    assert all(saved_selection[key] == value for key, value in selected.items())
    selection_hash = digest(members["selection.json"])
    assert members["selection.sha256"].decode().split()[0] == selection_hash
    assert summary["selection_sha256"] == selection_hash
    primary = protocol.holdout_primary(
        [row for row in rows if row["stage"] == "holdout" and row["phase"] == "eval"], selected)
    assert primary == summary["primary"], "published primary differs from raw panels"
    expected_order = [("selection", key, arm) for key in protocol.LEARNING_RATES for arm in protocol.ARMS]
    expected_order += [("holdout", selected["selected_lr_key"][arm], arm) for arm in protocol.ARMS]
    assert [(fit["stage"], fit["lr_key"], fit["arm"]) for fit in summary["fits"]] == expected_order
    assert [(fit["lr_key"], fit["arm"]) for fit in saved_selection["candidate_fits"]] == [
        (rate, arm) for _, rate, arm in expected_order[:6]]
    for candidate in saved_selection["candidate_fits"]:
        arm, rate = candidate["arm"], candidate["lr_key"]
        assert candidate["learning_rate"] == protocol.LEARNING_RATES[rate]
        assert candidate["validation_mean_J"] == selected["validation_mean_J"][arm][rate]
        assert candidate["checkpoint"] == f"selection_{rate}_{arm}.pt"
    expected_counts = {"train_episodes": 256, "eval_episodes": 32,
                       "train_team_steps": 65536, "eval_team_steps": 8192,
                       "team_steps": 73728, "optimizer_steps": 512, "rollouts": 128}
    fit_facts = []
    for stage, rate, arm in expected_order:
        fit = next(item for item in summary["fits"]
                   if (item["stage"], item["lr_key"], item["arm"]) == (stage, rate, arm))
        master = protocol.SELECTION_MASTER if stage == "selection" else protocol.HOLDOUT_MASTER
        assert fit["pair_master"] == master and fit["learning_rate"] == protocol.LEARNING_RATES[rate]
        assert fit["fit_complete"] and fit["panel_complete"] and fit["limits"] == []
        assert all(fit["counts"][key] == value for key, value in expected_counts.items())
        assert fit["training_counts"]["optimizer_steps"] == 512
        assert fit["training_counts"]["eval_episodes"] == 0
        fit_rows = [row for row in rows if (row["stage"], row["lr_key"], row["arm"]) == (stage, rate, arm)]
        assert len(fit_rows) == 288
        assert [(row["phase"], row["episode"]) for row in fit_rows] == [
            (phase, episode) for phase, size in (("train", 256), ("eval", 32)) for episode in range(size)]
        for row in fit_rows:
            assert row["object"] == protocol.OBJECT
            assert row["pair_master"] == master and row["learning_rate"] == protocol.LEARNING_RATES[rate]
            assert row["steps"] == 256 and math.isfinite(row["J"])
            assert math.isclose(row["J"], row["reward_sum"] / 256, rel_tol=1e-12, abs_tol=1e-12)
            assert all(row[key] == value for key, value in protocol.randomization(master, row["phase"], row["episode"]).items())
        fit_rollouts = [row for row in rollouts if (row["stage"], row["lr_key"], row["arm"]) == (stage, rate, arm)]
        assert [row["rollout"] for row in fit_rollouts] == list(range(128))
        assert all(row["pair_master"] == master and row["learning_rate"] == protocol.LEARNING_RATES[rate]
                   and row["episodes"] == 2 and row["steps"] == 512
                   and row["optimizer_steps"] == 4 and len(row["epochs"]) == 4 for row in fit_rollouts)
        assert all([epoch["epoch"] for epoch in row["epochs"]] == list(range(4)) for row in fit_rollouts)
        movement = {key: fit["exposure"][key]["displacement"]
                    for key in ("common_actor", "critic", "branch_inner", "branch_projection")}
        assert all(math.isfinite(value) and value > 0 for value in movement.values())
        assert fit["checkpoint"] in members and len(members[fit["checkpoint"]]) > 0
        fit_facts.append({"stage": stage, "pair_master": master, "lr_key": rate, "arm": arm,
                          "mean_eval_J": statistics.mean(row["J"] for row in fit_rows if row["phase"] == "eval"),
                          "counts": fit["counts"], "displacement": movement,
                          "fit_body_wall": fit["fit_body_wall"], "checkpoint": fit["checkpoint"]})
    assert len(rows) == summary["raw_episode_rows"] == 2304
    assert len(rollouts) == summary["raw_rollout_rows"] == 1024
    differences = primary["ordered_COND_minus_DENSE"]
    outer_log = members["supervisor/task.log"].decode("utf-8")
    outer = {key: float(re.search(r"^MGTAP_COMPLETE_COMMAND_" + key + r"=([0-9.]+)$", outer_log, re.M).group(1))
             for key in ("WALL_SECONDS", "PEAK_RSS_KIB", "EXIT")}
    assert outer["EXIT"] == 0
    counts = {"fits": len(fit_facts), "train_episodes": sum(row["phase"] == "train" for row in rows),
              "evaluation_episodes": sum(row["phase"] == "eval" for row in rows),
              "team_ticks": sum(row["steps"] for row in rows),
              "adam_calls": sum(row["optimizer_steps"] for row in rollouts), "rollouts": len(rollouts)}
    counts["actor_row_uses_collection_evaluation_replay"] = 5 * (
        counts["team_ticks"] + sum(row["steps"] * len(row["epochs"]) for row in rollouts))
    assert counts["team_ticks"] == 589824 and counts["adam_calls"] == 4096
    assert counts["actor_row_uses_collection_evaluation_replay"] == 13434880
    analysis = {"object": protocol.OBJECT, "launch_sha": SOURCE, "checks": "PASS",
                "raw_hash_match": True, "selection_and_primary_recompute_exact_match": True,
                "selection": selected, "primary": primary, "actual_counts": counts,
                "positive_final_worlds": sum(value > 0 for value in differences),
                "negative_final_worlds": sum(value < 0 for value in differences),
                "zero_final_worlds": sum(value == 0 for value in differences), "fits": fit_facts,
                "complete_command": outer, "peak_rss_mib": outer["PEAK_RSS_KIB"] / 1024,
                "sum_fit_body_wall": sum(fit["fit_body_wall"] for fit in fit_facts),
                "study_body_wall_before_summary": summary["study_body_wall_before_summary"],
                "uncertainty_limit": "one selection master and one final training pair; paired-world SE is conditional, not training/selection-population SE",
                "new_fits_evaluations_checkpoint_loads_or_native_calls_by_analysis": 0}
    write_json(out / "INTAKE_ANALYSIS.json", analysis)
    (out / "RUN_SUMMARY.json").write_bytes(members["summary.json"])
    with (out / "PAIRED_FINAL_SCORES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(("episode", "reset_seed", "COND_J", "DENSE_J", "COND_minus_DENSE"))
        for episode, difference in enumerate(differences):
            writer.writerow((episode, protocol.randomization(8252, "eval", episode)["reset_seed"],
                             primary["J_by_arm"]["COND"][episode], primary["J_by_arm"]["DENSE"][episode], difference))
    with (out / "FINAL_RUN_SCORES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(("task", "seed", "arm", "score"))
        for arm in protocol.ARMS:
            writer.writerow((protocol.OBJECT, 8252, arm, primary["mean_J_by_arm"][arm]))
    archive_path = out / "NATIVE_EVIDENCE.zip"
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, body in members.items():
            archive.writestr(name, body)
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == set(members)
        assert all(digest(archive.read(name)) == digest(body) for name, body in members.items())
    write_json(out / "COLLECTION.json", {
        "launch_sha": SOURCE, "archive": {"bytes": archive_path.stat().st_size,
                                           "sha256": digest(archive_path.read_bytes())},
        "files": {name: {"bytes": len(body), "sha256": digest(body)} for name, body in members.items()},
        "native_remote_hash_match": True, "member_readback_hash_match": True,
        "checkpoint_count": 8, "local_source_root": str(root.resolve()),
        "no_source_or_evidence_removed": True})
    print(json.dumps({"checks": "PASS", "counts": counts, "selected_lr": selected["selected_learning_rate"],
                      "delta_J": primary["delta_J"], "conditional_panel_se": primary["conditional_panel_se"],
                      "positive_worlds": analysis["positive_final_worlds"], "negative_worlds": analysis["negative_final_worlds"],
                      "outer": outer, "archive_bytes": archive_path.stat().st_size}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.root, args.out)
