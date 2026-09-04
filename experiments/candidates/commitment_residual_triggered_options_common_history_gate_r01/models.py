"""Fresh predictor and common-history gate architectures with explicit RNG."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import math
from typing import Iterator, Sequence

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.nn.utils.rnn import pack_padded_sequence

from .config import ACTION_DIM, OBSERVATION_DIM, PACKET_DIM, PREDICTOR_TARGET_DIM
from .contracts import ArrayRecord, canonical_array


HIDDEN_DIM = 64
ADAPTER_HIDDEN_DIM = 64
ADAPTER_OUTPUT_DIM = 32
HEAD_HIDDEN_DIM = 64
FORECAST_HORIZONS = (4, 8, 12, 16)
CHOLESKY_DIM = PREDICTOR_TARGET_DIM * (PREDICTOR_TARGET_DIM + 1) // 2
CHOLESKY_DIAGONAL_FLOOR = 1e-3


@contextmanager
def _preserve_ambient_torch_rng() -> Iterator[None]:
    """Construct a module without changing the process RNG stream."""

    state = torch.random.get_rng_state()
    try:
        yield
    finally:
        torch.random.set_rng_state(state)


def _fill_parameter(parameter: torch.Tensor, rng: np.random.Generator) -> None:
    if parameter.ndim >= 2:
        fan_in = int(parameter.shape[-1])
        fan_out = int(parameter.shape[-2])
        bound = math.sqrt(6.0 / float(fan_in + fan_out))
        values = rng.uniform(-bound, bound, size=tuple(parameter.shape))
    else:
        values = np.zeros(tuple(parameter.shape), dtype=np.float64)
    with torch.no_grad():
        parameter.copy_(torch.as_tensor(values, dtype=parameter.dtype))


def initialize_from_rng(module: nn.Module, rng: np.random.Generator) -> None:
    """Initialize every registered parameter from one explicit NumPy stream."""

    for _name, parameter in module.named_parameters():
        _fill_parameter(parameter, rng)


def canonical_state(module: nn.Module) -> tuple[tuple[str, ArrayRecord], ...]:
    """Return parameter names and exact tensor bytes for direct equality."""

    return tuple(
        (name, canonical_array(tensor.detach().cpu().contiguous().numpy()))
        for name, tensor in sorted(module.state_dict().items())
    )


class CommonHistoryGate(nn.Module):
    """GRU(42,64), 52->64->32 adapter, and 96->64->8 value head."""

    def __init__(self, initialization_rng: np.random.Generator) -> None:
        super().__init__()
        if not isinstance(initialization_rng, np.random.Generator):
            raise TypeError("gate initialization requires an explicit NumPy Generator")
        with _preserve_ambient_torch_rng():
            self.history_encoder = nn.GRU(OBSERVATION_DIM, HIDDEN_DIM, batch_first=True)
            self.packet_adapter_1 = nn.Linear(PACKET_DIM, ADAPTER_HIDDEN_DIM)
            self.packet_adapter_2 = nn.Linear(ADAPTER_HIDDEN_DIM, ADAPTER_OUTPUT_DIM)
            self.action_head_1 = nn.Linear(HIDDEN_DIM + ADAPTER_OUTPUT_DIM, HEAD_HIDDEN_DIM)
            self.action_head_2 = nn.Linear(HEAD_HIDDEN_DIM, ACTION_DIM)
        initialize_from_rng(self, initialization_rng)

    def forward(
        self, histories: torch.Tensor, lengths: torch.Tensor, packets: torch.Tensor,
    ) -> torch.Tensor:
        if histories.ndim != 3 or histories.shape[-1] != OBSERVATION_DIM:
            raise ValueError("histories must have shape [batch,time,42]")
        if lengths.shape != (histories.shape[0],):
            raise ValueError("lengths must have one entry per history")
        if packets.shape != (histories.shape[0], PACKET_DIM):
            raise ValueError("packets must have shape [batch,52]")
        if bool(torch.any(lengths <= 0)) or bool(torch.any(lengths > histories.shape[1])):
            raise ValueError("history length is outside its padded tensor")
        packed = pack_padded_sequence(
            histories, lengths.detach().cpu().to(torch.int64), batch_first=True,
            enforce_sorted=False,
        )
        _, hidden = self.history_encoder(packed)
        packet_hidden = torch.tanh(self.packet_adapter_1(packets))
        packet_hidden = torch.tanh(self.packet_adapter_2(packet_hidden))
        joined = torch.cat((hidden.squeeze(0), packet_hidden), dim=-1)
        return self.action_head_2(torch.tanh(self.action_head_1(joined)))


@dataclass(frozen=True)
class ForecastDistribution:
    horizons: tuple[int, ...]
    mean: torch.Tensor
    cholesky: torch.Tensor


class FreshPredictor(nn.Module):
    """Provisional fresh clean-room predictor R01.

    This is an ``INHERITED_ASSUMPTION`` implementation seam.  The registered
    runner refuses result execution until its law is frozen by source revision.
    """

    def __init__(self, initialization_rng: np.random.Generator) -> None:
        super().__init__()
        if not isinstance(initialization_rng, np.random.Generator):
            raise TypeError("predictor initialization requires an explicit NumPy Generator")
        with _preserve_ambient_torch_rng():
            self.observation_encoder = nn.GRU(OBSERVATION_DIM, HIDDEN_DIM, batch_first=True)
            self.transition_cell = nn.GRUCell(7 + 2, HIDDEN_DIM)
            self.readout_hidden = nn.Linear(HIDDEN_DIM, HIDDEN_DIM)
            self.readout_output = nn.Linear(HIDDEN_DIM, PREDICTOR_TARGET_DIM + CHOLESKY_DIM)
        initialize_from_rng(self, initialization_rng)

    @staticmethod
    def _cholesky(raw: torch.Tensor) -> torch.Tensor:
        result = raw.new_zeros((*raw.shape[:-1], PREDICTOR_TARGET_DIM, PREDICTOR_TARGET_DIM))
        rows, cols = torch.tril_indices(PREDICTOR_TARGET_DIM, PREDICTOR_TARGET_DIM, device=raw.device)
        result[..., rows, cols] = raw
        diagonal = torch.arange(PREDICTOR_TARGET_DIM, device=raw.device)
        result[..., diagonal, diagonal] = F.softplus(
            result[..., diagonal, diagonal]
        ) + CHOLESKY_DIAGONAL_FLOOR
        return result

    def encode(self, histories: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        packed = pack_padded_sequence(
            histories, lengths.detach().cpu().to(torch.int64), batch_first=True,
            enforce_sorted=False,
        )
        _, hidden = self.observation_encoder(packed)
        return hidden.squeeze(0)

    def forecast_from_hidden(
        self, hidden: torch.Tensor, option: torch.Tensor, k: torch.Tensor,
        horizons: Sequence[int] = FORECAST_HORIZONS,
    ) -> ForecastDistribution:
        requested = tuple(int(value) for value in horizons)
        if not requested or len(set(requested)) != len(requested) or any(
            value not in FORECAST_HORIZONS for value in requested
        ):
            raise ValueError("horizons must be a unique nonempty subset of 4,8,12,16")
        outputs: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
        origin = hidden
        one_hot = F.one_hot(option.to(torch.int64), 7).to(hidden.dtype)
        for index, horizon in enumerate(FORECAST_HORIZONS, start=1):
            transition = torch.cat((
                one_hot, (k.to(hidden.dtype) / 16.0).unsqueeze(-1),
                hidden.new_full((hidden.shape[0], 1), 4.0 * index / 16.0),
            ), dim=-1)
            hidden = self.transition_cell(transition, hidden)
            raw = self.readout_output(torch.tanh(self.readout_hidden(hidden)))
            outputs[horizon] = (
                raw[..., :PREDICTOR_TARGET_DIM], self._cholesky(raw[..., PREDICTOR_TARGET_DIM:]),
            )
        return ForecastDistribution(
            requested,
            torch.stack([outputs[h][0] for h in requested], dim=1),
            torch.stack([outputs[h][1] for h in requested], dim=1),
        )

    def forward(
        self, histories: torch.Tensor, lengths: torch.Tensor, option: torch.Tensor,
        k: torch.Tensor, horizons: Sequence[int] = FORECAST_HORIZONS,
    ) -> ForecastDistribution:
        return self.forecast_from_hidden(self.encode(histories, lengths), option, k, horizons)

    def packet_forecast(
        self, origin_history: np.ndarray, option: int, k: int, elapsed_horizon: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        history = torch.as_tensor(np.asarray(origin_history), dtype=torch.float32).unsqueeze(0)
        lengths = torch.tensor([history.shape[1]], dtype=torch.int64)
        with torch.no_grad():
            output = self(
                history, lengths, torch.tensor([option]), torch.tensor([k]), (elapsed_horizon,),
            )
        return (
            output.mean[0, 0].cpu().numpy().astype(np.float32),
            output.cholesky[0, 0].cpu().numpy().astype(np.float32),
        )


def gaussian_nll(target: torch.Tensor, mean: torch.Tensor, cholesky: torch.Tensor) -> torch.Tensor:
    if target.shape != mean.shape or target.shape[-1] != PREDICTOR_TARGET_DIM:
        raise ValueError("target and mean must have equal [...,8] shapes")
    whitened = torch.linalg.solve_triangular(
        cholesky, (target - mean).unsqueeze(-1), upper=False,
    ).squeeze(-1)
    log_det = 2.0 * torch.log(torch.diagonal(cholesky, dim1=-2, dim2=-1)).sum(-1)
    return 0.5 * (
        PREDICTOR_TARGET_DIM * math.log(2.0 * math.pi) + whitened.square().sum(-1) + log_det
    )
