from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / ".agents/skills/hmasd-agentify-transport/scripts/hmasd_agentify_result_path_guard.py"


def _run_guard(repo: Path, expected: Path, returned: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(GUARD),
            "--repo",
            str(repo),
            "--expected-results-path",
            str(expected),
            "--returned-results-path",
            str(returned),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _fixture(tmp_path: Path, assignment: str = "F_MEMBERSHIP_LIFECYCLE_EQUIVALENCE_2026-08-09_V1") -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    result = repo / "temp" / "sessions" / "agentify_transport_operator" / assignment / "results.json"
    result.parent.mkdir(parents=True)
    result.write_text('{"response":"SENSITIVE_RAW_REVIEW"}\n', encoding="utf-8")
    return repo, result


def _payload(process: subprocess.CompletedProcess[str]) -> dict[str, str]:
    assert process.stdout.strip(), process.stderr
    return json.loads(process.stdout)


def test_exact_assignment_path_is_valid_and_does_not_emit_or_modify_result(tmp_path: Path) -> None:
    """Catches the production break where a valid assignment file is rejected or rewritten."""
    repo, result = _fixture(tmp_path)
    before = result.read_bytes()

    process = _run_guard(repo, result, result)

    assert process.returncode == 0
    assert _payload(process) == {"status": "VALID"}
    assert "SENSITIVE_RAW_REVIEW" not in process.stdout
    assert result.read_bytes() == before


def test_generic_returned_root_path_is_a_result_path_mismatch(tmp_path: Path) -> None:
    """Catches the child returning temp/sessions/.../results.json instead of its assignment path."""
    repo, expected = _fixture(tmp_path)
    generic = repo / "temp" / "sessions" / "agentify_transport_operator" / "results.json"
    generic.write_text("GENERIC_SHOULD_NOT_BE_READ", encoding="utf-8")

    process = _run_guard(repo, expected, generic)

    assert process.returncode != 0
    assert _payload(process) == {"status": "ERROR", "code": "RESULT_PATH_MISMATCH"}
    assert "GENERIC_SHOULD_NOT_BE_READ" not in process.stdout


def test_expected_generic_root_path_is_rejected(tmp_path: Path) -> None:
    """Catches accepting the legacy shared root-level results.json as an assignment result."""
    repo, _ = _fixture(tmp_path)
    generic = repo / "temp" / "sessions" / "agentify_transport_operator" / "results.json"
    generic.write_text("ROOT_LEVEL_GENERIC", encoding="utf-8")

    process = _run_guard(repo, generic, generic)

    assert process.returncode != 0
    assert _payload(process)["status"] == "ERROR"
    assert _payload(process)["code"] == "RESULT_PATH_SCOPE_INVALID"
    assert "ROOT_LEVEL_GENERIC" not in process.stdout


def test_missing_exact_assignment_file_is_rejected_without_creation(tmp_path: Path) -> None:
    """Catches reporting COMPLETE when the exact assignment file was never written."""
    repo = tmp_path / "repo"
    result = repo / "temp" / "sessions" / "agentify_transport_operator" / "MISSING_ASSIGNMENT" / "results.json"
    result.parent.mkdir(parents=True)

    process = _run_guard(repo, result, result)

    assert process.returncode != 0
    assert _payload(process) == {"status": "ERROR", "code": "RESULT_FILE_MISSING"}
    assert not result.exists()


def test_redirected_assignment_path_is_rejected_when_symlinks_are_supported(tmp_path: Path) -> None:
    """Catches symlink/junction aliases that let two assignments share a physical result."""
    repo, expected = _fixture(tmp_path)
    outside = tmp_path / "outside-results.json"
    outside.write_text("OUTSIDE_RAW_RESPONSE", encoding="utf-8")
    redirected = expected.parent / "redirected-results.json"
    try:
        redirected.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable on this platform")

    process = _run_guard(repo, redirected, redirected)

    assert process.returncode != 0
    assert _payload(process) == {"status": "ERROR", "code": "RESULT_PATH_REDIRECT"}
    assert "OUTSIDE_RAW_RESPONSE" not in process.stdout
    assert outside.read_text(encoding="utf-8") == "OUTSIDE_RAW_RESPONSE"


def test_distinct_assignment_paths_remain_isolated(tmp_path: Path) -> None:
    """Catches path guards that collapse concurrent assignment directories to one result."""
    repo, first = _fixture(tmp_path, "ASSIGNMENT_ONE")
    second = first.parent.parent / "ASSIGNMENT_TWO" / "results.json"
    second.parent.mkdir(parents=True)
    second.write_text("SECOND_RAW_RESPONSE", encoding="utf-8")

    first_process = _run_guard(repo, first, first)
    second_process = _run_guard(repo, second, second)

    assert first_process.returncode == 0
    assert second_process.returncode == 0
    assert _payload(first_process) == {"status": "VALID"}
    assert _payload(second_process) == {"status": "VALID"}
    assert first.read_text(encoding="utf-8") == '{"response":"SENSITIVE_RAW_REVIEW"}\n'
    assert second.read_text(encoding="utf-8") == "SECOND_RAW_RESPONSE"


def test_guard_never_reads_result_contents_or_changes_file_metadata(tmp_path: Path) -> None:
    """Catches accidental JSON parsing/copying that could alter an archived raw response."""
    repo, result = _fixture(tmp_path)
    before = result.stat()
    before_bytes = result.read_bytes()

    process = _run_guard(repo, result, result)

    after = result.stat()
    assert process.returncode == 0
    assert result.read_bytes() == before_bytes
    assert after.st_size == before.st_size
    assert "SENSITIVE_RAW_REVIEW" not in process.stdout
    assert "SENSITIVE_RAW_REVIEW" not in process.stderr
