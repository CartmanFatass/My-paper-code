"""Hermetic compatibility smoke for the prompt-native HMASD research contract.

This test reads repository authorities and profiles and compares realistic local
packets/results with their declared contracts. It does not intercept OMP,
implement a dispatcher, or claim to enforce runtime scheduling behavior.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATHS = {
    "shared": REPO_ROOT / ".omp" / "AGENTS.md",
    "root": REPO_ROOT / ".omp" / "skills" / "hmasd-root-control" / "SKILL.md",
    "em": REPO_ROOT / ".omp" / "skills" / "hmasd-em-direction-cycle" / "SKILL.md",
    "cm": REPO_ROOT / ".omp" / "skills" / "hmasd-cm-engineering-cycle" / "SKILL.md",
    "result": REPO_ROOT / ".omp" / "skills" / "hmasd-result-run" / "SKILL.md",
    "protocol": REPO_ROOT / "docs" / "project" / "HMASD_OMP_CONTROL_PLANE_PROTOCOL.md",
}
PROFILE_PATHS = {
    "em": REPO_ROOT / ".omp" / "agents" / "hmasd-em.md",
    "cm": REPO_ROOT / ".omp" / "agents" / "hmasd-cm.md",
    "critic": REPO_ROOT / ".omp" / "agents" / "hmasd-research-critic.md",
    "reviewer": REPO_ROOT / ".omp" / "agents" / "hmasd-reviewer.md",
    "principles": REPO_ROOT / ".omp" / "agents" / "hmasd-research-principles-analyst.md",
}
RESULT_SCHEMA = REPO_ROOT / "scripts" / "schemas" / "hmasd_agent_result.schema.json"

TEST_BOUNDARY = (
    "repository source-contract compatibility only; no OMP interception, runtime "
    "dispatcher, scheduler, or policy enforcement"
)
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64

DIRECTION_LEAF_BYPASS = {
    "assignment_id": "root-bypass-direction-alpha",
    "sender": "Root",
    "recipient": "hmasd-research-critic",
    "scope": "direction-scoped",
    "direction_id": "alpha",
    "task_family": "counterexample/adversarial search",
    "expected_contract_compatible": False,
}
DIRECTION_EM_ROUTE = {
    "assignment_id": "root-route-em-alpha",
    "sender": "Root",
    "recipient": "EM-alpha",
    "scope": "direction-scoped",
    "direction_id": "alpha",
    "requested_work": "interpret the frozen discriminator and decide leaf gaps",
    "expected_contract_compatible": True,
}
PORTFOLIO_SHARED_ASSUMPTION_ROUTE = {
    "assignment_id": "root-portfolio-shared-assumption",
    "sender": "Root",
    "recipient": "hmasd-research-principles-analyst",
    "scope": "portfolio-owned cross-direction",
    "directions": ["alpha", "beta"],
    "portfolio_category": "shared-assumption audit",
    "manager_owned_variable": "whether common observation bias changes capacity allocation rationale",
    "requested_product": {
        "dependency": "shared outcome-normalization assumption",
        "affected_directions": ["alpha", "beta"],
        "layer": "measurement model",
        "necessity": "both direction claims use normalized episodic return",
        "common_mode_failure_path": "normalization drift creates the same apparent gain",
        "independent_discriminator": "raw-event reconstruction on a held-out trace",
    },
    "expected_contract_compatible": True,
}


def _compact(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


def _authorities() -> dict[str, str]:
    return {name: _compact(path) for name, path in AUTHORITY_PATHS.items()}


def _profiles() -> dict[str, str]:
    return {name: _compact(path) for name, path in PROFILE_PATHS.items()}


def _ref(path: str, sha256: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256}


def _first_wave_packet(assignment_id: str, gap_id: str, lens: str) -> dict[str, Any]:
    return {
        "assignment_id": assignment_id,
        "gap_id": gap_id,
        "task_family": "counterexample/adversarial search",
        "manager_owned_variable": "finite claim ceiling for direction alpha",
        "neutral_freeze_ref": _ref(
            "docs/research/candidates/alpha/workflow/research/cycle-alpha-scope-freeze.md",
            SHA_A,
        ),
        "question": "Can the observed gain arise without the proposed credit-assignment mechanism?",
        "claim": "Mechanism M is necessary for the held-out coordination gain.",
        "authoritative_definitions": {
            "mechanism_m": "the frozen event-to-credit pathway in claim C-17",
            "comparator": "same learner and observations without pathway M",
        },
        "authoritative_refs": [
            _ref("docs/research/candidates/alpha/DIRECTION.md", SHA_B),
            _ref("docs/project/ALGORITHM_PRINCIPLES.md", SHA_C),
        ],
        "facts": ["The held-out trace has 64 episodes."],
        "external_evidence": [],
        "inference": ["The aggregate gain is compatible with more than one causal family."],
        "speculation": ["A timing artifact may mimic credit improvement."],
        "contradictions": ["One seed has no gain."],
        "assigned_lens": lens,
        "outcome_branches": {
            "positive": "return a minimal alternative mechanism and discriminator",
            "negative": "return bounded search coverage and surviving claim",
            "null": "preserve both causal families",
            "ambiguous": "identify the exact identifiability gap",
            "invalid": "return the violated input assumption",
            "technical_failure": "return an operational failure without scientific update",
        },
        "non_goals": ["implementation", "Portfolio ranking", "claim approval"],
        "ownership": {"science": "EM-alpha", "workflow_state": "EM-alpha"},
        "authorized_effects": ["read repository evidence", "read cited public sources"],
        "required_output": "common analytical product",
        "stop_condition": "one minimal witness or exhaustion of the frozen two-family search",
        "reentry_trigger": "new mechanism, source, observation, premise, or corrected defect",
        "sibling_result_refs": [],
    }


def _analytical_product(
    assignment_id: str,
    gap_id: str,
    insight_status: str,
) -> dict[str, Any]:
    material = insight_status == "MATERIAL_INSIGHT"
    return {
        "assignment_id": assignment_id,
        "gap_id": gap_id,
        "task_family": "counterexample/adversarial search",
        "question_answered": "Can the gain arise without mechanism M?",
        "insight_status": insight_status,
        "claim_or_product": (
            "A one-step observation delay reproduces the aggregate gain without mechanism M."
            if material
            else "No answer-changing counterexample followed within the frozen two-family search."
        ),
        "evidence_refs": [
            _ref("docs/research/candidates/alpha/evidence/trace-analysis.json", SHA_B)
        ],
        "evidence_locators": ["episodes[17:32].event_timestamps"],
        "sources_inspected": [
            "held-out trace episodes 17-32",
            "claim C-17 and comparator definition",
        ],
        "methods_attempted": [
            "one-step observation-delay construction",
            "reward-relabeling boundary case",
        ],
        "assumptions": ["trace timestamps are monotonic"],
        "applicability_boundary": "held-out alpha trace under frozen comparator only",
        "verified_facts": ["delayed observations preserve the reported aggregate score"],
        "external_evidence": [],
        "inference": [
            "mechanism M is not uniquely identified" if material else "the frozen search did not lower the claim ceiling"
        ],
        "speculation": [],
        "contradiction": [],
        "falsifier_or_counterexample": (
            "one-step observation-delay witness" if material else "none within the frozen bound"
        ),
        "surviving_alternatives": ["mechanism M", "timing artifact"],
        "uncertainty": "unsearched longer delays",
        "limitations": ["single held-out environment family"],
        "residual_gap": "test event-causal reconstruction on a second environment",
        "conditional_consequence": (
            "lower the claim from necessity to compatibility" if material else "no claim delta"
        ),
        "decision_relevance": "changes the EM-owned claim ceiling only if the witness is admissible",
        "recommendation": "run raw-event reconstruction before increasing the claim",
        "next_discriminator": "held-out raw-event reconstruction",
        "done_reason": "frozen search bound completed",
        "reentry_trigger": "a new trace, mechanism family, premise, or corrected defect",
        "why_no_material_insight": (
            None
            if material
            else "Neither attempted construction changed the claim within the admissible evidence boundary."
        ),
    }


def _result_fixture(
    assignment_id: str,
    product: dict[str, Any],
) -> dict[str, Any]:
    artifact_path = f"docs/research/candidates/alpha/evidence/{assignment_id}.json"
    product_bytes = json.dumps(
        product, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    artifact_sha = hashlib.sha256(product_bytes).hexdigest()
    return {
        "envelope": {
            "schema_version": 1,
            "role": "hmasd-research-critic",
            "logical_identity": "hmasd-research-critic",
            "generation": 1,
            "assignment_id": assignment_id,
            "status": "COMPLETED",
            "materiality": "DIRECTION",
            "summary": f"{product['insight_status']}: {product['claim_or_product']}",
            "changed_paths": [],
            "state_refs": [],
            "artifact_refs": [_ref(artifact_path, artifact_sha)],
            "checkpoint_sha": None,
            "decision_requests": [],
            "next_action": None,
            "payload": {
                "kind": "artifact",
                "paths": [artifact_path],
                "sha256_by_path": {artifact_path: artifact_sha},
            },
        },
        "analytical_product": product,
    }


def _assert_common_product(product: dict[str, Any]) -> None:
    common_fields = {
        "assignment_id",
        "gap_id",
        "task_family",
        "question_answered",
        "insight_status",
        "claim_or_product",
        "evidence_refs",
        "evidence_locators",
        "sources_inspected",
        "methods_attempted",
        "assumptions",
        "applicability_boundary",
        "verified_facts",
        "external_evidence",
        "inference",
        "speculation",
        "contradiction",
        "falsifier_or_counterexample",
        "surviving_alternatives",
        "uncertainty",
        "limitations",
        "residual_gap",
        "conditional_consequence",
        "decision_relevance",
        "recommendation",
        "next_discriminator",
        "done_reason",
        "reentry_trigger",
    }
    assert common_fields <= set(product)
    assert product["insight_status"] in {"MATERIAL_INSIGHT", "NO_MATERIAL_INSIGHT"}


def test_route_fixtures_match_repository_authority_not_a_runtime_dispatcher() -> None:
    authorities = _authorities()
    profiles = _profiles()

    assert "source-contract compatibility only" in TEST_BOUNDARY
    assert "no omp interception" in TEST_BOUNDARY.lower()
    assert DIRECTION_LEAF_BYPASS["expected_contract_compatible"] is False
    assert DIRECTION_LEAF_BYPASS["scope"] == "direction-scoped"
    assert DIRECTION_LEAF_BYPASS["recipient"] == "hmasd-research-critic"
    assert "direction-scoped science always goes to the responsible em" in authorities["shared"]
    assert "root never bypasses that em by invoking a scientific leaf" in authorities["shared"]
    assert "must not send direction-scoped theorem, concept, mechanism, counterexample" in authorities["root"]

    assert DIRECTION_EM_ROUTE["expected_contract_compatible"] is True
    assert DIRECTION_EM_ROUTE["recipient"] == "EM-alpha"
    assert "root directly invokes em and cm managers" in authorities["shared"]
    assert "root creates one meaning-complete assignment for that direction's responsible em" in authorities["root"]
    assert "direction-scoped scientific research manager" in profiles["em"]

    assert PORTFOLIO_SHARED_ASSUMPTION_ROUTE["expected_contract_compatible"] is True
    assert PORTFOLIO_SHARED_ASSUMPTION_ROUTE["scope"] == "portfolio-owned cross-direction"
    assert PORTFOLIO_SHARED_ASSUMPTION_ROUTE["portfolio_category"] == "shared-assumption audit"
    assert len(PORTFOLIO_SHARED_ASSUMPTION_ROUTE["directions"]) == 2
    for text in (authorities["shared"], authorities["root"], authorities["protocol"]):
        assert "shared-assumption audit" in text
        assert "cross-direction" in text
    assert "these are the only portfolio analytical leaf categories" in authorities["root"]
    assert "concept/principles" in profiles["principles"]


def test_blind_first_wave_and_material_or_negative_complete_results_are_compatible() -> None:
    authorities = _authorities()
    profiles = _profiles()
    first = _first_wave_packet("alpha-wave-critic", "gap-causal-alternative", "timing artifact")
    second = _first_wave_packet("alpha-wave-innovator", "gap-family-alternative", "credit aliasing")

    assert first["neutral_freeze_ref"] == second["neutral_freeze_ref"]
    assert first["question"] == second["question"]
    assert first["claim"] == second["claim"]
    assert first["assigned_lens"] != second["assigned_lens"]
    assert first["sibling_result_refs"] == second["sibling_result_refs"] == []
    for packet in (first, second):
        assert {
            "assignment_id",
            "gap_id",
            "task_family",
            "manager_owned_variable",
            "neutral_freeze_ref",
            "question",
            "claim",
            "authoritative_definitions",
            "authoritative_refs",
            "facts",
            "external_evidence",
            "inference",
            "speculation",
            "contradictions",
            "assigned_lens",
            "outcome_branches",
            "non_goals",
            "ownership",
            "authorized_effects",
            "required_output",
            "stop_condition",
            "reentry_trigger",
        } <= set(packet)
        assert not {
            "favored_answer",
            "desired_pass",
            "sibling_conclusion",
            "vote_tally",
            "allocation_preference",
        } & set(packet)

    assert "first-wave packets contain no favored answer" in authorities["shared"]
    assert "blind to favored routes, em conclusions, and sibling outputs" in profiles["em"]
    assert "a first-wave packet must be neutral and sibling-blind" in profiles["critic"]

    material_product = _analytical_product(
        "alpha-wave-critic", "gap-causal-alternative", "MATERIAL_INSIGHT"
    )
    no_insight_product = _analytical_product(
        "alpha-wave-innovator", "gap-family-alternative", "NO_MATERIAL_INSIGHT"
    )
    material = _result_fixture("alpha-wave-critic", material_product)
    no_insight = _result_fixture("alpha-wave-innovator", no_insight_product)
    schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    for fixture in (material, no_insight):
        errors = sorted(
            validator.iter_errors(fixture["envelope"]),
            key=lambda error: tuple(str(part) for part in error.path),
        )
        assert not errors, [error.message for error in errors]
        _assert_common_product(fixture["analytical_product"])
        assert fixture["analytical_product"]["assignment_id"] == fixture["envelope"]["assignment_id"]
        assert fixture["envelope"]["payload"]["kind"] == "artifact"
        artifact_path = fixture["envelope"]["payload"]["paths"][0]
        expected_sha = hashlib.sha256(
            json.dumps(
                fixture["analytical_product"], sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        assert fixture["envelope"]["payload"]["sha256_by_path"][artifact_path] == expected_sha

    assert material_product["insight_status"] == "MATERIAL_INSIGHT"
    assert material_product["why_no_material_insight"] is None
    assert no_insight_product["insight_status"] == "NO_MATERIAL_INSIGHT"
    assert no_insight_product["sources_inspected"]
    assert no_insight_product["methods_attempted"]
    assert no_insight_product["why_no_material_insight"]
    assert no_insight_product["uncertainty"]
    assert no_insight["envelope"]["status"] == "COMPLETED"
    assert "successful, terminal, negative-complete analytical product" in authorities["shared"]
    assert "no new result carrier, schema, role, registry, lifecycle, or scheduler is introduced" in authorities["protocol"]


def test_scientific_critic_and_technical_reviewer_fixtures_do_not_collapse() -> None:
    profiles = _profiles()
    authorities = _authorities()
    critic_assignment = {
        "role": "hmasd-research-critic",
        "owner": "EM-alpha",
        "target": "frozen scientific claim C-17 and its causal evidence links",
        "requested_product": "scientific issue packet with conditional claim-ceiling effect",
        "forbidden_decisions": ["code acceptance", "Portfolio allocation", "lifecycle"],
    }
    reviewer_assignment = {
        "role": "hmasd-reviewer",
        "owner": "CM-alpha",
        "target": "frozen integrated engineering candidate at base 1a2b3c4d",
        "requested_product": "technical findings with file/symbol locators and focused checks",
        "forbidden_decisions": ["scientific validity", "claim ceiling", "Portfolio value"],
    }

    assert critic_assignment["role"] != reviewer_assignment["role"]
    assert critic_assignment["owner"] == "EM-alpha"
    assert reviewer_assignment["owner"] == "CM-alpha"
    assert "counterexample/adversarial review" in profiles["critic"]
    assert "conditional claim-ceiling effect" in profiles["critic"]
    assert "do not accept or reject code" in profiles["critic"]
    assert "frozen integrated engineering candidate" in profiles["reviewer"]
    assert "material technical finding" in profiles["reviewer"]
    assert "do not assess scientific validity" in profiles["reviewer"]
    assert "scientific criticism is a separate em-owned process" in profiles["reviewer"]
    assert "reviewer evaluates engineering conformance only" in authorities["cm"]


def test_dual_disjoint_writer_plan_is_compatible_but_overlap_is_not() -> None:
    authorities = _authorities()
    profiles = _profiles()
    allowed_plan = {
        "integration_owner": "CM-alpha",
        "expected_contract_compatible": True,
        "shared_interfaces_frozen": ["scripts/schemas/hmasd_agent_result.schema.json@sha256:a"],
        "writers": [
            {
                "identity": "hmasd-implementer",
                "owned_paths": {"src/alpha/trace_loader.py", "tests/alpha_trace_loader_test.py"},
                "semantic_boundaries": {"trace-loader cache key"},
            },
            {
                "identity": "hmasd-implementer-terra",
                "owned_paths": {"src/alpha/report.py", "tests/alpha_report_test.py"},
                "semantic_boundaries": {"human-readable report rendering"},
            },
        ],
    }
    overlapping_plan = {
        "integration_owner": "CM-alpha",
        "expected_contract_compatible": False,
        "shared_interfaces_frozen": [],
        "writers": [
            {
                "identity": "hmasd-implementer",
                "owned_paths": {"src/alpha/result_writer.py"},
                "semantic_boundaries": {"common-v1 result envelope"},
            },
            {
                "identity": "hmasd-implementer-terra",
                "owned_paths": {"tests/alpha_result_contract_test.py"},
                "semantic_boundaries": {"common-v1 result envelope"},
            },
        ],
    }

    first_allowed, second_allowed = allowed_plan["writers"]
    assert allowed_plan["expected_contract_compatible"] is True
    assert first_allowed["owned_paths"].isdisjoint(second_allowed["owned_paths"])
    assert first_allowed["semantic_boundaries"].isdisjoint(second_allowed["semantic_boundaries"])
    assert allowed_plan["shared_interfaces_frozen"]

    first_overlap, second_overlap = overlapping_plan["writers"]
    assert overlapping_plan["expected_contract_compatible"] is False
    assert first_overlap["owned_paths"].isdisjoint(second_overlap["owned_paths"])
    assert first_overlap["semantic_boundaries"] & second_overlap["semantic_boundaries"] == {
        "common-v1 result envelope"
    }
    assert "both their path ownership and their semantic/interface ownership are disjoint" in authorities["cm"]
    assert "different files are insufficient" in authorities["cm"]
    assert "exactly one writer owns every overlapping boundary" in authorities["cm"]
    assert "assigns exactly one writer to every overlapping boundary" in profiles["cm"]


def test_one_exact_command_has_one_operator_owner() -> None:
    authorities = _authorities()
    profiles = _profiles()
    exact_command = {
        "command_fingerprint": SHA_A,
        "argv": [
            "python3",
            "scripts/hmasd_run.py",
            "execute",
            "--spec",
            "temp/directions/alpha/exp/run-017/runner-spec.json",
        ],
        "canonical_cwd": ".",
        "baseline_sha": "1" * 40,
        "config_sha256": SHA_B,
        "data_sha256": SHA_C,
        "rng_seed": 1701,
        "stop_condition": "terminal witness or 7200 seconds",
    }
    ownership = [
        {
            "logical_identity": "hmasd-experiment-operator",
            "command_fingerprint": exact_command["command_fingerprint"],
            "phase": "launch-through-terminal-witness",
        }
    ]
    invalid_duplicate_ownership = ownership + [
        {
            "logical_identity": "hmasd-experiment-operator-duplicate",
            "command_fingerprint": exact_command["command_fingerprint"],
            "phase": "launch-through-terminal-witness",
        }
    ]

    owners = [
        item
        for item in ownership
        if item["command_fingerprint"] == exact_command["command_fingerprint"]
    ]
    duplicate_owners = [
        item
        for item in invalid_duplicate_ownership
        if item["command_fingerprint"] == exact_command["command_fingerprint"]
    ]
    assert len(owners) == 1
    assert len(duplicate_owners) == 2
    assert "delegate each actual result-bearing command to exactly one experiment operator" in profiles["cm"]
    assert "exactly one experiment operator owns exactly one command" in authorities["result"]
    assert "no cm, reviewer, verifier, or second operator shares that command ownership" in authorities["result"]
    assert "cm, reviewer, and verifier never duplicate or share command ownership" in authorities["cm"]
