"""B01 addressed training and checkpoint-invariant evaluation tapes."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Final

import numpy as np

from ..rng import AddressedRNG
from ..tapes import (
    EVENT_BASINS, EVENTS_PER_BASIN, EVENT_SLOT_COUNT, HORIZON,
    NATIVE_MAX_AGENTS, PUBLIC_ROLES, SURVEYOR_ROLE_COUNT, EpisodeTape,
    NativeEnvironmentTapePayload, generate_episode_tape,
)
from .constants import (
    CHECKPOINTS, EVALUATION_EPISODES, EVALUATION_ROSTERS, ROOT_LABELS,
    TEST_SEED_LABELS,
)
from .contract import B01ContractError, canonical_json_bytes

EVALUATION_ADDRESS_SCHEMA: Final = "FRRIE_B01_EVALUATION_ADDRESS_V1"
EVALUATION_TAPE_SCHEMA: Final = "FRRIE_B01_EVALUATION_TAPE_V1"
_KINDS: Final = {
    "event_time", "detection_uniform", "uplink_uniform", "base_uniform", "action_uniform",
}


def _frozen(value: np.ndarray, dtype: Any) -> np.ndarray:
    source = np.asarray(value, dtype=dtype, order="C")
    result = np.frombuffer(source.tobytes(order="C"), dtype=np.dtype(dtype)).reshape(source.shape)
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class B01EvaluationAddress:
    """Semantic coordinate with no arm/intervention/checkpoint field."""

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

    def validate(self) -> "B01EvaluationAddress":
        if self.seed_label not in (*ROOT_LABELS, *TEST_SEED_LABELS):
            raise B01ContractError("B01 evaluation address seed label is not registered")
        if self.roster not in EVALUATION_ROSTERS:
            raise B01ContractError("B01 evaluation roster is invalid")
        if type(self.episode) is not int or not 0 <= self.episode < EVALUATION_EPISODES:
            raise B01ContractError("B01 evaluation episode is outside [0,255]")
        if self.kind not in _KINDS or type(self.draw) is not int or not 0 <= self.draw < 2**32:
            raise B01ContractError("B01 evaluation random-variable kind/draw is invalid")
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
                    raise B01ContractError(f"B01 evaluation address {field} is invalid")
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
            raise B01ContractError(f"B01 {self.kind} address fields are incomplete")
        if agent <= present:
            if self.sender != self.public_role * multiplicity + self.role_local_index:
                raise B01ContractError("B01 sender differs from role-local identity")
            if self.kind == "detection_uniform" and self.public_role not in (0, 1):
                raise B01ContractError("detection draws exist only for surveyors")
        return self

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes({"schema": EVALUATION_ADDRESS_SCHEMA, **asdict(self.validate())})


class B01EvaluationRNG:
    """Stateless TOP24 PRF for the B01 evaluation panel."""

    def __init__(self, root: bytes) -> None:
        if type(root) is not bytes or len(root) != 32:
            raise B01ContractError("B01 evaluation root must contain exactly 32 bytes")
        self._root = root

    def block(self, address: B01EvaluationAddress, retry: int = 0) -> bytes:
        if type(retry) is not int or not 0 <= retry < 2**32:
            raise B01ContractError("B01 evaluation retry is outside uint32")
        return hashlib.sha256(
            b"FRRIE-B01-EVALUATION-RNG-V1\0" + self._root
            + address.canonical_bytes() + retry.to_bytes(4, "big")
        ).digest()

    def uniform_float32(self, address: B01EvaluationAddress) -> float:
        return int.from_bytes(self.block(address)[:3], "big") * (1.0 / 2**24)

    def integer(self, address: B01EvaluationAddress, upper: int) -> int:
        if type(upper) is not int or upper <= 0:
            raise B01ContractError("B01 integer upper bound must be positive")
        limit = 2**64 - (2**64 % upper)
        for retry in range(1_000_000):
            value = int.from_bytes(self.block(address, retry)[:8], "big")
            if value < limit:
                return value % upper
        raise RuntimeError("unreachable B01 rejection bound")


@dataclass(frozen=True, slots=True)
class B01EvaluationTape:
    seed_label: str
    roster: int
    episode: int
    event_times: np.ndarray
    detection_uniform: np.ndarray
    uplink_uniform: np.ndarray
    base_uniform: np.ndarray
    action_uniform: np.ndarray

    def __post_init__(self) -> None:
        if self.seed_label not in (*ROOT_LABELS, *TEST_SEED_LABELS) or self.roster not in EVALUATION_ROSTERS:
            raise B01ContractError("B01 evaluation tape identity is invalid")
        if type(self.episode) is not int or not 0 <= self.episode < EVALUATION_EPISODES:
            raise B01ContractError("B01 evaluation tape episode is invalid")
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
                raise B01ContractError(f"B01 evaluation tape {field} shape differs")
            object.__setattr__(self, field, array)
        for row in self.event_times:
            if len(set(map(int, row))) != 3 or np.any((row < 0) | (row >= 8)):
                raise B01ContractError("B01 evaluation event slots are invalid")
        for field in ("detection_uniform", "uplink_uniform", "base_uniform", "action_uniform"):
            array = getattr(self, field)
            if not np.isfinite(array).all() or np.any((array < 0.0) | (array >= 1.0)):
                raise B01ContractError(f"B01 evaluation tape {field} is outside [0,1)")

    def direct_bytes(self) -> bytes:
        return b"".join(
            getattr(self, field).tobytes(order="C")
            for field in (
                "event_times", "detection_uniform", "uplink_uniform",
                "base_uniform", "action_uniform",
            )
        )

    def binding(self, checkpoint: int) -> dict[str, Any]:
        if checkpoint not in CHECKPOINTS:
            raise B01ContractError("checkpoint is outside the B01 curve")
        return {
            "schema": EVALUATION_TAPE_SCHEMA,
            "seed_label": self.seed_label,
            "roster": self.roster,
            "episode": self.episode,
            "checkpoint": checkpoint,
            "checkpoint_role": "METADATA_ONLY",
            "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
            "arm_independent": True,
            "intervention_independent": True,
            "checkpoint_independent": True,
            "uniform_mapping": "TOP24 / 2**24",
        }

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


def _address(*, seed_label: str, roster: int, episode: int, kind: str, **fields: Any) -> B01EvaluationAddress:
    return B01EvaluationAddress(
        seed_label=seed_label, roster=roster, episode=episode, kind=kind, **fields,
    ).validate()


def evaluation_tape(
    root: bytes, *, seed_label: str, roster: int, episode: int,
) -> B01EvaluationTape:
    rng = B01EvaluationRNG(root)
    event_times = np.empty((EVENT_BASINS, EVENTS_PER_BASIN), dtype=np.int64)
    for basin in range(EVENT_BASINS):
        remaining = list(range(EVENT_SLOT_COUNT))
        for ordinal in range(EVENTS_PER_BASIN):
            event_times[basin, ordinal] = remaining.pop(rng.integer(_address(
                seed_label=seed_label, roster=roster, episode=episode,
                kind="event_time", basin=basin, event_ordinal=ordinal,
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
                seed_label=seed_label, roster=roster, episode=episode, slot=slot,
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
    return B01EvaluationTape(
        seed_label, roster, episode, event_times, detection, uplink, base, action,
    )

def training_tape(
    root: bytes, *, seed_label: str, roster: int, update: int, episode: int,
) -> EpisodeTape:
    """Reuse only the accepted TRAIN address/TOP24 semantics."""

    if seed_label not in ROOT_LABELS:
        raise B01ContractError("B01 training seed label is not registered")
    return generate_episode_tape(
        AddressedRNG(root), seed_block=seed_label, purpose="TRAIN",
        roster=roster, update=update, episode=episode,
    )
