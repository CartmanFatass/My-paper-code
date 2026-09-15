"""Recorded-byte B03 intake; no model execution or new scientific exposure."""
import hashlib
import json
import math
from pathlib import Path
import statistics

root = Path(__file__).resolve().parent
summary = json.loads((root / "summary.json").read_text())
rows = [json.loads(x) for x in (root / "episodes.jsonl").read_text().splitlines()]
updates = [json.loads(x) for x in (root / "updates.jsonl").read_text().splitlines()]
expected = dict(environment_constructors=4, explicit_resets=704, train_episodes=512,
                eval_episodes=192, rollouts=256, optimizer_steps=1024, backward_calls=1024,
                update_records=1024, train_team_steps=131072, eval_team_steps=49152,
                team_steps=180224, fresh_dense_initializations=1, post_fit_loads=3,
                final_checkpoints=1, new_fits=1, gate_constructions=0, duration_heads=0,
                selector_updates=0, evaluation_updates=0)
assert summary["status"] == "complete" and summary["primary"]["complete"]
assert summary["object"] == "ACVC_CLUSTER_DEPLOYMENT_B03"
assert summary["launch_sha"] == "091c6725b149cd2dfa9665408cabee17b8f958e3"
assert summary["master"] == 21937 and summary["evaluation_namespace"] == 31937
assert summary["scientific_invocations"] == 1
for key, value in expected.items():
    assert summary["counts"][key] == value, (key, summary["counts"][key], value)
for key, value in dict(user_distribution="cluster", training_rule="C", device="cpu",
                       dtype="float32", intraop_threads=1, interop_threads=1).items():
    assert summary["configuration"][key] == value, key
assert summary["configuration"]["evaluation_order"] == ["C", "F", "dwell"]
assert len(rows) == 704 and len(updates) == 1024
train = [r for r in rows if r["phase"] == "train"]
assert [r["episode"] for r in train] == list(range(512))
for row in train:
    assert row["base"] == row["master"] == 21937
    assert row["reset_seed"] == 21937 * 100000 + 1000 + row["episode"]
    assert row["steps"] == 256 and math.isfinite(row["S"]) and row["J"] == row["S"] / 256
assert [(r["master"], r["rollout"], r["epoch"]) for r in updates] == [
    (21937, rollout, epoch) for rollout in range(256) for epoch in range(4)]
for row in updates:
    assert all(math.isfinite(v) for v in row.values() if isinstance(v, float))
values = {}
for arm in ("C", "F", "dwell"):
    arm_rows = [r for r in rows if r["phase"] == "eval" and r["arm"] == arm]
    assert [r["episode"] for r in arm_rows] == list(range(64))
    for r in arm_rows:
        assert r["base"] == 21937 and r["evaluation_namespace"] == 31937
        assert r["reset_seed"] == 31937 * 100000 + 2000 + r["episode"]
        assert r["steps"] == 256 and math.isfinite(r["S"]) and r["J"] == r["S"] / 256
    values[arm] = [r["J"] for r in arm_rows]
    assert math.isclose(statistics.mean(values[arm]), summary["primary"]["arm_mean_J"][arm], abs_tol=1e-14, rel_tol=0)
contrasts = {}
for a, b in (("F", "C"), ("F", "dwell"), ("dwell", "C")):
    name = a + "-" + b
    diff = [x - y for x, y in zip(values[a], values[b])]
    mean, sd = statistics.mean(diff), statistics.stdev(diff)
    result = dict(mean_J=mean, sample_SD_J=sd, conditional_SE_J=sd / 8,
                  minimum_J=min(diff), maximum_J=max(diff), adverse=sum(v < 0 for v in diff),
                  favorable=sum(v > 0 for v in diff), zero=sum(v == 0 for v in diff),
                  reading="UP" if mean > .01 else "DOWN" if mean < -.01 else "WITHIN")
    original = summary["primary"]["contrasts"][name]
    assert diff == original["paired_differences_J"]
    for key, value in result.items():
        assert math.isclose(value, original[key], abs_tol=1e-14, rel_tol=0) if isinstance(value, float) else value == original[key]
    contrasts[name] = result
for model in ("common_actor", "critic"):
    assert summary["exposure"][model]["displacement"] > 0
time_fields = dict(line.split("=", 1) for line in (root / "native_time.txt").read_text().splitlines())
assert time_fields["exit_code"] == "0"
forecasts = {"F-C": dict(UP=.65, WITHIN=.20, DOWN=.15),
             "F-dwell": dict(UP=.55, WITHIN=.25, DOWN=.20)}
scoring = {name: dict(observed=contrasts[name]["reading"],
                     brier=sum((p - int(key == contrasts[name]["reading"])) ** 2 for key, p in forecast.items()))
           for name, forecast in forecasts.items()}
payload = dict(accepted=True, evidence_class="B/EXPLORE", independent_training_units=1,
               verification="All704 episode rows/1024 ordered updates, identity, reset, counts, configuration, finite values and all primary reductions; stdlib mean/SD match original float64 at absolute1e-14. No new scientific exposure.",
               expected_counts=expected, arm_means=summary["primary"]["arms"], contrasts=contrasts,
               exposure=summary["exposure"], intervention_by_rule=summary["intervention_by_rule"],
               native_wall_s=float(time_fields["native_wall_s"]), peak_rss_kib=int(time_fields["peak_rss_kib"]),
               forecasts=forecasts, scores=scoring, completion_brier=(1-.95)**2,
               owner_prediction="not taken (unattended)",
               hashes={p.name: dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                       for p in root.iterdir() if p.name in ("summary.json", "episodes.jsonl", "updates.jsonl", "admission.json", "native_time.txt", "stdout.log", "stderr.log")})
(root / "INTAKE_ANALYSIS.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
print(json.dumps({key: payload[key] for key in ("accepted", "contrasts", "native_wall_s", "peak_rss_kib", "scores")}, indent=2))
