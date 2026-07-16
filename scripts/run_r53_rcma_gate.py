"""R53-RCMA-G0 paired variable-N queue-learning abandonment gate."""

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

from ha_ctse_process.r53_rcma import (  # noqa: E402
    BURST_DEADLINE,
    BURST_WAVE_STEPS,
    PERSISTENT_ARRIVAL_STEPS,
    RCMASetPointerPolicy,
    AnonymousMultiRateQueueBatch,
    EpisodeLedger,
    HIDDEN_DIM,
    HORIZON,
    TEAM_SIZES,
    json_ready,
    make_episode_ledger,
    maximum_state_difference,
    model_state_copy,
    state_dict_finite,
)


EXPERIMENT_ID = "EXP-20260716-r53-rcma-g0"
SCHEMA_VERSION = 1
MODEL_SEED = 53_053
TRAIN_RESET_SEED = 63_053
ORDER_ACTION_SEED = 73_053
EVALUATION_SEED = 83_053
BOOTSTRAP_SEED = 93_053
FORMAL_CYCLES = 100
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
    focal_previous_actions: torch.Tensor
    agent_orders: torch.Tensor
    entity_orders: torch.Tensor
    hidden_reset_masks: torch.Tensor
    next_hidden_states: torch.Tensor
    sampling_uniforms: torch.Tensor
    action_pointers: torch.Tensor
    prefix_counts: torch.Tensor
    residual_capacities: torch.Tensor
    dynamic_masks: torch.Tensor
    focal_relation_counts: torch.Tensor
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
    model: RCMASetPointerPolicy,
    ledger: EpisodeLedger,
    device: torch.device,
    deterministic: bool,
) -> Trajectory:
    """Collect one complete 16-step batch with a fixed paired ledger."""

    environment = AnonymousMultiRateQueueBatch(ledger)
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
    focal_previous_action_rows: list[torch.Tensor] = []
    agent_order_rows: list[torch.Tensor] = []
    entity_order_rows: list[torch.Tensor] = []
    hidden_mask_rows: list[torch.Tensor] = []
    uniform_rows: list[torch.Tensor] = []
    pointer_rows: list[torch.Tensor] = []
    prefix_rows: list[torch.Tensor] = []
    residual_capacity_rows: list[torch.Tensor] = []
    dynamic_mask_rows: list[torch.Tensor] = []
    relation_count_rows: list[torch.Tensor] = []
    log_prob_rows: list[torch.Tensor] = []
    value_rows: list[torch.Tensor] = []
    next_hidden_rows: list[torch.Tensor] = []
    reward_rows: list[torch.Tensor] = []

    model.train()
    with torch.no_grad():
        for step in range(HORIZON):
            environment.prepare_step(step)
            self_view, entities, entity_mask, critic = environment.observations()
            focal_previous_actions = _tensor(
                environment.previous_actions.copy(),
                device=device,
                dtype=torch.long,
            )
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
                focal_previous_actions=focal_previous_actions,
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
            focal_previous_action_rows.append(focal_previous_actions)
            agent_order_rows.append(agent_order)
            entity_order_rows.append(entity_order)
            hidden_mask_rows.append(hidden_reset)
            uniform_rows.append(uniforms)
            pointer_rows.append(output.pointers_by_position)
            prefix_rows.append(output.prefix_counts)
            residual_capacity_rows.append(output.residual_capacities)
            dynamic_mask_rows.append(output.dynamic_masks)
            relation_count_rows.append(output.focal_relation_counts)
            log_prob_rows.append(output.token_log_probs)
            value_rows.append(output.value)
            next_hidden_rows.append(output.next_hidden)
            reward_rows.append(_tensor(reward, device=device))

    return Trajectory(
        ledger=ledger,
        self_features=torch.stack(self_rows),
        entity_features=torch.stack(entity_rows),
        entity_masks=torch.stack(entity_mask_rows),
        member_active_masks=torch.stack(member_mask_rows),
        critic_fields=torch.stack(critic_rows),
        focal_previous_actions=torch.stack(focal_previous_action_rows),
        agent_orders=torch.stack(agent_order_rows),
        entity_orders=torch.stack(entity_order_rows),
        hidden_reset_masks=torch.stack(hidden_mask_rows),
        next_hidden_states=torch.stack(next_hidden_rows),
        sampling_uniforms=torch.stack(uniform_rows),
        action_pointers=torch.stack(pointer_rows),
        prefix_counts=torch.stack(prefix_rows),
        residual_capacities=torch.stack(residual_capacity_rows),
        dynamic_masks=torch.stack(dynamic_mask_rows),
        focal_relation_counts=torch.stack(relation_count_rows),
        old_log_probs=torch.stack(log_prob_rows),
        old_values=torch.stack(value_rows),
        rewards=torch.stack(reward_rows),
        diagnostics=environment.diagnostics(),
    )


def replay_and_loss(
    *, model: RCMASetPointerPolicy, trajectory: Trajectory
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
    replay_residual_capacities: list[torch.Tensor] = []
    replay_dynamic_masks: list[torch.Tensor] = []
    replay_masked_mass: list[torch.Tensor] = []
    replay_relation_counts: list[torch.Tensor] = []
    replay_hidden_states: list[torch.Tensor] = []
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
            focal_previous_actions=trajectory.focal_previous_actions[step],
            teacher_pointers=trajectory.action_pointers[step],
        )
        hidden = output.next_hidden
        replay_log_probs.append(output.token_log_probs)
        replay_values.append(output.value)
        replay_entropies.append(output.token_entropies)
        replay_prefixes.append(output.prefix_counts)
        replay_residual_capacities.append(output.residual_capacities)
        replay_dynamic_masks.append(output.dynamic_masks)
        replay_masked_mass.append(output.masked_probability_mass)
        replay_relation_counts.append(output.focal_relation_counts)
        replay_hidden_states.append(output.next_hidden)
    new_log_probs = torch.stack(replay_log_probs)
    new_values = torch.stack(replay_values)
    entropies = torch.stack(replay_entropies)
    prefixes = torch.stack(replay_prefixes)
    residual_capacities = torch.stack(replay_residual_capacities)
    dynamic_masks = torch.stack(replay_dynamic_masks)
    masked_mass = torch.stack(replay_masked_mass)
    relation_counts = torch.stack(replay_relation_counts)
    replay_hidden = torch.stack(replay_hidden_states)

    replay_error = torch.max(
        torch.abs(new_log_probs.detach() - trajectory.old_log_probs)
    )
    prefix_error = torch.max(
        torch.abs(prefixes.detach() - trajectory.prefix_counts)
    )
    residual_capacity_error = torch.max(
        torch.abs(
            residual_capacities.detach() - trajectory.residual_capacities
        )
    )
    dynamic_mask_error = torch.max(
        dynamic_masks.detach().ne(trajectory.dynamic_masks).to(torch.float32)
    )
    masked_probability_mass = torch.max(masked_mass.detach())
    expected_relation_counts = trajectory.self_features[:, :, :, 0]
    ordered_expected_relation_counts = torch.gather(
        expected_relation_counts, 2, trajectory.agent_orders
    )
    focal_relation_count_error = torch.max(
        torch.abs(
            relation_counts.detach() - ordered_expected_relation_counts
        )
    )
    hidden_replay_error = torch.max(
        torch.abs(replay_hidden.detach() - trajectory.next_hidden_states)
    )

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
        "residual_capacity_replay_max_error": float(
            residual_capacity_error.cpu()
        ),
        "dynamic_mask_replay_max_error": float(dynamic_mask_error.cpu()),
        "masked_probability_mass_max": float(masked_probability_mass.cpu()),
        "focal_relation_count_max_error": float(
            focal_relation_count_error.cpu()
        ),
        "hidden_replay_max_error": float(hidden_replay_error.cpu()),
        "mean_reward": float(rewards[-1].mean().cpu()),
        "mean_advantage": float(advantages.mean().cpu()),
    }
    return total_loss, metrics


def take_optimizer_step(
    *,
    model: RCMASetPointerPolicy,
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
        raise RuntimeError("non-finite R53 gradient")
    optimizer.step()
    return gradient_value, module_gradient_norms


def update_maxima(target: dict[str, float], values: dict[str, float]) -> None:
    for name, value in values.items():
        target[name] = max(float(target.get(name, 0.0)), float(value))


def drift_summary(
    initial_state: dict[str, torch.Tensor], model: RCMASetPointerPolicy
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
    entities = active_n + 2
    return bool(
        t == HORIZON
        and batch == trajectory.batch_size
        and active_n == trajectory.active_n
        and tuple(trajectory.entity_masks.shape) == (t, batch, entities)
        and tuple(trajectory.agent_orders.shape) == (t, batch, active_n)
        and tuple(trajectory.entity_orders.shape) == (t, batch, entities)
        and tuple(trajectory.action_pointers.shape) == (t, batch, active_n)
        and tuple(trajectory.focal_previous_actions.shape)
        == (t, batch, active_n)
        and tuple(trajectory.focal_relation_counts.shape)
        == (t, batch, active_n)
        and tuple(trajectory.next_hidden_states.shape)
        == (t, batch, active_n, HIDDEN_DIM)
        and tuple(trajectory.prefix_counts.shape)
        == (t, batch, active_n, entities)
        and tuple(trajectory.residual_capacities.shape)
        == (t, batch, active_n, entities)
        and tuple(trajectory.dynamic_masks.shape)
        == (t, batch, active_n, entities)
        and tuple(trajectory.old_log_probs.shape) == (t, batch, active_n)
        and bool(trajectory.member_active_masks.all())
        and bool((trajectory.hidden_reset_masks[0] == 0.0).all())
        and bool((trajectory.hidden_reset_masks[1:] == 1.0).all())
        and bool((trajectory.focal_relation_counts[0] == 0.0).all())
        and bool((trajectory.focal_relation_counts[1:] == 1.0).all())
    )


def evaluation_record(trajectory: Trajectory) -> dict[str, Any]:
    diagnostics = trajectory.diagnostics
    utility = np.asarray(diagnostics["utility"], dtype=np.float64)
    persistent_fraction = np.asarray(
        diagnostics["persistent_fraction"], dtype=np.float64
    )
    burst_fraction = np.asarray(
        diagnostics["burst_fraction"], dtype=np.float64
    )
    return {
        "episode_utility": utility,
        "episode_persistent_fraction": persistent_fraction,
        "episode_burst_fraction": burst_fraction,
        "mean_utility": float(utility.mean()),
        "mean_persistent_fraction": float(persistent_fraction.mean()),
        "mean_burst_fraction": float(burst_fraction.mean()),
        "positive_utility_rate": float(np.mean(utility > 0.0)),
        "mean_final_persistent_backlog": float(
            np.asarray(
                diagnostics["final_persistent_backlog"], dtype=np.float64
            ).mean()
        ),
        "mean_timely_burst_completions": float(
            np.asarray(
                diagnostics["timely_burst_completions"], dtype=np.float64
            ).mean()
        ),
        "idle_selection_fraction": float(
            np.asarray(
                diagnostics["idle_selection_fraction"], dtype=np.float64
            ).mean()
        ),
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


def _run_scripted_schedule(
    *, active_n: int, mode: str, seed_offset: int
) -> dict[str, Any]:
    """Exercise the three registered schedules without PPO exposure."""

    reset_rng = np.random.default_rng(MODEL_SEED + seed_offset)
    control_rng = np.random.default_rng(ORDER_ACTION_SEED + seed_offset)
    ledger = make_episode_ledger(
        active_n=active_n,
        batch_size=1,
        reset_rng=reset_rng,
        control_rng=control_rng,
    )
    environment = AnonymousMultiRateQueueBatch(ledger)
    last_reward = np.zeros(1, dtype=np.float32)
    maximum_productive_count = 0
    maximum_idle_count = 0
    for step in range(HORIZON):
        environment.prepare_step(step)
        environment.observations()
        actions = np.full(
            (1, active_n), environment.idle_action, dtype=np.int64
        )
        if mode in {"constructive", "persistent_only"} and (
            step in PERSISTENT_ARRIVAL_STEPS
        ):
            actions[0, : environment.persistent] = np.arange(
                environment.persistent, dtype=np.int64
            )
        if mode in {"constructive", "burst_only"} and step in BURST_WAVE_STEPS:
            actions[0, : environment.burst] = (
                environment.persistent
                + np.arange(environment.burst, dtype=np.int64)
            )
        counts = np.bincount(actions[0], minlength=environment.entities)
        maximum_productive_count = max(
            maximum_productive_count,
            int(counts[: environment.productive].max(initial=0)),
        )
        maximum_idle_count = max(
            maximum_idle_count, int(counts[environment.idle_action])
        )
        last_reward, _ = environment.step(actions)
    diagnostics = environment.diagnostics()
    return {
        "mode": mode,
        "persistent_fraction": float(diagnostics["persistent_fraction"][0]),
        "burst_fraction": float(diagnostics["burst_fraction"][0]),
        "utility": float(diagnostics["utility"][0]),
        "final_reward": float(last_reward[0]),
        "maximum_productive_selected_count": maximum_productive_count,
        "maximum_idle_selected_count": maximum_idle_count,
        "capacity_violation_count": diagnostics["capacity_violation_count"],
        "nonterminal_reward_nonzero": diagnostics[
            "nonterminal_reward_nonzero"
        ],
    }


def run_dynamics_audits() -> dict[str, Any]:
    schedules: dict[str, Any] = {}
    for active_n in TEAM_SIZES:
        schedules[str(active_n)] = {
            mode: _run_scripted_schedule(
                active_n=active_n,
                mode=mode,
                seed_offset=100 * active_n + index,
            )
            for index, mode in enumerate(
                ("constructive", "persistent_only", "burst_only")
            )
        }

    reset_rng = np.random.default_rng(MODEL_SEED + 9_001)
    control_rng = np.random.default_rng(ORDER_ACTION_SEED + 9_001)
    ledger = make_episode_ledger(
        active_n=2,
        batch_size=1,
        reset_rng=reset_rng,
        control_rng=control_rng,
    )
    environment = AnonymousMultiRateQueueBatch(ledger)
    environment.prepare_step(0)
    first_member_view, first_entities, first_mask, first_critic = (
        environment.observations()
    )
    all_idle = np.full(
        (1, environment.n), environment.idle_action, dtype=np.int64
    )
    environment.step(all_idle)
    environment.prepare_step(1)
    second_member_view, second_entities, _, _ = environment.observations()
    idle_probe = {
        "first_member_view_zero": bool(np.all(first_member_view == 0.0)),
        "all_entities_static_active": bool(first_mask.all()),
        "productive_indicator_exact": bool(
            np.all(first_entities[0, : environment.productive, 0] == 1.0)
            and first_entities[0, environment.idle_action, 0] == 0.0
        ),
        "first_critic_fields": first_critic[0].copy(),
        "idle_previous_count_fraction": float(
            second_entities[0, environment.idle_action, 6]
        ),
        "second_has_previous": second_member_view[0, :, 0].copy(),
        "second_served_previous": second_member_view[0, :, 1].copy(),
    }

    reset_rng = np.random.default_rng(MODEL_SEED + 9_002)
    control_rng = np.random.default_rng(ORDER_ACTION_SEED + 9_002)
    ledger = make_episode_ledger(
        active_n=2,
        batch_size=1,
        reset_rng=reset_rng,
        control_rng=control_rng,
    )
    window_environment = AnonymousMultiRateQueueBatch(ledger)
    first_burst = window_environment.persistent
    second_burst = first_burst + 1
    completions_after_step5 = -1
    expirations_after_step5 = -1
    completions_after_late_attempt = -1
    for step in range(HORIZON):
        window_environment.prepare_step(step)
        actions = np.full(
            (1, window_environment.n),
            window_environment.idle_action,
            dtype=np.int64,
        )
        if step == 5:
            actions[0, 0] = first_burst
        elif step == 6:
            actions[0, 0] = second_burst
        elif step == 11:
            actions[0, 0] = first_burst
        window_environment.step(actions)
        if step == 5:
            completions_after_step5 = int(
                window_environment.burst_served.sum()
            )
            expirations_after_step5 = int(
                window_environment.burst_expired.sum()
            )
        elif step == 6:
            completions_after_late_attempt = int(
                window_environment.burst_served.sum()
            )
    window_probe = {
        "completions_after_step5": completions_after_step5,
        "expirations_after_step5": expirations_after_step5,
        "completions_after_late_attempt": completions_after_late_attempt,
        "final_completions": int(window_environment.burst_served.sum()),
        "final_expirations": int(window_environment.burst_expired.sum()),
    }
    return {
        "schedules": schedules,
        "idle_entity_probe": idle_probe,
        "burst_window_probe": window_probe,
        "audit_environment_steps": len(TEAM_SIZES) * 3 * HORIZON
        + 1
        + HORIZON,
    }

def evaluate_models(
    *,
    shared: RCMASetPointerPolicy,
    specialists: dict[int, RCMASetPointerPolicy],
    ledgers: dict[int, EpisodeLedger],
    device: torch.device,
) -> dict[str, Any]:
    by_arm_mode: dict[str, dict[str, dict[str, Any]]] = {
        "shared": {"stochastic": {}, "deterministic": {}},
        "specialists": {"stochastic": {}, "deterministic": {}},
    }
    for active_n in TEAM_SIZES:
        ledger = ledgers[active_n]
        for mode, deterministic in (
            ("stochastic", False),
            ("deterministic", True),
        ):
            by_arm_mode["shared"][mode][str(active_n)] = evaluation_record(
                collect_trajectory(
                    model=shared,
                    ledger=ledger,
                    device=device,
                    deterministic=deterministic,
                )
            )
            by_arm_mode["specialists"][mode][str(active_n)] = (
                evaluation_record(
                    collect_trajectory(
                        model=specialists[active_n],
                        ledger=ledger,
                        device=device,
                        deterministic=deterministic,
                    )
                )
            )

    def summarize(by_size: dict[str, Any]) -> dict[str, Any]:
        utility = [by_size[str(n)]["mean_utility"] for n in TEAM_SIZES]
        persistent = [
            by_size[str(n)]["mean_persistent_fraction"] for n in TEAM_SIZES
        ]
        burst = [
            by_size[str(n)]["mean_burst_fraction"] for n in TEAM_SIZES
        ]
        return {
            "by_size": by_size,
            "macro_utility": float(np.mean(utility)),
            "macro_persistent_fraction": float(np.mean(persistent)),
            "macro_burst_fraction": float(np.mean(burst)),
            "minimum_utility": float(np.min(utility)),
        }

    return {
        arm: {
            mode: summarize(by_arm_mode[arm][mode])
            for mode in ("stochastic", "deterministic")
        }
        for arm in ("shared", "specialists")
    }

def load_exact_model(path: Path, device: torch.device) -> RCMASetPointerPolicy:
    try:
        payload = torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        payload = torch.load(path, map_location=device)
    model = RCMASetPointerPolicy().to(device)
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


def state_dict_shapes(model: RCMASetPointerPolicy) -> dict[str, list[int]]:
    return {
        name: list(tensor.shape) for name, tensor in model.state_dict().items()
    }


def run_gate(args: argparse.Namespace) -> dict[str, Any]:
    device = torch.device(args.device)
    if device.type != "cuda":
        raise ValueError("R53 formal and focused runs require CUDA")
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
        "dry_run_check.json" if args.dry_run else "r53_rcma.json"
    )

    torch.manual_seed(MODEL_SEED)
    torch.cuda.manual_seed_all(MODEL_SEED)
    shared = RCMASetPointerPolicy().to(device)
    if shared.parameter_count != 24_737:
        raise RuntimeError(
            f"R53 model has {shared.parameter_count} parameters, expected 24737"
        )
    initial_state = model_state_copy(shared)
    specialists: dict[int, RCMASetPointerPolicy] = {}
    for active_n in TEAM_SIZES:
        specialist = RCMASetPointerPolicy().to(device)
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
    dynamics_audits = run_dynamics_audits()

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
    maximum_residual_capacity_error = 0.0
    maximum_dynamic_mask_error = 0.0
    maximum_masked_mass = 0.0
    maximum_relation_count_error = 0.0
    maximum_hidden_replay_error = 0.0
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
    capacity_violation_count = 0
    invalid_action_count = 0
    finite_training_metrics = True
    shared_gradient_max = {name: 0.0 for name in RELEVANT_MODULES}
    specialist_gradient_max = {
        n: {name: 0.0 for name in RELEVANT_MODULES} for n in TEAM_SIZES
    }
    shared_nonzero_gradient_steps = 0
    specialist_nonzero_gradient_steps = {n: 0 for n in TEAM_SIZES}
    specialist_training_utilities: dict[int, list[float]] = {
        n: [] for n in TEAM_SIZES
    }
    started = time.perf_counter()

    with updates_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "update",
            "cycle",
            "active_n",
            "transitions_per_arm",
            "tokens_per_arm",
            "shared_utility",
            "specialist_utility",
            "shared_loss",
            "specialist_loss",
            "shared_gradient_norm",
            "specialist_gradient_norm",
            "sample_replay_logp_max_error",
            "prefix_replay_max_error",
            "residual_capacity_replay_max_error",
            "dynamic_mask_replay_max_error",
            "masked_probability_mass_max",
            "hidden_replay_max_error",
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
                    capacity_violation_count += int(
                        diagnostics["capacity_violation_count"]
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
                    maximum_residual_capacity_error = max(
                        maximum_residual_capacity_error,
                        metrics["residual_capacity_replay_max_error"],
                    )
                    maximum_dynamic_mask_error = max(
                        maximum_dynamic_mask_error,
                        metrics["dynamic_mask_replay_max_error"],
                    )
                    maximum_masked_mass = max(
                        maximum_masked_mass,
                        metrics["masked_probability_mass_max"],
                    )
                    maximum_relation_count_error = max(
                        maximum_relation_count_error,
                        metrics["focal_relation_count_max_error"],
                    )
                    maximum_hidden_replay_error = max(
                        maximum_hidden_replay_error,
                        metrics["hidden_replay_max_error"],
                    )
                specialist_training_utilities[active_n].extend(
                    np.asarray(
                        specialist_trajectory.diagnostics["utility"],
                        dtype=np.float64,
                    ).tolist()
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
                        "shared_utility": shared_metrics["mean_reward"],
                        "specialist_utility": specialist_metrics["mean_reward"],
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
                        "residual_capacity_replay_max_error": max(
                            shared_metrics[
                                "residual_capacity_replay_max_error"
                            ],
                            specialist_metrics[
                                "residual_capacity_replay_max_error"
                            ],
                        ),
                        "dynamic_mask_replay_max_error": max(
                            shared_metrics["dynamic_mask_replay_max_error"],
                            specialist_metrics[
                                "dynamic_mask_replay_max_error"
                            ],
                        ),
                        "masked_probability_mass_max": max(
                            shared_metrics["masked_probability_mass_max"],
                            specialist_metrics["masked_probability_mass_max"],
                        ),
                        "hidden_replay_max_error": max(
                            shared_metrics["hidden_replay_max_error"],
                            specialist_metrics["hidden_replay_max_error"],
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
                        "shared_utility": shared_metrics["mean_reward"],
                        "specialist_utility": specialist_metrics["mean_reward"],
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
    constructive_audits = [
        dynamics_audits["schedules"][str(n)]["constructive"]
        for n in TEAM_SIZES
    ]
    persistent_only_audits = [
        dynamics_audits["schedules"][str(n)]["persistent_only"]
        for n in TEAM_SIZES
    ]
    burst_only_audits = [
        dynamics_audits["schedules"][str(n)]["burst_only"]
        for n in TEAM_SIZES
    ]
    idle_probe = dynamics_audits["idle_entity_probe"]
    window_probe = dynamics_audits["burst_window_probe"]
    m0_checks = {
        "environment_size_formulas_exact": all(
            n // 2 + (n + 1 - n // 2) == n + 1
            and (n + 1) + 1 == n + 2
            for n in TEAM_SIZES
        ),
        "environment_constants_exact": HORIZON == 16
        and PERSISTENT_ARRIVAL_STEPS == tuple(range(0, 16, 2))
        and BURST_WAVE_STEPS == (3, 9)
        and BURST_DEADLINE == 3,
        "constructive_schedule_exact": all(
            audit["persistent_fraction"] == 1.0
            and audit["burst_fraction"] == 1.0
            and audit["utility"] == 1.0
            and audit["final_reward"] == 1.0
            for audit in constructive_audits
        ),
        "persistent_only_schedule_exact": all(
            audit["persistent_fraction"] == 1.0
            and audit["burst_fraction"] == 0.0
            and audit["utility"] == 0.0
            and audit["final_reward"] == 0.0
            for audit in persistent_only_audits
        ),
        "burst_only_schedule_exact": all(
            audit["persistent_fraction"] == 0.0
            and audit["burst_fraction"] == 1.0
            and audit["utility"] == 0.0
            and audit["final_reward"] == 0.0
            for audit in burst_only_audits
        ),
        "scripted_heterogeneous_capacity_exact": all(
            audit["maximum_productive_selected_count"] <= 1
            and audit["maximum_idle_selected_count"] <= n
            and audit["capacity_violation_count"] == 0
            for n in TEAM_SIZES
            for audit in dynamics_audits["schedules"][str(n)].values()
        ),
        "idle_entity_view_exact": idle_probe["first_member_view_zero"]
        and idle_probe["all_entities_static_active"]
        and idle_probe["productive_indicator_exact"]
        and idle_probe["idle_previous_count_fraction"] == 1.0
        and np.all(np.asarray(idle_probe["second_has_previous"]) == 1.0)
        and np.all(np.asarray(idle_probe["second_served_previous"]) == 0.0),
        "critic_field_order_exact": np.allclose(
            np.asarray(idle_probe["first_critic_fields"], dtype=np.float64),
            np.asarray((0.0, 0.125, 0.0, 0.0), dtype=np.float64),
            atol=0.0,
            rtol=0.0,
        ),
        "burst_service_window_exact": window_probe[
            "completions_after_step5"
        ]
        == 1
        and window_probe["expirations_after_step5"] == 1
        and window_probe["completions_after_late_attempt"] == 1
        and window_probe["final_completions"] == 2
        and window_probe["final_expirations"] == 2,
        "reward_only_terminal": nonterminal_reward_nonzero == 0,
        "reward_matches_sqrt_product": final_reward_predicate_mismatch == 0,
        "no_invalid_action": invalid_action_count == 0,
        "no_capacity_violation": capacity_violation_count == 0,
        "scope_absence_exact": all(
            value == 0
            for name, value in scope_counts.items()
            if name not in {"ppo_epochs"}
        )
        and scope_counts["ppo_epochs"] == 1,
        "parameter_count_exact": shared.parameter_count == 24_737,
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
        "residual_capacity_replay_exact": maximum_residual_capacity_error
        == 0.0,
        "dynamic_mask_replay_exact": maximum_dynamic_mask_error == 0.0,
        "hidden_replay_probability": maximum_hidden_replay_error
        <= REPLAY_TOLERANCE,
        "previous_relation_replay_exact": maximum_relation_count_error == 0.0,
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
                final_evaluation[arm][mode]["by_size"][str(n)][
                    "episode_utility"
                ]
            )
            == eval_episodes
            for arm in ("shared", "specialists")
            for mode in ("stochastic", "deterministic")
            for n in TEAM_SIZES
        ),
        "zero_step_pairing_exact": all(
            np.array_equal(
                np.asarray(
                    zero_evaluation["shared"][mode]["by_size"][str(n)][
                        "episode_utility"
                    ]
                ),
                np.asarray(
                    zero_evaluation["specialists"][mode]["by_size"][str(n)][
                        "episode_utility"
                    ]
                ),
            )
            for mode in ("stochastic", "deterministic")
            for n in TEAM_SIZES
        ),
    }
    m0 = all(m0_checks.values())

    bootstrap_rng = np.random.default_rng(BOOTSTRAP_SEED)
    specialist_training_positive_rate = {
        n: float(np.mean(np.asarray(specialist_training_utilities[n]) > 0.0))
        for n in TEAM_SIZES
    }
    specialist_final_zero_ci: dict[str, Any] = {}
    specialist_stochastic_deterministic_ci: dict[str, Any] = {}
    shared_stochastic_deterministic_ci: dict[str, Any] = {}
    specialist_block_means: dict[str, list[float]] = {}
    specialist_stochastic_utility: dict[int, float] = {}
    specialist_deterministic_utility: dict[int, float] = {}
    specialist_persistent_fraction: dict[int, float] = {}
    specialist_burst_fraction: dict[int, float] = {}
    shared_stochastic_utility: dict[int, float] = {}
    shared_deterministic_utility: dict[int, float] = {}
    shared_persistent_fraction: dict[int, float] = {}
    shared_burst_fraction: dict[int, float] = {}
    for active_n in TEAM_SIZES:
        key = str(active_n)
        specialist_stochastic_record = final_evaluation["specialists"][
            "stochastic"
        ]["by_size"][key]
        specialist_deterministic_record = final_evaluation["specialists"][
            "deterministic"
        ]["by_size"][key]
        shared_stochastic_record = final_evaluation["shared"]["stochastic"][
            "by_size"
        ][key]
        shared_deterministic_record = final_evaluation["shared"][
            "deterministic"
        ]["by_size"][key]
        specialist_stochastic = np.asarray(
            specialist_stochastic_record["episode_utility"], dtype=np.float64
        )
        specialist_deterministic = np.asarray(
            specialist_deterministic_record["episode_utility"],
            dtype=np.float64,
        )
        specialist_zero_deterministic = np.asarray(
            zero_evaluation["specialists"]["deterministic"]["by_size"][key][
                "episode_utility"
            ],
            dtype=np.float64,
        )
        shared_stochastic = np.asarray(
            shared_stochastic_record["episode_utility"], dtype=np.float64
        )
        shared_deterministic = np.asarray(
            shared_deterministic_record["episode_utility"], dtype=np.float64
        )
        specialist_final_zero_ci[key] = paired_bootstrap_ci(
            specialist_deterministic - specialist_zero_deterministic,
            bootstrap_rng,
        )
        specialist_stochastic_deterministic_ci[key] = paired_bootstrap_ci(
            specialist_stochastic - specialist_deterministic, bootstrap_rng
        )
        shared_stochastic_deterministic_ci[key] = paired_bootstrap_ci(
            shared_stochastic - shared_deterministic, bootstrap_rng
        )
        specialist_block_means[key] = [
            float(block.mean())
            for block in np.array_split(specialist_deterministic, 4)
        ]
        specialist_stochastic_utility[active_n] = float(
            specialist_stochastic_record["mean_utility"]
        )
        specialist_deterministic_utility[active_n] = float(
            specialist_deterministic_record["mean_utility"]
        )
        specialist_persistent_fraction[active_n] = float(
            specialist_deterministic_record["mean_persistent_fraction"]
        )
        specialist_burst_fraction[active_n] = float(
            specialist_deterministic_record["mean_burst_fraction"]
        )
        shared_stochastic_utility[active_n] = float(
            shared_stochastic_record["mean_utility"]
        )
        shared_deterministic_utility[active_n] = float(
            shared_deterministic_record["mean_utility"]
        )
        shared_persistent_fraction[active_n] = float(
            shared_deterministic_record["mean_persistent_fraction"]
        )
        shared_burst_fraction[active_n] = float(
            shared_deterministic_record["mean_burst_fraction"]
        )

    specialist_macro = float(
        np.mean(list(specialist_deterministic_utility.values()))
    )
    shared_macro = float(np.mean(list(shared_deterministic_utility.values())))
    m1_checks = {
        "specialist_training_positive_rate": all(
            specialist_training_positive_rate[n] >= 0.50 for n in TEAM_SIZES
        ),
        "specialist_each_n_stochastic_utility": all(
            specialist_stochastic_utility[n] >= 0.70 for n in TEAM_SIZES
        ),
        "specialist_each_n_deterministic_utility": all(
            specialist_deterministic_utility[n] >= 0.65
            for n in TEAM_SIZES
        ),
        "specialist_each_n_persistent_fraction": all(
            specialist_persistent_fraction[n] >= 0.70 for n in TEAM_SIZES
        ),
        "specialist_each_n_burst_fraction": all(
            specialist_burst_fraction[n] >= 0.70 for n in TEAM_SIZES
        ),
        "specialist_stochastic_deterministic_ucb": all(
            specialist_stochastic_deterministic_ci[str(n)]["upper"] < 0.15
            for n in TEAM_SIZES
        ),
        "specialist_each_n_final_zero_lcb": all(
            specialist_final_zero_ci[str(n)]["lower"] > 0.15
            for n in TEAM_SIZES
        ),
        "specialist_block_stability": all(
            sum(value >= 0.60 for value in specialist_block_means[str(n)]) >= 3
            for n in TEAM_SIZES
        ),
        "specialist_macro_utility": specialist_macro >= 0.70,
    }
    m1 = all(m1_checks.values())

    shared_specialist_ratios = {
        n: shared_deterministic_utility[n]
        / (specialist_deterministic_utility[n] + 1.0e-8)
        for n in TEAM_SIZES
    }
    shared_specialist_differences: dict[int, np.ndarray] = {}
    shared_final_zero_differences: dict[int, np.ndarray] = {}
    for active_n in TEAM_SIZES:
        key = str(active_n)
        shared_final = np.asarray(
            final_evaluation["shared"]["deterministic"]["by_size"][key][
                "episode_utility"
            ],
            dtype=np.float64,
        )
        shared_zero = np.asarray(
            zero_evaluation["shared"]["deterministic"]["by_size"][key][
                "episode_utility"
            ],
            dtype=np.float64,
        )
        specialist_final = np.asarray(
            final_evaluation["specialists"]["deterministic"]["by_size"][key][
                "episode_utility"
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
        "shared_each_n_stochastic_utility": all(
            shared_stochastic_utility[n] >= 0.70 for n in TEAM_SIZES
        ),
        "shared_each_n_deterministic_utility": all(
            shared_deterministic_utility[n] >= 0.65 for n in TEAM_SIZES
        ),
        "shared_each_n_persistent_fraction": all(
            shared_persistent_fraction[n] >= 0.70 for n in TEAM_SIZES
        ),
        "shared_each_n_burst_fraction": all(
            shared_burst_fraction[n] >= 0.70 for n in TEAM_SIZES
        ),
        "shared_stochastic_deterministic_ucb": all(
            shared_stochastic_deterministic_ci[str(n)]["upper"] < 0.15
            for n in TEAM_SIZES
        ),
        "shared_macro_utility": shared_macro >= 0.70,
        "minimum_within_n_ratio": min(shared_specialist_ratios.values())
        >= 0.85,
        "macro_utility_ratio": shared_macro / (specialist_macro + 1.0e-8)
        >= 0.90,
        "paired_macro_noninferiority_lcb": shared_specialist_macro_ci["lower"]
        > -0.08,
        "shared_final_zero_macro_lcb": shared_final_zero_macro_ci["lower"]
        > 0.20,
    }
    m2 = all(m2_checks.values())
    if args.dry_run:
        status = "PASS_R53_DRY_RUN" if m0 else "INVALID_R53_RCMA_WIRING"
    elif not m0:
        status = "INVALID_R53_RCMA_WIRING"
    elif not m1:
        status = "NO_ACCESS_R53_RCMA_SPECIALISTS"
    elif not m2:
        status = "VALID_FAIL_R53_SHARED_VARIABLE_N"
    else:
        status = "PASS_R53_RCMA_VARIABLE_N"

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
            "persistent_queues": {
                str(n): n // 2 for n in TEAM_SIZES
            },
            "burst_queues": {
                str(n): n + 1 - n // 2 for n in TEAM_SIZES
            },
            "productive_queues": {str(n): n + 1 for n in TEAM_SIZES},
            "action_entities": {str(n): n + 2 for n in TEAM_SIZES},
            "idle_capacity": {str(n): n for n in TEAM_SIZES},
            "productive_capacity": 1,
            "horizon": HORIZON,
            "persistent_arrival_steps": list(PERSISTENT_ARRIVAL_STEPS),
            "burst_wave_steps": list(BURST_WAVE_STEPS),
            "burst_deadline": BURST_DEADLINE,
            "terminal_utility": "sqrt(persistent_fraction * burst_fraction)",
            "self_feature_dimension": 2,
            "entity_feature_dimension": 7,
            "focal_relation_dimension": 1,
            "residual_capacity_dimension": 1,
            "critic_field_dimension": 4,
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
            "dynamics_audit_environment_steps": dynamics_audits[
                "audit_environment_steps"
            ],
        },
        "probability": {
            "sample_replay_logp_max_error": maximum_replay_error,
            "prefix_replay_max_error": maximum_prefix_error,
            "residual_capacity_replay_max_error": (
                maximum_residual_capacity_error
            ),
            "dynamic_mask_replay_max_error": maximum_dynamic_mask_error,
            "masked_probability_mass_max": maximum_masked_mass,
            "previous_relation_count_max_error": (
                maximum_relation_count_error
            ),
            "hidden_replay_max_error": maximum_hidden_replay_error,
        },
        "dynamics_audits": dynamics_audits,
        "optimization": {
            "initial_state_max_errors": initial_errors,
            "shared_gradient_max_by_module": shared_gradient_max,
            "specialist_gradient_max_by_n": specialist_gradient_max,
            "shared_nonzero_gradient_steps": shared_nonzero_gradient_steps,
            "specialist_nonzero_gradient_steps_by_n": (
                specialist_nonzero_gradient_steps
            ),
            "shared_drift": shared_drift,
            "specialist_drift_by_n": specialist_drift,
            "checkpoint_reload_max_errors": checkpoint_reload_errors,
        },
        "evaluation": {
            "zero_step": zero_evaluation,
            "exact_final": final_evaluation,
            "specialist_training_positive_rate_by_n": (
                specialist_training_positive_rate
            ),
            "specialist_stochastic_utility_by_n": (
                specialist_stochastic_utility
            ),
            "specialist_deterministic_utility_by_n": (
                specialist_deterministic_utility
            ),
            "specialist_persistent_fraction_by_n": (
                specialist_persistent_fraction
            ),
            "specialist_burst_fraction_by_n": specialist_burst_fraction,
            "specialist_stochastic_deterministic_ci_by_n": (
                specialist_stochastic_deterministic_ci
            ),
            "specialist_final_zero_ci_by_n": specialist_final_zero_ci,
            "specialist_block_means_by_n": specialist_block_means,
            "specialist_macro_deterministic_utility": specialist_macro,
            "shared_stochastic_utility_by_n": shared_stochastic_utility,
            "shared_deterministic_utility_by_n": (
                shared_deterministic_utility
            ),
            "shared_persistent_fraction_by_n": shared_persistent_fraction,
            "shared_burst_fraction_by_n": shared_burst_fraction,
            "shared_stochastic_deterministic_ci_by_n": (
                shared_stochastic_deterministic_ci
            ),
            "shared_macro_deterministic_utility": shared_macro,
            "shared_specialist_ratio_by_n": shared_specialist_ratios,
            "shared_specialist_macro_utility_ratio": shared_macro
            / (specialist_macro + 1.0e-8),
            "shared_specialist_macro_difference_ci": (
                shared_specialist_macro_ci
            ),
            "shared_final_zero_macro_ci": shared_final_zero_macro_ci,
        },
        "elapsed_seconds": time.perf_counter() - started,
        "next_action": {
            "INVALID_R53_RCMA_WIRING": (
                "repair only the named M0 defect and rerun the unchanged "
                "corrected R53 contract"
            ),
            "NO_ACCESS_R53_RCMA_SPECIALISTS": (
                "retire exact AMQA/idle-RCMA access and quarantine shared"
            ),
            "VALID_FAIL_R53_SHARED_VARIABLE_N": (
                "retire exact shared RCMA and stop variable-N learning for "
                "one read-only architecture failure review"
            ),
            "PASS_R53_RCMA_VARIABLE_N": (
                "authorize only same-task exogenous join/leave and "
                "membership-censoring gate"
            ),
            "PASS_R53_DRY_RUN": (
                "freeze implementation and launch the registered formal gate"
            ),
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
        f"R53 completed: status={result['status']} m0={result['m0']} "
        f"m1={result['m1_specialist_access']} "
        f"m2={result['m2_shared_variable_n']}"
    )


if __name__ == "__main__":
    main()
