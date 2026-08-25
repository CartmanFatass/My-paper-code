from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = REPO_ROOT / ".omp" / "agents"
FrontmatterValue = str | list[str]



EXPECTED_AGENTS: dict[str, dict[str, FrontmatterValue]] = {
    "hmasd-em": {
        "model": "openai-codex/gpt-5.6-sol",
        "thinking-level": "max",
        "tools": ["read", "write", "edit", "grep", "glob", "bash", "task", "hub"],
        "spawns": [
            "hmasd-research-scout",
            "hmasd-research-innovator",
            "hmasd-research-critic",
            "hmasd-research-principles-analyst",
            "hmasd-research-artifact-writer",
            "hmasd-code-scout",
            "hmasd-external-pro-transport",
            "hmasd-external-gemini-transport",
            "librarian",
        ],
        "autoloadSkills": [
            "hmasd-em-direction-cycle",
            "hmasd-scientific-external-review",
            "hmasd-git-integration",
        ],
    },
    "hmasd-cm": {
        "model": "openai-codex/gpt-5.6-sol",
        "thinking-level": "high",
        "tools": ["read", "write", "edit", "grep", "glob", "bash", "task", "hub"],
        "spawns": [
            "hmasd-project-scout",
            "hmasd-code-scout",
            "hmasd-implementer",
            "hmasd-implementer-terra",
            "hmasd-reviewer",
            "hmasd-verifier",
            "hmasd-experiment-operator",
            "hmasd-research-scout",
            "librarian",
        ],
        "autoloadSkills": [
            "hmasd-cm-engineering-cycle",
            "hmasd-result-run",
            "hmasd-git-integration",
        ],
    },
    "hmasd-project-scout": {
        "model": "openai-codex/gpt-5.6-luna",
        "thinking-level": "medium",
        "tools": ["read", "grep", "glob"],
        "spawns": [],
        "autoloadSkills": [],
        "read-summarize": "false",
    },
    "hmasd-code-scout": {
        "model": "openai-codex/gpt-5.6-luna",
        "thinking-level": "medium",
        "tools": ["read", "grep", "glob"],
        "spawns": [],
        "autoloadSkills": [],
        "read-summarize": "false",
    },
    "hmasd-implementer": {
        "model": "openai-codex/gpt-5.6-sol",
        "thinking-level": "high",
        "tools": ["read", "write", "edit", "grep", "glob", "bash", "lsp"],
        "spawns": [],
        "autoloadSkills": ["hmasd-git-integration"],
    },
    "hmasd-implementer-terra": {
        "model": "openai-codex/gpt-5.6-terra",
        "thinking-level": "high",
        "tools": ["read", "write", "edit", "grep", "glob", "bash", "lsp"],
        "spawns": [],
        "autoloadSkills": ["hmasd-git-integration"],
    },
    "hmasd-reviewer": {
        "model": "openai-codex/gpt-5.6-sol",
        "thinking-level": "high",
        "tools": ["read", "grep", "glob"],
        "spawns": [],
        "autoloadSkills": [],
        "read-summarize": "false",
    },
    "hmasd-verifier": {
        "model": "openai-codex/gpt-5.6-luna",
        "thinking-level": "high",
        "tools": ["read", "grep", "glob", "bash"],
        "spawns": [],
        "autoloadSkills": [],
        "read-summarize": "false",
    },
    "hmasd-experiment-operator": {
        "model": "openai-codex/gpt-5.6-luna",
        "thinking-level": "low",
        "tools": ["read", "grep", "glob", "bash", "hub"],
        "spawns": [],
        "autoloadSkills": ["hmasd-result-run"],
    },
    "hmasd-workflow-recovery-manager": {
        "model": "openai-codex/gpt-5.6-terra",
        "thinking-level": "high",
        "tools": ["read", "write", "edit", "grep", "glob", "bash", "hub"],
        "spawns": [],
        "autoloadSkills": ["hmasd-workflow-recovery"],
    },
    "hmasd-external-pro-transport": {
        "model": "openai-codex/gpt-5.6-luna",
        "thinking-level": "medium",
        "tools": [
            "read",
            "grep",
            "glob",
            "mcp__agentify-desktop__agentify_review_prompt_sha256_preflight",
            "mcp__agentify-desktop__agentify_review_reasoning_mode_preflight",
            "mcp__agentify-desktop__agentify_review_query",
            "mcp__agentify-desktop__agentify_review_observe",
        ],
        "spawns": [],
        "autoloadSkills": ["hmasd-scientific-external-review"],
    },
    "hmasd-external-gemini-transport": {
        "model": "openai-codex/gpt-5.6-luna",
        "thinking-level": "high",
        "tools": [
            "read",
            "grep",
            "glob",
            "mcp__agentify-desktop__agentify_review_prompt_sha256_preflight",
            "mcp__agentify-desktop__agentify_review_preflight",
            "mcp__agentify-desktop__agentify_review_query",
            "mcp__agentify-desktop__agentify_review_observe",
        ],
        "spawns": [],
        "autoloadSkills": ["hmasd-scientific-external-review"],
    },
    "hmasd-research-scout": {
        "model": "openai-codex/gpt-5.6-sol",
        "thinking-level": "high",
        "tools": ["read", "grep", "glob", "web_search"],
        "spawns": [],
        "autoloadSkills": [],
        "read-summarize": "false",
    },
    "hmasd-research-innovator": {
        "model": "openai-codex/gpt-5.6-sol",
        "thinking-level": "max",
        "tools": ["read", "grep", "glob", "web_search"],
        "spawns": [],
        "autoloadSkills": [],
        "read-summarize": "false",
    },
    "hmasd-research-critic": {
        "model": "openai-codex/gpt-5.6-sol",
        "thinking-level": "max",
        "tools": ["read", "grep", "glob", "web_search"],
        "spawns": [],
        "autoloadSkills": [],
        "read-summarize": "false",
    },
    "hmasd-research-principles-analyst": {
        "model": "openai-codex/gpt-5.6-sol",
        "thinking-level": "max",
        "tools": ["read", "grep", "glob", "web_search"],
        "spawns": [],
        "autoloadSkills": [],
        "read-summarize": "false",
    },
    "hmasd-research-artifact-writer": {
        "model": "openai-codex/gpt-5.6-luna",
        "thinking-level": "medium",
        "tools": ["read", "write", "edit", "grep", "glob"],
        "spawns": [],
        "autoloadSkills": [],
    },
}

LEGACY_ACTIVE_NAMES = (
    "hmasd-independent-research-explorer",
    "hmasd-code-project-manager",
    "hmasd-explorer-agentify-transport",
    "hmasd-cpm-agentify-transport",
    "hmasd-portfolio",
)


def _parse_frontmatter(path: Path) -> dict[str, FrontmatterValue]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0] == "---", path
    end = lines.index("---", 1)
    result: dict[str, FrontmatterValue] = {}
    index = 1
    while index < end:
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        key, separator, value = line.partition(":")
        assert separator, (path, line)
        key = key.strip()
        value = value.strip()
        if value:
            result[key] = [] if value == "[]" else value
            index += 1
            continue
        values: list[str] = []
        index += 1
        while index < end and lines[index].startswith("  - "):
            values.append(lines[index][4:])
            index += 1
        result[key] = values
    return result


def _string_field(metadata: dict[str, FrontmatterValue], key: str) -> str:
    value = metadata[key]
    assert isinstance(value, str), (key, value)
    return value


def _list_field(metadata: dict[str, FrontmatterValue], key: str) -> list[str]:
    value = metadata[key]
    assert isinstance(value, list), (key, value)
    return value


def test_exact_project_agent_inventory_and_frontmatter() -> None:
    paths = sorted(AGENT_ROOT.glob("*.md"))
    assert {path.stem for path in paths} == set(EXPECTED_AGENTS)
    assert len(paths) == 17
    for path in paths:
        metadata = _parse_frontmatter(path)
        expected = EXPECTED_AGENTS[path.stem]
        assert _string_field(metadata, "name") == path.stem
        assert _string_field(metadata, "model") == _string_field(expected, "model")
        assert _string_field(metadata, "thinking-level") == _string_field(
            expected, "thinking-level"
        )
        assert _list_field(metadata, "tools") == _list_field(expected, "tools")
        assert _list_field(metadata, "spawns") == _list_field(expected, "spawns")
        assert _list_field(metadata, "autoloadSkills") == _list_field(
            expected, "autoloadSkills"
        )
        assert _string_field(metadata, "blocking") == "false"
        if "read-summarize" in expected:
            assert _string_field(metadata, "read-summarize") == _string_field(
                expected, "read-summarize"
            )
        else:
            assert "read-summarize" not in metadata


def test_depth_two_graph_and_leaf_specialists() -> None:
    parsed = {
        name: _parse_frontmatter(AGENT_ROOT / f"{name}.md")
        for name in EXPECTED_AGENTS
    }
    assert "hmasd-project-scout" in _list_field(parsed["hmasd-cm"], "spawns")
    assert _list_field(parsed["hmasd-em"], "spawns")
    for name, metadata in parsed.items():
        spawns = _list_field(metadata, "spawns")
        if name not in {"hmasd-em", "hmasd-cm"}:
            assert spawns == [], name
        assert "task" not in spawns, name
        assert "hmasd-workflow-recovery-manager" not in spawns, name
    assert _list_field(parsed["hmasd-cm"], "spawns")[-1] == "librarian"


def test_bundled_disablement_root_only_dispatch_and_legacy_cleanup() -> None:
    config = (REPO_ROOT / ".omp" / "config.yml").read_text(encoding="utf-8")
    for bundled in ("scout", "reviewer", "sonic", "designer", "security-reviewer"):
        assert re.search(rf"^    - {re.escape(bundled)}$", config, re.MULTILINE)
    assert re.search(r"^  enableEffort: false$", config, re.MULTILINE)

    active_paths = [
        path
        for root in (REPO_ROOT / ".omp", REPO_ROOT / "scripts")
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".json", ".md", ".py", ".yaml", ".yml"}
    ]
    active_text = "\n".join(path.read_text(encoding="utf-8") for path in active_paths)
    for old_name in LEGACY_ACTIVE_NAMES:
        assert old_name not in active_text

    agents = "\n".join(
        path.read_text(encoding="utf-8") for path in AGENT_ROOT.glob("*.md")
    )
    assert "hmasd-workflow-recovery-manager" in agents
    instructions = (REPO_ROOT / ".omp" / "AGENTS.md").read_text(encoding="utf-8")
    assert "Root-only" in instructions
    assert "bundled `task`" in instructions
    assert "bundled `librarian`" in instructions
    assert "hmasd-project-scout" in instructions
    assert "bundled `scout`" not in instructions
    assert "task.enableEffort` remains disabled" in instructions
    assert "highest supported tier" in instructions


def test_seven_complete_skills_and_authority_files() -> None:
    expected_anchors = {
        "hmasd-root-control": (
            "portfolio.md",
            ".omp/runtime",
            "bounded reassessment",
            "next_action.owner",
            "experiment_operator",
            "ownerless",
            "28",
            "four root/review/recovery slots",
            "idle",
            "complete",
        ),
        "hmasd-em-direction-cycle": (
            "two specialists",
            "up to four",
            "divergent",
            "local em synthesis",
            "durable reference",
        ),
        "hmasd-cm-engineering-cycle": (
            "two specialists",
            "at most six",
            "lsp",
            "provisioned engineering worktree",
            "scientific ambiguity",
        ),
        "hmasd-result-run": (
            "7200",
            "memory",
            "exit code `8`",
            "one operator",
            "never start a successor",
        ),
        "hmasd-scientific-external-review": (
            "mutually blind",
            "in parallel",
            "local em synthesis",
            "root alone",
            "unknown commitment",
        ),
        "hmasd-workflow-recovery": (
            "pure research",
            "manager missing",
            "partial code",
            "run says",
            "memory refusal",
            "git conflict",
            "push outcome",
            "external commitment",
            "late specialist",
            "dashboard failure",
            "compaction",
            "reconstruct",
            "three",
            "superseded",
            "user-visible blocker",
        ),
        "hmasd-git-integration": (
            "canonical",
            "omp/workflow",
            "one candidate commit",
            "stale bases",
            "em:<direction>",
            "cm:<direction>",
        ),
    }
    skill_paths = sorted((REPO_ROOT / ".omp" / "skills").glob("*/SKILL.md"))
    assert {path.parent.name for path in skill_paths} == set(expected_anchors)
    assert len(skill_paths) == 7
    for path in skill_paths:
        metadata = _parse_frontmatter(path)
        assert _string_field(metadata, "name") == path.parent.name
        assert _string_field(metadata, "description")
        body = path.read_text(encoding="utf-8")
        for heading in (
            "## Purpose",
            "## Inputs",
            "## Bounded cycle",
            "## State writes",
            "## Returned result envelope",
            "## Failure handling",
            "## Deletion condition",
        ):
            assert heading in body, path
        lower_body = body.lower()
        for anchor in expected_anchors[path.parent.name]:
            assert anchor in lower_body, (path, anchor)

    rules = (REPO_ROOT / ".omp" / "RULES.md").read_text(encoding="utf-8")
    numbered = re.findall(r"^([1-9])\. ", rules, re.MULTILINE)
    assert numbered == [str(index) for index in range(1, 10)]
    watchdog = (REPO_ROOT / ".omp" / "WATCHDOG.md").read_text(encoding="utf-8")
    assert "session_init" in watchdog
    assert "cold revival" in watchdog.lower()
    assert "WATCHDOG.yml" not in watchdog


def test_root_material_checkpoints_are_event_driven_scoped_and_pushed() -> None:
    instructions = (REPO_ROOT / ".omp" / "AGENTS.md").read_text(encoding="utf-8")
    root_skill = (
        REPO_ROOT / ".omp" / "skills" / "hmasd-root-control" / "SKILL.md"
    ).read_text(encoding="utf-8")
    concept = (
        REPO_ROOT
        / "docs"
        / "plans"
        / "2026-08-24-omp-autonomous-multidirection-research-concept.md"
    ).read_text(encoding="utf-8")
    implementation = (
        REPO_ROOT
        / "docs"
        / "plans"
        / "2026-08-24-omp-autonomous-multidirection-research-implementation.md"
    ).read_text(encoding="utf-8")

    for text in (instructions, root_skill, concept, implementation):
        lowered = text.lower()
        assert "event-driven" in lowered
        assert "git add -a" in lowered
        assert "unrelated" in lowered
        assert "fetch" in lowered
        assert "omp/workflow" in lowered

    combined = "\n".join((instructions, root_skill, concept, implementation))
    assert "em:<direction>" in combined
    assert "cm:<direction>" in combined
    assert "unknown push" in combined.lower()
    assert "conflict" in combined.lower()
    assert "report" in combined.lower()

    for trigger in (
        "research or engineering round",
        "accepted-result promotion",
        "terminal-run evidence",
        "external prompt/archive readiness",
        "portfolio lifecycle change",
        "schema migration",
    ):
        assert trigger in root_skill.lower()


def test_headless_advisor_boundary_is_deleted() -> None:
    assert not (REPO_ROOT / "scripts" / "run_hmasd_advisor.py").exists()
    assert not (REPO_ROOT / "tests" / "run_hmasd_advisor_test.py").exists()
    advisors = REPO_ROOT / ".omp" / "advisors"
    assert not advisors.exists() or not any(advisors.iterdir())
    assert not (REPO_ROOT / ".omp" / "WATCHDOG.yml").exists()
    assert not (REPO_ROOT / ".omp" / "WATCHDOG.yaml").exists()
    for path in (REPO_ROOT / ".omp").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert "run_hmasd_advisor" not in text
            assert "headless Advisor" not in text


def test_agentify_uses_windows_node_and_visible_windows_chrome_runtime() -> None:
    config = json.loads((REPO_ROOT / ".omp" / "mcp.json").read_text(encoding="utf-8"))
    server = config["mcpServers"]["agentify-desktop"]
    assert server["type"] == "stdio"
    assert server["command"] == "/mnt/c/Program Files/nodejs/node.exe"
    assert server["args"] == [
        r"C:\Projects\agentify-desktop\bin\agentify-desktop.mjs",
        "mcp",
    ]
    instructions = (REPO_ROOT / ".omp" / "AGENTS.md").read_text(encoding="utf-8")
    assert "visible Windows Chrome" in instructions
    assert "Linux browser or Linux Node runtime" in instructions
