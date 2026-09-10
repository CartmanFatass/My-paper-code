"""VSP03 B06: continuous512, fixed paired128/512 endpoints. scope: none"""
import json
import time
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.vsp_03.vsp03_b01.b01 import (
    objective, vectors, scales, write_json, peak_rss,
)
from experiments.candidates.vsp_03.vsp03_b02.b02 import (
    Model, worlds, action_tapes, rollout, metrics, difference,
)


def paired_budget_change(early, late):
    rows = [{"world": a["world"], "phase_zero_identity": a["phase_zero_identity"],
             "b": b["G_greedy-R0"] - a["G_greedy-R0"]} for a, b in zip(early, late)]
    values = np.array([row["b"] for row in rows])
    sd = float(values.std(ddof=1))
    return rows, {"mean": float(values.mean()), "conditional_world_sd": sd,
                  "conditional_world_se": sd / np.sqrt(len(values)), "worlds": len(values)}


def run(seed, out, launch_sha, started, node, command):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    deadline = started + 50
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    activity = {"episodes_started": 0, "episodes_completed": 0, "team_ticks": 0,
                "target_transitions": 0, "decision_rows": 0, "rollout_policy_forwards": 0}
    summary = {"object": "VSP03_B06", "seed": seed, "launch_sha": launch_sha,
        "node": node, "command": command, "status": "incomplete", "arms": {}, "checkpoints": {},
        "actual_rollouts": activity, "model_constructions": 0, "optimizer_steps": 0,
        "device": "cpu", "dtype": "float32", "compute_threads": 1,
        "rng": {"worlds": "PCG64 SeedSequence([302,seed,split,episode,target]);40 uniforms",
            "phase": "[302,seed,split,episode,2];one integers(0,2)",
            "actions": "[303,seed,split,mode,arm,episode];17 calendar-position uniforms",
            "splits": "train100/evaluation200", "modes": "train0/stochastic-evaluation1",
            "arms": "G1", "initialization": 40000 + seed},
        "cost_law": "admission+imports+G_init+512*batch128x40x2+8*eval1024x40x2"
                    "+weights+publication/readback/exit",
        "independent_training_instances": 1,
        "validation_models": 0, "validation_episodes": 0, "validation_optimizer_steps": 0,
        "aggregate_cpu_s": None}
    endpoints = {}
    try:
        eval_draws, eval_phase = worlds(seed, 200, 0, 1024)
        eval_uniforms = action_tapes(seed, 200, 1, 1, 0, 1024)
        arm_index, arm = 1, "G"
        arm_started = time.perf_counter()
        model = Model(seed, arm)
        summary["model_constructions"] += 1
        initial = vectors(model)
        record = {"initial": scales(model, initial), "training_episodes": 0,
                  "training_team_ticks": 0, "training_target_transitions": 0,
                  "training_valid_rows": 0, "gradient_rows": 0, "optimizer_steps": 0,
                  "backward_calls": 0, "evaluation_episodes": 0}
        summary["arms"][arm] = record
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999),
                                     eps=1e-8, weight_decay=0)
        with (out / f"{arm}_curve.jsonl").open("w", encoding="utf-8") as curve:
            for update in range(1, 513):
                first = (update - 1) * 128
                draws, phase = worlds(seed, 100, first, 128)
                batch = rollout(draws, phase, model,
                    action_tapes(seed, 100, 0, arm_index, first, 128),
                    deadline=deadline, activity=activity)
                loss, info = objective(model, batch, update)
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()
                record["training_episodes"] += 128
                record["training_team_ticks"] += 5120
                record["training_target_transitions"] += 10240
                record["training_valid_rows"] += batch["decision_rows"]
                record["gradient_rows"] += batch["decision_rows"]
                record["optimizer_steps"] += 1
                record["backward_calls"] += 1
                summary["optimizer_steps"] += 1
                curve.write(json.dumps({"update": update, **info, **metrics(batch["rows"]),
                    "valid_rows": batch["decision_rows"], "gradient_rows": batch["decision_rows"]},
                    allow_nan=False) + "\n")
                curve.flush()
                if update in (1, 128, 512):
                    record["first" if update == 1 else str(update)] = scales(model, initial)
                if update in (1, 128, 512):
                    print(json.dumps({"arm": arm, "update": update,
                        "elapsed_s": time.perf_counter() - started,
                        "actual_rollouts": activity,
                        "optimizer_steps": summary["optimizer_steps"]}), flush=True)
                if update in (128, 512):
                    panel = {"update": update, "status": "incomplete", "absolute": {}}
                    summary["checkpoints"][str(update)] = panel
                    # Serialize the actual boundary before any further update.
                    state = {k: v.detach().clone() for k, v in model.state_dict().items()}
                    weight_path = out / f"G_{update}.pt"
                    torch.save(state, weight_path)
                    persisted = torch.load(weight_path, map_location="cpu", weights_only=True)
                    assert all(torch.equal(state[k], persisted[k]) for k in state)
                    panel["weights_readback"] = True
                    rows = {}
                    with torch.no_grad():
                        for name in ("G_greedy", "G_stochastic", "R0", "R"):
                            batch = rollout(eval_draws, eval_phase,
                                model if name.startswith("G_") else None,
                                eval_uniforms if name == "G_stochastic" else None,
                                rule=name if name in ("R0", "R") else "R0",
                                deadline=deadline, activity=activity)
                            rows[name] = write_json(out / f"{name}_{update}.json", batch["rows"])
                            record["evaluation_episodes"] += 1024
                            panel["absolute"][name] = metrics(rows[name])
                    contrasts = [("G_greedy", "R0"), ("G_greedy", "R"),
                                 ("G_stochastic", "R0"), ("G_stochastic", "R"),
                                 ("G_stochastic", "G_greedy")]
                    differences = [
                        {"world": i, "phase_zero_identity": int(eval_phase[i]),
                         **{a + "-" + b: rows[a][i]["return"] - rows[b][i]["return"]
                            for a, b in contrasts}} for i in range(1024)]
                    write_json(out / f"paired_differences_{update}.json", differences)
                    panel["comparisons"] = {a + "-" + b: difference(rows[a], rows[b])
                                            for a, b in contrasts}
                    panel["status"] = "complete"
                    endpoints[update] = differences
                    # Preserve a trustworthy128 panel even if later work terminates.
                    write_json(out / f"checkpoint_{update}.json", panel)
        record["arm_wall_s"] = time.perf_counter() - arm_started
        summary["primary"] = summary["checkpoints"]["512"]["comparisons"]["G_greedy-R0"]
        summary["primary_name"] = "update512:G_greedy-R0"
        budget_rows, summary["budget_change"] = paired_budget_change(endpoints[128], endpoints[512])
        write_json(out / "paired_budget_change.json", budget_rows)
        summary["status"] = "complete"
    except Exception as exc:
        summary["error"] = repr(exc)
        raise
    finally:
        summary["elapsed_through_output_start_s"] = time.perf_counter() - started
        summary["peak_rss_bytes"] = peak_rss()
        persisted = write_json(out / "summary.json", summary)
        assert persisted["actual_rollouts"] == activity
        assert persisted["optimizer_steps"] == summary["optimizer_steps"]
        assert persisted["model_constructions"] == summary["model_constructions"]
        assert persisted["arms"] == summary["arms"]
        if summary["status"] == "complete":
            assert persisted["primary"] == summary["primary"]
        print(json.dumps({"status": summary["status"], "counts": activity,
                          "elapsed_through_readback_s": time.perf_counter() - started}), flush=True)
        if time.perf_counter() >= deadline:
            raise TimeoutError("complete invocation cap through publication/readback")
