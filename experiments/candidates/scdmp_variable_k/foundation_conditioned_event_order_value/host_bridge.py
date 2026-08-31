"""Narrow allowlisted bridge to the registered native pallet/gantry host."""

from __future__ import annotations

from dataclasses import dataclass
import struct

from ..target_bound_competent_controller_order_value.config import (
    FORMATION_ROTATE,
    HOOK_HANDOFF,
)
from ..target_bound_competent_controller_order_value.host_types import (
    HostOutput,
    RenewalLane,
    ResetLane,
)
from ..target_bound_competent_controller_order_value.native_backend import (
    NativeBatch,
    test_only_primitive,
    test_only_setup_composition,
)
from .contracts import A_HR_INDEX, A_RH_INDEX, COMMON_INDEX, fixed_claim_state


class HostBridgeError(RuntimeError):
    pass


def fixed_resets() -> tuple[ResetLane, ResetLane]:
    state = fixed_claim_state()
    return (
        ResetLane(
            middle_events=(HOOK_HANDOFF, FORMATION_ROTATE),
            k_initial=13,
            initial_v=state.v,
            initial_y=state.y,
            initial_phi=state.phi,
        ),
        ResetLane(
            middle_events=(FORMATION_ROTATE, HOOK_HANDOFF),
            k_initial=13,
            initial_v=state.v,
            initial_y=state.y,
            initial_phi=state.phi,
        ),
    )


def verify_public_alias() -> tuple[bytes, bytes]:
    """Materialize both native resets together and require byte equality."""

    setup = test_only_setup_composition(
        ((HOOK_HANDOFF, FORMATION_ROTATE), (FORMATION_ROTATE, HOOK_HANDOFF))
    )
    if setup != (((4, 2, 1, 3), 1), ((1, 4, 2, 3), 0)):
        raise HostBridgeError("native H/R setup composition differs")
    with NativeBatch(fixed_resets()) as batch:
        observed = tuple(struct.pack("<18d", *row.observation) for row in batch.initial)
    if observed[0] != observed[1]:
        raise HostBridgeError("native first-renewal public observations are not byte-identical")
    return observed


@dataclass(frozen=True, slots=True)
class HeadroomWitness:
    matched_load: float
    mismatched_load: float
    common_maximum_load: float


@dataclass(frozen=True, slots=True)
class HeadroomConformance:
    analytic_witness: HeadroomWitness
    native_matched_exposure_zero: bool
    native_mismatched_exposure: float
    native_common_exposure_zero: bool


def _maximum_load(q: int, action_index: int) -> float:
    from .contracts import ACTIONS

    forward, share = ACTIONS[action_index]
    b = (1, -1, 0, 0) if q == 1 else (0, 0, 1, -1)
    loads = tuple(
        0.38 + 0.12 * forward + 0.16 * forward * max(item, 0) - 0.10 * correction
        for item, correction in zip(b, share)
    )
    return max(loads)


def headroom_conformance() -> HeadroomConformance:
    """Separate the analytic load fixture from native threshold observation."""

    setup = test_only_setup_composition(
        ((HOOK_HANDOFF, FORMATION_ROTATE), (FORMATION_ROTATE, HOOK_HANDOFF))
    )
    if setup != (((4, 2, 1, 3), 1), ((1, 4, 2, 3), 0)):
        raise HostBridgeError("native graph composition differs")
    matched = (_maximum_load(1, A_HR_INDEX), _maximum_load(0, A_RH_INDEX))
    mismatched = (_maximum_load(1, A_RH_INDEX), _maximum_load(0, A_HR_INDEX))
    common = (_maximum_load(1, COMMON_INDEX), _maximum_load(0, COMMON_INDEX))
    witness = HeadroomWitness(max(matched), max(mismatched), max(common))
    if witness != HeadroomWitness(0.84, 0.94, 0.66):
        raise HostBridgeError("registered local loaded-cable witness differs")
    # The native one-tick exposure transition independently confirms that only
    # the .94 mismatched witness lies above the .88 exposure threshold.
    state = fixed_claim_state()
    observed_exposure = []
    for q, action in (
        (1, A_HR_INDEX), (0, A_RH_INDEX),
        (1, A_RH_INDEX), (0, A_HR_INDEX),
        (1, COMMON_INDEX), (0, COMMON_INDEX),
    ):
        output = test_only_primitive(
            q=q, tick=0, x=state.x, v=state.v, y=state.y, w=state.w,
            phi=state.phi, omega=state.omega, z=state.z, formation=state.formation,
            prior_a=state.prior_a, prior_r=state.prior_load_share, action=action,
            eta_v=0.003, eta_y=0.002, eta_omega=0.004,
        )
        observed_exposure.append(max(output.observation[6:10]) * 0.25)
    matched_zero = all(value == 0.0 for value in observed_exposure[:2])
    common_zero = all(value == 0.0 for value in observed_exposure[4:])
    if not matched_zero or not common_zero:
        raise HostBridgeError("native matched/common local exposure witness differs")
    if any(abs(value - 0.06) > 1e-15 for value in observed_exposure[2:4]):
        raise HostBridgeError("native mismatched local exposure witness differs")
    return HeadroomConformance(
        analytic_witness=witness,
        native_matched_exposure_zero=True,
        native_mismatched_exposure=sum(observed_exposure[2:4]) / 2.0,
        native_common_exposure_zero=True,
    )


__all__ = [
    "HeadroomConformance", "HeadroomWitness", "HostBridgeError", "HostOutput", "NativeBatch",
    "RenewalLane", "ResetLane", "fixed_resets", "headroom_conformance", "verify_public_alias",
]
