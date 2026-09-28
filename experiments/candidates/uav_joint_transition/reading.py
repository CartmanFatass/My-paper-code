"""Read saved B01 evidence without stepping an environment or fitting a model."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from stable_baselines3 import PPO

from experiments.candidates.energy_relay_availability.runner import _sha256, _write_json
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS
from .constants import TRAIN_SEEDS, EVAL_SEEDS, HORIZON, OPTIMIZER_STEPS, evaluation_plan
from .training import fingerprint, optimizer_steps


def read(out):
    out = Path(out)
    manifest = json.loads((out/"manifest.json").read_text())
    verified = 0
    for name, binding in manifest["artifacts"].items():
        path = out/name
        if path.stat().st_size != binding["bytes"] or _sha256(path) != binding["sha256"]:
            raise ValueError(f"artifact binding failed: {name}")
        verified += 1
    training = json.loads((out/"training.json").read_text())
    summary = json.loads((out/"summary.json").read_text())
    rows = json.loads((out/"perworld.json").read_text())
    train_rows = json.loads((out/"training_perworld.json").read_text())
    result = {"launch_sha": manifest["launch_sha"], "verified_artifacts": verified,
              "batch_status": summary["status"], "complete_reading": False,
              "training_status": training["status"]}
    if summary["status"] != "complete":
        result["interpretation"] = "Technical incompleteness; no complete paired or learned-policy conclusion."
        return result
    if (sorted(row["seed"] for row in train_rows) != list(TRAIN_SEEDS)
            or [row["job_key"] for row in rows] != [job["job_key"] for job in evaluation_plan()]
            or summary["known_native_step_lower_bound"] != 288000
            or training["optimizer_steps"] != OPTIMIZER_STEPS):
        raise ValueError("fixed count/identity mismatch")
    model = PPO.load(out/"endpoint.zip", device="cpu")
    if fingerprint(model.policy) != training["endpoint_fingerprint"] or optimizer_steps(model.policy) != OPTIMIZER_STEPS:
        raise ValueError("endpoint identity mismatch")
    maximum_error, clocks, worlds, eval_choices = 0.0, 0, 0, 0
    train_queries = eval_queries = prediction_ticks = 0
    for row in train_rows+rows:
        path = out/row["raw_path"]
        if _sha256(path) != row["raw_sha256"]:
            raise ValueError("world raw binding mismatch")
        arm = "L" if row["arm"] == "L_train" else row["arm"]
        with np.load(path, allow_pickle=False) as raw:
            if list(raw["metric_fields"]) != list(TRACE_FIELDS) or raw["reward"].shape != (HORIZON,):
                raise ValueError("world fields or length mismatch")
            metrics, reward = raw["metrics"], raw["reward"]
            q = metrics[:, TRACE_FIELDS.index("qos_satisfaction_ratio")]
            cost = metrics[:, TRACE_FIELDS.index("return_constraint_cost")]
            cutoff = metrics[:, TRACE_FIELDS.index("cutoff_event_penalty")]
            depletion = metrics[:, TRACE_FIELDS.index("depletion_event_penalty")]
            delta = metrics[:, TRACE_FIELDS.index("graph_potential_delta")]
            maximum_error = max(maximum_error, float(np.max(np.abs(reward-(q-2*cost-cutoff-depletion+delta)))))
            if not np.isclose(reward.sum(), row["raw_native_J"], rtol=0, atol=1e-9):
                raise ValueError("native J reconstruction mismatch")
            if not np.isclose(q.mean(), row["qos_per_step"], rtol=0, atol=1e-12):
                raise ValueError("native service reconstruction mismatch")
            if raw["physical_xyz_m"].shape != (HORIZON+1, 8, 3):
                raise ValueError("physical path missing endpoint")
            records = json.loads(str(raw["planner_records_json"]))
            period = 10 if arm == "P" else 30
            if [record["step"] for record in records] != list(range(0, HORIZON, period)):
                raise ValueError("clock record mismatch")
            clocks += len(records)
            if arm in ("L", "O"):
                queries = sum(record["destination_record"]["query_count"]
                              + record["transition_snapshot_calls"] for record in records)
                ticks = sum(30*(record["feature_forecasts"]+record["candidate_count"]) for record in records)
                if queries != row["service_snapshot_calls"] or ticks != row["prediction_team_ticks"]:
                    raise ValueError("native model count reconstruction mismatch")
                prediction_ticks += ticks
                for record in records:
                    if record["destination_record"]["step"] != record["step"]:
                        raise ValueError("R clock shifted")
                    modes, eligible = np.asarray(record["requested_modes"]), np.asarray(record["eligible"])
                    if np.any(modes[~eligible.astype(bool)]):
                        raise ValueError("ineligible member requested non-D")
                    if arm == "O":
                        candidates = record["candidate_scores"]
                        if len(candidates) != record["candidate_count"] or 3*len(candidates) != record["transition_snapshot_calls"]:
                            raise ValueError("O candidate query mismatch")
                        if candidates[0]["modes"] != [0]*8:
                            raise ValueError("O did not start all-D")
                        retained = [candidate for candidate in candidates if candidate.get("accepted")]
                        selected = retained[-1] if retained else candidates[0]
                        if selected["modes"] != record["selected_modes"]:
                            raise ValueError("O selection differs from retained accepted search")
                    if row["arm"] == "L":
                        features = np.asarray(record["features"], dtype=np.float32)[None]
                        predicted, _ = model.predict(features, deterministic=True)
                        if not np.array_equal(predicted[0], modes):
                            raise ValueError("final L choice differs from endpoint argmax")
                        with torch.no_grad():
                            stats = model.policy.get_distribution(torch.from_numpy(features)).statistics()
                        if not np.allclose(stats["probabilities"][0].numpy(), record["policy"]["probabilities"], rtol=0, atol=1e-7):
                            raise ValueError("final L probabilities differ")
                        eval_choices += 1
            if row["arm"] == "L_train":
                train_queries += row["service_snapshot_calls"]
            else:
                eval_queries += row["service_snapshot_calls"]
            worlds += 1
    if (maximum_error > 1e-7 or train_queries+eval_queries != summary["service_snapshot_calls"]
            or prediction_ticks != summary["prediction_team_ticks"]):
        raise ValueError("batch arithmetic/work count mismatch")
    exposures = [json.loads(line) for line in (out/"training/exposure.jsonl").read_text().splitlines()]
    updates = [json.loads(line) for line in (out/"training/updates.jsonl").read_text().splitlines()]
    if len(exposures) != 6400 or len(updates) != 32 or updates[-1]["optimizer_steps"] != 256:
        raise ValueError("training audit exposure mismatch")
    result.update(complete_reading=True, verified_worlds=worlds, verified_clocks=clocks,
                  endpoint_choices_verified=eval_choices, native_reward_max_absolute_error=maximum_error,
                  training_queries=train_queries, evaluation_queries=eval_queries,
                  prediction_team_ticks=prediction_ticks,
                  uncertainty="one trained instance, eight paired worlds; no mechanistic or safety identification")
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = read(args.out)
    _write_json(args.out/"reading.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
