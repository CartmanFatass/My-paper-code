"""Structural closure check for the HMASD control plane.

The control plane is `CLAUDE.md`, `AGENTS.md`, `.claude/agents/*.md` and
`.claude/skills/*/SKILL.md`. This checker asks one question of it: does every
rule name something that actually exists?

It exists because on 2026-07-28 a rule was found that had never been executable.
`hmasd-compaction/SKILL.md` said the cadence "must survive the thing it governs,
so `CURRENT_WORK.md` carries `iterations_since_last_compaction`" -- and that key
had never been written to that file, in any revision. The rule had been read many
times and followed never, because nothing compared the claim against the file it
named. Check H below is that comparison.

Ported from HMASD-new's `check_hmasd_agent_harness.py`. Checks B-G are the same
idea retargeted from `.codex` TOML profiles and `.agents/roles/` to this repo's
Claude-Code-native surfaces; that four-manager role tree does not exist here and
is deliberately not reintroduced.

Exit 0 prints a one-line OK with counts. Exit 1 prints one ERROR line per
finding on stderr.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
BACKTICK = re.compile(r"`([^`\r\n]+)`")
AGENT_NAME = re.compile(r"(?<![\w-])(hmasd-[a-z0-9-]+)(?![\w-])")
# A state key: lowercase, contains an underscore, long enough not to be prose.
STATE_KEY = re.compile(r"\A[a-z][a-z0-9]*(_[a-z0-9]+)+\Z")

DEFAULT_ACTIVE_PATHS = ("CLAUDE.md", "AGENTS.md", ".claude/agents", ".claude/skills")
# Names that were retired. A retired name in an active document is a live rule
# pointing at something that no longer exists.
# Only this repository's own retirements. A name retired elsewhere is not our
# business, and `.agents/roles` in particular appears in AGENTS.md as the record
# of a deletion -- history, not a live rule.
DEFAULT_FORBIDDEN = (
    "hmasd-compaction",
    "RESTART_HANDOFF",
    "iterations_since_last_compaction",
    # Retired 2026-07-25; its dispatch instruction survived in a rendered .ps1
    # prompt until 2026-07-31 because this scan covers only .md. The rendered
    # output is guarded by review_round_contract_test.ps1; this entry keeps the
    # name out of the md surface. Historical records say "delegated transport
    # child" instead of the name.
    "exchanger",
    # The cloud vehicle and every cross-device comparison design, retired by
    # user ruling 2026-08-01. One stem covers the routing doc and its rule.
    "COMPUTE_ROUTING",
    # The browser review transport, retired 2026-08-01 for the Agentify receipt
    # transport. One stem each for the tool namespace, the page monitor, the
    # heartbeat renderer and the browser bring-up script.
    "claude-in-chrome",
    "hmasd-review-monitor",
    "render_review_heartbeat",
    "ensure_review_browser",
)
# Referenced paths that are legitimately patterns or external, not files on disk.
REF_EXEMPT_SUFFIXES = ("/", "*")

# A cross-reference that names BOTH a document and a section of it:
#   `AGENTS.md`, **Scientific restraint**
#   (root `AGENTS.md`, "Acceptance, tests, and review")
#   `$hmasd-review-round`, **Convergence turns**
# Matched against whitespace-normalised paragraphs, so a reference that wraps
# across two lines is still one reference. `_repo_refs` cannot catch this class:
# the FILE resolves, and only the section inside it is gone.
SECTION_REF = re.compile(
    r"`(?P<target>[$A-Za-z0-9_/.-]+)`,\s*"
    r"(?:\*\*(?P<bold>[^*]+)\*\*|\"(?P<quoted>[^\"]+)\")"
)
# Documents that are not control plane themselves but are ROUTED from CLAUDE.md,
# so a dangling section reference in one misdirects whoever follows the route.
ROUTED_PROJECT_DOCS = (
    "docs/project/ALGORITHM_PRINCIPLES.md",
    "docs/project/EVIDENCE_COMPLEXITY_POLICY.md",
    "docs/project/AGENT_CONTEXT.md",
    "docs/project/RESEARCH_GOAL.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def _body(text: str) -> str:
    match = FRONTMATTER.match(text)
    return text[match.end():] if match else text


def _repo_refs(text: str) -> set[str]:
    """Backticked repository paths a document asserts exist."""
    refs: set[str] = set()
    for value in BACKTICK.findall(text):
        value = value.replace("\\", "/").strip()
        if not value.startswith((".claude/", "docs/", "scripts/", "tests/", "logs/")):
            continue
        if any(char in value for char in "*<>|$") or " " in value:
            continue
        value = value.rstrip(".,:;")
        if value.endswith(REF_EXEMPT_SUFFIXES):
            continue
        refs.add(value)
    return refs


def _paragraphs(text: str) -> Iterable[str]:
    for block in re.split(r"\r?\n\s*\r?\n", text):
        yield " ".join(block.split())


def _check_agents(repo: Path, errors: list[str]) -> tuple[dict[str, Path], str]:
    agent_root = repo / ".claude/agents"
    agents: dict[str, Path] = {}
    for path in sorted(agent_root.glob("*.md")):
        fields = _frontmatter(_read(path))
        if not fields:
            errors.append(f"agent definition has no parseable frontmatter: {path}")
            continue
        name = fields.get("name", "")
        if not name:
            errors.append(f"agent definition has no name: {path}")
            continue
        if name != path.stem:
            errors.append(f"agent name/filename mismatch: {path.name} declares {name}")
        if not fields.get("description"):
            errors.append(f"agent {name} has no description -- it can never be selected")
        # An omitted `tools` key is not a defect: it inherits the full grant.
        # Checking for its presence flagged hmasd-implementer, which omits it on
        # purpose. A checker that cries wolf gets ignored, which is worse than
        # not having it.
        if name in agents:
            errors.append(f"duplicate agent name {name}: {agents[name]} and {path}")
        agents[name] = path
    return agents, "\n".join(_read(p) for p in sorted(agent_root.glob("*.md")))


def _check_skills(repo: Path, errors: list[str]) -> dict[str, Path]:
    skill_root = repo / ".claude/skills"
    skills: dict[str, Path] = {}
    for directory in sorted(p for p in skill_root.iterdir() if p.is_dir()):
        doc = directory / "SKILL.md"
        if not doc.is_file():
            if any(p.is_file() for p in directory.rglob("*")):
                errors.append(f"skill directory has no SKILL.md: {directory}")
            continue
        name = _frontmatter(_read(doc)).get("name", "")
        if not name:
            errors.append(f"skill has no name in frontmatter: {doc}")
            continue
        if name != directory.name:
            errors.append(f"skill name/directory mismatch: {directory.name} declares {name}")
        skills[name] = doc
    return skills


def audit_repo(
    repo: Path,
    extra_active_paths: Iterable[str] = (),
    extra_forbidden: Iterable[str] = (),
    allow_forbidden: Iterable[str] = (),
) -> list[str]:
    repo = repo.resolve()
    errors: list[str] = []

    claude_md = repo / "CLAUDE.md"
    agents_md = repo / "AGENTS.md"
    agent_root = repo / ".claude/agents"
    skill_root = repo / ".claude/skills"

    # A -- required surfaces.
    for required in (claude_md, agents_md, agent_root, skill_root):
        if not required.exists():
            errors.append(f"missing control-plane surface: {required}")
    if errors:
        return errors

    agents_text = _read(agents_md)
    claude_text = _read(claude_md)

    # B -- agent definitions are well formed.
    agents, agents_blob = _check_agents(repo, errors)
    # E -- skills are well formed.
    skills = _check_skills(repo, errors)
    skills_blob = "\n".join(_read(p) for p in skills.values())

    route_blob = "\n".join([agents_text, claude_text, skills_blob])

    # C -- every agent on disk is routed from somewhere that is actually loaded.
    for name, path in sorted(agents.items()):
        if name not in route_blob:
            errors.append(f"unrouted agent: {path} -- no document tells anyone to dispatch it")

    # D -- every agent named by a routing document exists on disk.
    for blob_name, blob in (("AGENTS.md", agents_text), ("CLAUDE.md", claude_text)):
        for ref in sorted(set(AGENT_NAME.findall(blob))):
            if ref not in agents and ref not in skills:
                errors.append(f"{blob_name} routes a missing agent or skill: {ref}")

    # E2 -- every skill is routed from AGENTS.md or CLAUDE.md. A skill nobody is
    # told to load is a skill nobody loads.
    for name, path in sorted(skills.items()):
        if name not in agents_text and name not in claude_text:
            errors.append(f"unrouted skill: {path}")

    # F -- backticked repository paths in control-plane documents resolve.
    control_docs = [claude_md, agents_md, *sorted(skills.values()), *sorted(agent_root.glob("*.md"))]
    for doc in control_docs:
        for ref in sorted(_repo_refs(_read(doc))):
            if not (repo / ref).exists():
                errors.append(f"broken path reference in {doc.relative_to(repo)}: {ref}")

    # I -- a document that names a file AND a section of it must name a section
    # that file actually contains. Check F proves the FILE exists and stops
    # there, which is why ALGORITHM_PRINCIPLES.md could point at AGENTS.md for
    # "Acceptance, tests, and review" -- a heading that has lived in
    # hmasd-acceptance-gate/SKILL.md since the split -- and pass for days.
    # Membership, not heading-shape: the claim being checked is that the referent
    # exists, exactly as everywhere else in this checker.
    for rel in (*[str(d.relative_to(repo)).replace("\\", "/") for d in control_docs],
                *ROUTED_PROJECT_DOCS):
        doc = repo / rel
        if not doc.exists():
            continue
        for paragraph in _paragraphs(_read(doc)):
            for match in SECTION_REF.finditer(paragraph):
                target = match.group("target")
                section = (match.group("bold") or match.group("quoted") or "").strip()
                if not section:
                    continue
                if target.startswith("$"):
                    resolved = skills.get(target[1:])
                else:
                    candidate = repo / target
                    resolved = candidate if candidate.exists() else None
                if resolved is None or not resolved.exists():
                    continue  # check D/F owns a missing target; do not double-report
                if section not in _read(resolved):
                    errors.append(
                        f"dangling section reference in {rel}: "
                        f"{target} does not contain {section!r}")

    # G -- retired names must not survive in an active document.
    allowed = set(allow_forbidden)
    forbidden = [m for m in (*DEFAULT_FORBIDDEN, *extra_forbidden) if m and m not in allowed]
    active_paths = [*DEFAULT_ACTIVE_PATHS, *extra_active_paths]
    for raw in active_paths:
        root = (repo / raw).resolve()
        if not root.exists():
            errors.append(f"active path is missing: {raw}")
            continue
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
        for path in files:
            if path.suffix.lower() != ".md":
                continue
            # This procedure's own document is the one place a retired name is
            # supposed to appear: it teaches the failure by naming it. Exempting
            # it is not a loophole -- every other control-plane document is still
            # scanned, including the other Skills.
            if "hmasd-workflow-change-audit" in path.parts:
                continue
            try:
                text = _read(path)
            except UnicodeDecodeError:
                continue
            for marker in forbidden:
                if marker in text:
                    errors.append(f"retired name {marker!r} still active in {path.relative_to(repo)}")

    # H -- the no-op detector. When a paragraph names exactly one document and
    # backticks a state key, that key must actually appear in that document.
    # This is the check that would have caught iterations_since_last_compaction:
    # a cadence whose counter never existed anywhere.
    for doc in control_docs:
        for para in _paragraphs(_body(_read(doc))):
            quoted = BACKTICK.findall(para)
            targets = [q for q in quoted if q.endswith(".md") and "/" in q.replace("\\", "/")]
            if len(set(targets)) != 1:
                continue
            target = (repo / targets[0].replace("\\", "/")).resolve()
            if not target.is_file():
                continue
            target_text = _read(target)
            for key in quoted:
                if not STATE_KEY.match(key) or len(key) < 8:
                    continue
                if key not in target_text:
                    errors.append(
                        f"unbacked state claim in {doc.relative_to(repo)}: "
                        f"names {key!r} as carried by {targets[0]}, which does not contain it"
                    )

    return errors


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Structural closure check for the HMASD control plane.")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--active-path", action="append", default=[])
    parser.add_argument("--forbid", action="append", default=[])
    parser.add_argument("--allow-forbidden", action="append", default=[],
                        help="Drop a default retired-name marker, for the commit that retires it.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    errors = audit_repo(args.repo, args.active_path, args.forbid, args.allow_forbidden)
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    repo = args.repo.resolve()
    agents = len(list((repo / ".claude/agents").glob("*.md")))
    skills = len(list((repo / ".claude/skills").glob("*/SKILL.md")))
    print(f"HMASD_CONTROL_PLANE_OK agents={agents} skills={skills}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
