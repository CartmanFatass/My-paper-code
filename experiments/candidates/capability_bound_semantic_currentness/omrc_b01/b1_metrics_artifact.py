"""Lossless metrics-only publication boundary for CBSC-OMRC-B01.

This module owns file layout, canonical ordering, byte inventory, source/B0
identity and literal-null interpretation fields.  It deliberately does not
derive scientific reductions.  Domain rows are supplied by the four narrow
producer modules and are preserved one canonical JSON object per line.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from .artifact import canonical_json_bytes, ensure_confined
from .b1_contract import (
    B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
    B1_INNOVATOR_SELECTION_REQUEST_ID,
    B1_INNOVATOR_SELECTION_RESPONSE_SHA256,
    B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
    B1_LITERAL_BINDING_REQUEST_ID,
    B1_METRICS_ONLY_RESPONSE_SHA256,
    B1_METRICS_ONLY_SPEC_RELATIVE_PATH,
    B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
    B1_METRICS_ONLY_REQUEST_ID,
    B1_LITERAL_BINDING_RESPONSE_SHA256,
    B1_OBJECT_DURABLE_CAP_BYTES,
    B1_RUN_NAME,
    B1_SEEDS,
    B1Plan,
)


B1_METRICS_SCHEMA = "cbsc_omrc_b01_b_explore_result_v1"
B1_METRICS_TEST_SCHEMA = "cbsc_omrc_b01_b_explore_result_test_only_v1"
OBJECT_ID = "CBSC-OMRC-B01"
FORMAL_ANALYSIS_BOUND = False
READINESS_DISPOSITION = "REPAIR_REQUIRED"
SCIENTIFIC_DECISION = "DECISION_PENDING"
INCIDENT_CLAIM = "ENGINEERING_INCIDENT_ONLY"
MAXIMUM_CLAIM_CEILING = (
    "The maximum claim is one preliminary recurrent-PPO learning signal, competent null, "
    "instability diagnosis, generic-conditioning explanation, predictive-index sufficiency "
    "observation, or adverse counterexample on `CBSC-DYNAMIC-CACHE-2R-1C-v1` under the fixed "
    "three-to-five-seed B exposure."
)
EXPLICIT_CLAIM_EXCLUSIONS = (
    "It is not stable superiority, representation necessity, universal RAW inferiority, "
    "natural prevalence, paid acquisition, authentication, receiver credit, "
    "variable-population/lifetime or general MARL value, UAV transfer, safety, deployment, "
    "direction convergence/closure, or reinterpretation of the exact factorial or "
    "`CBSC-LR01=UNRESOLVED`."
)
REPO_ROOT = Path(__file__).resolve().parents[4]
LITERAL_BINDING_SPEC_RELATIVE_PATH = (
    "docs/research/candidates/capability_bound_semantic_currentness/"
    "CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md"
)

LITERAL_NULL_DERIVED_FIELDS = (
    "heldout_mean_return", "terminal_mean_return", "mean_oracle_regret",
    "normalized_return_auc", "struct_minus_raw_auc", "struct_minus_deranged_auc",
    "struct_minus_pi_auc", "oracle_action_accuracy", "invalid_serve_rate",
    "missed_serve_rate", "unnecessary_refresh_rate", "missed_refresh_rate",
    "inactive_fallback_accuracy", "owner_twin_flip_accuracy",
    "semantic_twin_flip_accuracy", "correct_swapped_sensitivity",
    "capability_specificity", "retention_gap_effect", "owner_event_order_effect",
    "semantic_event_order_effect", "clear_competent_null", "separation_from_deranged",
    "separation_from_pi", "residual_concentrated_in_gated", "material_instability",
    "adverse_seed", "catastrophic_seed", "promotion_eligible", "scientific_branch",
    "scientific_polarity", "b2_extension_trigger",
)
AUC_METADATA_FIELDS = (
    "return_auc_x_divisor", "return_auc_y_normalization", "return_auc_y_scale",
    "return_auc_split_scope", "return_auc_panel_pooling",
    "return_auc_episode_aggregation", "return_auc_seed_aggregation",
    "return_auc_pairing_rule", "return_auc_missing_rule",
    "return_auc_nonfinite_rule", "return_auc_scientific_interpretation",
)
DIAGNOSTIC_METADATA_FIELDS = (
    "numerator", "denominator", "eligible_support_rule", "panel_scope",
    "split_pooling", "per_seed_aggregation", "checkpoint_reduction", "paired_unit",
    "minimum_support", "zero_denominator_rule", "effect", "interpretation",
)
DIAGNOSTIC_NAMES = (
    "oracle_action_accuracy", "invalid_serve_rate", "missed_serve_rate",
    "unnecessary_refresh_rate", "missed_refresh_rate",
    "inactive_fallback_accuracy", "owner_twin_flip_accuracy",
    "semantic_twin_flip_accuracy", "correct_swapped_sensitivity",
    "capability_specificity", "retention_gap_effect", "owner_event_order_effect",
    "semantic_event_order_effect",
)

# Insertion order is the canonical raw publication inventory order.
TABLE_KEY_FIELDS: dict[str, tuple[str, ...]] = {
    "tape_transitions": ("run_order", "seed", "split_order", "tape_id", "transition_index"),
    "evaluator_decision_truth": ("run_order", "seed", "split_order", "tape_id", "opportunity_id"),
    "policy_decisions": ("run_order", "seed", "checkpoint_update", "split_order", "tape_id", "opportunity_id", "arm_order"),
    "per_tape_curves": ("run_order", "seed", "split_order", "tape_id", "arm_order"),
    "motif_twin_index": ("run_order", "seed", "tape_id", "pair_id", "member_role"),
    "support_signature_counts": (
        "run_order", "run_name", "seed", "split_order", "split", "motif_family_or_null", "motif_side_or_null",
        "request_active", "access_gated", "presented_body_native_neutral",
        "address_match_truth", "payload_source_match_truth", "content_match_truth",
        "owner_match_truth", "epoch_match_truth", "capability_match_truth",
        "overall_valid_truth", "oracle_action", "presented_body_age_opportunities",
    ),
    "policy_support_signature_counts": (
        "run_order", "run_name", "seed", "split_order", "split", "motif_family_or_null", "motif_side_or_null",
        "request_active", "access_gated", "presented_body_native_neutral",
        "address_match_truth", "payload_source_match_truth", "content_match_truth",
        "owner_match_truth", "epoch_match_truth", "capability_match_truth",
        "overall_valid_truth", "oracle_action", "presented_body_age_opportunities",
        "arm_order", "arm", "checkpoint_update", "selected_action",
    ),
    "motif_pair_support_counts": ("run_order", "seed", "motif_family"),
    "training_decisions": ("run_order", "seed", "arm_order", "training_episode_id", "opportunity_id"),
    "training_episodes": ("run_order", "seed", "arm_order", "training_episode_id"),
    "optimizer_steps": ("run_order", "seed", "arm_order", "rollout_update", "ppo_epoch", "minibatch_index"),
    "resource_admissions": (
        "run_order", "invocation_kind", "original_slot_index", "attempt_order",
        "seed", "arm_order",
    ),
    "telemetry": (
        "run_order", "invocation_kind", "original_slot_index", "attempt_order",
        "seed", "arm_order",
    ),
    "audits": ("run_order", "attempt_order", "seed_or_minus_one", "arm_or_minus_one", "audit_code"),
    "raw_competence": ("seed",),
}
FORMAL_TABLE_ROW_COUNTS = {
    "tape_transitions": 204_288,
    "evaluator_decision_truth": 32_256,
    "policy_decisions": 73_728,
    "per_tape_curves": 768,
    "motif_twin_index": 2_088,
    "motif_pair_support_counts": 24,
    "training_decisions": 110_592,
    "training_episodes": 4_608,
    "optimizer_steps": 9_216,
    "raw_competence": 3,
}
FORMAL_PROJECTION_MAX_ROW_COUNTS = {
    "resource_admissions": 48,
    "telemetry": 48,
}
FORMAL_SUPPORT_TOTALS = {
    "support_signature_counts": 32_256,
    "policy_support_signature_counts": 73_728,
}

PARALLEL_MODULE_PROTOCOL = {
    "b1_shared_tables": (
        "build_b1_shared_truth_tables", "SHARED_TABLES_SCHEMA", "RUN_ORDER", "SPLIT_ORDER",
    ),
    "b1_policy_records": (
        "build_checkpoint_policy_records", "build_complete_policy_curves",
        "build_policy_support_signature_counts", "build_literal_null_manifest_fields",
        "POLICY_DECISION_RECORD_SCHEMA", "POLICY_CURVE_RECORD_SCHEMA",
        "POLICY_SUPPORT_COUNT_RECORD_SCHEMA", "POLICY_RECORD_KEY_FIELDS",
        "POLICY_RECORD_OBSERVATION_FIELDS", "POLICY_CURVE_KEY_FIELDS",
        "POLICY_CURVE_VALUE_FIELDS", "POLICY_SUPPORT_SIGNATURE_FIELDS",
    ),
    "b1_training_records": (
        "build_training_exposure_records", "merge_training_exposure_slices",
        "TrainingExposureRecords",
    ),
    "b1_mechanical": (
        "compute_b1_mechanical", "compute_raw_competence", "b0_nonpolarity_record",
        "B1_MECHANICAL_SCHEMA", "RAW_COMPETENCE_SCHEMA", "B0_NONPOLARITY_SCHEMA",
    ),
}


class MetricsArtifactError(ValueError):
    """Metrics-only evidence is incomplete, reordered, drifted, or interpretive."""


_TRANSACTION_TOKEN = object()


class _CanonicalTransactionWitness:
    """Module-private proof that formal bytes came through the canonical producer path."""

    __slots__ = (
        "_token", "attempt_id", "source_identity_sha256",
        "prepared_inventory_sha256", "artifact_inventory_sha256", "reread_sha256",
    )

    def __init__(self, token: object, identity: Mapping[str, Any]) -> None:
        if token is not _TRANSACTION_TOKEN:
            raise MetricsArtifactError("canonical transaction witness is nonconstructible")
        self._token = token
        self.attempt_id = identity["attempt_id"]
        self.source_identity_sha256 = _digest(canonical_json_bytes(identity))
        self.prepared_inventory_sha256: str | None = None
        self.artifact_inventory_sha256: str | None = None
        self.reread_sha256: str | None = None


def _start_canonical_transaction(identity: Mapping[str, Any]) -> _CanonicalTransactionWitness:
    return _CanonicalTransactionWitness(_TRANSACTION_TOKEN, identity)


def _require_transaction_witness(
    witness: object, *, identity: Mapping[str, Any] | None = None,
    require_reread: bool = False,
) -> _CanonicalTransactionWitness:
    if (
        type(witness) is not _CanonicalTransactionWitness
        or witness._token is not _TRANSACTION_TOKEN
    ):
        raise MetricsArtifactError("formal metrics operation lacks canonical transaction witness")
    if identity is not None and (
        witness.attempt_id != identity.get("attempt_id")
        or witness.source_identity_sha256 != _digest(canonical_json_bytes(identity))
    ):
        raise MetricsArtifactError("canonical transaction source identity drifted")
    if require_reread and not all((
        witness.prepared_inventory_sha256,
        witness.artifact_inventory_sha256,
        witness.reread_sha256,
    )):
        raise MetricsArtifactError("canonical transaction lacks materialized reread binding")
    return witness


def _bind_transaction_reread(
    witness: object, *, prepared_inventory: Sequence[Mapping[str, Any]],
    artifact_inventory: Sequence[Mapping[str, Any]], reread: Mapping[str, Any],
) -> None:
    bound = _require_transaction_witness(witness)
    prepared_sha = _digest(canonical_json_bytes(list(prepared_inventory)))
    if bound.prepared_inventory_sha256 not in {None, prepared_sha}:
        raise MetricsArtifactError("canonical prepared inventory drifted before reread")
    bound.prepared_inventory_sha256 = prepared_sha
    bound.artifact_inventory_sha256 = _digest(
        canonical_json_bytes(list(artifact_inventory))
    )
    bound.reread_sha256 = _digest(canonical_json_bytes(reread))


@dataclass(frozen=True)
class PreparedMetricsTables:
    """Canonical encoded table bytes prepared without filesystem mutation."""

    inventory: tuple[Mapping[str, Any], ...]
    payloads: tuple[tuple[str, bytes], ...]

    @property
    def byte_count(self) -> int:
        return sum(len(payload) for _, payload in self.payloads)


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _require_hex(name: str, value: object, length: int) -> str:
    if (
        type(value) is not str or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise MetricsArtifactError(f"{name} must be {length} lowercase hexadecimal characters")
    return value


def _sort_atom(value: object) -> tuple[int, object]:
    if value is None:
        return (0, 0)
    if type(value) is bool:
        return (1, int(value))
    if type(value) is int:
        return (2, value)
    if type(value) is str:
        return (3, value)
    raise MetricsArtifactError("canonical key values must be null, bool, int, or string")


def _canonical_key(row: Mapping[str, Any], fields: Sequence[str]) -> tuple[Any, ...]:
    if any(field not in row for field in fields):
        raise MetricsArtifactError("raw table row is missing a canonical key field")
    run_order = {B1_RUN_NAME: 0, "CBSC-OMRC-B2-TWO-SEED-STABILITY": 1}
    arm_order = {
        "STRUCT-CURRENTNESS-GRU": 0, "RAW-GRU": 1,
        "PI-GRU": 2, "DERANGED-CURRENTNESS-GRU": 3,
    }
    split_order = {"TRAIN": 0, "EVAL_STOCHASTIC": 1, "EVAL_MOTIF": 2}
    categorical = {"run_name": run_order, "arm": arm_order, "split": split_order}
    values: list[tuple[int, object]] = []
    for field in fields:
        value = row[field]
        if field == "pair_id" and type(value) is str:
            try:
                values.append((2, int(value.rsplit(":", 1)[-1])))
            except ValueError as exc:
                raise MetricsArtifactError("pair_id has no canonical numeric member order") from exc
        elif field == "member_role":
            member_order = {"A": 0, "B": 1, "GAP1": 0, "GAP6": 1}
            if value not in member_order:
                raise MetricsArtifactError("member_role has no canonical order")
            values.append((2, member_order[value]))
        elif field in categorical:
            if value not in categorical[field]:
                raise MetricsArtifactError(f"{field} has no canonical order")
            values.append((2, categorical[field][value]))
        else:
            values.append(_sort_atom(value))
    return tuple(values)


def _validate_rows(table: str, value: object, *, allow_test_only: bool) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise MetricsArtifactError(f"{table} must be a list of lossless raw rows")
    if not value and not allow_test_only:
        raise MetricsArtifactError(f"formal {table} cannot be empty")
    fields = TABLE_KEY_FIELDS[table]
    keys: list[tuple[Any, ...]] = []
    rows: list[Mapping[str, Any]] = []
    for row in value:
        if not isinstance(row, Mapping):
            raise MetricsArtifactError(f"{table} contains a non-record")
        canonical_json_bytes(row)
        keys.append(_canonical_key(row, fields))
        rows.append(row)
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise MetricsArtifactError(f"{table} differs from strict canonical order/uniqueness")
    if table == "audits" and not allow_test_only:
        audit_fields = {
            "run_order", "attempt_order", "seed_or_minus_one", "arm_or_minus_one",
            "audit_code", "authority_type", "source_table", "source_key_range",
            "source_raw_slice", "fact_name", "expected", "observed",
            "expected_sha256", "actual_sha256", "binding_status",
            "source_relative_path", "json_pointer", "source_file_sha256",
            "payload_shape", "payload_dtype", "payload_nonzero_count",
        }
        for row in rows:
            if set(row) != audit_fields:
                raise MetricsArtifactError("formal typed audit row fields differ")
            table_authority = row["authority_type"] == "CANONICAL_TABLE_AUTHORITY"
            direct_authority = str(row["authority_type"]).startswith("DIRECT_RAW_FACT")
            if "PENDING" in str(row["binding_status"]):
                raise MetricsArtifactError("formal typed audit remains pending/unbound")
            if table_authority and (
                row["binding_status"] != "BOUND_MATERIALIZED_TABLE_REREAD"
                or row["observed"] is None or row["actual_sha256"] is None
            ):
                raise MetricsArtifactError("formal table audit is not materialized-bound")
            if direct_authority and (
                not str(row["binding_status"]).startswith("BOUND_SOURCE_REREAD")
                or row["expected_sha256"] is None or row["actual_sha256"] is None
                or row["source_relative_path"] is None or row["json_pointer"] is None
                or row["source_file_sha256"] is None or row["payload_shape"] is None
                or row["payload_dtype"] is None or row["payload_nonzero_count"] is None
            ):
                raise MetricsArtifactError("formal direct audit is not source-reread-bound")
    return rows


def canonicalize_metrics_table_order(
    tables: Mapping[str, object],
) -> dict[str, list[Mapping[str, Any]]]:
    """Sort producer rows once by the publication authority's exact keys."""

    if not isinstance(tables, Mapping) or list(tables) != list(TABLE_KEY_FIELDS):
        raise MetricsArtifactError("raw table inventory names/order differ")
    output: dict[str, list[Mapping[str, Any]]] = {}
    for name, fields in TABLE_KEY_FIELDS.items():
        value = tables[name]
        if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
            raise MetricsArtifactError(f"{name} is not a raw record list")
        rows = sorted(value, key=lambda row: _canonical_key(row, fields))
        keys = [_canonical_key(row, fields) for row in rows]
        if len(keys) != len(set(keys)):
            raise MetricsArtifactError(f"{name} contains duplicate canonical keys")
        output[name] = rows
    return output


def validate_support_aggregate(
    table: str, rows: Sequence[Mapping[str, Any]], *, expected_total: int,
) -> None:
    """Validate a Counter aggregate by unique signature and represented support."""

    if table not in FORMAL_SUPPORT_TOTALS or expected_total != FORMAL_SUPPORT_TOTALS[table]:
        raise MetricsArtifactError("support aggregate identity/total differs")
    if not isinstance(rows, Sequence) or not rows:
        raise MetricsArtifactError(f"formal {table} aggregate is empty")
    total = 0
    keys: list[tuple[Any, ...]] = []
    fields = TABLE_KEY_FIELDS[table]
    for row in rows:
        if not isinstance(row, Mapping):
            raise MetricsArtifactError(f"{table} contains a non-record")
        count = row.get("support_count")
        if type(count) is not int or count <= 0:
            raise MetricsArtifactError(f"{table} support_count must be a positive integer")
        keys.append(_canonical_key(row, fields))
        total += count
    if len(keys) != len(set(keys)):
        raise MetricsArtifactError(f"{table} contains duplicate canonical signatures")
    if total != expected_total:
        raise MetricsArtifactError(f"{table} represented support total differs")


def validate_formal_table_coverage(
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
    *, expected_invocation_keys: Sequence[tuple[str, int, int, int, int, int | None, int | None]] | None,
) -> None:
    """Validate formal fixed tables and aggregate support without expanding Counters."""

    if list(tables) != list(TABLE_KEY_FIELDS):
        raise MetricsArtifactError("formal 15-table inventory order differs")
    for name, expected in FORMAL_TABLE_ROW_COUNTS.items():
        if len(tables[name]) != expected:
            raise MetricsArtifactError(f"formal {name} row coverage differs")
    for name, expected in FORMAL_SUPPORT_TOTALS.items():
        validate_support_aggregate(name, tables[name], expected_total=expected)
    if expected_invocation_keys is None or not expected_invocation_keys:
        raise MetricsArtifactError("formal invocation-key authority is absent")
    validate_invocation_table_coverage(
        tables["resource_admissions"], tables["telemetry"],
        expected_invocation_keys=expected_invocation_keys,
    )


def validate_invocation_table_coverage(
    resource_rows: Sequence[Mapping[str, Any]],
    telemetry_rows: Sequence[Mapping[str, Any]],
    *, expected_invocation_keys: Sequence[tuple[str, int, int, int, int, int | None, int | None]],
) -> None:
    expected = set(expected_invocation_keys)
    if len(expected) != len(expected_invocation_keys) or len(expected) > 48:
        raise MetricsArtifactError("formal invocation keys are duplicate or exceed maximum")
    for name, rows in (
        ("resource_admissions", resource_rows), ("telemetry", telemetry_rows)
    ):
        observed = {
            (
                row.get("invocation_kind"), row.get("original_slot_index"),
                row.get("seed"), row.get("arm_order"), row.get("attempt_order"),
                row.get("slice_start_update"), row.get("slice_stop_update"),
            )
            for row in rows
        }
        if len(observed) != len(rows) or observed != expected:
            raise MetricsArtifactError(
                f"formal {name} invocation identity/order/interval coverage differs"
            )


def require_parallel_module_protocols() -> dict[str, object]:
    """Import the four producer seams or fail before any artifact mutation."""

    package = __package__ or ""
    loaded: dict[str, object] = {}
    for short_name, required in PARALLEL_MODULE_PROTOCOL.items():
        try:
            module = importlib.import_module(f"{package}.{short_name}")
        except ImportError as exc:
            raise MetricsArtifactError(f"required metrics producer module is absent: {short_name}") from exc
        missing = [name for name in required if not hasattr(module, name)]
        if missing:
            raise MetricsArtifactError(
                f"required metrics producer seam is absent: {short_name}:{','.join(missing)}"
            )
        loaded[short_name] = module
    shared = loaded["b1_shared_tables"]
    policy = loaded["b1_policy_records"]
    mechanical = loaded["b1_mechanical"]
    if getattr(shared, "SHARED_TABLES_SCHEMA") != "cbsc_omrc_b01_shared_truth_tables_v1":
        raise MetricsArtifactError("shared-table producer schema differs")
    expected_policy = {
        "POLICY_DECISION_RECORD_SCHEMA": "cbsc_omrc_b01_policy_decision_record_v1",
        "POLICY_CURVE_RECORD_SCHEMA": "cbsc_omrc_b01_policy_curve_record_v1",
        "POLICY_SUPPORT_COUNT_RECORD_SCHEMA": "cbsc_omrc_b01_policy_support_count_record_v1",
    }
    if any(getattr(policy, name) != value for name, value in expected_policy.items()):
        raise MetricsArtifactError("policy producer schema differs")
    if (
        tuple(getattr(policy, "DERIVED_NULL_FIELDS")) != LITERAL_NULL_DERIVED_FIELDS
        or tuple(getattr(policy, "AUC_METADATA_NULL_FIELDS")) != AUC_METADATA_FIELDS
        or tuple(getattr(policy, "DIAGNOSTIC_METADATA_NULL_FIELDS"))
        != DIAGNOSTIC_METADATA_FIELDS
        or tuple(getattr(policy, "DIAGNOSTIC_NAMES")) != DIAGNOSTIC_NAMES
    ):
        raise MetricsArtifactError("policy literal-null schema differs from metrics publication")
    _validate_null_packet(policy.build_literal_null_manifest_fields())
    if (
        getattr(mechanical, "B1_MECHANICAL_SCHEMA") != "cbsc_omrc_b01_b1_mechanical_v1"
        or getattr(mechanical, "RAW_COMPETENCE_SCHEMA")
        != "cbsc_omrc_b01_b1_raw_competence_v1"
    ):
        raise MetricsArtifactError("mechanical producer schema differs")
    return loaded


def prepare_metrics_only_tables(
    tables: Mapping[str, object], *, allow_test_only: bool = False,
    formal_invocation_keys: Sequence[
        tuple[str, int, int, int, int, int | None, int | None]
    ] | None = None,
    _transaction_witness: object = None,
) -> PreparedMetricsTables:
    """Encode canonical table bytes without touching the filesystem."""

    if not isinstance(tables, Mapping) or list(tables) != list(TABLE_KEY_FIELDS):
        raise MetricsArtifactError("raw table inventory names/order differ from the metrics-only spec")
    if not allow_test_only:
        _require_transaction_witness(_transaction_witness)
    validated = {
        name: _validate_rows(name, tables[name], allow_test_only=allow_test_only)
        for name in TABLE_KEY_FIELDS
    }
    if not allow_test_only:
        validate_formal_table_coverage(
            validated, expected_invocation_keys=formal_invocation_keys
        )
    inventory: list[dict[str, Any]] = []
    payloads: list[tuple[str, bytes]] = []
    for name, rows in validated.items():
        relative_path = f"metrics/raw/{name}.jsonl"
        payload = b"".join(canonical_json_bytes(row) + b"\n" for row in rows)
        inventory.append({
            "table": name,
            "relative_path": relative_path,
            "key_fields": list(TABLE_KEY_FIELDS[name]),
            "row_count": len(rows),
            "byte_count": len(payload),
            "sha256": _digest(payload),
            "codec": "CANONICAL_JSONL_ASCII_V1",
        })
        payloads.append((relative_path, payload))
    prepared = PreparedMetricsTables(tuple(inventory), tuple(payloads))
    if not allow_test_only:
        witness = _require_transaction_witness(_transaction_witness)
        witness.prepared_inventory_sha256 = _digest(canonical_json_bytes(inventory))
    return prepared


def materialize_prepared_metrics_tables(
    staging: Path,
    prepared: PreparedMetricsTables,
    *,
    allowed_root: Path,
    _transaction_witness: object = None,
) -> list[dict[str, Any]]:
    """Create every already-prepared table once, without cleanup or overwrite."""

    if type(prepared) is not PreparedMetricsTables:
        raise MetricsArtifactError("prepared metrics tables type differs")
    if _transaction_witness is not None:
        witness = _require_transaction_witness(_transaction_witness)
        if witness.prepared_inventory_sha256 != _digest(
            canonical_json_bytes(list(prepared.inventory))
        ):
            raise MetricsArtifactError("formal prepared bytes lack canonical inventory binding")
    try:
        root = ensure_confined(Path(staging), Path(allowed_root))
    except ValueError as exc:
        raise MetricsArtifactError("metrics staging lies outside allowed_root") from exc
    if not root.is_dir():
        root.mkdir(parents=True, exist_ok=False)
    raw_root = root / "metrics" / "raw"
    if raw_root.exists():
        raise FileExistsError(f"create-only metrics raw directory already exists: {raw_root}")
    raw_root.mkdir(parents=True)
    for relative_path, payload in prepared.payloads:
        path = root / relative_path
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    return [dict(record) for record in prepared.inventory]


def _materialize_prepared_metrics_subset(
    staging: Path, prepared: PreparedMetricsTables, *, table_names: Sequence[str],
    allowed_root: Path, _transaction_witness: object = None,
) -> None:
    """Internal acyclic writer for authority tables first and audits last."""

    requested = tuple(table_names)
    if len(requested) != len(set(requested)) or any(name not in TABLE_KEY_FIELDS for name in requested):
        raise MetricsArtifactError("metrics subset table inventory differs")
    if _transaction_witness is not None:
        witness = _require_transaction_witness(_transaction_witness)
        if witness.prepared_inventory_sha256 != _digest(
            canonical_json_bytes(list(prepared.inventory))
        ):
            raise MetricsArtifactError("formal subset lacks canonical prepared binding")
    root = ensure_confined(Path(staging), Path(allowed_root))
    raw_root = root / "metrics" / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    payloads = dict(prepared.payloads)
    for name in requested:
        relative = f"metrics/raw/{name}.jsonl"
        path = root / relative
        with path.open("xb") as stream:
            stream.write(payloads[relative])
            stream.flush()
            os.fsync(stream.fileno())


def materialize_metrics_only_tables(
    staging: Path,
    tables: Mapping[str, object],
    *,
    allowed_root: Path,
    allow_test_only: bool = False,
) -> list[dict[str, Any]]:
    """TEST_ONLY arbitrary-table seam; formal production never calls this API."""

    if not allow_test_only:
        raise MetricsArtifactError(
            "formal raw tables require canonical attempt reconstruction; caller table injection is TEST_ONLY"
        )
    prepared = prepare_metrics_only_tables(tables, allow_test_only=True)
    return materialize_prepared_metrics_tables(
        staging, prepared, allowed_root=allowed_root
    )


def build_complete_artifact_inventory(root: Path) -> list[dict[str, Any]]:
    """Inventory every current artifact byte except the self-referential manifest."""

    base = Path(root).resolve(strict=True)
    if not base.is_dir():
        raise MetricsArtifactError("artifact inventory root is not a directory")
    records: list[dict[str, Any]] = []
    for path in sorted(
        (
            item for item in base.rglob("*")
            if item.is_file() and item != base / "manifest.json"
        ),
        key=lambda item: item.relative_to(base).as_posix(),
    ):
        payload = path.read_bytes()
        records.append({
            "relative_path": path.relative_to(base).as_posix(),
            "byte_count": len(payload),
            "sha256": _digest(payload),
        })
    return records


def build_prospective_artifact_inventory(
    root: Path, prepared: PreparedMetricsTables, *, allow_existing_equal: bool = False,
) -> list[dict[str, Any]]:
    """Combine current staging bytes with exact prepared table bytes, without writes."""

    if type(prepared) is not PreparedMetricsTables:
        raise MetricsArtifactError("prepared metrics tables type differs")
    records = build_complete_artifact_inventory(root)
    existing = {record["relative_path"] for record in records}
    for descriptor in prepared.inventory:
        relative = descriptor["relative_path"]
        if relative in existing or (Path(root) / relative).exists():
            if allow_existing_equal:
                current = next(
                    (row for row in records if row["relative_path"] == relative), None
                )
                if current == {
                    "relative_path": relative,
                    "byte_count": descriptor["byte_count"],
                    "sha256": descriptor["sha256"],
                }:
                    continue
            raise FileExistsError(f"create-only prospective table already exists: {relative}")
        records.append({
            "relative_path": relative,
            "byte_count": descriptor["byte_count"],
            "sha256": descriptor["sha256"],
        })
    records.sort(key=lambda row: row["relative_path"])
    return records


def validate_prospective_output_cap(
    *, artifact_inventory: Sequence[Mapping[str, Any]], manifest: Mapping[str, Any]
) -> dict[str, int]:
    """Use actual canonical payload bytes to refuse an over-cap publication before writes."""

    artifact_bytes = sum(record["byte_count"] for record in artifact_inventory)
    manifest_bytes = len(canonical_json_bytes(manifest)) + 1
    total_bytes = artifact_bytes + manifest_bytes
    if total_bytes > B1_OBJECT_DURABLE_CAP_BYTES:
        raise MetricsArtifactError(
            "prospective canonical publication exceeds the 512 MiB object cap"
        )
    if manifest.get("durable_size_bytes") != total_bytes:
        raise MetricsArtifactError(
            "manifest durable_size_bytes differs from canonical final-size fixed point"
        )
    return {
        "artifact_bytes_excluding_manifest": artifact_bytes,
        "manifest_bytes": manifest_bytes,
        "total_bytes": total_bytes,
        "cap_bytes": B1_OBJECT_DURABLE_CAP_BYTES,
    }


def conservative_formal_size_projection() -> dict[str, Any]:
    """Frozen result-blind census and finite-capacity disposition.

    No observed row, checkpoint, support domain, TEST fixture, or result byte is
    consulted.  The current frozen object lacks maximum encoded lengths for
    several variable-width fields and retained evidence containers.  Therefore
    a finite byte total would be invented; the authoritative result is an
    unestablished capacity bound and ``REPAIR_REQUIRED``.
    """

    table_row_upper_bounds = {
        **dict(FORMAL_TABLE_ROW_COUNTS),
        "support_signature_counts": 32_256,
        "policy_support_signature_counts": 73_728,
        "resource_admissions": 48,
        "telemetry": 48,
        "audits": 11_638,
    }
    return {
        "schema": "cbsc_omrc_b01_b1_formal_canonical_capacity_projection_v1",
        "authority": "FROZEN_RESULT_BLIND_FORMAL_DESCRIPTOR",
        "codec": "CANONICAL_JSONL_ASCII_V1",
        "table_inventory_order": list(TABLE_KEY_FIELDS),
        "table_row_upper_bounds": table_row_upper_bounds,
        "audit_upper_bound_derivation": {
            "max_training_slices_per_slot": 3,
            "table_authority_rows": 10,
            "slot_count": 12,
            "max_direct_and_rollout_authorities_per_slot": 969,
            "total_rows": 10 + 12 * 969,
        },
        "non_table_inventory": {
            "checkpoint_envelopes": 48,
            "training_worker_slot_count": 12,
            "policy_replay_slot_count": 12,
            "resource_invocation_max": 48,
            "includes": [
                "raw_worker_results",
                "policy_replay_results",
                "bound_admissions",
                "raw_admission_receipts",
                "telemetry",
                "reviewed_b0_evidence",
                "pro_decision_evidence",
                "incident_lineage",
                "compact_full_mechanical_packet",
                "table_and_artifact_inventories",
                "manifest_fixed_point",
            ],
        },
        "unbounded_canonical_fields": [
            "attempt_id_utf8_length",
            "audit_code_and_fact_name_utf8_length",
            "source_and_incident_relative_path_utf8_length",
            "checkpoint_envelope_canonical_byte_length",
            "raw_worker_and_policy_replay_result_canonical_byte_length",
            "reviewed_b0_pro_decision_and_incident_evidence_byte_length",
        ],
        "depends_on_observed_or_test_bytes": False,
        "projected_total_bytes": None,
        "cap_bytes": B1_OBJECT_DURABLE_CAP_BYTES,
        "margin_bytes": None,
        "capacity_projection_pass": False,
        "performance_disposition": "REPAIR_REQUIRED",
        "reason": (
            "A finite full-formal canonical byte upper bound is not established because "
            "the frozen schema does not cap every retained variable-width field/container."
        ),
    }


def _validate_null_packet(value: object) -> tuple[dict[str, None], dict[str, None], dict[str, dict[str, None]]]:
    if not isinstance(value, Mapping) or set(value) != {
        "derived_fields", "auc_metadata", "diagnostic_metadata"
    }:
        raise MetricsArtifactError("literal-null packet fields differ")
    derived = value["derived_fields"]
    auc = value["auc_metadata"]
    diagnostics = value["diagnostic_metadata"]
    if not isinstance(derived, Mapping) or tuple(derived) != LITERAL_NULL_DERIVED_FIELDS:
        raise MetricsArtifactError("derived field names/order differ")
    if not isinstance(auc, Mapping) or tuple(auc) != AUC_METADATA_FIELDS:
        raise MetricsArtifactError("AUC metadata names/order differ")
    if not isinstance(diagnostics, Mapping) or tuple(diagnostics) != DIAGNOSTIC_NAMES:
        raise MetricsArtifactError("diagnostic metadata names/order differ")
    if any(item is not None for item in derived.values()) or any(item is not None for item in auc.values()):
        raise MetricsArtifactError("every derived and AUC metadata field must be literal null")
    for name, metadata in diagnostics.items():
        if not isinstance(metadata, Mapping) or tuple(metadata) != DIAGNOSTIC_METADATA_FIELDS:
            raise MetricsArtifactError(f"diagnostic metadata fields/order differ: {name}")
        if any(item is not None for item in metadata.values()):
            raise MetricsArtifactError(f"diagnostic metadata must be literal null: {name}")
    return dict(derived), dict(auc), {name: dict(metadata) for name, metadata in diagnostics.items()}


def _validate_identity(value: object) -> dict[str, Any]:
    required = {
        "attempt_id", "implementation_commit", "source_conformance_sha256",
        "configuration_sha256", "literal_binding_spec_path",
        "literal_binding_spec_sha256", "metrics_only_spec_path",
        "metrics_only_spec_sha256", "metrics_only_response_sha256",
        "literal_binding_response_sha256",
        "innovator_selection_request_id", "innovator_selection_archive_path",
        "innovator_selection_response_sha256", "literal_binding_request_id",
        "literal_binding_archive_path", "metrics_only_request_id",
        "metrics_only_archive_path",
        "decision_evidence_inventory",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise MetricsArtifactError("metrics source identity fields differ")
    identity = dict(value)
    if type(identity["attempt_id"]) is not str or not identity["attempt_id"]:
        raise MetricsArtifactError("attempt_id must be a nonempty exact string")
    _require_hex("implementation_commit", identity["implementation_commit"], 40)
    for field in ("source_conformance_sha256", "configuration_sha256",
                  "literal_binding_spec_sha256", "metrics_only_spec_sha256",
                  "metrics_only_response_sha256", "literal_binding_response_sha256",
                  "innovator_selection_response_sha256"):
        _require_hex(field, identity[field], 64)
    expected_paths = {
        "literal_binding_spec_path": LITERAL_BINDING_SPEC_RELATIVE_PATH,
        "metrics_only_spec_path": B1_METRICS_ONLY_SPEC_RELATIVE_PATH,
    }
    for field, relative in expected_paths.items():
        if identity[field] != relative:
            raise MetricsArtifactError(f"{field} differs from frozen spec path")
        path = REPO_ROOT / relative
        if not path.is_file() or _digest(path.read_bytes()) != identity[field.replace("path", "sha256")]:
            raise MetricsArtifactError(f"{field} bytes/digest differ")
    if identity["metrics_only_response_sha256"] != B1_METRICS_ONLY_RESPONSE_SHA256:
        raise MetricsArtifactError("metrics-only response SHA differs")
    if identity["literal_binding_response_sha256"] != B1_LITERAL_BINDING_RESPONSE_SHA256:
        raise MetricsArtifactError("literal-binding response SHA differs")
    expected_provenance = {
        "innovator_selection_request_id": B1_INNOVATOR_SELECTION_REQUEST_ID,
        "innovator_selection_archive_path": B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
        "innovator_selection_response_sha256": B1_INNOVATOR_SELECTION_RESPONSE_SHA256,
        "literal_binding_request_id": B1_LITERAL_BINDING_REQUEST_ID,
        "literal_binding_archive_path": B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
        "metrics_only_request_id": B1_METRICS_ONLY_REQUEST_ID,
        "metrics_only_archive_path": B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
    }
    if any(identity[field] != expected for field, expected in expected_provenance.items()):
        raise MetricsArtifactError(".01/.02/.03 request/response provenance differs")
    decision_inventory = identity["decision_evidence_inventory"]
    if not isinstance(decision_inventory, list) or len(decision_inventory) != 9:
        raise MetricsArtifactError("artifact-contained Pro decision inventory differs")
    expected_requests = (
        (B1_INNOVATOR_SELECTION_REQUEST_ID, B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
         B1_INNOVATOR_SELECTION_RESPONSE_SHA256),
        (B1_LITERAL_BINDING_REQUEST_ID, B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
         B1_LITERAL_BINDING_RESPONSE_SHA256),
        (B1_METRICS_ONLY_REQUEST_ID, B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
         B1_METRICS_ONLY_RESPONSE_SHA256),
    )
    expected_rows = []
    for request_id, response_origin, response_sha in expected_requests:
        origin_root = Path(response_origin).parent.as_posix()
        for kind, filename in (
            ("RESPONSE", "RESPONSE.md"),
            ("TRANSPORT_FACTS", "TRANSPORT_FACTS.json"),
            ("PACKET_MANIFEST", "PACKET_MANIFEST.json"),
        ):
            expected_rows.append((request_id, origin_root, response_sha, kind, filename))
    for row, expected in zip(decision_inventory, expected_rows, strict=True):
        request_id, origin_root, response_sha, kind, filename = expected
        if not isinstance(row, Mapping) or set(row) != {
            "request_id", "kind", "origin_relative_path", "artifact_relative_path",
            "sha256", "byte_count",
        }:
            raise MetricsArtifactError("Pro decision evidence descriptor fields differ")
        if (
            row["request_id"] != request_id or row["kind"] != kind
            or row["origin_relative_path"] != f"{origin_root}/{filename}"
            or row["artifact_relative_path"]
            != f"evidence/pro-decisions/{request_id}/{filename}"
            or type(row["byte_count"]) is not int or row["byte_count"] <= 0
        ):
            raise MetricsArtifactError("Pro decision evidence identity/path differs")
        _require_hex("Pro decision evidence SHA", row["sha256"], 64)
        if kind == "RESPONSE" and row["sha256"] != response_sha:
            raise MetricsArtifactError("Pro response SHA differs from frozen authority")
    expected_configuration = _digest(canonical_json_bytes(B1Plan().as_dict()))
    if identity["configuration_sha256"] != expected_configuration:
        raise MetricsArtifactError("configuration SHA differs from immutable B1Plan")
    return identity


def _validate_materialized_decisions(root: Path, source: Mapping[str, Any]) -> None:
    grouped: dict[str, dict[str, tuple[Mapping[str, Any], bytes]]] = {}
    for row in source["decision_evidence_inventory"]:
        path = (root / row["artifact_relative_path"]).resolve(strict=True)
        path.relative_to(root)
        payload = path.read_bytes()
        if len(payload) != row["byte_count"] or _digest(payload) != row["sha256"]:
            raise MetricsArtifactError("artifact-contained Pro decision bytes differ")
        grouped.setdefault(row["request_id"], {})[row["kind"]] = (row, payload)
    for request_id, records in grouped.items():
        if set(records) != {"RESPONSE", "TRANSPORT_FACTS", "PACKET_MANIFEST"}:
            raise MetricsArtifactError("Pro decision companion coverage differs")
        response_row, response_bytes = records["RESPONSE"]
        try:
            facts = json.loads(records["TRANSPORT_FACTS"][1].decode("utf-8"))
            packet = json.loads(records["PACKET_MANIFEST"][1].decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MetricsArtifactError("Pro decision companion JSON is unreadable") from exc
        if not isinstance(facts, Mapping) or not isinstance(packet, Mapping):
            raise MetricsArtifactError("Pro decision companion JSON schema differs")
        archive_paths = facts.get("archive_paths")
        packet_response = packet.get("response")
        expected_suffix = f"/{request_id}/RESPONSE.md"
        if (
            facts.get("schema_version") != 2
            or facts.get("request_id") != request_id
            or facts.get("response_sha256") != response_row["sha256"]
            or not isinstance(archive_paths, Mapping)
            or not str(archive_paths.get("response_file", "")).replace("\\", "/").endswith(expected_suffix)
            or packet.get("canonical_form") != "logical_packet_manifest"
            or packet.get("request_id") != request_id
            or not isinstance(packet_response, Mapping)
            or packet_response.get("sha256") != response_row["sha256"]
            or packet_response.get("bytes") != len(response_bytes)
            or not str(packet_response.get("path", "")).replace("\\", "/").endswith(expected_suffix)
            or response_row["artifact_relative_path"]
            != f"evidence/pro-decisions/{request_id}/RESPONSE.md"
        ):
            raise MetricsArtifactError("Pro response/transport/packet companion binding differs")


def _validate_b0(value: object) -> dict[str, Any]:
    required = {
        "manifest_sha256", "manifest_bytes", "reviewed_receipt_sha256",
        "inventory_sha256", "file_count", "total_bytes", "relative_root",
        "copied_inventory_sha256", "nonpolarity_index",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise MetricsArtifactError("B0 authority fields differ")
    result = dict(value)
    for field in ("manifest_sha256", "reviewed_receipt_sha256", "inventory_sha256"):
        _require_hex(f"B0 {field}", result[field], 64)
    for field in ("manifest_bytes", "file_count", "total_bytes"):
        if type(result[field]) is not int or result[field] <= 0:
            raise MetricsArtifactError(f"B0 {field} must be a positive integer")
    if result["relative_root"] != "b0-reviewed-evidence":
        raise MetricsArtifactError("B0 reviewed relative root differs")
    _require_hex("B0 copied inventory", result["copied_inventory_sha256"], 64)
    if result["copied_inventory_sha256"] != result["inventory_sha256"]:
        raise MetricsArtifactError("B0 copied inventory differs from reviewed authority")
    descriptor = result["nonpolarity_index"]
    if not isinstance(descriptor, Mapping) or set(descriptor) != {
        "relative_path", "sha256", "byte_count", "leaf_count"
    }:
        raise MetricsArtifactError("B0 nonpolarity index descriptor differs")
    _require_hex("B0 nonpolarity index SHA", descriptor["sha256"], 64)
    for field in ("byte_count", "leaf_count"):
        if type(descriptor[field]) is not int or descriptor[field] <= 0:
            raise MetricsArtifactError(f"B0 nonpolarity index {field} differs")
    return result


def _json_pointer(value: object, pointer: str) -> object:
    current = value
    for raw in pointer.split("/")[1:]:
        part = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, Mapping):
            current = current[part]
        else:
            raise MetricsArtifactError("B0 evaluator JSON pointer traverses a scalar")
    return current


def _b0_leaf_rows(
    source_relative_path: str, value: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Index only the two typed B0 evaluator-result subtrees fixed by B0 schema."""

    roots: list[tuple[str, object]] = []
    if source_relative_path == "manifest.json":
        arms = value.get("arm_records")
        if not isinstance(arms, list):
            raise MetricsArtifactError("reviewed B0 manifest arm_records are absent")
        for index, arm in enumerate(arms):
            try:
                evaluation = arm["records"]["diagnostics"]["evaluation"]
            except (KeyError, TypeError) as exc:
                raise MetricsArtifactError(
                    "reviewed B0 manifest evaluator subtree is absent"
                ) from exc
            roots.append((f"/arm_records/{index}/records/diagnostics/evaluation", evaluation))
    elif (
        source_relative_path.startswith("workers/")
        and source_relative_path.endswith("/result.json")
    ):
        try:
            evaluation = value["records"]["diagnostics"]["evaluation"]
        except (KeyError, TypeError) as exc:
            raise MetricsArtifactError("reviewed B0 worker evaluator subtree is absent") from exc
        roots.append(("/records/diagnostics/evaluation", evaluation))
    output: list[dict[str, Any]] = []
    flags = {
        "scientific_eligible": False,
        "classifier_eligible": False,
        "threshold_tuning_eligible": False,
        "b2_trigger_eligible": False,
        "promotion_eligible": False,
    }

    def descend(item: object, pointer: str) -> None:
        if isinstance(item, Mapping):
            for key in sorted(item):
                escaped = str(key).replace("~", "~0").replace("/", "~1")
                descend(item[key], f"{pointer}/{escaped}")
        elif isinstance(item, list):
            for index, child in enumerate(item):
                descend(child, f"{pointer}/{index}")
        else:
            output.append({
                "source_relative_path": source_relative_path,
                "json_pointer": pointer,
                "value_canonical_sha256": _digest(canonical_json_bytes(item)),
                **flags,
            })

    for pointer, item in roots:
        descend(item, pointer)
    return output


def build_b0_nonpolarity_leaf_index(
    json_records: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        row
        for relative in sorted(json_records)
        for row in _b0_leaf_rows(relative, json_records[relative])
    ]
    keys = [(row["source_relative_path"], row["json_pointer"]) for row in rows]
    if not rows or len(keys) != len(set(keys)):
        raise MetricsArtifactError("reviewed B0 evaluator leaf census is empty or duplicated")
    return rows


def _validate_materialized_b0(root: Path, b0: Mapping[str, Any]) -> None:
    evidence = (root / b0["relative_root"]).resolve(strict=True)
    evidence.relative_to(root)
    files = sorted(
        (path for path in evidence.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(evidence).as_posix(),
    )
    inventory = [
        {
            "path": path.relative_to(evidence).as_posix(),
            "byte_count": len(path.read_bytes()),
            "sha256": _digest(path.read_bytes()),
        }
        for path in files
    ]
    if (
        len(files) != b0["file_count"]
        or sum(row["byte_count"] for row in inventory) != b0["total_bytes"]
        or _digest(canonical_json_bytes(inventory)) != b0["copied_inventory_sha256"]
    ):
        raise MetricsArtifactError("materialized B0 inventory differs")
    manifest_path = evidence / "manifest.json"
    manifest_payload = manifest_path.read_bytes()
    if (
        len(manifest_payload) != b0["manifest_bytes"]
        or _digest(manifest_payload) != b0["manifest_sha256"]
    ):
        raise MetricsArtifactError("materialized B0 manifest differs")
    descriptor = b0["nonpolarity_index"]
    index_path = (root / descriptor["relative_path"]).resolve(strict=True)
    index_path.relative_to(root)
    payload = index_path.read_bytes()
    if len(payload) != descriptor["byte_count"] or _digest(payload) != descriptor["sha256"]:
        raise MetricsArtifactError("B0 nonpolarity index bytes differ")
    index = json.loads(payload.decode("ascii"))
    if index.get("nonpolarity", {}).get("b0_nonpolarity") != "ABSOLUTE":
        raise MetricsArtifactError("B0 nonpolarity authority differs")
    leaves = index.get("evaluator_leaves")
    if not isinstance(leaves, list) or len(leaves) != descriptor["leaf_count"]:
        raise MetricsArtifactError("B0 evaluator leaf count differs")
    flags = {
        "scientific_eligible", "classifier_eligible", "threshold_tuning_eligible",
        "b2_trigger_eligible", "promotion_eligible",
    }
    json_records: dict[str, Mapping[str, Any]] = {}
    for path in files:
        if path.suffix != ".json":
            continue
        try:
            value = json.loads(path.read_text(encoding="ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MetricsArtifactError("reviewed B0 JSON evidence is unreadable") from exc
        if not isinstance(value, Mapping):
            raise MetricsArtifactError("reviewed B0 JSON evidence must be an object")
        json_records[path.relative_to(evidence).as_posix()] = value
    expected_leaves = build_b0_nonpolarity_leaf_index(json_records)
    if leaves != expected_leaves:
        raise MetricsArtifactError("B0 evaluator leaf census has missing/extra/reordered rows")
    for row in leaves:
        if not isinstance(row, Mapping) or any(row.get(flag) is not False for flag in flags):
            raise MetricsArtifactError("B0 evaluator eligibility flag differs")
        source = (evidence / row["source_relative_path"]).resolve(strict=True)
        source.relative_to(evidence)
        source_value = json.loads(source.read_text(encoding="ascii"))
        leaf = _json_pointer(source_value, row["json_pointer"])
        if _digest(canonical_json_bytes(leaf)) != row["value_canonical_sha256"]:
            raise MetricsArtifactError("B0 evaluator pointer/value digest differs")


def _validate_law_digests(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {
        "environment", "adapter", "token", "analysis"
    }:
        raise MetricsArtifactError("law digest groups differ")
    result = dict(value)
    for name, digest in result.items():
        _require_hex(f"law digest {name}", digest, 64)
    return result


def _validate_mechanical(value: object) -> dict[str, Any]:
    required = {
        "schema", "mechanical_attempt_complete", "mechanical_conformance_pass",
        "scientific_packet_readable", "blocking_audit_codes", "mechanical_components",
        "raw_competence_by_seed", "inputs",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise MetricsArtifactError("mechanical packet fields differ")
    result = dict(value)
    if result["schema"] != "cbsc_omrc_b01_b1_mechanical_v1":
        raise MetricsArtifactError("mechanical packet schema differs")
    for field in ("mechanical_attempt_complete", "mechanical_conformance_pass", "scientific_packet_readable"):
        if type(result[field]) is not bool:
            raise MetricsArtifactError(f"mechanical {field} must be Boolean")
    if not isinstance(result["blocking_audit_codes"], list) or any(
        type(item) is not str or not item for item in result["blocking_audit_codes"]
    ):
        raise MetricsArtifactError("blocking_audit_codes differs")
    competence = result["raw_competence_by_seed"]
    if not isinstance(competence, list) or [row.get("seed") for row in competence if isinstance(row, Mapping)] != list(B1_SEEDS):
        raise MetricsArtifactError("RAW competence must cover the three seeds in canonical order")
    for row in competence:
        if set(row) != {"schema", "seed", "raw_competence_pass", "components", "inputs"}:
            raise MetricsArtifactError("RAW competence record fields differ")
        if row["schema"] != "cbsc_omrc_b01_b1_raw_competence_v1":
            raise MetricsArtifactError("RAW competence record schema differs")
        if row["raw_competence_pass"] not in {True, False, None}:
            raise MetricsArtifactError("RAW competence pass must be bool or null")
        canonical_json_bytes(row)
    return result


def _mechanical_summary(
    packet: Mapping[str, Any], *, table_inventory: Sequence[Mapping[str, Any]],
    artifact_inventory: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    competence = [{
        "schema": row["schema"], "seed": row["seed"],
        "raw_competence_pass": row["raw_competence_pass"],
        "components": dict(row["components"]),
    } for row in packet["raw_competence_by_seed"]]
    summary = {
        "schema": "cbsc_omrc_b01_b1_mechanical_summary_v1",
        "mechanical_schema": packet["schema"],
        "mechanical_attempt_complete": packet["mechanical_attempt_complete"],
        "mechanical_conformance_pass": packet["mechanical_conformance_pass"],
        "scientific_packet_readable": packet["scientific_packet_readable"],
        "blocking_audit_codes": list(packet["blocking_audit_codes"]),
        "mechanical_components": dict(packet["mechanical_components"]),
        "raw_competence_by_seed": competence,
        "input_bindings": {
            "tables": [{
                "table": row["table"], "sha256": row["sha256"],
                "row_count": row["row_count"], "byte_count": row["byte_count"],
            } for row in table_inventory],
            "artifact_inventory_sha256": _digest(
                canonical_json_bytes(list(artifact_inventory))
            ),
            "recomputed_full_packet_sha256": _digest(canonical_json_bytes(packet)),
        },
    }
    summary["summary_sha256"] = _digest(canonical_json_bytes(summary))
    return summary


def _validate_mechanical_summary(
    value: object, *, table_inventory: Sequence[Mapping[str, Any]],
    artifact_inventory: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    required = {
        "schema", "mechanical_schema", "mechanical_attempt_complete",
        "mechanical_conformance_pass", "scientific_packet_readable",
        "blocking_audit_codes", "mechanical_components", "raw_competence_by_seed",
        "input_bindings", "summary_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise MetricsArtifactError("mechanical summary fields differ")
    result = dict(value)
    supplied_summary_sha = result.pop("summary_sha256")
    _require_hex("mechanical summary SHA", supplied_summary_sha, 64)
    if _digest(canonical_json_bytes(result)) != supplied_summary_sha:
        raise MetricsArtifactError("mechanical summary fields differ from recomputed SHA")
    result["summary_sha256"] = supplied_summary_sha
    if (
        result["schema"] != "cbsc_omrc_b01_b1_mechanical_summary_v1"
        or result["mechanical_schema"] != "cbsc_omrc_b01_b1_mechanical_v1"
    ):
        raise MetricsArtifactError("mechanical summary schema differs")
    for field in (
        "mechanical_attempt_complete", "mechanical_conformance_pass",
        "scientific_packet_readable",
    ):
        if type(result[field]) is not bool:
            raise MetricsArtifactError(f"mechanical summary {field} must be Boolean")
    if not isinstance(result["blocking_audit_codes"], list) or not isinstance(
        result["mechanical_components"], Mapping
    ):
        raise MetricsArtifactError("mechanical summary codes/components differ")
    competence = result["raw_competence_by_seed"]
    if not isinstance(competence, list) or [row.get("seed") for row in competence] != list(B1_SEEDS):
        raise MetricsArtifactError("mechanical summary RAW competence coverage differs")
    for row in competence:
        if set(row) != {"schema", "seed", "raw_competence_pass", "components"}:
            raise MetricsArtifactError("mechanical summary RAW competence fields differ")
    expected_bindings = {
        "tables": [{
            "table": row["table"], "sha256": row["sha256"],
            "row_count": row["row_count"], "byte_count": row["byte_count"],
        } for row in table_inventory],
        "artifact_inventory_sha256": _digest(
            canonical_json_bytes(list(artifact_inventory))
        ),
    }
    bindings = result["input_bindings"]
    if not isinstance(bindings, Mapping) or set(bindings) != {
        "tables", "artifact_inventory_sha256", "recomputed_full_packet_sha256"
    }:
        raise MetricsArtifactError("mechanical typed input bindings differ")
    if (
        bindings["tables"] != expected_bindings["tables"]
        or bindings["artifact_inventory_sha256"]
        != expected_bindings["artifact_inventory_sha256"]
    ):
        raise MetricsArtifactError("mechanical input binding digest/coverage differs")
    _require_hex(
        "recomputed full mechanical packet SHA",
        bindings["recomputed_full_packet_sha256"], 64,
    )
    return result


def _validate_incident_lineage(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise MetricsArtifactError("incident lineage must be an ordered list")
    output: list[dict[str, Any]] = []
    seen_nodes: set[tuple[str, str]] = set()
    for row in value:
        if not isinstance(row, Mapping) or set(row) != {
            "attempt_id", "incident_manifest_sha256", "attempt_ledger_sha256",
            "incident_relative_path",
        }:
            raise MetricsArtifactError("incident lineage fields differ")
        attempt_id = row["attempt_id"]
        relative_path = row["incident_relative_path"]
        if type(attempt_id) is not str or not attempt_id:
            raise MetricsArtifactError("incident lineage attempt_id differs")
        relative = Path(relative_path) if type(relative_path) is str else Path(".")
        if (
            type(relative_path) is not str or not relative_path
            or "\\" in relative_path or relative.is_absolute()
            or ".." in relative.parts or relative.name != "incident.json"
            or relative.as_posix() != relative_path
        ):
            raise MetricsArtifactError("incident lineage relative path differs")
        _require_hex("incident manifest SHA", row["incident_manifest_sha256"], 64)
        _require_hex("attempt ledger SHA", row["attempt_ledger_sha256"], 64)
        node = (relative_path, row["incident_manifest_sha256"])
        if node in seen_nodes:
            raise MetricsArtifactError("incident lineage contains a duplicate/cycle")
        seen_nodes.add(node)
        output.append(dict(row))
    return output


def _claim_boundary(source: Mapping[str, Any]) -> dict[str, str]:
    return {
        "maximum_claim": MAXIMUM_CLAIM_CEILING,
        "explicit_exclusions": EXPLICIT_CLAIM_EXCLUSIONS,
        "bound_spec_path": B1_METRICS_ONLY_SPEC_RELATIVE_PATH,
        "bound_spec_sha256": source["metrics_only_spec_sha256"],
    }


def _validate_claim_boundary(value: object, source: Mapping[str, Any]) -> dict[str, str]:
    expected = _claim_boundary(source)
    if not isinstance(value, Mapping) or dict(value) != expected:
        raise MetricsArtifactError("scientific claim boundary differs from exact .03 text")
    return expected


def _build_metrics_only_manifest(
    *, identity: Mapping[str, Any], b0_evidence: Mapping[str, Any],
    law_digests: Mapping[str, str],
    table_inventory: Sequence[Mapping[str, Any]], artifact_inventory: Sequence[Mapping[str, Any]],
    literal_nulls: Mapping[str, Any],
    mechanical: Mapping[str, Any], incident_references: Sequence[Mapping[str, Any]],
    test_only: bool = False, _transaction_witness: object = None,
) -> dict[str, Any]:
    """Build a manifest only after raw-table bytes have been materialized."""

    if not test_only and not FORMAL_ANALYSIS_BOUND:
        raise MetricsArtifactError(
            "FORMAL_ANALYSIS_BOUND is false and caller manifests cannot replace canonical "
            "attempt reconstruction"
        )
    source = _validate_identity(identity)
    witness = None
    if not test_only:
        witness = _require_transaction_witness(
            _transaction_witness, identity=source, require_reread=True
        )
    b0 = _validate_b0(b0_evidence)
    laws = _validate_law_digests(law_digests)
    derived, auc, diagnostics = _validate_null_packet(literal_nulls)
    mechanical_full = _validate_mechanical(mechanical)
    lineage = _validate_incident_lineage(incident_references)
    inventory = [dict(row) for row in table_inventory]
    if [row.get("table") for row in inventory] != list(TABLE_KEY_FIELDS):
        raise MetricsArtifactError("table inventory names/order differ")
    all_files = [dict(row) for row in artifact_inventory]
    if any(
        not isinstance(row, Mapping)
        or set(row) != {"relative_path", "byte_count", "sha256"}
        for row in all_files
    ):
        raise MetricsArtifactError("complete artifact inventory descriptor fields differ")
    paths = [row["relative_path"] for row in all_files]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise MetricsArtifactError("complete artifact inventory order/uniqueness differs")
    if witness is not None and (
        witness.prepared_inventory_sha256 != _digest(canonical_json_bytes(inventory))
        or witness.artifact_inventory_sha256 != _digest(canonical_json_bytes(all_files))
    ):
        raise MetricsArtifactError("formal manifest inventory differs from transaction reread")
    artifact_bytes = sum(row["byte_count"] for row in all_files)
    mechanical_packet = mechanical_full
    manifest = {
        "schema": B1_METRICS_TEST_SCHEMA if test_only else B1_METRICS_SCHEMA,
        "test_only": test_only,
        "object_id": OBJECT_ID,
        "run_name": B1_RUN_NAME,
        "attempt_id": source["attempt_id"],
        "source_identity": source,
        "b0_evidence": b0,
        "law_digests": laws,
        "canonical_orders": {
            "run": [B1_RUN_NAME, "CBSC-OMRC-B2-TWO-SEED-STABILITY"],
            "arm": ["STRUCT-CURRENTNESS-GRU", "RAW-GRU", "PI-GRU", "DERANGED-CURRENTNESS-GRU"],
            "split": ["TRAIN", "EVAL_STOCHASTIC", "EVAL_MOTIF"],
            "checkpoints": [0, 12, 24, 48],
            "scientific_action": ["SERVE", "REFRESH", "SAFE_FALLBACK"],
        },
        "formal_capacity_projection": conservative_formal_size_projection(),
        "table_inventory": inventory,
        "artifact_inventory": all_files,
        "mechanical": mechanical_packet,
        "incident_references": lineage,
        "derived_fields": derived,
        "auc_metadata": auc,
        "diagnostic_metadata": diagnostics,
        "decision": SCIENTIFIC_DECISION,
        "claim_boundary": _claim_boundary(source),
        "incident_claim": INCIDENT_CLAIM,
        "convergence_required": False if test_only else True,
        "scientific_branch": None,
        "scientific_polarity": None,
        "promotion_eligible": None,
        "b2_extension_trigger": None,
        "formal_analysis_bound": FORMAL_ANALYSIS_BOUND,
        "readiness_disposition": READINESS_DISPOSITION,
        "durable_size_bytes": artifact_bytes,
    }
    for _ in range(16):
        fixed = artifact_bytes + len(canonical_json_bytes(manifest)) + 1
        if fixed == manifest["durable_size_bytes"]:
            break
        manifest["durable_size_bytes"] = fixed
    else:  # pragma: no cover - decimal-width fixed point converges immediately.
        raise MetricsArtifactError("durable-size fixed point did not converge")
    if manifest["durable_size_bytes"] > B1_OBJECT_DURABLE_CAP_BYTES:
        raise MetricsArtifactError("durable size exceeds the 512 MiB object cap")
    canonical_json_bytes(manifest)
    return manifest


def build_metrics_only_manifest(
    *, identity: Mapping[str, Any], b0_evidence: Mapping[str, Any],
    law_digests: Mapping[str, str],
    table_inventory: Sequence[Mapping[str, Any]],
    artifact_inventory: Sequence[Mapping[str, Any]],
    literal_nulls: Mapping[str, Any], mechanical: Mapping[str, Any],
    incident_references: Sequence[Mapping[str, Any]], test_only: bool = False,
) -> dict[str, Any]:
    """TEST_ONLY manifest builder; formal construction is production-internal."""

    return _build_metrics_only_manifest(
        identity=identity, b0_evidence=b0_evidence, law_digests=law_digests,
        table_inventory=table_inventory, artifact_inventory=artifact_inventory,
        literal_nulls=literal_nulls, mechanical=mechanical,
        incident_references=incident_references, test_only=test_only,
        _transaction_witness=None,
    )


def _load_jsonl(path: Path) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    payload = path.read_bytes()
    if payload and not payload.endswith(b"\n"):
        raise MetricsArtifactError("raw table JSONL lacks terminal newline")
    for line in payload.splitlines():
        try:
            row = json.loads(line.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MetricsArtifactError("raw table is not canonical ASCII JSONL") from exc
        if canonical_json_bytes(row) != line:
            raise MetricsArtifactError("raw table row bytes are not canonical JSON")
        rows.append(row)
    return rows


def validate_metrics_only_manifest(
    value: Mapping[str, Any], *, root: Path, allow_test_only: bool = False,
) -> dict[str, Any]:
    """Re-read every table byte and independently validate inventory/order/nulls."""

    if not isinstance(value, Mapping):
        raise MetricsArtifactError("metrics-only manifest must be a mapping")
    manifest = dict(value)
    required = {
        "schema", "test_only", "object_id", "run_name", "attempt_id",
        "source_identity", "b0_evidence", "canonical_orders", "table_inventory",
        "law_digests", "formal_capacity_projection",
        "artifact_inventory",
        "mechanical", "incident_references", "derived_fields", "auc_metadata",
        "diagnostic_metadata", "decision", "claim_boundary", "incident_claim",
        "convergence_required", "scientific_branch",
        "scientific_polarity", "promotion_eligible", "b2_extension_trigger",
        "formal_analysis_bound", "readiness_disposition", "durable_size_bytes",
    }
    if set(manifest) != required:
        raise MetricsArtifactError("metrics-only manifest fields differ")
    test_only = manifest["schema"] == B1_METRICS_TEST_SCHEMA
    if test_only:
        if not allow_test_only or manifest["test_only"] is not True:
            raise MetricsArtifactError("TEST_ONLY metrics manifest requires explicit opt-in")
    elif manifest["schema"] == B1_METRICS_SCHEMA:
        if manifest["test_only"] is not False or not FORMAL_ANALYSIS_BOUND:
            raise MetricsArtifactError("formal metrics manifest is not currently bound")
    else:
        raise MetricsArtifactError("metrics-only manifest schema differs")
    if manifest["object_id"] != OBJECT_ID or manifest["run_name"] != B1_RUN_NAME:
        raise MetricsArtifactError("metrics-only object/run identity differs")
    if manifest["formal_capacity_projection"] != conservative_formal_size_projection():
        raise MetricsArtifactError("formal capacity projection differs from frozen descriptor")
    source = _validate_identity(manifest["source_identity"])
    if manifest["attempt_id"] != source["attempt_id"]:
        raise MetricsArtifactError("attempt identity differs")
    b0 = _validate_b0(manifest["b0_evidence"])
    _validate_law_digests(manifest["law_digests"])
    _validate_incident_lineage(manifest["incident_references"])
    _validate_null_packet({
        "derived_fields": manifest["derived_fields"],
        "auc_metadata": manifest["auc_metadata"],
        "diagnostic_metadata": manifest["diagnostic_metadata"],
    })
    if manifest["decision"] != SCIENTIFIC_DECISION:
        raise MetricsArtifactError("scientific decision must remain DECISION_PENDING")
    _validate_claim_boundary(manifest["claim_boundary"], source)
    if manifest["incident_claim"] != INCIDENT_CLAIM:
        raise MetricsArtifactError("incident claim must remain ENGINEERING_INCIDENT_ONLY")
    for field in ("scientific_branch", "scientific_polarity", "promotion_eligible", "b2_extension_trigger"):
        if manifest[field] is not None:
            raise MetricsArtifactError(f"{field} must remain literal null")
    if manifest["convergence_required"] is not (False if test_only else True):
        raise MetricsArtifactError("convergence_required differs from complete-three-seed routing")
    if manifest["formal_analysis_bound"] is not FORMAL_ANALYSIS_BOUND or manifest["readiness_disposition"] != READINESS_DISPOSITION:
        raise MetricsArtifactError("formal readiness gate differs")
    inventory = manifest["table_inventory"]
    if not isinstance(inventory, list) or [row.get("table") for row in inventory if isinstance(row, Mapping)] != list(TABLE_KEY_FIELDS):
        raise MetricsArtifactError("table inventory names/order differ")
    artifact_inventory = manifest["artifact_inventory"]
    if not isinstance(artifact_inventory, list):
        raise MetricsArtifactError("artifact inventory must be a list")
    supplied_mechanical = _validate_mechanical(manifest["mechanical"])
    base = Path(root).resolve(strict=True)
    _validate_materialized_decisions(base, source)
    _validate_materialized_b0(base, b0)
    seen_paths: set[Path] = set()
    materialized_tables: dict[str, list[Mapping[str, Any]]] = {}
    for descriptor in inventory:
        if not isinstance(descriptor, Mapping) or set(descriptor) != {
            "table", "relative_path", "key_fields", "row_count", "byte_count", "sha256", "codec"
        }:
            raise MetricsArtifactError("table inventory descriptor fields differ")
        name = descriptor["table"]
        if descriptor["key_fields"] != list(TABLE_KEY_FIELDS[name]) or descriptor["codec"] != "CANONICAL_JSONL_ASCII_V1":
            raise MetricsArtifactError("table inventory key/codec identity differs")
        relative = Path(descriptor["relative_path"])
        path = (base / relative).resolve(strict=True)
        try:
            path.relative_to(base)
        except ValueError as exc:
            raise MetricsArtifactError("table inventory path escapes artifact root") from exc
        if path in seen_paths or not path.is_file():
            raise MetricsArtifactError("table inventory path is duplicate or absent")
        seen_paths.add(path)
        payload = path.read_bytes()
        if len(payload) != descriptor["byte_count"] or _digest(payload) != descriptor["sha256"]:
            raise MetricsArtifactError("table byte count/digest differs")
        rows = _load_jsonl(path)
        if len(rows) != descriptor["row_count"]:
            raise MetricsArtifactError("table row count differs")
        _validate_rows(name, rows, allow_test_only=test_only)
        materialized_tables[name] = rows
    actual_inventory = build_complete_artifact_inventory(base)
    if manifest["artifact_inventory"] != actual_inventory:
        raise MetricsArtifactError("complete artifact inventory digest differs")
    inputs = supplied_mechanical["inputs"]
    arguments_only = (
        test_only and isinstance(inputs, Mapping)
        and inputs.get("authority") == "TEST_ARGUMENTS_ONLY"
    )
    if not arguments_only:
        try:
            from .b1_metrics_production import reconstruct_b1_mechanical_from_artifact

            recomputed_mechanical = reconstruct_b1_mechanical_from_artifact(
                root=base,
                descriptor=inputs,
                tables=materialized_tables,
                table_inventory=inventory,
                artifact_inventory=actual_inventory,
                source_identity=source,
                test_only=test_only,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            raise MetricsArtifactError(
                "mechanical packet consumer reconstruction failed"
            ) from exc
        if canonical_json_bytes(recomputed_mechanical) != canonical_json_bytes(
            supplied_mechanical
        ):
            raise MetricsArtifactError(
                "full mechanical packet differs from consumer reconstruction"
            )
    durable = manifest["durable_size_bytes"]
    expected_durable = sum(
        row["byte_count"] for row in manifest["artifact_inventory"]
    ) + len(canonical_json_bytes(manifest)) + 1
    if (
        type(durable) is not int or durable != expected_durable
        or not 0 <= durable <= B1_OBJECT_DURABLE_CAP_BYTES
    ):
        raise MetricsArtifactError("durable size exceeds the 512 MiB object cap")
    canonical_json_bytes(manifest)
    return manifest


def _publish_metrics_only_complete(
    *, staging: Path, final_path: Path, manifest: Mapping[str, Any],
    allowed_root: Path, allow_test_only: bool = False,
    _transaction_witness: object = None,
) -> Path:
    """Create-only publish a fully materialized metrics bundle atomically."""

    root = ensure_confined(Path(staging), Path(allowed_root))
    final = ensure_confined(Path(final_path), Path(allowed_root))
    if final.exists():
        raise FileExistsError(f"create-only metrics final root exists: {final}")
    if (
        not root.is_dir() or root.parent != final.parent
        or ".partial-" not in root.name
    ):
        raise MetricsArtifactError("metrics staging must be an existing private sibling")
    if not allow_test_only:
        witness = _require_transaction_witness(
            _transaction_witness,
            identity=manifest.get("source_identity") if isinstance(manifest, Mapping) else None,
            require_reread=True,
        )
        if witness.artifact_inventory_sha256 != _digest(
            canonical_json_bytes(manifest.get("artifact_inventory"))
        ):
            raise MetricsArtifactError("formal publish inventory differs from transaction reread")
    validated = validate_metrics_only_manifest(
        manifest, root=root, allow_test_only=allow_test_only
    )
    size = validate_prospective_output_cap(
        artifact_inventory=validated["artifact_inventory"], manifest=validated
    )
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError("create-only metrics manifest exists")
    payload = canonical_json_bytes(validated) + b"\n"
    if len(payload) != size["manifest_bytes"]:
        raise MetricsArtifactError("prospective manifest bytes changed before publication")
    with manifest_path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    for path in root.rglob("*"):
        if path.is_file() and path != manifest_path:
            with path.open("r+b") as stream:
                os.fsync(stream.fileno())
    actual_total = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    if actual_total != size["total_bytes"] or actual_total > B1_OBJECT_DURABLE_CAP_BYTES:
        raise MetricsArtifactError("actual durable bytes differ from prospective cap census")
    _fsync_directory(root)
    if final.exists():
        raise FileExistsError(f"create-only metrics final root appeared: {final}")
    os.rename(root, final)
    _fsync_directory(final.parent)
    return final


def publish_metrics_only_complete(
    *, staging: Path, final_path: Path, manifest: Mapping[str, Any],
    allowed_root: Path, allow_test_only: bool = False,
) -> Path:
    """Public TEST_ONLY publisher; formal publication has one production entry point."""

    if not allow_test_only:
        raise MetricsArtifactError(
            "formal publication is available only through assemble_and_publish_b1_metrics"
        )
    return _publish_metrics_only_complete(
        staging=staging, final_path=final_path, manifest=manifest,
        allowed_root=allowed_root, allow_test_only=True,
        _transaction_witness=None,
    )


__all__ = [
    "AUC_METADATA_FIELDS", "B1_METRICS_SCHEMA", "B1_METRICS_TEST_SCHEMA",
    "DIAGNOSTIC_METADATA_FIELDS", "DIAGNOSTIC_NAMES", "FORMAL_ANALYSIS_BOUND",
    "LITERAL_NULL_DERIVED_FIELDS", "MetricsArtifactError", "PARALLEL_MODULE_PROTOCOL",
    "READINESS_DISPOSITION", "TABLE_KEY_FIELDS", "build_metrics_only_manifest",
    "canonicalize_metrics_table_order",
    "build_complete_artifact_inventory",
    "build_prospective_artifact_inventory", "PreparedMetricsTables",
    "prepare_metrics_only_tables",
    "publish_metrics_only_complete", "validate_prospective_output_cap",
    "conservative_formal_size_projection", "FORMAL_TABLE_ROW_COUNTS",
    "FORMAL_SUPPORT_TOTALS", "validate_formal_table_coverage",
    "FORMAL_PROJECTION_MAX_ROW_COUNTS",
    "validate_invocation_table_coverage",
    "validate_support_aggregate",
    "materialize_metrics_only_tables", "require_parallel_module_protocols",
    "validate_metrics_only_manifest", "build_b0_nonpolarity_leaf_index",
]
