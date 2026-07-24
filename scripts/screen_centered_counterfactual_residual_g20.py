"""Run the bounded paired G20 active-set-centered counterfactual residual screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.centered_residual_g20 import (
    CenteredRosterTrajectory,
    FastCenteredCounterfactualResidualPolicy,
    attach_slow_credit,
    maximum_state_difference,
    optimize_delayed_update,
    optimize_fast_update,
)
from ha_ctse_process.separated_credit_g18 import evaluate_battery_policy
from scripts import run_continuous_service_roster_proxy_g17 as g17_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = "ACTIVE_SET_CENTERED_COUNTERFACTUAL_RESIDUAL_G20"
GAMMA = 0.99
HIDDEN_DIM = 32
LEARNING_RATE = 1e-3
INITIAL_LOG_STD = -1.0
PPO_PASSES = 2
NUM_ENVS = 8
G17_FAST_UPDATES = 100
G17_DELAYED_UPDATES = 100
G18_FAST_UPDATES = 100
G18_DELAYED_UPDATES = 300
G17_EVAL_EPISODES = 48
G18_SLOT_PERMUTATIONS = 3

SEEDS = {
    "g17": {
        "model": 2_619_000,
        "ledger": 2_629_000,
        "action": 2_639_000,
        "evaluation_ledger": 2_649_000,
        "evaluation_action": 2_659_000,
    },
    "g18": {"model": 2_719_000, "action": 2_739_000},
}

REPLAY_TOLERANCE = 1e-6
CENTERING_TOLERANCE = 1e-6
G17_UTILITY_FLOOR = 0.90
G17_GAIN_FLOOR = 0.10
G17_MINIMUM_EPISODE_FLOOR = 0.80
G17_CORRELATION_FLOOR = 0.90
G17_MAE_CEILING = 0.05
G18_UTILITY_FLOOR = 0.95
G18_GAIN_FLOOR = 0.10
G18_SPIKE_UTILITY_FLOOR = 0.90
G18_ROTATING_EFFORT_SHARE_FLOOR = 0.75

INVALID_BRANCH = "INVALID_CENTERED_COUNTERFACTUAL_RESIDUAL_G20"
NO_G17_BRANCH = "NONFORMAL_NO_G17_COMPATIBILITY_CENTERED_RESIDUAL_G20"
NO_G18_ACCESS_BRANCH = "NONFORMAL_NO_DELAYED_ACCESS_CENTERED_RESIDUAL_G20"
NO_G18_MECHANISM_BRANCH = "NONFORMAL_NO_DELAYED_MECHANISM_CENTERED_RESIDUAL_G20"
PROMISING_BRANCH = "NONFORMAL_CENTERED_COUNTERFACTUAL_RESIDUAL_PROMISING_G20"

if len(battery_source.GATE_SLOT_ORDERS) != G18_SLOT_PERMUTATIONS:
    raise ValueError("G20 screen slot-permutation count differs from the frozen design")


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
        "critic_optimizer": "adam",
        "delayed_residual_initialization": "exact_zero_output",
        "delayed_credit_rule": "member_resolved_leave_one_out_counterfactual",
        "delayed_centering_rule": "active_set_exact",
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
    raise ValueError(f"unknown G20 source: {source}")


def make_model(source: str) -> FastCenteredCounterfactualResidualPolicy:
    observation_dim, critic_state_dim, capacity, action_dim = _dimensions(source)
    model = FastCenteredCounterfactualResidualPolicy(
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


def _battery_action_noise(
    episode_ids: Iterable[int], *, action_seed: int
) -> np.ndarray:
    rows = []
    for episode_id in episode_ids:
        rng = np.random.default_rng(
            np.random.SeedSequence([int(action_seed), int(episode_id), 380])
        )
        rows.append(
            rng.standard_normal(
                (
                    battery_source.HORIZON,
                    battery_source.CAPACITY,
                    battery_source.ACTION_DIM,
                )
            ).astype(np.float32)
        )
    if not rows:
        raise ValueError("G20 battery collection requires an episode")
    return np.stack(rows, axis=1)


def collect_battery_trajectory(
    model: FastCenteredCounterfactualResidualPolicy,
    *,
    episode_ids: Iterable[int],
    action_seed: int,
    device: torch.device,
    deterministic: bool = False,
) -> CenteredRosterTrajectory:
    ids = tuple(int(value) for value in episode_ids)
    if not ids:
        raise ValueError("G20 battery collection requires at least one episode")
    ledgers = tuple(
        battery_source.make_ledger(
            battery_source.GATE_SLOT_ORDERS[
                episode_id % len(battery_source.GATE_SLOT_ORDERS)
            ]
        )
        for episode_id in ids
    )
    environments = tuple(
        battery_source.BatteryRosterEnv(ledger) for ledger in ledgers
    )
    batch = len(ids)
    noise = _battery_action_noise(ids, action_seed=action_seed)
    hidden = torch.zeros(
        (batch, battery_source.CAPACITY, model.hidden_dim),
        dtype=torch.float32,
        device=device,
    )
    shapes = {
        "observations": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.OBSERVATION_DIM,
        ),
        "active_mask": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
        ),
        "critic_states": (
            battery_source.HORIZON,
            batch,
            battery_source.CRITIC_STATE_DIM,
        ),
        "actions": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        ),
        "pre_tanh_actions": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        ),
        "old_log_probs": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
        ),
        "old_values": (battery_source.HORIZON, batch),
        "rewards": (battery_source.HORIZON, batch),
        "hidden_before": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            model.hidden_dim,
        ),
        "hidden_after": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            model.hidden_dim,
        ),
        "prefix_action_sums": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        ),
    }
    rows: dict[str, torch.Tensor] = {}
    for name, shape in shapes.items():
        dtype = torch.bool if name == "active_mask" else torch.float32
        rows[name] = torch.empty(shape, dtype=dtype)

    model.eval()
    with torch.no_grad():
        for time in range(battery_source.HORIZON):
            views = tuple(environment.observe() for environment in environments)
            observations = torch.as_tensor(
                np.stack([view.observations for view in views]), device=device
            )
            active_mask = torch.as_tensor(
                np.stack([view.active_mask for view in views]), device=device
            )
            critic_states = torch.as_tensor(
                np.stack([view.critic_state for view in views]), device=device
            )
            hidden_before = hidden.clone()
            arguments = {
                "observations": observations,
                "active_mask": active_mask,
                "critic_state": critic_states,
                "hidden": hidden,
            }
            if deterministic:
                output = model.forward_step(**arguments, deterministic=True)
            else:
                output = model.forward_step(
                    **arguments,
                    sampling_noise=torch.as_tensor(noise[time], device=device),
                )
            action_values = output.actions.detach().cpu().numpy()
            rewards = np.empty(batch, dtype=np.float32)
            for index, environment in enumerate(environments):
                reward, _terminal, _info = environment.step(action_values[index])
                rewards[index] = reward
            values = {
                "observations": observations,
                "active_mask": active_mask,
                "critic_states": critic_states,
                "actions": output.actions,
                "pre_tanh_actions": output.pre_tanh_actions,
                "old_log_probs": output.token_log_probs,
                "old_values": output.value,
                "rewards": torch.as_tensor(rewards, device=device),
                "hidden_before": hidden_before,
                "hidden_after": output.next_hidden,
                "prefix_action_sums": output.prefix_action_sums,
            }
            for name, value in values.items():
                rows[name][time].copy_(value.detach().cpu())
            hidden = output.next_hidden

    provisional = SimpleNamespace(
        **rows,
        outcomes=tuple(environment.outcome() for environment in environments),
        ledgers=ledgers,
    )
    return attach_slow_credit(model, provisional, device=device)


def _collect(
    source: str,
    model: FastCenteredCounterfactualResidualPolicy,
    *,
    episode_ids: tuple[int, ...],
) -> CenteredRosterTrajectory:
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
        return attach_slow_credit(model, raw, device=torch.device("cpu"))
    return collect_battery_trajectory(
        model,
        episode_ids=episode_ids,
        action_seed=seeds["action"],
        device=torch.device("cpu"),
    )


def _trajectory_contract_valid(source: str, trajectory: CenteredRosterTrajectory) -> bool:
    inactive_actions = torch.where(
        trajectory.active_mask.unsqueeze(-1),
        torch.zeros_like(trajectory.actions),
        trajectory.actions,
    )
    if int(torch.count_nonzero(inactive_actions)) != 0:
        return False
    if not all(
        bool(torch.isfinite(row).all())
        for row in (
            trajectory.observations,
            trajectory.critic_states,
            trajectory.actions,
            trajectory.pre_tanh_actions,
            trajectory.old_log_probs,
            trajectory.old_values,
            trajectory.old_immediate_baselines,
            trajectory.old_centered_residual,
            trajectory.old_counterfactual_advantage,
            trajectory.rewards,
        )
    ):
        return False
    for ledger, outcome in zip(trajectory.ledgers, trajectory.outcomes):
        if source == "g17":
            if outcome.roster_sizes != ledger.expected_roster_sizes:
                return False
        elif outcome.roster_sizes != (
            4,
            4,
            4,
            4,
            4,
            4,
            2,
            2,
            2,
            2,
            4,
            4,
        ):
            return False
    return True


def _centering_bounds(trajectory: CenteredRosterTrajectory) -> tuple[float, float]:
    residual = trajectory.old_centered_residual
    mask = trajectory.active_mask
    row_sum = residual.sum(dim=-2)
    row_sum_max = float(row_sum.abs().max().item())
    inactive = torch.where(
        mask.unsqueeze(-1), torch.zeros_like(residual), residual
    )
    inactive_max = float(inactive.abs().max().item())
    return row_sum_max, inactive_max


def _g17_evaluate(
    model: FastCenteredCounterfactualResidualPolicy, domain: str
) -> dict[str, Any]:
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
    source: str, model: FastCenteredCounterfactualResidualPolicy
) -> dict[str, Any]:
    if source == "g17":
        return {
            "iid": _g17_evaluate(model, "iid"),
            "heldout": _g17_evaluate(model, "heldout"),
        }
    rows = evaluate_battery_policy(model, device=torch.device("cpu"))
    return {"slot_rows": rows}


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
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=LEARNING_RATE,
    )
    fast_updates, delayed_updates = _phase_updates(source)
    maximum_replay_errors: dict[str, float] = {}
    lifecycle_valid = True
    finite = True
    active_rows = 0
    maximum_centering_row_sum = 0.0
    maximum_inactive_residual_abs = 0.0
    for update in range(fast_updates):
        first_episode = update * NUM_ENVS
        trajectory = _collect(
            source,
            model,
            episode_ids=tuple(range(first_episode, first_episode + NUM_ENVS)),
        )
        lifecycle_valid = lifecycle_valid and _trajectory_contract_valid(
            source, trajectory
        )
        row_sum_max, inactive_max = _centering_bounds(trajectory)
        maximum_centering_row_sum = max(maximum_centering_row_sum, row_sum_max)
        maximum_inactive_residual_abs = max(
            maximum_inactive_residual_abs, inactive_max
        )
        metrics = optimize_fast_update(
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
    residual_optimizer = torch.optim.Adam(
        model.residual_parameters(), lr=LEARNING_RATE
    )
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
        lifecycle_valid = lifecycle_valid and _trajectory_contract_valid(
            source, trajectory
        )
        row_sum_max, inactive_max = _centering_bounds(trajectory)
        maximum_centering_row_sum = max(maximum_centering_row_sum, row_sum_max)
        maximum_inactive_residual_abs = max(
            maximum_inactive_residual_abs, inactive_max
        )
        metrics = optimize_delayed_update(
            model,
            residual_optimizer,
            critic_optimizer,
            trajectory,
            device=torch.device("cpu"),
            ppo_passes=PPO_PASSES,
            gamma=GAMMA,
        )
        finite = finite and bool(metrics["finite_update"])
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
        "maximum_replay_errors": maximum_replay_errors,
        "anchor_maximum_difference": maximum_state_difference(
            anchor_state, model.anchor_state()
        ),
        "residual_output_layer_maximum_absolute_value": (
            model.residual_output_layer_maximum_absolute_value()
        ),
        "maximum_centering_row_sum": float(maximum_centering_row_sum),
        "maximum_inactive_residual_abs": float(maximum_inactive_residual_abs),
        "zero_evaluation": zero_evaluation,
        "anchor_evaluation": anchor_evaluation,
        "final_evaluation": final_evaluation,
        "mapping": mapping,
    }


def _battery_means(evaluation: dict[str, Any]) -> dict[str, float]:
    rows = evaluation["slot_rows"]
    return {
        "utility": float(np.mean([row["utility"] for row in rows])),
        "spike_utility": float(
            np.mean([row["spike_utility"] for row in rows])
        ),
        "rotating_effort_share": float(
            np.mean([row["low_rotating_effort_share"] for row in rows])
        ),
        "minimum_step_utility": float(
            np.min([row["minimum_step_utility"] for row in rows])
        ),
    }


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_source = {row["source"]: row for row in rows}
    g17 = by_source["g17"]
    g18 = by_source["g18"]
    g17_zero = g17["zero_evaluation"]
    g17_anchor = g17["anchor_evaluation"]
    g17_final = g17["final_evaluation"]
    g18_anchor = _battery_means(g18["anchor_evaluation"])
    g18_final = _battery_means(g18["final_evaluation"])
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
        and replay_maximum <= REPLAY_TOLERANCE
        and all(row["anchor_maximum_difference"] == 0.0 for row in rows)
        and all(
            row["residual_output_layer_maximum_absolute_value"] > 0.0
            for row in rows
        )
        and all(
            row["maximum_centering_row_sum"] <= CENTERING_TOLERANCE
            for row in rows
        )
        and all(
            row["maximum_inactive_residual_abs"] == 0.0 for row in rows
        )
    )
    return {
        "operational_valid": bool(operational_valid),
        "maximum_replay_error": float(replay_maximum),
        "maximum_anchor_difference": float(
            max(row["anchor_maximum_difference"] for row in rows)
        ),
        "maximum_centering_row_sum": float(
            max(row["maximum_centering_row_sum"] for row in rows)
        ),
        "maximum_inactive_residual_abs": float(
            max(row["maximum_inactive_residual_abs"] for row in rows)
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
        float(metrics["g17_final_iid_utility"]) >= G17_UTILITY_FLOOR
        and float(metrics["g17_final_heldout_utility"]) >= G17_UTILITY_FLOOR
        and float(metrics["g17_gain"]) >= G17_GAIN_FLOOR
        and float(metrics["g17_minimum_episode"])
        >= G17_MINIMUM_EPISODE_FLOOR
        and float(metrics["g17_effort_correlation"])
        >= G17_CORRELATION_FLOOR
        and float(metrics["g17_mix_correlation"])
        >= G17_CORRELATION_FLOOR
        and float(metrics["g17_effort_mae"]) <= G17_MAE_CEILING
        and float(metrics["g17_mix_mae"]) <= G17_MAE_CEILING
    )
    if not g17_ok:
        return NO_G17_BRANCH
    if not (
        float(metrics["g18_final_utility"]) >= G18_UTILITY_FLOOR
        and float(metrics["g18_gain_over_anchor"]) >= G18_GAIN_FLOOR
        and float(metrics["g18_spike_utility"])
        >= G18_SPIKE_UTILITY_FLOOR
    ):
        return NO_G18_ACCESS_BRANCH
    if (
        float(metrics["g18_rotating_effort_share"])
        < G18_ROTATING_EFFORT_SHARE_FLOOR
    ):
        return NO_G18_MECHANISM_BRANCH
    return PROMISING_BRANCH


def run_screen(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    if not source_commit or source_commit == "NONFORMAL_WORKTREE":
        raise ValueError("G20 screen requires an integrated source commit")
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
