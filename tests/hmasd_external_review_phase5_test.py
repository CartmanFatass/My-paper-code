"""Focused current-only evidence for the HMASD external-review boundary."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import hmasd_external_review as external_review
from scripts.hmasd_external_review import (
    ArchiveConflict,
    ExternalReviewError,
    create_archive_if_absent,
    partition_monitors,
    round_id,
    validate_archive,
    validate_prompts,
)

render_handoff_input = getattr(external_review, "render_handoff_input")

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hmasd_external_review"


def _operation() -> dict[str, object]:
    return json.loads((FIXTURES / "operation_ref.json").read_text(encoding="utf-8"))


def _response(root: Path) -> Path:
    path = root / "source-response.md"
    path.write_bytes(b"hello")
    return path


def _destination(root: Path, operation: dict[str, object]) -> Path:
    return root / str(operation["response_path"])


def _operation_with_bytes(operation: dict[str, object], raw: bytes) -> dict[str, object]:
    bound = copy.deepcopy(operation)
    archive = bound["archive"]
    assert isinstance(archive, dict)
    archive["sha256"] = hashlib.sha256(raw).hexdigest()
    archive["size_bytes"] = len(raw)
    return bound


def _prompt_round(root: Path) -> Path:
    round_dir = root / "round"
    round_dir.mkdir()
    (round_dir / "PRO_INNOVATOR_PROMPT.md").write_text(
        "Find a falsifiable mechanism from the frozen evidence and report uncertainty.\n",
        encoding="utf-8",
    )
    (round_dir / "PRO_CONVERGENCE_PROMPT.md").write_text(
        "Challenge the EM-authored local synthesis against the declared repository evidence and list residual gaps.\n",
        encoding="utf-8",
    )
    return round_dir


def test_round_id_uses_all_frozen_inputs() -> None:
    expected = "a2604c701f39adec08f5"
    assert round_id("example-direction", "1" * 64, "2" * 64, "hmasd-external-review-v1") == expected
    assert round_id("example-direction", "3" * 64, "2" * 64, "hmasd-external-review-v1") != expected


def test_prompt_pair_and_monitor_partition_remain_mechanical(tmp_path: Path) -> None:
    validated = validate_prompts(_prompt_round(tmp_path))
    assert set(validated) == {"status", "round_dir", "prompts"}
    assert validated["status"] == "VALID"
    sessions = json.loads((FIXTURES / "sessions.json").read_text(encoding="utf-8"))
    partitions = partition_monitors(sessions, 2)
    assert sum(len(partition) for partition in partitions) == len(sessions)


def test_v4_operation_receipt_validates_exact_reread_response(tmp_path: Path) -> None:
    operation = _operation()
    assert operation["schema_version"] == 4
    assert validate_archive(operation, _response(tmp_path)) == operation
    with pytest.raises(ExternalReviewError, match="path to raw UTF-8"):
        validate_archive(operation, {"responseText": "hello"})


def test_product_model_and_reasoning_effort_remain_exact_target_axes(tmp_path: Path) -> None:
    for field, value in (("product_model", "GPT-5.6"), ("reasoning_effort", "High")):
        operation = _operation()
        operation[field] = value
        with pytest.raises(ExternalReviewError):
            validate_archive(operation, _response(tmp_path))


def test_gemini_operation_receipt_requires_null_reasoning_effort(tmp_path: Path) -> None:
    operation = _operation()
    operation["provider"] = "gemini"
    operation["product_model"] = "Gemini 3.1 Pro"
    operation["reasoning_effort"] = None
    operation["observed_conversation_url"] = (
        "https://gemini.google.com/app/" + str(operation["observed_conversation_id"])
    )
    operation["response_path"] = str(operation["response_path"]).replace("/chatgpt/", "/gemini/")
    archive = operation["archive"]
    assert isinstance(archive, dict)
    archive["path"] = operation["response_path"]
    assert validate_archive(operation, _response(tmp_path)) == operation

    operation["reasoning_effort"] = "Pro"
    with pytest.raises(ExternalReviewError, match="reasoning_effort null"):
        validate_archive(operation, _response(tmp_path))


def test_attempted_send_without_observed_user_id_never_publishes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(external_review, "_PROJECT_ROOT", tmp_path)
    operation = _operation()
    operation["observed_conversation_url"] = None
    operation["observed_conversation_id"] = None
    operation["provider_user_message_id"] = None
    operation["provider_assistant_message_id"] = None
    operation["archive"] = None
    operation["error"] = {"code": "USER_MESSAGE_NOT_OBSERVED"}
    with pytest.raises(ExternalReviewError, match="never resend"):
        create_archive_if_absent(operation, _response(tmp_path), tmp_path / "unused")
    assert not (tmp_path / "docs").exists()

def test_pre_send_error_is_retryable_but_not_archivable(tmp_path: Path) -> None:
    operation = _operation()
    operation["send_attempted"] = False
    operation["send_attempted_at"] = None
    operation["observed_conversation_url"] = None
    operation["observed_conversation_id"] = None
    operation["provider_user_message_id"] = None
    operation["provider_assistant_message_id"] = None
    operation["archive"] = None
    operation["error"] = {"code": "PRE_SEND_UI"}
    with pytest.raises(ExternalReviewError, match="remains retryable"):
        validate_archive(operation, _response(tmp_path))


def test_exact_response_and_separate_operation_receipt_publish_idempotently(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(external_review, "_PROJECT_ROOT", tmp_path)
    operation = _operation()
    destination = _destination(tmp_path, operation)
    created = create_archive_if_absent(operation, _response(tmp_path), destination)
    assert created["status"] == "CREATED"
    assert destination.read_bytes() == b"hello"
    operation_path = destination.with_name("operation_ref.json")
    assert json.loads(operation_path.read_text(encoding="utf-8")) == operation

    repeated = create_archive_if_absent(operation, _response(tmp_path), destination)
    assert repeated["status"] == "IDEMPOTENT"
    assert repeated["response_ref"]["sha256"] == hashlib.sha256(b"hello").hexdigest()


def test_conflicting_raw_response_never_rewrites_current_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(external_review, "_PROJECT_ROOT", tmp_path)
    operation = _operation()
    destination = _destination(tmp_path, operation)
    create_archive_if_absent(operation, _response(tmp_path), destination)
    source = tmp_path / "different.md"
    source.write_bytes(b"different")
    changed = _operation_with_bytes(operation, b"different")
    with pytest.raises(ArchiveConflict):
        create_archive_if_absent(changed, source, destination)
    assert destination.read_bytes() == b"hello"


def test_archive_projection_is_exact_only(tmp_path: Path) -> None:
    operation = _operation()
    archive = operation["archive"]
    assert isinstance(archive, dict)
    archive["projection"] = "normalized"
    with pytest.raises(ExternalReviewError, match="projection must be exact"):
        validate_archive(operation, _response(tmp_path))


def test_handoff_uses_v4_receipt_and_raw_response(tmp_path: Path) -> None:
    out = tmp_path / "handoff.json"
    rendered = render_handoff_input(_operation(), _response(tmp_path), out)
    assert rendered["handoff_kind"] == "hmasd_external_review_intake_v4"
    assert rendered["response_text"] == "hello"
    assert json.loads(out.read_text(encoding="utf-8")) == rendered
