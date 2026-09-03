from __future__ import annotations

import json
from dataclasses import asdict
import hashlib

import pytest

from experiments.candidates.variable_n_fleet_churn_r02 import artifact
from experiments.candidates.variable_n_fleet_churn_r02 import panel
from experiments.candidates.variable_n_fleet_churn_r02.autodiff import ScalarTape
from experiments.candidates.variable_n_fleet_churn_r02.fixtures import expected_host_call_ledger
from experiments.candidates.variable_n_fleet_churn_r02.runner import (
    bind_exact_backward_capability,
    build_complete_document,
    orchestrate_presentation_evaluations,
)
from experiments.candidates.variable_n_fleet_churn_r02.probability import (
    construct_probability,
    deterministic_choice,
    diagnostic_cdf_probes,
    entropy,
    forced_log_probability,
)


def test_incomplete_terminal_is_create_once_and_independently_validated(tmp_path) -> None:
    receipt = {"schema": "SYNTHETIC_NON_RESULT_GATE", "passed": False}
    document = artifact.incomplete_document("bounded synthetic fault", receipt)
    path = tmp_path / artifact.INCOMPLETE_FILENAME
    artifact.write_create_once(path, document)
    assert artifact.read_and_validate(path) == document
    with pytest.raises(artifact.ArtifactError, match="already exists"):
        artifact.write_create_once(path, document)


def test_incomplete_terminal_rejects_extra_missing_and_tampered_identity(tmp_path) -> None:
    document = artifact.incomplete_document("synthetic", {"schema": "TEST"})
    for mutation in (
        {**document, "extra": 1},
        {key: value for key, value in document.items() if key != "reason"},
        {**document, "law_config": "tampered"},
        {**document, "namespace": "elsewhere"},
    ):
        with pytest.raises(artifact.ArtifactError):
            artifact.validate_incomplete_artifact(mutation)


def test_writer_rejects_undeclared_output_name(tmp_path) -> None:
    document = artifact.incomplete_document("synthetic", {"schema": "TEST"})
    with pytest.raises(artifact.ArtifactError, match="filename"):
        artifact.write_create_once(tmp_path / "aggregate.json", document)
    assert not list(tmp_path.iterdir())


def test_complete_validator_rejects_aggregate_counter_substitute() -> None:
    aggregate_only = {
        "schema": artifact.SCHEMA,
        "object": artifact.OBJECT,
        "law_config": artifact.LAW_CONFIG,
        "namespace": artifact.NAMESPACE,
        "status": "PASS_CONFORMANT",
        "inventory": {"top_level_rows": 304, "presentation_optimizer_evaluations": 292},
    }
    with pytest.raises(artifact.ArtifactError):
        artifact.validate_complete_artifact(aggregate_only)


def test_token_validator_reconstructs_probability_and_rejects_coordinated_payload_tamper() -> None:
    kernel = artifact._FrozenAtenKernel()
    probability = construct_probability((0.0, -1.0), (1, None), kernel)
    token_address = "SYNTHETIC/TOKEN/0"
    candidates = []
    for index, candidate in enumerate(probability.candidates):
        label = "NULL" if candidate is None else str(candidate)
        candidates.append({
            "address": f"{token_address}/CANDIDATE/{label}",
            "base_logit_hex": probability.logits[index].hex(),
            "final_logit_hex": probability.logits[index].hex(),
            "centered_hex": probability.centered[index].hex(),
            "q_hex": probability.q[index].hex(),
            "weight_hex": probability.weights[index].hex(),
            "mass": probability.masses[index],
            "probability_hex": probability.probabilities[index].hex(),
        })
    cdf = [
        {
            "address": f"{token_address}/CDF/{probe.edge_index}/{probe.name}",
            "action": probe.action,
            "rejected": probe.rejected,
            "probe_value": artifact._probe_value(probe.value),
        }
        for probe in diagnostic_cdf_probes(probability)
    ]
    digest = "0" * 64
    record = {
        "address": token_address,
        "fixed": False,
        "support": [1, None],
        "candidate_records": candidates,
        "cdf_records": cdf,
        "deterministic_command": deterministic_choice(probability),
        "selected_command": 101,
        "selected_opaque_rank": 1,
        "log_probability_hex": forced_log_probability(probability, 1, kernel).hex(),
        "entropy_hex": entropy(probability, kernel).hex(),
        "prefix_before_sha256": digest,
        "prefix_after_sha256": digest,
        "semantic_sha256": digest,
    }
    artifact._validate_token(record, token_address)
    tampered_candidates = [dict(row) for row in candidates]
    tampered_candidates[0]["final_logit_hex"] = (0.5).hex()
    tampered = {**record, "candidate_records": tampered_candidates, "semantic_sha256": "f" * 64}
    with pytest.raises(artifact.ArtifactError, match="reconstruction"):
        artifact._validate_token(tampered, token_address)


def _mechanical_token(address, support, logits, fixed):
    kernel = artifact._FrozenAtenKernel()
    from experiments.candidates.variable_n_fleet_churn_r02.probability import construct_fixed_probability
    probability = construct_fixed_probability(support[0]) if fixed else construct_probability(logits, support, kernel)
    candidates = []
    for index, candidate in enumerate(probability.candidates):
        label = "NULL" if candidate is None else str(candidate)
        candidates.append({
            "address": f"{address}/CANDIDATE/{label}",
            "base_logit_hex": probability.logits[index].hex(),
            "final_logit_hex": probability.logits[index].hex(),
            "centered_hex": probability.centered[index].hex(),
            "q_hex": probability.q[index].hex(),
            "weight_hex": probability.weights[index].hex(),
            "mass": probability.masses[index],
            "probability_hex": probability.probabilities[index].hex(),
        })
    cdf = [] if fixed else [
        {
            "address": f"{address}/CDF/{probe.edge_index}/{probe.name}",
            "action": probe.action,
            "rejected": probe.rejected,
            "probe_value": artifact._probe_value(probe.value),
        }
        for probe in diagnostic_cdf_probes(probability)
    ]
    selected = probability.candidates[0]
    digest = "1" * 64
    return {
        "address": address,
        "fixed": fixed,
        "support": list(support),
        "candidate_records": candidates,
        "cdf_records": cdf,
        "deterministic_command": deterministic_choice(probability),
        "selected_command": selected,
        "selected_opaque_rank": selected,
        "log_probability_hex": forced_log_probability(probability, selected, kernel).hex(),
        "entropy_hex": entropy(probability, kernel).hex(),
        "prefix_before_sha256": digest,
        "prefix_after_sha256": digest,
        "semantic_sha256": digest,
    }


def _mechanical_rows():
    rows = []
    for plan in panel.all_top_rows():
        tokens = []
        if plan.kind == "PRIMITIVE":
            primitive = plan.address.split("/")[1]
            token_plans = panel.primitive_token_plans(primitive)
            for token_plan in token_plans:
                if primitive == "DUPLICATE_TIE" and token_plan.token == 0:
                    logits = (0.0, 0.0, -1.0)
                elif primitive == "NEXTAFTER_STRICT" and token_plan.token == 0:
                    logits = (0.0, float.fromhex("-0x0.0000000000001p-1022"), -16.0)
                elif primitive == "FIXED_PREFIX_NULL":
                    logits = {0: (0.0,), 1: (0.0, -2.0, -3.0), 2: (-2.0, 0.0), 3: (0.0, -1.0)}[token_plan.token]
                else:
                    logits = (0.0,)
                tokens.append(_mechanical_token(f"{plan.address}/TOKEN/{token_plan.token}", token_plan.support, logits, token_plan.fixed))
        else:
            tokens = [_mechanical_token(f"{plan.address}/TOKEN/{token}", (1,), (0.0,), True) for token in range(4)]
        bare = {
            "address": plan.address,
            "kind": plan.kind,
            "presentation": plan.presentation,
            "fixture": plan.fixture,
            "arm": plan.arm,
            "canonical_sha256": "2" * 64,
            "inverse_map_sha256": "3" * 64,
            "physical_command": [1, 1, 1, 1],
            "opaque_command": [1, 1, 1, 1],
            "value_hex": 0.0.hex(),
            "joint_log_probability_hex": 0.0.hex(),
            "base_gradient_sha256": "4" * 64,
            "token_records": tokens,
        }
        rows.append({**bare, "predicate_records": artifact.make_predicate_records(plan.address, bare)})
    return rows


def test_complete_builder_validates_full_address_resolved_mechanical_packet() -> None:
    class FakeEvaluator:
        exact_backward_api = ScalarTape

        def evaluate_clone(self, plan, prestate):
            return {
                name: hashlib.sha256(f"{plan.top_address}/{name}".encode("ascii")).hexdigest()
                for name in (
                    "replay_sha256", "raw_gradient_sha256", "clipped_gradient_sha256",
                    "optimizer_sha256", "node_table_sha256",
                )
            }

    plans = panel.evaluations()
    prestates = {key: {"key": key, "step": 0} for key in {row.comparison_key for row in plans}}
    evaluations = list(orchestrate_presentation_evaluations(prestates, bind_exact_backward_capability(FakeEvaluator())))
    rows = _mechanical_rows()
    ledger = [asdict(row) for row in expected_host_call_ledger()]
    receipt = {"schema": "SYNTHETIC_NON_RESULT_GATE", "passed": True}
    identity = {
        "source_family": "experiments/candidates/variable_n_fleet_churn_r02",
        "source_revision": "5" * 64,
        "source_manifest_sha256": "6" * 64,
        "dependency_receipt_sha256": artifact._digest(receipt),
        "law_config": artifact.LAW_CONFIG,
        "a0_seed": 2026090191,
        "rng_master_sha256": "7" * 64,
        "fixtures": ["F_ZERO_TIE_V1", "F_DYADIC_DENSE_V1"],
        "arms": ["MAPR", "DIRECT"],
    }
    terminal_evidence = {
        "rows_sha256": artifact._digest(rows),
        "evaluations_sha256": artifact._digest(evaluations),
        "host_call_ledger_sha256": artifact._digest(ledger),
        "decision": "PASS_CONFORMANT",
    }
    document = build_complete_document(
        status="PASS_CONFORMANT",
        identity=identity,
        gate_receipt=receipt,
        host_call_ledger=ledger,
        rows=rows,
        evaluations=evaluations,
        terminal_predicate_records=artifact.make_predicate_records("TERMINAL", terminal_evidence),
    )
    assert document["inventory"]["presentation_optimizer_evaluations"] == 292
    tampered = json.loads(json.dumps(document))
    tampered["rows"][292]["token_records"][0]["candidate_records"][0]["mass"] -= 1
    with pytest.raises(artifact.ArtifactError):
        artifact.validate_complete_artifact(tampered)
