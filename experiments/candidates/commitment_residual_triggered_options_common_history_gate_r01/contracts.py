"""Typed observable contracts shared by panel, training, and analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from numbers import Integral
from typing import Iterable, Mapping

import numpy as np

from .config import ACTION_DIM, OBSERVATION_DIM, PREDICTOR_TARGET_DIM, REPLICATES


ACTION_ORDER = (
    "KEEP", "TRACK-L", "TRACK-R", "RELAY-L", "RELAY-R",
    "TRANSIT-L", "TRANSIT-R", "RETURN",
)
ROW_REGIMES = ("K4", "K8", "K16", "K4_TO_16", "K16_TO_4")
REPLANNING_COSTS = (0.25, 4.0)


class Representation(str, Enum):
    RAW = "RAW"
    TRUE_RESIDUAL = "TRUE_RESIDUAL"
    CALIBRATED_DERANGEMENT = "CALIBRATED_DERANGEMENT"


class Budget(str, Enum):
    SHORT = "SHORT"
    LONG = "LONG"


class Split(str, Enum):
    PREDICTOR_FIT = "PREDICTOR_FIT"
    CALIBRATION = "CALIBRATION"
    TRAIN = "TRAIN"
    EVALUATION = "EVALUATION"


def _readonly(value: np.ndarray | Iterable[float], dtype: np.dtype | type) -> np.ndarray:
    array = np.asarray(value, dtype=dtype).copy()
    array.setflags(write=False)
    return array


ArrayRecord = tuple[str, tuple[int, ...], bytes]
TapeRecord = tuple[object, ...]


def canonical_array(value: np.ndarray) -> ArrayRecord:
    """Return exact dtype, shape, and C-order bytes for direct equality."""

    array = np.ascontiguousarray(value)
    return array.dtype.str, tuple(int(size) for size in array.shape), array.tobytes(order="C")


@dataclass(frozen=True)
class RowKey:
    replicate: int
    split: Split
    regime: str
    episode_index: int
    primitive_time: int
    agent: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "split", Split(self.split))
        coordinates = (self.replicate, self.episode_index, self.primitive_time, self.agent)
        if any(isinstance(value, bool) or not isinstance(value, Integral) for value in coordinates):
            raise ValueError("row-key coordinates must be integers")
        if self.replicate not in REPLICATES:
            raise ValueError("row-key replicate is outside the frozen eight replicates")
        if self.regime not in ROW_REGIMES:
            raise ValueError("row-key regime is outside the registered host regimes")
        if self.episode_index < 0 or not 0 <= self.primitive_time < 256 or not 0 <= self.agent < 4:
            raise ValueError("row-key episode, primitive-time, or agent coordinate is invalid")

    @property
    def canonical(self) -> tuple[object, ...]:
        return (
            self.replicate, self.split.value, self.regime, self.episode_index,
            self.primitive_time, self.agent,
        )

    @property
    def text(self) -> str:
        return "/".join(str(value) for value in self.canonical)


@dataclass(frozen=True)
class PanelRow:
    """One retained common-history state and its immutable native label."""

    key: RowKey
    cost: float
    elapsed_horizon: int
    history: np.ndarray
    target: np.ndarray
    mean: np.ndarray
    cholesky: np.ndarray
    legal_mask: np.ndarray
    g16: np.ndarray
    logged_action: int
    tape_record: TapeRecord

    def __post_init__(self) -> None:
        object.__setattr__(self, "history", _readonly(self.history, np.float32))
        object.__setattr__(self, "target", _readonly(self.target, np.float32))
        object.__setattr__(self, "mean", _readonly(self.mean, np.float32))
        object.__setattr__(self, "cholesky", _readonly(self.cholesky, np.float32))
        object.__setattr__(self, "legal_mask", _readonly(self.legal_mask, np.bool_))
        object.__setattr__(self, "g16", _readonly(self.g16, np.float64))
        self.validate()

    def validate(self) -> None:
        if self.history.ndim != 2 or self.history.shape[0] < 1 or self.history.shape[1] != OBSERVATION_DIM:
            raise ValueError("history must have shape [positive_time,42]")
        if self.target.shape != (PREDICTOR_TARGET_DIM,) or self.mean.shape != (PREDICTOR_TARGET_DIM,):
            raise ValueError("target and mean must have shape [8]")
        if self.cholesky.shape != (PREDICTOR_TARGET_DIM, PREDICTOR_TARGET_DIM):
            raise ValueError("Cholesky factor must have shape [8,8]")
        if not np.array_equal(self.cholesky, np.tril(self.cholesky)) or np.any(
            np.diag(self.cholesky) <= 0
        ):
            raise ValueError("Cholesky factor must be lower triangular with positive diagonal")
        if self.legal_mask.shape != (ACTION_DIM,) or not self.legal_mask[0]:
            raise ValueError("legal action mask must contain legal KEEP followed by seven options")
        if self.g16.shape != (ACTION_DIM,):
            raise ValueError("G16 must follow the eight-action printed order")
        if not np.all(np.isfinite(self.history)) or not np.all(np.isfinite(self.target)):
            raise ValueError("history and target must be finite")
        if not np.all(np.isfinite(self.mean)) or not np.all(np.isfinite(self.cholesky)):
            raise ValueError("predictor packet components must be finite")
        if not np.all(np.isfinite(self.g16[self.legal_mask])):
            raise ValueError("every legal action requires a finite G16 label")
        if not np.all(np.isnan(self.g16[~self.legal_mask])):
            raise ValueError("illegal G16 entries must be NaN")
        if self.elapsed_horizon not in (4, 8, 12, 16):
            raise ValueError("elapsed predictor horizon must be 4,8,12,16")
        if (
            isinstance(self.logged_action, bool)
            or not isinstance(self.logged_action, Integral)
            or not 0 <= int(self.logged_action) < ACTION_DIM
            or not self.legal_mask[int(self.logged_action)]
        ):
            raise ValueError("logged scripted action must be legal")
        if not isfinite(float(self.cost)) or float(self.cost) not in REPLANNING_COSTS:
            raise ValueError("replanning cost is outside the frozen cost cells")
        if not isinstance(self.tape_record, tuple) or not self.tape_record:
            raise ValueError("canonical tape record is required")

    @property
    def history_record(self) -> ArrayRecord:
        return canonical_array(self.history)

    @property
    def label_record(self) -> ArrayRecord:
        return canonical_array(self.g16)

    @property
    def canonical_record(self) -> tuple[object, ...]:
        return (
            self.key.canonical, float(self.cost), int(self.elapsed_horizon),
            self.history_record, canonical_array(self.target), canonical_array(self.mean),
            canonical_array(self.cholesky), canonical_array(self.legal_mask), self.label_record,
            int(self.logged_action), self.tape_record,
        )

    @property
    def derangement_cell(self) -> tuple[str, str, int, float]:
        return (self.key.split.value, self.key.regime, self.elapsed_horizon, float(self.cost))


@dataclass(frozen=True)
class PredictorExample:
    episode_index: int
    commitment_time: int
    target_age: int
    agent: int
    option: int
    k: int
    origin_history: np.ndarray
    target: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "origin_history", _readonly(self.origin_history, np.float32))
        object.__setattr__(self, "target", _readonly(self.target, np.float32))
        if self.origin_history.ndim != 2 or self.origin_history.shape[1] != OBSERVATION_DIM:
            raise ValueError("predictor origin history must have shape [time,42]")
        if self.target.shape != (PREDICTOR_TARGET_DIM,):
            raise ValueError("predictor target must have shape [8]")
        if self.target_age not in (4, 8, 12, 16) or self.k not in (4, 8, 16):
            raise ValueError("predictor clocks are outside the frozen horizons")

    @property
    def canonical_key(self) -> tuple[int, int, int, int]:
        return (self.episode_index, self.commitment_time, self.target_age, self.agent)


@dataclass(frozen=True)
class Panel:
    split: Split
    rows: tuple[PanelRow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "split", Split(self.split))
        if any(row.key.split is not self.split for row in self.rows):
            raise ValueError("panel contains a row from another split")
        keys = [row.key.canonical for row in self.rows]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("panel rows must be unique and canonically ordered")

    @property
    def canonical_record(self) -> tuple[tuple[object, ...], ...]:
        return tuple(row.canonical_record for row in self.rows)


@dataclass(frozen=True)
class ExposureAudit:
    initialization_state: tuple[tuple[str, ArrayRecord], ...]
    order: tuple[int, ...]
    rows: tuple[tuple[object, ...], ...]
    packets: tuple[object, ...]
    updates: int
    batch_size: int
    processed_examples: int
    logical_work: int


def assert_disjoint_panels(panels: Mapping[Split, Panel]) -> None:
    seen: set[tuple[object, ...]] = set()
    for split, panel in panels.items():
        if split is not panel.split:
            raise ValueError("panel mapping key disagrees with panel split")
        episode_keys = {(row.key.replicate, row.key.episode_index) for row in panel.rows}
        if seen.intersection(episode_keys):
            raise ValueError("panel episode key leaked across splits")
        seen.update(episode_keys)
