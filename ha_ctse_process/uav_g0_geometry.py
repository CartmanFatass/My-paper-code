"""Frozen geometry and source construction for UAV source-identifiability G0."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import itertools
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ha_ctse_process.uav_episode_schema import (
    ACTION_DIM,
    GROUND_USERS,
    PHYSICAL_HORIZON,
    PHYSICAL_UAVS,
    Cell,
    G0RealizationError,
    _readonly_array,
)


ALGORITHM_ID = "UAV_SOURCE_IDENTIFIABILITY_G0"
SOURCE_ID = "UAV_SOURCE_IDENTIFIABILITY_G0_P0"

GROUND_BASE_STATIONS = 1
HOTSPOT_COUNT = 3
USERS_PER_HOTSPOT = 10
FIXED_ALTITUDE_M = 50.0
USER_ALTITUDE_M = 1.5

RECOVERY_WINDOW_EXTENSION = 59

MAP_WIDTH_M = 8000.0
MAP_HEIGHT_M = 8000.0

class TargetKind(str, Enum):
    PRIMARY = "primary"
    STAGE = "stage"


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


def geometry_support_certificate(
    *,
    map_width: float,
    map_height: float,
    base_xy: np.ndarray,
) -> dict[str, Any]:
    """Prove the complete frozen geometry support for every episode angle.

    This proof is analytic and independent of the sampled ``phi``, users, UAV
    perturbations, or realized coordinates.  Each entry is the maximum radial
    distance from the map center over the complete support of that family.
    """

    width = float(map_width)
    height = float(map_height)
    base = _finite_array(base_xy, (2,), label="support-certificate base")
    if not (math.isfinite(width) and math.isfinite(height) and width > 0 and height > 0):
        raise G0RealizationError("support-certificate map dimensions are invalid")
    scale = min(width, height)
    margins = {
        "negative_x": float(base[0]),
        "positive_x": float(width - base[0]),
        "negative_y": float(base[1]),
        "positive_y": float(height - base[1]),
    }
    bounds = {
        "hotspot_centers": 0.300 * scale,
        "user_disks": (0.300 + 0.040) * scale,
        "primaries": math.hypot(0.300, 0.040) * scale,
        "primary_perturbation_disks": (
            math.hypot(0.300, 0.040) + 0.002
        )
        * scale,
        "stages": 0.050 * scale,
        "stage_perturbation_disks": (0.050 + 0.002) * scale,
        "gates": math.hypot(0.300 - 0.060, 0.040) * scale,
    }
    violations = [
        name
        for name, radial_bound in bounds.items()
        if any(radial_bound > margin for margin in margins.values())
    ]
    return {
        "certificate_kind": "analytic_radial_complete_support_every_phi_v2",
        "phi_domain": "[0,2*pi)",
        "scale": float(scale),
        "map_axis_inward_margins": margins,
        "support_radial_bounds": {
            name: float(value) for name, value in bounds.items()
        },
        "violations": violations,
        "violation_count": len(violations),
        "passed": not violations,
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
        analytic_support = geometry_support_certificate(
            map_width=width,
            map_height=height,
            base_xy=base,
        )
        if int(analytic_support["violation_count"]) != 0:
            raise G0RealizationError(
                "analytic every-phi geometry support certificate failed"
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
            "geometry_support_certificate": geometry_support_certificate(
                map_width=self.map_width,
                map_height=self.map_height,
                base_xy=self.base_xy,
            ),
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
