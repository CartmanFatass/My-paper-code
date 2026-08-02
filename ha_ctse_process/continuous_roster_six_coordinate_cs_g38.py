"""Exact foldable six-coordinate/current-state realization for G38-P0."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from envs.continuous_roster import runtime_capacity as roster_env
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import continuous_roster_reactive_reduction_g35 as g35
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from ha_ctse_process.continuous_roster_seed import (
    bootstrap_seed_from_base,
    seed_block_from_bases,
)


ALGORITHM_ID = "CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38"
SOURCE_ID = "CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_P0"
FULL10_ARM = "FULL10_CS"
FOLD6_ARM = "FOLD6_CS"
ARMS = (FULL10_ARM, FOLD6_ARM)
FULL10_INPUT = "FULL10"
FOLD6_INPUT = "FOLD6"
FOLDED6_INPUT = "FOLDED6"
INPUT_MODES = (FULL10_INPUT, FOLD6_INPUT, FOLDED6_INPUT)
FULL_OBSERVATION_DIM = 10
RETAINED_OBSERVATION_DIM = 6
CONSTANT_COORDINATES = (0.5, 0.5, 0.5, 24.0 / 47.0)
REMOVABLE_COLUMNS = (6, 7, 8, 9)
REMOVED_ACTOR_WEIGHTS = 136
HIDDEN_DIM = 32
INITIAL_LOG_STD = -1.0
GRADIENT_LIVE_TOLERANCE = 1e-12
INITIAL_EQUALITY_TOLERANCE = 1e-7
FOLD_MEAN_ACTION_PREFIX_TOLERANCE = 1e-6
FOLD_LOG_PROB_TOLERANCE = 1e-5
NONFORMAL_SEED_OFFSET = 900_000

SEED_BASES = {
    "model": 10_381_000,
    "training_ledger": 10_382_000,
    "training_action": 10_383_000,
    "evaluation_base_ledger": 10_384_000,
    "evaluation_process": 10_385_000,
    "evaluation_action": 10_386_000,
    "initial_gradient_probe": 10_387_000,
}
BOOTSTRAP_SEED = 10_388_038


def seed_block(replicate: int, *, formal: bool) -> dict[str, int]:
    if not 0 <= int(replicate) < 3:
        raise ValueError("G38 replicate outside registered support")
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


def _constant(*, like: torch.Tensor) -> torch.Tensor:
    return like.new_tensor(CONSTANT_COORDINATES)


def _last_four_linear(
    coordinates: torch.Tensor, weight: torch.Tensor
) -> torch.Tensor:
    """Evaluate the four-coordinate term with one shape-independent reduction."""

    if coordinates.shape[-1] != 4 or weight.ndim != 2 or weight.shape[-1] != 4:
        raise ValueError("G38 last-four affine shape mismatch")
    products = coordinates.unsqueeze(-2) * weight
    return (products[..., 0] + products[..., 1]) + (
        products[..., 2] + products[..., 3]
    )


def _fold6_effective_bias(affine: nn.Linear) -> torch.Tensor:
    """Combine the registered constants with removable trainable columns."""

    if affine.bias is None or affine.in_features != FULL_OBSERVATION_DIM:
        raise ValueError("G38 effective bias requires a biased ten-input affine")
    return affine.bias + _last_four_linear(
        _constant(like=affine.weight),
        affine.weight[:, RETAINED_OBSERVATION_DIM:],
    )


class _G38RawInputAffine(nn.Linear):
    """Shared factorized raw-input affine for pre-fold and folded actors."""

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        if input.shape[-1] != self.in_features:
            raise ValueError("G38 raw-input affine width mismatch")
        if self.bias is None:
            raise ValueError("G38 raw-input affine requires a bias")
        if self.in_features == RETAINED_OBSERVATION_DIM:
            return F.linear(input, self.weight, None) + self.bias
        if self.in_features != FULL_OBSERVATION_DIM:
            raise ValueError("G38 raw-input affine has unregistered width")
        retained_term = F.linear(
            input[..., :RETAINED_OBSERVATION_DIM],
            self.weight[:, :RETAINED_OBSERVATION_DIM],
        )
        effective_bias = self.bias + _last_four_linear(
            input[..., RETAINED_OBSERVATION_DIM:],
            self.weight[:, RETAINED_OBSERVATION_DIM:],
        )
        return retained_term + effective_bias


def _g38_raw_input_affine(source: nn.Linear) -> _G38RawInputAffine:
    """Retain initialized parameters while installing the G38 execution kernel."""

    rng_state = torch.random.get_rng_state()
    try:
        affine = _G38RawInputAffine(
            source.in_features,
            source.out_features,
            bias=source.bias is not None,
            device=source.weight.device,
            dtype=source.weight.dtype,
        )
    finally:
        torch.random.set_rng_state(rng_state)
    affine.weight = source.weight
    affine.bias = source.bias
    return affine


def build_g38_full10_actor_input(
    source_observations: torch.Tensor, active_mask: torch.Tensor
) -> torch.Tensor:
    """Read all registered coordinates for FULL10 and zero inactive rows."""

    if source_observations.shape[:-1] != active_mask.shape:
        raise ValueError("G38 FULL10 observation/mask shape mismatch")
    if source_observations.shape[-1] != FULL_OBSERVATION_DIM:
        raise ValueError("G38 FULL10 requires ten source coordinates")
    return torch.where(
        active_mask.unsqueeze(-1), source_observations, torch.zeros_like(source_observations)
    )


def build_g38_constant_actor_input(
    source_first_six: torch.Tensor, active_mask: torch.Tensor
) -> torch.Tensor:
    """Build FOLD6 input from a six-coordinate view; no history value is accepted."""

    if source_first_six.shape[:-1] != active_mask.shape:
        raise ValueError("G38 FOLD6 observation/mask shape mismatch")
    if source_first_six.shape[-1] != RETAINED_OBSERVATION_DIM:
        raise ValueError("G38 FOLD6 constructor accepts exactly six source coordinates")
    output = source_first_six.new_zeros((*source_first_six.shape[:-1], FULL_OBSERVATION_DIM))
    active = active_mask.unsqueeze(-1)
    output[..., :RETAINED_OBSERVATION_DIM] = torch.where(
        active, source_first_six, torch.zeros_like(source_first_six)
    )
    constants = _constant(like=source_first_six).expand(*source_first_six.shape[:-1], -1)
    output[..., RETAINED_OBSERVATION_DIM:] = torch.where(
        active, constants, torch.zeros_like(constants)
    )
    return output


def build_g38_folded_actor_input(
    source_first_six: torch.Tensor, active_mask: torch.Tensor
) -> torch.Tensor:
    if source_first_six.shape[:-1] != active_mask.shape:
        raise ValueError("G38 folded observation/mask shape mismatch")
    if source_first_six.shape[-1] != RETAINED_OBSERVATION_DIM:
        raise ValueError("G38 folded actor accepts exactly six coordinates")
    return torch.where(
        active_mask.unsqueeze(-1), source_first_six, torch.zeros_like(source_first_six)
    )


def observe_g38_actor_source(
    env: roster_env.RuntimeCapacityRosterEnv, *, input_mode: str
) -> roster_env.CapacityRosterView:
    """Construct only the coordinates owned by the selected actor input mode."""

    if input_mode not in (FULL10_INPUT, FOLD6_INPUT, FOLDED6_INPUT):
        raise ValueError("G38 reduced observer input mode mismatch")
    if env._terminated:
        raise RuntimeError("G38 cannot observe a terminal environment")
    env._prepare_membership()
    count = int(env.active.sum())
    if count <= 0:
        raise RuntimeError("G38 source produced an empty roster")
    capacity = env.ledger.member_capacity
    width = FULL_OBSERVATION_DIM if input_mode == FULL10_INPUT else RETAINED_OBSERVATION_DIM
    observations = np.zeros((capacity, width), dtype=np.float32)
    keys = np.flatnonzero(env.active)
    load = float(env.ledger.load[env.time])
    mix = float(env.ledger.target_mix[env.time])
    observations[keys, :2] = env.ledger.capabilities[keys]
    observations[keys, 2] = env.ledger.presentation_priority[env.time, keys]
    observations[keys, 3] = load
    observations[keys, 4] = mix
    observations[keys, 5] = np.float32(np.log1p(count))
    if input_mode == FULL10_INPUT:
        observations[keys, 6] = env.age[keys] / roster_env.HORIZON
        observations[keys, 7:9] = (env.previous_actions[keys] + 1.0) / 2.0
        observations[keys, 9] = env.time / (roster_env.HORIZON - 1)
    aggregate = env.ledger.capabilities[keys].sum(axis=0)
    critic_state = np.asarray(
        (
            load,
            mix,
            aggregate[0],
            aggregate[1],
            np.log1p(count),
            env.time / (roster_env.HORIZON - 1),
        ),
        dtype=np.float32,
    )
    return roster_env.CapacityRosterView(
        env.time,
        observations,
        env.active.copy(),
        critic_state,
        env._change,
        load,
        mix,
    )


def g38_immediate_reward(
    env: roster_env.RuntimeCapacityRosterEnv,
    view: roster_env.CapacityRosterView,
    actions: np.ndarray,
) -> float:
    """Evaluate reward from one pre-step state without mutating the environment."""

    values = np.asarray(actions, dtype=np.float32)
    expected = (env.ledger.member_capacity, roster_env.ACTION_DIM)
    if values.shape != expected or not np.isfinite(values).all():
        raise ValueError("G38 action shape/finite mismatch")
    if np.any(np.abs(values) > 1.0) or np.count_nonzero(values[~view.active_mask]):
        raise ValueError("G38 action support or inactive action mismatch")
    keys = np.flatnonzero(view.active_mask)
    effort = (values[keys, 0] + 1.0) / 2.0
    action_mix = (values[keys, 1] + 1.0) / 2.0
    capabilities = env.ledger.capabilities[keys]
    served = np.asarray(
        (
            np.sum(effort * action_mix * capabilities[:, 0], dtype=np.float64),
            np.sum(
                effort * (1.0 - action_mix) * capabilities[:, 1],
                dtype=np.float64,
            ),
        )
    )
    aggregate = capabilities.sum(axis=0, dtype=np.float64)
    target = np.asarray(
        (
            view.load * view.target_mix * aggregate[0],
            view.load * (1.0 - view.target_mix) * aggregate[1],
        )
    )
    relative_error = np.abs(served - target) / np.maximum(target, 1e-8)
    return float(np.clip(1.0 - relative_error.mean(), 0.0, 1.0))


def advance_g38_environment(
    env: roster_env.RuntimeCapacityRosterEnv,
    view: roster_env.CapacityRosterView,
    actions: np.ndarray,
) -> float:
    """Advance exactly once using an already constructed reduced/full view."""

    if view.time != env.time or env._terminated:
        raise RuntimeError("G38 environment/view clock mismatch")
    values = np.asarray(actions, dtype=np.float32)
    reward = g38_immediate_reward(env, view, values)
    keys = np.flatnonzero(view.active_mask)
    env.previous_actions[keys] = values[keys]
    env.age[keys] += 1
    env.reward_trace.append(reward)
    env.roster_sizes.append(len(keys))
    env.time += 1
    env._prepared_time = None
    env._change = roster_env.MembershipChange()
    env._terminated = env.time == roster_env.HORIZON
    return reward


def collect_g38_trajectory(
    model: "G38FoldableMatchedCSPolicy",
    *,
    episode_ids: Iterable[int],
    ledger_seed: int,
    action_seed: int,
    device: torch.device,
    profiles: Sequence[roster_env.RosterProfile] = roster_env.TRAIN_PROFILES,
) -> g32.ContinuousRosterTrajectory:
    """Collect FULL10 or genuinely six-wide FOLD6 trajectories."""

    if model.input_mode not in (FULL10_INPUT, FOLD6_INPUT):
        raise ValueError("G38 training collector rejects folded deployment models")
    ids = tuple(int(value) for value in episode_ids)
    profile_rows = tuple(profiles)
    if not ids or not profile_rows:
        raise ValueError("G38 collection requires episodes and profiles")
    capacity = profile_rows[0].member_capacity
    if (
        any(row.member_capacity != capacity for row in profile_rows)
        or model.member_capacity != capacity
    ):
        raise ValueError("G38 collection capacity mismatch")
    ledgers = tuple(
        roster_env.make_ledger(
            episode,
            master_seed=ledger_seed,
            profile=profile_rows[episode % len(profile_rows)],
        )
        for episode in ids
    )
    envs = tuple(roster_env.RuntimeCapacityRosterEnv(row) for row in ledgers)
    batch = len(ids)
    noise = roster_env.make_action_noise(
        ids, action_seed=action_seed, member_capacity=capacity
    )
    hidden = torch.zeros((batch, capacity, model.hidden_dim), device=device)
    observation_width = (
        FULL_OBSERVATION_DIM
        if model.input_mode == FULL10_INPUT
        else RETAINED_OBSERVATION_DIM
    )
    shapes = {
        "observations": (roster_env.HORIZON, batch, capacity, observation_width),
        "active_mask": (roster_env.HORIZON, batch, capacity),
        "critic_states": (roster_env.HORIZON, batch, roster_env.CRITIC_STATE_DIM),
        "actions": (roster_env.HORIZON, batch, capacity, roster_env.ACTION_DIM),
        "pre_tanh_actions": (roster_env.HORIZON, batch, capacity, roster_env.ACTION_DIM),
        "old_log_probs": (roster_env.HORIZON, batch, capacity),
        "old_values": (roster_env.HORIZON, batch),
        "rewards": (roster_env.HORIZON, batch),
        "hidden_before": (roster_env.HORIZON, batch, capacity, model.hidden_dim),
        "hidden_after": (roster_env.HORIZON, batch, capacity, model.hidden_dim),
        "prefix_action_sums": (roster_env.HORIZON, batch, capacity, roster_env.ACTION_DIM),
        "terminal_hidden_reset_mask": (roster_env.HORIZON, batch, capacity),
    }
    rows = {
        name: torch.empty(
            shape,
            dtype=(
                torch.bool
                if name in ("active_mask", "terminal_hidden_reset_mask")
                else torch.float32
            ),
        )
        for name, shape in shapes.items()
    }
    model.eval()
    with torch.no_grad():
        for time in range(roster_env.HORIZON):
            views = tuple(
                observe_g38_actor_source(env, input_mode=model.input_mode)
                for env in envs
            )
            terminal_reset = torch.zeros(
                (batch, capacity), dtype=torch.bool, device=device
            )
            for batch_index, view in enumerate(views):
                if view.membership_change.terminally_left:
                    terminal_reset[
                        batch_index, list(view.membership_change.terminally_left)
                    ] = True
            g32._delete_terminal_hidden(hidden, views)
            observations = torch.as_tensor(
                np.stack([row.observations for row in views]), device=device
            )
            active = torch.as_tensor(
                np.stack([row.active_mask for row in views]), device=device
            )
            critic = torch.as_tensor(
                np.stack([row.critic_state for row in views]), device=device
            )
            before = hidden.clone()
            output = model.forward_step(
                observations=observations,
                active_mask=active,
                critic_state=critic,
                hidden=hidden,
                sampling_noise=torch.as_tensor(noise[time], device=device),
            )
            rewards = np.asarray(
                [
                    advance_g38_environment(
                        env, view, output.actions[index].detach().cpu().numpy()
                    )
                    for index, (env, view) in enumerate(zip(envs, views))
                ],
                dtype=np.float32,
            )
            values = {
                "observations": observations,
                "active_mask": active,
                "critic_states": critic,
                "actions": output.actions,
                "pre_tanh_actions": output.pre_tanh_actions,
                "old_log_probs": output.token_log_probs,
                "old_values": output.value,
                "rewards": torch.as_tensor(rewards, device=device),
                "hidden_before": before,
                "hidden_after": output.next_hidden,
                "prefix_action_sums": output.prefix_action_sums,
                "terminal_hidden_reset_mask": terminal_reset,
            }
            for name, value in values.items():
                rows[name][time].copy_(value.detach().cpu())
            hidden = output.next_hidden
    return g32.ContinuousRosterTrajectory(
        **rows,
        outcomes=tuple(env.outcome() for env in envs),
        ledgers=ledgers,
    )


class G38FoldableMatchedCSActor(g35.G35MatchedStateCarryActor):
    """The inherited G35 actor with explicit names for its only raw-input affines."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # G35 inherited a delayed head over [u,p,o].  G38 keeps the G31
        # direction-balanced head and optimizer phase but removes its raw-o
        # route: both action-head components now consume only [u,p].
        hidden_dim = self.action_mean[0].out_features
        action_dim = self.current_readout.out_features
        head_input_dim = self.action_mean[0].in_features
        self.delayed_residual = nn.Sequential(
            nn.Linear(head_input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, action_dim),
        )
        nn.init.zeros_(self.delayed_residual[-1].weight)
        nn.init.zeros_(self.delayed_residual[-1].bias)
        self.member_encoder[0] = _g38_raw_input_affine(self.member_input)
        self.current_observation_residual = _g38_raw_input_affine(
            self.current_readout
        )

    @property
    def member_input(self) -> nn.Linear:
        row = self.member_encoder[0]
        if not isinstance(row, nn.Linear):
            raise TypeError("G38 member_input is not affine")
        return row

    @property
    def current_readout(self) -> nn.Linear:
        row = self.current_observation_residual
        if not isinstance(row, nn.Linear):
            raise TypeError("G38 current_readout is not affine")
        return row

    def _action_mean_for_member(
        self,
        *,
        candidate: torch.Tensor,
        prefix_fraction: torch.Tensor,
        observation: torch.Tensor,
    ) -> torch.Tensor:
        head_input = torch.cat((candidate, prefix_fraction), dim=-1)
        return (
            self.action_mean(head_input)
            + self.delayed_residual(head_input)
            + self.current_readout(observation)
        )


class G38FoldableMatchedCSPolicy(g35.ReturnToGoDirectionBalancedFullActorPolicy):
    """One serialized graph; ``input_mode`` is the sole nonserialized treatment."""

    def __init__(
        self,
        observation_dim: int,
        critic_state_dim: int,
        *,
        member_capacity: int,
        action_dim: int,
        input_mode: str,
        hidden_dim: int = HIDDEN_DIM,
    ) -> None:
        if input_mode not in INPUT_MODES:
            raise ValueError("G38 input mode must be FULL10, FOLD6, or FOLDED6")
        expected = (
            RETAINED_OBSERVATION_DIM
            if input_mode == FOLDED6_INPUT
            else FULL_OBSERVATION_DIM
        )
        if int(observation_dim) != expected:
            raise ValueError("G38 graph/input-mode observation width mismatch")
        super().__init__(
            observation_dim,
            critic_state_dim,
            member_capacity=member_capacity,
            action_dim=action_dim,
            hidden_dim=hidden_dim,
            current_observation_residual=True,
            policy_type=G38FoldableMatchedCSActor,
        )
        actor = self.policy
        assert isinstance(actor, G38FoldableMatchedCSActor)
        actor.set_carry_mode(g35.CS_ARM)
        self.input_mode = input_mode
        self.actual_history_read_counts = {
            "actual_age_read_count": 0,
            "actual_previous_action_read_count": 0,
            "actual_actor_time_read_count": 0,
            "donor_or_proxy_read_count": 0,
        }

    @property
    def member_input(self) -> nn.Linear:
        actor = self.policy
        assert isinstance(actor, G38FoldableMatchedCSActor)
        return actor.member_input

    @property
    def current_readout(self) -> nn.Linear:
        actor = self.policy
        assert isinstance(actor, G38FoldableMatchedCSActor)
        return actor.current_readout

    @property
    def carry_mode(self) -> str:
        return g35.CS_ARM

    def actor_input(
        self, source_observations: torch.Tensor, active_mask: torch.Tensor
    ) -> torch.Tensor:
        if self.input_mode == FULL10_INPUT:
            return build_g38_full10_actor_input(source_observations, active_mask)
        if self.input_mode == FOLD6_INPUT:
            return build_g38_constant_actor_input(source_observations, active_mask)
        return build_g38_folded_actor_input(source_observations, active_mask)

    def forward_step(self, *, observations: torch.Tensor, active_mask: torch.Tensor, **kwargs: Any) -> Any:
        expected = (
            FULL_OBSERVATION_DIM
            if self.input_mode == FULL10_INPUT
            else RETAINED_OBSERVATION_DIM
        )
        if observations.shape[-1] != expected:
            raise ValueError("G38 forward observation width mismatch")
        return super().forward_step(
            observations=self.actor_input(observations, active_mask),
            active_mask=active_mask,
            **kwargs,
        )


def make_model(
    member_capacity: int,
    *,
    input_mode: str,
    initialization_seed: int,
) -> G38FoldableMatchedCSPolicy:
    torch.manual_seed(int(initialization_seed))
    observation_dim = (
        RETAINED_OBSERVATION_DIM
        if input_mode == FOLDED6_INPUT
        else FULL_OBSERVATION_DIM
    )
    model = G38FoldableMatchedCSPolicy(
        observation_dim,
        roster_env.CRITIC_STATE_DIM,
        member_capacity=int(member_capacity),
        action_dim=roster_env.ACTION_DIM,
        input_mode=input_mode,
        hidden_dim=HIDDEN_DIM,
    )
    with torch.no_grad():
        model.log_std.fill_(INITIAL_LOG_STD)
    return model


def make_paired_models(
    member_capacity: int, *, initialization_seed: int
) -> dict[str, G38FoldableMatchedCSPolicy]:
    full = make_model(
        member_capacity,
        input_mode=FULL10_INPUT,
        initialization_seed=initialization_seed,
    )
    fold = make_model(
        member_capacity,
        input_mode=FOLD6_INPUT,
        initialization_seed=initialization_seed,
    )
    fold.load_state_dict(full.state_dict(), strict=True)
    assert_parameter_match(full, fold, require_byte_identity=True)
    return {FULL10_ARM: full, FOLD6_ARM: fold}


def _state_bytes(model: nn.Module) -> tuple[tuple[str, bytes], ...]:
    return tuple(
        (name, value.detach().cpu().contiguous().numpy().tobytes())
        for name, value in model.state_dict().items()
    )


def assert_parameter_match(
    full: G38FoldableMatchedCSPolicy,
    fold: G38FoldableMatchedCSPolicy,
    *,
    require_byte_identity: bool,
) -> None:
    left, right = full.state_dict(), fold.state_dict()
    if tuple(left) != tuple(right):
        raise ValueError("G38 arm state-dict key mismatch")
    if any(left[name].shape != right[name].shape for name in left):
        raise ValueError("G38 arm state-dict shape mismatch")
    left_mask = tuple((name, row.requires_grad) for name, row in full.named_parameters())
    right_mask = tuple((name, row.requires_grad) for name, row in fold.named_parameters())
    if left_mask != right_mask:
        raise ValueError("G38 arm trainable-mask mismatch")
    if full.parameter_count != fold.parameter_count:
        raise ValueError("G38 arm parameter-count mismatch")
    if require_byte_identity and _state_bytes(full) != _state_bytes(fold):
        raise ValueError("G38 initial state is not byte-identical")


def raw_input_inventory(model: G38FoldableMatchedCSPolicy) -> dict[str, object]:
    width = model.member_input.in_features
    raw_affines = tuple(
        name
        for name, module in model.policy.named_modules()
        if isinstance(module, nn.Linear) and module.in_features == width
    )
    expected = ("member_encoder.0", "current_observation_residual")
    return {
        "member_input_shape": tuple(model.member_input.weight.shape),
        "current_readout_shape": tuple(model.current_readout.weight.shape),
        "raw_affine_module_paths": raw_affines,
        "only_two_raw_affines": raw_affines == expected,
        "carry_mode": model.carry_mode,
    }


def forced_initial_equality(
    full: G38FoldableMatchedCSPolicy,
    fold: G38FoldableMatchedCSPolicy,
    *,
    retained_observations: torch.Tensor,
    active_mask: torch.Tensor,
    critic_state: torch.Tensor,
    sampling_noise: torch.Tensor,
) -> dict[str, float]:
    clamped = build_g38_constant_actor_input(retained_observations, active_mask)
    hidden = torch.zeros(
        (*active_mask.shape, full.hidden_dim),
        dtype=clamped.dtype,
        device=clamped.device,
    )
    common_arguments = {
        "active_mask": active_mask,
        "critic_state": critic_state,
        "hidden": hidden,
        "sampling_noise": sampling_noise,
    }
    left = full.forward_step(observations=clamped, **common_arguments)
    right = fold.forward_step(
        observations=retained_observations, **common_arguments
    )
    return {
        "pre_tanh": float((left.pre_tanh_actions - right.pre_tanh_actions).abs().max()),
        "actions": float((left.actions - right.actions).abs().max()),
        "token_log_prob": float((left.token_log_probs - right.token_log_probs).abs().max()),
        "value": float((left.value - right.value).abs().max()),
    }


def _objectives(
    model: G38FoldableMatchedCSPolicy,
    trajectory: Any,
    *,
    gamma: float,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    replay = g35.replay_trajectory(model, trajectory, device=device)
    rewards = trajectory.rewards.to(device)
    advantage = (rewards - trajectory.old_immediate_baselines.to(device)).detach()
    fast_policy = g35._channel_policy_loss(replay, trajectory, advantage)
    immediate_loss = F.mse_loss(replay.immediate_baselines, rewards.detach())
    active_count = replay.active_mask.sum(dim=-1).clamp_min(1)
    entropy = (
        torch.where(replay.active_mask, replay.entropies, 0.0).sum(dim=-1)
        / active_count
    ).mean()
    fast = (
        fast_policy
        + g35.VALUE_COEFFICIENT * immediate_loss
        - g35.ENTROPY_COEFFICIENT * entropy
    )
    terminals = torch.zeros_like(rewards, dtype=torch.bool)
    terminals[-1] = True
    credit = g35.compute_return_to_go_credit(
        rewards=rewards,
        slow_values=trajectory.old_values.to(device),
        immediate_baselines=trajectory.old_immediate_baselines.to(device),
        successor_baselines=trajectory.old_successor_baselines.to(device),
        terminals=terminals,
        gamma=float(gamma),
    )
    immediate_actor = g35._channel_policy_loss(
        replay, trajectory, credit.immediate_residual
    )
    successor_actor = g35._channel_policy_loss(
        replay, trajectory, credit.successor_residual
    )
    return fast, 0.5 * (immediate_actor + successor_actor)


def g38_initial_gradient_audit(
    model: G38FoldableMatchedCSPolicy,
    trajectory: Any,
    *,
    gamma: float,
    device: torch.device = torch.device("cpu"),
) -> dict[str, object]:
    common = g35.g35_initial_gradient_audit(model, trajectory, gamma=gamma, device=device)
    fast, rtg = _objectives(model, trajectory, gamma=gamma, device=device)
    result = {name: row for name, row in common.items() if name != "passed"}
    for affine_name, weight in (
        ("member_input", model.member_input.weight),
        ("current_readout", model.current_readout.weight),
    ):
        fast_grad = torch.autograd.grad(fast, weight, retain_graph=True)[0]
        rtg_grad = torch.autograd.grad(rtg, weight, retain_graph=True)[0]
        for column in REMOVABLE_COLUMNS:
            fast_max = float(fast_grad[:, column].abs().max().detach().cpu())
            rtg_max = float(rtg_grad[:, column].abs().max().detach().cpu())
            finite = bool(np.isfinite(fast_max) and np.isfinite(rtg_max))
            result[f"{affine_name}_column_{column}"] = {
                "fast_objective_gradient_max_abs": fast_max,
                "return_to_go_objective_gradient_max_abs": rtg_max,
                "finite": finite,
                "live": finite and max(fast_max, rtg_max) > GRADIENT_LIVE_TOLERANCE,
            }
    result["passed"] = bool(
        common["passed"]
        and all(bool(row["live"]) for row in result.values() if isinstance(row, dict))
    )
    return result


def fold_g38_constant_actor_checkpoint(
    model: G38FoldableMatchedCSPolicy,
) -> G38FoldableMatchedCSPolicy:
    if model.input_mode != FOLD6_INPUT:
        raise ValueError("G38 folding requires a pre-fold FOLD6 model")
    rng_state = torch.random.get_rng_state()
    try:
        folded = make_model(
            model.member_capacity,
            input_mode=FOLDED6_INPUT,
            initialization_seed=0,
        )
    finally:
        torch.random.set_rng_state(rng_state)
    source_state = model.state_dict()
    target_state = folded.state_dict()
    member_weight = model.member_input.weight.detach()
    readout_weight = model.current_readout.weight.detach()
    member_weight_key = "policy.member_encoder.0.weight"
    member_bias_key = "policy.member_encoder.0.bias"
    readout_weight_key = "policy.current_observation_residual.weight"
    readout_bias_key = "policy.current_observation_residual.bias"
    replacement: dict[str, torch.Tensor] = {}
    for name, target in target_state.items():
        if name == member_weight_key:
            value = member_weight[:, :RETAINED_OBSERVATION_DIM]
        elif name == member_bias_key:
            value = _fold6_effective_bias(model.member_input)
        elif name == readout_weight_key:
            value = readout_weight[:, :RETAINED_OBSERVATION_DIM]
        elif name == readout_bias_key:
            value = _fold6_effective_bias(model.current_readout)
        else:
            value = source_state[name]
        if value.shape != target.shape:
            raise ValueError(f"G38 folded tensor shape mismatch: {name}")
        replacement[name] = value.detach().clone()
    folded.load_state_dict(replacement, strict=True)
    if model.parameter_count - folded.parameter_count != REMOVED_ACTOR_WEIGHTS:
        raise ValueError("G38 fold did not remove exactly 136 actor weights")
    verify_folded_state_copy(model, folded)
    return folded


def verify_folded_state_copy(
    pre_fold: G38FoldableMatchedCSPolicy,
    folded: G38FoldableMatchedCSPolicy,
) -> None:
    source_state, folded_state = pre_fold.state_dict(), folded.state_dict()
    changed = {
        "policy.member_encoder.0.weight",
        "policy.member_encoder.0.bias",
        "policy.current_observation_residual.weight",
        "policy.current_observation_residual.bias",
    }
    for name in source_state:
        if name not in changed and not torch.equal(source_state[name], folded_state[name]):
            raise ValueError(f"G38 fold changed unrelated tensor: {name}")
    if not torch.equal(pre_fold.log_std, folded.log_std):
        raise ValueError("G38 fold changed log standard deviation")
    pre_critic = tuple(
        (name, row) for name, row in source_state.items()
        if name.startswith("slow_critic.") or name.startswith("policy.critic.")
    )
    post_critic = tuple(
        (name, row) for name, row in folded_state.items()
        if name.startswith("slow_critic.") or name.startswith("policy.critic.")
    )
    if len(pre_critic) != len(post_critic) or any(
        left_name != right_name or not torch.equal(left, right)
        for (left_name, left), (right_name, right) in zip(pre_critic, post_critic)
    ):
        raise ValueError("G38 fold changed critic tensors")


def fold_forward_equivalence(
    pre_fold: G38FoldableMatchedCSPolicy,
    folded: G38FoldableMatchedCSPolicy,
    *,
    retained_observations: torch.Tensor,
    active_mask: torch.Tensor,
    critic_state: torch.Tensor,
    sampling_noise: torch.Tensor | None = None,
    deterministic: bool = False,
) -> dict[str, object]:
    hidden = torch.zeros(
        (*active_mask.shape, pre_fold.hidden_dim),
        dtype=retained_observations.dtype,
        device=retained_observations.device,
    )
    arguments: dict[str, Any] = {
        "observations": retained_observations,
        "active_mask": active_mask,
        "critic_state": critic_state,
        "hidden": hidden,
    }
    if deterministic:
        arguments["deterministic"] = True
    else:
        if sampling_noise is None:
            raise ValueError("G38 stochastic fold verification requires paired noise")
        arguments["sampling_noise"] = sampling_noise
    with torch.no_grad():
        left = pre_fold.forward_step(**arguments)
        right = folded.forward_step(**arguments)
    active = active_mask
    inactive = ~active
    errors = {
        "pre_tanh_mean": float((left.pre_tanh_actions[active] - right.pre_tanh_actions[active]).abs().max()) if bool(active.any()) else 0.0,
        "actions": float((left.actions[active] - right.actions[active]).abs().max()) if bool(active.any()) else 0.0,
        "prefix_action_sums": float((left.prefix_action_sums[active] - right.prefix_action_sums[active]).abs().max()) if bool(active.any()) else 0.0,
        "token_log_probability": float((left.token_log_probs[active] - right.token_log_probs[active]).abs().max()) if bool(active.any()) else 0.0,
    }
    exact = {
        "log_std": torch.equal(pre_fold.log_std, folded.log_std),
        "value": torch.equal(left.value, right.value),
        "inactive_actions": bool(
            torch.equal(left.actions[inactive], right.actions[inactive])
            and torch.count_nonzero(right.actions[inactive]) == 0
        ),
        "inactive_likelihoods": bool(
            torch.equal(left.token_log_probs[inactive], right.token_log_probs[inactive])
            and torch.count_nonzero(right.token_log_probs[inactive]) == 0
        ),
        "next_hidden_zero": bool(
            torch.count_nonzero(left.next_hidden) == 0
            and torch.count_nonzero(right.next_hidden) == 0
        ),
    }
    passed = (
        all(exact.values())
        and errors["pre_tanh_mean"] <= FOLD_MEAN_ACTION_PREFIX_TOLERANCE
        and errors["actions"] <= FOLD_MEAN_ACTION_PREFIX_TOLERANCE
        and errors["prefix_action_sums"] <= FOLD_MEAN_ACTION_PREFIX_TOLERANCE
        and errors["token_log_probability"] <= FOLD_LOG_PROB_TOLERANCE
    )
    return {"errors": errors, "exact": exact, "passed": bool(passed)}


def _expected_membership_change(
    process: g34.RandomProcessLedger, *, process_kind: str, time: int
) -> roster_env.MembershipChange:
    if process_kind == "fixed":
        if time == roster_env.EVENT_TIMES[0]:
            return roster_env.MembershipChange(
                temporarily_left=process.base.temporarily_absent
            )
        if time == roster_env.EVENT_TIMES[1]:
            return roster_env.MembershipChange(
                joined=process.base.fresh_join,
                rejoined=process.base.temporarily_absent,
            )
        if time == roster_env.EVENT_TIMES[2]:
            return roster_env.MembershipChange(
                terminally_left=process.base.terminal_leave
            )
        return roster_env.MembershipChange()
    edit = dict(zip(process.event_times, process.event_order)).get(time)
    if edit == "L":
        return roster_env.MembershipChange(
            temporarily_left=process.base.temporarily_absent
        )
    if edit == "R":
        return roster_env.MembershipChange(rejoined=process.base.temporarily_absent)
    if edit == "J":
        return roster_env.MembershipChange(joined=process.base.fresh_join)
    if edit == "T":
        return roster_env.MembershipChange(
            terminally_left=process.base.terminal_leave
        )
    return roster_env.MembershipChange()


def _fold_reward_summaries(
    rewards: Sequence[float], process: g34.RandomProcessLedger
) -> np.ndarray:
    values = np.asarray(rewards, dtype=np.float64)
    if values.shape != (roster_env.HORIZON,) or not np.isfinite(values).all():
        raise ValueError("G38 fold reward trace mismatch")
    windows = tuple(
        float(values[event_time : event_time + 4].mean())
        for event_time in process.event_times
    )
    boundaries = (0, *process.event_times, roster_env.HORIZON)
    segments = tuple(
        float(values[left:right].mean())
        for left, right in zip(boundaries, boundaries[1:])
    )
    return np.asarray((float(values.mean()), *windows, *segments), dtype=np.float64)


def verify_g38_fold_equivalence(
    pre_fold: G38FoldableMatchedCSPolicy,
    folded: G38FoldableMatchedCSPolicy,
    *,
    processes: Sequence[g34.RandomProcessLedger],
    action_seed: int,
    process_kind: str,
    deterministic: bool,
    device: torch.device = torch.device("cpu"),
) -> tuple[tuple[dict[str, object], ...], bool, dict[str, object]]:
    """Run both actor forms in lockstep while advancing one environment path."""

    if pre_fold.input_mode != FOLD6_INPUT or folded.input_mode != FOLDED6_INPUT:
        raise ValueError("G38 fold verification model modes mismatch")
    if process_kind not in ("random", "fixed"):
        raise ValueError("G38 process kind must be random or fixed")
    rows = tuple(processes)
    if (
        not rows
        or pre_fold.member_capacity != folded.member_capacity
        or any(row.member_capacity != folded.member_capacity for row in rows)
    ):
        raise ValueError("G38 model/process capacity mismatch")
    verify_folded_state_copy(pre_fold, folded)
    envs = tuple(
        g34.RandomProcessRosterEnv(row)
        if process_kind == "random"
        else roster_env.RuntimeCapacityRosterEnv(row.base)
        for row in rows
    )
    ids = tuple(row.episode_id for row in rows)
    noise = roster_env.make_action_noise(
        ids, action_seed=int(action_seed), member_capacity=folded.member_capacity
    )
    hidden_pre = torch.zeros(
        (len(rows), folded.member_capacity, folded.hidden_dim), device=device
    )
    hidden_fold = torch.zeros_like(hidden_pre)
    frozen_age: list[dict[int, int]] = [dict() for _ in rows]
    frozen_action: list[dict[int, np.ndarray]] = [dict() for _ in rows]
    pre_fold_rewards: list[list[float]] = [[] for _ in rows]
    folded_rewards: list[list[float]] = [[] for _ in rows]
    lifecycle_valid = True
    membership_edit_checks = 0
    reward_comparisons = 0
    maximum = {
        "pre_tanh_mean": 0.0,
        "actions": 0.0,
        "prefix_action_sums": 0.0,
        "token_log_probability": 0.0,
        "reward_trace": 0.0,
        "summary": 0.0,
    }
    exact = {
        "log_std": torch.equal(pre_fold.log_std, folded.log_std),
        "critic_tensors": True,
        "value": True,
        "inactive_actions": True,
        "inactive_likelihoods": True,
        "roster_sizes": True,
        "membership_edits": True,
        "lifecycle": True,
        "zero_hidden_carry": True,
    }
    pre_state, fold_state = pre_fold.state_dict(), folded.state_dict()
    for name, row in pre_state.items():
        if name.startswith("slow_critic.") or name.startswith("policy.critic."):
            exact["critic_tensors"] &= torch.equal(row, fold_state[name])
    pre_fold.eval()
    folded.eval()
    with torch.no_grad():
        for time in range(roster_env.HORIZON):
            views = tuple(
                observe_g38_actor_source(env, input_mode=FOLDED6_INPUT)
                for env in envs
            )
            for index, view in enumerate(views):
                exact["membership_edits"] &= (
                    view.membership_change
                    == _expected_membership_change(
                        rows[index], process_kind=process_kind, time=time
                    )
                )
                membership_edit_checks += 1
                for key in view.membership_change.temporarily_left:
                    frozen_age[index][key] = int(envs[index].age[key])
                    frozen_action[index][key] = envs[index].previous_actions[key].copy()
                for key in tuple(frozen_age[index]):
                    if key not in view.membership_change.rejoined and not bool(view.active_mask[key]):
                        lifecycle_valid &= int(envs[index].age[key]) == frozen_age[index][key]
                        lifecycle_valid &= bool(
                            np.array_equal(
                                envs[index].previous_actions[key], frozen_action[index][key]
                            )
                        )
                for key in view.membership_change.rejoined:
                    lifecycle_valid &= int(envs[index].age[key]) == frozen_age[index][key]
                    lifecycle_valid &= bool(
                        np.array_equal(
                            envs[index].previous_actions[key], frozen_action[index][key]
                        )
                    )
                    frozen_age[index].pop(key)
                    frozen_action[index].pop(key)
                for key in view.membership_change.joined:
                    lifecycle_valid &= envs[index].age[key] == 0
                    lifecycle_valid &= not np.count_nonzero(envs[index].previous_actions[key])
            g32._delete_terminal_hidden(hidden_pre, views)
            g32._delete_terminal_hidden(hidden_fold, views)
            active = torch.as_tensor(
                np.stack([view.active_mask for view in views]), device=device
            )
            retained = torch.as_tensor(
                np.stack([view.observations for view in views]),
                device=device,
            )
            critic = torch.as_tensor(
                np.stack([view.critic_state for view in views]), device=device
            )
            arguments: dict[str, Any] = {
                "observations": retained,
                "active_mask": active,
                "critic_state": critic,
            }
            if deterministic:
                arguments["deterministic"] = True
            else:
                arguments["sampling_noise"] = torch.as_tensor(noise[time], device=device)
            left = pre_fold.forward_step(hidden=hidden_pre, **arguments)
            right = folded.forward_step(hidden=hidden_fold, **arguments)
            active_values = active
            for name, left_value, right_value in (
                ("pre_tanh_mean", left.pre_tanh_actions, right.pre_tanh_actions),
                ("actions", left.actions, right.actions),
                ("prefix_action_sums", left.prefix_action_sums, right.prefix_action_sums),
                ("token_log_probability", left.token_log_probs, right.token_log_probs),
            ):
                if bool(active_values.any()):
                    maximum[name] = max(
                        maximum[name],
                        float((left_value[active_values] - right_value[active_values]).abs().max()),
                    )
            inactive = ~active
            exact["value"] &= torch.equal(left.value, right.value)
            exact["inactive_actions"] &= bool(
                torch.equal(left.actions[inactive], right.actions[inactive])
                and torch.count_nonzero(right.actions[inactive]) == 0
            )
            exact["inactive_likelihoods"] &= bool(
                torch.equal(left.token_log_probs[inactive], right.token_log_probs[inactive])
                and torch.count_nonzero(right.token_log_probs[inactive]) == 0
            )
            exact["zero_hidden_carry"] &= bool(
                torch.count_nonzero(left.next_hidden) == 0
                and torch.count_nonzero(right.next_hidden) == 0
            )
            for index, (env, view) in enumerate(zip(envs, views)):
                left_actions = left.actions[index].detach().cpu().numpy()
                right_actions = right.actions[index].detach().cpu().numpy()
                left_reward = g38_immediate_reward(env, view, left_actions)
                right_reward = g38_immediate_reward(env, view, right_actions)
                maximum["reward_trace"] = max(
                    maximum["reward_trace"], abs(left_reward - right_reward)
                )
                pre_fold_rewards[index].append(left_reward)
                folded_rewards[index].append(right_reward)
                advanced_reward = advance_g38_environment(
                    env, view, right_actions
                )
                if advanced_reward != right_reward:
                    raise RuntimeError("G38 advanced reward algebra mismatch")
                reward_comparisons += 1
            hidden_pre, hidden_fold = left.next_hidden, right.next_hidden
    lifecycle_valid &= not any(frozen_age) and not any(frozen_action)
    metrics = tuple(
        g34._episode_metrics(
            process,
            env.outcome(),
            expected_roster_sizes=(
                process.expected_roster_sizes
                if process_kind == "random"
                else process.base.expected_roster_sizes
            ),
        )
        for process, env in zip(rows, envs)
    )
    exact["roster_sizes"] = all(bool(row["roster_sizes_valid"]) for row in metrics)
    exact["lifecycle"] = bool(lifecycle_valid)
    summary_comparisons = 0
    for process, left_rewards, right_rewards in zip(
        rows, pre_fold_rewards, folded_rewards
    ):
        left_summary = _fold_reward_summaries(left_rewards, process)
        right_summary = _fold_reward_summaries(right_rewards, process)
        maximum["summary"] = max(
            maximum["summary"],
            float(np.max(np.abs(left_summary - right_summary))),
        )
        summary_comparisons += int(left_summary.size)
    passed = (
        all(bool(value) for value in exact.values())
        and maximum["pre_tanh_mean"] <= FOLD_MEAN_ACTION_PREFIX_TOLERANCE
        and maximum["actions"] <= FOLD_MEAN_ACTION_PREFIX_TOLERANCE
        and maximum["prefix_action_sums"] <= FOLD_MEAN_ACTION_PREFIX_TOLERANCE
        and maximum["token_log_probability"] <= FOLD_LOG_PROB_TOLERANCE
        and maximum["reward_trace"] <= FOLD_MEAN_ACTION_PREFIX_TOLERANCE
        and maximum["summary"] <= FOLD_MEAN_ACTION_PREFIX_TOLERANCE
    )
    return metrics, bool(lifecycle_valid), {
        "maximum_errors": maximum,
        "exact": {name: bool(value) for name, value in exact.items()},
        "passed": bool(passed),
        "environment_trajectories_per_episode": 1,
        "reward_comparisons": reward_comparisons,
        "summary_comparisons": summary_comparisons,
        "membership_edit_checks": membership_edit_checks,
    }


def make_process_ledgers(
    *, replicate: int, capacity: int, episode_count: int, formal: bool
) -> tuple[g34.RandomProcessLedger, ...]:
    if capacity not in g34.CAPACITIES or not 1 <= int(episode_count) <= g35.EPISODE_SUPPORT:
        raise ValueError("G38 process request outside registered support")
    seeds = seed_block(replicate, formal=formal)
    times = g35._time_assignments(
        capacity=capacity, process_seed=seeds["evaluation_process"]
    )
    orders = g35._balanced_assignments(
        g34.EVENT_ORDERS,
        replicate=replicate,
        capacity=capacity,
        process_seed=seeds["evaluation_process"],
        stream=1,
    )
    profiles = g35._profile_assignments(
        replicate=replicate,
        capacity=capacity,
        process_seed=seeds["evaluation_process"],
    )
    rows: list[g34.RandomProcessLedger] = []
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
        rows.append(row)
    if len({row.signature for row in rows}) != len(rows):
        raise ValueError("G38 process signatures must be unique")
    return tuple(rows)


def source_controls() -> dict[str, object]:
    return {
        "source_id": SOURCE_ID,
        "training_source": "G32 capacity-8 fixed",
        "evaluation_source": "G34-P0 fixed/random capacities 6|8|12",
        "horizon": roster_env.HORIZON,
        "training_capacity": roster_env.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "seed_bases": dict(SEED_BASES),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "nonformal_seed_offset": NONFORMAL_SEED_OFFSET,
        "constant_coordinates": list(CONSTANT_COORDINATES),
        "fold6_actual_history_read_counts": {
            "actual_age_read_count": 0,
            "actual_previous_action_read_count": 0,
            "actual_actor_time_read_count": 0,
            "donor_or_proxy_read_count": 0,
        },
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }
