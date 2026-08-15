"""Exactly matched GRU learners and frozen AdamW training routine."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable, Sequence

import torch
from torch import nn

from .domain import Example
from .generator import NAMESPACE_CONTRACT, counter_seed
from .schema import TOKEN_WIDTH, encode_panel


HIDDEN_SIZE = 48
BATCH_SIZE = 256
EPOCHS = 20
GRAD_CLIP = 1.0
OPTIMIZER = {
    "name": "AdamW", "lr": 0.001, "betas": (0.9, 0.999),
    "eps": 1e-8, "weight_decay": 1e-4,
}


class MatchedGRU(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.gru = nn.GRU(TOKEN_WIDTH, HIDDEN_SIZE, num_layers=1, batch_first=True, dropout=0.0)
        self.head = nn.Linear(HIDDEN_SIZE, 3)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        output, _ = self.gru(inputs)
        return self.head(output[:, -1, :])


def parameter_count(model: nn.Module | None = None) -> int:
    target = model if model is not None else MatchedGRU()
    return sum(parameter.numel() for parameter in target.parameters() if parameter.requires_grad)


def new_model(base_seed: int) -> MatchedGRU:
    # Each arm calls this separately. Resetting to the paired seed gives equal
    # initial values without sharing parameter objects, gradients, or state.
    torch.manual_seed(counter_seed(NAMESPACE_CONTRACT["model_initialization"], base_seed) % (2**63 - 1))
    return MatchedGRU()


@dataclass(frozen=True)
class TrainingReport:
    epochs: int
    batches: int
    example_passes: int
    final_mean_loss: float
    optimizer: dict[str, object]
    final_checkpoint_only: bool = True


def train_arm(
    model: MatchedGRU, examples: Sequence[Example], arm: str, base_seed: int, *,
    epochs: int = EPOCHS, batch_size: int = BATCH_SIZE,
    cap_check: Callable[[], None] | None = None,
) -> TrainingReport:
    """Train an arm; nondefault knobs exist only for proof-sized engineering tests."""
    torch.set_num_threads(1)
    inputs, labels = encode_panel(examples, arm)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-4,
    )
    losses: list[float] = []
    batches = 0
    model.train()
    for epoch in range(int(epochs)):
        generator = torch.Generator(device="cpu")
        generator.manual_seed(
            counter_seed(NAMESPACE_CONTRACT["minibatch_order"], base_seed, epoch) % (2**63 - 1)
        )
        order = torch.randperm(len(examples), generator=generator)
        epoch_loss = 0.0
        seen = 0
        for start in range(0, len(examples), int(batch_size)):
            indices = order[start:start + int(batch_size)]
            batch_x = inputs.index_select(0, indices)
            batch_y = labels.index_select(0, indices)
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch_x)
            loss = nn.functional.cross_entropy(logits, batch_y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            optimizer.step()
            epoch_loss += float(loss.detach()) * len(indices)
            seen += len(indices)
            batches += 1
        losses.append(epoch_loss / seen)
        if cap_check is not None:
            cap_check()
    return TrainingReport(
        epochs=int(epochs), batches=batches, example_passes=len(examples) * int(epochs),
        final_mean_loss=losses[-1], optimizer=dict(OPTIMIZER),
    )


@torch.inference_mode()
def predict_probabilities(
    model: MatchedGRU, examples: Sequence[Example], arm: str, *, batch_size: int = BATCH_SIZE,
) -> torch.Tensor:
    model.eval()
    inputs, _ = encode_panel(examples, arm)
    chunks = []
    for start in range(0, len(examples), int(batch_size)):
        logits = model(inputs[start:start + int(batch_size)])
        chunks.append(torch.softmax(logits, dim=-1))
    return torch.cat(chunks, dim=0)
