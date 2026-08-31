"""Adaptation-free V2 evaluation interfaces and complete-only publication."""

from __future__ import annotations

import math
import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts.core import (
    EVALUATIONS_PER_CELL, FP32_PROBABILITY_TOLERANCE,
    FRRIE_COMPLETE_PANEL_RESULT_V2,
    HELDOUT_ROSTERS, INTERVENTIONS, LEARNED_ARMS, TRAIN_ROSTERS,
    ContractError, canonical_json_bytes, expected_block_checkpoint_path,
    validate_manifest,
)
from .host import PUBLIC_ROLES
from .policy import LEGAL_ACTION_INDICES


ALL_ARMS = (*LEARNED_ARMS, "UNIFORM_LEGAL")
ALL_ROSTERS = (*TRAIN_ROSTERS, *HELDOUT_ROSTERS)


@dataclass(frozen=True, slots=True)
class EvaluationOpportunity:
    roster: int
    intervention: str
    episode: int
    tape_identity: str


def evaluation_opportunities(
    tape_identities: Mapping[tuple[int, int], str], *,
    episodes_per_cell: int = EVALUATIONS_PER_CELL,
) -> tuple[EvaluationOpportunity, ...]:
    """Return the arm-independent ordered evaluation tape schedule."""

    if type(episodes_per_cell) is not int or episodes_per_cell <= 0:
        raise ContractError("evaluation episode count must be a positive integer")
    rows: list[EvaluationOpportunity] = []
    for roster in ALL_ROSTERS:
        for intervention in INTERVENTIONS:
            for episode in range(episodes_per_cell):
                identity = tape_identities.get((roster, episode))
                if not isinstance(identity, str) or not identity:
                    raise ContractError("every roster/episode requires one common tape identity")
                rows.append(EvaluationOpportunity(roster, intervention, episode, identity))
    return tuple(rows)


def uniform_legal_probabilities(role: int) -> list[float]:
    if type(role) is not int or not 0 <= role < 3:
        raise ContractError("public role must be in {0,1,2}")
    probabilities = [0.0] * 6
    for action in LEGAL_ACTION_INDICES[role]:
        probabilities[action] = 1.0 / len(LEGAL_ACTION_INDICES[role])
    return probabilities


def _probability_row(value: Sequence[float], role: int, field: str) -> tuple[float, ...]:
    if len(value) != 6:
        raise ContractError(f"{field} must have six action columns")
    row = tuple(float(item) for item in value)
    if any(not math.isfinite(item) or item < 0.0 for item in row):
        raise ContractError(f"{field} must contain finite nonnegative probabilities")
    legal = set(LEGAL_ACTION_INDICES[role])
    if any(row[action] != 0.0 for action in range(6) if action not in legal):
        raise ContractError(f"{field} assigns mass to an illegal action")
    if not math.isclose(math.fsum(row), 1.0, rel_tol=0.0, abs_tol=FP32_PROBABILITY_TOLERANCE):
        raise ContractError(f"{field} does not sum to one")
    floor = 0.04 / len(legal)
    if any(row[action] + FP32_PROBABILITY_TOLERANCE < floor for action in legal):
        raise ContractError(f"{field} violates the frozen legal-uniform floor")
    return row


def probability_vector_tv(
    intact: Sequence[Sequence[float]], shadow: Sequence[Sequence[float]],
    roles: Sequence[int],
) -> list[float]:
    """Reduce exact [decisions,6] intact/shadow vectors to per-decision TV."""

    if len(intact) != len(shadow) or len(intact) != len(roles):
        raise ContractError("TV inputs must share one decision axis")
    result: list[float] = []
    for index, role in enumerate(roles):
        if type(role) is not int or role not in (0, 1, 2):
            raise ContractError("TV roles must be literal W/E/R indices")
        left = _probability_row(intact[index], role, "intact probability")
        right = _probability_row(shadow[index], role, "shadow probability")
        result.append(0.5 * math.fsum(
            abs(left[action] - right[action]) for action in LEGAL_ACTION_INDICES[role]
        ))
    return result


def decision_probability_pairs(
    *, roster: int, intact: Sequence[Sequence[float]],
    shadow: Sequence[Sequence[float]], roles: Sequence[int],
) -> list[dict[str, Any]]:
    """Create fixed slot/entity/role records after validating TV shape."""

    expected = 12 * roster
    if len(intact) != expected or len(shadow) != expected or len(roles) != expected:
        raise ContractError("probability histories must cover every slot/entity decision")
    probability_vector_tv(intact, shadow, roles)
    role_width = roster // 3
    expected_roles = [entity // role_width for _slot in range(12) for entity in range(roster)]
    if list(roles) != expected_roles:
        raise ContractError("probability history roles differ from the fixed native layout")
    rows: list[dict[str, Any]] = []
    for index, role in enumerate(roles):
        rows.append({
            "slot": index // roster,
            "entity": index % roster,
            "role": PUBLIC_ROLES[role],
            "intact": list(_probability_row(intact[index], role, "intact probability")),
            "shadow": list(_probability_row(shadow[index], role, "shadow probability")),
        })
    return rows


def episode_record(
    *, episode: int, tape_contract: Mapping[str, Any],
    dw: int, de: int, waste: float,
    decision_pairs: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    if type(episode) is not int or not 0 <= episode < EVALUATIONS_PER_CELL:
        raise ContractError("evaluation episode index must be in [0,256)")
    if (
        not isinstance(tape_contract, Mapping)
        or set(tape_contract) != {
            "schema", "seed_block", "purpose", "roster", "update", "episode",
        }
        or tape_contract.get("schema") != "FRRIE_ADDRESSED_TAPE_V1"
        or not isinstance(tape_contract.get("seed_block"), str)
        or not tape_contract.get("seed_block")
        or tape_contract.get("episode") != episode
        or tape_contract.get("purpose") != "EVALUATE"
        or tape_contract.get("update") != 512
        or tape_contract.get("roster") not in ALL_ROSTERS
    ):
        raise ContractError("episode primitive requires its direct same-index evaluation tape")
    if type(dw) is not int or type(de) is not int or not 0 <= dw <= 3 or not 0 <= de <= 3:
        raise ContractError("evaluation delivery primitives must be integer counts in [0,3]")
    if (isinstance(waste, bool) or not isinstance(waste, (int, float))
            or not math.isfinite(waste) or not 0.0 <= float(waste) <= 1.0):
        raise ContractError("evaluation waste must be one finite scalar in [0,1]")
    return {
        "episode": episode,
        "tape_contract": dict(tape_contract),
        "dw": dw, "de": de, "waste": float(waste),
        "decision_probability_pairs": decision_pairs,
    }


def addressed_evaluation_tape_contract(
    *, seed_block: str, roster: int, episode: int,
) -> dict[str, Any]:
    if roster not in ALL_ROSTERS or type(episode) is not int or not 0 <= episode < EVALUATIONS_PER_CELL:
        raise ContractError("evaluation tape coordinate is outside the frozen panel")
    if not isinstance(seed_block, str) or not seed_block:
        raise ContractError("evaluation tape requires a direct seed block")
    return {
        "schema": "FRRIE_ADDRESSED_TAPE_V1", "seed_block": seed_block,
        "purpose": "EVALUATE", "roster": roster, "update": 512,
        "episode": episode,
    }


def evaluation_cell(
    *, manifest: Mapping[str, Any], checkpoint_inventory: Mapping[str, Any],
    seed_block: str, arm: str, roster: int, intervention: str,
    episode_records: Sequence[Mapping[str, Any]] | None,
    support_valid: bool, support_reason: str | None,
) -> dict[str, Any]:
    """Build one exact analysis-compatible V2 cell and direct result binding."""
    from .analysis import expected_result_binding

    validated = validate_manifest(manifest)
    if seed_block not in validated["seed_blocks"] or arm not in ALL_ARMS:
        raise ContractError("evaluation cell block/arm identity is outside the manifest")
    if roster not in ALL_ROSTERS or intervention not in INTERVENTIONS:
        raise ContractError("evaluation cell roster/intervention is outside the panel")
    if type(support_valid) is not bool:
        raise ContractError("evaluation support state must be literal boolean")
    if support_valid != (support_reason is None):
        raise ContractError("evaluation support validity and reason disagree")
    tapes = [
        addressed_evaluation_tape_contract(
            seed_block=seed_block, roster=roster, episode=episode,
        )
        for episode in range(EVALUATIONS_PER_CELL)
    ]
    records: list[dict[str, Any]] | None
    if episode_records is None:
        records = None
    else:
        if len(episode_records) != EVALUATIONS_PER_CELL:
            raise ContractError("supported evaluation cell requires all 256 episode records")
        records = []
        for episode, record in enumerate(episode_records):
            if (
                not isinstance(record, Mapping)
                or record.get("episode") != episode
                or record.get("tape_contract") != tapes[episode]
            ):
                raise ContractError("evaluation record differs from its same-index cell tape")
            records.append(dict(record))
    if support_valid and records is None:
        raise ContractError("supported evaluation cell cannot omit episode values")
    if not support_valid and records is not None:
        raise ContractError("unsupported evaluation cell must expose no values")
    return {
        "seed_block": seed_block,
        "arm": arm,
        "checkpoint": 512,
        "roster": roster,
        "intervention": intervention,
        "episodes": EVALUATIONS_PER_CELL,
        "tape_contracts": tapes,
        "episode_records": records,
        "support_valid": support_valid,
        "support_reason": support_reason,
        "result_binding": expected_result_binding(
            validated, checkpoint_inventory, block=seed_block, arm=arm,
            roster=roster, intervention=intervention,
        ),
    }


def complete_panel_result(
    *, manifest: Mapping[str, Any], checkpoint_inventory: Mapping[str, Any],
    cells: Sequence[Mapping[str, Any]], support_valid: bool,
    support_reason: str | None,
) -> dict[str, Any]:
    """Assemble the exact V2 panel envelope; staging performs full validation."""
    from .work import checkpoint_cumulative_work, final_cumulative_work

    validated = validate_manifest(manifest)
    if type(support_valid) is not bool or support_valid != (support_reason is None):
        raise ContractError("panel support validity and reason disagree")
    return {
        "schema": FRRIE_COMPLETE_PANEL_RESULT_V2,
        "manifest_contract": validated,
        "complete": True,
        "receipts": {
            "checkpoint": checkpoint_cumulative_work(validated["compute"]),
            "work": final_cumulative_work(validated["compute"]),
            "support": {
                "endpoint_support_complete": support_valid,
                "complete": True,
                "reason": support_reason,
            },
        },
        "checkpoint_inventory": dict(checkpoint_inventory),
        "cells": [dict(cell) for cell in cells],
    }


class CompleteOnlyEvaluationTransaction:
    """Private staging with one create-only atomic publication point.

    Evaluation always reloads the caller-supplied read-only update-512 bytes;
    no mutable training object is accepted by this transaction.
    """

    def __init__(
        self, target: str | Path, checkpoint512: bytes | Mapping[str, bytes], *,
        manifest: Mapping[str, Any] | None = None,
        seed_packet_contract: Mapping[str, Any] | None = None,
        seed_packet_path: str | Path | None = None,
        expected_seed_block: str | None = None,
        native_contract: Mapping[str, Any] | None = None,
        test_only: bool = False,
    ) -> None:
        self.target = Path(target)
        self.private = self.target.with_name(self.target.name + ".evaluation-private")
        if self.target.exists() or self.private.exists():
            raise ContractError("evaluation target/private staging must both be fresh")
        self._checkpoint512: bytes | dict[str, bytes]
        self._staged = False
        self._test_only = test_only
        self._manifest: dict[str, Any] | None = None
        self._checkpoint_inventory: dict[str, Any] | None = None
        if test_only:
            if not isinstance(checkpoint512, bytes) or not checkpoint512:
                raise ContractError("TEST_ONLY evaluation requires nonempty checkpoint witness bytes")
            self._checkpoint512 = checkpoint512
            if any(value is not None for value in (
                manifest, seed_packet_contract, seed_packet_path,
                expected_seed_block, native_contract,
            )):
                raise ContractError("TEST_ONLY evaluation must not bind a production manifest")
        else:
            from .checkpoint import restore_checkpoint
            from .contracts.core import validate_manifest
            from .lifecycle import ROOT_MARKER_NAME

            if manifest is None:
                raise ContractError("production evaluation requires the validated V2 manifest")
            self._manifest = validate_manifest(manifest)
            if (
                not isinstance(checkpoint512, Mapping)
                or set(checkpoint512) != set(self._manifest["seed_blocks"])
                or any(not isinstance(value, bytes) or not value for value in checkpoint512.values())
            ):
                raise ContractError(
                    "production evaluation requires one read-only update-512 checkpoint per seed block"
                )
            self._checkpoint512 = dict(checkpoint512)
            if (
                not isinstance(seed_packet_contract, Mapping)
                or seed_packet_path is None
                or not isinstance(expected_seed_block, str)
                or not isinstance(native_contract, Mapping)
            ):
                raise ContractError(
                    "production evaluation requires full packet/path/block/native checkpoint bindings"
                )
            manifest_packet_path = self._manifest["sealed_seed_packet"]["path"]
            if str(seed_packet_path) != manifest_packet_path:
                raise ContractError("evaluation seed packet path differs from the manifest literal")
            try:
                current_packet = json.loads(
                    Path(seed_packet_path).read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                raise ContractError("evaluation current sealed seed packet is unreadable") from exc
            if current_packet != dict(seed_packet_contract):
                raise ContractError("evaluation packet argument differs from the current bound packet")
            output_root = Path(self._manifest["roots"]["output"]).resolve(strict=False)
            target_resolved = self.target.resolve(strict=False)
            if not target_resolved.is_relative_to(output_root):
                raise ContractError("evaluation target must remain under the claimed output root")
            if not (output_root / ROOT_MARKER_NAME).is_file():
                raise ContractError("evaluation requires the claimed V2 output root marker")
            # Every block checkpoint is parsed and restored before the panel
            # inventory may assert bytes_revalidated=true.  No caller boolean
            # can manufacture this state.
            try:
                for seed_block in self._manifest["seed_blocks"]:
                    checkpoint_path = expected_block_checkpoint_path(
                        self._manifest, seed_block,
                    )
                    with checkpoint_path.open("rb") as handle:
                        checkpoint_file_bytes = handle.read()
                    if checkpoint_file_bytes != self._checkpoint512[seed_block]:
                        raise ContractError(
                            "supplied checkpoint bytes differ from the exact read-only block file"
                        )
                    restore_checkpoint(
                        checkpoint_file_bytes,
                        manifest_contract=self._manifest,
                        native_contract=native_contract,
                        seed_packet_contract=seed_packet_contract,
                        expected_update=512,
                        expected_seed_block=seed_block,
                        seed_packet_path=seed_packet_path,
                    )
            except (OSError, ContractError) as exc:
                raise ContractError(
                    "evaluation requires all exact read-only update-512 checkpoint files"
                ) from exc
            from .analysis import expected_checkpoint_inventory
            self._checkpoint_inventory = expected_checkpoint_inventory(
                self._manifest,
                generation_provenance=seed_packet_contract["generation_provenance"],
                checkpoint_bytes_revalidated=True,
            )

    @property
    def checkpoint512(self) -> bytes | dict[str, bytes]:
        # bytes are immutable; returning this value cannot mutate training state.
        return self._checkpoint512

    @property
    def checkpoint_inventory(self) -> dict[str, Any]:
        if self._checkpoint_inventory is None:
            raise ContractError("TEST_ONLY evaluation has no production checkpoint inventory")
        return dict(self._checkpoint_inventory)

    def stage_complete_panel(self, panel: Mapping[str, Any]) -> None:
        if panel.get("complete") is not True or not isinstance(panel.get("cells"), list):
            raise ContractError("only a structurally complete panel may enter staging")
        if not self._test_only:
            from .analysis import validate_complete_panel
            if self._manifest is None:
                raise ContractError("production evaluation manifest is absent")
            if panel.get("checkpoint_inventory") != self._checkpoint_inventory:
                raise ContractError(
                    "panel inventory was not produced by this all-block restore transaction"
                )
            validate_complete_panel(panel, self._manifest)
        data = canonical_json_bytes(panel)
        self.private.parent.mkdir(parents=True, exist_ok=True)
        with self.private.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        self._staged = True

    def publish(self) -> Path:
        if not self._staged or not self.private.is_file() or self.target.exists():
            raise ContractError("complete evaluation is not privately staged or target is not fresh")
        try:
            os.link(self.private, self.target)
        except OSError as exc:
            raise ContractError(f"complete-only evaluation publication failed: {exc}") from exc
        # Failure to remove the private name after the successful hard-link
        # publication never rolls back or unlinks the complete target.
        try:
            self.private.unlink()
        except OSError:
            pass
        return self.target

    def abort(self) -> None:
        """Discard unpublished private values; restart uses checkpoint512."""
        if self.private.is_file():
            self.private.unlink()
        self._staged = False


__all__ = [
    "ALL_ARMS", "ALL_ROSTERS", "EvaluationOpportunity",
    "evaluation_opportunities", "uniform_legal_probabilities",
    "probability_vector_tv", "decision_probability_pairs",
    "addressed_evaluation_tape_contract", "episode_record",
    "evaluation_cell", "complete_panel_result",
    "CompleteOnlyEvaluationTransaction",
]
