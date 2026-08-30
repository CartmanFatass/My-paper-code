#!/usr/bin/env python3
"""Fail-closed, offline provenance gate for the optional P1 research tools."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION = 1
TOOL_NAME = "research_provenance_gate"
MANIFEST_PATH = "docs/research-tooling/provenance.yml"
NOTICE_PATH = "docs/research-tooling/NOTICE"
REQUIREMENTS_SOURCE = "requirements_research_tools.in"
REQUIREMENTS_LOCK = "requirements_research_tools.txt"

K_DENSE_REPOSITORY = "https://github.com/K-Dense-AI/scientific-agent-skills"
K_DENSE_COMMIT = "f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f"
K_DENSE_LICENSE_URL = (
    f"{K_DENSE_REPOSITORY}/blob/{K_DENSE_COMMIT}/LICENSE"
)

SKILL_ROOTS = (
    ".omp/skills/hmasd-paper-lookup",
    ".omp/skills/hmasd-hypothesis-mechanisms",
    ".omp/skills/hmasd-experimental-design-tools",
    ".omp/skills/hmasd-scientific-writing-validation",
    ".omp/skills/hmasd-symbolic-counterexample-tools",
    ".omp/skills/hmasd-scientific-compute-contracts",
)
TOOL_ROOTS = (
    "tools/research/paper_lookup",
    "tools/research/hypothesis_mechanisms",
    "tools/research/experimental_design",
    "tools/research/scientific_writing",
    "tools/research/symbolic",
    "tools/research/scientific_compute",
)
MANAGED_SKILLS = frozenset(PurePosixPath(path).name for path in SKILL_ROOTS)
AGENT_PROFILE_ROOT = ".omp/agents"
EXCLUSIONS = (
    ("**/__pycache__/**", "Generated Python bytecode is not a shipped source adapter."),
    ("**/*.pyc", "Generated Python bytecode is not a shipped source adapter."),
    (
        "tests/research_tools/**",
        "Focused verification fixtures are not shipped adapter implementations.",
    ),
)

REQUIRED_DEPENDENCIES: dict[str, tuple[str, str, str, bool]] = {
    "attrs": ("attrs", "26.1.0", "MIT", False),
    "exceptiongroup": ("exceptiongroup", "1.3.1", "MIT", False),
    "hypothesis": ("Hypothesis", "6.131.9", "MPL-2.0", True),
    "mpmath": ("mpmath", "1.3.0", "BSD-3-Clause", False),
    "numpy": ("NumPy", "1.26.3", "BSD-3-Clause", True),
    "pandas": ("Pandas", "2.2.3", "BSD-3-Clause", True),
    "pydoe3": ("pyDOE3", "1.0.4", "BSD-3-Clause", True),
    "python-dateutil": (
        "python-dateutil",
        "2.9.0.post0",
        "Apache-2.0 OR BSD-3-Clause",
        False,
    ),
    "pytz": ("pytz", "2026.3.post1", "MIT", False),
    "scipy": ("SciPy", "1.15.2", "BSD-3-Clause", True),
    "six": ("six", "1.17.0", "MIT", False),
    "sortedcontainers": ("sortedcontainers", "2.4.0", "Apache-2.0", False),
    "sympy": ("SymPy", "1.13.3", "BSD-3-Clause", True),
    "typing-extensions": ("typing-extensions", "4.16.0", "PSF-2.0", False),
    "tzdata": ("tzdata", "2026.3", "Apache-2.0", False),
    "z3-solver": ("z3-solver", "4.13.4.0", "MIT", True),
}
DIRECT_DEPENDENCIES = {
    name for name, (_, _, _, direct) in REQUIRED_DEPENDENCIES.items() if direct
}

TOP_LEVEL_FIELDS = {
    "activation",
    "artifacts",
    "dependencies",
    "managed_roots",
    "manifest_type",
    "review",
    "schema_version",
    "unresolved_facts",
    "upstream",
}
ACTIVATION_FIELDS = {"autoload", "default_network", "managers", "mode", "secrets"}
MANAGED_FIELDS = {"exclusions", "skill_roots", "tool_roots"}
REVIEW_FIELDS = {"last_reviewed", "maintainer_release_risk"}
UPSTREAM_FIELDS = {
    "authored_date",
    "commit",
    "committed_date",
    "confirmed_paths",
    "inspection_limitations",
    "license",
    "license_url",
    "project_python",
    "project_version",
    "repository",
    "selected_compatibility",
    "signature_status",
}
ARTIFACT_FIELDS = {
    "dependencies",
    "kind",
    "license",
    "license_evidence",
    "modification_notice",
    "origin",
    "path",
    "sha256",
    "skill",
    "source_ref",
}
SOURCE_REF_FIELDS = {"commit", "paths", "repository"}
DEPENDENCY_FIELDS = {
    "direct",
    "license",
    "license_evidence_url",
    "name",
    "normalized_name",
    "notice",
    "required_by",
    "source_url",
    "version",
}
UNRESOLVED_FIELDS = {"fact", "impact", "resolution"}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
LOCK_HASH_RE = re.compile(r"^--hash=sha256:([0-9a-f]{64})$")
REQUIREMENT_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s]+)$")
INPUT_REQUIREMENT_RE = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:==([^\s]+))?$"
)

FULL_K_DENSE_MIT_NOTICE = """MIT License

Copyright (c) 2025 K-Dense Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the \"Software\"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "detail": self.detail, "path": self.path}


class DuplicateKeyError(ValueError):
    pass


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object key: {key}")
        result[key] = value
    return result


def _normalized_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _is_canonical_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and str(path) == value
        and all(part not in {"", ".", ".."} and ":" not in part for part in path.parts)
    )


def _add(issues: list[Issue], code: str, path: str, detail: str) -> None:
    issues.append(Issue(code=code, path=path, detail=detail))


def _expect_fields(
    value: object,
    expected: set[str],
    locator: str,
    issues: list[Issue],
) -> Mapping[str, Any] | None:
    if not isinstance(value, dict):
        _add(issues, "structure_type", locator, "must be an object")
        return None
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        _add(
            issues,
            "structure_fields",
            locator,
            f"closed fields differ; missing={missing}; extra={extra}",
        )
    return value


def _expect_nonempty_text(
    value: object, locator: str, issues: list[Issue]
) -> str | None:
    if not isinstance(value, str) or not value.strip():
        _add(issues, "required_text", locator, "must be a non-empty string")
        return None
    return value


def _safe_existing_path(
    root: Path,
    relative: object,
    locator: str,
    issues: list[Issue],
    *,
    directory: bool = False,
) -> Path | None:
    if not _is_canonical_relative_path(relative):
        _add(issues, "unsafe_path", locator, "must be a canonical POSIX repository-relative path")
        return None
    assert isinstance(relative, str)
    current = root
    try:
        for part in PurePosixPath(relative).parts:
            current = current / part
            status = os.lstat(current)
            if stat.S_ISLNK(status.st_mode):
                _add(issues, "symlink_path", locator, f"symlink component is forbidden: {part}")
                return None
    except OSError:
        _add(issues, "missing_path", locator, "path does not exist")
        return None
    try:
        status = os.stat(current)
    except OSError:
        _add(issues, "unreadable_path", locator, "path cannot be inspected")
        return None
    if directory and not stat.S_ISDIR(status.st_mode):
        _add(issues, "path_type", locator, "must be a directory")
        return None
    if not directory and not stat.S_ISREG(status.st_mode):
        _add(issues, "path_type", locator, "must be a regular file")
        return None
    return current


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _load_manifest(root: Path, issues: list[Issue]) -> Mapping[str, Any] | None:
    path = _safe_existing_path(root, MANIFEST_PATH, MANIFEST_PATH, issues)
    if path is None:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        _add(issues, "manifest_read", MANIFEST_PATH, "manifest must be readable UTF-8")
        return None
    try:
        value = json.loads(text, object_pairs_hook=_object_without_duplicates)
    except (json.JSONDecodeError, DuplicateKeyError, ValueError):
        _add(issues, "manifest_json", MANIFEST_PATH, "manifest must be duplicate-free JSON")
        return None
    if text != _canonical_json(value):
        _add(
            issues,
            "manifest_not_canonical",
            MANIFEST_PATH,
            "manifest must use sorted, indented canonical JSON serialization",
        )
    return _expect_fields(value, TOP_LEVEL_FIELDS, "$", issues)


def _validate_activation(manifest: Mapping[str, Any], issues: list[Issue]) -> None:
    activation = _expect_fields(manifest.get("activation"), ACTIVATION_FIELDS, "$.activation", issues)
    if activation is None:
        return
    if activation.get("autoload") is not False:
        _add(issues, "autoload_forbidden", "$.activation.autoload", "must be false")
    if activation.get("managers") != []:
        _add(
            issues,
            "manager_autoload_forbidden",
            "$.activation.managers",
            "must be empty; P1 tools are invoked only on demand",
        )
    if activation.get("mode") != "explicit-on-demand":
        _add(issues, "activation_mode", "$.activation.mode", "must be explicit-on-demand")
    if activation.get("default_network") != "disabled":
        _add(issues, "network_default", "$.activation.default_network", "must be disabled")
    _expect_nonempty_text(activation.get("secrets"), "$.activation.secrets", issues)


def _validate_managed_roots(manifest: Mapping[str, Any], issues: list[Issue]) -> None:
    managed = _expect_fields(
        manifest.get("managed_roots"), MANAGED_FIELDS, "$.managed_roots", issues
    )
    if managed is None:
        return
    if managed.get("skill_roots") != list(SKILL_ROOTS):
        _add(issues, "managed_skill_roots", "$.managed_roots.skill_roots", "must equal the frozen P1 skill roots")
    if managed.get("tool_roots") != list(TOOL_ROOTS):
        _add(issues, "managed_tool_roots", "$.managed_roots.tool_roots", "must equal the frozen P1 tool roots")
    expected_exclusions = [
        {"pattern": pattern, "reason": reason} for pattern, reason in EXCLUSIONS
    ]
    if managed.get("exclusions") != expected_exclusions:
        _add(issues, "managed_exclusions", "$.managed_roots.exclusions", "must equal the narrow frozen exclusions")


def _validate_review(manifest: Mapping[str, Any], issues: list[Issue]) -> None:
    review = _expect_fields(manifest.get("review"), REVIEW_FIELDS, "$.review", issues)
    if review is None:
        return
    if review.get("last_reviewed") != "2026-08-30":
        _add(issues, "review_date", "$.review.last_reviewed", "must be the approved review date")
    _expect_nonempty_text(review.get("maintainer_release_risk"), "$.review.maintainer_release_risk", issues)


def _validate_upstream(manifest: Mapping[str, Any], issues: list[Issue]) -> set[str]:
    upstream = _expect_fields(manifest.get("upstream"), UPSTREAM_FIELDS, "$.upstream", issues)
    if upstream is None:
        return set()
    exact_values = {
        "repository": K_DENSE_REPOSITORY,
        "commit": K_DENSE_COMMIT,
        "authored_date": "2026-08-29",
        "committed_date": "2026-08-29",
        "signature_status": "unsigned",
        "project_version": "2.65.0",
        "project_python": ">=3.13",
        "license": "MIT",
        "license_url": K_DENSE_LICENSE_URL,
    }
    for field, expected in exact_values.items():
        if upstream.get(field) != expected:
            _add(issues, "upstream_fact", f"$.upstream.{field}", f"must equal {expected!r}")
    for field in ("selected_compatibility", "inspection_limitations"):
        _expect_nonempty_text(upstream.get(field), f"$.upstream.{field}", issues)
    raw_paths = upstream.get("confirmed_paths")
    if not isinstance(raw_paths, list) or not raw_paths:
        _add(issues, "upstream_paths", "$.upstream.confirmed_paths", "must be a non-empty list")
        return set()
    paths: set[str] = set()
    for index, path in enumerate(raw_paths):
        locator = f"$.upstream.confirmed_paths[{index}]"
        if not _is_canonical_relative_path(path):
            _add(issues, "upstream_path", locator, "must be a canonical relative upstream path")
        elif path in paths:
            _add(issues, "upstream_path_duplicate", locator, "must be unique")
        else:
            paths.add(path)
    if raw_paths != sorted(paths):
        _add(issues, "upstream_path_order", "$.upstream.confirmed_paths", "must be sorted and unique")
    return paths


def _validate_dependencies(
    manifest: Mapping[str, Any], issues: list[Issue]
) -> tuple[dict[str, Mapping[str, Any]], int]:
    raw_dependencies = manifest.get("dependencies")
    if not isinstance(raw_dependencies, list):
        _add(issues, "dependencies_type", "$.dependencies", "must be a list")
        return {}, 0
    dependencies: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(raw_dependencies):
        locator = f"$.dependencies[{index}]"
        dependency = _expect_fields(raw, DEPENDENCY_FIELDS, locator, issues)
        if dependency is None:
            continue
        normalized = dependency.get("normalized_name")
        if not isinstance(normalized, str) or normalized != _normalized_name(normalized):
            _add(issues, "dependency_name", f"{locator}.normalized_name", "must be a normalized package name")
            continue
        if normalized in dependencies:
            _add(issues, "dependency_duplicate", f"{locator}.normalized_name", "must be unique")
            continue
        dependencies[normalized] = dependency
        expected = REQUIRED_DEPENDENCIES.get(normalized)
        if expected is None:
            _add(issues, "dependency_unexpected", f"{locator}.normalized_name", "is not in the frozen lock set")
            continue
        name, version, license_name, direct = expected
        expected_values: dict[str, object] = {
            "name": name,
            "version": version,
            "license": license_name,
            "direct": direct,
        }
        for field, wanted in expected_values.items():
            if dependency.get(field) != wanted:
                _add(issues, "dependency_fact", f"{locator}.{field}", f"must equal {wanted!r}")
        for field in ("source_url", "license_evidence_url"):
            value = _expect_nonempty_text(dependency.get(field), f"{locator}.{field}", issues)
            if value is not None and not value.startswith("https://"):
                _add(issues, "dependency_url", f"{locator}.{field}", "must be an HTTPS URL")
        _expect_nonempty_text(dependency.get("notice"), f"{locator}.notice", issues)
        required_by = dependency.get("required_by")
        if not isinstance(required_by, list) or not required_by:
            _add(issues, "dependency_linkage", f"{locator}.required_by", "must be a non-empty list")
        elif required_by != sorted(set(required_by)):
            _add(issues, "dependency_linkage_order", f"{locator}.required_by", "must be sorted and unique")
        else:
            for link_index, linked_path in enumerate(required_by):
                if not _is_canonical_relative_path(linked_path):
                    _add(issues, "dependency_linkage_path", f"{locator}.required_by[{link_index}]", "must be a canonical relative path")
    missing = sorted(set(REQUIRED_DEPENDENCIES) - set(dependencies))
    if missing:
        _add(issues, "dependency_missing", "$.dependencies", f"missing required packages: {missing}")
    if list(dependencies) != sorted(dependencies):
        _add(issues, "dependency_order", "$.dependencies", "must be ordered by normalized_name")
    return dependencies, len(raw_dependencies)


def _validate_artifacts(
    root: Path,
    manifest: Mapping[str, Any],
    dependencies: Mapping[str, Mapping[str, Any]],
    confirmed_upstream_paths: set[str],
    issues: list[Issue],
) -> tuple[dict[str, Mapping[str, Any]], int, int]:
    raw_artifacts = manifest.get("artifacts")
    if not isinstance(raw_artifacts, list):
        _add(issues, "artifacts_type", "$.artifacts", "must be a list")
        return {}, 0, 0
    artifacts: dict[str, Mapping[str, Any]] = {}
    adapted_count = 0
    local_count = 0
    valid_kinds = {"implementation", "notice", "requirements-lock", "requirements-source", "skill"}
    for index, raw in enumerate(raw_artifacts):
        locator = f"$.artifacts[{index}]"
        artifact = _expect_fields(raw, ARTIFACT_FIELDS, locator, issues)
        if artifact is None:
            continue
        relative = artifact.get("path")
        if not _is_canonical_relative_path(relative):
            _add(issues, "unsafe_path", f"{locator}.path", "must be a canonical POSIX repository-relative path")
            continue
        assert isinstance(relative, str)
        if relative == MANIFEST_PATH:
            _add(issues, "manifest_self_hash", f"{locator}.path", "the manifest must not hash itself")
        if relative in artifacts:
            _add(issues, "artifact_duplicate", f"{locator}.path", "must be unique")
            continue
        artifacts[relative] = artifact
        digest = artifact.get("sha256")
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
            _add(issues, "artifact_sha256", f"{locator}.sha256", "must be a lowercase full SHA-256")
        path = _safe_existing_path(root, relative, f"{locator}.path", issues)
        if path is not None and isinstance(digest, str) and SHA256_RE.fullmatch(digest):
            if _sha256(path) != digest:
                _add(issues, "artifact_hash_mismatch", relative, "local bytes do not match the manifest SHA-256")
        kind = artifact.get("kind")
        if kind not in valid_kinds:
            _add(issues, "artifact_kind", f"{locator}.kind", "is not an allowed artifact kind")
        skill = artifact.get("skill")
        if skill is not None and (not isinstance(skill, str) or skill not in {PurePosixPath(root).name for root in SKILL_ROOTS}):
            _add(issues, "artifact_skill", f"{locator}.skill", "must name a managed skill or be null")
        license_name = _expect_nonempty_text(artifact.get("license"), f"{locator}.license", issues)
        _expect_nonempty_text(artifact.get("license_evidence"), f"{locator}.license_evidence", issues)
        notice = _expect_nonempty_text(artifact.get("modification_notice"), f"{locator}.modification_notice", issues)
        origin = artifact.get("origin")
        source_ref = artifact.get("source_ref")
        if origin == "adapted":
            adapted_count += 1
            if license_name != "MIT":
                _add(issues, "adapted_license", f"{locator}.license", "K-Dense adaptations must record MIT")
            if notice is not None and "not byte-identical" not in notice:
                _add(issues, "adaptation_notice", f"{locator}.modification_notice", "must explicitly deny unproved byte identity")
            source = _expect_fields(source_ref, SOURCE_REF_FIELDS, f"{locator}.source_ref", issues)
            if source is not None:
                if source.get("repository") != K_DENSE_REPOSITORY:
                    _add(issues, "adapted_repository", f"{locator}.source_ref.repository", "must equal the pinned K-Dense repository")
                commit = source.get("commit")
                if commit != K_DENSE_COMMIT or not isinstance(commit, str) or COMMIT_RE.fullmatch(commit) is None:
                    _add(issues, "adapted_commit_invalid", f"{locator}.source_ref.commit", "must be the full pinned 40-hex commit")
                source_paths = source.get("paths")
                if not isinstance(source_paths, list) or not source_paths:
                    _add(issues, "adapted_paths", f"{locator}.source_ref.paths", "must be a non-empty exact path list")
                elif source_paths != sorted(set(source_paths)):
                    _add(issues, "adapted_path_order", f"{locator}.source_ref.paths", "must be sorted and unique")
                else:
                    for path_index, source_path in enumerate(source_paths):
                        source_locator = f"{locator}.source_ref.paths[{path_index}]"
                        if not _is_canonical_relative_path(source_path):
                            _add(issues, "adapted_path", source_locator, "must be a canonical upstream path")
                        elif source_path not in confirmed_upstream_paths:
                            _add(issues, "adapted_path_unconfirmed", source_locator, "must appear in upstream.confirmed_paths")
        elif origin == "local-original":
            local_count += 1
            if source_ref is not None:
                _add(issues, "local_source_ref", f"{locator}.source_ref", "local-original artifacts must use null")
        else:
            _add(issues, "artifact_origin", f"{locator}.origin", "must be adapted or local-original")
        links = artifact.get("dependencies")
        if not isinstance(links, list) or links != sorted(set(links)):
            _add(issues, "artifact_dependencies", f"{locator}.dependencies", "must be a sorted unique list")
        else:
            for link_index, dependency in enumerate(links):
                if dependency not in dependencies:
                    _add(issues, "artifact_dependency_unknown", f"{locator}.dependencies[{link_index}]", "does not name a manifest dependency")
    if list(artifacts) != sorted(artifacts):
        _add(issues, "artifact_order", "$.artifacts", "must be ordered by path")
    expected_special = {
        NOTICE_PATH: "notice",
        REQUIREMENTS_SOURCE: "requirements-source",
        REQUIREMENTS_LOCK: "requirements-lock",
    }
    for path, kind in expected_special.items():
        artifact = artifacts.get(path)
        if artifact is None:
            _add(issues, "artifact_required", "$.artifacts", f"missing {path}")
        elif artifact.get("kind") != kind:
            _add(issues, "artifact_kind", path, f"must use kind {kind}")
    return artifacts, adapted_count, local_count


def _managed_files(root: Path, issues: list[Issue]) -> set[str]:
    files: set[str] = set()
    for relative_root in (*SKILL_ROOTS, *TOOL_ROOTS):
        root_path = _safe_existing_path(root, relative_root, relative_root, issues, directory=True)
        if root_path is None:
            continue
        for entry in sorted(root_path.rglob("*")):
            relative = entry.relative_to(root).as_posix()
            try:
                status = os.lstat(entry)
            except OSError:
                _add(issues, "managed_unreadable", relative, "managed path cannot be inspected")
                continue
            if stat.S_ISLNK(status.st_mode):
                _add(issues, "managed_symlink", relative, "symlinks are forbidden in managed roots")
                continue
            if stat.S_ISDIR(status.st_mode):
                continue
            if "__pycache__" in entry.relative_to(root_path).parts or entry.suffix == ".pyc":
                continue
            if not stat.S_ISREG(status.st_mode):
                _add(issues, "managed_path_type", relative, "managed entries must be regular files")
                continue
            files.add(relative)
    return files


def _validate_coverage(
    root: Path,
    artifacts: Mapping[str, Mapping[str, Any]],
    issues: list[Issue],
) -> int:
    managed = _managed_files(root, issues)
    covered = {
        path
        for path, artifact in artifacts.items()
        if artifact.get("kind") in {"skill", "implementation"}
    }
    missing = sorted(managed - covered)
    extra = sorted(covered - managed)
    if missing:
        _add(issues, "managed_file_uncovered", "$.artifacts", f"uncovered managed files: {missing}")
    if extra:
        _add(issues, "managed_file_outside_roots", "$.artifacts", f"managed artifacts outside roots: {extra}")
    expected_skills = {f"{root}/SKILL.md" for root in SKILL_ROOTS}
    for path in sorted(expected_skills):
        artifact = artifacts.get(path)
        if artifact is not None and artifact.get("kind") != "skill":
            _add(issues, "skill_kind", path, "managed SKILL.md must use kind skill")
    for path in sorted(managed - expected_skills):
        artifact = artifacts.get(path)
        if artifact is not None and artifact.get("kind") != "implementation":
            _add(issues, "implementation_kind", path, "managed tool files must use kind implementation")
    return len(managed)


def _validate_dependency_linkage(
    artifacts: Mapping[str, Mapping[str, Any]],
    dependencies: Mapping[str, Mapping[str, Any]],
    issues: list[Issue],
) -> None:
    calculated: dict[str, list[str]] = {name: [] for name in dependencies}
    for path, artifact in artifacts.items():
        links = artifact.get("dependencies")
        if isinstance(links, list):
            for dependency in links:
                if dependency in calculated:
                    calculated[dependency].append(path)
    for name, dependency in dependencies.items():
        expected = sorted(calculated[name])
        if dependency.get("required_by") != expected:
            _add(issues, "dependency_linkage_mismatch", f"$.dependencies[{name}].required_by", f"must equal artifact links: {expected}")


def _parse_lock(text: str, issues: list[Issue]) -> dict[str, tuple[str, list[str]]]:
    chunks: list[list[str]] = []
    current: list[str] = []
    for line_number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        token = stripped[:-1].rstrip() if stripped.endswith("\\") else stripped
        if raw[:1].isspace():
            if current and token.startswith("--hash="):
                current.append(token)
            elif token:
                _add(issues, "lock_syntax", f"{REQUIREMENTS_LOCK}:{line_number}", "unexpected continuation")
            continue
        if current:
            chunks.append(current)
        current = [token]
    if current:
        chunks.append(current)

    packages: dict[str, tuple[str, list[str]]] = {}
    for index, chunk in enumerate(chunks):
        match = REQUIREMENT_RE.fullmatch(chunk[0])
        if match is None:
            _add(issues, "lock_requirement", f"{REQUIREMENTS_LOCK}[{index}]", "must be an exact name==version pin")
            continue
        normalized = _normalized_name(match.group(1))
        hashes: list[str] = []
        for hash_token in chunk[1:]:
            hash_match = LOCK_HASH_RE.fullmatch(hash_token)
            if hash_match is None:
                _add(issues, "lock_hash_invalid", f"{REQUIREMENTS_LOCK}[{index}]", "every artifact hash must be a full lowercase SHA-256")
            else:
                hashes.append(hash_match.group(1))
        if not hashes:
            _add(issues, "lock_hash_missing", f"{REQUIREMENTS_LOCK}[{index}]", "each pin must have at least one SHA-256 artifact hash")
        if hashes != sorted(set(hashes)):
            _add(issues, "lock_hash_order", f"{REQUIREMENTS_LOCK}[{index}]", "artifact hashes must be sorted and unique")
        if normalized in packages:
            _add(issues, "lock_duplicate", f"{REQUIREMENTS_LOCK}[{index}]", "package pin must be unique")
        else:
            packages[normalized] = (match.group(2), hashes)
    return packages


def _validate_lock(root: Path, issues: list[Issue]) -> None:
    path = _safe_existing_path(root, REQUIREMENTS_LOCK, REQUIREMENTS_LOCK, issues)
    if path is None:
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        _add(issues, "lock_read", REQUIREMENTS_LOCK, "lock must be readable UTF-8")
        return
    packages = _parse_lock(text, issues)
    if set(packages) != set(REQUIRED_DEPENDENCIES):
        _add(
            issues,
            "lock_package_set",
            REQUIREMENTS_LOCK,
            f"locked={sorted(packages)}; required={sorted(REQUIRED_DEPENDENCIES)}",
        )
    for name, (_, expected_version, _, _) in REQUIRED_DEPENDENCIES.items():
        locked = packages.get(name)
        if locked is not None and locked[0] != expected_version:
            _add(issues, "lock_version_mismatch", name, f"locked {locked[0]!r}; required {expected_version!r}")


def _validate_requirements_source(root: Path, issues: list[Issue]) -> None:
    path = _safe_existing_path(root, REQUIREMENTS_SOURCE, REQUIREMENTS_SOURCE, issues)
    if path is None:
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        _add(issues, "requirements_read", REQUIREMENTS_SOURCE, "source requirements must be readable UTF-8")
        return
    declared: set[str] = set()
    constraints: list[str] = []
    for line_number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("-c "):
            constraints.append(stripped[3:].strip())
            continue
        match = INPUT_REQUIREMENT_RE.fullmatch(stripped)
        if match is None:
            _add(issues, "requirements_syntax", f"{REQUIREMENTS_SOURCE}:{line_number}", "must be a package name with an optional exact pin")
            continue
        normalized = _normalized_name(match.group(1))
        declared.add(normalized)
        specified_version = match.group(2)
        expected = REQUIRED_DEPENDENCIES.get(normalized)
        if expected is None or normalized not in DIRECT_DEPENDENCIES:
            _add(issues, "requirements_unexpected", f"{REQUIREMENTS_SOURCE}:{line_number}", "must name a frozen direct dependency")
        elif specified_version is not None and specified_version != expected[1]:
            _add(issues, "requirements_version", f"{REQUIREMENTS_SOURCE}:{line_number}", f"must pin {expected[1]}")
    if declared != DIRECT_DEPENDENCIES:
        _add(issues, "requirements_direct_set", REQUIREMENTS_SOURCE, f"declared={sorted(declared)}; required={sorted(DIRECT_DEPENDENCIES)}")
    if constraints != ["requirements_server.txt"]:
        _add(issues, "requirements_constraint", REQUIREMENTS_SOURCE, "must retain exactly -c requirements_server.txt")


def _validate_notice(root: Path, issues: list[Issue]) -> None:
    path = _safe_existing_path(root, NOTICE_PATH, NOTICE_PATH, issues)
    if path is None:
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        _add(issues, "notice_read", NOTICE_PATH, "NOTICE must be readable UTF-8")
        return
    if FULL_K_DENSE_MIT_NOTICE not in text:
        _add(issues, "notice_k_dense_mit", NOTICE_PATH, "must retain the full K-Dense MIT notice")
    if K_DENSE_COMMIT not in text:
        _add(issues, "notice_commit", NOTICE_PATH, "must identify the pinned K-Dense commit")
    if "No dependency source code\nis copied or vendored" not in text:
        _add(issues, "notice_nonvendoring", NOTICE_PATH, "must state that dependencies are not copied or vendored")
    for _, (display_name, version, license_name, _) in sorted(REQUIRED_DEPENDENCIES.items()):
        expected = f"{display_name} {version} — {license_name} — source: https://"
        if expected not in text:
            _add(issues, "notice_dependency", NOTICE_PATH, f"missing dependency notice prefix: {expected}")


def _validate_no_manager_autoload(root: Path, issues: list[Issue]) -> None:
    profile_root = _safe_existing_path(
        root, AGENT_PROFILE_ROOT, AGENT_PROFILE_ROOT, issues, directory=True
    )
    if profile_root is None:
        return
    for profile in sorted(profile_root.glob("*.md")):
        relative = profile.relative_to(root).as_posix()
        if profile.is_symlink():
            _add(issues, "agent_profile_symlink", relative, "agent profiles must not be symlinks")
            continue
        try:
            lines = profile.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            _add(issues, "agent_profile_read", relative, "agent profile must be readable UTF-8")
            continue
        if not lines or lines[0] != "---":
            _add(issues, "agent_profile_frontmatter", relative, "agent profile must start with frontmatter")
            continue
        try:
            frontmatter_end = lines.index("---", 1)
        except ValueError:
            _add(issues, "agent_profile_frontmatter", relative, "agent profile frontmatter is not closed")
            continue
        frontmatter = lines[1:frontmatter_end]
        autoloaded: list[str] = []
        collecting = False
        for line in frontmatter:
            if not collecting and line.startswith("autoloadSkills:"):
                collecting = True
                inline = line.partition(":")[2].strip()
                if inline and inline != "[]":
                    autoloaded.append("*")
                continue
            if collecting:
                if not line.strip():
                    continue
                if not line[:1].isspace():
                    break
                item = line.strip()
                if item.startswith("- "):
                    autoloaded.append(item[2:].strip().strip("'\""))
        forbidden = sorted(
            skill
            for skill in autoloaded
            if skill in MANAGED_SKILLS or skill in {"*", "all"} or "*" in skill
        )
        if forbidden:
            _add(
                issues,
                "manager_autoload_forbidden",
                relative,
                f"P1 research skills may not be profile autoloads: {forbidden}",
            )


def _validate_unresolved(manifest: Mapping[str, Any], issues: list[Issue]) -> int:
    raw = manifest.get("unresolved_facts")
    if not isinstance(raw, list):
        _add(issues, "unresolved_type", "$.unresolved_facts", "must be a list")
        return 0
    for index, item in enumerate(raw):
        locator = f"$.unresolved_facts[{index}]"
        fact = _expect_fields(item, UNRESOLVED_FIELDS, locator, issues)
        if fact is not None:
            for field in UNRESOLVED_FIELDS:
                _expect_nonempty_text(fact.get(field), f"{locator}.{field}", issues)
    return len(raw)


def validate_repository(root: Path | str) -> dict[str, Any]:
    """Validate one repository tree and return a deterministic JSON-ready report."""
    root_path = Path(root)
    issues: list[Issue] = []
    if root_path.is_symlink() or not root_path.is_dir():
        _add(issues, "root_invalid", "$root", "root must be an existing non-symlink directory")
        return _report(issues, 0, 0, 0, 0, 0, 0)
    root_path = root_path.resolve()
    manifest = _load_manifest(root_path, issues)
    if manifest is None:
        return _report(issues, 0, 0, 0, 0, 0, 0)
    if manifest.get("schema_version") != SCHEMA_VERSION:
        _add(issues, "schema_version", "$.schema_version", f"must equal {SCHEMA_VERSION}")
    if manifest.get("manifest_type") != "hmasd-p1-research-tooling-provenance":
        _add(issues, "manifest_type", "$.manifest_type", "is not the P1 provenance manifest")
    _validate_activation(manifest, issues)
    _validate_managed_roots(manifest, issues)
    _validate_review(manifest, issues)
    confirmed = _validate_upstream(manifest, issues)
    dependencies, dependency_count = _validate_dependencies(manifest, issues)
    artifacts, adapted_count, local_count = _validate_artifacts(
        root_path, manifest, dependencies, confirmed, issues
    )
    managed_count = _validate_coverage(root_path, artifacts, issues)
    _validate_dependency_linkage(artifacts, dependencies, issues)
    _validate_requirements_source(root_path, issues)
    _validate_lock(root_path, issues)
    _validate_notice(root_path, issues)
    _validate_no_manager_autoload(root_path, issues)
    unresolved_count = _validate_unresolved(manifest, issues)
    return _report(
        issues,
        len(artifacts),
        adapted_count,
        local_count,
        dependency_count,
        managed_count,
        unresolved_count,
    )


def _report(
    issues: Iterable[Issue],
    artifact_count: int,
    adapted_count: int,
    local_count: int,
    dependency_count: int,
    managed_count: int,
    unresolved_count: int,
) -> dict[str, Any]:
    ordered = sorted(issues, key=lambda item: (item.code, item.path, item.detail))
    return {
        "errors": [issue.as_dict() for issue in ordered],
        "ok": not ordered,
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "adapted_artifact_count": adapted_count,
            "artifact_count": artifact_count,
            "dependency_count": dependency_count,
            "local_original_artifact_count": local_count,
            "managed_file_count": managed_count,
            "unresolved_fact_count": unresolved_count,
        },
        "tool": TOOL_NAME,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the offline P1 provenance, license, and dependency gate."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repository root (defaults to the root containing this script)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = validate_repository(args.root)
    json.dump(report, sys.stdout, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
