#!/usr/bin/env python3
"""Validate HMASD repository paths and apply the ordered Git path policy."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence
import unicodedata

try:
    from scripts import hmasd_platform
except ImportError:
    import hmasd_platform


PATH_POLICY_REF = "docs/project/git-path-policy-v1.json"
_CLASSIFICATIONS = {"direction-owned", "shared-core"}


class PathPolicyError(ValueError):
    """The path or versioned policy is unsafe or invalid."""


def normalize_repo_path(value: Any, *, label: str = "path") -> str:
    """Return one canonical Windows-safe repository-relative POSIX path."""

    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        raise PathPolicyError(f"{label} must be a repository-relative POSIX path")
    if re.match(r"^[A-Za-z]:", value):
        raise PathPolicyError(f"{label} must not have an absolute drive prefix")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise PathPolicyError(f"{label} contains an alias component")
    if any(":" in part for part in parts):
        raise PathPolicyError(f"{label} contains a colon or Windows ADS component")
    if any(part.endswith((".", " ")) for part in parts):
        raise PathPolicyError(f"{label} contains a Windows-ambiguous trailing dot or space")
    if any(unicodedata.category(character) == "Cc" for character in value):
        raise PathPolicyError(f"{label} contains a control character")
    return "/".join(parts)


def _assert_no_alias(path: Path, *, label: str, require_file: bool) -> None:
    current = path
    while True:
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            info = None
        if info is not None and hmasd_platform.is_reparse_or_symlink(current, info):
            raise PathPolicyError(f"{label} traverses a symlink or reparse point: {current}")
        parent = current.parent
        if parent == current:
            break
        current = parent
    if require_file and not path.is_file():
        raise PathPolicyError(f"{label} is not an existing regular file")


def resolve_repo_path(
    repo: os.PathLike[str] | str,
    relative: str,
    *,
    label: str = "path",
    require_file: bool = False,
) -> Path:
    """Resolve a canonical relative path without permitting filesystem aliases."""

    repository = Path(repo).absolute()
    normalized = normalize_repo_path(relative, label=label)
    candidate = repository.joinpath(*normalized.split("/"))
    try:
        candidate.relative_to(repository)
    except ValueError as exc:
        raise PathPolicyError(f"{label} escaped repository") from exc
    _assert_no_alias(candidate, label=label, require_file=require_file)
    return candidate


def path_is_owned(path: str, owned_paths: Sequence[str]) -> bool:
    """Apply Session Envelope v2 exact-path / trailing-slash-prefix ownership."""

    normalized = normalize_repo_path(path, label="requested path").casefold()
    for index, raw in enumerate(owned_paths):
        if not isinstance(raw, str):
            raise PathPolicyError(f"owned_paths[{index}] must be a path")
        is_prefix = raw.endswith("/")
        root = normalize_repo_path(
            raw[:-1] if is_prefix else raw,
            label=f"owned_paths[{index}]",
        ).casefold()
        if normalized == root or (is_prefix and normalized.startswith(root + "/")):
            return True
    return False


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def load_path_policy(
    repo: os.PathLike[str] | str,
) -> tuple[dict[str, Any], str]:
    """Load and validate the repository's versioned ordered path policy."""

    policy_path = resolve_repo_path(
        repo,
        PATH_POLICY_REF,
        label="path policy",
        require_file=True,
    )
    try:
        value = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PathPolicyError(f"path policy is unreadable: {exc}") from exc
    if not isinstance(value, Mapping) or set(value) != {
        "schema_version",
        "default_classification",
        "rules",
    }:
        raise PathPolicyError("path policy has an invalid top-level contract")
    if value["schema_version"] != 1 or isinstance(value["schema_version"], bool):
        raise PathPolicyError("path policy schema_version must be 1")
    if value["default_classification"] not in _CLASSIFICATIONS:
        raise PathPolicyError("path policy default_classification is invalid")
    if not isinstance(value["rules"], list):
        raise PathPolicyError("path policy rules must be an array")
    rules: list[dict[str, str]] = []
    for index, raw in enumerate(value["rules"]):
        if not isinstance(raw, Mapping) or set(raw) != {
            "type",
            "path",
            "classification",
        }:
            raise PathPolicyError(f"path policy rule {index} has an invalid contract")
        if raw["type"] not in {"exact", "prefix"}:
            raise PathPolicyError(f"path policy rule {index} type is invalid")
        if raw["classification"] not in _CLASSIFICATIONS:
            raise PathPolicyError(
                f"path policy rule {index} classification is invalid"
            )
        rules.append(
            {
                "type": str(raw["type"]),
                "path": normalize_repo_path(
                    raw["path"], label=f"path policy rule {index} path"
                ),
                "classification": str(raw["classification"]),
            }
        )
    normalized: dict[str, Any] = {
        "schema_version": 1,
        "default_classification": value["default_classification"],
        "rules": rules,
    }
    return normalized, hashlib.sha256(_canonical_bytes(normalized)).hexdigest()


def classify_path(path: str, policy: Mapping[str, Any]) -> str:
    """Classify one path by the first matching ordered policy rule."""

    normalized = normalize_repo_path(path, label="classified path")
    for rule in policy["rules"]:
        rule_path = str(rule["path"])
        if rule["type"] == "exact" and normalized == rule_path:
            return str(rule["classification"])
        if rule["type"] == "prefix" and (
            normalized == rule_path or normalized.startswith(rule_path + "/")
        ):
            return str(rule["classification"])
    return str(policy["default_classification"])


def observe_path_classifications(
    repo: os.PathLike[str] | str, paths: Sequence[str]
) -> dict[str, Any]:
    """Return policy provenance and ordered classification facts."""

    policy, digest = load_path_policy(repo)
    return {
        "ref": PATH_POLICY_REF,
        "sha256": digest,
        "classifications": [
            {"path": path, "classification": classify_path(path, policy)}
            for path in paths
        ],
    }
