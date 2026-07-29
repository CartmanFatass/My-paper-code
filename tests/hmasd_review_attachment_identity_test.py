from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO
    / ".agents"
    / "skills"
    / "hmasd-review-round"
    / "scripts"
    / "verify_assignment_attachment_identity.py"
)
ROUND = "20260728_fixture_attachment_backed_assignment_review"
STAGE = "35a924424f842699dd275949626ef568aee08a22"
QUESTION = "20_PRO_OPEN_QUESTION.md"
CONVERSATION = "registered-conversation-fixture"
TURN = "user-turn-fixture"
ATTACHMENT = "provider-attachment-fixture"
FENCE = "\n".join(
    (
        "CURRENT_REVIEW_ASSIGNMENT",
        "repository=CartmanFatass/My-paper-code",
        "branch=aggressive",
        f"round={ROUND}",
        f"stage_commit={STAGE}",
        f"question={QUESTION}",
        "instruction=Ignore earlier rounds and refs. Read only this question and "
        "its listed evidence from stage_commit.",
    )
)


@pytest.fixture
def pasted_text_attachment_fixture(tmp_path: Path) -> tuple[Path, Path, bytes]:
    payload = (
        FENCE
        + "\n\nQUESTION_PAYLOAD\n"
        + ("domain-specific evidence line\n" * 400)
    ).encode("utf-8")
    expected = tmp_path / "expected-assignment.txt"
    observed = tmp_path / "Pasted_text_fixture.txt"
    expected.write_bytes(payload)
    observed.write_bytes(payload)
    return expected, observed, payload


def run(
    expected: Path,
    *,
    observed: Path | None = None,
    metadata: Path | None = None,
    round_name: str = ROUND,
    stage: str = STAGE,
    question: str = QUESTION,
    attachment_id: str = ATTACHMENT,
) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        str(SCRIPT),
        "--expected-payload",
        str(expected),
        "--conversation-id",
        CONVERSATION,
        "--user-turn-id",
        TURN,
        "--round",
        round_name,
        "--stage-commit",
        stage,
        "--question",
        question,
    ]
    if observed is not None:
        args.extend(
            ("--observed-attachment", str(observed), "--attachment-id", attachment_id)
        )
    if metadata is not None:
        args.extend(("--provider-metadata", str(metadata)))
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_pasted_text_attachment_exact_match_is_verified(
    pasted_text_attachment_fixture: tuple[Path, Path, bytes],
) -> None:
    expected, observed, payload = pasted_text_attachment_fixture
    completed = run(expected, observed=observed)
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["status"] == "ATTACHMENT_IDENTITY_VERIFIED"
    assert result["identity_source"] == "readable_text"
    assert result["payload_bytes"] == len(payload)
    assert result["payload_sha256"] == hashlib.sha256(payload).hexdigest()
    identity = result["sentinel_fence_identity"]
    assert f"round={ROUND}" in identity
    assert f"stage_commit={STAGE}" in identity
    assert f"question={QUESTION}" in identity


@pytest.mark.parametrize(
    ("round_name", "stage"),
    ((ROUND + "_wrong", STAGE), (ROUND, "0" * 40)),
)
def test_wrong_round_or_stage_is_rejected(
    pasted_text_attachment_fixture: tuple[Path, Path, bytes],
    round_name: str,
    stage: str,
) -> None:
    expected, observed, _ = pasted_text_attachment_fixture
    completed = run(expected, observed=observed, round_name=round_name, stage=stage)
    assert completed.returncode == 3
    assert json.loads(completed.stdout)["status"] == "IDENTITY_MISMATCH"


def test_truncated_attachment_is_rejected(
    pasted_text_attachment_fixture: tuple[Path, Path, bytes],
) -> None:
    expected, observed, payload = pasted_text_attachment_fixture
    observed.write_bytes(payload[:-17])
    completed = run(expected, observed=observed)
    assert completed.returncode == 3
    assert json.loads(completed.stdout)["status"] == "IDENTITY_MISMATCH"


def test_unreadable_attachment_is_not_reported_as_send_failure(
    pasted_text_attachment_fixture: tuple[Path, Path, bytes],
) -> None:
    expected, _, _ = pasted_text_attachment_fixture
    completed = run(expected, observed=expected.parent / "missing-Pasted_text.txt")
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["status"] == "IDENTITY_UNREADABLE"


def test_filename_only_metadata_is_unreadable(
    pasted_text_attachment_fixture: tuple[Path, Path, bytes],
) -> None:
    expected, _, _ = pasted_text_attachment_fixture
    metadata = expected.parent / "metadata.json"
    metadata.write_text(json.dumps({"filename": "Pasted_text(5).txt"}), encoding="utf-8")
    completed = run(expected, metadata=metadata)
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["status"] == "IDENTITY_UNREADABLE"


def test_exact_provider_native_metadata_is_verified(
    pasted_text_attachment_fixture: tuple[Path, Path, bytes],
) -> None:
    expected, _, payload = pasted_text_attachment_fixture
    metadata = expected.parent / "metadata.json"
    metadata.write_text(
        json.dumps(
            {
                "metadata_source": "provider_native_attachment_payload",
                "provider_native": True,
                "conversation_id": CONVERSATION,
                "user_turn_id": TURN,
                "attachment_id": ATTACHMENT,
                "payload_bytes": len(payload),
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    completed = run(expected, metadata=metadata)
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["status"] == "ATTACHMENT_IDENTITY_VERIFIED"
    assert result["identity_source"] == "provider_native_metadata"


def test_crlf_renderer_block_preserves_byte_exact_payload_comparison(
    pasted_text_attachment_fixture: tuple[Path, Path, bytes],
) -> None:
    expected, observed, payload = pasted_text_attachment_fixture
    crlf_payload = payload.replace(
        FENCE.encode("utf-8"),
        FENCE.replace("\n", "\r\n").encode("utf-8"),
        1,
    )
    expected.write_bytes(crlf_payload)
    observed.write_bytes(crlf_payload)
    completed = run(expected, observed=observed)
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["payload_sha256"] == hashlib.sha256(
        crlf_payload
    ).hexdigest()
