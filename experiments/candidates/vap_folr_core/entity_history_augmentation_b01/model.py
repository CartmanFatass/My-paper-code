"""Generic64 actor augmented with independent persistent entity histories."""

import torch
from torch import nn
from torch.nn import functional as F

from ..entity_history_b01.model import Actor, ObserverAttention


class AugmentedActor(nn.Module):
    """Functional two-stream actor with packed Generic and entity state."""

    def __init__(self, arm="AUGMENTED_PERSISTENT"):
        super().__init__()
        if arm not in ("AUGMENTED_PERSISTENT", "AUGMENTED_CURRENT_ONLY"):
            raise ValueError(arm)
        self.arm = arm
        # Construct the complete reference so its discarded Q head consumes the
        # same draws as a fresh Generic actor from the same external RNG state.
        generic = Actor("GENERIC_RETAIN")
        self.fc1 = generic.fc1
        self.attn = generic.attn
        self.fc2 = generic.fc2
        self.rnn = generic.rnn
        self.register_buffer("labels", generic.labels)

        # The added stream is initialized without moving the caller's CPU RNG.
        with torch.random.fork_rng(devices=[]):
            self.entity_fc1 = nn.Linear(14, 128)
            self.entity_rnn = nn.GRUCell(128, 16)
            self.entity_token = nn.Linear(33, 128)
            self.entity_attn = ObserverAttention()
            self.entity_fc2 = nn.Linear(160, 64)
            self.head = nn.Linear(128, 5)

    def forward(self, batch, hidden=None):
        physical = torch.cat((batch["entities"], batch["previous_action"]), dim=-1)
        b, t, n, _ = physical.shape
        active = ~batch["entity_mask"].bool()
        pair_active = active[..., :, None] & active[..., None, :]
        visible = batch["visible"].bool() & pair_active

        # Forbidden current values are removed before either learned encoder.
        local_physical = torch.where(visible[..., None], physical[:, :, None], 0)
        labels = self.labels.expand(b, t, n, n, 5)
        generic_current = F.relu(self.fc1(torch.cat((local_physical, labels), -1)))
        generic_current = generic_current.masked_fill(~visible[..., None], 0)
        entity_input = F.relu(self.entity_fc1(torch.cat((local_physical, labels), -1)))

        local = torch.stack(
            (
                visible.to(physical.dtype),
                batch["seen"].to(physical.dtype),
                batch["age"].to(physical.dtype) / 20,
            ),
            dim=-1,
        )
        public = torch.stack(
            (active, batch["birth"].bool(), batch["departure"].bool()), -1
        )
        public = public.reshape(b, t, 1, 15).expand(-1, -1, n, -1).to(physical.dtype)
        metadata = torch.cat(
            (
                public,
                local.reshape(b, t, n, 15),
                batch["event"][:, :, None, None].expand(-1, -1, n, -1).to(physical.dtype),
                batch["birth"][..., None].to(physical.dtype),
            ),
            -1,
        )

        generic_attended = self.attn(
            generic_current.reshape(b * t, n, n, 128),
            visible.reshape(b * t, n, n),
            active.reshape(b * t, n),
        )
        generic_input = F.relu(
            self.fc2(
                torch.cat((generic_attended.reshape(b, t, n, 128), metadata), -1)
            )
        )

        if hidden is None:
            generic_state = physical.new_zeros(b, n, 64)
            entity_state = physical.new_zeros(b, n, n, 16)
        else:
            generic_state = hidden[..., :64]
            entity_state = hidden[..., 64:].reshape(b, n, n, 16)

        values, states = [], []
        for step in range(t):
            continuation = batch["continuation"][:, step].bool()
            generic_state = generic_state * continuation[..., None]
            generic_state = self.rnn(
                generic_input[:, step].reshape(b * n, 64),
                generic_state.reshape(b * n, 64),
            ).reshape(b, n, 64)
            generic_state = generic_state.masked_fill(~active[:, step, :, None], 0)

            pair_continuation = continuation[:, :, None] & continuation[:, None, :]
            entity_state = entity_state * pair_continuation[..., None]
            if self.arm == "AUGMENTED_CURRENT_ONLY":
                entity_state = torch.zeros_like(entity_state)
            candidate = self.entity_rnn(
                entity_input[:, step].reshape(b * n * n, 128),
                entity_state.reshape(b * n * n, 16),
            ).reshape(b, n, n, 16)
            entity_state = torch.where(
                visible[:, step, ..., None], candidate, entity_state
            ).masked_fill(~pair_active[:, step, ..., None], 0)

            tokens = F.relu(
                self.entity_token(
                    torch.cat(
                        (
                            entity_state,
                            local_physical[:, step],
                            labels[:, step],
                            local[:, step],
                        ),
                        -1,
                    )
                )
            )
            allowed = batch["seen"][:, step].bool() & pair_active[:, step]
            entity_attended = self.entity_attn(tokens, allowed, active[:, step])
            entity_features = F.relu(
                self.entity_fc2(torch.cat((entity_attended, metadata[:, step]), -1))
            )
            q = self.head(torch.cat((generic_state, entity_features), -1))
            q = q.masked_fill(~active[:, step, :, None], 0)
            packed = torch.cat((generic_state, entity_state.reshape(b, n, 80)), -1)
            values.append(q)
            states.append(packed)

        return torch.stack(values, 1), torch.stack(states, 1)
