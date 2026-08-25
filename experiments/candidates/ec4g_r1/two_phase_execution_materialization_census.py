"""EC4G-A4 immutable two-phase execution-materialization census.

Phase 1 derives the two declared action maps and ``Gamma`` only from the
authenticated C0 contract and C1 bindings, calls/compiles in the frozen
cell-major order, and seals exactly six rows.  Phase 2 is deliberately pure:
it reopens only the sealed snapshot/manifest bytes, performs all three
canonical-field comparisons, and computes ``D_RER3`` only when every witness
is complete.

Prediction fields in C0 are metadata.  No function in this module reads them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
from typing import Callable, Mapping, Sequence


C0_COMMIT = "c0beef960f5f731f0c994ecd2298a1e889210c7b"
C0_BLOB_OID = "6d37b33c933ee16f89186a507e67e1080b674ca0"
C0_SHA256 = "0d0c9b6f24ae2bb96fc0a3f542c737557f1cd66be1edbdb72d809dfce9bb0183"
C1_COMMIT = "ba9eae5cfc21c014f210e061561fe7b8f47f5592"
C1_SHA256 = "495702d04188a929e62e1e8d178bde84ed156dc83beab10106c67e612a50baef"
CONTRACT_PATH = "docs/research/candidates/ec4g_r1/EC4G_RER3_COMPLETE_CONTRACT_V1.json"
BINDING_PATH = "docs/research/candidates/ec4g_r1/EC4G_RER3_BINDING_RECORD_V1.json"
SOURCE_PATH = "experiments/candidates/ec4g_r1/two_phase_execution_materialization_census.py"
RUNNER_PATH = "scripts/run_ec4g_a4_two_phase_execution_materialization_census.py"
TREATMENT_ID = "EC4G-A4-TWO-PHASE-EXECUTION-MATERIALIZATION-CENSUS"
DESIGN_ID = "DESIGN-2026-08-10-EC4G-A4-TWO-PHASE-EXECUTION-MATERIALIZATION-CENSUS-V1"
CANDIDATE_VERSION = "CAND-VAP-EC4G-R1@rer3-prospective-complete-v8"
CONTRACT_ID = "EC4G-RER3-CONTRACT@1.0.0"
SERIALIZATION_ID = "ec4g-rer3-cjson-v1"

CELL_ORDER = ("k_join", "k_leave", "k_rejoin")
MAP_ORDER = ("M_E", "M_D")
PAIR_ORDER = ("join", "leave", "rejoin")
PAIR_CELLS = dict(zip(PAIR_ORDER, CELL_ORDER, strict=True))
MASSES = {"k_join": "0.50", "k_leave": "0.25", "k_rejoin": "0.25"}
COMPARED_FIELDS = (
    "cell",
    "phase_transitions",
    "primitive_actions",
    "receipt_branches",
    "envelope_and_body_literals",
    "probe_budget_changes",
    "cost_and_reward_rules",
    "post_mask",
    "memory_rule",
)
EXCLUDED_FIELDS = ("map_identity", "symbolic_gate_label")
ROW_SCHEMA = (
    "ordinal",
    "cell",
    "map_identity",
    "canonical_object",
    "object_sha256",
    "construction_receipt",
)
ENTRY_POINTS = (
    f"{SOURCE_PATH}::map_ec4g",
    f"{SOURCE_PATH}::map_direct_tau",
    f"{SOURCE_PATH}::compile_gamma",
    f"{SOURCE_PATH}::run_two_phase_census",
)
ORDERED_BRANCHES = (
    "A4_INPUT_OR_DESIGN_FREEZE_INVALID",
    "A4_FORBIDDEN_INFORMATION_FLOW_OR_SELF_REFERENCE",
    "A4_MATERIALIZATION_INCOMPLETE_OR_AMBIGUOUS",
    "A4_PHASE_BARRIER_OR_POST_SEAL_CHANGE_INVALID",
    "A4_PAIRED_CENSUS_INCOMPLETE_OR_NONCANONICAL",
    "A4_COMPLETE_TWO_PHASE_EXECUTION_CENSUS",
)
HARD_CAPS = {
    "registered_treatments": 1,
    "design_freezes": 1,
    "materialization_snapshots": 1,
    "complete_map_calls": 6,
    "complete_program_compilations": 6,
    "complete_execution_objects": 6,
    "complete_program_comparisons": 3,
    "complete_pair_witnesses": 3,
    "complete_D_aggregations": 1,
    "sha256_digests": 10,
    "prediction_field_uses": 0,
    "post_seal_writes_or_imports": 0,
    "human_decisions_between_phases": 0,
    "environment_policy_learning_training_optimizer_evaluation_model_fit_or_stochastic_activity": 0,
    "retry_rescue_rescan_repair_or_substitution": 0,
}

ROLE_SPECS = (
    (0, "objective_contract", "ec4g.rer3.v1.objective", "/objective_contract"),
    (1, "cell_registry_K", "ec4g.rer3.v1.K", "/cell_registry_K"),
    (2, "receipt_registry_R_k", "ec4g.rer3.v1.R", "/receipt_registry_R_k"),
    (3, "seven_arm_mean_and_covariance", "ec4g.rer3.v1.moments", "/seven_arm_mean_and_covariance"),
    (4, "cost_object", "ec4g.rer3.v1.cost", "/cost_object"),
    (5, "decision_parameters", "ec4g.rer3.v1.theta", "/decision_parameters"),
    (6, "total_EC4G_action_map_M_E", "ec4g.rer3.v1.M_E", "/total_EC4G_action_map_M_E"),
    (7, "total_Direct_tau_action_map_M_D", "ec4g.rer3.v1.M_D", "/total_Direct_tau_action_map_M_D"),
    (8, "fallback_program_F", "ec4g.rer3.v1.F", "/fallback_program_F"),
    (9, "donor_operator_J", "ec4g.rer3.v1.J", "/donor_operator_J"),
    (10, "canonicalizer_equality_Gamma", "ec4g.rer3.v1.Gamma", "/canonicalizer_equality_Gamma"),
    (11, "support_predicate_s", "ec4g.rer3.v1.s", "/support_predicate_s"),
    (12, "deployed_measure_m", "ec4g.rer3.v1.m", "/deployed_measure_m"),
    (13, "cross_cutting_freeze_manifest", "ec4g.rer3.v1.freeze", "/cross_cutting_freeze_manifest"),
)

_MAP_RULES = {
    "total_EC4G_action_map_M_E": (
        "if not s(k), return A",
        "else if L_T > max(0,U_F)+2 and L_C > 2 and L_V > 2, return P",
        "else if U_T <= 0 and U_F <= 0, return N",
        "else return A",
    ),
    "total_Direct_tau_action_map_M_D": (
        "if not s(k), return A",
        "else if L_T > max(0,U_F)+2, return P",
        "else if U_T <= 0 and U_F <= 0, return N",
        "else return A",
    ),
}

_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class CensusBranch(str, Enum):
    INPUT_OR_DESIGN_FREEZE_INVALID = ORDERED_BRANCHES[0]
    FORBIDDEN_INFORMATION_FLOW_OR_SELF_REFERENCE = ORDERED_BRANCHES[1]
    MATERIALIZATION_INCOMPLETE_OR_AMBIGUOUS = ORDERED_BRANCHES[2]
    PHASE_BARRIER_OR_POST_SEAL_CHANGE_INVALID = ORDERED_BRANCHES[3]
    PAIRED_CENSUS_INCOMPLETE_OR_NONCANONICAL = ORDERED_BRANCHES[4]
    COMPLETE_TWO_PHASE_EXECUTION_CENSUS = ORDERED_BRANCHES[5]


class StrictJsonError(ValueError):
    """Input bytes violate the frozen JSON boundary."""


class MaterializationError(RuntimeError):
    """One of the six frozen Phase-1 rows could not be materialized."""


@dataclass(frozen=True)
class AuthenticatedInputs:
    c0_bytes: bytes
    c1_bytes: bytes


@dataclass(frozen=True)
class DesignFreeze:
    source_revision: str
    source_path: str = SOURCE_PATH
    runner_path: str = RUNNER_PATH
    entry_points: tuple[str, ...] = ENTRY_POINTS
    row_schema: tuple[str, ...] = ROW_SCHEMA
    cell_order: tuple[str, ...] = CELL_ORDER
    map_order: tuple[str, ...] = MAP_ORDER
    pair_order: tuple[str, ...] = PAIR_ORDER
    compared_fields: tuple[str, ...] = COMPARED_FIELDS
    excluded_fields: tuple[str, ...] = EXCLUDED_FIELDS
    masses: Mapping[str, str] = field(default_factory=lambda: dict(MASSES))
    ordered_branches: tuple[str, ...] = ORDERED_BRANCHES
    hard_caps: Mapping[str, int] = field(default_factory=lambda: dict(HARD_CAPS))

    def payload(self) -> dict[str, object]:
        return {
            "source_revision": self.source_revision,
            "source_path": self.source_path,
            "runner_path": self.runner_path,
            "entry_points": list(self.entry_points),
            "row_schema": list(self.row_schema),
            "cell_order": list(self.cell_order),
            "map_order": list(self.map_order),
            "pair_order": list(self.pair_order),
            "canonical_equality": {
                "compared_fields": list(self.compared_fields),
                "excluded_fields": list(self.excluded_fields),
                "rule": "canonical compared-field bytes must be exactly equal; hashes are audit evidence only",
            },
            "D": {
                "formula": "0.50*I[join differs]+0.25*I[leave differs]+0.25*I[rejoin differs]",
                "masses": dict(self.masses),
            },
            "ordered_branches": list(self.ordered_branches),
            "hard_caps": dict(self.hard_caps),
        }


@dataclass(frozen=True)
class ExecutionComponents:
    map_E: Callable[[Mapping[str, object], str], str]
    map_D: Callable[[Mapping[str, object], str], str]
    compiler: Callable[[Mapping[str, object], str, str, str], Mapping[str, object]]


@dataclass(frozen=True)
class Phase1Seal:
    artifact_root: Path
    snapshot_path: Path
    manifest_path: Path
    snapshot_sha256: str
    manifest_sha256: str
    snapshot_bytes: bytes
    manifest_bytes: bytes
    rows: tuple[Mapping[str, object], ...]
    writers_closed: bool
    sha256_identities: tuple[str, ...]
    sealed_files: tuple[tuple[Path, bytes], ...]


@dataclass(frozen=True)
class PairWitness:
    pair: str
    cell: str
    left_ordinal: int
    right_ordinal: int
    status: str
    exact_equal: bool | None
    compared_fields: tuple[str, ...]
    excluded_fields: tuple[str, ...]
    detail: str | None = None

    def payload(self) -> dict[str, object]:
        return {
            "pair": self.pair,
            "cell": self.cell,
            "left_ordinal": self.left_ordinal,
            "right_ordinal": self.right_ordinal,
            "status": self.status,
            "exact_equal": self.exact_equal,
            "compared_fields": list(self.compared_fields),
            "excluded_fields": list(self.excluded_fields),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class CensusResult:
    terminal_branch: CensusBranch
    run_id: str
    source_revision: str
    first_failure: Mapping[str, object] | None
    design_freeze: DesignFreeze | None
    activity_counts: Mapping[str, int]
    partial_rows: tuple[Mapping[str, object], ...] = ()
    seal: Phase1Seal | None = None
    pair_witnesses: tuple[PairWitness, ...] = ()
    equality_vector: Mapping[str, bool] | None = None
    d_fraction: Fraction | None = None
    d_decimal: Decimal | None = None
    seal_evidence: Mapping[str, object] | None = None

    def payload(self) -> dict[str, object]:
        seal_payload = dict(self.seal_evidence) if self.seal_evidence is not None else None
        if seal_payload is None and self.seal is not None:
            seal_payload = {
                "artifact_root": str(self.seal.artifact_root),
                "status": "invalid_or_not_independently_validated",
            }
        return {
            "schema_version": 1,
            "document_kind": "ec4g_a4_two_phase_execution_materialization_census_result",
            "treatment_id": TREATMENT_ID,
            "design_id": DESIGN_ID,
            "candidate_version": CANDIDATE_VERSION,
            "run_id": self.run_id,
            "result_id": f"ec4g-a4-{self.run_id}",
            "terminal_branch": self.terminal_branch.value,
            "first_failure": dict(self.first_failure) if self.first_failure is not None else None,
            "source_identities": {
                "c0_commit": C0_COMMIT,
                "c0_blob_oid": C0_BLOB_OID,
                "c0_sha256": C0_SHA256,
                "c1_commit": C1_COMMIT,
                "c1_sha256": C1_SHA256,
                "implementation_source_revision": self.source_revision,
                "result_revision": None,
                "result_revision_status": "assigned only after one-shot publication",
            },
            "design_freeze": self.design_freeze.payload() if self.design_freeze is not None else None,
            "activity_counts": dict(self.activity_counts),
            "partial_rows": [dict(row) for row in self.partial_rows],
            "phase_1_seal": seal_payload,
            "pair_witnesses": [witness.payload() for witness in self.pair_witnesses],
            "equality_vector": dict(self.equality_vector) if self.equality_vector is not None else None,
            "D_RER3": (
                {
                    "fraction": _fraction_text(self.d_fraction),
                    "decimal": format(self.d_decimal, "f"),
                    "meaning": "configured-population structural discordance only",
                }
                if self.d_fraction is not None and self.d_decimal is not None
                else None
            ),
            "operator_receipt": {"owner": "code_project_manager", "status": "not_invoked_by_source"},
            "execution_readiness": {"owner": "code_project_manager", "status": "pending_registered_execution_readiness"},
            "technical_acceptance": {"owner": "code_project_manager", "status": "pending_code_project_manager_acceptance"},
            "nonclaims": (
                "No A2 repair, natural prevalence, causal value, reward or return superiority, learning, "
                "B, C, formal compute, Pro, promotion, retirement, or automatic successor."
            ),
        }

    def to_bytes(self) -> bytes:
        return canonical_json_bytes(self.payload())


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _reject_constant(value: str) -> object:
    raise StrictJsonError(f"nonfinite JSON number forbidden: {value}")


def _reject_float(value: str) -> object:
    raise StrictJsonError(f"bare noninteger JSON number forbidden: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise StrictJsonError(f"duplicate JSON key forbidden: {key}")
        result[key] = value
    return result


def parse_strict_json(content: bytes, *, canonical_plus_lf: bool = False) -> object:
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise StrictJsonError(f"not strict UTF-8: {exc}") from exc
    if text.startswith("\ufeff"):
        raise StrictJsonError("UTF-8 BOM forbidden")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except (json.JSONDecodeError, StrictJsonError) as exc:
        raise StrictJsonError(str(exc)) from exc
    if canonical_plus_lf and content != canonical_json_bytes(value) + b"\n":
        raise StrictJsonError("bytes are not canonical JSON plus one LF")
    return value


def authenticate_immutable_inputs(c0_bytes: bytes, c1_bytes: bytes) -> AuthenticatedInputs:
    """Authenticate the exact accepted C0/C1 blobs and their frozen bindings.

    These two whole-blob authentication digests are the first two of the ten
    SHA-256 identities on a complete treatment.  The accepted C1 was already
    audited against every C0 subtree; the checks below additionally enforce its
    role/pointer/source binding shape without recomputing fourteen extra hashes.
    """

    c0 = bytes(c0_bytes)
    c1 = bytes(c1_bytes)
    if hashlib.sha256(c0).hexdigest() != C0_SHA256:
        raise ValueError("C0 SHA-256 differs from the accepted immutable contract")
    if hashlib.sha256(c1).hexdigest() != C1_SHA256:
        raise ValueError("C1 SHA-256 differs from the accepted immutable binding record")
    contract = _require_mapping(parse_strict_json(c0), "C0 contract")
    binding = _require_mapping(parse_strict_json(c1, canonical_plus_lf=True), "C1 binding record")
    if contract.get("contract_id") != CONTRACT_ID or contract.get("version_id") != CANDIDATE_VERSION:
        raise ValueError("C0 identity differs from the accepted contract")
    if binding.get("contract_id") != CONTRACT_ID or binding.get("version_id") != CANDIDATE_VERSION:
        raise ValueError("C1 identity differs from the accepted contract")
    source = binding.get("contract_source")
    if source != {"blob_oid": C0_BLOB_OID, "commit": C0_COMMIT, "path": CONTRACT_PATH, "sha256": C0_SHA256}:
        raise ValueError("C1 contract source does not bind exact C0")
    bindings = binding.get("bindings")
    if not isinstance(bindings, list) or len(bindings) != len(ROLE_SPECS):
        raise ValueError("C1 must contain exactly fourteen bindings")
    for expected, row in zip(ROLE_SPECS, bindings, strict=True):
        ordinal, role, object_id, pointer = expected
        row = _require_mapping(row, f"C1 binding {ordinal}")
        required = {
            "ordinal": ordinal,
            "role": role,
            "object_id": object_id,
            "json_pointer": pointer,
            "source_commit": C0_COMMIT,
            "source_path": CONTRACT_PATH,
            "source_blob_oid": C0_BLOB_OID,
            "source_blob_sha256": C0_SHA256,
            "total": True,
        }
        if any(row.get(key) != value for key, value in required.items()):
            raise ValueError(f"C1 binding differs at role {role}")
        if not _DIGEST_RE.fullmatch(str(row.get("subtree_sha256", ""))):
            raise ValueError(f"C1 subtree digest invalid at role {role}")
    if _contains_scalar(binding, C1_COMMIT):
        raise PermissionError("C1 binding record self-references its containing commit")
    return AuthenticatedInputs(c0, c1)


def freeze_design(source_revision: str) -> DesignFreeze:
    if not _REVISION_RE.fullmatch(source_revision):
        raise ValueError("implementation source revision must be lowercase 40-hex")
    freeze = DesignFreeze(source_revision=source_revision)
    if freeze.entry_points != ENTRY_POINTS or freeze.row_schema != ROW_SCHEMA:
        raise ValueError("implementation entry points or six-row schema drifted")
    if freeze.cell_order != CELL_ORDER or freeze.map_order != MAP_ORDER or freeze.pair_order != PAIR_ORDER:
        raise ValueError("frozen execution order drifted")
    if freeze.compared_fields != COMPARED_FIELDS or freeze.excluded_fields != EXCLUDED_FIELDS:
        raise ValueError("canonical equality projection drifted")
    if freeze.ordered_branches != ORDERED_BRANCHES or dict(freeze.hard_caps) != HARD_CAPS:
        raise ValueError("branch precedence or hard caps drifted")
    if dict(freeze.masses) != MASSES:
        raise ValueError("D aggregation masses drifted")
    return freeze


def map_ec4g(contract: Mapping[str, object], cell: str) -> str:
    """Execute the C0-declared total EC4G map without prediction metadata."""

    _validate_cell(cell)
    _validate_map_declaration(contract, "total_EC4G_action_map_M_E")
    support = _support_value(contract, cell)
    intervals, parameters = _decision_literals(contract, cell)
    if not support:
        return "A"
    lower_t, upper_t = intervals["T"]
    lower_c, _upper_c = intervals["C"]
    lower_v, _upper_v = intervals["V"]
    _lower_f, upper_f = parameters["fallback_interval"]
    if (
        lower_t > max(Decimal(0), upper_f) + parameters["delta_T"]
        and lower_c > parameters["delta_C"]
        and lower_v > parameters["delta_V"]
    ):
        return "P"
    if upper_t <= 0 and upper_f <= 0:
        return "N"
    return "A"


def map_direct_tau(contract: Mapping[str, object], cell: str) -> str:
    """Execute the matched C0 Direct-tau map without prediction metadata."""

    _validate_cell(cell)
    _validate_map_declaration(contract, "total_Direct_tau_action_map_M_D")
    support = _support_value(contract, cell)
    intervals, parameters = _decision_literals(contract, cell)
    if not support:
        return "A"
    lower_t, upper_t = intervals["T"]
    _lower_f, upper_f = parameters["fallback_interval"]
    if lower_t > max(Decimal(0), upper_f) + parameters["delta_T"]:
        return "P"
    if upper_t <= 0 and upper_f <= 0:
        return "N"
    return "A"


def compile_gamma(
    contract: Mapping[str, object], cell: str, action: str, map_identity: str
) -> Mapping[str, object]:
    """Compile one complete C0-declared canonical execution object."""

    _validate_cell(cell)
    if action not in ("P", "N", "A") or map_identity not in MAP_ORDER:
        raise MaterializationError("Gamma received an action or map outside the frozen domain")
    gamma = _require_mapping(contract.get("canonicalizer_equality_Gamma"), "Gamma")
    if tuple(gamma.get("canonical_fields", ())) != COMPARED_FIELDS:
        raise MaterializationError("Gamma canonical field declaration differs from the frozen projection")
    if tuple(gamma.get("excluded_fields", ())) != EXCLUDED_FIELDS:
        raise MaterializationError("Gamma exclusions differ from the frozen projection")
    expected_gamma = {
        "P_transition": "event,budget=1 to receipt,budget=0 via native_safe_probe; exact RV/RB/RS selects named continuation; malformed/late/missing selects F(k,1); then terminal",
        "N_transition": "no_probe then baseline_continue then terminal",
        "A_transition": "F(k,0) then terminal",
        "failure_rule": "Second probe, wrong-phase action or unsafe primitive fails closed to the appropriate F branch.",
        "equality": "exact canonical-object equality; hashes are audit evidence only",
    }
    if any(gamma.get(key) != value for key, value in expected_gamma.items()):
        raise MaterializationError("Gamma callable/equality semantics cannot be derived exactly from C0")
    cells = _cell_rows(contract)
    cell_row = cells[cell]
    receipt = _require_mapping(contract.get("receipt_registry_R_k"), "receipt registry")
    fallback = _require_mapping(contract.get("fallback_program_F"), "fallback F")
    cost = _require_mapping(contract.get("cost_object"), "cost object")
    memory_rule = _require_mapping(contract.get("cell_registry_K"), "cell registry").get("memory_rule")
    own_bodies = _require_mapping(receipt.get("own_body_hex"), "own receipt bodies")
    body = own_bodies.get(cell)
    envelope = receipt.get("envelope_bytes_hex")
    if not isinstance(body, str) or not isinstance(envelope, str):
        raise MaterializationError("receipt envelope/body literals are incomplete")

    if action == "P":
        arm_semantics = _require_mapping(receipt.get("arm_semantics"), "receipt arm semantics")
        blind_rule = arm_semantics.get("RB")
        if not isinstance(blind_rule, str) or not blind_rule.endswith(" plus 00000000"):
            raise MaterializationError("RB blind-body literal cannot be derived from C0")
        donor = _require_mapping(contract.get("donor_operator_J"), "donor operator J")
        donor_mapping = _require_mapping(donor.get("mapping"), "donor mapping")
        donor_pool = _require_mapping(donor.get("pool"), "donor pool")
        donor_id = donor_mapping.get(cell)
        donor_row = _require_mapping(donor_pool.get(donor_id), "donor row")
        donor_body = donor_row.get("body_hex")
        if not isinstance(donor_body, str):
            raise MaterializationError("RS donor-body literal cannot be derived from C0")
        phase_transitions = ["event:budget=1->receipt:budget=0", "receipt:budget=0->terminal"]
        primitive_actions = [
            "native_safe_probe",
            "receipt_continue_valid",
            "receipt_continue_blind",
            "receipt_continue_swap",
            "safe_hold_after_probe",
        ]
        receipt_branches = {
            "RV": "receipt_continue_valid",
            "RB": "receipt_continue_blind",
            "RS": "receipt_continue_swap",
            "MALFORMED": "F(k,1):safe_hold_after_probe",
            "LATE": "F(k,1):safe_hold_after_probe",
            "MISSING": "F(k,1):safe_hold_after_probe",
        }
        envelope_and_body = {
            "envelope_id": receipt.get("envelope_id"),
            "envelope_bytes_hex": envelope,
            "body_length_bytes": receipt.get("body_length_bytes"),
            "body_hex_by_receipt": {"RV": body, "RB": "00000000", "RS": donor_body},
        }
        budget_changes = ["1->0", "0->0"]
        cost_reward = {
            "external_cost": "2",
            "subtract_exactly_once": cost.get("subtract_exactly_once"),
            "valid_receipts": "registered terminal gross-reward law",
            "failure": fallback.get("spent_1"),
        }
    elif action == "N":
        phase_transitions = ["event:budget=1->receipt:budget=1", "receipt:budget=1->terminal"]
        primitive_actions = ["no_probe", "baseline_continue"]
        receipt_branches = {"NONE": "baseline_continue"}
        envelope_and_body = {"envelope_id": None, "envelope_bytes_hex": None, "body_length_bytes": 0, "own_body_hex": None}
        budget_changes = ["1->1", "1->1"]
        cost_reward = {"external_cost": "0", "subtract_exactly_once": True, "terminal_law": "R0"}
    else:
        phase_transitions = ["event:budget=1->receipt:budget=1", "receipt:budget=1->terminal"]
        primitive_actions = ["no_probe", "safe_hold"]
        receipt_branches = {"F(k,0)": "safe_hold"}
        envelope_and_body = {"envelope_id": None, "envelope_bytes_hex": None, "body_length_bytes": 0, "own_body_hex": None}
        budget_changes = ["1->1"]
        cost_reward = {"external_cost": "0", "subtract_exactly_once": True, "fallback": fallback.get("spent_0")}

    compiled = {
        "cell": cell,
        "phase_transitions": phase_transitions,
        "primitive_actions": primitive_actions,
        "receipt_branches": receipt_branches,
        "envelope_and_body_literals": envelope_and_body,
        "probe_budget_changes": budget_changes,
        "cost_and_reward_rules": cost_reward,
        "post_mask": cell_row.get("active_post"),
        "memory_rule": memory_rule,
        "map_identity": map_identity,
        "symbolic_gate_label": action,
    }
    _canonical_projection(compiled)
    return compiled


DEFAULT_COMPONENTS = ExecutionComponents(map_ec4g, map_direct_tau, compile_gamma)


def materialize_and_seal_phase1(
    authenticated: AuthenticatedInputs,
    design: DesignFreeze,
    artifact_root: Path,
    *,
    components: ExecutionComponents = DEFAULT_COMPONENTS,
    activity: dict[str, int] | None = None,
) -> Phase1Seal:
    """Perform exactly six calls and six compilations, then close and seal."""

    contract = _require_mapping(parse_strict_json(authenticated.c0_bytes), "C0 contract")
    root = artifact_root.resolve(strict=False)
    root.mkdir(parents=False, exist_ok=False)
    rows: list[Mapping[str, object]] = []
    sealed_files: list[tuple[Path, bytes]] = []
    sha_identities = [f"C0:{C0_SHA256}", f"C1:{C1_SHA256}"]
    ordinal = 0
    for cell in design.cell_order:
        for map_identity in design.map_order:
            mapper = components.map_E if map_identity == "M_E" else components.map_D
            try:
                action = mapper(contract, cell)
            except Exception as exc:
                raise MaterializationError(
                    f"map failed at ordinal {ordinal}/{cell}/{map_identity}: {exc}"
                ) from exc
            if activity is not None:
                activity["complete_map_calls"] += 1
            try:
                compiled = dict(components.compiler(contract, cell, action, map_identity))
            except Exception as exc:
                raise MaterializationError(
                    f"compiler failed at ordinal {ordinal}/{cell}/{map_identity}: {exc}"
                ) from exc
            if activity is not None:
                activity["complete_program_compilations"] += 1
            projection = _canonical_projection(compiled)
            if set(compiled) != set(COMPARED_FIELDS + EXCLUDED_FIELDS):
                raise MaterializationError("compiled object has missing, default, or extra fields")
            object_bytes = canonical_json_bytes(compiled)
            object_digest = hashlib.sha256(object_bytes).hexdigest()
            if activity is not None:
                activity["sha256_digests"] += 1
            sha_identities.append(f"object:{ordinal}:{object_digest}")
            receipt = {
                "ordinal": ordinal,
                "cell": cell,
                "map_identity": map_identity,
                "map_entry_point": design.entry_points[0 if map_identity == "M_E" else 1],
                "compiler_entry_point": design.entry_points[2],
                "c0": {"commit": C0_COMMIT, "path": CONTRACT_PATH, "blob_oid": C0_BLOB_OID, "sha256": C0_SHA256},
                "c1": {"commit": C1_COMMIT, "path": BINDING_PATH, "sha256": C1_SHA256},
                "bound_roles": [
                    "cell_registry_K",
                    "receipt_registry_R_k",
                    "decision_parameters",
                    "total_EC4G_action_map_M_E" if map_identity == "M_E" else "total_Direct_tau_action_map_M_D",
                    "fallback_program_F",
                    "canonicalizer_equality_Gamma",
                    "support_predicate_s",
                ],
                "object_sha256": object_digest,
                "canonical_valid": canonical_json_bytes(projection) == canonical_json_bytes(projection),
            }
            row = {
                "ordinal": ordinal,
                "cell": cell,
                "map_identity": map_identity,
                "canonical_object": compiled,
                "object_sha256": object_digest,
                "construction_receipt": receipt,
            }
            if set(row) != set(ROW_SCHEMA):
                raise MaterializationError("six-row schema order/content drifted")
            object_path = root / f"{ordinal:02d}_{cell}_{map_identity}.object.json"
            receipt_path = root / f"{ordinal:02d}_{cell}_{map_identity}.receipt.json"
            object_file_bytes = object_bytes + b"\n"
            receipt_file_bytes = canonical_json_bytes(receipt) + b"\n"
            _write_new(object_path, object_file_bytes)
            _write_new(receipt_path, receipt_file_bytes)
            if object_path.read_bytes() != object_file_bytes or receipt_path.read_bytes() != receipt_file_bytes:
                raise MaterializationError("materialized object or receipt changed before the barrier")
            sealed_files.extend(((object_path, object_file_bytes), (receipt_path, receipt_file_bytes)))
            rows.append(row)
            if activity is not None:
                activity["complete_execution_objects"] += 1
            ordinal += 1

    _validate_complete_rows(rows, design)
    snapshot = {
        "schema_version": 1,
        "serialization_id": SERIALIZATION_ID,
        "source_revision": design.source_revision,
        "row_schema": list(design.row_schema),
        "rows": rows,
    }
    snapshot_bytes = canonical_json_bytes(snapshot) + b"\n"
    snapshot_digest = hashlib.sha256(snapshot_bytes).hexdigest()
    if activity is not None:
        activity["sha256_digests"] += 1
    sha_identities.append(f"snapshot:{snapshot_digest}")
    snapshot_path = root / f"snapshot-{snapshot_digest}.json"
    _write_new(snapshot_path, snapshot_bytes)
    manifest = {
        "schema_version": 1,
        "snapshot_file": snapshot_path.name,
        "snapshot_sha256": snapshot_digest,
        "row_count": 6,
        "row_order": [[cell, map_name] for cell in CELL_ORDER for map_name in MAP_ORDER],
        "row_object_sha256": [row["object_sha256"] for row in rows],
        "writers_closed": True,
        "write_once": True,
        "post_seal_imports_permitted": False,
    }
    manifest_bytes = canonical_json_bytes(manifest) + b"\n"
    manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
    if activity is not None:
        activity["sha256_digests"] += 1
    sha_identities.append(f"manifest:{manifest_digest}")
    manifest_path = root / f"manifest-{manifest_digest}.json"
    _write_new(manifest_path, manifest_bytes)
    if activity is not None:
        activity["materialization_snapshots"] += 1
    sealed_files.extend(((snapshot_path, snapshot_bytes), (manifest_path, manifest_bytes)))
    if len(sha_identities) != HARD_CAPS["sha256_digests"]:
        raise MaterializationError("complete seal did not produce exactly ten SHA-256 identities")
    return Phase1Seal(
        root,
        snapshot_path,
        manifest_path,
        snapshot_digest,
        manifest_digest,
        snapshot_bytes,
        manifest_bytes,
        tuple(rows),
        True,
        tuple(sha_identities),
        tuple(sealed_files),
    )


def census_sealed_phase2(seal: Phase1Seal, design: DesignFreeze) -> tuple[tuple[PairWitness, ...], Mapping[str, bool] | None, Fraction | None, Decimal | None, Mapping[str, object] | None]:
    """Reopen only sealed bytes, compare every pair, and aggregate only if complete.

    The function performs no imports, map/compiler calls, or filesystem writes.
    It recomputes all seal digests from reopened bytes before comparison.
    """

    try:
        rows = _reopen_and_validate_sealed_artifacts(seal.artifact_root, design)
    except OSError as exc:
        return (), None, None, None, _failure("SEALED_BYTES_UNREADABLE", str(exc))
    except (StrictJsonError, ValueError, MaterializationError) as exc:
        return (), None, None, None, _failure("SEALED_ARTIFACT_INTEGRITY_INVALID", str(exc))
    return _compare_validated_rows(rows, design)


def _compare_validated_rows(
    rows: Sequence[Mapping[str, object]],
    design: DesignFreeze,
) -> tuple[tuple[PairWitness, ...], Mapping[str, bool] | None, Fraction | None, Decimal | None, Mapping[str, object] | None]:
    """Compare a barrier-validated six-row population without early stop."""

    by_key = {(str(row["cell"]), str(row["map_identity"])): row for row in rows}
    witnesses: list[PairWitness] = []
    equality: dict[str, bool] = {}
    for pair in design.pair_order:  # Deliberately no early stop.
        cell = PAIR_CELLS[pair]
        left = by_key[(cell, "M_E")]
        right = by_key[(cell, "M_D")]
        left_ordinal = int(left["ordinal"])
        right_ordinal = int(right["ordinal"])
        try:
            left_projection = _canonical_projection(_require_mapping(left.get("canonical_object"), "left object"))
            right_projection = _canonical_projection(_require_mapping(right.get("canonical_object"), "right object"))
            equal = canonical_json_bytes(left_projection) == canonical_json_bytes(right_projection)
        except (ValueError, MaterializationError) as exc:
            witnesses.append(PairWitness(pair, cell, left_ordinal, right_ordinal, "NONCANONICAL", None, COMPARED_FIELDS, EXCLUDED_FIELDS, str(exc)))
            continue
        witnesses.append(PairWitness(pair, cell, left_ordinal, right_ordinal, "COMPLETE", equal, COMPARED_FIELDS, EXCLUDED_FIELDS))
        equality[pair] = equal
    if len(witnesses) != 3 or len(equality) != 3 or any(item.status != "COMPLETE" for item in witnesses):
        return tuple(witnesses), None, None, None, _failure("PAIR_WITNESS_INCOMPLETE_OR_NONCANONICAL", "all three comparisons ran but at least one witness was incomplete")
    d_fraction = sum(
        (Fraction(MASSES[PAIR_CELLS[pair]]) for pair in PAIR_ORDER if not equality[pair]),
        Fraction(0, 1),
    )
    d_decimal = sum(
        (Decimal(MASSES[PAIR_CELLS[pair]]) for pair in PAIR_ORDER if not equality[pair]),
        Decimal(0),
    )
    return tuple(witnesses), equality, d_fraction, d_decimal, None


def _reopen_and_validate_sealed_artifacts(
    artifact_root: Path,
    design: DesignFreeze,
) -> list[Mapping[str, object]]:
    """Independently authenticate the complete on-disk Phase-1 seal.

    No in-memory bytes, declared digest, filename, ``canonical_valid`` flag, or
    row object is used as an integrity oracle.  All identities are recomputed
    from the reopened files before any pair comparison.
    """

    root = artifact_root.resolve(strict=False)
    actual_paths = tuple(sorted(root.iterdir()))
    snapshot_paths = tuple(
        path
        for path in actual_paths
        if path.is_file() and re.fullmatch(r"snapshot-[0-9a-f]{64}\.json", path.name)
    )
    manifest_paths = tuple(
        path
        for path in actual_paths
        if path.is_file() and re.fullmatch(r"manifest-[0-9a-f]{64}\.json", path.name)
    )
    if any(not path.is_file() or path.is_symlink() for path in actual_paths):
        raise MaterializationError("sealed artifact set contains a directory, link, or non-file import")
    if len(snapshot_paths) != 1 or len(manifest_paths) != 1:
        raise MaterializationError("seal must contain exactly one content-addressed snapshot and manifest")
    snapshot_path = snapshot_paths[0]
    manifest_path = manifest_paths[0]
    row_paths: list[Path] = []
    for ordinal, (cell, map_identity) in enumerate(
        ((cell, map_name) for cell in design.cell_order for map_name in design.map_order)
    ):
        row_paths.extend(
            (
                root / f"{ordinal:02d}_{cell}_{map_identity}.object.json",
                root / f"{ordinal:02d}_{cell}_{map_identity}.receipt.json",
            )
        )
    expected_paths = tuple(sorted((*row_paths, snapshot_path, manifest_path)))
    if actual_paths != expected_paths:
        raise MaterializationError("sealed artifact file set contains a missing, duplicate, default, substitute, or import")

    snapshot_bytes = snapshot_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    snapshot_digest = hashlib.sha256(snapshot_bytes).hexdigest()
    manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
    if snapshot_path.name != f"snapshot-{snapshot_digest}.json":
        raise MaterializationError("snapshot content-addressed filename does not match recomputed SHA-256")
    if manifest_path.name != f"manifest-{manifest_digest}.json":
        raise MaterializationError("manifest content-addressed filename does not match recomputed SHA-256")

    snapshot = _require_mapping(parse_strict_json(snapshot_bytes, canonical_plus_lf=True), "sealed snapshot")
    manifest = _require_mapping(parse_strict_json(manifest_bytes, canonical_plus_lf=True), "sealed manifest")
    if set(snapshot) != {"schema_version", "serialization_id", "source_revision", "row_schema", "rows"}:
        raise MaterializationError("sealed snapshot schema differs from the frozen schema")
    if (
        snapshot.get("schema_version") != 1
        or snapshot.get("serialization_id") != SERIALIZATION_ID
        or snapshot.get("source_revision") != design.source_revision
        or snapshot.get("row_schema") != list(design.row_schema)
    ):
        raise MaterializationError("sealed snapshot header differs from the design freeze")
    rows_raw = snapshot.get("rows")
    if not isinstance(rows_raw, list):
        raise MaterializationError("sealed rows are not an array")
    rows = [_require_mapping(row, "sealed row") for row in rows_raw]
    _validate_complete_rows(rows, design)

    expected_manifest_keys = {
        "schema_version",
        "snapshot_file",
        "snapshot_sha256",
        "row_count",
        "row_order",
        "row_object_sha256",
        "writers_closed",
        "write_once",
        "post_seal_imports_permitted",
    }
    expected_row_order = [[cell, map_name] for cell in design.cell_order for map_name in design.map_order]
    if set(manifest) != expected_manifest_keys:
        raise MaterializationError("sealed manifest schema differs from the frozen schema")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("snapshot_file") != snapshot_path.name
        or manifest.get("snapshot_sha256") != snapshot_digest
        or manifest.get("row_count") != 6
        or manifest.get("row_order") != expected_row_order
        or manifest.get("writers_closed") is not True
        or manifest.get("write_once") is not True
        or manifest.get("post_seal_imports_permitted") is not False
    ):
        raise MaterializationError("manifest linkage/order/barrier flags differ from recomputed seal facts")

    manifest_digests = manifest.get("row_object_sha256")
    if not isinstance(manifest_digests, list) or len(manifest_digests) != 6:
        raise MaterializationError("manifest must bind exactly six row object digests")
    for ordinal, row in enumerate(rows):
        cell = str(row["cell"])
        map_identity = str(row["map_identity"])
        object_path = root / f"{ordinal:02d}_{cell}_{map_identity}.object.json"
        receipt_path = root / f"{ordinal:02d}_{cell}_{map_identity}.receipt.json"
        object_document = _require_mapping(
            parse_strict_json(object_path.read_bytes(), canonical_plus_lf=True),
            f"sealed object {ordinal}",
        )
        receipt_document = _require_mapping(
            parse_strict_json(receipt_path.read_bytes(), canonical_plus_lf=True),
            f"sealed receipt {ordinal}",
        )
        if object_document != row.get("canonical_object"):
            raise MaterializationError(f"sealed object file/row mismatch at ordinal {ordinal}")
        if receipt_document != row.get("construction_receipt"):
            raise MaterializationError(f"sealed receipt file/row mismatch at ordinal {ordinal}")
        object_digest = hashlib.sha256(canonical_json_bytes(object_document)).hexdigest()
        if (
            row.get("object_sha256") != object_digest
            or receipt_document.get("object_sha256") != object_digest
            or manifest_digests[ordinal] != object_digest
        ):
            raise MaterializationError(f"recomputed object digest linkage failed at ordinal {ordinal}")
        _validate_construction_receipt(receipt_document, design, ordinal, cell, map_identity)
    return rows


def _seal_evidence_from_disk(artifact_root: Path, design: DesignFreeze) -> dict[str, object]:
    """Build result-facing seal evidence exclusively from revalidated disk bytes."""

    rows = _reopen_and_validate_sealed_artifacts(artifact_root, design)
    root = artifact_root.resolve(strict=False)
    snapshot_path = next(path for path in root.iterdir() if re.fullmatch(r"snapshot-[0-9a-f]{64}\.json", path.name))
    manifest_path = next(path for path in root.iterdir() if re.fullmatch(r"manifest-[0-9a-f]{64}\.json", path.name))
    snapshot_digest = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
    manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    object_digests = [
        hashlib.sha256(canonical_json_bytes(_require_mapping(row["canonical_object"], "canonical object"))).hexdigest()
        for row in rows
    ]
    identities = [f"C0:{C0_SHA256}", f"C1:{C1_SHA256}"]
    identities.extend(f"object:{ordinal}:{digest}" for ordinal, digest in enumerate(object_digests))
    identities.extend((f"snapshot:{snapshot_digest}", f"manifest:{manifest_digest}"))
    if len(identities) != HARD_CAPS["sha256_digests"]:
        raise MaterializationError("independent result seal evidence did not contain ten SHA-256 identities")
    return {
        "artifact_root": str(root),
        "snapshot_path": str(snapshot_path),
        "snapshot_sha256": snapshot_digest,
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_digest,
        "writers_closed": True,
        "row_count": len(rows),
        "sha256_identities": identities,
        "status": "independently_recomputed_and_validated",
    }


def run_two_phase_census(
    c0_bytes: bytes,
    c1_bytes: bytes,
    *,
    artifact_root: Path,
    source_revision: str,
    run_id: str,
    components: ExecutionComponents = DEFAULT_COMPONENTS,
    information_flow_events: Sequence[Mapping[str, object]] = (),
    after_seal: Callable[[Phase1Seal], None] | None = None,
) -> CensusResult:
    """Run one treatment with the exact frozen six-branch precedence."""

    counts = _empty_counts()
    if not run_id.strip():
        return _result(CensusBranch.INPUT_OR_DESIGN_FREEZE_INVALID, run_id, source_revision, counts, _failure("EMPTY_RUN_ID", "run_id must be nonempty"))
    try:
        authenticated = authenticate_immutable_inputs(c0_bytes, c1_bytes)
        counts["sha256_digests"] = 2
        design = freeze_design(source_revision)
        counts["design_freezes"] = 1
        if artifact_root.resolve(strict=False).exists():
            raise ValueError("artifact root already exists; one-shot materialization refuses overwrite")
    except PermissionError as exc:
        return _result(CensusBranch.FORBIDDEN_INFORMATION_FLOW_OR_SELF_REFERENCE, run_id, source_revision, counts, _failure("SELF_REFERENCE", str(exc)))
    except (OSError, StrictJsonError, ValueError) as exc:
        return _result(CensusBranch.INPUT_OR_DESIGN_FREEZE_INVALID, run_id, source_revision, counts, _failure("INPUT_OR_DESIGN_INVALID", str(exc)))
    if information_flow_events:
        if information_flow_events[0].get("code") == "PREDICTION_FIELD_USE":
            counts["prediction_field_uses"] = 1
        return _result(
            CensusBranch.FORBIDDEN_INFORMATION_FLOW_OR_SELF_REFERENCE,
            run_id,
            source_revision,
            counts,
            dict(information_flow_events[0]),
            design=design,
        )

    seal: Phase1Seal | None = None
    try:
        seal = materialize_and_seal_phase1(
            authenticated,
            design,
            artifact_root,
            components=components,
            activity=counts,
        )
    except (OSError, StrictJsonError, ValueError, MaterializationError) as exc:
        partial = _read_partial_rows(artifact_root)
        return _result(
            CensusBranch.MATERIALIZATION_INCOMPLETE_OR_AMBIGUOUS,
            run_id,
            source_revision,
            counts,
            _failure("PHASE1_MATERIALIZATION_FAILED", str(exc)),
            design=design,
            partial=partial,
        )
    if after_seal is not None:
        after_seal(seal)

    witnesses, equality, d_fraction, d_decimal, failure = census_sealed_phase2(seal, design)
    if failure is not None and failure.get("code") in {
        "SEALED_BYTES_UNREADABLE",
        "SEALED_ARTIFACT_INTEGRITY_INVALID",
    }:
        if failure.get("code") == "SEALED_ARTIFACT_INTEGRITY_INVALID":
            counts["post_seal_writes_or_imports"] = 1
        return _result(
            CensusBranch.PHASE_BARRIER_OR_POST_SEAL_CHANGE_INVALID,
            run_id,
            source_revision,
            counts,
            failure,
            design=design,
            seal=seal,
        )
    counts["complete_program_comparisons"] = 3
    counts["complete_pair_witnesses"] = sum(item.status == "COMPLETE" for item in witnesses)
    seal_evidence = _seal_evidence_from_disk(seal.artifact_root, design)
    if failure is not None:
        return _result(
            CensusBranch.PAIRED_CENSUS_INCOMPLETE_OR_NONCANONICAL,
            run_id,
            source_revision,
            counts,
            failure,
            design=design,
            seal=seal,
            witnesses=witnesses,
            seal_evidence=seal_evidence,
        )
    counts["complete_D_aggregations"] = 1
    return CensusResult(
        CensusBranch.COMPLETE_TWO_PHASE_EXECUTION_CENSUS,
        run_id,
        source_revision,
        None,
        design,
        counts,
        seal=seal,
        pair_witnesses=witnesses,
        equality_vector=equality,
        d_fraction=d_fraction,
        d_decimal=d_decimal,
        seal_evidence=seal_evidence,
    )


def _decision_literals(contract: Mapping[str, object], cell: str) -> tuple[dict[str, tuple[Decimal, Decimal]], dict[str, object]]:
    parameters = _require_mapping(contract.get("decision_parameters"), "decision parameters")
    intervals_by_cell = _require_mapping(parameters.get("expected_intervals"), "expected intervals")
    raw = _require_mapping(intervals_by_cell.get(cell), f"intervals for {cell}")
    intervals: dict[str, tuple[Decimal, Decimal]] = {}
    for name in ("T", "C", "V"):
        bounds = raw.get(name)
        if not isinstance(bounds, list) or len(bounds) != 2:
            raise MaterializationError(f"{cell}/{name} interval is incomplete")
        intervals[name] = (_decimal(bounds[0]), _decimal(bounds[1]))
    fallback = parameters.get("fallback_interval")
    if not isinstance(fallback, list) or len(fallback) != 2:
        raise MaterializationError("fallback interval is incomplete")
    derived: dict[str, object] = {
        "delta_T": _decimal(parameters.get("delta_T")),
        "delta_C": _decimal(parameters.get("delta_C")),
        "delta_V": _decimal(parameters.get("delta_V")),
        "fallback_interval": (_decimal(fallback[0]), _decimal(fallback[1])),
    }
    return intervals, derived


def _validate_map_declaration(contract: Mapping[str, object], role: str) -> None:
    declaration = _require_mapping(contract.get(role), role)
    if tuple(declaration.get("ordered_rule", ())) != _MAP_RULES[role]:
        raise MaterializationError(f"callable semantics for {role} cannot be derived exactly from C0")


def _support_value(contract: Mapping[str, object], cell: str) -> bool:
    support = _require_mapping(contract.get("support_predicate_s"), "support predicate")
    if support.get("map_independent") is not True:
        raise MaterializationError("support must be map-independent")
    values = _require_mapping(support.get("values"), "support values")
    value = values.get(cell)
    if not isinstance(value, bool):
        raise MaterializationError(f"support for {cell} is not total Boolean")
    return value


def _cell_rows(contract: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    registry = _require_mapping(contract.get("cell_registry_K"), "cell registry")
    cells = registry.get("cells")
    if not isinstance(cells, list) or len(cells) != 3:
        raise MaterializationError("cell registry must contain exactly three rows")
    result: dict[str, Mapping[str, object]] = {}
    for raw in cells:
        row = _require_mapping(raw, "cell row")
        name = row.get("cell")
        if not isinstance(name, str) or name in result:
            raise MaterializationError("cell registry contains missing or duplicate identity")
        result[name] = row
    if tuple(result) != CELL_ORDER:
        raise MaterializationError("cell registry order differs from the frozen order")
    return result


def _canonical_projection(compiled: Mapping[str, object]) -> dict[str, object]:
    missing = [field_name for field_name in COMPARED_FIELDS if field_name not in compiled]
    if missing:
        raise MaterializationError(f"canonical object missing compared fields: {missing}")
    if any(compiled.get(field_name) is None for field_name in ("cell", "phase_transitions", "primitive_actions", "receipt_branches", "probe_budget_changes", "cost_and_reward_rules", "post_mask", "memory_rule")):
        raise MaterializationError("canonical object contains a default/null required field")
    projection = {field_name: compiled[field_name] for field_name in COMPARED_FIELDS}
    canonical_json_bytes(projection)
    return projection


def _validate_complete_rows(
    rows: Sequence[Mapping[str, object]],
    design: DesignFreeze,
    *,
    validate_objects: bool = True,
) -> None:
    if len(rows) != 6:
        raise MaterializationError("barrier requires exactly six rows")
    expected = [(cell, map_name) for cell in design.cell_order for map_name in design.map_order]
    seen: set[tuple[str, str]] = set()
    for ordinal, (row, key) in enumerate(zip(rows, expected, strict=True)):
        if set(row) != set(ROW_SCHEMA):
            raise MaterializationError("row schema differs or contains a default/substitute field")
        actual = (str(row.get("cell")), str(row.get("map_identity")))
        if actual != key or actual in seen or row.get("ordinal") != ordinal:
            raise MaterializationError("row order/identity is missing, duplicate, imported, or substituted")
        seen.add(actual)
        digest = row.get("object_sha256")
        receipt = _require_mapping(row.get("construction_receipt"), "construction receipt")
        if not _DIGEST_RE.fullmatch(str(digest)) or receipt.get("object_sha256") != digest:
            raise MaterializationError("row object/receipt digest binding is incomplete")
        compiled = _require_mapping(row.get("canonical_object"), "canonical object")
        if compiled.get("map_identity") != actual[1] or compiled.get("cell") != actual[0]:
            raise MaterializationError("row contains an imported/substituted object")
        if validate_objects:
            if set(compiled) != set(COMPARED_FIELDS + EXCLUDED_FIELDS):
                raise MaterializationError(
                    "canonical object key set must equal compared fields plus exclusions exactly"
                )
            _canonical_projection(compiled)


def _validate_construction_receipt(
    receipt: Mapping[str, object],
    design: DesignFreeze,
    ordinal: int,
    cell: str,
    map_identity: str,
) -> None:
    expected_keys = {
        "ordinal",
        "cell",
        "map_identity",
        "map_entry_point",
        "compiler_entry_point",
        "c0",
        "c1",
        "bound_roles",
        "object_sha256",
        "canonical_valid",
    }
    map_role = (
        "total_EC4G_action_map_M_E"
        if map_identity == "M_E"
        else "total_Direct_tau_action_map_M_D"
    )
    expected_roles = [
        "cell_registry_K",
        "receipt_registry_R_k",
        "decision_parameters",
        map_role,
        "fallback_program_F",
        "canonicalizer_equality_Gamma",
        "support_predicate_s",
    ]
    if set(receipt) != expected_keys:
        raise MaterializationError(f"construction receipt schema differs at ordinal {ordinal}")
    if (
        receipt.get("ordinal") != ordinal
        or receipt.get("cell") != cell
        or receipt.get("map_identity") != map_identity
        or receipt.get("map_entry_point") != design.entry_points[0 if map_identity == "M_E" else 1]
        or receipt.get("compiler_entry_point") != design.entry_points[2]
        or receipt.get("bound_roles") != expected_roles
        or receipt.get("c0")
        != {"commit": C0_COMMIT, "path": CONTRACT_PATH, "blob_oid": C0_BLOB_OID, "sha256": C0_SHA256}
        or receipt.get("c1")
        != {"commit": C1_COMMIT, "path": BINDING_PATH, "sha256": C1_SHA256}
        or receipt.get("canonical_valid") is not True
    ):
        raise MaterializationError(f"construction receipt provenance differs at ordinal {ordinal}")


def _read_partial_rows(artifact_root: Path) -> tuple[Mapping[str, object], ...]:
    root = artifact_root.resolve(strict=False)
    if not root.is_dir():
        return ()
    rows: list[Mapping[str, object]] = []
    for receipt_path in sorted(root.glob("*.receipt.json")):
        try:
            receipt = _require_mapping(parse_strict_json(receipt_path.read_bytes(), canonical_plus_lf=True), "partial receipt")
        except (OSError, StrictJsonError, ValueError):
            continue
        rows.append({"ordinal": receipt.get("ordinal"), "cell": receipt.get("cell"), "map_identity": receipt.get("map_identity"), "object_sha256": receipt.get("object_sha256")})
    return tuple(rows)


def _empty_counts() -> dict[str, int]:
    return {key: 0 for key in HARD_CAPS} | {"registered_treatments": 1}


def _result(
    branch: CensusBranch,
    run_id: str,
    source_revision: str,
    counts: Mapping[str, int],
    first_failure: Mapping[str, object],
    *,
    design: DesignFreeze | None = None,
    partial: Sequence[Mapping[str, object]] = (),
    seal: Phase1Seal | None = None,
    witnesses: Sequence[PairWitness] = (),
    seal_evidence: Mapping[str, object] | None = None,
) -> CensusResult:
    return CensusResult(
        branch,
        run_id,
        source_revision,
        first_failure,
        design,
        dict(counts),
        tuple(partial),
        seal,
        tuple(witnesses),
        seal_evidence=seal_evidence,
    )


def _failure(code: str, detail: str) -> dict[str, object]:
    return {"code": code, "detail": detail}


def _write_new(path: Path, content: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite write-once artifact: {path}") from exc


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _contains_scalar(value: object, target: str) -> bool:
    if isinstance(value, dict):
        return any(_contains_scalar(key, target) or _contains_scalar(item, target) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_scalar(item, target) for item in value)
    return value == target


def _decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise MaterializationError(f"exact numeric literal must be integer or decimal string, got {value!r}")
    return Decimal(str(value))


def _validate_cell(cell: str) -> None:
    if cell not in CELL_ORDER:
        raise MaterializationError(f"unknown cell rejected: {cell}")


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
