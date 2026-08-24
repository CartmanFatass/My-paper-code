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
    ("WORKER_LIMIT", re.compile(r"(?:global|project[- ]wide|default|fixed|hard upper|maximum|max(?:imum)?).*worker|worker.*(?:default|cap|limit|maximum|max(?:imum)?)", re.I)),
    ("HASH_HANDOFF", re.compile(r"(?:internal|repository).*handoff.*(?:sha|hash)|(?:sha-?256|hash).*required", re.I)),
    ("ONE_ATTEMPT", re.compile(r"one[- ]attempt|no[- ]retry|never retry|exactly one attempt", re.I)),
    ("WALL_CLOCK_STOP", re.compile(r"(?:hard|absolute|scientific).*wall[- ]?clock.*(?:stop|limit)|stop.*(?:after|at).*\d+.*(?:hour|day)", re.I)),
    ("FIXED_REVIEW_CHAIN", re.compile(r"(?:exactly|fixed|mandatory|required).*review(?:er| chain)|review(?:er| chain).*required", re.I)),
)


def lint_text(text: str, path: str = "<text>") -> list[ConstraintFinding]:
    findings: list[ConstraintFinding] = []
    offset = 0
    for block in re.split(r"\n\s*\n", text):
        start_line = text[:offset].count("\n") + 1
        offset += len(block) + 2
        flat = re.sub(r"\s+", " ", block)
        registered = bool(re.search(r"\[REQ:[A-Z0-9_.-]+\]|\b(?:UR|NR)-[A-Z0-9_.-]+\b|assignment_local\s*=\s*true|science_contract\s*=", flat, re.I))
        negated = bool(re.search(
            r"\b(?:there is no|no required|no fixed|not required|no longer required|"
            r"optional|neither prerequisites?|do not build|must not build)\b[^.]*?"
            r"(?:fixed|default|global|hard|maximum|cap|limit|direction|worker|review)",
            flat,
            re.I,
        ))
        historical_non_authority = bool(re.search(
            r"(?:no (?:scientific|portfolio).*authority|not .*routing authority|"
            r"legacy[^.]*?(?:factual|mechanical|not .*authority|cannot gate|not .*command))",
            flat,
            re.I,
        ))
        if historical_non_authority or (negated and not re.search(r"\b(?:retry|resend|one[- ]attempt)\b", flat, re.I)):
            continue
        allowed_assignment = registered and ("resource_preflight_ref" in block or "NR-WORKER-LIMIT-001" in block)
        for kind, pattern in _PATTERNS:
            match = pattern.search(block)
            if not match:
                continue
            if registered and (kind != "WORKER_LIMIT" or allowed_assignment):
                continue
            findings.append(ConstraintFinding(path, start_line, kind, block.strip(), registered))
    return findings


def lint_paths(paths: Iterable[Path]) -> list[ConstraintFinding]:
    findings: list[ConstraintFinding] = []
    for path in paths:
        if path.suffix.lower() not in {".md", ".toml"} or not path.is_file():
            continue
        findings.extend(lint_text(path.read_text(encoding="utf-8"), str(path)))
    return findings


def lint_repository(root: Path) -> list[ConstraintFinding]:
    excluded = {
        "AGENTIFY_TRANSPORT_INSTRUCTIONS.md", "EFFICIENCY_PRACTICES.md", "ExpRecord.md",
        "PROJECT_REQUIREMENTS.toml", "PROJECT_REQUIREMENTS.md",
    }
    paths = [path for path in (root / "docs/project").rglob("*.md") if path.name not in excluded and "migration-validation" not in path.parts]
    paths += [path for path in (root / "docs/project").rglob("*.toml") if path.name not in excluded]
    roles_root = root / ".agents/roles"
    skills_root = root / ".agents/skills"
    if roles_root.exists():
        paths += list(roles_root.rglob("*.md"))
    if skills_root.exists():
        paths += list(skills_root.rglob("SKILL.md"))
    paths += [root / "AGENTS.md"]
    return lint_paths(paths)
