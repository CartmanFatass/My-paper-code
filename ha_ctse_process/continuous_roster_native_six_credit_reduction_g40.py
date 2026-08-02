"""Frozen native-six G31 versus team-GAE1 credit realization for G40-P0."""

from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from envs.continuous_roster import cpp_backend as toy_cpp
from envs.continuous_roster import runtime_capacity as roster_env
from ha_ctse_process import continuous_roster_native_six_coordinate_training_g39 as g39
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import continuous_roster_reactive_reduction_g35 as g35
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from ha_ctse_process.continuous_roster_seed import (
    bootstrap_seed_from_base,
    seed_block_from_bases,
)
from ha_ctse_process.anchored_residual_g19 import (
    ENTROPY_COEFFICIENT,
    PPO_CLIP,
    VALUE_COEFFICIENT,
    AnchoredRosterTrajectory,
    normalize_advantage,
    replay_errors,
    replay_trajectory,
)
from ha_ctse_process.direction_balanced_full_actor_g30 import (
    compose_direction_balanced_gradients,
)


ALGORITHM_ID = "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40"
SOURCE_ID = "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_P0"
G31_ARM = "NATIVE6_G31"
GAE1_ARM = "NATIVE6_TEAM_GAE1"
ARMS = (G31_ARM, GAE1_ARM)

GAMMA = 0.99
GAE_LAMBDA = 1.0
LEARNING_RATE = 1e-3
GRADIENT_LIVE_TOLERANCE = 1e-12
GAE_IDENTITY_TOLERANCE = 1e-6
FORWARD_TOLERANCE = 1e-7
LOG_PROB_TOLERANCE = 1e-6
NONFORMAL_SEED_OFFSET = 900_000

REGISTERED_ACTOR_GROUPS = (
    "member_encoder",
    "context_encoder",
    "gated_cell_input_weights",
    "gated_cell_recurrent_weights",
    "gated_cell_biases",
    "action_head",
    "current_readout",
    "log_std",
)
REGISTERED_TRAINABLE_GROUPS = (
    *REGISTERED_ACTOR_GROUPS,
    "centralized_slow_critic",
    "immediate_baseline",
    "successor_baseline",
)

SEED_BASES = {
    "anchor_model": 10_401_000,
    "anchor_ledger": 10_402_000,
    "anchor_action": 10_403_000,
    "branch_ledger": 10_404_000,
    "branch_action": 10_405_000,
    "branch_gradient_probe": 10_406_000,
    "evaluation_base_ledger": 10_407_000,
    "evaluation_process": 10_408_000,
    "evaluation_action": 10_409_000,
}
BOOTSTRAP_SEED = 10_410_040


def seed_block(replicate: int, *, formal: bool) -> dict[str, int]:
    if not 0 <= int(replicate) < 3:
        raise ValueError("G40 replicate outside registered support")
    return seed_block_from_bases(
        SEED_BASES,
        int(replicate),
        formal=formal,
        nonformal_offset=NONFORMAL_SEED_OFFSET,
    )


def bootstrap_seed(*, formal: bool) -> int:
    return bootstrap_seed_from_base(
        BOOTSTRAP_SEED,
        formal=formal,
        nonformal_offset=NONFORMAL_SEED_OFFSET,
    )


class G40NativeSixPolicy(g39.G39NativeSixPolicy):
    """Accepted G39 native-six model with its shared two-output baseline."""

    def __init__(self, *, member_capacity: int) -> None:
        super().__init__(member_capacity=int(member_capacity))
        self._accepted_g39_initial_baseline_state_equal = False

    def actor_credit_parameters(self) -> tuple[nn.Parameter, ...]:
        return self.full_actor_parameters() + tuple(
            self.credit_baselines.parameters()
        )

    def slow_critic_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(self.slow_critic.parameters())

    def begin_credit_branch_phase(self) -> None:
        if self.phase != "fast":
            raise RuntimeError("G40 credit branch may begin exactly once")
        if self.residual_output_layer_maximum_absolute_value() != 0.0:
            raise RuntimeError("G40 residual must remain exact zero")
        for name, parameter in self.policy.named_parameters():
            parameter.requires_grad_(
                not name.startswith("delayed_residual.")
                and not name.startswith("critic.")
            )
        for parameter in self.slow_critic.parameters():
            parameter.requires_grad_(True)
        for parameter in self.credit_baselines.parameters():
            parameter.requires_grad_(True)
        self.phase = "credit_branch"


def _new_shell(member_capacity: int) -> G40NativeSixPolicy:
    rng_state = torch.random.get_rng_state()
    try:
        return G40NativeSixPolicy(member_capacity=int(member_capacity))
    finally:
        torch.random.set_rng_state(rng_state)


def make_model(
    member_capacity: int, *, initialization_seed: int
) -> G40NativeSixPolicy:
    """Create an exact accepted G39 native-six initialization."""

    base = g39.make_paired_models(
        int(member_capacity), initialization_seed=int(initialization_seed)
    )[g39.NATIVE6_ARM]
    model = _new_shell(int(member_capacity))
    model.load_state_dict(base.state_dict(), strict=True)
    if state_bytes(model) != state_bytes(base):
        raise RuntimeError("G40 initialization is not byte-identical to G39 native")
    if baseline_inventory(model) != baseline_inventory(base):
        raise RuntimeError("G40 baseline inventory differs from accepted G39")
    if state_bytes(model.credit_baselines) != state_bytes(base.credit_baselines):
        raise RuntimeError("G40 baseline state differs from accepted G39")
    model._accepted_g39_initial_baseline_state_equal = True
    model.phase = "fast"
    return model


def clone_anchor_models(
    anchor: G40NativeSixPolicy,
) -> dict[str, G40NativeSixPolicy]:
    arms = {arm: copy.deepcopy(anchor) for arm in ARMS}
    if shared_tensor_storage_count((anchor, *arms.values())) != 0:
        raise RuntimeError("G40 anchor clones share tensor storage")
    return arms


def _tensor_rows(
    rows: Iterable[tuple[str, torch.Tensor]],
) -> tuple[tuple[str, str, tuple[int, ...], bytes], ...]:
    return tuple(
        (
            name,
            str(value.dtype),
            tuple(value.shape),
            value.detach().cpu().contiguous().numpy().tobytes(),
        )
        for name, value in rows
    )


def state_bytes(model: nn.Module) -> tuple[tuple[str, str, tuple[int, ...], bytes], ...]:
    return _tensor_rows(model.state_dict().items())


def buffer_bytes(model: nn.Module) -> tuple[tuple[str, str, tuple[int, ...], bytes], ...]:
    return _tensor_rows(model.named_buffers())


def shared_tensor_storage_count(models: Sequence[nn.Module]) -> int:
    tensors = [tuple(model.parameters()) + tuple(model.buffers()) for model in models]
    return sum(
        int(left.data_ptr() == right.data_ptr())
        for left_index, left_rows in enumerate(tensors)
        for right_rows in tensors[left_index + 1 :]
        for left in left_rows
        for right in right_rows
    )


def _named_full_actor_parameters(
    model: G40NativeSixPolicy,
) -> tuple[tuple[str, nn.Parameter], ...]:
    return tuple(
        (f"policy.{name}", parameter)
        for name, parameter in model.policy.named_parameters()
        if not name.startswith("delayed_residual.")
        and not name.startswith("critic.")
    )


def actor_credit_parameter_names(model: G40NativeSixPolicy) -> tuple[str, ...]:
    return tuple(name for name, _ in _named_full_actor_parameters(model)) + tuple(
        name
        for name, _ in model.named_parameters()
        if name.startswith("credit_baselines.")
    )


def slow_critic_parameter_names(model: G40NativeSixPolicy) -> tuple[str, ...]:
    return tuple(
        name
        for name, _ in model.named_parameters()
        if name.startswith("slow_critic.")
    )


def baseline_inventory(model: g39.G39NativeSixPolicy) -> dict[str, object]:
    module = model.credit_baselines
    state = module.state_dict()
    first = module[0] if isinstance(module, nn.Sequential) and len(module) == 3 else None
    final = module[2] if isinstance(module, nn.Sequential) and len(module) == 3 else None
    return {
        "semantic_keys": list(state),
        "state_shapes": {name: list(value.shape) for name, value in state.items()},
        "parameter_count": sum(row.numel() for row in module.parameters()),
        "initial_tensor_bytes": sum(
            row.numel() * row.element_size() for row in state.values()
        ),
        "shared_two_output_module": bool(
            isinstance(module, nn.Sequential)
            and len(module) == 3
            and isinstance(first, nn.Linear)
            and first.in_features == model.critic_state_dim
            and first.out_features == model.hidden_dim
            and isinstance(module[1], nn.Tanh)
            and isinstance(final, nn.Linear)
            and final.in_features == model.hidden_dim
            and final.out_features == 2
        ),
    }


def model_inventory(model: G40NativeSixPolicy) -> dict[str, object]:
    named = tuple(model.named_parameters())
    return {
        "semantic_keys": list(model.state_dict()),
        "state_shapes": {
            name: list(value.shape) for name, value in model.state_dict().items()
        },
        "trainable_mask": [(name, row.requires_grad) for name, row in named],
        "trainable_parameter_count": sum(
            row.numel() for _, row in named if row.requires_grad
        ),
        "parameter_count": sum(row.numel() for _, row in named),
        "initial_tensor_bytes": sum(
            row.numel() * row.element_size() for row in model.state_dict().values()
        ),
        "actor_credit_optimizer_order": list(actor_credit_parameter_names(model)),
        "slow_critic_optimizer_order": list(slow_critic_parameter_names(model)),
        "credit_baseline": baseline_inventory(model),
    }


def branch_boundary_audit(
    anchor: G40NativeSixPolicy,
    models: Mapping[str, G40NativeSixPolicy],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    if set(models) != set(ARMS):
        raise ValueError("G40 branch model inventory mismatch")
    rows = tuple(models[arm] for arm in ARMS)
    optimizer_rows = tuple(optimizers.values())
    optimizer_parameters = tuple(
        parameter
        for optimizer in optimizer_rows
        for group in optimizer.param_groups
        for parameter in group["params"]
    )
    inventories = {arm: model_inventory(models[arm]) for arm in ARMS}
    model_equal = all(state_bytes(anchor) == state_bytes(row) for row in rows)
    buffers_equal = all(buffer_bytes(anchor) == buffer_bytes(row) for row in rows)
    log_std_equal = all(torch.equal(anchor.log_std, row.log_std) for row in rows)
    optimizers_valid = bool(
        optimizer_rows
        and all(row.state == {} for row in optimizer_rows)
        and len({id(row) for row in optimizer_rows}) == len(optimizer_rows)
        and len({id(row.state) for row in optimizer_rows}) == len(optimizer_rows)
        and len({id(row) for row in optimizer_parameters})
        == len(optimizer_parameters)
    )
    storage_count = shared_tensor_storage_count((anchor, *rows))
    inventory_equal = inventories[G31_ARM] == inventories[GAE1_ARM]
    anchor_baseline_inventory = baseline_inventory(anchor)
    baseline_inventories = {arm: baseline_inventory(models[arm]) for arm in ARMS}
    baseline_keys_equal = all(
        row["semantic_keys"] == anchor_baseline_inventory["semantic_keys"]
        for row in baseline_inventories.values()
    )
    baseline_shapes_equal = all(
        row["state_shapes"] == anchor_baseline_inventory["state_shapes"]
        for row in baseline_inventories.values()
    )
    baseline_parameter_count_equal = all(
        row["parameter_count"] == anchor_baseline_inventory["parameter_count"]
        for row in baseline_inventories.values()
    )
    baseline_initial_tensor_bytes_equal = all(
        row["initial_tensor_bytes"]
        == anchor_baseline_inventory["initial_tensor_bytes"]
        for row in baseline_inventories.values()
    )
    baseline_state_equal = all(
        state_bytes(row.credit_baselines) == state_bytes(anchor.credit_baselines)
        for row in rows
    )
    accepted_g39_initial_equal = bool(
        anchor._accepted_g39_initial_baseline_state_equal
        and all(row._accepted_g39_initial_baseline_state_equal for row in rows)
    )
    shared_two_output_baseline = bool(
        anchor_baseline_inventory["shared_two_output_module"] is True
        and all(
            row["shared_two_output_module"] is True
            for row in baseline_inventories.values()
        )
    )
    passed = bool(
        model_equal
        and buffers_equal
        and log_std_equal
        and optimizers_valid
        and storage_count == 0
        and inventory_equal
        and baseline_keys_equal
        and baseline_shapes_equal
        and baseline_parameter_count_equal
        and baseline_initial_tensor_bytes_equal
        and baseline_state_equal
        and accepted_g39_initial_equal
        and shared_two_output_baseline
    )
    return {
        "model_state_bytes_equal": model_equal,
        "buffer_bytes_equal": buffers_equal,
        "log_std_equal": log_std_equal,
        "optimizer_states_empty_and_separate": optimizers_valid,
        "shared_tensor_storage_count": storage_count,
        "arm_inventory_equal": inventory_equal,
        "baseline_semantic_keys_equal": baseline_keys_equal,
        "baseline_state_shapes_equal": baseline_shapes_equal,
        "baseline_parameter_count_equal": baseline_parameter_count_equal,
        "baseline_initial_tensor_bytes_equal": baseline_initial_tensor_bytes_equal,
        "baseline_state_bytes_equal": baseline_state_equal,
        "accepted_g39_initial_baseline_state_equal": accepted_g39_initial_equal,
        "shared_two_output_credit_baseline": shared_two_output_baseline,
        "baseline_inventory": {
            "anchor": anchor_baseline_inventory,
            **baseline_inventories,
        },
        "inventory": inventories,
        "passed": passed,
    }


def collect_g40_trajectory(
    model: G40NativeSixPolicy,
    *,
    episode_ids: Iterable[int],
    ledger_seed: int,
    action_seed: int,
    device: torch.device,
) -> AnchoredRosterTrajectory:
    raw = g39.collect_g39_trajectory(
        model,
        episode_ids=episode_ids,
        ledger_seed=int(ledger_seed),
        action_seed=int(action_seed),
        device=device,
    )
    from ha_ctse_process.anchored_residual_g19 import attach_credit_baselines

    return attach_credit_baselines(model, raw, device=device)


@dataclass(frozen=True)
class G40CreditTargets:
    returns: torch.Tensor
    successor_targets: torch.Tensor
    immediate_advantage: torch.Tensor
    successor_advantage: torch.Tensor
    gae1_advantage: torch.Tensor
    gae1_identity_error: float


def compute_credit_targets(
    *,
    rewards: torch.Tensor,
    slow_values: torch.Tensor,
    immediate_baselines: torch.Tensor,
    successor_baselines: torch.Tensor,
    terminals: torch.Tensor,
    gamma: float = GAMMA,
    gae_lambda: float = GAE_LAMBDA,
) -> G40CreditTargets:
    rows = (slow_values, immediate_baselines, successor_baselines, terminals)
    if rewards.ndim != 2 or any(row.shape != rewards.shape for row in rows):
        raise ValueError("G40 credit expects matching [time,batch] rows")
    if terminals.dtype != torch.bool:
        raise ValueError("G40 terminal mask must be bool")
    if float(gamma) != GAMMA or float(gae_lambda) != GAE_LAMBDA:
        raise ValueError("G40 gamma/lambda left the frozen contract")
    if any(
        not bool(torch.isfinite(row).all())
        for row in (rewards, slow_values, immediate_baselines, successor_baselines)
    ):
        raise ValueError("G40 credit received non-finite values")
    output_dtype = rewards.dtype
    rewards = rewards.detach()
    values = slow_values.detach()
    work_rewards = rewards.to(torch.float64)
    work_values = values.to(torch.float64)
    nonterminal = (~terminals).to(torch.float64)
    work_returns = torch.empty_like(work_rewards)
    running_return = torch.zeros_like(work_rewards[0])
    for time in range(rewards.shape[0] - 1, -1, -1):
        running_return = (
            work_rewards[time]
            + float(gamma) * nonterminal[time] * running_return
        )
        work_returns[time] = running_return
    next_returns = torch.cat(
        (work_returns[1:], torch.zeros_like(work_returns[:1])), dim=0
    )
    work_successor = nonterminal * next_returns
    next_values = torch.cat(
        (work_values[1:], torch.zeros_like(work_values[:1])), dim=0
    )
    deltas = (
        work_rewards + float(gamma) * nonterminal * next_values - work_values
    )
    recurrence = torch.empty_like(work_rewards)
    running_gae = torch.zeros_like(work_rewards[0])
    for time in range(rewards.shape[0] - 1, -1, -1):
        running_gae = (
            deltas[time]
            + float(gamma)
            * float(gae_lambda)
            * nonterminal[time]
            * running_gae
        )
        recurrence[time] = running_gae
    identity_error = float(
        (recurrence - (work_returns - work_values)).abs().max().cpu()
    )
    returns = work_returns.to(output_dtype)
    successor = work_successor.to(output_dtype)
    # Lambda-one GAE is algebraically the detached return residual.  The
    # float64 recurrence above verifies the frozen delta-sum identity; using
    # its closed form here prevents float32 accumulation order from violating
    # the 1e-6 fail-closed gate without changing the estimator.
    gae = (returns - values).detach()
    return G40CreditTargets(
        returns=returns.detach(),
        successor_targets=successor.detach(),
        immediate_advantage=(rewards - immediate_baselines.detach()).detach(),
        successor_advantage=(successor - successor_baselines.detach()).detach(),
        gae1_advantage=gae.detach(),
        gae1_identity_error=identity_error,
    )


def terminal_mask(trajectory: AnchoredRosterTrajectory) -> torch.Tensor:
    terminals = torch.zeros_like(trajectory.rewards, dtype=torch.bool)
    terminals[-1] = True
    return terminals


def branch_forward_match(
    left: G40NativeSixPolicy,
    right: G40NativeSixPolicy,
    *,
    observations: torch.Tensor,
    active_mask: torch.Tensor,
    critic_state: torch.Tensor,
    sampling_noise: torch.Tensor,
) -> dict[str, object]:
    hidden = torch.zeros((*active_mask.shape, left.hidden_dim), dtype=observations.dtype)
    arguments = {
        "observations": observations,
        "active_mask": active_mask,
        "critic_state": critic_state,
        "hidden": hidden,
        "sampling_noise": sampling_noise,
    }
    left_output = left.forward_step(**arguments)
    right_output = right.forward_step(**arguments)
    left_immediate, left_successor = left.baseline_values(critic_state)
    right_immediate, right_successor = right.baseline_values(critic_state)
    active = active_mask
    inactive = ~active
    errors = {
        "pre_tanh": float(
            (left_output.pre_tanh_actions[active] - right_output.pre_tanh_actions[active])
            .abs()
            .max()
        ),
        "actions": float(
            (left_output.actions[active] - right_output.actions[active]).abs().max()
        ),
        "prefix": float(
            (left_output.prefix_action_sums[active] - right_output.prefix_action_sums[active])
            .abs()
            .max()
        ),
        "token_log_prob": float(
            (left_output.token_log_probs[active] - right_output.token_log_probs[active])
            .abs()
            .max()
        ),
    }
    exact = {
        "slow_critic": torch.equal(left_output.value, right_output.value),
        "immediate_baseline": torch.equal(left_immediate, right_immediate),
        "successor_baseline": torch.equal(left_successor, right_successor),
        "inactive_actions": bool(
            torch.equal(left_output.actions[inactive], right_output.actions[inactive])
            and torch.count_nonzero(left_output.actions[inactive]) == 0
        ),
        "inactive_likelihoods": bool(
            torch.equal(
                left_output.token_log_probs[inactive],
                right_output.token_log_probs[inactive],
            )
            and torch.count_nonzero(left_output.token_log_probs[inactive]) == 0
        ),
        "next_hidden_zero": bool(
            torch.count_nonzero(left_output.next_hidden) == 0
            and torch.count_nonzero(right_output.next_hidden) == 0
        ),
    }
    return {
        "errors": errors,
        "exact": exact,
        "passed": bool(
            all(exact.values())
            and max(errors[name] for name in ("pre_tanh", "actions", "prefix"))
            <= FORWARD_TOLERANCE
            and errors["token_log_prob"] <= LOG_PROB_TOLERANCE
        ),
    }


def branch_trajectory_match(
    left: AnchoredRosterTrajectory, right: AnchoredRosterTrajectory
) -> dict[str, object]:
    inherited = g39.initial_trajectory_match(left, right)
    exact_baselines = {
        "immediate_baseline": torch.equal(
            left.old_immediate_baselines, right.old_immediate_baselines
        ),
        "successor_baseline": torch.equal(
            left.old_successor_baselines, right.old_successor_baselines
        ),
    }
    return {
        **inherited,
        "exact": {**inherited["exact"], **exact_baselines},
        "passed": bool(inherited["passed"] and all(exact_baselines.values())),
    }


def _actor_groups(
    model: G40NativeSixPolicy,
) -> dict[str, tuple[nn.Parameter, ...]]:
    actor = model.policy
    return {
        "member_encoder": tuple(actor.member_encoder.parameters()),
        "context_encoder": tuple(actor.context_encoder.parameters()),
        "gated_cell_input_weights": (actor.actor_rnn.weight_ih,),
        "gated_cell_recurrent_weights": (actor.actor_rnn.weight_hh,),
        "gated_cell_biases": (actor.actor_rnn.bias_ih, actor.actor_rnn.bias_hh),
        "action_head": tuple(actor.action_mean.parameters()),
        "current_readout": tuple(model.current_readout.parameters()),
        "log_std": (model.log_std,),
    }


def _gradient_norm(
    objective: torch.Tensor, parameters: Sequence[nn.Parameter], *, retain_graph: bool = True
) -> float:
    gradients = torch.autograd.grad(
        objective,
        tuple(parameters),
        retain_graph=retain_graph,
        allow_unused=True,
    )
    total = sum(
        torch.zeros((), dtype=torch.float64)
        if row is None
        else row.to(torch.float64).square().sum()
        for row in gradients
    )
    return float(torch.sqrt(total).detach().cpu())


def _entropy(replay: Any) -> torch.Tensor:
    active_count = replay.active_mask.sum(dim=-1).clamp_min(1)
    return (
        torch.where(replay.active_mask, replay.entropies, 0.0).sum(dim=-1)
        / active_count
    ).mean()


def _policy_loss_from_normalized_advantage(
    replay: Any,
    trajectory: AnchoredRosterTrajectory,
    normalized_advantage: torch.Tensor,
) -> torch.Tensor:
    """Apply the inherited PPO surrogate without re-normalizing a fixed credit."""

    device = replay.log_probs.device
    mask = replay.active_mask
    ratio = torch.exp(replay.log_probs - trajectory.old_log_probs.to(device))
    expanded = normalized_advantage.to(device).unsqueeze(-1)
    surrogate = torch.minimum(
        ratio * expanded,
        torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * expanded,
    )
    active_count = mask.sum(dim=-1).clamp_min(1)
    return -(
        torch.where(mask, surrogate, 0.0).sum(dim=-1) / active_count
    ).mean()


def pre_common_gradient_audit(
    model: G40NativeSixPolicy,
    trajectory: AnchoredRosterTrajectory,
) -> dict[str, object]:
    slow_mask = tuple(row.requires_grad for row in model.slow_critic.parameters())
    for parameter in model.slow_critic.parameters():
        parameter.requires_grad_(True)
    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    credit = compute_credit_targets(
        rewards=trajectory.rewards,
        slow_values=trajectory.old_values,
        immediate_baselines=trajectory.old_immediate_baselines,
        successor_baselines=trajectory.old_successor_baselines,
        terminals=terminal_mask(trajectory),
    )
    policy = _policy_loss_from_normalized_advantage(
        replay, trajectory, normalize_advantage(credit.immediate_advantage)
    )
    fast_objective = policy - ENTROPY_COEFFICIENT * _entropy(replay)
    slow_loss = F.mse_loss(replay.values, credit.returns)
    immediate_loss = F.mse_loss(
        replay.immediate_baselines, trajectory.rewards.detach()
    )
    successor_loss = F.mse_loss(
        replay.successor_baselines, credit.successor_targets
    )
    objectives: dict[str, tuple[Sequence[nn.Parameter], torch.Tensor]] = {
        **{
            name: (parameters, fast_objective)
            for name, parameters in _actor_groups(model).items()
        },
        "centralized_slow_critic": (tuple(model.slow_critic.parameters()), slow_loss),
        "immediate_baseline": (tuple(model.credit_baselines.parameters()), immediate_loss),
        "successor_baseline": (tuple(model.credit_baselines.parameters()), successor_loss),
    }
    rows: dict[str, object] = {}
    for name in REGISTERED_TRAINABLE_GROUPS:
        parameters, objective = objectives[name]
        norm = _gradient_norm(objective, parameters)
        rows[name] = {
            "gradient_norm": norm,
            "finite": bool(np.isfinite(norm)),
            "live": bool(np.isfinite(norm) and norm > GRADIENT_LIVE_TOLERANCE),
        }
    rows["passed"] = all(bool(rows[name]["live"]) for name in REGISTERED_TRAINABLE_GROUPS)  # type: ignore[index]
    for parameter, requires_grad in zip(model.slow_critic.parameters(), slow_mask):
        parameter.requires_grad_(requires_grad)
    return rows


def validate_pre_common_gradient_audit(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    if set(value) != {*REGISTERED_TRAINABLE_GROUPS, "passed"}:
        return False
    for name in REGISTERED_TRAINABLE_GROUPS:
        row = value.get(name)
        if (
            not isinstance(row, Mapping)
            or row.get("finite") is not True
            or row.get("live") is not True
            or not isinstance(row.get("gradient_norm"), (int, float))
            or isinstance(row.get("gradient_norm"), bool)
            or not np.isfinite(float(row["gradient_norm"]))
            or float(row["gradient_norm"]) <= GRADIENT_LIVE_TOLERANCE
        ):
            return False
    return True


def source_preflight_audit() -> dict[str, object]:
    loads = np.linspace(0.30, 0.70, 101, dtype=np.float64)[:, None]
    mixes = np.linspace(0.25, 0.75, 101, dtype=np.float64)[None, :]
    effort = 0.5 * (1.0 + np.tanh(2.0 * loads - 1.0))
    mix_action = 0.5 * (1.0 + np.tanh(2.0 * mixes - 1.0))
    witness = float(
        np.min(
            1.0
            - 0.5
            * (
                np.abs(effort * mix_action / (loads * mixes) - 1.0)
                + np.abs(
                    effort
                    * (1.0 - mix_action)
                    / (loads * (1.0 - mixes))
                    - 1.0
                )
            )
        )
    )
    source_match = bool(
        g39.source_controls()["stored_source_coordinates"] == 6
        and g39.source_controls()["intrinsic_K_search"] == 0
    )
    passed = bool(
        source_match
        and
        roster_env.HORIZON == 48
        and roster_env.TRAIN_CAPACITY == 8
        and tuple(g34.CAPACITIES) == (6, 8, 12)
        and witness >= g35.CURRENT_STATE_WITNESS_FLOOR
    )
    return {
        "source_controls_match": source_match,
        "constructive_policy_witness": witness,
        "constructive_policy_witness_floor": g35.CURRENT_STATE_WITNESS_FLOOR,
        "passed": passed,
    }


def _materialize(
    gradients: Sequence[torch.Tensor | None], parameters: Sequence[nn.Parameter]
) -> tuple[torch.Tensor, ...]:
    return tuple(
        torch.zeros_like(parameter) if gradient is None else gradient.detach()
        for gradient, parameter in zip(gradients, parameters)
    )


def _norm_rows(rows: Sequence[torch.Tensor]) -> float:
    return float(
        torch.sqrt(
            sum(row.to(torch.float64).square().sum() for row in rows)
        )
        .detach()
        .cpu()
    )


def _actor_objective_gradients(
    arm: str,
    model: G40NativeSixPolicy,
    replay: Any,
    trajectory: AnchoredRosterTrajectory,
    normalized_advantages: tuple[torch.Tensor, ...],
) -> tuple[torch.Tensor, tuple[torch.Tensor, ...]]:
    parameters = model.full_actor_parameters()
    entropy_loss = ENTROPY_COEFFICIENT * _entropy(replay)
    if arm == G31_ARM:
        if len(normalized_advantages) != 2:
            raise ValueError("G40 G31 requires two fixed normalized advantages")
        immediate = _policy_loss_from_normalized_advantage(
            replay, trajectory, normalized_advantages[0]
        ) - entropy_loss
        successor = _policy_loss_from_normalized_advantage(
            replay, trajectory, normalized_advantages[1]
        ) - entropy_loss
        left = torch.autograd.grad(
            immediate, parameters, retain_graph=True, allow_unused=True
        )
        right = torch.autograd.grad(
            successor, parameters, retain_graph=True, allow_unused=True
        )
        composition = compose_direction_balanced_gradients(left, right, parameters)
        return 0.5 * (immediate + successor), composition.gradients
    if arm == GAE1_ARM:
        if len(normalized_advantages) != 1:
            raise ValueError("G40 GAE1 requires one fixed normalized advantage")
        objective = _policy_loss_from_normalized_advantage(
            replay, trajectory, normalized_advantages[0]
        ) - entropy_loss
        gradients = torch.autograd.grad(
            objective, parameters, retain_graph=True, allow_unused=True
        )
        return objective, _materialize(gradients, parameters)
    raise ValueError("G40 unknown credit arm")


def shadow_independence_audit(
    model: G40NativeSixPolicy,
    trajectory: AnchoredRosterTrajectory,
) -> dict[str, object]:
    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    credit = compute_credit_targets(
        rewards=trajectory.rewards,
        slow_values=trajectory.old_values,
        immediate_baselines=trajectory.old_immediate_baselines,
        successor_baselines=trajectory.old_successor_baselines,
        terminals=terminal_mask(trajectory),
    )
    policy = (
        _policy_loss_from_normalized_advantage(
            replay, trajectory, normalize_advantage(credit.gae1_advantage)
        )
        - ENTROPY_COEFFICIENT * _entropy(replay)
    )
    immediate = F.mse_loss(
        replay.immediate_baselines, trajectory.rewards.detach()
    )
    successor = F.mse_loss(
        replay.successor_baselines, credit.successor_targets
    )
    shadow = immediate + successor
    actor_parameters = model.full_actor_parameters()
    without = torch.autograd.grad(
        policy, actor_parameters, retain_graph=True, allow_unused=True
    )
    with_shadow = torch.autograd.grad(
        policy + shadow, actor_parameters, retain_graph=True, allow_unused=True
    )
    without_rows = _materialize(without, actor_parameters)
    with_rows = _materialize(with_shadow, actor_parameters)
    actor_equal = all(
        torch.equal(left, right) for left, right in zip(without_rows, with_rows)
    )
    baseline_parameters = tuple(model.credit_baselines.parameters())
    immediate_norm = _gradient_norm(immediate, baseline_parameters)
    successor_norm = _gradient_norm(successor, baseline_parameters)
    disjoint = shared_tensor_storage_count(
        (
            model.policy,
            model.slow_critic,
            model.credit_baselines,
        )
    ) == 0
    passed = bool(
        actor_equal
        and immediate_norm > GRADIENT_LIVE_TOLERANCE
        and successor_norm > GRADIENT_LIVE_TOLERANCE
        and disjoint
    )
    return {
        "ordinary_actor_gradients_bitwise_equal_with_without_shadow": actor_equal,
        "slow_critic_objective_excludes_shadow": True,
        "immediate_shadow_gradient_norm": immediate_norm,
        "successor_shadow_gradient_norm": successor_norm,
        "shared_credit_baseline_module": True,
        "actor_critic_shadow_storage_disjoint": disjoint,
        "diagnostic_optimizer_steps": 0,
        "passed": passed,
    }


def branch_gradient_audit(
    models: Mapping[str, G40NativeSixPolicy],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
) -> dict[str, object]:
    if set(models) != set(ARMS) or set(trajectories) != set(ARMS):
        raise ValueError("G40 branch gradient audit inventory mismatch")
    audits: dict[str, object] = {}
    identity_errors: dict[str, float] = {}
    for arm in ARMS:
        model, trajectory = models[arm], trajectories[arm]
        replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
        credit = compute_credit_targets(
            rewards=trajectory.rewards,
            slow_values=trajectory.old_values,
            immediate_baselines=trajectory.old_immediate_baselines,
            successor_baselines=trajectory.old_successor_baselines,
            terminals=terminal_mask(trajectory),
        )
        normalized_advantages = (
            (
                normalize_advantage(credit.immediate_advantage),
                normalize_advantage(credit.successor_advantage),
            )
            if arm == G31_ARM
            else (normalize_advantage(credit.gae1_advantage),)
        )
        _, actor_gradients = _actor_objective_gradients(
            arm, model, replay, trajectory, normalized_advantages
        )
        gradient_by_id = {
            id(parameter): gradient
            for parameter, gradient in zip(model.full_actor_parameters(), actor_gradients)
        }
        rows: dict[str, object] = {}
        for name, parameters in _actor_groups(model).items():
            gradients = tuple(gradient_by_id[id(parameter)] for parameter in parameters)
            norm = _norm_rows(gradients)
            rows[name] = {
                "objective_gradient_norm": norm,
                "finite": bool(np.isfinite(norm)),
                "live": bool(np.isfinite(norm) and norm > GRADIENT_LIVE_TOLERANCE),
            }
        slow_loss = F.mse_loss(replay.values, credit.returns)
        immediate_loss = F.mse_loss(
            replay.immediate_baselines, trajectory.rewards.detach()
        )
        successor_loss = F.mse_loss(
            replay.successor_baselines, credit.successor_targets
        )
        for name, parameters, objective in (
            ("centralized_slow_critic", tuple(model.slow_critic.parameters()), slow_loss),
            ("immediate_baseline", tuple(model.credit_baselines.parameters()), immediate_loss),
            ("successor_baseline", tuple(model.credit_baselines.parameters()), successor_loss),
        ):
            norm = _gradient_norm(objective, parameters)
            rows[name] = {
                "objective_gradient_norm": norm,
                "finite": bool(np.isfinite(norm)),
                "live": bool(np.isfinite(norm) and norm > GRADIENT_LIVE_TOLERANCE),
            }
        rows["passed"] = all(bool(rows[name]["live"]) for name in REGISTERED_TRAINABLE_GROUPS)  # type: ignore[index]
        audits[arm] = rows
        identity_errors[arm] = credit.gae1_identity_error
    shadow = shadow_independence_audit(models[GAE1_ARM], trajectories[GAE1_ARM])
    passed = bool(
        all(bool(audits[arm]["passed"]) for arm in ARMS)  # type: ignore[index]
        and max(identity_errors.values()) <= GAE_IDENTITY_TOLERANCE
        and shadow["passed"] is True
    )
    return {
        "arms": audits,
        "gae1_identity_errors": identity_errors,
        "gae1_identity_tolerance": GAE_IDENTITY_TOLERANCE,
        "shadow_independence": shadow,
        "passed": passed,
    }


def validate_branch_gradient_audit(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    arms = value.get("arms")
    if not isinstance(arms, Mapping) or set(arms) != set(ARMS):
        return False
    for arm in ARMS:
        rows = arms.get(arm)
        if not isinstance(rows, Mapping) or rows.get("passed") is not True:
            return False
        if set(rows) != {*REGISTERED_TRAINABLE_GROUPS, "passed"}:
            return False
        for name in REGISTERED_TRAINABLE_GROUPS:
            row = rows.get(name)
            if (
                not isinstance(row, Mapping)
                or row.get("finite") is not True
                or row.get("live") is not True
                or not isinstance(row.get("objective_gradient_norm"), (int, float))
                or isinstance(row.get("objective_gradient_norm"), bool)
                or float(row["objective_gradient_norm"]) <= GRADIENT_LIVE_TOLERANCE
            ):
                return False
    errors = value.get("gae1_identity_errors")
    shadow = value.get("shadow_independence")
    return bool(
        isinstance(errors, Mapping)
        and set(errors) == set(ARMS)
        and max(float(row) for row in errors.values()) <= GAE_IDENTITY_TOLERANCE
        and isinstance(shadow, Mapping)
        and shadow.get("passed") is True
        and shadow.get("diagnostic_optimizer_steps") == 0
    )


def _gradient_global_norm(parameters: Sequence[nn.Parameter]) -> float:
    return _norm_rows(
        tuple(
            torch.zeros_like(parameter)
            if parameter.grad is None
            else parameter.grad.detach()
            for parameter in parameters
        )
    )


def _optimizer_step(
    optimizer: torch.optim.Optimizer, parameters: Sequence[nn.Parameter]
) -> None:
    if not isinstance(optimizer, torch.optim.Adam):
        raise TypeError("G40 requires Adam")
    owned = tuple(
        parameter for group in optimizer.param_groups for parameter in group["params"]
    )
    if tuple(id(row) for row in owned) != tuple(id(row) for row in parameters):
        raise ValueError("G40 optimizer parameter order mismatch")
    optimizer.step()


def optimize_common_fast_anchor_update(
    model: G40NativeSixPolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    ppo_passes: int,
) -> dict[str, float]:
    if model.phase != "fast":
        raise RuntimeError("G40 common anchor update requires fast phase")
    parameters = model.actor_credit_parameters()
    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    errors = replay_errors(replay, trajectory)
    credit = compute_credit_targets(
        rewards=trajectory.rewards,
        slow_values=trajectory.old_values,
        immediate_baselines=trajectory.old_immediate_baselines,
        successor_baselines=trajectory.old_successor_baselines,
        terminals=terminal_mask(trajectory),
    )
    normalized_advantage = normalize_advantage(credit.immediate_advantage)
    maximum_gradient = 0.0
    finite = True
    for pass_index in range(int(ppo_passes)):
        if pass_index:
            replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
        policy = _policy_loss_from_normalized_advantage(
            replay, trajectory, normalized_advantage
        )
        immediate = F.mse_loss(
            replay.immediate_baselines, trajectory.rewards.detach()
        )
        loss = policy + VALUE_COEFFICIENT * immediate - ENTROPY_COEFFICIENT * _entropy(replay)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient = _gradient_global_norm(parameters)
        finite &= bool(torch.isfinite(loss)) and np.isfinite(gradient)
        maximum_gradient = max(maximum_gradient, gradient)
        _optimizer_step(optimizer, parameters)
    return {
        **errors,
        "finite_update": float(finite),
        "maximum_gradient_norm": maximum_gradient,
        "optimizer_steps": float(ppo_passes),
        "advantage_normalization_count": 1.0,
        "advantage_recomputed_between_passes": 0.0,
        "gradient_clipping_applied": 0.0,
    }


def optimize_credit_branch_update(
    arm: str,
    model: G40NativeSixPolicy,
    actor_optimizer: torch.optim.Optimizer,
    slow_critic_optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    ppo_passes: int,
    include_shadow_losses: bool = True,
) -> dict[str, float]:
    if model.phase != "credit_branch":
        raise RuntimeError("G40 branch update requires credit-branch phase")
    if arm not in ARMS:
        raise ValueError("G40 branch update arm mismatch")
    actor_parameters = model.full_actor_parameters()
    actor_credit_parameters = model.actor_credit_parameters()
    slow_parameters = model.slow_critic_parameters()
    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    errors = replay_errors(replay, trajectory)
    credit = compute_credit_targets(
        rewards=trajectory.rewards,
        slow_values=trajectory.old_values,
        immediate_baselines=trajectory.old_immediate_baselines,
        successor_baselines=trajectory.old_successor_baselines,
        terminals=terminal_mask(trajectory),
    )
    if credit.gae1_identity_error > GAE_IDENTITY_TOLERANCE:
        raise RuntimeError("G40 GAE1 return identity failed before update")
    normalized_advantages = (
        (
            normalize_advantage(credit.immediate_advantage),
            normalize_advantage(credit.successor_advantage),
        )
        if arm == G31_ARM
        else (normalize_advantage(credit.gae1_advantage),)
    )
    maximum_actor_gradient = 0.0
    maximum_slow_gradient = 0.0
    finite = True
    for pass_index in range(int(ppo_passes)):
        if pass_index:
            replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
        policy, actor_gradients = _actor_objective_gradients(
            arm, model, replay, trajectory, normalized_advantages
        )
        immediate_loss = F.mse_loss(
            replay.immediate_baselines, trajectory.rewards.detach()
        )
        successor_loss = F.mse_loss(
            replay.successor_baselines, credit.successor_targets
        )
        actor_optimizer.zero_grad(set_to_none=True)
        if arm == G31_ARM or include_shadow_losses:
            (immediate_loss + successor_loss).backward()
        for parameter, gradient in zip(actor_parameters, actor_gradients):
            parameter.grad = gradient.clone()
        actor_gradient = _norm_rows(actor_gradients)
        maximum_actor_gradient = max(maximum_actor_gradient, actor_gradient)
        _optimizer_step(actor_optimizer, actor_credit_parameters)

        replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
        slow_loss = F.mse_loss(replay.values, credit.returns)
        slow_critic_optimizer.zero_grad(set_to_none=True)
        slow_loss.backward()
        slow_gradient = _gradient_global_norm(slow_parameters)
        maximum_slow_gradient = max(maximum_slow_gradient, slow_gradient)
        _optimizer_step(slow_critic_optimizer, slow_parameters)
        finite &= all(
            bool(torch.isfinite(value))
            for value in (policy, immediate_loss, successor_loss, slow_loss)
        ) and np.isfinite(actor_gradient) and np.isfinite(slow_gradient)
    return {
        **errors,
        "finite_update": float(finite),
        "actor_optimizer_steps": float(ppo_passes),
        "slow_critic_optimizer_steps": float(ppo_passes),
        "maximum_actor_gradient_norm": maximum_actor_gradient,
        "maximum_slow_critic_gradient_norm": maximum_slow_gradient,
        "gae1_return_identity_error": credit.gae1_identity_error,
        "advantage_normalization_count": float(len(normalized_advantages)),
        "advantage_recomputed_between_passes": 0.0,
        "baseline_gradients_enter_direction_norm": 0.0,
        "gradient_clipping_applied": 0.0,
    }


def make_process_ledgers(
    *, replicate: int, capacity: int, episode_count: int, formal: bool
) -> tuple[g34.RandomProcessLedger, ...]:
    if capacity not in g34.CAPACITIES or not 1 <= int(episode_count) <= 64:
        raise ValueError("G40 process request outside registered support")
    seeds = seed_block(replicate, formal=formal)
    times = g35._time_assignments(
        capacity=capacity, process_seed=seeds["evaluation_process"]
    )
    orders = g39._balanced_64_assignments(
        g34.EVENT_ORDERS,
        replicate=replicate,
        capacity=capacity,
        process_seed=seeds["evaluation_process"],
        stream=1,
    )
    if capacity == 6:
        profiles = (roster_env.SMALL_CAPACITY_6,) * 64
    elif capacity == 12:
        profiles = (roster_env.LARGE_CAPACITY_12,) * 64
    else:
        profiles = g39._balanced_64_assignments(
            roster_env.TRAIN_PROFILES,
            replicate=replicate,
            capacity=capacity,
            process_seed=seeds["evaluation_process"],
            stream=2,
        )
    result: list[g34.RandomProcessLedger] = []
    for local_episode in range(int(episode_count)):
        base = roster_env.make_ledger(
            g34.episode_address(capacity, local_episode),
            master_seed=seeds["evaluation_base_ledger"],
            profile=profiles[local_episode],
        )
        expected, trajectory = g34._expected_roster_schedule(
            base, times[local_episode], orders[local_episode]
        )
        row = g34.RandomProcessLedger(
            base=base,
            local_episode_id=local_episode,
            event_times=times[local_episode],
            event_order=orders[local_episode],
            expected_roster_sizes=expected,
            count_trajectory=trajectory,
        )
        row.validate()
        result.append(row)
    if len({row.signature for row in result}) != len(result):
        raise ValueError("G40 process signatures must be unique")
    return tuple(result)


def evaluate_model(
    model: G40NativeSixPolicy,
    *,
    processes: Sequence[g34.RandomProcessLedger],
    action_seed: int,
    process_kind: str,
    deterministic: bool,
) -> tuple[tuple[dict[str, object], ...], bool]:
    return g39.evaluate_g39_model(
        model,
        processes=processes,
        action_seed=int(action_seed),
        process_kind=process_kind,
        deterministic=deterministic,
    )


def source_controls() -> dict[str, object]:
    return {
        "source_id": SOURCE_ID,
        "parent_source_id": g39.SOURCE_ID,
        "training_source": "G32 capacity-8 fixed",
        "evaluation_source": "G34 fixed/random capacities 6|8|12",
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_backend_python_fallback": False,
        "environment_backend_build_interface": toy_cpp._BUILD_INTERFACE_VERSION,
        "horizon": roster_env.HORIZON,
        "training_capacity": roster_env.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "arms": list(ARMS),
        "credit_treatment_only": True,
        "gamma": GAMMA,
        "gae_lambda": GAE_LAMBDA,
        "terminal_bootstrap": 0,
        "membership_edits_reset_traces": False,
        "seed_bases": dict(SEED_BASES),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "nonformal_seed_offset": NONFORMAL_SEED_OFFSET,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }
