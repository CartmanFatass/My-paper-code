"""Parsers and validators for repository-owned assignment/result artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

from .incident_scope import ImpactEnvelope, IncidentLevel, validate_impact
from .requirements_registry import Requirement, require_active


KNOWN_ROLES = {
    "hmasd-implementer", "hmasd-implementer-terra", "hmasd-experiment-operator",
    "hmasd-workflow-recovery-manager", "hmasd-code-project-manager", "hmasd-independent-research-explorer",
}
KNOWN_PROFILES = {
    "R0_NAVIGATION_AND_MECHANICAL", "R1_ROUTINE_ENGINEERING", "R2_EXPERIMENT_EXECUTION",
    "R3_PROTECTED_SCIENTIFIC_SEMANTICS", "R4_CONTROL_PLANE_AND_AUTHORITY",
}
KNOWN_EVIDENCE = {"A", "B", "C"}
KNOWN_ASSIGNMENT_MODES = {"DISCOVERY", "IMPLEMENTATION", "REVIEW", "OPERATION"}
KNOWN_RESULT_KINDS = {"COMPLETED", "PARTIAL", "LOCAL_BOUNDARY", "INCIDENT", "SURFACE_MAP"}


@dataclass(frozen=True)
class AssignmentArtifact:
    assignment_id: str
    assignment_mode: str
    semantic_owner: str
    executor_role: str
    return_to: str
    strictness_profile: str
    evidence_class: str
    result_bearing: bool
    runtime_profile: str | None
    requirement_ids: tuple[str, ...]
    nonrequirement_ids: tuple[str, ...]
    recovery_owner: str
    result_path: str
    project_map_anchor: str
    architecture_role: str
    affected_files: tuple[str, ...]
    create_files: tuple[str, ...]
    affected_symbols: tuple[str, ...]
    search_roots: tuple[str, ...]
    direct_consumers: tuple[str, ...]
    upstream_inputs: tuple[str, ...]
    state_owner: str
    non_target_surfaces: tuple[str, ...]
    outcome: str = ""
    source_path: str = ""


@dataclass(frozen=True)
class ResultArtifact:
    assignment_id: str
    result_kind: str
    author_role: str
    owner_return: str
    project_map_anchor: str
    files_observed: tuple[str, ...]
    files_changed: tuple[str, ...]
    symbols_changed: tuple[str, ...]
    direct_consumer_checked: str
    impact: ImpactEnvelope | None
    source_path: str = ""


def _tuple(raw: object, field: str, allow_empty: bool = True) -> tuple[str, ...]:
    if raw is None:
        return () if allow_empty else (_ for _ in ()).throw(ValueError(f"missing {field}"))
    if not isinstance(raw, list) or not all(isinstance(item, str) and item.strip() for item in raw):
        raise ValueError(f"{field} must be a string array")
    return tuple(item.strip() for item in raw)


def _fenced(text: str, label: str) -> dict[str, object]:
    pattern = rf"```toml\s+hmasd-{re.escape(label)}\s*\r?\n(.*?)\r?\n```"
    match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError(f"missing fenced toml hmasd-{label} block")
    parsed = tomllib.loads(match.group(1))
    if not isinstance(parsed, dict):
        raise ValueError(f"hmasd-{label} metadata must be a table")
    return parsed


def _required_str(raw: Mapping[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or empty {key}")
    return value.strip()


def parse_assignment(path: Path) -> AssignmentArtifact:
    text = path.read_text(encoding="utf-8")
    raw = _fenced(text, "assignment")
    return AssignmentArtifact(
        assignment_id=_required_str(raw, "assignment_id"),
        assignment_mode=_required_str(raw, "assignment_mode"),
        semantic_owner=_required_str(raw, "semantic_owner"),
        executor_role=_required_str(raw, "executor_role"),
        return_to=_required_str(raw, "return_to"),
        strictness_profile=_required_str(raw, "strictness_profile"),
        evidence_class=_required_str(raw, "evidence_class"),
        result_bearing=bool(raw.get("result_bearing", False)),
        runtime_profile=str(raw.get("runtime_profile") or "") or None,
        requirement_ids=_tuple(raw.get("requirement_ids"), "requirement_ids"),
        nonrequirement_ids=_tuple(raw.get("nonrequirement_ids"), "nonrequirement_ids"),
        recovery_owner=_required_str(raw, "recovery_owner"),
        result_path=_required_str(raw, "result_path"),
        project_map_anchor=_required_str(raw, "project_map_anchor"),
        architecture_role=_required_str(raw, "architecture_role"),
        affected_files=_tuple(raw.get("affected_files"), "affected_files"),
        create_files=_tuple(raw.get("create_files"), "create_files"),
        affected_symbols=_tuple(raw.get("affected_symbols"), "affected_symbols"),
        search_roots=_tuple(raw.get("search_roots"), "search_roots"),
        direct_consumers=_tuple(raw.get("direct_consumers"), "direct_consumers"),
        upstream_inputs=_tuple(raw.get("upstream_inputs"), "upstream_inputs"),
        state_owner=_required_str(raw, "state_owner"),
        non_target_surfaces=_tuple(raw.get("non_target_surfaces"), "non_target_surfaces", allow_empty=False),
        outcome=_extract_section(text, "Outcome"),
        source_path=str(path),
    )


def _extract_section(text: str, title: str) -> str:
    match = re.search(rf"^##\s+{re.escape(title)}\s*$([\s\S]*?)(?=^##\s+|\Z)", text, flags=re.MULTILINE | re.IGNORECASE)
    return (match.group(1).strip() if match else "")


def _parse_impact(raw: Mapping[str, object]) -> ImpactEnvelope:
    return ImpactEnvelope(
        level=IncidentLevel(_required_str(raw, "incident_level")),
        observed_object_kind=_required_str(raw, "observed_object_kind"),
        observed_object_id=_required_str(raw, "observed_object_id"),
        affected_actions=_tuple(raw.get("affected_actions"), "affected_actions", allow_empty=False),
        unaffected_actions=_tuple(raw.get("unaffected_actions"), "unaffected_actions"),
        does_not_imply=_tuple(raw.get("does_not_imply"), "does_not_imply", allow_empty=False),
        recovery_owner=_required_str(raw, "recovery_owner"),
        escalate_to=_required_str(raw, "escalate_to"),
        escalate_when=_tuple(raw.get("escalate_when"), "escalate_when"),
        user_question=str(raw.get("user_question") or "") or None,
        technical=bool(raw.get("technical", False)),
    )


def parse_result(path: Path) -> ResultArtifact:
    text = path.read_text(encoding="utf-8")
    raw = _fenced(text, "result")
    impact = None
    try:
        impact = _parse_impact(_fenced(text, "impact"))
    except ValueError as exc:
        if "missing fenced" not in str(exc):
            raise
    return ResultArtifact(
        assignment_id=_required_str(raw, "assignment_id"),
        result_kind=_required_str(raw, "result_kind"),
        author_role=_required_str(raw, "author_role"),
        owner_return=_required_str(raw, "owner_return"),
        project_map_anchor=_required_str(raw, "project_map_anchor"),
        files_observed=_tuple(raw.get("files_observed"), "files_observed"),
        files_changed=_tuple(raw.get("files_changed"), "files_changed"),
        symbols_changed=_tuple(raw.get("symbols_changed"), "symbols_changed"),
        direct_consumer_checked=str(raw.get("direct_consumer_checked") or ""),
        impact=impact,
        source_path=str(path),
    )


def _repo_path(value: str) -> Path:
    return Path(value.replace("\\", "/"))


def _has_parent(value: str) -> bool:
    path = _repo_path(value)
    return path.is_absolute() or ".." in path.parts


def _root_for_assignment(assignment: AssignmentArtifact) -> Path:
    start = Path(assignment.source_path).resolve() if assignment.source_path else Path.cwd().resolve()
    if start.is_file():
        start = start.parent
    for candidate in (start, *start.parents):
        if (candidate / "docs/project/PROJECT_MAP.md").exists():
            return candidate
    return Path.cwd().resolve()


def _map_headings(root: Path | None = None) -> set[str]:
    map_path = (root or Path.cwd()) / "docs/project/PROJECT_MAP.md"
    if not map_path.exists():
        return set()
    return {match.group(1).strip() for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", map_path.read_text(encoding="utf-8"), re.MULTILINE)}


def validate_assignment(assignment: AssignmentArtifact, registry: Mapping[str, Requirement]) -> list[str]:
    errors: list[str] = []
    root = _root_for_assignment(assignment)
    if not assignment.assignment_id.startswith("asg_"):
        errors.append("assignment_id must start with asg_")
    if assignment.assignment_mode not in KNOWN_ASSIGNMENT_MODES:
        errors.append(f"unknown assignment_mode: {assignment.assignment_mode}")
    if assignment.executor_role not in KNOWN_ROLES:
        errors.append(f"unknown executor_role: {assignment.executor_role}")
    if assignment.strictness_profile not in KNOWN_PROFILES:
        errors.append(f"unknown strictness_profile: {assignment.strictness_profile}")
    if assignment.evidence_class not in KNOWN_EVIDENCE:
        errors.append(f"unknown evidence_class: {assignment.evidence_class}")
    if assignment.project_map_anchor not in _map_headings(root):
        errors.append("project_map_anchor does not match an exact PROJECT_MAP heading")
    if not assignment.state_owner or not assignment.architecture_role or not assignment.non_target_surfaces:
        errors.append("architecture role, state owner and non-target surfaces are required")
    if assignment.assignment_mode == "DISCOVERY":
        if assignment.affected_files or assignment.create_files:
            errors.append("DISCOVERY assignments cannot name writable files")
        if not assignment.search_roots:
            errors.append("DISCOVERY assignment requires bounded search_roots")
    elif not assignment.affected_files and not assignment.create_files:
        errors.append("implementation/review/operation assignment requires exact files")
    if not assignment.direct_consumers:
        errors.append("direct_consumers must not be empty")
    if not assignment.outcome or not any(token in assignment.outcome.lower() for token in ("consumer", "receives", "creates", "returns", "writes", "produces", "behavior")):
        errors.append("outcome must name an observable behavior and direct consumer")
    if any(word in assignment.outcome.lower() for word in ("pipeline", "backend", "orchestrator", "core", "manager", "runtime", "flow")) and not assignment.affected_files and not assignment.search_roots:
        errors.append("abstract labels without repository grounding are not scope")
    try:
        require_active(registry, assignment.requirement_ids + assignment.nonrequirement_ids)
    except (KeyError, ValueError) as exc:
        errors.append(str(exc))
    if not assignment.result_path or _has_parent(assignment.result_path):
        errors.append("result_path must be repository-relative")
    for name, values in (("affected_files", assignment.affected_files), ("create_files", assignment.create_files), ("direct_consumers", assignment.direct_consumers), ("upstream_inputs", assignment.upstream_inputs)):
        for value in values:
            if _has_parent(value):
                errors.append(f"{name} contains non-repository path: {value}")
            if name != "create_files" and not (root / _repo_path(value)).exists():
                errors.append(f"{name} path does not exist: {value}")
    if assignment.result_bearing and assignment.strictness_profile == "R2_EXPERIMENT_EXECUTION" and not assignment.runtime_profile:
        errors.append("result-bearing R2 assignment requires runtime_profile")
    return errors


def validate_result(result: ResultArtifact, assignment: AssignmentArtifact) -> list[str]:
    errors: list[str] = []
    root = _root_for_assignment(assignment)
    if result.assignment_id != assignment.assignment_id:
        errors.append("assignment_id mismatch")
    if result.result_kind not in KNOWN_RESULT_KINDS:
        errors.append(f"unknown result_kind: {result.result_kind}")
    if result.author_role != assignment.executor_role:
        errors.append("author_role does not match assignment executor_role")
    if result.owner_return != assignment.return_to:
        errors.append("owner_return does not match assignment return_to")
    if result.project_map_anchor != assignment.project_map_anchor:
        errors.append("project_map_anchor mismatch")
    if assignment.assignment_mode == "DISCOVERY" and result.result_kind != "SURFACE_MAP":
        errors.append("DISCOVERY assignment requires SURFACE_MAP result")
    if result.direct_consumer_checked and not (root / _repo_path(result.direct_consumer_checked)).exists():
        errors.append("direct_consumer_checked does not exist")
    if result.result_kind in {"INCIDENT", "LOCAL_BOUNDARY", "PARTIAL"}:
        if result.impact is None:
            errors.append("boundary/incident result requires impact envelope")
        else:
            errors.extend(validate_impact(result.impact))
    if result.impact is not None and result.result_kind == "COMPLETED":
        errors.append("completed result should not carry an impact envelope")
    for name, values in (("files_observed", result.files_observed), ("files_changed", result.files_changed)):
        for value in values:
            if _has_parent(value):
                errors.append(f"{name} contains non-repository path: {value}")
    return errors
