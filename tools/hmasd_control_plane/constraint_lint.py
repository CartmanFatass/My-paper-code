"""Boundary-only lint for hard constraints without registered provenance."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ConstraintFinding:
    path: str
    line: int
    kind: str
    text: str
    registered: bool = False


_PATTERNS = (
    ("DIRECTION_CAP", re.compile(r"(?:fixed|maximum|max(?:imum)?|hard|global|project[- ]wide)\s+(?:direction|directions)|direction(?:[- ]count| count| number)?\s+(?:cap|limit|maximum|max(?:imum)?)|\b\d+[- ]direction", re.I)),
    (
        "WORKER_LIMIT",
        re.compile(
            r"\b(?:global|project[- ]wide|default|fixed|hard upper|maximum|max(?:imum)?)\b[^.\n]{0,80}\bworkers?\b|"
            r"\bworkers?\b[^.\n]{0,80}\b(?:default|cap|limit|maximum|max(?:imum)?)\b|"
            r"\b(?:every|all)\s+worker(?:/environment)?(?:[- ]count| count)?\s+must\s+be\s+exactly\s+\d+\b",
            re.I,
        ),
    ),
    ("HASH_HANDOFF", re.compile(r"(?:internal|repository).*handoff.*(?:sha|hash)|(?:sha-?256|hash).*required", re.I)),
    ("ONE_ATTEMPT", re.compile(r"one[- ]attempt|no[- ]retry|never retry|exactly one attempt", re.I)),
    ("WALL_CLOCK_STOP", re.compile(r"(?:hard|absolute|scientific).*wall[- ]?clock.*(?:stop|limit)|stop.*(?:after|at).*\d+.*(?:hour|day)", re.I)),
    ("FIXED_REVIEW_CHAIN", re.compile(r"(?:exactly|fixed|mandatory|required).*review(?:er| chain)|review(?:er| chain).*required", re.I)),
)


COMPATIBLE_REQUIREMENTS = {
    "DIRECTION_CAP": {"NR-DIRECTION-CAP-001"},
    "WORKER_LIMIT": {"NR-WORKER-LIMIT-001", "UR-RESOURCE-001"},
    "HASH_HANDOFF": {"NR-HASH-HANDOFF-001"},
    "ONE_ATTEMPT": set(),
    "WALL_CLOCK_STOP": {"UR-PERF-001"},
    "FIXED_REVIEW_CHAIN": set(),
}


_NEGATIONS = {
    "DIRECTION_CAP": re.compile(
        r"\b(?:there is\s+no|no)\s+(?:required\s+|fixed\s+|hard\s+|global\s+|project[- ]wide\s+)*"
        r"(?:portfolio\s+)?(?:direction(?:[- ]count| count| number)?(?:\s+(?:cap|limit|maximum|max(?:imum)?))?|"
        r"(?:required\s+)?number\s+of\s+(?:leading,?\s+paused,?\s+or\s+retired\s+)?directions)|"
        r"\bno\s+longer\s+required\b[^.]*\bfixed\s+direction\b",
        re.I,
    ),
    "WORKER_LIMIT": re.compile(
        r"\b(?:there is\s+no|no)\s+(?:project[- ]wide\s+|global\s+|fixed\s+|hard\s+|default\s+|required\s+)*"
        r"(?:(?:default\s+or\s+hard\s+upper\s+limit\s+for\s+)?worker(?:/environment)?(?:[- ]count| count)?"
        r"\s*(?:default|cap|limit|maximum|max(?:imum)?)?|fixed\s+width)",
        re.I,
    ),
    "HASH_HANDOFF": re.compile(
        r"\b(?:internal\s+|repository\s+)?handoffs?\s+(?:do|does)\s+not\s+require\s+(?:sha-?256|hash)|"
        r"\bno\s+(?:sha-?256|hash)\s+(?:is\s+)?required\b",
        re.I,
    ),
    "ONE_ATTEMPT": re.compile(
        r"\b(?:there is\s+no|no)\s+(?:fixed\s+|required\s+|global\s+)*(?:one[- ]attempt|no[- ]retry)\b|"
        r"\blegacy\b[^.]*\b(?:one[- ]attempt|no[- ]retry)\b|"
        r"\b(?:one[- ]attempt|no[- ]retry)\b[^.]*\b(?:is\s+not|are\s+not|not\s+[^.]{0,40}(?:authority|command)|"
        r"remain\s+(?:mechanical\s+facts|factual\s+anchors)|required\s+not|never\s+means)\b",
        re.I,
    ),
    "WALL_CLOCK_STOP": re.compile(
        r"\b(?:there is\s+no|no)\s+(?:hard\s+|absolute\s+|scientific\s+)*wall[- ]?clock\s+(?:stop|limit)\b",
        re.I,
    ),
    "FIXED_REVIEW_CHAIN": re.compile(
        r"\b(?:there is\s+no|no)\s+(?:fixed\s+|mandatory\s+|required\s+|routine\s+)*review(?:er| chain)\b|"
        r"\breview(?:er| chain)[^.]*\b(?:optional|not\s+(?:mandatory|required))\b|"
        r"\b(?:do|must)\s+not\s+build\b[^.]*\bmandatory\b[^.]*\breview\s+chain\b",
        re.I,
    ),
}


_EXCLUDED_REPOSITORY_PATHS = {
    Path("docs/project/PROJECT_REQUIREMENTS.md"),
    Path("docs/project/archive/CURRENT_WORK_LEGACY_2026-08-01.md"),
    Path("docs/project/migration-validation/2026-08-10_cli_two_level_control_plane_final_audit.md"),
    Path("docs/project/migration-validation/2026-08-11_direction_scoped_owner_restart_handoff.md"),
}


def _requirement_ids(block: str) -> set[str]:
    return {
        match.upper()
        for match in re.findall(r"\b(?:UR|NR)-[A-Z0-9_.-]+\b", block, re.I)
    }


def _explicitly_constrains(kind: str, block: str) -> bool:
    if kind != "WORKER_LIMIT":
        return False
    local_selector = bool(
        re.search(
            r"resource_preflight_ref|assignment_local\s*=\s*true|"
            r"worker(?:/environment)?(?:[- ]count| count)?[^.]*selected\s+from[^.]*resource\s+preflight",
            block,
            re.I,
        )
    )
    prohibited_scope = bool(
        re.search(r"\b(?:global|project[- ]wide|default|hard upper|maximum|max(?:imum)?)\b", block, re.I)
    )
    return local_selector and not prohibited_scope


def _is_exact_operation_retry_fence(kind: str, block: str) -> bool:
    if kind != "ONE_ATTEMPT":
        return False
    return bool(
        re.search(
            r"\b(?:same|exact)\s+(?:operation|fingerprint|turn|call)\b|"
            r"\bno\s+retry\s+inside\s+the\s+call\b|"
            r"\bSame:\s*[^|\n]*(?:no|never)\s+retry[^|\n]*\bNew:",
            block,
            re.I,
        )
    )


def _match_is_requirement_id(block: str, match: re.Match[str]) -> bool:
    return any(
        requirement.start() <= match.start()
        and match.end() <= requirement.end()
        for requirement in re.finditer(
            r"\b(?:UR|NR)-[A-Z0-9_.-]+\b", block, re.I
        )
    )


def _local_match_context(block: str, match: re.Match[str]) -> str:
    line_start = block.rfind("\n", 0, match.start()) + 1
    line_end = block.find("\n", match.end())
    if line_end == -1:
        line_end = len(block)
    line = block[line_start:line_end]
    if line.lstrip().startswith("|"):
        return line

    clause_start = max(block.rfind(mark, 0, match.start()) for mark in ".!?;") + 1
    clause_ends = [
        position
        for mark in ".!?;"
        if (position := block.find(mark, match.end())) != -1
    ]
    clause_end = min(clause_ends) + 1 if clause_ends else len(block)
    return block[clause_start:clause_end]


def lint_text(text: str, path: str = "<text>") -> list[ConstraintFinding]:
    findings: list[ConstraintFinding] = []
    offset = 0
    for block in re.split(r"\n\s*\n", text):
        start_line = text[:offset].count("\n") + 1
        offset += len(block) + 2
        for kind, pattern in _PATTERNS:
            for match in pattern.finditer(block):
                if _match_is_requirement_id(block, match):
                    continue
                local_context = re.sub(
                    r"\s+", " ", _local_match_context(block, match)
                ).strip()
                requirement_ids = _requirement_ids(local_context)
                registered = bool(
                    requirement_ids
                    or re.search(
                        r"\[REQ:[A-Z0-9_.-]+\]|assignment_local\s*=\s*true|science_contract\s*=",
                        local_context,
                        re.I,
                    )
                )
                negates_rule = bool(_NEGATIONS[kind].search(local_context))
                compatible = bool(
                    requirement_ids & COMPATIBLE_REQUIREMENTS[kind]
                )
                if (
                    negates_rule
                    or _is_exact_operation_retry_fence(kind, local_context)
                    or (
                        compatible
                        and _explicitly_constrains(kind, local_context)
                    )
                ):
                    continue
                match_line = start_line + block[: match.start()].count("\n")
                findings.append(
                    ConstraintFinding(
                        path,
                        match_line,
                        kind,
                        block.strip(),
                        registered,
                    )
                )
                break
    return findings


def lint_paths(paths: Iterable[Path]) -> list[ConstraintFinding]:
    findings: list[ConstraintFinding] = []
    for path in paths:
        if path.suffix.lower() not in {".md", ".toml"} or not path.is_file():
            continue
        findings.extend(lint_text(path.read_text(encoding="utf-8"), str(path)))
    return findings


def lint_repository(root: Path) -> list[ConstraintFinding]:
    scan_roots = (
        root / "AGENTS.md",
        root / "docs/project",
        root / ".agents/roles",
        root / ".agents/skills",
    )
    paths: list[Path] = []
    for scan_root in scan_roots:
        candidates = [scan_root] if scan_root.is_file() else scan_root.rglob("*")
        for path in candidates:
            try:
                relative_path = path.relative_to(root)
            except ValueError:
                continue
            if relative_path in _EXCLUDED_REPOSITORY_PATHS:
                continue
            if path.is_file() and path.suffix.lower() in {".md", ".toml"}:
                paths.append(path)
    return lint_paths(paths)
