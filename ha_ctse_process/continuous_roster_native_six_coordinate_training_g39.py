"""Function-matched CONST10 versus native-six training realization for G39-P0."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np
import torch
from torch import nn

from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import continuous_roster_reactive_reduction_g35 as g35
from ha_ctse_process import continuous_roster_six_coordinate_cs_g38 as g38
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32


ALGORITHM_ID = "CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39"
SOURCE_ID = "CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_P0"
CONST10_ARM = "CONST10_FOLD6"
NATIVE6_ARM = "NATIVE6_CS"
ARMS = (CONST10_ARM, NATIVE6_ARM)
CONST10_INPUT = "CONST10"
NATIVE6_INPUT = "NATIVE6"
FOLDED_CONST6_INPUT = "FOLDED_CONST6"
FULL_OBSERVATION_DIM = 10
RETAINED_OBSERVATION_DIM = 6
CONSTANT_COORDINATES = (0.5, 0.5, 0.5, 24.0 / 47.0)
REMOVABLE_COLUMNS = (6, 7, 8, 9)
REMOVED_ACTOR_WEIGHTS = 136
HIDDEN_DIM = 32
INITIAL_LOG_STD = -1.0
INITIAL_ACTION_TOLERANCE = 1e-7
INITIAL_LOG_PROB_TOLERANCE = 1e-6
GRADIENT_TOLERANCE = 1e-6
GRADIENT_LIVE_TOLERANCE = 1e-12
NONFORMAL_SEED_OFFSET = 900_000

SEED_BASES = {
    "model": 10_391_000,
    "training_ledger": 10_392_000,
    "training_action": 10_393_000,
    "evaluation_base_ledger": 10_394_000,
    "evaluation_process": 10_395_000,
    "evaluation_action": 10_396_000,
    "initial_gradient_probe": 10_397_000,
}
BOOTSTRAP_SEED = 10_398_039


def seed_block(replicate: int, *, formal: bool) -> dict[str, int]:
    if not 0 <= int(replicate) < 3:
        raise ValueError("G39 replicate outside registered support")
    offset = int(replicate) + (0 if formal else NONFORMAL_SEED_OFFSET)
    return {name: base + offset for name, base in SEED_BASES.items()}


def bootstrap_seed(*, formal: bool) -> int:
    return BOOTSTRAP_SEED + (0 if formal else NONFORMAL_SEED_OFFSET)


class G39NativeSixPolicy(g38.G38FoldableMatchedCSPolicy):
    """A genuinely six-input graph with no constants and no folding operation."""

    def __init__(self, *, member_capacity: int) -> None:
        super().__init__(
            RETAINED_OBSERVATION_DIM,
            g32.CRITIC_STATE_DIM,
            member_capacity=int(member_capacity),
            action_dim=g32.ACTION_DIM,
            input_mode=g38.FOLDED6_INPUT,
            hidden_dim=HIDDEN_DIM,
        )
        self.input_mode = NATIVE6_INPUT

    def actor_input(
        self, source_observations: torch.Tensor, active_mask: torch.Tensor
    ) -> torch.Tensor:
        return g38.build_g38_folded_actor_input(source_observations, active_mask)

    def forward_step(
        self, *, observations: torch.Tensor, active_mask: torch.Tensor, **kwargs: Any
    ) -> Any:
        if observations.shape[-1] != RETAINED_OBSERVATION_DIM:
            raise ValueError("G39 native actor accepts exactly six coordinates")
        return g35.ReturnToGoDirectionBalancedFullActorPolicy.forward_step(
            self,
            observations=self.actor_input(observations, active_mask),
            active_mask=active_mask,
            **kwargs,
        )


G39Policy = g38.G38FoldableMatchedCSPolicy | G39NativeSixPolicy


def make_const_model(
    member_capacity: int, *, initialization_seed: int
) -> g38.G38FoldableMatchedCSPolicy:
    model = g38.make_model(
        int(member_capacity),
        input_mode=g38.FOLD6_INPUT,
        initialization_seed=int(initialization_seed),
    )
    return model


def _new_native_shell(member_capacity: int) -> G39NativeSixPolicy:
    rng_state = torch.random.get_rng_state()
    try:
        model = G39NativeSixPolicy(member_capacity=int(member_capacity))
    finally:
        torch.random.set_rng_state(rng_state)
    with torch.no_grad():
        model.log_std.fill_(INITIAL_LOG_STD)
    return model


def derive_native_from_const(
    const: g38.G38FoldableMatchedCSPolicy,
) -> G39NativeSixPolicy:
    """Apply the frozen affine map once; this is initialization, not a fold path."""

    if const.input_mode != g38.FOLD6_INPUT:
        raise ValueError("G39 native derivation requires CONST10 input mode")
    native = _new_native_shell(const.member_capacity)
    source_state = const.state_dict()
    target_state = native.state_dict()
    raw = {
        "policy.member_encoder.0.weight": const.member_input.weight[:, :6],
        "policy.member_encoder.0.bias": g38._fold6_effective_bias(const.member_input),
        "policy.current_observation_residual.weight": const.current_readout.weight[:, :6],
        "policy.current_observation_residual.bias": g38._fold6_effective_bias(
            const.current_readout
        ),
    }
    replacement: dict[str, torch.Tensor] = {}
    for name, target in target_state.items():
        value = raw.get(name, source_state[name])
        if value.shape != target.shape:
            raise ValueError(f"G39 derived tensor shape mismatch: {name}")
        replacement[name] = value.detach().clone()
    native.load_state_dict(replacement, strict=True)
    verify_derived_initialization(const, native)
    return native


def make_paired_models(
    member_capacity: int, *, initialization_seed: int
) -> dict[str, G39Policy]:
    const = make_const_model(
        int(member_capacity), initialization_seed=int(initialization_seed)
    )
    native = derive_native_from_const(const)
    assert_no_shared_state(const, native)
    return {CONST10_ARM: const, NATIVE6_ARM: native}


def _raw_state_names() -> set[str]:
    return {
        "policy.member_encoder.0.weight",
        "policy.member_encoder.0.bias",
        "policy.current_observation_residual.weight",
        "policy.current_observation_residual.bias",
    }


def verify_derived_initialization(
    const: g38.G38FoldableMatchedCSPolicy, native: G39NativeSixPolicy
) -> None:
    if tuple(const.member_input.weight.shape) != (32, 10):
        raise ValueError("G39 CONST member affine is not Linear(10,32)")
    if tuple(const.current_readout.weight.shape) != (2, 10):
        raise ValueError("G39 CONST readout affine is not Linear(10,2)")
    if tuple(native.member_input.weight.shape) != (32, 6):
        raise ValueError("G39 native member affine is not Linear(6,32)")
    if tuple(native.current_readout.weight.shape) != (2, 6):
        raise ValueError("G39 native readout affine is not Linear(6,2)")
    if const.parameter_count - native.parameter_count != REMOVED_ACTOR_WEIGHTS:
        raise ValueError("G39 parameter delta is not exactly 136")
    for const_affine, native_affine in (
        (const.member_input, native.member_input),
        (const.current_readout, native.current_readout),
    ):
        if not torch.equal(native_affine.weight, const_affine.weight[:, :6]):
            raise ValueError("G39 native retained weights were not derived exactly")
        if not torch.equal(
            native_affine.bias, g38._fold6_effective_bias(const_affine)
        ):
            raise ValueError("G39 native effective bias was not derived exactly")
    const_state, native_state = const.state_dict(), native.state_dict()
    for name in const_state:
        if name not in _raw_state_names() and not torch.equal(
            const_state[name], native_state[name]
        ):
            raise ValueError(f"G39 unaffected tensor changed: {name}")


def assert_no_shared_state(const: nn.Module, native: nn.Module) -> None:
    const_tensors = tuple(const.parameters()) + tuple(const.buffers())
    native_tensors = tuple(native.parameters()) + tuple(native.buffers())
    if any(left is right or left.data_ptr() == right.data_ptr() for left in const_tensors for right in native_tensors):
        raise ValueError("G39 arms share tensor storage")


def raw_input_inventory(models: Mapping[str, G39Policy]) -> dict[str, object]:
    const = models[CONST10_ARM]
    native = models[NATIVE6_ARM]
    return {
        "const_member_input_shape": tuple(const.member_input.weight.shape),
        "const_current_readout_shape": tuple(const.current_readout.weight.shape),
        "native_member_input_shape": tuple(native.member_input.weight.shape),
        "native_current_readout_shape": tuple(native.current_readout.weight.shape),
        "parameter_delta": const.parameter_count - native.parameter_count,
        "const_raw_width": const.member_input.in_features,
        "native_raw_width": native.member_input.in_features,
        "native_has_constant_columns": native.member_input.in_features != 6,
        "native_has_fold_path": hasattr(native, "fold"),
    }


def collect_g39_trajectory(
    model: G39Policy,
    *,
    episode_ids: Iterable[int],
    ledger_seed: int,
    action_seed: int,
    device: torch.device,
    profiles: Sequence[g32.RosterProfile] = g32.TRAIN_PROFILES,
) -> g32.ContinuousRosterTrajectory:
    """Collect one six-wide trajectory for either independent arm."""

    ids = tuple(int(value) for value in episode_ids)
    profile_rows = tuple(profiles)
    if not ids or not profile_rows:
        raise ValueError("G39 collection requires episodes and profiles")
    capacity = profile_rows[0].member_capacity
    if any(row.member_capacity != capacity for row in profile_rows) or model.member_capacity != capacity:
        raise ValueError("G39 collection capacity mismatch")
    ledgers = tuple(
        g32.make_ledger(
            episode,
            master_seed=int(ledger_seed),
            profile=profile_rows[episode % len(profile_rows)],
        )
        for episode in ids
    )
    envs = tuple(g32.RuntimeCapacityRosterEnv(row) for row in ledgers)
    batch = len(ids)
    noise = g32.make_action_noise(ids, action_seed=int(action_seed), member_capacity=capacity)
    hidden = torch.zeros((batch, capacity, model.hidden_dim), device=device)
    shapes = {
        "observations": (g32.HORIZON, batch, capacity, RETAINED_OBSERVATION_DIM),
        "active_mask": (g32.HORIZON, batch, capacity),
        "critic_states": (g32.HORIZON, batch, g32.CRITIC_STATE_DIM),
        "actions": (g32.HORIZON, batch, capacity, g32.ACTION_DIM),
        "pre_tanh_actions": (g32.HORIZON, batch, capacity, g32.ACTION_DIM),
        "old_log_probs": (g32.HORIZON, batch, capacity),
        "old_values": (g32.HORIZON, batch),
        "rewards": (g32.HORIZON, batch),
        "hidden_before": (g32.HORIZON, batch, capacity, model.hidden_dim),
        "hidden_after": (g32.HORIZON, batch, capacity, model.hidden_dim),
        "prefix_action_sums": (g32.HORIZON, batch, capacity, g32.ACTION_DIM),
        "terminal_hidden_reset_mask": (g32.HORIZON, batch, capacity),
    }
    rows = {
        name: torch.empty(
            shape,
            dtype=torch.bool if name in ("active_mask", "terminal_hidden_reset_mask") else torch.float32,
        )
        for name, shape in shapes.items()
    }
    model.eval()
    with torch.no_grad():
        for time in range(g32.HORIZON):
            views = tuple(
                g38.observe_g38_actor_source(env, input_mode=g38.FOLD6_INPUT)
                for env in envs
            )
            terminal_reset = torch.zeros((batch, capacity), dtype=torch.bool, device=device)
            for batch_index, view in enumerate(views):
                if view.membership_change.terminally_left:
                    terminal_reset[batch_index, list(view.membership_change.terminally_left)] = True
            g32._delete_terminal_hidden(hidden, views)
            observations = torch.as_tensor(np.stack([row.observations for row in views]), device=device)
            active = torch.as_tensor(np.stack([row.active_mask for row in views]), device=device)
            critic = torch.as_tensor(np.stack([row.critic_state for row in views]), device=device)
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
                    g38.advance_g38_environment(
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


def initial_forward_match(
    const: g38.G38FoldableMatchedCSPolicy,
    native: G39NativeSixPolicy,
    *,
    observations: torch.Tensor,
    active_mask: torch.Tensor,
    critic_state: torch.Tensor,
    sampling_noise: torch.Tensor,
) -> dict[str, object]:
    hidden = torch.zeros((*active_mask.shape, HIDDEN_DIM), dtype=observations.dtype)
    common = {
        "observations": observations,
        "active_mask": active_mask,
        "critic_state": critic_state,
        "hidden": hidden,
        "sampling_noise": sampling_noise,
    }
    left = const.forward_step(**common)
    right = native.forward_step(**common)
    active, inactive = active_mask, ~active_mask
    errors = {
        "pre_tanh": float((left.pre_tanh_actions[active] - right.pre_tanh_actions[active]).abs().max()) if bool(active.any()) else 0.0,
        "actions": float((left.actions[active] - right.actions[active]).abs().max()) if bool(active.any()) else 0.0,
        "prefix_action_sums": float((left.prefix_action_sums[active] - right.prefix_action_sums[active]).abs().max()) if bool(active.any()) else 0.0,
        "token_log_prob": float((left.token_log_probs[active] - right.token_log_probs[active]).abs().max()) if bool(active.any()) else 0.0,
    }
    exact = {
        "critic_value": torch.equal(left.value, right.value),
        "log_std": torch.equal(const.log_std, native.log_std),
        "inactive_actions": bool(torch.equal(left.actions[inactive], right.actions[inactive]) and torch.count_nonzero(left.actions[inactive]) == 0),
        "inactive_likelihoods": bool(torch.equal(left.token_log_probs[inactive], right.token_log_probs[inactive]) and torch.count_nonzero(left.token_log_probs[inactive]) == 0),
        "next_hidden_zero": bool(torch.count_nonzero(left.next_hidden) == 0 and torch.count_nonzero(right.next_hidden) == 0),
    }
    passed = (
        all(exact.values())
        and max(errors[name] for name in ("pre_tanh", "actions", "prefix_action_sums")) <= INITIAL_ACTION_TOLERANCE
        and errors["token_log_prob"] <= INITIAL_LOG_PROB_TOLERANCE
    )
    return {"errors": errors, "exact": exact, "passed": bool(passed)}


def initial_trajectory_match(
    const: g32.ContinuousRosterTrajectory,
    native: g32.ContinuousRosterTrajectory,
) -> dict[str, object]:
    exact_names = (
        "observations",
        "active_mask",
        "critic_states",
        "old_values",
        "hidden_before",
        "hidden_after",
        "terminal_hidden_reset_mask",
    )
    exact = {name: torch.equal(getattr(const, name), getattr(native, name)) for name in exact_names}
    exact.update(
        {
            "ledgers": all(repr(left) == repr(right) for left, right in zip(const.ledgers, native.ledgers)),
            "roster": all(left.roster_sizes == right.roster_sizes for left, right in zip(const.outcomes, native.outcomes)),
            "inactive_actions": bool(torch.equal(const.actions[~const.active_mask], native.actions[~native.active_mask]) and torch.count_nonzero(const.actions[~const.active_mask]) == 0),
            "inactive_likelihoods": bool(torch.equal(const.old_log_probs[~const.active_mask], native.old_log_probs[~native.active_mask]) and torch.count_nonzero(const.old_log_probs[~const.active_mask]) == 0),
            "next_hidden_zero": bool(torch.count_nonzero(const.hidden_after) == 0 and torch.count_nonzero(native.hidden_after) == 0),
        }
    )
    active = const.active_mask
    errors = {
        "rewards": float((const.rewards - native.rewards).abs().max()),
        "utilities": max(
            abs(left.utility - right.utility)
            for left, right in zip(const.outcomes, native.outcomes)
        ),
        "actions": float((const.actions[active] - native.actions[active]).abs().max()),
        "pre_tanh": float((const.pre_tanh_actions[active] - native.pre_tanh_actions[active]).abs().max()),
        "prefix_action_sums": float((const.prefix_action_sums[active] - native.prefix_action_sums[active]).abs().max()),
        "token_log_prob": float((const.old_log_probs[active] - native.old_log_probs[active]).abs().max()),
    }
    passed = (
        all(exact.values())
        and max(errors[name] for name in ("rewards", "utilities", "actions", "pre_tanh", "prefix_action_sums")) <= INITIAL_ACTION_TOLERANCE
        and errors["token_log_prob"] <= INITIAL_LOG_PROB_TOLERANCE
    )
    return {"errors": errors, "exact": exact, "passed": bool(passed)}


def _gradient_rows(
    objective: torch.Tensor,
    model: G39Policy,
) -> dict[str, tuple[torch.Tensor, torch.Tensor]]:
    pairs = {
        "member_input": (model.member_input.weight, model.member_input.bias),
        "current_readout": (model.current_readout.weight, model.current_readout.bias),
    }
    result: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
    for name, parameters in pairs.items():
        weight, bias = torch.autograd.grad(
            objective,
            parameters,
            retain_graph=True,
        )
        result[name] = (weight, bias)
    return result


def _combined_gradient_liveness(
    removable_gradients: Mapping[str, Sequence[torch.Tensor]],
    native_bias_gradients: Mapping[str, Sequence[torch.Tensor]],
) -> dict[str, object]:
    """Require fast-or-RTG liveness for every treated scalar, not just a column."""

    dead_removable: list[str] = []
    dead_native_biases: list[str] = []
    removable_total = 0
    removable_live = 0
    native_bias_total = 0
    native_bias_live = 0
    for affine in ("member_input", "current_readout"):
        removable_rows = tuple(removable_gradients[affine])
        native_bias_rows = tuple(native_bias_gradients[affine])
        if len(removable_rows) != 2 or len(native_bias_rows) != 2:
            raise ValueError("G39 liveness requires fast and RTG gradients")
        removable_max = torch.stack(
            tuple(row.detach().abs() for row in removable_rows)
        ).amax(dim=0)
        bias_max = torch.stack(
            tuple(row.detach().abs() for row in native_bias_rows)
        ).amax(dim=0)
        removable_mask = removable_max > GRADIENT_LIVE_TOLERANCE
        bias_mask = bias_max > GRADIENT_LIVE_TOLERANCE
        removable_total += int(removable_mask.numel())
        removable_live += int(removable_mask.sum())
        native_bias_total += int(bias_mask.numel())
        native_bias_live += int(bias_mask.sum())
        dead_removable.extend(
            f"{affine}[{output},{column + RETAINED_OBSERVATION_DIM}]"
            for output, column in torch.nonzero(~removable_mask).tolist()
        )
        dead_native_biases.extend(
            f"{affine}.bias[{index}]"
            for index in torch.nonzero(~bias_mask).flatten().tolist()
        )
    return {
        "removable_scalar_total": removable_total,
        "removable_scalar_live_count": removable_live,
        "dead_removable_scalars": dead_removable,
        "all_136_removable_scalars_live": bool(
            removable_total == REMOVED_ACTOR_WEIGHTS
            and removable_live == REMOVED_ACTOR_WEIGHTS
        ),
        "native_effective_bias_total": native_bias_total,
        "native_effective_bias_live_count": native_bias_live,
        "dead_native_effective_biases": dead_native_biases,
        "all_native_effective_biases_live": bool(
            native_bias_total > 0 and native_bias_live == native_bias_total
        ),
    }


def initial_gradient_audit(
    const: g38.G38FoldableMatchedCSPolicy,
    native: G39NativeSixPolicy,
    const_trajectory: Any,
    native_trajectory: Any,
    *,
    gamma: float,
) -> dict[str, object]:
    const_objectives = g38._objectives(const, const_trajectory, gamma=gamma, device=torch.device("cpu"))
    native_objectives = g38._objectives(native, native_trajectory, gamma=gamma, device=torch.device("cpu"))
    objectives = ("fast", "return_to_go")
    rows: dict[str, object] = {}
    passed = True
    constants = torch.tensor(CONSTANT_COORDINATES)
    removable_gradients: dict[str, list[torch.Tensor]] = {
        "member_input": [],
        "current_readout": [],
    }
    native_bias_gradients: dict[str, list[torch.Tensor]] = {
        "member_input": [],
        "current_readout": [],
    }
    native_gradient_norms: dict[str, list[float]] = {
        "member_input": [],
        "current_readout": [],
    }
    for objective_name, const_objective, native_objective in zip(objectives, const_objectives, native_objectives):
        const_grads = _gradient_rows(const_objective, const)
        native_grads = _gradient_rows(native_objective, native)
        for affine in ("member_input", "current_readout"):
            const_weight, const_bias = const_grads[affine]
            native_weight, native_bias = native_grads[affine]
            relation = constants[:, None] * native_bias[None, :]
            errors = {
                "retained_weight": float((const_weight[:, :6] - native_weight).abs().max()),
                "bias": float((const_bias - native_bias).abs().max()),
                "constant_columns": float((const_weight[:, 6:10].T - relation).abs().max()),
            }
            finite = bool(
                torch.isfinite(const_weight).all()
                and torch.isfinite(const_bias).all()
                and torch.isfinite(native_weight).all()
                and torch.isfinite(native_bias).all()
            )
            native_norm = float(torch.linalg.vector_norm(torch.cat((native_weight.reshape(-1), native_bias))).detach())
            removable_gradients[affine].append(
                const_weight[:, RETAINED_OBSERVATION_DIM:].detach()
            )
            native_bias_gradients[affine].append(native_bias.detach())
            native_gradient_norms[affine].append(native_norm)
            row_pass = finite and max(errors.values()) <= GRADIENT_TOLERANCE
            rows[f"{objective_name}_{affine}"] = {
                "errors": errors,
                "finite": finite,
                "native_gradient_norm": native_norm,
                "passed": bool(row_pass),
            }
            passed &= bool(row_pass)
    liveness = _combined_gradient_liveness(
        removable_gradients,
        native_bias_gradients,
    )
    liveness["native_gradient_norm_live"] = {
        affine: max(norms) > GRADIENT_LIVE_TOLERANCE
        for affine, norms in native_gradient_norms.items()
    }
    liveness["passed"] = bool(
        liveness["all_136_removable_scalars_live"]
        and liveness["all_native_effective_biases_live"]
        and all(liveness["native_gradient_norm_live"].values())
    )
    rows["scalar_liveness"] = liveness
    passed &= bool(liveness["passed"])
    rows["passed"] = bool(passed)
    return rows


def fold_const_checkpoint(
    const: g38.G38FoldableMatchedCSPolicy,
) -> g38.G38FoldableMatchedCSPolicy:
    return g38.fold_g38_constant_actor_checkpoint(const)


def evaluate_g39_model(
    model: G39Policy,
    *,
    processes: Sequence[g34.RandomProcessLedger],
    action_seed: int,
    process_kind: str,
    deterministic: bool,
    device: torch.device = torch.device("cpu"),
) -> tuple[tuple[dict[str, object], ...], bool]:
    """Evaluate a six-source-coordinate deployment on one paired G34 ledger set."""

    if process_kind not in ("random", "fixed"):
        raise ValueError("G39 process kind must be random or fixed")
    rows = tuple(processes)
    if not rows or any(row.member_capacity != model.member_capacity for row in rows):
        raise ValueError("G39 model/process capacity mismatch")
    envs = tuple(
        g34.RandomProcessRosterEnv(row)
        if process_kind == "random"
        else g32.RuntimeCapacityRosterEnv(row.base)
        for row in rows
    )
    noise = g32.make_action_noise(
        (row.episode_id for row in rows),
        action_seed=int(action_seed),
        member_capacity=model.member_capacity,
    )
    hidden = torch.zeros((len(rows), model.member_capacity, model.hidden_dim), device=device)
    frozen_hidden: list[dict[int, torch.Tensor]] = [dict() for _ in rows]
    frozen_age: list[dict[int, int]] = [dict() for _ in rows]
    frozen_actions: list[dict[int, np.ndarray]] = [dict() for _ in rows]
    lifecycle_valid = True
    model.eval()
    with torch.no_grad():
        for time in range(g32.HORIZON):
            views = tuple(
                g38.observe_g38_actor_source(env, input_mode=g38.FOLD6_INPUT)
                for env in envs
            )
            for index, view in enumerate(views):
                for key in view.membership_change.temporarily_left:
                    frozen_hidden[index][key] = hidden[index, key].clone()
                    frozen_age[index][key] = int(envs[index].age[key])
                    frozen_actions[index][key] = envs[index].previous_actions[key].copy()
                for key, value in frozen_hidden[index].items():
                    if key not in view.membership_change.rejoined and not bool(view.active_mask[key]):
                        lifecycle_valid &= bool(torch.equal(hidden[index, key], value))
                        lifecycle_valid &= int(envs[index].age[key]) == frozen_age[index][key]
                        lifecycle_valid &= bool(np.array_equal(envs[index].previous_actions[key], frozen_actions[index][key]))
                for key in view.membership_change.rejoined:
                    lifecycle_valid &= bool(torch.equal(hidden[index, key], frozen_hidden[index][key]))
                    lifecycle_valid &= int(envs[index].age[key]) == frozen_age[index][key]
                    lifecycle_valid &= bool(np.array_equal(envs[index].previous_actions[key], frozen_actions[index][key]))
                    frozen_hidden[index].pop(key)
                    frozen_age[index].pop(key)
                    frozen_actions[index].pop(key)
                for key in view.membership_change.joined:
                    lifecycle_valid &= bool(torch.count_nonzero(hidden[index, key]) == 0)
                    lifecycle_valid &= envs[index].age[key] == 0
                    lifecycle_valid &= not np.count_nonzero(envs[index].previous_actions[key])
            g32._delete_terminal_hidden(hidden, views)
            for index, view in enumerate(views):
                for key in view.membership_change.terminally_left:
                    lifecycle_valid &= bool(torch.count_nonzero(hidden[index, key]) == 0)
            active = torch.as_tensor(np.stack([view.active_mask for view in views]), device=device)
            arguments = {
                "observations": torch.as_tensor(np.stack([view.observations for view in views]), device=device),
                "active_mask": active,
                "critic_state": torch.as_tensor(np.stack([view.critic_state for view in views]), device=device),
                "hidden": hidden,
            }
            output = (
                model.forward_step(**arguments, deterministic=True)
                if deterministic
                else model.forward_step(
                    **arguments,
                    sampling_noise=torch.as_tensor(noise[time], device=device),
                )
            )
            lifecycle_valid &= bool(torch.equal(output.next_hidden[~active], hidden[~active]))
            for index, (env, view) in enumerate(zip(envs, views)):
                g38.advance_g38_environment(
                    env, view, output.actions[index].detach().cpu().numpy()
                )
            hidden = output.next_hidden
    lifecycle_valid &= not any(frozen_hidden) and not any(frozen_age) and not any(frozen_actions)
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
    return metrics, bool(lifecycle_valid)


def make_process_ledgers(
    *, replicate: int, capacity: int, episode_count: int, formal: bool
) -> tuple[g34.RandomProcessLedger, ...]:
    if capacity not in g34.CAPACITIES or not 1 <= int(episode_count) <= 64:
        raise ValueError("G39 process request outside registered support")
    seeds = seed_block(replicate, formal=formal)
    times = g35._time_assignments(capacity=capacity, process_seed=seeds["evaluation_process"])
    orders = _balanced_64_assignments(
        g34.EVENT_ORDERS,
        replicate=replicate,
        capacity=capacity,
        process_seed=seeds["evaluation_process"],
        stream=1,
    )
    if capacity == 6:
        profiles = (g32.SMALL_CAPACITY_6,) * 64
    elif capacity == 12:
        profiles = (g32.LARGE_CAPACITY_12,) * 64
    else:
        profiles = _balanced_64_assignments(
            g32.TRAIN_PROFILES,
            replicate=replicate,
            capacity=capacity,
            process_seed=seeds["evaluation_process"],
            stream=2,
        )
    rows: list[g34.RandomProcessLedger] = []
    for local_episode in range(int(episode_count)):
        base = g32.make_ledger(
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
        raise ValueError("G39 process signatures must be unique")
    return tuple(rows)


def _balanced_64_assignments(
    categories: Sequence[object],
    *,
    replicate: int,
    capacity: int,
    process_seed: int,
    stream: int,
) -> tuple[Any, ...]:
    """Assign the frozen rotating 22/21/21 inventory over 64 episode IDs."""

    if len(categories) != 3 or not 0 <= int(replicate) < 3:
        raise ValueError("G39 balanced source requires three categories and replicates")
    counts = [21, 21, 21]
    counts[int(replicate) % 3] = 22
    order = sorted(
        range(64),
        key=lambda episode: (
            int(
                g35._process_rng(
                    int(process_seed), int(capacity), episode, int(stream)
                ).integers(0, 2**63)
            ),
            episode,
        ),
    )
    assigned: list[object | None] = [None] * 64
    offset = 0
    for category, count in zip(categories, counts):
        for episode in order[offset : offset + count]:
            assigned[episode] = category
        offset += count
    if offset != 64 or any(row is None for row in assigned):
        raise RuntimeError("G39 balanced 64 assignment did not close")
    return tuple(assigned)


def source_controls() -> dict[str, object]:
    return {
        "source_id": SOURCE_ID,
        "training_source": "G32 capacity-8 fixed",
        "evaluation_source": "G34 fixed/random capacities 6|8|12",
        "horizon": g32.HORIZON,
        "training_capacity": g32.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "seed_bases": dict(SEED_BASES),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "nonformal_seed_offset": NONFORMAL_SEED_OFFSET,
        "constant_coordinates": list(CONSTANT_COORDINATES),
        "stored_source_coordinates": 6,
        "removed_actor_weights": REMOVED_ACTOR_WEIGHTS,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }
