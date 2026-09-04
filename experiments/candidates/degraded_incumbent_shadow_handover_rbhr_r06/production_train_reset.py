"""Master-addressed 32-lane TRAIN reset rows for frozen DISH RBHR r06.

The production functions are pure: callers must supply the already-authorized
32-byte r06 master, block, arm, lane and episode wave.  Importing this module
does not create a master, identity, coordinate, tape, model or activity.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from itertools import product
from typing import Final, Iterable

from .production_contract import ARMS, BLOCKS, RNG_PREFIX, TRAIN_LANES, TRAIN_SCHEDULES
from .production_population import address


REGIMES: Final = ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
TAU_D: Final = (42, 54, 66)
TAU_K: Final = (36, 48, 60, 72)
K_PAIR: Final = {
    "K4": (4, 4), "K12": (12, 12),
    "K4_TO_K12": (4, 12), "K12_TO_K4": (12, 4),
}
X_OFFSETS: Final = (-80, -40, 40, 80)
Y_OFFSETS: Final = (-180, -120, 120, 180)
TURN_MAGNITUDES: Final = (25, 35, 45)
TURN_SIGNS: Final = (-1, 1)
ROUTE_SPEEDS: Final = (4, 6, 8)


class TrainResetError(RuntimeError):
    pass


def _master(value: bytes) -> bytes:
    raw = bytes(value)
    if len(raw) != 32:
        raise TrainResetError("r06 master must be exactly 256 bits")
    return raw


def _uniform(master: bytes, rng_address: str) -> float:
    if not rng_address.startswith(RNG_PREFIX + "/"):
        raise TrainResetError("TRAIN draw escaped the r06 namespace")
    digest = hashlib.sha256(_master(master) + b"\0" + rng_address.encode("ascii")).digest()
    return ((int.from_bytes(digest[:8], "big") >> 11) + 0.5) / 2**53


def _choice(master: bytes, rng_address: str, values: tuple[int, ...]) -> int:
    return values[min(int(_uniform(master, rng_address) * len(values)), len(values) - 1)]


def _training_address(
    key: "TrainResetKey", *, purpose: str, field: str, draw_index: int,
    cycle: int | None = None, arm_substream: str = "COMMON",
) -> str:
    return address(
        purpose=purpose, block=key.block, split="TRAIN", regime=key.regime,
        schedule=key.schedule, evaluation_slot=None, lane=key.lane,
        cycle=cycle, arm_substream=arm_substream,
        degradation_flag="DEGRADED_ONLY", fork_branch="NONE",
        episode=key.episode_wave, field=field, draw_index=draw_index,
    )


@dataclass(frozen=True, order=True)
class TrainResetKey:
    block: int
    arm: str
    lane: int
    episode_wave: int

    def validate(self) -> None:
        if not 0 <= self.block < BLOCKS or self.arm not in ARMS:
            raise TrainResetError("TRAIN block or arm differs")
        if not 0 <= self.lane < TRAIN_LANES or self.episode_wave < 0:
            raise TrainResetError("TRAIN lane or episode wave differs")

    @property
    def regime(self) -> str:
        self.validate()
        return REGIMES[self.lane // 16]

    @property
    def schedule(self) -> str:
        self.validate()
        return TRAIN_SCHEDULES[(self.lane % 16) // 4]

    @property
    def lane_within_cell(self) -> int:
        return self.lane % 4

    @property
    def ordinal(self) -> int:
        return 4 * self.episode_wave + self.lane_within_cell

    def canonical_key(self) -> str:
        return "/".join((
            RNG_PREFIX, "TRAIN_RESET", str(self.block), self.arm, self.regime,
            self.schedule, str(self.lane), str(self.episode_wave),
        ))


def _omega(schedule: str) -> tuple[tuple[int, int, int], ...]:
    k_initial, k_new = K_PAIR[schedule]
    if k_initial == k_new:
        return tuple((tau_d, 1199, phase) for tau_d, phase in product(TAU_D, range(k_initial)))
    return tuple((tau_d, tau_k, phase) for tau_d, tau_k, phase in product(TAU_D, TAU_K, range(k_initial)))


def _omega_entry(master: bytes, key: TrainResetKey) -> tuple[int, int, int, int]:
    values = _omega(key.schedule)
    cycle = key.ordinal // len(values)
    scores: list[tuple[float, int]] = []
    for item_ordinal in range(len(values)):
        score_address = _training_address(
            key, purpose="K_SCHEDULE", field="OMEGA_PERM_SCORE",
            draw_index=item_ordinal, cycle=cycle,
        )
        scores.append((_uniform(master, score_address), item_ordinal))
    permutation = tuple(item for _, item in sorted(scores))
    item = permutation[key.ordinal % len(values)]
    return (*values[item], cycle)


def arm_substream(master: bytes, block: int, arm: str) -> str:
    if not 0 <= block < BLOCKS or arm not in ARMS:
        raise TrainResetError("arm assignment coordinate differs")
    probe = TrainResetKey(block, arm, 0, 0)
    scored: list[tuple[float, int]] = []
    for slot in range(len(ARMS)):
        value = address(
            purpose="ARM_PERM", block=block, split="TRAIN", regime="NONE",
            schedule="NONE", evaluation_slot=None, lane=None, cycle=None,
            arm_substream="COMMON", degradation_flag="DEGRADED_ONLY",
            fork_branch="NONE", episode=None, field="ARM_PERM_SCORE",
            draw_index=slot,
        )
        scored.append((_uniform(master, value), slot))
    ordered_slots = tuple(slot for _, slot in sorted(scored))
    return f"SLOT{ordered_slots[ARMS.index(probe.arm)]}"


def build_train_reset_row(master: bytes, key: TrainResetKey) -> dict[str, object]:
    """Return one exact native reset row without opening or stepping a host."""

    raw_master = _master(master); key.validate()
    tau_d, switch_tick, phase, cycle = _omega_entry(raw_master, key)
    bits = key.ordinal % 8
    draws = {
        "route_speed": _choice(raw_master, _training_address(key, purpose="TRAIN_TAPE", field="ROUTE_SPEED", draw_index=0), ROUTE_SPEEDS),
        "turn_magnitude_deg": _choice(raw_master, _training_address(key, purpose="TRAIN_TAPE", field="TURN_MAGNITUDE", draw_index=0), TURN_MAGNITUDES),
        "turn_sign": _choice(raw_master, _training_address(key, purpose="TRAIN_TAPE", field="TURN_SIGN", draw_index=0), TURN_SIGNS),
        "initial_ux": _choice(raw_master, _training_address(key, purpose="TRAIN_TAPE", field="INITIAL_UX", draw_index=0), X_OFFSETS),
        "initial_uy": _choice(raw_master, _training_address(key, purpose="TRAIN_TAPE", field="INITIAL_UY", draw_index=0), Y_OFFSETS),
    }
    k_initial, k_new = K_PAIR[key.schedule]
    fixture_key = int.from_bytes(hashlib.sha256(raw_master + b"\0" + key.canonical_key().encode("ascii")).digest()[:8], "big")
    return {
        "fixture_key": fixture_key, "master": raw_master.hex(), "test_mode": 0,
        "package": REGIMES.index(key.regime), "reflection": 1 if (bits & 1) == 0 else -1,
        "initial_owner": (bits >> 1) & 1, "qa_owner": (bits >> 2) & 1,
        "k_initial": k_initial, "k_new": k_new,
        "switch_tick": 10 * switch_tick if switch_tick != 1199 else 1199,
        "tau_d_tick": 10 * tau_d, "phase": phase,
        **draws, "block": key.block, "split": 0,
        "schedule": {"K4": 0, "K12": 2, "K4_TO_K12": 3, "K12_TO_K4": 4}[key.schedule],
        "evaluation_slot": -1, "lane": key.lane, "cycle": -1,
        "arm_substream": 0, "degradation_flag": 1, "mask_enabled": 1, "fork_branch": -1,
        "episode": key.episode_wave,
    }


def build_train_reset_wave(master: bytes, *, block: int, arm: str, episode_wave: int) -> tuple[dict[str, object], ...]:
    rows = tuple(build_train_reset_row(master, TrainResetKey(block, arm, lane, episode_wave)) for lane in range(TRAIN_LANES))
    if len(rows) != 32 or {int(row["lane"]) for row in rows} != set(range(32)):
        raise TrainResetError("TRAIN reset wave is not exactly 32 lanes")
    return rows


def flow_local_reset_fixture_manifest() -> dict[str, object]:
    """Value-blind E1 fixture: inventory and deterministic row identities only."""

    fixture_master = hashlib.sha256(b"TEST/DISH-RBHR-R06/E1/TRAIN-RESET/V1").digest()
    rows = build_train_reset_wave(fixture_master, block=0, arm="STRUCTURED", episode_wave=0)
    encoded = "\n".join(
        f"{row['lane']}|{row['package']}|{row['schedule']}|{row['tau_d_tick']}|{row['phase']}|{row['arm_substream']}"
        for row in rows
    ).encode("ascii")
    return {
        "schema": "DISH_RBHR_R06_E1_TRAIN_RESET_FLOW_LOCAL_FIXTURE_V1",
        "test_namespace": True, "scientific_master": False, "identity": False,
        "coordinate": False, "tape": False, "activity": False,
        "lanes": len(rows), "lane_ids_exact": True,
        "regime_schedule_cells": len({(row["package"], row["schedule"]) for row in rows}),
        "four_lanes_per_cell": all(
            sum((row["package"], row["schedule"]) == cell for row in rows) == 4
            for cell in product(range(2), (0, 2, 3, 4))
        ),
        "fixture_manifest_sha256": hashlib.sha256(encoded).hexdigest(),
        "question_relevant_output": False,
    }


__all__ = [
    "TrainResetError", "TrainResetKey", "arm_substream", "build_train_reset_row",
    "build_train_reset_wave", "flow_local_reset_fixture_manifest",
]
