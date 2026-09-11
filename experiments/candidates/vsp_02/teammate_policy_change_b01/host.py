"""Simultaneous local-information handoff host, in-process episode batching."""
import torch
from torch.nn.functional import one_hot


class HandoffEnv:
    def __init__(self, batch_size):
        self.batch_size = batch_size

    def reset(self, lights, changed):
        self.lights = lights.clone()
        self.changed = bool(changed)
        self.t = 0
        self.receiver = torch.zeros(self.batch_size, dtype=torch.int64)
        self.courier = torch.zeros_like(self.receiver)
        self.past_receiver = torch.zeros(self.batch_size, 4)
        self.past_courier = torch.zeros(self.batch_size, 4)
        self.past_visible = torch.zeros(self.batch_size)
        self.past_reward = torch.zeros(self.batch_size)
        return self.observation()

    def observation(self):
        obs = torch.zeros(self.batch_size, 18, dtype=torch.float32)
        obs[:, 0] = self.receiver
        obs[:, 1] = self.t % 3
        obs[:, 2] = self.t // 3
        light_visible = self.receiver.abs() <= 1
        obs[:, 3] = self.lights[:, self.t // 3] * light_visible
        obs[:, 4] = light_visible
        distance = self.courier - self.receiver
        visible = distance.abs() <= 1
        obs[:, 5] = distance * visible
        obs[:, 6] = visible
        obs[:, 7:11] = self.past_courier
        obs[:, 11] = self.past_visible
        obs[:, 12:16] = self.past_receiver
        obs[:, 16] = self.past_reward
        obs[:, 17] = self.changed
        return obs

    def step(self, receiver_actions):
        if self.t % 3 == 2:
            courier_actions = torch.full_like(receiver_actions, 3)
        else:
            direction = self.lights[:, self.t // 3] * (-1 if self.changed else 1)
            courier_actions = (direction > 0).long()
        visible = (self.courier - self.receiver).abs() <= 1
        reward = ((self.receiver == self.courier) & (self.receiver.abs() == 2)
                  & (receiver_actions == 3) & (courier_actions == 3)).float()
        self.receiver += (receiver_actions == 1).long() - (receiver_actions == 0).long()
        self.courier += (courier_actions == 1).long() - (courier_actions == 0).long()
        self.receiver.clamp_(-2, 2)
        self.courier.clamp_(-2, 2)
        self.past_receiver = one_hot(receiver_actions, 4).float()
        self.past_courier = one_hot(courier_actions, 4).float() * visible[:, None]
        self.past_visible = visible.float()
        self.past_reward = reward
        self.t += 1
        if self.t == 48:
            return None, reward, True
        if self.t % 3 == 0:
            self.receiver.zero_()
            self.courier.zero_()
        return self.observation(), reward, False
