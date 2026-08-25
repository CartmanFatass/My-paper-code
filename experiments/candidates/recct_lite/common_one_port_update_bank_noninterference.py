"""RECCT-A3 common one-port update-bank noninterference audit.

The audit consumes the accepted RECCT-A1 learner-owned callable without
opening its private capsule bytes.  Credit observations are carried by a
separate write-once fixture whose digest is bound to the A1 capsule digest.
Selectors receive only a narrow credit/tie view and return an LR/RL pointer;
the outer harness alone binds that pointer to the hidden immutable bank.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Callable, Iterable, Mapping, Protocol, Sequence

import torch

from experiments.candidates.recct_lite import directed_edge_masked_update as a1


TREATMENT_ID = "RECCT-A3-COMMON-ONE-PORT-UPDATE-BANK-NONINTERFERENCE"
TARGET_VERSION_ID = (
    "CAND-VAP-RECCT-LITE@factorized-one-port-policy-value-revision-v10"
)
RAW_OUTPUT_BINDING = "recct_lite.common_one_port_update_bank_noninterference.a3.v1"
SCHEMA_VERSION = 1
A1_SOURCE_COMMIT = "010da9a8bc3204d2363cfebaed022b130baa08e1"
A1_RESULT_COMMIT = "852538cf6a72429128d14de28ce2b17289b5dfd2"
A1_SOURCE_BLOB = "4e7d2231be938c4c77859eedf04b6c7c85007ca5"
A1_RESULT_BLOB = "bf67cb49bb3ebd4ec2cfe193f34aba8d3a2de16a"
A1_ACCEPTED_BRANCH = "A1_DIRECTED_EDGE_BINDING_PASS"
A1_RAW_OUTPUT_BINDING = "recct_lite.directed_edge_masked_update.a1.v1"

ORIENTATIONS = ("PLUS", "MINUS")
PORTS = ("LR", "RL")
SELECTORS = (
    "SIGNED_DIRECTED",
    "SIGN_DESTROYED",
    "BALANCED_DIRECTION_BLIND",
)
PROPOSAL_EPOCHS = (0, 2, 4, 6)
CONFIRMATION_HALVES = (("A", (1, 5)), ("B", (3, 7)))
SHADOW_STATES = ("00", "10", "01", "11")
TIE_VALUE = "LR"

A3_NOT_RUN_OR_CAP_READINESS_FAILURE = "A3_NOT_RUN_OR_CAP_READINESS_FAILURE"
A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE = (
    "A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE"
)
A3_A1_AUTHENTICATED_PORT_VERSION_ROLE_OR_MASK_BINDING_FAILURE = (
    "A3_A1_AUTHENTICATED_PORT_VERSION_ROLE_OR_MASK_BINDING_FAILURE"
)
A3_COMMON_PRETREATMENT_ANCESTRY_CARDINALITY_OR_RNG_ISOLATION_FAILURE = (
    "A3_COMMON_PRETREATMENT_ANCESTRY_CARDINALITY_OR_RNG_ISOLATION_FAILURE"
)
A3_BANK_COMPONENTWISE_RECOMPUTATION_IMMUTABILITY_OR_CALL_LEDGER_FAILURE = (
    "A3_BANK_COMPONENTWISE_RECOMPUTATION_IMMUTABILITY_OR_CALL_LEDGER_FAILURE"
)
A3_SELECTOR_FORMULA_TIE_SENTINEL_OR_INFORMATION_FIREWALL_FAILURE = (
    "A3_SELECTOR_FORMULA_TIE_SENTINEL_OR_INFORMATION_FIREWALL_FAILURE"
)
A3_ORIENTATION_INVOLUTION_OR_BALANCED_SCHEDULE_SPECIFICATION_FAILURE = (
    "A3_ORIENTATION_INVOLUTION_OR_BALANCED_SCHEDULE_SPECIFICATION_FAILURE"
)
A3_FACTORIZED_ONE_PORT_CONSTRUCTION_PASS = (
    "A3_FACTORIZED_ONE_PORT_CONSTRUCTION_PASS"
)

BRANCH_PRECEDENCE = (
    A3_NOT_RUN_OR_CAP_READINESS_FAILURE,
    A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE,
    A3_A1_AUTHENTICATED_PORT_VERSION_ROLE_OR_MASK_BINDING_FAILURE,
    A3_COMMON_PRETREATMENT_ANCESTRY_CARDINALITY_OR_RNG_ISOLATION_FAILURE,
    A3_BANK_COMPONENTWISE_RECOMPUTATION_IMMUTABILITY_OR_CALL_LEDGER_FAILURE,
    A3_SELECTOR_FORMULA_TIE_SENTINEL_OR_INFORMATION_FIREWALL_FAILURE,
    A3_ORIENTATION_INVOLUTION_OR_BALANCED_SCHEDULE_SPECIFICATION_FAILURE,
    A3_FACTORIZED_ONE_PORT_CONSTRUCTION_PASS,
)

EXPECTED_CAPS = MappingProxyType(
    {
        "named_audits": 1,
        "sealed_orientation_pairs": 1,
        "sealed_orientation_capsules": 2,
        "stored_cell_construction_calls": 4,
        "independent_cell_recomputation_calls": 4,
        "learner_backward_shadow_calls": 8,
        "optimizer_transition_shadow_calls": 8,
        "verified_stored_cells": 4,
        "real_selector_commitments": 6,
        "pure_selector_sentinel_calls": 36,
        "environment_episodes": 0,
        "environment_transitions": 0,
        "policy_calls": 0,
        "trainer_calls": 0,
        "evaluation_calls": 0,
        "committed_live_updates": 0,
        "retries_sweeps_rescues_replacement_capsules": 0,
        "pool_units": 0,
    }
)

FORBIDDEN_SELECTOR_FIELDS = frozenset(
    {
        "orientation",
        "outcome_label",
        "support",
        "reliability",
        "gradient",
        "global_norm",
        "clip_event",
        "clip_coefficient",
        "adam_state",
        "update_norm",
        "bank",
        "bank_digest",
        "held_out_outcome",
        "instance_id",
        "seed",
        "slot",
        "capsule_id",
        "capsule_digest",
        "source_digest",
    }
)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        _jsonable(value), separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(row) for key, row in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(row) for row in value]
    if isinstance(value, list):
        return [_jsonable(row) for row in value]
    return value


@dataclass(frozen=True)
class A1Binding:
    source_commit: str = A1_SOURCE_COMMIT
    result_commit: str = A1_RESULT_COMMIT
    source_blob: str = A1_SOURCE_BLOB
    result_blob: str = A1_RESULT_BLOB
    accepted_branch: str = A1_ACCEPTED_BRANCH
    raw_output_binding: str = A1_RAW_OUTPUT_BINDING
    port_payload_schema: str = a1.PORT_PAYLOAD_SCHEMA
    mint_provenance: str = a1.MINT_PROVENANCE

    def validate(self) -> None:
        if (
            self.source_commit != A1_SOURCE_COMMIT
            or self.result_commit != A1_RESULT_COMMIT
            or self.source_blob != A1_SOURCE_BLOB
            or self.result_blob != A1_RESULT_BLOB
            or self.accepted_branch != A1_ACCEPTED_BRANCH
            or self.raw_output_binding != a1.RAW_OUTPUT_BINDING
            or self.port_payload_schema != a1.PORT_PAYLOAD_SCHEMA
            or self.mint_provenance != a1.MINT_PROVENANCE
        ):
            raise ValueError("accepted RECCT-A1 source/result/callable binding changed")


@dataclass(frozen=True)
class CreditObservation:
    half: str
    state: str
    detached_predictions: tuple[float, float, float, float]
    observed_four_step_team_rewards: tuple[float, float, float, float]

    def validate(self) -> None:
        if (
            self.half not in {"A", "B"}
            or self.state not in SHADOW_STATES
            or len(self.detached_predictions) != 4
            or len(self.observed_four_step_team_rewards) != 4
            or not all(
                math.isfinite(float(row)) and 0.0 < float(row) < 1.0
                for row in self.detached_predictions
            )
            or not all(float(row) in {0.0, 1.0} for row in self.observed_four_step_team_rewards)
        ):
            raise ValueError("credit observation is incomplete, nonfinite, or misordered")


_CREDIT_OPEN_TOKEN = object()


@dataclass(frozen=True)
class CreditSourceLineage:
    source_kind: str
    source_record_id: str
    source_commit: str
    source_blob: str
    source_dto_sha256: str
    immutable_before_audit: bool

    def validate(self) -> None:
        if (
            self.source_kind not in {"REGISTERED_IMMUTABLE_DTO", "TECHNICAL_SYNTHETIC"}
            or not self.source_record_id
            or not self.source_commit
            or not self.source_blob
            or len(self.source_dto_sha256) != 64
            or not self.immutable_before_audit
        ):
            raise ValueError("credit source lineage is incomplete or not prospectively immutable")


@dataclass(frozen=True)
class CreditSourceManifest:
    schema: str
    capsule_digest: str
    opaque_content_digest: str
    lineage_digest: str
    observation_count: int
    ordered_key_digest: str


def credit_observation_order() -> tuple[tuple[str, str], ...]:
    return tuple(
        (half, state) for half in ("A", "B") for state in SHADOW_STATES
    )


def credit_observation_order_digest() -> str:
    return _digest(_canonical_json(credit_observation_order()))


class SealedCreditSource:
    """Write-once detached source observations bound to one capsule digest."""

    __slots__ = (
        "__capsule_digest",
        "__encoded_content",
        "__opaque_content_digest",
        "__digest",
        "__lineage",
        "__manifest",
        "__content_open_count",
        "__content_decode_count",
        "__manifest_access_count",
    )

    def __init__(
        self,
        capsule_digest: str,
        encoded_content: bytes,
        opaque_content_digest: str,
        declared_observation_count: int,
        declared_ordered_key_digest: str,
        lineage: CreditSourceLineage,
    ) -> None:
        lineage.validate()
        content = bytes(encoded_content)
        if (
            not capsule_digest
            or not content
            or _digest(content) != opaque_content_digest
            or int(declared_observation_count) != 8
            or declared_ordered_key_digest != credit_observation_order_digest()
        ):
            raise ValueError("opaque credit content manifest/digest binding failed")
        self.__capsule_digest = str(capsule_digest)
        self.__encoded_content = content
        self.__opaque_content_digest = str(opaque_content_digest)
        self.__lineage = lineage
        self.__digest = self._computed_digest()
        self.__manifest = CreditSourceManifest(
            schema="recct-a3.credit-source-manifest.v1",
            capsule_digest=self.__capsule_digest,
            opaque_content_digest=self.__opaque_content_digest,
            lineage_digest=_digest(_canonical_json(lineage)),
            observation_count=int(declared_observation_count),
            ordered_key_digest=str(declared_ordered_key_digest),
        )
        self.__content_open_count = 0
        self.__content_decode_count = 0
        self.__manifest_access_count = 0

    @classmethod
    def from_technical_observations(
        cls,
        capsule_digest: str,
        observations: Sequence[CreditObservation],
        lineage: CreditSourceLineage,
    ) -> "SealedCreditSource":
        rows = tuple(observations)
        for row in rows:
            row.validate()
        keys = tuple((row.half, row.state) for row in rows)
        if keys != credit_observation_order() or len(set(keys)) != len(keys):
            raise ValueError(
                "credit source must contain the exact ordered A/B x 00/10/01/11 rows"
            )
        encoded = _canonical_json(
            {
                "schema": "recct-a3.credit-observation-content.v1",
                "observations": rows,
            }
        )
        return cls(
            capsule_digest,
            encoded,
            _digest(encoded),
            8,
            credit_observation_order_digest(),
            lineage,
        )

    @property
    def capsule_digest(self) -> str:
        return self.__capsule_digest

    @property
    def digest(self) -> str:
        return self.__digest

    @property
    def lineage(self) -> CreditSourceLineage:
        return self.__lineage

    @property
    def content_open_count(self) -> int:
        return self.__content_open_count

    @property
    def content_decode_count(self) -> int:
        return self.__content_decode_count

    @property
    def manifest_access_count(self) -> int:
        return self.__manifest_access_count

    def inspect_manifest(self) -> CreditSourceManifest:
        self.__manifest_access_count += 1
        return self.__manifest

    def _open(self, token: object, capsule_digest: str) -> tuple[CreditObservation, ...]:
        if token is not _CREDIT_OPEN_TOKEN:
            raise PermissionError("credit source may be opened only by the A3 credit binder")
        if capsule_digest != self.__capsule_digest:
            raise ValueError("credit source/capsule digest binding failed")
        self.__content_open_count += 1
        if (
            self.__digest != self._computed_digest()
            or _digest(self.__encoded_content) != self.__opaque_content_digest
        ):
            raise ValueError("sealed credit source digest mismatch")
        self.__content_decode_count += 1
        try:
            payload = json.loads(self.__encoded_content.decode("utf-8"))
            if (
                payload.get("schema")
                != "recct-a3.credit-observation-content.v1"
                or not isinstance(payload.get("observations"), list)
            ):
                raise ValueError("encoded credit observation content schema failed")
            rows = tuple(
                CreditObservation(
                    half=str(item["half"]),
                    state=str(item["state"]),
                    detached_predictions=tuple(
                        float(value) for value in item["detached_predictions"]
                    ),
                    observed_four_step_team_rewards=tuple(
                        float(value)
                        for value in item["observed_four_step_team_rewards"]
                    ),
                )
                for item in payload["observations"]
            )
        except Exception as exc:
            raise ValueError("encoded credit observation content decode failed") from exc
        for row in rows:
            row.validate()
        keys = tuple((row.half, row.state) for row in rows)
        if (
            keys != credit_observation_order()
            or len(set(keys)) != len(keys)
            or len(rows) != self.__manifest.observation_count
            or _digest(_canonical_json(keys)) != self.__manifest.ordered_key_digest
        ):
            raise ValueError("decoded credit observation order/count failed")
        return rows

    def _computed_digest(self) -> str:
        return _digest(
            _canonical_json(
                {
                    "capsule_digest": self.__capsule_digest,
                    "proposal_epochs": PROPOSAL_EPOCHS,
                    "confirmation_halves": CONFIRMATION_HALVES,
                    "opaque_content_digest": self.__opaque_content_digest,
                    "lineage": self.__lineage,
                }
            )
        )


@dataclass(frozen=True)
class OrientationCapsule:
    orientation: str
    member_id: str
    capsule_id: str
    learner: a1.DirectedEdgeMaskedLearner
    capsule: a1.SealedLearnerCapsule
    lr_handle: a1.OpaqueDirectedHandle
    rl_handle: a1.OpaqueDirectedHandle
    lr_role: tuple[str, str]
    rl_role: tuple[str, str]
    role_instances: tuple[tuple[str, str], tuple[str, str]]
    credit_source: SealedCreditSource

    def structural_validate(
        self, manifest: CreditSourceManifest | None = None
    ) -> None:
        manifest = manifest or self.credit_source.inspect_manifest()
        if (
            self.orientation not in ORIENTATIONS
            or not self.member_id
            or not self.capsule_id
            or self.lr_handle is self.rl_handle
            or self.capsule.digest != manifest.capsule_digest
            or manifest.schema != "recct-a3.credit-source-manifest.v1"
            or manifest.observation_count != 8
            or not manifest.opaque_content_digest
            or not manifest.lineage_digest
            or self.capsule._owner() is not self.learner
            or self.lr_role != tuple(reversed(self.rl_role))
            or tuple(role for role, _ in self.role_instances) != ("LEFT", "RIGHT")
            or len({instance for _, instance in self.role_instances}) != 2
        ):
            raise ValueError("orientation capsule structural prerequisites failed")


@dataclass(frozen=True)
class ProspectiveOrientationPair:
    frame_id: str
    plus: OrientationCapsule
    minus: OrientationCapsule

    @property
    def ordering_key(self) -> tuple[str, str, str, str, str]:
        members = sorted((self.plus.member_id, self.minus.member_id))
        return (
            self.frame_id,
            members[0],
            members[1],
            self.plus.capsule_id,
            self.minus.capsule_id,
        )

    def structural_validate(
        self,
        manifests: tuple[CreditSourceManifest, CreditSourceManifest] | None = None,
    ) -> None:
        if manifests is None:
            manifests = (
                self.plus.credit_source.inspect_manifest(),
                self.minus.credit_source.inspect_manifest(),
            )
        self.plus.structural_validate(manifests[0])
        self.minus.structural_validate(manifests[1])
        if (
            not self.frame_id
            or self.plus.orientation != "PLUS"
            or self.minus.orientation != "MINUS"
            or self.plus.capsule.digest == self.minus.capsule.digest
            or self.plus.lr_role != self.minus.rl_role
            or self.plus.rl_role != self.minus.lr_role
        ):
            raise ValueError("orientation pair involution or distinct-capsule binding failed")


@dataclass(frozen=True)
class PairSelectionReceipt:
    ordering_keys: tuple[tuple[str, str, str, str, str], ...]
    selected_key: tuple[str, str, str, str, str]
    credit_content_open_counts_before_selection: tuple[int, ...]
    credit_content_open_counts_after_selection: tuple[int, ...]
    credit_content_decode_counts_before_selection: tuple[int, ...]
    credit_content_decode_counts_after_selection: tuple[int, ...]
    manifest_access_counts_before_selection: tuple[int, ...]
    manifest_access_counts_after_selection: tuple[int, ...]
    opaque_credit_manifests: tuple[
        tuple[CreditSourceManifest, CreditSourceManifest], ...
    ]
    prohibited_value_reads: int


def select_first_structural_pair(
    candidates: Sequence[ProspectiveOrientationPair],
) -> tuple[ProspectiveOrientationPair, PairSelectionReceipt]:
    """Select lexicographically before any credit or transition value is opened."""

    rows = tuple(candidates)
    if not rows:
        raise ValueError("eligible orientation frame is empty")
    content_before = tuple(
        row.plus.credit_source.content_open_count
        + row.minus.credit_source.content_open_count
        for row in rows
    )
    decode_before = tuple(
        row.plus.credit_source.content_decode_count
        + row.minus.credit_source.content_decode_count
        for row in rows
    )
    manifest_before = tuple(
        row.plus.credit_source.manifest_access_count
        + row.minus.credit_source.manifest_access_count
        for row in rows
    )
    manifests = tuple(
        (
            row.plus.credit_source.inspect_manifest(),
            row.minus.credit_source.inspect_manifest(),
        )
        for row in rows
    )
    for row, manifest_pair in zip(rows, manifests):
        row.structural_validate(manifest_pair)
    ordered = tuple(
        sorted(
            rows,
            key=lambda row: tuple(
                component.encode("utf-8") for component in row.ordering_key
            ),
        )
    )
    content_after = tuple(
        row.plus.credit_source.content_open_count
        + row.minus.credit_source.content_open_count
        for row in rows
    )
    decode_after = tuple(
        row.plus.credit_source.content_decode_count
        + row.minus.credit_source.content_decode_count
        for row in rows
    )
    manifest_after = tuple(
        row.plus.credit_source.manifest_access_count
        + row.minus.credit_source.manifest_access_count
        for row in rows
    )
    reads = sum(
        end - start for start, end in zip(content_before, content_after)
    )
    if reads != 0:
        raise ValueError("prospective selection inspected credit values")
    return ordered[0], PairSelectionReceipt(
        ordering_keys=tuple(row.ordering_key for row in ordered),
        selected_key=ordered[0].ordering_key,
        credit_content_open_counts_before_selection=content_before,
        credit_content_open_counts_after_selection=content_after,
        credit_content_decode_counts_before_selection=decode_before,
        credit_content_decode_counts_after_selection=decode_after,
        manifest_access_counts_before_selection=manifest_before,
        manifest_access_counts_after_selection=manifest_after,
        opaque_credit_manifests=manifests,
        prohibited_value_reads=reads,
    )


@dataclass(frozen=True)
class CreditTensor:
    orientation: str
    lr: tuple[float, float, float, float]
    rl: tuple[float, float, float, float]
    q_rows: tuple[tuple[str, str, float], ...]
    source_digest: str
    proposal_epochs: tuple[int, int, int, int] = PROPOSAL_EPOCHS
    confirmation_halves: tuple[tuple[str, tuple[int, int]], ...] = CONFIRMATION_HALVES
    exact_component_weights: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25)
    formula_order: tuple[str, ...] = (
        "LR:q10A-q00A",
        "LR:q11A-q01A",
        "LR:q10B-q00B",
        "LR:q11B-q01B",
        "RL:q01A-q00A",
        "RL:q11A-q10A",
        "RL:q01B-q00B",
        "RL:q11B-q10B",
    )

    @property
    def digest(self) -> str:
        return _digest(_canonical_json(self))


def _negative_bce(observation: CreditObservation) -> float:
    values = []
    for prediction, target in zip(
        observation.detached_predictions,
        observation.observed_four_step_team_rewards,
    ):
        p = float(prediction)
        y = float(target)
        values.append(y * math.log(p) + (1.0 - y) * math.log1p(-p))
    result = sum(values) / 4.0
    if not math.isfinite(result):
        raise ValueError("nonfinite detached negative-BCE credit")
    return result


def bind_credit_tensor(row: OrientationCapsule) -> CreditTensor:
    observations = row.credit_source._open(_CREDIT_OPEN_TOKEN, row.capsule.digest)
    q = {(item.half, item.state): _negative_bce(item) for item in observations}
    if len(q) != 8:
        raise ValueError("missing or duplicated q entry")
    lr = (
        q[("A", "10")] - q[("A", "00")],
        q[("A", "11")] - q[("A", "01")],
        q[("B", "10")] - q[("B", "00")],
        q[("B", "11")] - q[("B", "01")],
    )
    rl = (
        q[("A", "01")] - q[("A", "00")],
        q[("A", "11")] - q[("A", "10")],
        q[("B", "01")] - q[("B", "00")],
        q[("B", "11")] - q[("B", "10")],
    )
    if not all(math.isfinite(value) for value in lr + rl):
        raise ValueError("nonfinite credit tensor")
    return CreditTensor(
        orientation=row.orientation,
        lr=lr,
        rl=rl,
        q_rows=tuple((half, state, q[(half, state)]) for half in ("A", "B") for state in SHADOW_STATES),
        source_digest=row.credit_source.digest,
    )


class SelectorViewProtocol(Protocol):
    @property
    def lr(self) -> tuple[float, float, float, float]: ...

    @property
    def rl(self) -> tuple[float, float, float, float]: ...

    @property
    def tie(self) -> str: ...


@dataclass(frozen=True)
class SelectorView:
    lr: tuple[float, float, float, float]
    rl: tuple[float, float, float, float]
    tie: str

    def validate(self) -> None:
        if (
            len(self.lr) != 4
            or len(self.rl) != 4
            or self.tie not in PORTS
            or not all(math.isfinite(value) for value in self.lr + self.rl)
        ):
            raise ValueError("selector view is incomplete or nonfinite")


def _argmax(left: float, right: float, tie: str) -> str:
    if left > right:
        return "LR"
    if right > left:
        return "RL"
    return tie


def signed_directed(view: SelectorViewProtocol) -> str:
    return _argmax(sum(view.lr) / 4.0, sum(view.rl) / 4.0, view.tie)


def sign_destroyed(view: SelectorViewProtocol) -> str:
    return _argmax(
        sum(abs(value) for value in view.lr) / 4.0,
        sum(abs(value) for value in view.rl) / 4.0,
        view.tie,
    )


def balanced_direction_blind(view: SelectorViewProtocol) -> str:
    return view.tie


SELECTOR_FUNCTIONS: Mapping[str, Callable[[SelectorViewProtocol], str]] = MappingProxyType(
    {
        "SIGNED_DIRECTED": signed_directed,
        "SIGN_DESTROYED": sign_destroyed,
        "BALANCED_DIRECTION_BLIND": balanced_direction_blind,
    }
)


class AccessTrapSelectorView:
    """Auditable selector view that raises on every undeclared field."""

    __slots__ = (
        "_lr",
        "_rl",
        "_tie",
        "_forbidden_payload",
        "accesses",
        "forbidden_attempts",
    )

    def __init__(
        self,
        lr: tuple[float, float, float, float],
        rl: tuple[float, float, float, float],
        tie: str,
        forbidden_payload: Sequence[tuple[str, str]] = (),
    ) -> None:
        object.__setattr__(self, "_lr", lr)
        object.__setattr__(self, "_rl", rl)
        object.__setattr__(self, "_tie", tie)
        object.__setattr__(self, "_forbidden_payload", tuple(forbidden_payload))
        object.__setattr__(self, "accesses", [])
        object.__setattr__(self, "forbidden_attempts", [])

    @property
    def lr(self) -> tuple[float, float, float, float]:
        self.accesses.append("lr")
        return self._lr

    @property
    def rl(self) -> tuple[float, float, float, float]:
        self.accesses.append("rl")
        return self._rl

    @property
    def tie(self) -> str:
        self.accesses.append("tie")
        return self._tie

    def __getattr__(self, name: str) -> object:
        self.forbidden_attempts.append(name)
        raise PermissionError(f"selector attempted forbidden field: {name}")


@dataclass(frozen=True)
class CellLedger:
    orientation: str
    port: str
    mask: str
    active_port_count: int
    authenticated_opaque_handle: str
    capsule_digest: str
    batch_digest: str
    roster: tuple[tuple[str, int], ...]
    configuration: Mapping[str, object]
    rng_lineage: Mapping[str, object]
    before_state: Mapping[str, object]
    preclip_gradient_tree: tuple[Mapping[str, object], ...]
    global_norm: float
    clip_threshold: None
    clip_coefficient: float
    clip_event: bool
    postclip_gradient_tree: tuple[Mapping[str, object], ...]
    optimizer_hyperparameters: Mapping[str, object]
    after_state: Mapping[str, object]
    parameter_delta: tuple[Mapping[str, object], ...]
    original_capsule_digest_before: str
    original_capsule_digest_after: str
    call_kind: str
    call_lineage: str
    finite: bool
    stored_or_recomputed: str

    def to_dict(self) -> dict[str, object]:
        return _jsonable(self)  # type: ignore[return-value]


def _tensor_ledger(value: a1.TensorValue) -> Mapping[str, object]:
    tensor = value.tensor()
    return MappingProxyType(
        {
            "name": value.name,
            "entry_kind": "DENSE",
            "dtype": value.dtype,
            "shape": value.shape,
            "data_base64": value.data_base64,
            "finite": bool(torch.isfinite(tensor).all()),
        }
    )


def _global_norm(values: Sequence[a1.TensorValue]) -> float:
    squared = sum(float(torch.sum(row.tensor().double().square())) for row in values)
    return math.sqrt(squared)


def _receipt_to_ledger(
    orientation: OrientationCapsule,
    port: str,
    receipt: a1.UpdateReceipt,
    *,
    stored_or_recomputed: str,
) -> CellLedger:
    mask = "10" if port == "LR" else "01"
    active_handle = orientation.lr_handle if port == "LR" else orientation.rl_handle
    gradients = tuple(_tensor_ledger(row) for row in receipt.gradient)
    if not gradients or any(not bool(row["finite"]) for row in gradients):
        raise ValueError("preclip gradient tree is incomplete or nonfinite")
    manifest = orientation.capsule.manifest
    config = asdict(manifest.learner_config)
    return CellLedger(
        orientation=orientation.orientation,
        port=port,
        mask=mask,
        active_port_count=len(receipt.intervention.enabled_ports),
        authenticated_opaque_handle=active_handle.opaque_id,
        capsule_digest=orientation.capsule.digest,
        batch_digest=receipt.ancestry.pretreatment_batch_digest,
        roster=tuple((row.instance_id, row.slot) for row in manifest.roster),
        configuration=MappingProxyType(config),
        rng_lineage=MappingProxyType(
            {
                "plan_digest": receipt.ancestry.rng_plan_digest,
                "clone_id": receipt.ancestry.rng_clone_id,
                "counters_before": receipt.ancestry.rng_counters_before,
                "counters_after": receipt.ancestry.rng_counters_after,
            }
        ),
        before_state=MappingProxyType(receipt.before.__dict__),
        preclip_gradient_tree=gradients,
        global_norm=_global_norm(receipt.gradient),
        clip_threshold=None,
        clip_coefficient=1.0,
        clip_event=False,
        postclip_gradient_tree=gradients,
        optimizer_hyperparameters=MappingProxyType(config),
        after_state=MappingProxyType(receipt.after.__dict__),
        parameter_delta=tuple(_tensor_ledger(row) for row in receipt.parameter_delta),
        original_capsule_digest_before=orientation.capsule.digest,
        original_capsule_digest_after=orientation.capsule.digest,
        call_kind=receipt.call_kind,
        call_lineage=receipt.call_lineage,
        finite=receipt.finite,
        stored_or_recomputed=stored_or_recomputed,
    )


def _authenticated_orientation_binding(
    orientation: OrientationCapsule,
) -> Mapping[str, object]:
    """Narrow learner-owner adapter: authenticate handles, never capsule bytes."""

    orientation.learner._validate_registry(orientation.capsule)
    lr = orientation.learner._record_for(
        orientation.capsule, orientation.lr_handle
    )
    rl = orientation.learner._record_for(
        orientation.capsule, orientation.rl_handle
    )
    role_instances = dict(orientation.role_instances)
    expected_roles = {
        "PLUS": (("LEFT", "RIGHT"), ("RIGHT", "LEFT")),
        "MINUS": (("RIGHT", "LEFT"), ("LEFT", "RIGHT")),
    }[orientation.orientation]
    lr_expected_instances = tuple(role_instances[role] for role in orientation.lr_role)
    rl_expected_instances = tuple(role_instances[role] for role in orientation.rl_role)
    if not (
        (orientation.lr_role, orientation.rl_role) == expected_roles
        and (lr.source_instance, lr.receiver_instance) == lr_expected_instances
        and (rl.source_instance, rl.receiver_instance) == rl_expected_instances
        and lr.source_instance == rl.receiver_instance
        and lr.receiver_instance == rl.source_instance
        and lr.capsule_digest == rl.capsule_digest == orientation.capsule.digest
        and lr.roster_epoch == rl.roster_epoch
        == orientation.capsule.manifest.ancestry.roster_epoch
        and lr.payload_schema == rl.payload_schema == a1.PORT_PAYLOAD_SCHEMA
        and lr.mint_provenance == rl.mint_provenance == a1.MINT_PROVENANCE
        and lr.port_id == orientation.lr_handle.opaque_id
        and rl.port_id == orientation.rl_handle.opaque_id
    ):
        raise ValueError("A1 authenticated opposite-port role binding failed")
    return MappingProxyType(
        {
            "orientation": orientation.orientation,
            "capsule_digest": orientation.capsule.digest,
            "roster_epoch": lr.roster_epoch,
            "lr_opaque_handle": orientation.lr_handle.opaque_id,
            "rl_opaque_handle": orientation.rl_handle.opaque_id,
            "lr_source_instance": lr.source_instance,
            "lr_receiver_instance": lr.receiver_instance,
            "rl_source_instance": rl.source_instance,
            "rl_receiver_instance": rl.receiver_instance,
            "role_instances": orientation.role_instances,
            "lr_structural_role": orientation.lr_role,
            "rl_structural_role": orientation.rl_role,
            "coordinated_role_swap_rejected": True,
            "payload_schema": lr.payload_schema,
            "mint_provenance": lr.mint_provenance,
            "owner_authenticated_without_private_payload_access": True,
        }
    )


@dataclass(frozen=True)
class PotentialCell:
    orientation: str
    port: str
    receipt: a1.UpdateReceipt
    ledger: CellLedger

    @property
    def comparison_payload(self) -> tuple[object, ...]:
        return self.receipt.transition_predicate()

    @property
    def digest(self) -> str:
        return _digest(_canonical_json(self.comparison_payload))


class HiddenImmutableBank:
    __slots__ = ("__cells", "__digest")

    def __init__(self, cells: Mapping[tuple[str, str], PotentialCell]) -> None:
        expected = {(orientation, port) for orientation in ORIENTATIONS for port in PORTS}
        if set(cells) != expected:
            raise ValueError("hidden bank requires the exact four cells")
        self.__cells = MappingProxyType(dict(cells))
        self.__digest = _digest(
            _canonical_json(
                tuple(
                    (orientation, port, self.__cells[(orientation, port)].digest)
                    for orientation in ORIENTATIONS
                    for port in PORTS
                )
            )
        )

    @property
    def digest(self) -> str:
        return self.__digest

    def resolve(self, orientation: str, pointer: str) -> str:
        if orientation not in ORIENTATIONS or pointer not in PORTS:
            raise ValueError("bank pointer is outside the sealed four-cell bank")
        return self.__cells[(orientation, pointer)].digest


@dataclass(frozen=True)
class SelectorRecord:
    selector: str
    orientation: str
    pointer: str
    visible_input_digest: str
    access_log: tuple[str, ...]
    forbidden_read_attempts: tuple[str, ...]
    outer_bank_digest: str
    selected_cell_digest: str


def _invoke_selector(
    selector: str,
    orientation: str,
    tensor: CreditTensor,
    bank: HiddenImmutableBank,
) -> SelectorRecord:
    view = AccessTrapSelectorView(tensor.lr, tensor.rl, TIE_VALUE)
    pointer = SELECTOR_FUNCTIONS[selector](view)
    if pointer not in PORTS or view.forbidden_attempts:
        raise ValueError("selector returned an invalid pointer or read a forbidden field")
    if selector == "BALANCED_DIRECTION_BLIND" and tuple(view.accesses) != ("tie",):
        raise ValueError("balanced selector read credit")
    visible_digest = _digest(_canonical_json((tensor.lr, tensor.rl, TIE_VALUE)))
    return SelectorRecord(
        selector=selector,
        orientation=orientation,
        pointer=pointer,
        visible_input_digest=visible_digest,
        access_log=tuple(view.accesses),
        forbidden_read_attempts=tuple(view.forbidden_attempts),
        outer_bank_digest=bank.digest,
        selected_cell_digest=bank.resolve(orientation, pointer),
    )


@dataclass(frozen=True)
class SentinelCase:
    case_id: str
    lr: tuple[float, float, float, float]
    rl: tuple[float, float, float, float]
    tie: str
    expected_signed: str
    expected_destroyed: str
    expected_balanced: str
    access_trap: bool = False
    forbidden_payload: tuple[tuple[str, str], ...] = ()


SENTINEL_CASES = (
    SentinelCase("S01_BASE", (4.0, 2.0, -1.0, 1.0), (1.0, 0.0, 1.0, 0.0), "LR", "LR", "LR", "LR"),
    SentinelCase("S02_GLOBAL_NEGATION", (-4.0, -2.0, 1.0, -1.0), (-1.0, -0.0, -1.0, -0.0), "LR", "RL", "LR", "LR"),
    SentinelCase("S03_MIXED_SIGN", (-4.0, 2.0, 1.0, -1.0), (-1.0, 0.0, -1.0, 0.0), "LR", "LR", "LR", "LR"),
    SentinelCase("S04_CANDIDATE_SWAP", (1.0, 0.0, 1.0, 0.0), (4.0, 2.0, -1.0, 1.0), "LR", "RL", "RL", "LR"),
    SentinelCase("S05_BOTH_TIE_LR", (1.0, -1.0, 1.0, -1.0), (-1.0, 1.0, -1.0, 1.0), "LR", "LR", "LR", "LR"),
    SentinelCase("S06_BOTH_TIE_RL", (1.0, -1.0, 1.0, -1.0), (-1.0, 1.0, -1.0, 1.0), "RL", "RL", "RL", "RL"),
    SentinelCase("S07_SIGNED_TIE_LR", (2.0, -1.0, 2.0, -1.0), (0.5, 0.5, 0.5, 0.5), "LR", "LR", "LR", "LR"),
    SentinelCase("S08_SIGNED_TIE_RL", (2.0, -1.0, 2.0, -1.0), (0.5, 0.5, 0.5, 0.5), "RL", "RL", "LR", "RL"),
    SentinelCase("S09_ABSOLUTE_TIE_LR", (2.0, 2.0, 2.0, 2.0), (-2.0, -2.0, -2.0, -2.0), "LR", "LR", "LR", "LR"),
    SentinelCase("S10_ABSOLUTE_TIE_RL", (2.0, 2.0, 2.0, 2.0), (-2.0, -2.0, -2.0, -2.0), "RL", "LR", "RL", "RL"),
    SentinelCase("S11_ACCESS_TRAP_ONE", (3.0, 1.0, -1.0, 1.0), (0.0, 0.0, 0.0, 0.0), "LR", "LR", "LR", "LR", True, (("bank_digest", "forbidden-a"), ("orientation", "forbidden-plus"))),
    SentinelCase("S12_ACCESS_TRAP_TWO", (-1.0, -1.0, -1.0, -1.0), (1.0, 1.0, 1.0, 1.0), "LR", "RL", "LR", "LR", True, (("bank_digest", "forbidden-b"), ("orientation", "forbidden-minus"))),
)


@dataclass(frozen=True)
class SentinelRecord:
    case_id: str
    selector: str
    output: str
    expected: str
    access_log: tuple[str, ...]
    forbidden_read_attempts: tuple[str, ...]
    forbidden_payload_digest: str | None
    passed: bool


def run_sentinel_manifest() -> tuple[SentinelRecord, ...]:
    records: list[SentinelRecord] = []
    expected_key = {
        "SIGNED_DIRECTED": "expected_signed",
        "SIGN_DESTROYED": "expected_destroyed",
        "BALANCED_DIRECTION_BLIND": "expected_balanced",
    }
    for case in SENTINEL_CASES:
        for selector in SELECTORS:
            view = AccessTrapSelectorView(
                case.lr, case.rl, case.tie, case.forbidden_payload
            )
            output = SELECTOR_FUNCTIONS[selector](view)
            expected = str(getattr(case, expected_key[selector]))
            permitted = {"tie"} if selector == "BALANCED_DIRECTION_BLIND" else {"lr", "rl", "tie"}
            passed = bool(
                output == expected
                and not view.forbidden_attempts
                and set(view.accesses) <= permitted
                and (selector != "BALANCED_DIRECTION_BLIND" or tuple(view.accesses) == ("tie",))
            )
            records.append(
                SentinelRecord(
                    case.case_id,
                    selector,
                    output,
                    expected,
                    tuple(view.accesses),
                    tuple(view.forbidden_attempts),
                    _digest(_canonical_json(case.forbidden_payload))
                    if case.access_trap
                    else None,
                    passed,
                )
            )
    if len(records) != 36:
        raise ValueError("sentinel manifest did not perform exactly 36 calls")
    return tuple(records)


@dataclass(frozen=True)
class A3Result:
    schema_version: int
    treatment_id: str
    target_version_id: str
    raw_output_binding: str
    branch: str
    first_failure: str | None
    a1_binding: Mapping[str, object]
    pair_selection: Mapping[str, object]
    orientation_involution: Mapping[str, object]
    credits: tuple[Mapping[str, object], ...]
    call_ledgers: tuple[Mapping[str, object], ...]
    cell_equalities: tuple[Mapping[str, object], ...]
    bank: Mapping[str, object]
    selector_records: tuple[Mapping[str, object], ...]
    reverse_selector_records: tuple[Mapping[str, object], ...]
    sentinel_records: tuple[Mapping[str, object], ...]
    activity_events: tuple[Mapping[str, object], ...]
    checks: Mapping[str, bool]
    counts: Mapping[str, int]
    strongest_technical_limitation: str

    def to_dict(self) -> dict[str, object]:
        return _jsonable(self)  # type: ignore[return-value]

    def to_bytes(self) -> bytes:
        return _canonical_json(self.to_dict())


def _derive_counts(
    *,
    pair_selection: Mapping[str, object],
    call_ledgers: Sequence[Mapping[str, object]],
    cell_equalities: Sequence[Mapping[str, object]],
    selector_records: Sequence[Mapping[str, object]],
    reverse_selector_records: Sequence[Mapping[str, object]],
    sentinel_records: Sequence[Mapping[str, object]],
    activity_events: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    events = tuple(activity_events)
    shadow_attempts = tuple(row for row in events if row.get("event") == "SHADOW_CALL")
    counts = {key: 0 for key in EXPECTED_CAPS}
    counts.update(
        {
            "named_audits": sum(row.get("event") == "AUDIT_STARTED" for row in events),
            "sealed_orientation_pairs": int(bool(pair_selection.get("selected_key"))),
            "sealed_orientation_capsules": sum(
                row.get("event") == "CAPSULE_BOUND" for row in events
            ),
            "stored_cell_construction_calls": sum(
                row.get("phase") == "STORED" for row in shadow_attempts
            ),
            "independent_cell_recomputation_calls": sum(
                row.get("phase") == "RECOMPUTED" for row in shadow_attempts
            ),
            "learner_backward_shadow_calls": len(shadow_attempts),
            "optimizer_transition_shadow_calls": sum(
                int(row.get("optimizer_transitions_observed", 0))
                for row in shadow_attempts
            ),
            "verified_stored_cells": sum(
                bool(row.get("componentwise_bitwise_equal")) for row in cell_equalities
            ),
            "real_selector_commitments": len(selector_records),
            "pure_selector_sentinel_calls": len(sentinel_records),
        }
    )
    counts["reverse_selector_verification_calls"] = len(reverse_selector_records)
    counts["credit_source_open_calls"] = sum(
        row.get("event") == "CREDIT_SOURCE_OPENED" for row in events
    )
    counts["selector_forbidden_field_reads"] = sum(
        len(tuple(row.get("forbidden_read_attempts", ())))
        for row in tuple(selector_records) + tuple(reverse_selector_records)
    )
    counts["00_or_11_shadow_calls"] = sum(
        row.get("mask") in {"00", "11"} for row in shadow_attempts
    )
    counts["indeterminate_optimizer_transition_attempts"] = sum(
        row.get("status") == "FAILED_INDETERMINATE" for row in shadow_attempts
    )
    return counts


def _assemble_result(
    branch: str,
    first_failure: str | None,
    *,
    a1_binding: Mapping[str, object] = MappingProxyType({}),
    pair_selection: Mapping[str, object] = MappingProxyType({}),
    orientation_involution: Mapping[str, object] = MappingProxyType({}),
    credits: Sequence[Mapping[str, object]] = (),
    call_ledgers: Sequence[Mapping[str, object]] = (),
    cell_equalities: Sequence[Mapping[str, object]] = (),
    bank: Mapping[str, object] = MappingProxyType({}),
    selector_records: Sequence[Mapping[str, object]] = (),
    reverse_selector_records: Sequence[Mapping[str, object]] = (),
    sentinel_records: Sequence[Mapping[str, object]] = (),
    activity_events: Sequence[Mapping[str, object]] = (),
    checks: Mapping[str, bool] = MappingProxyType({}),
    strongest_technical_limitation: str | None = None,
) -> A3Result:
    call_rows = tuple(call_ledgers)
    equality_rows = tuple(cell_equalities)
    selector_rows = tuple(selector_records)
    reverse_rows = tuple(reverse_selector_records)
    sentinel_rows = tuple(sentinel_records)
    event_rows = tuple(activity_events)
    counts = _derive_counts(
        pair_selection=pair_selection,
        call_ledgers=call_rows,
        cell_equalities=equality_rows,
        selector_records=selector_rows,
        reverse_selector_records=reverse_rows,
        sentinel_records=sentinel_rows,
        activity_events=event_rows,
    )
    return A3Result(
        SCHEMA_VERSION,
        TREATMENT_ID,
        TARGET_VERSION_ID,
        RAW_OUTPUT_BINDING,
        branch,
        first_failure,
        a1_binding,
        pair_selection,
        orientation_involution,
        tuple(credits),
        call_rows,
        equality_rows,
        bank,
        selector_rows,
        reverse_rows,
        sentinel_rows,
        event_rows,
        checks,
        MappingProxyType(counts),
        strongest_technical_limitation
        or "No construction claim is available because the audit failed before completing its frozen branch checks.",
    )


def _empty_result(branch: str, first_failure: str) -> A3Result:
    return _assemble_result(
        branch,
        first_failure,
        activity_events=(MappingProxyType({"event": "AUDIT_STARTED"}),),
    )


def make_failure_result(branch: str, first_failure: str) -> A3Result:
    """Build a schema-valid pre/computation failure without claim-bearing calls."""

    if branch not in BRANCH_PRECEDENCE[:-1] or not first_failure:
        raise ValueError("failure result requires one frozen non-pass branch and cause")
    return _empty_result(branch, first_failure)


def run_common_bank_audit(
    candidates: Sequence[ProspectiveOrientationPair],
    *,
    a1_binding: A1Binding = A1Binding(),
) -> A3Result:
    """Run the unique deterministic A3 audit over one prospective pair."""

    activity_events: list[dict[str, object]] = [{"event": "AUDIT_STARTED"}]
    a1_evidence: Mapping[str, object] = MappingProxyType({})
    selection_evidence: Mapping[str, object] = MappingProxyType({})
    involution_evidence: Mapping[str, object] = MappingProxyType({})
    credit_evidence: list[Mapping[str, object]] = []
    completed_cells: list[PotentialCell] = []
    equality_evidence: list[Mapping[str, object]] = []
    bank_evidence: Mapping[str, object] = MappingProxyType({})
    selector_evidence: list[Mapping[str, object]] = []
    reverse_selector_evidence: list[Mapping[str, object]] = []
    sentinel_evidence: list[Mapping[str, object]] = []
    check_evidence: Mapping[str, bool] = MappingProxyType({})

    def fail(branch: str, message: str) -> A3Result:
        return _assemble_result(
            branch,
            message,
            a1_binding=a1_evidence,
            pair_selection=selection_evidence,
            orientation_involution=involution_evidence,
            credits=credit_evidence,
            call_ledgers=tuple(
                MappingProxyType(cell.ledger.to_dict()) for cell in completed_cells
            ),
            cell_equalities=equality_evidence,
            bank=bank_evidence,
            selector_records=selector_evidence,
            reverse_selector_records=reverse_selector_evidence,
            sentinel_records=sentinel_evidence,
            activity_events=tuple(MappingProxyType(row) for row in activity_events),
            checks=check_evidence,
        )

    try:
        a1_binding.validate()
    except Exception as exc:
        return fail(
            A3_A1_AUTHENTICATED_PORT_VERSION_ROLE_OR_MASK_BINDING_FAILURE,
            str(exc),
        )
    a1_evidence = MappingProxyType(_jsonable(a1_binding))  # type: ignore[arg-type]
    try:
        pair, selection = select_first_structural_pair(candidates)
    except Exception as exc:
        return fail(
            A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE,
            str(exc),
        )
    selection_evidence = MappingProxyType(_jsonable(selection))  # type: ignore[arg-type]
    activity_events.extend(
        (
            {
                "event": "PAIR_FROZEN",
                "selected_key": selection.selected_key,
                "credit_content_decode_counts": (
                    pair.plus.credit_source.content_decode_count,
                    pair.minus.credit_source.content_decode_count,
                ),
            },
            {"event": "CAPSULE_BOUND", "orientation": "PLUS", "capsule_digest": pair.plus.capsule.digest},
            {"event": "CAPSULE_BOUND", "orientation": "MINUS", "capsule_digest": pair.minus.capsule.digest},
        )
    )

    credits: dict[str, CreditTensor] = {}
    for orientation_name, orientation in (("PLUS", pair.plus), ("MINUS", pair.minus)):
        event = {
            "event": "CREDIT_SOURCE_OPENED",
            "orientation": orientation_name,
            "status": "STARTED",
        }
        activity_events.append(event)
        try:
            credit = bind_credit_tensor(orientation)
        except Exception as exc:
            event["status"] = "FAILED"
            return fail(
                A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE,
                str(exc),
            )
        event["status"] = "COMPLETED"
        event["source_digest"] = credit.source_digest
        credits[orientation_name] = credit
        credit_evidence.append(
            MappingProxyType(_jsonable(credit))  # type: ignore[arg-type]
        )

    try:
        authenticated_bindings = tuple(
            _authenticated_orientation_binding(row)
            for row in (pair.plus, pair.minus)
        )
    except Exception as exc:
        return fail(
            A3_A1_AUTHENTICATED_PORT_VERSION_ROLE_OR_MASK_BINDING_FAILURE,
            str(exc),
        )
    a1_evidence = MappingProxyType(
        {
            **_jsonable(a1_binding),  # type: ignore[misc]
            "authenticated_orientation_bindings": _jsonable(authenticated_bindings),
        }
    )

    orientations = {"PLUS": pair.plus, "MINUS": pair.minus}
    stored_order = (("PLUS", "LR"), ("PLUS", "RL"), ("MINUS", "LR"), ("MINUS", "RL"))
    recompute_order = tuple(reversed(stored_order))
    stored: dict[tuple[str, str], PotentialCell] = {}
    recomputed: dict[tuple[str, str], PotentialCell] = {}
    all_clone_ids: list[str] = []

    def execute_cell(
        orientation_name: str,
        port: str,
        phase: str,
    ) -> PotentialCell:
        orientation = orientations[orientation_name]
        mask = "10" if port == "LR" else "01"
        event: dict[str, object] = {
            "event": "SHADOW_CALL",
            "attempt_index": sum(
                row.get("event") == "SHADOW_CALL" for row in activity_events
            )
            + 1,
            "phase": phase,
            "orientation": orientation_name,
            "port": port,
            "mask": mask,
            "status": "STARTED",
            "optimizer_transitions_observed": 0,
        }
        activity_events.append(event)
        try:
            rng = orientation.learner.clone_counterfactual_rng(orientation.capsule)
            receipt = a1.DirectedEdgeMaskedUpdate(
                orientation.capsule,
                (orientation.lr_handle, orientation.rl_handle),
                mask,
                rng,
            )
        except Exception:
            event["status"] = "FAILED_INDETERMINATE"
            raise
        event["status"] = "COMPLETED"
        event["optimizer_transitions_observed"] = receipt.optimizer_transitions
        event["call_lineage"] = receipt.call_lineage
        all_clone_ids.append(receipt.ancestry.rng_clone_id)
        try:
            cell = PotentialCell(
                orientation_name,
                port,
                receipt,
                _receipt_to_ledger(
                    orientation,
                    port,
                    receipt,
                    stored_or_recomputed=phase,
                ),
            )
        except Exception:
            event["status"] = "RECEIPT_COMPLETED_LEDGER_FAILED"
            raise
        completed_cells.append(cell)
        return cell

    try:
        for orientation_name, port in stored_order:
            stored[(orientation_name, port)] = execute_cell(
                orientation_name, port, "STORED"
            )
        for orientation_name, port in recompute_order:
            recomputed[(orientation_name, port)] = execute_cell(
                orientation_name, port, "RECOMPUTED"
            )
    except Exception as exc:
        return fail(
            A3_BANK_COMPONENTWISE_RECOMPUTATION_IMMUTABILITY_OR_CALL_LEDGER_FAILURE,
            str(exc),
        )

    try:
        equalities = tuple(
            {
                "orientation": orientation,
                "port": port,
                "stored_digest": stored[(orientation, port)].digest,
                "recomputed_digest": recomputed[(orientation, port)].digest,
                "componentwise_bitwise_equal": stored[(orientation, port)].comparison_payload
                == recomputed[(orientation, port)].comparison_payload,
            }
            for orientation, port in stored_order
        )
        equality_evidence.extend(MappingProxyType(row) for row in equalities)
        rng_isolated = bool(
            len(set(all_clone_ids)) == 8
            and all(
                cell.receipt.ancestry.rng_counters_before
                == cell.receipt.ancestry.rng_counters_after
                for cell in tuple(stored.values()) + tuple(recomputed.values())
            )
        )
        common_ancestry = all(
            stored[(orientation, "LR")].receipt.before
            == stored[(orientation, "RL")].receipt.before
            for orientation in ORIENTATIONS
        )
        masks_valid = all(
            cell.receipt.mask == ("10" if port == "LR" else "01")
            and cell.receipt.intervention.enabled_ports
            == ((orientations[orientation].lr_handle if port == "LR" else orientations[orientation].rl_handle).opaque_id,)
            and len(cell.receipt.intervention.enabled_ports) == 1
            and not cell.receipt.ordinary_update_path
            and cell.receipt.optimizer_transitions == 1
            for (orientation, port), cell in {**stored, **recomputed}.items()
        )
        capsule_immutable = all(
            cell.ledger.original_capsule_digest_before
            == cell.ledger.original_capsule_digest_after
            == orientations[cell.orientation].capsule.digest
            for cell in tuple(stored.values()) + tuple(recomputed.values())
        )
        ledger_complete = all(
            cell.ledger.finite
            and cell.ledger.active_port_count == 1
            and cell.ledger.preclip_gradient_tree
            and cell.ledger.postclip_gradient_tree == cell.ledger.preclip_gradient_tree
            and cell.ledger.clip_threshold is None
            and cell.ledger.clip_coefficient == 1.0
            and not cell.ledger.clip_event
            for cell in tuple(stored.values()) + tuple(recomputed.values())
        )
        if not all(row["componentwise_bitwise_equal"] for row in equalities):
            raise ValueError("stored/recomputed componentwise equality failed")
        if not masks_valid:
            return fail(
                A3_A1_AUTHENTICATED_PORT_VERSION_ROLE_OR_MASK_BINDING_FAILURE,
                "A1 authenticated 10/01 one-port receipt binding failed",
            )
        if not (rng_isolated and common_ancestry):
            return fail(
                A3_COMMON_PRETREATMENT_ANCESTRY_CARDINALITY_OR_RNG_ISOLATION_FAILURE,
                "common pretreatment ancestry/cardinality or RNG isolation failed",
            )
        if not (capsule_immutable and ledger_complete):
            raise ValueError("original-capsule immutability or complete ledger failed")
        bank = HiddenImmutableBank(stored)
        bank_evidence = MappingProxyType(
            {
                "digest": bank.digest,
                "sealed_cell_count": 4,
                "hidden_from_selectors": True,
                "stored_construction_order": stored_order,
                "independent_recomputation_order": recompute_order,
            }
        )
    except Exception as exc:
        return fail(
            A3_BANK_COMPONENTWISE_RECOMPUTATION_IMMUTABILITY_OR_CALL_LEDGER_FAILURE,
            str(exc),
        )

    try:
        bank_digest_before = bank.digest
        selector_records_list: list[SelectorRecord] = []
        for orientation in ORIENTATIONS:
            for selector in SELECTORS:
                event = {
                    "event": "SELECTOR_COMMITMENT",
                    "orientation": orientation,
                    "selector": selector,
                    "status": "STARTED",
                }
                activity_events.append(event)
                record = _invoke_selector(
                    selector, orientation, credits[orientation], bank
                )
                event["status"] = "COMPLETED"
                event["pointer"] = record.pointer
                selector_records_list.append(record)
                selector_evidence.append(
                    MappingProxyType(_jsonable(record))  # type: ignore[arg-type]
                )
        selector_records = tuple(selector_records_list)
        sentinels = run_sentinel_manifest()
        sentinel_evidence.extend(
            MappingProxyType(_jsonable(record)) for record in sentinels  # type: ignore[arg-type]
        )
        activity_events.extend(
            {
                "event": "PURE_SENTINEL_CALL",
                "case_id": record.case_id,
                "selector": record.selector,
                "status": "COMPLETED",
            }
            for record in sentinels
        )
        reverse_records_list: list[SelectorRecord] = []
        for orientation in reversed(ORIENTATIONS):
            for selector in reversed(SELECTORS):
                event = {
                    "event": "REVERSE_SELECTOR_VERIFICATION",
                    "orientation": orientation,
                    "selector": selector,
                    "status": "STARTED",
                }
                activity_events.append(event)
                record = _invoke_selector(
                    selector, orientation, credits[orientation], bank
                )
                event["status"] = "COMPLETED"
                event["pointer"] = record.pointer
                reverse_records_list.append(record)
                reverse_selector_evidence.append(
                    MappingProxyType(_jsonable(record))  # type: ignore[arg-type]
                )
        reverse_records = tuple(reverse_records_list)
        forward_by_key = {(row.orientation, row.selector): row for row in selector_records}
        reverse_by_key = {(row.orientation, row.selector): row for row in reverse_records}
        reverse_invariant = all(
            forward_by_key[key].pointer == reverse_by_key[key].pointer
            and forward_by_key[key].selected_cell_digest == reverse_by_key[key].selected_cell_digest
            for key in forward_by_key
        )
        selector_firewall = all(not row.forbidden_read_attempts for row in selector_records + reverse_records)
        sentinels_pass = len(sentinels) == 36 and all(row.passed for row in sentinels)
        bank_immutable = bank.digest == bank_digest_before
        bank_evidence = MappingProxyType(
            {
                **dict(bank_evidence),
                "digest_unchanged_after_selectors_sentinels_and_reverse_order": bank_immutable,
            }
        )
        if not (reverse_invariant and selector_firewall and sentinels_pass and bank_immutable):
            raise ValueError("selector formula, sentinel, firewall, or order invariance failed")
    except Exception as exc:
        for row in reversed(activity_events):
            if row.get("status") == "STARTED":
                row["status"] = "FAILED"
                break
        return fail(
            A3_SELECTOR_FORMULA_TIE_SENTINEL_OR_INFORMATION_FIREWALL_FAILURE,
            str(exc),
        )

    involution = {
        "plus_lr_role": pair.plus.lr_role,
        "plus_rl_role": pair.plus.rl_role,
        "minus_lr_role": pair.minus.lr_role,
        "minus_rl_role": pair.minus.rl_role,
        "plus_lr_maps_to_minus_rl": pair.plus.lr_role == pair.minus.rl_role,
        "plus_rl_maps_to_minus_lr": pair.plus.rl_role == pair.minus.lr_role,
        "structural_aligned_cells": (("PLUS", "LR"), ("MINUS", "RL")),
        "pair_tie_value": TIE_VALUE,
        "tie_shared_across_orientations": True,
    }
    involution_evidence = MappingProxyType(involution)
    if not (
        involution["plus_lr_maps_to_minus_rl"]
        and involution["plus_rl_maps_to_minus_lr"]
        and TIE_VALUE == "LR"
    ):
        return fail(
            A3_ORIENTATION_INVOLUTION_OR_BALANCED_SCHEDULE_SPECIFICATION_FAILURE,
            "orientation involution or pair-level tie schedule changed",
        )

    checks = MappingProxyType(
        {
            "prospective_selection_zero_prohibited_reads": selection.prohibited_value_reads == 0,
            "a1_binding_exact": True,
            "opaque_one_port_masks_exact": masks_valid,
            "common_pretreatment_ancestry": common_ancestry,
            "rng_isolation": rng_isolated,
            "stored_recomputed_componentwise_equal": all(row["componentwise_bitwise_equal"] for row in equalities),
            "original_capsules_immutable": capsule_immutable,
            "hidden_bank_immutable": bank_immutable,
            "selector_information_firewall": selector_firewall,
            "sentinel_manifest_exact": sentinels_pass,
            "selector_order_reversal_invariant": reverse_invariant,
            "orientation_involution_exact": True,
        }
    )
    check_evidence = checks
    return _assemble_result(
        A3_FACTORIZED_ONE_PORT_CONSTRUCTION_PASS,
        None,
        a1_binding=a1_evidence,
        pair_selection=selection_evidence,
        orientation_involution=involution_evidence,
        credits=credit_evidence,
        call_ledgers=tuple(
            MappingProxyType(cell.ledger.to_dict()) for cell in completed_cells
        ),
        cell_equalities=equality_evidence,
        bank=bank_evidence,
        selector_records=selector_evidence,
        reverse_selector_records=reverse_selector_evidence,
        sentinel_records=sentinel_evidence,
        activity_events=tuple(MappingProxyType(row) for row in activity_events),
        checks=check_evidence,
        strongest_technical_limitation=(
            "This audit certifies deterministic construction and selector noninterference only for the one finite prospectively selected pair; it supplies no value, learning, signed-credit-validity, or cross-pair evidence."
        ),
    )


def validate_a3_result(result: A3Result) -> None:
    if (
        result.schema_version != SCHEMA_VERSION
        or result.treatment_id != TREATMENT_ID
        or result.target_version_id != TARGET_VERSION_ID
        or result.raw_output_binding != RAW_OUTPUT_BINDING
        or result.branch not in BRANCH_PRECEDENCE
    ):
        raise ValueError("RECCT-A3 result identity or branch schema failed")
    counts = dict(result.counts)
    derived_counts = _derive_counts(
        pair_selection=result.pair_selection,
        call_ledgers=result.call_ledgers,
        cell_equalities=result.cell_equalities,
        selector_records=result.selector_records,
        reverse_selector_records=result.reverse_selector_records,
        sentinel_records=result.sentinel_records,
        activity_events=result.activity_events,
    )
    if counts != derived_counts:
        raise ValueError("RECCT-A3 result counts do not rederive from retained evidence")
    if any(
        key not in counts
        or not isinstance(counts[key], int)
        or counts[key] < 0
        or counts[key] > cap
        for key, cap in EXPECTED_CAPS.items()
    ):
        raise ValueError("RECCT-A3 result count is missing, negative, or above a frozen cap")
    if result.branch == A3_FACTORIZED_ONE_PORT_CONSTRUCTION_PASS:
        if (
            result.first_failure is not None
            or not result.checks
            or not all(result.checks.values())
            or len(result.call_ledgers) != 8
            or len(result.cell_equalities) != 4
            or len(result.selector_records) != 6
            or len(result.reverse_selector_records) != 6
            or len(result.sentinel_records) != 36
            or any(
                counts.get(key) != expected
                for key, expected in EXPECTED_CAPS.items()
            )
            or counts.get("00_or_11_shadow_calls") != 0
        ):
            raise ValueError("RECCT-A3 passing result lacks required complete evidence")
    else:
        completed_shadow_events = sum(
            row.get("event") == "SHADOW_CALL" and row.get("status") == "COMPLETED"
            for row in result.activity_events
        )
        if not result.first_failure:
            raise ValueError("RECCT-A3 failure branch requires the first causal failure")
        if completed_shadow_events != len(result.call_ledgers):
            raise ValueError("RECCT-A3 failure lost a completed-call ledger")
        if counts["learner_backward_shadow_calls"] and not result.activity_events:
            raise ValueError("RECCT-A3 post-call failure lost its activity evidence")
