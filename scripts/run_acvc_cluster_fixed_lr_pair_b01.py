#!/usr/bin/env python3
"""One original fixed-rate C fit and its three private final panels."""
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
from pathlib import Path
import signal
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.candidates.acvc.cluster_fixed_lr_pair_b01.protocol import (
    ARMS, CARD, CHECKPOINTS, EVAL_EPISODES, EVALUATION_NAMESPACE, EVALUATION_ORDER,
    HORIZON, MASTER, OBJECT, PLANNING_SECONDS, RECIPES, TRAIN_EPISODES, final_panel, make_cluster,
)
from scripts import run_acvc_fresh_dense_reuse_b01 as shared

torch = shared.torch


def _save_checkpoint(path, actor, critic, checkpoint_episode, recipe):
    torch.save({
        "actor": actor.state_dict(),
        "critic": critic.state_dict(),
        "master": MASTER,
        "recipe": recipe,
        "learning_rate": RECIPES[recipe],
        "object": OBJECT,
        "checkpoint_episode": checkpoint_episode,
        "completed_rollout_index": checkpoint_episode // 2 - 1,
        "optimizer_steps": 2 * checkpoint_episode,
    }, path)


def optimizer_for(actor, critic, recipe):
    optimizer = shared.optimizer_for(actor, critic)
    for group in optimizer.param_groups:
        group["lr"] = RECIPES[recipe]
    return optimizer


def run(output, launch_sha, process_start, execution_seconds, recipe):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    counts = shared._counts()
    counts.update(fixed_snapshots=0)
    summary = {
        "object": OBJECT,
        "card": CARD,
        "mode": "UAV_B_EXPLORE",
        "master": MASTER,
        "recipe": recipe,
        "learning_rate": RECIPES[recipe],
        "evaluation_namespace": EVALUATION_NAMESPACE,
        "launch_sha": launch_sha,
        "status": "incomplete",
        "counts": counts,
        "configuration": {
            "horizon": HORIZON,
            "training_episodes": TRAIN_EPISODES,
            "episodes_per_rollout": 2,
            "ppo_epochs_per_rollout": 4,
            "chunk": 32,
            "checkpoint_episodes": list(CHECKPOINTS),
            "evaluation_episodes_per_arm": EVAL_EPISODES,
            "evaluation_order": [[checkpoint, arm] for checkpoint, arm in EVALUATION_ORDER],
            "common_reset_worlds": f"100000*{EVALUATION_NAMESPACE}+2000+episode across recipes/packages",
            "recipe_factor_in_rng": False,
            "learning_rate": RECIPES[recipe],
            "checkpoint_factor_in_evaluation_rng": False,
            "ratio_grouping": "agent_compound",
            "value_moments": None,
            "renewal": False,
            "duration_support": [1, 4],
            "velocity_mode": "sampled",
            "entropy_coef": .01,
            "training_rule": "C",
            "user_distribution": "cluster",
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
        "checkpoints": [],
        "checkpoint_exposures": {},
        "scientific_invocations": 1,
        "resources": "resources_unmeasured",
        "checkpoint_selection": (
            "One fixed final snapshot after episode 4096, chosen before outcomes; "
            "no midpoint or selection by fit or evaluation quality."
        ),
        "cost_law": (
            "imports+construction + 1048576 training team steps + 8192 ordered full-rollout "
            "replay/backward/Adam calls + 1 fixed snapshot serialization + 3 checkpoint loads + "
            "49152 evaluation team steps + three private C/F/dwell panels + within-recipe "
            "publication and process exit"
        ),
        "allocation_seconds": PLANNING_SECONDS,
    }
    rows = []
    actor = critic = initial = None
    old_handler = None
    alarm_installed = False
    scientific_path_complete = False
    checkpoint_paths = {}
    checkpoint_episode = None

    def timeout(*_):
        raise TimeoutError(f"{OBJECT} remaining process timeout reached")

    def check():
        if time.monotonic() - process_start >= execution_seconds:
            timeout()

    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, timeout)
        remaining = max(.001, execution_seconds - (time.monotonic() - process_start))
        signal.setitimer(signal.ITIMER_REAL, remaining)
        alarm_installed = True

    episode_path = output / "episodes.jsonl"
    update_path = output / "updates.jsonl"
    with episode_path.open("w", encoding="utf-8") as episode_file, \
            update_path.open("w", encoding="utf-8") as update_file:
        def emit_training(row):
            published = dict(row, base=MASTER, recipe=recipe, learning_rate=RECIPES[recipe],
                             rule="DENSE_fit", S=row["reward_sum"])
            rows.append(published)
            episode_file.write(json.dumps(published, allow_nan=False) + "\n")
            episode_file.flush()

        def emit_evaluation(row):
            published = dict(row, base=MASTER, recipe=recipe, learning_rate=RECIPES[recipe],
                             rule=row["arm"],
                             evaluation_namespace=EVALUATION_NAMESPACE,
                             checkpoint_episode=checkpoint_episode)
            rows.append(published)
            episode_file.write(json.dumps(published, allow_nan=False) + "\n")
            episode_file.flush()

        try:
            check()
            common_actor, critic = shared.templates(MASTER)
            actor = shared.NativeGeometryActor(common_actor, shared.DENSE, 100000 * MASTER + 12)
            counts["fresh_dense_initializations"] += 1
            initial = shared.geometry_snapshot(actor, critic)
            optimizer = optimizer_for(actor, critic, recipe)
            summary["optimizer_group_learning_rates"] = [group["lr"] for group in optimizer.param_groups]
            train_velocity = shared.generator(100000 * MASTER + 21)
            env = make_cluster(100000 * MASTER + 1000)
            counts["environment_constructors"] += 1
            counts["unscored_constructor_resets"] += 1
            for rollout_index in range(TRAIN_EPISODES // 2):
                episodes = []
                episode_ids = []
                for offset in (0, 1):
                    episode_index = 2 * rollout_index + offset
                    before_recurrent = counts["recurrent_observations"]
                    try:
                        episode = shared.collect_episode(
                            env, actor, critic, HORIZON,
                            100000 * MASTER + 1000 + episode_index,
                            train_velocity, shared.generator(100000 * MASTER + 4000 + episode_index),
                            {"master": MASTER, "base": MASTER, "arm": shared.DENSE,
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
                    records = shared.update(
                        actor, critic, optimizer, episodes, 32, check, counts,
                        ratio_grouping="agent_compound", entropy_coef=.01, value_moments=None,
                    )
                except Exception:
                    completed_adam = counts["optimizer_steps"] - before_updates
                    summary["interrupted_update"] = {
                        "rollout": rollout_index,
                        "completed_adam_steps": completed_adam,
                        "completed_adam_epoch_records_missing": completed_adam,
                        "record_limit": (
                            "The protected four-epoch update helper returned no partial epoch list; "
                            "no values are claimed for the missing records."
                        ),
                    }
                    raise
                performed = counts["optimizer_steps"] - before_updates
                counts["backward_calls"] += performed
                counts["replayed_actor_agent_steps"] += performed * 2 * HORIZON * 5
                counts["critic_update_rows"] += performed * 2 * HORIZON
                for record in records:
                    update_file.write(json.dumps(dict(
                        record, master=MASTER, recipe=recipe, learning_rate=RECIPES[recipe],
                        rollout=rollout_index, episodes=episode_ids,
                    ), allow_nan=False) + "\n")
                    counts["update_records"] += 1
                update_file.flush()
                counts["rollouts"] += 1
                completed_episodes = 2 * (rollout_index + 1)
                if completed_episodes in CHECKPOINTS:
                    path = output / f"DENSE_episode_{completed_episodes}.pt"
                    _save_checkpoint(path, actor, critic, completed_episodes, recipe)
                    checkpoint_paths[completed_episodes] = path
                    counts["fixed_snapshots"] += 1
                    counts["final_checkpoints"] += 1
                    summary["checkpoint_exposures"][str(completed_episodes)] = \
                        shared.geometry_exposure(initial, actor, critic)
                    summary["checkpoints"].append({
                        "checkpoint_episode": completed_episodes,
                        "completed_rollout_index": rollout_index,
                        "optimizer_steps": counts["optimizer_steps"],
                        "update_records": counts["update_records"],
                        "path": path.name,
                    })
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
            summary["exposure"] = shared.geometry_exposure(initial, actor, critic)
            summary["parameters"] = {
                "actor": shared.parameter_count(actor),
                "critic": shared.parameter_count(critic),
                "total": shared.parameter_count(actor, critic),
            }
            summary["checkpoint_complete"] = set(checkpoint_paths) == set(CHECKPOINTS)

            for checkpoint_episode, arm in EVALUATION_ORDER:
                arm_index = {"C": 2, "F": 3, "dwell": 4}[arm]
                panel_start = time.monotonic()
                base = shared.load_base(checkpoint_paths[checkpoint_episode], EVALUATION_NAMESPACE)
                counts["post_fit_loads"] += 1
                env = make_cluster(100000 * EVALUATION_NAMESPACE + 60 + arm_index)
                counts["environment_constructors"] += 1
                counts["unscored_constructor_resets"] += 1
                before_rows = len(rows)
                before_counts = counts.copy()
                for episode_index in range(EVAL_EPISODES):
                    before_steps = counts["team_steps"]
                    before_forwards = counts["base_agent_forwards"]
                    episode_complete = False
                    try:
                        shared.collect(
                            env, base, None, None, EVALUATION_NAMESPACE, arm, "eval",
                            episode_index, HORIZON, check, counts, emit_evaluation,
                        )
                        episode_complete = True
                    finally:
                        panel_steps = counts["team_steps"] - before_steps
                        counts["eval_team_steps"] += panel_steps
                        if episode_complete:
                            counts["completed_episode_steps"] += panel_steps
                        counts["scientific_uav_calls"] += panel_steps
                        counts["eval_actor_agent_forwards"] += \
                            counts["base_agent_forwards"] - before_forwards
                summary["panels"].append({
                    "checkpoint_episode": checkpoint_episode,
                    "arm": arm,
                    "episodes": len(rows) - before_rows,
                    "wall_s": time.monotonic() - panel_start,
                    "counts": {key: counts[key] - before_counts[key] for key in (
                        "explicit_resets", "step_calls", "team_steps", "eval_episodes",
                        "base_agent_forwards",
                    )},
                })
                print(json.dumps({
                    "checkpoint_episode": checkpoint_episode,
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
            counts["replayed_actor_agent_steps_lower_bound"] = counts["optimizer_steps"] * 2 * HORIZON * 5
            counts["critic_update_rows_lower_bound"] = counts["optimizer_steps"] * 2 * HORIZON
            if "interrupted_update" in summary:
                counts["backward_calls"] = None
                counts["replayed_actor_agent_steps"] = None
                counts["critic_update_rows"] = None
                summary["unavailable_measurements"] = [
                    "exact backward calls across the interrupted update",
                    "exact replayed actor-agent steps across the interrupted update",
                    "exact critic update rows across the interrupted update",
                ]
            summary["primary"] = final_panel(rows, recipe)
            if scientific_path_complete and summary["primary"]["complete"]:
                summary["status"] = "complete"
            if initial is not None and actor is not None and critic is not None:
                try:
                    summary["exposure"] = shared.geometry_exposure(initial, actor, critic)
                except Exception as error:
                    summary["limits"].append(f"exposure publication: {type(error).__name__}: {error}")
            summary["training_rows"] = sum(row.get("phase") == "train" for row in rows)
            summary["evaluation_rows"] = sum(row.get("phase") == "eval" for row in rows)
            summary["intervention_by_checkpoint_rule"] = {
                str(checkpoint): {
                    arm: {key: sum(row.get(key, 0) for row in rows
                                   if row.get("phase") == "eval"
                                   and row.get("checkpoint_episode") == checkpoint
                                   and row.get("arm") == arm)
                          for key in ("opportunities", "retrace", "dwell", "apply", "distinguishable")}
                    for arm in ARMS
                } for checkpoint in CHECKPOINTS
            }
            summary["process_wall_s_to_summary"] = time.monotonic() - process_start
            summary["timing_boundary"] = (
                "Runner timing starts before imports and is sampled immediately before summary "
                "serialization; GNU time encloses admission-adjacent execution through actual exit."
            )
            if summary["process_wall_s_to_summary"] >= execution_seconds:
                summary["status"] = "incomplete"
                summary.setdefault("error", f"TimeoutError: {OBJECT} remaining process timeout reached")
            cleaned = shared.clean_json(summary, summary["limits"])
            try:
                shared.write_json(output / "summary.json", cleaned)
            except Exception as error:
                summary["status"] = "publication_failed"
                summary["limits"].append(f"publication: {type(error).__name__}: {error}")
                shared.write_json(output / "summary.json", shared.clean_json(summary, summary["limits"]))
    return 0 if summary["status"] == "complete" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=[MASTER], default=MASTER)
    parser.add_argument("--recipe", choices=list(RECIPES), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--execution-seconds", type=float, required=True)
    args = parser.parse_args(argv)
    return run(args.output, args.launch_sha, PROCESS_START, args.execution_seconds, args.recipe)


if __name__ == "__main__":
    raise SystemExit(main())
