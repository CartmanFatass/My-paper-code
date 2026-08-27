"""Acceptance tests for the isolated HMASD science-tools environment.

These tests exercise the public, durable seams of the workstream: the Conda
specification, explicit lock, manifest provenance, and recorded verification.
They intentionally do not activate an environment or install adapter stacks.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_ROOT = REPO_ROOT / "environments" / "hmasd-science-tools"
ENVIRONMENT_YML = ENV_ROOT / "environment.yml"
LOCK_FILE = ENV_ROOT / "conda-win-64.lock.txt"
MANIFEST_FILE = ENV_ROOT / "manifest.json"
CONDA_EXE = Path(r"C:\ProgramData\anaconda3\Scripts\conda.exe")
EXISTING_ENV = Path(r"C:\Users\fires\.conda\envs\hmasd-amd-cpu")

REQUIRED_PACKAGES = {
    "sympy",
    "numpy",
    "scipy",
    "pandas",
    "networkx",
    "statsmodels",
    "matplotlib",
    "seaborn",
    "jsonschema",
    "psutil",
    "pytest",
}
ADAPTERS = {"stable-baselines3", "torch-geometric", "pufferlib"}


def _load_manifest() -> dict:
    return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))


def _environment_dependencies() -> set[str]:
    """Read dependency names without making PyYAML a test prerequisite."""

    dependencies: set[str] = set()
    in_dependencies = False
    for raw_line in ENVIRONMENT_YML.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "dependencies:":
            in_dependencies = True
            continue
        if in_dependencies and line and not raw_line.startswith(" "):
            break
        if in_dependencies and line.startswith("-"):
            token = line[1:].strip().split("=", 1)[0].split(">", 1)[0]
            if token:
                dependencies.add(token)
    return dependencies


def test_required_environment_artifacts_exist() -> None:
    assert ENVIRONMENT_YML.is_file()
    assert LOCK_FILE.is_file()
    assert MANIFEST_FILE.is_file()


def test_manifest_records_platform_conda_recreation_and_required_packages() -> None:
    manifest = _load_manifest()

    assert manifest["environment_name"] == "hmasd-science-tools"
    assert manifest["platform"] == "win-64"
    assert manifest["accelerator"] == "cpu"
    assert manifest["cpu_only"] is True
    assert manifest["conda"]["executable"].replace("/", "\\") == str(CONDA_EXE)
    assert manifest["conda"]["version"]
    assert manifest["python"]["version"].startswith("3.11.")
    assert manifest["recreate_command"]
    assert "conda-win-64.lock.txt" in manifest["recreate_command"]
    assert REQUIRED_PACKAGES <= set(manifest["packages"])


def test_environment_spec_contains_required_packages_but_no_optional_adapters() -> None:
    dependencies = _environment_dependencies()
    assert REQUIRED_PACKAGES <= dependencies
    assert not ADAPTERS & dependencies


def test_lock_digest_and_explicit_format_match_manifest() -> None:
    manifest = _load_manifest()
    lock_bytes = LOCK_FILE.read_bytes()
    digest = hashlib.sha256(lock_bytes).hexdigest()
    assert b"@EXPLICIT\r\n" in lock_bytes[:512] or b"@EXPLICIT\n" in lock_bytes[:512]
    assert manifest["lock_sha256"] == digest
    assert manifest["lock_file"] == "conda-win-64.lock.txt"


def test_compatibility_matrix_is_advisory_and_adapters_are_not_installed() -> None:
    manifest = _load_manifest()
    matrix = manifest["compatibility_matrix"]
    assert set(matrix) == ADAPTERS
    for adapter, record in matrix.items():
        assert record["status"] in {"optional", "not_installed"}
        assert record["installed"] is False
        assert record["reason"]
        assert adapter not in manifest["packages"]


def test_existing_environment_snapshot_is_proven_unchanged() -> None:
    manifest = _load_manifest()
    snapshot = manifest["existing_environment_snapshot"]
    assert snapshot["environment_prefix"].replace("/", "\\") == str(EXISTING_ENV)
    assert snapshot["before_sha256"]
    assert snapshot["after_sha256"]
    assert snapshot["before_sha256"] == snapshot["after_sha256"]
    assert snapshot["unchanged"] is True


def test_manifest_records_successful_fresh_prefix_recreation_and_smoke() -> None:
    manifest = _load_manifest()
    verification = manifest["verification"]
    assert verification["recreated_from_lock"] is True
    assert verification["fresh_prefix"]
    smoke = verification["smoke_test"]
    assert smoke["passed"] is True
    assert set(smoke["imports"]) >= REQUIRED_PACKAGES
    assert all(smoke["imports"][name]["version"] for name in REQUIRED_PACKAGES)


@pytest.mark.skipif(
    os.environ.get("HMASD_RUN_LIVE_SCIENCE_SMOKE") != "1",
    reason="set HMASD_RUN_LIVE_SCIENCE_SMOKE=1 for the optional live prefix check",
)
def test_live_prefix_smoke_uses_explicit_interpreter() -> None:
    """Optional integration check; it never activates or mutates an environment."""

    manifest = _load_manifest()
    interpreter = Path(manifest["verification"]["smoke_test"]["interpreter"])
    assert interpreter.is_file()
    command = [
        str(interpreter),
        "-c",
        "import sympy,numpy,scipy,pandas,networkx,statsmodels,matplotlib,seaborn,jsonschema,psutil,pytest; print('ok')",
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
