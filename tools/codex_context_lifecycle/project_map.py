"""Validate that PROJECT_MAP.md remains the single stable codemap."""

from __future__ import annotations

from pathlib import Path

REQUIRED_HEADINGS = (
    "Stable lineages",
    "Agent context control plane",
    "Repository context lifecycle",
    "Maintenance Protocol",
)
REQUIRED_PATHS = (
    "tools/codex_semantic_mvp/",
    "tools/codex_context_lifecycle/",
    "runtime/codex-semantic-mvp/",
    "tests/codex_semantic_mvp/",
    "tests/codex_context_lifecycle/",
    "docs/project/CONTEXT_SOURCE_REGISTRY.toml",
    "docs/project/DECISIONS_INDEX.md",
)
REQUIRED_PHRASES = (
    "runtime SQLite is noncanonical",
    "PROJECT_MAP is the stable codemap",
    "CURRENT_WORK is the current-work index",
)


def validate_project_map(path: Path) -> tuple[str, ...]:
    errors: list[str] = []
    text = Path(path).read_text(encoding="utf-8")
    lowered = text.lower()
    for heading in REQUIRED_HEADINGS:
        if f"## {heading}" not in text:
            errors.append(f"missing heading: {heading}")
    for required in REQUIRED_PATHS:
        if required not in text:
            errors.append(f"missing path: {required}")
    for phrase in REQUIRED_PHRASES:
        if phrase.lower() not in lowered:
            errors.append(f"missing phrase: {phrase}")
    map_path = Path(path).resolve()
    project_dir = map_path.parent
    docs_dir = project_dir.parent
    repo_root = docs_dir.parent
    for candidate in (
        repo_root / "CODEMAP.md",
        docs_dir / "CODEMAP.md",
        project_dir / "CODEMAP.md",
    ):
        if candidate.exists():
            errors.append("competing CODEMAP.md exists")
            break
    return tuple(errors)
