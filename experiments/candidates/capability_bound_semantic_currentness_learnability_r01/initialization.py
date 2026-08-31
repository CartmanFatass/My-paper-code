"""Addressed, arm-independent CBSC-LR01 learner initialization."""

from __future__ import annotations

import torch

from .addressing import block_id, glorot_scalar
from .model import DenseLearner
from .support import Purpose


def initialized_learner(purpose: Purpose, block: int) -> DenseLearner:
    """Create a fully overwritten learner without advancing ambient Torch RNG."""

    identity = block_id(purpose, block)
    with torch.random.fork_rng(devices=[], enabled=True):
        model = DenseLearner()
        with torch.no_grad():
            for layer_index, layer in enumerate(model.layers[:-1]):
                name = f"layers.{layer_index}.weight"
                flat = layer.weight.view(-1)
                values = [
                    glorot_scalar(
                        purpose.value,
                        identity,
                        name,
                        index,
                        layer.in_features,
                        layer.out_features,
                    )
                    for index in range(flat.numel())
                ]
                flat.copy_(torch.tensor(values, dtype=torch.float32))
                layer.bias.zero_()
            model.zero_output_head()
    return model


__all__ = ["initialized_learner"]
