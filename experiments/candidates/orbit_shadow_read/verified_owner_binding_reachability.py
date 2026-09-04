"""Typed zero-runtime ORBIT-A2 verified-owner-binding audit.

This direction-local fixture performs deterministic actor reads only.  It does
not train, update, fit, advance an environment, evaluate return, or attach
semantic meaning to an opaque owner category.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from enum import Enum
import hashlib
import hmac
import json
import math
import re
import sys
from typing import Mapping


ASSIGNMENT_ID = "ORBIT-A2-VERIFIED-OWNER-BINDING-REACHABILITY"
CANDIDATE = "CAND-VAP-ORBIT-LITE@verified-owner-binding-revision-v9"
VERIFIED_SCHEMA = "orbit.verified-owner-binding.v9"
OPAQUE_HANDLE_PATTERN = re.compile(r"obh_[0-9a-f]{32}")
ANONYMOUS_OWNER_TOKEN = "anonymous-owner"
SOURCE_PATHS = (
    "experiments/candidates/orbit_shadow_read/verified_owner_binding_reachability.py",
    "scripts/run_orbit_a2_verified_owner_binding_reachability.py",
    "tests/experiments/candidates/orbit_shadow_read/test_verified_owner_binding_reachability.py",
    "docs/research/candidates/orbit_shadow_read/CODE_SCIENCE_INDEX.md",
)


class VerificationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class _Bottom(str, Enum):
    BOTTOM = "BOTTOM"


BOTTOM = _Bottom.BOTTOM


class InvalidReason(str, Enum):
    UNTRUSTED_PRINCIPAL = "UNTRUSTED_PRINCIPAL"
    UNAUTHORIZED_PRINCIPAL = "UNAUTHORIZED_PRINCIPAL"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    EPOCH_MISMATCH = "EPOCH_MISMATCH"
    PAYLOAD_DIGEST_MISMATCH = "PAYLOAD_DIGEST_MISMATCH"
    SOURCE_SNAPSHOT_DIGEST_MISMATCH = "SOURCE_SNAPSHOT_DIGEST_MISMATCH"


class Route(str, Enum):
    CANDIDATE = "candidate"
    OWNER_BLIND = "owner_blind"
    VALIDITY_ONLY = "validity_only"


class Branch(str, Enum):
    A2_INVALID_CONTROL = "A2_INVALID_CONTROL"
    A2_OWNER_ALIAS_NOT_CONSUMED = "A2_OWNER_ALIAS_NOT_CONSUMED"
    A2_NO_LOGIT_ESTIMAND = "A2_NO_LOGIT_ESTIMAND"
    A2_FAIL_OPEN_INVALID = "A2_FAIL_OPEN_INVALID"
    A2_LEAKAGE_OR_UNCONTROLLED_PATH = "A2_LEAKAGE_OR_UNCONTROLLED_PATH"
    A2_GENERIC_PROVENANCE_GATE = "A2_GENERIC_PROVENANCE_GATE"
    A2_OWNER_MAIN_EFFECT_ONLY = "A2_OWNER_MAIN_EFFECT_ONLY"
    A2_LOGIT_REACHABILITY_ONLY = "A2_LOGIT_REACHABILITY_ONLY"
    A2_OWNER_BINDING_REACHES_FIRST_ACTION_KERNEL = (
        "A2_OWNER_BINDING_REACHES_FIRST_ACTION_KERNEL"
    )


@dataclass(frozen=True)
class VerifiedOwnerBindingView:
    status: VerificationStatus
    opaque_owner_handle: str | _Bottom
    epoch: int | _Bottom
    payload_digest: str | _Bottom
    source_snapshot_digest: str | _Bottom

    def __post_init__(self) -> None:
        tail = (
            self.opaque_owner_handle,
            self.epoch,
            self.payload_digest,
            self.source_snapshot_digest,
        )
        if self.status is VerificationStatus.INVALID:
            if any(value is not BOTTOM for value in tail):
                raise ValueError("INVALID VerifiedOwnerBindingView must be all bottom")
            return
        if self.status is not VerificationStatus.VALID:
            raise ValueError("unknown verification status")
        if not isinstance(self.opaque_owner_handle, str) or not OPAQUE_HANDLE_PATTERN.fullmatch(
            self.opaque_owner_handle
        ):
            raise ValueError("VALID view requires an equal-format opaque owner handle")
        if not isinstance(self.epoch, int) or self.epoch < 0:
            raise ValueError("VALID view requires a nonnegative epoch")
        if not _is_digest(self.payload_digest) or not _is_digest(
            self.source_snapshot_digest
        ):
            raise ValueError("VALID view requires canonical content digests")

    def as_tuple(self) -> tuple[object, object, object, object, object]:
        return (
            self.status,
            self.opaque_owner_handle,
            self.epoch,
            self.payload_digest,
            self.source_snapshot_digest,
        )


INVALID_VIEW = VerifiedOwnerBindingView(
    VerificationStatus.INVALID, BOTTOM, BOTTOM, BOTTOM, BOTTOM
)


@dataclass(frozen=True)
class SealedStatement:
    schema: str
    epoch: int
    payload: bytes
    payload_digest: str
    source_snapshot: bytes
    source_snapshot_digest: str

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(
            {
                "epoch": self.epoch,
                "payload_hex": self.payload.hex(),
                "payload_digest": self.payload_digest,
                "schema": self.schema,
                "source_snapshot_hex": self.source_snapshot.hex(),
                "source_snapshot_digest": self.source_snapshot_digest,
            }
        )


@dataclass(frozen=True)
class SignedCertificate:
    principal_id: str
    statement: SealedStatement
    signature: bytes


@dataclass(frozen=True)
class TrustedPrincipal:
    principal_id: str
    signing_secret: bytes
    authorized: bool


@dataclass(frozen=True)
class TrustStore:
    principals: tuple[TrustedPrincipal, ...]
    opaque_namespace_secret: bytes

    def lookup(self, principal_id: str) -> TrustedPrincipal | None:
        matches = tuple(item for item in self.principals if item.principal_id == principal_id)
        if len(matches) > 1:
            raise ValueError("trust store contains a duplicate principal")
        return matches[0] if matches else None


@dataclass(frozen=True)
class VerificationExpectation:
    schema: str
    epoch: int
    payload_digest: str
    source_snapshot_digest: str


@dataclass(frozen=True)
class QuarantineRecord:
    reason: InvalidReason
    payload: bytes


@dataclass(frozen=True)
class VerificationOutcome:
    view: VerifiedOwnerBindingView
    quarantine: QuarantineRecord | None


@dataclass(frozen=True)
class Fixture:
    trust_store: TrustStore
    expectation: VerificationExpectation
    valid_certificates: tuple[SignedCertificate, SignedCertificate]
    signature_corrupted_certificate: SignedCertificate


def seal_statement(
    payload: bytes,
    source_snapshot: bytes,
    *,
    schema: str = VERIFIED_SCHEMA,
    epoch: int = 11,
) -> SealedStatement:
    return SealedStatement(
        schema=schema,
        epoch=epoch,
        payload=payload,
        payload_digest=_digest(payload),
        source_snapshot=source_snapshot,
        source_snapshot_digest=_digest(source_snapshot),
    )


def sign_statement(principal: TrustedPrincipal, statement: SealedStatement) -> SignedCertificate:
    signature = hmac.new(
        principal.signing_secret, statement.canonical_bytes(), hashlib.sha256
    ).digest()
    return SignedCertificate(principal.principal_id, statement, signature)


def verify_owner_binding(
    certificate: SignedCertificate,
    trust_store: TrustStore,
    expectation: VerificationExpectation,
) -> VerificationOutcome:
    """Apply the frozen checks in order and expose only the typed actor view."""

    principal = trust_store.lookup(certificate.principal_id)
    if principal is None:
        return _invalid(certificate, InvalidReason.UNTRUSTED_PRINCIPAL)
    if not principal.authorized:
        return _invalid(certificate, InvalidReason.UNAUTHORIZED_PRINCIPAL)
    expected_signature = hmac.new(
        principal.signing_secret,
        certificate.statement.canonical_bytes(),
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(certificate.signature, expected_signature):
        return _invalid(certificate, InvalidReason.INVALID_SIGNATURE)

    statement = certificate.statement
    if statement.schema != expectation.schema:
        return _invalid(certificate, InvalidReason.SCHEMA_MISMATCH)
    if statement.epoch != expectation.epoch:
        return _invalid(certificate, InvalidReason.EPOCH_MISMATCH)
    if (
        statement.payload_digest != _digest(statement.payload)
        or statement.payload_digest != expectation.payload_digest
    ):
        return _invalid(certificate, InvalidReason.PAYLOAD_DIGEST_MISMATCH)
    if (
        statement.source_snapshot_digest != _digest(statement.source_snapshot)
        or statement.source_snapshot_digest != expectation.source_snapshot_digest
    ):
        return _invalid(certificate, InvalidReason.SOURCE_SNAPSHOT_DIGEST_MISMATCH)

    handle = "obh_" + hmac.new(
        trust_store.opaque_namespace_secret,
        principal.principal_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    return VerificationOutcome(
        VerifiedOwnerBindingView(
            VerificationStatus.VALID,
            handle,
            statement.epoch,
            statement.payload_digest,
            statement.source_snapshot_digest,
        ),
        None,
    )


def _invalid(certificate: SignedCertificate, reason: InvalidReason) -> VerificationOutcome:
    return VerificationOutcome(
        INVALID_VIEW,
        QuarantineRecord(reason=reason, payload=certificate.statement.payload),
    )


def build_fixture() -> Fixture:
    payload = _canonical_bytes(
        {"kind": "sealed-prior-owner-statement", "value": [0.25, -0.25]}
    )
    source_snapshot = _canonical_bytes(
        {"snapshot": "prior-epoch-s11", "state": [0.5, -0.25, 0.75]}
    )
    statement = seal_statement(payload, source_snapshot)
    principals = (
        TrustedPrincipal("fixture-principal-alpha", b"alpha-signing-secret", True),
        TrustedPrincipal("fixture-principal-beta", b"beta-signing-secret", True),
    )
    trust_store = TrustStore(principals, b"orbit-a2-opaque-namespace")
    certificates = tuple(sign_statement(item, statement) for item in principals)
    expectation = VerificationExpectation(
        VERIFIED_SCHEMA,
        statement.epoch,
        statement.payload_digest,
        statement.source_snapshot_digest,
    )
    corrupted = replace(
        certificates[0],
        signature=bytes((certificates[0].signature[0] ^ 1,))
        + certificates[0].signature[1:],
    )
    return Fixture(trust_store, expectation, certificates, corrupted)


def invalid_certificate_for(
    cause: str, fixture: Fixture
) -> tuple[SignedCertificate, TrustStore]:
    base = fixture.valid_certificates[0]
    principal = fixture.trust_store.principals[0]
    statement = base.statement
    trust_store = fixture.trust_store
    if cause == "trust":
        return replace(base, principal_id="unregistered-principal"), trust_store
    if cause == "authorization":
        denied = replace(principal, authorized=False)
        return base, replace(
            trust_store,
            principals=(denied,) + trust_store.principals[1:],
        )
    if cause == "signature":
        return fixture.signature_corrupted_certificate, trust_store
    if cause == "schema":
        statement = replace(statement, schema="orbit.unregistered-schema")
    elif cause == "epoch":
        statement = replace(statement, epoch=statement.epoch + 1)
    elif cause == "payload_digest":
        statement = replace(statement, payload_digest="0" * 64)
    elif cause == "source_snapshot_digest":
        statement = replace(statement, source_snapshot_digest="0" * 64)
    else:
        raise ValueError(f"unknown invalid cause: {cause}")
    return sign_statement(principal, statement), trust_store


@dataclass(frozen=True)
class ActionSpace:
    actions: tuple[str, ...]
    legal_mask: tuple[bool, ...]

    def __post_init__(self) -> None:
        if not self.actions or len(self.actions) != len(self.legal_mask):
            raise ValueError("action/mask shape mismatch")
        if len(set(self.actions)) != len(self.actions) or not any(self.legal_mask):
            raise ValueError("action space must contain unique actions and legal support")


@dataclass(frozen=True)
class FrozenContext:
    current_state: tuple[float, ...]
    action_space: ActionSpace
    recurrent_state: tuple[float, ...]
    evaluation_order: tuple[int, ...]
    clocks: tuple[int, ...]
    roster: tuple[str, ...]
    communication: tuple[float, ...]
    evaluation_mode: str

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(
            {
                "action_space": {
                    "actions": self.action_space.actions,
                    "legal_mask": self.action_space.legal_mask,
                },
                "clocks": self.clocks,
                "communication": self.communication,
                "current_state": self.current_state,
                "evaluation_mode": self.evaluation_mode,
                "evaluation_order": self.evaluation_order,
                "recurrent_state": self.recurrent_state,
                "roster": self.roster,
            }
        )


@dataclass(frozen=True)
class RouteModel:
    owner_embedding_rows: tuple[tuple[str, tuple[float, ...]], ...]
    anonymous_embedding_row: tuple[float, ...]
    action_width: int

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(
            {
                "anonymous_embedding_row": self.anonymous_embedding_row,
                "owner_embedding_rows": self.owner_embedding_rows,
                "action_width": self.action_width,
            }
        )

    def row_for(self, handle: str) -> tuple[float, ...]:
        matches = tuple(row for key, row in self.owner_embedding_rows if key == handle)
        if len(matches) != 1:
            raise ValueError("owner handle has no unique embedding row")
        return matches[0]


@dataclass(frozen=True)
class RouteClone:
    model: RouteModel
    context: FrozenContext
    model_digest: str
    recurrence_digest: str
    context_digest: str


@dataclass(frozen=True)
class ActorInput:
    status: VerificationStatus
    route: Route
    nonprincipal_tensor: tuple[float, ...]
    owner_slice: tuple[float, ...]
    current_state: tuple[float, ...]
    action_space: ActionSpace

    def nonprincipal_bytes(self) -> bytes:
        return _canonical_bytes(self.nonprincipal_tensor)


@dataclass(frozen=True)
class RouteOutput:
    logits: tuple[float, ...]
    kernel: tuple[float, ...]


@dataclass(frozen=True)
class RouteEvaluation:
    logits: tuple[float, ...]
    kernel: tuple[float, ...]
    owner_slice: tuple[float, ...]
    nonprincipal_digest: str
    model_digest: str
    recurrence_digest: str
    context_digest: str
    legal_actions: tuple[str, ...]
    used_zero_path: bool
    joint_alias_permutation_output_equal: bool


@dataclass(frozen=True)
class RouteCellRecord:
    route: Route
    principal_label: str
    role: int
    clone_id: str
    valid: bool
    logits: tuple[float, ...]
    kernel: tuple[float, ...]
    owner_slice: tuple[float, ...]
    nonprincipal_digest: str
    model_digest: str
    recurrence_digest: str
    context_digest: str
    legal_actions: tuple[str, ...]
    used_zero_path: bool
    joint_alias_permutation_output_equal: bool


def build_frozen_context() -> FrozenContext:
    return FrozenContext(
        current_state=(0.5, -0.25, 0.75),
        action_space=ActionSpace(("hold", "yield", "advance"), (True, False, True)),
        recurrent_state=(0.125, -0.125),
        evaluation_order=(0, 1, 2),
        clocks=(17, 17),
        roster=("structural-role-0", "structural-role-1"),
        communication=(0.0, 0.0),
        evaluation_mode="deterministic-eval",
    )


def build_model(handles: tuple[str, ...]) -> RouteModel:
    if len(handles) != 2 or len(set(handles)) != 2:
        raise ValueError("fixture requires exactly two distinct opaque handles")
    if not all(OPAQUE_HANDLE_PATTERN.fullmatch(handle) for handle in handles):
        raise ValueError("model accepts opaque handles only")
    scale = 1.0 / math.sqrt(2.0)
    rows = (
        (handles[0], (scale, -scale, 0.0)),
        (handles[1], (-scale, scale, 0.0)),
    )
    anonymous_scale = 1.0 / math.sqrt(6.0)
    anonymous = (anonymous_scale, anonymous_scale, -2.0 * anonymous_scale)
    return RouteModel(rows, anonymous, 3)


def owner_by_role_residual(
    model: RouteModel, opaque_owner_handle: str, role: int
) -> tuple[float, ...]:
    """The sole consumer of the opaque handle: a normalized role interaction."""

    if role not in (0, 1):
        raise ValueError("role must be one of the two structural clones")
    row = model.row_for(opaque_owner_handle)
    norm = math.sqrt(sum(value * value for value in row))
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=16.0 * sys.float_info.epsilon):
        raise ValueError("owner embedding row must be normalized")
    sign = -1.0 if role == 0 else 1.0
    return tuple(sign * value for value in row)


def _anonymous_owner_by_role_residual(
    model: RouteModel, anonymous_owner_token: str, role: int
) -> tuple[float, ...]:
    if anonymous_owner_token != ANONYMOUS_OWNER_TOKEN:
        raise ValueError("owner-blind route accepts only the registered anonymous token")
    if role not in (0, 1):
        raise ValueError("role must be one of the two structural clones")
    sign = -1.0 if role == 0 else 1.0
    return tuple(sign * value for value in model.anonymous_embedding_row)


def build_actor_input(
    *,
    view: VerifiedOwnerBindingView,
    route: Route,
    role: int,
    context: FrozenContext,
    model: RouteModel,
) -> ActorInput:
    if role not in (0, 1):
        raise ValueError("role must be one of the two structural clones")
    nonprincipal = context.current_state + (float(role),)
    if view.status is VerificationStatus.INVALID:
        owner_slice = (0.0,) * model.action_width
    elif route is Route.CANDIDATE:
        assert isinstance(view.opaque_owner_handle, str)
        owner_slice = owner_by_role_residual(model, view.opaque_owner_handle, role)
    elif route is Route.OWNER_BLIND:
        owner_slice = _anonymous_owner_by_role_residual(
            model, ANONYMOUS_OWNER_TOKEN, role
        )
    elif route is Route.VALIDITY_ONLY:
        owner_slice = (0.0,) * model.action_width
    else:
        raise ValueError("unknown route")
    return ActorInput(
        view.status,
        route,
        nonprincipal,
        owner_slice,
        context.current_state,
        context.action_space,
    )


def restore_route_clone(model: RouteModel, context: FrozenContext) -> RouteClone:
    model_clone = RouteModel(
        owner_embedding_rows=tuple(
            (str(handle), tuple(list(row)))
            for handle, row in model.owner_embedding_rows
        ),
        anonymous_embedding_row=tuple(list(model.anonymous_embedding_row)),
        action_width=model.action_width,
    )
    context_clone = FrozenContext(
        current_state=tuple(list(context.current_state)),
        action_space=ActionSpace(
            tuple(list(context.action_space.actions)),
            tuple(list(context.action_space.legal_mask)),
        ),
        recurrent_state=tuple(list(context.recurrent_state)),
        evaluation_order=tuple(list(context.evaluation_order)),
        clocks=tuple(list(context.clocks)),
        roster=tuple(list(context.roster)),
        communication=tuple(list(context.communication)),
        evaluation_mode=str(context.evaluation_mode),
    )
    context_bytes = context_clone.canonical_bytes()
    return RouteClone(
        model=model_clone,
        context=context_clone,
        model_digest=_digest(model_clone.canonical_bytes()),
        recurrence_digest=_digest(_canonical_bytes(context_clone.recurrent_state)),
        context_digest=_digest(context_bytes),
    )


def zero_path_owner_bypass(
    current_state: tuple[float, ...], action_space: ActionSpace
) -> RouteOutput:
    """Registered current-state-only ZERO_PATH over the unchanged actions."""

    logits = _center(_nonprincipal_base(current_state + (0.0,)))
    return RouteOutput(logits, _masked_kernel(logits, action_space))


def evaluate_route_cell(
    *,
    actor_input: ActorInput,
    clone: RouteClone,
    jointly_relabelled_actor_input: ActorInput,
    jointly_permuted_clone: RouteClone,
) -> RouteEvaluation:
    """Evaluate one registered cell and its joint alias/row intervention.

    Reporting identifiers are intentionally absent from this interface and
    from ``RouteClone``.  The caller attaches a reporting ID only after both
    evaluations have completed.
    """

    primary = _evaluate_principal_invariant_clone(actor_input, clone)
    permuted = _evaluate_principal_invariant_clone(
        jointly_relabelled_actor_input, jointly_permuted_clone
    )
    if (
        actor_input.status is not jointly_relabelled_actor_input.status
        or actor_input.route is not jointly_relabelled_actor_input.route
        or actor_input.nonprincipal_tensor
        != jointly_relabelled_actor_input.nonprincipal_tensor
        or actor_input.current_state != jointly_relabelled_actor_input.current_state
        or actor_input.action_space != jointly_relabelled_actor_input.action_space
    ):
        raise ValueError("joint alias permutation changed a non-owner actor field")
    return RouteEvaluation(
        logits=primary.logits,
        kernel=primary.kernel,
        owner_slice=actor_input.owner_slice,
        nonprincipal_digest=_digest(actor_input.nonprincipal_bytes()),
        model_digest=clone.model_digest,
        recurrence_digest=clone.recurrence_digest,
        context_digest=clone.context_digest,
        legal_actions=actor_input.action_space.actions,
        used_zero_path=actor_input.status is VerificationStatus.INVALID,
        joint_alias_permutation_output_equal=(
            actor_input.owner_slice == jointly_relabelled_actor_input.owner_slice
            and primary.logits == permuted.logits
            and primary.kernel == permuted.kernel
        ),
    )


def _evaluate_principal_invariant_clone(
    actor_input: ActorInput, clone: RouteClone
) -> RouteOutput:
    if actor_input.current_state != clone.context.current_state:
        raise ValueError("current state differs from frozen clone")
    if actor_input.action_space != clone.context.action_space:
        raise ValueError("mask/order differs from frozen clone")
    if actor_input.status is VerificationStatus.INVALID:
        output = zero_path_owner_bypass(actor_input.current_state, actor_input.action_space)
    else:
        base = _nonprincipal_base(actor_input.nonprincipal_tensor)
        logits = _center(tuple(a + b for a, b in zip(base, actor_input.owner_slice)))
        output = RouteOutput(logits, _masked_kernel(logits, actor_input.action_space))
    return output


def permute_owner_aliases_and_embedding_rows(
    model: RouteModel, permuted_handles: tuple[str, ...]
) -> RouteModel:
    if len(permuted_handles) != len(model.owner_embedding_rows):
        raise ValueError("owner alias permutation has the wrong cardinality")
    if len(set(permuted_handles)) != len(permuted_handles):
        raise ValueError("owner alias permutation must be bijective")
    rows = tuple(
        (new_handle, old_row)
        for new_handle, (_, old_row) in zip(
            permuted_handles, model.owner_embedding_rows
        )
    )
    return replace(model, owner_embedding_rows=rows)


@dataclass(frozen=True)
class Tolerances:
    dtype: str
    epsilon: float
    logit: float
    kernel: float
    observations_before_freeze: int


def freeze_tolerances() -> Tolerances:
    epsilon = sys.float_info.epsilon
    return Tolerances("float64", epsilon, 64.0 * epsilon, 128.0 * epsilon, 0)


@dataclass(frozen=True)
class BranchWitnesses:
    invalid_control: bool
    owner_alias_consumed: bool
    logit_estimand_defined: bool
    invalid_fallback_exact: bool
    controlled_path: bool
    comparator_invariant: bool
    owner_main_effect_zero: bool
    candidate_logit_reachable: bool
    candidate_kernel_reachable: bool

    def as_dict(self) -> dict[str, bool]:
        return {item.name: bool(getattr(self, item.name)) for item in fields(self)}


def select_branch(witnesses: BranchWitnesses) -> Branch:
    if not witnesses.invalid_control:
        return Branch.A2_INVALID_CONTROL
    if not witnesses.owner_alias_consumed:
        return Branch.A2_OWNER_ALIAS_NOT_CONSUMED
    if not witnesses.logit_estimand_defined or not witnesses.candidate_logit_reachable:
        return Branch.A2_NO_LOGIT_ESTIMAND
    if not witnesses.invalid_fallback_exact:
        return Branch.A2_FAIL_OPEN_INVALID
    if not witnesses.controlled_path:
        return Branch.A2_LEAKAGE_OR_UNCONTROLLED_PATH
    if not witnesses.comparator_invariant:
        return Branch.A2_GENERIC_PROVENANCE_GATE
    if not witnesses.owner_main_effect_zero:
        return Branch.A2_OWNER_MAIN_EFFECT_ONLY
    if not witnesses.candidate_kernel_reachable:
        return Branch.A2_LOGIT_REACHABILITY_ONLY
    return Branch.A2_OWNER_BINDING_REACHES_FIRST_ACTION_KERNEL


@dataclass(frozen=True)
class AuditResult:
    branch: Branch
    witnesses: BranchWitnesses
    tolerances: Tolerances
    metrics: tuple[tuple[str, float], ...]
    invariants: tuple[tuple[str, bool], ...]
    records: tuple[RouteCellRecord, ...]
    route_cell_calls: int
    environment_transitions: int = 0
    learner_calls: int = 0
    trainer_calls: int = 0
    optimizer_updates: int = 0
    return_evaluations: int = 0
    model_fits: int = 0

    def to_bytes(self) -> bytes:
        payload = {
            "assignment_id": ASSIGNMENT_ID,
            "candidate": CANDIDATE,
            "branch_precedence": [branch.value for branch in Branch],
            "branch": self.branch.value,
            "witnesses": self.witnesses.as_dict(),
            "tolerances": {
                "dtype": self.tolerances.dtype,
                "epsilon": self.tolerances.epsilon,
                "logit": self.tolerances.logit,
                "kernel": self.tolerances.kernel,
                "observations_before_freeze": self.tolerances.observations_before_freeze,
            },
            "metrics": dict(self.metrics),
            "invariants": dict(self.invariants),
            "activity_counts": {
                "route_cell_calls": self.route_cell_calls,
                "environment_transitions": self.environment_transitions,
                "learner_calls": self.learner_calls,
                "trainer_calls": self.trainer_calls,
                "optimizer_updates": self.optimizer_updates,
                "return_evaluations": self.return_evaluations,
                "model_fits": self.model_fits,
            },
            "records": [_record_payload(record) for record in self.records],
            "limitations": [
                "interface_actionability_only",
                "no_learned_owner_meaning",
                "no_natural_use_or_utility",
                "no_persistence_return_or_generalization_claim",
            ],
        }
        return _canonical_bytes(payload)


def run_verified_owner_binding_audit() -> AuditResult:
    """Execute the single deterministic 15-call registered audit payload."""

    tolerances = freeze_tolerances()  # Frozen before any route observation.
    fixture = build_fixture()
    outcomes = tuple(
        verify_owner_binding(item, fixture.trust_store, fixture.expectation)
        for item in fixture.valid_certificates
    )
    invalid = verify_owner_binding(
        fixture.signature_corrupted_certificate,
        fixture.trust_store,
        fixture.expectation,
    )
    handles = tuple(outcome.view.opaque_owner_handle for outcome in outcomes)
    if not all(isinstance(handle, str) for handle in handles):
        raise RuntimeError("valid fixture did not produce owner handles")
    typed_handles = tuple(str(handle) for handle in handles)
    model = build_model(typed_handles)
    jointly_permuted_model = permute_owner_aliases_and_embedding_rows(
        model, typed_handles[::-1]
    )
    context = build_frozen_context()

    records: list[RouteCellRecord] = []
    clones: list[RouteClone] = []
    jointly_permuted_clones: list[RouteClone] = []
    for route in Route:
        for principal_index, outcome in enumerate(outcomes):
            for role in (0, 1):
                label = f"P{principal_index}"
                reporting_clone_id = f"{route.value}-{label}-R{role}"
                actor_input = build_actor_input(
                    view=outcome.view,
                    route=route,
                    role=role,
                    context=context,
                    model=model,
                )
                jointly_relabelled_view = replace(
                    outcome.view,
                    opaque_owner_handle=typed_handles[1 - principal_index],
                )
                jointly_relabelled_actor_input = build_actor_input(
                    view=jointly_relabelled_view,
                    route=route,
                    role=role,
                    context=context,
                    model=jointly_permuted_model,
                )
                clone = restore_route_clone(model, context)
                jointly_permuted_clone = restore_route_clone(
                    jointly_permuted_model, context
                )
                clones.append(clone)
                jointly_permuted_clones.append(jointly_permuted_clone)
                evaluation = evaluate_route_cell(
                    actor_input=actor_input,
                    clone=clone,
                    jointly_relabelled_actor_input=jointly_relabelled_actor_input,
                    jointly_permuted_clone=jointly_permuted_clone,
                )
                records.append(
                    _attach_reporting_identity(
                        evaluation,
                        route=route,
                        principal_label=label,
                        role=role,
                        reporting_clone_id=reporting_clone_id,
                        valid=True,
                    )
                )
        reporting_clone_id = f"{route.value}-INVALID-R0"
        actor_input = build_actor_input(
            view=invalid.view,
            route=route,
            role=0,
            context=context,
            model=model,
        )
        jointly_relabelled_actor_input = build_actor_input(
            view=invalid.view,
            route=route,
            role=0,
            context=context,
            model=jointly_permuted_model,
        )
        clone = restore_route_clone(model, context)
        jointly_permuted_clone = restore_route_clone(jointly_permuted_model, context)
        clones.append(clone)
        jointly_permuted_clones.append(jointly_permuted_clone)
        evaluation = evaluate_route_cell(
            actor_input=actor_input,
            clone=clone,
            jointly_relabelled_actor_input=jointly_relabelled_actor_input,
            jointly_permuted_clone=jointly_permuted_clone,
        )
        records.append(
            _attach_reporting_identity(
                evaluation,
                route=route,
                principal_label="INVALID",
                role=0,
                reporting_clone_id=reporting_clone_id,
                valid=False,
            )
        )
    frozen_records = tuple(records)
    if len(frozen_records) != 15:
        raise RuntimeError("registered route-cell cap drift")

    route_metrics = {
        route: _route_metrics(frozen_records, route) for route in Route
    }
    candidate = route_metrics[Route.CANDIDATE]
    bypass = zero_path_owner_bypass(context.current_state, context.action_space)
    invalid_records = tuple(record for record in frozen_records if not record.valid)
    invalid_exact = len(invalid_records) == 3 and all(
        record.used_zero_path
        and record.logits == bypass.logits
        and record.kernel == bypass.kernel
        and record.legal_actions == context.action_space.actions
        for record in invalid_records
    )
    comparator_invariant = all(
        route_metrics[route]["mixed_logit"] <= tolerances.logit
        and route_metrics[route]["mixed_kernel"] <= tolerances.kernel
        and _principal_invariant(frozen_records, route)
        for route in (Route.OWNER_BLIND, Route.VALIDITY_ONLY)
    )
    candidate_records = _valid_route_records(frozen_records, Route.CANDIDATE)
    owner_alias_consumed = all(
        _cell(candidate_records, "P0", role).owner_slice
        != _cell(candidate_records, "P1", role).owner_slice
        for role in (0, 1)
    )
    outside_slice_identity = all(
        _cell(candidate_records, "P0", role).nonprincipal_digest
        == _cell(candidate_records, "P1", role).nonprincipal_digest
        for role in (0, 1)
    )
    alias_permutation = all(
        record.joint_alias_permutation_output_equal for record in frozen_records
    )
    actor_field_names = {item.name for item in fields(ActorInput)}
    forbidden_actor_fields = {
        "certificate",
        "signature",
        "key_id",
        "certificate_digest",
        "trust_store_index",
        "cache_address",
        "internal_id",
        "payload",
        "principal_id",
        "clone_id",
        "reporting_clone_id",
    }
    clone_field_names = {item.name for item in fields(RouteClone)}
    isolated_clones = (
        len({record.clone_id for record in frozen_records}) == 15
        and len({id(clone.model) for clone in clones + jointly_permuted_clones}) == 30
        and len({id(clone.context) for clone in clones + jointly_permuted_clones}) == 30
        and len({id(clone.context.recurrent_state) for clone in clones}) == 15
        and len(
            {
                id(clone.context.recurrent_state)
                for clone in jointly_permuted_clones
            }
        )
        == 15
        and len({record.model_digest for record in frozen_records}) == 1
        and len({record.recurrence_digest for record in frozen_records}) == 1
        and len({record.context_digest for record in frozen_records}) == 1
    )
    evaluator_metadata_principal_invariant = clone_field_names.isdisjoint(
        {"clone_id", "reporting_clone_id", "principal_label", "role"}
    )
    invalid_control = (
        invalid.view == INVALID_VIEW
        and invalid.quarantine is not None
        and invalid.quarantine.reason is InvalidReason.INVALID_SIGNATURE
        and invalid.quarantine.payload
        == fixture.signature_corrupted_certificate.statement.payload
    )
    complete_estimand = all(
        len(_valid_route_records(frozen_records, route)) == 4 for route in Route
    ) and all(
        math.isfinite(value)
        for metrics in route_metrics.values()
        for value in metrics.values()
    )
    owner_main_zero = (
        candidate["owner_main_logit"] <= tolerances.logit
        and candidate["owner_main_kernel"] <= tolerances.kernel
    )
    invariants = (
        ("two_distinct_equal_format_opaque_handles", len(set(typed_handles)) == 2),
        ("identical_sealed_content", fixture.valid_certificates[0].statement == fixture.valid_certificates[1].statement),
        ("byte_tensor_identity_outside_owner_slice", outside_slice_identity),
        ("isolated_equal_model_recurrence_context_clones", isolated_clones),
        ("frozen_mask_order_clocks_roster_communication_eval", len({record.context_digest for record in frozen_records}) == 1),
        (
            "no_actor_or_evaluator_auth_lookup_reporting_channel",
            actor_field_names.isdisjoint(forbidden_actor_fields)
            and evaluator_metadata_principal_invariant,
        ),
        ("joint_owner_alias_embedding_row_permutation_outputs", alias_permutation),
        ("comparator_principal_invariance", comparator_invariant),
        ("invalid_exact_zero_path", invalid_exact),
        ("route_call_cap", len(frozen_records) == 15),
    )
    controlled_path = all(value for name, value in invariants if name not in {
        "comparator_principal_invariance", "invalid_exact_zero_path"
    })
    witnesses = BranchWitnesses(
        invalid_control=invalid_control,
        owner_alias_consumed=owner_alias_consumed,
        logit_estimand_defined=complete_estimand,
        invalid_fallback_exact=invalid_exact,
        controlled_path=controlled_path,
        comparator_invariant=comparator_invariant,
        owner_main_effect_zero=owner_main_zero,
        candidate_logit_reachable=candidate["mixed_logit"] > tolerances.logit,
        candidate_kernel_reachable=candidate["mixed_kernel"] > tolerances.kernel,
    )
    metrics = tuple(
        (f"{route.value}_{name}", value)
        for route in Route
        for name, value in route_metrics[route].items()
    )
    return AuditResult(
        branch=select_branch(witnesses),
        witnesses=witnesses,
        tolerances=tolerances,
        metrics=metrics,
        invariants=invariants,
        records=frozen_records,
        route_cell_calls=len(frozen_records),
    )


def _attach_reporting_identity(
    evaluation: RouteEvaluation,
    *,
    route: Route,
    principal_label: str,
    role: int,
    reporting_clone_id: str,
    valid: bool,
) -> RouteCellRecord:
    """Attach report-only labels after evaluation has irreversibly completed."""

    return RouteCellRecord(
        route=route,
        principal_label=principal_label,
        role=role,
        clone_id=reporting_clone_id,
        valid=valid,
        logits=evaluation.logits,
        kernel=evaluation.kernel,
        owner_slice=evaluation.owner_slice,
        nonprincipal_digest=evaluation.nonprincipal_digest,
        model_digest=evaluation.model_digest,
        recurrence_digest=evaluation.recurrence_digest,
        context_digest=evaluation.context_digest,
        legal_actions=evaluation.legal_actions,
        used_zero_path=evaluation.used_zero_path,
        joint_alias_permutation_output_equal=(
            evaluation.joint_alias_permutation_output_equal
        ),
    )


def _route_metrics(
    records: tuple[RouteCellRecord, ...], route: Route
) -> dict[str, float]:
    cells = _valid_route_records(records, route)
    mixed_logits = _mixed_difference(cells, "logits", center=True)
    mixed_kernels = _mixed_difference(cells, "kernel", center=False)
    owner_main_logits = _owner_main_difference(cells, "logits", center=True)
    owner_main_kernels = _owner_main_difference(cells, "kernel", center=False)
    return {
        "mixed_logit": _l2(mixed_logits),
        "mixed_kernel": 0.5 * sum(abs(value) for value in mixed_kernels),
        "owner_main_logit": _l2(owner_main_logits),
        "owner_main_kernel": 0.5 * sum(abs(value) for value in owner_main_kernels),
    }


def _valid_route_records(
    records: tuple[RouteCellRecord, ...], route: Route
) -> tuple[RouteCellRecord, ...]:
    return tuple(record for record in records if record.route is route and record.valid)


def _cell(
    records: tuple[RouteCellRecord, ...], principal_label: str, role: int
) -> RouteCellRecord:
    matches = tuple(
        record
        for record in records
        if record.principal_label == principal_label and record.role == role
    )
    if len(matches) != 1:
        raise ValueError("route estimand requires one complete principal-by-role cell")
    return matches[0]


def _mixed_difference(
    records: tuple[RouteCellRecord, ...], field: str, *, center: bool
) -> tuple[float, ...]:
    values: dict[tuple[str, int], tuple[float, ...]] = {}
    for principal in ("P0", "P1"):
        for role in (0, 1):
            vector = getattr(_cell(records, principal, role), field)
            values[principal, role] = _center(vector) if center else vector
    return tuple(
        values["P1", 1][index]
        - values["P0", 1][index]
        - values["P1", 0][index]
        + values["P0", 0][index]
        for index in range(len(values["P0", 0]))
    )


def _owner_main_difference(
    records: tuple[RouteCellRecord, ...], field: str, *, center: bool
) -> tuple[float, ...]:
    means: dict[str, tuple[float, ...]] = {}
    for principal in ("P0", "P1"):
        vectors = tuple(
            _center(getattr(_cell(records, principal, role), field))
            if center
            else getattr(_cell(records, principal, role), field)
            for role in (0, 1)
        )
        means[principal] = tuple(
            0.5 * (vectors[0][index] + vectors[1][index])
            for index in range(len(vectors[0]))
        )
    return tuple(a - b for a, b in zip(means["P1"], means["P0"]))


def _principal_invariant(records: tuple[RouteCellRecord, ...], route: Route) -> bool:
    cells = _valid_route_records(records, route)
    return all(
        _cell(cells, "P0", role).logits == _cell(cells, "P1", role).logits
        and _cell(cells, "P0", role).kernel == _cell(cells, "P1", role).kernel
        for role in (0, 1)
    )


def _nonprincipal_base(tensor: tuple[float, ...]) -> tuple[float, ...]:
    if len(tensor) != 4:
        raise ValueError("nonprincipal base tensor shape drift")
    state0, state1, state2, role = tensor
    del role
    return (
        0.75 * state0 - 0.25 * state1,
        -0.5 * state0 + 0.5 * state2,
        state1 - 0.25 * state2,
    )


def _masked_kernel(logits: tuple[float, ...], action_space: ActionSpace) -> tuple[float, ...]:
    if len(logits) != len(action_space.actions):
        raise ValueError("logit/action shape mismatch")
    maximum = max(value for value, legal in zip(logits, action_space.legal_mask) if legal)
    masses = tuple(
        math.exp(value - maximum) if legal else 0.0
        for value, legal in zip(logits, action_space.legal_mask)
    )
    total = sum(masses)
    return tuple(value / total for value in masses)


def _center(vector: tuple[float, ...]) -> tuple[float, ...]:
    mean = sum(vector) / len(vector)
    return tuple(value - mean for value in vector)


def _l2(vector: tuple[float, ...]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _record_payload(record: RouteCellRecord) -> Mapping[str, object]:
    return {
        "route": record.route.value,
        "principal_label": record.principal_label,
        "role": record.role,
        "clone_id": record.clone_id,
        "valid": record.valid,
        "logits": record.logits,
        "kernel": record.kernel,
        "used_zero_path": record.used_zero_path,
        "joint_alias_permutation_output_equal": (
            record.joint_alias_permutation_output_equal
        ),
        "legal_actions": record.legal_actions,
    }


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )
