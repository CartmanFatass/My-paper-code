"""CAMA generic entity-attention GRU with the card's public lifecycle rule.

Adapted from CAMA/modules/agents/entity_rnn_agent.py, thu-rllab/CAMA
commit 1d8d6f8c44102d7b8904bf44eeb38cd1276dbb58. The selected source
fc1/attention/fc2/GRU/fc3 chain is retained; E and own B extend fc2 input.
"""
import torch
from torch import nn
from torch.nn import functional as F

from .attention import EntityAttentionLayer


class Actor(nn.Module):
    def __init__(self, arm):
        super().__init__()
        self.arm = arm
        self.fc1 = nn.Linear(9, 128)
        self.attn = EntityAttentionLayer()
        self.fc2 = nn.Linear(130, 64)
        self.rnn = nn.GRUCell(64, 64)
        self.fc3 = nn.Linear(64, 5)

    def forward(self, batch, hidden=None):
        entities = torch.cat((batch["entities"], batch["previous_action"]), dim=-1)
        bs, ts, ne, ed = entities.shape
        agent_mask = batch["entity_mask"].reshape(bs * ts, ne)
        x1 = F.relu(self.fc1(entities.reshape(bs * ts, ne, ed)))
        x2 = self.attn(x1, batch["obs_mask"].reshape(bs * ts, ne, ne), agent_mask)
        event = batch["event"].reshape(bs * ts, 1, 1).expand(-1, ne, -1)
        birth = batch["birth"].reshape(bs * ts, ne, 1)
        x2 = torch.cat((x2, event.to(x2.dtype), birth.to(x2.dtype)), dim=-1)
        x3 = F.relu(self.fc2(x2)).reshape(bs, ts, ne, 64)
        h = x3.new_zeros(bs * ne, 64) if hidden is None else hidden.reshape(bs * ne, 64)
        hs = []
        for t in range(ts):
            carry = batch["continuation"][:, t].bool()
            if self.arm == "EVENT":
                carry = carry & ~batch["event"][:, t, None].bool()
            elif self.arm == "RANDOM":
                carry = carry & ~batch["reset_mask"][:, t].bool()
            h = h * carry.reshape(bs * ne, 1).to(h.dtype)
            h = self.rnn(x3[:, t].reshape(bs * ne, 64), h)
            h = h.masked_fill(batch["entity_mask"][:, t].reshape(bs * ne, 1).bool(), 0)
            hs.append(h.reshape(bs, ne, 64))
        hs = torch.stack(hs, dim=1)
        q = self.fc3(hs)
        q = q.masked_fill(batch["entity_mask"].unsqueeze(-1).bool(), 0)
        return q, hs
