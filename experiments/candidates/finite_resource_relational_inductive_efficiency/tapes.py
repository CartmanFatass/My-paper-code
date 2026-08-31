"""Complete immutable addressed rollout tapes for the FRRIE native boundary.

This module materializes potential randomness before a trajectory begins.
Consequently an action, collision, listener, delivery, intervention, or shadow
branch cannot create or suppress a draw.  The arrays are C-contiguous,
read-only FP32/int64 values suitable for a batched native environment call;
this is not a Python environment fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from .contracts.core import ContractError, FP32_PROBABILITY_TOLERANCE
from .rng import AddressedRNG, SemanticRNGAddress, float32_uniform_mapping_contract

ALLOWED_ROSTERS = (6, 9, 15, 21)
TRAIN_ROSTERS = (9, 15)
HORIZON = 12
NATIVE_MAX_AGENTS = 21
EVENT_BASINS = 2
EVENTS_PER_BASIN = 3
EVENT_SLOT_COUNT = 8
PUBLIC_ROLES = ("W", "E", "R")
SURVEYOR_ROLE_COUNT = 2
TRAIN_EPISODES_PER_ROSTER = 32
TRAIN_PAIRS_PER_ROSTER = 16

EPISODE_TAPE_SCHEMA = "FRRIE_COMPLETE_EPISODE_TAPE_V1"
EPISODE_TAPE_RECEIPT_SCHEMA = "FRRIE_DIRECT_TAPE_RECEIPT_V1"
ORIGIN_SCHEDULE_SCHEMA = "FRRIE_RSCF_ORIGIN_SCHEDULE_V1"
_CONTRACT_ROLE_NAMES = ("WEST_SURVEYOR", "EAST_SURVEYOR", "RIDGE_RELAY")


def _readonly_array(value: np.ndarray, dtype: np.dtype[Any]) -> np.ndarray:
    copied = np.array(value, dtype=dtype, order="C", copy=True)
    # Immutable bytes, rather than an owning ndarray, are the ultimate base;
    # callers therefore cannot reverse the read-only flag with setflags().
    result = np.frombuffer(copied.tobytes(order="C"), dtype=dtype).reshape(copied.shape)
    result.setflags(write=False)
    return result


def _validate_rollout_coordinate(
    purpose: str, roster: int, update: int, episode: int,
) -> None:
    if purpose not in {"TRAIN", "EVALUATE", "TEST_ONLY"}:
        raise ContractError("episode tape purpose must be TRAIN, EVALUATE, or TEST_ONLY")
    if type(roster) is not int or roster not in ALLOWED_ROSTERS:
        raise ContractError("episode tape roster must be one of 6, 9, 15, or 21")
    if type(update) is not int or not 0 <= update <= 512:
        raise ContractError("episode tape update must be in [0,512]")
    if type(episode) is not int or episode < 0:
        raise ContractError("episode tape episode must be nonnegative")
    if purpose == "TRAIN" and (
        roster not in TRAIN_ROSTERS or not 1 <= update <= 512
        or episode >= TRAIN_EPISODES_PER_ROSTER
    ):
        raise ContractError("TRAIN episode tape coordinate is outside the per-roster panel")
    if purpose == "EVALUATE" and (not 1 <= update <= 512 or episode >= 256):
        raise ContractError("EVALUATE episode tape coordinate is outside the panel")
    if purpose == "TEST_ONLY" and episode >= 256:
        raise ContractError("TEST_ONLY episode tape episode must be in [0,255]")


def _semantic_address(
    *,
    seed_block: str,
    purpose: str,
    roster: int,
    update: int,
    episode: int,
    kind: str,
    basin: int | None = None,
    event_ordinal: int | None = None,
    slot: int | None = None,
    public_role: int | None = None,
    role_local_index: int | None = None,
    sender: int | None = None,
    receiver: int | None = None,
    draw: int = 0,
) -> SemanticRNGAddress:
    return SemanticRNGAddress(
        seed_block=seed_block,
        purpose=purpose,
        roster=roster,
        update=update,
        episode=episode,
        basin=basin,
        event_ordinal=event_ordinal,
        slot=slot,
        public_role=public_role,
        role_local_index=role_local_index,
        sender=sender,
        receiver=receiver,
        kind=kind,
        draw=draw,
    ).validate()


@dataclass(frozen=True, slots=True)
class EpisodeTapeReceipt:
    """A direct coordinate/shape receipt containing no root or random value."""

    schema: str
    seed_block: str
    purpose: str
    roster: int
    update: int
    episode: int
    shapes: tuple[tuple[str, tuple[int, ...]], ...]
    dtypes: tuple[tuple[str, str], ...]
    coordinate_counts: tuple[tuple[str, int], ...]
    uniform_mapping: tuple[tuple[str, Any], ...]
    complete: bool
    stateless: bool

    def as_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "seed_block": self.seed_block,
            "purpose": self.purpose,
            "roster": self.roster,
            "update": self.update,
            "episode": self.episode,
            "shapes": {name: list(shape) for name, shape in self.shapes},
            "dtypes": dict(self.dtypes),
            "coordinate_counts": dict(self.coordinate_counts),
            "uniform_mapping": dict(self.uniform_mapping),
            "complete": self.complete,
            "stateless": self.stateless,
        }


@dataclass(frozen=True, slots=True)
class NativeEnvironmentTapePayload:
    """Fixed-width read-only arrays for one native reset input.

    The native ABI receives ``roster`` and must ignore the deterministic zero
    padding at indices ``[roster, 21)``.  Action uniforms are intentionally
    absent: the external actor owns inverse-CDF sampling.
    """

    roster: int
    event_times: np.ndarray
    detection_uniforms: np.ndarray
    uplink_uniforms: np.ndarray
    base_uniforms: np.ndarray

    def __post_init__(self) -> None:
        arrays = {
            "event_times": (self.event_times, np.dtype(np.int32), (2, 3)),
            "detection_uniforms": (
                self.detection_uniforms,
                np.dtype(np.float32),
                (HORIZON, NATIVE_MAX_AGENTS),
            ),
            "uplink_uniforms": (
                self.uplink_uniforms,
                np.dtype(np.float32),
                (HORIZON, NATIVE_MAX_AGENTS, NATIVE_MAX_AGENTS),
            ),
            "base_uniforms": (
                self.base_uniforms,
                np.dtype(np.float32),
                (HORIZON, NATIVE_MAX_AGENTS),
            ),
        }
        if self.roster not in ALLOWED_ROSTERS:
            raise ContractError("native tape payload roster is invalid")
        for name, (value, dtype, shape) in arrays.items():
            frozen = _readonly_array(value, dtype)
            if frozen.shape != shape:
                raise ContractError(f"native tape payload {name} shape must equal {shape}")
            object.__setattr__(self, name, frozen)
        if np.any(self.detection_uniforms[:, self.roster:] != 0.0):
            raise ContractError("native detection padding must remain zero")
        if np.any(self.base_uniforms[:, self.roster:] != 0.0):
            raise ContractError("native base padding must remain zero")
        if np.any(self.uplink_uniforms[:, self.roster:, :] != 0.0) or np.any(
            self.uplink_uniforms[:, :, self.roster:] != 0.0
        ):
            raise ContractError("native uplink padding must remain zero")


@dataclass(frozen=True, slots=True)
class EpisodeTape:
    """One complete episode's potential randomness, frozen before rollout."""

    seed_block: str
    purpose: str
    roster: int
    update: int
    episode: int
    event_times: np.ndarray
    detection_uniform: np.ndarray
    uplink_uniform: np.ndarray
    base_uniform: np.ndarray
    action_uniform: np.ndarray

    def __post_init__(self) -> None:
        _validate_rollout_coordinate(self.purpose, self.roster, self.update, self.episode)
        multiplicity = self.roster // len(PUBLIC_ROLES)
        arrays = {
            "event_times": (self.event_times, np.dtype(np.int64), (EVENT_BASINS, EVENTS_PER_BASIN)),
            "detection_uniform": (
                self.detection_uniform,
                np.dtype(np.float32),
                (HORIZON, SURVEYOR_ROLE_COUNT, multiplicity),
            ),
            "uplink_uniform": (
                self.uplink_uniform,
                np.dtype(np.float32),
                (HORIZON, self.roster, self.roster),
            ),
            "base_uniform": (
                self.base_uniform, np.dtype(np.float32), (HORIZON, self.roster),
            ),
            "action_uniform": (
                self.action_uniform, np.dtype(np.float32), (HORIZON, self.roster),
            ),
        }
        for name, (value, dtype, shape) in arrays.items():
            frozen = _readonly_array(value, dtype)
            if frozen.shape != shape:
                raise ContractError(f"episode tape {name} shape must equal {shape}")
            object.__setattr__(self, name, frozen)
        for basin in range(EVENT_BASINS):
            row = self.event_times[basin]
            if len(set(int(value) for value in row)) != EVENTS_PER_BASIN or np.any(
                (row < 0) | (row >= EVENT_SLOT_COUNT)
            ):
                raise ContractError("each basin needs exactly three distinct event slots in [0,7]")
        for name in (
            "detection_uniform", "uplink_uniform", "base_uniform", "action_uniform",
        ):
            value = getattr(self, name)
            if not np.isfinite(value).all() or np.any((value < 0.0) | (value >= 1.0)):
                raise ContractError(f"episode tape {name} must contain finite values in [0,1)")

    @property
    def shapes(self) -> tuple[tuple[str, tuple[int, ...]], ...]:
        return tuple(
            (name, tuple(getattr(self, name).shape))
            for name in (
                "event_times", "detection_uniform", "uplink_uniform",
                "base_uniform", "action_uniform",
            )
        )

    def receipt(self) -> EpisodeTapeReceipt:
        multiplicity = self.roster // len(PUBLIC_ROLES)
        return EpisodeTapeReceipt(
            schema=EPISODE_TAPE_RECEIPT_SCHEMA,
            seed_block=self.seed_block,
            purpose=self.purpose,
            roster=self.roster,
            update=self.update,
            episode=self.episode,
            shapes=self.shapes,
            dtypes=tuple(
                (name, str(getattr(self, name).dtype)) for name, _ in self.shapes
            ),
            coordinate_counts=(
                ("event_time", EVENT_BASINS * EVENTS_PER_BASIN),
                ("detection_uniform", HORIZON * SURVEYOR_ROLE_COUNT * multiplicity),
                ("uplink_uniform", HORIZON * self.roster * self.roster),
                ("base_uniform", HORIZON * self.roster),
                ("action_uniform", HORIZON * self.roster),
            ),
            uniform_mapping=tuple(float32_uniform_mapping_contract().items()),
            complete=True,
            stateless=True,
        )

    def native_environment_payload(self) -> NativeEnvironmentTapePayload:
        """Pad active semantic potentials to the frozen 21-agent native ABI."""

        detection = np.zeros((HORIZON, NATIVE_MAX_AGENTS), dtype=np.float32)
        multiplicity = self.roster // len(PUBLIC_ROLES)
        for role in range(SURVEYOR_ROLE_COUNT):
            start = role * multiplicity
            detection[:, start:start + multiplicity] = self.detection_uniform[:, role, :]
        uplink = np.zeros(
            (HORIZON, NATIVE_MAX_AGENTS, NATIVE_MAX_AGENTS), dtype=np.float32,
        )
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


def _entity_coordinates(roster: int, sender: int) -> tuple[int, int]:
    multiplicity = roster // len(PUBLIC_ROLES)
    return sender // multiplicity, sender % multiplicity


def generate_episode_tape(
    rng: AddressedRNG,
    *,
    seed_block: str,
    purpose: str,
    roster: int,
    update: int,
    episode: int,
) -> EpisodeTape:
    """Materialize every native environment and external-actor potential.

    The signature deliberately has no arm, cut, intervention, factual/shadow,
    or branch argument.  Callers reuse this object literally across those
    executions.
    """

    if not isinstance(rng, AddressedRNG):
        raise ContractError("episode tape generation requires AddressedRNG")
    _validate_rollout_coordinate(purpose, roster, update, episode)
    multiplicity = roster // len(PUBLIC_ROLES)

    event_times = np.empty((EVENT_BASINS, EVENTS_PER_BASIN), dtype=np.int64)
    for basin in range(EVENT_BASINS):
        remaining = list(range(EVENT_SLOT_COUNT))
        for ordinal in range(EVENTS_PER_BASIN):
            address = _semantic_address(
                seed_block=seed_block, purpose=purpose, roster=roster,
                update=update, episode=episode, kind="event_time",
                basin=basin, event_ordinal=ordinal,
            )
            event_times[basin, ordinal] = remaining.pop(rng.integer(address, len(remaining)))

    detection_uniform = np.empty(
        (HORIZON, SURVEYOR_ROLE_COUNT, multiplicity), dtype=np.float32,
    )
    for slot in range(HORIZON):
        for public_role in range(SURVEYOR_ROLE_COUNT):
            for local_index in range(multiplicity):
                sender = public_role * multiplicity + local_index
                address = _semantic_address(
                    seed_block=seed_block, purpose=purpose, roster=roster,
                    update=update, episode=episode, kind="detection_uniform",
                    slot=slot, public_role=public_role,
                    role_local_index=local_index, sender=sender,
                )
                detection_uniform[slot, public_role, local_index] = rng.uniform_float32(address)

    uplink_uniform = np.empty((HORIZON, roster, roster), dtype=np.float32)
    base_uniform = np.empty((HORIZON, roster), dtype=np.float32)
    action_uniform = np.empty((HORIZON, roster), dtype=np.float32)
    for slot in range(HORIZON):
        for sender in range(roster):
            public_role, local_index = _entity_coordinates(roster, sender)
            common = {
                "seed_block": seed_block, "purpose": purpose, "roster": roster,
                "update": update, "episode": episode, "slot": slot,
                "public_role": public_role, "role_local_index": local_index,
                "sender": sender,
            }
            base_uniform[slot, sender] = rng.uniform_float32(
                _semantic_address(**common, kind="base_uniform")
            )
            action_uniform[slot, sender] = rng.uniform_float32(
                _semantic_address(**common, kind="action_uniform")
            )
            for receiver in range(roster):
                uplink_uniform[slot, sender, receiver] = rng.uniform_float32(
                    _semantic_address(**common, receiver=receiver, kind="uplink_uniform")
                )

    return EpisodeTape(
        seed_block=seed_block,
        purpose=purpose,
        roster=roster,
        update=update,
        episode=episode,
        event_times=event_times,
        detection_uniform=detection_uniform,
        uplink_uniform=uplink_uniform,
        base_uniform=base_uniform,
        action_uniform=action_uniform,
    )


def episode_tape_contract(
    *, seed_block: str, purpose: str, roster: int, update: int, episode: int,
) -> Mapping[str, Any]:
    """Return the direct tape contract without consuming a root or exposing values."""

    _validate_rollout_coordinate(purpose, roster, update, episode)
    multiplicity = roster // len(PUBLIC_ROLES)
    return {
        "schema": EPISODE_TAPE_SCHEMA,
        "seed_block": seed_block,
        "purpose": purpose,
        "roster": roster,
        "update": update,
        "episode": episode,
        "horizon": HORIZON,
        "shapes": {
            "event_times": [EVENT_BASINS, EVENTS_PER_BASIN],
            "detection_uniform": [HORIZON, SURVEYOR_ROLE_COUNT, multiplicity],
            "uplink_uniform": [HORIZON, roster, roster],
            "base_uniform": [HORIZON, roster],
            "action_uniform": [HORIZON, roster],
        },
        "uniform_mapping": float32_uniform_mapping_contract(),
        "complete": True,
        "stateless": True,
    }


def origin_schedule_contract() -> dict[str, Any]:
    """Return the direct runtime law for RSCF origin address construction."""

    return {
        "pairs_per_roster_update": TRAIN_PAIRS_PER_ROSTER,
        "episodes_per_roster_update": TRAIN_EPISODES_PER_ROSTER,
        "roles_in_order": list(_CONTRACT_ROLE_NAMES),
        "one_origin_per_episode_role": True,
        "base_slot_support": list(range(HORIZON)),
        "antithetic_pair_law": "slot_side0 + slot_side1 = 11",
        "base_slot_address_includes_side": False,
        "base_slot_shared_across_pair_sides": True,
        "side0_slot": "BASE_SLOT",
        "side1_slot": "11_MINUS_BASE_SLOT",
        "role_local_index_address_includes_side": True,
        "role_local_entity_shared_across_pair_sides": False,
        "role_local_entity_draws_independent_across_pair_sides": True,
        "role_local_index_support": "0..N/3-1",
        "matching_episode_coordinate_shared_across_arms": True,
    }


def training_origin_addresses(
    *,
    seed_block: str,
    roster: int,
    update: int,
    pair: int,
    side: int,
    public_role: int,
    purpose: str = "TRAIN",
) -> tuple[SemanticRNGAddress, SemanticRNGAddress]:
    """Return the base-slot and side-specific local-index coordinates.

    The base address deliberately uses the pair's side-zero episode coordinate
    for both sides.  The role-local address uses ``2*pair + side``; this is how
    side enters the otherwise label-free semantic RNG address.  No arm field
    exists, so matching episode coordinates are common across learned arms.
    """

    if purpose not in {"TRAIN", "TEST_ONLY"} or roster not in TRAIN_ROSTERS:
        raise ContractError("origin addresses require TRAIN/TEST_ONLY and roster 9 or 15")
    if type(update) is not int or not (
        1 <= update <= 512 if purpose == "TRAIN" else 0 <= update <= 512
    ):
        raise ContractError("origin address update is outside its purpose domain")
    if type(pair) is not int or not 0 <= pair < TRAIN_PAIRS_PER_ROSTER:
        raise ContractError("origin address pair must be in [0,15]")
    if type(side) is not int or side not in (0, 1):
        raise ContractError("origin address side must be zero or one")
    if type(public_role) is not int or not 0 <= public_role < len(PUBLIC_ROLES):
        raise ContractError("origin address public role must be W, E, or R")
    base_address = _semantic_address(
        seed_block=seed_block, purpose=purpose, roster=roster,
        update=update, episode=2 * pair, kind="origin_base_slot",
        public_role=public_role,
    )
    local_address = _semantic_address(
        seed_block=seed_block, purpose=purpose, roster=roster,
        update=update, episode=2 * pair + side,
        kind="origin_role_local_index", public_role=public_role,
    )
    return base_address, local_address


@dataclass(frozen=True, slots=True)
class OriginSelection:
    pair: int
    side: int
    episode: int
    public_role: str
    public_role_index: int
    base_slot: int
    selected_slot: int
    role_local_index: int
    simulator_index: int


@dataclass(frozen=True, slots=True)
class OriginSchedule:
    schema: str
    seed_block: str
    purpose: str
    roster: int
    update: int
    selections: tuple[OriginSelection, ...]

    def __post_init__(self) -> None:
        if self.schema != ORIGIN_SCHEDULE_SCHEMA:
            raise ContractError("origin schedule schema mismatch")
        if self.purpose not in {"TRAIN", "TEST_ONLY"} or self.roster not in TRAIN_ROSTERS:
            raise ContractError("origin schedule is defined only for training rosters")
        expected = {
            (pair, side, role)
            for pair in range(TRAIN_PAIRS_PER_ROSTER)
            for side in (0, 1)
            for role in range(len(PUBLIC_ROLES))
        }
        observed = {
            (item.pair, item.side, item.public_role_index) for item in self.selections
        }
        if len(self.selections) != len(expected) or observed != expected:
            raise ContractError("origin schedule must contain one origin per episode and role")
        by_pair_role: dict[tuple[int, int], dict[int, OriginSelection]] = {}
        for item in self.selections:
            by_pair_role.setdefault((item.pair, item.public_role_index), {})[item.side] = item
            if item.episode != 2 * item.pair + item.side:
                raise ContractError("origin episode must equal the pair/side schedule")
            if item.public_role != PUBLIC_ROLES[item.public_role_index]:
                raise ContractError("origin public role label/index mismatch")
            if item.simulator_index != (
                item.public_role_index * (self.roster // 3) + item.role_local_index
            ):
                raise ContractError("origin hidden role-local simulator identity mismatch")
        for sides in by_pair_role.values():
            if sides[0].base_slot != sides[1].base_slot:
                raise ContractError("paired origin base slot must omit side")
            if sides[0].selected_slot + sides[1].selected_slot != HORIZON - 1:
                raise ContractError("paired origin slots must be antithetic")

    def receipt(self) -> Mapping[str, Any]:
        """Return schedule coordinates/counts without roots or selected values."""

        return {
            "schema": ORIGIN_SCHEDULE_SCHEMA,
            "seed_block": self.seed_block,
            "purpose": self.purpose,
            "roster": self.roster,
            "update": self.update,
            "episodes": TRAIN_EPISODES_PER_ROSTER,
            "pairs": TRAIN_PAIRS_PER_ROSTER,
            "public_roles": list(PUBLIC_ROLES),
            "origins": len(self.selections),
            "one_origin_per_episode_role": True,
            "antithetic_slots": True,
            "arm_independent": True,
        }


def generate_training_origin_schedule(
    rng: AddressedRNG,
    *,
    seed_block: str,
    roster: int,
    update: int,
    purpose: str = "TRAIN",
) -> OriginSchedule:
    """Preselect the exact 16-pair, 32-episode RSCF origin schedule."""

    if not isinstance(rng, AddressedRNG):
        raise ContractError("origin schedule generation requires AddressedRNG")
    if purpose not in {"TRAIN", "TEST_ONLY"} or roster not in TRAIN_ROSTERS:
        raise ContractError("origin schedules require TRAIN/TEST_ONLY and roster 9 or 15")
    if type(update) is not int or not (1 <= update <= 512 if purpose == "TRAIN" else 0 <= update <= 512):
        raise ContractError("origin schedule update is outside its purpose domain")
    multiplicity = roster // len(PUBLIC_ROLES)
    selections: list[OriginSelection] = []
    for pair in range(TRAIN_PAIRS_PER_ROSTER):
        for role_index, role_name in enumerate(PUBLIC_ROLES):
            base_address, _ = training_origin_addresses(
                seed_block=seed_block, purpose=purpose, roster=roster,
                update=update, pair=pair, side=0, public_role=role_index,
            )
            base_slot = rng.integer(base_address, HORIZON)
            for side in (0, 1):
                episode = 2 * pair + side
                _, local_address = training_origin_addresses(
                    seed_block=seed_block, purpose=purpose, roster=roster,
                    update=update, pair=pair, side=side, public_role=role_index,
                )
                local_index = rng.integer(local_address, multiplicity)
                selections.append(OriginSelection(
                    pair=pair,
                    side=side,
                    episode=episode,
                    public_role=role_name,
                    public_role_index=role_index,
                    base_slot=base_slot,
                    selected_slot=base_slot if side == 0 else HORIZON - 1 - base_slot,
                    role_local_index=local_index,
                    simulator_index=role_index * multiplicity + local_index,
                ))
    return OriginSchedule(
        schema=ORIGIN_SCHEDULE_SCHEMA,
        seed_block=seed_block,
        purpose=purpose,
        roster=roster,
        update=update,
        selections=tuple(selections),
    )


def inverse_cdf_action(probabilities: Sequence[float], uniform: float) -> int:
    """Map one addressed action uniform through a categorical inverse CDF."""

    values = np.asarray(probabilities, dtype=np.float64)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ContractError("inverse-CDF probabilities must be a finite nonempty vector")
    if np.any(values < 0.0) or not np.isclose(
        values.sum(dtype=np.float64), 1.0,
        rtol=0.0, atol=FP32_PROBABILITY_TOLERANCE,
    ):
        raise ContractError("inverse-CDF probabilities must be nonnegative and sum to one")
    if isinstance(uniform, bool) or not isinstance(uniform, (int, float, np.floating)):
        raise ContractError("inverse-CDF uniform must be numeric")
    uniform_value = float(uniform)
    if not 0.0 <= uniform_value < 1.0:
        raise ContractError("inverse-CDF uniform must lie in [0,1)")
    return min(int(np.searchsorted(np.cumsum(values), uniform_value, side="right")), values.size - 1)


def complete_test_only_witness(roster: int = 6, episode: int = 0) -> EpisodeTape:
    """Return a complete deterministic TEST_ONLY tape without a production root."""

    # This literal is a test capability, not one of the later 24 production roots.
    rng = AddressedRNG(b"T" * 32)
    return generate_episode_tape(
        rng,
        seed_block="FRRIE-TEST-ONLY-COMPLETE-TAPE",
        purpose="TEST_ONLY",
        roster=roster,
        update=0,
        episode=episode,
    )
