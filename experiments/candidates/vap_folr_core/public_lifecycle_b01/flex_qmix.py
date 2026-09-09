"""Selected FlexQMixer path from thu-rllab/CAMA, commit
1d8d6f8c44102d7b8904bf44eeb38cd1276dbb58,
CAMA/modules/mixers/flex_qmix.py. Fixed attention/softmax/ELU configuration;
unused imagination, pooling, alternative mixer and configuration branches omitted.
"""
import torch
from torch import nn
from torch.nn import functional as F

from .attention import EntityAttentionLayer


class AttentionHyperNet(nn.Module):
    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.fc1 = nn.Linear(9, 128)
        self.attn = EntityAttentionLayer()
        self.fc2 = nn.Linear(128, 32)

    def forward(self, entities, entity_mask):
        x1 = F.relu(self.fc1(entities))
        agent_mask = entity_mask[:, :5]
        attn_mask = 1 - torch.bmm((1 - agent_mask.float()).unsqueeze(2),
                                  (1 - entity_mask.float()).unsqueeze(1))
        x2 = self.attn(x1, attn_mask.to(torch.uint8), agent_mask)
        x3 = self.fc2(x2)
        x3 = x3.masked_fill(agent_mask.unsqueeze(2).bool(), 0)
        # Source means include the zeroed inactive slots, not an active-count denominator.
        if self.mode == "vector":
            return x3.mean(dim=1)
        if self.mode == "scalar":
            return x3.mean(dim=(1, 2))
        return x3


class FlexQMixer(nn.Module):
    def __init__(self):
        super().__init__()
        self.hyper_w_1 = AttentionHyperNet("matrix")
        self.hyper_w_final = AttentionHyperNet("vector")
        self.hyper_b_1 = AttentionHyperNet("vector")
        self.V = AttentionHyperNet("scalar")

    def forward(self, agent_qs, inputs):
        entities, entity_mask = inputs
        bs, max_t, ne, ed = entities.shape
        entities = entities.reshape(bs * max_t, ne, ed)
        entity_mask = entity_mask.reshape(bs * max_t, ne)
        agent_qs = agent_qs.reshape(-1, 1, 5)
        w1 = self.hyper_w_1(entities, entity_mask)
        b1 = self.hyper_b_1(entities, entity_mask)
        w1 = F.softmax(w1.view(bs * max_t, -1, 32), dim=-1)
        b1 = b1.view(-1, 1, 32)
        hidden = F.elu(torch.bmm(agent_qs, w1) + b1)
        w_final = F.softmax(self.hyper_w_final(entities, entity_mask), dim=-1)
        w_final = w_final.view(-1, 32, 1)
        v = self.V(entities, entity_mask).view(-1, 1, 1)
        return (torch.bmm(hidden, w_final) + v).view(bs, -1, 1)
