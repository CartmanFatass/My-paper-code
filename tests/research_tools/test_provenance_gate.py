from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable

import pytest

from tools.research import validate_provenance as gate


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / gate.MANIFEST_PATH


def _load_manifest(root: Path) -> dict[str, Any]:
    return json.loads((root / gate.MANIFEST_PATH).read_text(encoding="utf-8"))


def _write_manifest(root: Path, manifest: dict[str, Any]) -> None:
    (root / gate.MANIFEST_PATH).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _copy_gate_tree(tmp_path: Path) -> Path:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = {gate.MANIFEST_PATH}
    paths.update(artifact["path"] for artifact in manifest["artifacts"])
    for relative in sorted(paths):
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    for source in sorted((ROOT / gate.AGENT_PROFILE_ROOT).glob("*.md")):
        destination = tmp_path / gate.AGENT_PROFILE_ROOT / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return tmp_path


def _codes(report: dict[str, Any]) -> set[str]:
    return {error["code"] for error in report["errors"]}


def test_repository_manifest_passes_the_offline_gate() -> None:
    report = gate.validate_repository(ROOT)

    assert report == {
        "errors": [],
        "ok": True,
        "schema_version": 1,
        "summary": {
            "adapted_artifact_count": 11,
            "artifact_count": 25,
            "dependency_count": 16,
            "local_original_artifact_count": 14,
            "managed_file_count": 22,
            "unresolved_fact_count": 1,
        },
        "tool": "research_provenance_gate",
    }


def test_tampered_local_hash_fails_closed(tmp_path: Path) -> None:
    root = _copy_gate_tree(tmp_path)
    manifest = _load_manifest(root)
    manifest["artifacts"][0]["sha256"] = "0" * 64
    _write_manifest(root, manifest)

    report = gate.validate_repository(root)

    assert not report["ok"]
    assert "artifact_hash_mismatch" in _codes(report)


def test_adapted_file_without_full_pinned_commit_fails_closed(tmp_path: Path) -> None:
    root = _copy_gate_tree(tmp_path)
    manifest = _load_manifest(root)
    adapted = next(
        artifact for artifact in manifest["artifacts"] if artifact["origin"] == "adapted"
    )
    adapted["source_ref"]["commit"] = "main"
    _write_manifest(root, manifest)

    report = gate.validate_repository(root)

    assert not report["ok"]
    assert "adapted_commit_invalid" in _codes(report)


def test_missing_full_k_dense_notice_fails_closed(tmp_path: Path) -> None:
    root = _copy_gate_tree(tmp_path)
    notice = root / gate.NOTICE_PATH
    notice.write_text(
        notice.read_text(encoding="utf-8").replace(
            "Permission is hereby granted, free of charge,", "Permission omitted,"
        ),
        encoding="utf-8",
    )

    report = gate.validate_repository(root)

    assert not report["ok"]
    assert "notice_k_dense_mit" in _codes(report)


def test_missing_dependency_license_fails_closed(tmp_path: Path) -> None:
    root = _copy_gate_tree(tmp_path)
    manifest = _load_manifest(root)
    manifest["dependencies"][0]["license"] = ""
    _write_manifest(root, manifest)

    report = gate.validate_repository(root)

    assert not report["ok"]
    assert "dependency_fact" in _codes(report)
    assert any(error["path"].endswith(".license") for error in report["errors"])


def test_uncovered_managed_file_fails_closed(tmp_path: Path) -> None:
    root = _copy_gate_tree(tmp_path)
    uncovered = root / "tools/research/paper_lookup/uncovered_adapter.py"
    uncovered.write_text("VALUE = 1\n", encoding="utf-8")

    report = gate.validate_repository(root)

    assert not report["ok"]
    assert "managed_file_uncovered" in _codes(report)


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (
            lambda text: text.replace(
                "hypothesis==6.131.9", "hypothesis==6.131.8", 1
            ),
            "lock_version_mismatch",
        ),
        (
            lambda text: text.replace(
                "c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309",
                "c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac30",
                1,
            ),
            "lock_hash_invalid",
        ),
    ],
)
def test_lock_version_or_hash_drift_fails_closed(
    tmp_path: Path,
    mutate: Callable[[str], str],
    expected_code: str,
) -> None:
    root = _copy_gate_tree(tmp_path)
    lock = root / gate.REQUIREMENTS_LOCK
    changed = mutate(lock.read_text(encoding="utf-8"))
    assert changed != lock.read_text(encoding="utf-8")
    lock.write_text(changed, encoding="utf-8")

    report = gate.validate_repository(root)

    assert not report["ok"]
    assert expected_code in _codes(report)
    assert "artifact_hash_mismatch" in _codes(report)


@pytest.mark.parametrize("unsafe", ["../outside.py", "/tmp/outside.py", "tools\\outside.py"])
def test_unsafe_manifest_paths_fail_closed(tmp_path: Path, unsafe: str) -> None:
    root = _copy_gate_tree(tmp_path)
    manifest = _load_manifest(root)
    manifest["artifacts"][0]["path"] = unsafe
    _write_manifest(root, manifest)

    report = gate.validate_repository(root)

    assert not report["ok"]
    assert "unsafe_path" in _codes(report)


def test_symlinked_managed_file_fails_closed(tmp_path: Path) -> None:
    root = _copy_gate_tree(tmp_path)
    target = root / "tools/research/paper_lookup/cli.py"
    target.unlink()
    target.symlink_to("normalizers.py")

    report = gate.validate_repository(root)

    assert not report["ok"]
    assert {"managed_symlink", "symlink_path"} <= _codes(report)


def test_cli_failure_is_nonzero_and_json_is_deterministic(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _copy_gate_tree(tmp_path)
    profile = root / gate.AGENT_PROFILE_ROOT / "hmasd-em.md"
    text = profile.read_text(encoding="utf-8")
    assert "autoloadSkills:\n" in text
    profile.write_text(
        text.replace(
            "autoloadSkills:\n",
            "autoloadSkills:\n  - hmasd-paper-lookup\n",
            1,
        ),
        encoding="utf-8",
    )

    first_exit = gate.main(["--root", str(root)])
    first_output = capsys.readouterr().out
    second_exit = gate.main(["--root", str(root)])
    second_output = capsys.readouterr().out

    assert first_exit == second_exit == 1
    assert first_output == second_output
    payload = json.loads(first_output)
    assert not payload["ok"]
    assert "manager_autoload_forbidden" in _codes(payload)
