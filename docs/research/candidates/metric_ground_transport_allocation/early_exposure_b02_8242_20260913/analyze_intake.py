"""Read retained native bytes only: no model loading, RNG, environment or learner."""
import ast
import csv
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
import statistics
import zipfile

ROOT = Path(__file__).resolve().parents[5]
RAW = ROOT / "temp/directions/metric_ground_transport_allocation/exp/early_exposure_b02_8242_20260913"
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
EXPECTED = json.loads((OUT / "EXPECTED_REMOTE_HASHES.json").read_text())

def digest(path):
    return {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")

for name, expected in EXPECTED.items():
    assert digest(RAW / name)["sha256"] == expected, name
s = json.loads((RAW / "summary.json").read_text())
rows = [json.loads(line) for line in (RAW / "episodes.jsonl").read_text().splitlines()]
rollouts = [json.loads(line) for line in (RAW / "rollouts.jsonl").read_text().splitlines()]
assert rows == s["rows"]
assert s["launch_sha"] == "8744085c293288e2c178fbc6d2a97ae9ca053c43"
assert s["source_sha"] == "0d161633e3bb6884b56ef57a0200060b659c56a8"
assert s["seed"] == 8242 and s["status"] == "COMPLETE"
assert s["pair_factory_calls"] == 1 and s["top_level_model_constructions"] == 6
assert not s["limits"] and not s["binding_errors"] and not s["cap_breach"]
assert len(rows) == 576 and len(rollouts) == 256
base = 824200000
for arm, train in (("COND", 256), ("DENSE", 256)):
    info = s["arms"][arm]
    assert info["fit_complete"] and info["complete"]
    expected_counts = dict(train_episodes=train, eval_episodes=32,
                           train_team_steps=train*256, eval_team_steps=8192,
                           team_steps=(train+32)*256, rollouts=train//2,
                           optimizer_steps=train*2, diagnostic_frames=0, duration_decisions=0)
    assert all(info["counts"][k] == v for k, v in expected_counts.items())
    assert all(group["displacement"] > 0 for group in info["exposure"].values())
    for phase, count, reset, duration in (("train", train, 1000, 4000), ("eval", 32, 2000, 5000)):
        panel = [r for r in rows if r["arm"] == arm and r["phase"] == phase]
        assert [r["episode"] for r in panel] == list(range(count))
        for r in panel:
            e = r["episode"]
            assert r["pair_master"] == 8242 and r["steps"] == 256
            assert r["reset_seed"] == base+reset+e
            assert r["duration_seed"] == base+duration+e
            assert r["velocity_seed"] == base+(21 if phase == "train" else 3000+e)
            assert math.isfinite(r["J"]) and r["J"] == r["reward_sum"]/256
    updates = [r for r in rollouts if r["arm"] == arm]
    assert [r["rollout"] for r in updates] == list(range(train//2))
    for r in updates:
        assert r["pair_master"] == 8242 and r["episodes"] == 2 and r["steps"] == 512
        assert r["optimizer_steps"] == 4 and [e["epoch"] for e in r["epochs"]] == [0,1,2,3]
        assert all(math.isfinite(v) for e in r["epochs"] for v in e.values())
    with zipfile.ZipFile(RAW / f"final_{arm}.pt") as z:
        assert z.testzip() is None

for k, expected in {"team_steps":147456, "optimizer_steps":1024,
                    "train_episodes":512, "eval_episodes":64, "rollouts":256,
                    "partial_episode_steps":0, "diagnostic_frames":0, "duration_decisions":0}.items():
    assert s["counts"][k] == expected
reducer_path = ROOT / "experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/conditional_pooling.py"
tree = ast.parse(reducer_path.read_text())
pure = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("reading", "primary")], type_ignores=[])
ns = {"math":math, "statistics":statistics, "COND":"COND", "DENSE":"DENSE"}
exec(compile(pure, str(reducer_path), "exec"), ns)
p = ns["primary"](rows)
assert p == s["primary"]
delta = p["COND_minus_DENSE"]["differences"]
means = {arm:statistics.mean(scores) for arm,scores in p["J"].items()}
log = (RAW / "supervisor/task.log").read_text()
def one_metric(name):
    values = re.findall(r"^" + name + r"=([0-9.]+)$", log, re.MULTILINE)
    assert len(values) == 1, (name, values)
    return float(values[0])
outer_wall = one_metric("MGTAP_NATIVE_WALL_SECONDS")
peak_rss = int(one_metric("MGTAP_NATIVE_PEAK_RSS_KIB"))
assert one_metric("MGTAP_NATIVE_EXIT") == 0
assert (RAW / "supervisor/exit_code").read_text().strip() == "0"
assert (RAW / "supervisor/status").read_text().strip() == "finished"
admission = json.loads((RAW / "admission.json").read_text())
assert admission["passed"] and admission["physical_floor_pass"] and admission["effective_floor_pass"]
assert min(admission["available_physical_bytes"], admission["effective_available_bytes"]) >= 4294967296
assert s["configuration"]["dtype"] == "float32" and s["configuration"]["device"] == "cpu"
assert s["configuration"]["threads"] == 1
cond_wall = s["arms"]["COND"]["elapsed_wall"]
dense_wall = outer_wall-cond_wall
# Operational elapsed-plan reporting is separate from primary completeness.
assert s["configuration"]["arm_cap"] == 1800 and s["configuration"]["pair_cap"] == 3600
watchdog_elapsed_within_plan = cond_wall <= 1800 and dense_wall <= 1800 and outer_wall <= 3600
analysis = {
    "unit":"one independently trained matched pair; 32 worlds conditional on that pair",
    "launch_sha":s["launch_sha"], "provenance_source_sha":s["source_sha"],
    "checks":{"all_native_hashes_match_remote":True, "all_episode_rows_equal_summary":True,
              "master_rng_reset_and_endpoint_binding":True, "all_rollouts_and_optimizer_counts":True,
              "nonzero_all_recorded_parameter_groups":True, "checkpoint_zip_crc":True,
              "accepted_pure_reducer_equals_closed_primary":True, "operational_elapsed_within_current_plan":watchdog_elapsed_within_plan},
    "episode_rows":len(rows), "rollout_rows":len(rollouts), "counts":s["counts"],
    "mean_J":means, "primary":p, "conditional_sd":statistics.stdev(delta),
    "positive_worlds":sum(d>0 for d in delta), "adverse_worlds":sum(d<0 for d in delta),
    "zero_worlds":sum(d==0 for d in delta), "min_delta":min(delta), "max_delta":max(delta),
    "native_cost_seconds":{"COND":cond_wall, "DENSE_including_outer_tail":dense_wall,
                           "pair":outer_wall, "python_last_clock":s["pair_elapsed_wall"],
                           "outer_tail_charged_to_DENSE":outer_wall-s["pair_elapsed_wall"],
                           "cpu_user":None, "cpu_system":None, "cpu_sum":None},
    "peak_rss_kib":peak_rss,
    "support_seconds":None, "complete_cost_seconds":None,
    "original_support_plan_seconds":2700, "original_complete_plan_seconds":3600,
    "support_complete_compliance":"UNKNOWN: unmeasured tails remain; original DM plans are not owner hard limits",
    "original_native_plan_seconds":{"per_arm":450,"pair":900},
    "prospective_operational_watchdog_seconds":{"per_arm":1800,"pair":3600},
    "new_scientific_execution_for_intake":False,
}
save("INTAKE_ANALYSIS.json", analysis)
save("RUN_SUMMARY.json", {k:v for k,v in s.items() if k != "rows"})
with (OUT / "PAIRED_FINAL_SCORES.csv").open("w", newline="", encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["master","episode","reset_seed","COND_J","DENSE_J","COND_minus_DENSE"])
    w.writerows([8242,e,base+2000+e,p["J"]["COND"][e],p["J"]["DENSE"][e],delta[e]] for e in range(32))
with (OUT / "RUN_SCORES.csv").open("w", newline="", encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["task","seed","arm","score"])
    w.writerows([s["object"],8242,arm,value] for arm,value in means.items())
spec=importlib.util.spec_from_file_location("run_summary", ROOT / ".agents/skills/hmasd-scientific-tools/scripts/summarize_runs.py")
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
save("RUN_LEVEL_DESCRIPTIVE.json", mod.summarize(OUT / "RUN_SCORES.csv", "DENSE", paired=True))
# Predeclared outcome-informed description of two independent training instances.
prior_path = ROOT / "docs/research/candidates/metric_ground_transport_allocation/early_exposure_b01_8241_20260913/RUN_SCORES.csv"
with prior_path.open(newline="", encoding="utf-8") as f:
    prior_rows = list(csv.DictReader(f))
assert len(prior_rows) == 2 and {r["seed"] for r in prior_rows} == {"8241"}
with (OUT / "TWO_TRAINING_INSTANCES.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["task","seed","arm","score"])
    w.writerows(["meanCOND256_DENSE256",8241,r["arm"],r["score"]] for r in prior_rows)
    w.writerows(["meanCOND256_DENSE256",8242,arm,value] for arm,value in means.items())
save("TWO_TRAINING_INSTANCES_DESCRIPTIVE.json",
     mod.summarize(OUT / "TWO_TRAINING_INSTANCES.csv", "DENSE", paired=True))


members = [RAW / name for name in EXPECTED] + [Path(__file__)]
def member_name(path):
    return "analyze_intake.py" if path == Path(__file__) else path.relative_to(RAW).as_posix()
archive=OUT / "NATIVE_EVIDENCE.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for path in members:
        z.write(path, member_name(path))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for path in members:
        assert hashlib.sha256(z.read(member_name(path))).hexdigest() == digest(path)["sha256"]
save("COLLECTION.json", {"archive":digest(archive), "files":{member_name(p):digest(p) for p in members},
                         "native_remote_hash_match":True, "member_readback_hash_match":True,
                         "remote_output":"/home/wu/hmasd-worktrees/mgtap-early-8242-20260913/temp/directions/metric_ground_transport_allocation/exp/early_exposure_b02_8242_20260913",
                         "no_source_or_evidence_removed":True})
print(json.dumps({k:v for k,v in analysis.items() if k not in ("primary","counts")},indent=2))
print("ARCHIVE", json.dumps(digest(archive)))
