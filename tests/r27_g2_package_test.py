from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "scripts" / "package_r27_g2_runtime.ps1"
MANIFEST = ROOT / "scripts" / "r27_g2_runtime_package_manifest.txt"


def find_pwsh() -> str:
    candidates = [
        shutil.which("pwsh"),
        r"C:\Program Files\PowerShell\7\pwsh.exe",
        shutil.which("powershell"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    pytest.skip("PowerShell is required for the R27-G2 package test")


def write_fixture_file(source_root: Path, relative_path: str, content: str = "fixture\n") -> None:
    path = source_root / Path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_runtime_manifest_tracks_required_boundary():
    source = MANIFEST.read_text(encoding="utf-8")
    for directory in ("ha_ctse_process", "envs", "hmasd"):
        assert f"directory {directory}" in source
    for relative_path in (
        "AGENTS.md",
        "config_1.py",
        "logger.py",
        "requirements_server.txt",
        "routing_protocols.py",
        "docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md",
        "docs/external-review/R27_G2_design_review_20260712_Claude.md",
        "scripts/audit_r27_forced_trajectory_effect.py",
        "scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh",
        "memory/CURRENT_WORK.md",
        "memory/ExpRecord.md",
        "tests/r27_g2_cli_test.py",
    ):
        assert f"file {relative_path}" in source


def test_packager_builds_verified_clean_directory_and_zip(tmp_path):
    source_root = tmp_path / "source"
    output_root = tmp_path / "output"
    required_paths = (
        "AGENTS.md",
        "config_1.py",
        "logger.py",
        "requirements_server.txt",
        "routing_protocols.py",
        "ha_ctse_process/env_factory.py",
        "ha_ctse_process/r27_g2_analysis.py",
        "ha_ctse_process/r27_g2_collector.py",
        "ha_ctse_process/r27_g2_runtime.py",
        "envs/pettingzoo/scenario7_energy_aware.py",
        "hmasd/r_mappo_utils.py",
        "scripts/audit_r27_forced_trajectory_effect.py",
        "scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh",
        "scripts/package_r27_g2_runtime.ps1",
        "scripts/remote/hmasd_autodl_ssh_config",
        "scripts/remote/run_hmasd_r27_g2.ps1",
        "scripts/remote/watch_r27_g2_status.sh",
        "docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md",
        "docs/external-review/R27_G2_design_review_20260712_Claude.md",
        "docs/operations/R27_G2_REMOTE_AUTOMATION_20260712.md",
        "memory/CURRENT_WORK.md",
        "memory/ALGORITHM_PRINCIPLES.md",
        "memory/IMPLEMENTATION_PLAN.md",
        "memory/ExpRecord.md",
        "tests/r27_g2_cloud_runner_test.py",
        "tests/r27_g2_cli_test.py",
        "tests/r27_g2_collector_test.py",
        "tests/r27_g2_live_hook_test.py",
        "tests/r27_g2_package_test.py",
        "tests/r27_g2_runtime_test.py",
        "tests/r27_g2_analysis_test.py",
        "tests/r27_g2_remote_workflow_test.py",
    )
    for relative_path in required_paths:
        write_fixture_file(source_root, relative_path)

    fixture_manifest = """# minimal fixture using the production syntax
directory ha_ctse_process
directory envs
directory hmasd
directory scripts
directory memory
directory tests
file AGENTS.md
file config_1.py
file logger.py
file requirements_server.txt
file routing_protocols.py
file scripts/remote/hmasd_autodl_ssh_config
file scripts/remote/run_hmasd_r27_g2.ps1
file scripts/remote/watch_r27_g2_status.sh
file docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md
file docs/external-review/R27_G2_design_review_20260712_Claude.md
file docs/operations/R27_G2_REMOTE_AUTOMATION_20260712.md
file tests/r27_g2_remote_workflow_test.py
"""
    write_fixture_file(
        source_root,
        "scripts/r27_g2_runtime_package_manifest.txt",
        fixture_manifest,
    )

    write_fixture_file(source_root, "ha_ctse_process/__pycache__/cache.pyc")
    write_fixture_file(source_root, "ha_ctse_process/model.pt")
    write_fixture_file(source_root, "ha_ctse_process/test_fixture.py")
    write_fixture_file(source_root, "tests/.pytest_tmp/scratch.txt")
    write_fixture_file(source_root, "scripts/logs_old/runner_output.log")
    write_fixture_file(source_root, "memory/backup_20260706/stale.md")

    result = subprocess.run(
        [
            find_pwsh(),
            "-NoProfile",
            "-File",
            str(PACKAGER),
            "-SourceRoot",
            str(source_root),
            "-OutputRoot",
            str(output_root),
            "-BundleName",
            "r27_g2_runtime_fixture",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    payload = json.loads(result.stdout)
    bundle_root = Path(payload["BundleRoot"])
    zip_path = Path(payload["ZipPath"])
    assert bundle_root.is_dir()
    assert zip_path.is_file()
    assert payload["ZipBytes"] == zip_path.stat().st_size
    assert payload["FileCount"] > len(required_paths)

    for relative_path in required_paths:
        assert (bundle_root / relative_path).is_file(), relative_path
    assert (bundle_root / "scripts/r27_g2_runtime_package_manifest.txt").is_file()
    assert (bundle_root / "PACKAGE_BUILD_INFO.txt").is_file()
    assert (bundle_root / "PACKAGE_SOURCE_STATUS.txt").is_file()
    build_info = (bundle_root / "PACKAGE_BUILD_INFO.txt").read_text(encoding="utf-8")
    assert "<repo>" not in build_info
    assert "default_parallel_reset_worker_limit=64" in build_info
    assert "default_parallel_collect_cost_hours=9-15" in build_info
    assert "serial_launch=disabled" in build_info
    assert "parallel_launch_command=MAX_WORKERS=64" in build_info
    assert "launch_authorization=blocked" in build_info
    assert "optional structural review artifact only" in build_info
    assert "remote launch authority is the clean Git checkout" in build_info
    assert "checkpoints are staged by registered filename" in build_info
    source_status = (bundle_root / "PACKAGE_SOURCE_STATUS.txt").read_text(
        encoding="utf-8"
    )
    assert "source_management=" in source_status
    assert "package_scope_dirty=" in source_status

    for forbidden in (
        "ha_ctse_process/__pycache__/cache.pyc",
        "ha_ctse_process/model.pt",
        "ha_ctse_process/test_fixture.py",
        "tests/.pytest_tmp/scratch.txt",
        "scripts/logs_old/runner_output.log",
        "memory/backup_20260706/stale.md",
    ):
        assert not (bundle_root / forbidden).exists()

    with zipfile.ZipFile(zip_path) as archive:
        archive_names = set(archive.namelist())
        assert archive.testzip() is None
    assert "scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh" in archive_names
    assert not any("__pycache__" in name for name in archive_names)
    assert not any(name.endswith((".pt", ".pyc", ".log")) for name in archive_names)


def test_packager_rejects_manifest_escape_without_creating_output(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    write_fixture_file(
        source_root,
        "scripts/r27_g2_runtime_package_manifest.txt",
        "file ../outside.txt\n",
    )
    output_root = tmp_path / "output"

    result = subprocess.run(
        [
            find_pwsh(),
            "-NoProfile",
            "-File",
            str(PACKAGER),
            "-SourceRoot",
            str(source_root),
            "-OutputRoot",
            str(output_root),
            "-BundleName",
            "r27_g2_runtime_escape",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "escapes SourceRoot" in (result.stdout + result.stderr)
    assert not output_root.exists()
