from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_file_fingerprint.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_fingerprint_reports_script_computed_sha_and_size(tmp_path: Path) -> None:
    target = tmp_path / "prompt.md"
    payload = b"first line\nsecond line\n"
    target.write_bytes(payload)

    result = _run("--path", str(target))

    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["file"]["sha256"] == hashlib.sha256(payload).hexdigest()
    assert data["file"]["size_bytes"] == len(payload)
    assert data["file"]["utf8"]["valid"] is True
    assert data["file"]["utf8"]["lf_count"] == 2
    assert data["checks"] == []


def test_expected_sha_and_size_mismatch_fail_closed(tmp_path: Path) -> None:
    target = tmp_path / "response.md"
    target.write_bytes(b"actual response")

    result = _run(
        "--path",
        str(target),
        "--expect-sha256",
        "0" * 64,
        "--expect-size-bytes",
        "999",
    )

    assert result.returncode == 2
    data = json.loads(result.stdout)
    assert data["ok"] is False
    checks = {check["name"]: check for check in data["checks"]}
    assert checks["sha256"]["ok"] is False
    assert checks["size_bytes"]["ok"] is False
    assert checks["sha256"]["actual"] == hashlib.sha256(b"actual response").hexdigest()
    assert checks["size_bytes"]["actual"] == len(b"actual response")


def test_require_utf8_rejects_invalid_bytes_and_appends_utf8_check(tmp_path: Path) -> None:
    target = tmp_path / "invalid-prompt.md"
    target.write_bytes(b"valid prefix\xff\xfe")

    result = _run("--path", str(target), "--require-utf8")

    assert result.returncode == 2
    data = json.loads(result.stdout)
    assert data["ok"] is False
    assert data["file"]["utf8"]["valid"] is False
    assert data["file"]["utf8"]["char_count"] is None
    assert data["checks"][-1] == {
        "actual": False,
        "expected": True,
        "name": "utf8",
        "ok": False,
    }


def test_missing_or_non_file_path_fails_closed(tmp_path: Path) -> None:
    missing = _run("--path", str(tmp_path / "missing.md"))
    directory = _run("--path", str(tmp_path))

    assert missing.returncode == 3
    assert json.loads(missing.stdout)["error"]["kind"] == "path_unreadable"
    assert directory.returncode == 3
    assert json.loads(directory.stdout)["error"]["kind"] == "not_a_file"
