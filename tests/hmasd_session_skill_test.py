from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"


def _skill(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def test_top_level_session_skills_are_discoverable_and_role_scoped() -> None:
    role_skills = {
        "hmasd-root-task": "Root",
        "hmasd-workflow-clerk-task": "Workflow-Clerk",
        "hmasd-portfolio-task": "Portfolio",
        "hmasd-em-task": "EM direction",
        "hmasd-cm-task": "CM direction",
    }

    for name, trigger in role_skills.items():
        text = _skill(name)
        frontmatter = text.split("---", 2)[1]
        assert f"name: {name}" in frontmatter
        assert "description: Use when" in frontmatter
        assert trigger.casefold() in frontmatter.casefold()

    for name in ("hmasd-slice-interface", "hmasd-operations-manual"):
        text = _skill(name)
        frontmatter = text.split("---", 2)[1]
        assert f"name: {name}" in frontmatter
        assert "description: Use when" in frontmatter


def test_participant_skills_expose_only_local_slice_and_return_interface() -> None:
    for name in ("hmasd-portfolio-task", "hmasd-em-task", "hmasd-cm-task"):
        text = _skill(name).casefold()
        assert "hmasd_session_envelope.py" in text
        assert "next_objective" in text
        assert "send_message_to_thread" in text
        assert "output.message" in text
        assert "list_threads" not in text
        assert "create_thread" not in text
        assert "wait_threads" not in text
        assert "topology snapshot" not in text

    shared = _skill("hmasd-slice-interface").casefold()
    assert "read-message" in shared
    assert "output.message" in shared
    assert "next_objective" in shared
    assert "topology" not in shared


def test_clerk_skill_owns_topology_and_exact_message_ingress() -> None:
    text = _skill("hmasd-workflow-clerk-task").casefold()

    assert "topology" in text
    assert "read-message" in text
    assert "non-envelope" in text
    assert "does not route" in text
    assert "output.message" in text
    assert "hmasd-operations-manual" in text

    manual = _skill("hmasd-operations-manual").casefold()
    assert "topology snapshot" in manual
    assert "direction-neutral" in manual
    assert "non-envelope" in manual


def test_every_leaf_returns_only_to_its_spawning_parent() -> None:
    profiles = sorted((ROOT / ".codex" / "agents").glob("hmasd-*.toml"))
    assert profiles
    for profile in profiles:
        text = profile.read_text(encoding="utf-8").casefold()
        assert "return only to the spawning parent" in text, profile.name
        assert "never call send_message_to_thread" in text, profile.name
        assert "workflow-clerk" in text, profile.name
        assert "never spawn or delegate another agent" in text, profile.name


def test_project_authority_names_only_the_current_session_skill_layer() -> None:
    agents = " ".join(
        (ROOT / "AGENTS.md").read_text(encoding="utf-8").split()
    ).casefold()
    protocol = " ".join(
        (ROOT / "docs" / "project" / "WORKFLOW_PROTOCOL.md")
        .read_text(encoding="utf-8")
        .split()
    ).casefold()

    for text in (agents, protocol):
        for name in (
            "hmasd-root-task",
            "hmasd-workflow-clerk-task",
            "hmasd-portfolio-task",
            "hmasd-em-task",
            "hmasd-cm-task",
            "hmasd-slice-interface",
            "hmasd-operations-manual",
        ):
            assert name in text
        assert "read-message" in text
        assert "leaf" in text
        assert "spawning parent" in text
