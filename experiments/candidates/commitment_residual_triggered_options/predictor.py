"""Frozen CRTO-B1 predictor, eligibility, calibration, and packet laws.

This module contains no environment logic.  The environment-facing boundary is
the pair of :class:`CommitmentAnchor` and :class:`PredecisionTarget` records.
Their opaque ``commitment_token`` must change on every renewal, termination, or
post-decision K-switch anchor.  Equality of that token at ``tau+h`` therefore
implements the science card's continuous-commitment eligibility law, including
eligibility of an observation made immediately before a same-boundary renewal.
"""

from __future__ import annotations

import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Hashable, Iterable, Sequence

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.nn.utils.rnn import pack_padded_sequence


REVISION = "CRTO-B1-SCIENCE-20260812-04"
OPTION_COUNT = 7
TARGET_DIM = 8
PACKET_DIM = 52
HIDDEN_DIM = 64
FORECAST_HORIZONS = (4, 8, 12, 16)
CHOLESKY_DIM = TARGET_DIM * (TARGET_DIM + 1) // 2
READOUT_DIM = TARGET_DIM + CHOLESKY_DIM
CHOLESKY_DIAGONAL_FLOOR = 1e-3


def _as_cpu_float_tensor(value: torch.Tensor, *, name: str) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor")
    if value.device.type != "cpu" or not value.dtype.is_floating_point:
        raise ValueError(f"{name} must be a floating CPU tensor")
    if not bool(torch.isfinite(value).all()):
        raise ValueError(f"{name} contains a non-finite value")
    return value


@dataclass(frozen=True)
class CommitmentAnchor:
    """A predictor anchor after its option decision has been resolved."""

    episode_index: int
    commitment_time: int
    environment_slot: int
    commitment_token: Hashable
    option: int
    k: int
    origin_history: torch.Tensor

    def validate(self) -> None:
        history = _as_cpu_float_tensor(self.origin_history, name="origin_history")
        if history.ndim != 2 or history.shape[0] < 1:
            raise ValueError("origin_history must have shape [positive_time, observation_dim]")
        if not 0 <= self.option < OPTION_COUNT:
            raise ValueError("anchor option is outside the frozen seven-option set")
        if self.k not in (4, 8, 16):
            raise ValueError("anchor K must be one of 4, 8, or 16")
        if self.commitment_time < 0 or self.environment_slot < 0:
            raise ValueError("anchor indices must be nonnegative")


@dataclass(frozen=True)
class PredecisionTarget:
    """Deployable Y observed before the action at a primitive boundary."""

    episode_index: int
    primitive_time: int
    environment_slot: int
    predecision_commitment_token: Hashable
    target: torch.Tensor

    def validate(self) -> None:
        target = _as_cpu_float_tensor(self.target, name="target")
        if target.shape != (TARGET_DIM,):
            raise ValueError("predictor target must be the frozen eight-vector")
        if self.primitive_time < 0 or self.environment_slot < 0:
            raise ValueError("target indices must be nonnegative")


@dataclass(frozen=True)
class ForecastExample:
    episode_index: int
    commitment_time: int
    target_age: int
    environment_slot: int
    option: int
    k: int
    origin_history: torch.Tensor
    target: torch.Tensor

    @property
    def canonical_key(self) -> tuple[int, int, int, int]:
        return (
            self.episode_index,
            self.commitment_time,
            self.target_age,
            self.environment_slot,
        )

    def validate(self) -> None:
        if self.target_age not in FORECAST_HORIZONS:
            raise ValueError("forecast target age must be 4, 8, 12, or 16")
        CommitmentAnchor(
            self.episode_index,
            self.commitment_time,
            self.environment_slot,
            "validated",
            self.option,
            self.k,
            self.origin_history,
        ).validate()
        if _as_cpu_float_tensor(self.target, name="target").shape != (TARGET_DIM,):
            raise ValueError("forecast target must have shape [8]")


def eligible_forecast_examples(
    anchors: Iterable[CommitmentAnchor],
    targets: Iterable[PredecisionTarget],
) -> list[ForecastExample]:
    """Join only same-token predecision targets at the four frozen horizons.

    A host must emit the old token on a target observed before a renewal action
    at that same boundary, and the new token on observations after a re-anchor.
    No missing target is borrowed from a replacement commitment.
    """

    target_by_key: dict[tuple[int, int, int], PredecisionTarget] = {}
    for target in targets:
        target.validate()
        key = (target.episode_index, target.primitive_time, target.environment_slot)
        if key in target_by_key:
            raise ValueError(f"duplicate predecision target record for {key}")
        target_by_key[key] = target

    examples: list[ForecastExample] = []
    seen_anchors: set[tuple[int, int, int]] = set()
    observation_dim: int | None = None
    for anchor in anchors:
        anchor.validate()
        anchor_key = (anchor.episode_index, anchor.commitment_time, anchor.environment_slot)
        if anchor_key in seen_anchors:
            raise ValueError(f"duplicate commitment anchor for {anchor_key}")
        seen_anchors.add(anchor_key)
        if observation_dim is None:
            observation_dim = int(anchor.origin_history.shape[1])
        elif int(anchor.origin_history.shape[1]) != observation_dim:
            raise ValueError("all origin histories must use one deployable observation width")
        for horizon in FORECAST_HORIZONS:
            target = target_by_key.get(
                (anchor.episode_index, anchor.commitment_time + horizon, anchor.environment_slot)
            )
            if target is None or target.predecision_commitment_token != anchor.commitment_token:
                continue
            examples.append(ForecastExample(
                episode_index=anchor.episode_index,
                commitment_time=anchor.commitment_time,
                target_age=horizon,
                environment_slot=anchor.environment_slot,
                option=anchor.option,
                k=anchor.k,
                origin_history=anchor.origin_history,
                target=target.target,
            ))
    examples.sort(key=lambda row: row.canonical_key)
    return examples


def _xavier_uniform_from_rng(
    parameter: torch.Tensor, rng: np.random.Generator, gain: float,
) -> None:
    if parameter.ndim != 2:
        raise ValueError("Xavier initialization requires a matrix")
    fan_out, fan_in = int(parameter.shape[0]), int(parameter.shape[1])
    bound = gain * math.sqrt(6.0 / float(fan_in + fan_out))
    values = rng.uniform(-bound, bound, size=tuple(parameter.shape))
    with torch.no_grad():
        parameter.copy_(torch.as_tensor(values, dtype=parameter.dtype, device=parameter.device))


def _orthogonal_square_from_rng(parameter: torch.Tensor, rng: np.random.Generator) -> None:
    if parameter.ndim != 2 or parameter.shape[0] != parameter.shape[1]:
        raise ValueError("registered recurrent gate matrix must be square")
    raw = rng.standard_normal(tuple(parameter.shape))
    q, r = np.linalg.qr(raw)
    signs = np.sign(np.diag(r))
    signs[signs == 0.0] = 1.0
    q *= signs
    with torch.no_grad():
        parameter.copy_(torch.as_tensor(q, dtype=parameter.dtype, device=parameter.device))


def _initialize_gru(module: nn.GRU | nn.GRUCell, rng: np.random.Generator) -> None:
    gain = nn.init.calculate_gain("tanh")
    _xavier_uniform_from_rng(module.weight_ih_l0 if isinstance(module, nn.GRU) else module.weight_ih, rng, gain)
    hidden_weight = module.weight_hh_l0 if isinstance(module, nn.GRU) else module.weight_hh
    if tuple(hidden_weight.shape) != (3 * HIDDEN_DIM, HIDDEN_DIM):
        raise ValueError("predictor GRU hidden matrix violates the registered width")
    for gate in range(3):
        _orthogonal_square_from_rng(
            hidden_weight[gate * HIDDEN_DIM:(gate + 1) * HIDDEN_DIM], rng
        )
    with torch.no_grad():
        if isinstance(module, nn.GRU):
            module.bias_ih_l0.zero_()
            module.bias_hh_l0.zero_()
        else:
            module.bias_ih.zero_()
            module.bias_hh.zero_()


@dataclass(frozen=True)
class ForecastDistribution:
    horizons: tuple[int, ...]
    mean: torch.Tensor
    cholesky: torch.Tensor


class FrozenPredictor(nn.Module):
    """64-wide deployable-history GRU, four-step GRUCell, and 64-64-44 readout."""

    def __init__(self, observation_dim: int, algorithm_seed: int) -> None:
        super().__init__()
        if observation_dim <= 0:
            raise ValueError("observation_dim must be positive")
        self.observation_dim = int(observation_dim)
        self.algorithm_seed = int(algorithm_seed)
        self.observation_encoder = nn.GRU(observation_dim, HIDDEN_DIM, batch_first=True)
        self.transition_cell = nn.GRUCell(OPTION_COUNT + 2, HIDDEN_DIM)
        self.readout_hidden = nn.Linear(HIDDEN_DIM, HIDDEN_DIM)
        self.readout_output = nn.Linear(HIDDEN_DIM, READOUT_DIM)
        self._initialize_registered()

    def _initialize_registered(self) -> None:
        rng = np.random.Generator(np.random.PCG64(400000 + self.algorithm_seed))
        _initialize_gru(self.observation_encoder, rng)
        _initialize_gru(self.transition_cell, rng)
        gain = nn.init.calculate_gain("tanh")
        _xavier_uniform_from_rng(self.readout_hidden.weight, rng, gain)
        _xavier_uniform_from_rng(self.readout_output.weight, rng, gain)
        with torch.no_grad():
            self.readout_hidden.bias.zero_()
            self.readout_output.bias.zero_()

    def encode_histories(self, histories: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        if histories.ndim != 3 or histories.shape[2] != self.observation_dim:
            raise ValueError("histories must have shape [batch,time,observation_dim]")
        if lengths.ndim != 1 or lengths.shape[0] != histories.shape[0]:
            raise ValueError("lengths must have one entry per history")
        if bool(torch.any(lengths <= 0)) or bool(torch.any(lengths > histories.shape[1])):
            raise ValueError("history lengths are outside the padded tensor")
        packed = pack_padded_sequence(
            histories,
            lengths.detach().to(device="cpu", dtype=torch.int64),
            batch_first=True,
            enforce_sorted=False,
        )
        _, hidden = self.observation_encoder(packed)
        return hidden.squeeze(0)

    @staticmethod
    def _construct_cholesky(raw: torch.Tensor) -> torch.Tensor:
        if raw.shape[-1] != CHOLESKY_DIM:
            raise ValueError("Cholesky readout must contain 36 coordinates")
        result = raw.new_zeros((*raw.shape[:-1], TARGET_DIM, TARGET_DIM))
        rows, cols = torch.tril_indices(TARGET_DIM, TARGET_DIM, device=raw.device)
        result[..., rows, cols] = raw
        diagonal = torch.arange(TARGET_DIM, device=raw.device)
        result[..., diagonal, diagonal] = (
            F.softplus(result[..., diagonal, diagonal]) + CHOLESKY_DIAGONAL_FLOOR
        )
        return result

    def forecast_from_hidden(
        self,
        origin_hidden: torch.Tensor,
        option: torch.Tensor,
        k: torch.Tensor,
        horizons: Sequence[int] = FORECAST_HORIZONS,
    ) -> ForecastDistribution:
        requested = tuple(int(h) for h in horizons)
        if not requested or any(h not in FORECAST_HORIZONS for h in requested):
            raise ValueError("requested horizons must be a nonempty subset of 4,8,12,16")
        if len(set(requested)) != len(requested):
            raise ValueError("requested horizons must be unique")
        if origin_hidden.ndim != 2 or origin_hidden.shape[1] != HIDDEN_DIM:
            raise ValueError("origin_hidden must have shape [batch,64]")
        batch = origin_hidden.shape[0]
        if option.shape != (batch,) or k.shape != (batch,):
            raise ValueError("option and K must each have shape [batch]")
        if bool(torch.any((option < 0) | (option >= OPTION_COUNT))):
            raise ValueError("option index outside the frozen option set")
        if bool(torch.any(~((k == 4) | (k == 8) | (k == 16)))):
            raise ValueError("K must be 4, 8, or 16")

        hidden = origin_hidden
        outputs: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
        option_one_hot = F.one_hot(option.to(torch.int64), OPTION_COUNT).to(origin_hidden.dtype)
        for unroll_index, horizon in enumerate(FORECAST_HORIZONS, start=1):
            transition_input = torch.cat((
                option_one_hot,
                (k.to(origin_hidden.dtype) / 16.0).unsqueeze(-1),
                origin_hidden.new_full((batch, 1), 4.0 * unroll_index / 16.0),
            ), dim=-1)
            hidden = self.transition_cell(transition_input, hidden)
            raw = self.readout_output(torch.tanh(self.readout_hidden(hidden)))
            outputs[horizon] = (raw[..., :TARGET_DIM], self._construct_cholesky(raw[..., TARGET_DIM:]))
        means = torch.stack([outputs[h][0] for h in requested], dim=1)
        factors = torch.stack([outputs[h][1] for h in requested], dim=1)
        return ForecastDistribution(requested, means, factors)

    def forward(
        self,
        histories: torch.Tensor,
        lengths: torch.Tensor,
        option: torch.Tensor,
        k: torch.Tensor,
        horizons: Sequence[int] = FORECAST_HORIZONS,
    ) -> ForecastDistribution:
        return self.forecast_from_hidden(
            self.encode_histories(histories, lengths), option, k, horizons
        )


def gaussian_negative_log_likelihood(
    target: torch.Tensor, mean: torch.Tensor, cholesky: torch.Tensor,
) -> torch.Tensor:
    """Per-example exact Gaussian NLL using the emitted factor and no jitter."""

    if target.shape != mean.shape or target.shape[-1] != TARGET_DIM:
        raise ValueError("target and mean must have equal [...,8] shapes")
    if cholesky.shape != (*target.shape, TARGET_DIM):
        raise ValueError("cholesky must have shape [...,8,8]")
    whitened = torch.linalg.solve_triangular(
        cholesky, (target - mean).unsqueeze(-1), upper=False
    ).squeeze(-1)
    log_determinant = 2.0 * torch.log(torch.diagonal(cholesky, dim1=-2, dim2=-1)).sum(-1)
    return 0.5 * (
        TARGET_DIM * math.log(2.0 * math.pi)
        + whitened.square().sum(-1)
        + log_determinant
    )


def _collate_examples(
    examples: Sequence[ForecastExample], indices: Sequence[int], observation_dim: int,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    selected = [examples[int(index)] for index in indices]
    if not selected:
        raise ValueError("cannot collate an empty forecast batch")
    for example in selected:
        example.validate()
        if example.origin_history.shape[1] != observation_dim:
            raise ValueError("forecast example observation width does not match predictor")
    lengths = torch.tensor([row.origin_history.shape[0] for row in selected], dtype=torch.int64)
    histories = selected[0].origin_history.new_zeros((len(selected), int(lengths.max()), observation_dim))
    for row_index, row in enumerate(selected):
        histories[row_index, :row.origin_history.shape[0]] = row.origin_history
    option = torch.tensor([row.option for row in selected], dtype=torch.int64)
    k = torch.tensor([row.k for row in selected], dtype=torch.int64)
    horizon = torch.tensor([row.target_age for row in selected], dtype=torch.int64)
    targets = torch.stack([row.target for row in selected])
    return histories, lengths, option, k, horizon, targets


@dataclass(frozen=True)
class PredictorFitReport:
    revision: str
    algorithm_seed: int
    examples: int
    optimizer_updates: int
    final_mean_nll: float


def fit_frozen_predictor(
    model: FrozenPredictor, predictor_fit_examples: Sequence[ForecastExample],
) -> PredictorFitReport:
    """Run the registered 400-update predictor fit and return the final update."""

    examples = sorted(predictor_fit_examples, key=lambda row: row.canonical_key)
    if not examples:
        raise ValueError("predictor-fit split has no eligible examples")
    for example in examples:
        example.validate()
        allowed = (example.k == 4 and example.target_age == 4) or (
            example.k == 8 and example.target_age in (4, 8)
        )
        if not allowed:
            raise ValueError("predictor fit may use only K4/age4 and K8/age4-or-8 targets")
    if next(model.parameters()).device.type != "cpu":
        raise ValueError("registered predictor training is CPU-only")
    optimizer = torch.optim.Adam(
        model.parameters(), lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-5
    )
    permutation = np.random.Generator(
        np.random.PCG64(500000 + model.algorithm_seed)
    ).permutation(len(examples))
    cursor = 0
    final_loss = math.nan
    model.train()
    for _update in range(400):
        positions = (cursor + np.arange(256, dtype=np.int64)) % len(examples)
        indices = permutation[positions]
        cursor = int((cursor + 256) % len(examples))
        histories, lengths, option, k, horizon, target = _collate_examples(
            examples, indices, model.observation_dim
        )
        distribution = model(histories, lengths, option, k, FORECAST_HORIZONS)
        horizon_to_index = {value: index for index, value in enumerate(FORECAST_HORIZONS)}
        selected_index = torch.tensor(
            [horizon_to_index[int(value)] for value in horizon], dtype=torch.int64
        )
        batch_index = torch.arange(target.shape[0], dtype=torch.int64)
        mean = distribution.mean[batch_index, selected_index]
        factor = distribution.cholesky[batch_index, selected_index]
        loss = gaussian_negative_log_likelihood(target, mean, factor).mean()
        if not bool(torch.isfinite(loss)):
            raise RuntimeError("predictor NLL became non-finite")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        final_loss = float(loss.detach())
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return PredictorFitReport(
        revision=REVISION,
        algorithm_seed=model.algorithm_seed,
        examples=len(examples),
        optimizer_updates=400,
        final_mean_nll=final_loss,
    )


def forecast_examples(
    model: FrozenPredictor, examples: Sequence[ForecastExample], batch_size: int = 256,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Return targets, means, and factors in canonical example order."""

    ordered = sorted(examples, key=lambda row: row.canonical_key)
    if not ordered:
        raise ValueError("forecast population is empty")
    targets: list[torch.Tensor] = []
    means: list[torch.Tensor] = []
    factors: list[torch.Tensor] = []
    horizon_to_index = {value: index for index, value in enumerate(FORECAST_HORIZONS)}
    with torch.no_grad():
        for begin in range(0, len(ordered), batch_size):
            batch_indices = list(range(begin, min(begin + batch_size, len(ordered))))
            histories, lengths, option, k, horizon, target = _collate_examples(
                ordered, batch_indices, model.observation_dim
            )
            distribution = model(histories, lengths, option, k, FORECAST_HORIZONS)
            selected_index = torch.tensor(
                [horizon_to_index[int(value)] for value in horizon], dtype=torch.int64
            )
            row_index = torch.arange(target.shape[0], dtype=torch.int64)
            targets.append(target)
            means.append(distribution.mean[row_index, selected_index])
            factors.append(distribution.cholesky[row_index, selected_index])
    return torch.cat(targets), torch.cat(means), torch.cat(factors)


def whitened_residual(
    target: torch.Tensor, mean: torch.Tensor, cholesky: torch.Tensor,
) -> torch.Tensor:
    if target.shape != mean.shape or target.shape[-1] != TARGET_DIM:
        raise ValueError("target and mean must have equal [...,8] shapes")
    if cholesky.shape != (*target.shape, TARGET_DIM):
        raise ValueError("factor must have shape [...,8,8]")
    return torch.linalg.solve_triangular(
        cholesky, (target - mean).unsqueeze(-1), upper=False
    ).squeeze(-1)


@dataclass(frozen=True)
class CalibrationTable:
    """Per-coordinate sorted calibration residuals for the frozen midrank CDF."""

    sorted_residuals: torch.Tensor

    def __post_init__(self) -> None:
        values = _as_cpu_float_tensor(self.sorted_residuals, name="sorted_residuals")
        if values.ndim != 2 or values.shape[0] != TARGET_DIM or values.shape[1] < 1:
            raise ValueError("calibration table must have shape [8,positive_n]")
        if not bool(torch.all(values[:, 1:] >= values[:, :-1])):
            raise ValueError("calibration residuals must be sorted within coordinate")

    @property
    def count_per_coordinate(self) -> int:
        return int(self.sorted_residuals.shape[1])

    def cdf(self, residual: torch.Tensor) -> torch.Tensor:
        if residual.shape[-1] != TARGET_DIM:
            raise ValueError("calibration CDF requires [...,8] residuals")
        flat = residual.reshape(-1, TARGET_DIM)
        output = torch.empty_like(flat)
        for coordinate in range(TARGET_DIM):
            support = self.sorted_residuals[coordinate].to(
                device=residual.device, dtype=residual.dtype
            )
            values = flat[:, coordinate].contiguous()
            below = torch.searchsorted(support, values, right=False)
            at_or_below = torch.searchsorted(support, values, right=True)
            ties = at_or_below - below
            output[:, coordinate] = (
                below.to(residual.dtype)
                + 0.5 * ties.to(residual.dtype)
                + 0.5
            ) / float(support.numel() + 1)
        return output.reshape(residual.shape)


def fit_calibration_table(
    model: FrozenPredictor, calibration_examples: Sequence[ForecastExample],
) -> CalibrationTable:
    target, mean, factor = forecast_examples(model, calibration_examples)
    residual = whitened_residual(target, mean, factor)
    return CalibrationTable(torch.sort(residual.transpose(0, 1).contiguous(), dim=1).values.cpu())


@dataclass(frozen=True)
class PacketBundle:
    whitened: torch.Tensor
    rank: torch.Tensor
    adverse: torch.Tensor
    explicit: torch.Tensor
    raw: torch.Tensor


_ADVERSE_SIGN = torch.tensor((1, 1, 1, 1, -1, -1, -1, 1), dtype=torch.float32)


def make_packets(
    target: torch.Tensor,
    mean: torch.Tensor,
    cholesky: torch.Tensor,
    calibration: CalibrationTable,
) -> PacketBundle:
    """Construct aligned explicit and raw 52-coordinate packets."""

    residual = whitened_residual(target, mean, cholesky)
    clipped = torch.clamp(residual, min=-6.0, max=6.0)
    rank = 2.0 * calibration.cdf(residual) - 1.0
    sign = _ADVERSE_SIGN.to(device=residual.device, dtype=residual.dtype)
    adverse = torch.clamp_min(sign * residual, 0.0)
    zeros = residual.new_zeros((*residual.shape[:-1], 28))
    explicit = torch.cat((clipped, rank, adverse, zeros), dim=-1)
    rows, cols = torch.tril_indices(TARGET_DIM, TARGET_DIM, device=cholesky.device)
    raw = torch.cat((target, mean, cholesky[..., rows, cols]), dim=-1)
    if explicit.shape[-1] != PACKET_DIM or raw.shape[-1] != PACKET_DIM:
        raise RuntimeError("packet construction violated the frozen width")
    return PacketBundle(clipped, rank, adverse, explicit, raw)


def _atomic_torch_save(payload: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(descriptor)
    try:
        torch.save(payload, temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_predictor_checkpoint(
    model: FrozenPredictor,
    calibration: CalibrationTable,
    fit_report: PredictorFitReport,
    path: Path,
) -> None:
    if fit_report.revision != REVISION or fit_report.optimizer_updates != 400:
        raise ValueError("only the registered final predictor update can be checkpointed")
    if any(parameter.requires_grad for parameter in model.parameters()):
        raise ValueError("predictor must be frozen before checkpointing")
    _atomic_torch_save({
        "schema": "CRTO-B1-PREDICTOR-v4",
        "revision": REVISION,
        "algorithm_seed": model.algorithm_seed,
        "observation_dim": model.observation_dim,
        "model_state": model.state_dict(),
        "calibration_sorted_residuals": calibration.sorted_residuals,
        "fit_report": fit_report.__dict__,
    }, Path(path))


def load_predictor_checkpoint(path: Path) -> tuple[FrozenPredictor, CalibrationTable, dict[str, object]]:
    payload = torch.load(Path(path), map_location="cpu", weights_only=True)
    if payload.get("schema") != "CRTO-B1-PREDICTOR-v4" or payload.get("revision") != REVISION:
        raise ValueError("checkpoint is not the exact CRTO-B1 v4 predictor")
    model = FrozenPredictor(int(payload["observation_dim"]), int(payload["algorithm_seed"]))
    model.load_state_dict(payload["model_state"], strict=True)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    calibration = CalibrationTable(payload["calibration_sorted_residuals"])
    return model, calibration, dict(payload["fit_report"])
