"""B09 changes gate parameterization only; collection and PPO remain B08."""
import math

import torch
from torch import nn
from torch.nn import functional as F


class Gate(nn.Module):
    def __init__(self, mode, seed, median, scale):
        super().__init__()
        if mode not in ("normalized", "scalar"):
            raise ValueError("unknown B09 gate mode")
        if not math.isfinite(median) or not math.isfinite(scale) or scale <= 0:
            raise ValueError("finite median and strictly positive fixed scale required")
        self.mode = mode
        self.b0 = nn.Parameter(torch.zeros((), dtype=torch.float32))
        if mode == "normalized":
            self.b1 = nn.Parameter(torch.zeros((), dtype=torch.float32))
        else:
            self.register_buffer("b1", torch.zeros((), dtype=torch.float32))
        self.register_buffer("median", torch.tensor(median, dtype=torch.float32))
        self.register_buffer("scale", torch.tensor(scale, dtype=torch.float32))
        # Initialization is exactly zero and consumes no RNG; seed is API parity.

    def forward(self, context):
        if context.shape[-2:] != (5, 175):
            raise ValueError("context must end in [5, 175]")
        if context.dtype != torch.float32 or context.device.type != "cpu":
            raise TypeError("gate context must be CPU float32")
        if not bool(torch.isfinite(context).all()):
            raise FloatingPointError("gate context must be finite")
        if self.mode == "scalar":
            return self.b0.expand(context.shape[:-1])
        return self.b0 + self.b1 * ((context[..., -1] - self.median) / self.scale)

    def log_prob(self, context, keep_bool):
        logits = self(context)
        if keep_bool.shape != logits.shape or keep_bool.dtype != torch.bool:
            raise TypeError("keep_bool must be bool with the gate-logit shape")
        if keep_bool.device != logits.device:
            raise ValueError("keep_bool and context must share a device")
        return torch.where(keep_bool, -F.softplus(-logits), -F.softplus(logits))
