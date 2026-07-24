"""Run the bounded paired G23 anchored dual-channel residual screen."""

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
from ha_ctse_process.dual_channel_residual_g23 import (
    AnchoredDualChannelResidualPolicy,
    optimize_dual_channel_delayed_update,
)
from ha_ctse_process.separated_credit_g18 import (
    collect_battery_trajectory,
    evaluate_battery_policy,
)
from scripts import run_continuous_service_roster_proxy_g17 as g17_runner
from scripts import screen_fast_policy_anchored_residual_g19 as g19


SCHEMA_VERSION = 1
ALGORITHM_ID = "ANCHORED_DUAL_CHANNEL_RESIDUAL_G23"
GAMMA = g19.GAMMA
HIDDEN_DIM = g19.HIDDEN_DIM
LEARNING_RATE = g19.LEARNING_RATE
INITIAL_LOG_STD = g19.INITIAL_LOG_STD
PPO_PASSES = g19.PPO_PASSES
NUM_ENVS = g19.NUM_ENVS
G17_FAST_UPDATES = g19.G17_FAST_UPDATES
G17_DELAYED_UPDATES = g19.G17_DELAYED_UPDATES
G18_FAST_UPDATES = g19.G18_FAST_UPDATES
G18_DELAYED_UPDATES = g19.G18_DELAYED_UPDATES
G17_EVAL_EPISODES = g19.G17_EVAL_EPISODES

SEEDS = {
    "g17": {
        "model": 3_219_000,
        "ledger": 3_229_000,
        "action": 3_239_000,
        "evaluation_ledger": 3_249_000,
        "evaluation_action": 3_259_000,
    },
    "g18": {"model": 3_319_000, "action": 3_339_000},
}

INVALID_BRANCH = "INVALID_ANCHORED_DUAL_CHANNEL_RESIDUAL_G23"
NO_G17_BRANCH = "NONFORMAL_NO_G17_COMPATIBILITY_DUAL_CHANNEL_RESIDUAL_G23"
NO_G18_ACCESS_BRANCH = "NONFORMAL_NO_DELAYED_ACCESS_DUAL_CHANNEL_RESIDUAL_G23"
NO_G18_MECHANISM_BRANCH = "NONFORMAL_NO_DELAYED_MECHANISM_DUAL_CHANNEL_RESIDUAL_G23"
PROMISING_BRANCH = "NONFORMAL_ANCHORED_DUAL_CHANNEL_RESIDUAL_PROMISING_G23"


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _runtime_identity() -> dict[str, Any]:
    return {
        "backend": "cpu",
        "torch": str(torch.__version__),
        "torch_threads": int(torch.get_num_threads()),
        "python": str(Path(sys.executable).resolve()),
    }


def _configuration() -> dict[str, Any]:
    return {
        "gamma": GAMMA,
        "hidden_dim": HIDDEN_DIM,
        "learning_rate": LEARNING_RATE,
        "initial_log_std": INITIAL_LOG_STD,
        "ppo_passes": PPO_PASSES,
        "num_envs": NUM_ENVS,
        "g17_fast_updates": G17_FAST_UPDATES,
        "g17_delayed_updates": G17_DELAYED_UPDATES,
        "g18_fast_updates": G18_FAST_UPDATES,
        "g18_delayed_updates": G18_DELAYED_UPDATES,
        "g17_eval_episodes": G17_EVAL_EPISODES,
        "fast_optimizer": "adam",
        "delayed_residual_optimizer": "adam",
        "delayed_residual_adam_betas": [0.9, 0.999],
        "delayed_residual_adam_eps": 1e-8,
        "delayed_residual_weight_decay": 0.0,
        "delayed_residual_amsgrad": False,
        "critic_optimizer": "adam",
        "delayed_residual_initialization": "exact_zero_output",
        "delayed_residual_geometry": "unconstrained_pre_squash_mean",
        "delayed_gradient_rule": "equal_normalized_immediate_successor",
        "immediate_channel_weight": 0.5,
        "successor_channel_weight": 0.5,
        "delayed_residual_entropy_coefficient": 0.0,
    }


def _dimensions(source: str) -> tuple[int, int, int, int]:
    if source == "g17":
        return (
            g17_source.OBSERVATION_DIM,
            g17_source.CRITIC_STATE_DIM,
            g17_source.CAPACITY,
            g17_source.ACTION_DIM,
        )
    if source == "g18":
        return (
            battery_source.OBSERVATION_DIM,
            battery_source.CRITIC_STATE_DIM,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        )
    raise ValueError(f"unknown G23 source: {source}")


def make_model(source: str) -> AnchoredDualChannelResidualPolicy:
    observation_dim, critic_state_dim, capacity, action_dim = _dimensions(source)
    model = AnchoredDualChannelResidualPolicy(
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


def make_residual_optimizer(
    model: AnchoredDualChannelResidualPolicy,
) -> torch.optim.Adam:
    return torch.optim.Adam(
        model.residual_parameters(),
        lr=LEARNING_RATE,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0,
        amsgrad=False,
    )


def _collect(
    source: str,
    model: AnchoredDualChannelResidualPolicy,
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
    model: AnchoredDualChannelResidualPolicy, domain: str
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
    source: str, model: AnchoredDualChannelResidualPolicy
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
        return G17_FAST_UPDATES, G17_DELAYED_UPDATES
    return G18_FAST_UPDATES, G18_DELAYED_UPDATES


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
    fast_updates, delayed_updates = _phase_updates(source)
    maximum_replay_errors: dict[str, float] = {}
    maximum_channel_loss_identity_error = 0.0
    channel_weights_valid = True
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
        lifecycle_valid = lifecycle_valid and g19._trajectory_contract_valid(
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
    anchor_state = model.anchor_state()
    model.begin_delayed_phase()
    residual_optimizer = make_residual_optimizer(model)
    critic_optimizer = torch.optim.Adam(
        model.critic_parameters(), lr=LEARNING_RATE
    )
    for update in range(delayed_updates):
        first_episode = (fast_updates + update) * NUM_ENVS
        trajectory = _collect(
            source,
            model,
            episode_ids=tuple(range(first_episode, first_episode + NUM_ENVS)),
        )
        lifecycle_valid = lifecycle_valid and g19._trajectory_contract_valid(
            source, trajectory
        )
        metrics = optimize_dual_channel_delayed_update(
            model,
            residual_optimizer,
            critic_optimizer,
            trajectory,
            device=torch.device("cpu"),
            ppo_passes=PPO_PASSES,
            gamma=GAMMA,
        )
        finite = finite and bool(metrics["finite_update"])
        channel_weights_valid = channel_weights_valid and (
            metrics["immediate_channel_weight"] == 0.5
            and metrics["successor_channel_weight"] == 0.5
        )
        maximum_channel_loss_identity_error = max(
            maximum_channel_loss_identity_error,
            abs(
                metrics["policy_loss"]
                - 0.5
                * (
                    metrics["immediate_policy_loss"]
                    + metrics["successor_policy_loss"]
                )
            ),
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
    return {
        "source": source,
        "seeds": seeds,
        "fast_updates": fast_updates,
        "delayed_updates": delayed_updates,
        "optimizer_steps": 2 * (fast_updates + 2 * delayed_updates),
        "active_rows": int(active_rows),
        "finite_updates": bool(finite),
        "lifecycle_contract_valid": bool(lifecycle_valid),
        "channel_weights_valid": bool(channel_weights_valid),
        "maximum_channel_loss_identity_error": float(
            maximum_channel_loss_identity_error
        ),
        "maximum_replay_errors": maximum_replay_errors,
        "anchor_maximum_difference": maximum_state_difference(
            anchor_state, model.anchor_state()
        ),
        "residual_output_layer_maximum_absolute_value": (
            model.residual_output_layer_maximum_absolute_value()
        ),
        "zero_evaluation": zero_evaluation,
        "anchor_evaluation": anchor_evaluation,
        "final_evaluation": final_evaluation,
        "mapping": mapping,
    }


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_source = {row["source"]: row for row in rows}
    g17 = by_source["g17"]
    g18 = by_source["g18"]
    g17_zero = g17["zero_evaluation"]
    g17_anchor = g17["anchor_evaluation"]
    g17_final = g17["final_evaluation"]
    g18_anchor = g19._battery_means(g18["anchor_evaluation"])
    g18_final = g19._battery_means(g18["final_evaluation"])
    mapping = g17["mapping"]
    assert isinstance(mapping, dict)
    replay_maximum = max(
        value
        for row in rows
        for value in row["maximum_replay_errors"].values()
    )
    operational_valid = (
        all(row["finite_updates"] for row in rows)
        and all(row["lifecycle_contract_valid"] for row in rows)
        and all(row["channel_weights_valid"] for row in rows)
        and all(
            row["maximum_channel_loss_identity_error"] <= 1e-7
            for row in rows
        )
        and replay_maximum <= g19.REPLAY_TOLERANCE
        and all(row["anchor_maximum_difference"] == 0.0 for row in rows)
        and all(
            row["residual_output_layer_maximum_absolute_value"] > 0.0
            for row in rows
        )
    )
    return {
        "operational_valid": bool(operational_valid),
        "maximum_replay_error": float(replay_maximum),
        "maximum_anchor_difference": float(
            max(row["anchor_maximum_difference"] for row in rows)
        ),
        "maximum_channel_loss_identity_error": float(
            max(row["maximum_channel_loss_identity_error"] for row in rows)
        ),
        "g17_zero_iid_utility": float(g17_zero["iid"]["utility_mean"]),
        "g17_zero_heldout_utility": float(
            g17_zero["heldout"]["utility_mean"]
        ),
        "g17_anchor_iid_utility": float(g17_anchor["iid"]["utility_mean"]),
        "g17_anchor_heldout_utility": float(
            g17_anchor["heldout"]["utility_mean"]
        ),
        "g17_final_iid_utility": float(g17_final["iid"]["utility_mean"]),
        "g17_final_heldout_utility": float(
            g17_final["heldout"]["utility_mean"]
        ),
        "g17_gain": float(
            min(
                g17_final["iid"]["utility_mean"]
                - g17_zero["iid"]["utility_mean"],
                g17_final["heldout"]["utility_mean"]
                - g17_zero["heldout"]["utility_mean"],
            )
        ),
        "g17_minimum_episode": float(
            min(
                g17_final["iid"]["minimum_episode"],
                g17_final["heldout"]["minimum_episode"],
            )
        ),
        "g17_effort_correlation": float(mapping["effort_correlation"]),
        "g17_mix_correlation": float(mapping["mix_correlation"]),
        "g17_effort_mae": float(mapping["effort_mae"]),
        "g17_mix_mae": float(mapping["mix_mae"]),
        "g18_anchor_utility": g18_anchor["utility"],
        "g18_final_utility": g18_final["utility"],
        "g18_gain_over_anchor": float(
            g18_final["utility"] - g18_anchor["utility"]
        ),
        "g18_spike_utility": g18_final["spike_utility"],
        "g18_rotating_effort_share": g18_final["rotating_effort_share"],
        "g18_minimum_step_utility": g18_final["minimum_step_utility"],
    }


def select_result_branch(metrics: dict[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    g17_ok = (
        float(metrics["g17_final_iid_utility"]) >= g19.G17_UTILITY_FLOOR
        and float(metrics["g17_final_heldout_utility"])
        >= g19.G17_UTILITY_FLOOR
        and float(metrics["g17_gain"]) >= g19.G17_GAIN_FLOOR
        and float(metrics["g17_minimum_episode"])
        >= g19.G17_MINIMUM_EPISODE_FLOOR
        and float(metrics["g17_effort_correlation"])
        >= g19.G17_CORRELATION_FLOOR
        and float(metrics["g17_mix_correlation"])
        >= g19.G17_CORRELATION_FLOOR
        and float(metrics["g17_effort_mae"]) <= g19.G17_MAE_CEILING
        and float(metrics["g17_mix_mae"]) <= g19.G17_MAE_CEILING
    )
    if not g17_ok:
        return NO_G17_BRANCH
    if not (
        float(metrics["g18_final_utility"]) >= g19.G18_UTILITY_FLOOR
        and float(metrics["g18_gain_over_anchor"]) >= g19.G18_GAIN_FLOOR
        and float(metrics["g18_spike_utility"])
        >= g19.G18_SPIKE_UTILITY_FLOOR
    ):
        return NO_G18_ACCESS_BRANCH
    if (
        float(metrics["g18_rotating_effort_share"])
        < g19.G18_ROTATING_EFFORT_SHARE_FLOOR
    ):
        return NO_G18_MECHANISM_BRANCH
    return PROMISING_BRANCH


def run_screen(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    if not source_commit or source_commit == "NONFORMAL_WORKTREE":
        raise ValueError("G23 screen requires an integrated source commit")
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
        "runtime": _runtime_identity(),
        "configuration": _configuration(),
        "source_controls": source_controls,
        "source_results": source_rows,
        "metrics": metrics,
        "branch": select_result_branch(metrics),
        "wall_seconds": float(time.perf_counter() - started),
    }
    _write_json(run_root / "result.json", result)
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
