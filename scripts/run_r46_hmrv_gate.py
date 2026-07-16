"""Run the registered standalone R46-HMRV-G0 worker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch

from r46_hmrv import (
    BEHAVIOR_ACTION_SEED,
    CHECKS_PER_EPISODE,
    CRITIC_TOTAL_STEPS,
    ENVIRONMENT_SEED,
    ENV_STEPS,
    EPISODES_PER_ENV,
    EVAL_ACTION_SEED,
    EVAL_EPISODES,
    EXPERIMENT_ID,
    FOCAL_ROWS,
    ROLLOUT_ENVS,
    TOTAL_CHECK_ROWS,
    USABLE_EVENT_ROWS,
    collect_formal_data,
    evaluation_schedule,
    run_evaluation_trace,
    train_crossfit_critics,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.write_text(serialized, encoding="utf-8")


def write_progress(path: Path, phase: str, **values: Any) -> None:
    write_json(path, {"phase": phase, **values})


def trace_equality(
    before: dict[str, np.ndarray], after: dict[str, np.ndarray]
) -> dict[str, bool]:
    return {
        name: bool(np.array_equal(before[name], after[name]))
        for name in (
            "role_assignments",
            "actions",
            "pre_health",
            "post_health",
            "service_output",
            "block_reward",
        )
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    progress_path = output_root / "progress.json"
    result_path = output_root / "seed_result.json"
    evidence_path = output_root / "r46_hmrv_evidence.npz"
    checkpoint_path = output_root / "r46_hmrv_critics.pt"

    if args.device != "cuda":
        raise RuntimeError("R46 formal gate requires CUDA; CPU fallback is prohibited")
    if not torch.cuda.is_available():
        raise RuntimeError("R46 requested CUDA but torch.cuda.is_available() is false")
    device = torch.device("cuda")

    write_progress(progress_path, "collection", environment_steps=0)
    rows, traces = collect_formal_data()
    write_progress(
        progress_path,
        "pre_fit_evaluation",
        environment_steps=ENV_STEPS,
        focal_rows=FOCAL_ROWS,
    )
    eval_roles, eval_actions = evaluation_schedule()
    eval_before = run_evaluation_trace(eval_roles, eval_actions)

    write_progress(
        progress_path,
        "critic_fit",
        environment_steps=ENV_STEPS,
        focal_rows=FOCAL_ROWS,
        critic_optimizer_steps=0,
    )
    checkpoint, predictions, critic_metadata = train_crossfit_critics(rows, device)
    torch.save(checkpoint, checkpoint_path)

    write_progress(
        progress_path,
        "post_fit_evaluation",
        environment_steps=ENV_STEPS,
        focal_rows=FOCAL_ROWS,
        critic_optimizer_steps=critic_metadata["total_optimizer_steps"],
    )
    eval_after = run_evaluation_trace(eval_roles, eval_actions)
    exact_eval = trace_equality(eval_before, eval_after)

    evidence = {
        **rows,
        **traces,
        **predictions,
        "eval_role_assignments": eval_roles,
        "eval_actions": eval_actions,
        "eval_pre_health_before": eval_before["pre_health"],
        "eval_post_health_before": eval_before["post_health"],
        "eval_service_output_before": eval_before["service_output"],
        "eval_block_reward_before": eval_before["block_reward"],
        "eval_pre_health_after": eval_after["pre_health"],
        "eval_post_health_after": eval_after["post_health"],
        "eval_service_output_after": eval_after["service_output"],
        "eval_block_reward_after": eval_after["block_reward"],
    }
    np.savez_compressed(evidence_path, **evidence)

    payload: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "scope": "formal",
        "state": "completed",
        "device": str(device),
        "seeds": {
            "environment": ENVIRONMENT_SEED,
            "behavior_action": BEHAVIOR_ACTION_SEED,
            "evaluation_action": EVAL_ACTION_SEED,
        },
        "telemetry": {
            "rollout_envs": ROLLOUT_ENVS,
            "episodes_per_env": EPISODES_PER_ENV,
            "environment_steps": ENV_STEPS,
            "total_check_rows": TOTAL_CHECK_ROWS,
            "usable_event_rows": USABLE_EVENT_ROWS,
            "focal_rows": FOCAL_ROWS,
            "policy_optimizer_steps": 0,
            "low_optimizer_steps": 0,
            "skill_optimizer_steps": 0,
            "intrinsic_optimizer_steps": 0,
            "critic_optimizer_steps": critic_metadata["total_optimizer_steps"],
        },
        "collection": {
            "context_shape": list(rows["context"].shape),
            "propensity_min": float(rows["propensity_renew"].min()),
            "propensity_max": float(rows["propensity_renew"].max()),
            "behavior_action_replay_mismatch": int(
                np.count_nonzero(
                    rows["action"]
                    != traces["behavior_actions"][
                        rows["env_rank"],
                        rows["episode_index"],
                        rows["check_index"],
                        rows["agent"],
                    ]
                )
            ),
            "zero_reward_blocks": int(np.count_nonzero(traces["block_reward"] == 0.0)),
            "full_service_blocks": int(np.count_nonzero(traces["block_reward"] == 1.0)),
        },
        "critic_training": critic_metadata,
        "evaluation": {
            "episodes": EVAL_EPISODES,
            "checks_per_episode": CHECKS_PER_EPISODE,
            "exact_trace_equality": exact_eval,
            "all_exact": bool(all(exact_eval.values())),
        },
        "algorithm_boundary": {
            "standalone_synthetic_substrate": True,
            "behavior_policy_fixed_bernoulli_half": True,
            "policy_module_exists": False,
            "low_module_exists": False,
            "skill_module_exists": False,
            "intrinsic_reward_exists": False,
            "task_specific_intrinsic_reward": False,
            "critic_only_learning": True,
            "reward_shaping": False,
            "early_stopping": False,
            "model_selection": False,
        },
        "artifacts": {
            "evidence": str(evidence_path),
            "critic_checkpoint": str(checkpoint_path),
        },
    }
    if payload["telemetry"]["critic_optimizer_steps"] != CRITIC_TOTAL_STEPS:
        raise RuntimeError("R46 critic optimizer-step count changed")
    write_json(result_path, payload)
    write_progress(
        progress_path,
        "completed",
        environment_steps=ENV_STEPS,
        focal_rows=FOCAL_ROWS,
        critic_optimizer_steps=CRITIC_TOTAL_STEPS,
        result_path=str(result_path),
    )
    print(f"R46 worker completed: {result_path}")


if __name__ == "__main__":
    main()
