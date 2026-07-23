"""Independent learned OR/DUM/EHC core for the frozen G1 source."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import os
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

import numpy as np
import torch
from torch import Tensor, nn

from ha_ctse_process.temporal_duty_g1 import G1EpisodeSpec, TemporalDutyG1Env


SOURCE_FAMILY = "ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1"
CHECKPOINT_SCHEMA = "access_positive_mechanism_matched_ehc_g1_v1"
ARM_NAMES = ("OR", "DUM", "EHC")
ACTION_VALUES = (-1, 0, 1)
EVENT_VALUES = ("KEEP", "RENEW")
MARK_VALUES = (-1, 1)
ACTOR_WIDTH = 6
CRITIC_WIDTH = 10
HIDDEN_WIDTH = 32
MAXIMUM_CAPACITY = 4

GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
PRIMITIVE_ENTROPY_COEFFICIENT = 0.01
EVENT_ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.50
LEARNING_RATE = 0.0003
PPO_PASSES = 4


@dataclass(frozen=True)
class SeedRegistry:
    model: int = 158058
    train_task: int = 168058
    train_membership: int = 169058
    train_duty: int = 170058
    train_opportunity: int = 171058
    train_event: int = 172058
    train_mark: int = 173058
    train_primitive: int = 174058
    evaluation_task: int = 198058
    evaluation_membership: int = 199058
    evaluation_duty: int = 200058
    evaluation_opportunity: int = 201058
    evaluation_event: int = 202058
    evaluation_mark: int = 203058
    evaluation_primitive: int = 204058
    audit: int = 206058
    bootstrap: int = 208058
    replicate_offset: int = 1000


class EHCPolicy(nn.Module):
    """Same parameter structure for every arm, with separated actor and critic."""

    def __init__(self) -> None:
        super().__init__()
        self.actor_encoder = nn.Linear(ACTOR_WIDTH, HIDDEN_WIDTH)
        self.recurrent = nn.GRUCell(HIDDEN_WIDTH, HIDDEN_WIDTH)
        self.primitive_head = nn.Linear(HIDDEN_WIDTH, len(ACTION_VALUES))
        self.critic_encoder = nn.Linear(CRITIC_WIDTH, HIDDEN_WIDTH)
        self.value_head = nn.Sequential(
            nn.Linear(HIDDEN_WIDTH, HIDDEN_WIDTH),
            nn.Tanh(),
            nn.Linear(HIDDEN_WIDTH, 1),
        )
        self.event_head = nn.Linear(HIDDEN_WIDTH, len(EVENT_VALUES))
        self.mark_head = nn.Linear(HIDDEN_WIDTH, len(MARK_VALUES))
        self.mark_treatment = nn.Parameter(torch.empty(len(ACTION_VALUES)))
        nn.init.normal_(self.mark_treatment, mean=0.0, std=0.02)

    def actor_step(self, actor: Tensor, hidden: Tensor) -> tuple[Tensor, Tensor]:
        _require_last_width(actor, ACTOR_WIDTH, "actor")
        _require_last_width(hidden, HIDDEN_WIDTH, "hidden")
        encoded = torch.tanh(self.actor_encoder(actor))
        next_hidden = self.recurrent(encoded, hidden)
        return next_hidden, next_hidden

    def primitive_logits(
        self,
        actor: Tensor,
        hidden: Tensor,
        held_mark: Tensor,
        *,
        arm: str,
    ) -> tuple[Tensor, Tensor]:
        _require_arm(arm)
        features, next_hidden = self.actor_step(actor, hidden)
        logits = self.primitive_head(features)
        if arm == "EHC":
            logits = logits + held_mark.to(logits.dtype).unsqueeze(-1) * self.mark_treatment
        return logits, next_hidden

    def event_mark_logits(
        self, actor_features: Tensor, *, detach_features: bool = True
    ) -> tuple[Tensor, Tensor]:
        _require_last_width(actor_features, HIDDEN_WIDTH, "actor_features")
        features = actor_features.detach() if detach_features else actor_features
        return self.event_head(features), self.mark_head(features)

    def value(self, critic: Tensor, active_mask: Tensor) -> Tensor:
        if critic.ndim != 3 or critic.shape[-1] != CRITIC_WIDTH:
            raise ValueError("critic must have shape [batch, capacity, 10]")
        if active_mask.shape != critic.shape[:-1] or active_mask.dtype != torch.bool:
            raise ValueError("active_mask must be boolean [batch, capacity]")
        encoded = torch.tanh(self.critic_encoder(critic))
        weights = active_mask.to(encoded.dtype).unsqueeze(-1)
        denominator = weights.sum(dim=1).clamp_min(1.0)
        pooled = (encoded * weights).sum(dim=1) / denominator
        return self.value_head(pooled).squeeze(-1)


@dataclass
class ArmTrainingState:
    arm: str
    replicate: int
    update: int
    backend: str
    torch_threads: int
    seed_registry: SeedRegistry
    model: EHCPolicy
    base_optimizer: torch.optim.Optimizer
    event_optimizer: torch.optim.Optimizer | None
    generators: dict[str, torch.Generator]
    base_optimizer_steps: int = 0
    event_optimizer_steps: int = 0


@dataclass(frozen=True)
class RolloutBatch:
    """One complete padded rollout; stochastic choices are stored, never redrawn."""

    source_family: str
    arm: str
    replicate: int
    actor: Tensor
    critic: Tensor
    active_mask: Tensor
    reset_mask: Tensor
    held_mark: Tensor
    opportunity_kind: Tensor
    actions: Tensor
    events: Tensor
    marks: Tensor
    old_primitive_logp: Tensor
    old_event_mark_logp: Tensor
    old_values: Tensor
    rewards: Tensor
    dones: Tensor
    advantages: Tensor
    returns: Tensor
    natural_rows: tuple[dict[str, Any], ...] = ()
    outcomes: tuple[dict[str, float], ...] = ()
    provenance: tuple[dict[str, Any], ...] = ()
    exposure: Mapping[str, int] | None = None


@dataclass(frozen=True)
class ReplayResult:
    primitive_logits: Tensor
    event_logits: Tensor
    mark_logits: Tensor
    primitive_logp: Tensor
    event_mark_logp: Tensor
    values: Tensor
    primitive_entropy: Tensor
    event_entropy: Tensor


def _require_last_width(tensor: Tensor, width: int, name: str) -> None:
    if tensor.ndim < 2 or tensor.shape[-1] != width:
        raise ValueError(f"{name} must have last dimension {width}")


def _require_arm(arm: str) -> None:
    if arm not in ARM_NAMES:
        raise ValueError(f"arm must be one of {ARM_NAMES}, got {arm!r}")


def _canonical_seed_registry(
    seed_registry: SeedRegistry | Mapping[str, Any] | None,
) -> SeedRegistry:
    canonical = SeedRegistry()
    if seed_registry is None:
        return canonical
    if isinstance(seed_registry, SeedRegistry):
        candidate = seed_registry
    elif isinstance(seed_registry, Mapping):
        try:
            candidate = SeedRegistry(**dict(seed_registry))
        except (TypeError, ValueError) as error:
            raise ValueError("seed_registry is not the exact frozen G1 registry") from error
    else:
        raise TypeError("seed_registry must be SeedRegistry, mapping, or None")
    if candidate != canonical:
        raise ValueError("seed_registry is not the exact frozen G1 registry")
    return candidate


def _require_runtime(backend: str, torch_threads: int) -> None:
    if backend != "cpu":
        raise ValueError("the frozen G1 backend is cpu")
    if type(torch_threads) is not int or torch_threads != 1:
        raise ValueError("the frozen G1 torch thread contract is exactly one")
    if torch.get_num_threads() != 1:
        raise RuntimeError("torch runtime must be configured for exactly one thread")


def _make_optimizers(
    model: EHCPolicy, arm: str
) -> tuple[torch.optim.Optimizer, torch.optim.Optimizer | None]:
    event_parameter_ids = {
        id(parameter)
        for module in (model.event_head, model.mark_head)
        for parameter in module.parameters()
    }
    base_parameters = [
        parameter
        for parameter in model.parameters()
        if id(parameter) not in event_parameter_ids
    ]
    event_parameters = [
        parameter
        for module in (model.event_head, model.mark_head)
        for parameter in module.parameters()
    ]
    base_optimizer = torch.optim.Adam(base_parameters, lr=LEARNING_RATE)
    event_optimizer = (
        None
        if arm == "OR"
        else torch.optim.Adam(event_parameters, lr=LEARNING_RATE)
    )
    return base_optimizer, event_optimizer


def _make_generators(registry: SeedRegistry, replicate: int) -> dict[str, torch.Generator]:
    offset = registry.replicate_offset * replicate
    seeds = {
        "primitive": registry.train_primitive + offset,
        "event": registry.train_event + offset,
        "mark": registry.train_mark + offset,
        "evaluation_primitive": registry.evaluation_primitive + offset,
        "evaluation_event": registry.evaluation_event + offset,
        "evaluation_mark": registry.evaluation_mark + offset,
    }
    return {
        name: torch.Generator(device="cpu").manual_seed(seed)
        for name, seed in seeds.items()
    }


def initialize_matched_arms(
    replicate: int,
    *,
    seed_registry: SeedRegistry | Mapping[str, Any] | None = None,
    backend: str = "cpu",
    torch_threads: int = 1,
) -> dict[str, ArmTrainingState]:
    """Create independent arms from one matched initialization."""

    if type(replicate) is not int or replicate < 0:
        raise ValueError("replicate must be a nonnegative integer")
    _require_runtime(backend, torch_threads)
    registry = _canonical_seed_registry(seed_registry)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(registry.model + registry.replicate_offset * replicate)
        common_model = EHCPolicy().to(device="cpu")

    states: dict[str, ArmTrainingState] = {}
    for arm in ARM_NAMES:
        model = deepcopy(common_model)
        base_optimizer, event_optimizer = _make_optimizers(model, arm)
        states[arm] = ArmTrainingState(
            arm=arm,
            replicate=replicate,
            update=0,
            backend=backend,
            torch_threads=torch_threads,
            seed_registry=registry,
            model=model,
            base_optimizer=base_optimizer,
            event_optimizer=event_optimizer,
            generators=_make_generators(registry, replicate),
        )
    return states


def _checkpoint_payload(state: ArmTrainingState) -> dict[str, Any]:
    _require_arm(state.arm)
    _require_runtime(state.backend, state.torch_threads)
    if state.arm == "OR" and state.event_optimizer is not None:
        raise ValueError("OR must not own an event optimizer")
    if state.arm != "OR" and state.event_optimizer is None:
        raise ValueError("DUM/EHC must own an event optimizer")
    _validate_optimizer_exposure(
        state.arm,
        state.update,
        state.base_optimizer_steps,
        state.event_optimizer_steps,
    )
    return {
        "schema": CHECKPOINT_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "backend": state.backend,
        "torch_threads": state.torch_threads,
        "arm": state.arm,
        "replicate": state.replicate,
        "update": state.update,
        "seed_registry": asdict(state.seed_registry),
        "model": state.model.state_dict(),
        "base_optimizer": state.base_optimizer.state_dict(),
        "event_optimizer": (
            None if state.event_optimizer is None else state.event_optimizer.state_dict()
        ),
        "base_optimizer_steps": state.base_optimizer_steps,
        "event_optimizer_steps": state.event_optimizer_steps,
        "owned_rng": {
            name: generator.get_state() for name, generator in state.generators.items()
        },
        "python_rng": random.getstate(),
        "numpy_rng": np.random.get_state(),
        "torch_rng": torch.get_rng_state(),
    }


def save_checkpoint(path: str | os.PathLike[str], state: ArmTrainingState) -> None:
    """Atomically write one completed-boundary independent G1 checkpoint."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    if temporary.exists():
        raise FileExistsError(f"checkpoint temporary path already exists: {temporary}")
    try:
        torch.save(_checkpoint_payload(state), temporary)
        os.replace(temporary, destination)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def load_checkpoint(
    path: str | os.PathLike[str],
    *,
    arm: str,
    replicate: int,
    backend: str,
    torch_threads: int,
) -> ArmTrainingState:
    """Load only the exact G1 arm/backend/thread/replicate continuation."""

    _require_arm(arm)
    _require_runtime(backend, torch_threads)
    payload = torch.load(Path(path), map_location="cpu", weights_only=False)
    if not isinstance(payload, dict):
        raise ValueError("checkpoint payload must be a mapping")
    expected = {
        "schema": CHECKPOINT_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "backend": backend,
        "torch_threads": torch_threads,
        "arm": arm,
        "replicate": replicate,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"checkpoint {key} does not match the requested G1 state")
    required_keys = {
        *expected,
        "update",
        "seed_registry",
        "model",
        "base_optimizer",
        "event_optimizer",
        "base_optimizer_steps",
        "event_optimizer_steps",
        "owned_rng",
        "python_rng",
        "numpy_rng",
        "torch_rng",
    }
    if set(payload) != required_keys:
        raise ValueError("checkpoint has an incomplete or foreign schema")
    update, base_optimizer_steps, event_optimizer_steps = (
        _validate_optimizer_exposure(
            arm,
            payload["update"],
            payload["base_optimizer_steps"],
            payload["event_optimizer_steps"],
        )
    )
    registry = _canonical_seed_registry(payload["seed_registry"])
    state = initialize_matched_arms(
        replicate,
        seed_registry=registry,
        backend=backend,
        torch_threads=torch_threads,
    )[arm]
    state.model.load_state_dict(payload["model"], strict=True)
    state.base_optimizer.load_state_dict(payload["base_optimizer"])
    if state.event_optimizer is None:
        if payload["event_optimizer"] is not None:
            raise ValueError("OR checkpoint must not contain an event optimizer")
    else:
        if payload["event_optimizer"] is None:
            raise ValueError("DUM/EHC checkpoint must contain an event optimizer")
        state.event_optimizer.load_state_dict(payload["event_optimizer"])
    state.update = update
    state.base_optimizer_steps = base_optimizer_steps
    state.event_optimizer_steps = event_optimizer_steps
    owned_rng = payload["owned_rng"]
    if not isinstance(owned_rng, dict) or set(owned_rng) != set(state.generators):
        raise ValueError("checkpoint owned RNG namespaces are incomplete")
    for name, generator in state.generators.items():
        generator.set_state(owned_rng[name])
    random.setstate(payload["python_rng"])
    np.random.set_state(payload["numpy_rng"])
    torch.set_rng_state(payload["torch_rng"])
    return state


def _nonnegative_int(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"checkpoint {name} must be a nonnegative integer")
    return value


def _validate_optimizer_exposure(
    arm: str,
    update: object,
    base_optimizer_steps: object,
    event_optimizer_steps: object,
) -> tuple[int, int, int]:
    normalized_update = _nonnegative_int(update, "update")
    normalized_base = _nonnegative_int(
        base_optimizer_steps, "base_optimizer_steps"
    )
    normalized_event = _nonnegative_int(
        event_optimizer_steps, "event_optimizer_steps"
    )
    expected_base = normalized_update * PPO_PASSES
    expected_event = 0 if arm == "OR" else expected_base
    if normalized_base != expected_base or normalized_event != expected_event:
        raise ValueError(
            "checkpoint optimizer exposure is inconsistent with arm/update"
        )
    return normalized_update, normalized_base, normalized_event


def _sample_indices(
    logits: Tensor,
    *,
    deterministic: bool,
    generator: torch.Generator,
) -> Tensor:
    if logits.ndim != 2 or logits.shape[0] == 0:
        raise ValueError("sample logits must be a nonempty matrix")
    if deterministic:
        return logits.argmax(dim=-1)
    probabilities = torch.softmax(logits, dim=-1)
    return torch.multinomial(probabilities, 1, generator=generator).squeeze(-1)


def collect_rollout(
    state: ArmTrainingState,
    episode_specs: Sequence[G1EpisodeSpec],
    *,
    deterministic: bool = False,
    rng_namespace: str = "train",
) -> RolloutBatch:
    """Collect one complete padded batch from precomputed G1 episode ledgers."""

    _require_runtime(state.backend, state.torch_threads)
    if not isinstance(deterministic, bool):
        raise TypeError("deterministic must be boolean")
    if rng_namespace not in ("train", "evaluation"):
        raise ValueError("rng_namespace must be 'train' or 'evaluation'")
    specs = tuple(episode_specs)
    if not specs:
        raise ValueError("episode_specs must be nonempty")
    if any(not isinstance(spec, G1EpisodeSpec) for spec in specs):
        raise TypeError("every episode spec must be a G1EpisodeSpec")
    if any(spec.source_family != SOURCE_FAMILY for spec in specs):
        raise ValueError("episode spec belongs to a foreign source family")
    horizons = {spec.horizon for spec in specs}
    if len(horizons) != 1:
        raise ValueError("all episode specs in a rollout must share one horizon")
    if any(spec.maximum_capacity != MAXIMUM_CAPACITY for spec in specs):
        raise ValueError("episode spec capacity does not match the G1 model")
    allowed_profiles = {"train"} if rng_namespace == "train" else {"iid", "heldout"}
    if any(spec.profile not in allowed_profiles for spec in specs):
        raise ValueError("episode profile does not match the policy RNG namespace")
    generator_prefix = "" if rng_namespace == "train" else "evaluation_"
    primitive_generator = state.generators[f"{generator_prefix}primitive"]
    event_generator = state.generators[f"{generator_prefix}event"]
    mark_generator = state.generators[f"{generator_prefix}mark"]

    environments = len(specs)
    horizon = horizons.pop()
    member_shape = (environments, horizon, MAXIMUM_CAPACITY)
    actor = torch.zeros(*member_shape, ACTOR_WIDTH)
    critic = torch.zeros(*member_shape, CRITIC_WIDTH)
    active_mask = torch.zeros(member_shape, dtype=torch.bool)
    reset_mask = torch.zeros(member_shape, dtype=torch.bool)
    held_mark_store = torch.zeros(member_shape)
    opportunity_kind = torch.zeros(member_shape, dtype=torch.long)
    actions = torch.full(member_shape, -1, dtype=torch.long)
    events = torch.full(member_shape, -1, dtype=torch.long)
    marks = torch.full(member_shape, -1, dtype=torch.long)
    old_primitive_logp = torch.zeros(member_shape)
    old_event_mark_logp = torch.zeros(member_shape)
    old_values = torch.zeros(environments, horizon)
    rewards = torch.zeros(environments, horizon)
    dones = torch.zeros(environments, horizon, dtype=torch.bool)

    envs = [TemporalDutyG1Env(spec) for spec in specs]
    logical_lifecycles = tuple(
        {
            ledger.physical_slot: ledger.logical_lifecycle
            for ledger in spec.lifecycle_ledgers
        }
        for spec in specs
    )
    hidden = torch.zeros(environments, MAXIMUM_CAPACITY, HIDDEN_WIDTH)
    held_marks = torch.zeros(environments, MAXIMUM_CAPACITY, dtype=torch.long)
    has_mark = torch.zeros(environments, MAXIMUM_CAPACITY, dtype=torch.bool)
    pending_reset = np.zeros((environments, MAXIMUM_CAPACITY), dtype=np.bool_)
    natural_rows: list[dict[str, Any]] = []

    state.model.eval()
    with torch.no_grad():
        for time in range(horizon):
            observations_by_env = [environment.observe() for environment in envs]
            actor_step = np.zeros(
                (environments, MAXIMUM_CAPACITY, ACTOR_WIDTH), dtype=np.float32
            )
            critic_step = np.zeros(
                (environments, MAXIMUM_CAPACITY, CRITIC_WIDTH), dtype=np.float32
            )
            active_step = np.zeros(
                (environments, MAXIMUM_CAPACITY), dtype=np.bool_
            )
            reset_step = np.zeros_like(active_step)
            opportunity_step = np.zeros(
                (environments, MAXIMUM_CAPACITY), dtype=np.int64
            )
            for env_index, observations in enumerate(observations_by_env):
                for slot, observation in observations.items():
                    actor_step[env_index, slot] = observation.actor
                    critic_step[env_index, slot] = observation.critic
                    active_step[env_index, slot] = True
                    if observation.actor[3] == 1.0:
                        pending_reset[env_index, slot] = True
                    reset_step[env_index, slot] = pending_reset[env_index, slot]
                    pending_reset[env_index, slot] = False
                    if state.arm != "OR":
                        if observation.opportunity_kind == "CREATE":
                            opportunity_step[env_index, slot] = 1
                        elif observation.opportunity_kind == "EVENT":
                            opportunity_step[env_index, slot] = 2
            actor[:, time].copy_(torch.from_numpy(actor_step))
            critic[:, time].copy_(torch.from_numpy(critic_step))
            active_mask[:, time].copy_(torch.from_numpy(active_step))
            reset_mask[:, time].copy_(torch.from_numpy(reset_step))
            opportunity_kind[:, time].copy_(torch.from_numpy(opportunity_step))

            reset_now = reset_mask[:, time].unsqueeze(-1)
            hidden = torch.where(reset_now, torch.zeros_like(hidden), hidden)
            flat_actor = actor[:, time].reshape(-1, ACTOR_WIDTH)
            candidate, _ = state.model.actor_step(
                flat_actor, hidden.reshape(-1, HIDDEN_WIDTH)
            )
            candidate = candidate.reshape(
                environments, MAXIMUM_CAPACITY, HIDDEN_WIDTH
            )
            active_now = active_mask[:, time].unsqueeze(-1)
            hidden = torch.where(active_now, candidate, hidden)
            features = torch.where(active_now, candidate, torch.zeros_like(candidate))
            event_logits, mark_logits = state.model.event_mark_logits(features)

            create_mask = opportunity_kind[:, time] == 1
            event_mask = opportunity_kind[:, time] == 2
            held_before = held_marks.clone()
            if create_mask.any():
                selected = _sample_indices(
                    mark_logits[create_mask],
                    deterministic=deterministic,
                    generator=mark_generator,
                )
                marks[:, time][create_mask] = selected
                held_marks[create_mask] = 2 * selected - 1
                has_mark[create_mask] = True
                selected_logp = torch.log_softmax(mark_logits[create_mask], dim=-1).gather(
                    -1, selected.unsqueeze(-1)
                ).squeeze(-1)
                old_event_mark_logp[:, time][create_mask] = selected_logp
            if event_mask.any():
                if torch.any(~has_mark[event_mask]):
                    raise RuntimeError("EVENT opportunity occurred before lifecycle mark creation")
                selected_events = _sample_indices(
                    event_logits[event_mask],
                    deterministic=deterministic,
                    generator=event_generator,
                )
                events[:, time][event_mask] = selected_events
                event_logp = torch.log_softmax(event_logits[event_mask], dim=-1).gather(
                    -1, selected_events.unsqueeze(-1)
                ).squeeze(-1)
                old_event_mark_logp[:, time][event_mask] = event_logp
                renew_mask = event_mask.clone()
                renew_mask[event_mask] = selected_events == 1
                if renew_mask.any():
                    selected_marks = _sample_indices(
                        mark_logits[renew_mask],
                        deterministic=deterministic,
                        generator=mark_generator,
                    )
                    marks[:, time][renew_mask] = selected_marks
                    held_marks[renew_mask] = 2 * selected_marks - 1
                    mark_logp = torch.log_softmax(mark_logits[renew_mask], dim=-1).gather(
                        -1, selected_marks.unsqueeze(-1)
                    ).squeeze(-1)
                    old_event_mark_logp[:, time][renew_mask] += mark_logp

                event_coordinates = event_mask.nonzero(as_tuple=False).tolist()
                selected_events_list = selected_events.tolist()
                for coordinate, selected_event in zip(
                    event_coordinates, selected_events_list, strict=True
                ):
                    env_index, slot = coordinate
                    chosen_mark_index = int(marks[env_index, time, slot])
                    natural_rows.append(
                        {
                            "source_family": SOURCE_FAMILY,
                            "arm": state.arm,
                            "replicate": state.replicate,
                            "update": state.update,
                            "rng_namespace": rng_namespace,
                            "deterministic": deterministic,
                            "profile": specs[env_index].profile,
                            "base_id": specs[env_index].base_id,
                            "sign_mate": specs[env_index].sign_mate,
                            "time": time,
                            "lifecycle": logical_lifecycles[env_index][slot],
                            "physical_slot": slot,
                            "packing_mode": specs[env_index].packing_mode,
                            "event": EVENT_VALUES[selected_event],
                            "held_mark_before": int(held_before[env_index, slot]),
                            "sampled_mark": (
                                None
                                if selected_event == 0
                                else MARK_VALUES[chosen_mark_index]
                            ),
                            "held_mark_after": int(held_marks[env_index, slot]),
                        }
                    )

            held_mark_store[:, time] = torch.where(
                has_mark, held_marks, torch.zeros_like(held_marks)
            )
            primitive_logits = state.model.primitive_head(features)
            if state.arm == "EHC":
                primitive_logits = primitive_logits + (
                    held_mark_store[:, time].unsqueeze(-1)
                    * state.model.mark_treatment
                )
            flat_active = active_mask[:, time]
            selected_actions = _sample_indices(
                primitive_logits[flat_active],
                deterministic=deterministic,
                generator=primitive_generator,
            )
            actions[:, time][flat_active] = selected_actions
            selected_action_logp = torch.log_softmax(
                primitive_logits[flat_active], dim=-1
            ).gather(-1, selected_actions.unsqueeze(-1)).squeeze(-1)
            old_primitive_logp[:, time][flat_active] = selected_action_logp
            action_values = [
                ACTION_VALUES[index] for index in selected_actions.tolist()
            ]
            action_cursor = 0
            for env_index, environment in enumerate(envs):
                active_slots = active_mask[env_index, time].nonzero(
                    as_tuple=False
                ).squeeze(-1).tolist()
                count = len(active_slots)
                step_actions = dict(
                    zip(
                        active_slots,
                        action_values[action_cursor : action_cursor + count],
                        strict=True,
                    )
                )
                action_cursor += count
                transition = environment.step(step_actions)
                rewards[env_index, time] = float(transition["reward"])
                dones[env_index, time] = bool(transition["done"])
                for segment_event in transition["segment_events"]:
                    slot = int(segment_event["slot"])
                    status = segment_event["status"]
                    if status == "COMPLETED":
                        hidden[env_index, slot].zero_()
                        pending_reset[env_index, slot] = True
                    elif status == "CENSORED_TERMINAL":
                        hidden[env_index, slot].zero_()
                        held_marks[env_index, slot] = 0
                        has_mark[env_index, slot] = False
                        pending_reset[env_index, slot] = False
            if action_cursor != len(action_values):
                raise RuntimeError("batched primitive action packing lost a lifecycle row")

    if not torch.all(dones[:, -1]) or torch.any(dones[:, :-1]):
        raise RuntimeError("episode ledger did not terminate at its declared horizon")
    with torch.no_grad():
        old_values.copy_(
            state.model.value(
                critic.reshape(
                    environments * horizon, MAXIMUM_CAPACITY, CRITIC_WIDTH
                ),
                active_mask.reshape(environments * horizon, MAXIMUM_CAPACITY),
            ).reshape(environments, horizon)
        )
    advantages, returns = compute_gae(rewards, old_values, dones)
    outcomes = tuple(environment.outcome() for environment in envs)
    natural_rows.sort(
        key=lambda row: (
            row["base_id"],
            row["sign_mate"],
            row["time"],
            row["lifecycle"],
        )
    )
    provenance = tuple(
        {
            "env_index": env_index,
            "arm": state.arm,
            "replicate": state.replicate,
            "update": state.update,
            "rng_namespace": rng_namespace,
            "deterministic": deterministic,
            "profile": spec.profile,
            "base_id": spec.base_id,
            "sign_mate": spec.sign_mate,
            "packing_mode": spec.packing_mode,
        }
        for env_index, spec in enumerate(specs)
    )
    natural_keep = sum(row["event"] == "KEEP" for row in natural_rows)
    natural_renew = len(natural_rows) - natural_keep
    exposure = {
        "active_member_actions": int(active_mask.sum()),
        "create_opportunities": int((opportunity_kind == 1).sum()),
        "event_opportunities": int((opportunity_kind == 2).sum()),
        "natural_keep": natural_keep,
        "natural_renew": natural_renew,
    }
    batch = RolloutBatch(
        source_family=SOURCE_FAMILY,
        arm=state.arm,
        replicate=state.replicate,
        actor=actor,
        critic=critic,
        active_mask=active_mask,
        reset_mask=reset_mask,
        held_mark=held_mark_store,
        opportunity_kind=opportunity_kind,
        actions=actions,
        events=events,
        marks=marks,
        old_primitive_logp=old_primitive_logp,
        old_event_mark_logp=old_event_mark_logp,
        old_values=old_values,
        rewards=rewards,
        dones=dones,
        advantages=advantages,
        returns=returns,
        natural_rows=tuple(natural_rows),
        outcomes=outcomes,
        provenance=provenance,
        exposure=exposure,
    )
    validate_replay(state, batch)
    return batch


def _validate_batch(state: ArmTrainingState, batch: RolloutBatch) -> tuple[int, int, int]:
    if batch.source_family != SOURCE_FAMILY:
        raise ValueError("rollout is not from the independent G1 source")
    if batch.arm != state.arm or batch.replicate != state.replicate:
        raise ValueError("rollout arm/replicate does not match training state")
    if batch.actor.ndim != 4 or batch.actor.shape[-1] != ACTOR_WIDTH:
        raise ValueError("actor rollout must have shape [env,time,capacity,6]")
    environments, horizon, capacity, _ = batch.actor.shape
    if capacity != MAXIMUM_CAPACITY:
        raise ValueError("rollout capacity must be exactly four")
    if batch.critic.shape != (environments, horizon, capacity, CRITIC_WIDTH):
        raise ValueError("critic rollout must have shape [env,time,capacity,10]")
    member_shape = (environments, horizon, capacity)
    step_shape = (environments, horizon)
    member_fields = {
        "active_mask": batch.active_mask,
        "reset_mask": batch.reset_mask,
        "held_mark": batch.held_mark,
        "opportunity_kind": batch.opportunity_kind,
        "actions": batch.actions,
        "events": batch.events,
        "marks": batch.marks,
        "old_primitive_logp": batch.old_primitive_logp,
        "old_event_mark_logp": batch.old_event_mark_logp,
    }
    for name, tensor in member_fields.items():
        if tensor.shape != member_shape:
            raise ValueError(f"{name} must have shape [env,time,capacity]")
    step_fields = {
        "old_values": batch.old_values,
        "rewards": batch.rewards,
        "dones": batch.dones,
        "advantages": batch.advantages,
        "returns": batch.returns,
    }
    for name, tensor in step_fields.items():
        if tensor.shape != step_shape:
            raise ValueError(f"{name} must have shape [env,time]")
    if batch.active_mask.dtype != torch.bool or batch.reset_mask.dtype != torch.bool:
        raise ValueError("active and reset masks must be boolean")
    if batch.dones.dtype != torch.bool:
        raise ValueError("done mask must be boolean")
    if torch.any(batch.reset_mask & ~batch.active_mask):
        raise ValueError("only active lifecycle rows may reset recurrence")
    if torch.any((batch.actions < 0) & batch.active_mask) or torch.any(
        (batch.actions >= len(ACTION_VALUES)) & batch.active_mask
    ):
        raise ValueError("stored primitive action is outside support")
    if torch.any((batch.opportunity_kind < 0) | (batch.opportunity_kind > 2)):
        raise ValueError("stored opportunity kind is outside support")
    if torch.any((batch.opportunity_kind != 0) & ~batch.active_mask):
        raise ValueError("inactive lifecycle row cannot carry an opportunity")
    if state.arm == "OR" and torch.any(batch.opportunity_kind != 0):
        raise ValueError("OR rollout must hard-mask the event path")
    event_mask = batch.opportunity_kind == 2
    if torch.any((batch.events < 0) & event_mask) or torch.any(
        (batch.events >= len(EVENT_VALUES)) & event_mask
    ):
        raise ValueError("stored event is outside support")
    mark_mask = (batch.opportunity_kind == 1) | (event_mask & (batch.events == 1))
    if torch.any((batch.marks < 0) & mark_mask) or torch.any(
        (batch.marks >= len(MARK_VALUES)) & mark_mask
    ):
        raise ValueError("stored mark is outside support")
    if torch.any(batch.events[~event_mask] != -1):
        raise ValueError("only EVENT opportunities may store an event")
    if torch.any(batch.marks[~mark_mask] != -1):
        raise ValueError("only CREATE/RENEW rows may store a sampled mark")
    if torch.any(batch.actions[~batch.active_mask] != -1):
        raise ValueError("inactive lifecycle rows cannot store primitive actions")
    if torch.any(
        batch.active_mask
        & ~((batch.held_mark == -1) | (batch.held_mark == 0) | (batch.held_mark == 1))
    ):
        raise ValueError("held mark must be -1, 0, or +1")
    if state.arm == "OR":
        if torch.any(batch.held_mark != 0):
            raise ValueError("OR rollout cannot carry a held mark")
    elif torch.any(batch.active_mask & (batch.held_mark == 0)):
        raise ValueError("DUM/EHC active rows must carry a created mark")
    if torch.any(batch.old_primitive_logp[~batch.active_mask] != 0):
        raise ValueError("inactive primitive likelihood padding must be zero")
    if torch.any(batch.old_event_mark_logp[batch.opportunity_kind == 0] != 0):
        raise ValueError("masked event likelihood padding must be zero")
    floating = (
        batch.actor,
        batch.critic,
        batch.held_mark,
        batch.old_primitive_logp,
        batch.old_event_mark_logp,
        batch.old_values,
        batch.rewards,
        batch.advantages,
        batch.returns,
    )
    if not all(torch.isfinite(tensor).all() for tensor in floating):
        raise ValueError("rollout contains a non-finite value")
    if not torch.all(batch.dones[:, -1]) or torch.any(batch.dones[:, :-1]):
        raise ValueError("optimization requires complete rollouts")
    return environments, horizon, capacity


def _actor_features(model: EHCPolicy, batch: RolloutBatch) -> Tensor:
    environments, horizon, capacity, _ = batch.actor.shape
    hidden = torch.zeros(
        environments,
        capacity,
        HIDDEN_WIDTH,
        dtype=batch.actor.dtype,
        device=batch.actor.device,
    )
    features_by_time: list[Tensor] = []
    for time in range(horizon):
        reset = batch.reset_mask[:, time].unsqueeze(-1)
        hidden = torch.where(reset, torch.zeros_like(hidden), hidden)
        actor = batch.actor[:, time].reshape(-1, ACTOR_WIDTH)
        candidate, _ = model.actor_step(actor, hidden.reshape(-1, HIDDEN_WIDTH))
        candidate = candidate.reshape(environments, capacity, HIDDEN_WIDTH)
        active = batch.active_mask[:, time].unsqueeze(-1)
        hidden = torch.where(active, candidate, hidden)
        features_by_time.append(torch.where(active, candidate, torch.zeros_like(candidate)))
    return torch.stack(features_by_time, dim=1)


def replay_rollout(state: ArmTrainingState, batch: RolloutBatch) -> ReplayResult:
    """Recompute stored likelihoods without consuming any RNG."""

    environments, horizon, capacity = _validate_batch(state, batch)
    features = _actor_features(state.model, batch)
    primitive_logits = state.model.primitive_head(features)
    if state.arm == "EHC":
        primitive_logits = primitive_logits + (
            batch.held_mark.unsqueeze(-1) * state.model.mark_treatment
        )
    event_logits, mark_logits = state.model.event_mark_logits(features)
    primitive_log_probs = torch.log_softmax(primitive_logits, dim=-1)
    primitive_logp = primitive_log_probs.gather(
        -1, batch.actions.clamp(0, len(ACTION_VALUES) - 1).unsqueeze(-1)
    ).squeeze(-1)
    primitive_logp = torch.where(
        batch.active_mask, primitive_logp, torch.zeros_like(primitive_logp)
    )

    event_mask = batch.opportunity_kind == 2
    event_log_probs = torch.log_softmax(event_logits, dim=-1)
    selected_event_logp = event_log_probs.gather(
        -1, batch.events.clamp(0, len(EVENT_VALUES) - 1).unsqueeze(-1)
    ).squeeze(-1)
    mark_mask = (batch.opportunity_kind == 1) | (event_mask & (batch.events == 1))
    mark_log_probs = torch.log_softmax(mark_logits, dim=-1)
    selected_mark_logp = mark_log_probs.gather(
        -1, batch.marks.clamp(0, len(MARK_VALUES) - 1).unsqueeze(-1)
    ).squeeze(-1)
    event_mark_logp = torch.where(
        event_mask, selected_event_logp, torch.zeros_like(selected_event_logp)
    ) + torch.where(mark_mask, selected_mark_logp, torch.zeros_like(selected_mark_logp))

    values = state.model.value(
        batch.critic.reshape(environments * horizon, capacity, CRITIC_WIDTH),
        batch.active_mask.reshape(environments * horizon, capacity),
    ).reshape(environments, horizon)
    primitive_entropy = -(
        primitive_log_probs.exp() * primitive_log_probs
    ).sum(dim=-1)
    primitive_entropy = torch.where(
        batch.active_mask, primitive_entropy, torch.zeros_like(primitive_entropy)
    )
    event_entropy = -(
        event_log_probs.exp() * event_log_probs
    ).sum(dim=-1)
    mark_entropy = -(mark_log_probs.exp() * mark_log_probs).sum(dim=-1)
    event_entropy = torch.where(
        event_mask, event_entropy, torch.zeros_like(event_entropy)
    ) + torch.where(mark_mask, mark_entropy, torch.zeros_like(mark_entropy))
    return ReplayResult(
        primitive_logits=primitive_logits,
        event_logits=event_logits,
        mark_logits=mark_logits,
        primitive_logp=primitive_logp,
        event_mark_logp=event_mark_logp,
        values=values,
        primitive_entropy=primitive_entropy,
        event_entropy=event_entropy,
    )


def validate_replay(
    state: ArmTrainingState,
    batch: RolloutBatch,
    *,
    atol: float = 1e-7,
) -> dict[str, float]:
    """Fail closed when stored stochastic likelihood/value provenance changed."""

    if not isinstance(atol, float) or not np.isfinite(atol) or atol < 0.0:
        raise ValueError("atol must be a finite nonnegative float")
    before = {
        name: generator.get_state().clone()
        for name, generator in state.generators.items()
    }
    with torch.no_grad():
        replay = replay_rollout(state, batch)
    for name, generator in state.generators.items():
        if not torch.equal(before[name], generator.get_state()):
            raise RuntimeError("replay consumed owned RNG")
    active = batch.active_mask
    event = batch.opportunity_kind != 0
    primitive_error = _masked_max_error(
        replay.primitive_logp, batch.old_primitive_logp, active
    )
    event_error = _masked_max_error(
        replay.event_mark_logp, batch.old_event_mark_logp, event
    )
    value_error = float((replay.values - batch.old_values).abs().max().item())
    if max(primitive_error, event_error, value_error) > atol:
        raise ValueError("stored rollout likelihood/value replay mismatch")
    return {
        "primitive_error": primitive_error,
        "event_error": event_error,
        "value_error": value_error,
    }


def _masked_max_error(actual: Tensor, expected: Tensor, mask: Tensor) -> float:
    selected = (actual - expected).abs()[mask]
    return 0.0 if selected.numel() == 0 else float(selected.max().item())


def compute_gae(rewards: Tensor, values: Tensor, dones: Tensor) -> tuple[Tensor, Tensor]:
    if rewards.ndim != 2 or values.shape != rewards.shape or dones.shape != rewards.shape:
        raise ValueError("rewards, values, and dones must share [env,time] shape")
    if dones.dtype != torch.bool:
        raise ValueError("dones must be boolean")
    advantages = torch.zeros_like(rewards)
    next_advantage = torch.zeros_like(rewards[:, 0])
    next_value = torch.zeros_like(values[:, 0])
    for time in range(rewards.shape[1] - 1, -1, -1):
        continuation = (~dones[:, time]).to(rewards.dtype)
        delta = rewards[:, time] + GAMMA * next_value * continuation - values[:, time]
        next_advantage = delta + GAMMA * GAE_LAMBDA * continuation * next_advantage
        advantages[:, time] = next_advantage
        next_value = values[:, time]
    return advantages, advantages + values


def optimize_rollout(
    state: ArmTrainingState,
    batch: RolloutBatch,
    *,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, float | int]:
    """Take four full-rollout base passes and matched DUM/EHC event passes."""

    if type(ppo_passes) is not int or ppo_passes != PPO_PASSES:
        raise ValueError(f"the frozen G1 contract requires exactly {PPO_PASSES} PPO passes")
    validate_replay(state, batch)
    advantages = batch.advantages
    normalized_advantages = (advantages - advantages.mean()) / (
        advantages.std(unbiased=False) + 1e-8
    )
    active_counts = batch.active_mask.sum(dim=-1).clamp_min(1)
    event_step_mask = (batch.opportunity_kind != 0).any(dim=-1)
    last_base_loss = 0.0
    last_event_loss = 0.0
    for _ in range(ppo_passes):
        state.base_optimizer.zero_grad(set_to_none=True)
        replay = replay_rollout(state, batch)
        primitive_joint_delta = (
            (replay.primitive_logp - batch.old_primitive_logp) * batch.active_mask
        ).sum(dim=-1)
        primitive_ratio = primitive_joint_delta.clamp(-20.0, 20.0).exp()
        unclipped = primitive_ratio * normalized_advantages
        clipped = primitive_ratio.clamp(1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * normalized_advantages
        policy_loss = -torch.minimum(unclipped, clipped).mean()
        value_delta = (replay.values - batch.old_values).clamp(-VALUE_CLIP, VALUE_CLIP)
        clipped_values = batch.old_values + value_delta
        value_loss = 0.5 * torch.maximum(
            (replay.values - batch.returns).square(),
            (clipped_values - batch.returns).square(),
        ).mean()
        primitive_entropy = (
            replay.primitive_entropy.sum(dim=-1) / active_counts
        ).mean()
        base_loss = (
            policy_loss
            + VALUE_COEFFICIENT * value_loss
            - PRIMITIVE_ENTROPY_COEFFICIENT * primitive_entropy
        )
        if not torch.isfinite(base_loss):
            raise FloatingPointError("non-finite base PPO loss")
        base_loss.backward()
        base_parameters = [
            parameter
            for group in state.base_optimizer.param_groups
            for parameter in group["params"]
        ]
        gradient_norm = nn.utils.clip_grad_norm_(base_parameters, GRADIENT_CLIP)
        if not torch.isfinite(gradient_norm):
            raise FloatingPointError("non-finite base PPO gradient")
        state.base_optimizer.step()
        state.base_optimizer_steps += 1
        last_base_loss = float(base_loss.detach().item())

        if state.event_optimizer is not None:
            state.base_optimizer.zero_grad(set_to_none=True)
            state.event_optimizer.zero_grad(set_to_none=True)
            replay = replay_rollout(state, batch)
            event_joint_delta = (
                (replay.event_mark_logp - batch.old_event_mark_logp)
                * (batch.opportunity_kind != 0)
            ).sum(dim=-1)
            event_ratio = event_joint_delta.clamp(-20.0, 20.0).exp()
            event_unclipped = event_ratio * normalized_advantages
            event_clipped = event_ratio.clamp(
                1.0 - PPO_CLIP, 1.0 + PPO_CLIP
            ) * normalized_advantages
            selected_policy_loss = -torch.minimum(
                event_unclipped, event_clipped
            )[event_step_mask]
            if selected_policy_loss.numel() == 0:
                raise ValueError("DUM/EHC rollout has no event or mark exposure")
            event_count = (batch.opportunity_kind != 0).sum(dim=-1).clamp_min(1)
            event_entropy = (
                replay.event_entropy.sum(dim=-1) / event_count
            )[event_step_mask].mean()
            event_loss = selected_policy_loss.mean() - EVENT_ENTROPY_COEFFICIENT * event_entropy
            if not torch.isfinite(event_loss):
                raise FloatingPointError("non-finite event PPO loss")
            event_loss.backward()
            event_parameters = [
                parameter
                for group in state.event_optimizer.param_groups
                for parameter in group["params"]
            ]
            event_gradient_norm = nn.utils.clip_grad_norm_(
                event_parameters, GRADIENT_CLIP
            )
            if not torch.isfinite(event_gradient_norm):
                raise FloatingPointError("non-finite event PPO gradient")
            if any(parameter.grad is not None for parameter in base_parameters):
                raise RuntimeError("event loss crossed the detached base boundary")
            state.event_optimizer.step()
            state.event_optimizer_steps += 1
            last_event_loss = float(event_loss.detach().item())
    state.update += 1
    return {
        "update": state.update,
        "base_optimizer_steps": state.base_optimizer_steps,
        "event_optimizer_steps": state.event_optimizer_steps,
        "base_loss": last_base_loss,
        "event_loss": last_event_loss,
    }
