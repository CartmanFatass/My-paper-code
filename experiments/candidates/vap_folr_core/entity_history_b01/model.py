"""Selected GRU16 observer-subject bank and equally informed generic GRU64."""
import torch
from torch import nn
from torch.nn import functional as F

from ..public_lifecycle_b01.attention import EntityAttentionLayer


class ObserverAttention(EntityAttentionLayer):
    def forward(self, tokens, allowed, observer_active):
        # [batch, observer, subject, feature]; one query from that observer's self.
        b, n, _, _ = tokens.shape
        query, key, value = self.in_trans(tokens).chunk(3, dim=-1)
        index = torch.arange(n, device=tokens.device)
        query = query[:, index, index].reshape(b, n, 4, 32)
        key = key.reshape(b, n, n, 4, 32)
        value = value.reshape(b, n, n, 4, 32)
        logits = (query[:, :, None] * key).sum(-1) / self.scale_factor
        # Finite masked logits avoid NaN softmax derivatives on empty rows.
        logits = logits.masked_fill(~allowed[..., None], torch.finfo(tokens.dtype).min)
        weight = F.softmax(logits, dim=2).masked_fill(~allowed[..., None], 0)
        result = (weight[..., None] * value).sum(2).reshape(b, n, 128)
        return self.out_trans(result).masked_fill(~observer_active[..., None], 0)


class Actor(nn.Module):
    def __init__(self, arm):
        super().__init__()
        if arm not in ('GENERIC_RETAIN', 'BANK'):
            raise ValueError(arm)
        self.arm = arm
        # Same-role common modules consume the same constructor stream in both arms.
        self.fc1 = nn.Linear(14, 128)  # nine permitted physical/action features + label
        self.attn = ObserverAttention()
        self.fc2 = nn.Linear(160, 64)  # attention + full public table + local indicators
        self.fc3 = nn.Linear(64, 5)
        self.register_buffer('labels', torch.eye(5))
        # Arm-specific construction cannot shift subsequent common mixer/action RNG.
        with torch.random.fork_rng(devices=[]):
            if arm == 'BANK':
                self.rnn = nn.GRUCell(128, 16)
                self.token = nn.Linear(33, 128)  # memory16 + current9 + label5 + local3
            else:
                self.rnn = nn.GRUCell(64, 64)

    def forward(self, batch, hidden=None):
        physical = torch.cat((batch['entities'], batch['previous_action']), dim=-1)
        b, t, n, _ = physical.shape
        active = ~batch['entity_mask'].bool()
        visible = batch['visible'].bool() & active[..., :, None] & active[..., None, :]
        # Sanitize before a learned operation; other observers' rows never mix.
        local_physical = torch.where(visible[..., None], physical[:, :, None], 0)
        labels = self.labels.expand(b, t, n, n, 5)
        embedded = F.relu(self.fc1(torch.cat((local_physical, labels), dim=-1)))
        current = embedded.masked_fill(~visible[..., None], 0)
        local = torch.stack((visible.to(physical.dtype), batch['seen'].to(physical.dtype),
                             batch['age'].to(physical.dtype) / 20), dim=-1)
        public = torch.stack((active, batch['birth'].bool(), batch['departure'].bool()), -1)
        public = public.reshape(b, t, 1, 15).expand(-1, -1, n, -1).to(physical.dtype)
        metadata = torch.cat((public, local.reshape(b, t, n, 15),
                              batch['event'][:, :, None, None].expand(-1, -1, n, -1).to(physical.dtype),
                              batch['birth'][..., None].to(physical.dtype)), -1)
        if self.arm == 'GENERIC_RETAIN':
            attended = self.attn(current.reshape(b*t, n, n, 128),
                                 visible.reshape(b*t, n, n), active.reshape(b*t, n))
            x = F.relu(self.fc2(torch.cat((attended.reshape(b, t, n, 128), metadata), -1)))
            h = physical.new_zeros(b, n, 64) if hidden is None else hidden
        else:
            h = physical.new_zeros(b, n, n, 16) if hidden is None else hidden
        states, values = [], []
        for step in range(t):
            continuation = batch['continuation'][:, step].bool()
            if self.arm == 'GENERIC_RETAIN':
                h = h * continuation[..., None]
                h = self.rnn(x[:, step].reshape(b*n, 64), h.reshape(b*n, 64)).reshape(b, n, 64)
                h = h.masked_fill(~active[:, step, :, None], 0)
                q_features = h
            else:
                carry = continuation[:, :, None] & continuation[:, None, :]
                h = h * carry[..., None]
                candidate = self.rnn(embedded[:, step].reshape(b*n*n, 128),
                                     h.reshape(b*n*n, 16)).reshape(b, n, n, 16)
                h = torch.where(visible[:, step, ..., None], candidate, h)
                # Direct current physical features bypass the sixteen-state bottleneck.
                tokens = F.relu(self.token(torch.cat((h, local_physical[:, step],
                                                      labels[:, step], local[:, step]), -1)))
                allowed = batch['seen'][:, step].bool() & active[:, step, :, None] & active[:, step, None, :]
                attended = self.attn(tokens, allowed, active[:, step])
                q_features = F.relu(self.fc2(torch.cat((attended, metadata[:, step]), -1)))
            states.append(h)
            values.append(self.fc3(q_features).masked_fill(~active[:, step, :, None], 0))
        return torch.stack(values, 1), torch.stack(states, 1)
