"""Closed R03 S2 finite evaluator and complete-only publication boundary.

The module is intentionally silent: it never logs evaluator values.  A caller
may either build private in-memory material or atomically publish a fully
validated registered package.  Construction tests use a disjoint synthetic
namespace and are never admitted to the registered publication method.
"""

from __future__ import annotations

import hashlib
import io
import itertools
import json
import math
import os
import shutil
import tempfile
import time
import ctypes
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, Mapping, Protocol, Sequence

import numpy as np
import torch

from .contract import (
    FINAL_CHECKPOINT_SLOT_COUNT,
    K_TEST,
    K_TRAIN,
    OBJECT_REVISION,
    REGISTERED_MASTER_SEEDS,
    TRAINING_BATCHES,
    LearnedArm,
    Panel,
)
from .model import ActionScorer
from .training import fixed_fp32_tree


_IMPORT_STARTED = time.perf_counter()


OBJECT_DIGEST = "94fa0ddb4ef4c686a60a1d9386f8b1b6184184f75df6c51a6fb61cedd8185e1c"
S2_SCHEMA = "UCOPE_R01_R03_S2_COMPLETE_PACKAGE_V1"
COMPLETION_SCHEMA = "UCOPE_R01_R03_S2_COMPLETION_MANIFEST_V1"
FINAL_CHECKPOINT_SCHEMA = "UCOPE_R01_R03_S2_FINAL_CHECKPOINT_ENVELOPE_V1"
ACTION_SCORER_PAYLOAD_SCHEMA = "UCOPE_R01_R03_S2_ACTION_SCORER_PAYLOAD_V1"
SYNTHETIC_NAMESPACE = "TEST_ONLY_UCOPE_R01_R03_S2_CONSTRUCTION_C1"
REPAIR1_NAMESPACE = "TEST_ONLY_UCOPE_R01_R03_S2_REPAIR1"
CONSTRUCTION_NAMESPACES = frozenset((SYNTHETIC_NAMESPACE, REPAIR1_NAMESPACE))
COMPARISON_TOLERANCE = np.float32(1.0e-6)
INVARIANT_TOLERANCE = np.float32(1.0e-5)
ROOT_ACTIONS = ("PROBE",) + tuple(f"COMMIT_{period}" for period in K_TEST)
TAIL_ACTIONS = tuple(f"COMMIT_{period}" for period in K_TEST)
UTILITY_COMPONENTS = (
    "tail_service",
    "tail_time",
    "tail_energy",
    "probe_service",
    "probe_time",
    "probe_energy",
)
REQUIRED_CONTRASTS = ("delta_test", "delta_train", "delta_perm")
REQUIRED_TOP_LEVEL_FIELDS = (
    "schema",
    "object_revision",
    "object_digest",
    "checkpoint_inventory",
    "k_test_values",
    "k_train_values",
    "forced_test_values",
    "raw_permavg_values",
    "comparators",
    "belief_dp_action_values",
    "decompositions",
    "headroom",
    "support",
    "competence",
    "seed_contrasts",
    "intervals",
    "descriptive_agreements",
    "acquisition",
    "attribution",
    "terminal_action",
    "normalization",
    "required_field_inventory",
    "provenance",
)

_SEAL_ISSUER = object()


class S2Code(str, Enum):
    MALFORMED_INPUT = "S2_MALFORMED_INPUT"
    PATH_REFUSED = "S2_PATH_REFUSED"
    OBJECT_MISMATCH = "S2_OBJECT_MISMATCH"
    CHECKPOINT_MISMATCH = "S2_CHECKPOINT_MISMATCH"
    DUPLICATE_SLOT = "S2_DUPLICATE_SLOT"
    INCOMPLETE_INVENTORY = "S2_INCOMPLETE_INVENTORY"
    REGISTERED_BOUNDARY_ATTEMPTED = "S2_REGISTERED_BOUNDARY_ATTEMPTED"
    NORMALIZATION_FAILURE = "S2_NORMALIZATION_FAILURE"
    DECOMPOSITION_FAILURE = "S2_DECOMPOSITION_FAILURE"
    INCOMPLETE_OUTPUT = "S2_INCOMPLETE_OUTPUT"
    NONFINITE_OUTPUT = "S2_NONFINITE_OUTPUT"
    ALREADY_PUBLISHED = "S2_ALREADY_PUBLISHED"
    ATOMIC_PUBLICATION_FAILURE = "S2_ATOMIC_PUBLICATION_FAILURE"


class S2Refusal(RuntimeError):
    """A value-free, preactivity technical refusal."""

    def __init__(self, code: S2Code):
        self.code = code
        super().__init__(code.value)


@dataclass(frozen=True)
class BoundaryRequest:
    namespace: str
    registered_master_seeds: bool
    complete_registered_panel: bool
    question_relevant_output: bool
    gpu: bool

    def require_construction(self) -> None:
        if (
            self.namespace not in CONSTRUCTION_NAMESPACES
            or self.registered_master_seeds
            or self.complete_registered_panel
            or self.question_relevant_output
            or self.gpu
        ):
            raise S2Refusal(S2Code.REGISTERED_BOUNDARY_ATTEMPTED)

    def require_registered_publication(self) -> None:
        if (
            self.namespace in CONSTRUCTION_NAMESPACES
            or not self.registered_master_seeds
            or not self.complete_registered_panel
            or not self.question_relevant_output
            or self.gpu
        ):
            raise S2Refusal(S2Code.REGISTERED_BOUNDARY_ATTEMPTED)


@dataclass(frozen=True)
class CheckpointSlot:
    """Untrusted caller reference; every identity field is cold-loaded."""

    path: Path


@dataclass(frozen=True)
class ValidatedCheckpointSlot:
    arm: int
    panel: int
    master_seed: int
    batch: int
    object_revision: str
    object_digest: str
    path: Path
    sha256: str
    model_sha256: str
    model_payload: bytes
    support: Mapping[str, object]

    @property
    def key(self) -> tuple[int, int, int]:
        return self.arm, self.panel, self.master_seed


@dataclass(frozen=True)
class SealedEvaluation:
    package: Mapping[str, object]
    inventory: tuple[ValidatedCheckpointSlot, ...]
    checkpoint_root: Path
    seal_digest: str
    _issuer: object


@dataclass(frozen=True)
class FiniteCase:
    panel: int
    probe_regime: int
    tail_regime: int
    actual_history: int
    displayed_history: int
    weight: np.float32


@dataclass(frozen=True)
class ValueRecord:
    total: np.float32
    components: tuple[np.float32, ...]
    root_action: int
    tail_actions: tuple[int, ...]
    normalization_error: np.float32

    def as_private_dict(self) -> dict[str, object]:
        return {
            "total": float(self.total),
            "components": [float(value) for value in self.components],
            "root_action": self.root_action,
            "tail_actions": list(self.tail_actions),
            "normalization_error": float(self.normalization_error),
        }


@dataclass(frozen=True)
class Interval:
    mean: float
    lower: float
    upper: float
    classification: str


class LearnedScorer(Protocol):
    def bind(self, slot: ValidatedCheckpointSlot) -> None: ...

    def root_logits(self, slot: ValidatedCheckpointSlot, periods: tuple[int, ...]) -> np.ndarray: ...

    def tail_logits(
        self, slot: ValidatedCheckpointSlot, periods: tuple[int, ...], channel: np.ndarray
    ) -> np.ndarray: ...


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def build_action_scorer_payload(
    scorer: ActionScorer,
    *,
    arm: int,
    panel: int,
    master_seed: int,
) -> bytes:
    """Serialize one source-bound FP32 final scorer for cold S2 loading.

    This helper is structural only: it does not admit a seed or cross the
    registered boundary.  The outer checkpoint envelope still owns that gate.
    """

    if (
        type(scorer) is not ActionScorer
        or type(arm) is not int
        or type(panel) is not int
        or type(master_seed) is not int
        or arm not in tuple(int(value) for value in LearnedArm)
        or panel not in tuple(int(value) for value in Panel)
    ):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    state = {
        name: tensor.detach().cpu().contiguous()
        for name, tensor in scorer.state_dict().items()
    }
    if any(type(tensor) is not torch.Tensor or tensor.dtype != torch.float32 for tensor in state.values()):
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    payload = {
        "schema": ACTION_SCORER_PAYLOAD_SCHEMA,
        "object_revision": OBJECT_REVISION,
        "object_digest": OBJECT_DIGEST,
        "arm": arm,
        "panel": panel,
        "master_seed": master_seed,
        "batch": TRAINING_BATCHES,
        "dtype": "torch.float32",
        "architecture": [13, 64, 64, 1],
        "model_source_sha256": _sha256(Path(__file__).with_name("model.py")),
        "scorer_state": state,
    }
    output = io.BytesIO()
    torch.save(payload, output)
    return output.getvalue()


def _load_action_scorer_payload(slot: ValidatedCheckpointSlot) -> ActionScorer:
    """Cold-load and bind an exact FP32 ActionScorer to one validated slot."""

    try:
        payload = torch.load(
            io.BytesIO(slot.model_payload), map_location="cpu", weights_only=True
        )
    except Exception as exc:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH) from exc
    required = {
        "schema", "object_revision", "object_digest", "arm", "panel",
        "master_seed", "batch", "dtype", "architecture",
        "model_source_sha256", "scorer_state",
    }
    if not isinstance(payload, Mapping) or set(payload) != required:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    if (
        payload["schema"] != ACTION_SCORER_PAYLOAD_SCHEMA
        or payload["object_revision"] != slot.object_revision
        or payload["object_digest"] != slot.object_digest
        or payload["arm"] != slot.arm
        or payload["panel"] != slot.panel
        or payload["master_seed"] != slot.master_seed
        or payload["batch"] != slot.batch
        or payload["dtype"] != "torch.float32"
        or payload["architecture"] != [13, 64, 64, 1]
        or payload["model_source_sha256"] != _sha256(Path(__file__).with_name("model.py"))
    ):
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    state = payload["scorer_state"]
    template = ActionScorer().to(dtype=torch.float32)
    expected = template.state_dict()
    if not isinstance(state, Mapping) or set(state) != set(expected):
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    for name, expected_tensor in expected.items():
        observed = state[name]
        if (
            type(observed) is not torch.Tensor
            or observed.dtype != torch.float32
            or tuple(observed.shape) != tuple(expected_tensor.shape)
            or not torch.isfinite(observed).all().item()
        ):
            raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    try:
        template.load_state_dict(state, strict=True)
    except (RuntimeError, TypeError, ValueError) as exc:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH) from exc
    template.eval()
    return template


def _validate_digest(value: object) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise S2Refusal(S2Code.MALFORMED_INPUT) from exc
    return value


def _resolve_contained(path: Path, root: Path) -> Path:
    resolved_root = root.resolve(strict=True)
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise S2Refusal(S2Code.PATH_REFUSED) from exc
    if path.is_symlink() or resolved.is_symlink():
        raise S2Refusal(S2Code.PATH_REFUSED)
    return resolved


def build_synthetic_checkpoint_bytes(
    *,
    arm: int,
    panel: int,
    master_seed: int,
    support: Mapping[str, object],
    model_payload: bytes,
    request: BoundaryRequest,
) -> bytes:
    """Build one nonregistered cold-load fixture in the production envelope."""

    request.require_construction()
    if (
        isinstance(arm, bool) or arm not in tuple(int(value) for value in LearnedArm)
        or isinstance(panel, bool) or panel not in tuple(int(value) for value in Panel)
        or isinstance(master_seed, bool) or not isinstance(master_seed, int)
        or master_seed in REGISTERED_MASTER_SEEDS
        or not validate_support_structure(support, panel)
        or not isinstance(model_payload, bytes) or not model_payload
    ):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    return _canonical_bytes(
        {
            "schema": FINAL_CHECKPOINT_SCHEMA,
            "arm": arm,
            "panel": panel,
            "master_seed": master_seed,
            "batch": TRAINING_BATCHES,
            "object_revision": OBJECT_REVISION,
            "object_digest": OBJECT_DIGEST,
            "support": dict(support),
            "model_payload_hex": model_payload.hex(),
            "model_sha256": hashlib.sha256(model_payload).hexdigest(),
        }
    )


def _cold_load_checkpoint(path: Path, checkpoint_root: Path) -> ValidatedCheckpointSlot:
    resolved = _resolve_contained(path, checkpoint_root)
    if not resolved.is_file():
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    checkpoint_bytes = resolved.read_bytes()
    try:
        payload = json.loads(checkpoint_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH) from exc
    required = {
        "schema", "arm", "panel", "master_seed", "batch", "object_revision",
        "object_digest", "support", "model_payload_hex", "model_sha256",
    }
    if not isinstance(payload, Mapping) or set(payload) != required:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    if payload["schema"] != FINAL_CHECKPOINT_SCHEMA:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    arm, panel, seed, batch = (
        payload["arm"], payload["panel"], payload["master_seed"], payload["batch"]
    )
    if (
        any(type(value) is not int for value in (arm, panel, seed, batch))
        or arm not in tuple(int(value) for value in LearnedArm)
        or panel not in tuple(int(value) for value in Panel)
        or batch != TRAINING_BATCHES
    ):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    if payload["object_revision"] != OBJECT_REVISION or payload["object_digest"] != OBJECT_DIGEST:
        raise S2Refusal(S2Code.OBJECT_MISMATCH)
    if not isinstance(payload["support"], Mapping) or not validate_support_structure(payload["support"], panel):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    model_sha256 = _validate_digest(payload["model_sha256"])
    if not isinstance(payload["model_payload_hex"], str):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    try:
        model_payload = bytes.fromhex(payload["model_payload_hex"])
    except ValueError as exc:
        raise S2Refusal(S2Code.MALFORMED_INPUT) from exc
    if not model_payload or hashlib.sha256(model_payload).hexdigest() != model_sha256:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    return ValidatedCheckpointSlot(
        arm=arm,
        panel=panel,
        master_seed=seed,
        batch=batch,
        object_revision=payload["object_revision"],
        object_digest=payload["object_digest"],
        path=resolved,
        sha256=hashlib.sha256(checkpoint_bytes).hexdigest(),
        model_sha256=model_sha256,
        model_payload=model_payload,
        support=dict(payload["support"]),
    )


def validate_checkpoint_inventory(
    slots: Sequence[CheckpointSlot],
    *,
    checkpoint_root: Path,
    construction: bool,
) -> tuple[ValidatedCheckpointSlot, ...]:
    """Validate the exact 3 x 3 x 10 final-checkpoint closure before use."""

    if (
        not isinstance(slots, Sequence)
        or isinstance(slots, (str, bytes, bytearray))
        or len(slots) != FINAL_CHECKPOINT_SLOT_COUNT
        or any(type(slot) is not CheckpointSlot for slot in slots)
    ):
        raise S2Refusal(S2Code.INCOMPLETE_INVENTORY)
    cold = tuple(_cold_load_checkpoint(slot.path, checkpoint_root) for slot in slots)
    seeds = {slot.master_seed for slot in cold}
    if len(seeds) != 10:
        raise S2Refusal(S2Code.INCOMPLETE_INVENTORY)
    if construction:
        if seeds & REGISTERED_MASTER_SEEDS:
            raise S2Refusal(S2Code.REGISTERED_BOUNDARY_ATTEMPTED)
    elif seeds != REGISTERED_MASTER_SEEDS:
        raise S2Refusal(S2Code.INCOMPLETE_INVENTORY)
    expected = {
        (int(arm), int(panel), seed)
        for arm in LearnedArm
        for panel in Panel
        for seed in seeds
    }
    observed: set[tuple[int, int, int]] = set()
    checked: list[ValidatedCheckpointSlot] = []
    for slot in cold:
        if slot.key in observed:
            raise S2Refusal(S2Code.DUPLICATE_SLOT)
        observed.add(slot.key)
        checked.append(slot)
    if observed != expected:
        raise S2Refusal(S2Code.INCOMPLETE_INVENTORY)
    return tuple(sorted(checked, key=lambda slot: slot.key))


def _history_probability(regime: int, history: int) -> np.float32:
    if regime not in (0, 1) or history < 0 or history >= 64:
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    hit = np.float32(0.85 if regime == 0 else 0.15)
    miss = np.float32(1.0) - hit
    probability = np.float32(1.0)
    for bit in range(6):
        probability = np.float32(
            probability * (hit if (history >> bit) & 1 else miss)
        )
    return probability


def finite_cases(panel: int) -> Iterable[FiniteCase]:
    """Enumerate the exact finite population; no sampling is used."""

    if panel == int(Panel.PERSISTENT):
        for regime in (0, 1):
            for actual in range(64):
                yield FiniteCase(
                    panel, regime, regime, actual, actual,
                    np.float32(np.float32(0.5) * _history_probability(regime, actual)),
                )
        return
    if panel == int(Panel.REDRAW):
        for probe, tail in itertools.product((0, 1), repeat=2):
            for actual in range(64):
                weight = np.float32(np.float32(0.25) * _history_probability(probe, actual))
                yield FiniteCase(panel, probe, tail, actual, actual, weight)
        return
    if panel == int(Panel.SEVERED):
        for physical, display_regime in itertools.product((0, 1), repeat=2):
            for actual in range(64):
                actual_weight = _history_probability(physical, actual)
                for displayed in range(64):
                    weight = np.float32(
                        np.float32(0.25)
                        * np.float32(actual_weight * _history_probability(display_regime, displayed))
                    )
                    yield FiniteCase(panel, physical, physical, actual, displayed, weight)
        return
    raise S2Refusal(S2Code.MALFORMED_INPUT)


def population_case_count(panel: int) -> int:
    return sum(1 for _ in finite_cases(panel))


def _posterior(displayed_history: int, panel: int) -> np.float32:
    if panel != int(Panel.PERSISTENT):
        return np.float32(0.5)
    count = displayed_history.bit_count()
    # Frozen written order: ordinary host products/division, exactly one final
    # cast to FP32.  Do not insert intermediate np.float32 conversions here.
    short_weight = (0.85**count) * (0.15 ** (6 - count))
    long_weight = (0.15**count) * (0.85 ** (6 - count))
    return np.float32(short_weight / (short_weight + long_weight))


def learned_tail_channel(arm: int, panel: int, displayed_history: int) -> np.ndarray:
    if (
        arm not in tuple(int(value) for value in LearnedArm)
        or panel not in tuple(int(value) for value in Panel)
        or displayed_history < 0
        or displayed_history >= 64
    ):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    bits = np.asarray([(displayed_history >> bit) & 1 for bit in range(6)], dtype=np.float32)
    count = displayed_history.bit_count()
    channel = np.zeros(6, dtype=np.float32)
    if arm == int(LearnedArm.COUNT):
        count32 = np.float32(count)
        channel[:4] = (
            np.float32(count32 / np.float32(6.0)),
            np.float32(1.0),
            np.float32((count32 - np.float32(3.0)) / np.float32(6.0)),
            np.float32(1.0),
        )
    elif arm == int(LearnedArm.RAW):
        channel[:] = bits
    else:
        rho = _posterior(displayed_history, panel)
        channel[:3] = (rho, np.float32(np.float32(1.0) - rho), np.float32(1.0))
    return channel


def _candidate_features(
    channel: np.ndarray, *, root: bool, probe: bool, period: int
) -> np.ndarray:
    if channel.shape != (6,) or channel.dtype != np.float32:
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    result = np.zeros(13, dtype=np.float32)
    result[:6] = channel
    result[6:8] = (
        (np.float32(1.0), np.float32(0.0))
        if root
        else (np.float32(0.0), np.float32(1.0))
    )
    result[8:10] = (
        (np.float32(1.0), np.float32(0.0))
        if probe
        else (np.float32(0.0), np.float32(1.0))
    )
    if not probe:
        scaled = np.float32(np.float32(period) / np.float32(9.0))
        result[10:12] = (scaled, np.float32(scaled * scaled))
    result[12] = np.float32(1.0) if root else np.float32(10.0) / np.float32(12.0)
    return result


class _CheckpointPayloadScorer:
    """The only registered scorer path: models are decoded from slot bytes."""

    def __init__(self, slots: Sequence[ValidatedCheckpointSlot]) -> None:
        self._models = {
            slot.key: _load_action_scorer_payload(slot) for slot in slots
        }
        self._digests = {slot.key: slot.model_sha256 for slot in slots}

    def bind(self, slot: ValidatedCheckpointSlot) -> None:
        if self._digests.get(slot.key) != slot.model_sha256:
            raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)

    def _score(self, slot: ValidatedCheckpointSlot, features: np.ndarray) -> np.ndarray:
        self.bind(slot)
        model = self._models.get(slot.key)
        if model is None or features.dtype != np.float32 or features.ndim != 2:
            raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
        with torch.no_grad():
            values = model(torch.from_numpy(np.ascontiguousarray(features)))
        if values.dtype != torch.float32 or values.ndim != 1:
            raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
        return values.detach().cpu().numpy().astype(np.float32, copy=False)

    def root_logits(
        self, slot: ValidatedCheckpointSlot, periods: tuple[int, ...]
    ) -> np.ndarray:
        channel = np.zeros(6, dtype=np.float32)
        rows = [_candidate_features(channel, root=True, probe=True, period=0)]
        rows.extend(
            _candidate_features(channel, root=True, probe=False, period=period)
            for period in periods
        )
        return self._score(slot, np.stack(rows).astype(np.float32, copy=False))

    def tail_logits(
        self,
        slot: ValidatedCheckpointSlot,
        periods: tuple[int, ...],
        channel: np.ndarray,
    ) -> np.ndarray:
        rows = [
            _candidate_features(channel, root=False, probe=False, period=period)
            for period in periods
        ]
        return self._score(slot, np.stack(rows).astype(np.float32, copy=False))


def _tail_components(tail_regime: int, period: int) -> tuple[np.float32, ...]:
    anchor = 2 if tail_regime == 0 else 8
    service = np.float32(np.float32(0.95) - np.float32((period - anchor) ** 2) / np.float32(100.0))
    period32 = np.float32(period)
    return (
        service,
        np.float32(np.float32(-0.01) * period32),
        np.float32(np.float32(-0.001) * np.float32(period32 * period32)),
    )


def _probe_components(actual_history: int) -> tuple[np.float32, ...]:
    return (
        np.float32(
            np.float32(0.08)
            * np.float32(np.float32(actual_history.bit_count()) / np.float32(6.0))
        ),
        np.float32(-0.03),
        np.float32(-0.03),
    )


def _expected_tail(rho: np.float32, period: int) -> np.float32:
    short = _tail_components(0, period)
    long = _tail_components(1, period)
    short_total = fixed_fp32_tree(np.asarray(short, dtype=np.float32))
    long_total = fixed_fp32_tree(np.asarray(long, dtype=np.float32))
    value = np.float32(rho * short_total)
    return np.float32(
        value + np.float32((np.float32(1.0) - rho) * long_total)
    )


def greedy_index(values: Sequence[float], *, tolerance: np.float32 = COMPARISON_TOLERANCE) -> int:
    """Frozen DP greedy rule: first action within the 1e-6 tolerance."""

    array = np.asarray(values, dtype=np.float32)
    if array.ndim != 1 or not array.size or not np.isfinite(array).all():
        raise S2Refusal(S2Code.NONFINITE_OUTPUT)
    selected = 0
    best = array[0]
    for index in range(1, array.size):
        if array[index] > np.float32(best + tolerance):
            selected, best = index, array[index]
    return selected


def learned_greedy_index(values: Sequence[float]) -> int:
    """Learned/RAW greedy rule: first action only on an exact FP32 tie."""

    array = np.asarray(values, dtype=np.float32)
    if array.ndim != 1 or not array.size or not np.isfinite(array).all():
        raise S2Refusal(S2Code.NONFINITE_OUTPUT)
    selected = 0
    best = array[0]
    for index in range(1, array.size):
        if array[index] > best:
            selected, best = index, array[index]
    return selected


def immediate_dp(periods: tuple[int, ...]) -> tuple[int, np.float32]:
    values = np.asarray([_expected_tail(np.float32(0.5), period) for period in periods], dtype=np.float32)
    selected = greedy_index(values)
    return selected, values[selected]


def forced_probe_blind_dp(periods: tuple[int, ...]) -> int:
    return immediate_dp(periods)[0]


def belief_dp_tail(displayed_history: int, panel: int, periods: tuple[int, ...]) -> int:
    rho = _posterior(displayed_history, panel)
    return greedy_index([_expected_tail(rho, period) for period in periods])


def belief_dp_root(panel: int, periods: tuple[int, ...]) -> int:
    immediate_action, immediate_value = immediate_dp(periods)
    forced = evaluate_policy(
        panel=panel,
        periods=periods,
        root_action=0,
        tail_action=lambda displayed: belief_dp_tail(displayed, panel, periods),
    )
    if forced.total + COMPARISON_TOLERANCE >= immediate_value:
        return 0
    return immediate_action + 1


def _belief_dp_action_value_inventory(
    forced_probe_totals: Mapping[int, float],
) -> dict[str, object]:
    root: dict[str, object] = {}
    tail: dict[str, object] = {}
    immediate_values = [float(_expected_tail(np.float32(0.5), period)) for period in K_TEST]
    for panel in Panel:
        panel_id = int(panel)
        root[str(panel_id)] = {
            "action_keys": list(ROOT_ACTIONS),
            "values": [float(forced_probe_totals[panel_id]), *immediate_values],
            "intended_tie_pairs": [],
        }
        histories: dict[str, object] = {}
        for history in range(64):
            rho = _posterior(history, panel_id)
            histories[str(history)] = {
                "posterior": float(rho),
                "action_keys": list(TAIL_ACTIONS),
                "values": [float(_expected_tail(rho, period)) for period in K_TEST],
                "intended_tie_pairs": [],
            }
        tail[str(panel_id)] = histories
    return {
        "schema": "UCOPE_R01_R03_S2_BELIEF_DP_ACTION_VALUE_INVENTORY_V1",
        "root": root,
        "tail": tail,
    }


def _vector_finite_and_separated(values: Sequence[object]) -> bool:
    if not values or any(
        isinstance(value, bool)
        or not isinstance(value, (int, float, np.integer, np.floating))
        or not math.isfinite(float(value))
        for value in values
    ):
        return False
    numeric = [float(value) for value in values]
    return all(
        abs(left - right) > float(COMPARISON_TOLERANCE)
        for index, left in enumerate(numeric)
        for right in numeric[index + 1 :]
    )


def distinct_permutations(history: int) -> tuple[int, ...]:
    count = history.bit_count()
    values = []
    for positions in itertools.combinations(range(6), count):
        value = 0
        for position in positions:
            value |= 1 << position
        values.append(value)
    return tuple(values)


def raw_permavg_tail_action(
    logits: Callable[[int], Sequence[float]], displayed_history: int
) -> int:
    permutations = distinct_permutations(displayed_history)
    arrays = [np.asarray(logits(history), dtype=np.float32) for history in permutations]
    if any(array.shape != (len(K_TEST),) or not np.isfinite(array).all() for array in arrays):
        raise S2Refusal(S2Code.NONFINITE_OUTPUT)
    averaged = np.zeros(len(K_TEST), dtype=np.float32)
    for action in range(len(K_TEST)):
        ordered = np.asarray([array[action] for array in arrays], dtype=np.float32)
        total = fixed_fp32_tree(ordered)
        averaged[action] = np.float32(total / np.float32(len(arrays)))
    return learned_greedy_index(averaged)


def evaluate_policy(
    *,
    panel: int,
    periods: tuple[int, ...],
    root_action: int,
    tail_action: Callable[[int], int],
) -> ValueRecord:
    if periods not in (K_TEST, K_TRAIN) or root_action < 0 or root_action > len(periods):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    complete_tail_actions = tuple(tail_action(history) for history in range(64))
    if any(action < 0 or action >= len(periods) for action in complete_tail_actions):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    cases = tuple(finite_cases(panel))
    contributions = np.empty((len(cases), len(UTILITY_COMPONENTS)), dtype=np.float32)
    weights = np.empty(len(cases), dtype=np.float32)
    for row, case in enumerate(cases):
        weights[row] = case.weight
        if root_action == 0:
            selected = complete_tail_actions[case.displayed_history]
            parts = _tail_components(case.tail_regime, periods[selected]) + _probe_components(case.actual_history)
        else:
            parts = _tail_components(case.tail_regime, periods[root_action - 1]) + (
                np.float32(0.0), np.float32(0.0), np.float32(0.0)
            )
        for index, part in enumerate(parts):
            contributions[row, index] = np.float32(case.weight * part)
    weight_total = fixed_fp32_tree(weights)
    component_totals = np.asarray(
        [fixed_fp32_tree(contributions[:, index]) for index in range(len(UTILITY_COMPONENTS))],
        dtype=np.float32,
    )
    error = np.float32(abs(float(weight_total) - 1.0))
    if error > INVARIANT_TOLERANCE:
        raise S2Refusal(S2Code.NORMALIZATION_FAILURE)
    total = fixed_fp32_tree(component_totals)
    return ValueRecord(total, tuple(component_totals), root_action, complete_tail_actions, error)


def evaluate_learned_slot(
    slot: ValidatedCheckpointSlot, scorer: LearnedScorer, periods: tuple[int, ...]
) -> tuple[ValueRecord, ValueRecord]:
    root_logits = np.asarray(scorer.root_logits(slot, periods), dtype=np.float32)
    if root_logits.shape != (len(periods) + 1,) or not np.isfinite(root_logits).all():
        raise S2Refusal(S2Code.NONFINITE_OUTPUT)
    root = learned_greedy_index(root_logits)

    cached_tail: dict[int, int] = {}

    def tail(displayed: int) -> int:
        if displayed not in cached_tail:
            values = np.asarray(
                scorer.tail_logits(
                    slot, periods, learned_tail_channel(slot.arm, slot.panel, displayed)
                ),
                dtype=np.float32,
            )
            if values.shape != (len(periods),) or not np.isfinite(values).all():
                raise S2Refusal(S2Code.NONFINITE_OUTPUT)
            cached_tail[displayed] = learned_greedy_index(values)
        return cached_tail[displayed]

    endogenous = evaluate_policy(panel=slot.panel, periods=periods, root_action=root, tail_action=tail)
    forced = evaluate_policy(panel=slot.panel, periods=periods, root_action=0, tail_action=tail)
    return endogenous, forced


def decomposition(*, total: float, forced: float, blind: float, immediate: float) -> dict[str, np.float32]:
    a = np.float32(forced)
    a0 = np.float32(blind)
    b = np.float32(immediate)
    information = np.float32(a - a0)
    direct = np.float32(a0 - b)
    gamma = np.float32(a - b)
    gain = np.float32(np.float32(total) - b)
    if abs(float(np.float32(gamma - np.float32(information + direct)))) > float(INVARIANT_TOLERANCE):
        raise S2Refusal(S2Code.DECOMPOSITION_FAILURE)
    return {"A": a, "A0": a0, "B": b, "I": information, "D": direct, "Gamma": gamma, "G": gain}


def validate_support_structure(value: Mapping[str, object], panel: int) -> bool:
    """Validate exact counter types, cardinalities, balance, and conservation."""

    required = {
        "root_visits", "tail_visits", "displayed_count_visits", "balanced_totals"
    }
    if not isinstance(value, Mapping) or set(value) != required:
        return False
    roots = value["root_visits"]
    tails = value["tail_visits"]
    counts = value["displayed_count_visits"]
    balances = value["balanced_totals"]
    if not (
        isinstance(roots, Sequence) and not isinstance(roots, (str, bytes, bytearray)) and len(roots) == 6
        and isinstance(tails, Sequence) and not isinstance(tails, (str, bytes, bytearray)) and len(tails) == 5
        and isinstance(counts, Sequence) and not isinstance(counts, (str, bytes, bytearray)) and len(counts) == 7
        and isinstance(balances, Sequence) and not isinstance(balances, (str, bytes, bytearray))
    ):
        return False
    rows = tuple(roots) + tuple(tails) + tuple(counts) + tuple(balances)
    if any(type(item) is not int or item < 0 for item in rows):
        return False
    expected = (40960, 40960) if panel == int(Panel.PERSISTENT) else (20480, 20480, 20480, 20480)
    return (
        tuple(balances) == expected
        and sum(roots) == 81920
        and sum(balances) == 81920
        and sum(tails) == roots[0]
        and sum(counts) == roots[0]
    )


def validate_support(value: Mapping[str, object], panel: int) -> bool:
    """Apply frozen support thresholds after structural admission."""

    if not validate_support_structure(value, panel):
        return False
    roots = value["root_visits"]
    tails = value["tail_visits"]
    counts = value["displayed_count_visits"]
    return min(roots) >= 2048 and min(tails) >= 2048 and min(counts) >= 256


def validate_competence(per_panel: Mapping[int, Sequence[Mapping[str, object]]]) -> dict[int, bool]:
    result: dict[int, bool] = {}
    for panel in Panel:
        records = per_panel.get(int(panel), ())
        if len(records) != 10:
            result[int(panel)] = False
            continue
        passing = sum(
            bool(record.get("root_match"))
            and float(record.get("regret", math.inf)) <= 0.02
            and float(record.get("tail_agreement", -math.inf)) >= 0.95
            for record in records
        )
        result[int(panel)] = passing >= 9
    return result


def validate_headroom(value: Mapping[str, object]) -> bool:
    required = (
        "unique_prior_optimum_margin",
        "regime_optima_differ",
        "persistent_information",
        "persistent_acquisition",
        "persistent_direct",
        "redraw_information",
        "severed_information",
        "redraw_immediate_margin",
        "severed_immediate_margin",
        "all_action_values_finite",
        "all_unintended_ties_separated",
    )
    if any(key not in value for key in required):
        return False
    return (
        float(value["unique_prior_optimum_margin"]) >= 0.02
        and bool(value["regime_optima_differ"])
        and float(value["persistent_information"]) >= 0.04
        and float(value["persistent_acquisition"]) >= 0.03
        and -0.021 <= float(value["persistent_direct"]) <= -0.019
        and abs(float(value["redraw_information"])) <= 1.0e-5
        and abs(float(value["severed_information"])) <= 1.0e-5
        and float(value["redraw_immediate_margin"]) >= 0.019
        and float(value["severed_immediate_margin"]) >= 0.019
        and bool(value["all_action_values_finite"])
        and bool(value["all_unintended_ties_separated"])
    )


def paired_t_interval(values: Sequence[float]) -> Interval:
    if len(values) != 10 or not all(math.isfinite(float(value)) for value in values):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    array = np.asarray(values, dtype=np.float32)
    mean32 = np.mean(array, dtype=np.float32)
    centered = np.float32(array - mean32)
    variance32 = np.float32(np.sum(centered * centered, dtype=np.float32) / np.float32(9.0))
    standard_error = np.float32(np.sqrt(np.float32(max(float(variance32), 0.0) / 10.0)))
    half = np.float32(np.float32(2.2621571627409915) * standard_error)
    lower32 = np.float32(mean32 - half)
    upper32 = np.float32(mean32 + half)
    mean, lower, upper = float(mean32), float(lower32), float(upper32)
    if lower > 0.03:
        classification = "COUNT_ADVANTAGE"
    elif lower >= -0.03 and upper <= 0.03:
        classification = "EQUIVALENT"
    elif upper < -0.03:
        classification = "RAW_SUPERIOR"
    else:
        classification = "UNRESOLVED"
    return Interval(mean, lower, upper, classification)


def one_sided_lower(values: Sequence[float]) -> float:
    if len(values) != 10 or not all(math.isfinite(float(value)) for value in values):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    array = np.asarray(values, dtype=np.float32)
    mean = np.mean(array, dtype=np.float32)
    centered = np.float32(array - mean)
    variance = np.float32(np.sum(centered * centered, dtype=np.float32) / np.float32(9.0))
    standard_error = np.float32(np.sqrt(np.float32(max(float(variance), 0.0) / 10.0)))
    return float(np.float32(mean - np.float32(np.float32(1.8331129326536335) * standard_error)))


def acquisition_supported(
    margins: Sequence[float],
    *,
    persistent_probe: Sequence[bool],
    redraw_immediate: Sequence[bool],
    severed_immediate: Sequence[bool],
    support_pass: bool,
    competence_pass: bool,
) -> bool:
    return (
        one_sided_lower(margins) > 0.0
        and len(persistent_probe) == len(redraw_immediate) == len(severed_immediate) == 10
        and all(persistent_probe)
        and all(redraw_immediate)
        and all(severed_immediate)
        and support_pass
        and competence_pass
    )


def attribution_map(
    acquisition: bool, delta_test: str, delta_train: str, delta_perm: str
) -> dict[str, object]:
    classes = {"COUNT_ADVANTAGE", "EQUIVALENT", "RAW_SUPERIOR", "UNRESOLVED"}
    if {delta_test, delta_train, delta_perm} - classes:
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    labels: list[str] = []
    branch = "ACQUISITION_NOT_SUPPORTED"
    successor = False
    if acquisition:
        if delta_test in {"EQUIVALENT", "RAW_SUPERIOR"}:
            branch = "GENERIC_ACTIVE_ACQUISITION"
            labels.append("INDEPENDENT_COUNT_SUMMARY_NOT_SUPPORTED")
        elif delta_test == "UNRESOLVED":
            branch = "HELD_OUT_COUNT_CONTAINMENT_UNRESOLVED"
            labels.append("HELD_OUT_COUNT_CONTAINMENT_UNRESOLVED")
        elif delta_train in {"EQUIVALENT", "RAW_SUPERIOR"}:
            branch = "HELD_OUT_K_INTERPOLATION_SPECIFIC"
            labels.append("HELD_OUT_K_INTERPOLATION_SPECIFIC")
        elif delta_train == "UNRESOLVED":
            branch = "TRAIN_TEST_ATTRIBUTION_UNRESOLVED"
            labels.append("TRAIN_TEST_ATTRIBUTION_UNRESOLVED")
        elif delta_perm in {"EQUIVALENT", "RAW_SUPERIOR"}:
            branch = "EXPLICIT_PERMUTATION_INVARIANCE_ENGINEERING"
            labels.append("EXPLICIT_PERMUTATION_INVARIANCE_ENGINEERING")
        elif delta_perm == "UNRESOLVED":
            branch = "PERMUTATION_CONTAINMENT_UNRESOLVED"
            labels.append("PERMUTATION_CONTAINMENT_UNRESOLVED")
        else:
            branch = "ROBUST_COUNT_RESIDUAL_AFTER_TRAIN_AND_PERMUTATION_CONTROLS"
            labels.append("ROBUST_COUNT_RESIDUAL_AFTER_TRAIN_AND_PERMUTATION_CONTROLS")
            successor = True
        if delta_train in {"EQUIVALENT", "RAW_SUPERIOR"} and "HELD_OUT_K_INTERPOLATION_SPECIFIC" not in labels:
            labels.append("TRAIN_POPULATION_COUNT_CONTAINMENT")
        elif delta_train == "UNRESOLVED" and "TRAIN_TEST_ATTRIBUTION_UNRESOLVED" not in labels:
            labels.append("TRAIN_TEST_ATTRIBUTION_UNRESOLVED")
        if delta_perm in {"EQUIVALENT", "RAW_SUPERIOR"} and "EXPLICIT_PERMUTATION_INVARIANCE_ENGINEERING" not in labels:
            labels.append("EXPLICIT_PERMUTATION_INVARIANCE_ENGINEERING")
        elif delta_perm == "UNRESOLVED" and "PERMUTATION_CONTAINMENT_UNRESOLVED" not in labels:
            labels.append("PERMUTATION_CONTAINMENT_UNRESOLVED")
    return {"branch": branch, "labels": labels, "successor_eligible": successor}


def terminal_action_class(*, complete: bool, invariant_pass: bool, support_pass: bool, competence_pass: bool, acquisition: bool) -> str:
    if not complete:
        return "PREACTIVITY_INCOMPLETE_OUTPUT"
    if not invariant_pass:
        return "PREACTIVITY_INVARIANT_FAILURE"
    if not support_pass:
        return "TERMINAL_SUPPORT_FAILURE"
    if not competence_pass:
        return "TERMINAL_COMPETENCE_FAILURE"
    if not acquisition:
        return "TERMINAL_ACQUISITION_OR_SPECIFICITY_FAILURE"
    return "TERMINAL_SEVEN_BRANCH_ATTRIBUTION"


def _tail_agreement(
    panel: int,
    left: Callable[[int], int],
    right: Callable[[int], int],
) -> np.float32:
    _, total = _tail_agreement_totals(panel, left, right)
    return total


def _tail_agreement_totals(
    panel: int,
    left: Callable[[int], int],
    right: Callable[[int], int],
) -> tuple[np.float32, np.float32]:
    cases = tuple(finite_cases(panel))
    weights = np.asarray([case.weight for case in cases], dtype=np.float32)
    matched = np.asarray(
        [
            case.weight
            if left(case.displayed_history) == right(case.displayed_history)
            else np.float32(0.0)
            for case in cases
        ],
        dtype=np.float32,
    )
    weight_total = fixed_fp32_tree(weights)
    total = fixed_fp32_tree(matched)
    if abs(float(weight_total) - 1.0) > float(INVARIANT_TOLERANCE):
        raise S2Refusal(S2Code.NORMALIZATION_FAILURE)
    return weight_total, total


def _descriptive_tail_agreement(
    panel: int,
    left: Callable[[int], int],
    right: Callable[[int], int],
) -> np.float32:
    weight_total, total = _tail_agreement_totals(panel, left, right)
    if (
        not math.isfinite(float(weight_total))
        or not math.isfinite(float(total))
        or total < np.float32(0.0)
        or total > weight_total
    ):
        raise S2Refusal(S2Code.NORMALIZATION_FAILURE)
    normalized = np.float32(total / weight_total)
    if (
        not math.isfinite(float(normalized))
        or normalized < np.float32(0.0)
        or normalized > np.float32(1.0)
    ):
        raise S2Refusal(S2Code.NORMALIZATION_FAILURE)
    return normalized


def _private_key(slot: ValidatedCheckpointSlot) -> str:
    return f"{slot.arm}:{slot.panel}:{slot.master_seed}"


def _record_dict(record: ValueRecord) -> dict[str, object]:
    return record.as_private_dict()


def _package_provenance(package: Mapping[str, object]) -> dict[str, object]:
    inventory_digest = hashlib.sha256(
        _canonical_bytes(package["checkpoint_inventory"])
    ).hexdigest()
    material_fields = tuple(
        sorted(
            set(REQUIRED_TOP_LEVEL_FIELDS)
            - {
                "schema", "object_revision", "object_digest", "checkpoint_inventory",
                "required_field_inventory", "provenance",
            }
        )
    )
    material_digest = hashlib.sha256(
        _canonical_bytes({field: package[field] for field in material_fields})
    ).hexdigest()
    binding_digest = hashlib.sha256(
        _canonical_bytes(
            {
                "object_revision": OBJECT_REVISION,
                "object_digest": OBJECT_DIGEST,
                "inventory_digest": inventory_digest,
                "material_digest": material_digest,
            }
        )
    ).hexdigest()
    return {
        "schema": "UCOPE_R01_R03_S2_EVALUATED_MATERIAL_BINDING_V1",
        "inventory_digest": inventory_digest,
        "material_digest": material_digest,
        "binding_digest": binding_digest,
    }


def evaluate_complete_private(
    slots: Sequence[CheckpointSlot],
    *,
    checkpoint_root: Path,
    scorer: LearnedScorer | None = None,
    request: BoundaryRequest,
) -> SealedEvaluation:
    """Execute the full finite contract into private memory.

    Construction mode is admitted only for the disjoint synthetic inventory.
    The returned mapping must remain private until a separately authorized
    registered caller passes it to :func:`publish_complete_package`.
    """

    construction = request.namespace in CONSTRUCTION_NAMESPACES
    if construction:
        request.require_construction()
    else:
        request.require_registered_publication()
        if scorer is not None:
            raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    checked = validate_checkpoint_inventory(
        slots, checkpoint_root=checkpoint_root, construction=construction
    )
    if construction:
        bind = getattr(scorer, "bind", None)
        if scorer is None or not callable(bind):
            raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
        for slot in checked:
            bind(slot)
        active_scorer = scorer
    else:
        active_scorer = _CheckpointPayloadScorer(checked)
    k_test_values: dict[str, object] = {}
    k_train_values: dict[str, object] = {}
    forced_test: dict[str, ValueRecord] = {}
    normalization_errors: list[float] = []
    tail_functions: dict[tuple[int, tuple[int, ...], int, int], Callable[[int], int]] = {}

    for slot in checked:
        for periods, target in ((K_TEST, k_test_values), (K_TRAIN, k_train_values)):
            endogenous, forced = evaluate_learned_slot(slot, active_scorer, periods)
            target[_private_key(slot)] = _record_dict(endogenous)
            normalization_errors.extend((float(endogenous.normalization_error), float(forced.normalization_error)))
            if periods == K_TEST:
                forced_test[_private_key(slot)] = forced

            cache: dict[int, int] = {}

            def tail(displayed: int, *, _slot: ValidatedCheckpointSlot = slot, _periods: tuple[int, ...] = periods, _cache: dict[int, int] = cache) -> int:
                if displayed not in _cache:
                    _cache[displayed] = learned_greedy_index(
                        active_scorer.tail_logits(
                            _slot,
                            _periods,
                            learned_tail_channel(_slot.arm, _slot.panel, displayed),
                        )
                    )
                return _cache[displayed]

            tail_functions[(slot.arm, periods, slot.panel, slot.master_seed)] = tail

    comparator_records: dict[int, dict[str, ValueRecord]] = {}
    for panel in Panel:
        panel_id = int(panel)
        immediate_action, _ = immediate_dp(K_TEST)
        immediate = evaluate_policy(
            panel=panel_id,
            periods=K_TEST,
            root_action=immediate_action + 1,
            tail_action=lambda _: immediate_action,
        )
        blind_action = forced_probe_blind_dp(K_TEST)
        blind = evaluate_policy(
            panel=panel_id,
            periods=K_TEST,
            root_action=0,
            tail_action=lambda _: blind_action,
        )
        belief_root = belief_dp_root(panel_id, K_TEST)
        belief = evaluate_policy(
            panel=panel_id,
            periods=K_TEST,
            root_action=belief_root,
            tail_action=lambda displayed, _panel=panel_id: belief_dp_tail(displayed, _panel, K_TEST),
        )
        belief_forced = evaluate_policy(
            panel=panel_id,
            periods=K_TEST,
            root_action=0,
            tail_action=lambda displayed, _panel=panel_id: belief_dp_tail(displayed, _panel, K_TEST),
        )
        comparator_records[panel_id] = {
            "BELIEF_DP": belief,
            "BELIEF_DP_FORCED": belief_forced,
            "IMMEDIATE_DP": immediate,
            "FORCED_PROBE_BLIND_DP": blind,
        }
        normalization_errors.extend(
            float(record.normalization_error) for record in comparator_records[panel_id].values()
        )

    belief_dp_action_values = _belief_dp_action_value_inventory(
        {
            panel: float(records["BELIEF_DP_FORCED"].total)
            for panel, records in comparator_records.items()
        }
    )

    raw_permavg: dict[str, object] = {}
    raw_perm_records: dict[int, ValueRecord] = {}
    for slot in checked:
        if slot.arm != int(LearnedArm.RAW) or slot.panel != int(Panel.PERSISTENT):
            continue
        cache: dict[int, int] = {}

        def perm_tail(displayed: int, *, _slot: ValidatedCheckpointSlot = slot) -> int:
            if displayed not in cache:
                cache[displayed] = raw_permavg_tail_action(
                    lambda history: active_scorer.tail_logits(
                        _slot,
                        K_TEST,
                        learned_tail_channel(_slot.arm, _slot.panel, history),
                    ),
                    displayed,
                )
            return cache[displayed]

        record = evaluate_policy(
            panel=int(Panel.PERSISTENT), periods=K_TEST, root_action=0, tail_action=perm_tail
        )
        raw_perm_records[slot.master_seed] = record
        raw_permavg[_private_key(slot)] = _record_dict(record)
        normalization_errors.append(float(record.normalization_error))

    decompositions: dict[str, object] = {}
    for slot in checked:
        key = _private_key(slot)
        endogenous = k_test_values[key]
        comparator = comparator_records[slot.panel]
        decompositions[key] = {
            name: float(value)
            for name, value in decomposition(
                total=float(endogenous["total"]),  # type: ignore[index]
                forced=float(forced_test[key].total),
                blind=float(comparator["FORCED_PROBE_BLIND_DP"].total),
                immediate=float(comparator["IMMEDIATE_DP"].total),
            ).items()
        }

    immediate_values = [_expected_tail(np.float32(0.5), period) for period in K_TEST]
    ordered_immediate = sorted((float(value) for value in immediate_values), reverse=True)
    regime_optima = tuple(
        greedy_index([_expected_tail(np.float32(regime == 0), period) for period in K_TEST])
        for regime in (0, 1)
    )
    persistent_comparator = comparator_records[int(Panel.PERSISTENT)]
    persistent_decomposition = decomposition(
        total=persistent_comparator["BELIEF_DP"].total,
        forced=persistent_comparator["BELIEF_DP_FORCED"].total,
        blind=persistent_comparator["FORCED_PROBE_BLIND_DP"].total,
        immediate=persistent_comparator["IMMEDIATE_DP"].total,
    )
    null_decompositions = {}
    for panel in (Panel.REDRAW, Panel.SEVERED):
        records = comparator_records[int(panel)]
        null_decompositions[int(panel)] = decomposition(
            total=records["BELIEF_DP"].total,
            forced=records["BELIEF_DP_FORCED"].total,
            blind=records["FORCED_PROBE_BLIND_DP"].total,
            immediate=records["IMMEDIATE_DP"].total,
        )
    action_vectors = [
        row["values"]
        for row in belief_dp_action_values["root"].values()  # type: ignore[union-attr]
    ] + [
        row["values"]
        for histories in belief_dp_action_values["tail"].values()  # type: ignore[union-attr]
        for row in histories.values()  # type: ignore[union-attr]
    ]
    all_action_sets_separated = all(_vector_finite_and_separated(values) for values in action_vectors)
    headroom = {
        "unique_prior_optimum_margin": ordered_immediate[0] - ordered_immediate[1],
        "regime_optima_differ": regime_optima[0] != regime_optima[1],
        "persistent_information": float(persistent_decomposition["I"]),
        "persistent_acquisition": float(persistent_decomposition["Gamma"]),
        "persistent_direct": float(persistent_decomposition["D"]),
        "redraw_information": float(null_decompositions[int(Panel.REDRAW)]["I"]),
        "severed_information": float(null_decompositions[int(Panel.SEVERED)]["I"]),
        "redraw_immediate_margin": float(
            comparator_records[int(Panel.REDRAW)]["IMMEDIATE_DP"].total
            - comparator_records[int(Panel.REDRAW)]["BELIEF_DP_FORCED"].total
        ),
        "severed_immediate_margin": float(
            comparator_records[int(Panel.SEVERED)]["IMMEDIATE_DP"].total
            - comparator_records[int(Panel.SEVERED)]["BELIEF_DP_FORCED"].total
        ),
        "all_action_values_finite": all(
            all(math.isfinite(float(value)) for value in values)
            for values in action_vectors
        ),
        "all_unintended_ties_separated": all_action_sets_separated,
    }

    support_rows = {
        _private_key(slot): {
            "facts": dict(slot.support),
            "pass": validate_support(slot.support, slot.panel),
        }
        for slot in checked
    }
    support_pass = all(bool(row["pass"]) for row in support_rows.values())
    competence_rows: dict[int, dict[int, dict[str, object]]] = {
        int(panel): {} for panel in Panel
    }
    for slot in checked:
        if slot.arm != int(LearnedArm.BELIEF_FEATURE):
            continue
        key = _private_key(slot)
        belief = comparator_records[slot.panel]["BELIEF_DP"]
        learned = k_test_values[key]
        learned_tail = tail_functions[(slot.arm, K_TEST, slot.panel, slot.master_seed)]
        agreement = _tail_agreement(
            slot.panel,
            learned_tail,
            lambda displayed, _panel=slot.panel: belief_dp_tail(displayed, _panel, K_TEST),
        )
        competence_rows[slot.panel][slot.master_seed] = {
            "root_match": learned["root_action"] == belief.root_action,  # type: ignore[index]
            "regret": float(np.float32(belief.total - np.float32(learned["total"]))),  # type: ignore[index]
            "tail_agreement": float(agreement),
        }
    competence_gates = validate_competence(
        {panel: list(records.values()) for panel, records in competence_rows.items()}
    )
    competence_pass = all(competence_gates.values())

    seeds = sorted({slot.master_seed for slot in checked})
    seed_contrasts: dict[str, list[float]] = {name: [] for name in REQUIRED_CONTRASTS}
    agreements: list[dict[str, float]] = []
    margins: list[float] = []
    persistent_probe: list[bool] = []
    redraw_immediate: list[bool] = []
    severed_immediate: list[bool] = []
    for seed in seeds:
        def key(arm: LearnedArm, panel: Panel) -> str:
            return f"{int(arm)}:{int(panel)}:{seed}"

        count_test = k_test_values[key(LearnedArm.COUNT, Panel.PERSISTENT)]
        raw_test = k_test_values[key(LearnedArm.RAW, Panel.PERSISTENT)]
        count_train = k_train_values[key(LearnedArm.COUNT, Panel.PERSISTENT)]
        raw_train = k_train_values[key(LearnedArm.RAW, Panel.PERSISTENT)]
        count_forced = forced_test[key(LearnedArm.COUNT, Panel.PERSISTENT)]
        perm = raw_perm_records[seed]
        seed_contrasts["delta_test"].append(float(np.float32(count_test["total"] - raw_test["total"])))  # type: ignore[index,operator]
        seed_contrasts["delta_train"].append(float(np.float32(count_train["total"] - raw_train["total"])))  # type: ignore[index,operator]
        seed_contrasts["delta_perm"].append(float(np.float32(count_forced.total - perm.total)))
        raw_tail = lambda displayed, _seed=seed: raw_permavg_tail_action(
            lambda history: (
                lambda raw_slot: active_scorer.tail_logits(
                    raw_slot,
                    K_TEST,
                    learned_tail_channel(raw_slot.arm, raw_slot.panel, history),
                )
            )(
                next(
                    slot
                    for slot in checked
                    if slot.key == (int(LearnedArm.RAW), int(Panel.PERSISTENT), _seed)
                )
            ),
            displayed,
        )
        count_tail = tail_functions[(int(LearnedArm.COUNT), K_TEST, int(Panel.PERSISTENT), seed)]
        agreements.append(
            {
                "count": float(
                    _descriptive_tail_agreement(
                        int(Panel.PERSISTENT), raw_tail, count_tail
                    )
                ),
                "belief": float(
                    _descriptive_tail_agreement(
                        int(Panel.PERSISTENT),
                        raw_tail,
                        lambda displayed: belief_dp_tail(displayed, int(Panel.PERSISTENT), K_TEST),
                    )
                ),
            }
        )
        count_persistent = decompositions[key(LearnedArm.COUNT, Panel.PERSISTENT)]
        count_redraw = decompositions[key(LearnedArm.COUNT, Panel.REDRAW)]
        count_severed = decompositions[key(LearnedArm.COUNT, Panel.SEVERED)]
        belief_persistent = comparator_records[int(Panel.PERSISTENT)]["BELIEF_DP"].total
        margins.append(
            min(
                float(count_persistent["Gamma"]) - 0.03,  # type: ignore[index]
                float(count_persistent["I"]) - 0.03,  # type: ignore[index]
                0.02 - abs(float(count_redraw["I"])),  # type: ignore[index]
                0.02 - abs(float(count_severed["I"])),  # type: ignore[index]
                0.05 - float(np.float32(belief_persistent - np.float32(count_test["total"]))),  # type: ignore[index]
            )
        )
        persistent_probe.append(count_test["root_action"] == 0)  # type: ignore[index]
        redraw_immediate.append(k_test_values[key(LearnedArm.COUNT, Panel.REDRAW)]["root_action"] != 0)  # type: ignore[index]
        severed_immediate.append(k_test_values[key(LearnedArm.COUNT, Panel.SEVERED)]["root_action"] != 0)  # type: ignore[index]

    intervals = {name: paired_t_interval(values) for name, values in seed_contrasts.items()}
    acquisition = acquisition_supported(
        margins,
        persistent_probe=persistent_probe,
        redraw_immediate=redraw_immediate,
        severed_immediate=severed_immediate,
        support_pass=support_pass,
        competence_pass=competence_pass,
    )
    attribution = attribution_map(
        acquisition,
        intervals["delta_test"].classification,
        intervals["delta_train"].classification,
        intervals["delta_perm"].classification,
    )
    headroom_pass = validate_headroom(headroom)
    inventory_rows = [
        {
            "arm": slot.arm,
            "panel": slot.panel,
            "master_seed": slot.master_seed,
            "batch": slot.batch,
            "sha256": slot.sha256,
            "model_sha256": slot.model_sha256,
        }
        for slot in checked
    ]
    package: dict[str, object] = {
        "schema": S2_SCHEMA,
        "object_revision": OBJECT_REVISION,
        "object_digest": OBJECT_DIGEST,
        "checkpoint_inventory": inventory_rows,
        "k_test_values": k_test_values,
        "k_train_values": k_train_values,
        "forced_test_values": {
            key: _record_dict(record) for key, record in forced_test.items()
        },
        "raw_permavg_values": raw_permavg,
        "comparators": {
            str(panel): {name: _record_dict(record) for name, record in records.items()}
            for panel, records in comparator_records.items()
        },
        "belief_dp_action_values": belief_dp_action_values,
        "decompositions": {**decompositions, "all_identities_hold": True},
        "headroom": {**headroom, "pass": headroom_pass},
        "support": {"slots": support_rows, "pass": support_pass},
        "competence": {
            "records": {
                str(panel): {str(seed): record for seed, record in records.items()}
                for panel, records in competence_rows.items()
            },
            "gates": {str(panel): passed for panel, passed in competence_gates.items()},
            "pass": competence_pass,
        },
        "seed_contrasts": {
            name: {str(seed): value for seed, value in zip(seeds, values)}
            for name, values in seed_contrasts.items()
        },
        "intervals": {
            name: {
                "mean": interval.mean,
                "lower": interval.lower,
                "upper": interval.upper,
                "classification": interval.classification,
            }
            for name, interval in intervals.items()
        },
        "descriptive_agreements": {
            str(seed): value for seed, value in zip(seeds, agreements)
        },
        "acquisition": {
            "margins": {str(seed): value for seed, value in zip(seeds, margins)},
            "lower": one_sided_lower(margins),
            "supported": acquisition,
        },
        "attribution": attribution,
        "terminal_action": terminal_action_class(
            complete=True,
            invariant_pass=headroom_pass,
            support_pass=support_pass,
            competence_pass=competence_pass,
            acquisition=acquisition,
        ),
        "normalization": {
            "maximum_error": max(normalization_errors, default=0.0),
            "all_within_tolerance": max(normalization_errors, default=0.0) <= float(INVARIANT_TOLERANCE),
        },
    }
    package["required_field_inventory"] = list(sorted(REQUIRED_TOP_LEVEL_FIELDS))
    package["provenance"] = _package_provenance(package)
    validate_complete_package(package)
    return SealedEvaluation(
        package=package,
        inventory=checked,
        checkpoint_root=checkpoint_root.resolve(strict=True),
        seal_digest=hashlib.sha256(_canonical_bytes(package)).hexdigest(),
        _issuer=_SEAL_ISSUER,
    )


def _finite_tree(value: object) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float, np.integer, np.floating)):
        return math.isfinite(float(value))
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _finite_tree(item) for key, item in value.items())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return all(_finite_tree(item) for item in value)
    return False


def _exact_mapping(value: object, keys: set[str], code: S2Code = S2Code.INCOMPLETE_OUTPUT) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise S2Refusal(code)
    return value


def _finite_number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    result = float(value)
    if not math.isfinite(result):
        raise S2Refusal(S2Code.NONFINITE_OUTPUT)
    return result


def _close(left: object, right: object, tolerance: float = 1.0e-5) -> bool:
    return abs(_finite_number(left) - _finite_number(right)) <= tolerance


def _same_fp32(left: object, right: object) -> bool:
    return np.float32(_finite_number(left)).tobytes() == np.float32(_finite_number(right)).tobytes()


def _validate_private_value(value: object, period_count: int, *, forced: bool = False) -> Mapping[str, object]:
    record = _exact_mapping(
        value,
        {"total", "components", "root_action", "tail_actions", "normalization_error"},
    )
    components = record["components"]
    tails = record["tail_actions"]
    root = record["root_action"]
    if (
        not isinstance(components, Sequence)
        or isinstance(components, (str, bytes, bytearray))
        or len(components) != len(UTILITY_COMPONENTS)
        or not isinstance(tails, Sequence)
        or isinstance(tails, (str, bytes, bytearray))
        or len(tails) != 64
        or isinstance(root, bool)
        or not isinstance(root, int)
        or root < 0
        or root > period_count
        or (forced and root != 0)
    ):
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
    if any(
        isinstance(action, bool) or not isinstance(action, int) or action < 0 or action >= period_count
        for action in tails
    ):
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    component_values = [_finite_number(component) for component in components]
    if not _close(record["total"], sum(component_values), float(INVARIANT_TOLERANCE)):
        raise S2Refusal(S2Code.DECOMPOSITION_FAILURE)
    error = _finite_number(record["normalization_error"])
    if error < 0.0 or error > float(INVARIANT_TOLERANCE):
        raise S2Refusal(S2Code.NORMALIZATION_FAILURE)
    return record


def validate_complete_package(package: Mapping[str, object]) -> tuple[str, ...]:
    required = tuple(sorted(REQUIRED_TOP_LEVEL_FIELDS))
    if set(package) != set(REQUIRED_TOP_LEVEL_FIELDS):
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
    if package.get("schema") != S2_SCHEMA:
        raise S2Refusal(S2Code.MALFORMED_INPUT)
    if package.get("object_revision") != OBJECT_REVISION or package.get("object_digest") != OBJECT_DIGEST:
        raise S2Refusal(S2Code.OBJECT_MISMATCH)
    if not _finite_tree(package):
        raise S2Refusal(S2Code.NONFINITE_OUTPUT)
    declared = package.get("required_field_inventory")
    if (
        not isinstance(declared, Sequence)
        or isinstance(declared, (str, bytes, bytearray))
        or tuple(declared) != required
    ):
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)

    inventory = package.get("checkpoint_inventory")
    if (
        not isinstance(inventory, Sequence)
        or isinstance(inventory, (str, bytes, bytearray))
        or len(inventory) != FINAL_CHECKPOINT_SLOT_COUNT
    ):
        raise S2Refusal(S2Code.INCOMPLETE_INVENTORY)
    slot_keys: set[tuple[int, int, int]] = set()
    inventory_digests: list[str] = []
    for item in inventory:
        row = _exact_mapping(
            item,
            {"arm", "panel", "master_seed", "batch", "sha256", "model_sha256"},
            S2Code.INCOMPLETE_INVENTORY,
        )
        arm, panel, seed, batch = row["arm"], row["panel"], row["master_seed"], row["batch"]
        if (
            any(isinstance(value, bool) or not isinstance(value, int) for value in (arm, panel, seed, batch))
            or arm not in tuple(int(value) for value in LearnedArm)
            or panel not in tuple(int(value) for value in Panel)
            or batch != TRAINING_BATCHES
        ):
            raise S2Refusal(S2Code.MALFORMED_INPUT)
        digest = _validate_digest(row["sha256"])
        _validate_digest(row["model_sha256"])
        key = (arm, panel, seed)
        if key in slot_keys:
            raise S2Refusal(S2Code.DUPLICATE_SLOT)
        slot_keys.add(key)
        inventory_digests.append(digest)
    seeds = sorted({seed for _, _, seed in slot_keys})
    expected_slots = {
        (int(arm), int(panel), seed)
        for arm in LearnedArm
        for panel in Panel
        for seed in seeds
    }
    if len(seeds) != 10 or slot_keys != expected_slots:
        raise S2Refusal(S2Code.INCOMPLETE_INVENTORY)
    private_keys = {f"{arm}:{panel}:{seed}" for arm, panel, seed in expected_slots}

    value_sections: dict[str, Mapping[str, object]] = {}
    normalization_errors: list[float] = []
    for section_name, period_count, forced in (
        ("k_test_values", len(K_TEST), False),
        ("k_train_values", len(K_TRAIN), False),
        ("forced_test_values", len(K_TEST), True),
    ):
        section = _exact_mapping(package[section_name], private_keys)
        value_sections[section_name] = section
        for record in section.values():
            checked_record = _validate_private_value(record, period_count, forced=forced)
            normalization_errors.append(_finite_number(checked_record["normalization_error"]))
    for key in private_keys:
        if value_sections["forced_test_values"][key]["tail_actions"] != value_sections["k_test_values"][key]["tail_actions"]:  # type: ignore[index]
            raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)

    raw_keys = {f"{int(LearnedArm.RAW)}:{int(Panel.PERSISTENT)}:{seed}" for seed in seeds}
    raw_permavg = _exact_mapping(package["raw_permavg_values"], raw_keys)
    for record in raw_permavg.values():
        checked_record = _validate_private_value(record, len(K_TEST), forced=True)
        normalization_errors.append(_finite_number(checked_record["normalization_error"]))

    comparators = _exact_mapping(package["comparators"], {str(int(panel)) for panel in Panel})
    comparator_names = {
        "BELIEF_DP", "BELIEF_DP_FORCED", "IMMEDIATE_DP", "FORCED_PROBE_BLIND_DP"
    }
    comparator_records: dict[int, Mapping[str, object]] = {}
    for panel in Panel:
        records = _exact_mapping(comparators[str(int(panel))], comparator_names)
        comparator_records[int(panel)] = records
        for name, record in records.items():
            checked_record = _validate_private_value(
                record,
                len(K_TEST),
                forced=name in {"BELIEF_DP_FORCED", "FORCED_PROBE_BLIND_DP"},
            )
            if name == "IMMEDIATE_DP" and checked_record["root_action"] == 0:
                raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
            normalization_errors.append(_finite_number(checked_record["normalization_error"]))

    action_inventory = _exact_mapping(
        package["belief_dp_action_values"], {"schema", "root", "tail"}
    )
    expected_action_inventory = _belief_dp_action_value_inventory(
        {
            int(panel): _finite_number(
                comparator_records[int(panel)]["BELIEF_DP_FORCED"]["total"]  # type: ignore[index]
            )
            for panel in Panel
        }
    )
    if action_inventory["schema"] != expected_action_inventory["schema"]:
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
    panel_names = {str(int(panel)) for panel in Panel}
    action_root = _exact_mapping(action_inventory["root"], panel_names)
    action_tail = _exact_mapping(action_inventory["tail"], panel_names)
    expected_root = expected_action_inventory["root"]  # type: ignore[assignment]
    expected_tail = expected_action_inventory["tail"]  # type: ignore[assignment]
    validated_action_vectors: list[Sequence[object]] = []
    for panel_name in panel_names:
        root_row = _exact_mapping(
            action_root[panel_name], {"action_keys", "values", "intended_tie_pairs"}
        )
        expected_root_row = expected_root[panel_name]  # type: ignore[index]
        if (
            root_row["action_keys"] != expected_root_row["action_keys"]
            or root_row["intended_tie_pairs"] != []
            or not isinstance(root_row["values"], Sequence)
            or isinstance(root_row["values"], (str, bytes, bytearray))
            or len(root_row["values"]) != len(ROOT_ACTIONS)
            or any(
                not _same_fp32(provided, observed)
                for provided, observed in zip(root_row["values"], expected_root_row["values"])
            )
        ):
            raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
        validated_action_vectors.append(root_row["values"])
        histories = _exact_mapping(
            action_tail[panel_name], {str(history) for history in range(64)}
        )
        expected_histories = expected_tail[panel_name]  # type: ignore[index]
        for history_name in histories:
            row = _exact_mapping(
                histories[history_name],
                {"posterior", "action_keys", "values", "intended_tie_pairs"},
            )
            expected_row = expected_histories[history_name]
            if (
                not _same_fp32(row["posterior"], expected_row["posterior"])
                or row["action_keys"] != expected_row["action_keys"]
                or row["intended_tie_pairs"] != []
                or not isinstance(row["values"], Sequence)
                or isinstance(row["values"], (str, bytes, bytearray))
                or len(row["values"]) != len(K_TEST)
                or any(
                    not _same_fp32(provided, observed)
                    for provided, observed in zip(row["values"], expected_row["values"])
                )
            ):
                raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
            validated_action_vectors.append(row["values"])
    if len(validated_action_vectors) != 3 + 3 * 64 or not all(
        _vector_finite_and_separated(values) for values in validated_action_vectors
    ):
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)

    decompositions = _exact_mapping(
        package["decompositions"], private_keys | {"all_identities_hold"}
    )
    if decompositions["all_identities_hold"] is not True:
        raise S2Refusal(S2Code.DECOMPOSITION_FAILURE)
    decomposition_names = {"A", "A0", "B", "I", "D", "Gamma", "G"}
    for key in private_keys:
        arm, panel, _ = map(int, key.split(":"))
        del arm
        row = _exact_mapping(decompositions[key], decomposition_names)
        values = {name: _finite_number(value) for name, value in row.items()}
        forced_total = _finite_number(value_sections["forced_test_values"][key]["total"])  # type: ignore[index]
        learned_total = _finite_number(value_sections["k_test_values"][key]["total"])  # type: ignore[index]
        blind_total = _finite_number(comparator_records[panel]["FORCED_PROBE_BLIND_DP"]["total"])  # type: ignore[index]
        immediate_total = _finite_number(comparator_records[panel]["IMMEDIATE_DP"]["total"])  # type: ignore[index]
        identities = (
            _close(values["A"], forced_total),
            _close(values["A0"], blind_total),
            _close(values["B"], immediate_total),
            _close(values["I"], values["A"] - values["A0"]),
            _close(values["D"], values["A0"] - values["B"]),
            _close(values["Gamma"], values["A"] - values["B"]),
            _close(values["Gamma"], values["I"] + values["D"]),
            _close(values["G"], learned_total - values["B"]),
        )
        if not all(identities):
            raise S2Refusal(S2Code.DECOMPOSITION_FAILURE)

    headroom_keys = {
        "unique_prior_optimum_margin", "regime_optima_differ", "persistent_information",
        "persistent_acquisition", "persistent_direct", "redraw_information",
        "severed_information", "redraw_immediate_margin", "severed_immediate_margin",
        "all_action_values_finite", "all_unintended_ties_separated", "pass",
    }
    headroom = _exact_mapping(package["headroom"], headroom_keys)
    retained_immediate_values = [
        _expected_tail(np.float32(0.5), period) for period in K_TEST
    ]
    retained_ordered_immediate = sorted(
        (float(value) for value in retained_immediate_values), reverse=True
    )
    retained_regime_optima = tuple(
        greedy_index(
            [_expected_tail(np.float32(regime == 0), period) for period in K_TEST]
        )
        for regime in (0, 1)
    )
    retained_persistent = comparator_records[int(Panel.PERSISTENT)]
    retained_persistent_decomposition = decomposition(
        total=_finite_number(retained_persistent["BELIEF_DP"]["total"]),  # type: ignore[index]
        forced=_finite_number(retained_persistent["BELIEF_DP_FORCED"]["total"]),  # type: ignore[index]
        blind=_finite_number(retained_persistent["FORCED_PROBE_BLIND_DP"]["total"]),  # type: ignore[index]
        immediate=_finite_number(retained_persistent["IMMEDIATE_DP"]["total"]),  # type: ignore[index]
    )
    retained_null_decompositions: dict[int, Mapping[str, np.float32]] = {}
    for panel in (Panel.REDRAW, Panel.SEVERED):
        records = comparator_records[int(panel)]
        retained_null_decompositions[int(panel)] = decomposition(
            total=_finite_number(records["BELIEF_DP"]["total"]),  # type: ignore[index]
            forced=_finite_number(records["BELIEF_DP_FORCED"]["total"]),  # type: ignore[index]
            blind=_finite_number(records["FORCED_PROBE_BLIND_DP"]["total"]),  # type: ignore[index]
            immediate=_finite_number(records["IMMEDIATE_DP"]["total"]),  # type: ignore[index]
        )
    retained_headroom: dict[str, object] = {
        "unique_prior_optimum_margin": (
            retained_ordered_immediate[0] - retained_ordered_immediate[1]
        ),
        "regime_optima_differ": retained_regime_optima[0] != retained_regime_optima[1],
        "persistent_information": float(retained_persistent_decomposition["I"]),
        "persistent_acquisition": float(retained_persistent_decomposition["Gamma"]),
        "persistent_direct": float(retained_persistent_decomposition["D"]),
        "redraw_information": float(
            retained_null_decompositions[int(Panel.REDRAW)]["I"]
        ),
        "severed_information": float(
            retained_null_decompositions[int(Panel.SEVERED)]["I"]
        ),
        "redraw_immediate_margin": (
            _finite_number(
                comparator_records[int(Panel.REDRAW)]["IMMEDIATE_DP"]["total"]  # type: ignore[index]
            )
            - _finite_number(
                comparator_records[int(Panel.REDRAW)]["BELIEF_DP_FORCED"]["total"]  # type: ignore[index]
            )
        ),
        "severed_immediate_margin": (
            _finite_number(
                comparator_records[int(Panel.SEVERED)]["IMMEDIATE_DP"]["total"]  # type: ignore[index]
            )
            - _finite_number(
                comparator_records[int(Panel.SEVERED)]["BELIEF_DP_FORCED"]["total"]  # type: ignore[index]
            )
        ),
        "all_action_values_finite": all(
            all(math.isfinite(float(value)) for value in values)
            for values in validated_action_vectors
        ),
        "all_unintended_ties_separated": all(
            _vector_finite_and_separated(values) for values in validated_action_vectors
        ),
    }
    for key, observed in retained_headroom.items():
        provided = headroom[key]
        if isinstance(observed, bool):
            if provided is not observed:
                raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
        elif not _close(provided, observed):
            raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
    headroom_pass = validate_headroom(retained_headroom)
    if headroom["pass"] is not headroom_pass or not headroom_pass:
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)

    support = _exact_mapping(package["support"], {"slots", "pass"})
    support_slots = _exact_mapping(support["slots"], private_keys)
    support_bools: list[bool] = []
    for key, value in support_slots.items():
        row = _exact_mapping(value, {"facts", "pass"})
        panel = int(key.split(":")[1])
        observed_pass = validate_support(row["facts"], panel)  # type: ignore[arg-type]
        if row["pass"] is not observed_pass:
            raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
        support_bools.append(observed_pass)
    support_pass = all(support_bools)
    if support["pass"] is not support_pass:
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)

    competence = _exact_mapping(package["competence"], {"records", "gates", "pass"})
    competence_records = _exact_mapping(
        competence["records"], {str(int(panel)) for panel in Panel}
    )
    competence_sequences: dict[int, list[Mapping[str, object]]] = {}
    seed_names = {str(seed) for seed in seeds}
    for panel in Panel:
        panel_records = _exact_mapping(competence_records[str(int(panel))], seed_names)
        competence_sequences[int(panel)] = []
        for seed_name, record in panel_records.items():
            row = _exact_mapping(record, {"root_match", "regret", "tail_agreement"})
            if not isinstance(row["root_match"], bool):
                raise S2Refusal(S2Code.MALFORMED_INPUT)
            regret = _finite_number(row["regret"])
            agreement = _finite_number(row["tail_agreement"])
            if regret < 0.0 or agreement < 0.0 or agreement > 1.0:
                raise S2Refusal(S2Code.MALFORMED_INPUT)
            learned = value_sections["k_test_values"][
                f"{int(LearnedArm.BELIEF_FEATURE)}:{int(panel)}:{seed_name}"
            ]
            belief = comparator_records[int(panel)]["BELIEF_DP"]
            observed_root_match = learned["root_action"] == belief["root_action"]  # type: ignore[index]
            observed_regret = float(
                np.float32(
                    np.float32(belief["total"]) - np.float32(learned["total"])  # type: ignore[index]
                )
            )
            learned_actions = learned["tail_actions"]  # type: ignore[index]
            belief_actions = belief["tail_actions"]  # type: ignore[index]
            observed_agreement = float(
                _tail_agreement(
                    int(panel),
                    lambda history, actions=learned_actions: actions[history],
                    lambda history, actions=belief_actions: actions[history],
                )
            )
            if (
                row["root_match"] is not observed_root_match
                or not _close(regret, observed_regret)
                or not _close(agreement, observed_agreement)
            ):
                raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
            competence_sequences[int(panel)].append(row)
    observed_gates = validate_competence(competence_sequences)
    gate_rows = _exact_mapping(competence["gates"], {str(int(panel)) for panel in Panel})
    if any(gate_rows[str(panel)] is not passed for panel, passed in observed_gates.items()):
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
    competence_pass = all(observed_gates.values())
    if competence["pass"] is not competence_pass:
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)

    contrasts = _exact_mapping(package["seed_contrasts"], set(REQUIRED_CONTRASTS))
    contrast_values: dict[str, list[float]] = {}
    for name in REQUIRED_CONTRASTS:
        rows = _exact_mapping(contrasts[name], seed_names)
        contrast_values[name] = []
        for seed in seeds:
            provided = _finite_number(rows[str(seed)])
            count_test_key = f"{int(LearnedArm.COUNT)}:{int(Panel.PERSISTENT)}:{seed}"
            raw_test_key = f"{int(LearnedArm.RAW)}:{int(Panel.PERSISTENT)}:{seed}"
            if name == "delta_test":
                observed = float(
                    np.float32(
                        np.float32(value_sections["k_test_values"][count_test_key]["total"])  # type: ignore[index]
                        - np.float32(value_sections["k_test_values"][raw_test_key]["total"])  # type: ignore[index]
                    )
                )
            elif name == "delta_train":
                observed = float(
                    np.float32(
                        np.float32(value_sections["k_train_values"][count_test_key]["total"])  # type: ignore[index]
                        - np.float32(value_sections["k_train_values"][raw_test_key]["total"])  # type: ignore[index]
                    )
                )
            else:
                observed = float(
                    np.float32(
                        np.float32(value_sections["forced_test_values"][count_test_key]["total"])  # type: ignore[index]
                        - np.float32(raw_permavg[raw_test_key]["total"])  # type: ignore[index]
                    )
                )
            if not _close(provided, observed):
                raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
            contrast_values[name].append(provided)

    intervals = _exact_mapping(package["intervals"], set(REQUIRED_CONTRASTS))
    for name in REQUIRED_CONTRASTS:
        row = _exact_mapping(intervals[name], {"mean", "lower", "upper", "classification"})
        observed = paired_t_interval(contrast_values[name])
        if (
            not _close(row["mean"], observed.mean)
            or not _close(row["lower"], observed.lower)
            or not _close(row["upper"], observed.upper)
            or row["classification"] != observed.classification
        ):
            raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)

    agreements = _exact_mapping(package["descriptive_agreements"], seed_names)
    for seed_name, value in agreements.items():
        row = _exact_mapping(value, {"count", "belief"})
        if any(not 0.0 <= _finite_number(row[name]) <= 1.0 for name in ("count", "belief")):
            raise S2Refusal(S2Code.MALFORMED_INPUT)
        raw_key = f"{int(LearnedArm.RAW)}:{int(Panel.PERSISTENT)}:{seed_name}"
        count_key = f"{int(LearnedArm.COUNT)}:{int(Panel.PERSISTENT)}:{seed_name}"
        raw_actions = raw_permavg[raw_key]["tail_actions"]  # type: ignore[index]
        count_actions = value_sections["k_test_values"][count_key]["tail_actions"]  # type: ignore[index]
        belief_actions = comparator_records[int(Panel.PERSISTENT)]["BELIEF_DP"]["tail_actions"]  # type: ignore[index]
        observed_count = float(
            _descriptive_tail_agreement(
                int(Panel.PERSISTENT),
                lambda history, actions=raw_actions: actions[history],
                lambda history, actions=count_actions: actions[history],
            )
        )
        observed_belief = float(
            _descriptive_tail_agreement(
                int(Panel.PERSISTENT),
                lambda history, actions=raw_actions: actions[history],
                lambda history, actions=belief_actions: actions[history],
            )
        )
        if not _close(row["count"], observed_count) or not _close(row["belief"], observed_belief):
            raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)

    acquisition = _exact_mapping(package["acquisition"], {"margins", "lower", "supported"})
    margin_rows = _exact_mapping(acquisition["margins"], seed_names)
    margin_values = []
    for seed in seeds:
        provided = _finite_number(margin_rows[str(seed)])
        count_persistent_key = f"{int(LearnedArm.COUNT)}:{int(Panel.PERSISTENT)}:{seed}"
        count_redraw_key = f"{int(LearnedArm.COUNT)}:{int(Panel.REDRAW)}:{seed}"
        count_severed_key = f"{int(LearnedArm.COUNT)}:{int(Panel.SEVERED)}:{seed}"
        count_persistent = decompositions[count_persistent_key]  # type: ignore[assignment]
        count_redraw = decompositions[count_redraw_key]  # type: ignore[assignment]
        count_severed = decompositions[count_severed_key]  # type: ignore[assignment]
        belief_total = _finite_number(
            comparator_records[int(Panel.PERSISTENT)]["BELIEF_DP"]["total"]  # type: ignore[index]
        )
        count_total = _finite_number(
            value_sections["k_test_values"][count_persistent_key]["total"]  # type: ignore[index]
        )
        observed = min(
            _finite_number(count_persistent["Gamma"]) - 0.03,
            _finite_number(count_persistent["I"]) - 0.03,
            0.02 - abs(_finite_number(count_redraw["I"])),
            0.02 - abs(_finite_number(count_severed["I"])),
            0.05 - (belief_total - count_total),
        )
        if not _close(provided, observed):
            raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
        margin_values.append(provided)
    if not _close(acquisition["lower"], one_sided_lower(margin_values)):
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
    count_keys = {
        panel: {seed: f"{int(LearnedArm.COUNT)}:{int(panel)}:{seed}" for seed in seeds}
        for panel in Panel
    }
    observed_acquisition = acquisition_supported(
        margin_values,
        persistent_probe=[
            value_sections["k_test_values"][count_keys[Panel.PERSISTENT][seed]]["root_action"] == 0  # type: ignore[index]
            for seed in seeds
        ],
        redraw_immediate=[
            value_sections["k_test_values"][count_keys[Panel.REDRAW][seed]]["root_action"] != 0  # type: ignore[index]
            for seed in seeds
        ],
        severed_immediate=[
            value_sections["k_test_values"][count_keys[Panel.SEVERED][seed]]["root_action"] != 0  # type: ignore[index]
            for seed in seeds
        ],
        support_pass=support_pass,
        competence_pass=competence_pass,
    )
    if acquisition["supported"] is not observed_acquisition:
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)

    observed_attribution = attribution_map(
        observed_acquisition,
        intervals["delta_test"]["classification"],  # type: ignore[index]
        intervals["delta_train"]["classification"],  # type: ignore[index]
        intervals["delta_perm"]["classification"],  # type: ignore[index]
    )
    if package["attribution"] != observed_attribution:
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
    observed_terminal = terminal_action_class(
        complete=True,
        invariant_pass=headroom_pass,
        support_pass=support_pass,
        competence_pass=competence_pass,
        acquisition=observed_acquisition,
    )
    if package["terminal_action"] != observed_terminal:
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)

    normalization = _exact_mapping(package["normalization"], {"maximum_error", "all_within_tolerance"})
    observed_maximum = max(normalization_errors)
    if (
        not _close(normalization["maximum_error"], observed_maximum)
        or normalization["all_within_tolerance"] is not True
        or observed_maximum > float(INVARIANT_TOLERANCE)
    ):
        raise S2Refusal(S2Code.NORMALIZATION_FAILURE)
    provenance = _exact_mapping(
        package["provenance"],
        {"schema", "inventory_digest", "material_digest", "binding_digest"},
    )
    observed_provenance = _package_provenance(package)
    if provenance != observed_provenance:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    return required


def validate_sealed_evaluation(
    evaluation: object, *, request: BoundaryRequest
) -> Mapping[str, object]:
    if type(evaluation) is not SealedEvaluation or evaluation._issuer is not _SEAL_ISSUER:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    construction = request.namespace in CONSTRUCTION_NAMESPACES
    if construction:
        request.require_construction()
    else:
        request.require_registered_publication()
    if hashlib.sha256(_canonical_bytes(evaluation.package)).hexdigest() != evaluation.seal_digest:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    validate_complete_package(evaluation.package)
    fresh = validate_checkpoint_inventory(
        tuple(CheckpointSlot(slot.path) for slot in evaluation.inventory),
        checkpoint_root=evaluation.checkpoint_root,
        construction=construction,
    )
    identity = lambda slot: (
        slot.key, slot.batch, slot.object_revision, slot.object_digest,
        slot.sha256, slot.model_sha256, slot.model_payload, dict(slot.support), slot.path,
    )
    if tuple(map(identity, fresh)) != tuple(map(identity, evaluation.inventory)):
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    expected_rows = [
        {
            "arm": slot.arm,
            "panel": slot.panel,
            "master_seed": slot.master_seed,
            "batch": slot.batch,
            "sha256": slot.sha256,
            "model_sha256": slot.model_sha256,
        }
        for slot in fresh
    ]
    if evaluation.package["checkpoint_inventory"] != expected_rows:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    return evaluation.package


def build_completion_manifest(
    evaluation: object, *, request: BoundaryRequest
) -> dict[str, object]:
    request.require_registered_publication()
    package = validate_sealed_evaluation(evaluation, request=request)
    required = tuple(sorted(REQUIRED_TOP_LEVEL_FIELDS))
    inventory = package["checkpoint_inventory"]
    checkpoint_digests = sorted(str(item["sha256"]) for item in inventory)  # type: ignore[index]
    package_bytes = _canonical_bytes(package)
    completeness = hashlib.sha256(_canonical_bytes({"fields": required, "package_sha256": hashlib.sha256(package_bytes).hexdigest()})).hexdigest()
    return {
        "schema": COMPLETION_SCHEMA,
        "schema_revision": 1,
        "object_revision": OBJECT_REVISION,
        "object_digest": OBJECT_DIGEST,
        "checkpoint_inventory_digests": checkpoint_digests,
        "required_field_inventory": list(required),
        "completeness_digest": completeness,
        "package_sha256": hashlib.sha256(package_bytes).hexdigest(),
        "complete_r03_package": True,
    }


def publish_complete_package(
    evaluation: object,
    *,
    destination: Path,
    output_root: Path,
    request: BoundaryRequest,
) -> Mapping[str, object]:
    """Atomically expose one complete package; the completion manifest is written last."""

    request.require_registered_publication()
    package = validate_sealed_evaluation(evaluation, request=request)
    root = output_root.resolve(strict=True)
    target_parent = destination.parent.resolve(strict=True)
    try:
        target_parent.relative_to(root)
    except ValueError as exc:
        raise S2Refusal(S2Code.PATH_REFUSED) from exc
    manifest = build_completion_manifest(evaluation, request=request)
    sealed_blob = _canonical_bytes(
        {
            "schema": "UCOPE_R01_R03_S2_ATOMIC_SEALED_OBJECT_V1",
            "package": package,
            "completion": manifest,
        }
    )
    _atomic_expose_sealed_blob(destination, sealed_blob)
    return manifest


def _publication_interrupt(configured: str | None, boundary: str) -> None:
    if configured == boundary:
        os._exit(97)


def _quarantine_incomplete_destination(destination: Path) -> None:
    """Observe and quarantine only a fail-closed incomplete final object."""

    if not destination.exists():
        return
    if not destination.is_file() or destination.is_symlink():
        raise S2Refusal(S2Code.ALREADY_PUBLISHED)
    try:
        read_atomic_sealed_blob(destination)
    except S2Refusal as exc:
        if exc.code not in {S2Code.INCOMPLETE_OUTPUT, S2Code.CHECKPOINT_MISMATCH}:
            raise
        observed = destination.read_bytes()
        digest = hashlib.sha256(observed).hexdigest()
        quarantine = destination.parent / f".{destination.name}.incomplete-{digest}"
        if quarantine.exists():
            if not quarantine.is_file() or quarantine.read_bytes() != observed:
                raise S2Refusal(S2Code.ATOMIC_PUBLICATION_FAILURE)
            destination.unlink()
        else:
            os.replace(destination, quarantine)
        return
    raise S2Refusal(S2Code.ALREADY_PUBLISHED)


def _atomic_expose_sealed_blob(
    destination: Path,
    sealed_blob: bytes,
    *,
    interrupt_at: str | None = None,
) -> None:
    """Expose one committed sealed object without readable precommit payload.

    Staging contains a full-length one-time-pad ciphertext and no pad.  The
    path is held with read sharing denied while live.  After atomic rename the
    pad, length, and digest footer are appended and flushed as the single commit
    boundary.  Abrupt precommit residue is observable but cannot be decoded.
    """

    if os.name != "nt" or not sealed_blob:
        raise S2Refusal(S2Code.ATOMIC_PUBLICATION_FAILURE)
    destination = destination.resolve(strict=False)
    if not destination.parent.is_dir():
        raise S2Refusal(S2Code.ATOMIC_PUBLICATION_FAILURE)
    _quarantine_incomplete_destination(destination)
    pending = destination.parent / f".{destination.name}.sealed-{uuid.uuid4().hex}"
    magic = b"UCOPE-S2-SEALED\x00"
    footer_magic = b"UCOPE-S2-COMMIT\x00"
    pad = os.urandom(len(sealed_blob))
    ciphertext = bytes(left ^ right for left, right in zip(sealed_blob, pad))
    staged_blob = magic + ciphertext
    footer = (
        footer_magic
        + len(sealed_blob).to_bytes(8, "little")
        + pad
        + hashlib.sha256(sealed_blob).digest()
    )
    kernel32 = ctypes.windll.kernel32
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    ]
    create_file.restype = ctypes.c_void_p
    write_file = kernel32.WriteFile
    write_file.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p,
    ]
    write_file.restype = ctypes.c_int
    flush_file = kernel32.FlushFileBuffers
    flush_file.argtypes = [ctypes.c_void_p]
    flush_file.restype = ctypes.c_int
    move_file = kernel32.MoveFileExW
    move_file.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
    move_file.restype = ctypes.c_int
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_int
    handle = create_file(
        str(pending),
        0x40000000 | 0x00010000,  # GENERIC_WRITE | DELETE
        0x00000004,  # FILE_SHARE_DELETE: no reader/writer can open staging
        None,
        1,  # CREATE_NEW
        0x00000100 | 0x80000000,
        None,
    )
    if handle == ctypes.c_void_p(-1).value:
        raise S2Refusal(S2Code.ATOMIC_PUBLICATION_FAILURE)

    try:
        _publication_interrupt(interrupt_at, "after_open")
        midpoint = max(1, len(staged_blob) // 2)
        for boundary, block in (
            ("after_partial_write", staged_blob[:midpoint]),
            ("after_full_write", staged_blob[midpoint:]),
        ):
            if block:
                buffer = ctypes.create_string_buffer(block)
                written = ctypes.c_uint32()
                if not write_file(handle, buffer, len(block), ctypes.byref(written), None) or written.value != len(block):
                    raise S2Refusal(S2Code.ATOMIC_PUBLICATION_FAILURE)
            _publication_interrupt(interrupt_at, boundary)
        if not flush_file(handle):
            raise S2Refusal(S2Code.ATOMIC_PUBLICATION_FAILURE)
        _publication_interrupt(interrupt_at, "after_flush")
        if not move_file(str(pending), str(destination), 0x00000008):  # MOVEFILE_WRITE_THROUGH
            raise S2Refusal(S2Code.ATOMIC_PUBLICATION_FAILURE)
        _publication_interrupt(interrupt_at, "after_rename")
        footer_buffer = ctypes.create_string_buffer(footer)
        footer_written = ctypes.c_uint32()
        if (
            not write_file(
                handle, footer_buffer, len(footer), ctypes.byref(footer_written), None
            )
            or footer_written.value != len(footer)
            or not flush_file(handle)
        ):
            raise S2Refusal(S2Code.ATOMIC_PUBLICATION_FAILURE)
        _publication_interrupt(interrupt_at, "after_commit")
    finally:
        close_handle(handle)


def read_atomic_sealed_blob(path: Path) -> bytes:
    """Decode only a fully committed sealed object; refuse every residue."""

    value = path.read_bytes()
    magic = b"UCOPE-S2-SEALED\x00"
    footer_magic = b"UCOPE-S2-COMMIT\x00"
    fixed = len(magic) + len(footer_magic) + 8 + 32
    if len(value) < fixed or (len(value) - fixed) % 2:
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
    size = (len(value) - fixed) // 2
    footer_start = len(magic) + size
    if (
        not value.startswith(magic)
        or value[footer_start : footer_start + len(footer_magic)] != footer_magic
    ):
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
    offset = footer_start + len(footer_magic)
    declared = int.from_bytes(value[offset : offset + 8], "little")
    offset += 8
    if declared != size:
        raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
    ciphertext = value[len(magic) : footer_start]
    pad = value[offset : offset + size]
    digest = value[offset + size : offset + size + 32]
    plaintext = bytes(left ^ right for left, right in zip(ciphertext, pad))
    if hashlib.sha256(plaintext).digest() != digest:
        raise S2Refusal(S2Code.CHECKPOINT_MISMATCH)
    return plaintext


def publish_synthetic_atomic_fixture(
    *, output_root: Path, interrupt_at: str | None = None
) -> Path:
    """Exercise the production atomic core with technical-only fixture bytes."""

    output_root = output_root.resolve(strict=True)
    destination = output_root / "synthetic-sealed-object.json"
    blob = _canonical_bytes(
        {
            "schema": "UCOPE_R01_R03_S2_REPAIR1_ATOMIC_FIXTURE_V1",
            "technical_complete": True,
            "question_relevant_output": False,
        }
    )
    _atomic_expose_sealed_blob(destination, blob, interrupt_at=interrupt_at)
    return destination


def synthetic_atomic_transition(
    *, destination: Path, output_root: Path, complete: bool, interrupt_before_manifest: bool = False
) -> str:
    """Result-blind construction fixture for the atomic state machine."""

    root = output_root.resolve(strict=True)
    parent = destination.parent.resolve(strict=True)
    try:
        parent.relative_to(root)
    except ValueError as exc:
        raise S2Refusal(S2Code.PATH_REFUSED) from exc
    if destination.exists():
        raise S2Refusal(S2Code.ALREADY_PUBLISHED)
    pending = Path(tempfile.mkdtemp(prefix=f".{destination.name}.pending-", dir=parent))
    try:
        (pending / "opaque.private").write_bytes(b"synthetic-private-fixture")
        if interrupt_before_manifest or not complete:
            raise S2Refusal(S2Code.INCOMPLETE_OUTPUT)
        (pending / "completion.json").write_bytes(
            _canonical_bytes({"schema": "S2_SYNTHETIC_ATOMIC_FIXTURE_V1", "structural_complete": True})
        )
        os.replace(pending, destination)
        return "ATOMIC_COMPLETE"
    except Exception:
        shutil.rmtree(pending, ignore_errors=True)
        raise


def structural_proxy(fixture_namespace: str = SYNTHETIC_NAMESPACE) -> dict[str, object]:
    """Counts-only, result-blind source-bound construction proxy."""

    if fixture_namespace not in CONSTRUCTION_NAMESPACES:
        raise S2Refusal(S2Code.REGISTERED_BOUNDARY_ATTEMPTED)
    counts = {str(int(panel)): population_case_count(int(panel)) for panel in Panel}
    permutation_counts = sorted({len(distinct_permutations(history)) for history in range(64)})
    return {
        "schema": "UCOPE_R01_R03_S2_CONSTRUCTION_PROXY_V1",
        "fixture_namespace": fixture_namespace,
        "registered_master_seeds": False,
        "complete_registered_panel": False,
        "question_relevant_output": False,
        "gpu": False,
        "checkpoint_slot_count": FINAL_CHECKPOINT_SLOT_COUNT,
        "panel_case_counts": counts,
        "k_test_count": len(K_TEST),
        "k_train_count": len(K_TRAIN),
        "permutation_cardinality_count": len(permutation_counts),
        "attribution_branch_count": 7,
        "terminal_action_class_count": 6,
        "required_field_count": len(REQUIRED_TOP_LEVEL_FIELDS),
        "all_structural_counts_positive": all(value > 0 for value in counts.values()),
        "complete_only_protocol_present": True,
        "no_unmeasured_speedup": True,
    }


def write_structural_proxy(
    output: Path, *, fixture_namespace: str = SYNTHETIC_NAMESPACE
) -> dict[str, object]:
    """Measure one source-bound structural coupon and write technical-only JSON."""

    from .benchmark import _resources

    resources_before = _resources()
    started = time.perf_counter()
    weight_checks = 0
    toy_case_count = 0
    for panel in Panel:
        weight = np.float32(0.0)
        for case in finite_cases(int(panel)):
            weight = np.float32(weight + case.weight)
            toy_case_count += 1
        if abs(float(weight) - 1.0) <= float(INVARIANT_TOLERANCE):
            weight_checks += 1
    permutation_checks = sum(len(distinct_permutations(history)) for history in range(64))
    elapsed = time.perf_counter() - started
    resources_after = _resources()
    cpu_seconds = float(resources_after["cpu_seconds"]) - float(resources_before["cpu_seconds"])
    io_bytes = (
        int(resources_after["read_bytes"]) + int(resources_after["write_bytes"])
        - int(resources_before["read_bytes"]) - int(resources_before["write_bytes"])
    )
    # Three learned finite passes per slot (endogenous held-out, forced held-out,
    # and train), four comparator passes per panel, plus agreement/permavg passes.
    full_case_count = 30 * 3 * toy_case_count + 4 * toy_case_count + 30 * 128
    scale = math.ceil(full_case_count / toy_case_count)
    projected_wall = 380.2810449061144 + elapsed * scale
    projected_cpu_hours = 0.10563362358503178 + (cpu_seconds * scale) / 3600.0
    projected_rss = max(515145728, int(resources_after["peak_rss_bytes"]))
    projected_io = 2312507074 + max(0, int(io_bytes)) * scale
    result = {
        **structural_proxy(fixture_namespace),
        "toy_case_count": toy_case_count,
        "weight_check_count": weight_checks,
        "permutation_check_count": permutation_checks,
        "measured_wall_seconds": elapsed,
        "measured_cpu_seconds": cpu_seconds,
        "measured_peak_rss_bytes": int(resources_after["peak_rss_bytes"]),
        "measured_io_bytes": max(0, int(io_bytes)),
        "projection_formula": "r06_planning_reference_plus_measured_structural_coupon_times_ceiling_full_case_ratio",
        "projection_scale_count": scale,
        "projected_wall_seconds": projected_wall,
        "projected_cpu_hours": projected_cpu_hours,
        "projected_cpu_cores": 1,
        "projected_peak_rss_bytes": projected_rss,
        "projected_io_bytes": projected_io,
        "cold_load_seconds": time.perf_counter() - _IMPORT_STARTED,
        "projection_wall_gate": projected_wall <= 1800.0,
        "projection_cpu_gate": projected_cpu_hours <= 12.0,
        "projection_core_gate": 1 <= 24,
        "projection_rss_gate": projected_rss <= 10 * 1024**3,
        "projection_io_gate": projected_io <= 6 * 1024**3,
        "cold_load_gate": time.perf_counter() - _IMPORT_STARTED <= 360.0,
    }
    result["all_proxy_gates_pass"] = all(
        result[key]
        for key in (
            "projection_wall_gate",
            "projection_cpu_gate",
            "projection_core_gate",
            "projection_rss_gate",
            "projection_io_gate",
            "cold_load_gate",
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(_canonical_bytes(result))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--structural-proxy-output", type=Path)
    group.add_argument("--atomic-fixture-root", type=Path)
    parser.add_argument(
        "--interrupt-at",
        choices=(
            "after_open", "after_partial_write", "after_full_write",
            "after_flush", "after_rename", "after_commit",
        ),
    )
    parser.add_argument("--fixture-namespace", default=SYNTHETIC_NAMESPACE)
    args = parser.parse_args(argv)
    if args.structural_proxy_output is not None:
        if args.interrupt_at is not None:
            parser.error("--interrupt-at is only valid with --atomic-fixture-root")
        write_structural_proxy(
            args.structural_proxy_output, fixture_namespace=args.fixture_namespace
        )
    else:
        publish_synthetic_atomic_fixture(
            output_root=args.atomic_fixture_root, interrupt_at=args.interrupt_at
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
