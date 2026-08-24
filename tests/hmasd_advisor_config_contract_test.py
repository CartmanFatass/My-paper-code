from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_CONFIG = """modelRoles:
  advisor: opencode-go/glm-5.3:high

advisor:
  enabled: true

autoResume: true

async:
  enabled: true

launch:
  enabled: true

task:
  maxConcurrency: 32
  maxRecursionDepth: 3
  enableEffort: true
  enableLsp: true
  agentAdvisor:
    hmasd-portfolio: openai-codex/gpt-5.6-sol:high
    hmasd-em: openai-codex/gpt-5.6-sol:high
    hmasd-cm: opencode-go/glm-5.3:high
    hmasd-implementer: opencode-go/glm-5.3:high
    hmasd-implementer-terra: opencode-go/glm-5.3:high
  disabledAgents:
    - scout
    - reviewer
    - sonic
    - designer
    - security-reviewer
"""

EXPECTED_ADVISORS = {
    "hmasd-portfolio": "openai-codex/gpt-5.6-sol:high",
    "hmasd-em": "openai-codex/gpt-5.6-sol:high",
    "hmasd-cm": "opencode-go/glm-5.3:high",
    "hmasd-implementer": "opencode-go/glm-5.3:high",
    "hmasd-implementer-terra": "opencode-go/glm-5.3:high",
}

EXPECTED_NO_ADVISOR = {
    "hmasd-project-scout",
    "hmasd-code-scout",
    "hmasd-reviewer",
    "hmasd-verifier",
    "hmasd-experiment-operator",
    "hmasd-workflow-recovery-manager",
    "hmasd-external-pro-transport",
    "hmasd-external-gemini-transport",
    "hmasd-research-scout",
    "hmasd-research-innovator",
    "hmasd-research-critic",
    "hmasd-research-principles-analyst",
    "hmasd-research-artifact-writer",
}


def _agent_advisor_mapping(config: str) -> dict[str, str]:
    lines = config.splitlines()
    start = lines.index("  agentAdvisor:") + 1
    mapping: dict[str, str] = {}
    for line in lines[start:]:
        if not line.startswith("    ") or line.startswith("    - "):
            break
        name, separator, model = line.strip().partition(": ")
        assert separator, line
        mapping[name] = model
    return mapping


def _frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    end = text.index("\n---\n", 4)
    return text[: end + 5]


def test_project_config_matches_phase_one_exactly() -> None:
    assert (REPO_ROOT / ".omp" / "config.yml").read_text(encoding="utf-8") == EXPECTED_CONFIG


def test_watchdog_routes_by_primary_role_without_authority() -> None:
    watchdog = (REPO_ROOT / ".omp" / "WATCHDOG.md").read_text(encoding="utf-8")
    expected_routes = (
        "Root                         -> architecture",
        "hmasd-portfolio, hmasd-em    -> science",
        "hmasd-cm                     -> architecture + engineering",
        "hmasd-implementer,\nhmasd-implementer-terra      -> engineering",
        "all other roles              -> no advice",
    )
    for route in expected_routes:
        assert route in watchdog
    assert "one role-aware" in watchdog.lower()
    assert "roster" not in watchdog.lower()
    assert "read-only" in watchdog.lower()
    assert "non-gating" in watchdog.lower()
    for forbidden in ("approve", "reject", "block", "authorize", "dispatch", "mutate", "run tests"):
        assert f"never {forbidden}" in watchdog.lower()


def test_native_advisor_matrix_and_cold_revival_metadata() -> None:
    config = (REPO_ROOT / ".omp" / "config.yml").read_text(encoding="utf-8")
    assert _agent_advisor_mapping(config) == EXPECTED_ADVISORS
    assert "modelRoles:\n  advisor: opencode-go/glm-5.3:high" in config

    agent_dir = REPO_ROOT / ".omp" / "agents"
    project_agents = {path.stem for path in agent_dir.glob("*.md")}
    assert project_agents == set(EXPECTED_ADVISORS) | EXPECTED_NO_ADVISOR
    for path in agent_dir.glob("*.md"):
        metadata = _frontmatter(path)
        assert "\nadvisor:" not in metadata
        assert "agentAdvisor" not in metadata

    instructions = (REPO_ROOT / ".omp" / "AGENTS.md").read_text(encoding="utf-8")
    watchdog = (REPO_ROOT / ".omp" / "WATCHDOG.md").read_text(encoding="utf-8")
    assert "task.agentAdvisor[agentName]" in watchdog
    assert "`session_init`" in instructions
    assert "`session_init`" in watchdog
    assert "cold revival" in instructions.lower()
    assert "cold revival" in watchdog.lower()
    assert "not a direct mutation of an already running Hub job by job ID" in watchdog
    assert "newly resolved child session rather than\nan in-place mutation" in watchdog
    assert "no Advisor" in watchdog


def test_disabled_bundled_agents_and_project_leaf_advisors_are_explicit() -> None:
    config = (REPO_ROOT / ".omp" / "config.yml").read_text(encoding="utf-8")
    disabled = ["scout", "reviewer", "sonic", "designer", "security-reviewer"]
    assert config.count("    - ") == len(disabled)
    for name in disabled:
        assert f"    - {name}\n" in config

    mapping = _agent_advisor_mapping(config)
    assert not (set(mapping) & EXPECTED_NO_ADVISOR)
    assert set(mapping) == set(EXPECTED_ADVISORS)
    agent_dir = REPO_ROOT / ".omp" / "agents"
    for path in agent_dir.glob("*.md"):
        assert "blocking: false" in _frontmatter(path)
