"""Focused fake-only evidence for the HMASD external-review boundary."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

import scripts.hmasd_external_review as external_review

from scripts.hmasd_external_review import (
    ArchiveConflict,
    CommitmentUnknown,
    ExternalReviewError,
    create_archive_if_absent,
    partition_monitors,
    render_handoff_input,
    round_id,
    validate_archive,
    validate_prompts,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hmasd_external_review"


def _operation() -> dict[str, object]:
    return json.loads((FIXTURES / "operation_ref.json").read_text(encoding="utf-8"))


def _archive() -> dict[str, object]:
    return json.loads((FIXTURES / "archive.json").read_text(encoding="utf-8"))


def _archive_destination(root: Path, operation: dict[str, object]) -> Path:
    return root / Path(str(operation["archive_path"]))

def _use_archive_root(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(external_review, "_PROJECT_ROOT", root)


def _operation_with_archive_bytes(operation: dict[str, object], raw: bytes) -> dict[str, object]:
    bound = dict(operation)
    bound["archive_sha256"] = hashlib.sha256(raw).hexdigest()
    return bound


def test_round_id_is_stable_and_uses_all_frozen_inputs() -> None:
    question = "1" * 64
    evidence = "2" * 64
    expected = hashlib.sha256(
        f"example-direction\n{question}\n{evidence}\nhmasd-external-review-v1".encode()
    ).hexdigest()[:20]

    assert round_id("example-direction", question, evidence, "hmasd-external-review-v1") == expected
    assert round_id("example-direction", "3" * 64, evidence, "hmasd-external-review-v1") != expected


def test_prompts_are_blind_and_convergence_isolation_is_enforced(tmp_path: Path) -> None:
    round_dir = tmp_path / "round"
    round_dir.mkdir()
    for source in (FIXTURES / "prompts").iterdir():
        (round_dir / source.name).write_bytes(source.read_bytes())

    result = validate_prompts(round_dir)
    assert result["status"] == "VALID"
    assert set(result["prompts"]) == {
        "gemini_divergent_prompt",
        "pro_divergent_prompt",
        "pro_convergence_prompt",
    }

    convergence = round_dir / "PRO_CONVERGENCE_PROMPT.md"
    convergence.write_text(
        convergence.read_text(encoding="utf-8") + "\nSee GEMINI_DIVERGENT_PROMPT.md.\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="forbidden provider reference"):
        validate_prompts(round_dir)


def test_monitor_partition_is_sorted_and_round_robin() -> None:
    sessions = json.loads((FIXTURES / "sessions.json").read_text(encoding="utf-8"))
    partitions = partition_monitors(sessions, 2)
    assert [[item["stableKey"] for item in group] for group in partitions] == [
        ["session-a", "session-c"],
        ["session-b", "session-d"],
    ]


def test_archive_validation_and_handoff_preserve_response_sha(tmp_path: Path) -> None:
    archive = _archive()
    validated = validate_archive(_operation(), archive)
    assert validated["responseSha256"] == archive["responseSha256"]

    out = tmp_path / "ignored" / "handoff-input.json"
    rendered = render_handoff_input(FIXTURES / "archive.json", out)
    assert rendered["responseSha256"] == archive["responseSha256"]
    assert rendered["responseText"] == archive["responseText"]
    assert json.loads(out.read_text(encoding="utf-8"))["archiveSha256"] == hashlib.sha256(
        (FIXTURES / "archive.json").read_bytes()
    ).hexdigest()


def test_complete_operation_identity_is_required_before_any_archive_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_archive_root(monkeypatch, tmp_path)
    operation = _operation()
    destination = _archive_destination(tmp_path, operation)
    source_bytes = (FIXTURES / "archive.json").read_bytes()
    destination.parent.mkdir(parents=True)
    destination.write_bytes(source_bytes)

    for missing in (
        "commitment_state",
        "provider",
        "stable_key",
        "session_id",
        "operation_id",
        "idempotency_key",
        "request_fingerprint",
        "prompt_sha256",
        "question_sha256",
        "evidence_sha256",
        "direction_id",
        "round_id",
        "archive_path",
        "archive_sha256",
    ):
        incomplete = dict(operation)
        incomplete.pop(missing)
        with pytest.raises(ExternalReviewError):
            create_archive_if_absent(incomplete, FIXTURES / "archive.json", destination)
        assert destination.read_bytes() == source_bytes

    wrong_binding = dict(operation)
    wrong_binding["archive_sha256"] = "0" * 64
    with pytest.raises(ExternalReviewError):
        create_archive_if_absent(wrong_binding, FIXTURES / "archive.json", destination)
    assert destination.read_bytes() == source_bytes


def test_unknown_commitment_refuses_before_archive_create(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_archive_root(monkeypatch, tmp_path)
    unknown = _operation()
    unknown["commitment_state"] = "UNKNOWN"
    destination = _archive_destination(tmp_path, unknown)

    with pytest.raises(CommitmentUnknown):
        create_archive_if_absent(unknown, FIXTURES / "archive.json", destination)

    assert not destination.exists()


def test_provider_path_mismatch_refuses_without_changing_existing_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_archive_root(monkeypatch, tmp_path)
    operation = _operation()
    destination = _archive_destination(tmp_path, operation)
    source_bytes = (FIXTURES / "archive.json").read_bytes()
    unowned = tmp_path / "unowned-archive.json"
    with pytest.raises(ExternalReviewError):
        create_archive_if_absent(operation, FIXTURES / "archive.json", unowned)
    assert not unowned.exists()
    destination.parent.mkdir(parents=True)
    destination.write_bytes(source_bytes)
    mismatch = dict(operation)
    mismatch["provider"] = "gemini"

    with pytest.raises(ExternalReviewError):
        create_archive_if_absent(mismatch, FIXTURES / "archive.json", destination)

    assert destination.read_bytes() == source_bytes


def test_same_response_with_different_archive_bytes_conflicts_without_rewrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_archive_root(monkeypatch, tmp_path)
    operation = _operation()
    source = FIXTURES / "archive.json"
    destination = _archive_destination(tmp_path, operation)
    create_archive_if_absent(operation, source, destination)
    source_bytes = destination.read_bytes()
    alternate = tmp_path / "same-response-different-archive.json"
    alternate_bytes = source_bytes + b"\n"
    alternate.write_bytes(alternate_bytes)
    alternate_operation = _operation_with_archive_bytes(operation, alternate_bytes)

    with pytest.raises(ArchiveConflict):
        create_archive_if_absent(alternate_operation, alternate, destination)

    assert destination.read_bytes() == source_bytes


def test_concurrent_distinct_archives_conflict_without_changing_existing_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_archive_root(monkeypatch, tmp_path)
    operation = _operation()
    source = FIXTURES / "archive.json"
    destination = _archive_destination(tmp_path, operation)
    create_archive_if_absent(operation, source, destination)
    source_bytes = destination.read_bytes()
    first = tmp_path / "first-distinct-archive.json"
    second = tmp_path / "second-distinct-archive.json"
    first_bytes = source_bytes + b"\n"
    second_bytes = source_bytes + b"\n\n"
    first.write_bytes(first_bytes)
    second.write_bytes(second_bytes)
    first_operation = _operation_with_archive_bytes(operation, first_bytes)
    second_operation = _operation_with_archive_bytes(operation, second_bytes)

    def import_distinct(candidate: tuple[dict[str, object], Path]) -> str:
        try:
            return str(create_archive_if_absent(candidate[0], candidate[1], destination)["status"])
        except ArchiveConflict:
            return "CONFLICT"

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(import_distinct, ((first_operation, first), (second_operation, second))))

    assert outcomes == ["CONFLICT", "CONFLICT"]
    assert destination.read_bytes() == source_bytes


def test_concurrent_identical_archive_create_is_exact_and_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_archive_root(monkeypatch, tmp_path)
    operation = _operation()
    source = FIXTURES / "archive.json"
    destination = _archive_destination(tmp_path, operation)

    def import_once() -> dict[str, object]:
        return create_archive_if_absent(operation, source, destination)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: import_once(), range(8)))

    assert sum(result["status"] == "CREATED" for result in results) == 1
    assert all(result["status"] in {"CREATED", "IDEMPOTENT"} for result in results)
    assert destination.read_bytes() == source.read_bytes()

    same = create_archive_if_absent(operation, source, destination)
    assert same["status"] == "IDEMPOTENT"


def test_cli_commitment_unknown_is_exit_code_seven_without_send_surface(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_archive_root(monkeypatch, tmp_path)
    unknown = _operation()
    unknown["commitment_state"] = "COMMITMENT_UNKNOWN"
    operation_path = tmp_path / "unknown-operation.json"
    operation_path.write_text(json.dumps(unknown), encoding="utf-8")
    destination = _archive_destination(tmp_path, unknown)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "hmasd_external_review.py"),
            "validate-archive",
            "--operation-ref",
            str(operation_path),
            "--archive",
            str(FIXTURES / "archive.json"),
            "--out",
            str(destination),
        ],
        check=False,
        capture_output=True,
        cwd=tmp_path,
        text=True,
    )
    assert result.returncode == 7
    assert not destination.exists()
