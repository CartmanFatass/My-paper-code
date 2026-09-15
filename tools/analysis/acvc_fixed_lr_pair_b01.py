"""Read recorded fixed-rate originals; no model load or native trajectory execution."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments.candidates.acvc.cluster_fixed_lr_pair_b01 import protocol as p


def jsonl(path, errors):
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        errors.append(f"{path.name}: {type(error).__name__}: {error}")
        return []
    rows = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as error:
            # A killed original may leave an unfinished final write. Keep other full records.
            errors.append(f"{path.name} line {number}: {type(error).__name__}: {error}")
    return rows


def read_summary(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{path.name}: {type(error).__name__}: {error}")
        return {}


def analyze(paths):
    originals, recipe_rows = {}, {}
    expected_counts = dict(train_episodes=4096, eval_episodes=192, team_steps=1097728,
                           train_team_steps=1048576, eval_team_steps=49152, rollouts=2048,
                           optimizer_steps=8192, backward_calls=8192, update_records=8192,
                           replayed_actor_agent_steps=20971520, critic_update_rows=4194304,
                           fixed_snapshots=1, post_fit_loads=3, environment_constructors=4,
                           new_fits=1, final_checkpoints=1)
    for recipe, path in paths.items():
        errors = []
        rows, updates = jsonl(path / "episodes.jsonl", errors), jsonl(path / "updates.jsonl", errors)
        summary = read_summary(path / "summary.json", errors)
        recipe_rows[recipe] = rows
        train = [row for row in rows if row.get("phase") == "train"]
        native = {}
        if (path / "native_time.txt").exists():
            for line in (path / "native_time.txt").read_text().splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    try:
                        native[key] = float(value)
                    except ValueError:
                        native[key] = None
        primary = p.final_panel(rows, recipe)
        checks = dict(
            original_files_complete=not errors,
            identity=summary.get("object") == p.OBJECT and summary.get("recipe") == recipe
                     and summary.get("master") == p.MASTER and summary.get("learning_rate") == p.RECIPES[recipe],
            original_complete=summary.get("status") == "complete" and summary.get("fit_complete") is True,
            rows=len(train) == 4096 and len(rows) == 4288,
            train_identity=[row.get("episode") for row in train] == list(range(4096)) and all(
                row.get("master") == p.MASTER and row.get("recipe") == recipe
                and row.get("learning_rate") == p.RECIPES[recipe]
                and row.get("reset_seed") == 100000*p.MASTER+1000+row["episode"]
                and row.get("steps") == 256 and row.get("J") == row.get("S", 0)/256
                and np.isfinite(row.get("J", np.nan)) for row in train),
            updates=len(updates) == 8192 and all(
                row.get("recipe") == recipe and row.get("learning_rate") == p.RECIPES[recipe]
                and row.get("master") == p.MASTER and row.get("rollout") == index//4
                and row.get("epoch") == index%4
                and row.get("episodes") == [2*(index//4),2*(index//4)+1]
                and all(np.isfinite(row.get(key,np.nan)) for key in
                        ("loss","policy_loss","value_loss","entropy","grad_norm"))
                for index,row in enumerate(updates)),
            counts=all(summary.get("counts",{}).get(key) == value for key,value in expected_counts.items()),
            panels=primary["complete"], primary_publication=summary.get("primary") == primary,
            group_rate=summary.get("optimizer_group_learning_rates") == [p.RECIPES[recipe]],
            native_exit_not_adverse=native.get("exit_code") in (0, None),
        )
        training = np.asarray([row["J"] for row in train], dtype=np.float64)
        originals[recipe] = dict(path=str(path), launch_sha=summary.get("launch_sha"), checks=checks,
                                checked=all(checks.values()), ingestion_errors=errors,
                                counts=summary.get("counts"), native=native,
                                training_blocks_256=[dict(first_episode=start, n=len(training[start:start+256]),
                                                        mean_J=float(training[start:start+256].mean()))
                                                     for start in range(0,len(training),256)],
                                parameter_exposure=summary.get("exposure"), parameters=summary.get("parameters"),
                                intervention_by_checkpoint_rule=summary.get("intervention_by_checkpoint_rule"))
    pair = p.paired_panel(recipe_rows)
    sources = [value["launch_sha"] for value in originals.values()]
    checks_passed = len(originals) == 2 and all(value["checked"] for value in originals.values()) and len(set(sources)) == 1
    probabilities = {"low_C-reference_C":[.45,.35,.20], "low:F-C":[.70,.20,.10],
                     "low:F-dwell":[.60,.25,.15], "reference:F-C":[.80,.15,.05], "reference:F-dwell":[.70,.20,.10]}
    predictions = {}
    for name,probs in probabilities.items():
        contrast = pair["cross_recipe"][name] if ":" not in name else pair["recipes"][name.split(":")[0]]["contrasts"][name.split(":")[1]]
        outcome = contrast["reading"]
        predictions[name] = dict(probabilities=dict(zip(["UP","WITHIN","DOWN"],probs)), observed=outcome,
                                 brier=sum((prob-float(label==outcome))**2 for label,prob in zip(["UP","WITHIN","DOWN"],probs)) if outcome != "INCOMPLETE" else None)
    native_complete = all(all(value["native"].get(key) is not None for key in ("native_wall_s","user_s","system_s")) for value in originals.values())
    return dict(object=p.OBJECT, master=p.MASTER, evaluation_namespace=p.EVALUATION_NAMESPACE,
                analysis="Recorded original bytes only; no model loading, new environment calls or learning.",
                checks_passed=checks_passed, object_status="complete" if checks_passed and pair["complete"] else "incomplete",
                original_completion_limit="Whole object requires both complete fit records and all panels. Panel completeness alone is narrower evidence. Missing resource telemetry is reported, not a scientific invalidity rule; supervisor receipts are checked separately at intake.",
                originals=originals, pair=pair, predictions=predictions,
                owner_prediction="not taken (unattended); replace only from an actual owner reply",
                costs=dict(resources="measured" if native_complete else "resources_unmeasured", native_wall_sum_s=sum(value["native"].get("native_wall_s",0) for value in originals.values()) if native_complete else None,
                           aggregate_cpu_s=sum(value["native"]["user_s"]+value["native"]["system_s"] for value in originals.values()) if native_complete else None,
                           overlapping_elapsed_s="requires supervisor acceptance/terminal timestamps; not the sum of native walls",
                           full_support_provider_maintenance_lifetime="UNKNOWN"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--low",type=Path,required=True)
    parser.add_argument("--reference",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    result = analyze({"low":args.low,"reference":args.reference})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(dict(checks_passed=result["checks_passed"],primary=result["pair"]["cross_recipe"]["low_C-reference_C"],costs=result["costs"])))
    return 0 if result["checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
