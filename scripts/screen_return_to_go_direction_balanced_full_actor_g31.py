"""Run the bounded paired G31 return-to-go direction screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.anchored_residual_g19 import (
    attach_credit_baselines,
    maximum_state_difference,
    optimize_fast_anchor_update,
)
from ha_ctse_process.return_to_go_direction_balanced_full_actor_g31 import (
    ReturnToGoDirectionBalancedFullActorPolicy,
    optimize_return_to_go_direction_balanced_update,
)
from ha_ctse_process.separated_credit_g18 import (
    collect_battery_trajectory,
    evaluate_battery_policy,
)
from scripts import run_continuous_service_roster_proxy_g17 as g17_runner
from scripts import screen_direction_balanced_full_actor_g30 as g30_screen


SCHEMA_VERSION = 1
ALGORITHM_ID = "RETURN_TO_GO_DIRECTION_BALANCED_FULL_ACTOR_G31"
GAMMA = g30_screen.GAMMA
HIDDEN_DIM = g30_screen.HIDDEN_DIM
LEARNING_RATE = g30_screen.LEARNING_RATE
INITIAL_LOG_STD = g30_screen.INITIAL_LOG_STD
PPO_PASSES = g30_screen.PPO_PASSES
NUM_ENVS = g30_screen.NUM_ENVS
G17_FAST_UPDATES = g30_screen.G17_FAST_UPDATES
G17_RETURN_TO_GO_UPDATES = g30_screen.G17_DIRECTION_BALANCED_UPDATES
G18_FAST_UPDATES = g30_screen.G18_FAST_UPDATES
G18_RETURN_TO_GO_UPDATES = g30_screen.G18_DIRECTION_BALANCED_UPDATES
G17_EVAL_EPISODES = g30_screen.G17_EVAL_EPISODES

SEEDS = {
    "g17": {
        "model": 9_119_000,
        "ledger": 9_129_000,
        "action": 9_139_000,
        "evaluation_ledger": 9_149_000,
        "evaluation_action": 9_159_000,
    },
    "g18": {"model": 9_219_000, "action": 9_239_000},
}

REPLAY_TOLERANCE = g30_screen.REPLAY_TOLERANCE
DIRECTION_DOT_TOLERANCE = g30_screen.DIRECTION_DOT_TOLERANCE
IDENTITY_TOLERANCE = g30_screen.IDENTITY_TOLERANCE

INVALID_BRANCH = "INVALID_RETURN_TO_GO_DIRECTION_BALANCED_G31"
NO_G17_BRANCH = "NONFORMAL_NO_G17_COMPATIBILITY_RETURN_TO_GO_G31"
NO_G18_ACCESS_BRANCH = "NONFORMAL_NO_DELAYED_ACCESS_RETURN_TO_GO_G31"
NO_G18_MECHANISM_BRANCH = "NONFORMAL_NO_DELAYED_MECHANISM_RETURN_TO_GO_G31"
PROMISING_BRANCH = "NONFORMAL_RETURN_TO_GO_DIRECTION_BALANCED_PROMISING_G31"


def _configuration() -> dict[str, Any]:
    return {
        "gamma": GAMMA,
        "hidden_dim": HIDDEN_DIM,
        "learning_rate": LEARNING_RATE,
        "initial_log_std": INITIAL_LOG_STD,
        "ppo_passes": PPO_PASSES,
        "num_envs": NUM_ENVS,
        "g17_fast_updates": G17_FAST_UPDATES,
        "g17_return_to_go_updates": G17_RETURN_TO_GO_UPDATES,
        "g18_fast_updates": G18_FAST_UPDATES,
        "g18_return_to_go_updates": G18_RETURN_TO_GO_UPDATES,
        "g17_eval_episodes": G17_EVAL_EPISODES,
        "successor_actor_target": (
            "detached_discounted_realized_future_tail_excluding_current"
        ),
        "slow_critic_target": "full_discounted_return_including_current",
        "actor_gradient_rule": "equal_global_unit_gradient_directions",
        "actor_global_rescale": "none_existing_gradient_clip_only",
        "actor_optimizer_state_rule": "ordinary_adam_on_applied_direction",
        "future_actor_input": "none_training_target_only",
        "checkpoint_identity": "fresh_no_g30_resume",
        "residual": "exact_zero_frozen",
    }


def make_model(source: str) -> ReturnToGoDirectionBalancedFullActorPolicy:
    observation_dim, critic_state_dim, capacity, action_dim = (
        g30_screen.g19_screen._dimensions(source)
    )
    model = ReturnToGoDirectionBalancedFullActorPolicy(
        observation_dim,
        critic_state_dim,
        member_capacity=capacity,
        action_dim=action_dim,
        hidden_dim=HIDDEN_DIM,
        current_observation_residual=True,
    )
    with torch.no_grad():
        model.log_std.fill_(INITIAL_LOG_STD)
    return model


def _collect(
    source: str,
    model: ReturnToGoDirectionBalancedFullActorPolicy,
    *,
    episode_ids: tuple[int, ...],
):
    seeds = SEEDS[source]
    if source == "g17":
        raw = g17_source.collect_trajectory(
            model,
            episode_ids=episode_ids,
            ledger_seed=seeds["ledger"],
            action_seed=seeds["action"],
            device=torch.device("cpu"),
            profiles=g17_source.TRAIN_PROFILES,
        )
        return attach_credit_baselines(
            model, raw, device=torch.device("cpu")
        )
    return collect_battery_trajectory(
        model,
        episode_ids=episode_ids,
        action_seed=seeds["action"],
        device=torch.device("cpu"),
    )


def _g17_evaluate(
    model: ReturnToGoDirectionBalancedFullActorPolicy, domain: str
) -> dict[str, float]:
    profiles = (
        g17_source.TRAIN_PROFILES
        if domain == "iid"
        else g17_source.HELDOUT_PROFILES
    )
    outcomes = g17_source.evaluate_policy(
        model,
        episode_ids=range(G17_EVAL_EPISODES),
        ledger_seed=SEEDS["g17"]["evaluation_ledger"],
        action_seed=SEEDS["g17"]["evaluation_action"],
        device=torch.device("cpu"),
        profiles=profiles,
        deterministic=True,
    )
    utilities = [float(row.utility) for row in outcomes]
    return {
        "utility_mean": float(np.mean(utilities)),
        "minimum_episode": float(np.min(utilities)),
    }


def _evaluate_phase(
    source: str, model: ReturnToGoDirectionBalancedFullActorPolicy
) -> dict[str, Any]:
    if source == "g17":
        return {
            "iid": _g17_evaluate(model, "iid"),
            "heldout": _g17_evaluate(model, "heldout"),
        }
    return {
        "slot_rows": evaluate_battery_policy(
            model, device=torch.device("cpu")
        )
    }


def _phase_updates(source: str) -> tuple[int, int]:
    if source == "g17":
        return G17_FAST_UPDATES, G17_RETURN_TO_GO_UPDATES
    return G18_FAST_UPDATES, G18_RETURN_TO_GO_UPDATES


def _actor_state(
    model: ReturnToGoDirectionBalancedFullActorPolicy,
) -> dict[str, torch.Tensor]:
    names = set(model.full_actor_parameter_names())
    return {
        name: parameter.detach().cpu().clone()
        for name, parameter in model.policy.named_parameters()
        if name in names
    }


def _train_source(source: str) -> dict[str, Any]:
    seeds = SEEDS[source]
    g17_runner.configure_runtime(seeds["model"])
    model = make_model(source)
    zero_evaluation = _evaluate_phase(source, model)
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters()
        + tuple(model.credit_baselines.parameters()),
        lr=LEARNING_RATE,
    )
    fast_updates, return_to_go_updates = _phase_updates(source)
    maximum_replay_errors: dict[str, float] = {}
    lifecycle_valid = True
    finite = True
    active_rows = 0
    for update in range(fast_updates):
        first_episode = update * NUM_ENVS
        trajectory = _collect(
            source,
            model,
            episode_ids=tuple(
                range(first_episode, first_episode + NUM_ENVS)
            ),
        )
        lifecycle_valid = (
            lifecycle_valid
            and g30_screen.g19_screen._trajectory_contract_valid(
                source, trajectory
            )
        )
        metrics = optimize_fast_anchor_update(
            model,
            fast_optimizer,
            trajectory,
            device=torch.device("cpu"),
            ppo_passes=PPO_PASSES,
        )
        finite = finite and bool(metrics["finite_update"])
        for name, value in metrics.items():
            if name.endswith("_error") or name.endswith("_max_abs"):
                maximum_replay_errors[name] = max(
                    maximum_replay_errors.get(name, 0.0), float(value)
                )
        active_rows += trajectory.active_token_count
    anchor_evaluation = _evaluate_phase(source, model)
    direction_start = _actor_state(model)
    model.begin_direction_balanced_phase()
    ownership_valid = g30_screen._optimizer_ownership_valid(model)
    actor_optimizer = torch.optim.Adam(
        model.full_actor_parameters(), lr=LEARNING_RATE
    )
    critic_optimizer = torch.optim.Adam(
        model.critic_parameters(), lr=LEARNING_RATE
    )
    minimum_direction_dot = float("inf")
    maximum_identity_error = 0.0
    minimum_step_increment = float("inf")
    maximum_return_to_go_target = 0.0
    maximum_terminal_tail_error = 0.0
    for update in range(return_to_go_updates):
        first_episode = (fast_updates + update) * NUM_ENVS
        trajectory = _collect(
            source,
            model,
            episode_ids=tuple(
                range(first_episode, first_episode + NUM_ENVS)
            ),
        )
        lifecycle_valid = (
            lifecycle_valid
            and g30_screen.g19_screen._trajectory_contract_valid(
                source, trajectory
            )
        )
        metrics = optimize_return_to_go_direction_balanced_update(
            model,
            actor_optimizer,
            critic_optimizer,
            trajectory,
            device=torch.device("cpu"),
            ppo_passes=PPO_PASSES,
            gamma=GAMMA,
        )
        finite = finite and bool(metrics["finite_update"])
        minimum_direction_dot = min(
            minimum_direction_dot,
            float(metrics["minimum_direction_immediate_dot"]),
        )
        maximum_identity_error = max(
            maximum_identity_error,
            float(metrics["maximum_direction_composition_identity_error"]),
        )
        minimum_step_increment = min(
            minimum_step_increment,
            float(metrics["minimum_actor_optimizer_step_increment"]),
        )
        maximum_return_to_go_target = max(
            maximum_return_to_go_target,
            float(metrics["maximum_return_to_go_target_absolute_value"]),
        )
        maximum_terminal_tail_error = max(
            maximum_terminal_tail_error,
            float(metrics["terminal_return_to_go_error"]),
        )
        for name, value in metrics.items():
            if name.endswith("_error") or name.endswith("_max_abs"):
                maximum_replay_errors[name] = max(
                    maximum_replay_errors.get(name, 0.0), float(value)
                )
        active_rows += trajectory.active_token_count
    final_evaluation = _evaluate_phase(source, model)
    mapping = None
    if source == "g17":
        mapping = g17_runner._mapping_diagnostic(
            model,
            episode_ids=tuple(range(G17_EVAL_EPISODES)),
            ledger_seed=seeds["evaluation_ledger"],
        )
    actor_difference = maximum_state_difference(
        direction_start, _actor_state(model)
    )
    return {
        "source": source,
        "seeds": seeds,
        "fast_updates": fast_updates,
        "return_to_go_updates": return_to_go_updates,
        "optimizer_steps": 2
        * (fast_updates + 2 * return_to_go_updates),
        "active_rows": int(active_rows),
        "finite_updates": bool(finite),
        "lifecycle_contract_valid": bool(lifecycle_valid),
        "optimizer_ownership_valid": bool(ownership_valid),
        "maximum_replay_errors": maximum_replay_errors,
        "anchor_maximum_difference": float(actor_difference),
        "actor_maximum_difference": float(actor_difference),
        "residual_output_layer_maximum_absolute_value": (
            model.residual_output_layer_maximum_absolute_value()
        ),
        "minimum_direction_immediate_dot": float(minimum_direction_dot),
        "maximum_direction_composition_identity_error": float(
            maximum_identity_error
        ),
        "minimum_actor_optimizer_step_increment": float(
            minimum_step_increment
        ),
        "maximum_return_to_go_target_absolute_value": float(
            maximum_return_to_go_target
        ),
        "maximum_terminal_return_to_go_error": float(
            maximum_terminal_tail_error
        ),
        "zero_evaluation": zero_evaluation,
        "anchor_evaluation": anchor_evaluation,
        "final_evaluation": final_evaluation,
        "mapping": mapping,
    }


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = g30_screen._metrics(rows)
    metrics.update(
        {
            "maximum_return_to_go_target_absolute_value": float(
                max(
                    row["maximum_return_to_go_target_absolute_value"]
                    for row in rows
                )
            ),
            "maximum_terminal_return_to_go_error": float(
                max(
                    row["maximum_terminal_return_to_go_error"]
                    for row in rows
                )
            ),
        }
    )
    metrics["operational_valid"] = bool(
        metrics["operational_valid"]
        and np.isfinite(metrics["maximum_return_to_go_target_absolute_value"])
        and metrics["maximum_return_to_go_target_absolute_value"] > 0.0
        and metrics["maximum_terminal_return_to_go_error"] == 0.0
    )
    return metrics


def select_result_branch(metrics: dict[str, Any]) -> str:
    branch = g30_screen.g19_screen.select_result_branch(metrics)
    return {
        g30_screen.g19_screen.INVALID_BRANCH: INVALID_BRANCH,
        g30_screen.g19_screen.NO_G17_BRANCH: NO_G17_BRANCH,
        g30_screen.g19_screen.NO_G18_ACCESS_BRANCH: NO_G18_ACCESS_BRANCH,
        g30_screen.g19_screen.NO_G18_MECHANISM_BRANCH: NO_G18_MECHANISM_BRANCH,
        g30_screen.g19_screen.PROMISING_BRANCH: PROMISING_BRANCH,
    }[branch]


def run_screen(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    if not source_commit or source_commit == "NONFORMAL_WORKTREE":
        raise ValueError("G31 screen requires an integrated source commit")
    run_root.mkdir(parents=True, exist_ok=False)
    g17_runner.configure_runtime(SEEDS["g17"]["model"])
    started = time.perf_counter()
    source_rows = [_train_source(source) for source in ("g17", "g18")]
    metrics = _metrics(source_rows)
    source_controls = {
        "g17": g17_runner._source_controls(),
        "g18": battery_source.run_information_gate(),
    }
    metrics["operational_valid"] = bool(
        metrics["operational_valid"]
        and source_controls["g17"]["constructive_access_valid"]
        and source_controls["g17"]["all_schedules_exact"]
        and source_controls["g18"]["branch"] == battery_source.PASS_BRANCH
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "screen",
        "status": "COMPLETE",
        "formal": False,
        "source_commit": source_commit,
        "runtime": g30_screen.g19_screen._runtime_identity(),
        "configuration": _configuration(),
        "source_controls": source_controls,
        "source_results": source_rows,
        "metrics": metrics,
        "branch": select_result_branch(metrics),
        "wall_seconds": float(time.perf_counter() - started),
    }
    g30_screen.g19_screen._write_json(run_root / "result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    arguments = parser.parse_args()
    result = run_screen(
        run_root=arguments.run_root,
        source_commit=arguments.source_commit,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
