from __future__ import annotations

import copy
import hashlib
import math

import torch
from torch import nn
from torch.nn import functional as F

from .config import (
    COMMON_BIAS_SPECS,
    MODEL_PARAMETER_COUNTS,
    R0_INPUT_MATRIX_SPECS,
    R1_CONTEXT_MATRIX_SPECS,
    R1_INPUT_MATRIX_SPECS,
    SHARED_MATRIX_SPECS,
    STATE_SCALE,
)
from .rng import HMACStream


def matrix_specs(representation: str) -> tuple[tuple[str, tuple[int, int]], ...]:
    if representation == "R0":
        return R0_INPUT_MATRIX_SPECS + SHARED_MATRIX_SPECS
    if representation == "R1":
        return R1_CONTEXT_MATRIX_SPECS + R1_INPUT_MATRIX_SPECS + SHARED_MATRIX_SPECS
    raise ValueError("representation must be R0 or R1")


def bias_specs(representation: str) -> tuple[tuple[str, int], ...]:
    if representation == "R0":
        return COMMON_BIAS_SPECS
    if representation == "R1":
        return (("b_c", 32),) + COMMON_BIAS_SPECS
    raise ValueError("representation must be R0 or R1")


class SegmentModel(nn.Module):
    """The exact R0 token-only or R1 context-conditioned direct segment model."""

    def __init__(self, representation: str) -> None:
        super().__init__()
        if representation not in ("R0", "R1"):
            raise ValueError("representation must be R0 or R1")
        self.representation = representation
        for name, shape in matrix_specs(representation):
            self.register_parameter(
                name, nn.Parameter(torch.empty(shape, dtype=torch.float32)),
            )
        for name, width in bias_specs(representation):
            self.register_parameter(
                name, nn.Parameter(torch.zeros(width, dtype=torch.float32)),
            )
        self.register_buffer("a_state", torch.tensor(STATE_SCALE, dtype=torch.float32))
        count = sum(parameter.numel() for parameter in self.parameters())
        if count != MODEL_PARAMETER_COUNTS[representation]:
            raise RuntimeError("SRF model parameter count does not match the frozen architecture")

    def ordered_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(getattr(self, name) for name, _shape in matrix_specs(self.representation)) \
            + tuple(getattr(self, name) for name, _width in bias_specs(self.representation))

    def forward(
        self,
        states: torch.Tensor,
        actions: torch.Tensor,
        words: torch.Tensor,
        lengths: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        states = states.to(dtype=torch.float32)
        actions = actions.to(dtype=torch.float32)
        words = words.to(dtype=torch.long)
        lengths = lengths.to(dtype=torch.long)
        batch_size = states.shape[0]
        if states.ndim != 2 or states.shape[1] != 9 \
                or actions.shape != (batch_size, 4):
            raise ValueError("segment model requires [B,9] states and [B,4] actions")
        if words.ndim != 2 or words.shape[0] != batch_size \
                or lengths.shape != (batch_size,):
            raise ValueError("word tensor and actual lengths do not match batch")

        q0 = torch.cat((
            states / self.a_state,
            actions,
            lengths.to(torch.float32).unsqueeze(1) / 12.0,
        ), dim=1)
        context = F.silu(F.linear(q0, self.W_c, self.b_c)) \
            if self.representation == "R1" else None
        hidden = torch.zeros((batch_size, 32), dtype=torch.float32, device=states.device)
        for position in range(words.shape[1]):
            event = F.one_hot(words[:, position].clamp_min(0), num_classes=5).to(torch.float32)
            recurrent_input = torch.cat((event, context), dim=1) \
                if context is not None else event
            reset = torch.sigmoid(
                F.linear(recurrent_input, self.W_ir, self.b_ir)
                + F.linear(hidden, self.W_hr, self.b_hr)
            )
            update = torch.sigmoid(
                F.linear(recurrent_input, self.W_iz, self.b_iz)
                + F.linear(hidden, self.W_hz, self.b_hz)
            )
            candidate_gate = torch.tanh(
                F.linear(recurrent_input, self.W_in, self.b_in)
                + reset * F.linear(hidden, self.W_hn, self.b_hn)
            )
            candidate = (1.0 - update) * candidate_gate + update * hidden
            active = (position < lengths).unsqueeze(1)
            hidden = torch.where(active, candidate, hidden)

        trunk1 = F.silu(F.linear(q0, self.W_t1, self.b_t1))
        trunk2 = F.silu(F.linear(trunk1, self.W_t2, self.b_t2))
        joined = torch.cat((trunk2, hidden), dim=1)
        state1 = F.silu(F.linear(joined, self.W_f1, self.b_f1))
        state2 = F.silu(F.linear(state1, self.W_f2, self.b_f2))
        reward1 = F.silu(F.linear(joined, self.W_g1, self.b_g1))
        reward2 = F.silu(F.linear(reward1, self.W_g2, self.b_g2))
        terminal = F.linear(state2, self.W_F, self.b_F)
        reward = F.linear(reward2, self.W_G, self.b_G).squeeze(1)
        return terminal, reward


def _xavier_values(stream: HMACStream, shape: tuple[int, int]) -> torch.Tensor:
    fan_out, fan_in = shape
    bound = math.sqrt(6.0 / (fan_in + fan_out))
    values = [
        float((2.0 * stream.uniform53() - 1.0) * bound)
        for _ in range(fan_out * fan_in)
    ]
    return torch.tensor(values, dtype=torch.float32).reshape(shape)


@torch.no_grad()
def initialized_representation_pair(
    shared_stream: HMACStream,
    r0_input_stream: HMACStream,
    r1_context_stream: HMACStream,
    r1_input_stream: HMACStream,
) -> tuple[dict[str, SegmentModel], dict[str, object]]:
    r0 = SegmentModel("R0")
    r1 = SegmentModel("R1")
    for name, shape in R0_INPUT_MATRIX_SPECS:
        getattr(r0, name).copy_(_xavier_values(r0_input_stream, shape))
    for name, shape in R1_CONTEXT_MATRIX_SPECS:
        getattr(r1, name).copy_(_xavier_values(r1_context_stream, shape))
    for name, shape in R1_INPUT_MATRIX_SPECS:
        getattr(r1, name).copy_(_xavier_values(r1_input_stream, shape))
    for name, shape in SHARED_MATRIX_SPECS:
        values = _xavier_values(shared_stream, shape)
        getattr(r0, name).copy_(values)
        getattr(r1, name).copy_(values)
        if not torch.equal(getattr(r0, name), getattr(r1, name)):
            raise RuntimeError(f"shared initialization is not byte-identical for {name}")
    for model in (r0, r1):
        for name, _width in bias_specs(model.representation):
            getattr(model, name).zero_()

    clones = {
        "S0R0": copy.deepcopy(r0),
        "S1R0": copy.deepcopy(r0),
        "S0R1": copy.deepcopy(r1),
        "S1R1": copy.deepcopy(r1),
    }
    support_clone_identity = {
        "R0": model_state_digest(clones["S0R0"]) == model_state_digest(clones["S1R0"]),
        "R1": model_state_digest(clones["S0R1"]) == model_state_digest(clones["S1R1"]),
    }
    if not all(support_clone_identity.values()):
        raise RuntimeError("support cells did not receive byte-identical initialized clones")
    information = {
        "draw_counts": {
            "init/shared": shared_stream.draw_count,
            "init/R0_input": r0_input_stream.draw_count,
            "init/R1_context": r1_context_stream.draw_count,
            "init/R1_input": r1_input_stream.draw_count,
        },
        "digests": {"R0": model_state_digest(r0), "R1": model_state_digest(r1)},
        "support_clone_identity": support_clone_identity,
    }
    return clones, information


def model_state_digest(model: nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in model.state_dict().items():
        digest.update(name.encode("utf-8"))
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()
