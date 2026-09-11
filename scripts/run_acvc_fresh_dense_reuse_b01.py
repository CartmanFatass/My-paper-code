#!/usr/bin/env python3
"""One fresh DENSE fit followed by the fixed C/F/dwell evaluation panels."""
import time

PROCESS_START = time.monotonic()

import os

for _name in (
    "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS",
):
    os.environ[_name] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse
import json
import math
from pathlib import Path
import signal
import sys
import traceback

import numpy as np
import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.set_default_dtype(torch.float32)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.candidates.acvc.native_link_loss_b01.learner import collect
from experiments.candidates.acvc.native_link_loss_b01.model import load_base
from experiments.candidates.acvc.native_link_loss_b01.report import reading, write_json
from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.geometry import (
    DENSE,
    NativeGeometryActor,
    geometry_exposure,
    geometry_snapshot,
    parameter_count,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    collect_episode,
    optimizer_for,
    update,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator, templates
from experiments.candidates.ucope.uav_motion_prefix_b01.study import clean_json


OBJECT = "ACVC_FRESH_DENSE_REUSE_B01"
CARD = "docs/research/candidates/acvc/ACVC_FRESH_DENSE_REUSE_B01_SCIENCE_CARD_20260910.md"
MASTER = 8951
EVALUATION_NAMESPACE = 8952
ARMS = ("C", "F", "dwell")


def _counts():
    return dict.fromkeys((
        "environment_constructors", "unscored_constructor_resets", "explicit_resets",
        "step_calls", "team_steps", "train_team_steps", "eval_team_steps",
        "completed_episode_steps", "train_episodes", "eval_episodes", "rollouts",
        "optimizer_steps", "backward_calls", "update_records",
        "backward_calls_lower_bound", "replayed_actor_agent_steps_lower_bound",
        "critic_update_rows_lower_bound",
        "base_agent_forwards", "train_actor_agent_forwards", "eval_actor_agent_forwards",
        "critic_forwards", "replayed_actor_agent_steps", "critic_update_rows",
        "learned_gate_agent_forwards", "recurrent_observations", "velocity_decisions",
        "duration_decisions", "d4", "scientific_uav_calls", "diagnostic_frames",
        "fresh_dense_initializations", "post_fit_loads", "final_checkpoints",
        "new_fits", "selected_final_checkpoints", "gate_constructions",
        "duration_heads", "selector_updates", "evaluation_updates",
    ), 0)


def _contrast(rows, first, second, expected):
    values = {
        arm: {row["episode"]: row["J"] for row in rows if row["arm"] == arm}
        for arm in (first, second)
    }
    complete = all(set(values[arm]) == set(range(expected)) for arm in values)
    episode_ids = sorted(set(values[first]) & set(values[second]))
    differences = [values[first][episode] - values[second][episode]
                   for episode in episode_ids]
    finite = all(math.isfinite(value) for value in differences)
    mean = float(np.mean(differences)) if differences and finite else None
    conditional_se = (float(np.std(differences, ddof=1) / math.sqrt(len(differences)))
                      if len(differences) > 1 and finite else None)
    return {
        "complete": complete and finite,
        "episode_ids": episode_ids,
        "paired_differences_J": differences,
        "mean_J": mean,
        "mean_S": mean * 256 if mean is not None else None,
        "conditional_SE_J": conditional_se,
        "n_joint_episodes": len(differences),
        "reading": reading(mean) if complete and mean is not None else "INCOMPLETE",
    }


def final_panel(rows, expected):
    evaluation = [row for row in rows if row.get("phase") == "eval"]
    arm_values = {
        arm: [row["J"] for row in sorted(evaluation, key=lambda item: item["episode"])
              if row["arm"] == arm]
        for arm in ARMS
    }
    contrasts = {
        f"{first}-{second}": _contrast(evaluation, first, second, expected)
        for first, second in (("F", "C"), ("F", "dwell"), ("dwell", "C"))
    }
    complete = (all(len(values) == expected for values in arm_values.values())
                and all(item["complete"] for item in contrasts.values()))
    return {
        "complete": complete,
        "arm_mean_J": {
            arm: float(np.mean(values)) if len(values) == expected else None
            for arm, values in arm_values.items()
        },
        "contrasts": contrasts,
        "primaries": ["F-C", "F-dwell"],
        "secondary": "dwell-C",
        "uncertainty": (
            "Paired episode sample SD/sqrt(64), conditional on one fresh final checkpoint; "
            "no training-seed uncertainty."
        ),
    }


def run(output, launch_sha, process_start, execution_seconds, make_env=make_real,
        train_episodes=512, horizon=256, eval_episodes=64):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    counts = _counts()
    summary = {
        "object": OBJECT,
        "card": CARD,
        "mode": "UAV_B_EXPLORE",
        "master": MASTER,
        "evaluation_namespace": EVALUATION_NAMESPACE,
        "launch_sha": launch_sha,
        "status": "incomplete",
        "counts": counts,
        "configuration": {
            "horizon": horizon,
            "training_episodes": train_episodes,
            "episodes_per_rollout": 2,
            "ppo_epochs_per_rollout": 4,
            "chunk": 32,
            "evaluation_episodes_per_arm": eval_episodes,
            "evaluation_order": list(ARMS),
            "ratio_grouping": "agent_compound",
            "value_moments": None,
            "renewal": False,
            "duration_support": [1, 4],
            "velocity_mode": "sampled",
            "entropy_coef": 0.01,
            "device": "cpu",
            "dtype": "float32",
            "intraop_threads": torch.get_num_threads(),
            "interop_threads": torch.get_num_interop_threads(),
            "remaining_process_timeout_s": execution_seconds,
        },
        "panels": [],
        "limits": [],
        "fit_complete": False,
        "checkpoint_complete": False,
        "scientific_invocations": 1,
        "resources": "resources_unmeasured",
        "checkpoint_selection": "final checkpoint after the fixed fit; no fit-quality gate",
        "cost_law": (
            "imports+construction + 131072 training team steps + 1024 full-rollout "
            "replay/backward/Adam calls + 3 checkpoint loads + 49152 evaluation team "
            "steps + C/F/dwell checks + publication and process exit"
        ),
        "allocation_seconds": {
            "whole_supervised_task": 270,
            "cumulative_runtime_support": 330,
            "complete_charge": 600,
        },
    }
    rows = []
    actor = critic = initial = None
    old_handler = None
    alarm_installed = False
    scientific_path_complete = False

    def timeout(*_):
        raise TimeoutError(f"{OBJECT} remaining process timeout reached")

    def check():
        if time.monotonic() - process_start >= execution_seconds:
            timeout()

    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, timeout)
        remaining = max(0.001, execution_seconds - (time.monotonic() - process_start))
        signal.setitimer(signal.ITIMER_REAL, remaining)
        alarm_installed = True

    episode_path = output / "episodes.jsonl"
    update_path = output / "updates.jsonl"
    with episode_path.open("w", encoding="utf-8") as episode_file, \
            update_path.open("w", encoding="utf-8") as update_file:
        def emit_training(row):
            published = dict(row, base=MASTER, rule="DENSE_fit", S=row["reward_sum"])
            rows.append(published)
            episode_file.write(json.dumps(published, allow_nan=False) + "\n")
            episode_file.flush()

        def emit_evaluation(row):
            published = dict(row, base=MASTER, rule=row["arm"],
                             evaluation_namespace=EVALUATION_NAMESPACE)
            rows.append(published)
            episode_file.write(json.dumps(published, allow_nan=False) + "\n")
            episode_file.flush()

        try:
            check()
            common_actor, critic = templates(MASTER)
            actor = NativeGeometryActor(common_actor, DENSE, 100000 * MASTER + 12)
            counts["fresh_dense_initializations"] += 1
            initial = geometry_snapshot(actor, critic)
            optimizer = optimizer_for(actor, critic)
            train_velocity = generator(100000 * MASTER + 21)
            env = make_env(100000 * MASTER + 1000)
            counts["environment_constructors"] += 1
            counts["unscored_constructor_resets"] += 1
            for rollout_index in range(train_episodes // 2):
                episodes = []
                episode_ids = []
                for offset in (0, 1):
                    episode_index = 2 * rollout_index + offset
                    before_recurrent = counts["recurrent_observations"]
                    try:
                        episode = collect_episode(
                            env, actor, critic, horizon,
                            100000 * MASTER + 1000 + episode_index,
                            train_velocity, generator(100000 * MASTER + 4000 + episode_index),
                            {"master": MASTER, "base": MASTER, "arm": DENSE,
                             "phase": "train", "episode": episode_index},
                            check, counts, emit_training, lambda _row: None, summary["limits"],
                            real=True, diagnostics=False, ratio_grouping="agent_compound",
                            value_moments=None, renewal=False, duration_support=(1, 4),
                            velocity_mode="sampled",
                        )
                    finally:
                        actor_forwards = counts["recurrent_observations"] - before_recurrent
                        counts["base_agent_forwards"] += actor_forwards
                        counts["train_actor_agent_forwards"] += actor_forwards
                        counts["critic_forwards"] += actor_forwards // 5
                    episodes.append(episode)
                    episode_ids.append(episode_index)
                before_updates = counts["optimizer_steps"]
                try:
                    records = update(
                        actor, critic, optimizer, episodes, 32, check, counts,
                        ratio_grouping="agent_compound", entropy_coef=0.01,
                        value_moments=None,
                    )
                except Exception:
                    completed_adam = counts["optimizer_steps"] - before_updates
                    summary["interrupted_update"] = {
                        "rollout": rollout_index,
                        "completed_adam_steps": completed_adam,
                        "completed_adam_epoch_records_missing": completed_adam,
                        "record_limit": (
                            "The protected four-epoch update helper returned no partial epoch "
                            "list; no values are claimed for the missing records."
                        ),
                    }
                    raise
                performed = counts["optimizer_steps"] - before_updates
                counts["backward_calls"] += performed
                counts["replayed_actor_agent_steps"] += performed * 2 * horizon * 5
                counts["critic_update_rows"] += performed * 2 * horizon
                for record in records:
                    update_file.write(json.dumps(dict(
                        record, master=MASTER, rollout=rollout_index,
                        episodes=episode_ids,
                    ), allow_nan=False) + "\n")
                    counts["update_records"] += 1
                update_file.flush()
                counts["rollouts"] += 1
                if (rollout_index + 1) % 16 == 0:
                    print(json.dumps({
                        "rollouts": rollout_index + 1,
                        "training_episodes": counts["train_episodes"],
                        "optimizer_steps": counts["optimizer_steps"],
                        "process_wall_s": time.monotonic() - process_start,
                    }), flush=True)
                check()
            summary["fit_complete"] = True
            counts["new_fits"] += 1
            summary["exposure"] = geometry_exposure(initial, actor, critic)
            summary["parameters"] = {
                "actor": parameter_count(actor),
                "critic": parameter_count(critic),
                "total": parameter_count(actor, critic),
            }
            checkpoint = output / "final_DENSE.pt"
            torch.save({
                "actor": actor.state_dict(),
                "critic": critic.state_dict(),
                "master": MASTER,
                "object": OBJECT,
            }, checkpoint)
            counts["final_checkpoints"] += 1
            counts["selected_final_checkpoints"] += 1
            summary["checkpoint_complete"] = True
            check()

            for arm, arm_index in zip(ARMS, (2, 3, 4)):
                panel_start = time.monotonic()
                base = load_base(checkpoint, EVALUATION_NAMESPACE)
                counts["post_fit_loads"] += 1
                env = make_env(100000 * EVALUATION_NAMESPACE + 60 + arm_index)
                counts["environment_constructors"] += 1
                counts["unscored_constructor_resets"] += 1
                before_rows = len(rows)
                before_counts = counts.copy()
                for episode_index in range(eval_episodes):
                    before_steps = counts["team_steps"]
                    before_forwards = counts["base_agent_forwards"]
                    episode_complete = False
                    try:
                        collect(
                            env, base, None, None, EVALUATION_NAMESPACE, arm, "eval",
                            episode_index, horizon, check, counts, emit_evaluation,
                        )
                        episode_complete = True
                    finally:
                        panel_steps = counts["team_steps"] - before_steps
                        counts["eval_team_steps"] += panel_steps
                        if episode_complete:
                            counts["completed_episode_steps"] += panel_steps
                        counts["scientific_uav_calls"] += panel_steps
                        counts["eval_actor_agent_forwards"] += (
                            counts["base_agent_forwards"] - before_forwards)
                summary["panels"].append({
                    "arm": arm,
                    "episodes": len(rows) - before_rows,
                    "wall_s": time.monotonic() - panel_start,
                    "counts": {
                        key: counts[key] - before_counts[key]
                        for key in ("explicit_resets", "step_calls", "team_steps",
                                    "eval_episodes", "base_agent_forwards")
                    },
                })
                print(json.dumps({
                    "completed_arm": arm,
                    "evaluation_episodes": counts["eval_episodes"],
                    "process_wall_s": time.monotonic() - process_start,
                }), flush=True)
                check()
            scientific_path_complete = True
        except Exception as error:
            summary["error"] = f"{type(error).__name__}: {error}"
            summary["traceback"] = traceback.format_exc()
            print(summary["traceback"], flush=True)
        finally:
            if alarm_installed:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old_handler)
            counts["backward_calls_lower_bound"] = counts["optimizer_steps"]
            counts["replayed_actor_agent_steps_lower_bound"] = (
                counts["optimizer_steps"] * 2 * horizon * 5)
            counts["critic_update_rows_lower_bound"] = (
                counts["optimizer_steps"] * 2 * horizon)
            if "interrupted_update" in summary:
                counts["backward_calls"] = None
                counts["replayed_actor_agent_steps"] = None
                counts["critic_update_rows"] = None
                summary["unavailable_measurements"] = [
                    "exact backward calls across the interrupted update",
                    "exact replayed actor-agent steps across the interrupted update",
                    "exact critic update rows across the interrupted update",
                ]
            summary["primary"] = final_panel(rows, eval_episodes)
            if scientific_path_complete and summary["primary"]["complete"]:
                summary["status"] = "complete"
            if initial is not None and actor is not None and critic is not None:
                try:
                    summary["exposure"] = geometry_exposure(initial, actor, critic)
                except Exception as error:
                    summary["limits"].append(
                        f"exposure publication: {type(error).__name__}: {error}")
            summary["training_rows"] = sum(row.get("phase") == "train" for row in rows)
            summary["evaluation_rows"] = sum(row.get("phase") == "eval" for row in rows)
            summary["intervention_by_rule"] = {
                arm: {
                    key: sum(row.get(key, 0) for row in rows
                             if row.get("phase") == "eval" and row.get("arm") == arm)
                    for key in ("opportunities", "retrace", "dwell", "apply", "distinguishable")
                }
                for arm in ARMS
            }
            summary["process_wall_s_to_summary"] = time.monotonic() - process_start
            summary["timing_boundary"] = (
                "Runner timing starts before imports and is sampled immediately before summary "
                "serialization; the supervisor records admission through final publication and "
                "actual process exit."
            )
            if summary["process_wall_s_to_summary"] >= execution_seconds:
                summary["status"] = "incomplete"
                summary.setdefault("error", f"TimeoutError: {OBJECT} remaining process timeout reached")
            cleaned = clean_json(summary, summary["limits"])
            try:
                write_json(output / "summary.json", cleaned)
            except Exception as error:
                summary["status"] = "publication_failed"
                summary["limits"].append(f"publication: {type(error).__name__}: {error}")
                cleaned = clean_json(summary, summary["limits"])
                write_json(output / "summary.json", cleaned)
    return 0 if summary["status"] == "complete" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=[MASTER], default=MASTER)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--execution-seconds", type=float, required=True)
    args = parser.parse_args()
    return run(args.output, args.launch_sha, PROCESS_START, args.execution_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
