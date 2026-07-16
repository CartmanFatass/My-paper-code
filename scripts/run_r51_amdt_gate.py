"""R51-AMDT-G0 paired variable-N task-learning abandonment gate."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process.r51_amdt import (  # noqa: E402
    AMDTSetPointerPolicy,
    AnonymousMaintenanceDispatchBatch,
    EpisodeLedger,
    HIDDEN_DIM,
    HORIZON,
    JOB_DEADLINE,
    STATION_HEALTH_MAX,
    TEAM_SIZES,
    WAVE_STARTS,
    json_ready,
    make_episode_ledger,
    maximum_state_difference,
    model_state_copy,
    state_dict_finite,
)


EXPERIMENT_ID = "EXP-20260716-r51-amdt-g0"
SCHEMA_VERSION = 1
MODEL_SEED = 51_051
TRAIN_RESET_SEED = 61_051
ORDER_ACTION_SEED = 71_051
EVALUATION_SEED = 81_051
BOOTSTRAP_SEED = 91_051
FORMAL_CYCLES = 125
FORMAL_BATCH_SIZE = 16
FORMAL_EVAL_EPISODES = 128
DRY_CYCLES = 2
DRY_BATCH_SIZE = 4
DRY_EVAL_EPISODES = 8
LEARNING_RATE = 3.0e-4
GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_EPOCHS = 1
ENTROPY_COEFFICIENT = 0.01
VALUE_COEFFICIENT = 0.5
PPO_CLIP = 0.2
GRADIENT_CLIP = 0.5
REPLAY_TOLERANCE = 1.0e-6
BOOTSTRAP_REPETITIONS = 10_000
RELEVANT_MODULES = (
    "member_encoder",
    "entity_encoder",
    "temporal_core",
    "query_mlp",
    "entity_key",
    "critic_hidden",
    "critic_value",
)


@dataclass
class Trajectory:
    ledger: EpisodeLedger
    self_features: torch.Tensor
    entity_features: torch.Tensor
    entity_masks: torch.Tensor
    member_active_masks: torch.Tensor
    critic_fields: torch.Tensor
    agent_orders: torch.Tensor
    entity_orders: torch.Tensor
    hidden_reset_masks: torch.Tensor
    sampling_uniforms: torch.Tensor
    action_pointers: torch.Tensor
    prefix_counts: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    rewards: torch.Tensor
    diagnostics: dict[str, Any]

    @property
    def active_n(self) -> int:
        return int(self.ledger.active_n)

    @property
    def batch_size(self) -> int:
        return int(self.ledger.batch_size)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(json_ready(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _all_finite(values: Iterable[float]) -> bool:
    return all(math.isfinite(float(value)) for value in values)


def configure_runtime(device: torch.device) -> None:
    random.seed(MODEL_SEED)
    np.random.seed(MODEL_SEED)
    torch.manual_seed(MODEL_SEED)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(MODEL_SEED)
    torch.use_deterministic_algorithms(True)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True


def _tensor(array: np.ndarray, *, device: torch.device, dtype: torch.dtype | None = None) -> torch.Tensor:
    return torch.as_tensor(array, device=device, dtype=dtype)


def collect_trajectory(
    *,
    model: AMDTSetPointerPolicy,
    ledger: EpisodeLedger,
    device: torch.device,
    deterministic: bool,
) -> Trajectory:
    """Collect one complete 32-step batch with a fixed paired ledger."""

    environment = AnonymousMaintenanceDispatchBatch(ledger)
    batch = ledger.batch_size
    active_n = ledger.active_n
    hidden = torch.zeros(
        (batch, active_n, HIDDEN_DIM), dtype=torch.float32, device=device
    )
    self_rows: list[torch.Tensor] = []
    entity_rows: list[torch.Tensor] = []
    entity_mask_rows: list[torch.Tensor] = []
    member_mask_rows: list[torch.Tensor] = []
    critic_rows: list[torch.Tensor] = []
    agent_order_rows: list[torch.Tensor] = []
    entity_order_rows: list[torch.Tensor] = []
    hidden_mask_rows: list[torch.Tensor] = []
    uniform_rows: list[torch.Tensor] = []
    pointer_rows: list[torch.Tensor] = []
    prefix_rows: list[torch.Tensor] = []
    log_prob_rows: list[torch.Tensor] = []
    value_rows: list[torch.Tensor] = []
    reward_rows: list[torch.Tensor] = []

    model.train()
    with torch.no_grad():
        for step in range(HORIZON):
            environment.prepare_step(step)
            self_view, entities, entity_mask, critic = environment.observations()
            self_tensor = _tensor(self_view, device=device)
            entity_tensor = _tensor(entities, device=device)
            entity_mask_tensor = _tensor(
                entity_mask, device=device, dtype=torch.bool
            )
            agent_order = _tensor(
                ledger.agent_orders[step], device=device, dtype=torch.long
            )
            entity_order = _tensor(
                ledger.entity_orders[step], device=device, dtype=torch.long
            )
            uniforms = _tensor(ledger.sampling_uniforms[step], device=device)
            hidden_reset = torch.full(
                (batch, active_n),
                0.0 if step == 0 else 1.0,
                dtype=torch.float32,
                device=device,
            )
            output = model.forward_step(
                self_features=self_tensor,
                entity_features=entity_tensor,
                entity_mask=entity_mask_tensor,
                agent_order=agent_order,
                entity_order=entity_order,
                hidden=hidden,
                hidden_reset_mask=hidden_reset,
                critic_fields=_tensor(critic, device=device),
                sampling_uniforms=None if deterministic else uniforms,
                deterministic=deterministic,
            )
            hidden = output.next_hidden
            reward, _info = environment.step(
                output.actions_by_agent.detach().cpu().numpy()
            )
            self_rows.append(self_tensor)
            entity_rows.append(entity_tensor)
            entity_mask_rows.append(entity_mask_tensor)
            member_mask_rows.append(
                torch.ones(
                    (batch, active_n), dtype=torch.bool, device=device
                )
            )
            critic_rows.append(_tensor(critic, device=device))
            agent_order_rows.append(agent_order)
            entity_order_rows.append(entity_order)
            hidden_mask_rows.append(hidden_reset)
            uniform_rows.append(uniforms)
            pointer_rows.append(output.pointers_by_position)
            prefix_rows.append(output.prefix_counts)
            log_prob_rows.append(output.token_log_probs)
            value_rows.append(output.value)
            reward_rows.append(_tensor(reward, device=device))

    return Trajectory(
        ledger=ledger,
        self_features=torch.stack(self_rows),
        entity_features=torch.stack(entity_rows),
        entity_masks=torch.stack(entity_mask_rows),
        member_active_masks=torch.stack(member_mask_rows),
        critic_fields=torch.stack(critic_rows),
        agent_orders=torch.stack(agent_order_rows),
        entity_orders=torch.stack(entity_order_rows),
        hidden_reset_masks=torch.stack(hidden_mask_rows),
        sampling_uniforms=torch.stack(uniform_rows),
        action_pointers=torch.stack(pointer_rows),
        prefix_counts=torch.stack(prefix_rows),
        old_log_probs=torch.stack(log_prob_rows),
        old_values=torch.stack(value_rows),
        rewards=torch.stack(reward_rows),
        diagnostics=environment.diagnostics(),
    )


def replay_and_loss(
    *, model: AMDTSetPointerPolicy, trajectory: Trajectory
) -> tuple[torch.Tensor, dict[str, float]]:
    """Teacher-force the stored AR trajectory and form one PPO epoch."""

    batch = trajectory.batch_size
    active_n = trajectory.active_n
    device = trajectory.self_features.device
    hidden = torch.zeros(
        (batch, active_n, HIDDEN_DIM), dtype=torch.float32, device=device
    )
    replay_log_probs: list[torch.Tensor] = []
    replay_values: list[torch.Tensor] = []
    replay_entropies: list[torch.Tensor] = []
    replay_prefixes: list[torch.Tensor] = []
    replay_masked_mass: list[torch.Tensor] = []
    for step in range(HORIZON):
        output = model.forward_step(
            self_features=trajectory.self_features[step],
            entity_features=trajectory.entity_features[step],
            entity_mask=trajectory.entity_masks[step],
            agent_order=trajectory.agent_orders[step],
            entity_order=trajectory.entity_orders[step],
            hidden=hidden,
            hidden_reset_mask=trajectory.hidden_reset_masks[step],
            critic_fields=trajectory.critic_fields[step],
            teacher_pointers=trajectory.action_pointers[step],
        )
        hidden = output.next_hidden
        replay_log_probs.append(output.token_log_probs)
        replay_values.append(output.value)
        replay_entropies.append(output.token_entropies)
        replay_prefixes.append(output.prefix_counts)
        replay_masked_mass.append(output.masked_probability_mass)
    new_log_probs = torch.stack(replay_log_probs)
    new_values = torch.stack(replay_values)
    entropies = torch.stack(replay_entropies)
    prefixes = torch.stack(replay_prefixes)
    masked_mass = torch.stack(replay_masked_mass)

    replay_error = torch.max(
        torch.abs(new_log_probs.detach() - trajectory.old_log_probs)
    )
    prefix_error = torch.max(
        torch.abs(prefixes.detach() - trajectory.prefix_counts)
    )
    masked_probability_mass = torch.max(masked_mass.detach())

    old_values = trajectory.old_values.detach()
    rewards = trajectory.rewards.detach()
    advantages = torch.zeros_like(rewards)
    running_advantage = torch.zeros(batch, dtype=torch.float32, device=device)
    for step in range(HORIZON - 1, -1, -1):
        next_value = (
            old_values[step + 1]
            if step + 1 < HORIZON
            else torch.zeros_like(old_values[step])
        )
        continuation = 1.0 if step + 1 < HORIZON else 0.0
        delta = rewards[step] + GAMMA * continuation * next_value - old_values[step]
        running_advantage = (
            delta + GAMMA * GAE_LAMBDA * continuation * running_advantage
        )
        advantages[step] = running_advantage
    returns = advantages + old_values
    normalized_advantages = (advantages - advantages.mean()) / (
        advantages.std(unbiased=False) + 1.0e-8
    )

    ratios = torch.exp(new_log_probs - trajectory.old_log_probs)
    token_advantages = normalized_advantages.unsqueeze(-1)
    unclipped = ratios * token_advantages
    clipped = torch.clamp(
        ratios, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP
    ) * token_advantages
    actor_loss = -torch.minimum(unclipped, clipped).mean(dim=-1).mean()
    value_loss = 0.5 * torch.mean((new_values - returns) ** 2)
    entropy = entropies.mean()
    total_loss = (
        actor_loss
        + VALUE_COEFFICIENT * value_loss
        - ENTROPY_COEFFICIENT * entropy
    )
    metrics = {
        "loss": float(total_loss.detach().cpu()),
        "actor_loss": float(actor_loss.detach().cpu()),
        "value_loss": float(value_loss.detach().cpu()),
        "entropy": float(entropy.detach().cpu()),
        "sample_replay_logp_max_error": float(replay_error.cpu()),
        "prefix_replay_max_error": float(prefix_error.cpu()),
        "masked_probability_mass_max": float(masked_probability_mass.cpu()),
        "mean_reward": float(rewards[-1].mean().cpu()),
        "mean_advantage": float(advantages.mean().cpu()),
    }
    return total_loss, metrics


def take_optimizer_step(
    *,
    model: AMDTSetPointerPolicy,
    optimizer: torch.optim.Optimizer,
    loss: torch.Tensor,
) -> tuple[float, dict[str, float]]:
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    module_gradient_norms = {name: 0.0 for name in RELEVANT_MODULES}
    for name, parameter in model.named_parameters():
        if parameter.grad is None:
            continue
        prefix = name.split(".", 1)[0]
        if prefix in module_gradient_norms:
            value = float(torch.linalg.vector_norm(parameter.grad).detach().cpu())
            module_gradient_norms[prefix] = max(
                module_gradient_norms[prefix], value
            )
    gradient_norm = torch.nn.utils.clip_grad_norm_(
        model.parameters(), GRADIENT_CLIP
    )
    gradient_value = float(gradient_norm.detach().cpu())
    if not _all_finite((gradient_value, *module_gradient_norms.values())):
        raise RuntimeError("non-finite R51 gradient")
    optimizer.step()
    return gradient_value, module_gradient_norms


def update_maxima(target: dict[str, float], values: dict[str, float]) -> None:
    for name, value in values.items():
        target[name] = max(float(target.get(name, 0.0)), float(value))


def drift_summary(
    initial_state: dict[str, torch.Tensor], model: AMDTSetPointerPolicy
) -> dict[str, Any]:
    final_state = model_state_copy(model)
    modules: dict[str, float] = {}
    for prefix in RELEVANT_MODULES:
        names = [name for name in initial_state if name.startswith(prefix + ".")]
        modules[prefix] = max(
            float(torch.max(torch.abs(final_state[name] - initial_state[name])))
            for name in names
        )
    return {
        "module_max_abs": modules,
        "minimum_relevant_module_max_abs": min(modules.values()),
        "maximum_parameter_abs": max(
            float(torch.max(torch.abs(tensor))) for tensor in final_state.values()
        ),
        "all_parameters_finite": state_dict_finite(final_state),
    }


def trajectory_storage_valid(trajectory: Trajectory) -> bool:
    t, batch, active_n = trajectory.member_active_masks.shape
    entities = active_n + 1
    return bool(
        t == HORIZON
        and batch == trajectory.batch_size
        and active_n == trajectory.active_n
        and tuple(trajectory.entity_masks.shape) == (t, batch, entities)
        and tuple(trajectory.agent_orders.shape) == (t, batch, active_n)
        and tuple(trajectory.entity_orders.shape) == (t, batch, entities)
        and tuple(trajectory.action_pointers.shape) == (t, batch, active_n)
        and tuple(trajectory.prefix_counts.shape)
        == (t, batch, active_n, entities)
        and tuple(trajectory.old_log_probs.shape) == (t, batch, active_n)
        and bool(trajectory.member_active_masks.all())
        and bool((trajectory.hidden_reset_masks[0] == 0.0).all())
        and bool((trajectory.hidden_reset_masks[1:] == 1.0).all())
    )


def evaluation_record(trajectory: Trajectory) -> dict[str, Any]:
    diagnostics = trajectory.diagnostics
    success = np.asarray(diagnostics["success"], dtype=np.float64)
    return {
        "episode_success": success,
        "success_rate": float(success.mean()),
        "station_failure_rate": float(
            np.asarray(diagnostics["station_failure"], dtype=np.float64).mean()
        ),
        "completed_job_fraction": float(
            np.asarray(
                diagnostics["completed_job_fraction"], dtype=np.float64
            ).mean()
        ),
        "deadline_miss_rate": float(
            np.asarray(
                diagnostics["deadline_miss_fraction"], dtype=np.float64
            ).mean()
        ),
        "duplicate_assignment_fraction": float(
            np.asarray(
                diagnostics["duplicate_assignment_fraction"], dtype=np.float64
            ).mean()
        ),
        "station_assignment_dwell_mean": float(
            diagnostics["station_dwell_mean"]
        ),
        "job_assignment_dwell_mean": float(diagnostics["job_dwell_mean"]),
    }


def make_evaluation_ledgers(cases_per_n: int) -> dict[int, EpisodeLedger]:
    reset_seed, control_seed = np.random.SeedSequence(EVALUATION_SEED).spawn(2)
    reset_rng = np.random.default_rng(reset_seed)
    control_rng = np.random.default_rng(control_seed)
    return {
        active_n: make_episode_ledger(
            active_n=active_n,
            batch_size=cases_per_n,
            reset_rng=reset_rng,
            control_rng=control_rng,
        )
        for active_n in TEAM_SIZES
    }


def evaluate_models(
    *,
    shared: AMDTSetPointerPolicy,
    specialists: dict[int, AMDTSetPointerPolicy],
    ledgers: dict[int, EpisodeLedger],
    device: torch.device,
) -> dict[str, Any]:
    shared_results: dict[str, Any] = {}
    specialist_results: dict[str, Any] = {}
    for active_n in TEAM_SIZES:
        ledger = ledgers[active_n]
        shared_results[str(active_n)] = evaluation_record(
            collect_trajectory(
                model=shared,
                ledger=ledger,
                device=device,
                deterministic=True,
            )
        )
        specialist_results[str(active_n)] = evaluation_record(
            collect_trajectory(
                model=specialists[active_n],
                ledger=ledger,
                device=device,
                deterministic=True,
            )
        )

    def summarize(by_size: dict[str, Any]) -> dict[str, Any]:
        success = [by_size[str(n)]["success_rate"] for n in TEAM_SIZES]
        return {
            "by_size": by_size,
            "macro_success": float(np.mean(success)),
            "minimum_success": float(np.min(success)),
        }

    return {
        "shared": summarize(shared_results),
        "specialists": summarize(specialist_results),
    }


def load_exact_model(path: Path, device: torch.device) -> AMDTSetPointerPolicy:
    try:
        payload = torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        payload = torch.load(path, map_location=device)
    model = AMDTSetPointerPolicy().to(device)
    model.load_state_dict(payload["state_dict"], strict=True)
    return model


def paired_bootstrap_ci(
    differences: np.ndarray,
    rng: np.random.Generator,
    repetitions: int = BOOTSTRAP_REPETITIONS,
) -> dict[str, float]:
    differences = np.asarray(differences, dtype=np.float64)
    indices = rng.integers(
        0, differences.size, size=(repetitions, differences.size)
    )
    estimates = differences[indices].mean(axis=1)
    return {
        "mean": float(differences.mean()),
        "lower": float(np.quantile(estimates, 0.025)),
        "upper": float(np.quantile(estimates, 0.975)),
    }


def macro_paired_bootstrap_ci(
    differences_by_n: dict[int, np.ndarray],
    rng: np.random.Generator,
    repetitions: int = BOOTSTRAP_REPETITIONS,
) -> dict[str, float]:
    bootstrap_by_n: list[np.ndarray] = []
    observed: list[float] = []
    for active_n in TEAM_SIZES:
        differences = np.asarray(differences_by_n[active_n], dtype=np.float64)
        observed.append(float(differences.mean()))
        indices = rng.integers(
            0, differences.size, size=(repetitions, differences.size)
        )
        bootstrap_by_n.append(differences[indices].mean(axis=1))
    estimates = np.stack(bootstrap_by_n, axis=1).mean(axis=1)
    return {
        "mean": float(np.mean(observed)),
        "lower": float(np.quantile(estimates, 0.025)),
        "upper": float(np.quantile(estimates, 0.975)),
    }


def state_dict_shapes(model: AMDTSetPointerPolicy) -> dict[str, list[int]]:
    return {
        name: list(tensor.shape) for name, tensor in model.state_dict().items()
    }


def run_gate(args: argparse.Namespace) -> dict[str, Any]:
    device = torch.device(args.device)
    if device.type != "cuda":
        raise ValueError("R51 formal and focused runs require CUDA")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required; CPU fallback is prohibited")
    configure_runtime(device)
    cycles = DRY_CYCLES if args.dry_run else FORMAL_CYCLES
    batch_size = DRY_BATCH_SIZE if args.dry_run else FORMAL_BATCH_SIZE
    eval_episodes = (
        DRY_EVAL_EPISODES if args.dry_run else FORMAL_EVAL_EPISODES
    )
    run_root = Path(args.run_root).resolve()
    seed_root = run_root / "seed"
    result_root = run_root / "result"
    checkpoint_root = seed_root / "checkpoints"
    for path in (seed_root, result_root, checkpoint_root):
        path.mkdir(parents=True, exist_ok=True)
    progress_path = seed_root / "progress.json"
    updates_path = seed_root / "train_updates.csv"
    result_path = result_root / (
        "dry_run_check.json" if args.dry_run else "r51_amdt.json"
    )

    torch.manual_seed(MODEL_SEED)
    torch.cuda.manual_seed_all(MODEL_SEED)
    shared = AMDTSetPointerPolicy().to(device)
    if shared.parameter_count >= 35_000:
        raise RuntimeError("R51 model exceeds the registered 35K parameter cap")
    initial_state = model_state_copy(shared)
    specialists: dict[int, AMDTSetPointerPolicy] = {}
    for active_n in TEAM_SIZES:
        specialist = AMDTSetPointerPolicy().to(device)
        specialist.load_state_dict(copy.deepcopy(initial_state), strict=True)
        specialists[active_n] = specialist
    initial_errors = {
        "shared": maximum_state_difference(
            initial_state, model_state_copy(shared)
        ),
        **{
            f"specialist_{active_n}": maximum_state_difference(
                initial_state, model_state_copy(specialists[active_n])
            )
            for active_n in TEAM_SIZES
        },
    }
    shared_optimizer = torch.optim.Adam(
        shared.parameters(), lr=LEARNING_RATE
    )
    specialist_optimizers = {
        active_n: torch.optim.Adam(
            specialists[active_n].parameters(), lr=LEARNING_RATE
        )
        for active_n in TEAM_SIZES
    }

    evaluation_ledgers = make_evaluation_ledgers(eval_episodes)
    zero_evaluation = evaluate_models(
        shared=shared,
        specialists=specialists,
        ledgers=evaluation_ledgers,
        device=device,
    )

    reset_seed, = np.random.SeedSequence(TRAIN_RESET_SEED).spawn(1)
    schedule_seed, control_seed = np.random.SeedSequence(
        ORDER_ACTION_SEED
    ).spawn(2)
    reset_rng = np.random.default_rng(reset_seed)
    schedule_rng = np.random.default_rng(schedule_seed)
    control_rng = np.random.default_rng(control_seed)
    schedule: list[int] = []
    maximum_replay_error = 0.0
    maximum_prefix_error = 0.0
    maximum_masked_mass = 0.0
    shared_optimizer_steps = 0
    specialist_optimizer_steps = {n: 0 for n in TEAM_SIZES}
    transitions_per_arm = 0
    transitions_by_n = {n: 0 for n in TEAM_SIZES}
    tokens_per_arm = 0
    tokens_by_n = {n: 0 for n in TEAM_SIZES}
    paired_ledger_checks = 0
    trajectory_storage_checks = 0
    reward_contract_checks = 0
    nonterminal_reward_nonzero = 0
    final_reward_predicate_mismatch = 0
    invalid_action_count = 0
    finite_training_metrics = True
    shared_gradient_max = {name: 0.0 for name in RELEVANT_MODULES}
    specialist_gradient_max = {
        n: {name: 0.0 for name in RELEVANT_MODULES} for n in TEAM_SIZES
    }
    shared_nonzero_gradient_steps = 0
    specialist_nonzero_gradient_steps = {n: 0 for n in TEAM_SIZES}
    started = time.perf_counter()

    with updates_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "update",
            "cycle",
            "active_n",
            "transitions_per_arm",
            "tokens_per_arm",
            "shared_success",
            "specialist_success",
            "shared_loss",
            "specialist_loss",
            "shared_gradient_norm",
            "specialist_gradient_norm",
            "sample_replay_logp_max_error",
            "prefix_replay_max_error",
            "masked_probability_mass_max",
            "elapsed_seconds",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        update = 0
        for cycle in range(1, cycles + 1):
            cycle_order = [
                int(value) for value in schedule_rng.permutation(TEAM_SIZES)
            ]
            schedule.extend(cycle_order)
            for active_n in cycle_order:
                update += 1
                ledger = make_episode_ledger(
                    active_n=active_n,
                    batch_size=batch_size,
                    reset_rng=reset_rng,
                    control_rng=control_rng,
                )
                shared_trajectory = collect_trajectory(
                    model=shared,
                    ledger=ledger,
                    device=device,
                    deterministic=False,
                )
                specialist_trajectory = collect_trajectory(
                    model=specialists[active_n],
                    ledger=ledger,
                    device=device,
                    deterministic=False,
                )
                paired_ledger_checks += int(
                    shared_trajectory.ledger is specialist_trajectory.ledger
                )
                trajectory_storage_checks += int(
                    trajectory_storage_valid(shared_trajectory)
                    and trajectory_storage_valid(specialist_trajectory)
                )
                for trajectory in (shared_trajectory, specialist_trajectory):
                    diagnostics = trajectory.diagnostics
                    nonterminal_reward_nonzero += int(
                        diagnostics["nonterminal_reward_nonzero"]
                    )
                    final_reward_predicate_mismatch += int(
                        diagnostics["final_reward_predicate_mismatch"]
                    )
                    invalid_action_count += int(
                        diagnostics["invalid_action_count"]
                    )
                    reward_contract_checks += 1

                shared_loss, shared_metrics = replay_and_loss(
                    model=shared, trajectory=shared_trajectory
                )
                specialist_loss, specialist_metrics = replay_and_loss(
                    model=specialists[active_n],
                    trajectory=specialist_trajectory,
                )
                for metrics in (shared_metrics, specialist_metrics):
                    maximum_replay_error = max(
                        maximum_replay_error,
                        metrics["sample_replay_logp_max_error"],
                    )
                    maximum_prefix_error = max(
                        maximum_prefix_error,
                        metrics["prefix_replay_max_error"],
                    )
                    maximum_masked_mass = max(
                        maximum_masked_mass,
                        metrics["masked_probability_mass_max"],
                    )
                shared_gradient, shared_module_gradients = take_optimizer_step(
                    model=shared,
                    optimizer=shared_optimizer,
                    loss=shared_loss,
                )
                specialist_gradient, specialist_module_gradients = (
                    take_optimizer_step(
                        model=specialists[active_n],
                        optimizer=specialist_optimizers[active_n],
                        loss=specialist_loss,
                    )
                )
                update_maxima(shared_gradient_max, shared_module_gradients)
                update_maxima(
                    specialist_gradient_max[active_n],
                    specialist_module_gradients,
                )
                shared_optimizer_steps += 1
                specialist_optimizer_steps[active_n] += 1
                shared_nonzero_gradient_steps += int(shared_gradient > 0.0)
                specialist_nonzero_gradient_steps[active_n] += int(
                    specialist_gradient > 0.0
                )
                batch_transitions = batch_size * HORIZON
                batch_tokens = batch_transitions * active_n
                transitions_per_arm += batch_transitions
                transitions_by_n[active_n] += batch_transitions
                tokens_per_arm += batch_tokens
                tokens_by_n[active_n] += batch_tokens
                finite_training_metrics = finite_training_metrics and _all_finite(
                    (
                        shared_gradient,
                        specialist_gradient,
                        *shared_metrics.values(),
                        *specialist_metrics.values(),
                    )
                )
                elapsed = time.perf_counter() - started
                writer.writerow(
                    {
                        "update": update,
                        "cycle": cycle,
                        "active_n": active_n,
                        "transitions_per_arm": transitions_per_arm,
                        "tokens_per_arm": tokens_per_arm,
                        "shared_success": shared_metrics["mean_reward"],
                        "specialist_success": specialist_metrics["mean_reward"],
                        "shared_loss": shared_metrics["loss"],
                        "specialist_loss": specialist_metrics["loss"],
                        "shared_gradient_norm": shared_gradient,
                        "specialist_gradient_norm": specialist_gradient,
                        "sample_replay_logp_max_error": max(
                            shared_metrics["sample_replay_logp_max_error"],
                            specialist_metrics["sample_replay_logp_max_error"],
                        ),
                        "prefix_replay_max_error": max(
                            shared_metrics["prefix_replay_max_error"],
                            specialist_metrics["prefix_replay_max_error"],
                        ),
                        "masked_probability_mass_max": max(
                            shared_metrics["masked_probability_mass_max"],
                            specialist_metrics["masked_probability_mass_max"],
                        ),
                        "elapsed_seconds": elapsed,
                    }
                )
                handle.flush()
                _write_json(
                    progress_path,
                    {
                        "state": "training",
                        "update": update,
                        "updates_total": cycles * len(TEAM_SIZES),
                        "cycle": cycle,
                        "cycles_total": cycles,
                        "active_n": active_n,
                        "fraction": update / (cycles * len(TEAM_SIZES)),
                        "transitions_per_arm": transitions_per_arm,
                        "transitions_total_per_arm": cycles
                        * len(TEAM_SIZES)
                        * batch_size
                        * HORIZON,
                        "shared_success": shared_metrics["mean_reward"],
                        "specialist_success": specialist_metrics["mean_reward"],
                        "sample_replay_logp_max_error": maximum_replay_error,
                        "elapsed_seconds": elapsed,
                    },
                )

    shared_path = checkpoint_root / "exact_final_shared.pt"
    torch.save({"state_dict": model_state_copy(shared)}, shared_path)
    specialist_paths: dict[int, Path] = {}
    for active_n in TEAM_SIZES:
        path = checkpoint_root / f"exact_final_specialist_n{active_n}.pt"
        torch.save(
            {"state_dict": model_state_copy(specialists[active_n])}, path
        )
        specialist_paths[active_n] = path
    loaded_shared = load_exact_model(shared_path, device)
    loaded_specialists = {
        active_n: load_exact_model(specialist_paths[active_n], device)
        for active_n in TEAM_SIZES
    }
    checkpoint_reload_errors = {
        "shared": maximum_state_difference(
            model_state_copy(shared), model_state_copy(loaded_shared)
        ),
        **{
            f"specialist_{active_n}": maximum_state_difference(
                model_state_copy(specialists[active_n]),
                model_state_copy(loaded_specialists[active_n]),
            )
            for active_n in TEAM_SIZES
        },
    }
    final_evaluation = evaluate_models(
        shared=loaded_shared,
        specialists=loaded_specialists,
        ledgers=evaluation_ledgers,
        device=device,
    )

    shared_drift = drift_summary(initial_state, shared)
    specialist_drift = {
        str(active_n): drift_summary(initial_state, specialists[active_n])
        for active_n in TEAM_SIZES
    }
    expected_updates = cycles * len(TEAM_SIZES)
    expected_transitions = expected_updates * batch_size * HORIZON
    expected_transitions_by_n = cycles * batch_size * HORIZON
    expected_tokens = cycles * batch_size * HORIZON * sum(TEAM_SIZES)
    expected_pair_checks = expected_updates
    schedule_counts = {n: schedule.count(n) for n in TEAM_SIZES}

    scope_counts = {
        "intermediate_reward_terms": 0,
        "shaping_reward_terms": 0,
        "intrinsic_reward_terms": 0,
        "agent_identity_inputs": 0,
        "slot_embedding_inputs": 0,
        "role_label_inputs": 0,
        "skill_latent_inputs": 0,
        "keep_set_inputs": 0,
        "ppo_epochs": PPO_EPOCHS,
        "collected_batch_reuse": 0,
    }
    model_shape_reference = state_dict_shapes(shared)
    state_shapes_equal = all(
        state_dict_shapes(specialists[n]) == model_shape_reference
        for n in TEAM_SIZES
    )
    m0_checks = {
        "environment_size_formulas_exact": all(
            n // 2 + (n - n // 2) == n and 1 + n == n + 1
            for n in TEAM_SIZES
        ),
        "environment_constants_exact": HORIZON == 32
        and WAVE_STARTS == (4, 12, 20)
        and JOB_DEADLINE == 6
        and STATION_HEALTH_MAX == 4,
        "reward_only_terminal": nonterminal_reward_nonzero == 0,
        "reward_matches_success_predicate": final_reward_predicate_mismatch == 0,
        "no_invalid_action": invalid_action_count == 0,
        "scope_absence_exact": all(
            value == 0
            for name, value in scope_counts.items()
            if name not in {"ppo_epochs"}
        )
        and scope_counts["ppo_epochs"] == 1,
        "parameter_count_below_35k": shared.parameter_count < 35_000,
        "n_independent_state_shapes": state_shapes_equal,
        "paired_initial_parameters_exact": max(initial_errors.values()) == 0.0,
        "balanced_cycles_exact": all(
            schedule_counts[n] == cycles for n in TEAM_SIZES
        ),
        "transitions_per_arm_exact": transitions_per_arm == expected_transitions,
        "transitions_per_n_exact": all(
            transitions_by_n[n] == expected_transitions_by_n
            for n in TEAM_SIZES
        ),
        "agent_token_decisions_exact": tokens_per_arm == expected_tokens,
        "shared_optimizer_steps_exact": shared_optimizer_steps
        == expected_updates,
        "specialist_optimizer_steps_exact": all(
            specialist_optimizer_steps[n] == cycles for n in TEAM_SIZES
        )
        and sum(specialist_optimizer_steps.values()) == expected_updates,
        "one_epoch_no_data_reuse": PPO_EPOCHS == 1
        and scope_counts["collected_batch_reuse"] == 0,
        "paired_ledgers_exact": paired_ledger_checks == expected_pair_checks,
        "trajectory_ledgers_complete": trajectory_storage_checks
        == expected_pair_checks,
        "reward_contract_checks_exact": reward_contract_checks
        == 2 * expected_pair_checks,
        "sample_replay_probability": maximum_replay_error
        <= REPLAY_TOLERANCE,
        "prefix_replay_exact": maximum_prefix_error == 0.0,
        "masked_probability_mass_zero": maximum_masked_mass == 0.0,
        "hidden_reset_episode_only": trajectory_storage_checks
        == expected_pair_checks,
        "finite_training_metrics": finite_training_metrics,
        "shared_gradient_support": all(
            shared_gradient_max[name] > 0.0 for name in RELEVANT_MODULES
        )
        and shared_nonzero_gradient_steps == expected_updates,
        "specialist_gradient_support": all(
            specialist_gradient_max[n][name] > 0.0
            for n in TEAM_SIZES
            for name in RELEVANT_MODULES
        )
        and all(
            specialist_nonzero_gradient_steps[n] == cycles for n in TEAM_SIZES
        ),
        "shared_parameter_drift": shared_drift[
            "minimum_relevant_module_max_abs"
        ]
        > 0.0,
        "specialist_parameter_drift": all(
            specialist_drift[str(n)]["minimum_relevant_module_max_abs"] > 0.0
            for n in TEAM_SIZES
        ),
        "all_parameters_finite": shared_drift["all_parameters_finite"]
        and all(
            specialist_drift[str(n)]["all_parameters_finite"]
            for n in TEAM_SIZES
        ),
        "exact_final_checkpoint_reload": max(
            checkpoint_reload_errors.values()
        )
        == 0.0,
        "evaluation_counts_exact": all(
            len(
                final_evaluation[arm]["by_size"][str(n)]["episode_success"]
            )
            == eval_episodes
            for arm in ("shared", "specialists")
            for n in TEAM_SIZES
        ),
        "zero_step_pairing_exact": all(
            np.array_equal(
                np.asarray(
                    zero_evaluation["shared"]["by_size"][str(n)][
                        "episode_success"
                    ]
                ),
                np.asarray(
                    zero_evaluation["specialists"]["by_size"][str(n)][
                        "episode_success"
                    ]
                ),
            )
            for n in TEAM_SIZES
        ),
    }
    m0 = all(m0_checks.values())

    bootstrap_rng = np.random.default_rng(BOOTSTRAP_SEED)
    specialist_final_zero_ci: dict[str, Any] = {}
    specialist_block_means: dict[str, list[float]] = {}
    specialist_successes: dict[int, float] = {}
    shared_successes: dict[int, float] = {}
    for active_n in TEAM_SIZES:
        key = str(active_n)
        specialist_final = np.asarray(
            final_evaluation["specialists"]["by_size"][key][
                "episode_success"
            ],
            dtype=np.float64,
        )
        specialist_zero = np.asarray(
            zero_evaluation["specialists"]["by_size"][key][
                "episode_success"
            ],
            dtype=np.float64,
        )
        specialist_final_zero_ci[key] = paired_bootstrap_ci(
            specialist_final - specialist_zero, bootstrap_rng
        )
        specialist_block_means[key] = [
            float(block.mean())
            for block in np.split(specialist_final, 4)
        ]
        specialist_successes[active_n] = float(specialist_final.mean())
        shared_successes[active_n] = float(
            np.asarray(
                final_evaluation["shared"]["by_size"][key][
                    "episode_success"
                ],
                dtype=np.float64,
            ).mean()
        )
    specialist_macro = float(np.mean(list(specialist_successes.values())))
    shared_macro = float(np.mean(list(shared_successes.values())))
    m1_checks = {
        "specialist_each_n_success": all(
            specialist_successes[n] >= 0.60 for n in TEAM_SIZES
        ),
        "specialist_macro_success": specialist_macro >= 0.70,
        "specialist_each_n_final_zero_lcb": all(
            specialist_final_zero_ci[str(n)]["lower"] > 0.20
            for n in TEAM_SIZES
        ),
        "specialist_block_stability": all(
            sum(value >= 0.50 for value in specialist_block_means[str(n)]) >= 3
            for n in TEAM_SIZES
        ),
    }
    m1 = all(m1_checks.values())

    shared_specialist_ratios = {
        n: shared_successes[n] / (specialist_successes[n] + 1.0e-8)
        for n in TEAM_SIZES
    }
    shared_specialist_differences: dict[int, np.ndarray] = {}
    shared_final_zero_differences: dict[int, np.ndarray] = {}
    for active_n in TEAM_SIZES:
        key = str(active_n)
        shared_final = np.asarray(
            final_evaluation["shared"]["by_size"][key]["episode_success"],
            dtype=np.float64,
        )
        shared_zero = np.asarray(
            zero_evaluation["shared"]["by_size"][key]["episode_success"],
            dtype=np.float64,
        )
        specialist_final = np.asarray(
            final_evaluation["specialists"]["by_size"][key][
                "episode_success"
            ],
            dtype=np.float64,
        )
        shared_specialist_differences[active_n] = (
            shared_final - specialist_final
        )
        shared_final_zero_differences[active_n] = shared_final - shared_zero
    shared_specialist_macro_ci = macro_paired_bootstrap_ci(
        shared_specialist_differences, bootstrap_rng
    )
    shared_final_zero_macro_ci = macro_paired_bootstrap_ci(
        shared_final_zero_differences, bootstrap_rng
    )
    m2_checks = {
        "shared_each_n_success": all(
            shared_successes[n] >= 0.50 for n in TEAM_SIZES
        ),
        "shared_macro_success": shared_macro >= 0.65,
        "minimum_within_n_ratio": min(shared_specialist_ratios.values())
        >= 0.75,
        "macro_success_ratio": shared_macro / (specialist_macro + 1.0e-8)
        >= 0.85,
        "paired_macro_noninferiority_lcb": shared_specialist_macro_ci["lower"]
        > -0.10,
        "shared_final_zero_macro_lcb": shared_final_zero_macro_ci["lower"]
        > 0.25,
    }
    m2 = all(m2_checks.values())
    if args.dry_run:
        status = "PASS_R51_DRY_RUN" if m0 else "INVALID_R51_AMDT_WIRING"
    elif not m0:
        status = "INVALID_R51_AMDT_WIRING"
    elif not m1:
        status = "NO_ACCESS_R51_AMDT_SPECIALISTS"
    elif not m2:
        status = "VALID_FAIL_R51_SHARED_VARIABLE_N"
    else:
        status = "PASS_R51_AMDT_VARIABLE_N"

    result = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "dry_run": bool(args.dry_run),
        "dry_run_valid": bool(args.dry_run and m0),
        "implementation_valid": bool(m0),
        "m0": bool(m0),
        "m0_checks": m0_checks,
        "m1_specialist_access": bool(m1),
        "m1_checks": m1_checks,
        "m2_shared_variable_n": bool(m2),
        "m2_checks": m2_checks,
        "contract": {
            "team_sizes": list(TEAM_SIZES),
            "persistent_stations": {str(n): n // 2 for n in TEAM_SIZES},
            "dispatch_jobs": {str(n): n - n // 2 for n in TEAM_SIZES},
            "entities": {str(n): n + 1 for n in TEAM_SIZES},
            "horizon": HORIZON,
            "wave_starts": list(WAVE_STARTS),
            "job_deadline": JOB_DEADLINE,
            "station_health_max": STATION_HEALTH_MAX,
            "model_seed": MODEL_SEED,
            "training_reset_seed": TRAIN_RESET_SEED,
            "order_action_seed": ORDER_ACTION_SEED,
            "evaluation_seed": EVALUATION_SEED,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "balanced_cycles": cycles,
            "n_specific_batches": expected_updates,
            "batch_size": batch_size,
            "eval_episodes_per_n_per_arm": eval_episodes,
            "learning_rate": LEARNING_RATE,
            "gamma": GAMMA,
            "gae_lambda": GAE_LAMBDA,
            "ppo_epochs": PPO_EPOCHS,
            "entropy_coefficient": ENTROPY_COEFFICIENT,
            "value_coefficient": VALUE_COEFFICIENT,
            "ppo_clip": PPO_CLIP,
            "gradient_clip": GRADIENT_CLIP,
            "replay_tolerance": REPLAY_TOLERANCE,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "parameter_count": shared.parameter_count,
            "state_dict_shapes": model_shape_reference,
            **scope_counts,
        },
        "counts": {
            "schedule": schedule,
            "schedule_counts": schedule_counts,
            "transitions_per_arm": transitions_per_arm,
            "transitions_by_n_per_arm": transitions_by_n,
            "agent_token_decisions_per_arm": tokens_per_arm,
            "agent_tokens_by_n_per_arm": tokens_by_n,
            "shared_optimizer_steps": shared_optimizer_steps,
            "specialist_optimizer_steps_by_n": specialist_optimizer_steps,
            "specialist_optimizer_steps_total": sum(
                specialist_optimizer_steps.values()
            ),
            "paired_ledger_checks": paired_ledger_checks,
            "trajectory_storage_checks": trajectory_storage_checks,
            "reward_contract_checks": reward_contract_checks,
        },
        "probability": {
            "sample_replay_logp_max_error": maximum_replay_error,
            "prefix_replay_max_error": maximum_prefix_error,
            "masked_probability_mass_max": maximum_masked_mass,
        },
        "optimization": {
            "initial_state_max_errors": initial_errors,
            "shared_gradient_max_by_module": shared_gradient_max,
            "specialist_gradient_max_by_n": specialist_gradient_max,
            "shared_nonzero_gradient_steps": shared_nonzero_gradient_steps,
            "specialist_nonzero_gradient_steps_by_n": specialist_nonzero_gradient_steps,
            "shared_drift": shared_drift,
            "specialist_drift_by_n": specialist_drift,
            "checkpoint_reload_max_errors": checkpoint_reload_errors,
        },
        "evaluation": {
            "zero_step": zero_evaluation,
            "exact_final": final_evaluation,
            "specialist_success_by_n": specialist_successes,
            "specialist_macro_success": specialist_macro,
            "specialist_final_zero_ci_by_n": specialist_final_zero_ci,
            "specialist_block_means_by_n": specialist_block_means,
            "shared_success_by_n": shared_successes,
            "shared_macro_success": shared_macro,
            "shared_specialist_ratio_by_n": shared_specialist_ratios,
            "shared_specialist_macro_ratio": shared_macro
            / (specialist_macro + 1.0e-8),
            "shared_specialist_macro_difference_ci": shared_specialist_macro_ci,
            "shared_final_zero_macro_ci": shared_final_zero_macro_ci,
        },
        "elapsed_seconds": time.perf_counter() - started,
        "next_action": {
            "INVALID_R51_AMDT_WIRING": "repair only the named wiring defect and rerun the unchanged 625-step contract",
            "NO_ACCESS_R51_AMDT_SPECIALISTS": "retire the exact AMDT dynamics, horizon, and reset contract; quarantine shared results",
            "VALID_FAIL_R51_SHARED_VARIABLE_N": "retire the exact shared set-pointer MAPPO contract and stop for one failure review",
            "PASS_R51_AMDT_VARIABLE_N": "authorize only the same-task exogenous join/leave membership-censor gate",
            "PASS_R51_DRY_RUN": "freeze the implementation boundary and launch the registered formal gate",
        }[status],
    }
    _write_json(result_path, result)
    _write_json(
        progress_path,
        {
            "state": "completed",
            "update": expected_updates,
            "updates_total": expected_updates,
            "fraction": 1.0,
            "status": status,
            "result_path": str(result_path),
            "elapsed_seconds": result["elapsed_seconds"],
        },
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    result = run_gate(parse_args())
    print(
        f"R51 completed: status={result['status']} m0={result['m0']} "
        f"m1={result['m1_specialist_access']} "
        f"m2={result['m2_shared_variable_n']}"
    )


if __name__ == "__main__":
    main()
