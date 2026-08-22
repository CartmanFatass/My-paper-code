"""Machine-readable project requirements and deterministic human projection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore


KNOWN_KINDS = {"USER_REQUIREMENT", "PROJECT_INVARIANT", "DEFAULT", "NONREQUIREMENT"}
KNOWN_STATUSES = {"ACTIVE", "SUPERSEDED"}
REQUIRED_FIELDS = (
    "id", "kind", "status", "authority", "owner", "scope", "summary",
    "source_ref", "enforced_at", "does_not_imply", "deviation_policy",
)


@dataclass(frozen=True)
class Requirement:
    id: str
    kind: str
    status: str
    authority: str
    owner: str
    scope: tuple[str, ...]
    summary: str
    source_ref: str
    enforced_at: tuple[str, ...]
    does_not_imply: tuple[str, ...]
    deviation_policy: str
    supersedes: str | None = None


def _tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{field} must be a non-empty string array")
    return tuple(item.strip() for item in value)


def _from_raw(raw: Mapping[str, object]) -> Requirement:
    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    if missing:
        raise ValueError(f"missing requirement fields: {', '.join(missing)}")
    return Requirement(
        id=str(raw["id"]), kind=str(raw["kind"]), status=str(raw["status"]),
        authority=str(raw["authority"]), owner=str(raw["owner"]),
        scope=_tuple(raw["scope"], "scope"), summary=str(raw["summary"]),
        source_ref=str(raw["source_ref"]), enforced_at=_tuple(raw["enforced_at"], "enforced_at"),
        does_not_imply=_tuple(raw["does_not_imply"], "does_not_imply"),
        deviation_policy=str(raw["deviation_policy"]),
        supersedes=str(raw["supersedes"]) if raw.get("supersedes") else None,
    )


def load_requirements(path: Path) -> dict[str, Requirement]:
    with path.open("rb") as handle:
        document = tomllib.load(handle)
    rows = document.get("requirements")
    if not isinstance(rows, list):
        raise ValueError("requirements must be an array of tables")
    result: dict[str, Requirement] = {}
    duplicate: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each requirement must be a table")
        item = _from_raw(row)
        if item.id in result:
            duplicate.append(item.id)
        result[item.id] = item
    if duplicate:
        raise ValueError("duplicate requirement id: " + ", ".join(sorted(set(duplicate))))
    errors = validate_registry(result)
    if errors:
        raise ValueError("invalid requirement registry: " + "; ".join(errors))
    return result


def validate_registry(requirements: Mapping[str, Requirement]) -> list[str]:
    errors: list[str] = []
    for key, item in requirements.items():
        if key != item.id:
            errors.append(f"key/id mismatch: {key}")
        if item.kind not in KNOWN_KINDS:
            errors.append(f"{item.id}: unknown kind {item.kind}")
        if item.status not in KNOWN_STATUSES:
            errors.append(f"{item.id}: unknown status {item.status}")
        if not item.does_not_imply:
            errors.append(f"{item.id}: missing does_not_imply")
        if item.authority == "P0_USER" and not item.source_ref.startswith("user:"):
            errors.append(f"{item.id}: P0 source_ref must begin with user:")
        if item.kind == "NONREQUIREMENT" and item.status != "ACTIVE":
            errors.append(f"{item.id}: NONREQUIREMENT must remain ACTIVE")
        if item.supersedes is not None:
            if item.supersedes == item.id:
                errors.append(f"{item.id}: cannot supersede itself")
            if item.supersedes not in requirements:
                errors.append(f"{item.id}: supersedes unknown id {item.supersedes}")
            elif item.status != "ACTIVE":
                errors.append(f"{item.id}: superseding entry must be ACTIVE")
        if item.status == "ACTIVE" and item.kind != "NONREQUIREMENT" and not item.summary.strip():
            errors.append(f"{item.id}: empty summary")
    active = [item for item in requirements.values() if item.status == "ACTIVE"]
    for left_index, left in enumerate(active):
        for right in active[left_index + 1 :]:
            if left.scope and left.scope == right.scope and left.kind == right.kind and left.summary != right.summary:
                errors.append(f"conflicting active requirements: {left.id} and {right.id}")
    return errors


def require_active(requirements: Mapping[str, Requirement], ids: Iterable[str]) -> tuple[Requirement, ...]:
    result: list[Requirement] = []
    for identifier in ids:
        item = requirements.get(identifier)
        if item is None:
            raise KeyError(f"unknown requirement id: {identifier}")
        if item.status != "ACTIVE":
            raise ValueError(f"requirement is not active: {identifier}")
        result.append(item)
    return tuple(result)


def render_requirements_markdown(requirements: Mapping[str, Requirement]) -> str:
    groups = (
        ("ACTIVE USER REQUIREMENTS", lambda r: r.status == "ACTIVE" and r.kind == "USER_REQUIREMENT"),
        ("ACTIVE PROJECT INVARIANTS", lambda r: r.status == "ACTIVE" and r.kind == "PROJECT_INVARIANT"),
        ("ACTIVE DEFAULTS", lambda r: r.status == "ACTIVE" and r.kind == "DEFAULT"),
        ("ACTIVE NONREQUIREMENTS", lambda r: r.status == "ACTIVE" and r.kind == "NONREQUIREMENT"),
        ("SUPERSEDED", lambda r: r.status == "SUPERSEDED"),
    )
    lines = ["# Project Requirements", "", "Generated from `PROJECT_REQUIREMENTS.toml`. Do not edit manually.", ""]
    for title, predicate in groups:
        lines.extend([f"## {title}", ""])
        selected = sorted((item for item in requirements.values() if predicate(item)), key=lambda item: item.id)
        if not selected:
            lines.extend(["_(none)_", ""])
            continue
        for item in selected:
            lines.extend([
                f"### `{item.id}`", "", item.summary, "",
                f"- Authority: `{item.authority}`; owner: `{item.owner}`",
                f"- Scope: `{', '.join(item.scope)}`",
                f"- Source: `{item.source_ref}`; enforced at: `{', '.join(item.enforced_at)}`",
                f"- Does not imply: `{', '.join(item.does_not_imply)}`",
                "",
            ])
    return "\n".join(lines)
