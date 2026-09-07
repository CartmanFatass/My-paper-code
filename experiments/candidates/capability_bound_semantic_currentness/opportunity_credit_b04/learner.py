"""B04 sampled opportunity targets with decision-only critic supervision.

Actor/Adam ordering and full episode BPTT follow the fixed B01 reference.
The B01 trainer methods below are copied locally to keep old GAE unchanged.
"""
from dataclasses import dataclass
import torch
from torch import nn
from ..omrc_b01.model import SERVE, SAFE_FALLBACK, model_parameter_digest
from ..omrc_b01.ppo import (
    AdvantageBatch, EpisodeRollout, PPOLossRecord, PPOValidationError,
    RecurrentPPOTrainer, ordered_episode_indices, EPISODES_PER_ROLLOUT,
    EPISODE_TRANSITIONS, DECISIONS_PER_ROLLOUT, PPO_EPOCHS,
    MINIBATCHES_PER_EPOCH, EPISODES_PER_MINIBATCH, ADAM_STEPS_PER_UPDATE,
)

OBJECT = "CBSC-OPPORTUNITY-CREDIT-B04"

@dataclass(frozen=True)
class OpportunityConfig:
    target: str = "sampled_FP32_reward[t]+reward[t+1]; no bootstrap"
    value_supervision: str = "unnormalized target; MSE mean over 48 minibatch decisions"
    advantage_normalization: str = "once over 192 rollout decisions; population std + 1e-8"
    native_gamma: float = 1.0
    clip: float = 0.20
    value_coefficient: float = 0.50
    entropy_coefficient: float = 0.01
    learning_rate: float = 3e-4
    adam_betas: tuple = (0.9, 0.999)
    adam_epsilon: float = 1e-8
    weight_decay: float = 0.0
    gradient_norm_cap: float = 0.5
    advantage_epsilon: float = 1e-8
    epochs: int = 4
    episodes_per_minibatch: int = 2


def opportunity_targets(rewards, old_values):
    """Only sampled decision+settlement rewards; detached old decision baseline."""
    targets = torch.zeros_like(rewards)
    targets[:, 12::6] = rewards.detach()[:, 12::6] + rewards.detach()[:, 13::6]
    advantages = torch.zeros_like(rewards)
    local = targets[:, 12::6] - old_values.detach()[:, 12::6]
    advantages[:, 12::6] = local
    centered = local - local.mean()
    normalized = torch.zeros_like(rewards)
    normalized[:, 12::6] = centered / (torch.sqrt((centered ** 2).mean()) + 1e-8)
    return AdvantageBatch(advantages, normalized, targets)


def decision_value_loss(values, targets, decisions):
    return ((values[decisions] - targets[decisions]) ** 2).mean()


class OpportunityTrainer(RecurrentPPOTrainer):
    def __init__(self, model, *, run_name, seed, address_u64):
        super().__init__(model, run_name=run_name, seed=seed,
                         address_u64=address_u64, config=OpportunityConfig())

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
        advantage_batch = opportunity_targets(rollout.rewards, rollout.old_values)
        self.last_targets = advantage_batch
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
        value_loss = decision_value_loss(sequence.values, target, decisions)
        total_loss = (
            actor_loss
            + self.config.value_coefficient * value_loss
            - self.config.entropy_coefficient * entropy
        )
        for name, scalar in (
            ("actor loss", actor_loss),
            ("value loss", value_loss),
            ("entropy", entropy),
            ("total loss", total_loss),
        ):
            if scalar.dtype != torch.float32 or not torch.isfinite(scalar).item():
                raise PPOValidationError(f"{name} must be a finite FP32 scalar")
        self.optimizer.zero_grad(set_to_none=True)
        total_loss.backward()
        gradient_norm = nn.utils.clip_grad_norm_(
            self.model.parameters(), self.config.gradient_norm_cap
        )
        if gradient_norm.dtype != torch.float32 or not torch.isfinite(gradient_norm).item():
            raise PPOValidationError("preclip global gradient norm must be finite FP32")
        gradients = [
            parameter.grad.detach()
            for parameter in self.model.parameters()
            if parameter.grad is not None
        ]
        if not gradients or any(
            gradient.dtype != torch.float32 or not torch.isfinite(gradient).all().item()
            for gradient in gradients
        ):
            raise PPOValidationError("postclip gradients must be finite FP32 tensors")
        postclip_gradient_norm = torch.linalg.vector_norm(
            torch.stack([torch.linalg.vector_norm(gradient) for gradient in gradients])
        )
        if (
            postclip_gradient_norm.dtype != torch.float32
            or not torch.isfinite(postclip_gradient_norm).item()
        ):
            raise PPOValidationError("postclip global gradient norm is not finite FP32")
        self.optimizer.step()
        expected_optimizer_step = self.counters.adam_steps + 1
        optimizer_step_counts = {
            int(self.optimizer.state[parameter]["step"].item())
            for parameter in self.model.parameters()
        }
        if optimizer_step_counts != {expected_optimizer_step}:
            raise PPOValidationError("Adam state step count differs across parameters")
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
            self.counters.rollout_updates,
            float(postclip_gradient_norm.detach().item()),
            expected_optimizer_step,
            model_parameter_digest(self.model),
        )
