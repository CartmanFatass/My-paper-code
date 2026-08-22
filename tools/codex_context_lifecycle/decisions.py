"""Durable shared decision records.

ADRs index shared architecture and control-plane choices. They do not restate
scientific, technical, or portfolio owner artifacts.
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 project interpreter
    import tomli as tomllib

from .models import DecisionRecord

ALLOWED_STATUSES = frozenset({"accepted", "superseded", "proposed"})
SHARED_ADR_OWNERS = frozenset({"operational_root", "user"})
DECISIONS_DIR = Path("docs/project/decisions")
INDEX_PATH = Path("docs/project/DECISIONS_INDEX.md")
EXTERNAL_SYSTEMS = (
    ("Portfolio adjudications", "docs/research/workflow-runs/2026-08-11_five-round-research-team/PORTFOLIO_OPERATIONAL_RECONCILIATION_20260814.md"),
    ("Science cards and EM interpretations", "docs/research/candidates/"),
    ("CM technical packets", "docs/research/workflow-runs/"),
    ("Research direction ledger", "docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md"),
)


class DecisionError(ValueError):
    """Raised when an ADR front matter is invalid."""


def _front_matter(text: str) -> dict[str, object]:
    if not text.startswith("+++"):
        raise DecisionError("TOML front matter is required")
    rest = text[3:]
    end = rest.find("\n+++")
    if end < 0:
        raise DecisionError("unterminated TOML front matter")
    return tomllib.loads(rest[:end])


def _as_tuple(value: object, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise DecisionError(f"{field} must be an array")
    return tuple(str(item) for item in value)


def parse_decision(path: Path) -> DecisionRecord:
    text = Path(path).read_text(encoding="utf-8")
    data = _front_matter(text)
    decision_id = str(data.get("decision_id") or "")
    owner = str(data.get("owner") or "")
    scope = str(data.get("scope") or "")
    status = str(data.get("status") or "")
    if not decision_id:
        raise DecisionError("decision_id is required")
    if not owner:
        raise DecisionError("missing owner")
    if not scope:
        raise DecisionError("missing scope")
    if status not in ALLOWED_STATUSES:
        raise DecisionError(f"unknown status: {status}")
    supersedes = _as_tuple(data.get("supersedes"), "supersedes")
    if decision_id in supersedes:
        raise DecisionError("self-supersede is forbidden")
    sources = _as_tuple(data.get("canonical_sources"), "canonical_sources")
    for source in sources:
        normalized = source.replace("\\", "/")
        if Path(normalized).is_absolute() or normalized.startswith("/") or (
            len(normalized) > 1 and normalized[1] == ":"
        ):
            raise DecisionError(f"absolute path is forbidden: {source}")
    return DecisionRecord(
        decision_id=decision_id,
        title=str(data.get("title") or ""),
        owner=owner,
        scope=scope,
        status=status,
        decision_date=str(data.get("decision_date") or ""),
        supersedes=supersedes,
        canonical_sources=sources,
        revisit_conditions=_as_tuple(data.get("revisit_conditions"), "revisit_conditions"),
        path=str(path).replace("\\", "/"),
    )


def validate_decision_set(
    root: Path,
    records: tuple[DecisionRecord, ...],
) -> tuple[str, ...]:
    errors: list[str] = []
    by_id = {item.decision_id: item for item in records}
    for record in records:
        if record.status == "accepted" and record.scope.startswith("shared:"):
            if record.owner not in SHARED_ADR_OWNERS:
                errors.append(
                    f"{record.decision_id}: shared accepted ADR owner must be operational_root or user"
                )
        for source in record.canonical_sources:
            if record.status == "accepted" and not (Path(root) / source).is_file():
                errors.append(
                    f"{record.decision_id}: missing canonical source {source}"
                )
        for superseded_id in record.supersedes:
            peer = by_id.get(superseded_id)
            if peer is None:
                errors.append(
                    f"{record.decision_id}: unknown superseded ADR {superseded_id}"
                )
            elif record.status == "accepted" and peer.status != "superseded":
                errors.append(
                    f"{record.decision_id}: superseded ADR {superseded_id} must be marked superseded"
                )
    return tuple(errors)


def collect_decisions(root: Path) -> tuple[DecisionRecord, ...]:
    directory = Path(root) / "docs" / "project" / "decisions"
    if not directory.is_dir():
        return ()
    records: list[DecisionRecord] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("ADR-*.md")):
        record = parse_decision(path)
        if record.decision_id in seen:
            raise DecisionError(f"duplicate ID: {record.decision_id}")
        seen.add(record.decision_id)
        records.append(record)
    decision_set = tuple(records)
    errors = list(validate_decision_set(root, decision_set))
    ids = {record.decision_id: record for record in decision_set}
    accepted_pairs: set[tuple[str, str]] = set()
    for record in records:
        if record.status != "accepted":
            continue
        for other in record.supersedes:
            peer = ids.get(other)
            if peer and peer.status == "accepted" and record.decision_id in peer.supersedes:
                pair = tuple(sorted((record.decision_id, other)))
                accepted_pairs.add(pair)
    if accepted_pairs:
        errors.append(
            "two accepted ADRs that supersede each other: "
            + ", ".join(f"{left}/{right}" for left, right in sorted(accepted_pairs))
        )
    if errors:
        raise DecisionError("\n".join(errors))
    return decision_set


def render_decision_index(records: tuple[DecisionRecord, ...] | list[DecisionRecord]) -> str:
    accepted = [item for item in records if item.status == "accepted"]
    superseded = [item for item in records if item.status == "superseded"]
    proposed = [item for item in records if item.status == "proposed"]
    lines = [
        "# Decision Index",
        "",
        "Generated from `docs/project/decisions/`. Do not hand-edit the lists.",
        "ADRs record durable shared architecture and control-plane choices.",
        "They do not restate scientific decisions, technical acceptance, or",
        "portfolio allocation.",
        "",
        "## Accepted shared ADRs",
        "",
    ]
    if accepted:
        for item in accepted:
            lines.append(f"- `{item.decision_id}` {item.title} ({item.scope})")
    else:
        lines.append("- none")
    lines.extend(["", "## Superseded ADRs", ""])
    if superseded:
        for item in superseded:
            lines.append(f"- `{item.decision_id}` {item.title}")
    else:
        lines.append("- none")
    lines.extend(["", "## Proposed ADRs", ""])
    if proposed:
        for item in proposed:
            lines.append(f"- `{item.decision_id}` {item.title}")
    else:
        lines.append("- none")
    lines.extend(["", "## External canonical decision systems", ""])
    for title, path in EXTERNAL_SYSTEMS:
        lines.append(f"- {title}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def write_decision_index(root: Path) -> Path:
    records = collect_decisions(root)
    target = Path(root) / INDEX_PATH
    target.write_text(render_decision_index(records), encoding="utf-8", newline="\n")
    return target
