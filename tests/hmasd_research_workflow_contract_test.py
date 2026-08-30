from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS = REPO_ROOT / ".omp" / "AGENTS.md"
ROOT_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-root-control" / "SKILL.md"
EM_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-em-direction-cycle" / "SKILL.md"
CM_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-cm-engineering-cycle" / "SKILL.md"
RESULT_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-result-run" / "SKILL.md"
EXTERNAL_REVIEW_SKILL = (
    REPO_ROOT / ".omp" / "skills" / "hmasd-scientific-external-review" / "SKILL.md"
)
EM_AGENT = REPO_ROOT / ".omp" / "agents" / "hmasd-em.md"
CM_AGENT = REPO_ROOT / ".omp" / "agents" / "hmasd-cm.md"
CRITIC_AGENT = REPO_ROOT / ".omp" / "agents" / "hmasd-research-critic.md"
REVIEWER_AGENT = REPO_ROOT / ".omp" / "agents" / "hmasd-reviewer.md"
PROTOCOL = REPO_ROOT / "docs" / "project" / "HMASD_OMP_CONTROL_PLANE_PROTOCOL.md"
RESULT_SCHEMA = REPO_ROOT / "scripts" / "schemas" / "hmasd_agent_result.schema.json"

COMMON_V2_REQUIRED = [
    "schema_version",
    "role",
    "logical_identity",
    "generation",
    "assignment_id",
    "status",
    "materiality",
    "summary",
    "changed_paths",
    "state_refs",
    "artifact_refs",
    "checkpoint_sha",
    "decision_requests",
    "next_actions",
    "payload",
]
COMMON_V2_PAYLOADS = [
    "#/$defs/root_payload",
    "#/$defs/git_payload",
    "#/$defs/portfolio_payload",
    "#/$defs/em_payload",
    "#/$defs/cm_payload",
    "#/$defs/implementation_payload",
    "#/$defs/review_payload",
    "#/$defs/verification_payload",
    "#/$defs/run_payload",
    "#/$defs/transport_payload",
    "#/$defs/artifact_payload",
    "#/$defs/recovery_payload",
    "#/$defs/clerk_payload",
]


def _compact(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


def _schema() -> dict[str, Any]:
    return json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))


def _assert_all(text: str, fragments: tuple[str, ...]) -> None:
    for fragment in fragments:
        assert " ".join(fragment.lower().split()) in text, fragment


def test_root_routes_direction_science_only_through_em() -> None:
    shared = _compact(AGENTS)
    root = _compact(ROOT_SKILL)
    protocol = _compact(PROTOCOL)

    _assert_all(
        shared,
        (
            "Direction-scoped science always goes to the responsible EM",
            "Root never bypasses that EM by invoking a scientific leaf",
            "Root directly invokes EM and CM managers",
        ),
    )
    for text in (root, protocol):
        _assert_all(
            text,
            (
                "direction-scoped",
                "theorem",
                "concept",
                "mechanism",
                "counterexample",
                "synthesis",
                "interpretation",
                "directly to a generic or scientific leaf",
                "EM",
            ),
        )
    assert "em alone decides whether a direction-scoped analytical leaf is warranted" in root
    assert "em determines which, if any, direction analytical gaps justify leaf work" in protocol


def test_portfolio_leaves_are_limited_to_four_cross_direction_questions() -> None:
    shared = _compact(AGENTS)
    root = _compact(ROOT_SKILL)
    protocol = _compact(PROTOCOL)
    categories = (
        "shared-assumption audit",
        "complement/substitute analysis",
        "option-value analysis",
        "cross-direction risk analysis",
    )

    for text in (shared, root, protocol):
        for category in categories:
            assert category in text
        assert "cross-direction" in text
    _assert_all(
        root,
        (
            "These are the only Portfolio analytical leaf categories",
            "never ranks directions, allocates resources, changes lifecycle",
            "Root synthesizes cited mechanisms and dependencies, never votes, majorities, confidence tallies, leaf counts, or quorum",
        ),
    )
    _assert_all(
        shared,
        (
            "They never rank directions, allocate resources, change lifecycle",
            "Root synthesizes cited mechanisms and dependencies, not leaf counts",
        ),
    )


def test_analytical_dispatch_is_gap_driven_blind_and_negative_complete() -> None:
    shared = _compact(AGENTS)
    em_skill = _compact(EM_SKILL)
    em_agent = _compact(EM_AGENT)
    protocol = _compact(PROTOCOL)

    _assert_all(
        shared,
        (
            "only for an unanswered information gap that can change that manager's own decision",
            "Zero qualifying gaps dispatch zero leaves",
            "Counts follow gaps, never a fixed leaf quota, wave size, utilization target, vote, majority, or quorum",
            "First-wave packets contain no favored answer, desired `PASS`, sibling conclusion, vote tally, allocation preference, or other result leakage",
            "each remains blind to sibling results until it returns a substantive product or `NO_MATERIAL_INSIGHT`",
            "common analytical product records `assignment_id`, `gap_id`, `task_family`",
            "`NO_MATERIAL_INSIGHT` is a successful, terminal, negative-complete analytical product",
            "These rules add no scheduler, authority role, lifecycle state, result schema, or registry",
        ),
    )
    _assert_all(
        em_skill,
        (
            "Distinct named information gaps determine whether any leaf is needed, its task family, and the specialist mix",
            "counts, quotas, votes, and quorum never do",
            "Choose the task family that matches the product needed, not a persona",
            "Theorem/proof derivation",
            "Concept/principles validation",
            "Counterexample/adversarial search",
            "Source/evidence retrieval",
            "Different-family innovation",
            "give them the same neutral freeze and keep each blind to favored routes, EM conclusions, and sibling outputs",
            "Synthesize mechanisms and discriminators, never response counts",
            "Agreement is coverage rather than independent evidence",
            "`NO_MATERIAL_INSIGHT` is a successful negative-complete analytical product",
        ),
    )
    _assert_all(
        em_agent,
        (
            "zero gaps means zero leaves",
            "no quota, vote, agreement count, or quorum controls synthesis",
            "first wave the same neutral freeze and distinct mechanism-level lenses",
            "blind to favored routes, EM conclusions, and sibling outputs",
            "`NO_MATERIAL_INSIGHT` is successful negative-complete work",
        ),
    )
    _assert_all(
        protocol,
        (
            "Analytical work follows an unanswered, decision-relevant information gap, not a staffing template",
            "A fixed leaf quota, wave size, utilization target, vote, majority, or quorum is not evidence",
            "The product remains inside the role-specific payload",
            "the clean-cut `next_actions` array carries every explicit successor obligation",
            "no alternative carrier, authority, lifecycle registry, or scheduler",
        ),
    )


def test_scientific_critic_and_technical_reviewer_remain_distinct() -> None:
    em = _compact(EM_AGENT)
    cm = _compact(CM_AGENT)
    critic = _compact(CRITIC_AGENT)
    reviewer = _compact(REVIEWER_AGENT)
    cm_skill = _compact(CM_SKILL)

    assert "hmasd-research-critic" in em
    assert "hmasd-reviewer" not in em
    assert "hmasd-reviewer" in cm
    assert "hmasd-research-critic" not in cm
    _assert_all(
        critic,
        (
            "counterexample/adversarial review",
            "material scientific issue",
            "conditional claim-ceiling effect",
            "Do not accept or reject code",
            "EM alone disposes scientific issues",
            "A no-finding review is `NO_MATERIAL_INSIGHT`, never approval",
        ),
    )
    _assert_all(
        reviewer,
        (
            "frozen integrated engineering candidate",
            "material technical finding",
            "Do not assess scientific validity, novelty, causal meaning, claim ceiling",
            "Scientific criticism is a separate EM-owned process",
            "Review is advisory technical evidence for CM disposition",
            "A no-finding return is `NO_MATERIAL_INSIGHT` within that reviewed scope",
        ),
    )
    _assert_all(
        cm_skill,
        (
            "Reviewer evaluates engineering conformance only",
            "scientific criticism, claim validity, novelty, and causal interpretation remain outside its authority",
            "Keep leaf returns distinct",
        ),
    )


def test_cm_defaults_to_one_vertical_owner_and_splits_only_disjoint_gaps() -> None:
    skill = _compact(CM_SKILL)
    profile = _compact(CM_AGENT)

    _assert_all(
        skill,
        (
            "One vertically complete Implementer normally owns the bounded slice's code mapping, caller/interface investigation, implementation, and focused test edits",
            "Use `hmasd-project-scout` or `hmasd-code-scout` only when the requested product is itself a read-only map reused across multiple independent slices, or when no implementation is authorized",
            "Never put a separate Scout in front of an Implementer for the same slice merely because the surface is nontrivial or unfamiliar",
            "Decompose only unresolved technical gaps",
            "both their path ownership and their semantic/interface ownership are disjoint",
            "exactly one writer owns every overlapping boundary",
            "Reserve `hmasd-reviewer` for a genuinely high-risk delta",
        ),
    )
    _assert_all(
        profile,
        (
            "Default to one vertically complete Implementer that maps the exact surface, edits the code, and authors focused tests for that slice",
            "Do not create a scout-to-implementer-to-reviewer chain merely because the surface is unfamiliar",
            "Writer cardinality follows genuinely disjoint unresolved technical gaps, not consecutive workflow steps or a fixed specialist wave",
            "assigns exactly one writer to every overlapping boundary",
        ),
    )


def test_one_experiment_operator_owns_one_exact_command() -> None:
    shared = _compact(AGENTS)
    root = _compact(ROOT_SKILL)
    cm = _compact(CM_SKILL)
    result = _compact(RESULT_SKILL)

    _assert_all(
        shared,
        ("The Experiment Operator owns exactly one result-bearing command from `hub start` through terminal return",),
    )
    _assert_all(
        root,
        ("one Experiment Operator owns one exact result-bearing command",),
    )
    _assert_all(
        cm,
        (
            "Exactly one Experiment Operator owns that one command from launch through its terminal witness",
            "CM, Reviewer, and Verifier never duplicate or share command ownership",
        ),
    )
    _assert_all(
        result,
        (
            "Exactly one Experiment Operator owns exactly one command from launch through its terminal witness",
            "No CM, Reviewer, Verifier, or second Operator shares that command ownership",
        ),
    )


def test_exact_pro_pair_and_provider_commitment_mechanics_are_preserved() -> None:
    em = _compact(EM_SKILL)
    review = _compact(EXTERNAL_REVIEW_SKILL)
    shared = _compact(AGENTS)

    _assert_all(
        em,
        (
            "exactly one Pro Innovator from the neutral freeze before or alongside local work and exactly one Pro Convergence after local synthesis",
            "Innovator remains blind to EM conclusions, favored answers, and local results",
        ),
    )
    _assert_all(
        review,
        (
            "One fresh cycle has only these two Pro operations",
            "Bind `provider: chatgpt`",
            "`review_stage: pro_innovator`, `product_model: GPT-5.6 Sol`",
            "`reasoning_effort: Pro`",
            "idempotency key, fingerprint, and current transport tuple",
            "Only the current strict Agentify review surface may activate",
            "A committed or uncertain activation is sealed and observe-only through the same Agentify operation",
            "unknown commitment never activates again",
            "never creates a replacement sender or automatic resend",
        ),
    )
    assert "unknown commitment never resends" in shared


def test_common_v2_result_envelope_has_closed_multi_action_carrier() -> None:
    schema = _schema()
    properties = schema["properties"]
    definitions = schema["$defs"]

    assert schema["$id"] == "hmasd_agent_result"
    assert schema["additionalProperties"] is False
    assert schema["required"] == COMMON_V2_REQUIRED
    assert properties["schema_version"] == {"type": "integer", "const": 2}
    assert properties["status"]["enum"] == ["COMPLETED", "PARTIAL", "BLOCKED", "FAILED"]
    assert properties["materiality"]["enum"] == [
        "NONE",
        "LOCAL",
        "DIRECTION",
        "PORTFOLIO",
        "USER",
    ]
    assert [entry["$ref"] for entry in properties["payload"]["oneOf"]] == COMMON_V2_PAYLOADS
    assert "analytical_product" not in properties
    assert "analytical_product" not in definitions

    cm_payload = definitions["cm_payload"]
    assert cm_payload["properties"]["engineering_status"]["enum"] == [
        "IN_PROGRESS",
        "IMPLEMENTED",
        "UNCHANGED",
        "BLOCKED",
        "NOT_REACHED",
    ]
    assert cm_payload["properties"]["observation_status"]["enum"] == [
        "IN_PROGRESS",
        "OBSERVED",
        "NOT_OBSERVED",
        "NOT_REQUIRED",
    ]
    assert cm_payload["properties"]["verification_status"]["enum"] == [
        "IN_PROGRESS",
        "SATISFIED",
        "UNSATISFIED",
        "NOT_RUN",
    ]
    for payload_name in ("em_payload", "cm_payload"):
        payload = definitions[payload_name]
        assert {
            "semantic_product_ref",
            "persistence_status",
            "durable_state_ref",
            "candidate_sha",
            "integrated_sha",
        } <= set(payload["required"])
        assert payload["properties"]["persistence_status"]["enum"] == [
            "PREPARED",
            "PERSISTED",
            "INTEGRATED",
        ]
    action = definitions["action"]
    assert action["additionalProperties"] is False
    assert action["required"] == [
        "action_id",
        "kind",
        "owner",
        "input_refs",
        "dependencies",
        "authorized_effect_ref",
        "stop_or_reentry_ref",
    ]
    assert action["properties"]["owner"]["enum"] == [
        "ROOT",
        "EM",
        "CM",
        "CLERK",
        "TRANSPORT",
        "EXPERIMENT_OPERATOR",
        "USER",
    ]
    assert "next_action" not in properties
    assert properties["next_actions"] == {
        "type": "array",
        "items": {"$ref": "#/$defs/action"},
    }
    dependency = definitions["exact_dependency"]["oneOf"]
    assert dependency == [
        {"$ref": "#/$defs/producer_dependency"},
        {"$ref": "#/$defs/authority_dependency"},
    ]
    assert definitions["producer_dependency"]["additionalProperties"] is False
    assert definitions["authority_dependency"]["additionalProperties"] is False
    clerk_payload = definitions["clerk_payload"]
    assert clerk_payload["additionalProperties"] is False
    assert clerk_payload["required"] == [
        "kind",
        "job_id",
        "operation",
        "outcome",
        "observations",
    ]
    assert clerk_payload["properties"]["outcome"]["enum"] == [
        "COMPLETED",
        "REFUSED",
        "UNKNOWN",
    ]
    assert "packet_ref" not in clerk_payload["properties"]
    assert "receipt_refs" not in clerk_payload["properties"]
    transport = definitions["transport_payload"]
    assert "_".join(("transport", "state")) not in transport["properties"]
    assert set(transport["properties"]["phase"]["enum"]) == {
        "VALIDATE",
        "PREPARE_UI",
        "ARMED",
        "VERIFY_COMMITMENT",
        "WAIT_RESPONSE",
        "READ_RESPONSE",
        "PUBLISH_ARCHIVE",
        "TERMINAL",
    }
    assert set(transport["properties"]["commitment"]["enum"]) == {
        "ZERO_PROVEN",
        "UNRESOLVED",
        "ONE_EXACT",
        "VIOLATION",
    }
    assert {"product_model", "reasoning_effort", "message_capability"} <= set(
        transport["required"]
    )


def test_obsolete_clerk_operation_schema_is_absent() -> None:
    assert not (
        REPO_ROOT / "scripts" / "schemas" / "hmasd_clerk_operation.schema.json"
    ).exists()
