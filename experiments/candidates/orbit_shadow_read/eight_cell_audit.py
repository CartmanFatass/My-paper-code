"""Deterministic ORBIT eight-cell cloned shadow-read audit.

The bundled fixture is synthetic implementation evidence.  It performs no
training, gradient update, task rollout, or utility measurement.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import json
import math


SCHEMAS = (
    ("F_match", ("snapshot_digest", "current_state", "legal_actions", "recurrent_state")),
    ("F_TQ", ("snapshot_digest", "current_state", "legal_actions", "role", "age")),
    (
        "F_ORBIT",
        ("payload", "valid", "age", "actor_tensor", "recurrent_state", "evaluation_order"),
    ),
    (
        "F_audit",
        ("source_snapshot_digest", "writer_input_digest", "ancestry_digest", "auth_digest"),
    ),
)


class Terminal(str, Enum):
    LOGIT_AND_KERNEL = "PASS_LOGIT_INTERACTION_REACHES_FIRST_ACTION_KERNEL"
    LOGIT_ONLY = "PASS_LOGIT_LEVEL_ONLY"
    KERNEL_ONLY = "KERNEL_NONSEPARABILITY_ONLY"
    NONE = "NO_REGISTERED_INTERACTION"
    INVALID = "INVALID_OR_PARK_SHADOW_AUDIT"


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    owner_epoch: int
    current_state: tuple[float, ...]
    legal_actions: tuple[str, ...]
    recurrent_state: tuple[float, ...]


@dataclass(frozen=True)
class WriterInput:
    source_snapshot_digest: str
    writer_schema: str
    b: int


@dataclass(frozen=True)
class SiblingWrite:
    writer_input: WriterInput
    payload: bytes
    valid: bool
    age: int
    writer_input_digest: str
    ancestry_digest: str
    auth_digest: str


@dataclass(frozen=True)
class Clone:
    clone_id: str
    snapshot: Snapshot
    source_bytes_digest: str


@dataclass(frozen=True)
class ActorInput:
    payload: bytes
    valid: bool
    age: int
    actor_tensor: tuple[float, ...]
    recurrent_state: tuple[float, ...]
    legal_actions: tuple[str, ...]
    evaluation_order: tuple[int, ...]


@dataclass(frozen=True)
class CellRecord:
    b: int
    role: int
    q: int
    clone_id: str
    snapshot_digest: str
    write_auth_digest: str
    actor_input: ActorInput
    logits: tuple[float, ...]
    kernel: tuple[float, ...]
    support: bool


@dataclass(frozen=True)
class Calibration:
    manifest_ids: tuple[str, str]
    calibration_snapshot_digest: str
    eta_logit: float
    eta_kernel: float
    one_ulp_logit: float
    one_ulp_kernel: float
    tau_logit: float
    tau_kernel: float
    delta_logit: float
    delta_kernel: float


@dataclass(frozen=True)
class AuditResult:
    terminal: Terminal
    valid: bool
    theta_logit: float
    theta_kernel: float
    strict_theta_logit: float
    strict_theta_kernel: float
    calibration: Calibration
    cells: tuple[CellRecord, ...]
    owner_agnostic_null_reproduces: bool
    invariants: tuple[tuple[str, bool], ...]

    def to_bytes(self) -> bytes:
        payload = {
            "calibration": {
                "delta_kernel": _clean(self.calibration.delta_kernel),
                "delta_logit": _clean(self.calibration.delta_logit),
                "eta_kernel": _clean(self.calibration.eta_kernel),
                "eta_logit": _clean(self.calibration.eta_logit),
                "manifest_ids": list(self.calibration.manifest_ids),
                "tau_kernel": _clean(self.calibration.tau_kernel),
                "tau_logit": _clean(self.calibration.tau_logit),
            },
            "cells": [_cell_payload(cell) for cell in self.cells],
            "invariants": {name: value for name, value in self.invariants},
            "owner_agnostic_null_reproduces": self.owner_agnostic_null_reproduces,
            "strict_theta_kernel": _clean(self.strict_theta_kernel),
            "strict_theta_logit": _clean(self.strict_theta_logit),
            "terminal": self.terminal.value,
            "theta_kernel": _clean(self.theta_kernel),
            "theta_logit": _clean(self.theta_logit),
            "valid": self.valid,
        }
        return json.dumps(
            payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")


def build_snapshot() -> Snapshot:
    return Snapshot(
        snapshot_id="synthetic-prior-epoch-s0",
        owner_epoch=7,
        current_state=(0.25, -0.25),
        legal_actions=("a0", "a1"),
        recurrent_state=(0.0, 0.0),
    )


def serialize_snapshot(snapshot: Snapshot) -> bytes:
    payload = {
        "current_state": list(snapshot.current_state),
        "legal_actions": list(snapshot.legal_actions),
        "owner_epoch": snapshot.owner_epoch,
        "recurrent_state": list(snapshot.recurrent_state),
        "snapshot_id": snapshot.snapshot_id,
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def restore_clone(source: bytes, clone_id: str) -> Clone:
    payload = json.loads(source)
    snapshot = Snapshot(
        snapshot_id=payload["snapshot_id"],
        owner_epoch=int(payload["owner_epoch"]),
        current_state=tuple(float(value) for value in payload["current_state"]),
        legal_actions=tuple(payload["legal_actions"]),
        recurrent_state=tuple(float(value) for value in payload["recurrent_state"]),
    )
    if serialize_snapshot(snapshot) != source:
        raise ValueError("snapshot roundtrip is not byte equivalent")
    return Clone(clone_id, snapshot, _digest(source))


def write_sibling(snapshot: Snapshot, b: int) -> SiblingWrite:
    if b not in (0, 1):
        raise ValueError("B must be binary")
    source_digest = _digest(serialize_snapshot(snapshot))
    writer_input = WriterInput(source_digest, "orbit-sibling-writer-v1", b)
    input_bytes = _writer_input_bytes(writer_input)
    payload = bytes((b,))
    input_digest = _digest(input_bytes)
    ancestry_digest = _digest(
        source_digest.encode("ascii") + input_digest.encode("ascii") + payload
    )
    auth_digest = _digest(b"orbit-auth-v1\x00" + ancestry_digest.encode("ascii"))
    return SiblingWrite(
        writer_input,
        payload,
        True,
        0,
        input_digest,
        ancestry_digest,
        auth_digest,
    )


def verify_sibling(write: SiblingWrite) -> bool:
    if write.writer_input.b not in (0, 1) or write.payload != bytes((write.writer_input.b,)):
        return False
    if write.writer_input_digest != _digest(_writer_input_bytes(write.writer_input)):
        return False
    ancestry = _digest(
        write.writer_input.source_snapshot_digest.encode("ascii")
        + write.writer_input_digest.encode("ascii")
        + write.payload
    )
    auth = _digest(b"orbit-auth-v1\x00" + ancestry.encode("ascii"))
    return (
        write.valid
        and write.age == 0
        and write.ancestry_digest == ancestry
        and write.auth_digest == auth
    )


def q_adapter(clone: Clone, write: SiblingWrite, role: int, q: int) -> ActorInput:
    if role not in (0, 1) or q not in (0, 1):
        raise ValueError("role and Q alias must be binary")
    if not verify_sibling(write):
        raise ValueError("sibling provenance is invalid")
    if write.writer_input.source_snapshot_digest != clone.source_bytes_digest:
        raise ValueError("sibling and clone source snapshots differ")
    snapshot = clone.snapshot
    actor_tensor = snapshot.current_state + (float(write.payload[0]), float(role))
    return ActorInput(
        payload=write.payload,
        valid=write.valid,
        age=write.age,
        actor_tensor=actor_tensor,
        recurrent_state=snapshot.recurrent_state,
        legal_actions=snapshot.legal_actions,
        evaluation_order=tuple(range(len(snapshot.legal_actions))),
    )


def actor(actor_input: ActorInput) -> tuple[float, float]:
    b, role = (int(value) for value in actor_input.actor_tensor[-2:])
    interaction = 0.5 if b == role else -0.5
    return interaction, -interaction


def strict_temporal_null(snapshot: Snapshot, role: int, age: int) -> tuple[float, float]:
    """F_TQ-only null: its signature cannot receive payload or B-derived data."""

    if role not in (0, 1) or age < 0:
        raise ValueError("invalid public temporal input")
    public_role_effect = 0.125 if role else -0.125
    del snapshot
    return public_role_effect, -public_role_effect


def owner_agnostic_payload_null(actor_input: ActorInput) -> tuple[float, float]:
    """Strongest owner-agnostic null reads payload but no owner identity."""

    return actor(actor_input)


def calibrate() -> Calibration:
    snapshot = Snapshot(
        snapshot_id="disjoint-calibration-s0",
        owner_epoch=3,
        current_state=(0.125, -0.125),
        legal_actions=("hold", "advance"),
        recurrent_state=(0.125, -0.125),
    )
    source = serialize_snapshot(snapshot)
    write = write_sibling(snapshot, 0)
    calibration_digest = _digest(source)
    clone = restore_clone(source, "calibration-clone")
    actor_input = q_adapter(clone, write, 0, 0)
    logits_a, logits_b = actor(actor_input), actor(actor_input)
    kernels_a, kernels_b = _softmax(logits_a), _softmax(logits_b)
    eta_logit = max(abs(a - b) for a, b in zip(logits_a, logits_b))
    eta_kernel = max(abs(a - b) for a, b in zip(kernels_a, kernels_b))
    one_ulp_logit = math.ulp(max(1.0, *(abs(value) for value in logits_a)))
    one_ulp_kernel = math.ulp(max(1.0, *(abs(value) for value in kernels_a)))
    tau_logit = 8.0 * max(eta_logit, one_ulp_logit)
    tau_kernel = 8.0 * max(eta_kernel, one_ulp_kernel)
    return Calibration(
        manifest_ids=("calibration-duplicate-a", "calibration-duplicate-b"),
        calibration_snapshot_digest=calibration_digest,
        eta_logit=eta_logit,
        eta_kernel=eta_kernel,
        one_ulp_logit=one_ulp_logit,
        one_ulp_kernel=one_ulp_kernel,
        tau_logit=tau_logit,
        tau_kernel=tau_kernel,
        delta_logit=4.0 * tau_logit,
        delta_kernel=4.0 * tau_kernel,
    )


def classify(
    valid: bool,
    theta_logit: float,
    theta_kernel: float,
    delta_logit: float,
    delta_kernel: float,
) -> Terminal:
    if not valid:
        return Terminal.INVALID
    logit = theta_logit > delta_logit
    kernel = theta_kernel > delta_kernel
    if logit and kernel:
        return Terminal.LOGIT_AND_KERNEL
    if logit:
        return Terminal.LOGIT_ONLY
    if kernel:
        return Terminal.KERNEL_ONLY
    return Terminal.NONE


def run_eight_cell_audit() -> AuditResult:
    snapshot = build_snapshot()
    source = serialize_snapshot(snapshot)
    source_digest = _digest(source)
    writes = (write_sibling(snapshot, 0), write_sibling(snapshot, 1))
    records: list[CellRecord] = []
    for b in (0, 1):
        for role in (0, 1):
            for q in (0, 1):
                clone = restore_clone(source, f"clone-b{b}-r{role}-q{q}")
                actor_input = q_adapter(clone, writes[b], role, q)
                logits = actor(actor_input)
                records.append(
                    CellRecord(
                        b,
                        role,
                        q,
                        clone.clone_id,
                        clone.source_bytes_digest,
                        writes[b].auth_digest,
                        actor_input,
                        logits,
                        _softmax(logits),
                        True,
                    )
                )
    cells = tuple(records)
    d_logit = _interaction(cells, "logits", center=True)
    d_kernel = _interaction(cells, "kernel", center=False)
    theta_logit = math.sqrt(sum(value * value for value in d_logit))
    theta_kernel = 0.5 * sum(abs(value) for value in d_kernel)

    strict_cells = tuple(
        replace(
            cell,
            logits=strict_temporal_null(snapshot, cell.role, cell.actor_input.age),
            kernel=_softmax(
                strict_temporal_null(snapshot, cell.role, cell.actor_input.age)
            ),
        )
        for cell in cells
    )
    strict_d_logit = _interaction(strict_cells, "logits", center=True)
    strict_d_kernel = _interaction(strict_cells, "kernel", center=False)
    strict_theta_logit = math.sqrt(sum(value * value for value in strict_d_logit))
    strict_theta_kernel = 0.5 * sum(abs(value) for value in strict_d_kernel)
    calibration = calibrate()

    sibling_only_b = replace(writes[0].writer_input, b=1) == writes[1].writer_input
    support_keys = tuple((cell.b, cell.role, cell.q) for cell in cells)
    q_equivalent = all(
        _find(cells, b, role, 0).actor_input == _find(cells, b, role, 1).actor_input
        for b in (0, 1)
        for role in (0, 1)
    )
    clones_equal = len({cell.clone_id for cell in cells}) == 8 and all(
        cell.snapshot_digest == source_digest for cell in cells
    )
    replay = all(
        actor(cell.actor_input) == cell.logits
        and _softmax(cell.logits) == cell.kernel
        and cell.write_auth_digest == writes[cell.b].auth_digest
        for cell in cells
    )
    owner_null = all(
        owner_agnostic_payload_null(cell.actor_input) == cell.logits for cell in cells
    )
    expected_keys = tuple(
        (b, role, q)
        for b in (0, 1)
        for role in (0, 1)
        for q in (0, 1)
    )
    schema_names = tuple(name for name, _ in SCHEMAS)
    calibration_disjoint = (
        calibration.manifest_ids[0] != calibration.manifest_ids[1]
        and calibration.calibration_snapshot_digest != source_digest
    )
    invariants = (
        (
            "explicit_field_schemas",
            schema_names == ("F_match", "F_TQ", "F_ORBIT", "F_audit"),
        ),
        ("sibling_b_is_sole_writer_input_difference", sibling_only_b),
        ("authenticated_provenance", all(verify_sibling(write) for write in writes)),
        (
            "whole_block_support",
            support_keys == expected_keys and all(cell.support for cell in cells),
        ),
        ("q_lookup_byte_equivalence", q_equivalent),
        ("independent_immutable_clones", clones_equal),
        ("ancestry_replay", replay),
        ("final_residual_zero_marginal", _zero_marginal(cells)),
        ("strict_temporal_null_b_blind", strict_theta_logit == 0.0 and strict_theta_kernel == 0.0),
        ("disjoint_duplicate_calibration", calibration_disjoint),
        ("owner_agnostic_payload_null_reproduces", owner_null),
    )
    valid = all(
        value
        for name, value in invariants
        if name != "owner_agnostic_payload_null_reproduces"
    )
    terminal = classify(
        valid,
        theta_logit,
        theta_kernel,
        calibration.delta_logit,
        calibration.delta_kernel,
    )
    return AuditResult(
        terminal,
        valid,
        theta_logit,
        theta_kernel,
        strict_theta_logit,
        strict_theta_kernel,
        calibration,
        cells,
        owner_null,
        invariants,
    )


def _interaction(
    cells: tuple[CellRecord, ...], field: str, *, center: bool
) -> tuple[float, ...]:
    result = [0.0, 0.0]
    for q in (0, 1):
        values = {}
        for b in (0, 1):
            for role in (0, 1):
                vector = getattr(_find(cells, b, role, q), field)
                values[b, role] = _center(vector) if center else vector
        for action in (0, 1):
            result[action] += 0.5 * (
                values[1, 1][action]
                - values[0, 1][action]
                - values[1, 0][action]
                + values[0, 0][action]
            )
    return tuple(result)


def _zero_marginal(cells: tuple[CellRecord, ...]) -> bool:
    for q in (0, 1):
        vectors = {
            (b, role): _center(_find(cells, b, role, q).logits)
            for b in (0, 1)
            for role in (0, 1)
        }
        grand = tuple(sum(vector[a] for vector in vectors.values()) / 4.0 for a in (0, 1))
        row_means = {
            b: tuple(sum(vectors[b, role][a] for role in (0, 1)) / 2.0 for a in (0, 1))
            for b in (0, 1)
        }
        column_means = {
            role: tuple(sum(vectors[b, role][a] for b in (0, 1)) / 2.0 for a in (0, 1))
            for role in (0, 1)
        }
        residual = {
            (b, role): tuple(
                vectors[b, role][a] - row_means[b][a] - column_means[role][a] + grand[a]
                for a in (0, 1)
            )
            for b in (0, 1)
            for role in (0, 1)
        }
        for b in (0, 1):
            if any(sum(residual[b, role][a] for role in (0, 1)) != 0.0 for a in (0, 1)):
                return False
        for role in (0, 1):
            if any(sum(residual[b, role][a] for b in (0, 1)) != 0.0 for a in (0, 1)):
                return False
    return True


def _find(cells: tuple[CellRecord, ...], b: int, role: int, q: int) -> CellRecord:
    return next(cell for cell in cells if (cell.b, cell.role, cell.q) == (b, role, q))


def _softmax(logits: tuple[float, ...]) -> tuple[float, ...]:
    maximum = max(logits)
    values = tuple(math.exp(value - maximum) for value in logits)
    total = sum(values)
    return tuple(value / total for value in values)


def _center(vector: tuple[float, ...]) -> tuple[float, ...]:
    mean = sum(vector) / len(vector)
    return tuple(value - mean for value in vector)


def _writer_input_bytes(item: WriterInput) -> bytes:
    return json.dumps(
        {
            "b": item.b,
            "source_snapshot_digest": item.source_snapshot_digest,
            "writer_schema": item.writer_schema,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _cell_payload(cell: CellRecord) -> dict[str, object]:
    return {
        "B": cell.b,
        "Q": cell.q,
        "clone_id": cell.clone_id,
        "kernel": [_clean(value) for value in cell.kernel],
        "logits": [_clean(value) for value in cell.logits],
        "role": cell.role,
        "support": cell.support,
    }


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _clean(value: float) -> float:
    value = round(float(value), 15)
    return 0.0 if value == 0.0 else value
