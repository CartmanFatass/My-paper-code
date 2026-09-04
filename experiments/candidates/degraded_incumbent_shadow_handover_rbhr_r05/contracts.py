from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import math


TEST_NAMESPACE = "TEST/DISH-RBHR-R05/GATE-AB/V1"
HOST_ID = "RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3"
ABI_VERSION = 1
TICKS = 1200


class ContractError(ValueError):
    pass


class Arm(IntEnum):
    STRUCTURED = 0
    FLEX_ZERO = 1
    NEVER = 2
    FORK_REAL = 3
    FORK_SHAM = 4


@dataclass(frozen=True)
class GateAFixture:
    """Deterministic TEST-only host fixture.

    `fixture_key` is not a science master or coordinate.  It is a fixed
    conformance constant used only under :data:`TEST_NAMESPACE`.
    """

    namespace: str
    fixture_key: int
    arm: Arm
    package: int
    reflection: int
    initial_owner: int
    k_initial: int
    k_new: int
    switch_tick: int
    tau_d_tick: int
    phase: int
    route_speed: int
    turn_magnitude_deg: int
    turn_sign: int
    initial_ux: int
    initial_uy: int

    def __post_init__(self) -> None:
        if self.namespace != TEST_NAMESPACE:
            raise ContractError("Gate A accepts only the exact TEST namespace")
        if not 0 <= self.fixture_key <= 0xFFFFFFFFFFFFFFFF:
            raise ContractError("fixture_key is outside uint64")
        if not isinstance(self.arm, Arm):
            raise ContractError("arm must be an Arm")
        if self.package not in (0, 1):
            raise ContractError("package must be visual-mask=0 or relay-mask=1")
        if self.reflection not in (-1, 1):
            raise ContractError("reflection must be -1 or +1")
        if self.initial_owner not in (0, 1):
            raise ContractError("initial_owner must be 0 or 1")
        if self.k_initial not in (4, 8, 12) or self.k_new not in (4, 8, 12):
            raise ContractError("k values must be in {4,8,12}")
        if not 0 <= self.switch_tick < TICKS:
            raise ContractError("switch_tick is outside the episode")
        if not 0 <= self.tau_d_tick < TICKS:
            raise ContractError("tau_d_tick is outside the episode")
        if not 0 <= self.phase < self.k_initial:
            raise ContractError("phase is outside the initial renewal period")
        if self.route_speed not in (4, 6, 8):
            raise ContractError("route speed is not registered")
        if self.turn_magnitude_deg not in (25, 35, 45):
            raise ContractError("turn magnitude is not registered")
        if self.turn_sign not in (-1, 1):
            raise ContractError("turn sign must be -1 or +1")
        if self.initial_ux not in (-80, -40, 40, 80):
            raise ContractError("initial_ux is not registered")
        if self.initial_uy not in (-180, -120, 120, 180):
            raise ContractError("initial_uy is not registered")


@dataclass(frozen=True)
class GateAResult:
    service_ticks: int
    owner: int
    service_epoch: int
    next_payload_sequence: int
    handover_used: int
    noop_count: int
    transaction_shell_bytes: int
    invalid_commit: int
    token_gap: int
    dual_owner: int
    dual_payload: int
    buffer_clear: int
    separation_breach: int
    protocol_bytes: int
    terminal_tick: int
    final_separation: float
    total_energy: float
    state_digest: int

    def __post_init__(self) -> None:
        ints = (
            self.service_ticks,
            self.owner,
            self.service_epoch,
            self.next_payload_sequence,
            self.handover_used,
            self.noop_count,
            self.transaction_shell_bytes,
            self.invalid_commit,
            self.token_gap,
            self.dual_owner,
            self.dual_payload,
            self.buffer_clear,
            self.separation_breach,
            self.protocol_bytes,
            self.terminal_tick,
            self.state_digest,
        )
        if any(type(value) is not int for value in ints):
            raise ContractError("native result integer field has the wrong type")
        if self.owner not in (0, 1):
            raise ContractError("native result lost the one-owner invariant")
        if not math.isfinite(self.final_separation) or not math.isfinite(self.total_energy):
            raise ContractError("native result contains a nonfinite measurement")


def fixture_family(width: int, *, arm: Arm = Arm.STRUCTURED) -> tuple[GateAFixture, ...]:
    if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
        raise ContractError("width must be a positive integer")
    rows: list[GateAFixture] = []
    ks = ((4, 12), (12, 4), (8, 8))
    for index in range(width):
        k_initial, k_new = ks[index % len(ks)]
        rows.append(
            GateAFixture(
                namespace=TEST_NAMESPACE,
                fixture_key=0xD15A000000000000 + index,
                arm=arm,
                package=index % 2,
                reflection=1 if index % 2 == 0 else -1,
                initial_owner=(index // 2) % 2,
                k_initial=k_initial,
                k_new=k_new,
                switch_tick=(360, 480, 600, 720)[index % 4],
                tau_d_tick=(420, 540, 660)[index % 3],
                phase=index % k_initial,
                route_speed=(4, 6, 8)[index % 3],
                turn_magnitude_deg=(25, 35, 45)[(index // 3) % 3],
                turn_sign=1 if (index // 5) % 2 == 0 else -1,
                initial_ux=(-80, -40, 40, 80)[index % 4],
                initial_uy=(-180, -120, 120, 180)[(index // 4) % 4],
            )
        )
    return tuple(rows)
