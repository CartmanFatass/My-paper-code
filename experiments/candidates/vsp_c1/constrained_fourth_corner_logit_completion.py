"""VSPC1-A1 constrained fourth-corner centered-logit audit.

The registered entry point is deliberately fail-closed.  It will execute a
rectangle only when production code exposes one constructor explicitly marked
with :data:`HOST_CONTRACT_ID`; the current production runtime exposes no such
constructor.  Synthetic/retained rectangles may exercise the algebra and the
independent result validator, but are never considered registered hosts.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from ha_ctse_process import dynamic_roster_supplied_executor as supplied_runtime
from ha_ctse_process import variable_roster_event as event_runtime


SCHEMA_VERSION = 1
DESIGN_ID = "VSP-C1-CCLC-BOUND-A-V1"
TREATMENT_ID = "VSPC1-A1-CONSTRAINED-FOURTH-CORNER-LOGIT-COMPLETION"
CANDIDATE_VERSION = (
    "CAND-VSP-C1-CROSSED_IDENTITY_PERIOD_FACTORIZATION@"
    "constrained-fourth-corner-v9"
)
RAW_OUTPUT_BINDING = "vsp_c1.constrained_fourth_corner_logit_completion.a1.v1"
HOST_CONTRACT_ID = "vspc1.authenticated-identity-period-four-clone-host.v1"

INVALID = "A1_INVALID_CONSTRUCTION"
HOST_UNREACHABLE = "A1_HOST_RECTANGLE_UNREACHABLE"
NONDISCRIMINATING = "A1_PRE_REVEAL_NONDISCRIMINATING"
FALSIFIED = "A1_CONSTRAINED_SUCCESSOR_FALSIFIED"
SUPPORTED = "A1_LOCAL_FOURTH_CORNER_PREDICTION_SUPPORTED"
AMBIGUOUS = "A1_VALID_AMBIGUOUS"

T_CELLS = ("i0p0", "i0p1", "i1p0")
H_CELL = "i1p1"
ALL_CELLS = T_CELLS + (H_CELL,)
PRE_REVEAL_JS_THRESHOLD = 0.02
FALSIFICATION_D_C_THRESHOLD = 0.05
FALSIFICATION_RELATIVE_THRESHOLD = 0.02
SUPPORT_D_C_THRESHOLD = 0.01
SUPPORT_DELTA_THRESHOLD = 0.02

PORT_FREE_STATE_FIELDS = (
    "actor_visible_inputs",
    "router_inputs",
    "recurrent_inputs",
    "partner_inputs",
    "roster_inputs",
    "checkpoint_inputs",
    "age_inputs",
    "gradient_inputs",
    "legal_action_inputs",
    "rng_inputs",
)

ACTIVITY_CAPS = {
    "registered_audits": 1,
    "checkpoints": 1,
    "rosters": 1,
    "boundary_states": 1,
    "clones": 4,
    "focused_production_kernel_calls": 4,
    "deterministic_predictor_fits": 2,
    "sealed_prediction_receipts": 2,
    "environment_transitions": 0,
    "learner_calls": 0,
    "trainer_calls": 0,
    "optimizer_updates": 0,
    "return_evaluations": 0,
    "model_fits": 0,
    "stochastic_calls": 0,
    "sweeps_retries_rescues": 0,
}

SCIENTIFIC_NONCLAIMS = (
    "no semantic identity",
    "no global factorization",
    "no same-support superiority",
    "no task-return or transfer",
    "no learning/sample-complexity law",
    "no C formal promotion ranking retirement or Pro",
)


class ContractViolation(ValueError):
    """A frozen construction, seal, numerical, or artifact contract failed."""


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractViolation(f"value is not canonical finite JSON: {exc}") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_exact_keys(value: Mapping[str, Any], keys: set[str], name: str) -> None:
    if not isinstance(value, Mapping):
        raise ContractViolation(f"{name} must be a mapping")
    actual = set(value)
    if actual != keys:
        raise ContractViolation(
            f"{name} fields differ: missing={sorted(keys - actual)} "
            f"extra={sorted(actual - keys)}"
        )


def _finite_vector(value: Any, name: str, *, positive: bool = False) -> list[float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ContractViolation(f"{name} must be a numeric sequence")
    result: list[float] = []
    for item in value:
        if isinstance(item, bool):
            raise ContractViolation(f"{name} contains a boolean")
        try:
            number = float(item)
        except (TypeError, ValueError) as exc:
            raise ContractViolation(f"{name} contains a non-number") from exc
        if not math.isfinite(number) or (positive and number <= 0.0):
            qualifier = "finite positive" if positive else "finite"
            raise ContractViolation(f"{name} must contain only {qualifier} values")
        result.append(number)
    if not result:
        raise ContractViolation(f"{name} must not be empty")
    return result


def _same_floats(left: Sequence[float], right: Sequence[float]) -> bool:
    return len(left) == len(right) and all(
        math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=1e-12)
        for a, b in zip(left, right)
    )


def _finite_scalar(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ContractViolation(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractViolation(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise ContractViolation(f"{name} must be a finite number")
    return number


def centered_logits(probabilities: Sequence[float]) -> list[float]:
    """Return the unique zero-mean logit representative of a positive kernel."""

    values = _finite_vector(probabilities, "probabilities", positive=True)
    total = math.fsum(values)
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ContractViolation("probabilities must sum to one")
    logs = [math.log(value) for value in values]
    mean = math.fsum(logs) / len(logs)
    return [value - mean for value in logs]


def _softmax(logits: Sequence[float]) -> list[float]:
    values = _finite_vector(logits, "logits")
    maximum = max(values)
    exponentials = [math.exp(value - maximum) for value in values]
    total = math.fsum(exponentials)
    return [value / total for value in exponentials]


def jensen_shannon(left: Sequence[float], right: Sequence[float]) -> float:
    """Jensen-Shannon divergence in natural-log nats."""

    p = _finite_vector(left, "left kernel", positive=True)
    q = _finite_vector(right, "right kernel", positive=True)
    if len(p) != len(q):
        raise ContractViolation("JS kernels have different dimensions")
    if not math.isclose(math.fsum(p), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ContractViolation("left JS kernel does not sum to one")
    if not math.isclose(math.fsum(q), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ContractViolation("right JS kernel does not sum to one")
    midpoint = [(a + b) / 2.0 for a, b in zip(p, q)]
    return 0.5 * math.fsum(a * math.log(a / m) for a, m in zip(p, midpoint)) + 0.5 * math.fsum(
        b * math.log(b / m) for b, m in zip(q, midpoint)
    )


def _valid_hex_bytes(value: Any) -> bool:
    if not isinstance(value, str) or len(value) % 2:
        return False
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return True


def nonfactor_state_sha256(state: Mapping[str, Any]) -> str:
    """Bind the exact port-free state bytes captured for one clone source."""

    if not isinstance(state, Mapping):
        raise ContractViolation("port-free clone state must be a mapping")
    _require_exact_keys(state, set(PORT_FREE_STATE_FIELDS), "port-free clone state")
    if any(not _valid_hex_bytes(state[field]) for field in PORT_FREE_STATE_FIELDS):
        raise ContractViolation("port-free state fields must contain exact hexadecimal bytes")
    return _digest(state)


def validate_state_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate the prospectively frozen port-free four-clone rectangle."""

    if not isinstance(manifest, Mapping):
        raise ContractViolation("state manifest must be a mapping")
    expected = {
        "schema_version",
        "design_id",
        "treatment_id",
        "candidate_version",
        "host_contract_id",
        "checkpoint_id",
        "roster_id",
        "boundary_state_id",
        "metadata_factor_order",
        "selected_factors",
        "training_cells",
        "heldout_cell",
        "legal_action_order",
        "clones",
        "joint_key_witness",
        "selection_receipt",
        "freeze_receipt",
    }
    _require_exact_keys(manifest, expected, "state manifest")
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ContractViolation("state manifest schema version differs")
    for field, expected_value in (
        ("design_id", DESIGN_ID),
        ("treatment_id", TREATMENT_ID),
        ("candidate_version", CANDIDATE_VERSION),
        ("host_contract_id", HOST_CONTRACT_ID),
    ):
        if manifest[field] != expected_value:
            raise ContractViolation(f"state manifest {field} differs")
    for field in ("checkpoint_id", "roster_id", "boundary_state_id"):
        if not isinstance(manifest[field], str) or not manifest[field]:
            raise ContractViolation(f"state manifest {field} is not bound")

    order = manifest["metadata_factor_order"]
    if not isinstance(order, Mapping):
        raise ContractViolation("metadata factor order must be a mapping")
    _require_exact_keys(order, {"identity_levels", "period_levels"}, "metadata factor order")
    identities = list(order["identity_levels"])
    periods = list(order["period_levels"])
    if (
        len(identities) < 2
        or len(periods) < 2
        or any(not isinstance(value, str) or not value for value in identities + periods)
        or len(set(identities)) != len(identities)
        or len(set(periods)) != len(periods)
    ):
        raise ContractViolation("metadata factor order lacks two unique levels per factor")

    selected = manifest["selected_factors"]
    if not isinstance(selected, Mapping):
        raise ContractViolation("selected factors must be a mapping")
    _require_exact_keys(selected, {"i0", "i1", "p0", "p1"}, "selected factors")
    if [selected["i0"], selected["i1"]] != identities[:2] or [selected["p0"], selected["p1"]] != periods[:2]:
        raise ContractViolation("factor selection is not the first two frozen metadata levels")
    if tuple(manifest["training_cells"]) != T_CELLS or manifest["heldout_cell"] != H_CELL:
        raise ContractViolation("T/H cell assignment differs from the frozen fourth corner")

    actions = list(manifest["legal_action_order"])
    if (
        not actions
        or any(isinstance(action, bool) or not isinstance(action, (str, int)) for action in actions)
        or len(set(actions)) != len(actions)
    ):
        raise ContractViolation("legal action order must be nonempty and unique")

    selection = manifest["selection_receipt"]
    _require_exact_keys(
        selection,
        {
            "metadata_order_used",
            "kernel_reads_before_selection",
            "return_information_used",
            "outcome_conditioned_selection",
        },
        "selection receipt",
    )
    if selection != {
        "metadata_order_used": True,
        "kernel_reads_before_selection": 0,
        "return_information_used": False,
        "outcome_conditioned_selection": False,
    }:
        raise ContractViolation("factor/holdout selection is not prospectively frozen")

    freeze = manifest["freeze_receipt"]
    _require_exact_keys(
        freeze,
        {"event_ordinal", "kernel_reads_before_freeze", "frozen_objects"},
        "freeze receipt",
    )
    expected_frozen = [
        "checkpoint",
        "roster",
        "boundary state",
        "metadata factor order",
        "i0 i1 p0 p1",
        "three-cell T",
        "heldout H=i1p1",
        "legal-action order",
        "state-equality manifest",
    ]
    if freeze["event_ordinal"] != 0 or freeze["kernel_reads_before_freeze"] != 0 or freeze["frozen_objects"] != expected_frozen:
        raise ContractViolation("freeze receipt permits pre-freeze kernel inspection")

    joint = manifest["joint_key_witness"]
    _require_exact_keys(
        joint,
        {"predictor_read_paths", "joint_identity_period_key_paths", "joint_identity_period_descendant_paths"},
        "joint-key witness",
    )
    if joint["predictor_read_paths"] != ["identity", "period"] or joint["joint_identity_period_key_paths"] != [] or joint["joint_identity_period_descendant_paths"] != []:
        raise ContractViolation("joint identity-period key or descendant reaches a predictor")

    clones = manifest["clones"]
    if not isinstance(clones, Sequence) or isinstance(clones, (str, bytes)) or len(clones) != 4:
        raise ContractViolation("state manifest requires exactly four clones")
    expected_pairs = {
        "i0p0": (selected["i0"], selected["p0"]),
        "i0p1": (selected["i0"], selected["p1"]),
        "i1p0": (selected["i1"], selected["p0"]),
        "i1p1": (selected["i1"], selected["p1"]),
    }
    by_cell: dict[str, Mapping[str, Any]] = {}
    source_ids: dict[str, set[str]] = {
        "clone_handle_id": set(),
        "reader_id": set(),
        "kernel_source_id": set(),
        "model_graph_id": set(),
    }
    for clone in clones:
        if not isinstance(clone, Mapping):
            raise ContractViolation("clone manifest row must be a mapping")
        _require_exact_keys(
            clone,
            {
                "cell",
                "identity",
                "period",
                "port_free_state_bytes",
                "legal_action_order",
                "source_binding",
            },
            "clone manifest row",
        )
        cell = clone["cell"]
        if cell not in expected_pairs or cell in by_cell:
            raise ContractViolation("clone cells do not form one exact 2x2 rectangle")
        if (clone["identity"], clone["period"]) != expected_pairs[cell]:
            raise ContractViolation("clone factor fields differ from the selected rectangle")
        if clone["legal_action_order"] != actions:
            raise ContractViolation("clones do not share one legal action order")
        state = clone["port_free_state_bytes"]
        state_digest = nonfactor_state_sha256(state)
        binding = clone["source_binding"]
        _require_exact_keys(
            binding,
            {
                "cell",
                "clone_handle_id",
                "reader_id",
                "kernel_source_id",
                "model_graph_id",
                "nonfactor_state_sha256",
            },
            "clone source binding",
        )
        if binding["cell"] != cell or binding["nonfactor_state_sha256"] != state_digest:
            raise ContractViolation("clone source binding does not match its manifest state bytes")
        for field in source_ids:
            value = binding[field]
            if not isinstance(value, str) or not value:
                raise ContractViolation(f"clone source binding {field} is not bound")
            if value in source_ids[field]:
                raise ContractViolation(
                    "clone handles, readers, kernel sources, and model graphs must be distinct per cell"
                )
            source_ids[field].add(value)
        by_cell[cell] = clone
    if set(by_cell) != set(ALL_CELLS):
        raise ContractViolation("clone rectangle omits a required cell")
    reference = by_cell[T_CELLS[0]]["port_free_state_bytes"]
    for cell in ALL_CELLS[1:]:
        if by_cell[cell]["port_free_state_bytes"] != reference:
            raise ContractViolation("port-free actor/router/state/RNG inputs are not byte-identical")

    _canonical_bytes(manifest)


def _validate_kernel(
    kernel: Mapping[str, Any],
    *,
    cell: str,
    action_order: Sequence[Any],
    expected_source_binding: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(kernel, Mapping):
        raise ContractViolation(f"kernel {cell} must be a mapping")
    _require_exact_keys(
        kernel,
        {
            "probabilities",
            "legal_action_order",
            "legal_mask",
            "capture_source_binding",
        },
        f"kernel {cell}",
    )
    if kernel["capture_source_binding"] != expected_source_binding:
        raise ContractViolation(
            f"kernel {cell} capture source does not match the frozen clone binding"
        )
    if list(kernel["legal_action_order"]) != list(action_order):
        raise ContractViolation(f"kernel {cell} action order differs")
    legal_mask = kernel["legal_mask"]
    if legal_mask != [True] * len(action_order):
        raise ContractViolation(f"kernel {cell} lacks the common all-positive legal support")
    probabilities = _finite_vector(kernel["probabilities"], f"kernel {cell}", positive=True)
    if len(probabilities) != len(action_order):
        raise ContractViolation(f"kernel {cell} dimension differs from legal support")
    if not math.isclose(math.fsum(probabilities), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ContractViolation(f"kernel {cell} probabilities do not sum to one")
    return {
        "probabilities": probabilities,
        "centered_logits": centered_logits(probabilities),
        "legal_action_order": list(action_order),
        "legal_mask": [True] * len(action_order),
        "capture_source_binding": deepcopy(dict(expected_source_binding)),
    }


def _manifest_clones(manifest: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {clone["cell"]: clone for clone in manifest["clones"]}


def _validate_cell_sources(
    manifest: Mapping[str, Any],
    cell_sources: Mapping[str, Any],
) -> dict[str, tuple[Any, Callable[[], Mapping[str, Any]]]]:
    """Reject aliased/sequential sources before any T kernel invocation."""

    if not isinstance(cell_sources, Mapping) or set(cell_sources) != set(ALL_CELLS):
        raise ContractViolation("complete rectangle requires four source-bound per-cell readers")
    clones = _manifest_clones(manifest)
    clone_objects: set[int] = set()
    reader_objects: set[int] = set()
    model_graph_objects: set[int] = set()
    kernel_source_objects: set[int] = set()
    resolved: dict[str, tuple[Any, Callable[[], Mapping[str, Any]]]] = {}
    for cell in ALL_CELLS:
        source = cell_sources[cell]
        _require_exact_keys(source, {"clone_handle", "reader"}, f"cell source {cell}")
        handle = source["clone_handle"]
        reader = source["reader"]
        if not callable(reader):
            raise ContractViolation(f"cell source {cell} reader is not callable")
        if id(handle) in clone_objects or id(reader) in reader_objects:
            raise ContractViolation(
                "clone handles and readers must be four distinct source objects; sequential reuse is forbidden"
            )
        clone_objects.add(id(handle))
        reader_objects.add(id(reader))
        binding = clones[cell]["source_binding"]
        live_state = getattr(handle, "port_free_state_bytes", None)
        model_graph_handle = getattr(handle, "model_graph_handle", None)
        kernel_source_handle = getattr(reader, "kernel_source_handle", None)
        if (
            live_state != clones[cell]["port_free_state_bytes"]
            or nonfactor_state_sha256(live_state)
            != binding["nonfactor_state_sha256"]
        ):
            raise ContractViolation(
                f"cell source {cell} captured nonfactor bytes differ from its manifest binding"
            )
        if model_graph_handle is None or kernel_source_handle is None:
            raise ContractViolation(
                f"cell source {cell} omits a concrete model graph or kernel source handle"
            )
        if (
            id(model_graph_handle) in model_graph_objects
            or id(kernel_source_handle) in kernel_source_objects
        ):
            raise ContractViolation(
                "model graph and kernel source handles must be distinct per cell; sequential one-model reuse is forbidden"
            )
        model_graph_objects.add(id(model_graph_handle))
        kernel_source_objects.add(id(kernel_source_handle))
        observed = {
            "clone_handle_id": getattr(handle, "clone_handle_id", None),
            "model_graph_id": getattr(handle, "model_graph_id", None),
            "reader_id": getattr(reader, "reader_id", None),
            "kernel_source_id": getattr(reader, "kernel_source_id", None),
        }
        if any(observed[field] != binding[field] for field in observed):
            raise ContractViolation(
                f"cell source {cell} live handle/reader identity differs from its manifest binding"
            )
        resolved[cell] = (handle, reader)
    return resolved


def _fit_payloads(
    manifest: Mapping[str, Any],
    kernels: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    logits = {cell: kernels[cell]["centered_logits"] for cell in T_CELLS}
    dimension = len(logits["i0p0"])
    if any(len(logits[cell]) != dimension for cell in T_CELLS):
        raise ContractViolation("T kernel dimensions differ")
    l00, l01, l10 = (logits[cell] for cell in T_CELLS)
    candidate_fit = {
        "class": "L_ip=m+u_i+v_p",
        "anchors": ["u_i0=0", "v_p0=0"],
        "m": list(l00),
        "u_i1": [a - b for a, b in zip(l10, l00)],
        "v_p1": [a - b for a, b in zip(l01, l00)],
        "scalar_dtype": "float64",
        "fitted_scalar_count": 3 * dimension,
        "exact_T_reconstruction": True,
    }
    null_fit = {
        "class": "three independent T-cell centered-logit vectors",
        "z_i0p0": list(l00),
        "z_i0p1": list(l01),
        "z_i1p0": list(l10),
        "fourth_cell_parameter": False,
        "scalar_dtype": "float64",
        "fitted_scalar_count": 3 * dimension,
        "exact_T_reconstruction": True,
    }
    candidate_logits = [a + b - c for a, b, c in zip(l10, l01, l00)]
    null_logits = [(a + b + c) / 3.0 for a, b, c in zip(l00, l01, l10)]
    q_candidate = _softmax(candidate_logits)
    q_null = _softmax(null_logits)
    manifest_digest = _digest(manifest)
    t_digest = _digest({cell: kernels[cell] for cell in T_CELLS})

    def receipt(arm: str, prediction_logits: list[float], prediction: list[float]) -> dict[str, Any]:
        body = {
            "arm": arm,
            "training_cells": list(T_CELLS),
            "predicted_cell": H_CELL,
            "prediction_centered_logits": prediction_logits,
            "prediction_probabilities": prediction,
            "dimension": dimension,
            "scalar_dtype": "float64",
            "fitted_scalar_count": 3 * dimension,
            "manifest_sha256": manifest_digest,
            "t_kernels_sha256": t_digest,
            "h_kernel_reads_before_seal": 0,
            "h_fields_present": False,
        }
        return {**body, "receipt_sha256": _digest(body)}

    candidate_receipt = receipt("candidate", candidate_logits, q_candidate)
    null_receipt = receipt("null", null_logits, q_null)
    return candidate_fit, null_fit, candidate_receipt, null_receipt


def select_terminal_branch(
    *,
    construction_valid: bool,
    host_reachable: bool,
    pre_reveal_js: float | None = None,
    d_candidate: float | None = None,
    d_null: float | None = None,
) -> str:
    """Apply the frozen branch precedence without interpreting the result."""

    if construction_valid is not True:
        return INVALID
    if host_reachable is not True:
        return HOST_UNREACHABLE
    if pre_reveal_js is None or not math.isfinite(pre_reveal_js):
        return INVALID
    if pre_reveal_js < PRE_REVEAL_JS_THRESHOLD:
        return NONDISCRIMINATING
    if d_candidate is None or d_null is None or not all(math.isfinite(value) for value in (d_candidate, d_null)):
        return INVALID
    if (
        d_candidate >= FALSIFICATION_D_C_THRESHOLD
        or d_candidate - d_null >= FALSIFICATION_RELATIVE_THRESHOLD
    ):
        return FALSIFIED
    delta = d_null - d_candidate
    if d_candidate <= SUPPORT_D_C_THRESHOLD and delta >= SUPPORT_DELTA_THRESHOLD:
        return SUPPORTED
    return AMBIGUOUS


def _zero_activity(*, registered_audits: int = 1) -> dict[str, int]:
    values = {name: 0 for name in ACTIVITY_CAPS}
    values["registered_audits"] = registered_audits
    return values


def observe_registered_host() -> dict[str, Any]:
    """Inspect registration metadata only; construct no model, core, or clone."""

    inspections: list[dict[str, Any]] = []
    qualified: list[tuple[str, str, Callable[..., Any]]] = []
    for module in (supplied_runtime, event_runtime):
        token_candidates: list[str] = []
        marked: list[str] = []
        for name, value in vars(module).items():
            if not callable(value):
                continue
            lowered = name.lower()
            if all(token in lowered for token in ("identity", "period", "clone")):
                token_candidates.append(name)
            if getattr(value, "__hmasd_host_contract__", None) == HOST_CONTRACT_ID:
                marked.append(name)
                qualified.append((module.__name__, name, value))
        inspections.append(
            {
                "module": module.__name__,
                "identity_period_clone_named_callables": sorted(token_candidates),
                "contract_marked_callables": sorted(marked),
            }
        )
    status = "reachable" if len(qualified) == 1 else "unreachable" if not qualified else "invalid_registration"
    return {
        "host_contract_id": HOST_CONTRACT_ID,
        "status": status,
        "qualified_constructor": (
            f"{qualified[0][0]}.{qualified[0][1]}" if len(qualified) == 1 else None
        ),
        "inspection": inspections,
        "mssr_shared_model_factory_present": all(
            callable(getattr(supplied_runtime, name, None))
            for name in ("make_mssr_joint_model_owner", "make_mssr_joint_runtime_core")
        ),
        "rejected_substitutions": ["toy", "ORBIT", "lifecycle", "MSSR"],
        "constructor_count": len(qualified),
    }


def _base_result(branch: str, host_observation: Mapping[str, Any], activity: Mapping[str, int]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "design_id": DESIGN_ID,
        "treatment_id": TREATMENT_ID,
        "candidate_version": CANDIDATE_VERSION,
        "terminal_branch": branch,
        "host_observation": deepcopy(dict(host_observation)),
        "activity_caps": dict(ACTIVITY_CAPS),
        "activity_counts": dict(activity),
        "scientific_nonclaims": list(SCIENTIFIC_NONCLAIMS),
        "scientific_disposition": None,
        "successor_selected": False,
        "publication_binding": {
            "accepted_source_commit": None,
            "accepted_result_commit": None,
            "source_locator": "experiments/candidates/vsp_c1/constrained_fourth_corner_logit_completion.py",
            "index_locator": "docs/research/candidates/vsp_c1/CODE_SCIENCE_INDEX.md",
            "result_locator": None,
            "acceptance_owned_by": "Code Project Manager",
        },
    }


def build_unreachable_result(host_observation: Mapping[str, Any]) -> dict[str, Any]:
    """Build the exact zero-runtime terminal package for absent host support."""

    if host_observation.get("status") != "unreachable" or host_observation.get("constructor_count") != 0:
        raise ContractViolation("unreachable result requires a fresh zero-constructor observation")
    result = _base_result(HOST_UNREACHABLE, host_observation, _zero_activity())
    result.update(
        {
            "bound_identities": {
                "checkpoint_id": None,
                "roster_id": None,
                "boundary_state_id": None,
                "i0": None,
                "i1": None,
                "p0": None,
                "p1": None,
                "heldout_cell": H_CELL,
                "legal_action_order": None,
            },
            "state_equality_manifest": None,
            "kernels": {},
            "predictor_fits": {},
            "sealed_prediction_receipts": {},
            "attempted_kernel_reads": [],
            "pre_reveal_js": None,
            "estimands": {
                "D_C": None,
                "D_N": None,
                "Delta": None,
                "mixed_logit_residual": None,
            },
            "construction_failures": [
                "no production constructor is registered for the exact authenticated identity-period four-clone host contract"
            ],
            "interpretation": (
                "Reactivate only with a prospectively reachable 2x2 authenticated "
                "identity-period rectangle satisfying the exact port-free "
                "equality/common-support manifest."
            ),
        }
    )
    return result


def _invalid_result(
    host_observation: Mapping[str, Any],
    activity: Mapping[str, int],
    failure: str,
    *,
    attempted_kernel_reads: Sequence[Mapping[str, Any]] = (),
    state_equality_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result = _base_result(INVALID, host_observation, activity)
    result.update(
        {
            "construction_failures": [failure],
            "state_equality_manifest": (
                deepcopy(dict(state_equality_manifest))
                if state_equality_manifest is not None
                else None
            ),
            "kernels": {},
            "predictor_fits": {},
            "sealed_prediction_receipts": {},
            "attempted_kernel_reads": [deepcopy(dict(row)) for row in attempted_kernel_reads],
            "pre_reveal_js": None,
            "estimands": {"D_C": None, "D_N": None, "Delta": None, "mixed_logit_residual": None},
        }
    )
    return result


def execute_complete_rectangle(
    manifest: Mapping[str, Any],
    cell_sources: Mapping[str, Mapping[str, Any]],
    *,
    host_observation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute one complete retained/registered rectangle under sealed ordering.

    This function owns the only read order: validate/freeze, read T, fit and
    seal both predictions, apply the divergence gate, then (and only then) read
    H exactly once.  It never advances an environment or calls a learner.
    """

    observation = dict(host_observation or {
        "host_contract_id": HOST_CONTRACT_ID,
        "status": "retained_fixture_only",
        "qualified_constructor": None,
        "inspection": [],
        "mssr_shared_model_factory_present": True,
        "rejected_substitutions": ["toy", "ORBIT", "lifecycle", "MSSR"],
        "constructor_count": 0,
    })
    activity = _zero_activity()
    transcript = [{"event_ordinal": 0, "event": "freeze"}]
    attempted_reads: list[dict[str, Any]] = []
    validated_manifest: Mapping[str, Any] | None = None
    try:
        validate_state_manifest(manifest)
        validated_manifest = manifest
        sources = _validate_cell_sources(manifest, cell_sources)
        activity.update({"checkpoints": 1, "rosters": 1, "boundary_states": 1, "clones": 4})
        actions = list(manifest["legal_action_order"])
        clones = _manifest_clones(manifest)
        kernels: dict[str, dict[str, Any]] = {}
        for ordinal, cell in enumerate(T_CELLS, start=1):
            activity["focused_production_kernel_calls"] += 1
            attempted_reads.append(
                {
                    "attempt_ordinal": activity["focused_production_kernel_calls"],
                    "cell": cell,
                    "kernel_source_id": clones[cell]["source_binding"]["kernel_source_id"],
                }
            )
            kernels[cell] = _validate_kernel(
                sources[cell][1](),
                cell=cell,
                action_order=actions,
                expected_source_binding=clones[cell]["source_binding"],
            )
            transcript.append({"event_ordinal": ordinal, "event": "kernel_read", "cell": cell})

        candidate_fit, null_fit, candidate_receipt, null_receipt = _fit_payloads(manifest, kernels)
        activity["deterministic_predictor_fits"] = 2
        activity["sealed_prediction_receipts"] = 2
        transcript.extend(
            [
                {"event_ordinal": 4, "event": "seal", "arm": "candidate", "receipt_sha256": candidate_receipt["receipt_sha256"]},
                {"event_ordinal": 5, "event": "seal", "arm": "null", "receipt_sha256": null_receipt["receipt_sha256"]},
            ]
        )
        q_candidate = candidate_receipt["prediction_probabilities"]
        q_null = null_receipt["prediction_probabilities"]
        pre_reveal_js = jensen_shannon(q_candidate, q_null)
        branch = select_terminal_branch(
            construction_valid=True,
            host_reachable=True,
            pre_reveal_js=pre_reveal_js,
        )
        estimands: dict[str, Any] = {"D_C": None, "D_N": None, "Delta": None, "mixed_logit_residual": None}
        if branch != NONDISCRIMINATING:
            activity["focused_production_kernel_calls"] += 1
            attempted_reads.append(
                {
                    "attempt_ordinal": activity["focused_production_kernel_calls"],
                    "cell": H_CELL,
                    "kernel_source_id": clones[H_CELL]["source_binding"]["kernel_source_id"],
                }
            )
            kernels[H_CELL] = _validate_kernel(
                sources[H_CELL][1](),
                cell=H_CELL,
                action_order=actions,
                expected_source_binding=clones[H_CELL]["source_binding"],
            )
            transcript.append({"event_ordinal": 6, "event": "h_reveal", "cell": H_CELL})
            d_candidate = jensen_shannon(kernels[H_CELL]["probabilities"], q_candidate)
            d_null = jensen_shannon(kernels[H_CELL]["probabilities"], q_null)
            delta = d_null - d_candidate
            l00, l01, l10, l11 = (kernels[cell]["centered_logits"] for cell in ALL_CELLS)
            residual = [d - c - b + a for a, b, c, d in zip(l00, l01, l10, l11)]
            estimands = {"D_C": d_candidate, "D_N": d_null, "Delta": delta, "mixed_logit_residual": residual}
            branch = select_terminal_branch(
                construction_valid=True,
                host_reachable=True,
                pre_reveal_js=pre_reveal_js,
                d_candidate=d_candidate,
                d_null=d_null,
            )
        result = _base_result(branch, observation, activity)
        result.update(
            {
                "bound_identities": {
                    "checkpoint_id": manifest["checkpoint_id"],
                    "roster_id": manifest["roster_id"],
                    "boundary_state_id": manifest["boundary_state_id"],
                    **dict(manifest["selected_factors"]),
                    "heldout_cell": H_CELL,
                    "legal_action_order": actions,
                },
                "state_equality_manifest": deepcopy(dict(manifest)),
                "kernels": kernels,
                "predictor_fits": {"candidate": candidate_fit, "null": null_fit},
                "sealed_prediction_receipts": {"candidate": candidate_receipt, "null": null_receipt},
                "attempted_kernel_reads": attempted_reads,
                "event_transcript": transcript,
                "pre_reveal_js": pre_reveal_js,
                "estimands": estimands,
                "construction_failures": [],
                "interpretation": (
                    "Supports only one local constrained additive fourth-corner action-kernel prediction unavailable to the matched support-saturated null."
                    if branch == SUPPORTED
                    else "No threshold/cell adjustment, retry or replacement construction."
                ),
            }
        )
        validate_audit_result(result, allow_retained_fixture=True)
        return result
    except ContractViolation as exc:
        return _invalid_result(
            observation,
            activity,
            str(exc),
            attempted_kernel_reads=attempted_reads,
            state_equality_manifest=validated_manifest,
        )
    except Exception as exc:  # external registered reader fails closed
        return _invalid_result(
            observation,
            activity,
            f"{type(exc).__name__}: {exc}",
            attempted_kernel_reads=attempted_reads,
            state_equality_manifest=validated_manifest,
        )


def _registered_constructor() -> tuple[dict[str, Any], Callable[..., Any] | None]:
    observation = observe_registered_host()
    if observation["status"] != "reachable":
        return observation, None
    locator = observation["qualified_constructor"]
    for module in (supplied_runtime, event_runtime):
        for name, value in vars(module).items():
            if callable(value) and f"{module.__name__}.{name}" == locator:
                return observation, value
    return {**observation, "status": "invalid_registration"}, None


@dataclass
class _RegisteredAuditReservation:
    output_path: Path
    claim_path: Path
    output_handle: Any
    claim_handle: Any
    active: bool = True


def run_registered_audit(
    reservation: _RegisteredAuditReservation,
) -> dict[str, Any]:
    """Run only after the one output and shared audit claim are held."""

    if (
        not isinstance(reservation, _RegisteredAuditReservation)
        or reservation.active is not True
        or reservation.output_handle.closed
        or reservation.claim_handle.closed
    ):
        raise ContractViolation(
            "registered audit requires one active pre-execution output/claim reservation"
        )

    observation, constructor = _registered_constructor()
    if observation["status"] == "unreachable":
        result = build_unreachable_result(observation)
        validate_audit_result(result)
        return result
    if constructor is None:
        return _invalid_result(observation, _zero_activity(), "registered host constructor count is not exactly one")
    try:
        host = constructor()
        if not isinstance(host, Mapping):
            raise ContractViolation("registered host constructor must return a mapping")
        _require_exact_keys(host, {"manifest", "cell_sources"}, "registered host")
        return execute_complete_rectangle(
            host["manifest"], host["cell_sources"], host_observation=observation
        )
    except ContractViolation as exc:
        return _invalid_result(observation, _zero_activity(), str(exc))
    except Exception as exc:  # constructor/runtime faults are technical invalidity
        return _invalid_result(
            observation, _zero_activity(), f"{type(exc).__name__}: {exc}"
        )


def _write_claimed_handle(handle: Any, payload: Mapping[str, Any]) -> bytes:
    encoded = (
        json.dumps(
            dict(payload),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    handle.seek(0)
    handle.truncate(0)
    handle.write(encoded)
    handle.flush()
    os.fsync(handle.fileno())
    return encoded


def claim_and_run_registered_audit(
    output_path: str | Path,
    claim_path: str | Path,
    *,
    audit_runner: Callable[[_RegisteredAuditReservation], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Exclusively reserve output and the shared one-audit claim before execution.

    The claim is independent of the output name, so a second destination cannot
    authorize another audit under the same claim.  Once the claim exists, any
    later failure remains terminal; neither reservation is recycled.
    """

    output = Path(output_path)
    claim = Path(claim_path)
    if output.resolve() == claim.resolve():
        raise ContractViolation("registered audit output and claim paths must differ")
    output.parent.mkdir(parents=True, exist_ok=True)
    claim.parent.mkdir(parents=True, exist_ok=True)

    output_handle = output.open("x+b")
    pending_output_payload = {
        "schema_version": SCHEMA_VERSION,
        "treatment_id": TREATMENT_ID,
        "output": str(output.resolve()),
        "claim": str(claim.resolve()),
        "status": "output_reserved_before_shared_claim",
    }
    _write_claimed_handle(output_handle, pending_output_payload)
    try:
        claim_handle = claim.open("x+b")
    except BaseException:
        output_handle.close()
        raise

    reservation = _RegisteredAuditReservation(
        output_path=output,
        claim_path=claim,
        output_handle=output_handle,
        claim_handle=claim_handle,
    )
    reservation_payload = {
        "schema_version": SCHEMA_VERSION,
        "treatment_id": TREATMENT_ID,
        "output": str(output.resolve()),
        "claim": str(claim.resolve()),
        "status": "reserved_before_source_execution",
    }
    claim_established = False
    try:
        _write_claimed_handle(output_handle, reservation_payload)
        _write_claimed_handle(claim_handle, reservation_payload)
        claim_established = True
        runner = run_registered_audit if audit_runner is None else audit_runner
        result = dict(runner(reservation))
        validate_audit_result(result)
        encoded_result = _write_claimed_handle(output_handle, result)
        _write_claimed_handle(
            claim_handle,
            {
                **reservation_payload,
                "status": "completed",
                "terminal_branch": result["terminal_branch"],
                "result_sha256": hashlib.sha256(encoded_result).hexdigest(),
            },
        )
        return result
    except BaseException as exc:
        if claim_established:
            try:
                _write_claimed_handle(
                    claim_handle,
                    {
                        **reservation_payload,
                        "status": "failed_after_claim",
                        "failure": f"{type(exc).__name__}: {exc}",
                    },
                )
            except BaseException:
                pass
        raise
    finally:
        reservation.active = False
        output_handle.close()
        claim_handle.close()


def _validate_base(result: Mapping[str, Any]) -> None:
    for field, expected in (
        ("schema_version", SCHEMA_VERSION),
        ("raw_output_binding", RAW_OUTPUT_BINDING),
        ("design_id", DESIGN_ID),
        ("treatment_id", TREATMENT_ID),
        ("candidate_version", CANDIDATE_VERSION),
    ):
        if result.get(field) != expected:
            raise ContractViolation(f"result {field} differs")
    if result.get("activity_caps") != ACTIVITY_CAPS:
        raise ContractViolation("activity caps differ from the frozen payload")
    counts = result.get("activity_counts")
    if not isinstance(counts, Mapping) or set(counts) != set(ACTIVITY_CAPS):
        raise ContractViolation("activity counts have the wrong fields")
    for name, cap in ACTIVITY_CAPS.items():
        value = counts[name]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > cap:
            raise ContractViolation(f"activity count {name} violates its cap")
    if any(counts[name] != 0 for name in (
        "environment_transitions", "learner_calls", "trainer_calls", "optimizer_updates",
        "return_evaluations", "model_fits", "stochastic_calls", "sweeps_retries_rescues",
    )):
        raise ContractViolation("forbidden scientific/runtime activity is nonzero")
    if result.get("scientific_nonclaims") != list(SCIENTIFIC_NONCLAIMS) or result.get("scientific_disposition") is not None or result.get("successor_selected") is not False:
        raise ContractViolation("scientific nonclaim/disposition boundary differs")
    publication = result.get("publication_binding")
    expected_publication = {
        "accepted_source_commit": None,
        "accepted_result_commit": None,
        "source_locator": "experiments/candidates/vsp_c1/constrained_fourth_corner_logit_completion.py",
        "index_locator": "docs/research/candidates/vsp_c1/CODE_SCIENCE_INDEX.md",
        "result_locator": None,
        "acceptance_owned_by": "Code Project Manager",
    }
    if publication != expected_publication:
        raise ContractViolation("runtime artifact fabricates or alters publication acceptance binding")


def validate_audit_result(
    result: Mapping[str, Any],
    *,
    allow_retained_fixture: bool = False,
) -> None:
    """Independently recompute manifest, fits, seals, estimands and precedence."""

    if not isinstance(result, Mapping):
        raise ContractViolation("audit result must be a mapping")
    _validate_base(result)
    branch = result.get("terminal_branch")
    counts = result["activity_counts"]
    if branch == HOST_UNREACHABLE:
        observation = result.get("host_observation")
        if not isinstance(observation, Mapping) or observation.get("status") != "unreachable" or observation.get("constructor_count") != 0:
            raise ContractViolation("host-unreachable branch lacks a zero-constructor observation")
        expected = _zero_activity()
        if counts != expected:
            raise ContractViolation("host-unreachable branch must have zero scientific/runtime/construction activity")
        if result.get("kernels") != {} or result.get("predictor_fits") != {} or result.get("sealed_prediction_receipts") != {} or result.get("pre_reveal_js") is not None:
            raise ContractViolation("host-unreachable branch contains kernel or prediction evidence")
        if result.get("state_equality_manifest") is not None:
            raise ContractViolation("host-unreachable branch fabricates a state manifest")
        if result.get("attempted_kernel_reads") != []:
            raise ContractViolation("host-unreachable branch contains attempted kernel reads")
        if select_terminal_branch(construction_valid=True, host_reachable=False) != branch:
            raise ContractViolation("host-unreachable branch precedence differs")
        _canonical_bytes(result)
        return
    if branch == INVALID:
        if not result.get("construction_failures"):
            raise ContractViolation("invalid construction lacks a concrete failure")
        attempts = result.get("attempted_kernel_reads")
        if not isinstance(attempts, Sequence) or isinstance(attempts, (str, bytes)):
            raise ContractViolation("invalid construction attempted-read evidence differs")
        if len(attempts) != counts["focused_production_kernel_calls"]:
            raise ContractViolation("invalid construction attempted reads do not match call count")
        manifest = result.get("state_equality_manifest")
        expected_sources: dict[str, str] = {}
        if manifest is not None:
            validate_state_manifest(manifest)
            expected_sources = {
                cell: clone["source_binding"]["kernel_source_id"]
                for cell, clone in _manifest_clones(manifest).items()
            }
        for ordinal, row in enumerate(attempts, start=1):
            _require_exact_keys(
                row,
                {"attempt_ordinal", "cell", "kernel_source_id"},
                "attempted kernel read",
            )
            if (
                row["attempt_ordinal"] != ordinal
                or row["cell"] not in ALL_CELLS
                or not isinstance(row["kernel_source_id"], str)
                or not row["kernel_source_id"]
            ):
                raise ContractViolation("invalid construction attempted-read evidence differs")
            if row["cell"] != ALL_CELLS[ordinal - 1]:
                raise ContractViolation("invalid construction attempted reads violate sealed cell order")
            if expected_sources and row["kernel_source_id"] != expected_sources[row["cell"]]:
                raise ContractViolation("invalid construction attempted read source differs from manifest")
        _canonical_bytes(result)
        return
    if branch not in {NONDISCRIMINATING, FALSIFIED, SUPPORTED, AMBIGUOUS}:
        raise ContractViolation("unknown terminal branch")
    observation = result.get("host_observation")
    status = observation.get("status") if isinstance(observation, Mapping) else None
    if status != "reachable" and not (allow_retained_fixture and status == "retained_fixture_only"):
        raise ContractViolation("complete result is not bound to a registered host")

    manifest = result.get("state_equality_manifest")
    validate_state_manifest(manifest)
    expected_identities = {
        "checkpoint_id": manifest["checkpoint_id"],
        "roster_id": manifest["roster_id"],
        "boundary_state_id": manifest["boundary_state_id"],
        **dict(manifest["selected_factors"]),
        "heldout_cell": H_CELL,
        "legal_action_order": list(manifest["legal_action_order"]),
    }
    if result.get("bound_identities") != expected_identities:
        raise ContractViolation("bound checkpoint/roster/state/factor/action identities differ")
    kernels = result.get("kernels")
    if not isinstance(kernels, Mapping):
        raise ContractViolation("complete result kernels must be a mapping")
    expected_cells = set(T_CELLS) if branch == NONDISCRIMINATING else set(ALL_CELLS)
    if set(kernels) != expected_cells:
        raise ContractViolation("kernel cells differ from sealed branch requirements")
    normalized = {}
    clones = _manifest_clones(manifest)
    for cell in kernels:
        stored = kernels[cell]
        if not isinstance(stored, Mapping) or set(stored) != {
            "probabilities",
            "centered_logits",
            "legal_action_order",
            "legal_mask",
            "capture_source_binding",
        }:
            raise ContractViolation(f"kernel {cell} stored fields differ")
        normalized[cell] = _validate_kernel(
            {
                "probabilities": stored["probabilities"],
                "legal_action_order": stored["legal_action_order"],
                "legal_mask": stored["legal_mask"],
                "capture_source_binding": stored["capture_source_binding"],
            },
            cell=cell,
            action_order=manifest["legal_action_order"],
            expected_source_binding=clones[cell]["source_binding"],
        )
    for cell in kernels:
        if not _same_floats(kernels[cell].get("centered_logits", []), normalized[cell]["centered_logits"]):
            raise ContractViolation(f"kernel {cell} centered logits were not recomputed")

    candidate_fit, null_fit, candidate_receipt, null_receipt = _fit_payloads(manifest, normalized)
    if result.get("predictor_fits") != {"candidate": candidate_fit, "null": null_fit}:
        raise ContractViolation("predictor fit/capacity/T-reconstruction proof differs")
    receipts = result.get("sealed_prediction_receipts")
    if receipts != {"candidate": candidate_receipt, "null": null_receipt}:
        raise ContractViolation("sealed prediction receipt or digest differs")
    pre_reveal = jensen_shannon(candidate_receipt["prediction_probabilities"], null_receipt["prediction_probabilities"])
    if not math.isclose(
        _finite_scalar(result.get("pre_reveal_js"), "pre-reveal JS"),
        pre_reveal,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ContractViolation("pre-reveal JS was not recomputed from sealed predictions")

    expected_transcript = [
        {"event_ordinal": 0, "event": "freeze"},
        {"event_ordinal": 1, "event": "kernel_read", "cell": "i0p0"},
        {"event_ordinal": 2, "event": "kernel_read", "cell": "i0p1"},
        {"event_ordinal": 3, "event": "kernel_read", "cell": "i1p0"},
        {"event_ordinal": 4, "event": "seal", "arm": "candidate", "receipt_sha256": candidate_receipt["receipt_sha256"]},
        {"event_ordinal": 5, "event": "seal", "arm": "null", "receipt_sha256": null_receipt["receipt_sha256"]},
    ]
    if branch != NONDISCRIMINATING:
        expected_transcript.append({"event_ordinal": 6, "event": "h_reveal", "cell": H_CELL})
    if result.get("event_transcript") != expected_transcript:
        raise ContractViolation("H was not read exactly once after both prediction seals")

    expected_attempt_cells = list(T_CELLS) if branch == NONDISCRIMINATING else list(ALL_CELLS)
    expected_attempts = [
        {
            "attempt_ordinal": ordinal,
            "cell": cell,
            "kernel_source_id": clones[cell]["source_binding"]["kernel_source_id"],
        }
        for ordinal, cell in enumerate(expected_attempt_cells, start=1)
    ]
    if result.get("attempted_kernel_reads") != expected_attempts:
        raise ContractViolation("attempted kernel reads do not match bound per-cell sources")

    expected_counts = _zero_activity()
    expected_counts.update(
        {
            "checkpoints": 1,
            "rosters": 1,
            "boundary_states": 1,
            "clones": 4,
            "focused_production_kernel_calls": 3 if branch == NONDISCRIMINATING else 4,
            "deterministic_predictor_fits": 2,
            "sealed_prediction_receipts": 2,
        }
    )
    if counts != expected_counts:
        raise ContractViolation("activity counts do not match the sealed event transcript")

    if branch == NONDISCRIMINATING:
        expected_branch = select_terminal_branch(construction_valid=True, host_reachable=True, pre_reveal_js=pre_reveal)
        if expected_branch != NONDISCRIMINATING or result.get("estimands") != {"D_C": None, "D_N": None, "Delta": None, "mixed_logit_residual": None}:
            raise ContractViolation("pre-reveal nondiscriminating branch leaks H or differs")
    else:
        h = normalized[H_CELL]
        d_candidate = jensen_shannon(h["probabilities"], candidate_receipt["prediction_probabilities"])
        d_null = jensen_shannon(h["probabilities"], null_receipt["prediction_probabilities"])
        delta = d_null - d_candidate
        l00, l01, l10, l11 = (normalized[cell]["centered_logits"] for cell in ALL_CELLS)
        residual = [d - c - b + a for a, b, c, d in zip(l00, l01, l10, l11)]
        estimands = result.get("estimands")
        expected_estimands = {"D_C": d_candidate, "D_N": d_null, "Delta": delta, "mixed_logit_residual": residual}
        if not isinstance(estimands, Mapping) or set(estimands) != set(expected_estimands):
            raise ContractViolation("estimand fields differ")
        for name in ("D_C", "D_N", "Delta"):
            if not math.isclose(
                _finite_scalar(estimands[name], f"estimand {name}"),
                expected_estimands[name],
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise ContractViolation(f"estimand {name} differs")
        if not _same_floats(estimands["mixed_logit_residual"], residual):
            raise ContractViolation("mixed-logit residual differs")
        expected_branch = select_terminal_branch(
            construction_valid=True,
            host_reachable=True,
            pre_reveal_js=pre_reveal,
            d_candidate=d_candidate,
            d_null=d_null,
        )
        if branch != expected_branch:
            raise ContractViolation("terminal branch precedence differs from recomputed estimands")
    _canonical_bytes(result)


def write_result_once(path: str | Path, result: Mapping[str, Any]) -> None:
    """Validate and install one JSON result without overwriting an earlier one."""

    validate_audit_result(result)
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite one-shot VSPC1-A1 artifact: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(dict(result), indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, destination)
        temporary.unlink()
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the one-shot VSPC1-A1 registered fourth-corner audit. The "
            "current host is expected to fail closed as unreachable."
        )
    )
    parser.add_argument("--output", required=True, help="new one-shot JSON result path")
    parser.add_argument(
        "--claim",
        required=True,
        help="shared exclusive claim path for the one registered VSPC1-A1 audit",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    result = claim_and_run_registered_audit(args.output, args.claim)
    print(
        json.dumps(
            {
                "output": str(Path(args.output)),
                "claim": str(Path(args.claim)),
                "terminal_branch": result["terminal_branch"],
            },
            sort_keys=True,
        )
    )
    return 0


__all__ = [
    "ContractViolation",
    "build_unreachable_result",
    "centered_logits",
    "claim_and_run_registered_audit",
    "execute_complete_rectangle",
    "jensen_shannon",
    "nonfactor_state_sha256",
    "observe_registered_host",
    "run_registered_audit",
    "select_terminal_branch",
    "validate_audit_result",
    "validate_state_manifest",
    "write_result_once",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
