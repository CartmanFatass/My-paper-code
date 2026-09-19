"""Generic64 with a deterministic observer-subject last-sighting cache."""

import torch
from torch.nn import functional as F

from ..entity_history_b01.model import Actor as GenericActor


N_ENTITIES = 5
PHYSICAL_FEATURES = 9
GENERIC_STATE = 64
CACHE_STATE = N_ENTITIES * PHYSICAL_FEATURES


class Actor(GenericActor):
    """The unchanged Generic64 modules reading lifetime-scoped cached tokens."""

    def __init__(self, arm="LAST_SIGHTING"):
        if arm != "LAST_SIGHTING":
            raise ValueError(arm)
        # This is the complete Generic construction. Changing only the semantic
        # label afterwards preserves its trainable state and caller RNG stream.
        super().__init__("GENERIC_RETAIN")
        self.arm = arm

    def forward(self, batch, hidden=None):
        physical = torch.cat((batch["entities"], batch["previous_action"]), dim=-1)
        b, t, n, features = physical.shape
        if n != N_ENTITIES or features != PHYSICAL_FEATURES:
            raise ValueError("LAST_SIGHTING requires the fixed 5x9 entity-history host")

        active = ~batch["entity_mask"].bool()
        pair_active = active[..., :, None] & active[..., None, :]
        visible = batch["visible"].bool() & pair_active
        # Expand a subject's physical row only after applying each observer's
        # visibility. Hidden current values never enter a cache or learned op.
        visible_physical = torch.where(
            visible[..., None], physical[:, :, None, :, :], 0
        )
        labels = self.labels.expand(b, t, n, n, N_ENTITIES)

        local = torch.stack(
            (
                visible.to(physical.dtype),
                batch["seen"].to(physical.dtype),
                batch["age"].to(physical.dtype) / 20,
            ),
            dim=-1,
        )
        public = torch.stack(
            (active, batch["birth"].bool(), batch["departure"].bool()), dim=-1
        )
        public = public.reshape(b, t, 1, 15).expand(-1, -1, n, -1).to(physical.dtype)
        metadata = torch.cat(
            (
                public,
                local.reshape(b, t, n, 15),
                batch["event"][:, :, None, None]
                .expand(-1, -1, n, -1)
                .to(physical.dtype),
                batch["birth"][..., None].to(physical.dtype),
            ),
            dim=-1,
        )

        if hidden is None:
            recurrent = physical.new_zeros(b, n, GENERIC_STATE)
            cache = physical.new_zeros(b, n, n, PHYSICAL_FEATURES)
        else:
            expected = GENERIC_STATE + CACHE_STATE
            if hidden.shape != (b, n, expected):
                raise ValueError(
                    f"LAST_SIGHTING hidden state must have shape {(b, n, expected)}"
                )
            recurrent = hidden[..., :GENERIC_STATE]
            cache = hidden[..., GENERIC_STATE:].reshape(
                b, n, n, PHYSICAL_FEATURES
            )

        values, states = [], []
        for step in range(t):
            continuation = batch["continuation"][:, step].bool()
            recurrent = recurrent * continuation[..., None]

            pair_continuation = continuation[:, :, None] & continuation[:, None, :]
            cache = cache * pair_continuation[..., None]
            cache = torch.where(visible[:, step, ..., None], visible_physical[:, step], cache)
            cache = cache.masked_fill(~pair_active[:, step, ..., None], 0)

            tokens = F.relu(
                self.fc1(torch.cat((cache, labels[:, step]), dim=-1))
            )
            allowed = batch["seen"][:, step].bool() & pair_active[:, step]
            attended = self.attn(tokens, allowed, active[:, step])
            recurrent_input = F.relu(
                self.fc2(torch.cat((attended, metadata[:, step]), dim=-1))
            )
            recurrent = self.rnn(
                recurrent_input.reshape(b * n, GENERIC_STATE),
                recurrent.reshape(b * n, GENERIC_STATE),
            ).reshape(b, n, GENERIC_STATE)
            recurrent = recurrent.masked_fill(~active[:, step, :, None], 0)

            values.append(
                self.fc3(recurrent).masked_fill(~active[:, step, :, None], 0)
            )
            states.append(
                torch.cat((recurrent, cache.reshape(b, n, CACHE_STATE)), dim=-1)
            )

        return torch.stack(values, dim=1), torch.stack(states, dim=1)

