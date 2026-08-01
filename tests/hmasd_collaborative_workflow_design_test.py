from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO / ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md"
UI_PATH = SKILL_PATH.parent / "agents/openai.yaml"
ROLE_PATH = REPO / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md"


def test_collaborative_skill_is_the_only_design_collaboration_skill() -> None:
    assert SKILL_PATH.is_file()
    assert not (
        REPO / ".agents/skills/hmasd-deliberate-workflow-design/SKILL.md"
    ).exists()
    assert "name: hmasd-collaborative-workflow-design" in SKILL_PATH.read_text()

    skill = SKILL_PATH.read_text().lower()
    for retired_mechanism in (
        "decision map",
        "fog",
        "freeze",
        "high-amplification risk gate",
    ):
        assert retired_mechanism not in skill


def test_read_only_and_fully_specified_requests_take_short_paths() -> None:
    skill = " ".join(SKILL_PATH.read_text().split())
    assert "It does not need plan confirmation" in skill
    assert "zero-question path" in skill
    assert "changes at least one named plan field" in skill
    assert "one question at a time" in skill
    assert "recommended answer" in skill


def test_mutation_requires_one_visible_confirmed_plan() -> None:
    skill = " ".join(SKILL_PATH.read_text().split())
    for field in (
        "Requirements understanding",
        "Goal and non-goals",
        "Exact paths",
        "Intended changes",
        "Verification and risks",
    ):
        assert field in skill
    assert "Perform no mutation until" in skill
    assert "confirms the complete plan in natural language" in skill
    assert "present a revised complete plan" in skill


def test_role_routes_mutations_through_collaboration_before_audit() -> None:
    role = ROLE_PATH.read_text()
    skill = SKILL_PATH.read_text()
    assert "workflow_collaboration_skill=hmasd-collaborative-workflow-design" in role
    assert "workflow_zero_question_path=fully_specified_mutations" in skill
    assert "workflow_decision_question_condition=changes_named_plan_field" in skill
    assert "workflow_plan_confirmation=required_before_mutation" in skill
    assert "workflow_zero_question_path=" not in role
    assert "workflow_decision_question_condition=" not in role
    assert role.index("$hmasd-collaborative-workflow-design") < role.index(
        "$hmasd-workflow-change-audit"
    )


def test_skill_cannot_be_invoked_implicitly() -> None:
    assert "allow_implicit_invocation: false" in UI_PATH.read_text()
