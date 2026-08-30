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
        "autoloadSkills": [],
    },
    "hmasd-implementer-terra": {
        "model": "openai-codex/gpt-5.6-terra",
        "thinking-level": "high",
        "tools": ["read", "write", "edit", "grep", "glob", "bash", "lsp"],
        "spawns": [],
        "autoloadSkills": [],
    },
    "hmasd-reviewer": {
        "model": "openai-codex/gpt-5.6-sol",
        "thinking-level": "xhigh",
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
    "hmasd-browser-transport": {
        "model": "openai-codex/gpt-5.6-luna",
        "thinking-level": "xhigh",
        "tools": [
            "read",
            "grep",
            "glob",
            "bash",
            "hub",
            "mcp__agentify-desktop__agentify_ensure_ready",
            "mcp__agentify-desktop__agentify_tabs",
            "mcp__agentify-desktop__agentify_status",
            "mcp__agentify-desktop__agentify_tab_create",
            "mcp__agentify-desktop__agentify_open_conversation",
            "mcp__agentify-desktop__agentify_new_conversation",
            "mcp__agentify-desktop__agentify_operator_observe",
            "mcp__agentify-desktop__agentify_operator_wait",
            "mcp__agentify-desktop__agentify_operator_act",
            "mcp__agentify-desktop__agentify_review_chatgpt_profile_snapshot",
            "mcp__agentify-desktop__agentify_review_preflight",
            "mcp__agentify-desktop__agentify_review_reasoning_mode_preflight",
            "mcp__agentify-desktop__agentify_review_query",
            "mcp__agentify-desktop__agentify_review_observe",
            "mcp__agentify-desktop__agentify_wait_response",
            "mcp__agentify-desktop__agentify_read_page",
            "mcp__agentify-desktop__agentify_tab_close",
        ],
        "spawns": [],
        "autoloadSkills": ["hmasd-browser-transport"],
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
}

LEGACY_ACTIVE_NAMES = (
    "hmasd-independent-research-explorer",
    "hmasd-code-project-manager",
    "hmasd-explorer-agentify-transport",
    "hmasd-cpm-agentify-transport",
    "hmasd-portfolio",
)


ON_DEMAND_RESEARCH_SKILLS = (
    "hmasd-paper-lookup",
    "hmasd-hypothesis-mechanisms",
    "hmasd-experimental-design-tools",
    "hmasd-scientific-writing-validation",
    "hmasd-symbolic-counterexample-tools",
    "hmasd-scientific-compute-contracts",
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
    assert "hmasd-research-artifact-writer" not in {path.stem for path in paths}
    assert len(paths) == 15
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
    for manager in ("hmasd-em", "hmasd-cm"):
        assert "hmasd-browser-transport" not in _list_field(
            parsed[manager], "spawns"
        )
    for name, metadata in parsed.items():
        spawns = _list_field(metadata, "spawns")
        if name not in {"hmasd-em", "hmasd-cm"}:
            assert spawns == [], name
        assert "task" not in spawns, name
        assert "hmasd-workflow-recovery-manager" not in spawns, name
    assert _list_field(parsed["hmasd-cm"], "spawns")[-1] == "librarian"

def test_implementers_are_skillless_non_git_leaf_workers() -> None:
    for name in ("hmasd-implementer", "hmasd-implementer-terra"):
        metadata = _parse_frontmatter(AGENT_ROOT / f"{name}.md")
        assert _list_field(metadata, "autoloadSkills") == []
        body = " ".join(
            (AGENT_ROOT / f"{name}.md").read_text(encoding="utf-8").lower().split()
        )
        assert "do not commit or push" in body
        assert "unless explicitly assigned" not in body


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
    assert "session-init evidence" in instructions.lower()
    for manager in ("hmasd-em.md", "hmasd-cm.md"):
        body = " ".join(
            (AGENT_ROOT / manager).read_text(encoding="utf-8").lower().split()
        )
        assert "task` item" in body
        assert "`effort`" in body
        assert "omit" in body


def test_fourteen_complete_skills_and_authority_files() -> None:
    expected_anchors = {
        "hmasd-root-control": (
            "portfolio.md",
            ".omp/runtime",
            "one user-facing controller",
            "singleton browsertransport mediation",
            "bounded recovery",
        ),
        "hmasd-em-direction-cycle": (
            "material-cycle boundary",
            "algorithm_principles.md",
            "counts, quotas, votes, and quorum never do",
            "exactly one pro innovator",
            "exactly one pro convergence",
            "returns frozen requests through root",
            "common v1 envelope",
        ),
        "hmasd-cm-engineering-cycle": (
            "contract-first gate",
            "writer cardinality follows those gaps",
            "exactly one writer owns every overlapping boundary",
            "singleton `hmasd-browser-transport` service",
            "no mandatory engineering document suite",
        ),
        "hmasd-result-run": (
            "7200",
            "memory",
            "`8` for the user decision boundary",
            "one operator",
            "never start a successor",
        ),
        "hmasd-browser-transport": (
            "browsertransport",
            "observe -> interpret -> act -> verify",
            "strict operation",
            "agentify operation",
            "provider conversation",
            "browser tab",
            "prompt file",
            "archive file",
            "unknown commitment",
            "zero_send_failed",
            "sent_unreadable",
        ),
        "hmasd-scientific-external-review": (
            "exactly one pro innovator",
            "exactly one pro convergence",
            "chatgpt pro",
            "one fresh cycle has only these two pro operations",
            "unknown commitment is terminal for sending",
        ),
        "hmasd-workflow-recovery": (
            "pure research task failed",
            "manager missing after resume",
            "partial code work",
            "run or result says running",
            "memory refusal",
            "git writer conflict",
            "push outcome unknown",
            "external commitment unknown",
            "late transport or specialist result",
            "dashboard failure",
            "compaction boundary",
            "reconstruct",
            "at most three",
            "superseded evidence",
            "user-visible blocker",
        ),
        "hmasd-git-integration": (
            "canonical",
            "omp/workflow",
            "one candidate commit",
            "stale base",
            "em:<direction>",
            "cm:<direction>",
        ),
        "hmasd-paper-lookup": ("on-demand", "explicit network boundary"),
        "hmasd-hypothesis-mechanisms": ("only on demand", "not a manager autoload"),
        "hmasd-experimental-design-tools": ("optional tool only", "not autoloaded"),
        "hmasd-scientific-writing-validation": (
            "on-demand professional research tool",
            "not standing manager context",
        ),
        "hmasd-symbolic-counterexample-tools": (
            "on-demand observation tool",
            "not a root, em, or cm autoload",
        ),
        "hmasd-scientific-compute-contracts": (
            "not manager-autoloaded",
            "optional research-tools environment",
        ),
    }
    skills_root = REPO_ROOT / ".omp" / "skills"
    skill_paths = sorted(skills_root.glob("*/SKILL.md"))
    assert {path.parent.name for path in skill_paths} == set(expected_anchors)
    assert len(skill_paths) == 14
    assert {
        path.name for path in skills_root.iterdir() if path.is_dir()
    } == set(expected_anchors)
    assert not (skills_root / "hmasd-portfolio-control").exists()
    for path in skill_paths:
        metadata = _parse_frontmatter(path)
        assert _string_field(metadata, "name") == path.parent.name
        assert _string_field(metadata, "description")
        body = path.read_text(encoding="utf-8")
        lower_body = " ".join(body.lower().split())
        for anchor in expected_anchors[path.parent.name]:
            assert anchor in lower_body, (path, anchor)

    project_agents = sorted(AGENT_ROOT.glob("*.md"))
    for agent_path in project_agents:
        autoloaded = _list_field(_parse_frontmatter(agent_path), "autoloadSkills")
        assert not set(autoloaded).intersection(ON_DEMAND_RESEARCH_SKILLS), agent_path
    config = (REPO_ROOT / ".omp" / "config.yml").read_text(encoding="utf-8")
    assert "autoload" not in config.lower()
    for skill in ON_DEMAND_RESEARCH_SKILLS:
        assert skill not in config

    inventory = (REPO_ROOT / ".omp" / "AGENTS.md").read_text(encoding="utf-8")
    assert "On-demand P1 research tools" in inventory
    for skill in ON_DEMAND_RESEARCH_SKILLS:
        assert skill in inventory
    assert "not agent-profile/config autoloads or default manager dependencies" in inventory
    assert "Loading a skill grants no authority or Effect" in inventory

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
        assert "omp/workflow" in lowered

    instructions_lower = instructions.lower()
    assert "git add -a" in instructions_lower
    assert "unrelated" in instructions_lower
    assert "fetch" in instructions_lower

    combined = "\n".join((instructions, root_skill, concept, implementation))
    assert "em:<direction>" in combined
    assert "cm:<direction>" in combined
    assert "unknown push" in combined.lower()
    assert "conflict" in combined.lower()
    root_skill_compact = " ".join(root_skill.lower().split())
    for trigger in (
        "completed research or engineering rounds",
        "accepted-result or terminal-run evidence promotion",
        "external prompt/archive readiness",
        "portfolio lifecycle changes",
        "schema migrations",
    ):
        assert trigger in root_skill_compact


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
