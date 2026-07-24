"""Run the bounded paired G27 immediate-tangent full-actor screen."""

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
from ha_ctse_process.immediate_tangent_full_actor_g27 import (
    ImmediateTangentProtectedFullActorPolicy,
    optimize_tangent_protected_update,
)
from ha_ctse_process.separated_credit_g18 import (
    collect_battery_trajectory,
    evaluate_battery_policy,
)
from scripts import run_continuous_service_roster_proxy_g17 as g17_runner
from scripts import screen_fast_policy_anchored_residual_g19 as g19_screen


SCHEMA_VERSION = 1
ALGORITHM_ID = "IMMEDIATE_TANGENT_PROTECTED_FULL_ACTOR_G27"
GAMMA = g19_screen.GAMMA
HIDDEN_DIM = g19_screen.HIDDEN_DIM
LEARNING_RATE = g19_screen.LEARNING_RATE
INITIAL_LOG_STD = g19_screen.INITIAL_LOG_STD
PPO_PASSES = g19_screen.PPO_PASSES
NUM_ENVS = g19_screen.NUM_ENVS
G17_FAST_UPDATES = g19_screen.G17_FAST_UPDATES
G17_TANGENT_UPDATES = g19_screen.G17_DELAYED_UPDATES
G18_FAST_UPDATES = g19_screen.G18_FAST_UPDATES
G18_TANGENT_UPDATES = g19_screen.G18_DELAYED_UPDATES
G17_EVAL_EPISODES = g19_screen.G17_EVAL_EPISODES

SEEDS = {
    "g17": {
        "model": 3_919_000,
        "ledger": 3_929_000,
        "action": 3_939_000,
        "evaluation_ledger": 3_949_000,
        "evaluation_action": 3_959_000,
    },
    "g18": {"model": 4_019_000, "action": 4_039_000},
}

REPLAY_TOLERANCE = g19_screen.REPLAY_TOLERANCE
PROJECTION_TOLERANCE = 1e-7
IDENTITY_TOLERANCE = 1e-7

INVALID_BRANCH = "INVALID_IMMEDIATE_TANGENT_PROTECTED_FULL_ACTOR_G27"
NO_G17_BRANCH = "NONFORMAL_NO_G17_COMPATIBILITY_TANGENT_FULL_ACTOR_G27"
NO_G18_ACCESS_BRANCH = "NONFORMAL_NO_DELAYED_ACCESS_TANGENT_FULL_ACTOR_G27"
NO_G18_MECHANISM_BRANCH = "NONFORMAL_NO_DELAYED_MECHANISM_TANGENT_FULL_ACTOR_G27"
PROMISING_BRANCH = "NONFORMAL_IMMEDIATE_TANGENT_FULL_ACTOR_PROMISING_G27"


def _configuration() -> dict[str, Any]:
    return {
        "gamma": GAMMA,
        "hidden_dim": HIDDEN_DIM,
        "learning_rate": LEARNING_RATE,
        "initial_log_std": INITIAL_LOG_STD,
        "ppo_passes": PPO_PASSES,
        "num_envs": NUM_ENVS,
        "g17_fast_updates": G17_FAST_UPDATES,
        "g17_tangent_updates": G17_TANGENT_UPDATES,
        "g18_fast_updates": G18_FAST_UPDATES,
        "g18_tangent_updates": G18_TANGENT_UPDATES,
        "g17_eval_episodes": G17_EVAL_EPISODES,
        "fast_optimizer": "adam",
        "tangent_actor_optimizer": "adam",
        "critic_optimizer": "adam",
        "residual": "exact_zero_frozen",
        "actor_gradient_rule": "half_immediate_plus_projected_successor",
    }


def make_model(source: str) -> ImmediateTangentProtectedFullActorPolicy:
    observation_dim, critic_state_dim, capacity, action_dim = (
        g19_screen._dimensions(source)
    )
    model = ImmediateTangentProtectedFullActorPolicy(
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
    model: ImmediateTangentProtectedFullActorPolicy,
    *,
    episode_ids: tuple[int, ...],
) -> Any:
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
    model: ImmediateTangentProtectedFullActorPolicy, domain: str
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
    source: str, model: ImmediateTangentProtectedFullActorPolicy
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
        return G17_FAST_UPDATES, G17_TANGENT_UPDATES
    return G18_FAST_UPDATES, G18_TANGENT_UPDATES


def _actor_state(
    model: ImmediateTangentProtectedFullActorPolicy,
) -> dict[str, torch.Tensor]:
    names = set(model.full_actor_parameter_names())
    return {
        name: parameter.detach().cpu().clone()
        for name, parameter in model.policy.named_parameters()
        if name in names
    }


def _optimizer_ownership_valid(
    model: ImmediateTangentProtectedFullActorPolicy,
) -> bool:
    actor = {id(row) for row in model.full_actor_parameters()}
    critic = {id(row) for row in model.critic_parameters()}
    residual = {id(row) for row in model.residual_parameters()}
    core_critic = {id(row) for row in model.policy.critic.parameters()}
    expected_actor = {
        id(parameter)
        for name, parameter in model.policy.named_parameters()
        if not name.startswith("delayed_residual.")
        and not name.startswith("critic.")
    }
    return bool(
        actor
        and critic
        and actor == expected_actor
        and actor.isdisjoint(critic | residual | core_critic)
        and critic.isdisjoint(residual | core_critic)
        and all(parameter.requires_grad for parameter in model.full_actor_parameters())
        and all(parameter.requires_grad for parameter in model.critic_parameters())
        and all(not parameter.requires_grad for parameter in model.residual_parameters())
        and all(not parameter.requires_grad for parameter in model.policy.critic.parameters())
    )


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
    fast_updates, tangent_updates = _phase_updates(source)
    maximum_replay_errors: dict[str, float] = {}
    lifecycle_valid = True
    finite = True
    active_rows = 0
    for update in range(fast_updates):
        first_episode = update * NUM_ENVS
        trajectory = _collect(
            source,
            model,
            episode_ids=tuple(range(first_episode, first_episode + NUM_ENVS)),
        )
        lifecycle_valid = lifecycle_valid and g19_screen._trajectory_contract_valid(
            source, trajectory
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
    tangent_start = _actor_state(model)
    model.begin_tangent_phase()
    optimizer_ownership_valid = _optimizer_ownership_valid(model)
    actor_optimizer = torch.optim.Adam(
        model.full_actor_parameters(), lr=LEARNING_RATE
    )
    critic_optimizer = torch.optim.Adam(
        model.critic_parameters(), lr=LEARNING_RATE
    )
    minimum_projection_dot = float("inf")
    maximum_identity_error = 0.0
    projection_conflict_passes = 0.0
    for update in range(tangent_updates):
        first_episode = (fast_updates + update) * NUM_ENVS
        trajectory = _collect(
            source,
            model,
            episode_ids=tuple(range(first_episode, first_episode + NUM_ENVS)),
        )
        lifecycle_valid = lifecycle_valid and g19_screen._trajectory_contract_valid(
            source, trajectory
        )
        metrics = optimize_tangent_protected_update(
            model,
            actor_optimizer,
            critic_optimizer,
            trajectory,
            device=torch.device("cpu"),
            ppo_passes=PPO_PASSES,
            gamma=GAMMA,
        )
        finite = finite and bool(metrics["finite_update"])
        minimum_projection_dot = min(
            minimum_projection_dot,
            float(metrics["minimum_projection_post_dot"]),
        )
        maximum_identity_error = max(
            maximum_identity_error,
            float(metrics["maximum_applied_gradient_identity_error"]),
        )
        projection_conflict_passes += (
            float(metrics["projection_conflict"]) * PPO_PASSES
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
        tangent_start, _actor_state(model)
    )
    return {
        "source": source,
        "seeds": seeds,
        "fast_updates": fast_updates,
        "tangent_updates": tangent_updates,
        "optimizer_steps": 2 * (fast_updates + 2 * tangent_updates),
        "active_rows": int(active_rows),
        "finite_updates": bool(finite),
        "lifecycle_contract_valid": bool(lifecycle_valid),
        "optimizer_ownership_valid": bool(optimizer_ownership_valid),
        "maximum_replay_errors": maximum_replay_errors,
        "anchor_maximum_difference": float(actor_difference),
        "actor_maximum_difference": float(actor_difference),
        "residual_output_layer_maximum_absolute_value": (
            model.residual_output_layer_maximum_absolute_value()
        ),
        "minimum_projection_post_dot": float(minimum_projection_dot),
        "maximum_applied_gradient_identity_error": float(
            maximum_identity_error
        ),
        "projection_conflict_passes": float(projection_conflict_passes),
        "zero_evaluation": zero_evaluation,
        "anchor_evaluation": anchor_evaluation,
        "final_evaluation": final_evaluation,
        "mapping": mapping,
    }


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = g19_screen._metrics(rows)
    metrics.pop("maximum_anchor_difference")
    replay_maximum = max(
        value
        for row in rows
        for value in row["maximum_replay_errors"].values()
    )
    metrics.update(
        {
            "maximum_actor_difference": float(
                max(row["actor_maximum_difference"] for row in rows)
            ),
            "minimum_actor_difference": float(
                min(row["actor_maximum_difference"] for row in rows)
            ),
            "maximum_applied_gradient_identity_error": float(
                max(
                    row["maximum_applied_gradient_identity_error"]
                    for row in rows
                )
            ),
        }
    )
    metrics["operational_valid"] = bool(
        all(row["finite_updates"] for row in rows)
        and all(row["lifecycle_contract_valid"] for row in rows)
        and all(row["optimizer_ownership_valid"] for row in rows)
        and replay_maximum <= REPLAY_TOLERANCE
        and all(row["actor_maximum_difference"] > 0.0 for row in rows)
        and all(
            row["residual_output_layer_maximum_absolute_value"] == 0.0
            for row in rows
        )
        and all(
            row["minimum_projection_post_dot"] >= -PROJECTION_TOLERANCE
            for row in rows
        )
        and all(
            row["maximum_applied_gradient_identity_error"]
            <= IDENTITY_TOLERANCE
            for row in rows
        )
    )
    return metrics


def select_result_branch(metrics: dict[str, Any]) -> str:
    branch = g19_screen.select_result_branch(metrics)
    return {
        g19_screen.INVALID_BRANCH: INVALID_BRANCH,
        g19_screen.NO_G17_BRANCH: NO_G17_BRANCH,
        g19_screen.NO_G18_ACCESS_BRANCH: NO_G18_ACCESS_BRANCH,
        g19_screen.NO_G18_MECHANISM_BRANCH: NO_G18_MECHANISM_BRANCH,
        g19_screen.PROMISING_BRANCH: PROMISING_BRANCH,
    }[branch]


def run_screen(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    if not source_commit or source_commit == "NONFORMAL_WORKTREE":
        raise ValueError("G27 screen requires an integrated source commit")
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
        "runtime": g19_screen._runtime_identity(),
        "configuration": _configuration(),
        "source_controls": source_controls,
        "source_results": source_rows,
        "metrics": metrics,
        "branch": select_result_branch(metrics),
        "wall_seconds": float(time.perf_counter() - started),
    }
    g19_screen._write_json(run_root / "result.json", result)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    return parser.parse_args()


def main() -> None:
    arguments = _parse_args()
    result = run_screen(
        run_root=arguments.run_root,
        source_commit=arguments.source_commit,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
