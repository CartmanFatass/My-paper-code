from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
README = ROOT / ".codex" / "agents" / "README.md"
TEMPLATE = ROOT / "docs" / "superpowers" / "subagent-templates" / "hmasd-dispatch-templates.md"
REFERENCE = ROOT / "docs" / "subagents" / "hmasd-subagent-workflow-reference.md"
AGENT_DIR = ROOT / ".codex" / "agents"
CONFIG = ROOT / ".codex" / "config.toml"

STATUS_TERMS = ("DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED")
COMMON_RUNTIME_FIELDS = (
    "name",
    "description",
    "sandbox_mode",
    "approval_policy",
    "nickname_candidates",
    "developer_instructions",
)

EXPECTED_PROFILES = {
    "CodebaseScout": "codebase-scout.toml",
    "SimplePatcher": "simple-patcher.toml",
    "TestRunner": "test-runner.toml",
    "FastReviewer": "fast-reviewer.toml",
    "Implementer": "implementer.toml",
    "PlanImplementer": "plan-implementer.toml",
    "ImplementationReviewer": "implementation-reviewer.toml",
    "ExpManager": "exp-manager.toml",
    "ResultAnalyst": "result-analyst.toml",
    "ExternalReviewManager": "external-review-manager.toml",
    "LongTimeMemoryManager": "long-time-memory-manager.toml",
    "WorkflowAuditor": "workflow-auditor.toml",
    "PlanImplementerFrontier": "plan-implementer-frontier.toml",
    "ImplementationReviewerFrontier": "implementation-reviewer-frontier.toml",
    "SparkExplicitSimplePatcher": "spark-explicit-simple-patcher.toml",
}

OBSOLETE_AGENT_NAMES = {
    "LunaCodebaseScout",
    "LunaSimplePatcher",
    "LunaTestRunner",
    "TerraImplementer",
    "TerraFastReviewer",
    "TerraExpManager",
    "TerraResultAnalyst",
    "TerraExternalReviewManager",
    "TerraLongTimeMemoryManager",
    "SolWorkflowAuditor",
    "SolPlanImplementer",
    "SolImplementationReviewer",
    "SolPlanImplementerFrontier",
    "SolImplementationReviewerFrontier",
}

REQUIRED_TEXT = {
    AGENTS: (
        "Subagent Terminal Status Protocol",
        "Mandatory Dispatch Brief Gate",
        "No project subagent may be spawned",
        "Runtime Output Contract",
        "logs/<experiment-id-or-run-id>",
        "unexpected root-level runtime files",
        "Pre-Flight Wave Review",
        "Review Package Protocol",
        "PlanImplementerFrontier",
        "Reviewer cost is controlled by explicit reviewer model tiers",
        "final whole-branch review",
        "fix -> re-review",
        "Spec Compliance",
        "Code Quality",
        "Do not retry with the same model",
        "batch-fix brief",
        "LunaSimplePatcher",
        "TerraImplementer",
        "SolPlanImplementer",
        "SparkExplicitSimplePatcher",
        "Cache-Aware Subagent Lifetime",
        "prompt_cache_key",
        "max_threads = 12",
        "retention capacity",
        "send_input",
    ),
    README: (
        "Terminal Status Protocol",
        "Mandatory Dispatch Brief Gate",
        "No project subagent may be spawned",
        "Runtime Output Contract",
        "logs/<experiment-id-or-run-id>",
        "unexpected root-level runtime files",
        "No-Blind-Retry Rule",
        "Pre-Flight Review",
        "Review Packages And Batch Fixes",
        "PlanImplementerFrontier",
        "Reviewer cost control uses explicit model-tier roles",
        "final whole-branch review",
        "fix -> re-review",
        "Spec Compliance",
        "Code Quality",
        "one batch-fix brief",
        "LunaSimplePatcher",
        "TerraImplementer",
        "SolPlanImplementer",
        "SparkExplicitSimplePatcher",
        "cache-aware policy",
        "max_threads = 12",
        "send_input",
        "`DONE` is a task status",
    ),
    TEMPLATE: (
        "Shared Short Reply Contract",
        "Pre-Flight Wave Table",
        "Do not spawn a project subagent until",
        "Runtime output rule",
        "logs/<experiment-id-or-run-id>",
        "Loose repository-root runtime files",
        "PlanImplementer Dispatch",
        "PlanImplementerFrontier Dispatch",
        "SparkExplicitSimplePatcher Dispatch",
        "ExpManager Dispatch",
        "ResultAnalyst Dispatch",
        "ImplementationReviewer Dispatch",
        "Reviewer profile/model tier",
        "Spec Compliance",
        "Code Quality",
        "Batch Review Fix Dispatch",
        "TestRunner Dispatch",
        "CodebaseScout Dispatch",
        "WorkflowAuditor Dispatch",
        "LunaSimplePatcher",
        "TerraImplementer",
        "SolPlanImplementer",
        "SparkExplicitSimplePatcher",
    ),
    REFERENCE: (
        "Status: exploratory living reference",
        "Latest explicit user request",
        "not an active skill",
        "not a requirement to run Superpowers",
        "Superpowers Pattern Lessons",
        "Custom Subagent Design Checklist",
        "Main Controller Dispatch Gate",
        "Minimum fields",
        "Runtime output ownership",
        "logs/<experiment-id-or-run-id>",
        "Current Working Principles",
        "Controller Communication Contract",
        "Model-Tier Reference",
        "PlanImplementerFrontier",
        "Update Checklist For Subagent Workflow Changes",
        "Decision Log",
    ),
}

FORBIDDEN_PATTERNS = (
    re.compile(r"\b2" + r"-3 agents\b", re.IGNORECASE),
    re.compile(r"old2", re.IGNORECASE),
    re.compile(r"not a hard " + r"cap", re.IGNORECASE),
    re.compile(r"not a " + r"cap", re.IGNORECASE),
    re.compile(r"fallback to (worker|explorer|default)", re.IGNORECASE),
    re.compile(r"automatic review after every small task", re.IGNORECASE),
    re.compile(r"not automatically after every small task", re.IGNORECASE),
    re.compile(r"automatic per-task review", re.IGNORECASE),
    re.compile(r"not as an automatic per-small-task reviewer", re.IGNORECASE),
    re.compile(r"Review only at batch, milestone, high-risk, or final gates", re.IGNORECASE),
)

REQUIRED_REVIEWER_NAMES = {
    "FastReviewer",
    "ImplementationReviewer",
    "ImplementationReviewerFrontier",
}


def read_text(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def require_terms(path: Path, terms: tuple[str, ...]) -> None:
    text = read_text(path)
    for term in terms:
        if term not in text:
            raise AssertionError(f"{path} missing required term: {term}")
    for status in STATUS_TERMS:
        if status not in text:
            raise AssertionError(f"{path} missing status term: {status}")


def check_forbidden(path: Path) -> None:
    text = read_text(path)
    for pattern in FORBIDDEN_PATTERNS:
        match = pattern.search(text)
        if match:
            raise AssertionError(f"{path} has forbidden phrase: {match.group(0)!r}")


def check_toml(path: Path) -> None:
    data = tomllib.loads(read_text(path))
    for field in COMMON_RUNTIME_FIELDS:
        if field not in data:
            raise AssertionError(f"{path} missing runtime field: {field}")
    instructions = str(data["developer_instructions"])
    for status in STATUS_TERMS:
        if status not in instructions:
            raise AssertionError(f"{path} developer_instructions missing {status}")
    for phrase in (
        "Status:",
        "Artifact/report:",
        "Changed files:",
        "Commands/tests:",
        "Concerns/blockers:",
        "Next owner:",
    ):
        if phrase not in instructions:
            raise AssertionError(f"{path} developer_instructions missing short reply field {phrase!r}")


def check_agent_identity_contract(toml_files: list[Path]) -> None:
    config = tomllib.loads(read_text(CONFIG))
    features = config.get("features", {})
    if features.get("multi_agent") is not True:
        raise AssertionError("multi_agent must remain true")
    if features.get("multi_agent_v2") is not False:
        raise AssertionError("multi_agent_v2 must remain false")
    raw_agents = config.get("agents")
    if not isinstance(raw_agents, dict):
        raise AssertionError(f"{CONFIG} missing [agents] table")
    for field, expected in (
        ("max_threads", 12),
        ("max_depth", 1),
        ("job_max_runtime_seconds", 1800),
    ):
        if raw_agents.get(field) != expected:
            raise AssertionError(f"agents.{field} must remain {expected}")
    for field in ("model", "model_reasoning_effort"):
        if field in config:
            raise AssertionError(f"project config must not pin controller {field}")
    registry = {
        name: entry
        for name, entry in raw_agents.items()
        if isinstance(entry, dict) and "config_file" in entry
    }
    expected_names = set(EXPECTED_PROFILES)
    registry_names = set(registry)
    missing = sorted(expected_names - registry_names)
    unexpected = sorted(registry_names - expected_names)
    if missing or unexpected:
        raise AssertionError(
            f"{CONFIG} agent registry mismatch: missing={missing}, unexpected={unexpected}"
        )
    obsolete = sorted(OBSOLETE_AGENT_NAMES & registry_names)
    if obsolete:
        raise AssertionError(f"{CONFIG} retains obsolete agent aliases: {obsolete}")

    expected_files = set(EXPECTED_PROFILES.values())
    actual_files = {path.name for path in toml_files}
    missing_files = sorted(expected_files - actual_files)
    unexpected_files = sorted(actual_files - expected_files)
    if missing_files or unexpected_files:
        raise AssertionError(
            f"{AGENT_DIR} profile files mismatch: "
            f"missing={missing_files}, unexpected={unexpected_files}"
        )

    for name, filename in EXPECTED_PROFILES.items():
        entry = registry[name]
        config_file = str(entry["config_file"])
        expected_config_file = f"./agents/{filename}"
        if config_file != expected_config_file:
            raise AssertionError(
                f"{CONFIG} registration for {name} points to {config_file!r}, "
                f"expected {expected_config_file!r}"
            )
        profile_path = AGENT_DIR / filename
        data = tomllib.loads(read_text(profile_path))
        if data.get("name") != name:
            raise AssertionError(f"{profile_path} name does not match {name}")
        instructions = str(data.get("developer_instructions", ""))
        if name == "SparkExplicitSimplePatcher":
            if data.get("model") != "gpt-5.3-codex-spark":
                raise AssertionError(f"{profile_path} must pin gpt-5.3-codex-spark")
            if data.get("model_reasoning_effort") != "low":
                raise AssertionError(f"{profile_path} must use low reasoning")
            if "Legacy Spark opt-in: explicitly requested" not in instructions:
                raise AssertionError(
                    f"{profile_path} missing explicit Legacy Spark opt-in contract"
                )
        else:
            forbidden_pins = sorted(
                field
                for field in ("model", "model_reasoning_effort", "service_tier")
                if field in data
            )
            if forbidden_pins:
                raise AssertionError(f"{profile_path} pins routing fields: {forbidden_pins}")


def check_reviewer_tiers(toml_files: list[Path]) -> None:
    names: set[str] = set()
    for path in toml_files:
        data = tomllib.loads(read_text(path))
        names.add(str(data.get("name", "")))
    missing = sorted(REQUIRED_REVIEWER_NAMES - names)
    if missing:
        raise AssertionError(f"missing reviewer tier agents: {', '.join(missing)}")


def main() -> int:
    try:
        toml_files = sorted(AGENT_DIR.glob("*.toml"))
        if not toml_files:
            raise AssertionError(f"no TOML files found under {AGENT_DIR}")
        check_agent_identity_contract(toml_files)
        for path, terms in REQUIRED_TEXT.items():
            require_terms(path, terms)
        for path in (AGENTS, README, TEMPLATE):
            check_forbidden(path)
        check_reviewer_tiers(toml_files)
        for path in toml_files:
            check_toml(path)
        print("HMASD subagent protocol validation ok")
        return 0
    except AssertionError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
