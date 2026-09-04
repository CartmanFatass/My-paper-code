"""Production orchestration over the accepted SGSP RSCF-r01 lower-level chain.

The module introduces no second environment.  Python constructs only batched,
counter-addressed potential-outcome tapes and lifecycle metadata.  Every task
transition, factual rollout, shadow rollout and full-suffix continuation runs
through the exact source-keyed C++ ABI V3 host.  PyTorch remains the frozen
batched actor/critic/backward/Adam boundary.

Nothing in this module is constructible before a :class:`ValidatedRootLease`,
post-lease master and matching coordinate adapter exist.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field, fields, replace
import hashlib
import io
import math
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import numpy as np
import torch

from .analysis import (
    AUTHORITATIVE_SUPPORT_SLACK_FORMULAS,
    QUANTITY_NAMES,
    SimultaneousAnalysis,
    analyze_complete_family,
    compute_known_seed_quantities,
)
from .comparator import audit_literal_comparator
from .contracts import FROZEN_LOGICAL_COUNTS, legal_actions
from .evaluation import EDGE, INTACT, PHY, ROTATED, UNIFORM, expected_cell_keys
from .native_contract import (
    MAX_AGENTS,
    MODE_FULL_ROTATED,
    MODE_INTACT,
    FactualEpisodeBatch,
    validate_factual_episode_batch,
)
from .native_loader import (
    load_native_host,
    native_factual_trajectory,
    native_shadow_trajectory,
)
from .policy import RSCFActor, TerminalCritic, build_rolewise_critic_input
from .production_boundary import (
    ARMS,
    EXPECTED_ORIGINS_PER_SEED,
    RESERVED_SCIENTIFIC_NAMESPACE,
    SCIENCE_REVISION,
    WIDTH,
    BlindedSeedFrontier,
    BoundEmpiricalMaster,
    EmpiricalCoordinateAdapter,
    IntegrityError,
    NonValueConformanceDiagnostic,
    ParameterInitialization,
    ProductionLifecycleStore,
    SealedSeedResultRef,
    Update512CheckpointRef,
    ValidatedRootLease,
    canonical_json_bytes,
    canonical_sha256,
    initialize_one_worker_parameters,
)
from .continuation_lineage import (
    AuthenticatedContinuationCut,
    ContinuationIdentity,
    ContinuationLineage,
    ContinuationLineageError,
    OwnerAuthenticatedContinuationCut,
    source_epoch_provenance,
    validate_source_epoch_provenance,
)
from .runner import (
    ARM_PROJECTION,
    FactualGraphAudit,
    FactualTraceBatch,
    NativeTargetAudit,
    RSCFGateBRunner,
    SelectedOriginSnapshot,
    _native_parameters,
    _structured_state_digest,
    _tensor_digest,
)
from .selector import OriginSelection, SelectorCounts
from .training import (
    make_projected_adam,
    projected_adam_step,
    rscf_full_batch_loss,
)


PRODUCTION_RUNNER_SCHEMA = "SGSP_RSCF_R01_PRODUCTION_RUNNER_V1"
PRODUCTION_EVALUATION_SCHEMA = "SGSP_RSCF_R01_PRODUCTION_EVALUATION_V1"
PRODUCTION_AUDIT_SCHEMA = "SGSP_RSCF_R01_PRODUCTION_AUDIT_V1"


def _require_optional_source_epoch(
    continuation_identity_sha256: str | None,
    lineage_sha256: str | None,
    provenance: Mapping[str, Any] | None,
    *,
    label: str,
) -> None:
    if (continuation_identity_sha256 is None) != (lineage_sha256 is None):
        raise IntegrityError(f"{label} continuation provenance is partial")
    if continuation_identity_sha256 is None:
        if provenance is not None:
            raise IntegrityError(f"ordinary {label} acquired source-epoch provenance")
        return
    if provenance is None:
        raise IntegrityError(f"{label} lacks the full source-epoch tuple")
    try:
        validated = validate_source_epoch_provenance(provenance)
    except ContinuationLineageError as exc:
        raise IntegrityError(str(exc)) from exc
    if (
        validated["continuation_identity_sha256"] != continuation_identity_sha256
        or validated["lineage_sha256"] != lineage_sha256
    ):
        raise IntegrityError(f"{label} source-epoch cross-digest changed")


@dataclass(frozen=True)
class ProductionIdentity:
    namespace: str
    lease_lineage_id: str
    master_commitment_sha256: str
    coordinate_manifest_sha256: str
    source_binding_sha256: str
    width: int = WIDTH
    outer_workers: int = 1
    native_threads: int = 1

    def __post_init__(self) -> None:
        if self.namespace != RESERVED_SCIENTIFIC_NAMESPACE:
            raise IntegrityError("production identity namespace changed")
        if (self.width, self.outer_workers, self.native_threads) != (32, 1, 1):
            raise IntegrityError("production identity changed the accepted worker mode")
        for value in (
            self.master_commitment_sha256,
            self.coordinate_manifest_sha256,
            self.source_binding_sha256,
        ):
            if len(value) != 64:
                raise IntegrityError("production identity digest is invalid")
        if not self.lease_lineage_id.startswith("SGSP-RG2Z-RSCF-R01-LINEAGE-"):
            raise IntegrityError("production identity lease lineage changed")

    @property
    def digest(self) -> str:
        return canonical_sha256(asdict(self))


@dataclass(frozen=True)
class ProductionSelectorSchedule:
    namespace: str
    seed_block_index: int
    update_index: int
    roster_size: int
    selections: tuple[OriginSelection, ...]
    counts: SelectorCounts
    provenance_digest: str

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": "SGSP_RSCF_R01_PRODUCTION_SELECTOR_V1",
            "namespace": self.namespace,
            "seed_block_index": self.seed_block_index,
            "update_index": self.update_index,
            "roster_size": self.roster_size,
            "selections": [item.canonical_payload() for item in self.selections],
            "counts": self.counts.canonical_payload(),
        }


@dataclass(frozen=True)
class ProductionAuditCertificate:
    namespace: str
    seed_block_id: str
    structural_valid: bool
    failed_names: tuple[str, ...]
    compact_facts: Mapping[str, Any]
    schema_version: str = PRODUCTION_AUDIT_SCHEMA
    continuation_identity_sha256: str | None = None
    lineage_sha256: str | None = None
    source_epoch_provenance: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        _require_optional_source_epoch(
            self.continuation_identity_sha256,
            self.lineage_sha256,
            self.source_epoch_provenance,
            label="audit",
        )

    @property
    def digest(self) -> str:
        return canonical_sha256(asdict(self))

    # The frozen analyzer reads this legacy attribute name structurally.  This
    # is an interface alias on a genuine production certificate, never a
    # TestIdentity or TEST namespace.
    @property
    def test_seed_block_id(self) -> str:
        return self.seed_block_id


@dataclass(frozen=True)
class ProductionEvaluationCell:
    roster_n: int
    arm: str
    condition: str
    episode_count: int
    mean_return: float
    basin_west_mean: float
    basin_east_mean: float
    accumulator_sha256: str
    checkpoint_sha256: str
    audit_certificate_sha256: str
    mean_legal_action_tv_to_shadow: float | None = None
    mean_legal_simplex_tv_sup: float | None = None

    def __post_init__(self) -> None:
        if self.key not in expected_cell_keys() or self.episode_count != 256:
            raise IntegrityError("production evaluation cell identity/population changed")
        for value in (self.mean_return, self.basin_west_mean, self.basin_east_mean):
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise IntegrityError("production evaluation mean is outside [0,1]")
        tv_required = self.arm == PHY and self.condition == INTACT and self.roster_n in (6, 21)
        if tv_required != (self.mean_legal_action_tv_to_shadow is not None) or tv_required != (self.mean_legal_simplex_tv_sup is not None):
            raise IntegrityError("production evaluation TV accumulator inventory changed")
        for value in (self.mean_legal_action_tv_to_shadow, self.mean_legal_simplex_tv_sup):
            if value is not None and (not math.isfinite(value) or not 0.0 <= value <= 1.0):
                raise IntegrityError("production evaluation TV mean is outside [0,1]")
        for digest in (self.accumulator_sha256, self.checkpoint_sha256, self.audit_certificate_sha256):
            if len(digest) != 64:
                raise IntegrityError("production evaluation digest is invalid")

    @property
    def key(self) -> tuple[int, str, str]:
        return (self.roster_n, self.arm, self.condition)


@dataclass(frozen=True)
class ProductionEvaluationPanel:
    namespace: str
    seed_block_id: str
    checkpoint_sha256: str
    audit_certificate_sha256: str
    cells: tuple[ProductionEvaluationCell, ...]
    schema_version: str = PRODUCTION_EVALUATION_SCHEMA
    continuation_identity_sha256: str | None = None
    lineage_sha256: str | None = None
    source_epoch_provenance: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        _require_optional_source_epoch(
            self.continuation_identity_sha256,
            self.lineage_sha256,
            self.source_epoch_provenance,
            label="evaluation",
        )
        if self.namespace != RESERVED_SCIENTIFIC_NAMESPACE:
            raise IntegrityError("production evaluation namespace changed")
        if {cell.key for cell in self.cells} != set(expected_cell_keys()) or len(self.cells) != len(expected_cell_keys()):
            raise IntegrityError("production evaluation panel cell inventory is incomplete")
        if any(
            cell.episode_count != 256
            or cell.checkpoint_sha256 != self.checkpoint_sha256
            or cell.audit_certificate_sha256 != self.audit_certificate_sha256
            for cell in self.cells
        ):
            raise IntegrityError("production evaluation cells changed checkpoint, audit, or population")

    @property
    def by_key(self) -> Mapping[tuple[int, str, str], ProductionEvaluationCell]:
        return {cell.key: cell for cell in self.cells}

    @property
    def digest(self) -> str:
        return canonical_sha256(asdict(self))

    @property
    def test_seed_block_id(self) -> str:
        return self.seed_block_id


@dataclass(frozen=True)
class ProductionSeedQuantityVector:
    namespace: str
    seed_block_id: str
    evaluation_panel_sha256: str
    audit_certificate_sha256: str
    support_formula_set_sha256: str
    values: Mapping[str, float]
    continuation_identity_sha256: str | None = None
    lineage_sha256: str | None = None
    source_epoch_provenance: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        _require_optional_source_epoch(
            self.continuation_identity_sha256,
            self.lineage_sha256,
            self.source_epoch_provenance,
            label="quantity-vector",
        )
        if self.namespace != RESERVED_SCIENTIFIC_NAMESPACE or set(self.values) != set(QUANTITY_NAMES):
            raise IntegrityError("production seed vector identity or 28-family changed")
        if any(not math.isfinite(float(value)) for value in self.values.values()):
            raise IntegrityError("production seed vector contains a nonfinite value")

    @property
    def test_seed_block_id(self) -> str:
        return self.seed_block_id


@dataclass
class _ArmState:
    actor: RSCFActor
    critic: TerminalCritic
    optimizer: torch.optim.Adam


@dataclass(frozen=True)
class ProductionUpdateReceipt:
    update_index: int
    selector_sha256: str
    arm_state_sha256: Mapping[str, str]
    optimizer_state_sha256: Mapping[str, str]
    q_entry_count: int
    alternative_count: int
    batch_roster_order: tuple[int, ...]
    structural_valid: bool
    audit_failures: tuple[str, ...]
    conformance_leaf_passed: Mapping[str, bool] = field(default_factory=dict)
    max_probability_abs_error: float = 0.0

    def nonvalue_diagnostic(
        self, *, seed_block_index: int, completed_updates: int
    ) -> NonValueConformanceDiagnostic:
        identifiers = tuple(sorted({
            name.rsplit(":", 1)[-1] for name in self.conformance_leaf_passed
        }))
        passed_by_leaf = {
            leaf: all(
                passed
                for name, passed in self.conformance_leaf_passed.items()
                if name.endswith(":" + leaf)
            )
            for leaf in identifiers
        }
        return NonValueConformanceDiagnostic(
            seed_block_index=seed_block_index,
            attempted_update_index=self.update_index,
            completed_updates=completed_updates,
            leaf_identifiers=identifiers,
            leaf_passed=passed_by_leaf,
            max_probability_abs_error=self.max_probability_abs_error,
        )


@dataclass(frozen=True)
class ProductionSeedResult:
    seed_block_index: int
    checkpoint: Update512CheckpointRef
    audit_certificate: ProductionAuditCertificate
    evaluation_panel: ProductionEvaluationPanel
    quantity_vector: ProductionSeedQuantityVector
    sealed_ref: SealedSeedResultRef


@dataclass(frozen=True)
class ProductionEvaluatedSeed:
    """In-memory evaluation state that has not entered sealed publication."""

    seed_block_index: int
    checkpoint: Update512CheckpointRef
    audit_certificate: ProductionAuditCertificate
    evaluation_panel: ProductionEvaluationPanel
    quantity_vector: ProductionSeedQuantityVector


def require_complete_seed_provenance(
    *,
    seed_block_index: int,
    checkpoint: Update512CheckpointRef,
    certificate: ProductionAuditCertificate,
    panel: ProductionEvaluationPanel,
    vector: ProductionSeedQuantityVector,
    sealed_ref: SealedSeedResultRef | None,
    expected_source_epoch_provenance: Mapping[str, Any] | None,
) -> None:
    """Cross-authenticate every object used to accept a finished seed."""

    seed_id = f"SB{seed_block_index:02d}"
    objects = (certificate, panel, vector)
    if (
        checkpoint.seed_block_index != seed_block_index
        or checkpoint.update != 512
        or certificate.seed_block_id != seed_id
        or panel.seed_block_id != seed_id
        or vector.seed_block_id != seed_id
        or panel.checkpoint_sha256 != checkpoint.checkpoint_sha256
        or any(cell.checkpoint_sha256 != checkpoint.checkpoint_sha256 for cell in panel.cells)
        or panel.audit_certificate_sha256 != certificate.digest
        or any(cell.audit_certificate_sha256 != certificate.digest for cell in panel.cells)
        or vector.audit_certificate_sha256 != certificate.digest
        or vector.evaluation_panel_sha256 != panel.digest
        or any(item.source_epoch_provenance != expected_source_epoch_provenance for item in objects)
    ):
        raise IntegrityError("finished seed provenance or cross-digest changed")
    expected_flat = {
        "continuation_identity_sha256": None,
        "lineage_sha256": None,
        "predecessor_source_binding_sha256": None,
        "cut_generation": None,
    }
    if expected_source_epoch_provenance is not None:
        expected_flat = {
            "continuation_identity_sha256": expected_source_epoch_provenance["continuation_identity_sha256"],
            "lineage_sha256": expected_source_epoch_provenance["lineage_sha256"],
            "predecessor_source_binding_sha256": expected_source_epoch_provenance["predecessor_source_binding_sha256"],
            "cut_generation": expected_source_epoch_provenance["cut_generation"],
        }
    if {
        "continuation_identity_sha256": checkpoint.continuation_identity_sha256,
        "lineage_sha256": checkpoint.lineage_sha256,
        "predecessor_source_binding_sha256": checkpoint.predecessor_source_binding_sha256,
        "cut_generation": checkpoint.cut_generation,
    } != expected_flat:
        raise IntegrityError("finished seed checkpoint provenance changed")
    if sealed_ref is not None and (
        sealed_ref.seed_block_index != seed_block_index
        or sealed_ref.source_epoch_provenance != expected_source_epoch_provenance
        or sealed_ref.continuation_identity_sha256 != expected_flat["continuation_identity_sha256"]
        or sealed_ref.lineage_sha256 != expected_flat["lineage_sha256"]
    ):
        raise IntegrityError("finished seed sealed-reference provenance changed")


def _readonly(value: np.ndarray) -> np.ndarray:
    result = np.ascontiguousarray(value)
    result.setflags(write=False)
    return result


def _splitmix64(value: np.ndarray) -> np.ndarray:
    value = value.astype(np.uint64, copy=False)
    value = value + np.uint64(0x9E3779B97F4A7C15)
    value = (value ^ (value >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    value = (value ^ (value >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return value ^ (value >> np.uint64(31))


def _uniform_grid(
    key: int,
    *,
    kind: int,
    phase: int,
    roster: int,
    update: int,
    episode_indices: np.ndarray,
    slot_indices: np.ndarray,
    sender_indices: np.ndarray,
    receiver_indices: np.ndarray,
) -> np.ndarray:
    """Vectorized counter-addressed uniforms; no conditional stream exists."""

    value = np.full(np.broadcast_shapes(
        episode_indices.shape, slot_indices.shape, sender_indices.shape,
        receiver_indices.shape,
    ), np.uint64(key), dtype=np.uint64)
    mask = (1 << 64) - 1
    value ^= np.uint64((kind * 0xD6E8FEB86659FD93) & mask)
    value ^= np.uint64((phase * 0xA5A35625AA5A3563) & mask)
    value ^= np.uint64((roster * 0x9E3779B185EBCA87) & mask)
    value ^= np.uint64(((update + 1) * 0xC2B2AE3D27D4EB4F) & mask)
    value ^= episode_indices.astype(np.uint64) * np.uint64(0x165667B19E3779F9)
    value ^= slot_indices.astype(np.uint64) * np.uint64(0x85EBCA77C2B2AE63)
    value ^= sender_indices.astype(np.uint64) * np.uint64(0x27D4EB2F165667C5)
    value ^= receiver_indices.astype(np.uint64) * np.uint64(0x94D049BB133111EB)
    words = _splitmix64(value)
    return ((words >> np.uint64(11)).astype(np.float32)) * (1.0 / (1 << 53))


class ProductionSeedEngine:
    """One sequential seed-block engine over width-32 native batches."""

    def __init__(
        self,
        lease: ValidatedRootLease,
        master: BoundEmpiricalMaster,
        coordinates: EmpiricalCoordinateAdapter,
        lifecycle: ProductionLifecycleStore,
        *,
        seed_block_index: int,
        continuation_lineage: ContinuationLineage | None = None,
        continuation_identity: ContinuationIdentity | None = None,
    ) -> None:
        if lifecycle.lease.lease_payload_sha256 != lease.lease_payload_sha256:
            raise IntegrityError("engine lifecycle belongs to another lease")
        self.lease = lease
        self.master = master
        self.coordinates = coordinates
        self.lifecycle = lifecycle
        self.seed_block_index = seed_block_index
        initialization = initialize_one_worker_parameters(
            lease, master, coordinates, seed_block_index=seed_block_index
        )
        self.initialization = initialization
        self.identity = ProductionIdentity(
            RESERVED_SCIENTIFIC_NAMESPACE,
            lease.lease_lineage_id,
            master.commitment_sha256,
            coordinates.manifest_sha256,
            lease.source_binding.digest,
        )
        if (continuation_lineage is None) != (continuation_identity is None):
            raise IntegrityError("continuation lineage and identity must be supplied together")
        self.continuation_lineage = continuation_lineage
        self.continuation_identity = continuation_identity
        self.source_epoch_provenance = lifecycle.source_epoch_provenance
        if continuation_lineage is not None and continuation_identity is not None:
            try:
                continuation_identity.require_exact_lineage(continuation_lineage)
            except ContinuationLineageError as exc:
                raise IntegrityError(str(exc)) from exc
            if (
                continuation_lineage.namespace != self.identity.namespace
                or continuation_lineage.lease_lineage_id != self.identity.lease_lineage_id
                or continuation_lineage.predecessor_master_commitment_sha256
                != self.identity.master_commitment_sha256
                or continuation_lineage.predecessor_coordinate_manifest_sha256
                != self.identity.coordinate_manifest_sha256
                or continuation_lineage.continuation_source_binding_sha256
                != self.identity.source_binding_sha256
                or continuation_identity.continuation_source_binding_sha256
                != self.identity.source_binding_sha256
            ):
                raise IntegrityError("continuation objects differ from the new engine identity")
            if lifecycle.source_epoch_provenance != source_epoch_provenance(
                continuation_lineage, continuation_identity
            ):
                raise IntegrityError("continuation lifecycle does not bind both source epochs")
        combined = {**initialization.actor_parameters, **initialization.critic_parameters}
        comparator = audit_literal_comparator(
            phy_initialization=combined, edge_initialization=combined
        )
        if not comparator.passed:
            raise IntegrityError("production initializer failed literal comparator containment")
        native_identity = load_native_host(expected_identity=None)
        if (
            native_identity.source_sha256 != lease.source_binding.native_source_sha256
            or native_identity.build_key_sha256 != lease.source_binding.native_build_key_sha256
            or native_identity.artifact_sha256 != lease.source_binding.native_artifact_sha256
        ):
            raise IntegrityError("production engine loaded a different native ABI tuple")
        self.native_identity = native_identity
        self._helper = RSCFGateBRunner.__new__(RSCFGateBRunner)
        self._helper.width = WIDTH
        self._helper.native_identity = native_identity
        self._helper.runner_identity_sha256 = canonical_sha256({
            "schema": PRODUCTION_RUNNER_SCHEMA,
            "production_identity": self.identity.digest,
            "seed_block": seed_block_index,
            "initialization": initialization.initialization_sha256,
            "accepted_gate_b_runner": lease.source_binding.runner_sha256,
        })
        self._arms: dict[str, _ArmState] = {}
        for arm in ARMS:
            actor = RSCFActor({name: value.clone() for name, value in initialization.actor_parameters.items()})
            critic = TerminalCritic({name: value.clone() for name, value in initialization.critic_parameters.items()})
            self._arms[arm] = _ArmState(actor, critic, make_projected_adam(actor, critic))
        if _tensor_digest(dict(self._arms[PHY].actor.named_parameters())) != _tensor_digest(dict(self._arms[EDGE].actor.named_parameters())):
            raise IntegrityError("learned arms did not receive bitwise-equal initialization copies")
        self.completed_updates = 0
        self._rolling_origin_digest = canonical_sha256([])
        self._update_receipts: list[ProductionUpdateReceipt] = []

    def _seed_key(self) -> int:
        return int.from_bytes(self.coordinates._seed_secret(self.seed_block_index)[:8], "little")

    def selector_schedules(self, update_index: int) -> tuple[ProductionSelectorSchedule, ProductionSelectorSchedule]:
        schedules = []
        for roster in (9, 15):
            selections = []
            for pair in range(16):
                for side in (0, 1):
                    for role in range(3):
                        origin = self.coordinates.origin(
                            seed_block_index=self.seed_block_index,
                            update_index=update_index,
                            roster_size=roster,
                            pair_index=pair,
                            side=side,
                            role_index=role,
                        )
                        selector_common = {
                            "schema": "SGSP_RSCF_R01_PRODUCTION_SELECTOR_V1",
                            "namespace": self.identity.namespace,
                            "seed_block_index": self.seed_block_index,
                            "update_index": update_index,
                            "roster_size": roster,
                            "pair_index": pair,
                            "role_index": role,
                        }
                        selections.append(OriginSelection(
                            pair, side, role,
                            ("WEST-SURVEYOR", "EAST-SURVEYOR", "RIDGE-RELAY")[role],
                            origin.base_slot, origin.selected_slot,
                            origin.role_local_index,
                            role * (roster // 3) + origin.role_local_index,
                            canonical_sha256({**selector_common, "kind": "base_slot"}),
                            canonical_sha256({**selector_common, "side": side, "kind": "local_index"}),
                        ))
            counts = SelectorCounts(32, 96, 320, 96, 224)
            provisional = ProductionSelectorSchedule(
                self.identity.namespace,
                self.seed_block_index,
                update_index,
                roster,
                tuple(selections),
                counts,
                "",
            )
            schedules.append(replace(provisional, provenance_digest=canonical_sha256(provisional.canonical_payload())))
        return tuple(schedules)  # type: ignore[return-value]

    def _event_schedule(self, roster: int, update: int, episodes: np.ndarray, phase: str) -> np.ndarray:
        result = np.empty((len(episodes), 2, 3), dtype=np.int64)
        for lane, episode in enumerate(episodes.tolist()):
            for basin in (0, 1):
                result[lane, basin] = self.coordinates.event_times(
                    seed_block_index=self.seed_block_index,
                    phase=phase,
                    roster_size=roster,
                    update_index=update,
                    episode_index=int(episode),
                    basin=basin,
                )
        return result

    def _episode_batch(
        self,
        *,
        roster: int,
        update: int,
        episode_offset: int,
        phase: str,
        schedule: ProductionSelectorSchedule | None = None,
    ) -> FactualEpisodeBatch:
        width = WIDTH
        episodes = np.arange(episode_offset, episode_offset + width, dtype=np.uint64)
        n_agents = np.full(width, roster, dtype=np.int64)
        roles = np.full((width, MAX_AGENTS), -1, dtype=np.int64)
        roles[:, :roster] = np.repeat(np.arange(3, dtype=np.int64), roster // 3)
        event_schedule = self._event_schedule(roster, update, episodes, phase)
        selector_slot = np.zeros((width, 3), dtype=np.int64)
        selector_local_index = np.zeros((width, 3), dtype=np.int64)
        if schedule is not None:
            for lane in range(32):
                pair, side = divmod(lane, 2)
                for item in schedule.selections:
                    if item.pair_index == pair and item.side == side:
                        selector_slot[lane, item.role_index] = item.selected_slot
                        selector_local_index[lane, item.role_index] = item.role_local_index
        slot = np.arange(12, dtype=np.uint64)[None, :, None]
        episode3 = episodes[:, None, None]
        sender = np.arange(MAX_AGENTS, dtype=np.uint64)[None, None, :]
        zero = np.zeros((1, 1, 1), dtype=np.uint64)
        detection_uniform = self.coordinates.uniform_grid(
            seed_block_index=self.seed_block_index,
            random_variable_kind="detection_uniform", phase=phase,
            roster_size=roster, update_index=update,
            episode_indices=episode3, slot_indices=slot, sender_indices=sender,
            receiver_indices=zero,
        )
        base_uniform = self.coordinates.uniform_grid(
            seed_block_index=self.seed_block_index,
            random_variable_kind="base_uniform", phase=phase,
            roster_size=roster, update_index=update,
            episode_indices=episode3, slot_indices=slot, sender_indices=sender,
            receiver_indices=zero,
        )
        action_uniform = self.coordinates.uniform_grid(
            seed_block_index=self.seed_block_index,
            random_variable_kind="action_uniform", phase=phase,
            roster_size=roster, update_index=update,
            episode_indices=episode3, slot_indices=slot, sender_indices=sender,
            receiver_indices=zero,
        )
        receiver = np.arange(MAX_AGENTS, dtype=np.uint64)[None, None, None, :]
        uplink_uniform = self.coordinates.uniform_grid(
            seed_block_index=self.seed_block_index,
            random_variable_kind="uplink_uniform", phase=phase,
            roster_size=roster, update_index=update,
            episode_indices=episodes[:, None, None, None],
            slot_indices=np.arange(12, dtype=np.uint64)[None, :, None, None],
            sender_indices=np.arange(MAX_AGENTS, dtype=np.uint64)[None, None, :, None],
            receiver_indices=receiver,
        )
        batch = FactualEpisodeBatch(
            n_agents=_readonly(n_agents), roles=_readonly(roles),
            event_schedule=_readonly(event_schedule), selector_slot=_readonly(selector_slot),
            selector_local_index=_readonly(selector_local_index),
            detection_uniform=_readonly(detection_uniform), uplink_uniform=_readonly(uplink_uniform),
            base_uniform=_readonly(base_uniform), action_uniform=_readonly(action_uniform),
        )
        validate_factual_episode_batch(batch)
        return batch

    def _trace_batches(
        self, actor: RSCFActor, schedules: tuple[ProductionSelectorSchedule, ProductionSelectorSchedule]
    ) -> tuple[FactualTraceBatch, FactualTraceBatch]:
        parameters = _native_parameters(actor)
        records = []
        for index, schedule in enumerate(schedules):
            episode = self._episode_batch(
                roster=schedule.roster_size, update=schedule.update_index,
                episode_offset=0, phase="TRAINING", schedule=schedule,
            )
            trajectory = native_factual_trajectory(
                episode, parameters, mode=MODE_INTACT, identity=self.native_identity
            )
            records.append(FactualTraceBatch(schedule, episode, trajectory, index * 32))
        return tuple(records)  # type: ignore[return-value]

    def run_update(self, update_index: int) -> ProductionUpdateReceipt:
        if update_index != self.completed_updates or not 0 <= update_index < 512:
            raise IntegrityError("production update is not the exact next atomic update")
        schedules = self.selector_schedules(update_index)
        selector_sha = canonical_sha256([schedule.provenance_digest for schedule in schedules])
        arm_state: dict[str, str] = {}
        optimizer_state: dict[str, str] = {}
        failures: set[str] = set()
        q_entries = 0
        alternatives = 0
        origin_keys_by_arm: dict[str, tuple[str, ...]] = {}
        conformance_leaf_passed: dict[str, bool] = {}
        max_probability_abs_error = 0.0
        rollback = {
            arm: {
                "actor": copy.deepcopy(state.actor.state_dict()),
                "critic": copy.deepcopy(state.critic.state_dict()),
                "optimizer": copy.deepcopy(state.optimizer.state_dict()),
            }
            for arm, state in self._arms.items()
        }
        try:
            for arm, bound in ARM_PROJECTION.items():
                state = self._arms[arm]
                traces = self._trace_batches(state.actor, schedules)
                origins = self._helper.selected_origin_inventory(traces)
                targets = self._helper.native_target_inventory(
                    state.actor, traces, origins, verify_reverse_order=False
                )
                origin_keys_by_arm[arm] = tuple(
                    canonical_sha256({
                        "episode_index": item.episode_index,
                        "roster_size": item.roster_size,
                        "selection": item.selection.canonical_payload(),
                    })
                    for item in origins
                )
                by_episode: dict[int, list[SelectedOriginSnapshot]] = {}
                for origin in origins:
                    by_episode.setdefault(origin.episode_index, []).append(origin)
                target_by_episode = {target.episode_index: target for target in targets}
                inputs = []
                graph_audits: list[FactualGraphAudit] = []
                # Frozen r03 order is N9[0],N15[0],...,N9[31],N15[31].
                for trace_lane in range(32):
                    for trace_index in (0, 1):
                        episode_index = trace_index * 32 + trace_lane
                        episode, graph = self._helper._episode_inputs(
                            state.actor, state.critic, traces[trace_index],
                            trace_lane, by_episode[episode_index],
                            target_by_episode[episode_index],
                        )
                        inputs.append(episode)
                        graph_audits.append(graph)
                loss, _, _ = rscf_full_batch_loss(inputs, required_episode_count=64)
                step = projected_adam_step(
                    loss, actor=state.actor, critic=state.critic,
                    optimizer=state.optimizer, projection_bound=bound,
                )
                if step.backward_calls != 1 or step.optimizer_steps != 1 or not step.projection_after_step:
                    failures.add(f"{arm}:OPTIMIZER_OPPORTUNITY")
                leaf_values = {
                    "Q_TARGET_DETACHED": all(not graph.q_target_requires_grad for graph in graph_audits),
                    "PRIVATE_TARGET_ISOLATED": all(
                        graph.no_private_target_in_actor_or_critic for graph in graph_audits
                    ),
                    "TORCH_NATIVE_ACTION_IDENTITY": all(
                        graph.torch_native_action_identity for graph in graph_audits
                    ),
                    "TORCH_NATIVE_PROBABILITY_TOLERANCE": all(
                        graph.torch_native_probability_max_abs_error < 2.0e-5
                        for graph in graph_audits
                    ),
                }
                max_probability_abs_error = max(
                    max_probability_abs_error,
                    max(
                        graph.torch_native_probability_max_abs_error
                        for graph in graph_audits
                    ),
                )
                for leaf, passed in leaf_values.items():
                    conformance_leaf_passed[f"{arm}:{leaf}"] = passed
                    if not passed:
                        failures.add(f"{arm}:{leaf}")
                if any(
                    not target.common_tape
                    or not target.factual_suffix_identity
                    or not target.immutable_parameter_identity
                    or not target.closed_loop_recurrence
                    for target in targets
                ):
                    failures.add(f"{arm}:NATIVE_TARGET_CONFORMANCE")
                q_entries += sum(item.q_entry_count for item in targets)
                alternatives += sum(item.alternative_count for item in targets)
                arm_state[arm] = _tensor_digest({
                    **dict(state.actor.named_parameters()),
                    **{f"critic.{key}": value for key, value in state.critic.named_parameters()},
                })
                optimizer_state[arm] = _structured_state_digest(state.optimizer.state_dict())
        except BaseException:
            for arm, state in self._arms.items():
                state.actor.load_state_dict(rollback[arm]["actor"], strict=True)
                state.critic.load_state_dict(rollback[arm]["critic"], strict=True)
                state.optimizer.load_state_dict(rollback[arm]["optimizer"])
            raise
        if origin_keys_by_arm[PHY] != origin_keys_by_arm[EDGE]:
            failures.add("ARM_DEPENDENT_ORIGIN_COORDINATES")
        next_rolling_origin_digest = canonical_sha256({
            "prior": self._rolling_origin_digest,
            "update": update_index,
            "selector": selector_sha,
            "arm_origin_keys": origin_keys_by_arm[PHY],
            "arms": ARMS,
        })
        receipt = ProductionUpdateReceipt(
            update_index, selector_sha, arm_state, optimizer_state,
            q_entries, alternatives,
            tuple(roster for _lane in range(32) for roster in (9, 15)),
            not failures, tuple(sorted(failures)),
            conformance_leaf_passed, max_probability_abs_error,
        )
        if failures:
            for arm, state in self._arms.items():
                state.actor.load_state_dict(rollback[arm]["actor"], strict=True)
                state.critic.load_state_dict(rollback[arm]["critic"], strict=True)
                state.optimizer.load_state_dict(rollback[arm]["optimizer"])
            return receipt
        self.completed_updates += 1
        self._rolling_origin_digest = next_rolling_origin_digest
        self._update_receipts.append(receipt)
        return receipt

    def frontier(self, generation: int) -> BlindedSeedFrontier:
        return BlindedSeedFrontier(
            self.seed_block_index,
            generation,
            self.completed_updates,
            self.completed_updates * 384,
            self._rolling_origin_digest,
            self.coordinates.manifest_sha256,
            self.lease.source_binding.digest,
            **self.lifecycle._provenance_fields(),
        )

    def serialize_resume_state(self) -> bytes:
        continuation = self.continuation_identity is not None
        payload = {
            "schema": PRODUCTION_RUNNER_SCHEMA + (
                "_CONTINUATION_NON_EVALUABLE_RESUME_V1"
                if continuation else "_NON_EVALUABLE_RESUME_V1"
            ),
            "production_identity_sha256": self.identity.digest,
            "continuation_identity_sha256": (
                None if self.continuation_identity is None else self.continuation_identity.digest
            ),
            "lineage_sha256": (
                None if self.continuation_lineage is None else self.continuation_lineage.digest
            ),
            "seed_block_index": self.seed_block_index,
            "completed_updates": self.completed_updates,
            "rolling_origin_digest": self._rolling_origin_digest,
            "update_receipts": [asdict(item) for item in self._update_receipts],
            "arms": {
                arm: {
                    "actor": state.actor.state_dict(),
                    "critic": state.critic.state_dict(),
                    "optimizer": state.optimizer.state_dict(),
                }
                for arm, state in self._arms.items()
            },
            "evaluable": False,
        }
        buffer = io.BytesIO()
        torch.save(payload, buffer)
        data = buffer.getvalue()
        for forbidden in (b"q_targets", b"factual_return", b"branch_private"):
            if forbidden in data:
                raise IntegrityError("resume state retained a private target/value")
        return data

    def restore_resume_state(self, data: bytes) -> None:
        payload = torch.load(io.BytesIO(data), map_location="cpu", weights_only=False)
        expected_schema = PRODUCTION_RUNNER_SCHEMA + (
            "_CONTINUATION_NON_EVALUABLE_RESUME_V1"
            if self.continuation_identity is not None else "_NON_EVALUABLE_RESUME_V1"
        )
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != expected_schema
            or payload.get("production_identity_sha256") != self.identity.digest
            or payload.get("continuation_identity_sha256") != (
                None if self.continuation_identity is None else self.continuation_identity.digest
            )
            or payload.get("lineage_sha256") != (
                None if self.continuation_lineage is None else self.continuation_lineage.digest
            )
            or payload.get("seed_block_index") != self.seed_block_index
            or payload.get("evaluable") is not False
        ):
            raise IntegrityError("resume state identity changed")
        arms = payload.get("arms")
        if not isinstance(arms, dict) or set(arms) != set(ARMS):
            raise IntegrityError("resume state arm inventory changed")
        for arm, state in self._arms.items():
            state.actor.load_state_dict(arms[arm]["actor"], strict=True)
            state.critic.load_state_dict(arms[arm]["critic"], strict=True)
            state.optimizer.load_state_dict(arms[arm]["optimizer"])
        self.completed_updates = int(payload["completed_updates"])
        self._rolling_origin_digest = str(payload["rolling_origin_digest"])
        self._update_receipts = [ProductionUpdateReceipt(**item) for item in payload["update_receipts"]]

    def import_continuation_state(
        self,
        cut: AuthenticatedContinuationCut | OwnerAuthenticatedContinuationCut,
        predecessor_identity: ProductionIdentity,
    ) -> None:
        """Atomically import the exact authenticated A state into B."""

        lineage = self.continuation_lineage
        continuation = self.continuation_identity
        if lineage is None or continuation is None:
            raise IntegrityError("ordinary engines cannot import a continuation cut")
        if self.completed_updates != 0 or self._update_receipts:
            raise IntegrityError("continuation import requires one untouched destination engine")
        if (
            predecessor_identity.digest != lineage.predecessor_production_identity_sha256
            or predecessor_identity.namespace != lineage.namespace
            or predecessor_identity.lease_lineage_id != lineage.lease_lineage_id
            or predecessor_identity.master_commitment_sha256
            != lineage.predecessor_master_commitment_sha256
            or predecessor_identity.coordinate_manifest_sha256
            != lineage.predecessor_coordinate_manifest_sha256
            or predecessor_identity.source_binding_sha256
            != lineage.predecessor_source_binding_sha256
        ):
            raise IntegrityError("predecessor identity differs from the lineage")
        try:
            cut.authenticate(lineage)
        except ContinuationLineageError as exc:
            raise IntegrityError(str(exc)) from exc
        payload = torch.load(
            io.BytesIO(cut.resume_state_bytes), map_location="cpu", weights_only=False
        )
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != PRODUCTION_RUNNER_SCHEMA + "_NON_EVALUABLE_RESUME_V1"
            or payload.get("production_identity_sha256") != predecessor_identity.digest
            or payload.get("seed_block_index") != self.seed_block_index
            or payload.get("completed_updates") != 154
            or payload.get("evaluable") is not False
            or not isinstance(payload.get("rolling_origin_digest"), str)
            or len(payload["rolling_origin_digest"]) != 64
            or not isinstance(payload.get("update_receipts"), list)
            or len(payload["update_receipts"]) != 154
            or [item.get("update_index") for item in payload["update_receipts"]]
            != list(range(154))
        ):
            raise IntegrityError("predecessor resume payload is not the exact generation-154 state")
        arms = payload.get("arms")
        if not isinstance(arms, dict) or set(arms) != set(ARMS):
            raise IntegrityError("predecessor resume arm inventory changed")
        imported_arms: dict[str, _ArmState] = {}
        try:
            for arm in ARMS:
                actor = RSCFActor({
                    name: value.clone()
                    for name, value in self.initialization.actor_parameters.items()
                })
                critic = TerminalCritic({
                    name: value.clone()
                    for name, value in self.initialization.critic_parameters.items()
                })
                optimizer = make_projected_adam(actor, critic)
                if (
                    not isinstance(arms[arm], dict)
                    or set(arms[arm]) != {"actor", "critic", "optimizer"}
                ):
                    raise IntegrityError("predecessor arm state schema changed")
                actor.load_state_dict(arms[arm]["actor"], strict=True)
                critic.load_state_dict(arms[arm]["critic"], strict=True)
                optimizer.load_state_dict(arms[arm]["optimizer"])
                if any(parameter.dtype is not torch.float32 for parameter in actor.parameters()):
                    raise IntegrityError("imported actor state is not FP32")
                if any(parameter.dtype is not torch.float32 for parameter in critic.parameters()):
                    raise IntegrityError("imported critic state is not FP32")
                imported_arms[arm] = _ArmState(actor, critic, optimizer)
            receipts = [
                ProductionUpdateReceipt(**item) for item in payload["update_receipts"]
            ]
        except (KeyError, TypeError, ValueError, RuntimeError) as exc:
            raise IntegrityError("predecessor state failed strict schema import") from exc
        self._arms = imported_arms
        self.completed_updates = 154
        self._rolling_origin_digest = payload["rolling_origin_digest"]
        self._update_receipts = receipts

    def _checkpoint_bytes(self) -> bytes:
        if self.completed_updates != 512:
            raise IntegrityError("sole evaluable checkpoint requires all 512 updates")
        payload = {
            "schema": PRODUCTION_RUNNER_SCHEMA + "_UPDATE512_CHECKPOINT_V1",
            "production_identity_sha256": self.identity.digest,
            "continuation_identity_sha256": (
                None if self.continuation_identity is None else self.continuation_identity.digest
            ),
            "lineage_sha256": (
                None if self.continuation_lineage is None else self.continuation_lineage.digest
            ),
            "seed_block_index": self.seed_block_index,
            "update": 512,
            "arms": {
                arm: {
                    "actor": state.actor.state_dict(),
                    "critic": state.critic.state_dict(),
                    "optimizer": state.optimizer.state_dict(),
                }
                for arm, state in self._arms.items()
            },
        }
        buffer = io.BytesIO()
        torch.save(payload, buffer)
        return buffer.getvalue()

    def _evaluation_batch(self, roster: int, offset: int):
        return self._episode_batch(
            roster=roster, update=-1, episode_offset=offset,
            phase="EVALUATION", schedule=None,
        )

    def _evaluation_accumulators(self, roster: int, arm: str) -> dict[str, list[Any]]:
        actor = self._arms[arm].actor
        parameters = _native_parameters(actor)
        result: dict[str, list[Any]] = {
            "intact": [], "rotated": [], "shadow": [], "uniform": [], "episode": []
        }
        zero_head = np.zeros_like(parameters.actor_w)
        zero_bias = np.zeros_like(parameters.actor_b)
        zero_head.setflags(write=False)
        zero_bias.setflags(write=False)
        uniform_parameters = replace(parameters, actor_w=zero_head, actor_b=zero_bias)
        for offset in range(0, 256, WIDTH):
            episode = self._evaluation_batch(roster, offset)
            intact = native_factual_trajectory(episode, parameters, mode=MODE_INTACT, identity=self.native_identity)
            rotated = native_factual_trajectory(episode, parameters, mode=MODE_FULL_ROTATED, identity=self.native_identity)
            shadow = native_shadow_trajectory(episode, intact, parameters, identity=self.native_identity)
            uniform = native_factual_trajectory(episode, uniform_parameters, mode=MODE_INTACT, identity=self.native_identity)
            result["episode"].append(episode)
            result["intact"].append(intact)
            result["rotated"].append(rotated)
            result["shadow"].append(shadow)
            result["uniform"].append(uniform)
        return result

    def evaluate(self, checkpoint: Update512CheckpointRef, certificate: ProductionAuditCertificate) -> ProductionEvaluationPanel:
        if self.completed_updates != 512 or checkpoint.update != 512:
            raise IntegrityError("production evaluation requires the sole update-512 checkpoint")
        cache = {(roster, arm): self._evaluation_accumulators(roster, arm) for roster in (9, 15, 6, 21) for arm in ARMS}
        cells = []
        for roster, arm_name, condition in sorted(expected_cell_keys()):
            learned_arm = PHY if arm_name == UNIFORM else arm_name
            bundles = cache[(roster, learned_arm)]
            key = "uniform" if arm_name == UNIFORM else "rotated" if condition == ROTATED else "intact"
            trajectories = bundles[key]
            returns = np.concatenate([item.terminal_return for item in trajectories])
            west = np.concatenate([item.final_delivered[:, 0] for item in trajectories]).astype(np.float32) / 3.0
            east = np.concatenate([item.final_delivered[:, 1] for item in trajectories]).astype(np.float32) / 3.0
            tv_mean = None
            tv_sup = None
            if arm_name == PHY and condition == INTACT and roster in (6, 21):
                per_episode_mean = []
                per_episode_sup = []
                for intact, shadow, episode in zip(bundles["intact"], bundles["shadow"], bundles["episode"]):
                    tv = 0.5 * np.abs(intact.legal_probabilities - shadow.legal_probabilities).sum(axis=-1, dtype=np.float32)
                    active = episode.roles[:, None, :] >= 0
                    tv = np.where(active, tv, 0.0)
                    per_episode_mean.extend((tv.sum(axis=(1, 2)) / (episode.n_agents * 12.0)).tolist())
                    per_episode_sup.extend(tv.max(axis=(1, 2)).tolist())
                tv_mean = float(np.mean(per_episode_mean, dtype=np.float32))
                tv_sup = float(np.mean(per_episode_sup, dtype=np.float32))
            digest = hashlib.sha256()
            for trajectory in trajectories:
                digest.update(trajectory.trajectory_digest.tobytes())
            cells.append(ProductionEvaluationCell(
                roster, arm_name, condition, 256,
                float(returns.mean(dtype=np.float32)),
                float(west.mean(dtype=np.float32)), float(east.mean(dtype=np.float32)),
                digest.hexdigest(), checkpoint.checkpoint_sha256,
                certificate.digest, tv_mean, tv_sup,
            ))
        return ProductionEvaluationPanel(
            RESERVED_SCIENTIFIC_NAMESPACE, f"SB{self.seed_block_index:02d}",
            checkpoint.checkpoint_sha256, certificate.digest, tuple(cells),
            continuation_identity_sha256=(
                None if self.continuation_identity is None else self.continuation_identity.digest
            ),
            lineage_sha256=(
                None if self.continuation_lineage is None else self.continuation_lineage.digest
            ),
            source_epoch_provenance=self.source_epoch_provenance,
        )

    def finish_seed_evaluation(self) -> ProductionEvaluatedSeed:
        """Evaluate update 512 without publishing a persistent seed result."""

        if self.completed_updates != 512:
            raise IntegrityError("cannot finish a partial seed block")
        failures = tuple(sorted({failure for item in self._update_receipts for failure in item.audit_failures}))
        certificate = ProductionAuditCertificate(
            RESERVED_SCIENTIFIC_NAMESPACE,
            f"SB{self.seed_block_index:02d}",
            not failures and len(self._update_receipts) == 512,
            failures,
            {
                "updates": len(self._update_receipts),
                "backward_calls": 1024,
                "q_entries": sum(item.q_entry_count for item in self._update_receipts),
                "alternative_continuations": sum(item.alternative_count for item in self._update_receipts),
                "arm_independent_selector": True,
                "frozen_logical_counts_sha256": canonical_sha256(FROZEN_LOGICAL_COUNTS.as_dict()),
            },
            continuation_identity_sha256=(
                None if self.continuation_identity is None else self.continuation_identity.digest
            ),
            lineage_sha256=(
                None if self.continuation_lineage is None else self.continuation_lineage.digest
            ),
            source_epoch_provenance=self.source_epoch_provenance,
        )
        frontier = self.frontier(512)
        checkpoint_bytes = self._checkpoint_bytes()
        checkpoint = self.lifecycle.install_update512_checkpoint(
            self.seed_block_index, checkpoint_bytes, frontier
        )
        panel = self.evaluate(checkpoint, certificate)
        known = compute_known_seed_quantities(panel)  # type: ignore[arg-type]
        support = AUTHORITATIVE_SUPPORT_SLACK_FORMULAS.compute(panel)  # type: ignore[arg-type]
        vector = ProductionSeedQuantityVector(
            RESERVED_SCIENTIFIC_NAMESPACE,
            f"SB{self.seed_block_index:02d}", panel.digest, certificate.digest,
            AUTHORITATIVE_SUPPORT_SLACK_FORMULAS.identity_sha256,
            {**known, **support},
            continuation_identity_sha256=(
                None if self.continuation_identity is None else self.continuation_identity.digest
            ),
            lineage_sha256=(
                None if self.continuation_lineage is None else self.continuation_lineage.digest
            ),
            source_epoch_provenance=self.source_epoch_provenance,
        )
        return ProductionEvaluatedSeed(
            self.seed_block_index, checkpoint, certificate, panel, vector
        )

    def publish_evaluated_seed(
        self, evaluated: ProductionEvaluatedSeed
    ) -> ProductionSeedResult:
        """Persist one evaluated seed only after the launcher revalidates Root authority."""

        if (
            type(evaluated) is not ProductionEvaluatedSeed
            or evaluated.seed_block_index != self.seed_block_index
            or evaluated.checkpoint.seed_block_index != self.seed_block_index
            or evaluated.checkpoint.update != 512
            or evaluated.evaluation_panel.seed_block_id != f"SB{self.seed_block_index:02d}"
            or evaluated.quantity_vector.seed_block_id != f"SB{self.seed_block_index:02d}"
            or evaluated.evaluation_panel.checkpoint_sha256 != evaluated.checkpoint.checkpoint_sha256
            or evaluated.quantity_vector.evaluation_panel_sha256 != evaluated.evaluation_panel.digest
        ):
            raise IntegrityError("evaluated seed publication identity changed")
        require_complete_seed_provenance(
            seed_block_index=self.seed_block_index,
            checkpoint=evaluated.checkpoint,
            certificate=evaluated.audit_certificate,
            panel=evaluated.evaluation_panel,
            vector=evaluated.quantity_vector,
            sealed_ref=None,
            expected_source_epoch_provenance=self.source_epoch_provenance,
        )
        sealed_ref = self.lifecycle.install_sealed_seed_result(
            self.seed_block_index,
            {
                "schema": "SGSP_RSCF_R01_SEALED_SEED_RESULT_V1",
                "namespace": RESERVED_SCIENTIFIC_NAMESPACE,
                "seed_block_index": self.seed_block_index,
                "audit_certificate": asdict(evaluated.audit_certificate),
                "evaluation_panel": asdict(evaluated.evaluation_panel),
                "quantity_vector": asdict(evaluated.quantity_vector),
            },
            self.master,
        )
        result = ProductionSeedResult(
            self.seed_block_index, evaluated.checkpoint,
            evaluated.audit_certificate, evaluated.evaluation_panel,
            evaluated.quantity_vector, sealed_ref,
        )
        require_complete_seed_provenance(
            seed_block_index=self.seed_block_index,
            checkpoint=result.checkpoint,
            certificate=result.audit_certificate,
            panel=result.evaluation_panel,
            vector=result.quantity_vector,
            sealed_ref=result.sealed_ref,
            expected_source_epoch_provenance=self.source_epoch_provenance,
        )
        return result


def analyze_complete_production_family(
    results: Sequence[ProductionSeedResult],
) -> SimultaneousAnalysis:
    if {item.seed_block_index for item in results} != set(range(24)) or len(results) != 24:
        raise IntegrityError("complete analyzer requires exactly 24 unique seed results")
    expected_provenance = results[0].audit_certificate.source_epoch_provenance
    for item in results:
        require_complete_seed_provenance(
            seed_block_index=item.seed_block_index,
            checkpoint=item.checkpoint,
            certificate=item.audit_certificate,
            panel=item.evaluation_panel,
            vector=item.quantity_vector,
            sealed_ref=item.sealed_ref,
            expected_source_epoch_provenance=expected_provenance,
        )
    return analyze_complete_family(
        tuple(item.quantity_vector for item in results),  # type: ignore[arg-type]
        audit_certificates=tuple(item.audit_certificate for item in results),  # type: ignore[arg-type]
    )
