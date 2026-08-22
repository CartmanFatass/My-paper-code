from pathlib import Path

import pytest

from tools.codex_context_lifecycle.decisions import (
    DecisionError,
    collect_decisions,
    parse_decision,
    render_decision_index,
)


def _write_adr(directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


def write_adr(
    root: Path,
    *,
    decision_id: str,
    owner: str,
    status: str,
    supersedes: list[str] | None = None,
    canonical_sources: list[str] | None = None,
) -> Path:
    decisions = root / "docs" / "project" / "decisions"
    decisions.mkdir(parents=True, exist_ok=True)
    supersedes_text = ", ".join(f'"{item}"' for item in (supersedes or []))
    canonical_sources_text = ", ".join(
        f'"{item}"' for item in (canonical_sources or [])
    )
    return _write_adr(
        decisions,
        f"{decision_id}.md",
        f'''+++
decision_id = "{decision_id}"
title = "Test decision"
owner = "{owner}"
scope = "shared:test"
status = "{status}"
decision_date = "2026-08-22"
supersedes = [{supersedes_text}]
canonical_sources = [{canonical_sources_text}]
revisit_conditions = []
+++
''',
    )


def test_parse_toml_front_matter(tmp_path: Path) -> None:
    path = _write_adr(
        tmp_path,
        "ADR-0001-sample.md",
        """+++
decision_id = "ADR-0001"
title = "Repository-owned context hierarchy"
owner = "operational_root"
scope = "shared:codex-context-control-plane"
status = "accepted"
decision_date = "2026-08-17"
supersedes = []
canonical_sources = ["docs/project/CONTEXT_PRECEDENCE.md"]
revisit_conditions = ["A new official Codex context authority model replaces repository ownership."]
+++

# body
""",
    )
    record = parse_decision(path)
    assert record.decision_id == "ADR-0001"
    assert record.owner == "operational_root"
    assert record.status == "accepted"
    assert record.canonical_sources == ("docs/project/CONTEXT_PRECEDENCE.md",)


@pytest.mark.parametrize(
    "body, match",
    [
        (
            """+++
decision_id = "ADR-X"
title = "x"
owner = ""
scope = "s"
status = "accepted"
decision_date = "2026-08-17"
supersedes = []
canonical_sources = []
revisit_conditions = []
+++
""",
            "missing owner",
        ),
        (
            """+++
decision_id = "ADR-X"
title = "x"
owner = "o"
scope = "s"
status = "weird"
decision_date = "2026-08-17"
supersedes = []
canonical_sources = []
revisit_conditions = []
+++
""",
            "unknown status",
        ),
        (
            """+++
decision_id = "ADR-X"
title = "x"
owner = "o"
scope = "s"
status = "accepted"
decision_date = "2026-08-17"
supersedes = ["ADR-X"]
canonical_sources = []
revisit_conditions = []
+++
""",
            "self-supersede",
        ),
        (
            """+++
decision_id = "ADR-X"
title = "x"
owner = "o"
scope = "s"
status = "accepted"
decision_date = "2026-08-17"
supersedes = []
canonical_sources = ["C:/abs/path.md"]
revisit_conditions = []
+++
""",
            "absolute path",
        ),
    ],
)
def test_parse_rejects_invalid_front_matter(tmp_path: Path, body: str, match: str) -> None:
    path = _write_adr(tmp_path, "ADR-X.md", body)
    with pytest.raises(DecisionError, match=match):
        parse_decision(path)


@pytest.mark.parametrize(
    "canonical_source",
    [
        '"../outside.md"',
        '"docs/project/../outside.md"',
        "'docs\\..\\outside.md'",
        '"https://example.invalid/source.md"',
        "'C:\\outside.md'",
    ],
)
def test_parse_rejects_non_repository_relative_canonical_source(
    tmp_path: Path,
    canonical_source: str,
) -> None:
    path = _write_adr(
        tmp_path,
        "ADR-X.md",
        f'''+++
decision_id = "ADR-X"
title = "x"
owner = "operational_root"
scope = "shared:test"
status = "accepted"
decision_date = "2026-08-17"
supersedes = []
canonical_sources = [{canonical_source}]
revisit_conditions = []
+++
''',
    )
    with pytest.raises(DecisionError, match="repository-relative path"):
        parse_decision(path)


def test_collect_rejects_duplicate_and_mutual_supersede(tmp_path: Path) -> None:
    decisions = tmp_path / "docs" / "project" / "decisions"
    decisions.mkdir(parents=True)
    template = """+++
decision_id = "{id}"
title = "t"
owner = "o"
scope = "s"
status = "accepted"
decision_date = "2026-08-17"
supersedes = [{supersedes}]
canonical_sources = []
revisit_conditions = []
+++
"""
    _write_adr(decisions, "ADR-0001-a.md", template.format(id="ADR-0001", supersedes='"ADR-0002"'))
    _write_adr(decisions, "ADR-0002-b.md", template.format(id="ADR-0002", supersedes='"ADR-0001"'))
    with pytest.raises(DecisionError, match="supersede each other"):
        collect_decisions(tmp_path)
    _write_adr(decisions, "ADR-0001-dup.md", template.format(id="ADR-0001", supersedes=""))
    with pytest.raises(DecisionError, match="duplicate ID"):
        collect_decisions(tmp_path)


def test_shared_accepted_adr_rejects_non_root_owner(tmp_path):
    write_adr(
        tmp_path,
        decision_id="ADR-0099",
        owner="cm",
        status="accepted",
        canonical_sources=["docs/project/PROJECT_MAP.md"],
    )
    with pytest.raises(DecisionError, match="shared accepted ADR owner"):
        collect_decisions(tmp_path)


def test_accepted_adr_requires_existing_canonical_source(tmp_path):
    write_adr(
        tmp_path,
        decision_id="ADR-0098",
        owner="operational_root",
        status="accepted",
        canonical_sources=["docs/project/missing.md"],
    )
    with pytest.raises(DecisionError, match="missing canonical source"):
        collect_decisions(tmp_path)


def test_collect_rejects_resolved_canonical_source_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_adr(
        tmp_path,
        decision_id="ADR-0098",
        owner="operational_root",
        status="accepted",
        canonical_sources=["linked-outside/source.md"],
    )
    repository = tmp_path.resolve()
    escaped_source = tmp_path.parent / "outside" / "source.md"
    original_resolve = Path.resolve

    def resolve_with_escape(path: Path, *args, **kwargs) -> Path:
        if path == repository / "linked-outside" / "source.md":
            return escaped_source
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_with_escape)
    with pytest.raises(DecisionError, match="resolve inside the repository"):
        collect_decisions(tmp_path)


def test_supersedes_requires_existing_adr(tmp_path):
    write_adr(
        tmp_path,
        decision_id="ADR-0097",
        owner="operational_root",
        status="accepted",
        supersedes=["ADR-0042"],
        canonical_sources=["docs/project/PROJECT_MAP.md"],
    )
    with pytest.raises(DecisionError, match="unknown superseded ADR"):
        collect_decisions(tmp_path)


def test_accepted_replacement_requires_old_record_superseded(tmp_path):
    write_adr(
        tmp_path,
        decision_id="ADR-0096",
        owner="operational_root",
        status="accepted",
        supersedes=["ADR-0095"],
        canonical_sources=["docs/project/PROJECT_MAP.md"],
    )
    write_adr(
        tmp_path,
        decision_id="ADR-0095",
        owner="operational_root",
        status="accepted",
        canonical_sources=["docs/project/PROJECT_MAP.md"],
    )
    with pytest.raises(DecisionError, match="must be marked superseded"):
        collect_decisions(tmp_path)


def test_committed_index_matches_renderer(repo_root: Path) -> None:
    records = collect_decisions(repo_root)
    rendered = render_decision_index(records)
    committed = (repo_root / "docs/project/DECISIONS_INDEX.md").read_text(encoding="utf-8")
    assert rendered == committed
    assert any(record.decision_id == "ADR-0001" for record in records)


def test_current_shared_architecture_adrs_are_present(repo_root):
    records = {item.decision_id: item for item in collect_decisions(repo_root)}
    assert records["ADR-0005"].status == "accepted"
    assert records["ADR-0006"].status == "accepted"
    assert records["ADR-0007"].status == "accepted"
