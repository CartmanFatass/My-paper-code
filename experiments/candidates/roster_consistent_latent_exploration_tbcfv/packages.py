"""Exact deterministic draw tying and renewal laws for the five TBCFV arms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence

import torch

from .config import ACTIVE_CONTINUATION, C0P0, C0P1, C1P0, C1P1, FLEX, LEARNED_PACKAGES, NEW_EPOCH
from .models import TBCFVModel

PhysicalKey = Hashable


@dataclass(frozen=True)
class FixtureDrawBank:
    """Caller-owned deterministic tensors; unused banks may remain ``None``."""

    epoch_common: torch.Tensor | None = None
    epoch_private: Mapping[PhysicalKey, torch.Tensor] | None = None
    active_common_refresh: torch.Tensor | None = None
    active_private_refresh: Mapping[PhysicalKey, torch.Tensor] | None = None
    newcomer_private: Mapping[PhysicalKey, torch.Tensor] | None = None
    new_epoch_common: torch.Tensor | None = None
    new_epoch_private: Mapping[PhysicalKey, torch.Tensor] | None = None
    flex_event_noise: Mapping[PhysicalKey, torch.Tensor] | None = None


@dataclass(frozen=True)
class PlanState:
    """Internal physical-survivor transport state, never an actor observation."""

    arm: str
    common: torch.Tensor | None
    private: Mapping[PhysicalKey, torch.Tensor] | None


@dataclass(frozen=True)
class PlanTransition:
    plans: torch.Tensor
    state: PlanState
    used_draws: tuple[str, ...]
    score_draws: tuple[tuple[str, PhysicalKey | None], ...] = ()
    common_delta: torch.Tensor | None = None
    agent_delta: torch.Tensor | None = None


def _plan(value: torch.Tensor | None, name: str) -> torch.Tensor:
    if value is None:
        raise ValueError(f"required fixture draw is absent: {name}")
    tensor = value.to(torch.float64)
    if tensor.shape != (4,):
        raise ValueError(f"{name} must be a four-dimensional plan tensor")
    return tensor.detach()


def _mapped(
    values: Mapping[PhysicalKey, torch.Tensor] | None,
    keys: Sequence[PhysicalKey],
    name: str,
) -> dict[PhysicalKey, torch.Tensor]:
    if values is None:
        raise ValueError(f"required fixture draw bank is absent: {name}")
    missing = [key for key in keys if key not in values]
    if missing:
        raise ValueError(f"{name} lacks required physical keys: {missing!r}")
    return {key: _plan(values[key], f"{name}[{key!r}]") for key in keys}


def _aligned(state: PlanState, current_keys: Sequence[PhysicalKey]) -> torch.Tensor:
    if state.common is not None:
        return torch.stack([state.common for _ in current_keys], dim=0)
    if state.private is None:
        raise RuntimeError("plan state has neither common nor private plan storage")
    return torch.stack([state.private[key] for key in current_keys], dim=0)


def initialize_plans(
    arm: str,
    current_physical_keys: Sequence[PhysicalKey],
    draws: FixtureDrawBank,
) -> PlanTransition:
    """Apply the epoch-start tying law without generating any draw."""

    if arm not in LEARNED_PACKAGES:
        raise ValueError(f"unknown learned package: {arm}")
    keys = tuple(current_physical_keys)
    if not keys:
        raise ValueError("current roster must be nonempty")
    if len(set(keys)) != len(keys):
        raise ValueError("physical transport keys must be unique")
    if arm in (C1P1, FLEX, C1P0):
        common = _plan(draws.epoch_common, "epoch_common")
        state = PlanState(arm=arm, common=common, private=None)
        return PlanTransition(
            _aligned(state, keys), state, ("epoch_common",), (("epoch_common", None),)
        )
    private = _mapped(draws.epoch_private, keys, "epoch_private")
    state = PlanState(arm=arm, common=None, private=private)
    return PlanTransition(
        _aligned(state, keys),
        state,
        ("epoch_private",),
        tuple(("epoch_private", key) for key in keys),
    )


def transition_plans(
    state: PlanState,
    current_physical_keys: Sequence[PhysicalKey],
    event_condition: str,
    draws: FixtureDrawBank,
    *,
    model: TBCFVModel | None = None,
    public_event_summary: torch.Tensor | None = None,
    physical_features: torch.Tensor | None = None,
) -> PlanTransition:
    """Apply the exact active-event or new-epoch renewal/transport law.

    Physical keys are confined to this transport layer. Returned actor plans
    are aligned tensors and carry no fixed key or roster-slot feature.
    """

    if state.arm not in LEARNED_PACKAGES:
        raise ValueError(f"unknown learned package: {state.arm}")
    if event_condition not in (ACTIVE_CONTINUATION, NEW_EPOCH):
        raise ValueError(f"unknown event condition: {event_condition}")
    keys = tuple(current_physical_keys)
    if not keys or len(set(keys)) != len(keys):
        raise ValueError("current physical roster must be nonempty with unique keys")

    if event_condition == NEW_EPOCH:
        if state.arm in (C1P1, FLEX, C1P0):
            common = _plan(draws.new_epoch_common, "new_epoch_common")
            next_state = PlanState(state.arm, common=common, private=None)
            base = _aligned(next_state, keys)
            used = ("new_epoch_common",)
            score_draws = (("new_epoch_common", None),)
        else:
            private = _mapped(draws.new_epoch_private, keys, "new_epoch_private")
            next_state = PlanState(state.arm, common=None, private=private)
            base = _aligned(next_state, keys)
            used = ("new_epoch_private",)
            score_draws = tuple(("new_epoch_private", key) for key in keys)
    elif state.arm == C1P0:
        common = _plan(draws.active_common_refresh, "active_common_refresh")
        next_state = PlanState(state.arm, common=common, private=None)
        base = _aligned(next_state, keys)
        used = ("active_common_refresh",)
        score_draws = (("active_common_refresh", None),)
    elif state.arm == C0P0:
        private = _mapped(draws.active_private_refresh, keys, "active_private_refresh")
        next_state = PlanState(state.arm, common=None, private=private)
        base = _aligned(next_state, keys)
        used = ("active_private_refresh",)
        score_draws = tuple(("active_private_refresh", key) for key in keys)
    elif state.arm == C0P1:
        if state.private is None:
            raise ValueError("C0P1 requires private pre-event state")
        survivor_keys = tuple(key for key in keys if key in state.private)
        newcomer_keys = tuple(key for key in keys if key not in state.private)
        private = {key: state.private[key] for key in survivor_keys}
        if newcomer_keys:
            private.update(_mapped(draws.newcomer_private, newcomer_keys, "newcomer_private"))
        next_state = PlanState(state.arm, common=None, private=private)
        base = _aligned(next_state, keys)
        used = ("survivor_private_transport",) + (("newcomer_private",) if newcomer_keys else ())
        score_draws = tuple(("newcomer_private", key) for key in newcomer_keys)
    else:
        # C1P1 and FLEX retain the pre-event common physical commitment.
        if state.common is None:
            raise ValueError(f"{state.arm} requires common pre-event state")
        next_state = state
        base = _aligned(next_state, keys)
        used = ("common_physical_transport",)
        score_draws = ()

    if state.arm != FLEX:
        return PlanTransition(
            base,
            next_state,
            used,
            score_draws,
            common_delta=None,
            agent_delta=None,
        )
    if model is None or public_event_summary is None or physical_features is None:
        raise ValueError("FLEX transition requires model, public event summary, and physical features")
    if tuple(physical_features.shape) != (len(keys), 5):
        raise ValueError("FLEX physical features must be [current_agents,5]")
    noises = _mapped(draws.flex_event_noise, keys, "flex_event_noise")
    noise_tensor = torch.stack([noises[key] for key in keys], dim=0)
    event = public_event_summary.to(torch.float64)
    if event.shape == (68,):
        event = event.expand(len(keys), -1)
    if tuple(event.shape) != (len(keys), 68):
        raise ValueError("public event summary must be [68] or [current_agents,68]")
    flex_plans, common_delta, agent_delta = model.event_plan(
        FLEX,
        base,
        event,
        physical_features,
        noise_tensor,
    )
    return PlanTransition(
        plans=flex_plans,
        state=next_state,
        used_draws=used + ("flex_event_noise",),
        score_draws=score_draws,
        common_delta=common_delta,
        agent_delta=agent_delta,
    )
