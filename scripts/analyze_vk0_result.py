"""Analyze the V-K0B unrestricted-R30 natural-access result.

Consumes exactly four durable inputs -- the two frozen JSONL row files, the
V-K0A oracle-panel authorization artifact, and the training/checkpoint
exposure manifest -- and recomputes every statistic and the eight-row
first-match result branch solely from those files, per:

  docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md (VK-D6, VK-D9,
  VK-D7, and amendments A-VK-D6, A-VK-D9, A-VK-D10)
  docs/external-review/rounds/20260801_variable_k_algorithm_direction/21_PRO_OPEN_RAW.md
  docs/external-review/rounds/20260801_vk0_design_conformance/21_PRO_OPEN_RAW.md

The V-K0B driver that emits real rows does not exist yet. This module is
developed and tested against the frozen row schema alone, using synthetic
fixture rows built by its test suite.

The analyzer never guesses: any row, manifest, or oracle-panel field that
fails the frozen schema raises SchemaValidationError, and no summary is
written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

# =============================================================================
# Frozen identity and schema constants
# =============================================================================

VK0_CONTRACT_ID = "VK0_TOY_RENEWAL_URGENCY"
VK0_TRACE_SCHEMA_VERSION = "vk0-trace-1"

URGENT = "URGENT"
STABLE = "STABLE"
BOUNDARY = "BOUNDARY"
URGENCY_CLASSES = {URGENT, STABLE, BOUNDARY}

AGENT_ORDER_CANONICAL = "canonical"
AGENT_ORDER_REVERSED = "reversed"
AGENT_ORDER_CODES = {AGENT_ORDER_CANONICAL, AGENT_ORDER_REVERSED}

SEGMENT_ENDING_AUTHORITIES = {
    "voluntary_set",
    "initial_assignment",
    "episode_termination",
    "active_mask_change",
    "team_intent_boundary",
    "forced_renewal",
}

NATURAL_TOKEN_KEEP = "KEEP"
NATURAL_TOKEN_SET = "SET"
NATURAL_TOKEN_KINDS = {NATURAL_TOKEN_KEEP, NATURAL_TOKEN_SET}

ESTIMAND_KEEP_REFERENCE = "KEEP_REFERENCE"
ESTIMAND_OPP_NAMED_SET = "OPP_NAMED_SET"
ESTIMAND_SET_SAMPLED = "SET_SAMPLED"
ESTIMAND_NATURAL = "NATURAL"
ESTIMAND_FAMILIES = {
    ESTIMAND_KEEP_REFERENCE,
    ESTIMAND_OPP_NAMED_SET,
    ESTIMAND_SET_SAMPLED,
    ESTIMAND_NATURAL,
}

PHASE_SELECT = "select"
PHASE_EVALUATE = "evaluate"
PHASES = {PHASE_SELECT, PHASE_EVALUATE}

VK0A_VERDICT_IDENTIFIED = "TOY_HETEROGENEOUS_RENEWAL_URGENCY_IDENTIFIED"
VK0A_VERDICT_NOT_IDENTIFIED = "TOY_HETEROGENEOUS_RENEWAL_URGENCY_NOT_IDENTIFIED"
VK0A_PANEL_VERDICTS = {VK0A_VERDICT_IDENTIFIED, VK0A_VERDICT_NOT_IDENTIFIED}

# A-VK-D2 / VK-D10: the frozen source panel is exactly 112 focal rows
# (4 signs x 2 permutation tracks x 7 noninitial checks x 2 focals).
VK0A_PANEL_ROW_COUNT = 112

# The V-K0A authorization-artifact tuple (VK-D10 / A-VK-D10): contract_id,
# stage_commit, environment_blob_sha, action_table_hash, oracle_script_hash,
# panel_schema_version, row_count, validity_predicates, verdict, plus the
# artifact_sha256 hash over the first nine. The RAW panel file
# (source_oracle_panel.json, scripts/audit_vk0a_source_urgency_oracle.py)
# does not carry validity_predicates or artifact_sha256 itself -- it carries
# a raw `validity` dict, and the driver (scripts/audit_vk0b_r30_access.py,
# `resolve_oracle_panel`) derives validity_predicates from it and computes
# artifact_sha256, recording the whole nine-field-plus-hash "authorization"
# tuple in the run manifest rather than in the panel file (panel identity is
# instead checked byte-for-byte against a sidecar digest, out of this
# analyzer's four-input scope). The analyzer therefore reproduces the same
# derivation from the raw panel and cross-checks it against the manifest's
# recorded authorization -- never against a field the panel itself lacks.
ORACLE_PANEL_AUTHORIZATION_TUPLE_FIELDS = (
    "contract_id",
    "stage_commit",
    "environment_blob_sha",
    "action_table_hash",
    "oracle_script_hash",
    "panel_schema_version",
    "row_count",
    "validity_predicates",
    "verdict",
)

# Mirrors scripts/audit_vk0a_source_urgency_oracle.py:ValidityTracker.NAMES
# exactly -- the eight AND-accumulated V-K0A validity predicates the driver
# folds into validity_predicates. Mirrored rather than imported: importing
# that audit script would couple this analyzer's import surface (and its
# reproducibility) to a large, separately evolving driver module for the
# sake of one tuple of literals. Drift between the two tuples is guarded by
# a test against the real panel's actual `validity` key set.
VK0A_VALIDITY_PREDICATE_NAMES = (
    "identical_initial_state_across_branches",
    "no_check_crossed_within_window",
    "legal_edit_enumeration_exact",
    "same_label_set_excluded",
    "fixed_primitive_table_consistent",
    "only_external_reward_used",
    "permutation_relabels_only",
    "full_action_support_maximization_exhausted",
)

# MEASUREMENT §3: the task-semantic materiality unit and the STABLE
# equivalence half-width are both delta_U = 0.5 external-return units.
MATERIALITY = 0.5

# EVIDENCE_DESIGN / V-K0B primary gates: support and competence floors.
SUPPORT_FLOOR_CLASS_MIN = 192
SUPPORT_FLOOR_CLASS_ORDER_MIN = 64
COMPETENCE_FLOOR_MIN = 0.75

# Inference: seed-first nested bootstrap, 10,000 iterations, one frozen seed.
BOOTSTRAP_ITERATIONS = 10_000
LOWER_QUANTILE = 0.05
UPPER_QUANTILE = 0.95

# First-match result system (MEASUREMENT, "First-match result system").
RESULT_ROWS = {
    1: "INVALID_VARIABLE_K_URGENCY_AUDIT",
    2: "TOY_HETEROGENEOUS_RENEWAL_URGENCY_NOT_IDENTIFIED",
    3: "R30_URGENCY_TRACE_SUPPORT_INSUFFICIENT",
    4: "R30_TOY_ACCESS_NOT_ESTABLISHED",
    5: "SOURCE_IDENTIFIED_R30_OPPORTUNITY_NOT_ACCESSED",
    6: "SOURCE_IDENTIFIED_R30_NATURAL_ALIGNMENT_WRONG_DIRECTION",
    7: "SOURCE_IDENTIFIED_R30_NATURAL_ALIGNMENT_UNRESOLVED",
    8: "HETEROGENEOUS_URGENCY_AND_R30_NATURAL_ACCESS_IDENTIFIED",
}

REQUIRED_OPPORTUNITY_STRATA = ("pooled", AGENT_ORDER_CANONICAL, AGENT_ORDER_REVERSED)

# VK-D7: the one frozen bootstrap seed, derived exactly as SHA-256 of
# (VK0_CONTRACT_ID, "bootstrap"), first 8 bytes read as a big-endian int --
# mirroring the audit script's stream_seed pattern (scripts/audit_d7_s_event_aligned.py).
BOOTSTRAP_SEED_DERIVATION = (
    "int.from_bytes(sha256('VK0_TOY_RENEWAL_URGENCY|bootstrap')[:8], 'big')"
)


def _derive_bootstrap_seed() -> int:
    digest = hashlib.sha256(f"{VK0_CONTRACT_ID}|bootstrap".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


BOOTSTRAP_SEED = _derive_bootstrap_seed()


# =============================================================================
# Refusal on schema violation
# =============================================================================


class SchemaValidationError(ValueError):
    """Raised when any row, manifest, or oracle-panel field violates the
    frozen VK0 schema. The analyzer refuses to select a result row rather
    than guess -- no summary is produced when this is raised."""


# =============================================================================
# Small type predicates
# =============================================================================


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def _is_probability_or_ineligible(value: Any) -> bool:
    """keep_prob is valid only for active learned-KEEP decisions; initial
    assignment and forced-refresh/native-categorical paths stay NaN/null."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return _is_number(value) and 0.0 <= float(value) <= 1.0


def _is_five_vector(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 5 and all(_is_number(x) for x in value)


def _is_binary(x: Any) -> bool:
    if isinstance(x, bool):
        return True
    if isinstance(x, int):
        return x in (0, 1)
    if isinstance(x, float):
        return x in (0.0, 1.0)
    return False


def _is_five_binary_vector(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 5 and all(_is_binary(x) for x in value)


# =============================================================================
# Row schema validation (A-VK-D6 identity keys + the ruled semantic fields)
# =============================================================================


def _validate_common_identity(row: dict[str, Any], fail) -> None:
    if row.get("contract_id") != VK0_CONTRACT_ID:
        fail("contract_id must equal the frozen VK0 contract id")
    if row.get("trace_schema_version") != VK0_TRACE_SCHEMA_VERSION:
        fail("trace_schema_version must equal the frozen trace schema version")
    if not _is_int(row.get("training_seed")):
        fail("training_seed must be an int")
    if not _is_int(row.get("evaluation_seed")):
        fail("evaluation_seed must be an int")
    if not isinstance(row.get("episode_id"), (int, str)) or isinstance(row.get("episode_id"), bool):
        fail("episode_id must be an int or str")
    if row.get("agent_order_code") not in AGENT_ORDER_CODES:
        fail("agent_order_code must be canonical or reversed")
    if not _is_int(row.get("check_index")):
        fail("check_index must be an int")
    if not _is_int(row.get("focal_agent")) or row.get("focal_agent") not in (0, 1):
        fail("focal_agent must be 0 or 1")
    if not isinstance(row.get("check_unit_id"), str) or not row.get("check_unit_id"):
        fail("check_unit_id must be a non-empty str")
    if not isinstance(row.get("checkpoint_hash"), str) or not row.get("checkpoint_hash"):
        fail("checkpoint_hash must be a non-empty str")
    if not isinstance(row.get("resolved_config_hash"), str) or not row.get("resolved_config_hash"):
        fail("resolved_config_hash must be a non-empty str")


def validate_check_row(row: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []

    def fail(msg: str) -> None:
        errors.append(f"check_row[{index}] ({row.get('check_unit_id', '?')}): {msg}")

    _validate_common_identity(row, fail)

    u_src = row.get("oracle_u_src")
    if not _is_number(u_src) or float(u_src) < 0.0:
        fail("oracle_u_src must be a finite non-negative number")
    if row.get("oracle_urgency_class") not in URGENCY_CLASSES:
        fail("oracle_urgency_class must be URGENT, STABLE, or BOUNDARY")

    token_kind = row.get("natural_token_kind")
    if token_kind not in NATURAL_TOKEN_KINDS:
        fail("natural_token_kind must be KEEP or SET")
    natural_set_skill = row.get("natural_set_skill")
    if token_kind == NATURAL_TOKEN_SET:
        if not isinstance(natural_set_skill, str) or not natural_set_skill:
            fail("natural_set_skill must be a non-empty str when natural_token_kind is SET")
    elif natural_set_skill is not None:
        fail("natural_set_skill must be null when natural_token_kind is KEEP")

    if not _is_probability_or_ineligible(row.get("keep_prob")):
        fail("keep_prob must be a probability in [0,1], null, or NaN")

    if row.get("segment_ending_authority") not in SEGMENT_ENDING_AUTHORITIES:
        fail("segment_ending_authority must be one of the enumerated segment-ending authorities")

    if not _is_five_vector(row.get("natural_external_reward_vector")):
        fail("natural_external_reward_vector must be a five-element numeric vector")
    if not _is_five_binary_vector(row.get("slow_match_vector")):
        fail("slow_match_vector must be a five-element 0/1 vector")
    if not _is_five_binary_vector(row.get("fast_match_vector")):
        fail("fast_match_vector must be a five-element 0/1 vector")

    return errors


def validate_unit_row(row: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []

    def fail(msg: str) -> None:
        errors.append(f"unit_row[{index}] ({row.get('branch_unit_id', '?')}): {msg}")

    _validate_common_identity(row, fail)

    if not isinstance(row.get("branch_unit_id"), str) or not row.get("branch_unit_id"):
        fail("branch_unit_id must be a non-empty str")
    family = row.get("estimand_family")
    if family not in ESTIMAND_FAMILIES:
        fail("estimand_family must be one of KEEP_REFERENCE/OPP_NAMED_SET/SET_SAMPLED/NATURAL")
    if not isinstance(row.get("parent_check_unit_id"), str) or not row.get("parent_check_unit_id"):
        fail("parent_check_unit_id must be a non-empty str")

    candidate_skill = row.get("candidate_skill")
    if family in (ESTIMAND_OPP_NAMED_SET, ESTIMAND_SET_SAMPLED):
        if not isinstance(candidate_skill, str) or not candidate_skill:
            fail("candidate_skill must be a non-empty str for OPP_NAMED_SET/SET_SAMPLED rows")
    elif candidate_skill is not None:
        fail("candidate_skill must be null for KEEP_REFERENCE/NATURAL rows")

    if row.get("phase") not in PHASES:
        fail("phase must be select or evaluate")
    if not _is_int(row.get("replicate_index")) or row.get("replicate_index") < 0:
        fail("replicate_index must be a non-negative int")
    if not _is_int(row.get("derived_seed")):
        fail("derived_seed must be an int")

    vector = row.get("external_reward_vector")
    if not _is_five_vector(vector):
        fail("external_reward_vector must be a five-element numeric vector")
    window_return = row.get("window_return")
    if not _is_number(window_return):
        fail("window_return must be a finite number")
    elif isinstance(vector, list) and len(vector) == 5 and all(_is_number(x) for x in vector):
        if abs(float(window_return) - float(sum(vector))) > 1e-6:
            fail("window_return must equal the sum of external_reward_vector")

    replay_conformance = row.get("replay_conformance")
    if not isinstance(replay_conformance, dict) or not replay_conformance:
        fail("replay_conformance must be a non-empty dict of booleans")
    elif not all(isinstance(v, bool) for v in replay_conformance.values()):
        fail("replay_conformance values must all be booleans")

    return errors


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("contract_id") != VK0_CONTRACT_ID:
        errors.append("manifest.contract_id must equal the frozen VK0 contract id")
    if manifest.get("trace_schema_version") != VK0_TRACE_SCHEMA_VERSION:
        errors.append("manifest.trace_schema_version must equal the frozen trace schema version")
    seeds = manifest.get("seeds")
    if not isinstance(seeds, dict) or not seeds:
        errors.append("manifest.seeds must be a non-empty dict keyed by training seed")
    else:
        for seed_key, entry in seeds.items():
            if not isinstance(entry, dict):
                errors.append(f"manifest.seeds[{seed_key}] must be a dict")
                continue
            if not isinstance(entry.get("checkpoint_hash"), str) or not entry.get("checkpoint_hash"):
                errors.append(f"manifest.seeds[{seed_key}].checkpoint_hash must be a non-empty str")
            if not isinstance(entry.get("resolved_config_hash"), str) or not entry.get("resolved_config_hash"):
                errors.append(f"manifest.seeds[{seed_key}].resolved_config_hash must be a non-empty str")
            if not _is_int(entry.get("low_optimizer_steps")) or entry.get("low_optimizer_steps") < 0:
                errors.append(f"manifest.seeds[{seed_key}].low_optimizer_steps must be a non-negative int")

    # manifest.authorization is OPTIONAL at the schema level: its total
    # absence is itself a meaningful, valid precedence-1 finding (VK-D10 --
    # "V-K0B must verify that tuple before loading any checkpoint"; a
    # manifest that never recorded having done so feeds
    # INVALID_VARIABLE_K_URGENCY_AUDIT, not a refusal). If the key IS
    # present, however, it must be a well-formed authorization tuple.
    if "authorization" in manifest and manifest["authorization"] is not None:
        authorization = manifest["authorization"]
        if not isinstance(authorization, dict):
            errors.append("manifest.authorization must be a dict when present")
        else:
            for field in (
                "contract_id",
                "stage_commit",
                "environment_blob_sha",
                "action_table_hash",
                "oracle_script_hash",
                "panel_schema_version",
                "verdict",
                "artifact_sha256",
            ):
                if not isinstance(authorization.get(field), str) or not authorization.get(field):
                    errors.append(f"manifest.authorization.{field} must be a non-empty str")
            if not _is_int(authorization.get("row_count")):
                errors.append("manifest.authorization.row_count must be an int")
            validity_predicates = authorization.get("validity_predicates")
            if (
                not isinstance(validity_predicates, dict)
                or not validity_predicates
                or not all(isinstance(v, bool) for v in validity_predicates.values())
            ):
                errors.append("manifest.authorization.validity_predicates must be a non-empty dict of booleans")
    return errors


def validate_oracle_panel(panel: dict[str, Any]) -> list[str]:
    """Validates the RAW V-K0A panel schema (source_oracle_panel.json, as
    scripts/audit_vk0a_source_urgency_oracle.py actually emits it) -- a
    `validity` dict of named booleans, not a pre-derived
    `validity_predicates`/`artifact_sha256` pair. Those are the driver's
    authorization-view derivation (scripts/audit_vk0b_r30_access.py), which
    the analyzer reproduces itself in _panel_tuple_payload/
    _panel_expected_sha256 and cross-checks against the manifest."""
    errors: list[str] = []
    for field in (
        "contract_id",
        "stage_commit",
        "environment_blob_sha",
        "action_table_hash",
        "oracle_script_hash",
        "panel_schema_version",
        "verdict",
    ):
        if not isinstance(panel.get(field), str) or not panel.get(field):
            errors.append(f"oracle_panel.{field} must be a non-empty str")
    if not _is_int(panel.get("row_count")):
        errors.append("oracle_panel.row_count must be an int")
    validity = panel.get("validity")
    if not isinstance(validity, dict):
        errors.append("oracle_panel.validity must be a dict")
    else:
        for name in VK0A_VALIDITY_PREDICATE_NAMES:
            if not isinstance(validity.get(name), bool):
                errors.append(f"oracle_panel.validity.{name} must be a bool")
    if panel.get("verdict") not in VK0A_PANEL_VERDICTS:
        errors.append("oracle_panel.verdict must be a recognized V-K0A verdict")
    return errors


# =============================================================================
# I/O
# =============================================================================


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SchemaValidationError(f"{path}:{line_no}: invalid JSON ({exc})") from exc
    return rows


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _git_blob_sha1(path: Path) -> str:
    """The exact `git hash-object` algorithm, computed without invoking git
    (subagents never run Git; this replicates the hashing scheme in-process
    against the analyzer's own source bytes)."""
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


# =============================================================================
# Precedence-1: INVALID_VARIABLE_K_URGENCY_AUDIT
# =============================================================================


def derive_validity_predicates(panel: dict[str, Any]) -> dict[str, bool]:
    """Exactly scripts/audit_vk0b_r30_access.py's `resolve_oracle_panel`
    derivation: `{name: bool(validity[name]) for name in ValidityTracker.NAMES}`."""
    validity = panel["validity"]
    return {name: bool(validity[name]) for name in VK0A_VALIDITY_PREDICATE_NAMES}


def _panel_tuple_payload(panel: dict[str, Any]) -> dict[str, Any]:
    """Reproduces the driver's nine-field authorization tuple from the RAW
    panel -- validity_predicates is derived (the panel itself carries no
    such field), row_count is cast to int exactly as the driver does."""
    return {
        "contract_id": panel["contract_id"],
        "stage_commit": panel["stage_commit"],
        "environment_blob_sha": panel["environment_blob_sha"],
        "action_table_hash": panel["action_table_hash"],
        "oracle_script_hash": panel["oracle_script_hash"],
        "panel_schema_version": panel["panel_schema_version"],
        "row_count": int(panel["row_count"]),
        "validity_predicates": derive_validity_predicates(panel),
        "verdict": panel["verdict"],
    }


def _panel_expected_sha256(panel: dict[str, Any]) -> str:
    """Exactly the driver's `artifact_sha256 = hash_text(json.dumps(tuple_payload,
    sort_keys=True, separators=(",", ":")))` -- reproduced independently
    from the raw panel and compared against the manifest's recorded value in
    compute_invalid_reasons (the panel is not self-referential: it carries
    no hash of its own tuple, only a sidecar byte-digest of the whole file,
    which is out of this analyzer's four-input scope)."""
    canonical = json.dumps(_panel_tuple_payload(panel), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_invalid_reasons(
    check_rows: list[dict[str, Any]],
    unit_rows: list[dict[str, Any]],
    oracle_panel: dict[str, Any],
    manifest: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []

    false_replay = [
        u["branch_unit_id"]
        for u in unit_rows
        if any(v is False for v in u["replay_conformance"].values())
    ]
    if false_replay:
        reasons.append(
            f"replay-conformance boolean false in {len(false_replay)} unit row(s), "
            f"e.g. {false_replay[0]}"
        )

    seeds_map = manifest["seeds"]
    mismatched: list[str] = []
    for row in (*check_rows, *unit_rows):
        seed_key = str(row["training_seed"])
        entry = seeds_map.get(seed_key)
        unit_id = row.get("check_unit_id") or row.get("branch_unit_id")
        if entry is None:
            mismatched.append(unit_id)
            continue
        if (
            row["checkpoint_hash"] != entry["checkpoint_hash"]
            or row["resolved_config_hash"] != entry["resolved_config_hash"]
        ):
            mismatched.append(unit_id)
    if mismatched:
        reasons.append(
            f"checkpoint_hash/resolved_config_hash inconsistent with the manifest for "
            f"{len(mismatched)} row(s), e.g. {mismatched[0]}"
        )

    prohibited = sorted(
        seed for seed, entry in seeds_map.items() if entry.get("low_optimizer_steps", 0) != 0
    )
    if prohibited:
        reasons.append(f"prohibited low-level optimizer exposure nonzero for seed(s) {prohibited}")

    # VK-D10 / A-VK-D10: V-K0B must verify the whole authorization tuple
    # before loading any checkpoint. The raw panel carries no artifact hash
    # of its own (VK-D3 sidecar-digest territory, out of this analyzer's
    # scope) -- the durable record of "this tuple was verified" is the
    # authorization block the driver writes into the manifest. The analyzer
    # independently re-derives the same tuple from the raw panel and
    # cross-checks it (fields and hash) against that recorded authorization.
    authorization = manifest.get("authorization")
    if authorization is None:
        reasons.append(
            "manifest carries no oracle-panel authorization record "
            "(the V-K0A artifact tuple was never verified before this run)"
        )
    else:
        recomputed_payload = _panel_tuple_payload(oracle_panel)
        recomputed_hash = _panel_expected_sha256(oracle_panel)
        recorded_payload = {
            field: authorization.get(field) for field in ORACLE_PANEL_AUTHORIZATION_TUPLE_FIELDS
        }
        if isinstance(recorded_payload.get("row_count"), int) and not isinstance(
            recorded_payload.get("row_count"), bool
        ):
            recorded_payload["row_count"] = int(recorded_payload["row_count"])
        if recomputed_payload != recorded_payload:
            reasons.append(
                "oracle-panel verdict tuple mismatch: the tuple re-derived from the raw panel "
                "does not match the authorization tuple recorded in the manifest"
            )
        if recomputed_hash != authorization.get("artifact_sha256"):
            reasons.append(
                "oracle-panel verdict tuple mismatch: recomputed artifact_sha256 does not match "
                "manifest.authorization.artifact_sha256 (stale or differently constituted artifact)"
            )
    if oracle_panel["row_count"] != VK0A_PANEL_ROW_COUNT:
        reasons.append(
            f"oracle-panel verdict tuple mismatch: row_count {oracle_panel['row_count']} "
            f"!= frozen {VK0A_PANEL_ROW_COUNT}"
        )
    if oracle_panel["contract_id"] != VK0_CONTRACT_ID:
        reasons.append("oracle-panel verdict tuple mismatch: contract_id does not match")

    return reasons


def is_source_not_identified(oracle_panel: dict[str, Any]) -> bool:
    return oracle_panel["verdict"] == VK0A_VERDICT_NOT_IDENTIFIED


# =============================================================================
# Row-level quantities: U_opp, U_SET, U_nat, hazard, urgency classification
# =============================================================================


def classify_urgency(u_src: float) -> str:
    """MEASUREMENT §3: URGENT U_src>0.5, STABLE U_src<0.5, BOUNDARY U_src=0.5.

    Recomputed from oracle_u_src -- the row's own oracle_urgency_class field
    is validated for shape but never trusted for classification, so the
    analyzer recomputes this statistic solely from the row files as required.
    """
    if u_src > MATERIALITY:
        return URGENT
    if u_src < MATERIALITY:
        return STABLE
    return BOUNDARY


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(float(v) for v in values) / len(values)


def compute_u_opp(units: list[dict[str, Any]]) -> float | None:
    """MEASUREMENT §4A / §5: select the argmax named-SET candidate on
    select-phase draws, then compute its effect on disjoint evaluate-phase
    draws -- the maximizer may not be selected and evaluated on the same
    draws."""
    keep_select = [
        u["window_return"] for u in units
        if u["estimand_family"] == ESTIMAND_KEEP_REFERENCE and u["phase"] == PHASE_SELECT
    ]
    keep_eval = [
        u["window_return"] for u in units
        if u["estimand_family"] == ESTIMAND_KEEP_REFERENCE and u["phase"] == PHASE_EVALUATE
    ]
    opp_units = [u for u in units if u["estimand_family"] == ESTIMAND_OPP_NAMED_SET]
    candidates = sorted({u["candidate_skill"] for u in opp_units})
    mean_keep_select = _mean(keep_select)
    mean_keep_eval = _mean(keep_eval)
    if not candidates or mean_keep_select is None or mean_keep_eval is None:
        return None

    best_candidate = None
    best_select_effect = None
    for z in candidates:
        select_returns = [
            u["window_return"] for u in opp_units
            if u["candidate_skill"] == z and u["phase"] == PHASE_SELECT
        ]
        mean_select = _mean(select_returns)
        if mean_select is None:
            continue
        effect = mean_select - mean_keep_select
        if best_select_effect is None or effect > best_select_effect:
            best_select_effect = effect
            best_candidate = z
    if best_candidate is None:
        return None

    eval_returns = [
        u["window_return"] for u in opp_units
        if u["candidate_skill"] == best_candidate and u["phase"] == PHASE_EVALUATE
    ]
    mean_eval = _mean(eval_returns)
    if mean_eval is None:
        return None
    return max(0.0, mean_eval - mean_keep_eval)


def compute_u_set(units: list[dict[str, Any]]) -> float | None:
    """MEASUREMENT §4B: mean(SET_SAMPLED - KEEP_REFERENCE) on paired
    evaluate draws."""
    keep_eval = [
        u["window_return"] for u in units
        if u["estimand_family"] == ESTIMAND_KEEP_REFERENCE and u["phase"] == PHASE_EVALUATE
    ]
    set_eval = [
        u["window_return"] for u in units
        if u["estimand_family"] == ESTIMAND_SET_SAMPLED and u["phase"] == PHASE_EVALUATE
    ]
    mean_keep = _mean(keep_eval)
    mean_set = _mean(set_eval)
    if mean_keep is None or mean_set is None:
        return None
    return mean_set - mean_keep


def compute_u_nat(units: list[dict[str, Any]]) -> float | None:
    """MEASUREMENT §4C: mean(NATURAL - KEEP_REFERENCE) on paired evaluate
    draws."""
    keep_eval = [
        u["window_return"] for u in units
        if u["estimand_family"] == ESTIMAND_KEEP_REFERENCE and u["phase"] == PHASE_EVALUATE
    ]
    nat_eval = [
        u["window_return"] for u in units
        if u["estimand_family"] == ESTIMAND_NATURAL and u["phase"] == PHASE_EVALUATE
    ]
    mean_keep = _mean(keep_eval)
    mean_nat = _mean(nat_eval)
    if mean_keep is None or mean_nat is None:
        return None
    return mean_nat - mean_keep


def build_row_table(
    check_rows: list[dict[str, Any]], unit_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    units_by_parent: dict[str, list[dict[str, Any]]] = {}
    for u in unit_rows:
        units_by_parent.setdefault(u["parent_check_unit_id"], []).append(u)

    table: list[dict[str, Any]] = []
    for row in check_rows:
        units = units_by_parent.get(row["check_unit_id"], [])
        keep_prob = row["keep_prob"]
        ineligible = keep_prob is None or (isinstance(keep_prob, float) and math.isnan(keep_prob))
        table.append(
            {
                "check_unit_id": row["check_unit_id"],
                "training_seed": int(row["training_seed"]),
                "episode_id": row["episode_id"],
                "agent_order_code": row["agent_order_code"],
                "urgency_class": classify_urgency(float(row["oracle_u_src"])),
                "u_opp": compute_u_opp(units),
                "u_set": compute_u_set(units),
                "u_nat": compute_u_nat(units),
                "hazard": None if ineligible else 1.0 - float(keep_prob),
                "natural_set_indicator": 1 if row["natural_token_kind"] == NATURAL_TOKEN_SET else 0,
                "slow_match_vector": [int(x) for x in row["slow_match_vector"]],
                "fast_match_vector": [int(x) for x in row["fast_match_vector"]],
            }
        )
    return table


# =============================================================================
# Support floor (deterministic counts; EVIDENCE_DESIGN "Support floor")
# =============================================================================


def compute_support_floor(check_rows: list[dict[str, Any]]) -> dict[str, Any]:
    per_seed: dict[str, Any] = {}
    seeds = sorted({int(row["training_seed"]) for row in check_rows})
    overall_pass = True
    for seed in seeds:
        rows = [row for row in check_rows if int(row["training_seed"]) == seed]
        urgency = [classify_urgency(float(row["oracle_u_src"])) for row in rows]
        orders = [row["agent_order_code"] for row in rows]
        urgent_total = sum(1 for u in urgency if u == URGENT)
        stable_total = sum(1 for u in urgency if u == STABLE)
        urgent_canonical = sum(
            1 for u, o in zip(urgency, orders) if u == URGENT and o == AGENT_ORDER_CANONICAL
        )
        stable_canonical = sum(
            1 for u, o in zip(urgency, orders) if u == STABLE and o == AGENT_ORDER_CANONICAL
        )
        urgent_reversed = sum(
            1 for u, o in zip(urgency, orders) if u == URGENT and o == AGENT_ORDER_REVERSED
        )
        stable_reversed = sum(
            1 for u, o in zip(urgency, orders) if u == STABLE and o == AGENT_ORDER_REVERSED
        )
        seed_pass = (
            urgent_total >= SUPPORT_FLOOR_CLASS_MIN
            and stable_total >= SUPPORT_FLOOR_CLASS_MIN
            and urgent_canonical >= SUPPORT_FLOOR_CLASS_ORDER_MIN
            and stable_canonical >= SUPPORT_FLOOR_CLASS_ORDER_MIN
            and urgent_reversed >= SUPPORT_FLOOR_CLASS_ORDER_MIN
            and stable_reversed >= SUPPORT_FLOOR_CLASS_ORDER_MIN
        )
        per_seed[str(seed)] = {
            "urgent_total": urgent_total,
            "stable_total": stable_total,
            "urgent_canonical": urgent_canonical,
            "stable_canonical": stable_canonical,
            "urgent_reversed": urgent_reversed,
            "stable_reversed": stable_reversed,
            "pass": seed_pass,
        }
        overall_pass = overall_pass and seed_pass
    return {"per_seed": per_seed, "pass": overall_pass}


# =============================================================================
# Seed-first nested bootstrap (Inference; top=training seed, nested=episode)
# =============================================================================


def _cluster_key(entry: dict[str, Any]) -> tuple[int, str]:
    return (int(entry["training_seed"]), str(entry["episode_id"]))


def build_bootstrap_context(
    table: list[dict[str, Any]], iterations: int, seed: int
) -> dict[str, Any]:
    clusters = sorted({_cluster_key(e) for e in table})
    cluster_index = {c: i for i, c in enumerate(clusters)}
    n_clusters = len(clusters)
    cluster_id = np.array([cluster_index[_cluster_key(e)] for e in table], dtype=np.int64)

    seeds = sorted({c[0] for c in clusters})
    clusters_of_seed = {s: [cluster_index[c] for c in clusters if c[0] == s] for s in seeds}
    n_seeds = len(seeds)

    rng = np.random.default_rng(seed)
    weight_matrix = np.zeros((iterations, n_clusters), dtype=np.int32)
    for it in range(iterations):
        chosen_positions = rng.integers(0, n_seeds, size=n_seeds)
        for pos in chosen_positions:
            members = clusters_of_seed[seeds[int(pos)]]
            n_members = len(members)
            if n_members == 0:
                continue
            draw = rng.integers(0, n_members, size=n_members)
            drawn = [members[int(i)] for i in draw]
            np.add.at(weight_matrix[it], drawn, 1)

    return {
        "cluster_index": cluster_index,
        "cluster_id": cluster_id,
        "n_clusters": n_clusters,
        "weight_matrix": weight_matrix,
        "seeds": seeds,
    }


def _group_bound(
    values: np.ndarray,
    eligible: np.ndarray,
    mask: np.ndarray,
    cluster_id: np.ndarray,
    ctx: dict[str, Any],
) -> tuple[dict[str, float], np.ndarray]:
    n_clusters = ctx["n_clusters"]
    weight_matrix = ctx["weight_matrix"]
    included = eligible & mask
    cluster_sum = np.bincount(cluster_id[included], weights=values[included], minlength=n_clusters)
    cluster_count = np.bincount(cluster_id[included], minlength=n_clusters).astype(np.float64)
    total_count = float(cluster_count.sum())
    point = float(cluster_sum.sum() / total_count) if total_count > 0 else float("nan")
    iter_sum = weight_matrix @ cluster_sum
    iter_count = weight_matrix @ cluster_count
    with np.errstate(invalid="ignore", divide="ignore"):
        iter_mean = np.where(iter_count > 0, iter_sum / np.where(iter_count > 0, iter_count, 1), np.nan)
    finite = iter_mean[np.isfinite(iter_mean)]
    lower = float(np.quantile(finite, LOWER_QUANTILE)) if finite.size else float("nan")
    upper = float(np.quantile(finite, UPPER_QUANTILE)) if finite.size else float("nan")
    stats = {"point": point, "lower_95": lower, "upper_95": upper, "n": int(total_count)}
    return stats, iter_mean


def _group_difference(
    values: np.ndarray,
    eligible: np.ndarray,
    mask_a: np.ndarray,
    mask_b: np.ndarray,
    cluster_id: np.ndarray,
    ctx: dict[str, Any],
) -> dict[str, float]:
    stats_a, iter_a = _group_bound(values, eligible, mask_a, cluster_id, ctx)
    stats_b, iter_b = _group_bound(values, eligible, mask_b, cluster_id, ctx)
    diff_point = stats_a["point"] - stats_b["point"]
    diff_iter = iter_a - iter_b
    finite = diff_iter[np.isfinite(diff_iter)]
    lower = float(np.quantile(finite, LOWER_QUANTILE)) if finite.size else float("nan")
    upper = float(np.quantile(finite, UPPER_QUANTILE)) if finite.size else float("nan")
    return {"point": diff_point, "lower_95": lower, "upper_95": upper}


def _values_and_eligibility(table: list[dict[str, Any]], key: str) -> tuple[np.ndarray, np.ndarray]:
    values = np.array([e[key] if e[key] is not None else 0.0 for e in table], dtype=np.float64)
    eligible = np.array([e[key] is not None for e in table], dtype=bool)
    return values, eligible


def _expanded_match_arrays(
    table: list[dict[str, Any]], key: str, ctx: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    cluster_index = ctx["cluster_index"]
    values: list[float] = []
    cluster_ids: list[int] = []
    orders: list[str] = []
    for e in table:
        cid = cluster_index[_cluster_key(e)]
        for v in e[key]:
            values.append(float(v))
            cluster_ids.append(cid)
            orders.append(e["agent_order_code"])
    return (
        np.asarray(values, dtype=np.float64),
        np.asarray(cluster_ids, dtype=np.int64),
        np.asarray(orders, dtype=object),
    )


# =============================================================================
# Competence floor
# =============================================================================


def compute_competence_floor(table: list[dict[str, Any]], ctx: dict[str, Any]) -> dict[str, Any]:
    slow_values, slow_clusters, slow_orders = _expanded_match_arrays(table, "slow_match_vector", ctx)
    fast_values, fast_clusters, fast_orders = _expanded_match_arrays(table, "fast_match_vector", ctx)
    eligible_slow = np.ones(len(slow_values), dtype=bool)
    eligible_fast = np.ones(len(fast_values), dtype=bool)

    result: dict[str, Any] = {}
    passes: list[bool] = []
    for order in (AGENT_ORDER_CANONICAL, AGENT_ORDER_REVERSED):
        slow_stats, _ = _group_bound(slow_values, eligible_slow, slow_orders == order, slow_clusters, ctx)
        fast_stats, _ = _group_bound(fast_values, eligible_fast, fast_orders == order, fast_clusters, ctx)
        result[order] = {"slow_match": slow_stats, "fast_match": fast_stats}
        passes.append(slow_stats["lower_95"] > COMPETENCE_FLOOR_MIN)
        passes.append(fast_stats["lower_95"] > COMPETENCE_FLOOR_MIN)
    result["pass"] = all(passes)
    return result


# =============================================================================
# Opportunity access (VK-D9 / A-VK-D9 executable predicates, verbatim)
# =============================================================================


def compute_opportunity(table: list[dict[str, Any]], ctx: dict[str, Any]) -> dict[str, Any]:
    u_opp_values, u_opp_eligible = _values_and_eligibility(table, "u_opp")
    urgency = np.array([e["urgency_class"] for e in table], dtype=object)
    order = np.array([e["agent_order_code"] for e in table], dtype=object)
    cluster_id = ctx["cluster_id"]

    urgent_mask = urgency == URGENT
    stable_mask = urgency == STABLE
    strata = {
        "pooled": np.ones(len(table), dtype=bool),
        AGENT_ORDER_CANONICAL: order == AGENT_ORDER_CANONICAL,
        AGENT_ORDER_REVERSED: order == AGENT_ORDER_REVERSED,
    }

    result: dict[str, Any] = {}
    any_decisive_fail = False
    all_pass = True
    for name in REQUIRED_OPPORTUNITY_STRATA:
        stratum_mask = strata[name]
        urgent_stats, _ = _group_bound(
            u_opp_values, u_opp_eligible, stratum_mask & urgent_mask, cluster_id, ctx
        )
        stable_stats, _ = _group_bound(
            u_opp_values, u_opp_eligible, stratum_mask & stable_mask, cluster_id, ctx
        )
        diff_stats = _group_difference(
            u_opp_values,
            u_opp_eligible,
            stratum_mask & urgent_mask,
            stratum_mask & stable_mask,
            cluster_id,
            ctx,
        )
        # A-VK-D9, opp_pass: strict inequalities.
        stratum_pass = (
            urgent_stats["lower_95"] > MATERIALITY
            and stable_stats["upper_95"] < MATERIALITY
            and diff_stats["lower_95"] > MATERIALITY
        )
        # A-VK-D9, decisive failure: inclusive (<=, >=) inequalities.
        decisive_fail = (
            urgent_stats["upper_95"] <= MATERIALITY
            or stable_stats["lower_95"] >= MATERIALITY
            or diff_stats["upper_95"] <= MATERIALITY
        )
        result[name] = {
            "urgent": urgent_stats,
            "stable": stable_stats,
            "diff": diff_stats,
            "pass": bool(stratum_pass),
            "decisive_fail": bool(decisive_fail),
        }
        any_decisive_fail = any_decisive_fail or decisive_fail
        all_pass = all_pass and stratum_pass

    result["any_decisive_fail"] = bool(any_decisive_fail)
    result["all_pass"] = bool(all_pass)
    return result


def compute_diagnostic_u_set(table: list[dict[str, Any]], ctx: dict[str, Any]) -> dict[str, Any]:
    """MEASUREMENT §4 'Replacement-skill diagnosis': reported, not gating."""
    u_set_values, u_set_eligible = _values_and_eligibility(table, "u_set")
    urgency = np.array([e["urgency_class"] for e in table], dtype=object)
    cluster_id = ctx["cluster_id"]
    urgent_stats, _ = _group_bound(u_set_values, u_set_eligible, urgency == URGENT, cluster_id, ctx)
    stable_stats, _ = _group_bound(u_set_values, u_set_eligible, urgency == STABLE, cluster_id, ctx)
    return {"urgent": urgent_stats, "stable": stable_stats}


# =============================================================================
# Natural alignment (A-VK-D9 corrected natural predicates, pooled)
# =============================================================================


def compute_natural(table: list[dict[str, Any]], ctx: dict[str, Any]) -> dict[str, Any]:
    u_nat_values, u_nat_eligible = _values_and_eligibility(table, "u_nat")
    hazard_values, hazard_eligible = _values_and_eligibility(table, "hazard")
    setrate_values = np.array([e["natural_set_indicator"] for e in table], dtype=np.float64)
    setrate_eligible = np.ones(len(table), dtype=bool)
    urgency = np.array([e["urgency_class"] for e in table], dtype=object)
    cluster_id = ctx["cluster_id"]

    urgent_mask = urgency == URGENT
    stable_mask = urgency == STABLE

    nat_urgent, _ = _group_bound(u_nat_values, u_nat_eligible, urgent_mask, cluster_id, ctx)
    nat_stable, _ = _group_bound(u_nat_values, u_nat_eligible, stable_mask, cluster_id, ctx)
    lambda_diff = _group_difference(hazard_values, hazard_eligible, urgent_mask, stable_mask, cluster_id, ctx)
    setrate_diff = _group_difference(
        setrate_values, setrate_eligible, urgent_mask, stable_mask, cluster_id, ctx
    )

    # A-VK-D9: natural decisively wrong iff any of these (inclusive bounds).
    decisive_wrong = (
        nat_urgent["upper_95"] <= MATERIALITY
        or nat_stable["lower_95"] >= MATERIALITY
        or nat_stable["upper_95"] <= -MATERIALITY
        or lambda_diff["upper_95"] <= 0.0
        or setrate_diff["upper_95"] <= 0.0
    )
    # A-VK-D9 / MEASUREMENT "Natural access": pass requires all of these
    # (strict bounds), including a positive point-estimate SET-rate contrast.
    natural_pass = (
        nat_urgent["lower_95"] > MATERIALITY
        and nat_stable["lower_95"] > -MATERIALITY
        and nat_stable["upper_95"] < MATERIALITY
        and lambda_diff["lower_95"] > 0.0
        and setrate_diff["point"] > 0.0
    )

    return {
        "u_nat_urgent": nat_urgent,
        "u_nat_stable": nat_stable,
        "lambda_diff": lambda_diff,
        "set_rate_diff": setrate_diff,
        "decisive_wrong": bool(decisive_wrong),
        "pass": bool(natural_pass and not decisive_wrong),
    }


# =============================================================================
# Top-level selection: first-match precedence 1..8
# =============================================================================


def run_analysis(
    trace_path: str | Path,
    units_path: str | Path,
    oracle_panel_path: str | Path,
    manifest_path: str | Path,
) -> dict[str, Any]:
    check_rows = _load_jsonl(Path(trace_path))
    unit_rows = _load_jsonl(Path(units_path))
    oracle_panel = _load_json(Path(oracle_panel_path))
    manifest = _load_json(Path(manifest_path))

    errors: list[str] = []
    for i, row in enumerate(check_rows):
        errors.extend(validate_check_row(row, i))
    for i, row in enumerate(unit_rows):
        errors.extend(validate_unit_row(row, i))
    errors.extend(validate_manifest(manifest))
    errors.extend(validate_oracle_panel(oracle_panel))
    if errors:
        raise SchemaValidationError("; ".join(errors))

    result: dict[str, Any] = {
        "contract_id": VK0_CONTRACT_ID,
        "trace_schema_version": VK0_TRACE_SCHEMA_VERSION,
        "analyzer_git_blob_sha1": _git_blob_sha1(Path(__file__)),
        "row_counts": {"check_rows": len(check_rows), "unit_rows": len(unit_rows)},
        "training_seeds": sorted({int(row["training_seed"]) for row in check_rows}),
    }
    chain: list[str] = []

    invalid_reasons = compute_invalid_reasons(check_rows, unit_rows, oracle_panel, manifest)
    if invalid_reasons:
        chain.append(f"row 1 ({RESULT_ROWS[1]}): triggered -- {invalid_reasons}")
        result["result"] = {"row": 1, "code": RESULT_ROWS[1], "reasons": invalid_reasons, "reason_chain": chain}
        return result
    chain.append(f"row 1 ({RESULT_ROWS[1]}): not triggered")

    if is_source_not_identified(oracle_panel):
        reasons = ["oracle panel verdict is TOY_HETEROGENEOUS_RENEWAL_URGENCY_NOT_IDENTIFIED"]
        chain.append(f"row 2 ({RESULT_ROWS[2]}): triggered -- {reasons}")
        result["result"] = {"row": 2, "code": RESULT_ROWS[2], "reasons": reasons, "reason_chain": chain}
        return result
    chain.append(f"row 2 ({RESULT_ROWS[2]}): not triggered -- panel verdict is IDENTIFIED")

    support_floor = compute_support_floor(check_rows)
    result["support_floor"] = support_floor
    if not support_floor["pass"]:
        reasons = ["support floor not met for at least one training seed; see support_floor.per_seed"]
        chain.append(f"row 3 ({RESULT_ROWS[3]}): triggered -- {reasons}")
        result["result"] = {"row": 3, "code": RESULT_ROWS[3], "reasons": reasons, "reason_chain": chain}
        return result
    chain.append(f"row 3 ({RESULT_ROWS[3]}): not triggered -- support floor met for every seed")

    table = build_row_table(check_rows, unit_rows)
    ctx = build_bootstrap_context(table, BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED)
    result["bootstrap"] = {
        "iterations": BOOTSTRAP_ITERATIONS,
        "seed": BOOTSTRAP_SEED,
        "seed_derivation": BOOTSTRAP_SEED_DERIVATION,
    }

    competence = compute_competence_floor(table, ctx)
    result["competence_floor"] = competence
    if not competence["pass"]:
        reasons = ["competence floor not met; see competence_floor"]
        chain.append(f"row 4 ({RESULT_ROWS[4]}): triggered -- {reasons}")
        result["result"] = {"row": 4, "code": RESULT_ROWS[4], "reasons": reasons, "reason_chain": chain}
        return result
    chain.append(f"row 4 ({RESULT_ROWS[4]}): not triggered -- competence floor met both orders")

    opportunity = compute_opportunity(table, ctx)
    result["opportunity"] = opportunity
    result["diagnostic_u_set"] = compute_diagnostic_u_set(table, ctx)
    if opportunity["any_decisive_fail"]:
        reasons = ["at least one required opportunity stratum decisively failed"]
        chain.append(f"row 5 ({RESULT_ROWS[5]}): triggered -- {reasons}")
        result["result"] = {"row": 5, "code": RESULT_ROWS[5], "reasons": reasons, "reason_chain": chain}
        return result
    chain.append(f"row 5 ({RESULT_ROWS[5]}): not triggered -- no required stratum decisively failed")
    if not opportunity["all_pass"]:
        reasons = ["opportunity access unresolved in at least one required stratum"]
        chain.append(f"row 7 ({RESULT_ROWS[7]}): triggered via opportunity -- {reasons}")
        result["result"] = {"row": 7, "code": RESULT_ROWS[7], "reasons": reasons, "reason_chain": chain}
        return result
    chain.append("opportunity access: all required strata pass")

    natural = compute_natural(table, ctx)
    result["natural"] = natural
    if natural["decisive_wrong"]:
        reasons = ["natural alignment decisively wrong-direction"]
        chain.append(f"row 6 ({RESULT_ROWS[6]}): triggered -- {reasons}")
        result["result"] = {"row": 6, "code": RESULT_ROWS[6], "reasons": reasons, "reason_chain": chain}
        return result
    chain.append(f"row 6 ({RESULT_ROWS[6]}): not triggered")
    if natural["pass"]:
        reasons = ["opportunity access and natural alignment both identified"]
        chain.append(f"row 8 ({RESULT_ROWS[8]}): triggered -- {reasons}")
        result["result"] = {"row": 8, "code": RESULT_ROWS[8], "reasons": reasons, "reason_chain": chain}
        return result
    reasons = ["natural alignment unresolved"]
    chain.append(f"row 7 ({RESULT_ROWS[7]}): triggered via natural alignment -- {reasons}")
    result["result"] = {"row": 7, "code": RESULT_ROWS[7], "reasons": reasons, "reason_chain": chain}
    return result


# =============================================================================
# CLI
# =============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze the V-K0B unrestricted-R30 result.")
    parser.add_argument("--trace", required=True)
    parser.add_argument("--units", required=True)
    parser.add_argument("--oracle-panel", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    try:
        summary = run_analysis(args.trace, args.units, args.oracle_panel, args.manifest)
    except SchemaValidationError as exc:
        print(f"VK0 analyzer refuses -- frozen schema violation: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    _write_json(Path(args.out), summary)
    print(
        f"VK0 analysis completed result={summary['result']['code']} output={args.out}",
        flush=True,
    )


if __name__ == "__main__":
    main()
