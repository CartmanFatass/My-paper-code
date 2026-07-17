"""Variable-roster event runtime shared by the F0 and F1 architectures.

This module is deliberately environment-free.  It owns policy lifecycle state,
active-only packing, the exogenous opportunity clocks, exact event ledgers and
strict schema-3 checkpoint payloads.  The first production boundary is the
deterministic transaction trace in
``tests/ha_ctse_process_variable_roster_event_test.py``; this module does not
construct an environment or start training.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import math
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

from hmasd.r_mappo_utils import ACTLayer, MLPBase, RNNLayer, check


CHECKPOINT_SCHEMA_VERSION = 3
EVENT_ARCHITECTURE_SCHEMA_VERSION = 1
EVENT_CONTROLLER = "variable_roster_event"
EVENT_MODES = ("f0", "f1")
OPPORTUNITY_SCHEDULE_NAME = "uniform_active_gap_v1"
OPPORTUNITY_K0 = 10
OPPORTUNITY_GAP_LOW = 1
OPPORTUNITY_GAP_HIGH = 19
AGE_REFERENCE_STEPS = 500
SNAPSHOT_CAPABILITY_NAME = "variable_roster_event_snapshot"
SNAPSHOT_CAPABILITY_VERSION = 1
VECTOR_CHECKPOINT_SCHEMA_VERSION = 1
VECTOR_RUNTIME_FIELDS = {
    "environment_index",
    "rng_ledger",
    "lifecycle_table_schema",
    "lifecycle_records",
    "opportunity_rng_state",
    "frontier_order_rng_state",
    "policy_action_rng_state",
    "open_event_trace_schema",
    "high_ledger",
    "closed_event_rows",
    "low_ledger",
    "low_chunk_boundaries",
    "policy_version",
    "physical_time",
    "current_observation_state_boundary",
    "pending_membership_transaction",
}
PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.50
MAX_RECURRENT_CHUNK = 20

ACTIVE = "ACTIVE"
TEMPORARILY_ABSENT = "TEMPORARILY_ABSENT"
TERMINAL = "TERMINAL"

JOIN = "JOIN"
TEMPORARY_LEAVE = "TEMPORARY_LEAVE"
TERMINAL_LEAVE = "TERMINAL_LEAVE"
REJOIN = "REJOIN"
MEMBERSHIP_KINDS = (JOIN, TEMPORARY_LEAVE, TERMINAL_LEAVE, REJOIN)

ORDINARY_BOUNDARY = "ordinary_opportunity"
ROLLOUT_TRUNCATION = "rollout_truncation"
TEMPORARY_BOUNDARY = "temporary_pre_removal_leave"
TERMINAL_BOUNDARY = "terminal_boundary"
BOUNDARY_KINDS = (
    ORDINARY_BOUNDARY,
    ROLLOUT_TRUNCATION,
    TEMPORARY_BOUNDARY,
    TERMINAL_BOUNDARY,
)


def _float_array(value: Any, *, size: int, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float32).reshape(-1)
    if tuple(array.shape) != (int(size),):
        raise ValueError(f"{name} must have shape [{size}]")
    if not bool(np.all(np.isfinite(array))):
        raise ValueError(f"{name} contains a non-finite value")
    return array.copy()


def _state_dict_shapes(module: nn.Module) -> dict[str, tuple[int, ...]]:
    return {name: tuple(tensor.shape) for name, tensor in module.state_dict().items()}


def parameter_count(module: nn.Module) -> int:
    return int(sum(parameter.numel() for parameter in module.parameters()))


def normalized_log_age(ages: torch.Tensor) -> torch.Tensor:
    return torch.log1p(torch.clamp(ages.float(), min=0.0)) / math.log1p(
        float(AGE_REFERENCE_STEPS)
    )


def make_pcg64_rng(master_seed: int, episode_id: int, stream_id: int) -> np.random.Generator:
    """Construct one frozen ledger stream without folding or secondary seeding."""

    return np.random.Generator(
        np.random.PCG64(
            np.random.SeedSequence(
                [int(master_seed), int(episode_id), int(stream_id)]
            )
        )
    )


def inverse_cdf_action(probabilities: np.ndarray, uniform: float) -> int:
    values = np.asarray(probabilities, dtype=np.float64).reshape(-1)
    if values.size <= 0 or not np.isfinite(values).all() or np.any(values < 0.0):
        raise ValueError("categorical probabilities are invalid")
    total = float(values.sum())
    if not np.isfinite(total) or total <= 0.0:
        raise ValueError("categorical probability mass must be positive")
    normalized = values / total
    draw = float(uniform)
    if not 0.0 <= draw < 1.0:
        raise ValueError("inverse-CDF uniform must lie in [0,1)")
    return min(int(np.searchsorted(np.cumsum(normalized), draw, side="right")), values.size - 1)


@dataclass(frozen=True)
class BoundaryMember:
    """One physical member row carried by a typed boundary transaction.

    ``lifecycle_key`` and ``membership_epoch`` are routing-only.  The model
    receives only the observation and critic feature arrays.
    """

    lifecycle_key: str
    membership_epoch: int
    observation: np.ndarray
    critic_member_features: np.ndarray

    @classmethod
    def make(
        cls,
        lifecycle_key: str,
        membership_epoch: int,
        observation: Any,
        critic_member_features: Any,
        *,
        obs_dim: int,
        critic_member_dim: int,
    ) -> "BoundaryMember":
        key = str(lifecycle_key)
        if not key:
            raise ValueError("lifecycle_key must be non-empty")
        return cls(
            lifecycle_key=key,
            membership_epoch=int(membership_epoch),
            observation=_float_array(observation, size=obs_dim, name="observation"),
            critic_member_features=_float_array(
                critic_member_features,
                size=critic_member_dim,
                name="critic_member_features",
            ),
        )


@dataclass(frozen=True)
class BoundarySnapshot:
    physical_time: int
    members: tuple[BoundaryMember, ...]
    critic_global_features: np.ndarray
    frontier: tuple[str, ...] = ()

    @classmethod
    def make(
        cls,
        physical_time: int,
        members: Sequence[BoundaryMember],
        critic_global_features: Any,
        *,
        critic_global_dim: int,
        frontier: Sequence[str] = (),
    ) -> "BoundarySnapshot":
        rows = tuple(members)
        keys = tuple(row.lifecycle_key for row in rows)
        if len(keys) != len(set(keys)):
            raise ValueError("boundary snapshot contains duplicate lifecycle keys")
        frontier_keys = tuple(str(key) for key in frontier)
        if len(frontier_keys) != len(set(frontier_keys)):
            raise ValueError("boundary frontier contains duplicate lifecycle keys")
        if not set(frontier_keys).issubset(set(keys)):
            raise ValueError("boundary frontier contains an inactive lifecycle")
        return cls(
            physical_time=int(physical_time),
            members=rows,
            critic_global_features=_float_array(
                critic_global_features,
                size=critic_global_dim,
                name="critic_global_features",
            ),
            frontier=frontier_keys,
        )

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(member.lifecycle_key for member in self.members)


@dataclass(frozen=True)
class MembershipDelta:
    kind: str
    lifecycle_key: str
    expected_membership_epoch: int

    def __post_init__(self) -> None:
        if str(self.kind) not in MEMBERSHIP_KINDS:
            raise ValueError(f"unsupported membership delta kind {self.kind!r}")
        if not str(self.lifecycle_key):
            raise ValueError("membership delta lifecycle key must be non-empty")


@dataclass(frozen=True)
class MembershipTransaction:
    pre_membership_boundary_snapshot: BoundarySnapshot
    atomic_membership_delta: tuple[MembershipDelta, ...]
    post_membership_pre_policy_snapshot: BoundarySnapshot

    def __post_init__(self) -> None:
        deltas = tuple(self.atomic_membership_delta)
        keys = tuple(delta.lifecycle_key for delta in deltas)
        if len(keys) != len(set(keys)):
            raise ValueError("one transaction cannot mutate a lifecycle twice")
        if (
            int(self.pre_membership_boundary_snapshot.physical_time)
            != int(self.post_membership_pre_policy_snapshot.physical_time)
        ):
            raise ValueError("transaction snapshots must share physical time")


@dataclass
class OpenEventTrace:
    start_time: int
    policy_version: int
    actor_valid: bool
    old_value: float
    old_log_probability: float | None
    token_ledger_index: int | None
    discounted_reward: float = 0.0
    elapsed_physical_time: int = 0

    def accumulate(self, reward: float, gamma: float) -> None:
        self.discounted_reward += (float(gamma) ** self.elapsed_physical_time) * float(
            reward
        )
        self.elapsed_physical_time += 1


@dataclass
class LifecycleRecord:
    lifecycle_key: str
    status: str
    membership_epoch: int
    low_actor_hidden: np.ndarray
    low_critic_hidden: np.ndarray
    high_hidden: np.ndarray
    active_skill: int | None
    skill_active_age: int
    active_gap_remaining: int | None
    last_policy_event_time: int | None
    open_event_trace: OpenEventTrace | None
    policy_version: int
    is_genuine_join: bool = False
    is_rejoin: bool = False

    def clone(self) -> "LifecycleRecord":
        return deepcopy(self)


@dataclass(frozen=True)
class ClosedEventRow:
    lifecycle_key: str
    membership_epoch: int
    policy_version: int
    actor_valid: bool
    start_time: int
    end_time: int
    elapsed_physical_time: int
    discounted_reward: float
    old_value: float
    bootstrap_value: float
    bootstrap_discount: float
    return_target: float
    old_log_probability: float | None
    token_ledger_index: int | None
    boundary_kind: str


@dataclass(frozen=True)
class EventTokenRow:
    environment_index: int
    policy_version: int
    physical_event_time: int
    owner_lifecycle_key: str
    membership_epoch: int
    frontier: tuple[str, ...]
    sampled_order: tuple[str, ...]
    order_log_probability: float
    token_position: int
    sampled_replacement_gap: int
    active_lifecycle_keys: tuple[str, ...]
    active_membership_epochs: tuple[int, ...]
    active_observations: np.ndarray
    active_critic_member_features: np.ndarray
    critic_global_features: np.ndarray
    event_flags: np.ndarray
    initial_skills: np.ndarray
    initial_ages: np.ndarray
    pre_token_working_skills: np.ndarray
    pre_token_working_ages: np.ndarray
    post_token_working_skills: np.ndarray
    post_token_working_ages: np.ndarray
    active_high_hidden: np.ndarray
    pre_token_high_hidden: np.ndarray
    exact_legal_mask: np.ndarray
    policy_action_uniform: float | None
    combined_action: int
    old_token_log_probability: float
    old_owner_value: float
    action_kind: str


@dataclass
class LowTransitionRow:
    lifecycle_key: str
    membership_epoch: int
    policy_version: int
    physical_time: int
    observation: np.ndarray
    skill: int
    action: np.ndarray
    old_log_probability: float
    old_value: float
    actor_hidden_before: np.ndarray
    critic_hidden_before: np.ndarray
    critic_member_features: np.ndarray
    active_critic_member_features: np.ndarray
    active_skills: np.ndarray
    critic_global_features: np.ndarray
    focal_active_index: int
    critic_source_summary: np.ndarray
    policy_action_uniform: float | None = None
    reward: float | None = None
    terminal_or_truncation_kind: str | None = None
    environment_step_pointer: int = 0
    lifecycle_chunk_pointer: int = 0
    bootstrap_source: str | None = None
    bootstrap_value: float | None = None


@dataclass(frozen=True)
class PackedActiveBatch:
    """Model-facing active-only tensors.  Routing metadata is excluded."""

    env_ptr: torch.Tensor
    member_obs: torch.Tensor
    critic_member_features: torch.Tensor
    critic_global_features: torch.Tensor
    skills: torch.Tensor
    active_ages: torch.Tensor
    event_flags: torch.Tensor
    low_actor_hidden: torch.Tensor
    low_critic_hidden: torch.Tensor
    high_hidden: torch.Tensor


@dataclass(frozen=True)
class ActiveRoutingView:
    lifecycle_keys: tuple[str, ...]
    membership_epochs: tuple[int, ...]


@dataclass(frozen=True)
class EventTransactionResult:
    sampled_order: tuple[str, ...]
    order_log_probability: float
    token_rows: tuple[EventTokenRow, ...]
    final_skills: dict[str, int]


@dataclass(frozen=True)
class EventPPOLosses:
    high_loss: torch.Tensor
    low_loss: torch.Tensor
    high_policy_loss: torch.Tensor
    high_value_loss: torch.Tensor
    low_policy_loss: torch.Tensor
    low_value_loss: torch.Tensor
    high_entropy: torch.Tensor
    low_entropy: torch.Tensor
    high_rows: int
    low_rows: int
    high_logp_max_error: float
    high_value_max_error: float
    low_logp_max_error: float
    low_value_max_error: float


class EventCommitmentPolicy(nn.Module):
    """One parameter graph used by both F0 and F1."""

    def __init__(
        self,
        *,
        obs_dim: int,
        n_skills: int,
        member_hidden_dim: int,
        high_hidden_dim: int,
        skill_embedding_dim: int,
    ) -> None:
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.n_skills = int(n_skills)
        self.member_hidden_dim = int(member_hidden_dim)
        self.high_hidden_dim = int(high_hidden_dim)
        self.skill_embedding_dim = int(skill_embedding_dim)
        self.summary_dim = self.member_hidden_dim + 1

        self.skill_embedding = nn.Embedding(self.n_skills, self.skill_embedding_dim)
        member_input_dim = self.obs_dim + self.skill_embedding_dim + 3
        self.member_encoder = nn.Sequential(
            nn.LayerNorm(member_input_dim),
            nn.Linear(member_input_dim, self.member_hidden_dim),
            nn.GELU(),
            nn.Linear(self.member_hidden_dim, self.member_hidden_dim),
            nn.GELU(),
        )
        self.high_rnn = nn.GRUCell(
            self.member_hidden_dim + self.summary_dim,
            self.high_hidden_dim,
        )
        self.decoder_hidden = nn.Sequential(
            nn.Linear(self.high_hidden_dim + self.summary_dim, self.member_hidden_dim),
            nn.GELU(),
        )
        self.skill_head = nn.Linear(self.member_hidden_dim, self.n_skills)

    def encode_members(
        self,
        observations: torch.Tensor,
        skills: torch.Tensor,
        ages: torch.Tensor,
        event_flags: torch.Tensor,
    ) -> torch.Tensor:
        observations = observations.float()
        skills = skills.long().reshape(-1)
        ages = ages.float().reshape(-1)
        event_flags = event_flags.bool().reshape(-1, 2)
        if observations.ndim != 2 or observations.shape[1] != self.obs_dim:
            raise ValueError("active observations have the wrong shape")
        if observations.shape[0] != skills.shape[0]:
            raise ValueError("active observation/skill row mismatch")
        genuine_join = event_flags[:, 0]
        undefined = skills < 0
        if bool(torch.any(undefined & ~genuine_join).item()):
            raise ValueError("only a genuine join may have an undefined skill")
        safe_skills = skills.clamp(0, self.n_skills - 1)
        skill_features = self.skill_embedding(safe_skills)
        skill_features = torch.where(
            undefined.unsqueeze(-1),
            torch.zeros_like(skill_features),
            skill_features,
        )
        member_input = torch.cat(
            (
                observations,
                skill_features,
                normalized_log_age(ages).unsqueeze(-1),
                event_flags.to(dtype=torch.float32),
            ),
            dim=-1,
        )
        return self.member_encoder(member_input)

    @staticmethod
    def set_summary(member_embeddings: torch.Tensor) -> torch.Tensor:
        if member_embeddings.ndim != 2 or member_embeddings.shape[0] <= 0:
            raise ValueError("set summary requires at least one active member")
        log_count = torch.log1p(
            torch.tensor(
                float(member_embeddings.shape[0]),
                dtype=member_embeddings.dtype,
                device=member_embeddings.device,
            )
        ).reshape(1)
        return torch.cat((member_embeddings.sum(dim=0), log_count), dim=0)

    def logits(
        self,
        member_embedding: torch.Tensor,
        selected_summary: torch.Tensor,
        pre_hidden: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        member_embedding = member_embedding.reshape(1, self.member_hidden_dim)
        selected_summary = selected_summary.reshape(1, self.summary_dim)
        pre_hidden = pre_hidden.reshape(1, self.high_hidden_dim)
        new_hidden = self.high_rnn(
            torch.cat((member_embedding, selected_summary), dim=-1),
            pre_hidden,
        )
        hidden = self.decoder_hidden(torch.cat((new_hidden, selected_summary), dim=-1))
        return self.skill_head(hidden).squeeze(0), new_hidden.squeeze(0)

    def zero_summary_path(self) -> None:
        """Create the registered action-independent reduction control."""

        with torch.no_grad():
            self.high_rnn.weight_ih[:, self.member_hidden_dim :] = 0.0
            first = self.decoder_hidden[0]
            first.weight[:, self.high_hidden_dim :] = 0.0


class EventHighCritic(nn.Module):
    def __init__(
        self,
        *,
        critic_member_dim: int,
        critic_global_dim: int,
        n_skills: int,
        member_hidden_dim: int,
        high_hidden_dim: int,
        skill_embedding_dim: int,
    ) -> None:
        super().__init__()
        self.critic_member_dim = int(critic_member_dim)
        self.critic_global_dim = int(critic_global_dim)
        self.n_skills = int(n_skills)
        self.member_hidden_dim = int(member_hidden_dim)
        self.high_hidden_dim = int(high_hidden_dim)
        self.skill_embedding_dim = int(skill_embedding_dim)
        self.skill_embedding = nn.Embedding(self.n_skills, self.skill_embedding_dim)
        input_dim = (
            self.critic_member_dim
            + self.skill_embedding_dim
            + 3
        )
        self.member_encoder = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, self.member_hidden_dim),
            nn.GELU(),
        )
        value_input_dim = (
            2 * self.member_hidden_dim
            + 1
            + self.critic_global_dim
            + self.high_hidden_dim
            + len(BOUNDARY_KINDS)
        )
        self.value = nn.Sequential(
            nn.Linear(value_input_dim, self.member_hidden_dim),
            nn.GELU(),
            nn.Linear(self.member_hidden_dim, 1),
        )

    def values(
        self,
        critic_member_features: torch.Tensor,
        skills: torch.Tensor,
        ages: torch.Tensor,
        event_flags: torch.Tensor,
        high_hidden: torch.Tensor,
        critic_global_features: torch.Tensor,
        boundary_kind: str,
    ) -> torch.Tensor:
        if boundary_kind not in BOUNDARY_KINDS:
            raise ValueError(f"unknown critic boundary kind {boundary_kind!r}")
        flags = event_flags.bool().reshape(-1, 2)
        raw_skills = skills.long().reshape(-1)
        genuine_join = flags[:, 0]
        undefined = raw_skills < 0
        if bool(torch.any(undefined & ~genuine_join).item()):
            raise ValueError("only a genuine join may have an undefined critic skill")
        safe_skills = raw_skills.clamp(0, self.n_skills - 1)
        skill_features = self.skill_embedding(safe_skills)
        skill_features = torch.where(
            undefined.unsqueeze(-1),
            torch.zeros_like(skill_features),
            skill_features,
        )
        member_input = torch.cat(
            (
                critic_member_features.float(),
                skill_features,
                normalized_log_age(ages.float().reshape(-1)).unsqueeze(-1),
                flags.to(dtype=torch.float32),
            ),
            dim=-1,
        )
        encoded = self.member_encoder(member_input)
        set_sum = encoded.sum(dim=0, keepdim=True).expand_as(encoded)
        log_count = torch.log1p(
            torch.tensor(
                float(encoded.shape[0]), dtype=encoded.dtype, device=encoded.device
            )
        ).expand(encoded.shape[0], 1)
        global_rows = critic_global_features.float().reshape(1, -1).expand(
            encoded.shape[0], -1
        )
        kind = torch.zeros(
            encoded.shape[0], len(BOUNDARY_KINDS), dtype=encoded.dtype, device=encoded.device
        )
        kind[:, BOUNDARY_KINDS.index(boundary_kind)] = 1.0
        return self.value(
            torch.cat(
                (
                    encoded,
                    set_sum,
                    log_count,
                    global_rows,
                    high_hidden.float(),
                    kind,
                ),
                dim=-1,
            )
        ).squeeze(-1)


class Discrete:
    def __init__(self, n: int) -> None:
        self.n = int(n)


class Box:
    def __init__(self, shape: Sequence[int]) -> None:
        self.shape = tuple(int(value) for value in shape)


class EventLowActor(nn.Module):
    """Trainable actor-only ragged policy with the strict HMASD actor stack."""

    def __init__(
        self,
        *,
        obs_dim: int,
        n_skills: int,
        action_dim: int,
        hidden_dim: int,
        action_space_type: str = "discrete",
        device: str | torch.device = "cpu",
    ) -> None:
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.n_skills = int(n_skills)
        self.action_dim = int(action_dim)
        self.hidden_dim = int(hidden_dim)
        self.action_space_type = str(action_space_type)
        self.device = torch.device(device)

        class Args:
            pass

        args = Args()
        args.hidden_size = self.hidden_dim
        args.gain = 0.01
        args.use_orthogonal = True
        args.use_policy_active_masks = True
        args.use_naive_recurrent_policy = False
        args.use_recurrent_policy = True
        args.recurrent_N = 1
        args.use_feature_normalization = False
        args.use_popart = False
        args.continuous_action_distribution = "tanh_gaussian"
        args.continuous_logstd_init = -1.0
        args.continuous_logstd_min = -5.0
        args.continuous_logstd_max = 0.0
        self.actor_base = MLPBase(args, (self.obs_dim,))
        self.actor_film = nn.Linear(self.n_skills, 2 * self.hidden_dim)
        self.actor_rnn = RNNLayer(
            self.hidden_dim, self.hidden_dim, args.recurrent_N, args.use_orthogonal
        )
        action_space = (
            Discrete(self.action_dim)
            if self.action_space_type == "discrete"
            else Box((self.action_dim,))
        )
        self.actor_act = ACTLayer(
            action_space, self.hidden_dim, args.use_orthogonal, args.gain, args
        )
        self.to(self.device)

    @staticmethod
    def _squeeze_logp(logp: torch.Tensor) -> torch.Tensor:
        if logp.ndim > 1 and logp.shape[-1] == 1:
            return logp.squeeze(-1)
        return logp

    def _features(self, observations: torch.Tensor, skills: torch.Tensor) -> torch.Tensor:
        observations = check(observations).to(dtype=torch.float32, device=self.device)
        skills = check(skills).to(dtype=torch.long, device=self.device)
        features = self.actor_base(observations)
        film = self.actor_film(F.one_hot(skills, num_classes=self.n_skills).float())
        gamma, beta = torch.chunk(film, 2, dim=-1)
        return gamma * features + beta

    def actor_step(
        self,
        observations: torch.Tensor,
        skills: torch.Tensor,
        hidden: torch.Tensor,
        *,
        deterministic: bool = False,
        sampling_uniforms: np.ndarray | torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        observations = observations.to(self.device)
        skills = skills.to(self.device)
        hidden = hidden.to(dtype=torch.float32, device=self.device)
        features = self._features(observations, skills)
        masks = torch.ones(features.shape[0], 1, dtype=torch.float32, device=self.device)
        features, new_hidden = self.actor_rnn(features, hidden, masks)
        if self.action_space_type == "discrete":
            distribution = self.actor_act.action_out(features)
            if deterministic:
                actions = distribution.mode()
            else:
                if sampling_uniforms is None:
                    raise ValueError("discrete event low sampling requires owned uniforms")
                uniforms = np.asarray(
                    sampling_uniforms.detach().cpu().numpy()
                    if isinstance(sampling_uniforms, torch.Tensor)
                    else sampling_uniforms,
                    dtype=np.float64,
                ).reshape(-1)
                if uniforms.shape != (features.shape[0],):
                    raise ValueError("event low sampling-uniform shape mismatch")
                probability_rows = distribution.probs.detach().cpu().numpy()
                sampled = [
                    inverse_cdf_action(probability, uniform)
                    for probability, uniform in zip(probability_rows, uniforms)
                ]
                actions = torch.as_tensor(
                    sampled, dtype=torch.long, device=features.device
                ).unsqueeze(-1)
            logp = distribution.log_probs(actions)
            actions = actions.squeeze(-1)
        else:
            if sampling_uniforms is not None:
                raise ValueError("continuous event low policy does not accept discrete uniforms")
            actions, logp = self.actor_act(features, deterministic=deterministic)
        return actions, self._squeeze_logp(logp), new_hidden

    def actor_replay(
        self,
        observations: torch.Tensor,
        skills: torch.Tensor,
        actions: torch.Tensor,
        initial_hidden: torch.Tensor,
        valid_masks: torch.Tensor,
        reset_masks: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        logp, _entropy, final_hidden = self.actor_replay_with_entropy(
            observations,
            skills,
            actions,
            initial_hidden,
            valid_masks,
            reset_masks,
        )
        return logp, final_hidden

    def actor_replay_with_entropy(
        self,
        observations: torch.Tensor,
        skills: torch.Tensor,
        actions: torch.Tensor,
        initial_hidden: torch.Tensor,
        valid_masks: torch.Tensor,
        reset_masks: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        observations = observations.to(dtype=torch.float32, device=self.device)
        skills = skills.to(dtype=torch.long, device=self.device)
        actions = actions.to(device=self.device)
        valid_masks = valid_masks.to(dtype=torch.float32, device=self.device).reshape(
            observations.shape[0], observations.shape[1], 1
        )
        reset_masks = reset_masks.to(dtype=torch.float32, device=self.device).reshape_as(
            valid_masks
        )
        features = self._features(observations, skills)
        rnn_masks = torch.ones_like(valid_masks)
        if observations.shape[0] > 1:
            rnn_masks[1:] = reset_masks[:-1]
        features, final_hidden = self.actor_rnn(
            features,
            initial_hidden.to(dtype=torch.float32, device=self.device),
            rnn_masks,
        )
        flat_actions = (
            actions.reshape(-1, 1)
            if self.action_space_type == "discrete"
            else actions.reshape(-1, self.action_dim)
        )
        logp, entropy = self.actor_act.evaluate_actions(
            features.reshape(-1, self.hidden_dim),
            flat_actions,
            active_masks=valid_masks.reshape(-1, 1),
        )
        logp = self._squeeze_logp(logp).reshape(observations.shape[:2])
        return logp, entropy, final_hidden


class EventActiveSetLowCritic(nn.Module):
    """Separate active-set critic; no identity or fixed roster axis."""

    def __init__(
        self,
        *,
        critic_member_dim: int,
        critic_global_dim: int,
        n_skills: int,
        hidden_dim: int,
        skill_embedding_dim: int,
        device: str | torch.device = "cpu",
    ) -> None:
        super().__init__()
        self.critic_member_dim = int(critic_member_dim)
        self.critic_global_dim = int(critic_global_dim)
        self.n_skills = int(n_skills)
        self.hidden_dim = int(hidden_dim)
        self.device = torch.device(device)
        self.skill_embedding = nn.Embedding(self.n_skills, int(skill_embedding_dim))
        self.member_encoder = nn.Sequential(
            nn.Linear(self.critic_member_dim + int(skill_embedding_dim), self.hidden_dim),
            nn.GELU(),
        )
        self.source_dim = self.hidden_dim + 1 + self.critic_global_dim
        self.critic_input = nn.Sequential(
            nn.Linear(self.hidden_dim + self.source_dim, self.hidden_dim),
            nn.GELU(),
        )
        self.critic_rnn = nn.GRUCell(self.hidden_dim, self.hidden_dim)
        self.value_head = nn.Linear(self.hidden_dim, 1)
        self.to(self.device)

    def _member_encoded(
        self, member_features: torch.Tensor, skills: torch.Tensor
    ) -> torch.Tensor:
        member_features = member_features.to(dtype=torch.float32, device=self.device)
        skills = skills.to(dtype=torch.long, device=self.device)
        return self.member_encoder(
            torch.cat((member_features, self.skill_embedding(skills)), dim=-1)
        )

    def critic_step(
        self,
        member_features: torch.Tensor,
        skills: torch.Tensor,
        env_ptr: torch.Tensor,
        global_features: torch.Tensor,
        hidden: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        encoded = self._member_encoded(member_features, skills)
        env_ptr = env_ptr.to(dtype=torch.long, device=self.device)
        global_features = global_features.to(dtype=torch.float32, device=self.device)
        source = torch.empty(
            encoded.shape[0], self.source_dim, dtype=encoded.dtype, device=self.device
        )
        for env_id in range(int(env_ptr.numel()) - 1):
            start = int(env_ptr[env_id].item())
            end = int(env_ptr[env_id + 1].item())
            if end <= start:
                raise ValueError("event low critic does not admit an empty active set")
            set_sum = encoded[start:end].sum(dim=0)
            count = torch.log1p(
                torch.tensor(float(end - start), dtype=encoded.dtype, device=self.device)
            ).reshape(1)
            row = torch.cat((set_sum, count, global_features[env_id]), dim=0)
            source[start:end] = row.unsqueeze(0).expand(end - start, -1)
        features = self.critic_input(torch.cat((encoded, source), dim=-1))
        new_hidden = self.critic_rnn(features, hidden.to(self.device).float())
        return self.value_head(new_hidden).squeeze(-1), new_hidden, source

    def critic_replay(
        self,
        member_features: torch.Tensor,
        skills: torch.Tensor,
        source_summary: torch.Tensor,
        initial_hidden: torch.Tensor,
        valid_masks: torch.Tensor,
        reset_masks: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        member_features = member_features.to(dtype=torch.float32, device=self.device)
        skills = skills.to(dtype=torch.long, device=self.device)
        source_summary = source_summary.to(dtype=torch.float32, device=self.device)
        valid_masks = valid_masks.to(dtype=torch.float32, device=self.device)
        reset_masks = reset_masks.to(dtype=torch.float32, device=self.device)
        hidden = initial_hidden.to(dtype=torch.float32, device=self.device)
        values: list[torch.Tensor] = []
        for step in range(member_features.shape[0]):
            if step > 0:
                hidden = hidden * reset_masks[step - 1].reshape(-1, 1)
            encoded = self._member_encoded(member_features[step], skills[step])
            features = self.critic_input(
                torch.cat((encoded, source_summary[step]), dim=-1)
            )
            proposed = self.critic_rnn(features, hidden)
            valid = valid_masks[step].reshape(-1, 1)
            hidden = proposed * valid + hidden * (1.0 - valid)
            values.append(self.value_head(hidden).squeeze(-1))
        return torch.stack(values), hidden

    def critic_replay_from_active_sets(
        self,
        active_member_features: torch.Tensor,
        active_skills: torch.Tensor,
        active_masks: torch.Tensor,
        focal_indices: torch.Tensor,
        global_features: torch.Tensor,
        initial_hidden: torch.Tensor,
        valid_masks: torch.Tensor,
        reset_masks: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Re-encode each anonymous active set under current critic parameters."""

        features = active_member_features.to(dtype=torch.float32, device=self.device)
        skills = active_skills.to(dtype=torch.long, device=self.device)
        masks = active_masks.to(dtype=torch.bool, device=self.device)
        focal = focal_indices.to(dtype=torch.long, device=self.device)
        globals_ = global_features.to(dtype=torch.float32, device=self.device)
        valid = valid_masks.to(dtype=torch.float32, device=self.device)
        reset = reset_masks.to(dtype=torch.float32, device=self.device)
        if features.ndim != 4 or features.shape[-1] != self.critic_member_dim:
            raise ValueError("raw active critic features have the wrong shape")
        if skills.shape != features.shape[:3] or masks.shape != features.shape[:3]:
            raise ValueError("raw active critic skills/masks do not match features")
        if focal.shape != features.shape[:2]:
            raise ValueError("raw active critic focal indices have the wrong shape")
        if globals_.shape != (*features.shape[:2], self.critic_global_dim):
            raise ValueError("raw active critic global features have the wrong shape")
        if bool(torch.any(masks.sum(dim=-1) <= 0).item()):
            raise ValueError("raw active critic replay does not admit an empty set")
        if bool(
            torch.any(
                (focal < 0)
                | (focal >= features.shape[2])
                | ~torch.gather(masks, 2, focal.unsqueeze(-1)).squeeze(-1)
            ).item()
        ):
            raise ValueError("raw active critic focal row is invalid")

        time_steps, batch_size, max_active, _ = features.shape
        encoded = self._member_encoded(
            features.reshape(time_steps * batch_size * max_active, -1),
            skills.reshape(-1),
        ).reshape(time_steps, batch_size, max_active, self.hidden_dim)
        float_masks = masks.to(dtype=encoded.dtype).unsqueeze(-1)
        set_sum = (encoded * float_masks).sum(dim=2)
        count = torch.log1p(masks.sum(dim=2).to(dtype=encoded.dtype)).unsqueeze(-1)
        source = torch.cat((set_sum, count, globals_), dim=-1)
        gather_index = focal.unsqueeze(-1).unsqueeze(-1).expand(
            time_steps, batch_size, 1, self.hidden_dim
        )
        focal_encoded = torch.gather(encoded, 2, gather_index).squeeze(2)
        hidden = initial_hidden.to(dtype=torch.float32, device=self.device)
        values: list[torch.Tensor] = []
        for step in range(time_steps):
            if step > 0:
                hidden = hidden * reset[step - 1].reshape(-1, 1)
            critic_input = self.critic_input(
                torch.cat((focal_encoded[step], source[step]), dim=-1)
            )
            proposed = self.critic_rnn(critic_input, hidden)
            step_valid = valid[step].reshape(-1, 1)
            hidden = proposed * step_valid + hidden * (1.0 - step_valid)
            values.append(self.value_head(hidden).squeeze(-1))
        return torch.stack(values), hidden, source


class VariableRosterEventCore:
    """Single-environment lifecycle runtime used by the focused trace."""

    def __init__(
        self,
        *,
        architecture_mode: str,
        obs_dim: int,
        critic_member_dim: int,
        critic_global_dim: int,
        n_skills: int,
        action_dim: int,
        member_hidden_dim: int = 16,
        high_hidden_dim: int = 16,
        low_hidden_dim: int = 16,
        skill_embedding_dim: int = 8,
        action_space_type: str = "discrete",
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        environment_index: int = 0,
        opportunity_seed: int = 1,
        frontier_seed: int = 2,
        action_seed: int = 3,
        rng_episode_id: int = 0,
        opportunity_stream_id: int = 0,
        frontier_stream_id: int = 1,
        action_stream_id: int = 0,
        device: str | torch.device = "cpu",
        shared_models_from: "VariableRosterEventCore | None" = None,
    ) -> None:
        mode = str(architecture_mode).lower()
        if mode not in EVENT_MODES:
            raise ValueError(f"event architecture mode must be one of {EVENT_MODES}")
        if int(n_skills) < 2:
            raise ValueError("event runtime requires at least two skills")
        self.architecture_mode = mode
        self.obs_dim = int(obs_dim)
        self.critic_member_dim = int(critic_member_dim)
        self.critic_global_dim = int(critic_global_dim)
        self.n_skills = int(n_skills)
        self.action_dim = int(action_dim)
        self.member_hidden_dim = int(member_hidden_dim)
        self.high_hidden_dim = int(high_hidden_dim)
        self.low_hidden_dim = int(low_hidden_dim)
        self.skill_embedding_dim = int(skill_embedding_dim)
        self.action_space_type = str(action_space_type)
        self.gamma = float(gamma)
        self.gae_lambda = float(gae_lambda)
        self.environment_index = int(environment_index)
        self.rng_episode_id = int(rng_episode_id)
        self.opportunity_master_seed = int(opportunity_seed)
        self.frontier_master_seed = int(frontier_seed)
        self.action_master_seed = int(action_seed)
        self.opportunity_stream_id = int(opportunity_stream_id)
        self.frontier_stream_id = int(frontier_stream_id)
        self.action_stream_id = int(action_stream_id)
        self.device = torch.device(device)
        self.policy_version = 0
        self.physical_time = 0

        if shared_models_from is None:
            self.commitment_model = EventCommitmentPolicy(
                obs_dim=self.obs_dim,
                n_skills=self.n_skills,
                member_hidden_dim=self.member_hidden_dim,
                high_hidden_dim=self.high_hidden_dim,
                skill_embedding_dim=self.skill_embedding_dim,
            ).to(self.device)
            self.event_critic = EventHighCritic(
                critic_member_dim=self.critic_member_dim,
                critic_global_dim=self.critic_global_dim,
                n_skills=self.n_skills,
                member_hidden_dim=self.member_hidden_dim,
                high_hidden_dim=self.high_hidden_dim,
                skill_embedding_dim=self.skill_embedding_dim,
            ).to(self.device)
            self.low_actor = EventLowActor(
                obs_dim=self.obs_dim,
                n_skills=self.n_skills,
                action_dim=self.action_dim,
                hidden_dim=self.low_hidden_dim,
                action_space_type=self.action_space_type,
                device=self.device,
            )
            self.low_critic = EventActiveSetLowCritic(
                critic_member_dim=self.critic_member_dim,
                critic_global_dim=self.critic_global_dim,
                n_skills=self.n_skills,
                hidden_dim=self.low_hidden_dim,
                skill_embedding_dim=self.skill_embedding_dim,
                device=self.device,
            )
        else:
            if shared_models_from.architecture_state() != self.architecture_state():
                raise ValueError("shared event cores must have identical architecture")
            self.commitment_model = shared_models_from.commitment_model
            self.event_critic = shared_models_from.event_critic
            self.low_actor = shared_models_from.low_actor
            self.low_critic = shared_models_from.low_critic

        self.records: dict[str, LifecycleRecord] = {}
        self.high_ledger: list[EventTokenRow] = []
        self.closed_event_rows: list[ClosedEventRow] = []
        self.low_ledger: list[LowTransitionRow] = []
        self.low_chunk_boundaries: list[dict[str, Any]] = []
        self.current_observation_state_boundary: dict[str, Any] | None = None
        self.pending_membership_transaction: Any = None
        self.opportunity_rng = make_pcg64_rng(
            self.opportunity_master_seed,
            self.rng_episode_id,
            self.opportunity_stream_id,
        )
        self.frontier_rng = make_pcg64_rng(
            self.frontier_master_seed,
            self.rng_episode_id,
            self.frontier_stream_id,
        )
        self.action_rng = make_pcg64_rng(
            self.action_master_seed,
            self.rng_episode_id,
            self.action_stream_id,
        )

    def model_signature(self) -> dict[str, dict[str, tuple[int, ...]]]:
        return {
            "commitment_model": _state_dict_shapes(self.commitment_model),
            "event_critic": _state_dict_shapes(self.event_critic),
            "low_actor": _state_dict_shapes(self.low_actor),
            "low_critic": _state_dict_shapes(self.low_critic),
        }

    def model_parameter_count(self) -> int:
        return sum(
            parameter_count(module)
            for module in (
                self.commitment_model,
                self.event_critic,
                self.low_actor,
                self.low_critic,
            )
        )

    def _new_record(self, key: str) -> LifecycleRecord:
        return LifecycleRecord(
            lifecycle_key=str(key),
            status=ACTIVE,
            membership_epoch=0,
            low_actor_hidden=np.zeros(self.low_hidden_dim, dtype=np.float32),
            low_critic_hidden=np.zeros(self.low_hidden_dim, dtype=np.float32),
            high_hidden=np.zeros(self.high_hidden_dim, dtype=np.float32),
            active_skill=None,
            skill_active_age=0,
            active_gap_remaining=0,
            last_policy_event_time=None,
            open_event_trace=None,
            policy_version=self.policy_version,
            is_genuine_join=True,
            is_rejoin=False,
        )

    @staticmethod
    def _active_keys(records: Mapping[str, LifecycleRecord]) -> tuple[str, ...]:
        return tuple(key for key, record in records.items() if record.status == ACTIVE)

    def _validate_snapshot(
        self,
        records: Mapping[str, LifecycleRecord],
        snapshot: BoundarySnapshot,
        *,
        allow_empty: bool,
    ) -> None:
        active_keys = set(self._active_keys(records))
        snapshot_keys = set(snapshot.keys)
        if snapshot_keys != active_keys:
            raise ValueError(
                "boundary active set does not match LifecycleStore: "
                f"snapshot={sorted(snapshot_keys)}, store={sorted(active_keys)}"
            )
        if not snapshot_keys and not allow_empty:
            raise ValueError("schema-1 event runtime does not admit an empty active set")
        for member in snapshot.members:
            record = records[member.lifecycle_key]
            if int(member.membership_epoch) != int(record.membership_epoch):
                raise ValueError("boundary snapshot carries a stale membership epoch")

    def _simulate_deltas(
        self, transaction: MembershipTransaction
    ) -> dict[str, LifecycleRecord]:
        trial = {key: record.clone() for key, record in self.records.items()}
        for delta in transaction.atomic_membership_delta:
            key = str(delta.lifecycle_key)
            expected = int(delta.expected_membership_epoch)
            if delta.kind == JOIN:
                if key in trial:
                    raise ValueError("genuine join attempted to reuse a lifecycle key")
                if expected != 0:
                    raise ValueError("genuine join must declare membership epoch 0")
                trial[key] = self._new_record(key)
                continue
            if key not in trial:
                raise ValueError("membership delta references an unknown lifecycle")
            record = trial[key]
            if int(record.membership_epoch) != expected:
                raise ValueError("membership delta carries a stale epoch")
            if delta.kind == TEMPORARY_LEAVE:
                if record.status != ACTIVE:
                    raise ValueError("temporary leave requires an active lifecycle")
                record.status = TEMPORARILY_ABSENT
                record.is_genuine_join = False
                record.is_rejoin = False
            elif delta.kind == REJOIN:
                if record.status != TEMPORARILY_ABSENT:
                    raise ValueError("rejoin requires a temporarily absent lifecycle")
                record.status = ACTIVE
                record.membership_epoch += 1
                record.active_gap_remaining = 0
                record.is_genuine_join = False
                record.is_rejoin = True
            elif delta.kind == TERMINAL_LEAVE:
                if record.status not in (ACTIVE, TEMPORARILY_ABSENT):
                    raise ValueError("terminal leave references a terminal lifecycle")
                record.status = TERMINAL
                record.active_skill = None
                record.active_gap_remaining = None
                record.low_actor_hidden = np.empty(0, dtype=np.float32)
                record.low_critic_hidden = np.empty(0, dtype=np.float32)
                record.high_hidden = np.empty(0, dtype=np.float32)
                record.is_genuine_join = False
                record.is_rejoin = False
            else:  # pragma: no cover - guarded by MembershipDelta
                raise ValueError(f"unsupported membership delta {delta.kind!r}")
        return trial

    def _validate_expected_frontier(
        self, records: Mapping[str, LifecycleRecord], snapshot: BoundarySnapshot
    ) -> None:
        expected = {
            key
            for key, record in records.items()
            if record.status == ACTIVE
            and (
                record.is_genuine_join
                or record.is_rejoin
                or int(record.active_gap_remaining or 0) <= 0
            )
        }
        if set(snapshot.frontier) != expected:
            raise ValueError(
                "post-membership frontier does not match lifecycle opportunity state: "
                f"snapshot={sorted(snapshot.frontier)}, expected={sorted(expected)}"
            )

    def pack_active(
        self, snapshot: BoundarySnapshot
    ) -> tuple[PackedActiveBatch, ActiveRoutingView]:
        self._validate_snapshot(self.records, snapshot, allow_empty=False)
        keys = snapshot.keys
        records = [self.records[key] for key in keys]
        skills = np.asarray(
            [(-1 if record.active_skill is None else record.active_skill) for record in records],
            dtype=np.int64,
        )
        ages = np.asarray([record.skill_active_age for record in records], dtype=np.int64)
        flags = np.asarray(
            [[record.is_genuine_join, record.is_rejoin] for record in records],
            dtype=np.bool_,
        )
        batch = PackedActiveBatch(
            env_ptr=torch.tensor([0, len(records)], dtype=torch.int64, device=self.device),
            member_obs=torch.as_tensor(
                np.stack([member.observation for member in snapshot.members]),
                dtype=torch.float32,
                device=self.device,
            ),
            critic_member_features=torch.as_tensor(
                np.stack(
                    [member.critic_member_features for member in snapshot.members]
                ),
                dtype=torch.float32,
                device=self.device,
            ),
            critic_global_features=torch.as_tensor(
                snapshot.critic_global_features.reshape(1, -1),
                dtype=torch.float32,
                device=self.device,
            ),
            skills=torch.as_tensor(skills, dtype=torch.long, device=self.device),
            active_ages=torch.as_tensor(ages, dtype=torch.long, device=self.device),
            event_flags=torch.as_tensor(flags, dtype=torch.bool, device=self.device),
            low_actor_hidden=torch.as_tensor(
                np.stack([record.low_actor_hidden for record in records]),
                dtype=torch.float32,
                device=self.device,
            ),
            low_critic_hidden=torch.as_tensor(
                np.stack([record.low_critic_hidden for record in records]),
                dtype=torch.float32,
                device=self.device,
            ),
            high_hidden=torch.as_tensor(
                np.stack([record.high_hidden for record in records]),
                dtype=torch.float32,
                device=self.device,
            ),
        )
        routing = ActiveRoutingView(
            lifecycle_keys=keys,
            membership_epochs=tuple(record.membership_epoch for record in records),
        )
        return batch, routing

    def _critic_values(
        self, snapshot: BoundarySnapshot, boundary_kind: str
    ) -> tuple[torch.Tensor, ActiveRoutingView]:
        packed, routing = self.pack_active(snapshot)
        values = self.event_critic.values(
            packed.critic_member_features,
            packed.skills,
            packed.active_ages,
            packed.event_flags,
            packed.high_hidden,
            packed.critic_global_features[0],
            boundary_kind,
        )
        return values, routing

    def _low_critic_values(
        self, snapshot: BoundarySnapshot
    ) -> tuple[torch.Tensor, ActiveRoutingView]:
        packed, routing = self.pack_active(snapshot)
        values, _next_hidden, _source = self.low_critic.critic_step(
            packed.critic_member_features,
            packed.skills,
            packed.env_ptr,
            packed.critic_global_features,
            packed.low_critic_hidden,
        )
        return values, routing

    def _close_trace(
        self,
        record: LifecycleRecord,
        *,
        bootstrap_value: float,
        boundary_kind: str,
    ) -> ClosedEventRow | None:
        trace = record.open_event_trace
        if trace is None:
            return None
        elapsed = int(trace.elapsed_physical_time)
        discount = 0.0 if boundary_kind == TERMINAL_BOUNDARY else self.gamma ** elapsed
        bootstrap = 0.0 if boundary_kind == TERMINAL_BOUNDARY else float(bootstrap_value)
        row = ClosedEventRow(
            lifecycle_key=record.lifecycle_key,
            membership_epoch=int(record.membership_epoch),
            policy_version=int(trace.policy_version),
            actor_valid=bool(trace.actor_valid),
            start_time=int(trace.start_time),
            end_time=int(self.physical_time),
            elapsed_physical_time=elapsed,
            discounted_reward=float(trace.discounted_reward),
            old_value=float(trace.old_value),
            bootstrap_value=bootstrap,
            bootstrap_discount=float(discount),
            return_target=float(trace.discounted_reward + discount * bootstrap),
            old_log_probability=trace.old_log_probability,
            token_ledger_index=trace.token_ledger_index,
            boundary_kind=str(boundary_kind),
        )
        self.closed_event_rows.append(row)
        record.open_event_trace = None
        return row

    def _record_low_boundary(
        self,
        record: LifecycleRecord,
        kind: str,
        *,
        bootstrap_value: float,
    ) -> None:
        bootstrap_source = {
            TEMPORARY_BOUNDARY: "pre_membership_boundary_snapshot",
            TERMINAL_BOUNDARY: "zero",
            ROLLOUT_TRUNCATION: "old_critic_policy_truncation",
        }.get(str(kind))
        closed_row: LowTransitionRow | None = None
        for row in reversed(self.low_ledger):
            if (
                row.lifecycle_key == record.lifecycle_key
                and row.membership_epoch == record.membership_epoch
                and row.terminal_or_truncation_kind is None
            ):
                row.terminal_or_truncation_kind = str(kind)
                row.bootstrap_source = bootstrap_source
                row.bootstrap_value = float(bootstrap_value)
                closed_row = row
                break
        if closed_row is None:
            return
        self.low_chunk_boundaries.append(
            {
                "lifecycle_key": record.lifecycle_key,
                "membership_epoch": int(record.membership_epoch),
                "physical_time": int(self.physical_time),
                "policy_version": int(record.policy_version),
                "boundary_kind": str(kind),
                "bootstrap_source": bootstrap_source,
                "bootstrap_value": float(bootstrap_value),
                "actor_hidden": np.asarray(record.low_actor_hidden, dtype=np.float32).copy(),
                "critic_hidden": np.asarray(record.low_critic_hidden, dtype=np.float32).copy(),
            }
        )

    def bind_due_frontier(
        self, transaction: MembershipTransaction
    ) -> MembershipTransaction:
        """Bind private opportunity clocks to an environment-owned transaction."""

        pre = transaction.pre_membership_boundary_snapshot
        post = transaction.post_membership_pre_policy_snapshot
        if int(pre.physical_time) != int(self.physical_time):
            raise ValueError("transaction physical time does not match runtime")
        self._validate_snapshot(self.records, pre, allow_empty=not bool(self.records))
        trial = self._simulate_deltas(transaction)
        self._validate_snapshot(trial, post, allow_empty=False)
        structural = {
            str(delta.lifecycle_key)
            for delta in transaction.atomic_membership_delta
            if delta.kind in (JOIN, REJOIN)
        }
        if set(post.frontier) != structural:
            raise ValueError("environment frontier may contain only structural arrivals")
        expected = {
            key
            for key, record in trial.items()
            if record.status == ACTIVE
            and (
                record.is_genuine_join
                or record.is_rejoin
                or int(record.active_gap_remaining or 0) <= 0
            )
        }
        bound_post = BoundarySnapshot.make(
            post.physical_time,
            post.members,
            post.critic_global_features,
            critic_global_dim=self.critic_global_dim,
            frontier=tuple(key for key in post.keys if key in expected),
        )
        return MembershipTransaction(
            pre,
            transaction.atomic_membership_delta,
            bound_post,
        )

    def apply_transaction(
        self,
        transaction: MembershipTransaction,
        *,
        teacher_order: Sequence[str] | None = None,
        teacher_actions: Mapping[str, int] | None = None,
        deterministic_policy: bool = False,
    ) -> EventTransactionResult:
        pre = transaction.pre_membership_boundary_snapshot
        post = transaction.post_membership_pre_policy_snapshot
        if int(pre.physical_time) != int(self.physical_time):
            raise ValueError("transaction physical time does not match runtime")
        self._validate_snapshot(self.records, pre, allow_empty=not bool(self.records))
        trial = self._simulate_deltas(transaction)
        self._validate_snapshot(trial, post, allow_empty=False)
        self._validate_expected_frontier(trial, post)

        pre_values: dict[str, float] = {}
        pre_low_values: dict[str, float] = {}
        if pre.members:
            values, routing = self._critic_values(pre, TEMPORARY_BOUNDARY)
            pre_values = {
                key: float(values[index].detach().cpu())
                for index, key in enumerate(routing.lifecycle_keys)
            }
            low_values, low_routing = self._low_critic_values(pre)
            pre_low_values = {
                key: float(low_values[index].detach().cpu())
                for index, key in enumerate(low_routing.lifecycle_keys)
            }

        # Validation above completed on a clone; state mutation starts here.
        for delta in transaction.atomic_membership_delta:
            current = self.records.get(delta.lifecycle_key)
            if current is None:
                continue
            if delta.kind == TEMPORARY_LEAVE:
                self._close_trace(
                    current,
                    bootstrap_value=pre_values[current.lifecycle_key],
                    boundary_kind=TEMPORARY_BOUNDARY,
                )
                self._record_low_boundary(
                    current,
                    TEMPORARY_BOUNDARY,
                    bootstrap_value=pre_low_values[current.lifecycle_key],
                )
                trial[current.lifecycle_key].open_event_trace = None
            elif delta.kind == TERMINAL_LEAVE:
                self._close_trace(
                    current,
                    bootstrap_value=0.0,
                    boundary_kind=TERMINAL_BOUNDARY,
                )
                self._record_low_boundary(
                    current,
                    TERMINAL_BOUNDARY,
                    bootstrap_value=0.0,
                )
                trial[current.lifecycle_key].open_event_trace = None
        self.records = trial

        result = self._process_frontier(
            post,
            teacher_order=teacher_order,
            teacher_actions=teacher_actions,
            deterministic_policy=deterministic_policy,
        )
        for key in post.keys:
            self.records[key].is_genuine_join = False
            self.records[key].is_rejoin = False
        return result

    def _process_frontier(
        self,
        snapshot: BoundarySnapshot,
        *,
        teacher_order: Sequence[str] | None,
        teacher_actions: Mapping[str, int] | None,
        deterministic_policy: bool,
    ) -> EventTransactionResult:
        frontier = tuple(snapshot.frontier)
        if not frontier:
            return EventTransactionResult((), 0.0, (), self.active_skills())
        if teacher_order is None:
            sampled_order = tuple(
                str(value)
                for value in self.frontier_rng.permutation(np.asarray(frontier, dtype=object))
            )
        else:
            sampled_order = tuple(str(value) for value in teacher_order)
            if len(sampled_order) != len(set(sampled_order)) or set(sampled_order) != set(
                frontier
            ):
                raise ValueError("teacher order is not a permutation of the frontier")
        order_logp = -math.lgamma(len(frontier) + 1.0)

        packed, routing = self.pack_active(snapshot)
        key_to_row = {key: index for index, key in enumerate(routing.lifecycle_keys)}
        working_skills = packed.skills.clone()
        working_ages = packed.active_ages.clone()
        flags = packed.event_flags.clone()
        observations = packed.member_obs.clone()
        initial_skills = working_skills.clone()
        initial_ages = working_ages.clone()
        member_embeddings = self.commitment_model.encode_members(
            observations, working_skills, working_ages, flags
        )
        working_embeddings = member_embeddings.clone()
        initial_summary = self.commitment_model.set_summary(member_embeddings)
        working_summary = initial_summary.clone()
        token_rows: list[EventTokenRow] = []

        for position, key in enumerate(sampled_order):
            row_index = key_to_row[key]
            record = self.records[key]
            pre_skills = working_skills.detach().cpu().numpy().copy()
            pre_ages = working_ages.detach().cpu().numpy().copy()
            pre_hidden = torch.as_tensor(
                record.high_hidden, dtype=torch.float32, device=self.device
            )
            active_high_hidden = torch.stack(
                [
                    torch.as_tensor(
                        self.records[route_key].high_hidden,
                        dtype=torch.float32,
                        device=self.device,
                    )
                    for route_key in routing.lifecycle_keys
                ]
            )
            critic_values = self.event_critic.values(
                packed.critic_member_features,
                working_skills,
                working_ages,
                flags,
                active_high_hidden,
                packed.critic_global_features[0],
                ORDINARY_BOUNDARY,
            )
            old_value = float(critic_values[row_index].detach().cpu())
            self._close_trace(
                record,
                bootstrap_value=old_value,
                boundary_kind=ORDINARY_BOUNDARY,
            )
            selected_summary = (
                initial_summary if self.architecture_mode == "f0" else working_summary
            )
            logits, new_hidden = self.commitment_model.logits(
                working_embeddings[row_index], selected_summary, pre_hidden
            )
            legal_mask = torch.ones(self.n_skills, dtype=torch.bool, device=self.device)
            masked_logits = logits.masked_fill(~legal_mask, -torch.inf)
            log_probabilities = F.log_softmax(masked_logits, dim=-1)
            policy_action_uniform: float | None = None
            if teacher_actions is not None:
                if key not in teacher_actions:
                    raise ValueError("teacher actions omit a frontier owner")
                action = int(teacher_actions[key])
            elif deterministic_policy:
                action = int(torch.argmax(masked_logits).item())
            else:
                policy_action_uniform = float(self.action_rng.random())
                action = inverse_cdf_action(
                    torch.softmax(masked_logits.detach(), dim=-1).cpu().numpy(),
                    policy_action_uniform,
                )
            if not 0 <= action < self.n_skills or not bool(legal_mask[action].item()):
                raise ValueError("combined event action is outside the stored support")
            old_logp = float(log_probabilities[action].detach().cpu())
            incumbent = record.active_skill
            if incumbent is None:
                action_kind = "SET"
            elif int(action) == int(incumbent):
                action_kind = "KEEP"
            else:
                action_kind = "SET"
            if action_kind == "SET":
                record.active_skill = int(action)
                record.skill_active_age = 0
                working_skills[row_index] = int(action)
                working_ages[row_index] = 0
            record.high_hidden = new_hidden.detach().cpu().numpy().astype(np.float32)
            record.last_policy_event_time = int(self.physical_time)
            record.policy_version = int(self.policy_version)
            new_embedding = self.commitment_model.encode_members(
                observations[row_index : row_index + 1],
                working_skills[row_index : row_index + 1],
                working_ages[row_index : row_index + 1],
                flags[row_index : row_index + 1],
            )[0]
            working_summary = working_summary.clone()
            working_summary[:-1] += new_embedding - working_embeddings[row_index]
            working_embeddings = working_embeddings.clone()
            working_embeddings[row_index] = new_embedding
            gap = int(
                self.opportunity_rng.integers(
                    OPPORTUNITY_GAP_LOW, OPPORTUNITY_GAP_HIGH + 1
                )
            )
            record.active_gap_remaining = gap
            record.open_event_trace = OpenEventTrace(
                start_time=int(self.physical_time),
                policy_version=int(self.policy_version),
                actor_valid=True,
                old_value=old_value,
                old_log_probability=old_logp,
                token_ledger_index=len(self.high_ledger),
            )
            token_row = EventTokenRow(
                environment_index=self.environment_index,
                policy_version=self.policy_version,
                physical_event_time=self.physical_time,
                owner_lifecycle_key=key,
                membership_epoch=record.membership_epoch,
                frontier=frontier,
                sampled_order=sampled_order,
                order_log_probability=float(order_logp),
                token_position=position,
                sampled_replacement_gap=gap,
                active_lifecycle_keys=routing.lifecycle_keys,
                active_membership_epochs=routing.membership_epochs,
                active_observations=observations.detach().cpu().numpy().copy(),
                active_critic_member_features=packed.critic_member_features.detach()
                .cpu()
                .numpy()
                .copy(),
                critic_global_features=packed.critic_global_features[0]
                .detach()
                .cpu()
                .numpy()
                .copy(),
                event_flags=flags.detach().cpu().numpy().copy(),
                initial_skills=initial_skills.detach().cpu().numpy().copy(),
                initial_ages=initial_ages.detach().cpu().numpy().copy(),
                pre_token_working_skills=pre_skills,
                pre_token_working_ages=pre_ages,
                post_token_working_skills=working_skills.detach().cpu().numpy().copy(),
                post_token_working_ages=working_ages.detach().cpu().numpy().copy(),
                active_high_hidden=active_high_hidden.detach().cpu().numpy().copy(),
                pre_token_high_hidden=pre_hidden.detach().cpu().numpy().copy(),
                exact_legal_mask=legal_mask.detach().cpu().numpy().copy(),
                policy_action_uniform=policy_action_uniform,
                combined_action=action,
                old_token_log_probability=old_logp,
                old_owner_value=old_value,
                action_kind=action_kind,
            )
            self.high_ledger.append(token_row)
            token_rows.append(token_row)
        return EventTransactionResult(
            sampled_order=sampled_order,
            order_log_probability=float(order_logp),
            token_rows=tuple(token_rows),
            final_skills=self.active_skills(),
        )

    def replay_token_log_probability(self, row: EventTokenRow) -> float:
        logp, _value, _entropy = self.replay_event_token(row)
        return float(logp.detach().cpu())

    def replay_token_distribution(
        self,
        row: EventTokenRow,
        *,
        summary_source: str,
    ) -> np.ndarray:
        """Read one stored token under an explicit initial/working summary.

        This is an audit-only probability read.  It teacher-forces the stored
        observation, support, hidden state, skills and ages and never samples
        or mutates runtime state.
        """

        source = str(summary_source)
        if source not in {"initial", "working"}:
            raise ValueError("summary_source must be initial or working")
        observations = torch.as_tensor(
            row.active_observations, dtype=torch.float32, device=self.device
        )
        flags = torch.as_tensor(row.event_flags, dtype=torch.bool, device=self.device)
        initial_skills = torch.as_tensor(
            row.initial_skills, dtype=torch.long, device=self.device
        )
        initial_ages = torch.as_tensor(
            row.initial_ages, dtype=torch.long, device=self.device
        )
        working_skills = torch.as_tensor(
            row.pre_token_working_skills, dtype=torch.long, device=self.device
        )
        working_ages = torch.as_tensor(
            row.pre_token_working_ages, dtype=torch.long, device=self.device
        )
        initial_embeddings = self.commitment_model.encode_members(
            observations, initial_skills, initial_ages, flags
        )
        working_embeddings = self.commitment_model.encode_members(
            observations, working_skills, working_ages, flags
        )
        owner_index = row.active_lifecycle_keys.index(row.owner_lifecycle_key)
        summary = self.commitment_model.set_summary(
            initial_embeddings if source == "initial" else working_embeddings
        )
        logits, _ = self.commitment_model.logits(
            working_embeddings[owner_index],
            summary,
            torch.as_tensor(
                row.pre_token_high_hidden,
                dtype=torch.float32,
                device=self.device,
            ),
        )
        mask = torch.as_tensor(row.exact_legal_mask, dtype=torch.bool, device=self.device)
        probabilities = torch.softmax(logits.masked_fill(~mask, -torch.inf), dim=-1)
        return probabilities.detach().cpu().numpy().astype(np.float64, copy=True)

    def replay_event_token(
        self, row: EventTokenRow
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        observations = torch.as_tensor(
            row.active_observations, dtype=torch.float32, device=self.device
        )
        flags = torch.as_tensor(row.event_flags, dtype=torch.bool, device=self.device)
        initial_skills = torch.as_tensor(
            row.initial_skills, dtype=torch.long, device=self.device
        )
        initial_ages = torch.as_tensor(
            row.initial_ages, dtype=torch.long, device=self.device
        )
        working_skills = torch.as_tensor(
            row.pre_token_working_skills, dtype=torch.long, device=self.device
        )
        working_ages = torch.as_tensor(
            row.pre_token_working_ages, dtype=torch.long, device=self.device
        )
        initial_embeddings = self.commitment_model.encode_members(
            observations, initial_skills, initial_ages, flags
        )
        working_embeddings = self.commitment_model.encode_members(
            observations, working_skills, working_ages, flags
        )
        initial_summary = self.commitment_model.set_summary(initial_embeddings)
        working_summary = self.commitment_model.set_summary(working_embeddings)
        owner_index = row.active_lifecycle_keys.index(row.owner_lifecycle_key)
        selected_summary = (
            initial_summary if self.architecture_mode == "f0" else working_summary
        )
        logits, _new_hidden = self.commitment_model.logits(
            working_embeddings[owner_index],
            selected_summary,
            torch.as_tensor(
                row.pre_token_high_hidden, dtype=torch.float32, device=self.device
            ),
        )
        mask = torch.as_tensor(row.exact_legal_mask, dtype=torch.bool, device=self.device)
        masked_logits = logits.masked_fill(~mask, -torch.inf)
        logp = F.log_softmax(masked_logits, dim=-1)
        probability = torch.softmax(masked_logits, dim=-1)
        entropy = -(probability[mask] * logp[mask]).sum()
        all_high_hidden = torch.as_tensor(
            row.active_high_hidden,
            dtype=torch.float32,
            device=self.device,
        )
        # The owner value is replayed from the stored pre-token critic sources.
        # Non-owner hidden values do not enter the owner's focal term but do
        # enter the shared set critic; store them explicitly in new rows below.
        values = self.event_critic.values(
            torch.as_tensor(
                row.active_critic_member_features,
                dtype=torch.float32,
                device=self.device,
            ),
            working_skills,
            working_ages,
            flags,
            all_high_hidden,
            torch.as_tensor(
                row.critic_global_features, dtype=torch.float32, device=self.device
            ),
            ORDINARY_BOUNDARY,
        )
        return logp[int(row.combined_action)], values[owner_index], entropy

    def complete_primitive_transition(self, team_reward: float) -> None:
        if not np.isfinite(float(team_reward)):
            raise ValueError("team reward must be finite")
        active_records = [
            record for record in self.records.values() if record.status == ACTIVE
        ]
        pending_rows: dict[str, LowTransitionRow] = {}
        for record in active_records:
            if record.active_skill is None:
                raise RuntimeError("an active lifecycle reached a primitive step without a skill")
            if record.active_gap_remaining is None:
                raise RuntimeError("active lifecycle is missing its opportunity gap")
            transition_rows = [
                row
                for row in self.low_ledger
                if row.lifecycle_key == record.lifecycle_key
                and row.membership_epoch == record.membership_epoch
                and row.physical_time == self.physical_time
                and row.reward is None
            ]
            if len(transition_rows) != 1:
                raise RuntimeError(
                    "each active lifecycle requires exactly one pending low transition"
                )
            pending_rows[record.lifecycle_key] = transition_rows[0]
        for record in active_records:
            pending_rows[record.lifecycle_key].reward = float(team_reward)
            record.skill_active_age += 1
            record.active_gap_remaining = max(int(record.active_gap_remaining) - 1, 0)
            if record.open_event_trace is not None:
                record.open_event_trace.accumulate(float(team_reward), self.gamma)
        self.physical_time += 1

    def close_terminal(self) -> None:
        """Close every active owner/low trace after the terminal primitive step."""

        for record in self.records.values():
            if record.status != ACTIVE:
                continue
            self._close_trace(
                record,
                bootstrap_value=0.0,
                boundary_kind=TERMINAL_BOUNDARY,
            )
            self._record_low_boundary(
                record,
                TERMINAL_BOUNDARY,
                bootstrap_value=0.0,
            )

    def active_skills(self) -> dict[str, int]:
        return {
            key: int(record.active_skill)
            for key, record in self.records.items()
            if record.status == ACTIVE and record.active_skill is not None
        }

    def due_frontier(self) -> tuple[str, ...]:
        return tuple(
            key
            for key, record in self.records.items()
            if record.status == ACTIVE
            and (
                record.is_genuine_join
                or record.is_rejoin
                or int(record.active_gap_remaining or 0) <= 0
            )
        )

    def low_step(
        self,
        snapshot: BoundarySnapshot,
        *,
        deterministic: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        packed, routing = self.pack_active(snapshot)
        if bool(torch.any(packed.skills < 0).item()):
            raise RuntimeError("low actor cannot run before genuine joins receive SET")
        actor_hidden_before = packed.low_actor_hidden.clone()
        critic_hidden_before = packed.low_critic_hidden.clone()
        sampling_uniforms = (
            None
            if deterministic or self.action_space_type != "discrete"
            else np.asarray(
                self.action_rng.random(len(routing.lifecycle_keys)), dtype=np.float64
            )
        )
        actions, logp, actor_hidden = self.low_actor.actor_step(
            packed.member_obs,
            packed.skills,
            packed.low_actor_hidden,
            deterministic=deterministic,
            sampling_uniforms=sampling_uniforms,
        )
        values, critic_hidden, critic_source = self.low_critic.critic_step(
            packed.critic_member_features,
            packed.skills,
            packed.env_ptr,
            packed.critic_global_features,
            packed.low_critic_hidden,
        )
        for index, key in enumerate(routing.lifecycle_keys):
            record = self.records[key]
            if any(
                row.lifecycle_key == key
                and row.membership_epoch == record.membership_epoch
                and row.physical_time == self.physical_time
                and row.reward is None
                for row in self.low_ledger
            ):
                raise RuntimeError("duplicate low transition at one physical step")
            chunk_pointer = sum(
                1
                for boundary in self.low_chunk_boundaries
                if boundary["lifecycle_key"] == key
                and boundary["membership_epoch"] == record.membership_epoch
            )
            record.low_actor_hidden = (
                actor_hidden[index].detach().cpu().numpy().astype(np.float32)
            )
            record.low_critic_hidden = (
                critic_hidden[index].detach().cpu().numpy().astype(np.float32)
            )
            action_array = actions[index].detach().cpu().numpy().reshape(-1).copy()
            self.low_ledger.append(
                LowTransitionRow(
                    lifecycle_key=key,
                    membership_epoch=record.membership_epoch,
                    policy_version=self.policy_version,
                    physical_time=self.physical_time,
                    observation=packed.member_obs[index].detach().cpu().numpy().copy(),
                    skill=int(packed.skills[index].item()),
                    action=action_array,
                    old_log_probability=float(logp[index].detach().cpu()),
                    old_value=float(values[index].detach().cpu()),
                    actor_hidden_before=actor_hidden_before[index]
                    .detach()
                    .cpu()
                    .numpy()
                    .copy(),
                    critic_hidden_before=critic_hidden_before[index]
                    .detach()
                    .cpu()
                    .numpy()
                    .copy(),
                    critic_member_features=packed.critic_member_features[index]
                    .detach()
                    .cpu()
                    .numpy()
                    .copy(),
                    active_critic_member_features=packed.critic_member_features
                    .detach()
                    .cpu()
                    .numpy()
                    .copy(),
                    active_skills=packed.skills.detach().cpu().numpy().copy(),
                    critic_global_features=packed.critic_global_features[0]
                    .detach()
                    .cpu()
                    .numpy()
                    .copy(),
                    focal_active_index=index,
                    critic_source_summary=critic_source[index]
                    .detach()
                    .cpu()
                    .numpy()
                    .copy(),
                    policy_action_uniform=(
                        None
                        if sampling_uniforms is None
                        else float(sampling_uniforms[index])
                    ),
                    environment_step_pointer=self.physical_time,
                    lifecycle_chunk_pointer=chunk_pointer,
                )
            )
        return actions, logp, values

    def truncate_policy_version(self, snapshot: BoundarySnapshot) -> None:
        values, routing = self._critic_values(snapshot, ROLLOUT_TRUNCATION)
        low_values, low_routing = self._low_critic_values(snapshot)
        value_by_key = {
            key: float(values[index].detach().cpu())
            for index, key in enumerate(routing.lifecycle_keys)
        }
        low_value_by_key = {
            key: float(low_values[index].detach().cpu())
            for index, key in enumerate(low_routing.lifecycle_keys)
        }
        for key in routing.lifecycle_keys:
            record = self.records[key]
            self._close_trace(
                record,
                bootstrap_value=value_by_key[key],
                boundary_kind=ROLLOUT_TRUNCATION,
            )
            self._record_low_boundary(
                record,
                ROLLOUT_TRUNCATION,
                bootstrap_value=low_value_by_key[key],
            )
        self.policy_version += 1
        for key in routing.lifecycle_keys:
            record = self.records[key]
            record.policy_version = self.policy_version
            record.open_event_trace = OpenEventTrace(
                start_time=self.physical_time,
                policy_version=self.policy_version,
                actor_valid=False,
                old_value=value_by_key[key],
                old_log_probability=None,
                token_ledger_index=None,
            )

    def owner_gae(self) -> np.ndarray:
        advantages = np.zeros(len(self.closed_event_rows), dtype=np.float64)
        next_advantage: dict[tuple[str, int, int], float] = {}
        for index in range(len(self.closed_event_rows) - 1, -1, -1):
            row = self.closed_event_rows[index]
            key = (row.lifecycle_key, row.membership_epoch, row.policy_version)
            delta = row.return_target - row.old_value
            carry = next_advantage.get(key, 0.0)
            continuation = 0.0 if row.boundary_kind in (
                ROLLOUT_TRUNCATION,
                TEMPORARY_BOUNDARY,
                TERMINAL_BOUNDARY,
            ) else 1.0
            advantage = delta + continuation * row.bootstrap_discount * self.gae_lambda * carry
            advantages[index] = advantage
            next_advantage[key] = advantage
        return advantages

    def low_gae(self) -> tuple[np.ndarray, np.ndarray]:
        advantages = np.zeros(len(self.low_ledger), dtype=np.float64)
        next_value: dict[tuple[str, int, int], float] = {}
        next_advantage: dict[tuple[str, int, int], float] = {}
        for index in range(len(self.low_ledger) - 1, -1, -1):
            row = self.low_ledger[index]
            if row.reward is None:
                raise RuntimeError("low GAE cannot consume an incomplete transition")
            key = (row.lifecycle_key, row.membership_epoch, row.policy_version)
            boundary = row.terminal_or_truncation_kind is not None
            if boundary:
                if row.bootstrap_value is None:
                    raise RuntimeError("closed low chunk is missing its bootstrap")
                bootstrap = float(row.bootstrap_value)
                carry = 0.0
            else:
                if key not in next_value:
                    raise RuntimeError("open low chunk must be closed before replay")
                bootstrap = next_value[key]
                carry = next_advantage[key]
            delta = float(row.reward) + self.gamma * bootstrap - float(row.old_value)
            advantage = delta + (0.0 if boundary else self.gamma * self.gae_lambda * carry)
            advantages[index] = advantage
            next_value[key] = float(row.old_value)
            next_advantage[key] = advantage
        old_values = np.asarray([row.old_value for row in self.low_ledger], dtype=np.float64)
        return advantages, advantages + old_values

    def low_recurrent_chunks(
        self, max_length: int = MAX_RECURRENT_CHUNK
    ) -> tuple[tuple[int, ...], ...]:
        limit = int(max_length)
        if limit <= 0:
            raise ValueError("recurrent chunk length must be positive")
        by_owner: dict[tuple[str, int, int], list[int]] = {}
        for index, row in enumerate(self.low_ledger):
            key = (row.lifecycle_key, row.membership_epoch, row.policy_version)
            by_owner.setdefault(key, []).append(index)
        chunks: list[tuple[int, ...]] = []
        for indices in by_owner.values():
            start = 0
            for position, row_index in enumerate(indices):
                row = self.low_ledger[row_index]
                at_boundary = row.terminal_or_truncation_kind is not None
                if at_boundary or position - start + 1 >= limit:
                    chunks.append(tuple(indices[start : position + 1]))
                    start = position + 1
            if start < len(indices):
                raise RuntimeError("low recurrent ledger contains an open chunk")
        return tuple(chunks)

    def clear_rollout_ledgers(self) -> None:
        if any(record.open_event_trace is not None for record in self.records.values()):
            raise RuntimeError("cannot clear event rollout with an open owner trace")
        self.high_ledger.clear()
        self.closed_event_rows.clear()
        self.low_ledger.clear()
        self.low_chunk_boundaries.clear()

    def architecture_state(self) -> dict[str, Any]:
        return {
            "obs_dim": self.obs_dim,
            "critic_member_dim": self.critic_member_dim,
            "critic_global_dim": self.critic_global_dim,
            "n_skills": self.n_skills,
            "action_dim": self.action_dim,
            "member_hidden_dim": self.member_hidden_dim,
            "high_hidden_dim": self.high_hidden_dim,
            "low_hidden_dim": self.low_hidden_dim,
            "skill_embedding_dim": self.skill_embedding_dim,
            "action_space_type": self.action_space_type,
            "gamma": self.gamma,
            "gae_lambda": self.gae_lambda,
            "age_reference_steps": AGE_REFERENCE_STEPS,
        }

    @staticmethod
    def _record_to_state(record: LifecycleRecord) -> dict[str, Any]:
        return deepcopy(record.__dict__)

    @staticmethod
    def _record_from_state(state: Mapping[str, Any]) -> LifecycleRecord:
        data = deepcopy(dict(state))
        trace = data.get("open_event_trace")
        if isinstance(trace, Mapping):
            data["open_event_trace"] = OpenEventTrace(**dict(trace))
        for name in ("low_actor_hidden", "low_critic_hidden", "high_hidden"):
            data[name] = np.asarray(data[name], dtype=np.float32).copy()
        return LifecycleRecord(**data)

    def checkpoint_payload(
        self,
        *,
        collector_snapshot: Mapping[str, Any],
        current_observation_state_boundary: Mapping[str, Any],
        optimizer_states: Mapping[str, Any],
        normalizer_states: Mapping[str, Any],
        pending_membership_transaction: Any = None,
    ) -> dict[str, Any]:
        collector_snapshot = deepcopy(dict(collector_snapshot))
        capability_name = collector_snapshot.get("snapshot_capability_name")
        capability_version = collector_snapshot.get("snapshot_capability_version")
        if capability_name != SNAPSHOT_CAPABILITY_NAME or int(
            capability_version or -1
        ) != SNAPSHOT_CAPABILITY_VERSION:
            raise ValueError("collector snapshot lacks the registered event capability")
        optimizer_states = deepcopy(dict(optimizer_states))
        normalizer_states = deepcopy(dict(normalizer_states))
        if set(optimizer_states) != {"high", "low"}:
            raise ValueError("event checkpoint requires exact high/low optimizer states")
        if set(normalizer_states) != {"high", "low"}:
            raise ValueError("event checkpoint requires exact high/low normalizer states")
        self.current_observation_state_boundary = deepcopy(
            dict(current_observation_state_boundary)
        )
        self.pending_membership_transaction = deepcopy(
            pending_membership_transaction
        )
        bundle = {
            "architecture_mode": self.architecture_mode,
            "event_architecture_schema_version": EVENT_ARCHITECTURE_SCHEMA_VERSION,
            "opportunity_schedule_name": OPPORTUNITY_SCHEDULE_NAME,
            "k0": OPPORTUNITY_K0,
            "snapshot_capability_name": SNAPSHOT_CAPABILITY_NAME,
            "snapshot_capability_version": SNAPSHOT_CAPABILITY_VERSION,
            "architecture_state": self.architecture_state(),
            "environment_index": self.environment_index,
            "rng_ledger": {
                "episode_id": self.rng_episode_id,
                "opportunity": {
                    "master_seed": self.opportunity_master_seed,
                    "stream_id": self.opportunity_stream_id,
                },
                "frontier_order": {
                    "master_seed": self.frontier_master_seed,
                    "stream_id": self.frontier_stream_id,
                },
                "policy_action": {
                    "master_seed": self.action_master_seed,
                    "stream_id": self.action_stream_id,
                },
            },
            "commitment_model_state": deepcopy(self.commitment_model.state_dict()),
            "event_critic_state": deepcopy(self.event_critic.state_dict()),
            "low_actor_state": deepcopy(self.low_actor.state_dict()),
            "low_critic_state": deepcopy(self.low_critic.state_dict()),
            "optimizer_states": optimizer_states,
            "normalizer_states": normalizer_states,
            "lifecycle_table_schema": 1,
            "lifecycle_records": {
                key: self._record_to_state(record) for key, record in self.records.items()
            },
            "opportunity_rng_state": deepcopy(self.opportunity_rng.bit_generator.state),
            "frontier_order_rng_state": deepcopy(self.frontier_rng.bit_generator.state),
            "policy_action_rng_state": deepcopy(self.action_rng.bit_generator.state),
            "open_event_trace_schema": 1,
            "high_ledger": deepcopy(self.high_ledger),
            "closed_event_rows": deepcopy(self.closed_event_rows),
            "low_ledger": deepcopy(self.low_ledger),
            "low_chunk_boundaries": deepcopy(self.low_chunk_boundaries),
            "policy_version": self.policy_version,
            "physical_time": self.physical_time,
            "current_observation_state_boundary": deepcopy(
                self.current_observation_state_boundary
            ),
            "collector_active_presentation": deepcopy(
                collector_snapshot.get("collector_active_presentation")
            ),
            "pending_membership_transaction": deepcopy(
                self.pending_membership_transaction
            ),
            "collector_pending_command_response_state": deepcopy(
                collector_snapshot.get("collector_pending_command_response_state")
            ),
            "worker_environment_snapshot": deepcopy(
                collector_snapshot.get("worker_environment_snapshot")
            ),
            "environment_rng_state": deepcopy(
                collector_snapshot.get("environment_rng_state")
            ),
            "collector_snapshot": collector_snapshot,
        }
        return {
            "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
            "high_controller": EVENT_CONTROLLER,
            "event_architecture": bundle,
        }

    def restore_checkpoint_payload(
        self,
        payload: Mapping[str, Any],
        *,
        collector: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        payload = dict(payload)
        if int(payload.get("checkpoint_schema_version", -1)) != CHECKPOINT_SCHEMA_VERSION:
            raise ValueError("event runtime requires checkpoint schema 3")
        if payload.get("high_controller") != EVENT_CONTROLLER:
            raise ValueError("event checkpoint controller mismatch")
        bundle = payload.get("event_architecture")
        if not isinstance(bundle, Mapping):
            raise ValueError("event checkpoint is missing event_architecture")
        required = {
            "architecture_mode",
            "event_architecture_schema_version",
            "opportunity_schedule_name",
            "k0",
            "snapshot_capability_name",
            "snapshot_capability_version",
            "architecture_state",
            "environment_index",
            "rng_ledger",
            "commitment_model_state",
            "event_critic_state",
            "low_actor_state",
            "low_critic_state",
            "optimizer_states",
            "normalizer_states",
            "lifecycle_table_schema",
            "lifecycle_records",
            "opportunity_rng_state",
            "frontier_order_rng_state",
            "policy_action_rng_state",
            "open_event_trace_schema",
            "high_ledger",
            "closed_event_rows",
            "low_ledger",
            "low_chunk_boundaries",
            "policy_version",
            "physical_time",
            "current_observation_state_boundary",
            "collector_active_presentation",
            "pending_membership_transaction",
            "collector_pending_command_response_state",
            "worker_environment_snapshot",
            "environment_rng_state",
            "collector_snapshot",
        }
        missing = sorted(required - set(bundle))
        if missing:
            raise ValueError(f"event checkpoint is missing mandatory fields: {missing}")
        if str(bundle["architecture_mode"]) != self.architecture_mode:
            raise ValueError("event checkpoint architecture mode mismatch")
        if int(bundle["event_architecture_schema_version"]) != EVENT_ARCHITECTURE_SCHEMA_VERSION:
            raise ValueError("event architecture schema mismatch")
        if bundle["opportunity_schedule_name"] != OPPORTUNITY_SCHEDULE_NAME or int(
            bundle["k0"]
        ) != OPPORTUNITY_K0:
            raise ValueError("event opportunity schedule mismatch")
        if dict(bundle["architecture_state"]) != self.architecture_state():
            raise ValueError("event checkpoint architecture dimensions mismatch")
        if int(bundle["environment_index"]) != self.environment_index:
            raise ValueError("event checkpoint runtime environment index mismatch")
        rng_ledger = dict(bundle["rng_ledger"])
        if set(rng_ledger) != {
            "episode_id", "opportunity", "frontier_order", "policy_action"
        }:
            raise ValueError("event checkpoint RNG ledger schema mismatch")
        for name in ("opportunity", "frontier_order", "policy_action"):
            if set(dict(rng_ledger[name])) != {"master_seed", "stream_id"}:
                raise ValueError("event checkpoint RNG ledger stream mismatch")
        for name in (
            "opportunity_rng_state",
            "frontier_order_rng_state",
            "policy_action_rng_state",
        ):
            state = bundle[name]
            if not isinstance(state, Mapping) or state.get("bit_generator") != "PCG64":
                raise ValueError("event checkpoint requires exact PCG64 RNG state")
        if bundle["snapshot_capability_name"] != SNAPSHOT_CAPABILITY_NAME or int(
            bundle["snapshot_capability_version"]
        ) != SNAPSHOT_CAPABILITY_VERSION:
            raise ValueError("event snapshot capability mismatch")
        if int(bundle["lifecycle_table_schema"]) != 1 or int(
            bundle["open_event_trace_schema"]
        ) != 1:
            raise ValueError("event runtime ledger schema mismatch")
        if set(dict(bundle["optimizer_states"])) != {"high", "low"}:
            raise ValueError("event checkpoint optimizer state mismatch")
        if set(dict(bundle["normalizer_states"])) != {"high", "low"}:
            raise ValueError("event checkpoint normalizer state mismatch")

        self.commitment_model.load_state_dict(bundle["commitment_model_state"], strict=True)
        self.event_critic.load_state_dict(bundle["event_critic_state"], strict=True)
        self.low_actor.load_state_dict(bundle["low_actor_state"], strict=True)
        self.low_critic.load_state_dict(bundle["low_critic_state"], strict=True)
        self.rng_episode_id = int(rng_ledger["episode_id"])
        self.opportunity_master_seed = int(rng_ledger["opportunity"]["master_seed"])
        self.opportunity_stream_id = int(rng_ledger["opportunity"]["stream_id"])
        self.frontier_master_seed = int(rng_ledger["frontier_order"]["master_seed"])
        self.frontier_stream_id = int(rng_ledger["frontier_order"]["stream_id"])
        self.action_master_seed = int(rng_ledger["policy_action"]["master_seed"])
        self.action_stream_id = int(rng_ledger["policy_action"]["stream_id"])
        self.records = {
            str(key): self._record_from_state(state)
            for key, state in dict(bundle["lifecycle_records"]).items()
        }
        self.opportunity_rng.bit_generator.state = deepcopy(
            bundle["opportunity_rng_state"]
        )
        self.frontier_rng.bit_generator.state = deepcopy(
            bundle["frontier_order_rng_state"]
        )
        self.action_rng.bit_generator.state = deepcopy(bundle["policy_action_rng_state"])
        self.high_ledger = deepcopy(list(bundle["high_ledger"]))
        self.closed_event_rows = deepcopy(list(bundle["closed_event_rows"]))
        self.low_ledger = deepcopy(list(bundle["low_ledger"]))
        self.low_chunk_boundaries = deepcopy(list(bundle["low_chunk_boundaries"]))
        self.policy_version = int(bundle["policy_version"])
        self.physical_time = int(bundle["physical_time"])
        self.current_observation_state_boundary = deepcopy(
            dict(bundle["current_observation_state_boundary"])
        )
        self.pending_membership_transaction = deepcopy(
            bundle["pending_membership_transaction"]
        )
        collector.restore_event_runtime(deepcopy(bundle["collector_snapshot"]))
        return deepcopy(dict(bundle["optimizer_states"])), deepcopy(
            dict(bundle["normalizer_states"])
        )


def _event_checkpoint_header(core: VariableRosterEventCore) -> dict[str, Any]:
    return {
        "architecture_mode": core.architecture_mode,
        "event_architecture_schema_version": EVENT_ARCHITECTURE_SCHEMA_VERSION,
        "opportunity_schedule_name": OPPORTUNITY_SCHEDULE_NAME,
        "k0": OPPORTUNITY_K0,
        "snapshot_capability_name": SNAPSHOT_CAPABILITY_NAME,
        "snapshot_capability_version": SNAPSHOT_CAPABILITY_VERSION,
        "architecture_state": core.architecture_state(),
    }


def _validate_shared_vector_cores(
    model_owner: VariableRosterEventCore,
    cores: Sequence[VariableRosterEventCore],
) -> tuple[VariableRosterEventCore, ...]:
    rows = tuple(cores)
    if not rows:
        raise ValueError("vector event checkpoint requires at least one runtime")
    if any(core.architecture_state() != model_owner.architecture_state() for core in rows):
        raise ValueError("vector event checkpoint architecture mismatch")
    if any(core.architecture_mode != model_owner.architecture_mode for core in rows):
        raise ValueError("vector event checkpoint mode mismatch")
    if tuple(core.environment_index for core in rows) != tuple(range(len(rows))):
        raise ValueError("vector event checkpoint environment indices are not canonical")
    for core in rows:
        if (
            core.commitment_model is not model_owner.commitment_model
            or core.event_critic is not model_owner.event_critic
            or core.low_actor is not model_owner.low_actor
            or core.low_critic is not model_owner.low_critic
        ):
            raise ValueError("vector event runtimes do not share one parameter graph")
    return rows


def vector_event_checkpoint_payload(
    *,
    model_owner: VariableRosterEventCore,
    cores: Sequence[VariableRosterEventCore],
    collector_snapshot: Mapping[str, Any],
    current_boundaries: Sequence[Mapping[str, Any]],
    optimizer_states: Mapping[str, Any],
    normalizer_states: Mapping[str, Any],
    counters: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one strict schema-3 checkpoint for a complete vector boundary."""

    rows = _validate_shared_vector_cores(model_owner, cores)
    boundaries = tuple(deepcopy(dict(value)) for value in current_boundaries)
    if len(boundaries) != len(rows):
        raise ValueError("vector event checkpoint boundary count mismatch")
    optimizer_value = deepcopy(dict(optimizer_states))
    normalizer_value = deepcopy(dict(normalizer_states))
    if set(optimizer_value) != {"high", "low"}:
        raise ValueError("vector event checkpoint requires high/low optimizers")
    if set(normalizer_value) != {"high", "low"}:
        raise ValueError("vector event checkpoint requires high/low normalizers")
    counter_value = deepcopy(dict(counters))
    required_counters = {
        "total_steps",
        "update_idx",
        "high_optimizer_steps",
        "low_optimizer_steps",
        "next_episode_id",
        "intrinsic_applied_count",
    }
    if set(counter_value) != required_counters:
        raise ValueError("vector event checkpoint counter schema mismatch")
    snapshot_value = deepcopy(dict(collector_snapshot))
    if snapshot_value.get("snapshot_capability_name") != SNAPSHOT_CAPABILITY_NAME or int(
        snapshot_value.get("snapshot_capability_version", -1)
    ) != SNAPSHOT_CAPABILITY_VERSION:
        raise ValueError("vector collector snapshot capability mismatch")
    runtime_payloads = []
    for core, boundary in zip(rows, boundaries):
        full_bundle = core.checkpoint_payload(
            collector_snapshot=snapshot_value,
            current_observation_state_boundary=boundary,
            optimizer_states=optimizer_value,
            normalizer_states=normalizer_value,
            pending_membership_transaction=core.pending_membership_transaction,
        )["event_architecture"]
        runtime_payloads.append(
            {name: deepcopy(full_bundle[name]) for name in VECTOR_RUNTIME_FIELDS}
        )
    bundle = {
        **_event_checkpoint_header(model_owner),
        "vector_checkpoint_schema_version": VECTOR_CHECKPOINT_SCHEMA_VERSION,
        "num_envs": len(rows),
        "runtime_state_absent_for_fresh_eval": False,
        "commitment_model_state": deepcopy(model_owner.commitment_model.state_dict()),
        "event_critic_state": deepcopy(model_owner.event_critic.state_dict()),
        "low_actor_state": deepcopy(model_owner.low_actor.state_dict()),
        "low_critic_state": deepcopy(model_owner.low_critic.state_dict()),
        "runtime_payloads": runtime_payloads,
        "collector_snapshot": snapshot_value,
        "optimizer_states": optimizer_value,
        "normalizer_states": normalizer_value,
        "counters": counter_value,
    }
    return {
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "high_controller": EVENT_CONTROLLER,
        "event_architecture": bundle,
    }


class _ValidatedNoOpCollector:
    def restore_event_runtime(self, snapshot: Mapping[str, Any]) -> None:
        value = dict(snapshot)
        if value.get("snapshot_capability_name") != SNAPSHOT_CAPABILITY_NAME or int(
            value.get("snapshot_capability_version", -1)
        ) != SNAPSHOT_CAPABILITY_VERSION:
            raise ValueError("runtime payload collector capability mismatch")


def restore_vector_event_checkpoint(
    payload: Mapping[str, Any],
    *,
    model_owner: VariableRosterEventCore,
    cores: Sequence[VariableRosterEventCore],
    collector: Any,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Strictly restore one complete vector event checkpoint."""

    value = dict(payload)
    if int(value.get("checkpoint_schema_version", -1)) != CHECKPOINT_SCHEMA_VERSION:
        raise ValueError("vector event resume requires checkpoint schema 3")
    if value.get("high_controller") != EVENT_CONTROLLER:
        raise ValueError("vector event checkpoint controller mismatch")
    bundle = value.get("event_architecture")
    if not isinstance(bundle, Mapping):
        raise ValueError("vector event checkpoint is missing event_architecture")
    required = {
        *set(_event_checkpoint_header(model_owner)),
        "vector_checkpoint_schema_version",
        "num_envs",
        "runtime_state_absent_for_fresh_eval",
        "commitment_model_state",
        "event_critic_state",
        "low_actor_state",
        "low_critic_state",
        "runtime_payloads",
        "collector_snapshot",
        "optimizer_states",
        "normalizer_states",
        "counters",
    }
    missing = sorted(required - set(bundle))
    if missing:
        raise ValueError(f"vector event checkpoint is missing mandatory fields: {missing}")
    if bool(bundle["runtime_state_absent_for_fresh_eval"]):
        raise ValueError("model-only fresh-evaluation checkpoint cannot resume live state")
    header = _event_checkpoint_header(model_owner)
    for name, expected in header.items():
        actual = bundle[name]
        mismatch = (
            dict(actual) != dict(expected)
            if isinstance(expected, Mapping)
            else actual != expected
        )
        if mismatch:
            raise ValueError(f"vector event checkpoint header mismatch: {name}")
    rows = _validate_shared_vector_cores(model_owner, cores)
    if int(bundle["vector_checkpoint_schema_version"]) != VECTOR_CHECKPOINT_SCHEMA_VERSION:
        raise ValueError("vector event checkpoint schema mismatch")
    if int(bundle["num_envs"]) != len(rows):
        raise ValueError("vector event checkpoint environment count mismatch")
    runtime_payloads = list(bundle["runtime_payloads"])
    if len(runtime_payloads) != len(rows):
        raise ValueError("vector event runtime payload count mismatch")
    collector_snapshot = deepcopy(dict(bundle["collector_snapshot"]))
    if collector_snapshot.get("snapshot_capability_name") != SNAPSHOT_CAPABILITY_NAME or int(
        collector_snapshot.get("snapshot_capability_version", -1)
    ) != SNAPSHOT_CAPABILITY_VERSION:
        raise ValueError("vector collector snapshot capability mismatch")
    first_optimizer: dict[str, Any] | None = None
    first_normalizer: dict[str, Any] | None = None
    for index, (core, runtime_payload) in enumerate(zip(rows, runtime_payloads)):
        if not isinstance(runtime_payload, Mapping) or set(runtime_payload) != VECTOR_RUNTIME_FIELDS:
            raise ValueError("vector event runtime field schema mismatch")
        runtime_bundle = {
            **header,
            "commitment_model_state": bundle["commitment_model_state"],
            "event_critic_state": bundle["event_critic_state"],
            "low_actor_state": bundle["low_actor_state"],
            "low_critic_state": bundle["low_critic_state"],
            "optimizer_states": bundle["optimizer_states"],
            "normalizer_states": bundle["normalizer_states"],
            **deepcopy(dict(runtime_payload)),
            "collector_active_presentation": deepcopy(
                collector_snapshot.get("collector_active_presentation")
            ),
            "collector_pending_command_response_state": deepcopy(
                collector_snapshot.get("collector_pending_command_response_state")
            ),
            "worker_environment_snapshot": deepcopy(
                collector_snapshot.get("worker_environment_snapshot")
            ),
            "environment_rng_state": deepcopy(
                collector_snapshot.get("environment_rng_state")
            ),
            "collector_snapshot": collector_snapshot,
        }
        optimizers, normalizers = core.restore_checkpoint_payload(
            {
                "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
                "high_controller": EVENT_CONTROLLER,
                "event_architecture": runtime_bundle,
            },
            collector=collector if index == 0 else _ValidatedNoOpCollector(),
        )
        if first_optimizer is None:
            first_optimizer = optimizers
            first_normalizer = normalizers
    assert first_optimizer is not None and first_normalizer is not None
    if set(first_optimizer) != {"high", "low"} or set(first_normalizer) != {
        "high",
        "low",
    }:
        raise ValueError("vector event restored optimizer/normalizer schema mismatch")
    counters = deepcopy(dict(bundle["counters"]))
    if set(counters) != {
        "total_steps",
        "update_idx",
        "high_optimizer_steps",
        "low_optimizer_steps",
        "next_episode_id",
        "intrinsic_applied_count",
    }:
        raise ValueError("vector event restored counter schema mismatch")
    return first_optimizer, first_normalizer, counters


def event_model_only_checkpoint_payload(
    *,
    model_owner: VariableRosterEventCore,
    normalizer_states: Mapping[str, Any],
    total_steps: int,
    update_idx: int,
) -> dict[str, Any]:
    normalizers = deepcopy(dict(normalizer_states))
    if set(normalizers) != {"high", "low"}:
        raise ValueError("fresh evaluation requires exact high/low normalizers")
    bundle = {
        **_event_checkpoint_header(model_owner),
        "runtime_state_absent_for_fresh_eval": True,
        "commitment_model_state": deepcopy(model_owner.commitment_model.state_dict()),
        "event_critic_state": deepcopy(model_owner.event_critic.state_dict()),
        "low_actor_state": deepcopy(model_owner.low_actor.state_dict()),
        "low_critic_state": deepcopy(model_owner.low_critic.state_dict()),
        "normalizer_states": normalizers,
        "total_steps": int(total_steps),
        "update_idx": int(update_idx),
    }
    return {
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "high_controller": EVENT_CONTROLLER,
        "event_architecture": bundle,
    }


def restore_event_model_only_checkpoint(
    payload: Mapping[str, Any],
    *,
    model_owner: VariableRosterEventCore,
) -> tuple[dict[str, Any], int, int]:
    value = dict(payload)
    if int(value.get("checkpoint_schema_version", -1)) != CHECKPOINT_SCHEMA_VERSION or value.get(
        "high_controller"
    ) != EVENT_CONTROLLER:
        raise ValueError("fresh evaluation requires an event schema-3 checkpoint")
    bundle = value.get("event_architecture")
    if not isinstance(bundle, Mapping):
        raise ValueError("fresh evaluation checkpoint is missing event_architecture")
    required = {
        *set(_event_checkpoint_header(model_owner)),
        "runtime_state_absent_for_fresh_eval",
        "commitment_model_state",
        "event_critic_state",
        "low_actor_state",
        "low_critic_state",
        "normalizer_states",
        "total_steps",
        "update_idx",
    }
    missing = sorted(required - set(bundle))
    if missing:
        raise ValueError(f"fresh evaluation checkpoint is missing fields: {missing}")
    if not bool(bundle["runtime_state_absent_for_fresh_eval"]):
        raise ValueError("fresh evaluation checkpoint must explicitly omit runtime state")
    header = _event_checkpoint_header(model_owner)
    for name, expected in header.items():
        actual = bundle[name]
        mismatch = (
            dict(actual) != dict(expected)
            if isinstance(expected, Mapping)
            else actual != expected
        )
        if mismatch:
            raise ValueError(f"fresh evaluation checkpoint header mismatch: {name}")
    model_owner.commitment_model.load_state_dict(bundle["commitment_model_state"], strict=True)
    model_owner.event_critic.load_state_dict(bundle["event_critic_state"], strict=True)
    model_owner.low_actor.load_state_dict(bundle["low_actor_state"], strict=True)
    model_owner.low_critic.load_state_dict(bundle["low_critic_state"], strict=True)
    normalizers = deepcopy(dict(bundle["normalizer_states"]))
    if set(normalizers) != {"high", "low"}:
        raise ValueError("fresh evaluation normalizer schema mismatch")
    return normalizers, int(bundle["total_steps"]), int(bundle["update_idx"])


def _normalize_advantages(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        return values
    return (values - values.mean()) / (values.std() + 1e-8)


def event_ppo_losses(cores: Iterable[VariableRosterEventCore]) -> EventPPOLosses:
    """Differentiably replay one shared F0/F1 high+low on-policy update."""

    core_rows = tuple(cores)
    if not core_rows:
        raise ValueError("event PPO requires at least one runtime core")
    owner = core_rows[0]
    if any(core.commitment_model is not owner.commitment_model for core in core_rows):
        raise ValueError("vector event runtimes must share one parameter graph")

    high_entries: list[tuple[VariableRosterEventCore, ClosedEventRow, EventTokenRow, float]] = []
    for core in core_rows:
        advantages = core.owner_gae()
        for index, closed in enumerate(core.closed_event_rows):
            if not closed.actor_valid:
                continue
            if closed.token_ledger_index is None:
                raise RuntimeError("actor-valid owner row is missing its event token")
            token = core.high_ledger[int(closed.token_ledger_index)]
            high_entries.append((core, closed, token, float(advantages[index])))
    if not high_entries:
        raise RuntimeError("event PPO has no actor-valid high rows")
    high_norm = _normalize_advantages(
        np.asarray([entry[3] for entry in high_entries], dtype=np.float64)
    )
    high_policy_terms: list[torch.Tensor] = []
    high_value_terms: list[torch.Tensor] = []
    high_entropies: list[torch.Tensor] = []
    high_logp_max_error = 0.0
    high_value_max_error = 0.0
    for normalized_advantage, (core, closed, token, raw_advantage) in zip(
        high_norm, high_entries
    ):
        logp, value, entropy = core.replay_event_token(token)
        old_logp = torch.tensor(
            float(token.old_token_log_probability), dtype=logp.dtype, device=logp.device
        )
        old_value = torch.tensor(float(closed.old_value), dtype=value.dtype, device=value.device)
        high_logp_max_error = max(
            high_logp_max_error,
            float(torch.abs(logp.detach() - old_logp).cpu()),
        )
        high_value_max_error = max(
            high_value_max_error,
            float(torch.abs(value.detach() - old_value).cpu()),
        )
        target = torch.tensor(
            float(closed.old_value + raw_advantage), dtype=value.dtype, device=value.device
        )
        advantage = torch.tensor(float(normalized_advantage), dtype=logp.dtype, device=logp.device)
        ratio = torch.exp(logp - old_logp)
        high_policy_terms.append(
            -torch.minimum(
                ratio * advantage,
                torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * advantage,
            )
        )
        clipped_value = old_value + torch.clamp(value - old_value, -VALUE_CLIP, VALUE_CLIP)
        high_value_terms.append(
            torch.maximum(torch.square(value - target), torch.square(clipped_value - target))
        )
        high_entropies.append(entropy)

    low_advantages: list[float] = []
    low_returns: dict[tuple[int, int], float] = {}
    low_advantage_by_row: dict[tuple[int, int], float] = {}
    low_chunks: list[tuple[VariableRosterEventCore, tuple[int, ...]]] = []
    for core_index, core in enumerate(core_rows):
        advantages, returns = core.low_gae()
        for row_index, (advantage, target) in enumerate(zip(advantages, returns)):
            low_advantages.append(float(advantage))
            low_advantage_by_row[(core_index, row_index)] = float(advantage)
            low_returns[(core_index, row_index)] = float(target)
        low_chunks.extend((core, chunk) for chunk in core.low_recurrent_chunks())
    if not low_advantages:
        raise RuntimeError("event PPO has no low transitions")
    normalized_low = _normalize_advantages(np.asarray(low_advantages, dtype=np.float64))
    normalized_by_row: dict[tuple[int, int], float] = {}
    cursor = 0
    for core_index, core in enumerate(core_rows):
        for row_index in range(len(core.low_ledger)):
            normalized_by_row[(core_index, row_index)] = float(normalized_low[cursor])
            cursor += 1

    low_policy_terms: list[torch.Tensor] = []
    low_value_terms: list[torch.Tensor] = []
    low_entropy_terms: list[torch.Tensor] = []
    low_logp_max_error = 0.0
    low_value_max_error = 0.0
    core_index_by_id = {id(core): index for index, core in enumerate(core_rows)}
    for core, chunk in low_chunks:
        rows = [core.low_ledger[index] for index in chunk]
        observations = torch.as_tensor(
            np.stack([row.observation for row in rows])[:, None, :],
            dtype=torch.float32,
            device=core.device,
        )
        skills = torch.as_tensor(
            [[row.skill] for row in rows], dtype=torch.long, device=core.device
        )
        actions = torch.as_tensor(
            np.stack([row.action for row in rows])[:, None, ...],
            device=core.device,
        )
        if core.action_space_type == "discrete":
            actions = actions.reshape(len(rows), 1).long()
        valid = torch.ones(len(rows), 1, dtype=torch.float32, device=core.device)
        reset = torch.ones_like(valid)
        actor_logp, entropy, _actor_hidden = core.low_actor.actor_replay_with_entropy(
            observations,
            skills,
            actions,
            torch.as_tensor(rows[0].actor_hidden_before, device=core.device).reshape(1, -1),
            valid,
            reset,
        )
        max_active = max(len(row.active_skills) for row in rows)
        raw_members = np.zeros(
            (len(rows), 1, max_active, core.critic_member_dim), dtype=np.float32
        )
        raw_skills = np.zeros((len(rows), 1, max_active), dtype=np.int64)
        raw_masks = np.zeros((len(rows), 1, max_active), dtype=np.bool_)
        focal_indices = np.zeros((len(rows), 1), dtype=np.int64)
        raw_globals = np.zeros(
            (len(rows), 1, core.critic_global_dim), dtype=np.float32
        )
        for position, row in enumerate(rows):
            active_count = len(row.active_skills)
            if row.active_critic_member_features.shape != (
                active_count,
                core.critic_member_dim,
            ):
                raise RuntimeError("stored raw active critic rows have the wrong shape")
            raw_members[position, 0, :active_count] = row.active_critic_member_features
            raw_skills[position, 0, :active_count] = row.active_skills
            raw_masks[position, 0, :active_count] = True
            focal_indices[position, 0] = int(row.focal_active_index)
            raw_globals[position, 0] = row.critic_global_features
        values, _critic_hidden, _current_sources = (
            core.low_critic.critic_replay_from_active_sets(
                torch.as_tensor(raw_members, device=core.device),
                torch.as_tensor(raw_skills, device=core.device),
                torch.as_tensor(raw_masks, device=core.device),
                torch.as_tensor(focal_indices, device=core.device),
                torch.as_tensor(raw_globals, device=core.device),
                torch.as_tensor(rows[0].critic_hidden_before, device=core.device).reshape(1, -1),
                valid,
                reset,
            )
        )
        core_index = core_index_by_id[id(core)]
        for position, row_index in enumerate(chunk):
            current_logp = actor_logp[position, 0]
            current_value = values[position, 0]
            row = rows[position]
            old_logp = torch.tensor(row.old_log_probability, device=core.device)
            old_value = torch.tensor(row.old_value, device=core.device)
            low_logp_max_error = max(
                low_logp_max_error,
                float(torch.abs(current_logp.detach() - old_logp).cpu()),
            )
            low_value_max_error = max(
                low_value_max_error,
                float(torch.abs(current_value.detach() - old_value).cpu()),
            )
            advantage = torch.tensor(
                normalized_by_row[(core_index, row_index)], device=core.device
            )
            target = torch.tensor(low_returns[(core_index, row_index)], device=core.device)
            ratio = torch.exp(current_logp - old_logp)
            low_policy_terms.append(
                -torch.minimum(
                    ratio * advantage,
                    torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * advantage,
                )
            )
            clipped_value = old_value + torch.clamp(
                current_value - old_value, -VALUE_CLIP, VALUE_CLIP
            )
            low_value_terms.append(
                torch.maximum(
                    torch.square(current_value - target),
                    torch.square(clipped_value - target),
                )
            )
        low_entropy_terms.extend([entropy] * len(rows))

    high_policy = torch.stack(high_policy_terms).mean()
    high_value = torch.stack(high_value_terms).mean()
    high_entropy = torch.stack(high_entropies).mean()
    low_policy = torch.stack(low_policy_terms).mean()
    low_value = torch.stack(low_value_terms).mean()
    low_entropy = torch.stack(low_entropy_terms).mean()
    return EventPPOLosses(
        high_loss=high_policy + VALUE_COEFFICIENT * high_value - ENTROPY_COEFFICIENT * high_entropy,
        low_loss=low_policy + VALUE_COEFFICIENT * low_value - ENTROPY_COEFFICIENT * low_entropy,
        high_policy_loss=high_policy,
        high_value_loss=high_value,
        low_policy_loss=low_policy,
        low_value_loss=low_value,
        high_entropy=high_entropy,
        low_entropy=low_entropy,
        high_rows=len(high_entries),
        low_rows=len(low_advantages),
        high_logp_max_error=high_logp_max_error,
        high_value_max_error=high_value_max_error,
        low_logp_max_error=low_logp_max_error,
        low_value_max_error=low_value_max_error,
    )


def apply_event_ppo_update(
    cores: Iterable[VariableRosterEventCore],
    *,
    high_optimizer: torch.optim.Optimizer,
    low_optimizer: torch.optim.Optimizer,
) -> dict[str, float]:
    """Apply one shared high/low PPO pass; callers own the exposure schedule."""

    core_rows = tuple(cores)
    losses = event_ppo_losses(core_rows)
    owner = core_rows[0]
    high_parameters = tuple(owner.commitment_model.parameters()) + tuple(
        owner.event_critic.parameters()
    )
    low_parameters = tuple(owner.low_actor.parameters()) + tuple(
        owner.low_critic.parameters()
    )
    high_optimizer.zero_grad(set_to_none=True)
    losses.high_loss.backward()
    high_gradient = torch.nn.utils.clip_grad_norm_(high_parameters, GRADIENT_CLIP)
    high_optimizer.step()
    low_optimizer.zero_grad(set_to_none=True)
    losses.low_loss.backward()
    low_gradient = torch.nn.utils.clip_grad_norm_(low_parameters, GRADIENT_CLIP)
    low_optimizer.step()
    return {
        "high_loss": float(losses.high_loss.detach().cpu()),
        "low_loss": float(losses.low_loss.detach().cpu()),
        "high_policy_loss": float(losses.high_policy_loss.detach().cpu()),
        "high_value_loss": float(losses.high_value_loss.detach().cpu()),
        "low_policy_loss": float(losses.low_policy_loss.detach().cpu()),
        "low_value_loss": float(losses.low_value_loss.detach().cpu()),
        "high_entropy": float(losses.high_entropy.detach().cpu()),
        "low_entropy": float(losses.low_entropy.detach().cpu()),
        "high_gradient_norm": float(torch.as_tensor(high_gradient).detach().cpu()),
        "low_gradient_norm": float(torch.as_tensor(low_gradient).detach().cpu()),
        "high_rows": float(losses.high_rows),
        "low_rows": float(losses.low_rows),
        "high_logp_max_error": float(losses.high_logp_max_error),
        "high_value_max_error": float(losses.high_value_max_error),
        "low_logp_max_error": float(losses.low_logp_max_error),
        "low_value_max_error": float(losses.low_value_max_error),
    }


def centered_logits(logits: torch.Tensor, support: torch.Tensor) -> torch.Tensor:
    support = support.to(dtype=torch.bool, device=logits.device)
    selected = logits[support]
    if selected.numel() < 2:
        raise ValueError("common support must contain at least two actions")
    return selected - selected.mean()


def validate_event_runtime_configuration(config: Any) -> dict[str, Any]:
    controller = str(getattr(config, "high_controller", ""))
    mode = str(getattr(config, "event_architecture_mode", "")).lower()
    schema = int(getattr(config, "event_architecture_schema_version", -1))
    schedule = str(getattr(config, "event_opportunity_schedule", ""))
    if controller != EVENT_CONTROLLER:
        raise ValueError("event runtime configuration has the wrong controller")
    if mode not in EVENT_MODES:
        raise ValueError("event runtime requires event_architecture_mode=f0|f1")
    if schema != EVENT_ARCHITECTURE_SCHEMA_VERSION:
        raise ValueError("event runtime requires architecture schema version 1")
    if schedule != OPPORTUNITY_SCHEDULE_NAME:
        raise ValueError("event runtime requires uniform_active_gap_v1")
    return {
        "high_controller": controller,
        "event_architecture_mode": mode,
        "event_architecture_schema_version": schema,
        "event_opportunity_schedule": schedule,
    }


def assert_deterministic_trace_boundary(config: Any) -> None:
    """Fail before real collector construction under the current authorization."""

    validate_event_runtime_configuration(config)
    raise RuntimeError(
        "variable_roster_event currently stops at the authorized deterministic "
        "transaction trace; real environment construction and training are not authorized"
    )
