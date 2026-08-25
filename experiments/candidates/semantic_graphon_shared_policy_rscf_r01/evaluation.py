"""Compact update-512-only evaluation-consumer schemas.

This module does not run an evaluation.  It validates synthetic TEST-only
complete-seed summaries before they can reach the analyzer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Iterable, Mapping

from .lifecycle import (
    CompleteSeedPacket,
    EvaluableCheckpointRef,
    LifecycleContractError,
    canonical_sha256,
    reject_private_persistence,
    validate_test_namespace,
)


EVALUATION_SCHEMA_VERSION = "SGSP_RSCF_EVALUATION_CONSUMER_V1"
EVALUATION_ROSTERS = (9, 15, 6, 21)
SEEN_ROSTERS = (9, 15)
HELD_OUT_ROSTERS = (6, 21)
EXPECTED_EPISODES_PER_CELL = 256

PHY = "PHY-TRUST"
EDGE = "EDGE-FLEX"
UNIFORM = "UNIFORM-LEGAL"
INTACT = "intact"
ROTATED = "semantic-column-rotate"


def _require_sha256(name: str, value: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise LifecycleContractError(f"{name} must be lowercase SHA-256")


def _finite_unit(name: str, value: float) -> None:
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise LifecycleContractError(f"{name} must be finite and in [0,1]")


@dataclass(frozen=True)
class EvaluationCellSummary:
    """One compact seed/roster/arm/condition accumulator.

    Episode arrays and branch-private material are intentionally absent.  The
    digest binds the external accumulator that produced these compact means.
    """

    namespace: str
    test_seed_block_id: str
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
        validate_test_namespace(self.namespace)
        if not self.test_seed_block_id.startswith("TEST_"):
            raise LifecycleContractError("evaluation seed-block identity must be explicitly TEST-only")
        if self.roster_n not in EVALUATION_ROSTERS:
            raise LifecycleContractError(f"unsupported roster N={self.roster_n}")
        if self.arm not in (PHY, EDGE, UNIFORM):
            raise LifecycleContractError(f"unsupported arm {self.arm!r}")
        if self.condition not in (INTACT, ROTATED):
            raise LifecycleContractError(f"unsupported condition {self.condition!r}")
        if self.episode_count != EXPECTED_EPISODES_PER_CELL:
            raise LifecycleContractError("evaluation cells must be complete 256-episode accumulators")
        _finite_unit("mean_return", self.mean_return)
        _finite_unit("basin_west_mean", self.basin_west_mean)
        _finite_unit("basin_east_mean", self.basin_east_mean)
        if self.mean_legal_action_tv_to_shadow is not None:
            _finite_unit("mean_legal_action_tv_to_shadow", self.mean_legal_action_tv_to_shadow)
        if self.mean_legal_simplex_tv_sup is not None:
            _finite_unit("mean_legal_simplex_tv_sup", self.mean_legal_simplex_tv_sup)
        for name in ("accumulator_sha256", "checkpoint_sha256", "audit_certificate_sha256"):
            _require_sha256(name, getattr(self, name))
        if self.arm == UNIFORM and (self.roster_n not in SEEN_ROSTERS or self.condition != INTACT):
            raise LifecycleContractError("UNIFORM-LEGAL is only admitted for intact N=9,15 competence cells")
        if self.condition == ROTATED and (self.roster_n not in HELD_OUT_ROSTERS or self.arm == UNIFORM):
            raise LifecycleContractError("semantic cut cells are only admitted for trained arms at N=6,21")
        tv_required = self.arm == PHY and self.condition == INTACT and self.roster_n in HELD_OUT_ROSTERS
        if tv_required != (self.mean_legal_action_tv_to_shadow is not None):
            raise LifecycleContractError(
                "legal-action-TV accumulator is required exactly for intact PHY held-out cells"
            )
        if tv_required != (self.mean_legal_simplex_tv_sup is not None):
            raise LifecycleContractError(
                "legal-simplex TV-sup support accumulator is required exactly for intact PHY held-out cells"
            )
        reject_private_persistence(asdict(self))

    @property
    def key(self) -> tuple[int, str, str]:
        return (self.roster_n, self.arm, self.condition)


def expected_cell_keys() -> frozenset[tuple[int, str, str]]:
    keys: set[tuple[int, str, str]] = set()
    for roster_n in SEEN_ROSTERS:
        keys.update(
            {
                (roster_n, PHY, INTACT),
                (roster_n, EDGE, INTACT),
                (roster_n, UNIFORM, INTACT),
            }
        )
    for roster_n in HELD_OUT_ROSTERS:
        keys.update(
            {
                (roster_n, PHY, INTACT),
                (roster_n, EDGE, INTACT),
                (roster_n, PHY, ROTATED),
                (roster_n, EDGE, ROTATED),
            }
        )
    return frozenset(keys)


@dataclass(frozen=True)
class CompleteEvaluationPanel:
    namespace: str
    test_seed_block_id: str
    complete_seed_packet_sha256: str
    checkpoint: EvaluableCheckpointRef
    cells: tuple[EvaluationCellSummary, ...]
    schema_version: str = EVALUATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_test_namespace(self.namespace)
        if self.schema_version != EVALUATION_SCHEMA_VERSION:
            raise LifecycleContractError("evaluation consumer schema mismatch")
        _require_sha256("complete_seed_packet_sha256", self.complete_seed_packet_sha256)
        if self.checkpoint.namespace != self.namespace:
            raise LifecycleContractError("evaluation panel/checkpoint namespace mismatch")
        by_key: dict[tuple[int, str, str], EvaluationCellSummary] = {}
        for cell in self.cells:
            if cell.namespace != self.namespace or cell.test_seed_block_id != self.test_seed_block_id:
                raise LifecycleContractError("evaluation cell identity mismatch")
            if cell.checkpoint_sha256 != self.checkpoint.checkpoint_sha256:
                raise LifecycleContractError("evaluation cell consumed a different checkpoint")
            if cell.key in by_key:
                raise LifecycleContractError(f"duplicate evaluation cell {cell.key}")
            by_key[cell.key] = cell
        missing = expected_cell_keys() - by_key.keys()
        extra = by_key.keys() - expected_cell_keys()
        if missing or extra:
            raise LifecycleContractError(
                f"evaluation panel is not atomic and complete; missing={sorted(missing)}, extra={sorted(extra)}"
            )
        audit_digests = {cell.audit_certificate_sha256 for cell in self.cells}
        if len(audit_digests) != 1:
            raise LifecycleContractError("evaluation cells do not share one audit certificate")
        reject_private_persistence(self.to_compact_payload())

    @classmethod
    def consume(
        cls,
        packet: CompleteSeedPacket,
        cells: Iterable[EvaluationCellSummary],
    ) -> "CompleteEvaluationPanel":
        materialized = tuple(cells)
        if not packet.evaluable:
            raise LifecycleContractError("evaluation consumer requires an atomic complete-seed packet")
        if any(cell.audit_certificate_sha256 != packet.audit_certificate_sha256 for cell in materialized):
            raise LifecycleContractError("evaluation cells are not bound to the packet audit certificate")
        return cls(
            namespace=packet.resume_identity.namespace,
            test_seed_block_id=packet.resume_identity.test_schedule_id,
            complete_seed_packet_sha256=packet.digest,
            checkpoint=packet.checkpoint,
            cells=materialized,
        )

    @property
    def by_key(self) -> Mapping[tuple[int, str, str], EvaluationCellSummary]:
        return {cell.key: cell for cell in self.cells}

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_compact_payload())

    def to_compact_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "kind": "COMPLETE_TEST_EVALUATION_PANEL",
            "namespace": self.namespace,
            "test_seed_block_id": self.test_seed_block_id,
            "complete_seed_packet_sha256": self.complete_seed_packet_sha256,
            "checkpoint": asdict(self.checkpoint),
            "cells": [asdict(cell) for cell in sorted(self.cells, key=lambda item: item.key)],
            "partial_row_count": 0,
        }
