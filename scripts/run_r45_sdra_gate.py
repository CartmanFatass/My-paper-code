"""Collect and fit the single R45-SDRA reward-off identifiability gate."""

from __future__ import annotations

import argparse
import copy
import math
import os
import random
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np

from r45_sdra import (
    CRITIC_EPOCHS,
    CRITIC_MINIBATCH,
    ENV_STEPS,
    EVAL_EPISODES,
    EXPERIMENT_ID,
    OUTER_UPDATES,
    ROLLOUT_ENVS,
    install_r45_collector,
    rows_to_arrays,
    train_crossfit_critics,
)
from run_r41_official_hmasd_seed import (
    ExternalSummaryWriter,
    atomic_json,
    install_optimizer_counter,
    runtime_manifest,
    selected_arguments,
    source_identity,
)
from run_r43_native_renewal_arm import load_source_checkpoint
from run_r44_frozen_source_nrc_arm import (
    _evaluate_without_rng_effect,
    r44_argument_vector,
    source_state_drift,
    source_state_snapshot,
)


def _module_snapshot(module: Any) -> dict[str, Any]:
    return {
        name: value.detach().cpu().clone()
        for name, value in module.state_dict().items()
    }


def _module_drift(module: Any, before: dict[str, Any]) -> dict[str, float]:
    delta_sq = 0.0
    base_sq = 0.0
    maximum = 0.0
    for name, initial in before.items():
        final = module.state_dict()[name].detach().cpu()
        delta = final - initial
        delta_sq += float(delta.float().pow(2).sum().item())
        base_sq += float(initial.float().pow(2).sum().item())
        maximum = max(maximum, float(delta.abs().max().item()))
    absolute = math.sqrt(delta_sq)
    return {
        "absolute_l2": absolute,
        "relative_l2": absolute / max(math.sqrt(base_sq), 1e-12),
        "max_abs": maximum,
    }


def _trace_equal(left: dict[str, Any], right: dict[str, Any], name: str) -> bool:
    return left[name] == right[name]


def run_gate(
    source_archive: Path,
    source_root: Path,
    source_checkpoint: Path,
    output_root: Path,
    seed: int,
    outer_updates: int = OUTER_UPDATES,
    critic_epochs: int = CRITIC_EPOCHS,
    eval_episodes: int = EVAL_EPISODES,
) -> dict[str, Any]:
    identity_before = source_identity(source_archive, source_root)
    official_entry = source_root / "hmasd" / "scripts" / "train" / "train_alice_and_bob.py"
    if not identity_before["archive_present"] or not official_entry.is_file():
        raise RuntimeError("fresh official HMASD source tree is unavailable")
    if not source_checkpoint.is_file():
        raise RuntimeError(f"R41B checkpoint is missing: {source_checkpoint}")
    sys.path.insert(0, str(source_root))
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("WANDB_MODE", "disabled")

    import torch
    from hmasd.config import get_config
    import hmasd.runner.shared.base_runner as official_base_runner
    from hmasd.runner.shared.alice_and_bob_runner import AliceBobRunner
    from hmasd.scripts.train.train_alice_and_bob import (
        make_eval_env,
        make_train_env,
        parse_args,
    )

    if not torch.cuda.is_available():
        raise RuntimeError("R45 requires CUDA")
    official_base_runner.SummaryWriter = ExternalSummaryWriter
    device = torch.device("cuda:0")
    torch.set_num_threads(8)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    all_args = parse_args(r44_argument_vector(seed, outer_updates), get_config())
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    official_run_dir = output_root / "official_runner"
    official_run_dir.mkdir(parents=True, exist_ok=True)
    all_args.run_dir = official_run_dir
    envs = make_train_env(all_args)
    config = {
        "all_args": all_args,
        "envs": envs,
        "eval_envs": None,
        "num_agents": 2,
        "device": device,
        "run_dir": official_run_dir,
    }
    runner = AliceBobRunner(config)
    environment_contract = {
        "agents": len(envs.action_space),
        "obs": int(envs.observation_space[0][0]),
        "state": int(envs.share_observation_space[0][0]),
        "actions": int(envs.action_space[0].n),
        "horizon": int(all_args.episode_length),
    }
    checkpoint_source = load_source_checkpoint(torch, runner, source_checkpoint)
    initial_source = source_state_snapshot(runner)
    installation = install_r45_collector(runner)
    initial_actor = _module_snapshot(runner.h_policy.transformer.r43_renewal_actor)
    zero_eval = _evaluate_without_rng_effect(
        torch,
        runner,
        make_eval_env,
        all_args,
        seed,
        "r45_sdra_source",
        eval_episodes,
    )

    source_optimizers = {
        "high": runner.h_policy.optimizer,
        "low_actor": runner.l_policy.actor_optimizer,
        "low_critic": runner.l_policy.critic_optimizer,
        "team_discriminator": runner.discri.team_discri_optimizer,
        "individual_discriminator": runner.discri.indi_discri_optimizer,
    }
    source_optimizer_stats = {
        name: install_optimizer_counter(torch, optimizer, name)
        for name, optimizer in source_optimizers.items()
    }
    telemetry: dict[str, Any] = {
        "outer_updates": 0,
        "actual_env_steps": 0,
        "source_optimizers": source_optimizer_stats,
        "renewal_actor_optimizer_steps": 0,
    }
    progress_path = output_root / "progress.json"
    collection_train = runner.train

    def instrumented_train() -> dict[str, Any]:
        train_info = collection_train()
        telemetry["outer_updates"] += 1
        telemetry["actual_env_steps"] = (
            telemetry["outer_updates"]
            * all_args.episode_length
            * all_args.n_rollout_threads
        )
        atomic_json(
            progress_path,
            {
                "state": "collecting",
                "outer_updates": telemetry["outer_updates"],
                "expected_outer_updates": outer_updates,
                "actual_env_steps": telemetry["actual_env_steps"],
                "expected_env_steps": outer_updates * 100 * ROLLOUT_ENVS,
                "env_check_rows": runner.r45_collection_stats["env_check_rows"],
                "normal_factor_rows": runner.r45_collection_stats["factor_rows"],
                "source_optimizer_steps": {
                    name: stats["steps"]
                    for name, stats in source_optimizer_stats.items()
                },
                "renewal_actor_optimizer_steps": 0,
                "updated_unix": time.time(),
            },
        )
        return train_info

    runner.train = instrumented_train
    started = time.time()
    try:
        runner.run()
    finally:
        envs.close()

    final_eval = _evaluate_without_rng_effect(
        torch,
        runner,
        make_eval_env,
        all_args,
        seed,
        "r45_sdra_source",
        eval_episodes,
    )
    frozen_drift = source_state_drift(runner, initial_source)
    actor_drift = _module_drift(
        runner.h_policy.transformer.r43_renewal_actor, initial_actor
    )
    arrays = rows_to_arrays(runner.r45_rows)
    expected_rows = (2 * outer_updates - 1) * ROLLOUT_ENVS * runner.num_agents
    if len(arrays["action"]) != expected_rows:
        raise RuntimeError(
            f"R45 factor rows {len(arrays['action'])}, expected {expected_rows}"
        )

    atomic_json(
        progress_path,
        {
            "state": "critic_training",
            "outer_updates": telemetry["outer_updates"],
            "actual_env_steps": telemetry["actual_env_steps"],
            "normal_factor_rows": len(arrays["action"]),
            "critic_epochs": critic_epochs,
            "updated_unix": time.time(),
        },
    )
    critic_checkpoint, predictions, critic_training = train_crossfit_critics(
        arrays,
        device,
        seed,
        epochs=critic_epochs,
        minibatch=CRITIC_MINIBATCH,
    )
    checkpoint_dir = output_root / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    critic_checkpoint_path = checkpoint_dir / "r45_sdra_critics.pt"
    torch.save(critic_checkpoint, critic_checkpoint_path)
    evidence_path = output_root / "r45_sdra_rows.npz"
    np.savez_compressed(evidence_path, **arrays, **predictions)

    action_counts = {
        f"agent_{agent}": {
            "KEEP": int(((arrays["agent"] == agent) & (arrays["action"] == 0)).sum()),
            "RENEW": int(((arrays["agent"] == agent) & (arrays["action"] == 1)).sum()),
        }
        for agent in range(runner.num_agents)
    }
    source_steps = {
        name: stats["steps"] for name, stats in source_optimizer_stats.items()
    }
    scope = (
        "formal"
        if outer_updates == OUTER_UPDATES
        and critic_epochs == CRITIC_EPOCHS
        and eval_episodes == EVAL_EPISODES
        else "focused_smoke"
    )
    result = {
        "experiment_id": EXPERIMENT_ID,
        "state": "completed",
        "scope": scope,
        "seed": seed,
        "source": {
            "before": identity_before,
            "after": source_identity(source_archive, source_root),
            "fresh_extract": True,
            "checkpoint": checkpoint_source,
        },
        "runtime": runtime_manifest(torch),
        "official_arguments": selected_arguments(all_args),
        "official_argument_vector": r44_argument_vector(seed, outer_updates),
        "environment": environment_contract,
        "algorithm_boundary": {
            "source_algorithm": "frozen_r41b_hmasd_skill_system",
            "controller_clock": "source_global_k50_reset_censored",
            "behavior_policy": "source_exact_zero_renewal_residual",
            "outcome": "discounted_next_50_external_reward_steps",
            "renewal_actor_updates": False,
            "source_optimizer_updates": False,
            "critic_only": True,
            "crossfit": "env_0_7_vs_8_15",
            "true_prediction": "q_observed_action",
            "sham_prediction": "behavior_propensity_mixture",
            "forced_branch": False,
            "simulator_clone": False,
            "extra_shaping": False,
            "extra_intrinsic": False,
            "task_fields_in_context": False,
        },
        "installation": installation,
        "source_frozen_drift": frozen_drift,
        "renewal_actor_drift": actor_drift,
        "telemetry": {
            **telemetry,
            "source_optimizer_steps": source_steps,
        },
        "training_clock": copy.deepcopy(runner.r43_clock_ledger),
        "collection": {
            **copy.deepcopy(runner.r45_collection_stats),
            "rows_path": str(evidence_path),
            "row_count": int(len(arrays["action"])),
            "context_shape": list(arrays["context"].shape),
            "action_counts": action_counts,
            "propensity_renew_min": float(arrays["propensity_renew"].min()),
            "propensity_renew_max": float(arrays["propensity_renew"].max()),
            "outcome_min": float(arrays["outcome"].min()),
            "outcome_max": float(arrays["outcome"].max()),
            "event_count": int(len(np.unique(arrays["event_id"]))),
        },
        "critic_training": critic_training,
        "critic_checkpoint": {
            "path": str(critic_checkpoint_path),
            "schema": critic_checkpoint["schema"],
        },
        "zero_step_evaluation": zero_eval,
        "evaluation": final_eval,
        "exact_trace_equality": {
            "outcomes": all(
                _trace_equal(zero_eval, final_eval, field)
                for field in (
                    "episode_wins",
                    "episode_key0",
                    "episode_key1",
                    "episode_steps",
                )
            ),
            "high_actions": _trace_equal(
                zero_eval, final_eval, "high_action_traces"
            ),
            "low_actions": _trace_equal(zero_eval, final_eval, "low_action_traces"),
        },
        "elapsed_seconds": time.time() - started,
    }
    atomic_json(output_root / "seed_result.json", result)
    atomic_json(
        progress_path,
        {
            "state": "completed",
            "scope": scope,
            "outer_updates": telemetry["outer_updates"],
            "actual_env_steps": telemetry["actual_env_steps"],
            "normal_factor_rows": len(arrays["action"]),
            "critic_optimizer_steps": critic_training["total_optimizer_steps"],
            "win_rate": final_eval["win_rate"],
            "updated_unix": time.time(),
        },
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-archive", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--source-checkpoint", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--outer-updates", type=int, default=OUTER_UPDATES)
    parser.add_argument("--critic-epochs", type=int, default=CRITIC_EPOCHS)
    parser.add_argument("--eval-episodes", type=int, default=EVAL_EPISODES)
    args = parser.parse_args()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    status_path = output_root / "seed_status.json"
    atomic_json(status_path, {"state": "running", "updated_unix": time.time()})
    try:
        result = run_gate(
            Path(args.source_archive).resolve(),
            Path(args.source_root).resolve(),
            Path(args.source_checkpoint).resolve(),
            output_root,
            args.seed,
            args.outer_updates,
            args.critic_epochs,
            args.eval_episodes,
        )
        atomic_json(
            status_path,
            {
                "state": "completed",
                "scope": result["scope"],
                "updated_unix": time.time(),
            },
        )
    except Exception as exc:
        atomic_json(
            status_path,
            {
                "state": "failed",
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "updated_unix": time.time(),
            },
        )
        raise


if __name__ == "__main__":
    main()
