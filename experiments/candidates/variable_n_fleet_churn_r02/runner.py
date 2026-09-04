"""Fail-closed A0 orchestration and complete-document assembly boundary."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from typing import Callable, Mapping, Protocol, Sequence

from .artifact import LAW_CONFIG, NAMESPACE, OBJECT, SCHEMA, make_predicate_records, validate_complete_artifact
from .panel import Evaluation, evaluations


class RunnerError(RuntimeError):
    pass


REQUIRED_BACKWARD_CAPABILITY = "VNFC_R02_EXACT_FROZEN_BACKWARD_ORDER_V1"


class PresentationEvaluator(Protocol):
    exact_backward_api: object

    def evaluate_clone(self, plan: Evaluation, prestate: object) -> Mapping[str, object]: ...


@dataclass(frozen=True)
class ExactBackwardCapability:
    evaluator: PresentationEvaluator
    capability: str
    api_name: str


def bind_exact_backward_capability(evaluator: PresentationEvaluator) -> ExactBackwardCapability:
    from .autodiff import ScalarTape
    if getattr(evaluator, "exact_backward_api", None) is not ScalarTape or not callable(getattr(evaluator, "evaluate_clone", None)):
        raise RunnerError("evaluator is not bound to the source-owned ScalarTape API")
    return ExactBackwardCapability(evaluator, REQUIRED_BACKWARD_CAPABILITY, "ScalarTape")


def require_exact_backward_engine(engine: object) -> ExactBackwardCapability:
    if not isinstance(engine, ExactBackwardCapability) or engine.capability != REQUIRED_BACKWARD_CAPABILITY or engine.api_name != "ScalarTape":
        raise RunnerError("exact frozen backward-order capability is absent")
    from .autodiff import ScalarTape
    if getattr(engine.evaluator, "exact_backward_api", None) is not ScalarTape or not callable(getattr(engine.evaluator, "evaluate_clone", None)):
        raise RunnerError("exact backward capability lost its ScalarTape evaluator binding")
    return engine


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()


def orchestrate_presentation_evaluations(
    prestates: Mapping[str, object], capability: object
) -> tuple[dict[str, object], ...]:
    bound = require_exact_backward_engine(capability)
    plans = evaluations()
    required_keys = {plan.comparison_key for plan in plans}
    if set(prestates) != required_keys:
        raise RunnerError("logical group-arm prestate inventory differs from exact 74 keys")
    source_digests = {key: _canonical_digest(prestates[key]) for key in required_keys}
    records: list[dict[str, object]] = []
    for plan in plans:
        clone = deepcopy(prestates[plan.comparison_key])
        clone_digest = _canonical_digest(clone)
        if clone_digest != source_digests[plan.comparison_key]:
            raise RunnerError("presentation clone differs before evaluation")
        result = bound.evaluator.evaluate_clone(plan, clone)
        if not isinstance(result, Mapping) or set(result) != {
            "replay_sha256", "raw_gradient_sha256", "clipped_gradient_sha256",
            "optimizer_sha256", "node_table_sha256",
        } or any(not isinstance(result[key], str) or len(result[key]) != 64 for key in result):
            raise RunnerError("exact evaluator result identity schema differs")
        if _canonical_digest(prestates[plan.comparison_key]) != source_digests[plan.comparison_key]:
            raise RunnerError("evaluator mutated the shared logical prestate")
        replay_input = _canonical_digest({"prestate": clone_digest, "top_address": plan.top_address})
        gradient_input = _canonical_digest({"replay": result["replay_sha256"], "node_table": result["node_table_sha256"]})
        optimizer_input = _canonical_digest({"prestate": clone_digest, "raw_gradient": result["raw_gradient_sha256"]})
        bare: dict[str, object] = {
            "comparison_key": plan.comparison_key,
            "top_address": plan.top_address,
            "presentation": plan.presentation,
            "arm": plan.arm,
            "clone_ordinal": plan.clone_ordinal,
            "source_prestate_sha256": source_digests[plan.comparison_key],
            "clone_prestate_sha256": clone_digest,
            "replay": {"address": plan.replay_address, "input_sha256": replay_input, "output_sha256": result["replay_sha256"]},
            "gradient": {"address": plan.gradient_address, "input_sha256": gradient_input, "output_sha256": result["raw_gradient_sha256"]},
            "optimizer": {"address": plan.optimizer_address, "input_sha256": optimizer_input, "output_sha256": result["optimizer_sha256"]},
        }
        records.append({**bare, "predicate_records": make_predicate_records(plan.top_address, bare)})
    if len(records) != 292:
        raise AssertionError("presentation orchestration cardinality differs")
    return tuple(records)


def build_complete_document(
    *,
    status: str,
    identity: Mapping[str, object],
    gate_receipt: Mapping[str, object],
    host_call_ledger: Sequence[Mapping[str, object]],
    rows: Sequence[Mapping[str, object]],
    evaluations: Sequence[Mapping[str, object]],
    terminal_predicate_records: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Assemble, then independently validate, already computed literal evidence."""
    document = {
        "schema": SCHEMA,
        "object": OBJECT,
        "law_config": LAW_CONFIG,
        "namespace": NAMESPACE,
        "status": status,
        "identity": dict(identity),
        "dependency_gate_receipt": dict(gate_receipt),
        "inventory": {
            "top_level_rows": 304, "forward_rows": 292, "primitive_rows": 12, "token_records": 1216,
            "primitive_token_records": 48, "primitive_candidate_children": 80, "primitive_cdf_children": 512,
            "logical_group_arm_steps": 74, "presentation_optimizer_evaluations": 292,
            "replay_records": 292, "gradient_records": 292, "optimizer_records": 292,
        },
        "host_call_ledger": [dict(row) for row in host_call_ledger],
        "rows": [dict(row) for row in rows],
        "evaluations": [dict(row) for row in evaluations],
        "terminal_predicate_records": [dict(row) for row in terminal_predicate_records],
        "decision": status,
    }
    validate_complete_artifact(document)
    return document


def run_with_components(
    *,
    gate_receipt: Mapping[str, object],
    backward_engine: object,
    panel_request: Mapping[str, object],
) -> Mapping[str, object]:
    """Refuse before panel evaluation when the exact backward capability is absent."""
    capability = require_exact_backward_engine(backward_engine)
    prestates = panel_request.get("prestates")
    if not isinstance(prestates, Mapping):
        raise RunnerError("panel request lacks exact logical prestates")
    return {"evaluations": orchestrate_presentation_evaluations(prestates, capability)}


def build_complete_a0_document(gate_receipt: Mapping[str, object]) -> Mapping[str, object]:
    """CLI composition seam; currently blocked by the unresolved backward freeze."""
    raise RunnerError("exact frozen backward-order capability is absent; complete A0 construction refused")
