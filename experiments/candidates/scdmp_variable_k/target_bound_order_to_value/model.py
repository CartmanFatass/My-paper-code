from __future__ import annotations

import math
from collections.abc import Iterable

import torch
from torch import nn
from torch.nn import functional as F

from .config import MODEL_PARAMETER_COUNT, STATE_SCALE
from .rng import HMACStream


class SegmentModel(nn.Module):
    MATRIX_ORDER = (
        "W_ir", "W_iz", "W_in", "W_hr", "W_hz", "W_hn",
        "W_t1", "W_t2", "W_f1", "W_f2", "W_F", "W_g1", "W_g2", "W_G",
    )

    def __init__(self) -> None:
        super().__init__()
        shapes = {
            "W_ir": (32, 5), "W_iz": (32, 5), "W_in": (32, 5),
            "W_hr": (32, 32), "W_hz": (32, 32), "W_hn": (32, 32),
            "W_t1": (128, 14), "W_t2": (128, 128),
            "W_f1": (128, 160), "W_f2": (128, 128), "W_F": (9, 128),
            "W_g1": (128, 160), "W_g2": (128, 128), "W_G": (1, 128),
        }
        for name in self.MATRIX_ORDER:
            self.register_parameter(name, nn.Parameter(torch.empty(shapes[name], dtype=torch.float32)))
        for name, width in (
            ("b_ir", 32), ("b_iz", 32), ("b_in", 32),
            ("b_hr", 32), ("b_hz", 32), ("b_hn", 32),
            ("b_t1", 128), ("b_t2", 128),
            ("b_f1", 128), ("b_f2", 128), ("b_F", 9),
            ("b_g1", 128), ("b_g2", 128), ("b_G", 1),
        ):
            self.register_parameter(name, nn.Parameter(torch.zeros(width, dtype=torch.float32)))
        self.register_buffer("a_state", torch.tensor(STATE_SCALE, dtype=torch.float32))
        if sum(parameter.numel() for parameter in self.parameters()) != MODEL_PARAMETER_COUNT:
            raise RuntimeError("r07 model parameter count does not match the frozen architecture")

    @torch.no_grad()
    def exact_initialize(self, stream: HMACStream) -> None:
        for name in self.MATRIX_ORDER:
            matrix = getattr(self, name)
            fan_out, fan_in = matrix.shape
            bound = math.sqrt(6.0 / (fan_in + fan_out))
            values = [
                float((2.0 * stream.uniform53() - 1.0) * bound)
                for _ in range(matrix.numel())
            ]
            matrix.copy_(torch.tensor(values, dtype=torch.float32).reshape(matrix.shape))
        for name, parameter in self.named_parameters():
            if name.startswith("b_"):
                parameter.zero_()

    def ordered_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(getattr(self, name) for name in self.MATRIX_ORDER) + tuple(
            getattr(self, name) for name in (
                "b_ir", "b_iz", "b_in", "b_hr", "b_hz", "b_hn",
                "b_t1", "b_t2", "b_f1", "b_f2", "b_F",
                "b_g1", "b_g2", "b_G",
            )
        )

    def forward(self, states: torch.Tensor, actions: torch.Tensor,
                words: torch.Tensor, lengths: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        states = states.to(dtype=torch.float32)
        actions = actions.to(dtype=torch.float32)
        words = words.to(dtype=torch.long)
        lengths = lengths.to(dtype=torch.long)
        if states.ndim != 2 or states.shape[1] != 9 or actions.shape != (states.shape[0], 4):
            raise ValueError("segment model requires [B,9] states and [B,4] actions")
        if words.ndim != 2 or words.shape[0] != states.shape[0] or lengths.shape != (states.shape[0],):
            raise ValueError("word tensor and actual lengths do not match batch")
        hidden = torch.zeros((states.shape[0], 32), dtype=torch.float32, device=states.device)
        for position in range(words.shape[1]):
            event = F.one_hot(words[:, position].clamp_min(0), num_classes=5).to(torch.float32)
            r = torch.sigmoid(F.linear(event, self.W_ir, self.b_ir)
                              + F.linear(hidden, self.W_hr, self.b_hr))
            z = torch.sigmoid(F.linear(event, self.W_iz, self.b_iz)
                              + F.linear(hidden, self.W_hz, self.b_hz))
            n = torch.tanh(F.linear(event, self.W_in, self.b_in)
                           + r * F.linear(hidden, self.W_hn, self.b_hn))
            candidate = (1.0 - z) * n + z * hidden
            active = (position < lengths).unsqueeze(1)
            hidden = torch.where(active, candidate, hidden)
        q0 = torch.cat((states / self.a_state, actions, lengths.to(torch.float32).unsqueeze(1) / 12.0), 1)
        t1 = F.silu(F.linear(q0, self.W_t1, self.b_t1))
        t2 = F.silu(F.linear(t1, self.W_t2, self.b_t2))
        joined = torch.cat((t2, hidden), 1)
        f1 = F.silu(F.linear(joined, self.W_f1, self.b_f1))
        f2 = F.silu(F.linear(f1, self.W_f2, self.b_f2))
        g1 = F.silu(F.linear(joined, self.W_g1, self.b_g1))
        g2 = F.silu(F.linear(g1, self.W_g2, self.b_g2))
        terminal = F.linear(f2, self.W_F, self.b_F)
        reward = F.linear(g2, self.W_G, self.b_G).squeeze(1)
        return terminal, reward


def model_state_digest(model: nn.Module) -> str:
    import hashlib

    digest = hashlib.sha256()
    for name, value in model.state_dict().items():
        digest.update(name.encode("utf-8"))
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()
