"""Public behavior tests for the narrow HMASD Git path-policy module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import hmasd_path_policy


def _policy(repo: Path, rules: list[dict[str, str]]) -> None:
    path = repo / "docs/project/git-path-policy-v1.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "default_classification": "shared-core",
                "rules": rules,
            }
        ),
        encoding="utf-8",
    )


def test_ordered_policy_and_windows_safe_posix_paths(tmp_path: Path) -> None:
    _policy(
        tmp_path,
        [
            {
                "type": "prefix",
                "path": "experiments/candidates",
                "classification": "direction-owned",
            },
            {
                "type": "exact",
                "path": "experiments/candidates/alpha/shared.py",
                "classification": "shared-core",
            },
        ],
    )

    facts = hmasd_path_policy.observe_path_classifications(
        tmp_path,
        ["experiments/candidates/alpha/shared.py", "scripts/shared.py"],
    )

    assert facts["ref"] == "docs/project/git-path-policy-v1.json"
    assert facts["classifications"] == [
        {
            "path": "experiments/candidates/alpha/shared.py",
            "classification": "direction-owned",
        },
        {"path": "scripts/shared.py", "classification": "shared-core"},
    ]
    assert len(facts["sha256"]) == 64
    for alias in (
        "../outside.py",
        "experiments\\candidates\\alpha.py",
        "C:/outside.py",
        "file.py:stream",
        "file.py.",
    ):
        with pytest.raises(hmasd_path_policy.PathPolicyError):
            hmasd_path_policy.normalize_repo_path(alias, label="test path")
