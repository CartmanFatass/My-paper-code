from __future__ import annotations

import copy
import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from tools.research.hypothesis_mechanisms import mechanism_cards


def _material_draft() -> dict[str, Any]:
    return {
        "assignment_id": "ASSIGN-001",
        "gap_id": "GAP-MECHANISM-001",
        "task_family": "genuinely_different_family_generation",
        "insight_status": "MATERIAL_INSIGHT",
        "claim": "Condition X may change outcome Y through intermediate M.",
        "evidence_status": "reported",
        "evidence_references": [
            {
                "reference_id": "PACKET-OBS-001",
                "locator": "observation.json#/measurements/0",
            }
        ],
        "assumptions": [
            "The frozen observation and its provenance are represented accurately."
        ],
        "falsifier_or_counterexample": (
            "A successful manipulation changes Y without the declared change in M."
        ),
        "uncertainty_limitations": [
            "The available observation does not distinguish mediation from measurement drift."
        ],
        "consequence_decision_relevance": (
            "A discriminator could determine whether an executable measurement request is useful."
        ),
        "recommendation": (
            "EM should consider the declared discriminator without treating this card as evidence."
        ),
        "mechanism_cards": [
            {
                "candidate_statement": (
                    "Condition X changes outcome Y through the proposed intermediate M."
                ),
                "mechanism_family": "intermediate_process",
                "mechanism_statement": (
                    "Condition X changes intermediate M before outcome Y is measured."
                ),
                "assumptions": [
                    {
                        "assumption_id": "A-CALIBRATED",
                        "statement": (
                            "The assignment and measurement procedures operate as declared."
                        ),
                    }
                ],
                "boundary_conditions": [
                    "The candidate is limited to the declared synthetic units and horizon."
                ],
                "predictions": [
                    {
                        "prediction_id": "P-ORDERED",
                        "statement": (
                            "Assignment to X precedes a change in M and then a change in Y."
                        ),
                        "observable": "Ordered measurements of M and Y",
                        "conditions": (
                            "Units are assigned as declared and instruments pass calibration."
                        ),
                        "expected_pattern": (
                            "M changes before Y in X but not comparator units."
                        ),
                        "uncertainty": (
                            "Timing resolution may make the order indeterminate."
                        ),
                        "falsifier_ids": ["F-NO-M"],
                        "rival_mechanism_ids": ["R-DRIFT"],
                        "discriminator_ids": ["D-REFERENCE"],
                    }
                ],
                "rival_mechanisms": [
                    {
                        "rival_mechanism_id": "R-DRIFT",
                        "family": "measurement_artifact",
                        "statement": (
                            "Acquisition drift changes recorded Y without changing the target construct."
                        ),
                        "contrast": (
                            "Drift predicts a shared reference offset; the proposed process does not."
                        ),
                    }
                ],
                "discriminators": [
                    {
                        "discriminator_id": "D-REFERENCE",
                        "statement": (
                            "Measure a reference quantity that shares acquisition but cannot respond through M."
                        ),
                        "prediction_ids": ["P-ORDERED"],
                        "rival_mechanism_ids": ["R-DRIFT"],
                        "indeterminate_outcome": (
                            "An unstable or insensitive reference leaves the two mechanisms unresolved."
                        ),
                        "controls": [
                            {
                                "control_type": "negative_outcome",
                                "statement": (
                                    "The reference shares acquisition pathways but cannot be changed by M."
                                ),
                            }
                        ],
                    }
                ],
                "falsifiers": [
                    {
                        "falsifier_id": "F-NO-M",
                        "statement": (
                            "Y changes reproducibly without the prespecified change in M."
                        ),
                        "assumption_ids": ["A-CALIBRATED"],
                        "consequence": (
                            "The proposed M-mediated candidate is incompatible with that result under the assumption."
                        ),
                    }
                ],
                "uncertainty_limitations": [
                    "M could be a marker rather than a mediator."
                ],
                "admissible_packet_ids": ["PACKET-OBS-001"],
            }
        ],
        "no_material_insight": None,
        "scientific_authority": "EM",
        "scientific_status_effect": "NONE",
        "lifecycle_status_effect": "NONE",
    }


def _no_material_insight_draft() -> dict[str, Any]:
    return {
        "assignment_id": "ASSIGN-002",
        "gap_id": "GAP-MECHANISM-EMPTY",
        "task_family": "genuinely_different_family_generation",
        "insight_status": "NO_MATERIAL_INSIGHT",
        "claim": "The frozen claim remains unchanged within the inspected scope.",
        "evidence_status": "not_reported",
        "evidence_references": [],
        "assumptions": [
            "Only the frozen local packet and declared method were in scope."
        ],
        "falsifier_or_counterexample": (
            "No new falsifier or counterexample was derived within the frozen scope."
        ),
        "uncertainty_limitations": [
            "Uninspected mechanisms may still change the answer."
        ],
        "consequence_decision_relevance": (
            "This return supplies no answer-changing scientific delta."
        ),
        "recommendation": (
            "EM should retain the residual gap and decide whether a new premise warrants reentry."
        ),
        "mechanism_cards": [],
        "no_material_insight": {
            "sources_inspected": [
                {
                    "reference_id": "PACKET-LOCAL-002",
                    "locator": "neutral-packet.json#/frozen_claim",
                }
            ],
            "methods_attempted": [
                "Derived observable implications and checked for a rival with a distinct prediction."
            ],
            "why_no_material_insight": (
                "No distinct mechanism produced a new answer-changing prediction from the admissible packet."
            ),
            "residual_uncertainty": (
                "A new mechanism, source, observation, premise, or corrected defect could reopen the gap."
            ),
        },
        "scientific_authority": "EM",
        "scientific_status_effect": "NONE",
        "lifecycle_status_effect": "NONE",
    }


def _codes_at(issues: list[dict[str, str]], path: str) -> set[str]:
    return {issue["code"] for issue in issues if issue["path"] == path}


def test_complete_mechanism_card_validates_without_scoring_or_decision() -> None:
    artifact = mechanism_cards.generate_artifact(_material_draft())

    assert mechanism_cards.validate_artifact(artifact) == []
    assert artifact["scientific_authority"] == "EM"
    assert artifact["scientific_status_effect"] == "NONE"
    assert artifact["lifecycle_status_effect"] == "NONE"
    assert "score" not in json.dumps(artifact).lower()
    card = artifact["mechanism_cards"][0]
    assert card["rival_mechanisms"]
    assert card["falsifiers"]
    assert card["discriminators"][0]["indeterminate_outcome"]


def test_missing_falsifier_or_rival_is_rejected() -> None:
    without_falsifier = _material_draft()
    without_falsifier["mechanism_cards"][0]["falsifiers"] = []
    falsifier_issues = mechanism_cards.validate_artifact(
        mechanism_cards.generate_artifact(without_falsifier)
    )
    assert "minimum" in _codes_at(
        falsifier_issues, "$.mechanism_cards[0].falsifiers"
    )
    assert "unknown_reference" in _codes_at(
        falsifier_issues, "$.mechanism_cards[0].predictions[0].falsifier_ids"
    )

    without_rival = _material_draft()
    without_rival["mechanism_cards"][0]["rival_mechanisms"] = []
    rival_issues = mechanism_cards.validate_artifact(
        mechanism_cards.generate_artifact(without_rival)
    )
    assert "minimum" in _codes_at(
        rival_issues, "$.mechanism_cards[0].rival_mechanisms"
    )
    assert "unknown_reference" in _codes_at(
        rival_issues, "$.mechanism_cards[0].predictions[0].rival_mechanism_ids"
    )


def test_generation_uses_deterministic_content_identifiers() -> None:
    draft = _material_draft()
    original = copy.deepcopy(draft)

    first = mechanism_cards.generate_artifact(draft)
    second = mechanism_cards.generate_artifact(copy.deepcopy(draft))

    assert draft == original
    assert first == second
    assert first["artifact_id"].startswith("HMA-")
    assert first["mechanism_cards"][0]["card_id"].startswith("HMC-")
    assert mechanism_cards.validate_artifact(first) == []


def test_no_material_insight_is_negative_complete_not_technical_failure() -> None:
    artifact = mechanism_cards.generate_artifact(_no_material_insight_draft())
    issues = mechanism_cards.validate_artifact(artifact)
    result = mechanism_cards.result_envelope("generate", issues, artifact=artifact)

    assert issues == []
    assert artifact["insight_status"] == "NO_MATERIAL_INSIGHT"
    assert artifact["mechanism_cards"] == []
    assert artifact["no_material_insight"]["sources_inspected"]
    assert artifact["no_material_insight"]["methods_attempted"]
    assert result["technical_status"] == "SUCCEEDED"
    assert result["scientific_status_effect"] == "NONE"
    assert result["lifecycle_status_effect"] == "NONE"


def test_cli_generate_returns_machine_readable_local_v1_envelope() -> None:
    with TemporaryDirectory() as directory:
        input_path = Path(directory) / "draft.json"
        input_path.write_text(json.dumps(_material_draft()), encoding="utf-8")
        stdout = StringIO()
        with redirect_stdout(stdout):
            exit_code = mechanism_cards.main(["generate", str(input_path)])

    result = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert result["schema_version"] == 1
    assert result["tool"] == "hypothesis_mechanisms"
    assert result["operation"] == "generate"
    assert result["valid"] is True
    assert result["artifact"]["mechanism_cards"][0]["rival_mechanisms"]
    assert result["scientific_authority"] == "EM"


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    del loader, tests, pattern
    return unittest.TestSuite(
        unittest.FunctionTestCase(value)
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    )


if __name__ == "__main__":
    unittest.main()
