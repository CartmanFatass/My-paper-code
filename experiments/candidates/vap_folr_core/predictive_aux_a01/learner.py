"""Separate-head factual-reward auxiliary for the unchanged Generic learner."""

import torch
from torch import nn
from torch.nn import functional as F
from torch.optim import RMSprop

from ..entity_history_augmentation_b01.learner import Learner as NativeLearner


ARMS = ("DETACHED", "COUPLED")
AUXILIARY_WEIGHT = 0.1
PREDICTION_HORIZON = 3
PREDICTION_STEPS = 18


def prediction_targets(batch):
    """Return factual FP32 three-reward means and active-at-t eligibility."""
    rewards = batch["reward"]
    if rewards.ndim != 2 or rewards.shape[1] != 20:
        raise ValueError("predictive auxiliary requires complete H20 rewards")
    if rewards.dtype != torch.float32:
        raise ValueError("predictive auxiliary labels require native FP32 rewards")
    targets = torch.stack(
        [rewards[:, offset:offset + PREDICTION_STEPS] for offset in range(PREDICTION_HORIZON)],
        dim=0,
    ).mean(dim=0)
    targets = targets[..., None].expand(-1, -1, 5)
    eligible = ~batch["entity_mask"][:, :PREDICTION_STEPS].bool()
    if eligible.shape != targets.shape:
        raise ValueError("active-agent mask does not match fixed H20 predictive labels")
    return targets, eligible


def masked_prediction_mse(predictions, targets, eligible):
    count = int(eligible.sum().item())
    if count == 0:
        raise ValueError("predictive auxiliary batch has no eligible agent-time labels")
    error = predictions[eligible] - targets[eligible]
    return error.square().mean(), error, count


class Learner(NativeLearner):
    """Native learner plus an isolated linear predictor in one selected arm."""

    def __init__(self, arm):
        if arm not in ARMS:
            raise ValueError(arm)
        super().__init__("GENERIC_RETAIN")
        self.auxiliary_arm = arm
        # Construction must neither move the native stream nor contaminate the target actor.
        with torch.random.fork_rng(devices=[]):
            self.predictor = nn.Linear(64, 1)
        self.predictor_params = list(self.predictor.parameters())
        self.predictor_optimiser = RMSprop(
            self.predictor_params, lr=0.0005, alpha=0.99, eps=0.00001
        )
        self.predictor_updates = 0

    def update(self, batch, episode_num):
        # This native block intentionally matches public_lifecycle_b01.Learner.update.
        self.actor.train()
        self.mixer.train()
        self.predictor.train()
        self.target_actor.eval()
        self.target_mixer.eval()
        online_q, hidden = self.actor(batch)
        chosen_q = online_q[:, :-1].gather(
            3, batch["actions"].long().unsqueeze(-1)
        ).squeeze(3)
        entities = torch.cat((batch["entities"], batch["previous_action"]), dim=-1)
        mix_inputs = (entities[:, :-1], batch["entity_mask"][:, :-1])
        chosen_total = self.mixer(chosen_q, mix_inputs)
        with torch.no_grad():
            target_q, _ = self.target_actor(batch)
            greedy_actions = online_q.detach()[:, 1:].max(dim=3, keepdim=True)[1]
            target_max = target_q[:, 1:].gather(3, greedy_actions).squeeze(3)
            target_total = self.target_mixer(
                target_max, (entities[:, 1:], batch["entity_mask"][:, 1:])
            )
            targets = batch["reward"].unsqueeze(-1) + 0.99 * (
                1 - batch["terminated"].float().unsqueeze(-1)
            ) * target_total
        native_loss = ((chosen_total - targets) ** 2).mean()

        prediction_target, eligible = prediction_targets(batch)
        detached_predictions = self.predictor(
            hidden[:, :PREDICTION_STEPS].detach()
        ).squeeze(-1)
        predictor_loss, prediction_error, prediction_count = masked_prediction_mse(
            detached_predictions, prediction_target, eligible
        )

        self.optimiser.zero_grad()
        self.predictor_optimiser.zero_grad()
        if self.auxiliary_arm == "COUPLED":
            # The head is a constant linear map on this path; only h_t receives it.
            coupled_predictions = F.linear(
                hidden[:, :PREDICTION_STEPS],
                self.predictor.weight.detach(),
                self.predictor.bias.detach(),
            ).squeeze(-1)
            coupled_loss, _, coupled_count = masked_prediction_mse(
                coupled_predictions, prediction_target, eligible
            )
            if coupled_count != prediction_count:
                raise RuntimeError("predictor path eligibility drift")
            (native_loss + AUXILIARY_WEIGHT * coupled_loss).backward()
        else:
            native_loss.backward()
        predictor_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.params, 10)
        torch.nn.utils.clip_grad_norm_(self.predictor_params, 10)
        self.optimiser.step()
        self.predictor_optimiser.step()
        self.updates += 1
        self.predictor_updates += 1
        if episode_num - self.last_target_update_episode >= 200:
            self.target_actor.load_state_dict(self.actor.state_dict())
            self.target_mixer.load_state_dict(self.mixer.state_dict())
            self.last_target_update_episode = episode_num

        selected_predictions = detached_predictions[eligible].detach()
        selected_targets = prediction_target[eligible].detach()
        return {
            "native_loss": native_loss.item(),
            "prediction_mse": predictor_loss.item(),
            "prediction_count": prediction_count,
            "prediction_sum": selected_predictions.double().sum().item(),
            "prediction_square_sum": selected_predictions.double().square().sum().item(),
            "target_sum": selected_targets.double().sum().item(),
            "target_square_sum": selected_targets.double().square().sum().item(),
            "error_sum": prediction_error.detach().double().sum().item(),
            "error_square_sum": prediction_error.detach().double().square().sum().item(),
        }

    def save(self, path):
        """Publish the sole final learner, including separately owned head state."""
        torch.save(
            {
                "actor": self.actor.state_dict(),
                "mixer": self.mixer.state_dict(),
                "target_actor": self.target_actor.state_dict(),
                "target_mixer": self.target_mixer.state_dict(),
                "optimiser": self.optimiser.state_dict(),
                "predictor": self.predictor.state_dict(),
                "predictor_optimiser": self.predictor_optimiser.state_dict(),
                "updates": self.updates,
                "predictor_updates": self.predictor_updates,
                "arm": self.auxiliary_arm,
                "native_actor_arm": self.actor.arm,
            },
            path,
        )
