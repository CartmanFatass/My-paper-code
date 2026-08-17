from pathlib import Path

from tests.codex_context_lifecycle.helpers import make_pair
from tools.codex_context_lifecycle.source_registry import load_registry, sources_for_actor
from tools.codex_semantic_mvp.actor_models import EpochKind
from tools.codex_semantic_mvp.capsules import build_capsule, render_capsule
from tools.codex_semantic_mvp.epochs import plan_epoch_open
from tools.codex_semantic_mvp.store import SemanticStore


def test_epoch_refs_are_ids_not_file_copies(store: SemanticStore, repo_root: Path) -> None:
    _root, em, _cm = make_pair(store)
    registry = load_registry(repo_root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml")
    epoch = plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="next discriminator",
        authority_refs=["AGENTS.md"],
        frozen_invariants=[],
        exit_boundary="rollover",
        navigation_refs=(),
        procedure_refs=("em-procedure",),
        registry=registry,
    )
    assert epoch["procedure_refs"] == ["em-procedure"]
    capsule = build_capsule(store, em.actor_context_id)
    text = render_capsule(capsule)
    skill = (repo_root / ".agents/skills/hmasd-independent-research-exploration/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert skill[:80] not in text
    assert "CONTEXT PRECEDENCE" in text


def test_old_epoch_open_defaults_empty_refs(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    epoch = plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="compat",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="exit",
    )
    assert epoch["navigation_refs"] == []
    assert epoch["procedure_refs"] == []


def test_role_examples_are_visible(repo_root: Path) -> None:
    registry = load_registry(repo_root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml")
    em = {
        source.id
        for source in sources_for_actor(registry, "EM", requested_source_ids=("em-procedure",))
    }
    cm = {
        source.id
        for source in sources_for_actor(
            registry, "CM", requested_source_ids=("agent-runtime-context",)
        )
    }
    portfolio = {
        source.id
        for source in sources_for_actor(
            registry,
            "PORTFOLIO",
            requested_source_ids=("portfolio-contract", "portfolio-handoff-procedure", "portfolio-reconciliation"),
        )
    }
    assert "em-procedure" in em
    assert "project-map" in cm
    assert "agent-runtime-context" in cm
    assert "portfolio-contract" in portfolio
