"""Frozen, result-blind contract for the SCDMP MF-RS-MK B01 replacement run.

This module contains the exact experiment inventory only.  It neither creates
an artifact root nor authorizes a result-bearing run.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
from typing import Final, Mapping

class ContractError(ValueError):
    """A supplied value differs from the frozen B01 observable."""


STUDY_ID: Final[str] = "SCDMP-MF-RS-MK-ORDER-VALUE-B01"
QUARANTINED_NAMED_RUN_ID: Final[str] = f"{STUDY_ID}-RUN-01"
NAMED_RUN_ID: Final[str] = f"{STUDY_ID}-RUN-01-REPLACEMENT-01"
ATTEMPT_ID: Final[str] = f"{NAMED_RUN_ID}-ATTEMPT-01"
RUN_LABEL: Final[str] = "RUN-01-REPLACEMENT-01"
SCHEMA: Final[str] = NAMED_RUN_ID
# The non-q scientific streams are an unchanged registered factor.  Keep the
# exact historical byte namespace even though the serialized run identity is new.
SCIENTIFIC_RNG_NAMESPACE: Final[str] = QUARANTINED_NAMED_RUN_ID
HELDOUT_NAMESPACE_TOKEN: Final[str] = f"SCDMP-MF-RS-MK-B01/heldout/{RUN_LABEL}"
RUN_02A_ID: Final[str] = f"{STUDY_ID}-RUN-02A"
RUN_02B_ID: Final[str] = f"{STUDY_ID}-RUN-02B"
SCIENCE_CARD_REVISION: Final[str] = (
    "SCDMP_MF_RS_MK_ORDER_VALUE_B01_SCIENCE_CARD_20260901"
)
TRAINING_SEEDS: Final[tuple[int, int]] = (1709, 2903)
K_VALUES: Final[tuple[int, int]] = (7, 13)
GRAPHS: Final[tuple[str, str]] = ("HR", "RH")
FOUNDATION_UPDATES: Final[int] = 160
EPISODES_PER_UPDATE: Final[int] = 12
OPTIMIZER_STEPS_PER_UPDATE: Final[int] = 12
ADAMW_STEPS_PER_FOUNDATION: Final[int] = 1_920
CHECKPOINT_UPDATES: Final[tuple[int, ...]] = (160,)
CURVE_UPDATES: Final[tuple[int, ...]] = tuple(range(0, 161, 20))
CURVE_MISSIONS_PER_CELL: Final[int] = 8
COMPETENCE_MISSIONS_PER_CELL: Final[int] = 32
DEVELOPMENT_TAPES: Final[tuple[int, ...]] = tuple(range(8))
HELDOUT_TAPES: Final[tuple[int, ...]] = tuple(range(16))
Q_PATTERNS: Final[tuple[tuple[int, ...], ...]] = (
    (0, 0, 1, 1, 1, 0),
    (0, 1, 1, 1, 0, 0),
    (1, 0, 0, 0, 1, 1),
    (1, 1, 0, 0, 0, 1),
)
Q_COUNTER_ADDRESS: Final[tuple[object, ...]] = (
    STUDY_ID, RUN_LABEL, "PRE_EVENT_Q_PATTERN", 0,
)

# Literal B01 copy of the existing host catalogue.  Keeping it local prevents
# the new run from importing or executing the consumed FCEOV package.
_LOAD_SHARE_ACTIONS: Final[tuple[tuple[int, int, int, int], ...]] = (
    (0, 0, 0, 0), (1, -1, 0, 0), (-1, 1, 0, 0),
    (0, 0, 1, -1), (0, 0, -1, 1), (1, 0, -1, 0),
    (-1, 0, 1, 0), (0, 1, 0, -1), (0, -1, 0, 1),
)
ACTION_TABLE: Final[tuple[tuple[int, tuple[int, int, int, int]], ...]] = tuple(
    (forward, share) for forward in (1, 2) for share in _LOAD_SHARE_ACTIONS
)

HR_ASSIGNMENT: Final[tuple[int, int, int, int]] = (4, 2, 1, 3)
RH_ASSIGNMENT: Final[tuple[int, int, int, int]] = (1, 4, 2, 3)


@dataclass(frozen=True, slots=True)
class StateSpec:
    cell: str
    k: int
    stratum: str
    target_tick: int
    source_seed: int


# The source foundation alternates across the k-by-stratum panel.  This is the
# precommitted checkerboard, not an outcome-selected assignment.
STATE_SPECS: Final[tuple[StateSpec, ...]] = (
    StateSpec("k7-early", 7, "early", 64, 1709),
    StateSpec("k7-middle", 7, "middle", 160, 2903),
    StateSpec("k7-late", 7, "late", 256, 1709),
    StateSpec("k13-early", 13, "early", 64, 2903),
    StateSpec("k13-middle", 13, "middle", 160, 1709),
    StateSpec("k13-late", 13, "late", 256, 2903),
)

ORDERED_BRANCHES: Final[tuple[str, ...]] = (
    "INVALID_OR_INCOMPLETE_ATTEMPT",
    "FOUNDATION_COMPETENCE_NOT_ESTABLISHED",
    "REACHABLE_STATE_PANEL_NOT_ESTABLISHED",
    "ACTION_CONSTRUCTION_NONDISCRIMINATING",
    "PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL",
    "GENERIC_ACTION_OR_RECOVERY_EXPLANATION",
    "ORDER_ASSOCIATION_NOT_OBSERVED_IN_RUN_01",
    "FOUNDATION_STATE_OR_SELECTOR_HETEROGENEITY",
)

RESOURCE_CAPS: Final[dict[str, int]] = {
    "peak_rss_bytes": 2_147_483_648,
    "scratch_bytes": 268_435_456,
    "durable_bytes": 268_435_456,
    "wall_seconds": 1_800,
}

WORKLOADS: Final[dict[str, int]] = {
    "foundations": len(TRAINING_SEEDS),
    "training_episodes_per_foundation": 1_920,
    "foundation_training_missions": 3_840,
    "adamw_steps_per_foundation": ADAMW_STEPS_PER_FOUNDATION,
    "fixed_learning_curve_missions": 576,
    "final_competence_missions": 256,
    "reachable_state_source_scans": 48,
    "development_graph_action_mission_cells": 3_456,
    "heldout_matched_swapped_common_mission_cells": 1_152,
    "total_missions_rollouts": 9_328,
    "allocated_primitive_slots": 3_395_392,
    "ppo_updates": 320,
    "adamw_steps": 3_840,
    "unique_development_tape_blocks": 48,
    "unique_heldout_tape_blocks": 96,
}


@dataclass(frozen=True, slots=True)
class Manifest:
    schema: str = SCHEMA
    study_id: str = STUDY_ID
    named_run_id: str = NAMED_RUN_ID
    attempt_id: str = ATTEMPT_ID
    quarantined_named_run_id: str = QUARANTINED_NAMED_RUN_ID
    science_card_revision: str = SCIENCE_CARD_REVISION
    expansion_run_02a_id: str = RUN_02A_ID
    expansion_run_02b_id: str = RUN_02B_ID
    expansion_base_candidate: str = NAMED_RUN_ID
    expansion_binding_rule: str = "first_valid_base_run_reuse_state_panel_and_q_without_redraw"
    training_seeds: tuple[int, int] = TRAINING_SEEDS
    k_values: tuple[int, int] = K_VALUES
    foundation_updates: int = FOUNDATION_UPDATES
    episodes_per_update: int = EPISODES_PER_UPDATE
    optimizer_steps_per_update: int = OPTIMIZER_STEPS_PER_UPDATE
    checkpoint_updates: tuple[int, ...] = CHECKPOINT_UPDATES
    curve_updates: tuple[int, ...] = CURVE_UPDATES
    curve_missions_per_cell: int = CURVE_MISSIONS_PER_CELL
    competence_missions_per_cell: int = COMPETENCE_MISSIONS_PER_CELL
    states: tuple[StateSpec, ...] = STATE_SPECS
    actions: tuple[tuple[int, tuple[int, int, int, int]], ...] = ACTION_TABLE
    development_tapes: tuple[int, ...] = DEVELOPMENT_TAPES
    heldout_tapes: tuple[int, ...] = HELDOUT_TAPES
    ordered_branches: tuple[str, ...] = ORDERED_BRANCHES
    workloads: tuple[tuple[str, int], ...] = tuple(WORKLOADS.items())
    resource_caps: tuple[tuple[str, int], ...] = tuple(RESOURCE_CAPS.items())

    def validate(self) -> None:
        if self != Manifest():
            raise ContractError("manifest differs from the SCDMP MF-RS-MK B01 replacement run")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        result = json.loads(json.dumps(asdict(self), allow_nan=False))
        result["workloads"] = dict(self.workloads)
        result["resource_caps"] = dict(self.resource_caps)
        return result


@dataclass(frozen=True, slots=True)
class RunManifest:
    static: Manifest
    master_commitment: str
    q_counter_u64: int
    q_pattern_index: int
    q_by_cell: tuple[int, ...]
    pre_event_p: tuple[int, int, int, int]
    hr_post_pq: tuple[tuple[int, int, int, int], int]
    rh_post_pq: tuple[tuple[int, int, int, int], int]

    def validate(self) -> None:
        self.static.validate()
        if (
            len(self.master_commitment) != 64
            or self.q_pattern_index != self.q_counter_u64 % 4
            or self.q_by_cell != Q_PATTERNS[self.q_pattern_index]
            or self.pre_event_p != (1, 2, 3, 4)
            or self.hr_post_pq != (HR_ASSIGNMENT, 1)
            or self.rh_post_pq != (RH_ASSIGNMENT, 0)
        ):
            raise ContractError("run-level q manifest differs from the frozen source law")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return json.loads(json.dumps(asdict(self), allow_nan=False))


def build_run_manifest(run_master: bytes) -> RunManifest:
    """Seal the one stateless PRF64 q draw before any model or tape activity."""

    if not isinstance(run_master, bytes) or len(run_master) != 32:
        raise ContractError("M_ATTEMPT must be an exact 32-byte master")
    message = json.dumps(Q_COUNTER_ADDRESS, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    value = int.from_bytes(hmac.new(run_master, message, hashlib.sha256).digest()[:8], "big")
    index = value % 4
    result = RunManifest(
        Manifest(), hashlib.sha256(run_master).hexdigest(), value, index, Q_PATTERNS[index],
        (1, 2, 3, 4), (HR_ASSIGNMENT, 1), (RH_ASSIGNMENT, 0),
    )
    result.validate()
    return result


def validate_resource_caps(observed: Mapping[str, int]) -> None:
    if not isinstance(observed, Mapping) or dict(observed) != RESOURCE_CAPS:
        raise ContractError("resource caps differ from the B01 contract")


if len(ACTION_TABLE) != 18 or len(set(ACTION_TABLE)) != 18:
    raise RuntimeError("registered full action table drifted")
if ADAMW_STEPS_PER_FOUNDATION != FOUNDATION_UPDATES * OPTIMIZER_STEPS_PER_UPDATE:
    raise RuntimeError("registered AdamW step budget drifted")
# Numeric tape indices are local to disjoint RNG domains, so the two address
# spaces intentionally both begin at zero.


__all__ = [
    "ACTION_TABLE", "ADAMW_STEPS_PER_FOUNDATION", "ATTEMPT_ID", "CHECKPOINT_UPDATES",
    "COMPETENCE_MISSIONS_PER_CELL", "ContractError", "CURVE_MISSIONS_PER_CELL",
    "CURVE_UPDATES", "DEVELOPMENT_TAPES", "EPISODES_PER_UPDATE",
    "FOUNDATION_UPDATES", "GRAPHS", "HELDOUT_NAMESPACE_TOKEN", "HELDOUT_TAPES",
    "HR_ASSIGNMENT", "K_VALUES",
    "Manifest", "OPTIMIZER_STEPS_PER_UPDATE", "ORDERED_BRANCHES", "Q_COUNTER_ADDRESS",
    "NAMED_RUN_ID", "Q_PATTERNS", "QUARANTINED_NAMED_RUN_ID", "RESOURCE_CAPS",
    "RUN_02A_ID", "RUN_02B_ID", "RUN_LABEL", "RunManifest", "build_run_manifest",
    "RH_ASSIGNMENT", "SCHEMA", "SCIENCE_CARD_REVISION", "SCIENTIFIC_RNG_NAMESPACE",
    "STATE_SPECS", "STUDY_ID",
    "StateSpec", "TRAINING_SEEDS",
    "WORKLOADS", "validate_resource_caps",
]
