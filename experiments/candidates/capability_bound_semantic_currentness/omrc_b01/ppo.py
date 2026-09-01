"""Full-episode recurrent PPO substrate for CBSC-OMRC-B01."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

import torch
from torch import nn

from .model import (
    ACTION_COUNT,
    INPUT_DIM,
    OBJECT_ID,
    REFRESH,
    SAFE_FALLBACK,
    SERVE,
    WAIT,
    AddressU64,
    CommonRecurrentActorCritic,
    ModelValidationError,
    _default_u64,
)


EPISODE_TRANSITIONS = 152
OPPORTUNITIES = 24
EPISODES_PER_ROLLOUT = 8
DECISIONS_PER_ROLLOUT = EPISODES_PER_ROLLOUT * OPPORTUNITIES
PPO_EPOCHS = 4
EPISODES_PER_MINIBATCH = 2
MINIBATCHES_PER_EPOCH = 4
ADAM_STEPS_PER_UPDATE = PPO_EPOCHS * MINIBATCHES_PER_EPOCH


class PPOValidationError(ValueError):
    """Raised when a rollout or update violates the frozen PPO contract."""


@dataclass(frozen=True)
class PPOConfig:
    gamma: float = 1.0
    gae_lambda: float = 0.95
    clip: float = 0.20
    value_coefficient: float = 0.50
    entropy_coefficient: float = 0.01
    learning_rate: float = 3e-4
    adam_betas: tuple[float, float] = (0.9, 0.999)
    adam_epsilon: float = 1e-8
    weight_decay: float = 0.0
    gradient_norm_cap: float = 0.5
    advantage_epsilon: float = 1e-8
    epochs: int = PPO_EPOCHS
    episodes_per_minibatch: int = EPISODES_PER_MINIBATCH

    def __post_init__(self) -> None:
        expected = (
            self.gamma == 1.0
            and self.gae_lambda == 0.95
            and self.clip == 0.20
            and self.value_coefficient == 0.50
            and self.entropy_coefficient == 0.01
            and self.learning_rate == 3e-4
            and self.adam_betas == (0.9, 0.999)
            and self.adam_epsilon == 1e-8
            and self.weight_decay == 0.0
            and self.gradient_norm_cap == 0.5
            and self.advantage_epsilon == 1e-8
            and self.epochs == PPO_EPOCHS
            and self.episodes_per_minibatch == EPISODES_PER_MINIBATCH
        )
        if not expected:
            raise PPOValidationError("PPOConfig must equal the frozen B01 configuration")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "gamma": self.gamma,
            "gae_lambda": self.gae_lambda,
            "clip": self.clip,
            "value_coefficient": self.value_coefficient,
            "entropy_coefficient": self.entropy_coefficient,
            "learning_rate": self.learning_rate,
            "adam_betas": list(self.adam_betas),
            "adam_epsilon": self.adam_epsilon,
            "weight_decay": self.weight_decay,
            "gradient_norm_cap": self.gradient_norm_cap,
            "advantage_epsilon": self.advantage_epsilon,
            "epochs": self.epochs,
            "episodes_per_minibatch": self.episodes_per_minibatch,
        }


@dataclass(frozen=True)
class EpisodeRollout:
    """Eight complete 152-transition episodes; no recurrent state is stored."""

    observations: torch.Tensor
    actions: torch.Tensor
    rewards: torch.Tensor
    terminated: torch.Tensor
    decision_mask: torch.Tensor
    old_log_probabilities: torch.Tensor
    old_values: torch.Tensor
    episode_ids: torch.Tensor

    def __post_init__(self) -> None:
        shape = (EPISODES_PER_ROLLOUT, EPISODE_TRANSITIONS)
        if (
            not isinstance(self.observations, torch.Tensor)
            or self.observations.shape != (*shape, INPUT_DIM)
            or self.observations.dtype != torch.float32
        ):
            raise PPOValidationError("observations must have shape [8,152,168] in FP32")
        specifications = (
            ("actions", self.actions, shape, torch.int64),
            ("rewards", self.rewards, shape, torch.float32),
            ("terminated", self.terminated, shape, torch.bool),
            ("decision_mask", self.decision_mask, shape, torch.bool),
            ("old_log_probabilities", self.old_log_probabilities, shape, torch.float32),
            ("old_values", self.old_values, shape, torch.float32),
            ("episode_ids", self.episode_ids, (EPISODES_PER_ROLLOUT,), torch.int64),
        )
        for name, value, expected_shape, dtype in specifications:
            if (
                not isinstance(value, torch.Tensor)
                or value.shape != expected_shape
                or value.dtype != dtype
                or value.device != self.observations.device
            ):
                raise PPOValidationError(
                    f"{name} must have shape {expected_shape}, dtype {dtype}, and matching device"
                )
        for name in ("observations", "rewards", "old_log_probabilities", "old_values"):
            if not torch.isfinite(getattr(self, name)).all().item():
                raise PPOValidationError(f"{name} contains nonfinite values")
        expected_decisions = torch.zeros(shape, dtype=torch.bool, device=self.observations.device)
        expected_decisions[:, 12::6] = True
        if not torch.equal(self.decision_mask, expected_decisions):
            raise PPOValidationError("decision mask must identify exactly 24 frozen clock rows")
        if not torch.all(self.actions[~self.decision_mask] == WAIT).item():
            raise PPOValidationError("nondecision transitions must use forced WAIT")
        decision_actions = self.actions[self.decision_mask]
        if not torch.all(
            (decision_actions >= SERVE) & (decision_actions <= SAFE_FALLBACK)
        ).item():
            raise PPOValidationError("decision transitions require one of the three scientific actions")
        expected_terminal = torch.zeros(shape, dtype=torch.bool, device=self.observations.device)
        expected_terminal[:, -1] = True
        if not torch.equal(self.terminated, expected_terminal):
            raise PPOValidationError("each complete episode must terminate only at transition 151")
        if len(set(self.episode_ids.detach().cpu().tolist())) != EPISODES_PER_ROLLOUT:
            raise PPOValidationError("rollout episode IDs must be unique")


@dataclass(frozen=True)
class AdvantageBatch:
    advantages: torch.Tensor
    decision_advantages: torch.Tensor
    value_targets: torch.Tensor


@dataclass
class PPOCounters:
    rollout_updates: int = 0
    adam_steps: int = 0
    train_episodes: int = 0
    train_transitions: int = 0
    train_decisions: int = 0

    def validate(self) -> None:
        values = tuple(vars(self).values())
        if any(type(value) is not int or value < 0 for value in values):
            raise PPOValidationError("PPO counters must be nonnegative integers")
        if self.adam_steps != self.rollout_updates * ADAM_STEPS_PER_UPDATE:
            raise PPOValidationError("Adam step count is inconsistent with rollout updates")
        if self.train_episodes != self.rollout_updates * EPISODES_PER_ROLLOUT:
            raise PPOValidationError("episode count is inconsistent with rollout updates")
        if self.train_transitions != self.train_episodes * EPISODE_TRANSITIONS:
            raise PPOValidationError("transition count is inconsistent with episode count")
        if self.train_decisions != self.train_episodes * OPPORTUNITIES:
            raise PPOValidationError("decision count is inconsistent with episode count")


@dataclass(frozen=True)
class PPOLossRecord:
    ppo_epoch: int
    minibatch: int
    episode_ids: tuple[int, int]
    actor_loss: float
    value_loss: float
    entropy: float
    total_loss: float
    gradient_norm: float


def compute_gae(rollout: EpisodeRollout, config: PPOConfig | None = None) -> AdvantageBatch:
    """Compute per-episode GAE with a literal terminal-zero bootstrap."""

    cfg = config or PPOConfig()
    values = rollout.old_values.detach()
    rewards = rollout.rewards.detach()
    advantages = torch.zeros_like(values)
    running = torch.zeros(
        (EPISODES_PER_ROLLOUT,), dtype=torch.float32, device=values.device
    )
    for transition in range(EPISODE_TRANSITIONS - 1, -1, -1):
        nonterminal = (~rollout.terminated[:, transition]).to(torch.float32)
        if transition == EPISODE_TRANSITIONS - 1:
            next_value = torch.zeros_like(running)
        else:
            next_value = values[:, transition + 1]
        delta = rewards[:, transition] + cfg.gamma * nonterminal * next_value - values[:, transition]
        running = delta + cfg.gamma * cfg.gae_lambda * nonterminal * running
        advantages[:, transition] = running
    decision_values = advantages[rollout.decision_mask]
    mean = decision_values.mean()
    variance = ((decision_values - mean) ** 2).mean()
    normalized = (decision_values - mean) / (
        torch.sqrt(variance) + cfg.advantage_epsilon
    )
    decision_advantages = torch.zeros_like(advantages)
    decision_advantages[rollout.decision_mask] = normalized
    return AdvantageBatch(advantages, decision_advantages, advantages + values)


def _unbiased_integer(
    n: int,
    prefix: tuple[str | int, ...],
    u64: AddressU64,
) -> tuple[int, tuple[str | int, ...]]:
    if type(n) is not int or n <= 0:
        raise PPOValidationError("permutation range must be positive")
    limit = ((1 << 64) // n) * n
    for retry in range(1 << 31):
        address = (*prefix, retry)
        value = u64(address)
        if type(value) is not int or not 0 <= value < (1 << 64):
            raise PPOValidationError("u64 addressing function returned an invalid value")
        if value < limit:
            return value % n, address
    raise PPOValidationError("unbiased-integer rejection loop did not terminate")


def ordered_episode_indices(
    run_name: str,
    seed: int,
    rollout_update: int,
    ppo_epoch: int,
    *,
    address_u64: AddressU64 | None = None,
) -> tuple[tuple[int, ...], tuple[tuple[str | int, ...], ...]]:
    """Descending Fisher-Yates using only the exact common ORDER addresses."""

    if not run_name or type(seed) is not int:
        raise PPOValidationError("run name and integer seed are required")
    if not 0 <= ppo_epoch < PPO_EPOCHS or rollout_update < 0:
        raise PPOValidationError("rollout update or PPO epoch is invalid")
    u64 = address_u64 or _default_u64
    order = list(range(EPISODES_PER_ROLLOUT))
    addresses: list[tuple[str | int, ...]] = []
    for position in range(EPISODES_PER_ROLLOUT - 1, 0, -1):
        prefix = (
            OBJECT_ID,
            "ORDER",
            run_name,
            seed,
            rollout_update,
            ppo_epoch,
            position,
        )
        selected, address = _unbiased_integer(position + 1, prefix, u64)
        addresses.append(address)
        order[position], order[selected] = order[selected], order[position]
    return tuple(order), tuple(addresses)


def make_adam(
    model: CommonRecurrentActorCritic, config: PPOConfig | None = None
) -> torch.optim.Adam:
    """Construct Adam with explicit FP32 zero moments and step counters."""

    cfg = config or PPOConfig()
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=cfg.learning_rate,
        betas=cfg.adam_betas,
        eps=cfg.adam_epsilon,
        weight_decay=cfg.weight_decay,
    )
    for parameter in model.parameters():
        state = optimizer.state[parameter]
        state["step"] = torch.zeros((), dtype=torch.float32, device=parameter.device)
        state["exp_avg"] = torch.zeros_like(parameter, memory_format=torch.preserve_format)
        state["exp_avg_sq"] = torch.zeros_like(parameter, memory_format=torch.preserve_format)
    return optimizer


class RecurrentPPOTrainer:
    """Exactly four epochs and four two-episode full-BPTT steps per rollout."""

    def __init__(
        self,
        model: CommonRecurrentActorCritic,
        *,
        run_name: str,
        seed: int,
        config: PPOConfig | None = None,
        optimizer: torch.optim.Adam | None = None,
        address_u64: AddressU64 | None = None,
    ) -> None:
        if not isinstance(model, CommonRecurrentActorCritic):
            raise PPOValidationError("trainer requires CommonRecurrentActorCritic")
        if not run_name or type(seed) is not int or seed != model.seed:
            raise PPOValidationError("trainer identity must use the model's seed")
        self.model = model
        self.run_name = run_name
        self.seed = seed
        self.config = config or PPOConfig()
        self.optimizer = optimizer or make_adam(model, self.config)
        self.address_u64 = address_u64 or _default_u64
        self.counters = PPOCounters()
        self._order_digest = hashlib.sha256(b"").hexdigest()

    @property
    def minibatch_order_digest(self) -> str:
        return self._order_digest

    def restore_minibatch_order_digest(self, digest: str) -> None:
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise PPOValidationError("minibatch-order digest must be lowercase SHA-256")
        self._order_digest = digest

    def train_rollout(self, rollout: EpisodeRollout) -> tuple[PPOLossRecord, ...]:
        expected_ids = tuple(
            range(
                self.counters.rollout_updates * EPISODES_PER_ROLLOUT,
                (self.counters.rollout_updates + 1) * EPISODES_PER_ROLLOUT,
            )
        )
        if tuple(rollout.episode_ids.cpu().tolist()) != expected_ids:
            raise PPOValidationError(
                f"rollout update {self.counters.rollout_updates} requires episode IDs {expected_ids}"
            )
        advantage_batch = compute_gae(rollout, self.config)
        records: list[PPOLossRecord] = []
        update = self.counters.rollout_updates
        for epoch in range(PPO_EPOCHS):
            order, addresses = ordered_episode_indices(
                self.run_name,
                self.seed,
                update,
                epoch,
                address_u64=self.address_u64,
            )
            self._record_order(update, epoch, order, addresses)
            for minibatch in range(MINIBATCHES_PER_EPOCH):
                selected = order[
                    minibatch * EPISODES_PER_MINIBATCH :
                    (minibatch + 1) * EPISODES_PER_MINIBATCH
                ]
                records.append(
                    self._train_minibatch(
                        rollout, advantage_batch, epoch, minibatch, selected
                    )
                )
                self.counters.adam_steps += 1
        self.counters.rollout_updates += 1
        self.counters.train_episodes += EPISODES_PER_ROLLOUT
        self.counters.train_transitions += EPISODES_PER_ROLLOUT * EPISODE_TRANSITIONS
        self.counters.train_decisions += DECISIONS_PER_ROLLOUT
        self.counters.validate()
        if len(records) != ADAM_STEPS_PER_UPDATE:
            raise AssertionError("frozen update did not produce exactly 16 Adam steps")
        return tuple(records)

    def _record_order(
        self,
        update: int,
        epoch: int,
        order: tuple[int, ...],
        addresses: tuple[tuple[str | int, ...], ...],
    ) -> None:
        payload = {
            "update": update,
            "epoch": epoch,
            "order": list(order),
            "addresses": [list(address) for address in addresses],
        }
        encoded = json.dumps(
            payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        self._order_digest = hashlib.sha256(
            bytes.fromhex(self._order_digest) + encoded
        ).hexdigest()

    def _train_minibatch(
        self,
        rollout: EpisodeRollout,
        advantages: AdvantageBatch,
        epoch: int,
        minibatch: int,
        selected: tuple[int, ...],
    ) -> PPOLossRecord:
        if len(selected) != EPISODES_PER_MINIBATCH:
            raise PPOValidationError("every minibatch must contain exactly two complete episodes")
        indices = torch.tensor(selected, dtype=torch.int64, device=rollout.observations.device)
        sequence = self.model.forward_episode(rollout.observations.index_select(0, indices))
        actions = rollout.actions.index_select(0, indices)
        decisions = rollout.decision_mask.index_select(0, indices)
        old_log_prob = rollout.old_log_probabilities.index_select(0, indices)[decisions]
        actor_advantage = advantages.decision_advantages.index_select(0, indices)[decisions]

        legal_logits = sequence.logits[decisions][:, SERVE : SAFE_FALLBACK + 1]
        legal_log_prob = torch.log_softmax(legal_logits, dim=-1)
        decision_actions = actions[decisions] - SERVE
        selected_log_prob = legal_log_prob.gather(
            1, decision_actions.unsqueeze(-1)
        ).squeeze(-1)
        ratio = torch.exp(selected_log_prob - old_log_prob)
        unclipped = ratio * actor_advantage
        clipped = torch.clamp(
            ratio, 1.0 - self.config.clip, 1.0 + self.config.clip
        ) * actor_advantage
        actor_loss = -torch.minimum(unclipped, clipped).mean()
        probabilities = torch.softmax(legal_logits, dim=-1)
        entropy = -(probabilities * legal_log_prob).sum(dim=-1).mean()
        target = advantages.value_targets.index_select(0, indices)
        value_loss = ((sequence.values - target) ** 2).mean()
        total_loss = (
            actor_loss
            + self.config.value_coefficient * value_loss
            - self.config.entropy_coefficient * entropy
        )
        if not torch.isfinite(total_loss).item():
            raise PPOValidationError("nonfinite PPO loss")
        self.optimizer.zero_grad(set_to_none=True)
        total_loss.backward()
        gradient_norm = nn.utils.clip_grad_norm_(
            self.model.parameters(), self.config.gradient_norm_cap
        )
        if not torch.isfinite(gradient_norm).item():
            raise PPOValidationError("nonfinite global gradient norm")
        self.optimizer.step()
        ids = tuple(int(rollout.episode_ids[index].item()) for index in selected)
        return PPOLossRecord(
            epoch,
            minibatch,
            ids,  # type: ignore[arg-type]
            float(actor_loss.detach().item()),
            float(value_loss.detach().item()),
            float(entropy.detach().item()),
            float(total_loss.detach().item()),
            float(gradient_norm.detach().item()),
        )


def config_digest(config: PPOConfig) -> str:
    payload = json.dumps(
        config.canonical_dict(), ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
