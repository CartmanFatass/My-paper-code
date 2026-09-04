"""Frozen ctypes ABI for the package-owned RIDGEGATE-2Z environment.

The native library owns only environment state transitions.  Policy state,
probabilities, legal sampling, and recurrent inference remain external.  All
structures are packed PODs so a state snapshot is exactly ``sizeof(StateV1)``
bytes and contains no pointer, digest, or authentication field.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Final


# Semantic environment/actor seam V2.  The required exported symbol suffix
# ``_v1`` denotes only the revision of this packed C calling convention.
ABI_VERSION: Final = 2
NATIVE_STEP_ABI: Final = "FRRIE_NATIVE_STEP_ABI_V2_FP32"
NATIVE_ABI_DESCRIPTOR_SCHEMA: Final = "FRRIE_PACKAGE_NATIVE_ABI_DESCRIPTOR_V2"
STATE_VERSION: Final = 1
MAX_AGENTS: Final = 21
HORIZON: Final = 12
BASINS: Final = 2
EVENTS_PER_BASIN: Final = 3
ACTION_COUNT: Final = 6
OBSERVATION_DIM: Final = 22
FIFO_CAPACITY: Final = 4

ROLE_WEST_SURVEYOR: Final = 0
ROLE_EAST_SURVEYOR: Final = 1
ROLE_RIDGE_RELAY: Final = 2
ROLE_INACTIVE: Final = 255

ACTION_SCAN: Final = 0
ACTION_UPLINK: Final = 1
ACTION_LISTEN_WEST: Final = 2
ACTION_LISTEN_EAST: Final = 3
ACTION_FORWARD_BASE: Final = 4
ACTION_HOLD: Final = 5
ACTION_UNSET: Final = 255

LEGAL_MASKS: Final = (
    (1, 1, 0, 0, 0, 1),
    (1, 1, 0, 0, 0, 1),
    (0, 0, 1, 1, 1, 1),
)
REGISTERED_ROSTERS: Final = (6, 9, 15, 21)

ERR_OK: Final = 0
ERR_NULL: Final = 1
ERR_ABI_VERSION: Final = 2
ERR_BATCH_COUNT: Final = 3
ERR_ROSTER: Final = 4
ERR_EVENT_TIMES: Final = 5
ERR_UNIFORM_NONFINITE: Final = 6
ERR_UNIFORM_RANGE: Final = 7
ERR_STATE_VERSION: Final = 8
ERR_STATE_INVALID: Final = 9
ERR_ACTION_ILLEGAL: Final = 10
ERR_TERMINAL: Final = 11
ERR_SNAPSHOT_SIZE: Final = 12

ABI_SYMBOLS: Final = (
    "frrie_native_abi_v1",
    "frrie_native_state_size_v1",
    "frrie_reset_batch_v1",
    "frrie_observe_batch_v1",
    "frrie_step_batch_v1",
    "frrie_snapshot_batch_v1",
    "frrie_restore_batch_v1",
)


class _PackedPOD(ctypes.Structure):
    _pack_ = 1


class ReportV1(_PackedPOD):
    _fields_ = [
        ("occupied", ctypes.c_uint8),
        ("basin", ctypes.c_uint8),
        ("event_ordinal", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8),
        ("event_time", ctypes.c_int32),
    ]


class PendingUplinkV1(_PackedPOD):
    _fields_ = [
        ("report", ReportV1),
        ("sender", ctypes.c_int16),
        ("receiver", ctypes.c_int16),
        ("decoded", ctypes.c_uint8),
    ]


class PendingBaseV1(_PackedPOD):
    _fields_ = [
        ("report", ReportV1),
        ("sender", ctypes.c_int16),
        ("decoded", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8),
    ]


class MetricsV1(_PackedPOD):
    _fields_ = [
        ("dw", ctypes.c_uint32),
        ("de", ctypes.c_uint32),
        ("duplicate_arrivals", ctypes.c_uint32),
        ("expired_arrivals", ctypes.c_uint32),
        ("collision_loss", ctypes.c_uint32),
        ("empty_actions", ctypes.c_uint32),
        ("radio_actions", ctypes.c_uint32),
        ("waste_actions", ctypes.c_uint32),
        ("new_timely_deliveries", ctypes.c_uint32),
        ("waste", ctypes.c_float),
        ("terminal_audit", ctypes.c_float),
    ]


EventTimes = (ctypes.c_int32 * EVENTS_PER_BASIN) * BASINS
DetectionTape = (ctypes.c_float * MAX_AGENTS) * HORIZON
UplinkTape = ((ctypes.c_float * MAX_AGENTS) * MAX_AGENTS) * HORIZON
BaseTape = (ctypes.c_float * MAX_AGENTS) * HORIZON
FifoRow = ReportV1 * FIFO_CAPACITY
FifoTable = FifoRow * MAX_AGENTS
DeliveredMask = (ctypes.c_uint8 * EVENTS_PER_BASIN) * BASINS


class ResetInputV1(_PackedPOD):
    _fields_ = [
        ("abi_version", ctypes.c_uint32),
        ("state_version", ctypes.c_uint32),
        ("roster", ctypes.c_int32),
        ("reserved", ctypes.c_uint32),
        ("event_times", EventTimes),
        ("detection_uniforms", DetectionTape),
        ("uplink_uniforms", UplinkTape),
        ("base_uniforms", BaseTape),
    ]


class NativeStateV1(_PackedPOD):
    _fields_ = [
        ("abi_version", ctypes.c_uint32),
        ("state_version", ctypes.c_uint32),
        ("roster", ctypes.c_int32),
        ("slot", ctypes.c_int32),
        ("terminal", ctypes.c_uint8),
        ("predecision_prepared", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 2),
        ("roles", ctypes.c_uint8 * MAX_AGENTS),
        ("event_times", EventTimes),
        ("detection_uniforms", DetectionTape),
        ("uplink_uniforms", UplinkTape),
        ("base_uniforms", BaseTape),
        ("fifos", FifoTable),
        ("fifo_sizes", ctypes.c_uint8 * MAX_AGENTS),
        ("pending_uplinks", PendingUplinkV1 * MAX_AGENTS),
        ("pending_uplink_count", ctypes.c_uint8),
        ("pending_base", PendingBaseV1),
        ("pending_base_present", ctypes.c_uint8),
        ("delivered", DeliveredMask),
        ("previous_action", ctypes.c_uint8 * MAX_AGENTS),
        ("previous_success", ctypes.c_uint8 * MAX_AGENTS),
        ("metrics", MetricsV1),
    ]


class StepInputV1(_PackedPOD):
    _fields_ = [
        ("abi_version", ctypes.c_uint32),
        ("actions", ctypes.c_uint8 * MAX_AGENTS),
        ("reserved", ctypes.c_uint8 * 3),
    ]


ObservationRows = (ctypes.c_float * OBSERVATION_DIM) * MAX_AGENTS
MaskRows = (ctypes.c_uint8 * ACTION_COUNT) * MAX_AGENTS


class ObservationOutputV1(_PackedPOD):
    _fields_ = [
        ("abi_version", ctypes.c_uint32),
        ("state_version", ctypes.c_uint32),
        ("roster", ctypes.c_int32),
        ("slot", ctypes.c_int32),
        ("terminal", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("roles", ctypes.c_uint8 * MAX_AGENTS),
        ("legal_masks", MaskRows),
        ("observations", ObservationRows),
    ]


class StepOutputV1(_PackedPOD):
    _fields_ = [
        ("abi_version", ctypes.c_uint32),
        ("state_version", ctypes.c_uint32),
        ("slot_before", ctypes.c_int32),
        ("slot_after", ctypes.c_int32),
        ("terminal", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("previous_success", ctypes.c_uint8 * MAX_AGENTS),
        ("metrics", MetricsV1),
    ]


STATE_SIZE: Final = ctypes.sizeof(NativeStateV1)


@dataclass(frozen=True, slots=True)
class BoundNativeABI:
    """Configured function references and the externally frozen native width."""

    library: ctypes.CDLL
    native_width: int


def bind_native_abi(library: ctypes.CDLL, *, native_width: int) -> BoundNativeABI:
    """Validate/configure the exact ABI without constructing policy behavior."""

    if type(library) is not ctypes.CDLL:
        raise TypeError("library must be a directly loaded ctypes.CDLL")
    if isinstance(native_width, bool) or not isinstance(native_width, int) or native_width <= 0:
        raise ValueError("native_width must be a positive literal integer")
    missing = [name for name in ABI_SYMBOLS if not hasattr(library, name)]
    if missing:
        raise AttributeError(f"native library is missing ABI symbols: {missing!r}")

    library.frrie_native_abi_v1.argtypes = []
    library.frrie_native_abi_v1.restype = ctypes.c_uint32
    library.frrie_native_state_size_v1.argtypes = []
    library.frrie_native_state_size_v1.restype = ctypes.c_size_t

    library.frrie_reset_batch_v1.argtypes = [
        ctypes.POINTER(NativeStateV1), ctypes.POINTER(ResetInputV1),
        ctypes.c_uint32, ctypes.c_uint32,
    ]
    library.frrie_observe_batch_v1.argtypes = [
        ctypes.POINTER(NativeStateV1), ctypes.POINTER(ObservationOutputV1),
        ctypes.c_uint32, ctypes.c_uint32,
    ]
    library.frrie_step_batch_v1.argtypes = [
        ctypes.POINTER(NativeStateV1), ctypes.POINTER(StepInputV1),
        ctypes.POINTER(StepOutputV1), ctypes.c_uint32, ctypes.c_uint32,
    ]
    library.frrie_snapshot_batch_v1.argtypes = [
        ctypes.POINTER(NativeStateV1), ctypes.c_void_p, ctypes.c_size_t,
        ctypes.c_uint32, ctypes.c_uint32,
    ]
    library.frrie_restore_batch_v1.argtypes = [
        ctypes.POINTER(NativeStateV1), ctypes.c_void_p, ctypes.c_size_t,
        ctypes.c_uint32, ctypes.c_uint32,
    ]
    for name in ABI_SYMBOLS[2:]:
        getattr(library, name).restype = ctypes.c_int32

    if library.frrie_native_abi_v1() != ABI_VERSION:
        raise RuntimeError("native ABI version mismatch")
    if library.frrie_native_state_size_v1() != STATE_SIZE:
        raise RuntimeError("native/Python state POD size mismatch")
    return BoundNativeABI(library=library, native_width=native_width)


__all__ = [
    "ABI_VERSION", "NATIVE_STEP_ABI", "NATIVE_ABI_DESCRIPTOR_SCHEMA",
    "STATE_VERSION", "MAX_AGENTS", "HORIZON", "BASINS",
    "EVENTS_PER_BASIN", "ACTION_COUNT", "OBSERVATION_DIM", "FIFO_CAPACITY",
    "REGISTERED_ROSTERS", "LEGAL_MASKS", "ABI_SYMBOLS", "STATE_SIZE",
    "ERR_OK", "ERR_NULL", "ERR_ABI_VERSION", "ERR_BATCH_COUNT", "ERR_ROSTER",
    "ERR_EVENT_TIMES", "ERR_UNIFORM_NONFINITE", "ERR_UNIFORM_RANGE",
    "ERR_STATE_VERSION", "ERR_STATE_INVALID", "ERR_ACTION_ILLEGAL",
    "ERR_TERMINAL", "ERR_SNAPSHOT_SIZE", "ReportV1", "PendingUplinkV1",
    "PendingBaseV1", "MetricsV1", "ResetInputV1", "NativeStateV1",
    "StepInputV1", "ObservationOutputV1", "StepOutputV1", "BoundNativeABI",
    "bind_native_abi",
]
