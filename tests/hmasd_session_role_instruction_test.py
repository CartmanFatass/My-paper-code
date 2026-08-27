from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _prompt(name: str) -> str:
    return " ".join(
        (ROOT / ".codex" / "prompts" / name).read_text(encoding="utf-8").split()
    ).casefold()


def test_em_material_science_uses_independent_leaf_challenge() -> None:
    text = _prompt("hmasd-em.md")

    assert "material scientific conclusion" in text
    assert "research scout" in text
    assert "research innovator" in text
    assert "research principles analyst" in text
    assert "research critic" in text
    assert "agentify external transport" in text
    assert "hmasd-explorer-agentify-transport" in text
    assert "gpt-5.6 pro" in text
    assert "constructive" in text
    assert "adversarial" in text
    assert "direct leaf" in text
    assert "before accepting" in text
    assert "routing, bookkeeping, or a purely mechanical return" in text
    assert "constructive pro review first" in text
    assert "em applies or rejects its corrections" in text
    assert "adversarial pro review tests the revised object" in text


def test_cm_uses_leaf_roles_at_proportional_engineering_seams() -> None:
    text = _prompt("hmasd-cm.md")

    assert "non-mechanical implementation" in text
    assert "implementer" in text
    assert "independent reviewer" in text
    assert "production, protocol, scientific, numerical, rng, or checkpoint code" in text
    assert "exactly one operator" in text
    assert "any result-bearing command" in text
    assert "these triggers are independent" in text
    assert "read-only diagnosis, bookkeeping, git closure, or return correction" in text
    assert "static prelaunch dossier" in text
    assert "runtime prepare" in text
    assert "payload/result execution" in text
    assert "direct cm leaf" in text
    assert "focused runtime or equivalence-risk verification" in text
    assert "verifier" in text


def test_required_em_cm_leaf_profiles_are_registered() -> None:
    config = (ROOT / ".codex/config.toml").read_text(encoding="utf-8")
    for registered in (
        "HMASDImplementer",
        "HMASDReviewer",
        "HMASDVerifier",
        "HMASDExperimentOperator",
        "HMASDResearchScout",
        "HMASDResearchInnovator",
        "HMASDResearchPrinciplesAnalyst",
        "HMASDResearchCritic",
        "HMASDExplorerAgentifyTransport",
    ):
        assert f"[agents.{registered}]" in config

    assert "[agents.HMASDCodeProjectManager]" not in config
    assert "[agents.HMASDIndependentResearchExplorer]" not in config

    transport = " ".join(
        (ROOT / ".codex/agents/hmasd-explorer-agentify-transport.toml")
        .read_text(encoding="utf-8")
        .split()
    )
    assert "GPT-5.6 Pro" in transport
    assert "at most once" in transport
    assert "do not interpret the science" in transport.casefold()


def test_root_is_not_normal_direction_git_or_manifest_owner() -> None:
    agents = " ".join((ROOT / "AGENTS.md").read_text(encoding="utf-8").split()).casefold()
    goals = " ".join(
        (ROOT / "docs/project/WORKFLOW_GOALS_AND_ACCEPTANCE.md")
        .read_text(encoding="utf-8")
        .split()
    ).casefold()
    protocol = " ".join(
        (ROOT / "docs/project/WORKFLOW_PROTOCOL.md").read_text(encoding="utf-8").split()
    ).casefold()

    assert "不代替 cm 完成 direction-owned candidate 或 manifest preparation" in agents
    assert "direction-owned candidate 与 manifest preparation 是 cm" in goals
    assert "direction-owned candidate 和 manifest preparation 属于同方向 cm" in protocol
    assert "root 是 manifest preparation 的正常 owner" not in protocol
    for text in (agents, goals, protocol):
        assert "shared-core" in text
