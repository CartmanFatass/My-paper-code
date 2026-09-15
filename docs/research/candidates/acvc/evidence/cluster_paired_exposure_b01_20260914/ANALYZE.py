"""Verify recorded paired-exposure B01 bytes; never load a model or run an environment."""
import hashlib
import json
import math
from pathlib import Path
import statistics

import numpy as np


ROOT = Path(__file__).resolve().parent
MASTER, EVALUATION, HORIZON = 22591, 32591, 256
STAGES, ARMS = (512, 1024), ("C", "F", "dwell")
summary = json.loads((ROOT / "summary.json").read_text(encoding="utf-8"))
execution = json.loads((ROOT / "EXECUTION_FACTS.json").read_text(encoding="utf-8"))
rows = [json.loads(line) for line in (ROOT / "episodes.jsonl").read_text().splitlines()]
updates = [json.loads(line) for line in (ROOT / "updates.jsonl").read_text().splitlines()]
expected = dict(environment_constructors=7, explicit_resets=1408, train_episodes=1024,
                eval_episodes=384, rollouts=512, optimizer_steps=2048, backward_calls=2048,
                update_records=2048, train_team_steps=262144, eval_team_steps=98304,
                team_steps=360448, fresh_dense_initializations=1, post_fit_loads=6,
                fixed_snapshots=2, midpoint_snapshots=1, final_checkpoints=1, new_fits=1,
                gate_constructions=0, duration_heads=0, selector_updates=0, evaluation_updates=0)
assert summary["status"] == "complete" and summary["primary"]["complete"]
assert summary["object"] == "ACVC_CLUSTER_PAIRED_EXPOSURE_B01"
assert summary["launch_sha"] == execution["launch_sha"]
assert summary["master"] == MASTER and summary["evaluation_namespace"] == EVALUATION
assert summary["scientific_invocations"] == 1
assert summary["fit_complete"] and summary["checkpoint_complete"]
for key, value in expected.items():
    assert summary["counts"][key] == value, (key, summary["counts"][key], value)
configuration = dict(horizon=256, training_episodes=1024, episodes_per_rollout=2,
                     ppo_epochs_per_rollout=4, chunk=32, checkpoint_episodes=[512, 1024],
                     evaluation_episodes_per_arm=64, user_distribution="cluster",
                     training_rule="C", device="cpu", dtype="float32", intraop_threads=1,
                     interop_threads=1, checkpoint_factor_in_evaluation_rng=False)
for key, value in configuration.items():
    assert summary["configuration"][key] == value, key
assert summary["configuration"]["evaluation_order"] == [[stage, arm] for stage in STAGES for arm in ARMS]
assert [(item["checkpoint_episode"], item["completed_rollout_index"],
         item["optimizer_steps"], item["update_records"]) for item in summary["checkpoints"]] == [
             (512, 255, 1024, 1024), (1024, 511, 2048, 2048)]
assert len(rows) == 1408 and len(updates) == 2048
assert [row["phase"] for row in rows] == ["train"] * 1024 + ["eval"] * 384
assert [row["episode"] for row in rows[:1024]] == list(range(1024))
for row in rows[:1024]:
    assert row["base"] == row["master"] == MASTER
    assert row["reset_seed"] == MASTER * 100000 + 1000 + row["episode"]
    assert row["steps"] == HORIZON and math.isfinite(row["S"]) and row["J"] == row["S"] / HORIZON
assert [(row["master"], row["rollout"], row["epoch"], row["episodes"]) for row in updates] == [
    (MASTER, rollout, epoch, [2 * rollout, 2 * rollout + 1])
    for rollout in range(512) for epoch in range(4)]
for row in updates:
    assert all(math.isfinite(value) for value in row.values() if isinstance(value, float))
assert [(row["checkpoint_episode"], row["arm"], row["episode"]) for row in rows[1024:]] == [
    (stage, arm, episode) for stage in STAGES for arm in ARMS for episode in range(64)]
assert [(panel["checkpoint_episode"], panel["arm"], panel["episodes"]) for panel in summary["panels"]] == [
    (stage, arm, 64) for stage in STAGES for arm in ARMS]


def check_stats(values, original, change=False, descriptive=False):
    values = np.asarray(values, dtype=np.float64)
    assert len(values) == 64 and np.isfinite(values).all()
    mean, sd = float(values.mean()), float(values.std(ddof=1))
    reading = ("INCREASE" if mean > .01 else "DECREASE" if mean < -.01 else "WITHIN") if change else (
        "UP" if mean > .01 else "DOWN" if mean < -.01 else "WITHIN")
    if descriptive:
        reading = "DESCRIPTIVE"
    result = dict(mean_J=mean, sample_SD_J=sd, conditional_SE_J=sd / 8,
                  minimum_J=float(values.min()), maximum_J=float(values.max()),
                  negative=int((values < 0).sum()), positive=int((values > 0).sum()),
                  zero=int((values == 0).sum()), reading=reading)
    vector_key = "paired_difference_of_differences_J" if change else "paired_differences_J"
    assert original["complete"] and values.tolist() == original[vector_key]
    for key, value in result.items():
        assert math.isclose(value, original[key], abs_tol=1e-14, rel_tol=0) if isinstance(value, float) else value == original[key], key
    assert math.isclose(statistics.mean(values.tolist()), mean, abs_tol=1e-14, rel_tol=0)
    assert math.isclose(statistics.stdev(values.tolist()), sd, abs_tol=1e-14, rel_tol=0)
    return dict(result, **{vector_key: values.tolist()})


values, endpoints = {}, {}
for stage in STAGES:
    native = summary["primary"]["endpoints"][str(stage)]
    values[stage], endpoints[str(stage)] = {}, {"arms": {}, "contrasts": {}}
    for arm in ARMS:
        arm_rows = [row for row in rows[1024:] if row["checkpoint_episode"] == stage and row["arm"] == arm]
        assert [row["episode"] for row in arm_rows] == list(range(64))
        for row in arm_rows:
            assert row["base"] == MASTER and row["evaluation_namespace"] == EVALUATION
            assert row["reset_seed"] == EVALUATION * 100000 + 2000 + row["episode"]
            assert row["steps"] == HORIZON and math.isfinite(row["S"]) and row["J"] == row["S"] / HORIZON
        vector = np.asarray([row["J"] for row in arm_rows], dtype=np.float64)
        values[stage][arm] = vector
        assert vector.tolist() == native["arms"][arm]["values_J"]
        assert [row["S"] for row in arm_rows] == native["arms"][arm]["values_S"]
        assert math.isclose(float(vector.mean()), native["arms"][arm]["mean_J"], abs_tol=1e-14, rel_tol=0)
        endpoints[str(stage)]["arms"][arm] = native["arms"][arm]
    for first, second in (("F", "C"), ("F", "dwell"), ("dwell", "C")):
        name = first + "-" + second
        diff = values[stage][first] - values[stage][second]
        endpoints[str(stage)]["contrasts"][name] = check_stats(diff, native["contrasts"][name], descriptive=name == "dwell-C")
    for model in ("common_actor", "critic"):
        assert summary["checkpoint_exposures"][str(stage)][model]["displacement"] > 0
changes = {}
for name, comparator in (("G_dwell", "dwell"), ("G_C", "C")):
    early = values[512]["F"] - values[512][comparator]
    late = values[1024]["F"] - values[1024][comparator]
    result = check_stats(late - early, summary["primary"]["changes"][name], change=True)
    covariance = float(np.cov(early, late, ddof=1)[0, 1])
    variance_from_covariance = float(early.var(ddof=1) + late.var(ddof=1) - 2 * covariance)
    assert math.isclose(variance_from_covariance, result["sample_SD_J"] ** 2, abs_tol=1e-14, rel_tol=0)
    changes[name] = dict(result, endpoint_sample_covariance_J2=covariance,
                         variance_from_paired_covariance_J2=variance_from_covariance)
time_fields = dict(line.split("=", 1) for line in (ROOT / "native_time.txt").read_text().splitlines())
assert time_fields["exit_code"] == "0"
forecasts = {"F-C": dict(UP=.70, WITHIN=.20, DOWN=.10),
             "F-dwell": dict(UP=.60, WITHIN=.25, DOWN=.15),
             "G_dwell": dict(INCREASE=.25, WITHIN=.35, DECREASE=.40)}
scores = {}
for stage in STAGES:
    for name in ("F-C", "F-dwell"):
        observed = endpoints[str(stage)]["contrasts"][name]["reading"]
        scores[f"{stage}:{name}"] = dict(observed=observed, brier=sum((p - int(key == observed)) ** 2 for key, p in forecasts[name].items()))
observed = changes["G_dwell"]["reading"]
scores["G_dwell"] = dict(observed=observed, brier=sum((p - int(key == observed)) ** 2 for key, p in forecasts["G_dwell"].items()))
payload = dict(accepted=True, evidence_class="B/EXPLORE", independent_training_units=1,
               correlated_snapshots=[512, 1024], conditional_worlds=64,
               verification="All1408 episode rows/2048 ordered updates, fixed stage order and exposures, identity/reset/counts/configuration; all original endpoint/change vectors and float64 reductions checked with independent stdlib mean/SD at absolute1e-14. No model loading or new scientific exposure.",
               expected_counts=expected, endpoints=endpoints, changes=changes,
               checkpoint_exposures=summary["checkpoint_exposures"],
               intervention_by_checkpoint_rule=summary["intervention_by_checkpoint_rule"],
               native_wall_s=float(time_fields["native_wall_s"]), peak_rss_kib=int(time_fields["peak_rss_kib"]),
               forecasts=forecasts, scores=scores, completion_brier=(1-.95)**2,
               owner_prediction="not taken (unattended)",
               hashes={path.name: dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                       for path in ROOT.iterdir() if path.name in ("summary.json", "episodes.jsonl", "updates.jsonl", "admission.json", "native_time.txt", "stdout.log", "stderr.log")})
(ROOT / "INTAKE_ANALYSIS.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(dict(accepted=True, scores=scores, native_wall_s=payload["native_wall_s"],
                     endpoints={stage: {name: {key: value for key, value in contrast.items() if not isinstance(value, list)}
                                for name, contrast in endpoint["contrasts"].items()} for stage, endpoint in endpoints.items()},
                     changes={name: {key: value for key, value in change.items() if not isinstance(value, list)}
                              for name, change in changes.items()}), indent=2))
