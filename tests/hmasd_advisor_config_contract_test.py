from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_CONFIG = """modelRoles:
  advisor: openai-codex/gpt-5.6-luna:xhigh

advisor:
  enabled: true

autoResume: true

async:
  enabled: true

launch:
  enabled: true

task:
  batch: true
  isolation:
    mode: auto
    apply: false
    merge: patch
  maxConcurrency: 32
  maxRecursionDepth: 2
  enableEffort: false
  enableLsp: true
  agentAdvisor:
    hmasd-implementer: xai-oauth/grok-4.6:high
    hmasd-implementer-terra: xai-oauth/grok-4.6:high
  disabledAgents:
    - scout
    - reviewer
    - sonic
    - designer
    - security-reviewer
"""

EXPECTED_ADVISORS = {
    "hmasd-implementer": "xai-oauth/grok-4.6:high",
    "hmasd-implementer-terra": "xai-oauth/grok-4.6:high",
}


EXPECTED_NO_ADVISOR = {
    "hmasd-em",
    "hmasd-cm",
    "hmasd-clerk",
    "hmasd-project-scout",
    "hmasd-code-scout",
    "hmasd-reviewer",
    "hmasd-verifier",
    "hmasd-experiment-operator",
    "hmasd-workflow-recovery-manager",
    "hmasd-browser-transport",
    "hmasd-research-scout",
    "hmasd-research-innovator",
    "hmasd-research-critic",
    "hmasd-research-principles-analyst",
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


def test_project_config_matches_current_advisor_contract_exactly() -> None:
    assert (REPO_ROOT / ".omp" / "config.yml").read_text(encoding="utf-8") == EXPECTED_CONFIG


def test_watchdog_routes_root_simplicity_without_authority() -> None:
    watchdog = (REPO_ROOT / ".omp" / "WATCHDOG.md").read_text(encoding="utf-8")
    for route in (
        "Root                          -> local-project simplicity",
        "hmasd-implementer             -> engineering",
        "hmasd-implementer-terra       -> engineering",
        "all other roles               -> no Advisor",
    ):
        assert route in watchdog
    for principle in (
        "one trusted local repository",
        "Root hand-writes operation JSON",
        "one coherent chore is split into per-primitive agents",
        "content-addressed authorization",
        "long-lived chore subagent",
        "**Directness:**",
        "**Threat:**",
        "**Generation:**",
        "**Weight:**",
    ):
        assert principle in watchdog
    assert "read-only and non-authoritative" in watchdog
    assert "never approves, rejects, blocks, authorizes, mutates, runs" in watchdog


def test_native_advisor_matrix_and_cold_revival_metadata() -> None:
    config = (REPO_ROOT / ".omp" / "config.yml").read_text(encoding="utf-8")
    assert _agent_advisor_mapping(config) == EXPECTED_ADVISORS
    assert "advisor:\n  enabled: true" in config
    assert "advisor: openai-codex/gpt-5.6-luna:xhigh" in config
    assert "  batch: true" in config
    assert "  isolation:\n    mode: auto\n    apply: false\n    merge: patch" in config

    agent_dir = REPO_ROOT / ".omp" / "agents"
    project_agents = {path.stem for path in agent_dir.glob("*.md")}
    assert project_agents == set(EXPECTED_ADVISORS) | EXPECTED_NO_ADVISOR
    for path in agent_dir.glob("*.md"):
        metadata = _frontmatter(path)
        assert "\nadvisor:" not in metadata
        assert "agentAdvisor" not in metadata
        if path.stem == "hmasd-clerk":
            assert "\nprewalk:" not in metadata
            assert "\neffort:" not in metadata

    instructions = (REPO_ROOT / ".omp" / "AGENTS.md").read_text(encoding="utf-8")
    watchdog = (REPO_ROOT / ".omp" / "WATCHDOG.md").read_text(encoding="utf-8")
    assert "Root's continuous Advisor uses the dedicated" in instructions
    assert "`task.agentAdvisor[agentName]`" in watchdog
    assert "`session_init`" in watchdog
    assert "cold-revival contract" in watchdog.lower()
    assert "cannot mutate it in place" in watchdog
    assert "material role change creates a new session" in watchdog
    assert "EM, CM, Clerk, Transport" in instructions

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
