"""Create-once terminal artifact and independent structural validator for R02 A0."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from fractions import Fraction
from typing import Mapping, Sequence

from .fixtures import expected_host_call_ledger, validate_host_call_ledger
from .panel import (
    PREDICATE_NAMES,
    all_top_rows,
    evaluations,
    expected_cdf_probe_names,
    primitive_candidate_addresses,
    primitive_cdf_addresses,
)


SCHEMA = "VNFC_R02_A0_CONFORMANCE_ARTIFACT_V1"
INCOMPLETE_SCHEMA = "VNFC_R02_A0_INCOMPLETE_ARTIFACT_V1"
OBJECT = "VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0"
LAW_CONFIG = "VNFC-R02-ORC-B64-Q52-U64-V1"
NAMESPACE = "temp/vnfc-r02-a0/VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0"
COMPLETE_FILENAME = "A0_CONFORMANCE.json"
INCOMPLETE_FILENAME = "INCOMPLETE.json"


class ArtifactError(ValueError):
    pass


class _FrozenAtenKernel:
    """Exact shape-(1,) ATen callables already admitted by the dependency gate."""

    @staticmethod
    def _call(name: str, value: float) -> float:
        import torch
        tensor = torch.tensor([value], dtype=torch.float64, device="cpu").contiguous()
        return float(getattr(torch.ops.aten, name).default(tensor)[0].item())

    def sigmoid_R02(self, value: float) -> float:
        return self._call("sigmoid", value)

    def exp_R02(self, value: float) -> float:
        return self._call("exp", value)

    def log_R02(self, value: float) -> float:
        return self._call("log", value)

    def sqrt_R02(self, value: float) -> float:
        return self._call("sqrt", value)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii") + b"\n"


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _exact_keys(row: Mapping[str, object], expected: set[str], context: str) -> None:
    if set(row) != expected:
        raise ArtifactError(f"{context} schema differs")


def _validate_identity(identity: Mapping[str, object]) -> None:
    _exact_keys(identity, {
        "source_family", "source_revision", "source_manifest_sha256", "dependency_receipt_sha256",
        "law_config", "a0_seed", "rng_master_sha256", "fixtures", "arms",
    }, "identity")
    if identity["source_family"] != "experiments/candidates/variable_n_fleet_churn_r02":
        raise ArtifactError("source family differs")
    if identity["law_config"] != LAW_CONFIG or identity["a0_seed"] != 2026090191:
        raise ArtifactError("law/seed identity differs")
    if identity["fixtures"] != ["F_ZERO_TIE_V1", "F_DYADIC_DENSE_V1"] or identity["arms"] != ["MAPR", "DIRECT"]:
        raise ArtifactError("fixture/arm identity differs")
    for key in ("source_revision", "source_manifest_sha256", "dependency_receipt_sha256", "rng_master_sha256"):
        if not _sha256(identity[key]):
            raise ArtifactError(f"{key} is not a lowercase SHA-256")


def _validate_predicates(rows: object, owner_address: str, evidence_value: object) -> None:
    if not isinstance(rows, list) or len(rows) != len(PREDICATE_NAMES):
        raise ArtifactError("address-resolved predicate inventory differs")
    expected_addresses = {f"{owner_address}/PREDICATE/{name}" for name in PREDICATE_NAMES}
    seen = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise ArtifactError("predicate record is not an object")
        _exact_keys(row, {"address", "observed", "evidence_sha256"}, "predicate")
        if row["address"] not in expected_addresses or row["address"] in seen:
            raise ArtifactError("predicate address differs")
        if row["observed"] is not True or row["evidence_sha256"] != _digest(evidence_value):
            raise ArtifactError("typed predicate observation is false or not bound to its literal evidence")
        seen.add(row["address"])
    if seen != expected_addresses:
        raise ArtifactError("predicate address set differs")


def make_predicate_records(owner_address: str, evidence_value: object) -> list[dict[str, object]]:
    evidence_sha256 = _digest(evidence_value)
    return [
        {
            "address": f"{owner_address}/PREDICATE/{name}",
            "observed": True,
            "evidence_sha256": evidence_sha256,
        }
        for name in PREDICATE_NAMES
    ]


def _probe_value(value: object) -> str:
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    raise ArtifactError("CDF core probe value type differs")


def _validate_cdf(records: object, token_address: str, probability: object, fixed: bool) -> set[str]:
    from .probability import diagnostic_cdf_probes
    support_count = len(getattr(probability, "candidates"))
    if not isinstance(records, list):
        raise ArtifactError("CDF records must be a list")
    expected = set() if fixed else {f"{token_address}/CDF/{edge}/{probe}" for edge, probe in expected_cdf_probe_names(support_count)}
    core = {} if fixed else {
        f"{token_address}/CDF/{probe.edge_index}/{probe.name}": probe
        for probe in diagnostic_cdf_probes(probability)
    }
    seen = set()
    for record in records:
        if not isinstance(record, Mapping):
            raise ArtifactError("CDF record is not an object")
        _exact_keys(record, {"address", "action", "rejected", "probe_value"}, "CDF record")
        address = record["address"]
        if address not in expected or address in seen:
            raise ArtifactError("CDF address differs")
        if not isinstance(record["rejected"], bool) or not isinstance(record["probe_value"], str):
            raise ArtifactError("CDF probe encoding differs")
        expected_probe = core[address]
        if record["action"] != expected_probe.action or record["rejected"] != expected_probe.rejected or record["probe_value"] != _probe_value(expected_probe.value):
            raise ArtifactError("CDF probe value/action/rejection differs from independent reconstruction")
        probe = str(address).rsplit("/", 1)[-1]
        edge = int(str(address).split("/CDF/", 1)[1].split("/", 1)[0])
        if probe == "PRODUCTION_WORD_BELOW" and edge == 0:
            raise ArtifactError("nonexistent below-zero word was persisted")
        if probe == "PRODUCTION_WORD_ABOVE" and edge == support_count:
            raise ArtifactError("nonexistent above-one word was persisted")
        seen.add(address)
    if seen != expected:
        raise ArtifactError("CDF inventory differs")
    return seen


def _validate_token(record: Mapping[str, object], expected_address: str) -> tuple[set[str], set[str]]:
    from .probability import construct_fixed_probability, construct_probability, deterministic_choice, entropy, forced_log_probability
    _exact_keys(record, {
        "address", "fixed", "support", "candidate_records", "cdf_records", "deterministic_command",
        "selected_command", "selected_opaque_rank", "log_probability_hex", "entropy_hex",
        "prefix_before_sha256", "prefix_after_sha256", "semantic_sha256",
    }, "token record")
    if record["address"] != expected_address or not isinstance(record["fixed"], bool):
        raise ArtifactError("token address/fixed declaration differs")
    support = record["support"]
    candidates = record["candidate_records"]
    if not isinstance(support, list) or not support or not isinstance(candidates, list) or len(candidates) != len(support):
        raise ArtifactError("token support/candidate inventory differs")
    physical = support if record["fixed"] else support[:-1]
    if any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in physical):
        raise ArtifactError("support must use positive opaque ranks")
    if physical != sorted(set(physical)) or (not record["fixed"] and support[-1] is not None):
        raise ArtifactError("support must be ascending opaque rank with NULL last")
    expected_candidates = {f"{expected_address}/CANDIDATE/{'NULL' if item is None else item}" for item in support}
    seen_candidates = set()
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise ArtifactError("candidate record is not an object")
        _exact_keys(candidate, {"address", "base_logit_hex", "final_logit_hex", "centered_hex", "q_hex", "weight_hex", "mass", "probability_hex"}, "candidate")
        if candidate["address"] not in expected_candidates or candidate["address"] in seen_candidates:
            raise ArtifactError("candidate child address differs")
        if not isinstance(candidate["mass"], int) or candidate["mass"] <= 0:
            raise ArtifactError("candidate mass must be a positive integer")
        for key in ("base_logit_hex", "final_logit_hex", "centered_hex", "q_hex", "weight_hex", "probability_hex"):
            try:
                value = float.fromhex(str(candidate[key]))
            except ValueError as error:
                raise ArtifactError("candidate binary64 encoding differs") from error
            if not math_isfinite(value):
                raise ArtifactError("candidate contains a nonfinite value")
            if candidate[key] != value.hex() or (value == 0.0 and str(candidate[key]).startswith("-")):
                raise ArtifactError("candidate binary64 must use canonical exact hex and positive zero")
        seen_candidates.add(candidate["address"])
    if seen_candidates != expected_candidates:
        raise ArtifactError("candidate address inventory differs")
    kernel = _FrozenAtenKernel()
    probability = construct_fixed_probability(int(support[0])) if record["fixed"] else construct_probability(
        tuple(float.fromhex(str(row["final_logit_hex"])) for row in candidates),
        tuple(support),
        kernel,
    )
    for candidate, centered, q, weight, mass, probability_value in zip(
        candidates, probability.centered, probability.q, probability.weights, probability.masses, probability.probabilities,
    ):
        if candidate["centered_hex"] != centered.hex() or candidate["q_hex"] != q.hex() or candidate["weight_hex"] != weight.hex() or candidate["mass"] != mass or candidate["probability_hex"] != probability_value.hex():
            raise ArtifactError("candidate q/weight/mass/probability differs from independent reconstruction")
    if record["deterministic_command"] != deterministic_choice(probability):
        raise ArtifactError("deterministic opaque-rank command differs")
    selected_rank = record["selected_opaque_rank"]
    if selected_rank not in tuple(support):
        raise ArtifactError("selected opaque-rank command is outside support")
    expected_logp = forced_log_probability(probability, selected_rank, kernel)
    expected_entropy = entropy(probability, kernel)
    if record["log_probability_hex"] != expected_logp.hex() or record["entropy_hex"] != expected_entropy.hex():
        raise ArtifactError("forced log probability or entropy differs from independent reconstruction")
    if record["fixed"]:
        if len(support) != 1 or record["cdf_records"] != [] or int(candidates[0]["mass"]) != 2**52:
            raise ArtifactError("fixed token support/CDF law differs")
        if candidates[0]["base_logit_hex"] != 0.0.hex() or candidates[0]["final_logit_hex"] != 0.0.hex():
            raise ArtifactError("fixed token scalar fields must be canonical positive zero")
    else:
        if support[-1] is not None or sum(int(row["mass"]) for row in candidates) != 2**52:
            raise ArtifactError("variable support order or exact mass total differs")
    cdf = _validate_cdf(record["cdf_records"], expected_address, probability, bool(record["fixed"]))
    for key in ("prefix_before_sha256", "prefix_after_sha256", "semantic_sha256"):
        if not _sha256(record[key]):
            raise ArtifactError("token digest differs")
    for key in ("log_probability_hex", "entropy_hex"):
        try:
            value = float.fromhex(str(record[key]))
        except ValueError as error:
            raise ArtifactError("token scalar encoding differs") from error
        if not math_isfinite(value):
            raise ArtifactError("token scalar is nonfinite")
    return seen_candidates, cdf


def math_isfinite(value: float) -> bool:
    return value == value and value not in (float("inf"), float("-inf"))


def _validate_rows(rows: object) -> None:
    if not isinstance(rows, list) or len(rows) != 304:
        raise ArtifactError("top-level row cardinality differs")
    expected = {row.address: row for row in all_top_rows()}
    seen = set()
    primitive_candidates: set[str] = set()
    primitive_cdf: set[str] = set()
    for record in rows:
        if not isinstance(record, Mapping):
            raise ArtifactError("top-level row is not an object")
        _exact_keys(record, {
            "address", "kind", "presentation", "fixture", "arm", "canonical_sha256", "inverse_map_sha256",
            "physical_command", "opaque_command", "value_hex", "joint_log_probability_hex", "base_gradient_sha256",
            "token_records", "predicate_records",
        }, "top-level row")
        address = record["address"]
        plan = expected.get(address)
        if plan is None or address in seen:
            raise ArtifactError("top-level address differs")
        if (record["kind"], record["presentation"], record["fixture"], record["arm"]) != (plan.kind, plan.presentation, plan.fixture, plan.arm):
            raise ArtifactError("top-level address fields differ")
        for key in ("canonical_sha256", "inverse_map_sha256", "base_gradient_sha256"):
            if not _sha256(record[key]):
                raise ArtifactError("top-level digest differs")
        tokens = record["token_records"]
        if not isinstance(tokens, list) or len(tokens) != 4:
            raise ArtifactError("every top-level row must contain four token records")
        for token, token_record in enumerate(tokens):
            if not isinstance(token_record, Mapping):
                raise ArtifactError("token record is not an object")
            candidate_addresses, cdf_addresses = _validate_token(token_record, f"{address}/TOKEN/{token}")
            if plan.kind == "PRIMITIVE":
                primitive_candidates.update(candidate_addresses)
                primitive_cdf.update(cdf_addresses)
        _validate_predicates(record["predicate_records"], str(address), {key: record[key] for key in record if key != "predicate_records"})
        seen.add(address)
    if seen != set(expected):
        raise ArtifactError("top-level address set differs")
    if primitive_candidates != set(primitive_candidate_addresses()) or primitive_cdf != set(primitive_cdf_addresses()):
        raise ArtifactError("primitive 80/512 child address inventory differs")


def _validate_evaluations(records: object) -> None:
    if not isinstance(records, list) or len(records) != 292:
        raise ArtifactError("presentation evaluation cardinality differs")
    expected = evaluations()
    for record, plan in zip(records, expected):
        if not isinstance(record, Mapping):
            raise ArtifactError("evaluation is not an object")
        _exact_keys(record, {
            "comparison_key", "top_address", "presentation", "arm", "clone_ordinal", "source_prestate_sha256",
            "clone_prestate_sha256", "replay", "gradient", "optimizer", "predicate_records",
        }, "evaluation")
        if (record["comparison_key"], record["top_address"], record["presentation"], record["arm"], record["clone_ordinal"]) != (
            plan.comparison_key, plan.top_address, plan.presentation, plan.arm, plan.clone_ordinal,
        ):
            raise ArtifactError("evaluation address/clone identity differs")
        if not _sha256(record["source_prestate_sha256"]) or record["clone_prestate_sha256"] != record["source_prestate_sha256"]:
            raise ArtifactError("presentation evaluation is not an independent identical-prestate clone")
        for key, suffix in (("replay", "REPLAY"), ("gradient", "GRADIENT"), ("optimizer", "OPTIMIZER")):
            child = record[key]
            if not isinstance(child, Mapping):
                raise ArtifactError("evaluation child is not an object")
            _exact_keys(child, {"address", "input_sha256", "output_sha256"}, key)
            if child["address"] != f"{plan.top_address}/{suffix}" or not _sha256(child["input_sha256"]) or not _sha256(child["output_sha256"]):
                raise ArtifactError(f"{key} record differs")
        _validate_predicates(record["predicate_records"], plan.top_address, {key: record[key] for key in record if key != "predicate_records"})


def validate_complete_artifact(document: Mapping[str, object]) -> None:
    _exact_keys(document, {
        "schema", "object", "law_config", "namespace", "status", "identity", "dependency_gate_receipt",
        "inventory", "host_call_ledger", "rows", "evaluations", "terminal_predicate_records", "decision",
    }, "terminal artifact")
    if document["schema"] != SCHEMA or document["object"] != OBJECT or document["law_config"] != LAW_CONFIG or document["namespace"] != NAMESPACE:
        raise ArtifactError("terminal schema/object/law/namespace differs")
    if document["status"] not in ("PASS_CONFORMANT", "FAIL_LAW") or document["decision"] != document["status"]:
        raise ArtifactError("terminal decision differs")
    if not isinstance(document["identity"], Mapping):
        raise ArtifactError("identity is absent")
    _validate_identity(document["identity"])
    receipt = document["dependency_gate_receipt"]
    if not isinstance(receipt, Mapping) or _digest(receipt) != document["identity"]["dependency_receipt_sha256"]:
        raise ArtifactError("dependency receipt identity differs")
    inventory = document["inventory"]
    if inventory != {
        "top_level_rows": 304, "forward_rows": 292, "primitive_rows": 12, "token_records": 1216,
        "primitive_token_records": 48, "primitive_candidate_children": 80, "primitive_cdf_children": 512,
        "logical_group_arm_steps": 74, "presentation_optimizer_evaluations": 292,
        "replay_records": 292, "gradient_records": 292, "optimizer_records": 292,
    }:
        raise ArtifactError("exact inventory differs")
    if not isinstance(document["host_call_ledger"], list):
        raise ArtifactError("host-call ledger is absent")
    validate_host_call_ledger(document["host_call_ledger"])
    _validate_rows(document["rows"])
    _validate_evaluations(document["evaluations"])
    _validate_predicates(
        document["terminal_predicate_records"],
        "TERMINAL",
        {
            "rows_sha256": _digest(document["rows"]),
            "evaluations_sha256": _digest(document["evaluations"]),
            "host_call_ledger_sha256": _digest(document["host_call_ledger"]),
            "decision": document["decision"],
        },
    )


def validate_incomplete_artifact(document: Mapping[str, object]) -> None:
    _exact_keys(document, {"schema", "object", "law_config", "namespace", "status", "reason", "dependency_gate_receipt"}, "incomplete artifact")
    if document["schema"] != INCOMPLETE_SCHEMA or document["object"] != OBJECT or document["law_config"] != LAW_CONFIG or document["namespace"] != NAMESPACE or document["status"] != "INCOMPLETE":
        raise ArtifactError("incomplete terminal identity differs")
    if not isinstance(document["reason"], str) or not document["reason"] or not isinstance(document["dependency_gate_receipt"], Mapping):
        raise ArtifactError("incomplete terminal reason/receipt differs")


def write_create_once(path: Path, document: Mapping[str, object]) -> Path:
    resolved = Path(path)
    if resolved.name not in (COMPLETE_FILENAME, INCOMPLETE_FILENAME):
        raise ArtifactError("terminal output filename is undeclared")
    if resolved.name == COMPLETE_FILENAME:
        validate_complete_artifact(document)
    else:
        validate_incomplete_artifact(document)
    if not resolved.parent.is_dir():
        raise ArtifactError("declared output namespace must already exist")
    sibling = resolved.parent / (INCOMPLETE_FILENAME if resolved.name == COMPLETE_FILENAME else COMPLETE_FILENAME)
    if sibling.exists():
        raise ArtifactError("terminal artifacts are mutually exclusive")
    try:
        with resolved.open("xb") as handle:
            handle.write(_canonical_bytes(document))
    except FileExistsError as error:
        raise ArtifactError("terminal artifact is create-once and already exists") from error
    return resolved


def read_and_validate(path: Path) -> Mapping[str, object]:
    value = json.loads(Path(path).read_text("ascii"))
    if not isinstance(value, Mapping):
        raise ArtifactError("terminal artifact is not an object")
    if Path(path).name == COMPLETE_FILENAME:
        validate_complete_artifact(value)
    elif Path(path).name == INCOMPLETE_FILENAME:
        validate_incomplete_artifact(value)
    else:
        raise ArtifactError("terminal filename is undeclared")
    return value


def incomplete_document(reason: str, gate_receipt: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema": INCOMPLETE_SCHEMA,
        "object": OBJECT,
        "law_config": LAW_CONFIG,
        "namespace": NAMESPACE,
        "status": "INCOMPLETE",
        "reason": reason,
        "dependency_gate_receipt": dict(gate_receipt),
    }


def execute_a0(output_namespace: Path, gate_receipt: Mapping[str, object]) -> Mapping[str, object]:
    """Formal route seam.

    The effectful native/model runner is intentionally required.  Until CM wires
    that bounded runner, this returns an explicit incomplete terminal rather than
    silently substituting synthetic fixtures or aggregate counters.
    """
    output = Path(output_namespace)
    if output.as_posix().replace("\\", "/").rstrip("/") != NAMESPACE:
        raise ArtifactError("formal output namespace differs")
    if (output / COMPLETE_FILENAME).exists() or (output / INCOMPLETE_FILENAME).exists():
        raise ArtifactError("terminal artifact already exists")
    try:
        from .runner import build_complete_a0_document  # type: ignore[import-not-found]
        document = build_complete_a0_document(gate_receipt)
        if not isinstance(document, Mapping):
            raise ArtifactError("formal runner did not return an artifact object")
    except Exception as error:
        document = incomplete_document(f"{type(error).__name__}: {error}", gate_receipt)
        write_create_once(output / INCOMPLETE_FILENAME, document)
        return document
    write_create_once(output / COMPLETE_FILENAME, document)
    return document
