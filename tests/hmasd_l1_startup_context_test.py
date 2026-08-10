"""Focused contracts for compact, action-triggered L1 startup context."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "AGENTS.md"
HOOKS = ROOT / ".codex" / "hooks.json"


L1_SURFACES = {
    "wdm": (
        ROOT / ".agents" / "roles" / "WORKFLOW_DESIGN_MANAGER.md",
        ROOT / ".codex" / "agents" / "hmasd-workflow-design-manager.toml",
    ),
    "cpm": (
        ROOT / ".agents" / "roles" / "CODE_PROJECT_MANAGER.md",
        ROOT / ".codex" / "agents" / "hmasd-code-project-manager.toml",
    ),
    "explorer": (
        ROOT / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md",
        ROOT / ".codex" / "agents" / "hmasd-independent-research-explorer.toml",
    ),
}


def _normalized(paths: tuple[Path, ...]) -> str:
    return " ".join(" ".join(path.read_text(encoding="utf-8").split()) for path in paths).lower()


def _has_nearby(text: str, *terms: str, window: int = 180) -> bool:
    """Require all terms in one compact contract clause, not scattered text."""
    for match in re.finditer(terms[0], text):
        fragment = text[match.start() : match.start() + window]
        if all(re.search(term, fragment) for term in terms[1:]):
            return True
    return False


def test_wdm_cpm_and_explorer_start_compact_and_action_triggered() -> None:
    for name, paths in L1_SURFACES.items():
        text = _normalized(paths)
        assert _has_nearby(text, r"startup", r"compact"), name
        assert _has_nearby(text, r"startup", r"action[- ]trigger"), name


def test_explorer_keeps_mandatory_compact_continuity_and_lazy_optional_context() -> None:
    explorer = _normalized(L1_SURFACES["explorer"])
    assert _has_nearby(explorer, r"continuity", r"mandatory", r"compact")
    assert _has_nearby(explorer, r"portfolio", r"owner[- ]approved", r"lazy")
    assert _has_nearby(explorer, r"historical", r"handoff", r"lazy")


def test_hooks_are_empty_disabled_and_non_authoritative() -> None:
    hooks = json.loads(HOOKS.read_text(encoding="utf-8"))
    assert hooks["hooks"] == {}
    router = _normalized((ROUTER,))
    assert _has_nearby(router, r"hooks", r"disabled", r"non[- ]authoritative")
