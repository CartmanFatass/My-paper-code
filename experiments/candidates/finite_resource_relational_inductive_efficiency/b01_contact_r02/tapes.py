"""R02 tape addresses: B01 laws with the frozen B02 seed identity."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from ..b01.contract import B01ContractError, canonical_json_bytes
from ..orchestration import OriginCoordinate
from ..rng import AddressedRNG
from ..tapes import (
    EVENT_BASINS,
    EVENTS_PER_BASIN,
    EVENT_SLOT_COUNT,
    HORIZON,
    NATIVE_MAX_AGENTS,
    PUBLIC_ROLES,
    SURVEYOR_ROLE_COUNT,
    NativeEnvironmentTapePayload,
    generate_episode_tape,
    generate_training_origin_schedule,
)
from .semantics import SEED_LABEL, TEST_SEED_LABEL

ROSTERS = (9, 15)
SEED_LABELS = (SEED_LABEL, TEST_SEED_LABEL, "FRRIE-B07-CONTACT-BLOCK-002", "FRRIE-B09-CONTACT-BLOCK-003")
KINDS = {
    "event_time", "detection_uniform", "uplink_uniform", "base_uniform", "action_uniform",
}


def _frozen(value: np.ndarray, dtype: Any) -> np.ndarray:
    source = np.asarray(value, dtype=dtype, order="C")
    result = np.frombuffer(source.tobytes(order="C"), dtype=np.dtype(dtype)).reshape(source.shape)
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class R02EvaluationAddress:
    seed_label: str
    roster: int
    episode: int
    kind: str
    basin: int | None = None
    event_ordinal: int | None = None
    slot: int | None = None
    public_role: int | None = None
    role_local_index: int | None = None
    sender: int | None = None
    receiver: int | None = None
    draw: int = 0

    def validate(self) -> "R02EvaluationAddress":
        if self.seed_label not in SEED_LABELS or self.roster not in ROSTERS:
            raise B01ContractError("R02 evaluation address identity differs")
        if type(self.episode) is not int or not 0 <= self.episode < 256:
            raise B01ContractError("R02 evaluation episode is outside [0,255]")
        if self.kind not in KINDS or type(self.draw) is not int or not 0 <= self.draw < 2**32:
            raise B01ContractError("R02 evaluation random-variable kind/draw is invalid")
        multiplicity = self.roster // 3
        bounds = {
            "basin": 2, "event_ordinal": 3, "slot": HORIZON,
            "public_role": 3, "role_local_index": multiplicity,
            "sender": self.roster, "receiver": self.roster,
        }
        present = set()
        for field, upper in bounds.items():
            value = getattr(self, field)
            if value is not None:
                if type(value) is not int or not 0 <= value < upper:
                    raise B01ContractError(f"R02 evaluation address {field} is invalid")
                present.add(field)
        agent = {"slot", "public_role", "role_local_index", "sender"}
        expected = {
            "event_time": {"basin", "event_ordinal"},
            "detection_uniform": agent,
            "uplink_uniform": agent | {"receiver"},
            "base_uniform": agent,
            "action_uniform": agent,
        }[self.kind]
        if present != expected:
            raise B01ContractError(f"R02 {self.kind} address fields are incomplete")
        if agent <= present:
            if self.sender != self.public_role * multiplicity + self.role_local_index:
                raise B01ContractError("R02 sender differs from role-local identity")
            if self.kind == "detection_uniform" and self.public_role not in (0, 1):
                raise B01ContractError("R02 detection draws exist only for surveyors")
        return self

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes({
            "schema": "FRRIE_B01_EVALUATION_ADDRESS_V1", **asdict(self.validate()),
        })


class R02EvaluationRNG:
    def __init__(self, root: bytes) -> None:
        if type(root) is not bytes or len(root) != 32:
            raise B01ContractError("R02 evaluation root must contain exactly 32 bytes")
        self.root = root

    def block(self, address: R02EvaluationAddress, retry: int = 0) -> bytes:
        return hashlib.sha256(
            b"FRRIE-B01-EVALUATION-RNG-V1\0" + self.root
            + address.canonical_bytes() + retry.to_bytes(4, "big")
        ).digest()

    def uniform_float32(self, address: R02EvaluationAddress) -> float:
        return int.from_bytes(self.block(address)[:3], "big") * (1.0 / 2**24)

    def integer(self, address: R02EvaluationAddress, upper: int) -> int:
        limit = 2**64 - (2**64 % upper)
        for retry in range(1_000_000):
            value = int.from_bytes(self.block(address, retry)[:8], "big")
            if value < limit:
                return value % upper
        raise RuntimeError("unreachable R02 rejection bound")


@dataclass(frozen=True, slots=True)
class R02EvaluationTape:
    seed_label: str
    roster: int
    episode: int
    event_times: np.ndarray
    detection_uniform: np.ndarray
    uplink_uniform: np.ndarray
    base_uniform: np.ndarray
    action_uniform: np.ndarray

    def __post_init__(self) -> None:
        if self.seed_label not in SEED_LABELS or self.roster not in ROSTERS:
            raise B01ContractError("R02 evaluation tape identity differs")
        multiplicity = self.roster // 3
        expected = {
            "event_times": (np.int64, (2, 3)),
            "detection_uniform": (np.float32, (HORIZON, 2, multiplicity)),
            "uplink_uniform": (np.float32, (HORIZON, self.roster, self.roster)),
            "base_uniform": (np.float32, (HORIZON, self.roster)),
            "action_uniform": (np.float32, (HORIZON, self.roster)),
        }
        for field, (dtype, shape) in expected.items():
            array = _frozen(getattr(self, field), dtype)
            if array.shape != shape:
                raise B01ContractError(f"R02 evaluation tape {field} shape differs")
            object.__setattr__(self, field, array)
        for row in self.event_times:
            if len(set(map(int, row))) != 3 or np.any((row < 0) | (row >= 8)):
                raise B01ContractError("R02 evaluation event slots are invalid")
        for field in ("detection_uniform", "uplink_uniform", "base_uniform", "action_uniform"):
            array = getattr(self, field)
            if not np.isfinite(array).all() or np.any((array < 0.0) | (array >= 1.0)):
                raise B01ContractError(f"R02 evaluation tape {field} is outside [0,1)")

    def native_environment_payload(self) -> NativeEnvironmentTapePayload:
        detection = np.zeros((HORIZON, NATIVE_MAX_AGENTS), dtype=np.float32)
        multiplicity = self.roster // 3
        for role in range(SURVEYOR_ROLE_COUNT):
            start = role * multiplicity
            detection[:, start:start + multiplicity] = self.detection_uniform[:, role, :]
        uplink = np.zeros((HORIZON, NATIVE_MAX_AGENTS, NATIVE_MAX_AGENTS), dtype=np.float32)
        uplink[:, :self.roster, :self.roster] = self.uplink_uniform
        base = np.zeros((HORIZON, NATIVE_MAX_AGENTS), dtype=np.float32)
        base[:, :self.roster] = self.base_uniform
        return NativeEnvironmentTapePayload(
            roster=self.roster,
            event_times=self.event_times.astype(np.int32),
            detection_uniforms=detection,
            uplink_uniforms=uplink,
            base_uniforms=base,
        )


def _address(
    *, seed_label: str, roster: int, episode: int, kind: str, **fields: Any,
) -> R02EvaluationAddress:
    return R02EvaluationAddress(seed_label, roster, episode, kind, **fields).validate()


def evaluation_tape(
    root: bytes, *, seed_label: str, roster: int, episode: int,
) -> R02EvaluationTape:
    rng = R02EvaluationRNG(root)
    event_times = np.empty((EVENT_BASINS, EVENTS_PER_BASIN), dtype=np.int64)
    for basin in range(EVENT_BASINS):
        remaining = list(range(EVENT_SLOT_COUNT))
        for ordinal in range(EVENTS_PER_BASIN):
            event_times[basin, ordinal] = remaining.pop(rng.integer(_address(
                seed_label=seed_label, roster=roster, episode=episode, kind="event_time",
                basin=basin, event_ordinal=ordinal,
            ), len(remaining)))
    multiplicity = roster // len(PUBLIC_ROLES)
    detection = np.empty((HORIZON, 2, multiplicity), dtype=np.float32)
    uplink = np.empty((HORIZON, roster, roster), dtype=np.float32)
    base = np.empty((HORIZON, roster), dtype=np.float32)
    action = np.empty((HORIZON, roster), dtype=np.float32)
    for slot in range(HORIZON):
        for sender in range(roster):
            role, local = divmod(sender, multiplicity)
            common = dict(
                roster=roster, episode=episode, slot=slot,
                seed_label=seed_label,
                public_role=role, role_local_index=local, sender=sender,
            )
            base[slot, sender] = rng.uniform_float32(_address(**common, kind="base_uniform"))
            action[slot, sender] = rng.uniform_float32(_address(**common, kind="action_uniform"))
            if role < 2:
                detection[slot, role, local] = rng.uniform_float32(
                    _address(**common, kind="detection_uniform")
                )
            for receiver in range(roster):
                uplink[slot, sender, receiver] = rng.uniform_float32(
                    _address(**common, receiver=receiver, kind="uplink_uniform")
                )
    return R02EvaluationTape(
        seed_label, roster, episode, event_times, detection, uplink, base, action,
    )


def production_training_inputs(
    root: bytes, seed_label: str, update: int,
) -> tuple[tuple[Any, ...], tuple[tuple[OriginCoordinate, ...], ...]]:
    rng = AddressedRNG(root)
    schedules = {
        roster: generate_training_origin_schedule(
            rng, seed_block=seed_label, roster=roster, update=update, purpose="TRAIN",
        )
        for roster in ROSTERS
    }
    by_coordinate = {
        (roster, episode): tuple(
            OriginCoordinate(row.public_role_index, row.selected_slot, row.simulator_index)
            for row in sorted(
                (item for item in schedule.selections if item.episode == episode),
                key=lambda item: item.public_role_index,
            )
        )
        for roster, schedule in schedules.items()
        for episode in range(32)
    }
    roster_order = ROSTERS * 32
    tapes = tuple(
        generate_episode_tape(
            rng, seed_block=seed_label, purpose="TRAIN", roster=roster,
            update=update, episode=position // 2,
        )
        for position, roster in enumerate(roster_order)
    )
    return tapes, tuple(by_coordinate[(tape.roster, tape.episode)] for tape in tapes)
