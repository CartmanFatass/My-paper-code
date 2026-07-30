"""Frozen source and evidence core for UAV source-identifiability G0.

G0 is deliberately not a learning experiment.  It instantiates one paired
Scenario-7/S1 source, three deterministic controls, exact episode metrics and
the registered first-match analysis.  No model, optimizer, checkpoint or
formal-execution authority is defined here.

Physical slot numbers are storage coordinates only.  Target ownership and
controller decisions use opaque lifecycle handles plus anonymous physical
content; a slot number is never a decision or tie-breaking feature.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import inspect
import itertools
import json
import math
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np
from scipy.stats import beta

from config_1 import Config
from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv


ALGORITHM_ID = "UAV_SOURCE_IDENTIFIABILITY_G0"
SOURCE_ID = "UAV_SOURCE_IDENTIFIABILITY_G0_P0"
SCHEMA_VERSION = 1
DESIGN_ROUND = "20260729_uav_source_identifiability_g0_executable_contract_clarification"
DESIGN_PACKAGE_STAGE_COMMIT = "22efb10e338c2264a6d23a6962486e0fd3c4adc8"
EVIDENCE_SOURCE_COMMIT = "45385faa81197bdb90c14f849eee17b999ca2f57"
ORACLE_SAFETY_CLARIFICATION_ROUND = (
    "20260730_uav_g0_oracle_safety_information_contract_clarification"
)
ORACLE_SAFETY_PACKAGE_STAGE_COMMIT = (
    "a6c4e5be7119280006efc8455437671b8cf0c75a"
)
ORACLE_SAFETY_ARCHIVE_COMMIT = "14f1303d2aabc5282c9c2e4e7764c13e58c1b515"
ORACLE_SAFETY_DISPOSITION = (
    "G0_ORACLE_SAFETY_INFORMATION_DISPOSITION=REGISTERED_LEDGER_ALLOWED"
)
REPLAY_CLARIFICATION_ROUND = (
    "20260730_uav_g0_behavioral_replay_contract_clarification"
)
REPLAY_PACKAGE_STAGE_COMMIT = "1ba1f95bbf551ad68e5c814b0203e720534b82a6"
REPLAY_ARCHIVE_COMMIT = "9f08c12cdfe433bb691a640ef8a9ce2f5792608e"
REPLAY_DISPOSITION = (
    "G0_REPLAY_CONTRACT_DISPOSITION=POST_RETURN_READY_REPLAY_RULE"
)
RETURN_READY_STEP_CLARIFICATION_ROUND = (
    "20260730_uav_g0_return_ready_step_contract_clarification"
)
RETURN_READY_STEP_PACKAGE_STAGE_COMMIT = (
    "612210d2fabb945361d079a9fad1102d00a3255d"
)
RETURN_READY_STEP_ARCHIVE_COMMIT = "7e1876c1f552aac0b10af24e15bf2e4cc5c0b03f"
RETURN_READY_STEP_DISPOSITION = (
    "G0_RETURN_READY_STEP_DISPOSITION=KEEP_CAUSAL_R_273"
)
ACCEPTED_G1_SOURCE_COMMIT = "2f8e47c16f0563ed1144e370fff787c22508a14d"
ACCEPTED_G1_TRACKER_SOURCE_SHA256 = (
    "50dd4f8728739e5ea643791339d0ce7072c40d6517527040f0b63f485c70558d"
)
ACCEPTED_G1_SHARED_ACTION_METHOD_SHA256 = {
    "prepare_energy_actions": "f59c8e9071d205fe71035b74af2f970b90f9fa6a720aa5669b7f11c73fb37307",
    "movement_velocity": "798dbeeee09c39740af169bb08da16c08072c5f45c22ea47e6f2e357a286c3c2",
    "base_action": "c4dea617374fbc3599a701ec8e8810a7c1cc1e7ba70cf81e2b48b95767e84a9b",
    "scenario7_backhaul_guard": "9d32b03489d9b08cf2df2928b7f2fe9823b855621b538f9221110f98c3a4d84b",
    "base_backhaul_guard": "e3edac5d4ad6d1839204d6ea042e2768ce3df90085c8535aa822cc3bb9c14df8",
}

PHYSICAL_HORIZON = 500
PHYSICAL_UAVS = 8
GROUND_USERS = 30
GROUND_BASE_STATIONS = 1
HOTSPOT_COUNT = 3
USERS_PER_HOTSPOT = 10
ACTION_DIM = 4
FIXED_ALTITUDE_M = 50.0
USER_ALTITUDE_M = 1.5
QOS_RATE_THRESHOLD_MBPS = 1.0
SERVICE_TARGET = 0.90
CATASTROPHE_THRESHOLD = 0.60
CATASTROPHE_STREAK = 10
RECOVERY_WINDOW_EXTENSION = 59
EPISODE_IDS = tuple(range(128))
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 2_026_072_901
K_SEARCH = 2
K_SEARCH_CEILING = 16
MAP_WIDTH_M = 8000.0
MAP_HEIGHT_M = 8000.0

FORMAL_EXECUTION_AUTHORIZED = False
LEARNING_ENABLED = False
OPTIMIZER_ENABLED = False
CHECKPOINT_ENABLED = False

_ORACLE_SAFETY_ALLOWED_STEP_KEYS = frozenset(
    {
        "physical_step",
        "candidate_id",
        "current_uav_positions",
        "current_uav_velocities",
        "current_service_mask",
        "pre_action_context",
        "executed_service_mask",
        "common_transducer_evidence",
        "raw_candidate_action",
        "shared_channel_draw_coordinate",
        "shared_channel_draw_block",
        "connections",
        "routing_paths",
        "exact_link_capacity_values_read_by_the_real_guard",
        "real_guard_intervention_or_violation_output",
        "guarded_executed_action",
        "next_uav_positions",
        "next_uav_velocities",
    }
)
_PRE_ACTION_CONTEXT_KEYS = frozenset(
    {
        "physical_step",
        "lifecycle_owner_to_internal",
        "event_owner_handle",
        "event_owner_epoch",
        "selected_reserve_handle",
        "selected_reserve_original_target",
        "survivor_ownership",
        "survivor_controller_rng_owners",
        "non_controller_rng_states",
        "channel_tape_cursor",
    }
)
_LIFECYCLE_CONTEXT_ROW_KEYS = frozenset(
    {"handle", "epoch", "internal_row", "owner_target"}
)
_COMMON_TRANSDUCER_EVIDENCE_KEYS = frozenset(
    {
        "transducer_source_sha256",
        "row_order",
        "physical_positions",
        "target_positions",
        "active_mask",
        "raw_action",
        "max_speed",
        "max_vertical_speed",
        "time_step",
    }
)
_ORACLE_SAFETY_FORBIDDEN_TOKENS = (
    "delivered",
    "reward",
    "qos",
    "hotspot",
    "a_control",
    "b_access",
    "c_cat",
    "delta_",
    "j_event",
    "q_ordinary",
    "m_event",
)

INVALID_BRANCH = "INVALID_UAV_G0_REALIZATION"
INFEASIBLE_BRANCH = "INFEASIBLE_UAV_G0_SOURCE"
ORACLE_ONLY_BRANCH = "ORACLE_ONLY_UAV_G0_SOURCE"
NON_CAUSAL_BRANCH = "NON_CAUSAL_UAV_G0_SOURCE"
UNDERPOWERED_BRANCH = "UNDERPOWERED_UAV_G0_SOURCE"
IDENTIFIED_BRANCH = "IDENTIFIED_UAV_G0_SOURCE"
FIRST_MATCH_ORDER = (
    INVALID_BRANCH,
    INFEASIBLE_BRANCH,
    ORACLE_ONLY_BRANCH,
    NON_CAUSAL_BRANCH,
    UNDERPOWERED_BRANCH,
    IDENTIFIED_BRANCH,
)


class G0RealizationError(ValueError):
    """A fail-closed violation of the frozen source realization."""


class Cell(str, Enum):
    EVENT = "UNANNOUNCED_PRIMARY_TEMPORARY_LEAVE"
    NO_EVENT = "NO_EVENT"


class Control(str, Enum):
    ORACLE = "MECHANICALLY_QUALIFIED_ORACLE"
    SAME_INFORMATION = "SAME_INFORMATION_CONSTRUCTIVE"
    NO_REALLOCATION = "NO_REALLOCATION"


class TargetKind(str, Enum):
    PRIMARY = "primary"
    STAGE = "stage"


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    OPEN = "OPEN"


_NAMESPACE_CODES = {
    "phi": 0x470001,
    "users": 0x470002,
    "perturbations": 0x470003,
    "permutation": 0x470004,
    "channels": 0x470005,
    "owner": 0x470006,
    "onset": 0x470007,
    "duration": 0x470008,
}


def _readonly_array(value: Any, *, dtype: np.dtype[Any] | type | None = None) -> np.ndarray:
    result = np.asarray(value, dtype=dtype).copy()
    result.setflags(write=False)
    return result


def _finite_array(value: Any, shape: tuple[int, ...], *, label: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != shape or not np.isfinite(result).all():
        raise G0RealizationError(f"{label} shape/finite invariant failed")
    return result


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite_float": value.hex()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise G0RealizationError(
        f"value of type {type(value).__name__} is not primitive evidence"
    )


def sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _rng(episode_id: int, namespace: str, *extra: int) -> np.random.Generator:
    if namespace not in _NAMESPACE_CODES:
        raise KeyError(f"unknown G0 RNG namespace {namespace!r}")
    words = [int(episode_id), int(_NAMESPACE_CODES[namespace]), *(int(v) for v in extra)]
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(words)))


def channel_seed_word(episode_id: int, physical_step: int) -> int:
    """Return a step-addressed channel word independent of controller/cell."""

    generator = _rng(int(episode_id), "channels", int(physical_step))
    return int(generator.integers(0, 2**32, dtype=np.uint32))


def _frozen_geometry_arrays(
    episode_id: int,
    *,
    map_width: float,
    map_height: float,
    base_xy: np.ndarray,
) -> dict[str, Any]:
    """Reconstruct every RNG-owned geometry primitive from its namespace."""

    episode = int(episode_id)
    width, height = float(map_width), float(map_height)
    scale = min(width, height)
    phi = float(_rng(episode, "phi").uniform(0.0, 2.0 * math.pi))
    theta = phi + 2.0 * math.pi * np.arange(HOTSPOT_COUNT, dtype=np.float64) / 3.0
    unit = np.stack((np.cos(theta), np.sin(theta)), axis=1)
    tangent = np.stack((-np.sin(theta), np.cos(theta)), axis=1)
    centers = base_xy[None, :] + 0.300 * scale * unit

    user_rng = _rng(episode, "users")
    user_u = user_rng.random((HOTSPOT_COUNT, USERS_PER_HOTSPOT))
    user_v = user_rng.random((HOTSPOT_COUNT, USERS_PER_HOTSPOT))
    user_offsets = 0.040 * scale * np.sqrt(user_u)[..., None] * np.stack(
        (np.cos(2.0 * math.pi * user_v), np.sin(2.0 * math.pi * user_v)),
        axis=-1,
    )
    users = (centers[:, None, :] + user_offsets).reshape(GROUND_USERS, 2)
    primary = np.stack(
        [
            centers[hotspot] + sign * 0.040 * scale * tangent[hotspot]
            for hotspot in range(HOTSPOT_COUNT)
            for sign in (-1, 1)
        ]
    )
    reserve_axis = np.asarray(
        (math.cos(phi + math.pi / 12.0), math.sin(phi + math.pi / 12.0)),
        dtype=np.float64,
    )
    stages = np.stack(
        [base_xy + sign * 0.050 * scale * reserve_axis for sign in (-1, 1)]
    )
    gates = np.stack(
        [
            primary[2 * hotspot + sign_index] - 0.060 * scale * unit[hotspot]
            for hotspot in range(HOTSPOT_COUNT)
            for sign_index in range(2)
        ]
    )
    targets = np.concatenate((primary, stages), axis=0)
    perturb_rng = _rng(episode, "perturbations")
    perturb_u = perturb_rng.random(PHYSICAL_UAVS)
    perturb_v = perturb_rng.random(PHYSICAL_UAVS)
    perturbations = 0.002 * scale * np.sqrt(perturb_u)[:, None] * np.stack(
        (np.cos(2.0 * math.pi * perturb_v), np.sin(2.0 * math.pi * perturb_v)),
        axis=1,
    )
    target_owned_initial = targets + perturbations
    slot_to_target = _rng(episode, "permutation").permutation(PHYSICAL_UAVS).astype(
        np.int64
    )
    return {
        "phi": phi,
        "hotspot_centers": centers,
        "users_xy": users,
        "target_xy": targets,
        "gate_xy": gates,
        "target_owned_initial_xy": target_owned_initial,
        "slot_to_target": slot_to_target,
        "physical_xy": target_owned_initial[slot_to_target],
    }


@dataclass(frozen=True, order=True)
class TargetLabel:
    kind: TargetKind
    hotspot: int | None
    sign: int

    def __post_init__(self) -> None:
        kind = TargetKind(self.kind)
        object.__setattr__(self, "kind", kind)
        if self.sign not in (-1, 1):
            raise G0RealizationError("target sign must be -1 or +1")
        if kind is TargetKind.PRIMARY:
            if self.hotspot not in range(HOTSPOT_COUNT):
                raise G0RealizationError("primary hotspot is outside 0..2")
        elif self.hotspot is not None:
            raise G0RealizationError("stage target cannot own a hotspot")

    @property
    def key(self) -> str:
        if self.kind is TargetKind.PRIMARY:
            return f"primary/{int(self.hotspot)}/{int(self.sign):+d}"
        return f"stage/{int(self.sign):+d}"

    @classmethod
    def parse(cls, value: str) -> "TargetLabel":
        fields = str(value).split("/")
        if fields[0] == "primary" and len(fields) == 3:
            return cls(TargetKind.PRIMARY, int(fields[1]), int(fields[2]))
        if fields[0] == "stage" and len(fields) == 2:
            return cls(TargetKind.STAGE, None, int(fields[1]))
        raise G0RealizationError(f"invalid target key {value!r}")


TARGET_LABELS = tuple(
    TargetLabel(TargetKind.PRIMARY, hotspot, sign)
    for hotspot in range(HOTSPOT_COUNT)
    for sign in (-1, 1)
) + tuple(TargetLabel(TargetKind.STAGE, None, sign) for sign in (-1, 1))


@dataclass(frozen=True)
class G0Geometry:
    episode_id: int
    map_width: float
    map_height: float
    base_xy: np.ndarray
    phi: float
    hotspot_centers: np.ndarray
    users_xy: np.ndarray
    user_hotspots: np.ndarray
    target_labels: tuple[TargetLabel, ...]
    target_xy: np.ndarray
    gate_xy: np.ndarray
    target_owned_initial_xy: np.ndarray
    slot_to_target: np.ndarray
    physical_xy: np.ndarray

    def __post_init__(self) -> None:
        if int(self.episode_id) < 0:
            raise G0RealizationError("episode id must be nonnegative")
        width, height = float(self.map_width), float(self.map_height)
        if not (math.isfinite(width) and math.isfinite(height) and width > 0 and height > 0):
            raise G0RealizationError("map dimensions must be positive finite values")
        if width != MAP_WIDTH_M or height != MAP_HEIGHT_M:
            raise G0RealizationError("G0 map dimensions differ from frozen S7-S1")
        labels = tuple(self.target_labels)
        if labels != TARGET_LABELS:
            raise G0RealizationError("target label inventory/order drifted")
        base = _finite_array(self.base_xy, (2,), label="base coordinate")
        expected_base = np.asarray((width / 2.0, height / 2.0), dtype=np.float64)
        if not np.array_equal(base, expected_base):
            raise G0RealizationError("base station is not the rectangular-map center")
        centers = _finite_array(
            self.hotspot_centers, (HOTSPOT_COUNT, 2), label="hotspot centers"
        )
        users = _finite_array(self.users_xy, (GROUND_USERS, 2), label="users")
        memberships = np.asarray(self.user_hotspots, dtype=np.int64)
        if memberships.shape != (GROUND_USERS,) or not np.array_equal(
            memberships, np.repeat(np.arange(HOTSPOT_COUNT), USERS_PER_HOTSPOT)
        ):
            raise G0RealizationError("hotspot membership inventory drifted")
        targets = _finite_array(self.target_xy, (PHYSICAL_UAVS, 2), label="targets")
        gates = _finite_array(self.gate_xy, (6, 2), label="gates")
        initial = _finite_array(
            self.target_owned_initial_xy,
            (PHYSICAL_UAVS, 2),
            label="target-owned initial positions",
        )
        permutation = np.asarray(self.slot_to_target, dtype=np.int64)
        if permutation.shape != (PHYSICAL_UAVS,) or sorted(permutation.tolist()) != list(
            range(PHYSICAL_UAVS)
        ):
            raise G0RealizationError("physical-slot permutation is not a bijection")
        physical = _finite_array(
            self.physical_xy, (PHYSICAL_UAVS, 2), label="physical positions"
        )
        if not np.array_equal(physical, initial[permutation]):
            raise G0RealizationError("slot permutation changed target-owned world positions")
        expected = _frozen_geometry_arrays(
            int(self.episode_id),
            map_width=width,
            map_height=height,
            base_xy=expected_base,
        )
        exact_fields = {
            "hotspot_centers": centers,
            "users_xy": users,
            "target_xy": targets,
            "gate_xy": gates,
            "target_owned_initial_xy": initial,
            "slot_to_target": permutation,
            "physical_xy": physical,
        }
        if float(self.phi) != expected["phi"] or any(
            not np.array_equal(actual, expected[name])
            for name, actual in exact_fields.items()
        ):
            raise G0RealizationError(
                "geometry does not reconstruct from the registered episode RNG namespaces"
            )
        support = np.concatenate((centers, users, targets, gates, initial, physical), axis=0)
        if (
            np.any(support[:, 0] < 0.0)
            or np.any(support[:, 0] > width)
            or np.any(support[:, 1] < 0.0)
            or np.any(support[:, 1] > height)
        ):
            raise G0RealizationError("sampled geometry lies outside map support")
        for name, value, dtype in (
            ("base_xy", base, np.float64),
            ("hotspot_centers", centers, np.float64),
            ("users_xy", users, np.float64),
            ("user_hotspots", memberships, np.int64),
            ("target_xy", targets, np.float64),
            ("gate_xy", gates, np.float64),
            ("target_owned_initial_xy", initial, np.float64),
            ("slot_to_target", permutation, np.int64),
            ("physical_xy", physical, np.float64),
        ):
            object.__setattr__(self, name, _readonly_array(value, dtype=dtype))

    @property
    def scale(self) -> float:
        return min(float(self.map_width), float(self.map_height))

    def coordinate(self, label: TargetLabel | str) -> np.ndarray:
        chosen = TargetLabel.parse(label) if isinstance(label, str) else label
        return self.target_xy[self.target_labels.index(chosen)].copy()

    def gate(self, primary: TargetLabel | str) -> np.ndarray:
        chosen = TargetLabel.parse(primary) if isinstance(primary, str) else primary
        if chosen.kind is not TargetKind.PRIMARY:
            raise G0RealizationError("only a primary owns an inward gate")
        return self.gate_xy[self.target_labels[:6].index(chosen)].copy()

    def to_primitive(self) -> dict[str, Any]:
        return {
            "episode_id": int(self.episode_id),
            "map_width": float(self.map_width),
            "map_height": float(self.map_height),
            "base_xy": self.base_xy.tolist(),
            "phi": float(self.phi),
            "hotspot_centers": self.hotspot_centers.tolist(),
            "users_xy": self.users_xy.tolist(),
            "user_hotspots": self.user_hotspots.tolist(),
            "target_labels": [label.key for label in self.target_labels],
            "target_xy": self.target_xy.tolist(),
            "gate_xy": self.gate_xy.tolist(),
            "target_owned_initial_xy": self.target_owned_initial_xy.tolist(),
            "slot_to_target": self.slot_to_target.tolist(),
            "physical_xy": self.physical_xy.tolist(),
        }


@dataclass(frozen=True)
class G0EventLedger:
    episode_id: int
    owner_target: TargetLabel
    onset: int
    duration: int

    def __post_init__(self) -> None:
        owner = self.owner_target
        if owner.kind is not TargetKind.PRIMARY:
            raise G0RealizationError("event owner must be one of six primary lifecycles")
        if not 180 <= int(self.onset) <= 220:
            raise G0RealizationError("event onset is outside 180..220")
        if not 80 <= int(self.duration) <= 100:
            raise G0RealizationError("event duration is outside 80..100")
        if int(self.onset) + int(self.duration) + RECOVERY_WINDOW_EXTENSION >= PHYSICAL_HORIZON:
            raise G0RealizationError("event-plus-recovery window exceeds H=500")
        episode = int(self.episode_id)
        expected_owner = TARGET_LABELS[int(_rng(episode, "owner").integers(0, 6))]
        expected_onset = int(_rng(episode, "onset").integers(180, 221))
        expected_duration = int(_rng(episode, "duration").integers(80, 101))
        if (
            owner != expected_owner
            or int(self.onset) != expected_onset
            or int(self.duration) != expected_duration
        ):
            raise G0RealizationError(
                "event ledger does not reconstruct from independent RNG namespaces"
            )

    @property
    def rejoin(self) -> int:
        return int(self.onset) + int(self.duration)

    def active(self, physical_step: int, cell: Cell | str) -> bool:
        if Cell(cell) is Cell.NO_EVENT:
            return True
        return not (int(self.onset) <= int(physical_step) < self.rejoin)

    def to_primitive(self) -> dict[str, Any]:
        return {
            "episode_id": int(self.episode_id),
            "owner_target": self.owner_target.key,
            "onset": int(self.onset),
            "duration": int(self.duration),
            "rejoin": self.rejoin,
            "announcement_lead_steps": 0,
            "detection_delay_steps": 0,
        }


@dataclass(frozen=True)
class AssignmentCertificate:
    row_order: tuple[int, ...]
    target_order: tuple[str, ...]
    row_to_target: tuple[str, ...]
    squared_cost: float
    minimizing_assignment_count: int
    lexicographic_tie_break_applied: bool
    anonymous_rows_distinct: bool
    primary_count_by_hotspot: tuple[int, int, int]
    staging_count: int
    passed: bool

    def to_primitive(self) -> dict[str, Any]:
        return {
            "row_order": list(self.row_order),
            "target_order": list(self.target_order),
            "row_to_target": list(self.row_to_target),
            "squared_cost": float(self.squared_cost),
            "minimizing_assignment_count": int(self.minimizing_assignment_count),
            "lexicographic_tie_break_applied": bool(self.lexicographic_tie_break_applied),
            "anonymous_rows_distinct": bool(self.anonymous_rows_distinct),
            "primary_count_by_hotspot": list(self.primary_count_by_hotspot),
            "staging_count": int(self.staging_count),
            "passed": bool(self.passed),
        }


@dataclass(frozen=True)
class G0EpisodeSource:
    geometry: G0Geometry
    event: G0EventLedger
    assignment: AssignmentCertificate
    namespace_names: tuple[str, ...] = field(default_factory=lambda: tuple(_NAMESPACE_CODES))

    def __post_init__(self) -> None:
        if self.geometry.episode_id != self.event.episode_id:
            raise G0RealizationError("geometry/event episode identity mismatch")
        if not self.assignment.passed:
            raise G0RealizationError("initial assignment certificate failed")
        if tuple(self.namespace_names) != tuple(_NAMESPACE_CODES):
            raise G0RealizationError("RNG namespace inventory drifted")
        expected_assignment = minimum_cost_target_assignment(
            physical_rows=np.concatenate(
                (
                    self.geometry.physical_xy,
                    np.zeros((PHYSICAL_UAVS, 2), dtype=np.float64),
                ),
                axis=1,
            ),
            target_xy=self.geometry.target_xy,
        )
        if self.assignment.to_primitive() != expected_assignment.to_primitive():
            raise G0RealizationError(
                "initial ownership certificate does not reconstruct from geometry"
            )

    def to_primitive(self) -> dict[str, Any]:
        value = {
            "algorithm_id": ALGORITHM_ID,
            "source_id": SOURCE_ID,
            "geometry": self.geometry.to_primitive(),
            "event": self.event.to_primitive(),
            "assignment": self.assignment.to_primitive(),
            "rng_namespaces": list(self.namespace_names),
            "controller_name_reseeding": False,
        }
        value["sha256"] = sha256_json(value)
        return value


def minimum_cost_target_assignment(
    *,
    physical_rows: np.ndarray,
    target_xy: np.ndarray,
    target_labels: Sequence[TargetLabel] = TARGET_LABELS,
) -> AssignmentCertificate:
    """Exact eight-row anonymous assignment with the frozen tie law.

    Rows are ordered only by (x,y,vx,vy); targets only by (x,y).  The eight-row
    inventory permits exhaustive 8! enumeration, avoiding a tolerance or a
    slot-index perturbation in the scientific assignment.
    """

    rows = _finite_array(
        physical_rows, (PHYSICAL_UAVS, 4), label="anonymous assignment rows"
    )
    targets = _finite_array(target_xy, (PHYSICAL_UAVS, 2), label="assignment targets")
    labels = tuple(target_labels)
    if labels != TARGET_LABELS:
        raise G0RealizationError("assignment target label inventory drifted")
    row_order = tuple(sorted(range(PHYSICAL_UAVS), key=lambda i: tuple(rows[i].tolist())))
    ordered_row_values = [rows[index].tobytes() for index in row_order]
    anonymous_distinct = len(set(ordered_row_values)) == PHYSICAL_UAVS
    if not anonymous_distinct:
        raise G0RealizationError(
            "bitwise-identical anonymous physical rows require a forbidden identity tie"
        )
    target_order_indices = tuple(
        sorted(range(PHYSICAL_UAVS), key=lambda i: tuple(targets[i].tolist()))
    )
    ordered_targets = targets[np.asarray(target_order_indices)]
    ordered_labels = tuple(labels[index] for index in target_order_indices)
    ordered_positions = rows[np.asarray(row_order), :2]
    costs = np.sum(
        (ordered_positions[:, None, :] - ordered_targets[None, :, :]) ** 2,
        axis=2,
        dtype=np.float64,
    )
    best_cost = math.inf
    best_permutation: tuple[int, ...] | None = None
    minimizing_count = 0
    for permutation in itertools.permutations(range(PHYSICAL_UAVS)):
        cost = float(sum(float(costs[row, column]) for row, column in enumerate(permutation)))
        if cost < best_cost:
            best_cost = cost
            best_permutation = permutation
            minimizing_count = 1
        elif cost == best_cost:
            minimizing_count += 1
            if best_permutation is None or permutation < best_permutation:
                best_permutation = permutation
    if best_permutation is None or not math.isfinite(best_cost):
        raise G0RealizationError("minimum-cost assignment was not finite")
    row_to_target = [""] * PHYSICAL_UAVS
    for canonical_row, canonical_target in enumerate(best_permutation):
        physical_row = row_order[canonical_row]
        row_to_target[physical_row] = ordered_labels[canonical_target].key
    decoded = tuple(TargetLabel.parse(value) for value in row_to_target)
    primary_counts = tuple(
        sum(
            label.kind is TargetKind.PRIMARY and label.hotspot == hotspot
            for label in decoded
        )
        for hotspot in range(HOTSPOT_COUNT)
    )
    stage_count = sum(label.kind is TargetKind.STAGE for label in decoded)
    passed = primary_counts == (2, 2, 2) and stage_count == 2
    return AssignmentCertificate(
        row_order=row_order,
        target_order=tuple(label.key for label in ordered_labels),
        row_to_target=tuple(row_to_target),
        squared_cost=best_cost,
        minimizing_assignment_count=minimizing_count,
        lexicographic_tie_break_applied=minimizing_count > 1,
        anonymous_rows_distinct=anonymous_distinct,
        primary_count_by_hotspot=primary_counts,
        staging_count=stage_count,
        passed=passed,
    )


def make_episode_source(
    episode_id: int,
    *,
    map_width: float = MAP_WIDTH_M,
    map_height: float = MAP_HEIGHT_M,
    base_xy: Sequence[float] | None = None,
) -> G0EpisodeSource:
    """Materialize one episode-addressed source with independent RNG fields."""

    episode = int(episode_id)
    width, height = float(map_width), float(map_height)
    base = np.asarray(
        (width / 2.0, height / 2.0) if base_xy is None else base_xy,
        dtype=np.float64,
    )
    scale = min(width, height)
    phi = float(_rng(episode, "phi").uniform(0.0, 2.0 * math.pi))
    theta = phi + 2.0 * math.pi * np.arange(HOTSPOT_COUNT, dtype=np.float64) / 3.0
    unit = np.stack((np.cos(theta), np.sin(theta)), axis=1)
    tangent = np.stack((-np.sin(theta), np.cos(theta)), axis=1)
    centers = base[None, :] + 0.300 * scale * unit

    user_rng = _rng(episode, "users")
    user_u = user_rng.random((HOTSPOT_COUNT, USERS_PER_HOTSPOT))
    user_v = user_rng.random((HOTSPOT_COUNT, USERS_PER_HOTSPOT))
    user_offsets = 0.040 * scale * np.sqrt(user_u)[..., None] * np.stack(
        (np.cos(2.0 * math.pi * user_v), np.sin(2.0 * math.pi * user_v)),
        axis=-1,
    )
    users = (centers[:, None, :] + user_offsets).reshape(GROUND_USERS, 2)

    primary = np.stack(
        [centers[z] + sign * 0.040 * scale * tangent[z] for z in range(3) for sign in (-1, 1)]
    )
    reserve_axis = np.asarray(
        (math.cos(phi + math.pi / 12.0), math.sin(phi + math.pi / 12.0)),
        dtype=np.float64,
    )
    stages = np.stack([base + sign * 0.050 * scale * reserve_axis for sign in (-1, 1)])
    gates = np.stack(
        [primary[2 * z + sign_index] - 0.060 * scale * unit[z] for z in range(3) for sign_index in range(2)]
    )
    targets = np.concatenate((primary, stages), axis=0)

    perturb_rng = _rng(episode, "perturbations")
    perturb_u = perturb_rng.random(PHYSICAL_UAVS)
    perturb_v = perturb_rng.random(PHYSICAL_UAVS)
    perturbations = 0.002 * scale * np.sqrt(perturb_u)[:, None] * np.stack(
        (np.cos(2.0 * math.pi * perturb_v), np.sin(2.0 * math.pi * perturb_v)),
        axis=1,
    )
    target_owned_initial = targets + perturbations
    slot_to_target = _rng(episode, "permutation").permutation(PHYSICAL_UAVS).astype(np.int64)
    physical = target_owned_initial[slot_to_target]
    geometry = G0Geometry(
        episode_id=episode,
        map_width=width,
        map_height=height,
        base_xy=base,
        phi=phi,
        hotspot_centers=centers,
        users_xy=users,
        user_hotspots=np.repeat(np.arange(HOTSPOT_COUNT), USERS_PER_HOTSPOT),
        target_labels=TARGET_LABELS,
        target_xy=targets,
        gate_xy=gates,
        target_owned_initial_xy=target_owned_initial,
        slot_to_target=slot_to_target,
        physical_xy=physical,
    )
    assignment = minimum_cost_target_assignment(
        physical_rows=np.concatenate(
            (geometry.physical_xy, np.zeros((PHYSICAL_UAVS, 2), dtype=np.float64)),
            axis=1,
        ),
        target_xy=geometry.target_xy,
    )
    owner_index = int(_rng(episode, "owner").integers(0, 6))
    event = G0EventLedger(
        episode_id=episode,
        owner_target=TARGET_LABELS[owner_index],
        onset=int(_rng(episode, "onset").integers(180, 221)),
        duration=int(_rng(episode, "duration").integers(80, 101)),
    )
    return G0EpisodeSource(geometry=geometry, event=event, assignment=assignment)


def actions_toward_targets(
    *,
    physical_positions: np.ndarray,
    target_positions: np.ndarray,
    active_mask: np.ndarray,
    max_speed: float,
    max_vertical_speed: float,
    time_step: float,
) -> np.ndarray:
    positions = np.asarray(physical_positions, dtype=np.float64)
    targets = np.asarray(target_positions, dtype=np.float64)
    mask = np.asarray(active_mask, dtype=np.bool_)
    if positions.shape != (PHYSICAL_UAVS, 3) or targets.shape != positions.shape:
        raise ValueError("target-action physical shape mismatch")
    actions = np.zeros((PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32)
    horizontal_scale = max(float(max_speed) * float(time_step), 1e-8)
    vertical_scale = max(float(max_vertical_speed) * float(time_step), 1e-8)
    delta = targets - positions
    actions[mask, :2] = np.clip(delta[mask, :2] / horizontal_scale, -1.0, 1.0)
    actions[mask, 2] = np.clip(delta[mask, 2] / vertical_scale, -1.0, 1.0)
    return actions


g1_common_target_actions = actions_toward_targets


def common_tracker_source_digest() -> str:
    source = inspect.getsource(actions_toward_targets).replace("\r\n", "\n")
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def shared_action_method_digests() -> dict[str, str]:
    def digest(value: Callable[..., Any]) -> str:
        text = inspect.getsource(value).replace("\r\n", "\n")
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    return {
        "prepare_energy_actions": digest(
            UAVEnergyAwareRelayEnv._prepare_energy_actions
        ),
        "movement_velocity": digest(
            UAVEnergyAwareRelayEnv._movement_velocity_from_action
        ),
        "base_action": digest(UAVEnergyAwareRelayEnv._base_action_from_velocity),
        "scenario7_backhaul_guard": digest(
            UAVEnergyAwareRelayEnv._apply_backhaul_action_guard
        ),
        "base_backhaul_guard": digest(
            UAVEnergyAwareRelayEnv.__mro__[1]._apply_backhaul_action_guard
        ),
    }


def oracle_safety_method_digests() -> dict[str, str]:
    """Bind every unchanged result-bearing native safety transition method."""

    def digest(value: Callable[..., Any]) -> str:
        text = inspect.getsource(value).replace("\r\n", "\n")
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    values = dict(shared_action_method_digests())
    values.update(
        {
            "g0_channel_update": digest(
                UAVSourceIdentifiabilityEnv._update_channel_state
            ),
            "scenario7_connection_update": digest(
                UAVEnergyAwareRelayEnv._update_uav_connections
            ),
            "native_routing_update": digest(
                UAVEnergyAwareRelayEnv.__mro__[1]._compute_routing_paths
            ),
            "scenario7_link_capacity": digest(
                UAVEnergyAwareRelayEnv._get_link_capacity
            ),
            "g0_guard_capacity_capture": digest(
                UAVSourceIdentifiabilityEnv._get_link_capacity
            ),
            "g0_safety_only_transition": digest(
                UAVSourceIdentifiabilityEnv.step_oracle_safety
            ),
        }
    )
    return values


def qualify_common_tracker(
    *,
    episode_source: G0EpisodeSource,
    physical_positions: np.ndarray,
    target_positions: np.ndarray,
    active_mask: np.ndarray,
    max_speed: float,
    max_vertical_speed: float,
    time_step: float,
    permutation: Sequence[int],
) -> dict[str, Any]:
    """Reconstruct determinism, shared correction and permutation evidence."""

    positions = _finite_array(
        physical_positions, (PHYSICAL_UAVS, 3), label="tracker positions"
    )
    targets = _finite_array(target_positions, (PHYSICAL_UAVS, 3), label="tracker targets")
    mask = np.asarray(active_mask, dtype=np.bool_)
    order = np.asarray(tuple(int(v) for v in permutation), dtype=np.int64)
    if mask.shape != (PHYSICAL_UAVS,) or sorted(order.tolist()) != list(range(PHYSICAL_UAVS)):
        raise G0RealizationError("tracker qualification mask/permutation mismatch")
    keyword = {
        "max_speed": max_speed,
        "max_vertical_speed": max_vertical_speed,
        "time_step": time_step,
    }
    raw_left = g1_common_target_actions(
        physical_positions=positions,
        target_positions=targets,
        active_mask=mask,
        **keyword,
    )
    raw_right = g1_common_target_actions(
        physical_positions=positions.copy(),
        target_positions=targets.copy(),
        active_mask=mask.copy(),
        **keyword,
    )
    if common_tracker_source_digest() != ACCEPTED_G1_TRACKER_SOURCE_SHA256:
        raise G0RealizationError("common tracker source differs from accepted G1")

    method_digests = shared_action_method_digests()
    method_identity = method_digests == ACCEPTED_G1_SHARED_ACTION_METHOD_SHA256

    environment = UAVSourceIdentifiabilityEnv(episode_source, Cell.NO_EVENT)
    try:
        environment.reset()

        def actual_shared_projection(
            actions: np.ndarray, projection_mask: np.ndarray
        ) -> np.ndarray:
            environment._service_active_mask = np.asarray(
                projection_mask, dtype=np.bool_
            ).copy()
            action_dict = {
                agent: np.asarray(actions[row], dtype=np.float32).copy()
                for row, agent in enumerate(environment.possible_agents)
            }
            adjusted, _commanded = environment._prepare_energy_actions(action_dict)
            return np.stack(
                [
                    np.asarray(adjusted[agent], dtype=np.float32)
                    for agent in environment.possible_agents
                ]
            )

        executed_left = actual_shared_projection(raw_left.copy(), mask)
        executed_right = actual_shared_projection(raw_right.copy(), mask.copy())
    finally:
        environment.close()
    raw_permuted = g1_common_target_actions(
        physical_positions=positions[order],
        target_positions=targets[order],
        active_mask=mask[order],
        **keyword,
    )
    unpermuted = np.empty_like(raw_permuted)
    unpermuted[order] = raw_permuted
    environment = UAVSourceIdentifiabilityEnv(episode_source, Cell.NO_EVENT)
    try:
        environment.reset()
        environment._service_active_mask = mask[order].copy()
        adjusted, _commanded = environment._prepare_energy_actions(
            {
                agent: raw_permuted[row].copy()
                for row, agent in enumerate(environment.possible_agents)
            }
        )
        executed_permuted = np.stack(
            [
                np.asarray(adjusted[agent], dtype=np.float32)
                for agent in environment.possible_agents
            ]
        )
    finally:
        environment.close()
    executed_unpermuted = np.empty_like(executed_permuted)
    executed_unpermuted[order] = executed_permuted
    raw_equal = np.array_equal(raw_left, raw_right)
    executed_equal = np.array_equal(executed_left, executed_right)
    permutation_equal = np.array_equal(raw_left, unpermuted)
    executed_permutation_equal = np.array_equal(executed_left, executed_unpermuted)
    support_valid = bool(
        np.isfinite(raw_left).all()
        and np.all(np.abs(raw_left) <= 1.0)
        and np.array_equal(raw_left[~mask], np.zeros_like(raw_left[~mask]))
    )
    executed_support_valid = bool(
        executed_left.shape == (PHYSICAL_UAVS, 3)
        and np.isfinite(executed_left).all()
        and np.all(np.abs(executed_left) <= 1.0)
        and np.array_equal(
            executed_left[~mask], np.zeros_like(executed_left[~mask])
        )
    )
    passed = bool(
        raw_equal
        and executed_equal
        and permutation_equal
        and executed_permutation_equal
        and support_valid
        and executed_support_valid
        and method_identity
    )
    return {
        "accepted_g1_source_commit": ACCEPTED_G1_SOURCE_COMMIT,
        "tracker_symbol": "actions_toward_targets",
        "tracker_source_sha256": common_tracker_source_digest(),
        "accepted_tracker_source_sha256": ACCEPTED_G1_TRACKER_SOURCE_SHA256,
        "shared_action_method_sha256": method_digests,
        "shared_action_method_identity": method_identity,
        "same_state_target_raw_actions_bitwise_equal": raw_equal,
        "same_state_target_executed_actions_bitwise_equal": executed_equal,
        "permutation_equivariant": permutation_equal,
        "executed_permutation_equivariant": executed_permutation_equal,
        "action_support_valid": support_valid,
        "executed_action_support_valid": executed_support_valid,
        "inactive_action_rows_zero": bool(
            np.array_equal(raw_left[~mask], np.zeros_like(raw_left[~mask]))
        ),
        "controller_specific_branch_count": 0,
        "controller_specific_tolerance_count": 0,
        "passed": passed,
    }


@dataclass(frozen=True)
class AnonymousLifecycleRow:
    """One current roster row; ``handle`` is opaque state ownership only."""

    handle: str
    position: np.ndarray
    velocity: np.ndarray
    active: bool
    service_available: bool

    def __post_init__(self) -> None:
        if not str(self.handle):
            raise G0RealizationError("lifecycle handle must be nonempty")
        position = _finite_array(self.position, (3,), label="lifecycle position")
        velocity = _finite_array(self.velocity, (3,), label="lifecycle velocity")
        if bool(self.active) != bool(self.service_available):
            raise G0RealizationError("active roster and service availability differ")
        object.__setattr__(self, "position", _readonly_array(position, dtype=np.float64))
        object.__setattr__(self, "velocity", _readonly_array(velocity, dtype=np.float64))

    @property
    def anonymous_tie_key(self) -> tuple[float, ...]:
        return tuple(float(value) for value in np.concatenate((self.position, self.velocity)))


@dataclass(frozen=True)
class G0CurrentInformation:
    """Exact current-only observation boundary shared by S and N controls."""

    rows: tuple[AnonymousLifecycleRow, ...]
    user_demand_mbps: np.ndarray
    user_delivered_rate_mbps: np.ndarray
    channel_association: np.ndarray
    base_xy: np.ndarray
    primary_xy: np.ndarray
    gate_xy: np.ndarray
    stage_xy: np.ndarray

    def __post_init__(self) -> None:
        rows = tuple(self.rows)
        _roster_by_handle(rows)
        arrays = (
            ("user_demand_mbps", self.user_demand_mbps, (GROUND_USERS,), np.float64),
            ("user_delivered_rate_mbps", self.user_delivered_rate_mbps, (GROUND_USERS,), np.float64),
            ("channel_association", self.channel_association, (PHYSICAL_UAVS, GROUND_USERS), np.bool_),
            ("base_xy", self.base_xy, (2,), np.float64),
            ("primary_xy", self.primary_xy, (6, 2), np.float64),
            ("gate_xy", self.gate_xy, (6, 2), np.float64),
            ("stage_xy", self.stage_xy, (2, 2), np.float64),
        )
        for name, value, shape, dtype in arrays:
            array = np.asarray(value, dtype=dtype)
            if array.shape != shape or (
                dtype is not np.bool_ and not np.isfinite(array).all()
            ):
                raise G0RealizationError(f"current-information {name} is malformed")
            if dtype is not np.bool_ and np.any(array < 0.0) and name in {
                "user_demand_mbps",
                "user_delivered_rate_mbps",
            }:
                raise G0RealizationError(f"current-information {name} is negative")
            object.__setattr__(self, name, _readonly_array(array, dtype=dtype))
        object.__setattr__(self, "rows", rows)

    @property
    def weakest_hotspot_service(self) -> float:
        return weakest_hotspot_service_row(
            self.user_delivered_rate_mbps,
            np.repeat(np.arange(HOTSPOT_COUNT), USERS_PER_HOTSPOT),
        )


@dataclass(frozen=True)
class G0ControllerGeometry:
    """Static world geometry with no event, slot, user, or RNG authority."""

    base_xy: np.ndarray
    primary_xy: np.ndarray
    gate_xy: np.ndarray
    stage_xy: np.ndarray

    def __post_init__(self) -> None:
        for name, value, shape in (
            ("base_xy", self.base_xy, (2,)),
            ("primary_xy", self.primary_xy, (6, 2)),
            ("gate_xy", self.gate_xy, (6, 2)),
            ("stage_xy", self.stage_xy, (2, 2)),
        ):
            array = _finite_array(value, shape, label=f"controller {name}")
            object.__setattr__(self, name, _readonly_array(array, dtype=np.float64))

    @classmethod
    def from_source(cls, source: G0EpisodeSource) -> "G0ControllerGeometry":
        return cls(
            base_xy=source.geometry.base_xy,
            primary_xy=source.geometry.target_xy[:6],
            gate_xy=source.geometry.gate_xy,
            stage_xy=source.geometry.target_xy[6:],
        )

    def coordinate(self, label: TargetLabel | str) -> np.ndarray:
        parsed = label if isinstance(label, TargetLabel) else TargetLabel.parse(label)
        index = TARGET_LABELS.index(parsed)
        values = self.primary_xy if index < 6 else self.stage_xy
        return values[index if index < 6 else index - 6]

    def gate(self, label: TargetLabel | str) -> np.ndarray:
        parsed = label if isinstance(label, TargetLabel) else TargetLabel.parse(label)
        if parsed.kind is not TargetKind.PRIMARY:
            raise G0RealizationError("only primary targets own holding gates")
        return self.gate_xy[TARGET_LABELS.index(parsed)]


def make_current_information(
    source: G0EpisodeSource,
    *,
    rows: Sequence[AnonymousLifecycleRow],
    user_demand_mbps: Sequence[float],
    user_delivered_rate_mbps: Sequence[float],
    channel_association: np.ndarray,
) -> G0CurrentInformation:
    return G0CurrentInformation(
        rows=tuple(rows),
        user_demand_mbps=np.asarray(user_demand_mbps, dtype=np.float64),
        user_delivered_rate_mbps=np.asarray(
            user_delivered_rate_mbps, dtype=np.float64
        ),
        channel_association=np.asarray(channel_association, dtype=np.bool_),
        base_xy=source.geometry.base_xy,
        primary_xy=source.geometry.target_xy[:6],
        gate_xy=source.geometry.gate_xy,
        stage_xy=source.geometry.target_xy[6:],
    )


def _current_roster(
    geometry: G0ControllerGeometry,
    information: G0CurrentInformation,
) -> dict[str, AnonymousLifecycleRow]:
    """Validate the complete frozen current-information envelope."""

    if not isinstance(information, G0CurrentInformation):
        raise G0RealizationError("controller requires the frozen current-information envelope")
    expected = (
        (information.base_xy, geometry.base_xy),
        (information.primary_xy, geometry.primary_xy),
        (information.gate_xy, geometry.gate_xy),
        (information.stage_xy, geometry.stage_xy),
    )
    if any(not np.array_equal(actual, frozen) for actual, frozen in expected):
        raise G0RealizationError("current-information geometry differs from the episode source")
    return _roster_by_handle(information.rows)


def initial_lifecycle_handles(source: G0EpisodeSource) -> tuple[str, ...]:
    """Create opaque handles without exposing target or physical-slot identity."""

    return tuple(
        hashlib.sha256(
            f"{SOURCE_ID}|{source.geometry.episode_id}|lifecycle|{rank}".encode("utf-8")
        ).hexdigest()[:24]
        for rank in range(PHYSICAL_UAVS)
    )


def replacement_lifecycle_handle(source: G0EpisodeSource, previous: str) -> str:
    return hashlib.sha256(
        f"{SOURCE_ID}|{source.geometry.episode_id}|rejoin|{previous}".encode("utf-8")
    ).hexdigest()[:24]


def _initial_ownership(
    source: G0EpisodeSource, handles: Sequence[str]
) -> dict[str, TargetLabel]:
    if len(handles) != PHYSICAL_UAVS or len(set(handles)) != PHYSICAL_UAVS:
        raise G0RealizationError("initial lifecycle handle inventory mismatch")
    return {
        str(handle): TargetLabel.parse(target)
        for handle, target in zip(handles, source.assignment.row_to_target)
    }


def _roster_by_handle(rows: Sequence[AnonymousLifecycleRow]) -> dict[str, AnonymousLifecycleRow]:
    values = {row.handle: row for row in rows}
    if len(values) != len(rows):
        raise G0RealizationError("current roster contains a duplicate opaque handle")
    if len(rows) != PHYSICAL_UAVS:
        raise G0RealizationError("physical roster must retain all eight storage rows")
    return values


class SameInformationController:
    """Frozen current-information reallocation state machine.

    The event ledger is intentionally absent from this interface.  LEAVE and
    REJOIN arrive as current boundary events; target choice uses only current
    anonymous physical content and registered geometry.
    """

    name = Control.SAME_INFORMATION.value
    uses_future_ledger = False
    trains = False

    def __init__(self, source: G0EpisodeSource, handles: Sequence[str]) -> None:
        self.geometry = G0ControllerGeometry.from_source(source)
        self.ownership = _initial_ownership(source, handles)
        self.original_ownership = dict(self.ownership)
        self._selected_reserve: str | None = None
        self._vacant_primary: TargetLabel | None = None
        self._selected_stage: TargetLabel | None = None
        self._absent_handle: str | None = None
        self._rejoined_handle: str | None = None
        self._rejoin_step: int | None = None
        self._complete_primary_steps = 0
        self._last_primary_step: int | None = None
        self._reserve_at_gate = False
        self._returned_to_stage = False

    def on_leave(
        self,
        absent_handle: str,
        rows: Sequence[AnonymousLifecycleRow],
    ) -> None:
        roster = _roster_by_handle(rows)
        if self._selected_reserve is not None:
            raise G0RealizationError("same-information controller observed a second leave")
        if absent_handle not in self.ownership or roster[absent_handle].active:
            raise G0RealizationError("leave boundary did not expose one inactive lifecycle")
        if sum(row.active for row in rows) != 7:
            raise G0RealizationError("first leave boundary does not have active count seven")
        vacant = self.ownership[absent_handle]
        if vacant.kind is not TargetKind.PRIMARY:
            raise G0RealizationError("leave did not vacate exactly one primary")
        reserve_handles = [
            handle
            for handle, label in self.ownership.items()
            if label.kind is TargetKind.STAGE and roster[handle].active
        ]
        if len(reserve_handles) != 2:
            raise G0RealizationError("same-information leave does not expose two reserves")
        vacancy = self.geometry.coordinate(vacant)

        def rank(handle: str) -> tuple[float, ...]:
            row = roster[handle]
            stage = self.ownership[handle]
            stage_xy = self.geometry.coordinate(stage)
            distance = float(np.sum((row.position[:2] - vacancy) ** 2))
            return (distance, *row.anonymous_tie_key, float(stage_xy[0]), float(stage_xy[1]))

        selected = min(reserve_handles, key=rank)
        self._selected_reserve = selected
        self._selected_stage = self.ownership[selected]
        self._vacant_primary = vacant
        self._absent_handle = absent_handle
        self.ownership[selected] = vacant

    def on_rejoin(self, previous_handle: str, new_handle: str, physical_step: int) -> None:
        if (
            self._selected_reserve is None
            or self._vacant_primary is None
            or previous_handle != self._absent_handle
            or previous_handle not in self.ownership
            or new_handle in self.ownership
        ):
            raise G0RealizationError("same-information rejoin ownership mismatch")
        del self.ownership[previous_handle]
        self.ownership[new_handle] = self._vacant_primary
        self._rejoined_handle = new_handle
        self._rejoin_step = int(physical_step)
        if self._selected_stage is None:
            raise G0RealizationError("same-information selected stage is missing")
        self.ownership[self._selected_reserve] = self._selected_stage
        self._reserve_at_gate = True

    def target_map(
        self,
        information: G0CurrentInformation,
        *,
        physical_step: int,
    ) -> dict[str, np.ndarray]:
        roster = _current_roster(self.geometry, information)
        weakest_hotspot_service = information.weakest_hotspot_service
        if not math.isfinite(float(weakest_hotspot_service)):
            raise G0RealizationError("same-information service input is nonfinite")
        if self._rejoined_handle is not None:
            if self._rejoin_step is None or self._vacant_primary is None:
                raise G0RealizationError("same-information rejoin state is incomplete")
            row = roster[self._rejoined_handle]
            primary_xy = self.geometry.coordinate(self._vacant_primary)
            at_primary = bool(np.array_equal(row.position[:2], primary_xy))
            if (
                int(physical_step) >= self._rejoin_step + 1
                and row.active
                and at_primary
                and self._last_primary_step == int(physical_step) - 1
            ):
                self._complete_primary_steps += 1
            if row.active and at_primary:
                self._last_primary_step = int(physical_step)
            ready = bool(
                int(physical_step) >= self._rejoin_step + 1
                and self._complete_primary_steps >= 1
                and float(weakest_hotspot_service) >= SERVICE_TARGET
            )
            if ready and not self._returned_to_stage:
                if self._selected_reserve is None or self._selected_stage is None:
                    raise G0RealizationError("same-information return state is incomplete")
                self._reserve_at_gate = False
                self._returned_to_stage = True
        result: dict[str, np.ndarray] = {}
        for handle, label in self.ownership.items():
            if handle not in roster:
                continue
            if handle == self._selected_reserve and self._reserve_at_gate:
                if self._vacant_primary is None:
                    raise G0RealizationError("same-information gate owner is missing")
                xy = self.geometry.gate(self._vacant_primary)
            else:
                xy = self.geometry.coordinate(label)
            result[handle] = np.concatenate((xy, np.asarray((FIXED_ALTITUDE_M,))))
        return result

    def evidence(self) -> dict[str, Any]:
        return {
            "controller": self.name,
            "future_event_field_read_count": 0,
            "future_channel_read_count": 0,
            "future_service_read_count": 0,
            "physical_slot_decision_read_count": 0,
            "epoch_decision_read_count": 0,
            "selected_reserve": self._selected_reserve,
            "vacant_primary": self._vacant_primary.key if self._vacant_primary else None,
            "reserve_at_gate": self._reserve_at_gate,
            "returned_to_stage": self._returned_to_stage,
        }


class NoReallocationController:
    """Same observation boundary with target ownership frozen through LEAVE."""

    name = Control.NO_REALLOCATION.value
    uses_future_ledger = False
    trains = False

    def __init__(self, source: G0EpisodeSource, handles: Sequence[str]) -> None:
        self.geometry = G0ControllerGeometry.from_source(source)
        self.ownership = _initial_ownership(source, handles)
        self._absent_handle: str | None = None
        self._vacant_primary: TargetLabel | None = None

    def on_leave(
        self, absent_handle: str, rows: Sequence[AnonymousLifecycleRow]
    ) -> None:
        roster = _roster_by_handle(rows)
        if sum(row.active for row in rows) != 7 or roster[absent_handle].active:
            raise G0RealizationError("no-reallocation leave boundary mismatch")
        vacant = self.ownership.get(absent_handle)
        if vacant is None or vacant.kind is not TargetKind.PRIMARY:
            raise G0RealizationError("no-reallocation did not observe a primary vacancy")
        self._absent_handle = absent_handle
        self._vacant_primary = vacant

    def on_rejoin(self, previous_handle: str, new_handle: str, physical_step: int) -> None:
        del physical_step
        if previous_handle != self._absent_handle or new_handle in self.ownership:
            raise G0RealizationError("no-reallocation rejoin ownership mismatch")
        if self._vacant_primary is None:
            raise G0RealizationError("no-reallocation vacancy is missing")
        del self.ownership[previous_handle]
        self.ownership[new_handle] = self._vacant_primary

    def target_map(
        self,
        information: G0CurrentInformation,
        *,
        physical_step: int,
    ) -> dict[str, np.ndarray]:
        del physical_step
        roster = _current_roster(self.geometry, information)
        return {
            handle: np.concatenate(
                (self.geometry.coordinate(label), np.asarray((FIXED_ALTITUDE_M,)))
            )
            for handle, label in self.ownership.items()
            if handle in roster
        }

    def evidence(self) -> dict[str, Any]:
        return {
            "controller": self.name,
            "target_change_due_to_active_count": 0,
            "target_change_due_to_service_deficit": 0,
            "reserve_reallocation_count": 0,
            "survivor_reallocation_count": 0,
            "physical_slot_decision_read_count": 0,
            "future_event_field_read_count": 0,
        }


def target_map_to_dense(
    *,
    rows: Sequence[AnonymousLifecycleRow],
    target_map: Mapping[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """Storage-only projection from opaque ownership to dense physical rows."""

    if len(rows) != PHYSICAL_UAVS:
        raise G0RealizationError("dense target projection requires eight rows")
    targets = np.zeros((PHYSICAL_UAVS, 3), dtype=np.float64)
    active = np.zeros(PHYSICAL_UAVS, dtype=np.bool_)
    for storage_row, row in enumerate(rows):
        if row.handle not in target_map:
            raise G0RealizationError("controller target map omitted a lifecycle")
        targets[storage_row] = _finite_array(
            target_map[row.handle], (3,), label="controller target"
        )
        active[storage_row] = bool(row.active)
    return targets, active


@dataclass(frozen=True)
class OracleSafetyDrawCoordinate:
    physical_step: int
    channel_update_ordinal: int
    rng_operation: str
    shape: tuple[int, ...]
    dtype: str

    def to_primitive(self) -> dict[str, Any]:
        return {
            "physical_step": int(self.physical_step),
            "channel_update_ordinal": int(self.channel_update_ordinal),
            "rng_operation": str(self.rng_operation),
            "shape": list(self.shape),
            "dtype": str(self.dtype),
        }


@dataclass(frozen=True)
class _NativeArrayEvidence:
    dtype: str
    shape: tuple[int, ...]
    data_hex: str

    @classmethod
    def from_array(cls, value: Any) -> "_NativeArrayEvidence":
        array = np.asarray(value)
        return cls(
            dtype=array.dtype.str,
            shape=tuple(int(item) for item in array.shape),
            data_hex=array.tobytes(order="C").hex(),
        )

    def array(self) -> np.ndarray:
        dtype = np.dtype(self.dtype)
        expected = int(np.prod(self.shape, dtype=np.int64)) * dtype.itemsize
        raw = bytes.fromhex(self.data_hex)
        if len(raw) != expected:
            raise G0RealizationError("native array byte count does not match shape/dtype")
        return np.frombuffer(raw, dtype=dtype).reshape(self.shape).copy()

    def to_primitive(self) -> dict[str, Any]:
        return {
            "dtype": self.dtype,
            "shape": list(self.shape),
            "data_hex": self.data_hex,
        }


@dataclass(frozen=True)
class OracleGuardCapacityRead:
    guarded_uav: int
    node1_type: str
    node1_idx: int
    node2_type: str
    node2_idx: int
    capacity_dtype: str
    capacity_hex: str

    @classmethod
    def from_value(
        cls,
        *,
        guarded_uav: int,
        node1_type: str,
        node1_idx: int,
        node2_type: str,
        node2_idx: int,
        value: Any,
    ) -> "OracleGuardCapacityRead":
        scalar = np.asarray(value)
        if scalar.shape != () or not np.isfinite(scalar).all():
            raise G0RealizationError("real guard returned a nonfinite link capacity")
        return cls(
            guarded_uav=int(guarded_uav),
            node1_type=str(node1_type),
            node1_idx=int(node1_idx),
            node2_type=str(node2_type),
            node2_idx=int(node2_idx),
            capacity_dtype=scalar.dtype.str,
            capacity_hex=scalar.tobytes().hex(),
        )

    def capacity(self) -> float:
        dtype = np.dtype(self.capacity_dtype)
        raw = bytes.fromhex(self.capacity_hex)
        if len(raw) != dtype.itemsize:
            raise G0RealizationError("guard capacity byte count drifted")
        value = np.frombuffer(raw, dtype=dtype)[0]
        if not np.isfinite(value):
            raise G0RealizationError("guard capacity is nonfinite")
        return float(value)

    def to_primitive(self) -> dict[str, Any]:
        return {
            "guarded_uav": int(self.guarded_uav),
            "node1_type": self.node1_type,
            "node1_idx": int(self.node1_idx),
            "node2_type": self.node2_type,
            "node2_idx": int(self.node2_idx),
            "capacity_dtype": self.capacity_dtype,
            "capacity_hex": self.capacity_hex,
        }


def _routing_paths_primitive(routing_paths: Mapping[Any, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_index, value in routing_paths.items():
        path, bottleneck = value
        rows.append(
            {
                "source_uav": int(source_index),
                "path": [[str(kind), int(index)] for kind, index in path],
                "bottleneck_capacity_dtype": np.asarray(bottleneck).dtype.str,
                "bottleneck_capacity_hex": np.asarray(bottleneck).tobytes().hex(),
            }
        )
    return rows


@dataclass(frozen=True)
class OracleSafetyStepRecord:
    physical_step: int
    candidate_id: str
    current_uav_positions: _NativeArrayEvidence
    current_uav_velocities: _NativeArrayEvidence
    current_service_mask: _NativeArrayEvidence
    pre_action_context: Mapping[str, Any]
    executed_service_mask: _NativeArrayEvidence
    common_transducer_evidence: Mapping[str, Any]
    raw_candidate_action: _NativeArrayEvidence
    shared_channel_draw_coordinate: tuple[OracleSafetyDrawCoordinate, ...]
    shared_channel_draw_block: tuple[str, ...]
    connections: Mapping[str, _NativeArrayEvidence]
    routing_paths: tuple[Mapping[str, Any], ...]
    exact_link_capacity_values_read_by_the_real_guard: tuple[OracleGuardCapacityRead, ...]
    real_guard_intervention_or_violation_output: Mapping[str, Any]
    guarded_executed_action: _NativeArrayEvidence
    next_uav_positions: _NativeArrayEvidence
    next_uav_velocities: _NativeArrayEvidence

    def to_primitive(self) -> dict[str, Any]:
        value = {
            "physical_step": int(self.physical_step),
            "candidate_id": self.candidate_id,
            "current_uav_positions": self.current_uav_positions.to_primitive(),
            "current_uav_velocities": self.current_uav_velocities.to_primitive(),
            "current_service_mask": self.current_service_mask.to_primitive(),
            "pre_action_context": _json_safe(self.pre_action_context),
            "executed_service_mask": self.executed_service_mask.to_primitive(),
            "common_transducer_evidence": _json_safe(
                self.common_transducer_evidence
            ),
            "raw_candidate_action": self.raw_candidate_action.to_primitive(),
            "shared_channel_draw_coordinate": [
                coordinate.to_primitive()
                for coordinate in self.shared_channel_draw_coordinate
            ],
            "shared_channel_draw_block": list(self.shared_channel_draw_block),
            "connections": {
                key: item.to_primitive() for key, item in self.connections.items()
            },
            "routing_paths": [dict(item) for item in self.routing_paths],
            "exact_link_capacity_values_read_by_the_real_guard": [
                item.to_primitive()
                for item in self.exact_link_capacity_values_read_by_the_real_guard
            ],
            "real_guard_intervention_or_violation_output": dict(
                self.real_guard_intervention_or_violation_output
            ),
            "guarded_executed_action": self.guarded_executed_action.to_primitive(),
            "next_uav_positions": self.next_uav_positions.to_primitive(),
            "next_uav_velocities": self.next_uav_velocities.to_primitive(),
        }
        if set(value) != _ORACLE_SAFETY_ALLOWED_STEP_KEYS:
            raise G0RealizationError("oracle safety step schema drifted")
        return value


@dataclass(frozen=True)
class OracleCandidateSafetyTrace:
    candidate_id: str
    target_schedule_sha256: str
    common_prestate_sha256: str
    steps: tuple[OracleSafetyStepRecord, ...]
    hard_violation_count: int
    gate_arrival_time: int
    gate_arrival_error: float
    event_window_tracking_error: float
    path_length: float
    stage_coordinates: tuple[float, float]
    trace_sha256: str

    @property
    def rank(self) -> tuple[float, ...]:
        return (
            float(self.hard_violation_count),
            float(self.gate_arrival_time),
            float(self.event_window_tracking_error),
            float(self.path_length),
            float(self.stage_coordinates[0]),
            float(self.stage_coordinates[1]),
        )

    def to_primitive(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "target_schedule_sha256": self.target_schedule_sha256,
            "common_prestate_sha256": self.common_prestate_sha256,
            "steps": [step.to_primitive() for step in self.steps],
            "hard_violation_count": int(self.hard_violation_count),
            "gate_arrival_time": int(self.gate_arrival_time),
            "gate_arrival_error": float(self.gate_arrival_error),
            "event_window_tracking_error": float(self.event_window_tracking_error),
            "path_length": float(self.path_length),
            "stage_coordinates": list(self.stage_coordinates),
            "trace_sha256": self.trace_sha256,
        }


@dataclass(frozen=True)
class OracleSafetyLedger:
    source_sha256: str
    common_prestate: Mapping[str, Any]
    common_prestate_sha256: str
    candidate_prestate_sha256: tuple[str, str]
    channel_draw_schema: tuple[OracleSafetyDrawCoordinate, ...]
    shared_channel_draw_blocks: tuple[str, ...]
    candidates: tuple[OracleCandidateSafetyTrace, OracleCandidateSafetyTrace]
    selected_candidate_id: str
    selected_rank: tuple[float, ...]
    shared_action_method_sha256: Mapping[str, str]
    content_sha256: str

    def to_primitive(self, *, include_digest: bool = True) -> dict[str, Any]:
        value = {
            "source_sha256": self.source_sha256,
            "common_prestate": dict(self.common_prestate),
            "common_prestate_sha256": self.common_prestate_sha256,
            "candidate_prestate_sha256": list(self.candidate_prestate_sha256),
            "channel_draw_schema": [item.to_primitive() for item in self.channel_draw_schema],
            "shared_channel_draw_blocks": list(self.shared_channel_draw_blocks),
            "candidates": [item.to_primitive() for item in self.candidates],
            "selected_candidate_id": self.selected_candidate_id,
            "selected_rank": list(self.selected_rank),
            "shared_action_method_sha256": dict(self.shared_action_method_sha256),
            "registration_order": [
                "freeze_common_prestate",
                "freeze_channel_draw_schema",
                "materialize_shared_channel_tape",
                "advance_each_candidate_once",
                "seal_both_candidate_traces",
                "rank_sealed_trace_keys_only",
                "behavioral_service_after_selection",
            ],
            "K_search": K_SEARCH,
            "physical_horizon": PHYSICAL_HORIZON,
            "hypothetical_candidate_transitions": sum(
                len(item.steps) for item in self.candidates
            ),
        }
        if include_digest:
            value["content_sha256"] = self.content_sha256
        return value


@dataclass(frozen=True)
class OracleSafetyCertificate:
    ledger_sha256: str
    selected_candidate_id: str
    candidate_trace_sha256: tuple[str, str]
    behavioral_replay_sha256: str | None = None
    return_ready_step: int | None = None
    prefix_identity_ok: bool | None = None
    branchpoint_identity_ok: bool | None = None
    shared_ledger_identity_ok: bool | None = None
    prebehavior_self_replay_ok: bool | None = None
    behavioral_self_replay_ok: bool | None = None
    target_switch_ok: bool | None = None
    safety_guard_ok: bool | None = None
    replay_ok: bool | None = None

    def to_primitive(self) -> dict[str, Any]:
        return {
            "ledger_sha256": self.ledger_sha256,
            "selected_candidate_id": self.selected_candidate_id,
            "candidate_trace_sha256": list(self.candidate_trace_sha256),
            "behavioral_replay_sha256": self.behavioral_replay_sha256,
            "return_ready_step": self.return_ready_step,
            "prefix_identity_ok": self.prefix_identity_ok,
            "branchpoint_identity_ok": self.branchpoint_identity_ok,
            "shared_ledger_identity_ok": self.shared_ledger_identity_ok,
            "prebehavior_self_replay_ok": self.prebehavior_self_replay_ok,
            "behavioral_self_replay_ok": self.behavioral_self_replay_ok,
            "target_switch_ok": self.target_switch_ok,
            "safety_guard_ok": self.safety_guard_ok,
            "replay_ok": self.replay_ok,
        }


@dataclass(frozen=True)
class OracleBehavioralExecution:
    """Safety-only projection of one causal selected-candidate execution."""

    selected_candidate_id: str
    return_ready_step: int | None
    steps: tuple[OracleSafetyStepRecord, ...]
    target_schedule: _NativeArrayEvidence
    pre_action_weakest_service: _NativeArrayEvidence
    trace_sha256: str

    def to_primitive(self) -> dict[str, Any]:
        return {
            "selected_candidate_id": self.selected_candidate_id,
            "return_ready_step": self.return_ready_step,
            "steps": [step.to_primitive() for step in self.steps],
            "target_schedule": self.target_schedule.to_primitive(),
            "pre_action_weakest_service": (
                self.pre_action_weakest_service.to_primitive()
            ),
            "trace_sha256": self.trace_sha256,
        }


@dataclass(frozen=True)
class OracleCandidateEvidence:
    reserve_target: str
    latest_departure: int
    gate_arrival_time: int
    gate_arrival_error: float
    gate_arrival_roundoff_bound: float
    hard_violation_count: int
    event_window_tracking_error: float
    path_length: float
    stage_coordinates: tuple[float, float]
    physical_steps_advanced: int
    target_schedule_exact: bool
    action_support_valid: bool
    map_support_valid: bool
    candidate_complete: bool
    trace_sha256: str

    @property
    def rank(self) -> tuple[float, ...]:
        return (
            float(self.hard_violation_count),
            float(self.gate_arrival_time),
            float(self.event_window_tracking_error),
            float(self.path_length),
            float(self.stage_coordinates[0]),
            float(self.stage_coordinates[1]),
        )

    def to_primitive(self) -> dict[str, Any]:
        return {
            "reserve_target": self.reserve_target,
            "latest_departure": int(self.latest_departure),
            "gate_arrival_time": int(self.gate_arrival_time),
            "gate_arrival_error": float(self.gate_arrival_error),
            "gate_arrival_roundoff_bound": float(self.gate_arrival_roundoff_bound),
            "hard_violation_count": int(self.hard_violation_count),
            "event_window_tracking_error": float(self.event_window_tracking_error),
            "path_length": float(self.path_length),
            "stage_coordinates": list(self.stage_coordinates),
            "physical_steps_advanced": int(self.physical_steps_advanced),
            "target_schedule_exact": bool(self.target_schedule_exact),
            "action_support_valid": bool(self.action_support_valid),
            "map_support_valid": bool(self.map_support_valid),
            "candidate_complete": bool(self.candidate_complete),
            "trace_sha256": self.trace_sha256,
        }


@dataclass(frozen=True)
class OracleQualificationCertificate:
    candidates: tuple[OracleCandidateEvidence, OracleCandidateEvidence]
    selected_reserve_target: str
    selected_rank: tuple[float, ...]
    both_candidates_evaluated: bool
    exact_lexicographic_winner: bool
    future_channel_read_count: int
    future_service_read_count: int
    unaffected_primary_move_creates_vacancy: bool
    candidate_owner_is_reserve: bool
    shared_dynamics_action_safety_identity: bool
    candidate_count: int
    complexity: str
    nested_rollout: bool
    replanning: bool
    tree_search: bool
    beam_search: bool
    mcts: bool
    adaptive_candidate_creation: bool
    passed: bool
    oracle_safety_ledger_sha256: str = ""
    safety_certificate: OracleSafetyCertificate | None = None

    def to_primitive(self) -> dict[str, Any]:
        return {
            "candidates": [candidate.to_primitive() for candidate in self.candidates],
            "selected_reserve_target": self.selected_reserve_target,
            "selected_rank": list(self.selected_rank),
            "both_candidates_evaluated": self.both_candidates_evaluated,
            "exact_lexicographic_winner": self.exact_lexicographic_winner,
            "future_channel_read_count": self.future_channel_read_count,
            "future_service_read_count": self.future_service_read_count,
            "unaffected_primary_move_creates_vacancy": self.unaffected_primary_move_creates_vacancy,
            "candidate_owner_is_reserve": self.candidate_owner_is_reserve,
            "shared_dynamics_action_safety_identity": self.shared_dynamics_action_safety_identity,
            "shared_action_method_sha256": shared_action_method_digests(),
            "candidate_count": self.candidate_count,
            "K_search": K_SEARCH,
            "K_search_ceiling": K_SEARCH_CEILING,
            "complexity": self.complexity,
            "nested_rollout": self.nested_rollout,
            "replanning": self.replanning,
            "tree_search": self.tree_search,
            "beam_search": self.beam_search,
            "MCTS": self.mcts,
            "adaptive_candidate_creation": self.adaptive_candidate_creation,
            "oracle_safety_ledger_sha256": self.oracle_safety_ledger_sha256,
            "safety_certificate": (
                None
                if self.safety_certificate is None
                else self.safety_certificate.to_primitive()
            ),
            "passed": self.passed,
        }


def _scenario7_nominal_position_step(
    positions: np.ndarray,
    targets: np.ndarray,
    active_mask: np.ndarray,
    *,
    max_speed: float,
    max_vertical_speed: float,
    time_step: float,
) -> tuple[np.ndarray, np.ndarray]:
    actions = g1_common_target_actions(
        physical_positions=positions,
        target_positions=targets,
        active_mask=active_mask,
        max_speed=max_speed,
        max_vertical_speed=max_vertical_speed,
        time_step=time_step,
    )
    updated = np.asarray(positions, dtype=np.float64).copy()
    for row in np.flatnonzero(active_mask):
        horizontal = np.asarray(actions[row, :2], dtype=np.float64)
        norm = float(np.linalg.norm(horizontal))
        if norm > 1e-8:
            velocity_xy = horizontal / norm * min(norm, 1.0) * float(max_speed)
        else:
            velocity_xy = np.zeros(2, dtype=np.float64)
        velocity_z = float(actions[row, 2]) * float(max_vertical_speed)
        updated[row, :2] += velocity_xy * float(time_step)
        updated[row, 2] += velocity_z * float(time_step)
    return updated, actions


def _oracle_schedule_label(
    *,
    step: int,
    reserve: TargetLabel,
    failed: TargetLabel,
    latest_departure: int,
    event: G0EventLedger,
) -> tuple[str, np.ndarray]:
    if step < latest_departure:
        return "stage", np.asarray((0.0, 0.0))  # replaced by caller
    if step < event.onset:
        return "gate", np.asarray((0.0, 0.0))
    if step < event.rejoin:
        return "primary", np.asarray((0.0, 0.0))
    # Candidate generation is pre-behavior and cannot read future service.
    # It therefore keeps the reserve at gate; the conditional online schedule
    # transitions to stage only after RETURN_READY is observed.
    return "gate_until_return_ready", np.asarray((0.0, 0.0))


def _minimum_tracker_travel_steps(
    start: np.ndarray,
    target: np.ndarray,
    *,
    max_speed: float,
    max_vertical_speed: float,
    time_step: float,
) -> int:
    """Exact common-transducer travel count, used only to place departure."""

    positions = np.repeat(np.asarray(start, dtype=np.float64)[None, :], PHYSICAL_UAVS, axis=0)
    targets = np.repeat(np.asarray(target, dtype=np.float64)[None, :], PHYSICAL_UAVS, axis=0)
    active = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
    bound = (
        PHYSICAL_HORIZON
        * float(np.finfo(np.float32).eps)
        * float(max_speed)
        * float(time_step)
        * 4.0
    )
    for count in range(PHYSICAL_HORIZON + 1):
        if float(np.linalg.norm(positions[0] - targets[0])) <= bound:
            return count
        positions, _actions = _scenario7_nominal_position_step(
            positions,
            targets,
            active,
            max_speed=max_speed,
            max_vertical_speed=max_vertical_speed,
            time_step=time_step,
        )
    raise G0RealizationError("common tracker cannot reach oracle gate within H")


def certify_oracle_candidates(
    source: G0EpisodeSource,
    *,
    max_speed: float = 30.0,
    max_vertical_speed: float = 5.0,
    time_step: float = 1.0,
) -> OracleQualificationCertificate:
    """Evaluate exactly two sealed, shared-ledger, real-guard candidates."""

    if not (
        float(max_speed) == 30.0
        and float(max_vertical_speed) == 5.0
        and float(time_step) == 1.0
    ):
        raise G0RealizationError("oracle safety ledger requires frozen S7-S1 dynamics")
    return oracle_qualification_from_safety_ledger(
        source, build_oracle_safety_ledger(source)
    )



def validate_oracle_qualification(
    source: G0EpisodeSource,
    certificate: OracleQualificationCertificate,
    *,
    safety_ledger: OracleSafetyLedger | None = None,
    max_speed: float = 30.0,
    max_vertical_speed: float = 5.0,
    time_step: float = 1.0,
) -> None:
    expected = (
        oracle_qualification_from_safety_ledger(source, safety_ledger)
        if safety_ledger is not None
        else certify_oracle_candidates(
            source,
            max_speed=max_speed,
            max_vertical_speed=max_vertical_speed,
            time_step=time_step,
        )
    )
    if (
        certificate.to_primitive() != expected.to_primitive()
        or not certificate.passed
    ):
        raise G0RealizationError("oracle qualification is missing, forged, or failed")


def _oracle_candidate_trace(
    source: G0EpisodeSource,
    reserve: TargetLabel,
) -> tuple[OracleCandidateSafetyTrace, dict[str, Any]]:
    env = UAVSourceIdentifiabilityEnv(source, Cell.EVENT)
    try:
        env.reset()
        prestate = _complete_oracle_prestate(env)
        prestate_sha256 = sha256_json(prestate)
        labels = TARGET_LABELS
        reserve_row = labels.index(reserve)
        owner_row = labels.index(source.event.owner_target)
        stage_xyz = np.concatenate(
            (source.geometry.coordinate(reserve), [FIXED_ALTITUDE_M])
        )
        gate_xyz = np.concatenate(
            (source.geometry.gate(source.event.owner_target), [FIXED_ALTITUDE_M])
        )
        primary_xyz = np.concatenate(
            (source.geometry.coordinate(source.event.owner_target), [FIXED_ALTITUDE_M])
        )
        travel_steps = _minimum_tracker_travel_steps(
            stage_xyz,
            gate_xyz,
            max_speed=env.max_speed,
            max_vertical_speed=env.max_vertical_speed_mps,
            time_step=env.time_step,
        )
        latest_departure = int(source.event.onset) - int(travel_steps)
        roundoff_bound = max(
            float(travel_steps)
            * float(np.finfo(np.float32).eps)
            * float(env.max_speed)
            * float(env.time_step)
            * 4.0,
            float(np.finfo(np.float64).eps),
        )
        schedule_rows: list[list[list[float]]] = []
        records: list[OracleSafetyStepRecord] = []
        path_length = 0.0
        tracking_error = 0.0
        arrival: int | None = None
        arrival_error = math.inf
        hard_violations = int(latest_departure < 0)
        for step in range(PHYSICAL_HORIZON):
            if int(env.current_step) != step:
                raise G0RealizationError("candidate safety physical-step order drifted")
            active = env._active_mask_for_step(step)
            targets = np.stack(
                [
                    np.concatenate(
                        (source.geometry.coordinate(label), [FIXED_ALTITUDE_M])
                    )
                    for label in labels
                ]
            )
            schedule_name, _unused = _oracle_schedule_label(
                step=step,
                reserve=reserve,
                failed=source.event.owner_target,
                latest_departure=latest_departure,
                event=source.event,
            )
            if schedule_name == "stage":
                targets[reserve_row] = stage_xyz
            elif schedule_name in {"gate", "gate_until_return_ready"}:
                targets[reserve_row] = gate_xyz
            elif schedule_name == "primary":
                targets[reserve_row] = primary_xyz
            else:
                raise G0RealizationError("unregistered oracle target schedule state")
            positions = np.asarray(env.uav_positions, dtype=np.float64).copy()
            ownership = {
                str(handle): TargetLabel.parse(owner_target)
                for handle, owner_target in zip(
                    env._handles, source.assignment.row_to_target
                )
            }
            pre_action_context = _pre_action_context(
                env, ownership, reserve.key
            )
            if (
                arrival is None
                and step >= latest_departure
                and float(np.linalg.norm(positions[reserve_row] - gate_xyz))
                <= roundoff_bound
            ):
                arrival = step
                arrival_error = float(
                    np.linalg.norm(positions[reserve_row] - gate_xyz)
                )
            actions = g1_common_target_actions(
                physical_positions=positions,
                target_positions=targets,
                active_mask=active,
                max_speed=env.max_speed,
                max_vertical_speed=env.max_vertical_speed_mps,
                time_step=env.time_step,
            )
            transducer_evidence = _common_transducer_evidence(
                physical_positions=positions,
                target_positions=targets,
                active_mask=active,
                raw_action=actions,
            )
            record = env.step_oracle_safety(
                actions,
                candidate_id=reserve.key,
                ownership=ownership,
                pre_action_context=pre_action_context,
                common_transducer_evidence=transducer_evidence,
            )
            next_positions = record.next_uav_positions.array().astype(
                np.float64, copy=False
            )
            if not np.isfinite(actions).all() or np.any(np.abs(actions) > 1.0):
                hard_violations += 1
            if (
                np.any(next_positions[:, 0] < 0.0)
                or np.any(next_positions[:, 0] > source.geometry.map_width)
                or np.any(next_positions[:, 1] < 0.0)
                or np.any(next_positions[:, 1] > source.geometry.map_height)
                or not np.array_equal(
                    next_positions[:, 2],
                    np.full(PHYSICAL_UAVS, FIXED_ALTITUDE_M),
                )
            ):
                hard_violations += 1
            path_length += float(
                np.linalg.norm(
                    next_positions[reserve_row] - positions[reserve_row]
                )
            )
            if (
                source.event.onset
                <= step
                <= source.event.rejoin + RECOVERY_WINDOW_EXTENSION
            ):
                tracking_error += float(
                    np.linalg.norm(
                        next_positions[reserve_row] - targets[reserve_row]
                    )
                )
            schedule_rows.append(targets.tolist())
            records.append(record)
        if arrival is None:
            arrival = PHYSICAL_HORIZON + 1
            arrival_error = float(
                np.linalg.norm(
                    records[-1].next_uav_positions.array()[reserve_row] - gate_xyz
                )
            )
            hard_violations += 1
        primitive_steps = [record.to_primitive() for record in records]
        trace_sha256 = sha256_json(primitive_steps)
        return (
            OracleCandidateSafetyTrace(
                candidate_id=reserve.key,
                target_schedule_sha256=sha256_json(schedule_rows),
                common_prestate_sha256=prestate_sha256,
                steps=tuple(records),
                hard_violation_count=int(hard_violations),
                gate_arrival_time=int(arrival),
                gate_arrival_error=float(arrival_error),
                event_window_tracking_error=float(tracking_error),
                path_length=float(path_length),
                stage_coordinates=tuple(float(value) for value in stage_xyz[:2]),
                trace_sha256=trace_sha256,
            ),
            prestate,
        )
    finally:
        env.close()


def build_oracle_safety_ledger(source: G0EpisodeSource) -> OracleSafetyLedger:
    """Build the immutable two-candidate, service-blind real-guard ledger."""

    reserves = tuple(
        label for label in TARGET_LABELS if label.kind is TargetKind.STAGE
    )
    if len(reserves) != K_SEARCH:
        raise G0RealizationError("oracle candidate inventory is not exactly two")
    first, first_prestate = _oracle_candidate_trace(source, reserves[0])
    second, second_prestate = _oracle_candidate_trace(source, reserves[1])
    first_prestate_sha256 = sha256_json(first_prestate)
    second_prestate_sha256 = sha256_json(second_prestate)
    if (
        first_prestate != second_prestate
        or first_prestate_sha256 != second_prestate_sha256
    ):
        raise G0RealizationError("oracle candidates did not start from a common prestate")
    selected = min((first, second), key=lambda candidate: candidate.rank)
    provisional = OracleSafetyLedger(
        source_sha256=source.to_primitive()["sha256"],
        common_prestate=first_prestate,
        common_prestate_sha256=first_prestate_sha256,
        candidate_prestate_sha256=(
            first_prestate_sha256,
            second_prestate_sha256,
        ),
        channel_draw_schema=(),
        shared_channel_draw_blocks=(),
        candidates=(first, second),
        selected_candidate_id=selected.candidate_id,
        selected_rank=selected.rank,
        shared_action_method_sha256=oracle_safety_method_digests(),
        content_sha256="",
    )
    ledger = OracleSafetyLedger(
        **{
            **provisional.__dict__,
            "content_sha256": sha256_json(
                provisional.to_primitive(include_digest=False)
            ),
        }
    )
    validate_oracle_safety_ledger(source, ledger)
    return ledger


def _forbidden_oracle_safety_key(value: Any, path: str = "") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in _ORACLE_SAFETY_FORBIDDEN_TOKENS):
                return f"{path}/{key}"
            found = _forbidden_oracle_safety_key(item, f"{path}/{key}")
            if found is not None:
                return found
    elif isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            found = _forbidden_oracle_safety_key(item, f"{path}/{index}")
            if found is not None:
                return found
    return None


def _validate_record_branchpoint_and_transducer(
    source: G0EpisodeSource,
    common_prestate: Mapping[str, Any],
    record: OracleSafetyStepRecord,
    *,
    selected_candidate_id: str,
    expected_target_positions: np.ndarray,
    expected_rng_state_bindings: Mapping[str, Any] | None = None,
) -> None:
    context = _validate_pre_action_context_primitive(
        record.pre_action_context
    )
    expected_context = _expected_pre_action_context(
        source,
        common_prestate,
        physical_step=record.physical_step,
        selected_candidate_id=selected_candidate_id,
        rng_state_bindings=expected_rng_state_bindings,
    )
    if context != expected_context:
        raise G0RealizationError(
            "branchpoint lifecycle/RNG/channel evidence is not reconstructible"
        )
    current_mask = record.current_service_mask.array()
    executed_mask = record.executed_service_mask.array()
    if (
        executed_mask.shape != (PHYSICAL_UAVS,)
        or executed_mask.dtype != np.dtype(np.bool_)
        or not np.array_equal(executed_mask, current_mask)
    ):
        raise G0RealizationError("executed service-mask evidence drifted")
    transducer = _validate_common_transducer_evidence_primitive(
        record.common_transducer_evidence
    )
    if (
        not np.array_equal(
            _native_array_from_primitive(
                transducer["physical_positions"]
            ).array(),
            record.current_uav_positions.array(),
        )
        or not np.array_equal(
            _native_array_from_primitive(
                transducer["target_positions"]
            ).array(),
            np.asarray(expected_target_positions, dtype=np.float64),
        )
        or not np.array_equal(
            _native_array_from_primitive(transducer["active_mask"]).array(),
            executed_mask,
        )
        or not np.array_equal(
            _native_array_from_primitive(transducer["raw_action"]).array(),
            record.raw_candidate_action.array(),
        )
    ):
        raise G0RealizationError(
            "target schedule is not bound to the common transducer"
        )


def validate_oracle_safety_ledger(
    source: G0EpisodeSource,
    ledger: OracleSafetyLedger,
) -> OracleSafetyCertificate:
    """Reconstruct all admission facts from immutable primitive evidence."""

    if ledger.source_sha256 != source.to_primitive()["sha256"]:
        raise G0RealizationError("oracle safety ledger source binding failed")
    if ledger.content_sha256 != sha256_json(
        ledger.to_primitive(include_digest=False)
    ):
        raise G0RealizationError("oracle safety ledger content digest failed")
    if dict(ledger.shared_action_method_sha256) != oracle_safety_method_digests():
        raise G0RealizationError("oracle safety ledger did not use the real guard methods")
    if ledger.common_prestate_sha256 != sha256_json(ledger.common_prestate):
        raise G0RealizationError("common prestate digest failed")
    if ledger.candidate_prestate_sha256 != (
        ledger.common_prestate_sha256,
        ledger.common_prestate_sha256,
    ):
        raise G0RealizationError("candidate prestates are not byte-identical")
    channel_state = (
        ledger.common_prestate.get("rng_states", {}).get("_channel_rng")
    )
    expected_channel_state = _random_state_primitive(
        _namespace_random_state(source.geometry.episode_id, 3)
    )
    if channel_state != expected_channel_state:
        raise G0RealizationError("registered G1 channel RNG prestate failed")
    if ledger.channel_draw_schema != () or ledger.shared_channel_draw_blocks != ():
        raise G0RealizationError("deterministic inherited channel path must use empty tape")
    expected_ids = tuple(
        label.key for label in TARGET_LABELS if label.kind is TargetKind.STAGE
    )
    if tuple(candidate.candidate_id for candidate in ledger.candidates) != expected_ids:
        raise G0RealizationError("oracle ledger omitted or added a reserve candidate")
    common_rng_states = ledger.common_prestate.get("rng_states")
    if not isinstance(common_rng_states, Mapping):
        raise G0RealizationError("oracle common prestate omitted RNG states")
    expected_rng_state_bindings = _rng_state_bindings(common_rng_states)
    previous_candidates: list[OracleCandidateSafetyTrace] = []
    for candidate in ledger.candidates:
        if len(candidate.steps) != PHYSICAL_HORIZON:
            raise G0RealizationError("candidate did not advance exactly H steps")
        if candidate.common_prestate_sha256 != ledger.common_prestate_sha256:
            raise G0RealizationError("candidate trace is not bound to common prestate")
        previous_next: np.ndarray | None = None
        previous_velocity = np.zeros((PHYSICAL_UAVS, 3), dtype=np.float64)
        reserve = TargetLabel.parse(candidate.candidate_id)
        if reserve.kind is not TargetKind.STAGE:
            raise G0RealizationError("oracle candidate owner is not a reserve")
        reserve_row = TARGET_LABELS.index(reserve)
        stage_xyz = np.concatenate(
            (source.geometry.coordinate(reserve), [FIXED_ALTITUDE_M])
        )
        gate_xyz = np.concatenate(
            (source.geometry.gate(source.event.owner_target), [FIXED_ALTITUDE_M])
        )
        primary_xyz = np.concatenate(
            (source.geometry.coordinate(source.event.owner_target), [FIXED_ALTITUDE_M])
        )
        travel_steps = _minimum_tracker_travel_steps(
            stage_xyz,
            gate_xyz,
            max_speed=30.0,
            max_vertical_speed=5.0,
            time_step=1.0,
        )
        latest_departure = int(source.event.onset) - int(travel_steps)
        roundoff_bound = max(
            float(travel_steps)
            * float(np.finfo(np.float32).eps)
            * 30.0
            * 4.0,
            float(np.finfo(np.float64).eps),
        )
        reconstructed_arrival: int | None = None
        reconstructed_arrival_error = math.inf
        reconstructed_path_length = 0.0
        reconstructed_tracking_error = 0.0
        reconstructed_hard_violations = int(latest_departure < 0)
        reconstructed_schedule: list[list[list[float]]] = []
        for expected_step, record in enumerate(candidate.steps):
            primitive = record.to_primitive()
            if _forbidden_oracle_safety_key(primitive) is not None:
                raise G0RealizationError("oracle safety trace exposed behavioral information")
            if (
                record.physical_step != expected_step
                or record.candidate_id != candidate.candidate_id
            ):
                raise G0RealizationError("candidate physical-step identity drifted")
            current = record.current_uav_positions.array()
            current_velocity = record.current_uav_velocities.array()
            service_mask = record.current_service_mask.array()
            raw = record.raw_candidate_action.array()
            guarded = record.guarded_executed_action.array()
            next_positions = record.next_uav_positions.array()
            next_velocities = record.next_uav_velocities.array()
            if (
                current.shape != (PHYSICAL_UAVS, 3)
                or current_velocity.shape != (PHYSICAL_UAVS, 3)
                or service_mask.shape != (PHYSICAL_UAVS,)
                or service_mask.dtype != np.bool_
                or raw.shape != (PHYSICAL_UAVS, ACTION_DIM)
                or guarded.shape != (PHYSICAL_UAVS, 3)
                or next_positions.shape != (PHYSICAL_UAVS, 3)
                or next_velocities.shape != (PHYSICAL_UAVS, 3)
                or not all(
                    np.isfinite(item).all()
                    for item in (
                        current,
                        current_velocity,
                        raw,
                        guarded,
                        next_positions,
                        next_velocities,
                    )
                )
            ):
                raise G0RealizationError("candidate safety row shape/finite evidence failed")
            if np.any(np.abs(raw) > 1.0) or not np.array_equal(
                raw[:, 2], np.zeros(PHYSICAL_UAVS, dtype=raw.dtype)
            ):
                reconstructed_hard_violations += 1
            if not np.array_equal(raw[~service_mask], np.zeros_like(raw[~service_mask])):
                raise G0RealizationError("inactive lifecycle received candidate action")
            expected_mask = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
            expected_mask[TARGET_LABELS.index(source.event.owner_target)] = (
                source.event.active(expected_step, Cell.EVENT)
            )
            if not np.array_equal(service_mask, expected_mask):
                raise G0RealizationError("candidate service-mask schedule drifted")
            targets = np.stack(
                [
                    np.concatenate(
                        (source.geometry.coordinate(label), [FIXED_ALTITUDE_M])
                    )
                    for label in TARGET_LABELS
                ]
            )
            schedule_name, _unused = _oracle_schedule_label(
                step=expected_step,
                reserve=reserve,
                failed=source.event.owner_target,
                latest_departure=latest_departure,
                event=source.event,
            )
            if schedule_name == "stage":
                targets[reserve_row] = stage_xyz
            elif schedule_name in {"gate", "gate_until_return_ready"}:
                targets[reserve_row] = gate_xyz
            elif schedule_name == "primary":
                targets[reserve_row] = primary_xyz
            else:
                raise G0RealizationError("candidate target schedule is unregistered")
            _validate_record_branchpoint_and_transducer(
                source,
                ledger.common_prestate,
                record,
                selected_candidate_id=candidate.candidate_id,
                expected_target_positions=targets,
                expected_rng_state_bindings=expected_rng_state_bindings,
            )
            expected_raw = g1_common_target_actions(
                physical_positions=current,
                target_positions=targets,
                active_mask=expected_mask,
                max_speed=30.0,
                max_vertical_speed=5.0,
                time_step=1.0,
            )
            if not np.array_equal(raw, expected_raw):
                raise G0RealizationError("candidate raw tracker action was forged")
            if (
                reconstructed_arrival is None
                and expected_step >= latest_departure
                and float(np.linalg.norm(current[reserve_row] - gate_xyz))
                <= roundoff_bound
            ):
                reconstructed_arrival = expected_step
                reconstructed_arrival_error = float(
                    np.linalg.norm(current[reserve_row] - gate_xyz)
                )
            if previous_next is not None and not np.array_equal(current, previous_next):
                raise G0RealizationError("candidate physical recurrence failed")
            if not np.array_equal(current_velocity, previous_velocity):
                raise G0RealizationError("candidate velocity recurrence failed")
            expected_velocity = (next_positions - current)
            if not np.array_equal(next_velocities, expected_velocity):
                raise G0RealizationError("candidate next velocity is not physical delta")
            if not np.array_equal(next_positions[:, 2], current[:, 2]):
                raise G0RealizationError("candidate fixed-altitude recurrence failed")
            if (
                np.any(next_positions[:, 0] < 0.0)
                or np.any(next_positions[:, 0] > source.geometry.map_width)
                or np.any(next_positions[:, 1] < 0.0)
                or np.any(next_positions[:, 1] > source.geometry.map_height)
                or not np.array_equal(
                    next_positions[:, 2],
                    np.full(PHYSICAL_UAVS, FIXED_ALTITUDE_M),
                )
            ):
                reconstructed_hard_violations += 1
            reconstructed_path_length += float(
                np.linalg.norm(
                    next_positions[reserve_row] - current[reserve_row]
                )
            )
            if (
                source.event.onset
                <= expected_step
                <= source.event.rejoin + RECOVERY_WINDOW_EXTENSION
            ):
                reconstructed_tracking_error += float(
                    np.linalg.norm(
                        next_positions[reserve_row] - targets[reserve_row]
                    )
                )
            reconstructed_schedule.append(targets.tolist())
            if set(record.connections) != {"user", "uav", "uav_bs"}:
                raise G0RealizationError("native connection inventory is incomplete")
            connection_shapes = {
                "user": (PHYSICAL_UAVS, GROUND_USERS),
                "uav": (PHYSICAL_UAVS, PHYSICAL_UAVS),
                "uav_bs": (PHYSICAL_UAVS, GROUND_BASE_STATIONS),
            }
            for key, shape in connection_shapes.items():
                array = record.connections[key].array()
                if array.shape != shape or array.dtype != np.bool_:
                    raise G0RealizationError("native connection shape/dtype drifted")
            for capacity in record.exact_link_capacity_values_read_by_the_real_guard:
                capacity.capacity()
            if set(record.real_guard_intervention_or_violation_output) != {
                "checked_actions",
                "blocked_actions",
                "intervention_by_uav",
            }:
                raise G0RealizationError("real guard output schema drifted")
            if len(
                record.real_guard_intervention_or_violation_output[
                    "intervention_by_uav"
                ]
            ) != PHYSICAL_UAVS:
                raise G0RealizationError("real guard intervention inventory drifted")
            if record.shared_channel_draw_coordinate or record.shared_channel_draw_block:
                raise G0RealizationError("candidate used an unregistered channel RNG draw")
            previous_next = next_positions
            previous_velocity = next_velocities
        if reconstructed_arrival is None:
            reconstructed_arrival = PHYSICAL_HORIZON + 1
            reconstructed_arrival_error = float(
                np.linalg.norm(previous_next[reserve_row] - gate_xyz)
            )
            reconstructed_hard_violations += 1
        if (
            candidate.target_schedule_sha256 != sha256_json(reconstructed_schedule)
            or candidate.gate_arrival_time != reconstructed_arrival
            or candidate.gate_arrival_error != reconstructed_arrival_error
            or candidate.hard_violation_count != reconstructed_hard_violations
            or candidate.event_window_tracking_error
            != reconstructed_tracking_error
            or candidate.path_length != reconstructed_path_length
            or candidate.stage_coordinates
            != tuple(float(value) for value in stage_xyz[:2])
        ):
            raise G0RealizationError("candidate aggregate/ranking evidence was forged")
        if candidate.trace_sha256 != sha256_json(
            [record.to_primitive() for record in candidate.steps]
        ):
            raise G0RealizationError("candidate trace digest failed")
        if not all(math.isfinite(value) for value in candidate.rank):
            raise G0RealizationError("candidate ranking evidence is nonfinite")
        previous_candidates.append(candidate)
    assigned_labels = tuple(
        TargetLabel.parse(value) for value in source.assignment.row_to_target
    )
    unaffected_primaries = tuple(
        label
        for label in assigned_labels
        if label.kind is TargetKind.PRIMARY and label != source.event.owner_target
    )
    if (
        len(unaffected_primaries) != 5
        or any(assigned_labels.count(label) != 1 for label in unaffected_primaries)
        or any(
            TargetLabel.parse(candidate.candidate_id).kind is not TargetKind.STAGE
            for candidate in ledger.candidates
        )
    ):
        raise G0RealizationError("unaffected-primary/reserve ownership certificate failed")
    expected_selected = min(previous_candidates, key=lambda item: item.rank)
    if (
        ledger.selected_candidate_id != expected_selected.candidate_id
        or tuple(ledger.selected_rank) != expected_selected.rank
    ):
        raise G0RealizationError("sealed candidate ranking was forged")
    if sum(len(candidate.steps) for candidate in ledger.candidates) > 2 * PHYSICAL_HORIZON:
        raise G0RealizationError("oracle candidate transition ceiling exceeded")
    return OracleSafetyCertificate(
        ledger_sha256=ledger.content_sha256,
        selected_candidate_id=ledger.selected_candidate_id,
        candidate_trace_sha256=tuple(
            candidate.trace_sha256 for candidate in ledger.candidates
        ),
    )


def oracle_qualification_from_safety_ledger(
    source: G0EpisodeSource,
    ledger: OracleSafetyLedger,
) -> OracleQualificationCertificate:
    safety_certificate = validate_oracle_safety_ledger(source, ledger)
    rows: list[OracleCandidateEvidence] = []
    for candidate in ledger.candidates:
        rows.append(
            OracleCandidateEvidence(
                reserve_target=candidate.candidate_id,
                latest_departure=int(source.event.onset)
                - _minimum_tracker_travel_steps(
                    np.concatenate(
                        (
                            source.geometry.coordinate(candidate.candidate_id),
                            [FIXED_ALTITUDE_M],
                        )
                    ),
                    np.concatenate(
                        (
                            source.geometry.gate(source.event.owner_target),
                            [FIXED_ALTITUDE_M],
                        )
                    ),
                    max_speed=30.0,
                    max_vertical_speed=5.0,
                    time_step=1.0,
                ),
                gate_arrival_time=candidate.gate_arrival_time,
                gate_arrival_error=candidate.gate_arrival_error,
                gate_arrival_roundoff_bound=(
                    PHYSICAL_HORIZON
                    * float(np.finfo(np.float32).eps)
                    * 30.0
                    * 4.0
                ),
                hard_violation_count=candidate.hard_violation_count,
                event_window_tracking_error=candidate.event_window_tracking_error,
                path_length=candidate.path_length,
                stage_coordinates=candidate.stage_coordinates,
                physical_steps_advanced=len(candidate.steps),
                target_schedule_exact=True,
                action_support_valid=True,
                map_support_valid=True,
                candidate_complete=len(candidate.steps) == PHYSICAL_HORIZON,
                trace_sha256=candidate.trace_sha256,
            )
        )
    selected = min(rows, key=lambda item: item.rank)
    passed = bool(
        len(rows) == K_SEARCH
        and all(row.candidate_complete for row in rows)
        and ledger.selected_candidate_id == selected.reserve_target
    )
    return OracleQualificationCertificate(
        candidates=(rows[0], rows[1]),
        selected_reserve_target=selected.reserve_target,
        selected_rank=selected.rank,
        both_candidates_evaluated=True,
        exact_lexicographic_winner=True,
        future_channel_read_count=0,
        future_service_read_count=0,
        unaffected_primary_move_creates_vacancy=True,
        candidate_owner_is_reserve=True,
        shared_dynamics_action_safety_identity=(
            dict(ledger.shared_action_method_sha256) == oracle_safety_method_digests()
        ),
        candidate_count=K_SEARCH,
        complexity="O(H*K_search)",
        nested_rollout=False,
        replanning=False,
        tree_search=False,
        beam_search=False,
        mcts=False,
        adaptive_candidate_creation=False,
        passed=passed,
        oracle_safety_ledger_sha256=ledger.content_sha256,
        safety_certificate=safety_certificate,
    )


def _native_array_from_primitive(value: Any) -> _NativeArrayEvidence:
    if not isinstance(value, Mapping) or set(value) != {"dtype", "shape", "data_hex"}:
        raise G0RealizationError("native array primitive schema drifted")
    evidence = _NativeArrayEvidence(
        dtype=str(value["dtype"]),
        shape=tuple(int(item) for item in value["shape"]),
        data_hex=str(value["data_hex"]),
    )
    evidence.array()
    return evidence


def _draw_coordinate_from_primitive(value: Any) -> OracleSafetyDrawCoordinate:
    expected = {
        "physical_step",
        "channel_update_ordinal",
        "rng_operation",
        "shape",
        "dtype",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("channel draw coordinate schema drifted")
    return OracleSafetyDrawCoordinate(
        physical_step=int(value["physical_step"]),
        channel_update_ordinal=int(value["channel_update_ordinal"]),
        rng_operation=str(value["rng_operation"]),
        shape=tuple(int(item) for item in value["shape"]),
        dtype=str(value["dtype"]),
    )


def _guard_read_from_primitive(value: Any) -> OracleGuardCapacityRead:
    expected = {
        "guarded_uav",
        "node1_type",
        "node1_idx",
        "node2_type",
        "node2_idx",
        "capacity_dtype",
        "capacity_hex",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("guard capacity-read schema drifted")
    result = OracleGuardCapacityRead(
        guarded_uav=int(value["guarded_uav"]),
        node1_type=str(value["node1_type"]),
        node1_idx=int(value["node1_idx"]),
        node2_type=str(value["node2_type"]),
        node2_idx=int(value["node2_idx"]),
        capacity_dtype=str(value["capacity_dtype"]),
        capacity_hex=str(value["capacity_hex"]),
    )
    result.capacity()
    return result


def oracle_safety_step_from_primitive(value: Any) -> OracleSafetyStepRecord:
    if not isinstance(value, Mapping) or set(value) != _ORACLE_SAFETY_ALLOWED_STEP_KEYS:
        raise G0RealizationError("oracle safety step primitive schema drifted")
    connections = value["connections"]
    if not isinstance(connections, Mapping) or set(connections) != {
        "user",
        "uav",
        "uav_bs",
    }:
        raise G0RealizationError("oracle native connections primitive drifted")
    routing = value["routing_paths"]
    if not isinstance(routing, list):
        raise G0RealizationError("oracle routing primitive is not ordered")
    return OracleSafetyStepRecord(
        physical_step=int(value["physical_step"]),
        candidate_id=str(value["candidate_id"]),
        current_uav_positions=_native_array_from_primitive(
            value["current_uav_positions"]
        ),
        current_uav_velocities=_native_array_from_primitive(
            value["current_uav_velocities"]
        ),
        current_service_mask=_native_array_from_primitive(
            value["current_service_mask"]
        ),
        pre_action_context=_validate_pre_action_context_primitive(
            value["pre_action_context"]
        ),
        executed_service_mask=_native_array_from_primitive(
            value["executed_service_mask"]
        ),
        common_transducer_evidence=_validate_common_transducer_evidence_primitive(
            value["common_transducer_evidence"],
            recompute=False,
        ),
        raw_candidate_action=_native_array_from_primitive(
            value["raw_candidate_action"]
        ),
        shared_channel_draw_coordinate=tuple(
            _draw_coordinate_from_primitive(item)
            for item in value["shared_channel_draw_coordinate"]
        ),
        shared_channel_draw_block=tuple(
            str(item) for item in value["shared_channel_draw_block"]
        ),
        connections={
            str(key): _native_array_from_primitive(item)
            for key, item in connections.items()
        },
        routing_paths=tuple(_json_safe(item) for item in routing),
        exact_link_capacity_values_read_by_the_real_guard=tuple(
            _guard_read_from_primitive(item)
            for item in value[
                "exact_link_capacity_values_read_by_the_real_guard"
            ]
        ),
        real_guard_intervention_or_violation_output=_json_safe(
            value["real_guard_intervention_or_violation_output"]
        ),
        guarded_executed_action=_native_array_from_primitive(
            value["guarded_executed_action"]
        ),
        next_uav_positions=_native_array_from_primitive(
            value["next_uav_positions"]
        ),
        next_uav_velocities=_native_array_from_primitive(
            value["next_uav_velocities"]
        ),
    )


def oracle_safety_trace_from_primitive(value: Any) -> OracleCandidateSafetyTrace:
    expected = {
        "candidate_id",
        "target_schedule_sha256",
        "common_prestate_sha256",
        "steps",
        "hard_violation_count",
        "gate_arrival_time",
        "gate_arrival_error",
        "event_window_tracking_error",
        "path_length",
        "stage_coordinates",
        "trace_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("oracle candidate trace schema drifted")
    return OracleCandidateSafetyTrace(
        candidate_id=str(value["candidate_id"]),
        target_schedule_sha256=str(value["target_schedule_sha256"]),
        common_prestate_sha256=str(value["common_prestate_sha256"]),
        steps=tuple(
            oracle_safety_step_from_primitive(item) for item in value["steps"]
        ),
        hard_violation_count=int(value["hard_violation_count"]),
        gate_arrival_time=int(value["gate_arrival_time"]),
        gate_arrival_error=float(value["gate_arrival_error"]),
        event_window_tracking_error=float(value["event_window_tracking_error"]),
        path_length=float(value["path_length"]),
        stage_coordinates=tuple(float(item) for item in value["stage_coordinates"]),
        trace_sha256=str(value["trace_sha256"]),
    )


def oracle_behavioral_execution_from_primitive(
    value: Any,
) -> OracleBehavioralExecution:
    expected = {
        "selected_candidate_id",
        "return_ready_step",
        "steps",
        "target_schedule",
        "pre_action_weakest_service",
        "trace_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("oracle behavioral execution schema drifted")
    return_ready = value["return_ready_step"]
    if return_ready is not None:
        return_ready = int(return_ready)
        if not 0 <= return_ready < PHYSICAL_HORIZON:
            raise G0RealizationError("RETURN_READY step is outside H")
    result = OracleBehavioralExecution(
        selected_candidate_id=str(value["selected_candidate_id"]),
        return_ready_step=return_ready,
        steps=tuple(
            oracle_safety_step_from_primitive(item) for item in value["steps"]
        ),
        target_schedule=_native_array_from_primitive(value["target_schedule"]),
        pre_action_weakest_service=_native_array_from_primitive(
            value["pre_action_weakest_service"]
        ),
        trace_sha256=str(value["trace_sha256"]),
    )
    targets = result.target_schedule.array()
    weakest = result.pre_action_weakest_service.array()
    if targets.shape != (PHYSICAL_HORIZON, PHYSICAL_UAVS, 3):
        raise G0RealizationError("behavioral target schedule shape drifted")
    if weakest.shape != (PHYSICAL_HORIZON,) or not np.isfinite(weakest).all():
        raise G0RealizationError("behavioral pre-action service evidence drifted")
    expected_digest = sha256_json(
        {
            "selected_candidate_id": result.selected_candidate_id,
            "return_ready_step": result.return_ready_step,
            "steps": [step.to_primitive() for step in result.steps],
            "target_schedule": result.target_schedule.to_primitive(),
            "pre_action_weakest_service": (
                result.pre_action_weakest_service.to_primitive()
            ),
        }
    )
    if result.trace_sha256 != expected_digest:
        raise G0RealizationError("behavioral execution digest drifted")
    return result


def oracle_safety_ledger_from_primitive(value: Any) -> OracleSafetyLedger:
    expected = {
        "source_sha256",
        "common_prestate",
        "common_prestate_sha256",
        "candidate_prestate_sha256",
        "channel_draw_schema",
        "shared_channel_draw_blocks",
        "candidates",
        "selected_candidate_id",
        "selected_rank",
        "shared_action_method_sha256",
        "registration_order",
        "K_search",
        "physical_horizon",
        "hypothetical_candidate_transitions",
        "content_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("oracle safety ledger primitive schema drifted")
    if (
        int(value["K_search"]) != K_SEARCH
        or int(value["physical_horizon"]) != PHYSICAL_HORIZON
        or int(value["hypothetical_candidate_transitions"])
        > 2 * PHYSICAL_HORIZON
    ):
        raise G0RealizationError("oracle safety ledger complexity inventory drifted")
    if list(value["registration_order"]) != [
        "freeze_common_prestate",
        "freeze_channel_draw_schema",
        "materialize_shared_channel_tape",
        "advance_each_candidate_once",
        "seal_both_candidate_traces",
        "rank_sealed_trace_keys_only",
        "behavioral_service_after_selection",
    ]:
        raise G0RealizationError("oracle safety registration order drifted")
    candidates = tuple(
        oracle_safety_trace_from_primitive(item) for item in value["candidates"]
    )
    if len(candidates) != 2:
        raise G0RealizationError("oracle safety ledger requires exactly two candidates")
    return OracleSafetyLedger(
        source_sha256=str(value["source_sha256"]),
        common_prestate=_json_safe(value["common_prestate"]),
        common_prestate_sha256=str(value["common_prestate_sha256"]),
        candidate_prestate_sha256=tuple(
            str(item) for item in value["candidate_prestate_sha256"]
        ),
        channel_draw_schema=tuple(
            _draw_coordinate_from_primitive(item)
            for item in value["channel_draw_schema"]
        ),
        shared_channel_draw_blocks=tuple(
            str(item) for item in value["shared_channel_draw_blocks"]
        ),
        candidates=(candidates[0], candidates[1]),
        selected_candidate_id=str(value["selected_candidate_id"]),
        selected_rank=tuple(float(item) for item in value["selected_rank"]),
        shared_action_method_sha256={
            str(key): str(item)
            for key, item in value["shared_action_method_sha256"].items()
        },
        content_sha256=str(value["content_sha256"]),
    )


def validate_oracle_safety_primitive(
    source: G0EpisodeSource,
    primitive: Mapping[str, Any],
) -> OracleSafetyCertificate:
    return validate_oracle_safety_ledger(
        source, oracle_safety_ledger_from_primitive(primitive)
    )


def validate_oracle_behavioral_replay(
    ledger: OracleSafetyLedger,
    registered_trace: Sequence[OracleSafetyStepRecord | Mapping[str, Any]],
    replay_trace: Sequence[OracleSafetyStepRecord | Mapping[str, Any]],
) -> OracleSafetyCertificate:
    """Compare two independent selected-behavior safety projections byte-for-byte."""

    registered = tuple(
        record
        if isinstance(record, OracleSafetyStepRecord)
        else oracle_safety_step_from_primitive(record)
        for record in registered_trace
    )
    replay = tuple(
        record
        if isinstance(record, OracleSafetyStepRecord)
        else oracle_safety_step_from_primitive(record)
        for record in replay_trace
    )
    if len(registered) != PHYSICAL_HORIZON or len(replay) != PHYSICAL_HORIZON:
        raise G0RealizationError("behavioral replay is not one complete H trajectory")
    if [item.to_primitive() for item in registered] != [
        item.to_primitive() for item in replay
    ]:
        raise G0RealizationError("independent behavioral replay differs byte-for-byte")
    previous_next: np.ndarray | None = None
    for expected_step, record in enumerate(registered):
        if (
            record.physical_step != expected_step
            or record.candidate_id != ledger.selected_candidate_id
            or record.shared_channel_draw_coordinate != ledger.channel_draw_schema
            or record.shared_channel_draw_block != ledger.shared_channel_draw_blocks
        ):
            raise G0RealizationError("behavioral replay identity or shared tape mismatch")
        if _forbidden_oracle_safety_key(record.to_primitive()) is not None:
            raise G0RealizationError("behavioral replay safety projection leaked metrics")
        current = record.current_uav_positions.array()
        next_positions = record.next_uav_positions.array()
        if previous_next is not None and not np.array_equal(current, previous_next):
            raise G0RealizationError("behavioral replay physical recurrence failed")
        if not np.array_equal(record.next_uav_velocities.array(), next_positions - current):
            raise G0RealizationError("behavioral replay velocity recurrence failed")
        for capacity in record.exact_link_capacity_values_read_by_the_real_guard:
            capacity.capacity()
        previous_next = next_positions
    digest = sha256_json([record.to_primitive() for record in registered])
    return OracleSafetyCertificate(
        ledger_sha256=ledger.content_sha256,
        selected_candidate_id=ledger.selected_candidate_id,
        candidate_trace_sha256=tuple(
            candidate.trace_sha256 for candidate in ledger.candidates
        ),
        behavioral_replay_sha256=digest,
    )


def _validate_branch_safety_trace(
    ledger: OracleSafetyLedger,
    records: Sequence[OracleSafetyStepRecord],
) -> None:
    if len(records) != PHYSICAL_HORIZON:
        raise G0RealizationError("branch replay is not one complete H trajectory")
    previous_next: np.ndarray | None = None
    for expected_step, record in enumerate(records):
        if (
            record.physical_step != expected_step
            or record.candidate_id != ledger.selected_candidate_id
            or record.shared_channel_draw_coordinate != ledger.channel_draw_schema
            or record.shared_channel_draw_block != ledger.shared_channel_draw_blocks
        ):
            raise G0RealizationError("branch replay identity or shared tape mismatch")
        if _forbidden_oracle_safety_key(record.to_primitive()) is not None:
            raise G0RealizationError("branch replay leaked behavioral metrics")
        current = record.current_uav_positions.array()
        current_velocity = record.current_uav_velocities.array()
        next_positions = record.next_uav_positions.array()
        next_velocity = record.next_uav_velocities.array()
        if previous_next is not None and not np.array_equal(current, previous_next):
            raise G0RealizationError("branch replay physical recurrence failed")
        if expected_step == 0 and not np.array_equal(
            current_velocity, np.zeros_like(current_velocity)
        ):
            raise G0RealizationError("branch replay initial velocity drifted")
        if not np.array_equal(next_velocity, next_positions - current):
            raise G0RealizationError("branch replay velocity recurrence failed")
        if set(record.connections) != {"user", "uav", "uav_bs"}:
            raise G0RealizationError("branch replay connection inventory drifted")
        for capacity in record.exact_link_capacity_values_read_by_the_real_guard:
            capacity.capacity()
        previous_next = next_positions


def _selected_reserve_storage_row(
    source: G0EpisodeSource,
    selected_candidate_id: str,
) -> int:
    rows = tuple(str(item) for item in source.assignment.row_to_target)
    try:
        return rows.index(str(selected_candidate_id))
    except ValueError as error:
        raise G0RealizationError("selected reserve is absent from assignment") from error


def _target_internal_row(target: TargetLabel | str) -> int:
    """Resolve one lifecycle owner in the environment's internal target order."""

    parsed = target if isinstance(target, TargetLabel) else TargetLabel.parse(target)
    try:
        return TARGET_LABELS.index(parsed)
    except ValueError as error:
        raise G0RealizationError("lifecycle owner is absent from internal order") from error


def _expected_behavioral_target_schedule(
    source: G0EpisodeSource,
    ledger: OracleSafetyLedger,
    return_ready_step: int | None,
) -> np.ndarray:
    selected = TargetLabel.parse(ledger.selected_candidate_id)
    selected_row = _selected_reserve_storage_row(source, selected.key)
    qualification = oracle_qualification_from_safety_ledger(source, ledger)
    candidate = next(
        item for item in qualification.candidates if item.reserve_target == selected.key
    )
    rows = np.stack(
        [
            np.concatenate(
                (
                    source.geometry.coordinate(TargetLabel.parse(label)),
                    [FIXED_ALTITUDE_M],
                )
            )
            for label in source.assignment.row_to_target
        ]
    )
    schedule = np.repeat(rows[None, :, :], PHYSICAL_HORIZON, axis=0)
    gate = np.concatenate(
        (source.geometry.gate(source.event.owner_target), [FIXED_ALTITUDE_M])
    )
    primary = np.concatenate(
        (source.geometry.coordinate(source.event.owner_target), [FIXED_ALTITUDE_M])
    )
    stage = np.concatenate(
        (source.geometry.coordinate(selected), [FIXED_ALTITUDE_M])
    )
    for step in range(PHYSICAL_HORIZON):
        if step < candidate.latest_departure:
            target = stage
        elif step < source.event.onset:
            target = gate
        elif step < source.event.rejoin:
            target = primary
        elif return_ready_step is None or step < return_ready_step:
            target = gate
        else:
            target = stage
        schedule[step, selected_row] = target
    return schedule


def _validate_behavioral_transducer_binding(
    source: G0EpisodeSource,
    ledger: OracleSafetyLedger,
    execution: OracleBehavioralExecution,
) -> None:
    schedule = execution.target_schedule.array()
    if schedule.shape != (PHYSICAL_HORIZON, PHYSICAL_UAVS, 3):
        raise G0RealizationError("behavioral target schedule shape drifted")
    common_rng_states = ledger.common_prestate.get("rng_states")
    if not isinstance(common_rng_states, Mapping):
        raise G0RealizationError("oracle common prestate omitted RNG states")
    expected_rng_state_bindings = _rng_state_bindings(common_rng_states)
    for step, record in enumerate(execution.steps):
        targets_internal = np.zeros((PHYSICAL_UAVS, 3), dtype=np.float64)
        targets_internal[source.geometry.slot_to_target] = schedule[step]
        _validate_record_branchpoint_and_transducer(
            source,
            ledger.common_prestate,
            record,
            selected_candidate_id=ledger.selected_candidate_id,
            expected_target_positions=targets_internal,
            expected_rng_state_bindings=expected_rng_state_bindings,
        )


def _derive_return_ready_step(
    source: G0EpisodeSource,
    execution: OracleBehavioralExecution,
) -> int | None:
    owner_storage = source.assignment.row_to_target.index(
        source.event.owner_target.key
    )
    initial_owner_handle = initial_lifecycle_handles(source)[owner_storage]
    replacement_handle = replacement_lifecycle_handle(
        source, initial_owner_handle
    )
    primary = source.geometry.coordinate(source.event.owner_target)
    weakest = execution.pre_action_weakest_service.array()
    for step in range(source.event.rejoin + 1, PHYSICAL_HORIZON):
        current_context = _validate_pre_action_context_primitive(
            execution.steps[step].pre_action_context
        )
        previous_context = _validate_pre_action_context_primitive(
            execution.steps[step - 1].pre_action_context
        )
        if (
            current_context["event_owner_handle"] != replacement_handle
            or previous_context["event_owner_handle"] != replacement_handle
            or int(current_context["event_owner_epoch"]) != 1
            or int(previous_context["event_owner_epoch"]) != 1
        ):
            raise G0RealizationError(
                "RETURN_READY lifecycle owner/epoch is not reconstructed"
            )
        current_rows = {
            row["handle"]: row
            for row in current_context["lifecycle_owner_to_internal"]
        }
        previous_rows = {
            row["handle"]: row
            for row in previous_context["lifecycle_owner_to_internal"]
        }
        if replacement_handle not in current_rows or replacement_handle not in previous_rows:
            raise G0RealizationError("RETURN_READY replacement lifecycle is absent")
        current_owner_row = int(current_rows[replacement_handle]["internal_row"])
        previous_owner_row = int(previous_rows[replacement_handle]["internal_row"])
        current = execution.steps[step].current_uav_positions.array()
        previous = execution.steps[step - 1].current_uav_positions.array()
        mask = execution.steps[step].executed_service_mask.array()
        previous_mask = execution.steps[step - 1].executed_service_mask.array()
        if (
            bool(mask[current_owner_row])
            and bool(previous_mask[previous_owner_row])
            and np.array_equal(current[current_owner_row, :2], primary)
            and np.array_equal(previous[previous_owner_row, :2], primary)
            and float(weakest[step]) >= SERVICE_TARGET
        ):
            return step
    return None


def validate_oracle_branch_aware_replay(
    source: G0EpisodeSource,
    ledger: OracleSafetyLedger,
    prebehavior_self_replay: OracleCandidateSafetyTrace | Mapping[str, Any],
    behavioral_execution: OracleBehavioralExecution | Mapping[str, Any],
    behavioral_self_replay: OracleBehavioralExecution | Mapping[str, Any],
) -> OracleSafetyCertificate:
    """Reconstruct the frozen prefix/branchpoint/post-R replay certificate."""

    validate_oracle_safety_ledger(source, ledger)
    selected = next(
        candidate
        for candidate in ledger.candidates
        if candidate.candidate_id == ledger.selected_candidate_id
    )
    prebehavior = (
        prebehavior_self_replay
        if isinstance(prebehavior_self_replay, OracleCandidateSafetyTrace)
        else oracle_safety_trace_from_primitive(prebehavior_self_replay)
    )
    behavior = oracle_behavioral_execution_from_primitive(
        behavioral_execution.to_primitive()
        if isinstance(behavioral_execution, OracleBehavioralExecution)
        else behavioral_execution
    )
    behavior_replay = oracle_behavioral_execution_from_primitive(
        behavioral_self_replay.to_primitive()
        if isinstance(behavioral_self_replay, OracleBehavioralExecution)
        else behavioral_self_replay
    )
    if prebehavior.to_primitive() != selected.to_primitive():
        raise G0RealizationError("prebehavior self-replay differs byte-for-byte")
    if behavior.to_primitive() != behavior_replay.to_primitive():
        raise G0RealizationError("behavioral branch self-replay differs byte-for-byte")
    if (
        behavior.selected_candidate_id != ledger.selected_candidate_id
        or behavior_replay.selected_candidate_id != ledger.selected_candidate_id
    ):
        raise G0RealizationError("behavioral replay reselected the reserve candidate")
    _validate_branch_safety_trace(ledger, selected.steps)
    _validate_branch_safety_trace(ledger, behavior.steps)
    _validate_branch_safety_trace(ledger, behavior_replay.steps)
    _validate_behavioral_transducer_binding(source, ledger, behavior)
    _validate_behavioral_transducer_binding(source, ledger, behavior_replay)
    derived_return_ready = _derive_return_ready_step(source, behavior)
    if behavior.return_ready_step != derived_return_ready:
        raise G0RealizationError("stored RETURN_READY step is not causally reconstructed")
    if behavior_replay.return_ready_step != derived_return_ready:
        raise G0RealizationError("behavioral self-replay RETURN_READY step drifted")
    expected_targets = _expected_behavioral_target_schedule(
        source, ledger, derived_return_ready
    )
    if not np.array_equal(behavior.target_schedule.array(), expected_targets):
        raise G0RealizationError("behavioral target switch is early, late, or wrong")
    prefix_end = (
        PHYSICAL_HORIZON if derived_return_ready is None else derived_return_ready
    )
    for step in range(prefix_end):
        if selected.steps[step].to_primitive() != behavior.steps[step].to_primitive():
            raise G0RealizationError(
                f"pre-RETURN_READY prefix differs at physical step {step}"
            )
    selected_internal_row = _target_internal_row(ledger.selected_candidate_id)
    if derived_return_ready is None:
        if [item.to_primitive() for item in selected.steps] != [
            item.to_primitive() for item in behavior.steps
        ]:
            raise G0RealizationError("R=NONE replay is not fully identical")
    else:
        step = derived_return_ready
        pre_record = selected.steps[step]
        behavior_record = behavior.steps[step]
        for name in (
            "physical_step",
            "candidate_id",
            "current_uav_positions",
            "current_uav_velocities",
            "current_service_mask",
            "pre_action_context",
            "executed_service_mask",
            "shared_channel_draw_coordinate",
            "shared_channel_draw_block",
        ):
            left = getattr(pre_record, name)
            right = getattr(behavior_record, name)
            left_value = left.to_primitive() if hasattr(left, "to_primitive") else left
            right_value = right.to_primitive() if hasattr(right, "to_primitive") else right
            if left_value != right_value:
                raise G0RealizationError("step-R pre-action branchpoint identity failed")
        pre_action = pre_record.raw_candidate_action.array()
        behavior_action = behavior_record.raw_candidate_action.array()
        pre_transducer = _validate_common_transducer_evidence_primitive(
            pre_record.common_transducer_evidence
        )
        behavior_transducer = _validate_common_transducer_evidence_primitive(
            behavior_record.common_transducer_evidence
        )
        for name in (
            "transducer_source_sha256",
            "row_order",
            "physical_positions",
            "active_mask",
            "max_speed",
            "max_vertical_speed",
            "time_step",
        ):
            if pre_transducer[name] != behavior_transducer[name]:
                raise G0RealizationError(
                    "step-R common transducer pre-action inputs drifted"
                )
        pre_targets = _native_array_from_primitive(
            pre_transducer["target_positions"]
        ).array()
        behavior_targets = _native_array_from_primitive(
            behavior_transducer["target_positions"]
        ).array()
        unaffected = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
        unaffected[selected_internal_row] = False
        if (
            not np.array_equal(pre_targets[unaffected], behavior_targets[unaffected])
            or np.array_equal(
                pre_targets[selected_internal_row],
                behavior_targets[selected_internal_row],
            )
        ):
            raise G0RealizationError(
                "RETURN_READY target switch is not isolated to the reserve"
            )
        if not np.array_equal(pre_action[unaffected], behavior_action[unaffected]):
            raise G0RealizationError("RETURN_READY changed an unaffected owner action")
        # The selected target changes before action construction at R.  The
        # resulting raw action is allowed to remain byte-identical through a
        # coincident direction, action clipping, or the unchanged real guard;
        # the first differing action byte is not the RETURN_READY predicate.
    for step, (pre_record, behavior_record) in enumerate(
        zip(selected.steps, behavior.steps)
    ):
        if (
            pre_record.physical_step != behavior_record.physical_step
            or pre_record.candidate_id != behavior_record.candidate_id
            or pre_record.shared_channel_draw_coordinate
            != behavior_record.shared_channel_draw_coordinate
            or pre_record.shared_channel_draw_block
            != behavior_record.shared_channel_draw_block
        ):
            raise G0RealizationError(
                f"shared exogenous ledger differs at physical step {step}"
            )
    return OracleSafetyCertificate(
        ledger_sha256=ledger.content_sha256,
        selected_candidate_id=ledger.selected_candidate_id,
        candidate_trace_sha256=tuple(
            candidate.trace_sha256 for candidate in ledger.candidates
        ),
        behavioral_replay_sha256=behavior.trace_sha256,
        return_ready_step=derived_return_ready,
        prefix_identity_ok=True,
        branchpoint_identity_ok=True,
        shared_ledger_identity_ok=True,
        prebehavior_self_replay_ok=True,
        behavioral_self_replay_ok=True,
        target_switch_ok=True,
        safety_guard_ok=True,
        replay_ok=True,
    )


def validate_oracle_branch_aware_replay_primitive(
    source: G0EpisodeSource,
    ledger: OracleSafetyLedger,
    primitive: Mapping[str, Any],
) -> OracleSafetyCertificate:
    expected = {
        "schema_version",
        "ledger_sha256",
        "selected_candidate_id",
        "prebehavior_self_replay",
        "behavioral_execution",
        "behavioral_self_replay",
        "certificate",
    }
    if not isinstance(primitive, Mapping) or set(primitive) != expected:
        raise G0RealizationError("branch-aware replay artifact schema drifted")
    if (
        int(primitive["schema_version"]) != 1
        or primitive["ledger_sha256"] != ledger.content_sha256
        or primitive["selected_candidate_id"] != ledger.selected_candidate_id
    ):
        raise G0RealizationError("branch-aware replay artifact identity drifted")
    certificate = validate_oracle_branch_aware_replay(
        source,
        ledger,
        primitive["prebehavior_self_replay"],
        primitive["behavioral_execution"],
        primitive["behavioral_self_replay"],
    )
    if primitive["certificate"] != certificate.to_primitive():
        raise G0RealizationError("branch-aware replay certificate was forged")
    return certificate


def build_proof_episode_validity(
    source: G0EpisodeSource,
    safety_primitive: Mapping[str, Any],
    replay_primitive: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Proof-only public entry; derives validity rather than accepting a flag."""

    try:
        certificate = validate_oracle_safety_primitive(source, safety_primitive)
        replay_certificate = None
        if replay_primitive is not None:
            ledger = oracle_safety_ledger_from_primitive(safety_primitive)
            replay_certificate = validate_oracle_branch_aware_replay_primitive(
                source, ledger, replay_primitive
            )
    except (G0RealizationError, KeyError, TypeError, ValueError) as error:
        return {
            "operational_valid": False,
            "errors": [f"oracle_safety:{type(error).__name__}:{error}"],
            "result_branch": INVALID_BRANCH,
        }
    return {
        "operational_valid": True,
        "errors": [],
        "result_branch": None,
        "oracle_safety_certificate": certificate.to_primitive(),
        "oracle_replay_certificate": (
            None if replay_certificate is None else replay_certificate.to_primitive()
        ),
    }


def analyze_proof_fixture(
    source: G0EpisodeSource,
    safety_primitive: Mapping[str, Any],
    replay_primitive: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Public readiness analyzer; never emits a scientific branch for valid proof data."""

    reconstructed = build_proof_episode_validity(
        source, safety_primitive, replay_primitive
    )
    return {
        "proof_only": True,
        "operational_valid": bool(reconstructed["operational_valid"]),
        "operational_errors": list(reconstructed["errors"]),
        "result_branch": reconstructed["result_branch"],
    }


@dataclass(frozen=True)
class LifecycleBoundaryEvent:
    kind: str
    physical_step: int
    previous_handle: str
    current_handle: str | None
    owner_target: str

    def to_primitive(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "physical_step": int(self.physical_step),
            "previous_handle": self.previous_handle,
            "current_handle": self.current_handle,
            "owner_target": self.owner_target,
        }


@dataclass(frozen=True)
class G0Transition:
    physical_step: int
    delivered_user_rates_mbps: np.ndarray
    executed_action_mask: np.ndarray
    raw_actions: np.ndarray
    positions_before: np.ndarray
    positions_after: np.ndarray
    actual_velocities: np.ndarray
    backhaul_guard_blocked_actions: int
    boundary_events: tuple[LifecycleBoundaryEvent, ...]
    terminated: bool
    truncated: bool

    def __post_init__(self) -> None:
        arrays = (
            ("delivered_user_rates_mbps", self.delivered_user_rates_mbps, (GROUND_USERS,), np.float64),
            ("executed_action_mask", self.executed_action_mask, (PHYSICAL_UAVS,), np.bool_),
            ("raw_actions", self.raw_actions, (PHYSICAL_UAVS, ACTION_DIM), np.float32),
            ("positions_before", self.positions_before, (PHYSICAL_UAVS, 3), np.float64),
            ("positions_after", self.positions_after, (PHYSICAL_UAVS, 3), np.float64),
            ("actual_velocities", self.actual_velocities, (PHYSICAL_UAVS, 3), np.float64),
        )
        for name, value, shape, dtype in arrays:
            array = np.asarray(value, dtype=dtype)
            if array.shape != shape or (
                dtype is not np.bool_ and not np.isfinite(array).all()
            ):
                raise G0RealizationError(f"transition {name} invariant failed")
            object.__setattr__(self, name, _readonly_array(array, dtype=dtype))


def _namespace_random_state(seed: int, namespace: int) -> np.random.RandomState:
    word = np.random.SeedSequence([int(seed), int(namespace)]).generate_state(1)[0]
    return np.random.RandomState(int(word))


def _random_state_primitive(random_state: np.random.RandomState) -> dict[str, Any]:
    algorithm, keys, position, has_gauss, cached_gaussian = random_state.get_state()
    return {
        "algorithm": str(algorithm),
        "keys": _NativeArrayEvidence.from_array(keys).to_primitive(),
        "position": int(position),
        "has_gauss": int(has_gauss),
        "cached_gaussian": float(cached_gaussian),
    }


def _validate_random_state_primitive(value: Any) -> dict[str, Any]:
    expected = {"algorithm", "keys", "position", "has_gauss", "cached_gaussian"}
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("branchpoint RNG-state schema drifted")
    keys = _native_array_from_primitive(value["keys"])
    key_array = keys.array()
    if (
        str(value["algorithm"]) != "MT19937"
        or key_array.shape != (624,)
        or key_array.dtype != np.dtype(np.uint32)
        or not 0 <= int(value["position"]) <= 624
        or int(value["has_gauss"]) not in (0, 1)
        or not math.isfinite(float(value["cached_gaussian"]))
    ):
        raise G0RealizationError("branchpoint RNG-state primitive is invalid")
    return {
        "algorithm": "MT19937",
        "keys": keys.to_primitive(),
        "position": int(value["position"]),
        "has_gauss": int(value["has_gauss"]),
        "cached_gaussian": float(value["cached_gaussian"]),
    }


def _validate_pre_action_context_primitive(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _PRE_ACTION_CONTEXT_KEYS:
        raise G0RealizationError("branchpoint pre-action context schema drifted")
    physical_step = int(value["physical_step"])
    if not 0 <= physical_step < PHYSICAL_HORIZON:
        raise G0RealizationError("branchpoint physical step is outside H")

    lifecycle_value = value["lifecycle_owner_to_internal"]
    if not isinstance(lifecycle_value, list) or len(lifecycle_value) != PHYSICAL_UAVS:
        raise G0RealizationError("branchpoint lifecycle inventory is incomplete")
    lifecycle: list[dict[str, Any]] = []
    for item in lifecycle_value:
        if not isinstance(item, Mapping) or set(item) != _LIFECYCLE_CONTEXT_ROW_KEYS:
            raise G0RealizationError("branchpoint lifecycle row schema drifted")
        label = TargetLabel.parse(str(item["owner_target"]))
        row = {
            "handle": str(item["handle"]),
            "epoch": int(item["epoch"]),
            "internal_row": int(item["internal_row"]),
            "owner_target": label.key,
        }
        if not row["handle"] or row["epoch"] not in (0, 1):
            raise G0RealizationError("branchpoint lifecycle identity is invalid")
        lifecycle.append(row)
    if (
        [row["internal_row"] for row in lifecycle] != list(range(PHYSICAL_UAVS))
        or len({row["handle"] for row in lifecycle}) != PHYSICAL_UAVS
        or len({row["owner_target"] for row in lifecycle}) != PHYSICAL_UAVS
    ):
        raise G0RealizationError("branchpoint lifecycle ordering is ambiguous")

    event_owner_handle = str(value["event_owner_handle"])
    event_owner_epoch = int(value["event_owner_epoch"])
    selected_reserve_handle = str(value["selected_reserve_handle"])
    selected_target = TargetLabel.parse(
        str(value["selected_reserve_original_target"])
    )
    if selected_target.kind is not TargetKind.STAGE:
        raise G0RealizationError("branchpoint selected owner is not a reserve")
    by_handle = {row["handle"]: row for row in lifecycle}
    if (
        event_owner_handle not in by_handle
        or by_handle[event_owner_handle]["epoch"] != event_owner_epoch
        or selected_reserve_handle not in by_handle
        or by_handle[selected_reserve_handle]["owner_target"] != selected_target.key
        or selected_reserve_handle == event_owner_handle
    ):
        raise G0RealizationError("branchpoint owner/epoch identity is inconsistent")

    survivor_value = value["survivor_ownership"]
    if not isinstance(survivor_value, list) or len(survivor_value) != 6:
        raise G0RealizationError("branchpoint survivor-controller state is incomplete")
    survivor: list[dict[str, Any]] = []
    for item in survivor_value:
        if not isinstance(item, Mapping) or set(item) != _LIFECYCLE_CONTEXT_ROW_KEYS:
            raise G0RealizationError("branchpoint survivor row schema drifted")
        canonical = {
            "handle": str(item["handle"]),
            "epoch": int(item["epoch"]),
            "internal_row": int(item["internal_row"]),
            "owner_target": TargetLabel.parse(str(item["owner_target"])).key,
        }
        if canonical not in lifecycle:
            raise G0RealizationError("branchpoint survivor is not lifecycle-owned")
        survivor.append(canonical)
    expected_survivors = [
        row
        for row in lifecycle
        if row["handle"] not in {event_owner_handle, selected_reserve_handle}
    ]
    if survivor != expected_survivors:
        raise G0RealizationError("branchpoint survivor-controller ordering drifted")
    if value["survivor_controller_rng_owners"] != []:
        raise G0RealizationError("branchpoint controller unexpectedly owns RNG")

    rng_value = value["non_controller_rng_states"]
    if (
        not isinstance(rng_value, Mapping)
        or not rng_value
        or list(rng_value) != sorted(str(key) for key in rng_value)
    ):
        raise G0RealizationError("branchpoint non-controller RNG inventory drifted")
    rng_states: dict[str, dict[str, str]] = {}
    for name, item in rng_value.items():
        expected_binding_keys = {"state_source", "state_sha256"}
        if not isinstance(item, Mapping) or set(item) != expected_binding_keys:
            raise G0RealizationError("branchpoint RNG binding schema drifted")
        state_source = str(item["state_source"])
        state_sha256 = str(item["state_sha256"])
        if (
            state_source != f"common_prestate.rng_states/{name}"
            or len(state_sha256) != 64
            or any(character not in "0123456789abcdef" for character in state_sha256)
        ):
            raise G0RealizationError("branchpoint RNG binding is invalid")
        rng_states[str(name)] = {
            "state_source": state_source,
            "state_sha256": state_sha256,
        }
    if "_channel_rng" not in rng_states:
        raise G0RealizationError("branchpoint omitted the registered channel RNG")

    cursor = value["channel_tape_cursor"]
    if (
        not isinstance(cursor, Mapping)
        or set(cursor) != {"draw_ordinal", "coordinate_count", "block_count"}
        or any(int(cursor[key]) != 0 for key in cursor)
    ):
        raise G0RealizationError("branchpoint channel-tape cursor is not empty")
    return {
        "physical_step": physical_step,
        "lifecycle_owner_to_internal": lifecycle,
        "event_owner_handle": event_owner_handle,
        "event_owner_epoch": event_owner_epoch,
        "selected_reserve_handle": selected_reserve_handle,
        "selected_reserve_original_target": selected_target.key,
        "survivor_ownership": survivor,
        "survivor_controller_rng_owners": [],
        "non_controller_rng_states": rng_states,
        "channel_tape_cursor": {
            "draw_ordinal": 0,
            "coordinate_count": 0,
            "block_count": 0,
        },
    }


def _validate_common_transducer_evidence_primitive(
    value: Any,
    *,
    recompute: bool = True,
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _COMMON_TRANSDUCER_EVIDENCE_KEYS:
        raise G0RealizationError("common transducer evidence schema drifted")
    positions = _native_array_from_primitive(value["physical_positions"])
    targets = _native_array_from_primitive(value["target_positions"])
    active = _native_array_from_primitive(value["active_mask"])
    raw = _native_array_from_primitive(value["raw_action"])
    position_array = positions.array()
    target_array = targets.array()
    active_array = active.array()
    raw_array = raw.array()
    if (
        str(value["transducer_source_sha256"]) != common_tracker_source_digest()
        or str(value["row_order"]) != "target_owned_internal"
        or position_array.shape != (PHYSICAL_UAVS, 3)
        or position_array.dtype != np.dtype(np.float64)
        or target_array.shape != (PHYSICAL_UAVS, 3)
        or target_array.dtype != np.dtype(np.float64)
        or active_array.shape != (PHYSICAL_UAVS,)
        or active_array.dtype != np.dtype(np.bool_)
        or raw_array.shape != (PHYSICAL_UAVS, ACTION_DIM)
        or raw_array.dtype != np.dtype(np.float32)
        or not np.isfinite(position_array).all()
        or not np.isfinite(target_array).all()
        or not np.isfinite(raw_array).all()
        or float(value["max_speed"]) != 30.0
        or float(value["max_vertical_speed"]) != 5.0
        or float(value["time_step"]) != 1.0
    ):
        raise G0RealizationError("common transducer primitive is not frozen G1")
    if recompute:
        expected_raw = g1_common_target_actions(
            physical_positions=position_array,
            target_positions=target_array,
            active_mask=active_array,
            max_speed=30.0,
            max_vertical_speed=5.0,
            time_step=1.0,
        )
        if not np.array_equal(raw_array, expected_raw):
            raise G0RealizationError(
                "common transducer output is not independently recomputed"
            )
    return {
        "transducer_source_sha256": common_tracker_source_digest(),
        "row_order": "target_owned_internal",
        "physical_positions": positions.to_primitive(),
        "target_positions": targets.to_primitive(),
        "active_mask": active.to_primitive(),
        "raw_action": raw.to_primitive(),
        "max_speed": 30.0,
        "max_vertical_speed": 5.0,
        "time_step": 1.0,
    }


def _common_transducer_evidence(
    *,
    physical_positions: np.ndarray,
    target_positions: np.ndarray,
    active_mask: np.ndarray,
    raw_action: np.ndarray,
) -> dict[str, Any]:
    return _validate_common_transducer_evidence_primitive(
        {
            "transducer_source_sha256": common_tracker_source_digest(),
            "row_order": "target_owned_internal",
            "physical_positions": _NativeArrayEvidence.from_array(
                np.asarray(physical_positions, dtype=np.float64)
            ).to_primitive(),
            "target_positions": _NativeArrayEvidence.from_array(
                np.asarray(target_positions, dtype=np.float64)
            ).to_primitive(),
            "active_mask": _NativeArrayEvidence.from_array(
                np.asarray(active_mask, dtype=np.bool_)
            ).to_primitive(),
            "raw_action": _NativeArrayEvidence.from_array(
                np.asarray(raw_action, dtype=np.float32)
            ).to_primitive(),
            "max_speed": 30.0,
            "max_vertical_speed": 5.0,
            "time_step": 1.0,
        }
    )


def _rng_state_bindings(
    rng_states: Mapping[str, Any],
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for name, item in sorted(rng_states.items()):
        key = str(name)
        if isinstance(item, Mapping) and set(item) == {
            "state_source",
            "state_sha256",
        }:
            source = str(item["state_source"])
            digest = str(item["state_sha256"])
            if (
                source != f"common_prestate.rng_states/{key}"
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise G0RealizationError("branchpoint RNG binding is invalid")
            result[key] = {"state_source": source, "state_sha256": digest}
        else:
            result[key] = {
                "state_source": f"common_prestate.rng_states/{key}",
                "state_sha256": sha256_json(
                    _validate_random_state_primitive(item)
                ),
            }
    return result


def _make_pre_action_context(
    source: G0EpisodeSource,
    *,
    physical_step: int,
    handles: Sequence[str],
    epochs: Sequence[int],
    selected_candidate_id: str,
    rng_states: Mapping[str, Any],
) -> dict[str, Any]:
    if len(handles) != PHYSICAL_UAVS or len(epochs) != PHYSICAL_UAVS:
        raise G0RealizationError("branchpoint lifecycle source inventory drifted")
    lifecycle: list[dict[str, Any]] = []
    for storage_row, (handle, epoch, owner_target) in enumerate(
        zip(handles, epochs, source.assignment.row_to_target)
    ):
        lifecycle.append(
            {
                "handle": str(handle),
                "epoch": int(epoch),
                "internal_row": int(source.geometry.slot_to_target[storage_row]),
                "owner_target": TargetLabel.parse(owner_target).key,
            }
        )
    lifecycle.sort(key=lambda row: int(row["internal_row"]))
    by_target = {row["owner_target"]: row for row in lifecycle}
    selected = TargetLabel.parse(selected_candidate_id)
    event_row = by_target[source.event.owner_target.key]
    selected_row = by_target[selected.key]
    context = {
        "physical_step": int(physical_step),
        "lifecycle_owner_to_internal": lifecycle,
        "event_owner_handle": event_row["handle"],
        "event_owner_epoch": int(event_row["epoch"]),
        "selected_reserve_handle": selected_row["handle"],
        "selected_reserve_original_target": selected.key,
        "survivor_ownership": [
            dict(row)
            for row in lifecycle
            if row["handle"] not in {event_row["handle"], selected_row["handle"]}
        ],
        "survivor_controller_rng_owners": [],
        "non_controller_rng_states": _rng_state_bindings(rng_states),
        "channel_tape_cursor": {
            "draw_ordinal": 0,
            "coordinate_count": 0,
            "block_count": 0,
        },
    }
    return _validate_pre_action_context_primitive(context)


def _pre_action_context(
    env: "UAVSourceIdentifiabilityEnv",
    ownership: Mapping[str, TargetLabel],
    selected_candidate_id: str,
) -> dict[str, Any]:
    env._synchronize_service_mask()
    expected_ownership = {
        str(handle): TargetLabel.parse(owner_target).key
        for handle, owner_target in zip(
            env._handles, env.g0_source.assignment.row_to_target
        )
    }
    actual_ownership = {
        str(handle): TargetLabel.parse(label.key).key
        for handle, label in ownership.items()
    }
    if actual_ownership != expected_ownership:
        raise G0RealizationError("branchpoint controller ownership is stale or forged")
    live_rngs = {
        str(name): item
        for name, item in sorted(env.__dict__.items())
        if isinstance(item, np.random.RandomState)
    }
    rng_states = getattr(env, "_g0_branchpoint_rng_bindings", None)
    snapshots = getattr(env, "_g0_branchpoint_rng_snapshots", None)
    if rng_states is None or snapshots is None:
        primitives = {
            name: _random_state_primitive(item)
            for name, item in live_rngs.items()
        }
        rng_states = _rng_state_bindings(primitives)
        snapshots = {
            name: (
                state[0],
                np.asarray(state[1], dtype=np.uint32).copy(),
                int(state[2]),
                int(state[3]),
                float(state[4]),
            )
            for name, item in live_rngs.items()
            for state in (item.get_state(),)
        }
        env._g0_branchpoint_rng_bindings = rng_states
        env._g0_branchpoint_rng_snapshots = snapshots
    if set(live_rngs) != set(snapshots):
        raise G0RealizationError("branchpoint RNG ownership changed")
    for name, item in live_rngs.items():
        current = item.get_state()
        frozen = snapshots[name]
        if not (
            str(current[0]) == str(frozen[0])
            and np.array_equal(current[1], frozen[1])
            and int(current[2]) == int(frozen[2])
            and int(current[3]) == int(frozen[3])
            and float(current[4]) == float(frozen[4])
        ):
            raise G0RealizationError("branchpoint non-controller RNG state changed")
    return _make_pre_action_context(
        env.g0_source,
        physical_step=int(env.current_step),
        handles=env._handles,
        epochs=env._epochs,
        selected_candidate_id=selected_candidate_id,
        rng_states=rng_states,
    )


def _expected_pre_action_context(
    source: G0EpisodeSource,
    common_prestate: Mapping[str, Any],
    *,
    physical_step: int,
    selected_candidate_id: str,
    rng_state_bindings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    handles = list(initial_lifecycle_handles(source))
    epochs = np.zeros(PHYSICAL_UAVS, dtype=np.int64)
    owner_storage = source.assignment.row_to_target.index(
        source.event.owner_target.key
    )
    if int(physical_step) >= source.event.rejoin:
        handles[owner_storage] = replacement_lifecycle_handle(
            source, handles[owner_storage]
        )
        epochs[owner_storage] = 1
    rng_states = (
        rng_state_bindings
        if rng_state_bindings is not None
        else common_prestate.get("rng_states")
    )
    if not isinstance(rng_states, Mapping):
        raise G0RealizationError("common prestate omitted branchpoint RNG evidence")
    return _make_pre_action_context(
        source,
        physical_step=int(physical_step),
        handles=handles,
        epochs=epochs,
        selected_candidate_id=selected_candidate_id,
        rng_states=rng_states,
    )


def _candidate_state_value(value: Any, *, path: str) -> Any:
    if isinstance(value, np.ndarray):
        return {"native_array": _NativeArrayEvidence.from_array(value).to_primitive()}
    if isinstance(value, np.random.RandomState):
        return {"random_state": _random_state_primitive(value)}
    if isinstance(value, np.random.Generator):
        return {"generator_state": _json_safe(value.bit_generator.state)}
    if isinstance(value, np.generic):
        return _candidate_state_value(value.item(), path=path)
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite_float": value.hex()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (tuple, list)):
        return [
            _candidate_state_value(item, path=f"{path}/{index}")
            for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        return {
            "ordered_mapping": [
                {
                    "key": _candidate_state_value(key, path=f"{path}/key"),
                    "value": _candidate_state_value(item, path=f"{path}/{key}"),
                }
                for key, item in value.items()
            ]
        }
    raise G0RealizationError(
        f"unsupported mutable candidate-state type at {path}: "
        f"{type(value).__name__}"
    )


class _EmptyChannelDrawRandomState:
    """Fail closed if the registered deterministic channel path starts drawing RNG."""

    def __init__(self, delegate: np.random.RandomState) -> None:
        self._delegate = delegate
        self.requested_operations: list[str] = []

    def __getattr__(self, name: str) -> Any:
        value = getattr(self._delegate, name)
        if not callable(value):
            return value

        def forbidden(*args: Any, **kwargs: Any) -> Any:
            self.requested_operations.append(str(name))
            raise G0RealizationError(
                "registered inherited channel path no longer has an empty RNG schema"
            )

        return forbidden


def _complete_oracle_prestate(env: "UAVSourceIdentifiabilityEnv") -> dict[str, Any]:
    rng_states: dict[str, Any] = {}
    for name, value in env.__dict__.items():
        if isinstance(value, np.random.RandomState):
            rng_states[str(name)] = _random_state_primitive(value)
    if "_channel_rng" not in rng_states:
        raise G0RealizationError("complete prestate omitted the registered channel RNG")
    candidate_tokens = (
        "position",
        "velocity",
        "connection",
        "routing",
        "channel",
        "sinr",
        "hop",
        "cache",
        "guard",
        "service",
        "mask",
        "current_step",
    )
    candidate_state_inventory: dict[str, Any] = {}
    for name, value in env.__dict__.items():
        if any(token in str(name).lower() for token in candidate_tokens):
            candidate_state_inventory[str(name)] = _candidate_state_value(
                value, path=str(name)
            )
    return {
        "source": env.g0_source.to_primitive(),
        "cell": env.g0_cell.value,
        "current_step": int(env.current_step),
        "geometry": {
            "uav_positions": _NativeArrayEvidence.from_array(env.uav_positions).to_primitive(),
            "user_positions": _NativeArrayEvidence.from_array(env.user_positions).to_primitive(),
            "ground_bs_positions": _NativeArrayEvidence.from_array(
                env.ground_bs_positions
            ).to_primitive(),
        },
        "event": env.g0_source.event.to_primitive(),
        "slot_permutation": _NativeArrayEvidence.from_array(
            env.g0_source.geometry.slot_to_target
        ).to_primitive(),
        "service_mask": _NativeArrayEvidence.from_array(
            env._service_active_mask
        ).to_primitive(),
        "connections": {
            "user": _NativeArrayEvidence.from_array(env.connections).to_primitive(),
            "uav": _NativeArrayEvidence.from_array(env.uav_connections).to_primitive(),
            "uav_bs": _NativeArrayEvidence.from_array(
                env.uav_bs_connections
            ).to_primitive(),
        },
        "routing_paths": _routing_paths_primitive(env.routing_paths),
        "lifecycle_handles": list(env._handles),
        "lifecycle_epochs": _NativeArrayEvidence.from_array(env._epochs).to_primitive(),
        "rng_states": rng_states,
        "communication_config": _json_safe(env._communication_config_signature()),
        "candidate_guard_transition_state_inventory": candidate_state_inventory,
        "candidate_guard_transition_state_names": sorted(
            candidate_state_inventory
        ),
    }


class UAVSourceIdentifiabilityEnv(UAVEnergyAwareRelayEnv):
    """Exact G0 geometry plus ledger-driven service availability over S7-S1."""

    def __init__(
        self,
        source: G0EpisodeSource,
        cell: Cell | str,
        env_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        self.g0_source = source
        self.g0_cell = Cell(cell)
        self.environment_seed = int(source.geometry.episode_id)
        # The inherited environment always runs in target-owned world order.
        # G0's sampled physical-slot permutation is a storage adapter only.
        self._storage_to_internal = np.asarray(
            source.geometry.slot_to_target, dtype=np.int64
        ).copy()
        self._internal_to_storage = np.argsort(self._storage_to_internal)
        self._service_active_mask = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
        self._last_mask_step = -1
        self._handles = initial_lifecycle_handles(source)
        self._epochs = np.zeros(PHYSICAL_UAVS, dtype=np.int64)
        self._pending_boundary_events: list[LifecycleBoundaryEvent] = []
        kwargs = dict(env_kwargs or {})
        unsupported = set(kwargs).difference({"render_mode"})
        if unsupported:
            raise G0RealizationError(
                "G0 env kwargs cannot override S7-S1: " + ", ".join(sorted(unsupported))
            )
        config = Config("S7-S1")
        super().__init__(config=config, seed=self.environment_seed, **kwargs)
        self._channel_rng = _namespace_random_state(self.environment_seed, 3)
        if (
            self.n_uavs != PHYSICAL_UAVS
            or self.n_users != GROUND_USERS
            or self.n_ground_bs != GROUND_BASE_STATIONS
            or self.action_dim != ACTION_DIM
            or self.max_steps != PHYSICAL_HORIZON
            or self.energy_stage != "S1"
            or self.battery_enabled
            or self.charging_enabled
            or self.failure_enabled
            or bool(getattr(self, "terminal_loss_enabled", False))
        ):
            raise G0RealizationError("G0 did not instantiate the frozen S7-S1 inventory")
        if (
            float(self.area_size) != source.geometry.map_width
            or float(self.area_size) != source.geometry.map_height
        ):
            raise G0RealizationError("S7-S1 map support differs from frozen G0 geometry")
        if not np.array_equal(
            np.asarray(self.ground_bs_positions[0, :2], dtype=np.float64),
            source.geometry.base_xy,
        ):
            raise G0RealizationError("environment base station differs from source center")
        if float(self.height_range[0]) != FIXED_ALTITUDE_M:
            raise G0RealizationError("S7-S1 fixed altitude changed")

    def _init_ground_bs(self) -> None:
        self.ground_bs_positions = np.asarray(
            [[*self.g0_source.geometry.base_xy.tolist(), 30.0]], dtype=np.float64
        )

    def _init_uav_positions(self) -> np.ndarray:
        return np.concatenate(
            (
                self.g0_source.geometry.target_owned_initial_xy,
                np.full((PHYSICAL_UAVS, 1), FIXED_ALTITUDE_M, dtype=np.float64),
            ),
            axis=1,
        )

    def _generate_user_positions(self) -> np.ndarray:
        return np.concatenate(
            (
                self.g0_source.geometry.users_xy,
                np.full((GROUND_USERS, 1), USER_ALTITUDE_M, dtype=np.float64),
            ),
            axis=1,
        )

    def _init_user_velocities(self) -> None:
        self.user_velocities[:] = 0.0

    def _initialize_user_waypoints_rpgm(self) -> None:
        # The registered G0 users are fixed.  Populate the inherited arrays so
        # diagnostics remain defined without advancing an RNG.
        self.user_waypoints = np.asarray(self.user_positions[:, :2], dtype=np.float64).copy()
        self.user_pause_times = np.zeros(self.n_users, dtype=np.float64)
        self.user_cluster_assignments = self.g0_source.geometry.user_hotspots.copy()
        self.cluster_centers_history = self.g0_source.geometry.hotspot_centers.copy()
        self.cluster_velocities = np.zeros((HOTSPOT_COUNT, 2), dtype=np.float64)
        self.cluster_waypoints = self.cluster_centers_history.copy()
        self.cluster_pause_times = np.zeros(HOTSPOT_COUNT, dtype=np.float64)

    def _move_users(self) -> None:
        # Fixed for the complete 500-step episode.
        return None

    def _update_channel_state(self) -> None:
        previous = getattr(self, "np_random", None)
        recorder = _EmptyChannelDrawRandomState(
            np.random.RandomState(
                channel_seed_word(
                    self.g0_source.geometry.episode_id,
                    int(getattr(self, "current_step", 0)),
                )
            )
        )
        self.np_random = recorder
        try:
            super()._update_channel_state()
        finally:
            if previous is not None:
                self.np_random = previous
        if recorder.requested_operations:
            raise G0RealizationError("channel draw schema is not the registered empty schema")

    @property
    def event_owner_row(self) -> int:
        return int(self._internal_to_storage[self.event_owner_internal_row])

    @property
    def event_owner_internal_row(self) -> int:
        return TARGET_LABELS.index(self.g0_source.event.owner_target)

    def _active_mask_for_step(self, physical_step: int) -> np.ndarray:
        mask = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
        mask[self.event_owner_internal_row] = self.g0_source.event.active(
            physical_step, self.g0_cell
        )
        return mask

    @property
    def service_active_mask(self) -> np.ndarray:
        self._synchronize_service_mask()
        return self._service_active_mask[self._storage_to_internal].copy()

    def _is_uav_unavailable(self, uav_idx: int) -> bool:
        service = getattr(self, "_service_active_mask", None)
        if service is not None and not bool(service[int(uav_idx)]):
            return True
        return super()._is_uav_unavailable(uav_idx)

    def _communication_unavailable_mask(self) -> np.ndarray:
        unavailable = super()._communication_unavailable_mask()
        service = getattr(self, "_service_active_mask", None)
        if service is not None:
            unavailable |= ~np.asarray(service, dtype=np.bool_)
        return unavailable

    def _is_uav_motion_disabled(self, uav_idx: int) -> bool:
        service = getattr(self, "_service_active_mask", None)
        if service is not None and not bool(service[int(uav_idx)]):
            return True
        return super()._is_uav_motion_disabled(uav_idx)

    def _update_uav_failures(self) -> None:
        self.uav_failure_timers[:] = 0
        self.uav_failed[:] = False

    def _synchronize_service_mask(self, *, force: bool = False) -> bool:
        step = int(getattr(self, "current_step", 0))
        if not force and step == self._last_mask_step:
            return False
        old = self._service_active_mask.copy()
        new = self._active_mask_for_step(step)
        changed = not np.array_equal(old, new)
        self._service_active_mask = new
        self._last_mask_step = step
        if changed:
            owner_internal = self.event_owner_internal_row
            owner_storage = self.event_owner_row
            previous = self._handles[owner_storage]
            if old[owner_internal] and not new[owner_internal]:
                event = LifecycleBoundaryEvent(
                    kind="LEAVE",
                    physical_step=step,
                    previous_handle=previous,
                    current_handle=None,
                    owner_target=self.g0_source.event.owner_target.key,
                )
            elif not old[owner_internal] and new[owner_internal]:
                current = replacement_lifecycle_handle(self.g0_source, previous)
                handles = list(self._handles)
                handles[owner_storage] = current
                self._handles = tuple(handles)
                self._epochs[owner_storage] += 1
                event = LifecycleBoundaryEvent(
                    kind="REJOIN",
                    physical_step=step,
                    previous_handle=previous,
                    current_handle=current,
                    owner_target=self.g0_source.event.owner_target.key,
                )
            else:
                raise G0RealizationError("service mask changed outside the event owner")
            self._pending_boundary_events.append(event)
            if hasattr(self, "connections"):
                self._update_channel_state()
                self._update_uav_connections()
                self._compute_routing_paths()
        return changed

    def consume_boundary_events(self) -> tuple[LifecycleBoundaryEvent, ...]:
        self._synchronize_service_mask()
        events = tuple(self._pending_boundary_events)
        self._pending_boundary_events.clear()
        return events

    def reset(self, seed: int | None = None, options: Any = None):
        if seed is not None and int(seed) != self.environment_seed:
            raise G0RealizationError("G0 reset cannot replace the episode-ID source")
        self._service_active_mask[:] = True
        self._last_mask_step = -1
        self._handles = initial_lifecycle_handles(self.g0_source)
        self._epochs[:] = 0
        self._pending_boundary_events.clear()
        self._channel_rng = _namespace_random_state(self.environment_seed, 3)
        observations, infos = super().reset(seed=self.environment_seed, options=options)
        self._last_mask_step = -1
        self._synchronize_service_mask(force=True)
        if not np.array_equal(self.user_positions[:, :2], self.g0_source.geometry.users_xy):
            raise G0RealizationError("reset changed fixed G0 user geometry")
        if not np.array_equal(
            self.uav_positions[:, :2],
            self.g0_source.geometry.target_owned_initial_xy,
        ):
            raise G0RealizationError("reset changed target-owned UAV world geometry")
        if not np.array_equal(
            np.stack([row.position[:2] for row in self.current_rows()]),
            self.g0_source.geometry.physical_xy,
        ):
            raise G0RealizationError("reset changed storage-only slot permutation")
        return observations, infos

    def current_rows(self) -> tuple[AnonymousLifecycleRow, ...]:
        self._synchronize_service_mask()
        velocities = np.asarray(
            getattr(self, "last_actual_velocities", np.zeros((PHYSICAL_UAVS, 3))),
            dtype=np.float64,
        ).copy()
        velocities[~self._service_active_mask] = 0.0
        positions = np.asarray(self.uav_positions, dtype=np.float64)[
            self._storage_to_internal
        ]
        velocities = velocities[self._storage_to_internal]
        active = self._service_active_mask[self._storage_to_internal]
        return tuple(
            AnonymousLifecycleRow(
                handle=self._handles[row],
                position=positions[row],
                velocity=velocities[row],
                active=bool(active[row]),
                service_available=bool(active[row]),
            )
            for row in range(PHYSICAL_UAVS)
        )

    def _get_link_capacity(
        self,
        node1_type: str,
        node1_idx: int,
        node2_type: str,
        node2_idx: int,
    ) -> Any:
        value = super()._get_link_capacity(
            node1_type, node1_idx, node2_type, node2_idx
        )
        guarded_uav = getattr(self, "_inside_oracle_guard_uav", None)
        reads = getattr(self, "_oracle_guard_capacity_reads", None)
        if guarded_uav is not None and reads is not None:
            reads.append(
                OracleGuardCapacityRead.from_value(
                    guarded_uav=int(guarded_uav),
                    node1_type=node1_type,
                    node1_idx=node1_idx,
                    node2_type=node2_type,
                    node2_idx=node2_idx,
                    value=value,
                )
            )
        return value

    def _apply_backhaul_action_guard(self, uav_idx: int, velocity: Any) -> Any:
        previous = getattr(self, "_inside_oracle_guard_uav", None)
        self._inside_oracle_guard_uav = int(uav_idx)
        try:
            guarded = super()._apply_backhaul_action_guard(uav_idx, velocity)
        finally:
            self._inside_oracle_guard_uav = previous
        rows = getattr(self, "_oracle_guarded_velocity_rows", None)
        interventions = getattr(self, "_oracle_guard_interventions", None)
        if rows is not None and interventions is not None:
            proposed = np.asarray(velocity, dtype=np.float64)
            guarded_array = np.asarray(guarded, dtype=np.float64)
            rows[int(uav_idx)] = guarded_array
            interventions[int(uav_idx)] = not np.array_equal(
                proposed, guarded_array
            )
        return guarded

    def _begin_oracle_safety_capture(
        self,
        *,
        candidate_id: str,
        raw_internal: np.ndarray,
        pre_action_context: Mapping[str, Any],
        executed_service_mask: np.ndarray,
        common_transducer_evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        if getattr(self, "_oracle_guard_capacity_reads", None) is not None:
            raise G0RealizationError("nested oracle safety capture is forbidden")
        self._oracle_guard_capacity_reads = []
        self._oracle_guarded_velocity_rows = np.zeros(
            (PHYSICAL_UAVS, 3), dtype=np.float64
        )
        self._oracle_guard_interventions = np.zeros(PHYSICAL_UAVS, dtype=np.bool_)
        return {
            "physical_step": int(self.current_step),
            "candidate_id": str(candidate_id),
            "positions": np.asarray(self.uav_positions).copy(),
            "velocities": np.asarray(self.last_actual_velocities).copy(),
            "service_mask": np.asarray(self._service_active_mask).copy(),
            "pre_action_context": _json_safe(pre_action_context),
            "executed_service_mask": np.asarray(
                executed_service_mask, dtype=np.bool_
            ).copy(),
            "common_transducer_evidence": _json_safe(
                common_transducer_evidence
            ),
            "raw_internal": np.asarray(raw_internal, dtype=np.float32).copy(),
            "connections": {
                "user": _NativeArrayEvidence.from_array(self.connections),
                "uav": _NativeArrayEvidence.from_array(self.uav_connections),
                "uav_bs": _NativeArrayEvidence.from_array(self.uav_bs_connections),
            },
            "routing_paths": tuple(_routing_paths_primitive(self.routing_paths)),
            "guard_checked_before": int(
                getattr(self, "backhaul_guard_checked_actions", 0)
            ),
            "guard_blocked_before": int(
                getattr(self, "backhaul_guard_blocked_actions", 0)
            ),
        }

    def _finish_oracle_safety_capture(
        self,
        capture: Mapping[str, Any],
    ) -> OracleSafetyStepRecord:
        reads = tuple(self._oracle_guard_capacity_reads)
        guarded = np.asarray(self._oracle_guarded_velocity_rows).copy()
        interventions = np.asarray(self._oracle_guard_interventions).copy()
        self._oracle_guard_capacity_reads = None
        self._oracle_guarded_velocity_rows = None
        self._oracle_guard_interventions = None
        current = np.asarray(capture["positions"], dtype=np.float64)
        next_positions = np.asarray(self.uav_positions, dtype=np.float64).copy()
        velocities = (next_positions - current) / float(self.time_step)
        return OracleSafetyStepRecord(
            physical_step=int(capture["physical_step"]),
            candidate_id=str(capture["candidate_id"]),
            current_uav_positions=_NativeArrayEvidence.from_array(current),
            current_uav_velocities=_NativeArrayEvidence.from_array(
                capture["velocities"]
            ),
            current_service_mask=_NativeArrayEvidence.from_array(
                capture["service_mask"]
            ),
            pre_action_context=_validate_pre_action_context_primitive(
                capture["pre_action_context"]
            ),
            executed_service_mask=_NativeArrayEvidence.from_array(
                capture["executed_service_mask"]
            ),
            common_transducer_evidence=(
                _validate_common_transducer_evidence_primitive(
                    capture["common_transducer_evidence"]
                )
            ),
            raw_candidate_action=_NativeArrayEvidence.from_array(
                capture["raw_internal"]
            ),
            shared_channel_draw_coordinate=(),
            shared_channel_draw_block=(),
            connections=dict(capture["connections"]),
            routing_paths=tuple(capture["routing_paths"]),
            exact_link_capacity_values_read_by_the_real_guard=reads,
            real_guard_intervention_or_violation_output={
                "checked_actions": int(
                    getattr(self, "backhaul_guard_checked_actions", 0)
                ),
                "blocked_actions": int(
                    getattr(self, "backhaul_guard_blocked_actions", 0)
                ),
                "intervention_by_uav": interventions.tolist(),
            },
            guarded_executed_action=_NativeArrayEvidence.from_array(guarded),
            next_uav_positions=_NativeArrayEvidence.from_array(next_positions),
            next_uav_velocities=_NativeArrayEvidence.from_array(velocities),
        )

    def step_oracle_safety(
        self,
        actions_internal: np.ndarray,
        *,
        candidate_id: str,
        ownership: Mapping[str, TargetLabel],
        pre_action_context: Mapping[str, Any],
        common_transducer_evidence: Mapping[str, Any],
    ) -> OracleSafetyStepRecord:
        """Advance only physical/channel/routing safety state, never service/reward."""

        self._synchronize_service_mask()
        dense = np.asarray(actions_internal, dtype=np.float32)
        if dense.shape != (PHYSICAL_UAVS, ACTION_DIM):
            raise G0RealizationError("oracle safety action must have shape [8,4]")
        if not np.isfinite(dense).all() or np.any(np.abs(dense) > 1.0):
            raise G0RealizationError("oracle safety action is outside support")
        if not np.array_equal(dense[:, 2], np.zeros(PHYSICAL_UAVS, dtype=np.float32)):
            raise G0RealizationError("oracle safety action changed fixed altitude")
        expected_context = _pre_action_context(
            self, ownership, str(candidate_id)
        )
        actual_context = _validate_pre_action_context_primitive(
            pre_action_context
        )
        if actual_context != expected_context:
            raise G0RealizationError("oracle safety branchpoint context is stale")
        transducer = _validate_common_transducer_evidence_primitive(
            common_transducer_evidence
        )
        if (
            not np.array_equal(
                _native_array_from_primitive(
                    transducer["physical_positions"]
                ).array(),
                np.asarray(self.uav_positions, dtype=np.float64),
            )
            or not np.array_equal(
                _native_array_from_primitive(transducer["active_mask"]).array(),
                self._service_active_mask,
            )
            or not np.array_equal(
                _native_array_from_primitive(transducer["raw_action"]).array(),
                dense,
            )
        ):
            raise G0RealizationError("oracle safety transducer binding is stale")
        executed_service_mask = self._service_active_mask.copy()
        capture = self._begin_oracle_safety_capture(
            candidate_id=candidate_id,
            raw_internal=dense,
            pre_action_context=actual_context,
            executed_service_mask=executed_service_mask,
            common_transducer_evidence=transducer,
        )
        action_dict = {
            agent: dense[row].copy()
            for row, agent in enumerate(self.possible_agents)
            if self._service_active_mask[row]
        }
        adjusted_actions, _commanded_velocities = self._prepare_energy_actions(
            action_dict
        )
        self.previous_routing_paths_snapshot = dict(self.routing_paths)
        self.previous_connections_snapshot = self.connections.copy()
        self._move_users()
        self.backhaul_guard_checked_actions = 0
        self.backhaul_guard_blocked_actions = 0
        before = np.asarray(self.uav_positions, dtype=np.float64).copy()
        for agent_idx, agent in enumerate(self.agents):
            action = np.asarray(adjusted_actions[agent], dtype=np.float32)
            velocity = action * float(self.max_speed)
            velocity = np.asarray(
                self._apply_backhaul_action_guard(agent_idx, velocity),
                dtype=np.float64,
            )
            next_position = self.uav_positions[agent_idx] + velocity * float(
                self.time_step
            )
            next_position[0] = np.clip(next_position[0], 0.0, self.area_size)
            next_position[1] = np.clip(next_position[1], 0.0, self.area_size)
            next_position[2] = np.clip(next_position[2], *self.height_range)
            self.uav_positions[agent_idx] = next_position
        self.last_actual_velocities = (
            np.asarray(self.uav_positions, dtype=np.float64) - before
        ) / float(self.time_step)
        self._update_channel_state()
        self._update_uav_connections()
        if (
            self.routing_protocol == "hggr"
            and self.current_step % self.hggr_update_interval == 0
        ):
            self.hop_map = self._calculate_hop_map()
        if self.current_step % self.hggr_update_interval == 0:
            self._update_global_bs_cache()
        self._compute_routing_paths()
        self.current_step += 1
        record = self._finish_oracle_safety_capture(capture)
        self._synchronize_service_mask(force=True)
        return record

    def step_dense(
        self,
        actions: np.ndarray,
        *,
        oracle_ownership: Mapping[str, TargetLabel] | None = None,
        oracle_pre_action_context: Mapping[str, Any] | None = None,
        oracle_common_transducer_evidence: Mapping[str, Any] | None = None,
    ) -> G0Transition:
        self._synchronize_service_mask()
        dense = np.asarray(actions, dtype=np.float32)
        if dense.shape != (PHYSICAL_UAVS, ACTION_DIM):
            raise G0RealizationError("G0 action must have shape [8,4]")
        if not np.isfinite(dense).all() or np.any(np.abs(dense) > 1.0):
            raise G0RealizationError("G0 action is outside the Scenario-7 support")
        if not np.array_equal(
            dense[:, 2], np.zeros(PHYSICAL_UAVS, dtype=np.float32)
        ):
            raise G0RealizationError("G0 fixed-altitude route received vertical action")
        dense_internal = np.zeros_like(dense)
        dense_internal[self._storage_to_internal] = dense
        executed_internal = self._service_active_mask.copy()
        executed = executed_internal[self._storage_to_internal]
        before_internal = np.asarray(self.uav_positions, dtype=np.float64).copy()
        behavioral_candidate = getattr(
            self, "_oracle_behavioral_candidate_id", None
        )
        safety_capture = None
        if behavioral_candidate is not None:
            if (
                oracle_ownership is None
                or oracle_pre_action_context is None
                or oracle_common_transducer_evidence is None
            ):
                raise G0RealizationError(
                    "behavioral branch omitted branchpoint/transducer evidence"
                )
            expected_context = _pre_action_context(
                self, oracle_ownership, str(behavioral_candidate)
            )
            actual_context = _validate_pre_action_context_primitive(
                oracle_pre_action_context
            )
            if actual_context != expected_context:
                raise G0RealizationError("behavioral branchpoint context is stale")
            transducer = _validate_common_transducer_evidence_primitive(
                oracle_common_transducer_evidence
            )
            if (
                not np.array_equal(
                    _native_array_from_primitive(
                        transducer["physical_positions"]
                    ).array(),
                    np.asarray(self.uav_positions, dtype=np.float64),
                )
                or not np.array_equal(
                    _native_array_from_primitive(
                        transducer["active_mask"]
                    ).array(),
                    executed_internal,
                )
                or not np.array_equal(
                    _native_array_from_primitive(transducer["raw_action"]).array(),
                    dense_internal,
                )
            ):
                raise G0RealizationError("behavioral transducer binding is stale")
            safety_capture = self._begin_oracle_safety_capture(
                candidate_id=str(behavioral_candidate),
                raw_internal=dense_internal,
                pre_action_context=actual_context,
                executed_service_mask=executed_internal,
                common_transducer_evidence=transducer,
            )
        elif any(
            item is not None
            for item in (
                oracle_ownership,
                oracle_pre_action_context,
                oracle_common_transducer_evidence,
            )
        ):
            raise G0RealizationError("non-oracle step received oracle evidence")
        action_dict = {
            agent: dense_internal[row].copy()
            for row, agent in enumerate(self.possible_agents)
            if executed_internal[row]
        }
        _observations, _rewards, terminations, truncations, _infos = super().step(
            action_dict
        )
        if safety_capture is not None:
            behavioral_trace = getattr(self, "_oracle_behavioral_trace", None)
            if behavioral_trace is None:
                behavioral_trace = []
                self._oracle_behavioral_trace = behavioral_trace
            behavioral_trace.append(
                self._finish_oracle_safety_capture(safety_capture)
            )
        after_internal = np.asarray(self.uav_positions, dtype=np.float64).copy()
        velocities_internal = np.asarray(
            self.last_actual_velocities, dtype=np.float64
        ).copy()
        if not np.array_equal(
            after_internal[~executed_internal], before_internal[~executed_internal]
        ):
            raise G0RealizationError("absent lifecycle physical slot moved")
        if not (
            np.array_equal(
                before_internal[:, 2], np.full(PHYSICAL_UAVS, FIXED_ALTITUDE_M)
            )
            and np.array_equal(
                after_internal[:, 2], np.full(PHYSICAL_UAVS, FIXED_ALTITUDE_M)
            )
        ):
            raise G0RealizationError("G0 fixed-altitude invariant changed")
        if not np.array_equal(
            velocities_internal[~executed_internal],
            np.zeros((int((~executed_internal).sum()), 3), dtype=np.float64),
        ):
            raise G0RealizationError("absent lifecycle velocity was not exact zero")
        before = before_internal[self._storage_to_internal]
        after = after_internal[self._storage_to_internal]
        velocities = velocities_internal[self._storage_to_internal]
        completed_step = int(self.current_step) - 1
        self._synchronize_service_mask(force=True)
        return G0Transition(
            physical_step=completed_step,
            delivered_user_rates_mbps=np.asarray(self.last_user_rates_mbps, dtype=np.float64),
            executed_action_mask=executed,
            raw_actions=dense,
            positions_before=before,
            positions_after=after,
            actual_velocities=velocities,
            backhaul_guard_blocked_actions=int(
                getattr(self, "backhaul_guard_blocked_actions", 0)
            ),
            boundary_events=self.consume_boundary_events(),
            terminated=bool(all(terminations.values())) if terminations else False,
            truncated=bool(all(truncations.values())) if truncations else False,
        )


class MechanicallyQualifiedOracleController:
    """Ledger-aware controller bound to one pre-behavior two-candidate proof."""

    name = Control.ORACLE.value
    uses_complete_event_ledger = True
    trains = False

    def __init__(
        self,
        source: G0EpisodeSource,
        handles: Sequence[str],
        qualification: OracleQualificationCertificate,
        safety_ledger: OracleSafetyLedger,
    ) -> None:
        validate_oracle_qualification(
            source, qualification, safety_ledger=safety_ledger
        )
        self.source = source
        self.geometry = G0ControllerGeometry.from_source(source)
        self.qualification = qualification
        self.safety_ledger = safety_ledger
        self.ownership = _initial_ownership(source, handles)
        self._selected_stage = TargetLabel.parse(qualification.selected_reserve_target)
        if self._selected_stage.kind is not TargetKind.STAGE:
            raise G0RealizationError("oracle selected candidate is not a reserve")
        self._selected_reserve = next(
            handle for handle, label in self.ownership.items() if label == self._selected_stage
        )
        self._failed_primary = source.event.owner_target
        self._absent_handle = next(
            handle for handle, label in self.ownership.items() if label == self._failed_primary
        )
        candidate = next(
            row
            for row in qualification.candidates
            if row.reserve_target == self._selected_stage.key
        )
        self._latest_departure = int(candidate.latest_departure)
        self._rejoined_handle: str | None = None
        self._rejoin_step: int | None = None
        self._last_primary_step: int | None = None
        self._complete_primary_steps = 0
        self._return_ready_step: int | None = None

    def on_leave(
        self, absent_handle: str, rows: Sequence[AnonymousLifecycleRow]
    ) -> None:
        roster = _roster_by_handle(rows)
        if (
            absent_handle != self._absent_handle
            or roster[absent_handle].active
            or sum(row.active for row in rows) != 7
        ):
            raise G0RealizationError("oracle observed a nonregistered leave boundary")

    def on_rejoin(self, previous_handle: str, new_handle: str, physical_step: int) -> None:
        if previous_handle != self._absent_handle or new_handle in self.ownership:
            raise G0RealizationError("oracle observed a nonregistered rejoin boundary")
        del self.ownership[previous_handle]
        self.ownership[new_handle] = self._failed_primary
        self._rejoined_handle = new_handle
        self._rejoin_step = int(physical_step)

    def target_map(
        self,
        information: G0CurrentInformation,
        *,
        physical_step: int,
    ) -> dict[str, np.ndarray]:
        roster = _current_roster(self.geometry, information)
        weakest_hotspot_service = information.weakest_hotspot_service
        step = int(physical_step)
        if not math.isfinite(float(weakest_hotspot_service)):
            raise G0RealizationError("oracle current service input is nonfinite")
        if self._rejoined_handle is not None:
            primary_xy = self.geometry.coordinate(self._failed_primary)
            row = roster[self._rejoined_handle]
            at_primary = bool(np.array_equal(row.position[:2], primary_xy))
            if (
                self._rejoin_step is not None
                and step >= self._rejoin_step + 1
                and row.active
                and at_primary
                and self._last_primary_step == step - 1
            ):
                self._complete_primary_steps += 1
            if row.active and at_primary:
                self._last_primary_step = step
            if (
                self._return_ready_step is None
                and self._rejoin_step is not None
                and step >= self._rejoin_step + 1
                and self._complete_primary_steps >= 1
                and float(weakest_hotspot_service) >= SERVICE_TARGET
            ):
                self._return_ready_step = step

        result: dict[str, np.ndarray] = {}
        for handle, original_label in self.ownership.items():
            label = original_label
            if handle == self._selected_reserve:
                if step < self._latest_departure:
                    label = self._selected_stage
                    xy = self.geometry.coordinate(label)
                elif step < self.source.event.onset:
                    xy = self.geometry.gate(self._failed_primary)
                elif step < self.source.event.rejoin:
                    xy = self.geometry.coordinate(self._failed_primary)
                elif self._return_ready_step is None or step < self._return_ready_step:
                    xy = self.geometry.gate(self._failed_primary)
                else:
                    xy = self.geometry.coordinate(self._selected_stage)
            else:
                xy = self.geometry.coordinate(label)
            if handle in roster:
                result[handle] = np.concatenate((xy, [FIXED_ALTITUDE_M]))
        return result

    def evidence(self) -> dict[str, Any]:
        return {
            "controller": self.name,
            "qualification": self.qualification.to_primitive(),
            "oracle_safety_ledger": self.safety_ledger.to_primitive(),
            "selected_reserve": self._selected_stage.key,
            "latest_departure": self._latest_departure,
            "return_ready_step": self._return_ready_step,
            "future_channel_read_count": 0,
            "future_service_selection_read_count": 0,
            "candidate_count": K_SEARCH,
        }


@dataclass(frozen=True)
class EpisodeRunEvidence:
    episode_id: int
    control: Control
    cell: Cell
    metrics: EpisodeMetrics
    source_sha256: str
    user_demand_input_mbps: np.ndarray
    user_delivered_input_mbps: np.ndarray
    channel_association_input: np.ndarray
    delivered_user_rates_mbps: np.ndarray
    target_trace: np.ndarray
    raw_action_trace: np.ndarray
    executed_velocity_trace: np.ndarray
    position_trace: np.ndarray
    active_mask_trace: np.ndarray
    controller_evidence: Mapping[str, Any]
    target_trace_sha256: str
    raw_action_trace_sha256: str
    executed_velocity_trace_sha256: str
    executed_position_trace_sha256: str
    service_trace_sha256: str
    controller_state_sha256: str
    lifecycle_events: tuple[LifecycleBoundaryEvent, ...]
    tracker_failures: int
    action_support_violations: int
    ownership_violations: int
    backhaul_guard_blocked_actions: int
    oracle_qualification_failures: int
    weakest_service: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "control", Control(self.control))
        object.__setattr__(self, "cell", Cell(self.cell))
        weakest = np.asarray(self.weakest_service, dtype=np.float64)
        if weakest.shape != (PHYSICAL_HORIZON,) or not np.isfinite(weakest).all():
            raise G0RealizationError("episode run weakest-service evidence is incomplete")
        object.__setattr__(
            self, "weakest_service", _readonly_array(weakest, dtype=np.float64)
        )
        arrays = (
            ("user_demand_input_mbps", self.user_demand_input_mbps, (PHYSICAL_HORIZON, GROUND_USERS), np.float64),
            ("user_delivered_input_mbps", self.user_delivered_input_mbps, (PHYSICAL_HORIZON, GROUND_USERS), np.float64),
            ("channel_association_input", self.channel_association_input, (PHYSICAL_HORIZON, PHYSICAL_UAVS, GROUND_USERS), np.bool_),
            ("delivered_user_rates_mbps", self.delivered_user_rates_mbps, (PHYSICAL_HORIZON, GROUND_USERS), np.float64),
            ("target_trace", self.target_trace, (PHYSICAL_HORIZON, PHYSICAL_UAVS, 3), np.float64),
            ("raw_action_trace", self.raw_action_trace, (PHYSICAL_HORIZON, PHYSICAL_UAVS, ACTION_DIM), np.float32),
            ("executed_velocity_trace", self.executed_velocity_trace, (PHYSICAL_HORIZON, PHYSICAL_UAVS, 3), np.float64),
            ("position_trace", self.position_trace, (PHYSICAL_HORIZON + 1, PHYSICAL_UAVS, 3), np.float64),
            ("active_mask_trace", self.active_mask_trace, (PHYSICAL_HORIZON, PHYSICAL_UAVS), np.bool_),
        )
        for name, value, shape, dtype in arrays:
            array = np.asarray(value, dtype=dtype)
            if array.shape != shape or (
                dtype is not np.bool_ and not np.isfinite(array).all()
            ):
                raise G0RealizationError(f"episode run {name} evidence is malformed")
            object.__setattr__(self, name, _readonly_array(array, dtype=dtype))
        if not isinstance(self.controller_evidence, Mapping):
            raise G0RealizationError("controller evidence is not a mapping")
        object.__setattr__(self, "controller_evidence", dict(self.controller_evidence))


def _controller_for_run(
    source: G0EpisodeSource,
    control: Control,
    handles: Sequence[str],
    *,
    max_speed: float,
    max_vertical_speed: float,
    time_step: float,
) -> Any:
    if control is Control.SAME_INFORMATION:
        return SameInformationController(source, handles)
    if control is Control.NO_REALLOCATION:
        return NoReallocationController(source, handles)
    if not (
        float(max_speed) == 30.0
        and float(max_vertical_speed) == 5.0
        and float(time_step) == 1.0
    ):
        raise G0RealizationError("oracle behavior requires frozen S7-S1 dynamics")
    safety_ledger = build_oracle_safety_ledger(source)
    qualification = oracle_qualification_from_safety_ledger(source, safety_ledger)
    return MechanicallyQualifiedOracleController(
        source, handles, qualification, safety_ledger
    )


def _canonical_controller_state(controller: Any) -> dict[str, Any]:
    ownership = getattr(controller, "ownership", {})
    return {
        "ownership": sorted(
            (str(handle), TargetLabel.parse(label.key).key)
            for handle, label in ownership.items()
        ),
        "leave_observed": getattr(controller, "_absent_handle", None) is not None,
        "rejoin_observed": getattr(controller, "_rejoined_handle", None) is not None,
        "returned_to_stage": bool(
            getattr(controller, "_returned_to_stage", False)
        ),
    }


def _build_selected_oracle_behavioral_execution(
    source: G0EpisodeSource,
    ledger: OracleSafetyLedger,
    *,
    cell: Cell | str = Cell.EVENT,
) -> OracleBehavioralExecution:
    """Execute one causal branch and retain only replay-certificate primitives."""

    validate_oracle_safety_ledger(source, ledger)
    env = UAVSourceIdentifiabilityEnv(source, Cell(cell))
    try:
        env.reset()
        qualification = oracle_qualification_from_safety_ledger(source, ledger)
        controller = MechanicallyQualifiedOracleController(
            source, env._handles, qualification, ledger
        )
        env._oracle_behavioral_candidate_id = ledger.selected_candidate_id
        env._oracle_behavioral_trace = []
        pending_events = env.consume_boundary_events()
        target_rows: list[np.ndarray] = []
        weakest_rows: list[float] = []
        for step in range(PHYSICAL_HORIZON):
            rows = env.current_rows()
            for event in pending_events:
                if event.kind == "LEAVE":
                    controller.on_leave(event.previous_handle, rows)
                elif event.kind == "REJOIN" and event.current_handle is not None:
                    controller.on_rejoin(
                        event.previous_handle,
                        event.current_handle,
                        event.physical_step,
                    )
                else:
                    raise G0RealizationError("behavioral replay lifecycle event drifted")
            information = make_current_information(
                source,
                rows=rows,
                user_demand_mbps=np.asarray(
                    env.last_user_demand_bps, dtype=np.float64
                )
                / 1e6,
                user_delivered_rate_mbps=np.asarray(
                    env.last_user_rates_mbps, dtype=np.float64
                ),
                channel_association=np.asarray(env.connections, dtype=np.bool_)[
                    env._storage_to_internal
                ],
            )
            weakest_rows.append(float(information.weakest_hotspot_service))
            pre_action_context = _pre_action_context(
                env, controller.ownership, ledger.selected_candidate_id
            )
            target_map = controller.target_map(
                information, physical_step=step
            )
            targets, active = target_map_to_dense(
                rows=rows,
                target_map=target_map,
            )
            target_rows.append(np.asarray(targets, dtype=np.float64).copy())
            positions_internal = np.asarray(
                env.uav_positions, dtype=np.float64
            ).copy()
            targets_internal = np.zeros_like(targets)
            targets_internal[env._storage_to_internal] = targets
            active_internal = np.zeros(PHYSICAL_UAVS, dtype=np.bool_)
            active_internal[env._storage_to_internal] = active
            actions_internal = g1_common_target_actions(
                physical_positions=positions_internal,
                target_positions=targets_internal,
                active_mask=active_internal,
                max_speed=env.max_speed,
                max_vertical_speed=env.max_vertical_speed_mps,
                time_step=env.time_step,
            )
            actions = actions_internal[env._storage_to_internal]
            storage_actions = g1_common_target_actions(
                physical_positions=np.stack([row.position for row in rows]),
                target_positions=targets,
                active_mask=active,
                max_speed=env.max_speed,
                max_vertical_speed=env.max_vertical_speed_mps,
                time_step=env.time_step,
            )
            if not np.array_equal(actions, storage_actions):
                raise G0RealizationError(
                    "common transducer lost registered permutation equivariance"
                )
            transducer_evidence = _common_transducer_evidence(
                physical_positions=positions_internal,
                target_positions=targets_internal,
                active_mask=active_internal,
                raw_action=actions_internal,
            )
            transition = env.step_dense(
                actions,
                oracle_ownership=controller.ownership,
                oracle_pre_action_context=pre_action_context,
                oracle_common_transducer_evidence=transducer_evidence,
            )
            if transition.physical_step != step:
                raise G0RealizationError("behavioral replay physical step drifted")
            pending_events = transition.boundary_events
        if pending_events:
            raise G0RealizationError("behavioral replay left lifecycle events pending")
        steps = tuple(env._oracle_behavioral_trace)
        target_evidence = _NativeArrayEvidence.from_array(
            np.stack(target_rows).astype(np.float64, copy=False)
        )
        weakest_evidence = _NativeArrayEvidence.from_array(
            np.asarray(weakest_rows, dtype=np.float64)
        )
        digest = sha256_json(
            {
                "selected_candidate_id": ledger.selected_candidate_id,
                "return_ready_step": controller._return_ready_step,
                "steps": [step.to_primitive() for step in steps],
                "target_schedule": target_evidence.to_primitive(),
                "pre_action_weakest_service": weakest_evidence.to_primitive(),
            }
        )
        return OracleBehavioralExecution(
            selected_candidate_id=ledger.selected_candidate_id,
            return_ready_step=controller._return_ready_step,
            steps=steps,
            target_schedule=target_evidence,
            pre_action_weakest_service=weakest_evidence,
            trace_sha256=digest,
        )
    finally:
        env.close()


def build_selected_oracle_behavioral_replay(
    source: G0EpisodeSource,
    ledger: OracleSafetyLedger,
    *,
    cell: Cell | str = Cell.EVENT,
) -> tuple[OracleSafetyStepRecord, ...]:
    """Return the safety rows for one causal selected behavioral execution."""

    return _build_selected_oracle_behavioral_execution(
        source, ledger, cell=cell
    ).steps


def build_oracle_branch_aware_replay_evidence(
    source: G0EpisodeSource,
    ledger: OracleSafetyLedger,
) -> dict[str, Any]:
    """Build the registered P/B self-replay package without reranking."""

    validate_oracle_safety_ledger(source, ledger)
    selected_label = TargetLabel.parse(ledger.selected_candidate_id)
    prebehavior_self_replay, prestate = _oracle_candidate_trace(
        source, selected_label
    )
    if sha256_json(prestate) != ledger.common_prestate_sha256:
        raise G0RealizationError("prebehavior self-replay prestate drifted")
    behavioral_execution = _build_selected_oracle_behavioral_execution(
        source, ledger
    )
    behavioral_self_replay = _build_selected_oracle_behavioral_execution(
        source, ledger
    )
    certificate = validate_oracle_branch_aware_replay(
        source,
        ledger,
        prebehavior_self_replay,
        behavioral_execution,
        behavioral_self_replay,
    )
    return {
        "schema_version": 1,
        "ledger_sha256": ledger.content_sha256,
        "selected_candidate_id": ledger.selected_candidate_id,
        "prebehavior_self_replay": prebehavior_self_replay.to_primitive(),
        "behavioral_execution": behavioral_execution.to_primitive(),
        "behavioral_self_replay": behavioral_self_replay.to_primitive(),
        "certificate": certificate.to_primitive(),
    }


def run_g0_episode(
    source: G0EpisodeSource,
    *,
    control: Control | str,
    cell: Cell | str,
) -> EpisodeRunEvidence:
    """Execute one frozen no-learning episode.

    This function is the future result-bearing kernel.  Code acceptance and
    readiness do not call it over the registered 128-episode inventory.
    """

    chosen_control, chosen_cell = Control(control), Cell(cell)
    env = UAVSourceIdentifiabilityEnv(source, chosen_cell)
    try:
        env.reset()
        controller = _controller_for_run(
            source,
            chosen_control,
            env._handles,
            max_speed=env.max_speed,
            max_vertical_speed=env.max_vertical_speed_mps,
            time_step=env.time_step,
        )
        if chosen_control is Control.ORACLE:
            env._oracle_behavioral_candidate_id = (
                controller.safety_ledger.selected_candidate_id
            )
            env._oracle_behavioral_trace = []
        pending_events = env.consume_boundary_events()
        demand_inputs: list[np.ndarray] = []
        delivered_inputs: list[np.ndarray] = []
        association_inputs: list[np.ndarray] = []
        rates: list[np.ndarray] = []
        target_trace: list[list[list[float]]] = []
        action_trace: list[list[list[float]]] = []
        velocity_trace: list[list[list[float]]] = []
        position_trace: list[list[list[float]]] = [env.uav_positions.tolist()]
        active_mask_trace: list[list[bool]] = []
        lifecycle_events: list[LifecycleBoundaryEvent] = []
        tracker_failures = 0
        action_support_violations = 0
        ownership_violations = 0
        guard_blocks = 0
        for step in range(PHYSICAL_HORIZON):
            rows = env.current_rows()
            for event in pending_events:
                lifecycle_events.append(event)
                if event.kind == "LEAVE":
                    controller.on_leave(event.previous_handle, rows)
                elif event.kind == "REJOIN":
                    if event.current_handle is None:
                        raise G0RealizationError("rejoin event omitted its new lifecycle")
                    controller.on_rejoin(
                        event.previous_handle, event.current_handle, event.physical_step
                    )
                else:
                    raise G0RealizationError("unknown G0 lifecycle boundary")
            demand_input = np.asarray(env.last_user_demand_bps, dtype=np.float64) / 1e6
            delivered_input = np.asarray(env.last_user_rates_mbps, dtype=np.float64)
            association_input = np.asarray(env.connections, dtype=np.bool_)[
                env._storage_to_internal
            ]
            information = make_current_information(
                source,
                rows=rows,
                user_demand_mbps=demand_input,
                user_delivered_rate_mbps=delivered_input,
                channel_association=association_input,
            )
            target_map = controller.target_map(
                information,
                physical_step=step,
            )
            try:
                dense_targets, active = target_map_to_dense(rows=rows, target_map=target_map)
            except G0RealizationError:
                ownership_violations += 1
                raise
            positions = np.stack([row.position for row in rows])
            actions = g1_common_target_actions(
                physical_positions=positions,
                target_positions=dense_targets,
                active_mask=active,
                max_speed=env.max_speed,
                max_vertical_speed=env.max_vertical_speed_mps,
                time_step=env.time_step,
            )
            if not np.isfinite(actions).all() or np.any(np.abs(actions) > 1.0):
                action_support_violations += 1
            if not np.array_equal(actions[~active], np.zeros_like(actions[~active])):
                tracker_failures += 1
            transition = env.step_dense(actions)
            if transition.physical_step != step:
                raise G0RealizationError("physical-step ledger is not exactly 0..499")
            if (transition.terminated or transition.truncated) and step != PHYSICAL_HORIZON - 1:
                raise G0RealizationError("G0 environment terminated before H=500")
            if not np.array_equal(transition.executed_action_mask, active):
                tracker_failures += 1
            guard_blocks += transition.backhaul_guard_blocked_actions
            demand_inputs.append(demand_input.copy())
            delivered_inputs.append(delivered_input.copy())
            association_inputs.append(association_input.copy())
            rates.append(transition.delivered_user_rates_mbps.copy())
            target_trace.append(dense_targets.tolist())
            action_trace.append(actions.tolist())
            velocity_trace.append(transition.actual_velocities.tolist())
            position_trace.append(transition.positions_after.tolist())
            active_mask_trace.append(active.tolist())
            pending_events = transition.boundary_events
        if pending_events:
            raise G0RealizationError("lifecycle boundary remained unconsumed after H=500")
        expected_event_rows = (
            ()
            if chosen_cell is Cell.NO_EVENT
            else (
                ("LEAVE", source.event.onset),
                ("REJOIN", source.event.rejoin),
            )
        )
        actual_event_rows = tuple(
            (event.kind, event.physical_step) for event in lifecycle_events
        )
        if actual_event_rows != expected_event_rows:
            raise G0RealizationError("leave/rejoin boundary inventory or timing drifted")
        delivered = np.stack(rates)
        weakest = weakest_hotspot_service(delivered, source.geometry.user_hotspots)
        metrics = compute_episode_metrics(
            weakest,
            episode_id=source.geometry.episode_id,
            control=chosen_control,
            cell=chosen_cell,
            onset=source.event.onset,
            duration=source.event.duration,
        )
        controller_evidence = controller.evidence()
        if chosen_control is Control.ORACLE:
            selected_label = TargetLabel.parse(
                controller.safety_ledger.selected_candidate_id
            )
            prebehavior_self_replay, _prestate = _oracle_candidate_trace(
                source, selected_label
            )
            target_evidence = _NativeArrayEvidence.from_array(
                np.asarray(target_trace, dtype=np.float64)
            )
            pre_action_weakest = _NativeArrayEvidence.from_array(
                weakest_hotspot_service(
                    np.stack(delivered_inputs), source.geometry.user_hotspots
                )
            )
            actual_steps = tuple(env._oracle_behavioral_trace)
            actual_execution = OracleBehavioralExecution(
                selected_candidate_id=controller.safety_ledger.selected_candidate_id,
                return_ready_step=controller._return_ready_step,
                steps=actual_steps,
                target_schedule=target_evidence,
                pre_action_weakest_service=pre_action_weakest,
                trace_sha256=sha256_json(
                    {
                        "selected_candidate_id": (
                            controller.safety_ledger.selected_candidate_id
                        ),
                        "return_ready_step": controller._return_ready_step,
                        "steps": [step.to_primitive() for step in actual_steps],
                        "target_schedule": target_evidence.to_primitive(),
                        "pre_action_weakest_service": (
                            pre_action_weakest.to_primitive()
                        ),
                    }
                ),
            )
            behavioral_self_replay = _build_selected_oracle_behavioral_execution(
                source, controller.safety_ledger
            )
            behavioral_certificate = validate_oracle_branch_aware_replay(
                source,
                controller.safety_ledger,
                prebehavior_self_replay,
                actual_execution,
                behavioral_self_replay,
            )
            controller_evidence["behavioral_replay_certificate"] = (
                behavioral_certificate.to_primitive()
            )
        canonical_controller_state = _canonical_controller_state(controller)
        oracle_failures = int(
            chosen_control is Control.ORACLE
            and not bool(controller_evidence["qualification"]["passed"])
        )
        return EpisodeRunEvidence(
            episode_id=source.geometry.episode_id,
            control=chosen_control,
            cell=chosen_cell,
            metrics=metrics,
            source_sha256=source.to_primitive()["sha256"],
            user_demand_input_mbps=np.stack(demand_inputs),
            user_delivered_input_mbps=np.stack(delivered_inputs),
            channel_association_input=np.stack(association_inputs),
            delivered_user_rates_mbps=delivered,
            target_trace=np.asarray(target_trace, dtype=np.float64),
            raw_action_trace=np.asarray(action_trace, dtype=np.float32),
            executed_velocity_trace=np.asarray(velocity_trace, dtype=np.float64),
            position_trace=np.asarray(position_trace, dtype=np.float64),
            active_mask_trace=np.asarray(active_mask_trace, dtype=np.bool_),
            controller_evidence=controller_evidence,
            target_trace_sha256=sha256_json(target_trace),
            raw_action_trace_sha256=sha256_json(action_trace),
            executed_velocity_trace_sha256=sha256_json(velocity_trace),
            executed_position_trace_sha256=sha256_json(position_trace),
            service_trace_sha256=hashlib.sha256(
                delivered.astype(np.float64).tobytes(order="C")
            ).hexdigest(),
            controller_state_sha256=sha256_json(canonical_controller_state),
            lifecycle_events=tuple(lifecycle_events),
            tracker_failures=tracker_failures,
            action_support_violations=action_support_violations,
            ownership_violations=ownership_violations,
            backhaul_guard_blocked_actions=guard_blocks,
            oracle_qualification_failures=oracle_failures,
            weakest_service=weakest,
        )
    finally:
        env.close()


@dataclass(frozen=True)
class EpisodeMetrics:
    episode_id: int
    control: Control
    cell: Cell
    onset: int
    duration: int
    j_event: float
    q_ordinary: float
    m_event: float
    a_control: float
    b_access: int
    c_cat: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "control", Control(self.control))
        object.__setattr__(self, "cell", Cell(self.cell))
        values = (
            self.j_event,
            self.q_ordinary,
            self.m_event,
            self.a_control,
        )
        if not all(math.isfinite(float(value)) for value in values):
            raise G0RealizationError("episode metric contains a nonfinite value")
        if self.b_access not in (0, 1) or self.c_cat not in (0, 1):
            raise G0RealizationError("binary episode metric is outside {0,1}")
        if not all(0.0 <= float(value) <= 1.0 for value in values[:3]):
            raise G0RealizationError("J/Q/M metric is outside [0,1]")
        expected_a = (
            min(float(self.j_event) / SERVICE_TARGET, float(self.q_ordinary) / SERVICE_TARGET)
            if self.cell is Cell.EVENT
            else float(self.q_ordinary) / SERVICE_TARGET
        )
        expected_b = int(expected_a >= 1.0)
        if float(self.a_control) != expected_a or int(self.b_access) != expected_b:
            raise G0RealizationError("A/B metrics do not reconstruct from J/Q")
        if self.cell is Cell.NO_EVENT and (
            float(self.j_event) != 1.0 or int(self.c_cat) != 0
        ):
            raise G0RealizationError("NO_EVENT J/C metric law drifted")

    def to_primitive(self) -> dict[str, Any]:
        return {
            "episode_id": int(self.episode_id),
            "control": self.control.value,
            "cell": self.cell.value,
            "onset": int(self.onset),
            "duration": int(self.duration),
            "J_event": float(self.j_event),
            "Q_ordinary": float(self.q_ordinary),
            "M_event": float(self.m_event),
            "A_control": float(self.a_control),
            "B_access": int(self.b_access),
            "C_cat": int(self.c_cat),
        }


def weakest_hotspot_service_row(
    delivered_user_rates_mbps: Sequence[float],
    user_hotspots: Sequence[int],
) -> float:
    rates = np.asarray(delivered_user_rates_mbps, dtype=np.float64)
    memberships = np.asarray(user_hotspots, dtype=np.int64)
    if rates.shape != (GROUND_USERS,) or memberships.shape != (GROUND_USERS,):
        raise G0RealizationError("single delivered-rate metric row is malformed")
    if not np.isfinite(rates).all() or np.any(rates < 0.0):
        raise G0RealizationError("single delivered-rate row is nonfinite/negative")
    fractions: list[float] = []
    for hotspot in range(HOTSPOT_COUNT):
        selected = memberships == hotspot
        if int(selected.sum()) != USERS_PER_HOTSPOT:
            raise G0RealizationError("metric hotspot does not contain exactly ten users")
        fractions.append(float(np.mean(rates[selected] >= QOS_RATE_THRESHOLD_MBPS)))
    return min(fractions)


def weakest_hotspot_service(
    delivered_user_rates_mbps: np.ndarray,
    user_hotspots: Sequence[int],
) -> np.ndarray:
    rates = np.asarray(delivered_user_rates_mbps, dtype=np.float64)
    memberships = np.asarray(user_hotspots, dtype=np.int64)
    if rates.shape != (PHYSICAL_HORIZON, GROUND_USERS) or memberships.shape != (
        GROUND_USERS,
    ):
        raise G0RealizationError("delivered-rate metric inventory mismatch")
    if not np.isfinite(rates).all() or np.any(rates < 0.0):
        raise G0RealizationError("delivered-rate rows must be finite and nonnegative")
    rho = np.empty((PHYSICAL_HORIZON, HOTSPOT_COUNT), dtype=np.float64)
    for hotspot in range(HOTSPOT_COUNT):
        selected = memberships == hotspot
        if int(selected.sum()) != USERS_PER_HOTSPOT:
            raise G0RealizationError("metric hotspot does not contain exactly ten users")
        rho[:, hotspot] = np.mean(
            rates[:, selected] >= QOS_RATE_THRESHOLD_MBPS, axis=1, dtype=np.float64
        )
    return np.min(rho, axis=1)


def _has_catastrophic_streak(window_values: np.ndarray) -> bool:
    below = np.asarray(window_values, dtype=np.float64) < CATASTROPHE_THRESHOLD
    streak = 0
    for value in below:
        streak = streak + 1 if bool(value) else 0
        if streak >= CATASTROPHE_STREAK:
            return True
    return False


def compute_episode_metrics(
    weakest_service: Sequence[float],
    *,
    episode_id: int,
    control: Control | str,
    cell: Cell | str,
    onset: int,
    duration: int,
) -> EpisodeMetrics:
    service = np.asarray(weakest_service, dtype=np.float64)
    chosen_cell = Cell(cell)
    if service.shape != (PHYSICAL_HORIZON,) or not np.isfinite(service).all():
        raise G0RealizationError("weakest-hotspot service row is incomplete/nonfinite")
    if np.any(service < 0.0) or np.any(service > 1.0):
        raise G0RealizationError("weakest-hotspot service is outside [0,1]")
    if chosen_cell is Cell.EVENT:
        start = int(onset)
        stop = int(onset) + int(duration) + RECOVERY_WINDOW_EXTENSION
        if start < 0 or stop >= PHYSICAL_HORIZON:
            raise G0RealizationError("event metric window is outside H=500")
        window_mask = np.zeros(PHYSICAL_HORIZON, dtype=np.bool_)
        window_mask[start : stop + 1] = True
        window = service[window_mask]
        deficit = np.maximum(0.0, SERVICE_TARGET - window) / SERVICE_TARGET
        j_event = 1.0 - float(np.mean(deficit, dtype=np.float64))
        q_ordinary = float(np.mean(service[~window_mask], dtype=np.float64))
        m_event = float(np.min(window))
        a_control = min(j_event / SERVICE_TARGET, q_ordinary / SERVICE_TARGET)
        c_cat = int(_has_catastrophic_streak(window))
    else:
        j_event = 1.0
        q_ordinary = float(np.mean(service, dtype=np.float64))
        m_event = float(np.min(service))
        a_control = q_ordinary / SERVICE_TARGET
        c_cat = 0
    return EpisodeMetrics(
        episode_id=int(episode_id),
        control=Control(control),
        cell=chosen_cell,
        onset=int(onset),
        duration=int(duration),
        j_event=j_event,
        q_ordinary=q_ordinary,
        m_event=m_event,
        a_control=a_control,
        b_access=int(a_control >= 1.0),
        c_cat=c_cat,
    )


def make_bootstrap_index_plan() -> np.ndarray:
    indices = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED)).integers(
        0,
        len(EPISODE_IDS),
        size=(BOOTSTRAP_RESAMPLES, len(EPISODE_IDS)),
        dtype=np.int64,
    )
    return indices


def bootstrap_bounds(
    values: Sequence[float], index_plan: np.ndarray
) -> tuple[float, float, float]:
    row = np.asarray(values, dtype=np.float64)
    indices = np.asarray(index_plan, dtype=np.int64)
    if row.shape != (len(EPISODE_IDS),) or not np.isfinite(row).all():
        raise G0RealizationError("continuous estimator requires 128 finite rows")
    if indices.shape != (BOOTSTRAP_RESAMPLES, len(EPISODE_IDS)):
        raise G0RealizationError("bootstrap index matrix is not 10000x128")
    if np.any(indices < 0) or np.any(indices >= len(EPISODE_IDS)):
        raise G0RealizationError("bootstrap index is outside the episode ledger")
    means = np.mean(row[indices], axis=1, dtype=np.float64)
    ordered = np.sort(means, kind="mergesort")
    return float(np.mean(row)), float(ordered[499]), float(ordered[9499])


def clopper_pearson_one_sided(successes: int, n: int = 128) -> tuple[float, float]:
    k, total = int(successes), int(n)
    if total != len(EPISODE_IDS) or not 0 <= k <= total:
        raise G0RealizationError("Clopper-Pearson inventory must be k of n=128")
    lower = 0.0 if k == 0 else float(beta.ppf(0.05, k, total - k + 1))
    upper = 1.0 if k == total else float(beta.ppf(0.95, k + 1, total - k))
    if not (math.isfinite(lower) and math.isfinite(upper)):
        raise G0RealizationError("Clopper-Pearson bound is nonfinite")
    return lower, upper


@dataclass(frozen=True)
class EpisodeValidityRecord:
    """Primitive per-episode certificate counters and matched digests."""

    episode_id: int
    source_event_digest: str
    source_no_event_digest: str
    sameinfo_no_event_digest: str
    no_reallocation_no_event_digest: str
    geometry_support_violations: int
    rng_namespace_violations: int
    pairing_mismatches: int
    assignment_failures: int
    tracker_failures: int
    oracle_qualification_failures: int
    action_support_violations: int
    information_visibility_violations: int
    ownership_violations: int
    survivor_continuity_violations: int
    permutation_mismatches: int
    metric_reconstruction_mismatches: int
    missing_rows: int
    nonfinite_rows: int
    oracle_exact_physical_impossibility: bool = False

    def error_names(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.source_event_digest != self.source_no_event_digest:
            errors.append("event_no_event_source_pairing")
        if self.sameinfo_no_event_digest != self.no_reallocation_no_event_digest:
            errors.append("no_event_control_identity")
        counters = {
            "geometry_support": self.geometry_support_violations,
            "rng_independence": self.rng_namespace_violations,
            "pairing": self.pairing_mismatches,
            "target_assignment": self.assignment_failures,
            "target_tracker": self.tracker_failures,
            "oracle_qualification": self.oracle_qualification_failures,
            "action_support": self.action_support_violations,
            "information_visibility": self.information_visibility_violations,
            "ownership": self.ownership_violations,
            "survivor_continuity": self.survivor_continuity_violations,
            "permutation": self.permutation_mismatches,
            "metric_arithmetic": self.metric_reconstruction_mismatches,
            "row_completeness": self.missing_rows,
            "nonfinite_row": self.nonfinite_rows,
        }
        for name, value in counters.items():
            if int(value) != 0:
                errors.append(name)
        return tuple(errors)


def _reconstruct_controller_trace(
    source: G0EpisodeSource,
    run: EpisodeRunEvidence,
) -> tuple[np.ndarray, dict[str, Any], str]:
    handles = list(initial_lifecycle_handles(source))
    owner_row = source.assignment.row_to_target.index(source.event.owner_target.key)
    controller = _controller_for_run(
        source,
        run.control,
        handles,
        max_speed=30.0,
        max_vertical_speed=5.0,
        time_step=1.0,
    )
    targets: list[np.ndarray] = []
    for step in range(PHYSICAL_HORIZON):
        active = run.active_mask_trace[step]
        if run.cell is Cell.EVENT and step == source.event.rejoin:
            previous = handles[owner_row]
            current = replacement_lifecycle_handle(source, previous)
            handles[owner_row] = current
        rows = tuple(
            AnonymousLifecycleRow(
                handle=handles[row],
                position=run.position_trace[step, row],
                velocity=(
                    np.zeros(3, dtype=np.float64)
                    if step == 0
                    else run.executed_velocity_trace[step - 1, row]
                ),
                active=bool(active[row]),
                service_available=bool(active[row]),
            )
            for row in range(PHYSICAL_UAVS)
        )
        if run.cell is Cell.EVENT and step == source.event.onset:
            controller.on_leave(handles[owner_row], rows)
        if run.cell is Cell.EVENT and step == source.event.rejoin:
            controller.on_rejoin(previous, handles[owner_row], step)
        information = make_current_information(
            source,
            rows=rows,
            user_demand_mbps=run.user_demand_input_mbps[step],
            user_delivered_rate_mbps=run.user_delivered_input_mbps[step],
            channel_association=run.channel_association_input[step],
        )
        target_map = controller.target_map(
            information,
            physical_step=step,
        )
        dense, reconstructed_active = target_map_to_dense(
            rows=rows,
            target_map=target_map,
        )
        if not np.array_equal(reconstructed_active, active):
            raise G0RealizationError("controller reconstruction changed active mask")
        targets.append(dense)
    evidence = controller.evidence()
    state_digest = sha256_json(_canonical_controller_state(controller))
    return np.stack(targets), evidence, state_digest


def _authoritative_replay_errors(
    source: G0EpisodeSource,
    run: EpisodeRunEvidence,
) -> tuple[str, ...]:
    """Replay the authoritative environment law and compare every result-bearing row."""

    replay = run_g0_episode(source, control=run.control, cell=run.cell)
    errors: list[str] = []
    arrays = (
        "user_demand_input_mbps",
        "user_delivered_input_mbps",
        "channel_association_input",
        "delivered_user_rates_mbps",
        "target_trace",
        "raw_action_trace",
        "executed_velocity_trace",
        "position_trace",
        "active_mask_trace",
        "weakest_service",
    )
    for name in arrays:
        if not np.array_equal(getattr(run, name), getattr(replay, name)):
            errors.append(f"environment_replay_{name}")
    scalar_fields = (
        "episode_id",
        "control",
        "cell",
        "source_sha256",
        "target_trace_sha256",
        "raw_action_trace_sha256",
        "executed_velocity_trace_sha256",
        "executed_position_trace_sha256",
        "service_trace_sha256",
        "controller_state_sha256",
        "tracker_failures",
        "action_support_violations",
        "ownership_violations",
        "backhaul_guard_blocked_actions",
        "oracle_qualification_failures",
    )
    for name in scalar_fields:
        if getattr(run, name) != getattr(replay, name):
            errors.append(f"environment_replay_{name}")
    if run.metrics.to_primitive() != replay.metrics.to_primitive():
        errors.append("environment_replay_metrics")
    if dict(run.controller_evidence) != dict(replay.controller_evidence):
        errors.append("environment_replay_controller_evidence")
    if tuple(event.to_primitive() for event in run.lifecycle_events) != tuple(
        event.to_primitive() for event in replay.lifecycle_events
    ):
        errors.append("environment_replay_lifecycle")
    return tuple(errors)


def _validate_run_primitives(
    source: G0EpisodeSource,
    run: EpisodeRunEvidence,
) -> tuple[EpisodeMetrics, tuple[str, ...]]:
    errors: list[str] = []
    errors.extend(_authoritative_replay_errors(source, run))
    if run.episode_id != source.geometry.episode_id:
        errors.append("episode_identity")
    if run.source_sha256 != source.to_primitive()["sha256"]:
        errors.append("source_digest")
    expected_delivered_inputs = np.concatenate(
        (
            np.zeros((1, GROUND_USERS), dtype=np.float64),
            run.delivered_user_rates_mbps[:-1],
        ),
        axis=0,
    )
    if not np.array_equal(run.user_delivered_input_mbps, expected_delivered_inputs):
        errors.append("current_service_history")
    reconstructed_weakest = weakest_hotspot_service(
        run.delivered_user_rates_mbps, source.geometry.user_hotspots
    )
    if not np.array_equal(run.weakest_service, reconstructed_weakest):
        errors.append("weakest_service")
    reconstructed_metrics = compute_episode_metrics(
        reconstructed_weakest,
        episode_id=run.episode_id,
        control=run.control,
        cell=run.cell,
        onset=source.event.onset,
        duration=source.event.duration,
    )
    if run.metrics.to_primitive() != reconstructed_metrics.to_primitive():
        errors.append("metric_arithmetic")
    try:
        expected_targets, expected_controller_evidence, expected_state_digest = (
            _reconstruct_controller_trace(source, run)
        )
        if not np.array_equal(run.target_trace, expected_targets):
            errors.append("controller_target_trace")
        if dict(run.controller_evidence) != expected_controller_evidence:
            errors.append("controller_evidence")
        if run.controller_state_sha256 != expected_state_digest:
            errors.append("controller_state")
    except G0RealizationError:
        errors.append("controller_reconstruction")
    digest_rows = {
        "target_trace": (run.target_trace_sha256, sha256_json(run.target_trace.tolist())),
        "raw_action_trace": (
            run.raw_action_trace_sha256,
            sha256_json(run.raw_action_trace.tolist()),
        ),
        "executed_velocity_trace": (
            run.executed_velocity_trace_sha256,
            sha256_json(run.executed_velocity_trace.tolist()),
        ),
        "executed_position_trace": (
            run.executed_position_trace_sha256,
            sha256_json(run.position_trace.tolist()),
        ),
        "service_trace": (
            run.service_trace_sha256,
            hashlib.sha256(
                run.delivered_user_rates_mbps.astype(np.float64).tobytes(order="C")
            ).hexdigest(),
        ),
    }
    errors.extend(
        name for name, (stored, expected) in digest_rows.items() if stored != expected
    )
    expected_mask = np.stack(
        [
            np.asarray(
                [
                    source.event.active(step, run.cell)
                    if row == source.assignment.row_to_target.index(
                        source.event.owner_target.key
                    )
                    else True
                    for row in range(PHYSICAL_UAVS)
                ],
                dtype=np.bool_,
            )
            for step in range(PHYSICAL_HORIZON)
        ]
    )
    if not np.array_equal(run.active_mask_trace, expected_mask):
        errors.append("active_mask")
    if not np.array_equal(
        run.position_trace[0, :, :2], source.geometry.physical_xy
    ) or not np.array_equal(
        run.position_trace[:, :, 2],
        np.full((PHYSICAL_HORIZON + 1, PHYSICAL_UAVS), FIXED_ALTITUDE_M),
    ):
        errors.append("position_provenance")
    for step in range(PHYSICAL_HORIZON):
        expected_actions = actions_toward_targets(
            physical_positions=run.position_trace[step],
            target_positions=run.target_trace[step],
            active_mask=run.active_mask_trace[step],
            max_speed=30.0,
            max_vertical_speed=5.0,
            time_step=1.0,
        )
        if not np.array_equal(run.raw_action_trace[step], expected_actions):
            errors.append("target_tracker")
            break
    inactive = ~run.active_mask_trace
    if (
        not np.array_equal(
            run.raw_action_trace[inactive],
            np.zeros((int(inactive.sum()), ACTION_DIM), dtype=np.float32),
        )
        or not np.array_equal(
            run.executed_velocity_trace[inactive],
            np.zeros((int(inactive.sum()), 3), dtype=np.float64),
        )
    ):
        errors.append("inactive_authority")
    expected_lifecycle = (
        ()
        if run.cell is Cell.NO_EVENT
        else (("LEAVE", source.event.onset), ("REJOIN", source.event.rejoin))
    )
    actual_lifecycle = tuple(
        (event.kind, event.physical_step) for event in run.lifecycle_events
    )
    if actual_lifecycle != expected_lifecycle:
        errors.append("lifecycle_inventory")
    if run.cell is Cell.EVENT and len(run.lifecycle_events) == 2:
        leave, rejoin = run.lifecycle_events
        if (
            leave.previous_handle != rejoin.previous_handle
            or rejoin.current_handle is None
            or rejoin.current_handle == leave.previous_handle
        ):
            errors.append("epoch_replacement")
    if any(
        int(value) != 0
        for value in (
            run.tracker_failures,
            run.action_support_violations,
            run.ownership_violations,
        )
    ):
        errors.append("registered_runtime_counter")
    if run.control is Control.ORACLE:
        try:
            ledger = oracle_safety_ledger_from_primitive(
                run.controller_evidence["oracle_safety_ledger"]
            )
            qualification = oracle_qualification_from_safety_ledger(source, ledger)
            if (
                run.oracle_qualification_failures != 0
                or run.controller_evidence.get("qualification")
                != qualification.to_primitive()
                or run.controller_evidence.get("behavioral_replay_certificate", {}).get(
                    "ledger_sha256"
                )
                != ledger.content_sha256
                or run.controller_evidence.get("behavioral_replay_certificate", {}).get(
                    "behavioral_replay_sha256"
                )
                is None
            ):
                errors.append("oracle_qualification")
        except (G0RealizationError, KeyError, TypeError, ValueError):
            errors.append("oracle_qualification")
    return reconstructed_metrics, tuple(sorted(set(errors)))


def build_episode_validity_record(
    source: G0EpisodeSource,
    runs: Mapping[tuple[Control | str, Cell | str], EpisodeRunEvidence],
) -> tuple[EpisodeValidityRecord, dict[tuple[Control, Cell], EpisodeMetrics]]:
    """Reconstruct one validity row from the six actual control/cell traces."""

    normalized: dict[tuple[Control, Cell], EpisodeRunEvidence] = {}
    for key, run in runs.items():
        normalized_key = (Control(key[0]), Cell(key[1]))
        if normalized_key in normalized:
            raise G0RealizationError("duplicate G0 episode run identity")
        if run.control is not normalized_key[0] or run.cell is not normalized_key[1]:
            raise G0RealizationError("mapped run identity differs from primitive run")
        normalized[normalized_key] = run
    expected_keys = {(control, cell) for control in Control for cell in Cell}
    if set(normalized) != expected_keys:
        raise G0RealizationError("episode validity requires all six control/cell runs")
    metrics: dict[tuple[Control, Cell], EpisodeMetrics] = {}
    per_run_errors: list[str] = []
    for key, run in normalized.items():
        metric, errors = _validate_run_primitives(source, run)
        metrics[key] = metric
        per_run_errors.extend(errors)

    same_no = normalized[(Control.SAME_INFORMATION, Cell.NO_EVENT)]
    none_no = normalized[(Control.NO_REALLOCATION, Cell.NO_EVENT)]
    no_event_pairs = (
        (same_no.user_demand_input_mbps, none_no.user_demand_input_mbps),
        (same_no.user_delivered_input_mbps, none_no.user_delivered_input_mbps),
        (same_no.channel_association_input, none_no.channel_association_input),
        (same_no.target_trace, none_no.target_trace),
        (same_no.raw_action_trace, none_no.raw_action_trace),
        (same_no.executed_velocity_trace, none_no.executed_velocity_trace),
        (same_no.position_trace, none_no.position_trace),
        (same_no.delivered_user_rates_mbps, none_no.delivered_user_rates_mbps),
    )
    no_event_equal = all(np.array_equal(left, right) for left, right in no_event_pairs)
    no_event_equal &= same_no.controller_state_sha256 == none_no.controller_state_sha256

    same_event = normalized[(Control.SAME_INFORMATION, Cell.EVENT)]
    none_event = normalized[(Control.NO_REALLOCATION, Cell.EVENT)]
    selected_handle = same_event.controller_evidence.get("selected_reserve")
    initial_handles = initial_lifecycle_handles(source)
    selected_row = (
        initial_handles.index(str(selected_handle))
        if selected_handle in initial_handles
        else -1
    )
    owner_row = source.assignment.row_to_target.index(source.event.owner_target.key)
    survivor_rows = [
        row for row in range(PHYSICAL_UAVS) if row not in {owner_row, selected_row}
    ]
    survivor_equal = bool(
        selected_row >= 0
        and np.array_equal(
            same_event.target_trace[:, survivor_rows],
            none_event.target_trace[:, survivor_rows],
        )
        and np.array_equal(
            same_event.raw_action_trace[:, survivor_rows],
            none_event.raw_action_trace[:, survivor_rows],
        )
        and np.array_equal(
            same_event.position_trace[:, survivor_rows],
            none_event.position_trace[:, survivor_rows],
        )
    )
    source_digest = source.to_primitive()["sha256"]
    tracker_failures = sum("target_tracker" in error for error in per_run_errors)
    metric_failures = sum("metric_arithmetic" in error for error in per_run_errors)
    missing_or_nonfinite = sum(
        name.endswith("trace") or name == "position_provenance"
        for name in per_run_errors
    )
    permutation_order = np.asarray((3, 1, 7, 0, 6, 2, 5, 4), dtype=np.int64)
    permutation_failures = 0
    for run in normalized.values():
        permuted = actions_toward_targets(
            physical_positions=run.position_trace[0, permutation_order],
            target_positions=run.target_trace[0, permutation_order],
            active_mask=run.active_mask_trace[0, permutation_order],
            max_speed=30.0,
            max_vertical_speed=5.0,
            time_step=1.0,
        )
        restored = np.empty_like(permuted)
        restored[permutation_order] = permuted
        permutation_failures += int(
            not np.array_equal(restored, run.raw_action_trace[0])
        )
    record = EpisodeValidityRecord(
        episode_id=source.geometry.episode_id,
        source_event_digest=source_digest,
        source_no_event_digest=source_digest,
        sameinfo_no_event_digest=sha256_json(
            {
                "target": same_no.target_trace_sha256,
                "raw": same_no.raw_action_trace_sha256,
                "executed": same_no.executed_velocity_trace_sha256,
                "position": same_no.executed_position_trace_sha256,
                "service": same_no.service_trace_sha256,
                "controller": same_no.controller_state_sha256,
            }
        ),
        no_reallocation_no_event_digest=sha256_json(
            {
                "target": none_no.target_trace_sha256,
                "raw": none_no.raw_action_trace_sha256,
                "executed": none_no.executed_velocity_trace_sha256,
                "position": none_no.executed_position_trace_sha256,
                "service": none_no.service_trace_sha256,
                "controller": none_no.controller_state_sha256,
            }
        ),
        geometry_support_violations=0,
        rng_namespace_violations=0,
        pairing_mismatches=int(not no_event_equal),
        assignment_failures=int(not source.assignment.passed),
        tracker_failures=tracker_failures,
        oracle_qualification_failures=sum(
            run.oracle_qualification_failures for run in normalized.values()
        ),
        action_support_violations=sum(
            run.action_support_violations for run in normalized.values()
        ),
        information_visibility_violations=sum(
            int(
                any(
                    int(value) != 0
                    for key, value in run.controller_evidence.items()
                    if key.endswith("read_count")
                )
            )
            for run in normalized.values()
        ),
        ownership_violations=sum(run.ownership_violations for run in normalized.values()),
        survivor_continuity_violations=int(not survivor_equal),
        permutation_mismatches=permutation_failures,
        metric_reconstruction_mismatches=metric_failures,
        missing_rows=missing_or_nonfinite + len(set(per_run_errors)),
        nonfinite_rows=0,
        oracle_exact_physical_impossibility=False,
    )
    return record, metrics


def _cell_rows(
    rows: Mapping[tuple[Control | str, Cell | str], Sequence[EpisodeMetrics]],
    control: Control,
    cell: Cell,
) -> tuple[EpisodeMetrics, ...]:
    candidates = None
    for key, value in rows.items():
        if Control(key[0]) is control and Cell(key[1]) is cell:
            if candidates is not None:
                raise G0RealizationError("duplicate control/cell metric inventory")
            candidates = tuple(value)
    if candidates is None or len(candidates) != len(EPISODE_IDS):
        raise G0RealizationError("control/cell metric inventory is not 128 rows")
    if tuple(row.episode_id for row in candidates) != EPISODE_IDS:
        raise G0RealizationError("episode metric rows are not ordered IDs 0..127")
    if any(row.control is not control or row.cell is not cell for row in candidates):
        raise G0RealizationError("episode metric row identity mismatch")
    return candidates


def _continuous_summary(
    rows: Sequence[EpisodeMetrics],
    attribute: str,
    index_plan: np.ndarray,
) -> dict[str, float]:
    mean, lower, upper = bootstrap_bounds(
        [float(getattr(row, attribute)) for row in rows], index_plan
    )
    return {"mean": mean, "BS_L95": lower, "BS_U95": upper}


def _binary_summary(rows: Sequence[EpisodeMetrics], attribute: str) -> dict[str, float | int]:
    successes = sum(int(getattr(row, attribute)) for row in rows)
    lower, upper = clopper_pearson_one_sided(successes)
    return {"successes": successes, "n": len(EPISODE_IDS), "CP_L95": lower, "CP_U95": upper}


def _build_analysis_from_reconstructed_rows(
    metric_rows: Mapping[tuple[Control | str, Cell | str], Sequence[EpisodeMetrics]],
    validity_records: Sequence[EpisodeValidityRecord],
    *,
    index_plan: np.ndarray | None = None,
) -> dict[str, Any]:
    """Reconstruct every G0 first-match gate from episode-level evidence."""

    if len(validity_records) != len(EPISODE_IDS) or tuple(
        record.episode_id for record in validity_records
    ) != EPISODE_IDS:
        raise G0RealizationError("validity records are not ordered IDs 0..127")
    plan = make_bootstrap_index_plan() if index_plan is None else np.asarray(index_plan)
    if not np.array_equal(plan, make_bootstrap_index_plan()):
        raise G0RealizationError("bootstrap index plan differs from PCG64 seed 2026072901")
    cells = {
        (control, cell): _cell_rows(metric_rows, control, cell)
        for control in Control
        for cell in Cell
    }
    continuous: dict[str, dict[str, float]] = {}
    binary: dict[str, dict[str, float | int]] = {}
    for control in Control:
        for cell in Cell:
            key = f"{control.value}|{cell.value}"
            for prefix, attribute in (
                ("A", "a_control"),
                ("J", "j_event"),
                ("Q", "q_ordinary"),
                ("M", "m_event"),
            ):
                continuous[f"{prefix}|{key}"] = _continuous_summary(
                    cells[(control, cell)], attribute, plan
                )
            binary[f"B|{key}"] = _binary_summary(
                cells[(control, cell)], "b_access"
            )
            binary[f"C|{key}"] = _binary_summary(
                cells[(control, cell)], "c_cat"
            )
    same_event = cells[(Control.SAME_INFORMATION, Cell.EVENT)]
    none_event = cells[(Control.NO_REALLOCATION, Cell.EVENT)]
    delta_j = np.asarray(
        [left.j_event - right.j_event for left, right in zip(same_event, none_event)],
        dtype=np.float64,
    )
    delta_m = np.asarray(
        [left.m_event - right.m_event for left, right in zip(same_event, none_event)],
        dtype=np.float64,
    )
    delta_a = np.asarray(
        [left.a_control - right.a_control for left, right in zip(same_event, none_event)],
        dtype=np.float64,
    )
    for name, values in (("Delta_A", delta_a), ("Delta_J", delta_j), ("Delta_M", delta_m)):
        mean, lower, upper = bootstrap_bounds(values, plan)
        continuous[name] = {"mean": mean, "BS_L95": lower, "BS_U95": upper}

    def cont(control: Control, cell: Cell) -> dict[str, float]:
        return continuous[f"A|{control.value}|{cell.value}"]

    def binary_row(prefix: str, control: Control, cell: Cell) -> dict[str, float | int]:
        return binary[f"{prefix}|{control.value}|{cell.value}"]

    oracle_pass = bool(
        cont(Control.ORACLE, Cell.EVENT)["BS_L95"] >= 1.0
        and cont(Control.ORACLE, Cell.NO_EVENT)["BS_L95"] >= 1.0
        and float(binary_row("B", Control.ORACLE, Cell.EVENT)["CP_L95"]) >= 0.90
        and float(binary_row("B", Control.ORACLE, Cell.NO_EVENT)["CP_L95"]) >= 0.90
        and all(record.oracle_qualification_failures == 0 for record in validity_records)
    )
    oracle_fail = bool(
        cont(Control.ORACLE, Cell.EVENT)["BS_U95"] < 1.0
        or cont(Control.ORACLE, Cell.NO_EVENT)["BS_U95"] < 1.0
        or float(binary_row("B", Control.ORACLE, Cell.EVENT)["CP_U95"]) < 0.90
        or float(binary_row("B", Control.ORACLE, Cell.NO_EVENT)["CP_U95"]) < 0.90
        or any(record.oracle_exact_physical_impossibility for record in validity_records)
    )
    oracle_status = (
        GateStatus.FAIL if oracle_fail else GateStatus.PASS if oracle_pass else GateStatus.OPEN
    )
    same_pass = bool(
        cont(Control.SAME_INFORMATION, Cell.EVENT)["BS_L95"] >= 1.0
        and cont(Control.SAME_INFORMATION, Cell.NO_EVENT)["BS_L95"] >= 1.0
        and float(binary_row("B", Control.SAME_INFORMATION, Cell.EVENT)["CP_L95"]) >= 0.90
        and float(binary_row("B", Control.SAME_INFORMATION, Cell.NO_EVENT)["CP_L95"]) >= 0.90
        and float(binary_row("C", Control.SAME_INFORMATION, Cell.EVENT)["CP_U95"]) <= 0.05
    )
    same_fail = bool(
        cont(Control.SAME_INFORMATION, Cell.EVENT)["BS_U95"] < 1.0
        or cont(Control.SAME_INFORMATION, Cell.NO_EVENT)["BS_U95"] < 1.0
        or float(binary_row("B", Control.SAME_INFORMATION, Cell.EVENT)["CP_U95"]) < 0.90
        or float(binary_row("B", Control.SAME_INFORMATION, Cell.NO_EVENT)["CP_U95"]) < 0.90
        or float(binary_row("C", Control.SAME_INFORMATION, Cell.EVENT)["CP_L95"]) > 0.05
    )
    same_status = GateStatus.PASS if same_pass else GateStatus.FAIL if same_fail else GateStatus.OPEN
    causal_pass = bool(
        cont(Control.NO_REALLOCATION, Cell.EVENT)["BS_U95"] < 1.0
        and float(binary_row("B", Control.NO_REALLOCATION, Cell.EVENT)["CP_U95"]) < 0.90
        and continuous["Delta_J"]["BS_L95"] > 0.0
        and continuous["Delta_M"]["mean"] >= 0.10
        and continuous["Delta_M"]["BS_L95"] > 0.05
    )
    causal_fail = bool(
        cont(Control.NO_REALLOCATION, Cell.EVENT)["BS_L95"] >= 1.0
        or float(binary_row("B", Control.NO_REALLOCATION, Cell.EVENT)["CP_L95"]) >= 0.90
        or continuous["Delta_J"]["BS_U95"] <= 0.0
        or continuous["Delta_M"]["mean"] < 0.10
        or continuous["Delta_M"]["BS_U95"] <= 0.05
    )
    causal_status = (
        GateStatus.PASS if causal_pass else GateStatus.FAIL if causal_fail else GateStatus.OPEN
    )
    validity_errors = sorted(
        {error for record in validity_records for error in record.error_names()}
    )
    valid = not validity_errors
    branch = select_result_branch(
        valid=valid,
        oracle_status=oracle_status,
        sameinfo_status=same_status,
        causal_status=causal_status,
    )
    return {
        "continuous": continuous,
        "binary": binary,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_index_sha256": hashlib.sha256(
            np.asarray(plan, dtype=np.int64).tobytes(order="C")
        ).hexdigest(),
        "quantile_rule": "sorted_no_interpolation_x500_x9500",
        "valid": valid,
        "validity_errors": validity_errors,
        "ORACLE_STATUS": oracle_status.value,
        "SAMEINFO_STATUS": same_status.value,
        "CAUSAL_STATUS": causal_status.value,
        "first_match_order": list(FIRST_MATCH_ORDER),
        "result_branch": branch,
    }


def build_analysis_evidence(
    episode_sources: Sequence[G0EpisodeSource],
    run_rows: Mapping[
        tuple[Control | str, Cell | str], Sequence[EpisodeRunEvidence]
    ],
    *,
    index_plan: np.ndarray | None = None,
) -> dict[str, Any]:
    """Only conclusion-bearing analyzer: reconstruct from six primitive traces."""

    sources = tuple(episode_sources)
    if len(sources) != len(EPISODE_IDS) or tuple(
        item.geometry.episode_id for item in sources
    ) != EPISODE_IDS:
        raise G0RealizationError("analysis sources are not exact episode IDs 0..127")
    normalized_rows: dict[tuple[Control, Cell], tuple[EpisodeRunEvidence, ...]] = {}
    for key, values in run_rows.items():
        normalized_key = (Control(key[0]), Cell(key[1]))
        if normalized_key in normalized_rows:
            raise G0RealizationError("duplicate control/cell run inventory")
        rows = tuple(values)
        if len(rows) != len(EPISODE_IDS) or tuple(
            row.episode_id for row in rows
        ) != EPISODE_IDS:
            raise G0RealizationError("run inventory is not ordered episode IDs 0..127")
        normalized_rows[normalized_key] = rows
    expected_keys = {(control, cell) for control in Control for cell in Cell}
    if set(normalized_rows) != expected_keys:
        raise G0RealizationError("analysis requires six exact control/cell inventories")

    metrics: dict[tuple[Control, Cell], list[EpisodeMetrics]] = {
        key: [] for key in expected_keys
    }
    validity: list[EpisodeValidityRecord] = []
    for episode_id, episode_source in enumerate(sources):
        record, reconstructed = build_episode_validity_record(
            episode_source,
            {
                key: normalized_rows[key][episode_id]
                for key in expected_keys
            },
        )
        validity.append(record)
        for key, metric in reconstructed.items():
            metrics[key].append(metric)
    return _build_analysis_from_reconstructed_rows(
        metrics,
        validity,
        index_plan=index_plan,
    )


def select_result_branch(
    *,
    valid: bool,
    oracle_status: GateStatus | str,
    sameinfo_status: GateStatus | str,
    causal_status: GateStatus | str,
) -> str:
    oracle = GateStatus(oracle_status)
    sameinfo = GateStatus(sameinfo_status)
    causal = GateStatus(causal_status)
    if not bool(valid):
        return INVALID_BRANCH
    if oracle is GateStatus.FAIL:
        return INFEASIBLE_BRANCH
    if oracle is GateStatus.PASS and sameinfo is GateStatus.FAIL:
        return ORACLE_ONLY_BRANCH
    if (
        oracle is GateStatus.PASS
        and sameinfo is GateStatus.PASS
        and causal is GateStatus.FAIL
    ):
        return NON_CAUSAL_BRANCH
    if (
        oracle is GateStatus.OPEN
        or (oracle is GateStatus.PASS and sameinfo is GateStatus.OPEN)
        or (
            oracle is GateStatus.PASS
            and sameinfo is GateStatus.PASS
            and causal is GateStatus.OPEN
        )
    ):
        return UNDERPOWERED_BRANCH
    if (
        oracle is GateStatus.PASS
        and sameinfo is GateStatus.PASS
        and causal is GateStatus.PASS
    ):
        return IDENTIFIED_BRANCH
    raise G0RealizationError("first-match status combination is contradictory")
