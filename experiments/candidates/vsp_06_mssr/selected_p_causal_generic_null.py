"""VSP06-A2 selected-P causal audit and equal-information generic null.

The registered audit consumes the accepted public A1 two-history witness and
calls only the registered production ``first_logits`` kernel.  It does not
advance an environment or invoke a learner, trainer, optimizer, evaluator, or
model-fitting routine.  The finite generic compiler is deliberately allowed to
store the complete two-row mapping: A2 is a causal/null audit, not an
expressivity contest.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from experiments.candidates.vsp_06_mssr import joint_production_binding as a1
from ha_ctse_process.variable_roster_event import MSSR_JOINT_PRODUCTION_ACTION_PATH


RAW_OUTPUT_BINDING = "vsp_06_mssr.selected_p_causal_generic_null.a2.v1"
TREATMENT = "VSP06-A2-SELECTED-P-CAUSAL-AND-GENERIC-COMPILE-NULL"
CANDIDATE = a1.CANDIDATE

INVALID = "A2_INVALID_CONTRACT_PROVENANCE_OR_UNMATCHED_NULL"
ACTION_NULL = "A2_SELECTED_P_ACTION_NULL"
DECOY_SENSITIVE = "A2_DECOY_OR_UNAUTHENTICATED_PAYLOAD_SENSITIVE"
LOGIT_ONLY = "A2_SELECTED_P_LOGIT_ONLY"
CURRENT_REBUILD_COMPILES = "A2_CURRENT_REBUILD_COMPILES_BOTH_HISTORIES"
GENERIC_COMPILER_FAILS = (
    "A2_GENERIC_COMPILER_DOES_NOT_MATCH_WITH_EQUAL_INFORMATION"
)
CAUSAL_GENERIC_COMPILES = "A2_SELECTED_P_CAUSAL_EFFECT_GENERIC_NULL_COMPILES"

ACCEPTED_COMMITS = {
    "a1_source": "6ee1ee4efeddcc71175a0860ca52a9aa15bb2c1d",
    "a1_result": "575e6cefa6d3cf7d1e84b782806147cd5e7f11f7",
    "a1_final_package": "a62892e9487c8aad30cff1c83b1bbc46cb0df588",
}
PUBLIC_LOCATORS = {
    "a2_source": (
        "experiments/candidates/vsp_06_mssr/selected_p_causal_generic_null.py"
    ),
    "a2_runner": "scripts/run_vsp06_a2_selected_p_causal_generic_null.py",
    "a2_test": (
        "tests/experiments/candidates/vsp_06_mssr/"
        "test_selected_p_causal_generic_null.py"
    ),
    "code_science_index": (
        "docs/research/candidates/vsp_06_mssr/CODE_SCIENCE_INDEX.md"
    ),
    "a1_witness": (
        "docs/research/candidates/vsp_06_mssr/"
        "VSP06_A1_MATCHED_SUPPORT_WITNESS.json"
    ),
    "a1_result": (
        "docs/research/candidates/vsp_06_mssr/"
        "VSP06_A1_JOINT_PRODUCTION_BINDING_RESULT.json"
    ),
    "production_core": "ha_ctse_process/variable_roster_event.py",
    "production_model": "ha_ctse_process/variable_roster_event_models.py",
}

# Frozen before any audit observation.  Every retained model value is float32;
# 64 ULPs at unit scale is deliberately conservative for a replay of the same
# CPU graph while remaining far below the accepted A1 P effect.
FLOAT32_EPSILON = float(np.finfo(np.float32).eps)
TOLERANCE_MULTIPLIER = 64
FLOAT32_SCALED_TOLERANCE = TOLERANCE_MULTIPLIER * FLOAT32_EPSILON
MAX_PRODUCTION_KERNEL_CALLS = 24
REGISTERED_PRODUCTION_KERNEL_CALLS = 10
CURRENT_REBUILD_P = np.float32(0.0)

GENERIC_INFORMATION_FIELDS = (
    "X",
    "P",
    "provenance",
    "recurrence",
    "legal_mask",
    "sampled_order",
    "production_path",
)


class AuditContractError(ValueError):
    """Fail-closed A2 contract or accepted-witness mismatch."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _decode_plain(value: Any) -> Any:
    if isinstance(value, Mapping) and value.get("kind") in {"tensor", "ndarray"}:
        if set(value) != {"kind", "dtype", "shape", "bytes"}:
            raise AuditContractError("encoded A1 array has unexpected fields")
        dtype = np.dtype(str(value["dtype"]))
        shape = tuple(int(item) for item in value["shape"])
        array = np.frombuffer(bytes.fromhex(str(value["bytes"])), dtype=dtype).copy()
        try:
            array = array.reshape(shape)
        except ValueError as exc:
            raise AuditContractError("encoded A1 array shape is invalid") from exc
        return torch.from_numpy(array) if value["kind"] == "tensor" else array
    if isinstance(value, Mapping):
        return {str(key): _decode_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decode_plain(item) for item in value]
    return value


def _decode_hex_json(payload_hex: str) -> Any:
    try:
        encoded = json.loads(bytes.fromhex(payload_hex).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditContractError("accepted A1 hexadecimal JSON is invalid") from exc
    return _decode_plain(encoded)


def _array_hex(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    return value.tobytes().hex()


def _owner_weight_digest(owner: Any) -> str:
    digest = hashlib.sha256()
    modules = (
        ("commitment_model", getattr(owner, "commitment_model", None)),
        ("event_critic", getattr(owner, "event_critic", None)),
    )
    if any(not isinstance(module, torch.nn.Module) for _name, module in modules):
        raise AuditContractError("registered model owner omits actor/critic weights")
    for module_name, module in modules:
        for name, tensor in sorted(module.state_dict().items()):
            array = tensor.detach().cpu().contiguous().numpy()
            digest.update(module_name.encode("utf-8"))
            digest.update(name.encode("utf-8"))
            digest.update(str(array.dtype).encode("ascii"))
            digest.update(_canonical_bytes(list(array.shape)))
            digest.update(array.tobytes())
    return digest.hexdigest()


def _numpy_rng_equal(left: tuple[Any, ...], right: tuple[Any, ...]) -> bool:
    return bool(
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


@dataclass(frozen=True)
class HistoryInput:
    label: str
    context_hex: str
    context: Mapping[str, Any]
    selected_p_hex: str
    selected_p: torch.Tensor
    provenance: Mapping[str, Any]
    accepted_logits: np.ndarray
    accepted_probabilities: np.ndarray
    accepted_action: int

    @property
    def preimage(self) -> Mapping[str, Any]:
        return self.context["preimage_without_P"]

    @property
    def partition(self) -> Mapping[str, Any]:
        return self.preimage["mssr_spf_partition"]


@dataclass(frozen=True)
class UnselectedPCarrier:
    """One real carrier presented to, but rejected by, P selection."""

    carrier_id: str
    payload: torch.Tensor
    provenance: Mapping[str, Any]
    selected: bool = False


@dataclass(frozen=True)
class KernelOutput:
    logits: np.ndarray
    centered_logits: np.ndarray
    probabilities: np.ndarray
    selected_argmax: int
    recurrence_digest: str
    selection_trace: Mapping[str, Any] | None = None

    def public(self) -> dict[str, Any]:
        result = {
            "logits": [float(item) for item in self.logits],
            "centered_logits": [float(item) for item in self.centered_logits],
            "probabilities": [float(item) for item in self.probabilities],
            "selected_argmax": int(self.selected_argmax),
            "recurrence_digest": self.recurrence_digest,
        }
        if self.selection_trace is not None:
            result["selection_trace"] = dict(self.selection_trace)
        return result


@dataclass(frozen=True)
class GenericInput:
    X: str
    P: str
    provenance: str
    recurrence: str
    legal_mask: str
    sampled_order: tuple[str, ...]
    production_path: str

    def key(self) -> bytes:
        return _canonical_bytes(
            {
                "X": self.X,
                "P": self.P,
                "provenance": self.provenance,
                "recurrence": self.recurrence,
                "legal_mask": self.legal_mask,
                "sampled_order": list(self.sampled_order),
                "production_path": self.production_path,
            }
        )


class GenericFiniteCompiler:
    """Exact two-row compiler with the same audit information and capacity."""

    def __init__(
        self,
        *,
        support_cardinality: int,
        action_dimension: int,
        scalar_capacity: int | None = None,
    ) -> None:
        self.support_cardinality = int(support_cardinality)
        self.action_dimension = int(action_dimension)
        required = self.support_cardinality * self.action_dimension
        self.scalar_capacity = required if scalar_capacity is None else int(scalar_capacity)
        if self.scalar_capacity < required:
            raise AuditContractError("generic compiler scalar capacity is unmatched")
        self._rows: dict[bytes, np.ndarray] = {}

    @property
    def compiled_scalar_count(self) -> int:
        return self.support_cardinality * self.action_dimension

    @property
    def reserved_scalar_capacity(self) -> int:
        return self.scalar_capacity - self.compiled_scalar_count

    def compile(self, rows: Sequence[tuple[GenericInput, np.ndarray]]) -> None:
        if len(rows) != self.support_cardinality:
            raise AuditContractError("generic compiler support capacity is unmatched")
        compiled: dict[bytes, np.ndarray] = {}
        for inputs, centered_logits in rows:
            key = inputs.key()
            value = np.asarray(centered_logits, dtype=np.float32).reshape(-1)
            if value.shape != (self.action_dimension,) or key in compiled:
                raise AuditContractError("generic compiler rows are invalid or duplicated")
            compiled[key] = value.copy()
        self._rows = compiled

    def __call__(self, inputs: GenericInput) -> np.ndarray:
        try:
            return self._rows[inputs.key()].copy()
        except KeyError as exc:
            raise AuditContractError("generic compiler received unseen information") from exc


def _validate_carrier(
    history: HistoryInput, *, target_label: str
) -> str:
    row = dict(history.provenance)
    required = {
        "episode_id",
        "owner_lifecycle_key",
        "membership_epoch",
        "partner_lifecycle_key",
        "event_index",
        "prior_p",
        "payload",
        "next_p",
        "writer_policy_version",
    }
    if set(row) != required:
        raise AuditContractError("A1 authenticated P carrier schema changed")
    if (
        target_label not in {"left", "right"}
        or int(row["episode_id"]) != 60809
        or row["owner_lifecycle_key"] != a1.OWNER
        or row["partner_lifecycle_key"] != a1.HISTORICAL_SOURCE
        or int(row["membership_epoch"]) != 0
        or int(row["event_index"]) != 0
        or int(row["writer_policy_version"]) != 0
    ):
        raise AuditContractError("A1 authenticated P carrier identity changed")
    prior = float(row["prior_p"])
    payload = float(row["payload"])
    next_p = float(row["next_p"])
    expected = float(np.clip(0.8 * prior + 0.2 * payload, -1.0, 1.0))
    if (
        not all(np.isfinite(value) for value in (prior, payload, next_p))
        or prior != 0.0
        or not -1.0 <= payload <= 1.0
        or next_p != expected
    ):
        raise AuditContractError("A1 authenticated P transition is invalid")
    selected = np.asarray(history.selected_p.detach().cpu(), dtype=np.float32).reshape(-1)
    if selected.shape != (1,) or selected[0] != np.float32(next_p):
        raise AuditContractError("A1 selected P does not match its provenance tail")
    return _digest_bytes(_canonical_bytes(row))


def _make_unauthenticated_decoy(
    history: HistoryInput, *, value: np.float32, carrier_id: str
) -> UnselectedPCarrier:
    scalar = np.float32(value)
    if not np.isfinite(scalar) or abs(float(scalar)) > 0.2:
        raise AuditContractError("decoy P must fit one bounded technical carrier")
    provenance = dict(history.provenance)
    provenance.update(
        {
            "prior_p": 0.0,
            "payload": float(scalar) / 0.2,
            "next_p": float(scalar),
            # The negative writer version makes this an actual but
            # unauthenticated carrier at the selection boundary.
            "writer_policy_version": -1,
        }
    )
    return UnselectedPCarrier(
        carrier_id=str(carrier_id),
        payload=torch.as_tensor([[scalar]], dtype=torch.float32),
        provenance=provenance,
    )


def _select_p_at_production_boundary(
    history: HistoryInput, decoy: UnselectedPCarrier
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Select authenticated P from two presented carriers, rejecting decoy."""

    selected_digest = _validate_carrier(history, target_label=history.label)
    if decoy.selected:
        raise AuditContractError("unauthenticated decoy was marked selected")
    candidate = replace(
        history,
        selected_p=decoy.payload,
        selected_p_hex=_array_hex(decoy.payload.detach().cpu().numpy()),
        provenance=dict(decoy.provenance),
    )
    try:
        _validate_carrier(candidate, target_label=history.label)
    except AuditContractError:
        decoy_authenticated = False
    else:
        decoy_authenticated = True
    if decoy_authenticated:
        raise AuditContractError("decoy carrier unexpectedly authenticated")
    decoy_array = decoy.payload.detach().cpu().contiguous().numpy()
    return history.selected_p, {
        "presented_carrier_count": 2,
        "selected_carrier": "authenticated_selected_p",
        "selected_p_digest": _digest_bytes(
            history.selected_p.detach().cpu().contiguous().numpy().tobytes()
        ),
        "selected_provenance_digest": selected_digest,
        "unselected_carrier": decoy.carrier_id,
        "unselected_payload_digest": _digest_bytes(decoy_array.tobytes()),
        "unselected_payload": float(decoy_array.reshape(-1)[0]),
        "unselected_authenticated": decoy_authenticated,
        "unselected_selected": decoy.selected,
    }


def _history_from_witness(witness: Mapping[str, Any], label: str) -> HistoryInput:
    body = witness.get(label)
    if not isinstance(body, Mapping):
        raise AuditContractError(f"A1 witness omits {label} history")
    decision = body.get("decision")
    provenance = body.get("historical_write")
    if not isinstance(decision, Mapping) or not isinstance(provenance, Mapping):
        raise AuditContractError("A1 witness history is incomplete")
    context_hex = str(decision.get("current_non_p_context_hex", ""))
    selected_p_hex = str(decision.get("authenticated_p_hex", ""))
    context = _decode_hex_json(context_hex)
    selected_p = _decode_hex_json(selected_p_hex)
    if not isinstance(context, Mapping) or not isinstance(selected_p, torch.Tensor):
        raise AuditContractError("A1 witness context/P encoding has the wrong type")
    preimage = context.get("preimage_without_P")
    if not isinstance(preimage, Mapping):
        raise AuditContractError("A1 witness omits its non-P actor preimage")
    partition = preimage.get("mssr_spf_partition")
    if not isinstance(partition, Mapping) or set(partition) != {
        "S",
        "F",
        "owners",
        "production_action_path",
    }:
        raise AuditContractError("A1 witness non-P partition changed")
    if (
        partition["production_action_path"] != MSSR_JOINT_PRODUCTION_ACTION_PATH
        or tuple(partition["owners"])
        != ("unit.slow_context", "unit.partner_interaction", "unit.fast_control")
        or decision.get("production_action_path")
        != MSSR_JOINT_PRODUCTION_ACTION_PATH
        or tuple(decision.get("partition_owners", ())) != tuple(partition["owners"])
    ):
        raise AuditContractError("A1 registered production path/owners changed")
    if (
        decision.get("authenticated_p_digest") != a1._digest(selected_p)
        or decision.get("S_digest") != a1._digest(partition["S"])
        or decision.get("F_digest") != a1._digest(partition["F"])
        or decision.get("current_non_p_context_digest")
        != _digest_bytes(bytes.fromhex(context_hex))
    ):
        raise AuditContractError("A1 witness digest binding failed")
    logits = np.asarray(decision.get("full_masked_logits"), dtype=np.float32)
    probabilities = np.asarray(decision.get("full_probabilities"), dtype=np.float32)
    action = int(decision.get("selected_action", -1))
    if (
        logits.ndim != 1
        or logits.shape != probabilities.shape
        or logits.shape[0] <= 1
        or action != int(np.argmax(logits))
        or not bool(decision.get("action_from_full_kernel"))
        or bool(decision.get("teacher_action_used"))
    ):
        raise AuditContractError("A1 factual production kernel binding changed")
    result = HistoryInput(
        label=label,
        context_hex=context_hex,
        context=context,
        selected_p_hex=selected_p_hex,
        selected_p=selected_p,
        provenance=dict(provenance),
        accepted_logits=logits,
        accepted_probabilities=probabilities,
        accepted_action=action,
    )
    _validate_carrier(result, target_label=label)
    return result


def _mask_and_owner_row(history: HistoryInput) -> tuple[torch.Tensor, int]:
    preimage = history.preimage
    legal_mask = preimage["legal_mask"]
    if not isinstance(legal_mask, torch.Tensor) or legal_mask.dtype != torch.bool:
        raise AuditContractError("A1 legal mask encoding changed")
    active_keys = tuple(str(item) for item in preimage["active_lifecycle_keys"])
    if active_keys != (a1.OWNER, a1.CURRENT_SOURCE):
        raise AuditContractError("A1 active lifecycle order changed")
    return legal_mask.reshape(-1), active_keys.index(a1.OWNER)


def _production_kernel(
    model: torch.nn.Module,
    history: HistoryInput,
    selected_p: torch.Tensor,
    *,
    unselected_carrier: UnselectedPCarrier | None = None,
) -> KernelOutput:
    """Call production after the explicit authenticated-carrier selection."""

    selection_trace = None
    if unselected_carrier is not None:
        selected_p, selection_trace = _select_p_at_production_boundary(
            history, unselected_carrier
        )
    preimage = history.preimage
    partition = history.partition
    observations = preimage["observations"]
    flags = preimage["event_flags"]
    skills = torch.as_tensor(preimage["pre_token_working_skills"], dtype=torch.long)
    ages = torch.as_tensor(preimage["pre_token_working_ages"], dtype=torch.long)
    pre_hidden = preimage["pre_token_high_hidden"]
    legal_mask, owner_row = _mask_and_owner_row(history)
    tensors = (observations, flags, pre_hidden, partition["S"], partition["F"])
    if not all(isinstance(item, torch.Tensor) for item in tensors):
        raise AuditContractError("A1 production preimage tensor encoding changed")
    with torch.inference_mode():
        embeddings = model.encode_members(observations, skills, ages, flags)
        typed_partition = model.selective_spf_partition(
            partition["S"], partition["F"], selected_p
        )
        logits, recurrence = model.first_logits(
            embeddings[owner_row],
            partition["S"],
            pre_hidden,
            partition=typed_partition,
        )
        masked = logits.masked_fill(~legal_mask, -torch.inf)
        probabilities = torch.softmax(masked, dim=-1)
    logits_array = masked.detach().cpu().numpy().astype(np.float32, copy=True)
    probabilities_array = (
        probabilities.detach().cpu().numpy().astype(np.float32, copy=True)
    )
    legal = legal_mask.detach().cpu().numpy().astype(bool, copy=False)
    center = float(np.mean(logits_array[legal], dtype=np.float64))
    centered = logits_array.astype(np.float64) - center
    centered[~legal] = 0.0
    recurrence_array = recurrence.detach().cpu().contiguous().numpy()
    return KernelOutput(
        logits=logits_array,
        centered_logits=centered,
        probabilities=probabilities_array,
        selected_argmax=int(np.argmax(logits_array)),
        recurrence_digest=_digest_bytes(recurrence_array.tobytes()),
        selection_trace=selection_trace,
    )


def _max_error(left: np.ndarray, right: np.ndarray) -> float:
    lhs = np.asarray(left, dtype=np.float64)
    rhs = np.asarray(right, dtype=np.float64)
    if lhs.shape != rhs.shape or not np.all(np.isfinite(lhs)) or not np.all(np.isfinite(rhs)):
        return float("inf")
    return float(np.max(np.abs(lhs - rhs), initial=0.0))


def _production_head_scalar_capacity(model: torch.nn.Module) -> int:
    first_decoder = getattr(model, "first_decoder", None)
    first_head = getattr(model, "first_head", None)
    if not isinstance(first_decoder, torch.nn.Module) or not isinstance(
        first_head, torch.nn.Module
    ):
        raise AuditContractError("registered selected-P production head is absent")
    return sum(
        int(parameter.numel())
        for module in (first_decoder, first_head)
        for parameter in module.parameters()
    )


def _full_current_rebuild_p(histories: Sequence[HistoryInput]) -> np.float32:
    """Frozen accepted VSP06 B_P(X): one full-X key, no historical read."""

    if len(histories) != 2 or histories[0].context_hex != histories[1].context_hex:
        raise AuditContractError("B_P(X) requires the accepted identical full current X")
    # Parsing and field checks make X byte-complete: observations, recurrence,
    # mask, order, roster, skills/ages, event flags, S/F and path are all in the
    # single key.  The accepted VSP06 current rebuild at this X is exactly zero.
    required = {
        "observations",
        "event_flags",
        "initial_skills",
        "initial_ages",
        "pre_token_working_skills",
        "pre_token_working_ages",
        "pre_token_high_hidden",
        "legal_mask",
        "sampled_order",
        "active_lifecycle_keys",
        "active_membership_epochs",
        "architecture_mode",
        "mssr_spf_partition",
    }
    if set(histories[0].preimage) != required:
        raise AuditContractError("B_P(X) current-context inventory changed")
    return CURRENT_REBUILD_P


def _generic_input(history: HistoryInput, provenance_digest: str) -> GenericInput:
    preimage = history.preimage
    recurrence = preimage["pre_token_high_hidden"].detach().cpu().contiguous().numpy()
    legal_mask = preimage["legal_mask"].detach().cpu().contiguous().numpy()
    return GenericInput(
        X=history.context_hex,
        P=history.selected_p_hex,
        provenance=provenance_digest,
        recurrence=_array_hex(recurrence),
        legal_mask=_array_hex(legal_mask),
        sampled_order=tuple(str(item) for item in preimage["sampled_order"]),
        production_path=str(history.partition["production_action_path"]),
    )


REQUIRED_BOOLEAN_EVIDENCE = {
    "contract_valid",
    "provenance_authenticated",
    "cross_swap_provenance_authenticated",
    "non_p_byte_equal",
    "registered_path",
    "weights_unchanged",
    "evaluation_conditions_frozen",
    "generic_equal_information",
    "generic_matched_capacity",
    "call_budget_valid",
    "decoy_selected_p_fixed",
    "decoy_carriers_unauthenticated",
}


def classify_audit(evidence: Mapping[str, Any]) -> str:
    """Authoritative exact seven-branch fail-closed precedence."""

    numeric = {
        "selected_p_raw_logit_effect",
        "selected_p_centered_logit_effect",
        "selected_p_kernel_effect",
        "decoy_kernel_error",
        "current_rebuild_error",
        "generic_compiler_error",
        "tolerance",
    }
    if (
        not isinstance(evidence, Mapping)
        or not REQUIRED_BOOLEAN_EVIDENCE.issubset(evidence)
        or not numeric.issubset(evidence)
        or any(not isinstance(evidence[name], bool) for name in REQUIRED_BOOLEAN_EVIDENCE)
        or any(
            not isinstance(evidence[name], (int, float))
            or not np.isfinite(float(evidence[name]))
            for name in numeric
        )
        or not all(evidence[name] for name in REQUIRED_BOOLEAN_EVIDENCE)
    ):
        return INVALID
    tolerance = float(evidence["tolerance"])
    if tolerance <= 0.0:
        return INVALID
    if float(evidence["selected_p_raw_logit_effect"]) <= tolerance:
        return ACTION_NULL
    if float(evidence["decoy_kernel_error"]) > tolerance:
        return DECOY_SENSITIVE
    if float(evidence["selected_p_kernel_effect"]) <= tolerance:
        return LOGIT_ONLY
    if float(evidence["current_rebuild_error"]) <= tolerance:
        return CURRENT_REBUILD_COMPILES
    if float(evidence["generic_compiler_error"]) > tolerance:
        return GENERIC_COMPILER_FAILS
    return CAUSAL_GENERIC_COMPILES


def registered_audit(witness: Mapping[str, Any]) -> dict[str, Any]:
    """Execute the one registered ten-call selected-P causal/null audit."""

    if (
        witness.get("raw_output_binding") != a1.RAW_OUTPUT_BINDING
        or witness.get("candidate") != CANDIDATE
        or witness.get("branch") != a1.ESTABLISHED
    ):
        raise AuditContractError("input is not the accepted A1 two-history witness")
    histories = tuple(_history_from_witness(witness, side) for side in ("left", "right"))
    if histories[0].context_hex != histories[1].context_hex:
        raise AuditContractError("accepted A1 full non-P contexts are not byte equal")
    if histories[0].selected_p_hex == histories[1].selected_p_hex:
        raise AuditContractError("accepted A1 selected P carriers are not distinct")

    provenance_digests = tuple(
        _validate_carrier(history, target_label=history.label) for history in histories
    )
    # Cross-substitution is authenticated because each complete carrier has the
    # same registered owner/partner/episode identity and is revalidated for the
    # opposite accepted target before its P is selected.
    _validate_carrier(histories[1], target_label="left")
    _validate_carrier(histories[0], target_label="right")

    torch_rng_before = torch.get_rng_state().clone()
    numpy_rng_before = np.random.get_state()
    factory, model_owner, _left_core, _right_core = a1._factory_triplet()
    if not (
        factory.get("factory_available")
        and factory.get("factory_identity")
        and factory.get("path_bound")
        and model_owner is not None
    ):
        raise AuditContractError("registered A1 production factory/path is unavailable")
    model = model_owner.commitment_model
    training_mode = bool(model.training)
    weight_digest_before = _owner_weight_digest(model_owner)

    keep = tuple(
        _production_kernel(model, history, history.selected_p) for history in histories
    )
    cross = tuple(
        _production_kernel(model, history, histories[1 - index].selected_p)
        for index, history in enumerate(histories)
    )
    rebuilt_p = _full_current_rebuild_p(histories)
    rebuild = tuple(
        _production_kernel(model, history, torch.as_tensor([[rebuilt_p]]))
        for history in histories
    )
    decoy_baseline_carriers = tuple(
        _make_unauthenticated_decoy(
            history,
            value=np.float32(-0.125),
            carrier_id=f"unauthenticated_decoy_{history.label}",
        )
        for history in histories
    )
    decoy_perturbed_carriers = tuple(
        _make_unauthenticated_decoy(
            history,
            value=np.float32(0.125),
            carrier_id=f"unauthenticated_decoy_{history.label}",
        )
        for history in histories
    )
    decoy_baseline = tuple(
        _production_kernel(
            model,
            history,
            history.selected_p,
            unselected_carrier=decoy_baseline_carriers[index],
        )
        for index, history in enumerate(histories)
    )
    decoy_perturbed = tuple(
        _production_kernel(
            model,
            history,
            history.selected_p,
            unselected_carrier=decoy_perturbed_carriers[index],
        )
        for index, history in enumerate(histories)
    )

    weight_digest_after = _owner_weight_digest(model_owner)
    torch_rng_after = torch.get_rng_state().clone()
    numpy_rng_after = np.random.get_state()
    factual_replay_error = max(
        max(
            _max_error(output.logits, history.accepted_logits),
            _max_error(output.probabilities, history.accepted_probabilities),
        )
        for output, history in zip(keep, histories)
    )

    raw_effect = max(
        _max_error(factual.logits, swapped.logits)
        for factual, swapped in zip(keep, cross)
    )
    centered_effect = max(
        _max_error(factual.centered_logits, swapped.centered_logits)
        for factual, swapped in zip(keep, cross)
    )
    kernel_effect = max(
        _max_error(factual.probabilities, swapped.probabilities)
        for factual, swapped in zip(keep, cross)
    )
    decoy_error = max(
        max(
            _max_error(baseline.centered_logits, perturbed.centered_logits),
            _max_error(baseline.probabilities, perturbed.probabilities),
        )
        for baseline, perturbed in zip(decoy_baseline, decoy_perturbed)
    )
    selection_pairs = tuple(
        (baseline.selection_trace, perturbed.selection_trace)
        for baseline, perturbed in zip(decoy_baseline, decoy_perturbed)
    )
    decoy_selected_p_fixed = all(
        isinstance(baseline, Mapping)
        and isinstance(perturbed, Mapping)
        and baseline["selected_p_digest"] == perturbed["selected_p_digest"]
        and baseline["selected_provenance_digest"]
        == perturbed["selected_provenance_digest"]
        and baseline["unselected_payload_digest"]
        != perturbed["unselected_payload_digest"]
        for baseline, perturbed in selection_pairs
    )
    decoy_carriers_unauthenticated = all(
        not bool(trace["unselected_authenticated"])
        and not bool(trace["unselected_selected"])
        for pair in selection_pairs
        for trace in pair
        if isinstance(trace, Mapping)
    ) and all(isinstance(trace, Mapping) for pair in selection_pairs for trace in pair)
    rebuild_errors = tuple(
        _max_error(factual.centered_logits, rebuilt.centered_logits)
        for factual, rebuilt in zip(keep, rebuild)
    )

    generic_inputs = tuple(
        _generic_input(history, provenance)
        for history, provenance in zip(histories, provenance_digests)
    )
    production_head_capacity = _production_head_scalar_capacity(model)
    compiler = GenericFiniteCompiler(
        support_cardinality=len(histories),
        action_dimension=keep[0].logits.shape[0],
        scalar_capacity=production_head_capacity,
    )
    compiler.compile(
        tuple(
            (inputs, output.centered_logits)
            for inputs, output in zip(generic_inputs, keep)
        )
    )
    generic_errors = tuple(
        _max_error(compiler(inputs), output.centered_logits)
        for inputs, output in zip(generic_inputs, keep)
    )

    evidence = {
        "contract_valid": factual_replay_error <= FLOAT32_SCALED_TOLERANCE,
        "provenance_authenticated": True,
        "cross_swap_provenance_authenticated": True,
        "non_p_byte_equal": histories[0].context_hex == histories[1].context_hex,
        "registered_path": model_owner.production_action_path
        == MSSR_JOINT_PRODUCTION_ACTION_PATH,
        "weights_unchanged": weight_digest_before == weight_digest_after,
        "evaluation_conditions_frozen": (
            bool(model.training) == training_mode
            and torch.equal(torch_rng_before, torch_rng_after)
            and _numpy_rng_equal(numpy_rng_before, numpy_rng_after)
            and all(
                output.selected_argmax == history.accepted_action
                for output, history in zip(keep, histories)
            )
        ),
        "generic_equal_information": tuple(GenericInput.__dataclass_fields__)
        == GENERIC_INFORMATION_FIELDS,
        "generic_matched_capacity": compiler.scalar_capacity
        == production_head_capacity,
        "call_budget_valid": REGISTERED_PRODUCTION_KERNEL_CALLS
        <= MAX_PRODUCTION_KERNEL_CALLS,
        "decoy_selected_p_fixed": decoy_selected_p_fixed,
        "decoy_carriers_unauthenticated": decoy_carriers_unauthenticated,
        "selected_p_raw_logit_effect": raw_effect,
        "selected_p_centered_logit_effect": centered_effect,
        "selected_p_kernel_effect": kernel_effect,
        "decoy_kernel_error": decoy_error,
        "current_rebuild_error": max(rebuild_errors),
        "generic_compiler_error": max(generic_errors),
        "tolerance": FLOAT32_SCALED_TOLERANCE,
    }
    branch = classify_audit(evidence)

    arms: dict[str, Any] = {}
    for index, history in enumerate(histories):
        baseline_trace, perturbed_trace = selection_pairs[index]
        pair_selected_p_fixed = bool(
            baseline_trace["selected_p_digest"]
            == perturbed_trace["selected_p_digest"]
            and baseline_trace["selected_provenance_digest"]
            == perturbed_trace["selected_provenance_digest"]
        )
        pair_decoy_authenticated = bool(
            baseline_trace["unselected_authenticated"]
            or perturbed_trace["unselected_authenticated"]
        )
        pair_decoy_selected = bool(
            baseline_trace["unselected_selected"]
            or perturbed_trace["unselected_selected"]
        )
        arms[history.label] = {
            "factual_keep": keep[index].public(),
            "authenticated_selected_p_cross_swap": cross[index].public(),
            "full_current_rebuild": {
                **rebuild[index].public(),
                "B_P_X": float(rebuilt_p),
                "centered_residual": [
                    float(item)
                    for item in (
                        keep[index].centered_logits - rebuild[index].centered_logits
                    )
                ],
                "error": rebuild_errors[index],
            },
            "decoy_or_unauthenticated_perturbation": {
                "baseline": decoy_baseline[index].public(),
                "perturbed": decoy_perturbed[index].public(),
                "selected_p_fixed": pair_selected_p_fixed,
                "decoy_authenticated": pair_decoy_authenticated,
                "decoy_selected": pair_decoy_selected,
                "kernel_error": max(
                    _max_error(
                        decoy_baseline[index].centered_logits,
                        decoy_perturbed[index].centered_logits,
                    ),
                    _max_error(
                        decoy_baseline[index].probabilities,
                        decoy_perturbed[index].probabilities,
                    ),
                ),
            },
            "selected_p_hex": history.selected_p_hex,
            "selected_p_provenance_digest": provenance_digests[index],
            "current_non_p_context_digest": _digest_bytes(
                bytes.fromhex(history.context_hex)
            ),
            "generic_compiler_error": generic_errors[index],
        }

    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "treatment": TREATMENT,
        "candidate": CANDIDATE,
        "branch": branch,
        "accepted_commits": dict(ACCEPTED_COMMITS),
        "public_locators": dict(PUBLIC_LOCATORS),
        "tolerance": {
            "dtype": "float32",
            "epsilon": FLOAT32_EPSILON,
            "multiplier": TOLERANCE_MULTIPLIER,
            "absolute": FLOAT32_SCALED_TOLERANCE,
            "frozen_before_observation": True,
        },
        "evidence": evidence,
        "arms": arms,
        "generic_compiler": {
            "kind": "exact_finite_lookup",
            "information_fields": list(GENERIC_INFORMATION_FIELDS),
            "support_cardinality": compiler.support_cardinality,
            "action_dimension": compiler.action_dimension,
            "scalar_capacity": compiler.scalar_capacity,
            "compiled_scalar_count": compiler.compiled_scalar_count,
            "reserved_scalar_capacity": compiler.reserved_scalar_capacity,
            "production_head_scalar_capacity": production_head_capacity,
            "matched_capacity": evidence["generic_matched_capacity"],
            "error": max(generic_errors),
            "model_fit_calls": 0,
        },
        "controls": {
            "registered_production_path": MSSR_JOINT_PRODUCTION_ACTION_PATH,
            "weight_digest_before": weight_digest_before,
            "weight_digest_after": weight_digest_after,
            "factual_a1_replay_error": factual_replay_error,
            "full_current_non_p_bytes_equal": evidence["non_p_byte_equal"],
            "cross_swap_provenance_authenticated": True,
            "decoy_side_channel_present": decoy_error
            > FLOAT32_SCALED_TOLERANCE,
            "decoy_selected_p_fixed": decoy_selected_p_fixed,
            "decoy_carriers_unauthenticated": decoy_carriers_unauthenticated,
            "deterministic_argmax": True,
            "current_source_fixed": all(
                tuple(history.preimage["active_lifecycle_keys"])
                == (a1.OWNER, a1.CURRENT_SOURCE)
                for history in histories
            ),
            "teacher_action_used": False,
            "legal_mask_and_order_fixed": all(
                tuple(history.preimage["sampled_order"]) == (a1.OWNER,)
                and bool(torch.all(history.preimage["legal_mask"]).item())
                for history in histories
            ),
        },
        "activity_counts": {
            "production_kernel_calls": REGISTERED_PRODUCTION_KERNEL_CALLS,
            "environment_transitions": 0,
            "learner_calls": 0,
            "trainer_calls": 0,
            "optimizer_updates": 0,
            "evaluation_episodes": 0,
            "model_fit_calls": 0,
            "environment_rng_draws": 0,
            "action_rng_draws": 0,
        },
        "limitations": (
            "A2 is one deterministic two-history production-kernel causal/null "
            "audit. It establishes no learning, return, deployment, promotion, "
            "retirement, B, or C conclusion."
        ),
    }


__all__ = [
    "registered_audit",
    "classify_audit",
    "GenericFiniteCompiler",
    "GenericInput",
    "AuditContractError",
    "INVALID",
    "ACTION_NULL",
    "DECOY_SENSITIVE",
    "LOGIT_ONLY",
    "CURRENT_REBUILD_COMPILES",
    "GENERIC_COMPILER_FAILS",
    "CAUSAL_GENERIC_COMPILES",
]
