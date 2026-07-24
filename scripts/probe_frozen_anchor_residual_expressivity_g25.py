"""Run the diagnostic-only G25 frozen-anchor residual expressivity gate."""

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

from ha_ctse_process import delayed_battery_roster_g18 as source
from ha_ctse_process.anchored_residual_g19 import (
    FastAnchoredResidualPolicy,
    maximum_state_difference,
    optimize_fast_anchor_update,
)
from ha_ctse_process.separated_credit_g18 import (
    collect_battery_trajectory,
    evaluate_battery_policy,
)
from scripts import run_continuous_service_roster_proxy_g17 as runtime
from scripts import screen_fast_policy_anchored_residual_g19 as g19


SCHEMA_VERSION = 1
ALGORITHM_ID = "FROZEN_ANCHOR_LOCAL_RESIDUAL_EXPRESSIVITY_G25"
MODEL_SEED = 3_619_000
ACTION_SEED = 3_639_000
MINIBATCH_SEED = 3_659_000
FAST_UPDATES = 100
NUM_ENVS = 8
PPO_PASSES = 2
FIT_STEPS = 200
FIT_BATCH_SIZE = 36
LEARNING_RATE = 1e-3
GRADIENT_CLIP = 1.0
ABSOLUTE_MSE_CEILING = 1e-3
RELATIVE_MSE_CEILING = 0.10

INVALID_BRANCH = "INVALID_FROZEN_ANCHOR_RESIDUAL_EXPRESSIVITY_G25"
NO_POINTWISE_BRANCH = "NO_POINTWISE_LOCAL_RESIDUAL_FIT_G25"
NO_CLOSED_LOOP_BRANCH = "NO_CLOSED_LOOP_LOCAL_RESIDUAL_REALIZATION_G25"
PASS_BRANCH = "PASS_FROZEN_ANCHOR_LOCAL_RESIDUAL_EXPRESSIVITY_G25"


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


def make_model() -> FastAnchoredResidualPolicy:
    model = FastAnchoredResidualPolicy(
        source.OBSERVATION_DIM,
        source.CRITIC_STATE_DIM,
        member_capacity=source.CAPACITY,
        action_dim=source.ACTION_DIM,
        hidden_dim=g19.HIDDEN_DIM,
        current_observation_residual=True,
    )
    with torch.no_grad():
        model.log_std.fill_(g19.INITIAL_LOG_STD)
    return model


def constructive_dataset() -> dict[str, Any]:
    tensor_rows: dict[str, list[np.ndarray]] = {
        name: []
        for name in ("observations", "active_mask", "critic_state", "actions")
    }
    order_indices: list[int] = []
    times: list[int] = []
    for order_index, slot_order in enumerate(source.GATE_SLOT_ORDERS):
        environment = source.BatteryRosterEnv(source.make_ledger(slot_order))
        for _ in range(source.HORIZON):
            view = environment.observe()
            actions = source.constructive_actions(view)
            tensor_rows["observations"].append(view.observations)
            tensor_rows["active_mask"].append(view.active_mask)
            tensor_rows["critic_state"].append(view.critic_state)
            tensor_rows["actions"].append(actions)
            order_indices.append(order_index)
            times.append(view.time)
            environment.step(actions)
    return {
        name: torch.as_tensor(np.stack(values))
        for name, values in tensor_rows.items()
    } | {
        "order_indices": tuple(order_indices),
        "times": tuple(times),
    }


def dataset_contract(dataset: dict[str, Any]) -> dict[str, Any]:
    active_mask = dataset["active_mask"]
    actions = dataset["actions"]
    inactive = torch.where(
        active_mask.unsqueeze(-1), torch.zeros_like(actions), actions
    )
    row_count = int(dataset["observations"].shape[0])
    return {
        "row_count": row_count,
        "row_count_exact": row_count
        == len(source.GATE_SLOT_ORDERS) * source.HORIZON,
        "slot_order_counts_exact": all(
            dataset["order_indices"].count(index) == source.HORIZON
            for index in range(len(source.GATE_SLOT_ORDERS))
        ),
        "time_coverage_exact": all(
            tuple(
                time
                for time, order_index in zip(
                    dataset["times"], dataset["order_indices"]
                )
                if order_index == index
            )
            == tuple(range(source.HORIZON))
            for index in range(len(source.GATE_SLOT_ORDERS))
        ),
        "finite": all(
            bool(torch.isfinite(dataset[name]).all())
            for name in ("observations", "critic_state", "actions")
        ),
        "inactive_targets_exact_zero": int(torch.count_nonzero(inactive)) == 0,
    }


def frozen_state(model: FastAnchoredResidualPolicy) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
        if not name.startswith("policy.delayed_residual.")
    }


def residual_optimizer(
    model: FastAnchoredResidualPolicy,
) -> torch.optim.Adam:
    return torch.optim.Adam(
        model.residual_parameters(),
        lr=LEARNING_RATE,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0,
        amsgrad=False,
    )


def optimizer_owns_only_residual(
    model: FastAnchoredResidualPolicy, optimizer: torch.optim.Optimizer
) -> bool:
    expected = {id(parameter) for parameter in model.residual_parameters()}
    actual = {
        id(parameter)
        for group in optimizer.param_groups
        for parameter in group["params"]
    }
    return bool(expected and actual == expected)


def pointwise_loss(
    model: FastAnchoredResidualPolicy,
    dataset: dict[str, Any],
    indices: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    active_mask = dataset["active_mask"][indices]
    output = model.forward_step(
        observations=dataset["observations"][indices],
        active_mask=active_mask,
        critic_state=dataset["critic_state"][indices],
        hidden=torch.zeros(
            (len(indices), source.CAPACITY, model.hidden_dim), dtype=torch.float32
        ),
        deterministic=True,
    )
    squared = torch.square(output.actions - dataset["actions"][indices]).mean(
        dim=-1
    )
    return squared[active_mask].mean(), output.actions


def fit_residual(
    model: FastAnchoredResidualPolicy,
    dataset: dict[str, Any],
    *,
    steps: int = FIT_STEPS,
    batch_size: int = FIT_BATCH_SIZE,
) -> dict[str, Any]:
    if min(int(steps), int(batch_size)) <= 0:
        raise ValueError("G25 fit counts must be positive")
    if model.phase != "delayed":
        raise RuntimeError("G25 fit requires a frozen delayed phase")
    optimizer = residual_optimizer(model)
    owner_exact = optimizer_owns_only_residual(model, optimizer)
    anchor = frozen_state(model)
    all_indices = torch.arange(len(dataset["observations"]))
    generator = torch.Generator().manual_seed(MINIBATCH_SEED)
    with torch.no_grad():
        initial_loss, initial_actions = pointwise_loss(model, dataset, all_indices)
    inactive_initial = torch.where(
        dataset["active_mask"].unsqueeze(-1),
        torch.zeros_like(initial_actions),
        initial_actions,
    )
    finite = True
    maximum_gradient_norm = 0.0
    model.train()
    for _ in range(int(steps)):
        indices = torch.randint(
            len(all_indices),
            (min(int(batch_size), len(all_indices)),),
            generator=generator,
        )
        loss, _ = pointwise_loss(model, dataset, indices)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(
            model.residual_parameters(), GRADIENT_CLIP
        )
        optimizer.step()
        finite = finite and bool(torch.isfinite(loss)) and bool(
            torch.isfinite(gradient_norm)
        )
        maximum_gradient_norm = max(
            maximum_gradient_norm, float(gradient_norm.detach().cpu())
        )
    model.eval()
    with torch.no_grad():
        final_loss, final_actions = pointwise_loss(model, dataset, all_indices)
    inactive_final = torch.where(
        dataset["active_mask"].unsqueeze(-1),
        torch.zeros_like(final_actions),
        final_actions,
    )
    initial = float(initial_loss.detach().cpu())
    final = float(final_loss.detach().cpu())
    return {
        "steps": int(steps),
        "batch_size": int(batch_size),
        "optimizer": "adam",
        "learning_rate": LEARNING_RATE,
        "gradient_clip": GRADIENT_CLIP,
        "optimizer_owns_only_residual": owner_exact,
        "finite_updates": bool(finite),
        "maximum_gradient_norm": maximum_gradient_norm,
        "initial_mse": initial,
        "final_mse": final,
        "final_to_initial_ratio": final / max(initial, torch.finfo().tiny),
        "anchor_maximum_difference": maximum_state_difference(
            anchor, frozen_state(model)
        ),
        "residual_output_layer_maximum_absolute_value": (
            model.residual_output_layer_maximum_absolute_value()
        ),
        "inactive_initial_actions_exact_zero": int(
            torch.count_nonzero(inactive_initial)
        )
        == 0,
        "inactive_final_actions_exact_zero": int(
            torch.count_nonzero(inactive_final)
        )
        == 0,
    }


def battery_metrics(evaluation: list[dict[str, Any]]) -> dict[str, float]:
    summary = g19._battery_means({"slot_rows": evaluation})
    return {name: float(value) for name, value in summary.items()}


def select_result_branch(metrics: dict[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not (
        float(metrics["final_mse"]) <= ABSOLUTE_MSE_CEILING
        and float(metrics["final_to_initial_ratio"]) <= RELATIVE_MSE_CEILING
    ):
        return NO_POINTWISE_BRANCH
    if not (
        float(metrics["final_utility"]) >= g19.G18_UTILITY_FLOOR
        and float(metrics["gain_over_anchor"]) >= g19.G18_GAIN_FLOOR
        and float(metrics["spike_utility"]) >= g19.G18_SPIKE_UTILITY_FLOOR
        and float(metrics["rotating_effort_share"])
        >= g19.G18_ROTATING_EFFORT_SHARE_FLOOR
    ):
        return NO_CLOSED_LOOP_BRANCH
    return PASS_BRANCH


def run_probe(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    if not source_commit or source_commit == "NONFORMAL_WORKTREE":
        raise ValueError("G25 probe requires an integrated source commit")
    run_root.mkdir(parents=True, exist_ok=False)
    runtime.configure_runtime(MODEL_SEED)
    started = time.perf_counter()
    model = make_model()
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.credit_baselines.parameters()),
        lr=g19.LEARNING_RATE,
    )
    replay_maximum = 0.0
    lifecycle_valid = True
    fast_finite = True
    for update in range(FAST_UPDATES):
        first_episode = update * NUM_ENVS
        trajectory = collect_battery_trajectory(
            model,
            episode_ids=tuple(range(first_episode, first_episode + NUM_ENVS)),
            action_seed=ACTION_SEED,
            device=torch.device("cpu"),
        )
        lifecycle_valid = lifecycle_valid and g19._trajectory_contract_valid(
            "g18", trajectory
        )
        update_metrics = optimize_fast_anchor_update(
            model,
            fast_optimizer,
            trajectory,
            device=torch.device("cpu"),
            ppo_passes=PPO_PASSES,
        )
        fast_finite = fast_finite and bool(update_metrics["finite_update"])
        replay_maximum = max(
            replay_maximum,
            *(
                float(value)
                for name, value in update_metrics.items()
                if name.endswith("_error") or name.endswith("_max_abs")
            ),
        )
    anchor_evaluation = battery_metrics(
        evaluate_battery_policy(model, device=torch.device("cpu"))
    )
    model.begin_delayed_phase()
    dataset = constructive_dataset()
    dataset_controls = dataset_contract(dataset)
    fit = fit_residual(model, dataset)
    final_evaluation = battery_metrics(
        evaluate_battery_policy(model, device=torch.device("cpu"))
    )
    source_controls = source.run_information_gate()
    runtime_identity = _runtime_identity()
    operational_valid = bool(
        runtime_identity["backend"] == "cpu"
        and runtime_identity["torch_threads"] == 1
        and source_controls["branch"] == source.PASS_BRANCH
        and all(
            bool(dataset_controls[name])
            for name in (
                "row_count_exact",
                "slot_order_counts_exact",
                "time_coverage_exact",
                "finite",
                "inactive_targets_exact_zero",
            )
        )
        and lifecycle_valid
        and fast_finite
        and replay_maximum <= g19.REPLAY_TOLERANCE
        and fit["optimizer_owns_only_residual"]
        and fit["finite_updates"]
        and fit["anchor_maximum_difference"] == 0.0
        and fit["residual_output_layer_maximum_absolute_value"] > 0.0
        and fit["inactive_initial_actions_exact_zero"]
        and fit["inactive_final_actions_exact_zero"]
    )
    metrics = {
        "operational_valid": operational_valid,
        "maximum_replay_error": float(replay_maximum),
        "anchor_utility": anchor_evaluation["utility"],
        "final_utility": final_evaluation["utility"],
        "gain_over_anchor": final_evaluation["utility"]
        - anchor_evaluation["utility"],
        "spike_utility": final_evaluation["spike_utility"],
        "rotating_effort_share": final_evaluation["rotating_effort_share"],
        "minimum_step_utility": final_evaluation["minimum_step_utility"],
        **{
            name: fit[name]
            for name in (
                "initial_mse",
                "final_mse",
                "final_to_initial_ratio",
                "anchor_maximum_difference",
            )
        },
    }
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "diagnostic_probe",
        "status": "COMPLETE",
        "formal": False,
        "iteration_consumed": False,
        "source_commit": source_commit,
        "runtime": runtime_identity,
        "configuration": {
            "model_seed": MODEL_SEED,
            "action_seed": ACTION_SEED,
            "minibatch_seed": MINIBATCH_SEED,
            "fast_updates": FAST_UPDATES,
            "num_envs": NUM_ENVS,
            "ppo_passes": PPO_PASSES,
            "fit_steps": FIT_STEPS,
            "fit_batch_size": FIT_BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "absolute_mse_ceiling": ABSOLUTE_MSE_CEILING,
            "relative_mse_ceiling": RELATIVE_MSE_CEILING,
            "teacher_scope": "diagnostic_runner_only",
        },
        "source_controls": source_controls,
        "dataset_controls": dataset_controls,
        "fast_anchor": {
            "finite_updates": bool(fast_finite),
            "lifecycle_contract_valid": bool(lifecycle_valid),
            "maximum_replay_error": float(replay_maximum),
            "evaluation": anchor_evaluation,
        },
        "fit": fit,
        "final_evaluation": final_evaluation,
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
    result = run_probe(
        run_root=arguments.run_root, source_commit=arguments.source_commit
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
