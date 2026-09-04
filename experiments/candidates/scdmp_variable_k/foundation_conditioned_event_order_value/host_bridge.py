"""Narrow allowlisted bridge to the registered native pallet/gantry host."""

from __future__ import annotations

from dataclasses import dataclass
import math
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
from .contracts import A_HR_INDEX, A_RH_INDEX, COMMON_INDEX, PublicClaimState, fixed_claim_state


class HostBridgeError(RuntimeError):
    pass


def validate_native_transition(
    previous: tuple[HostOutput, ...],
    following: tuple[HostOutput, ...],
    *,
    width: int,
    context: str,
) -> None:
    """Validate fixed-width native advancement and absorbed-lane immutability."""

    if len(previous) != width or len(following) != width:
        raise HostBridgeError(f"{context} native transition width differs")
    for before, after in zip(previous, following):
        failures = any(bool(getattr(after, label)) for label in (
            "cable_overload", "gantry_contact", "attitude_loss", "formation_loss"
        ))
        if after.terminal:
            validate_terminal_endpoints((after,), context=context)
        elif (
            not after.active
            or after.safe_dock
            or after.timeout
            or failures
            or after.dock_tick is not None
        ):
            raise HostBridgeError(f"{context} nonterminal native endpoint is incoherent")
        if before.terminal or not before.active:
            if after != before:
                raise HostBridgeError(f"{context} absorbed native lane mutated or reactivated")
            continue
        delta = after.tick - before.tick
        reward_trace = tuple(after.last_hold_rewards)
        if (
            not 1 <= delta <= 13
            or after.advanced is not True
            or after.ticks_advanced != delta
            or after.hold_k != 13
            or after.next_k != 13
            or after.last_hold_reward_count != delta
            or len(reward_trace) != 13
            or any(not math.isfinite(value) for value in reward_trace)
            or any(value != 0.0 for value in reward_trace[delta:])
            or (after.active and (after.terminal or delta != 13))
            or (after.terminal and after.active)
        ):
            raise HostBridgeError(f"{context} active native tick/terminal frontier differs")


def validate_native_reset_outputs(
    resets: tuple[ResetLane, ...],
    outputs: tuple[HostOutput, ...],
    *,
    width: int,
    context: str,
) -> None:
    """Require exact public reset materialization and zero endpoint/counter state."""

    if len(resets) != width or len(outputs) != width:
        raise HostBridgeError(f"{context} native reset width differs")
    for reset, output in zip(resets, outputs):
        expected = PublicClaimState(
            v=reset.initial_v, y=reset.initial_y, phi=reset.initial_phi, k=13
        ).observation_bytes()
        try:
            observed = struct.pack("<18d", *output.observation)
        except (TypeError, struct.error) as error:
            raise HostBridgeError(f"{context} native reset observation differs") from error
        if (
            reset.k_initial != 13
            or output.advanced is not False
            or not output.active
            or output.terminal
            or output.tick != 0
            or output.ticks_advanced != 0
            or output.hold_k != 0
            or output.next_k != 13
            or output.cumulative_reward != 0.0
            or output.cumulative_energy != 0.0
            or output.energy_ticks != 0
            or output.safe_dock
            or output.timeout
            or any(bool(getattr(output, label)) for label in (
                "cable_overload", "gantry_contact", "attitude_loss", "formation_loss"
            ))
            or output.dock_tick is not None
            or output.last_hold_reward_count != 0
            or tuple(output.last_hold_rewards) != (0.0,) * 13
            or observed != expected
        ):
            raise HostBridgeError(f"{context} native reset state/counters differ")


def validate_terminal_endpoints(outputs: tuple[HostOutput, ...], *, context: str) -> None:
    """Require exactly one coherent native terminal cause class per lane."""

    labels = ("cable_overload", "gantry_contact", "attitude_loss", "formation_loss")
    for output in outputs:
        failures = tuple(label for label in labels if bool(getattr(output, label)))
        safe = bool(output.safe_dock)
        timeout = bool(output.timeout)
        if output.active or not output.terminal or sum((safe, timeout, bool(failures))) != 1:
            raise HostBridgeError(f"{context} terminal cause classes are incoherent")
        if safe:
            if (
                isinstance(output.dock_tick, bool)
                or not isinstance(output.dock_tick, int)
                or output.dock_tick != output.tick
                or not 1 <= output.dock_tick <= 364
                or timeout
                or failures
            ):
                raise HostBridgeError(f"{context} safe terminal endpoint is incoherent")
        elif timeout:
            if output.tick != 364 or output.dock_tick is not None or failures:
                raise HostBridgeError(f"{context} timeout terminal endpoint is incoherent")
        elif output.dock_tick is not None or timeout or not failures:
            raise HostBridgeError(f"{context} failure terminal endpoint is incoherent")


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
    "RenewalLane", "ResetLane", "fixed_resets", "headroom_conformance",
    "validate_native_reset_outputs", "validate_native_transition", "validate_terminal_endpoints",
    "verify_public_alias",
]
