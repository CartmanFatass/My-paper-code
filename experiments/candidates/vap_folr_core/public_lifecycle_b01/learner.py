"""Fixed complete-episode double Q learner derived from CAMA QLearner.

Source: thu-rllab/CAMA at 1d8d6f8c44102d7b8904bf44eeb38cd1276dbb58,
CAMA/learners/q_learner.py. All 20 transitions are filled; native actions
are all available. Lifecycle-aligned actor unroll is shared by both networks.
"""
import copy

import torch
from torch.optim import RMSprop

from .flex_qmix import FlexQMixer
from .model import Actor


class Learner:
    def __init__(self, arm):
        self.actor = Actor(arm)
        self.mixer = FlexQMixer()
        self.target_mixer = copy.deepcopy(self.mixer)
        self.params = list(self.actor.parameters()) + list(self.mixer.parameters())
        self.optimiser = RMSprop(self.params, lr=0.0005, alpha=0.99, eps=0.00001)
        self.target_actor = copy.deepcopy(self.actor)
        self.last_target_update_episode = 0
        self.updates = 0

    def update(self, batch, episode_num):
        self.actor.train()
        self.mixer.train()
        self.target_actor.eval()
        self.target_mixer.eval()
        online_q, _ = self.actor(batch)
        chosen_q = online_q[:, :-1].gather(3, batch["actions"].long().unsqueeze(-1)).squeeze(3)
        entities = torch.cat((batch["entities"], batch["previous_action"]), dim=-1)
        mix_inputs = (entities[:, :-1], batch["entity_mask"][:, :-1])
        chosen_total = self.mixer(chosen_q, mix_inputs)
        with torch.no_grad():
            target_q, _ = self.target_actor(batch)
            greedy_actions = online_q.detach()[:, 1:].max(dim=3, keepdim=True)[1]
            target_max = target_q[:, 1:].gather(3, greedy_actions).squeeze(3)
            target_total = self.target_mixer(target_max, (entities[:, 1:], batch["entity_mask"][:, 1:]))
            targets = batch["reward"].unsqueeze(-1) + 0.99 * (
                1 - batch["terminated"].float().unsqueeze(-1)) * target_total
        # No padding or early cooperative termination in the fixed 20-step host.
        loss = ((chosen_total - targets) ** 2).mean()
        self.optimiser.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.params, 10)
        self.optimiser.step()
        self.updates += 1
        if episode_num - self.last_target_update_episode >= 200:
            self.target_actor.load_state_dict(self.actor.state_dict())
            self.target_mixer.load_state_dict(self.mixer.state_dict())
            self.last_target_update_episode = episode_num
        return loss.item()

    def save(self, path):
        """Publish the single final learner checkpoint; no resume route."""
        torch.save({"actor": self.actor.state_dict(), "mixer": self.mixer.state_dict(),
                    "target_actor": self.target_actor.state_dict(),
                    "target_mixer": self.target_mixer.state_dict(),
                    "optimiser": self.optimiser.state_dict(), "updates": self.updates,
                    "arm": self.actor.arm}, path)
