from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".agents/skills/hmasd-chatgpt-pro-transport/scripts"


def _fixture(tmp_path):
    # Only the published source dependencies, no ignored session scripts or live registry.
    scripts = tmp_path / "clean-source" / "scripts"
    scripts.mkdir(parents=True)
    for name in ("archive_delivered_claude_request.py", "transport_contract.py"):
        shutil.copyfile(SCRIPTS / name, scripts / name)
    artifacts = {}
    for name, content in (("prompt", "fixed prompt"), ("receipt", "delivered"),
                          ("facts", "{}"), ("response", "full decision")):
        path = tmp_path / (name + ".txt")
        path.write_text(content, encoding="utf-8")
        artifacts[name] = path
    record = {"state": "DIRECTION_VERIFIED", "request_id": "r1", "direction_id": "alpha",
              "provider_url": "https://chatgpt.com/c/conversation-1",
              "conversation_id": "conversation-1", "prompt_sha256": hashlib.sha256(artifacts["prompt"].read_bytes()).hexdigest()}
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"bindings": {"em:alpha:convergence": record},
                                    "directions": {"alpha": dict(record)}}), encoding="utf-8")
    args = [sys.executable, "-B", str(scripts / "archive_delivered_claude_request.py"),
            "--registry", str(registry), "--binding-key", "em:alpha:convergence",
            "--request-id", "r1", "--user-message-id", "u1", "--assistant-message-id", "a1",
            "--prompt-file", str(artifacts["prompt"]), "--short-receipt", str(artifacts["receipt"]),
            "--transport-facts", str(artifacts["facts"]), "--github-response", str(artifacts["response"]),
            "--github-commit", "a" * 40, "--send-attempted-at", "1800000000000",
            "--completed-at", "1800000001000"]
    return registry, args


def test_archive_from_clean_source_and_idempotent_replay(tmp_path):
    registry, args = _fixture(tmp_path)
    result = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    data = json.loads(registry.read_text(encoding="utf-8"))
    record = data["bindings"]["em:alpha:convergence"]
    assert record["state"] == data["directions"]["alpha"]["state"] == "ARCHIVED"
    assert record["conversation_id"] == "conversation-1"
    assert record["send_click_count"] == 1
    assert record["user_message_id"] == "u1" and record["assistant_message_id"] == "a1"
    assert record["tab_lifecycle"] == "CLOSED"
    assert record["archive"]["github_response_sha256"] == hashlib.sha256(b"full decision").hexdigest()
    response_sha = hashlib.sha256(b"full decision").hexdigest()
    receipt_sha = hashlib.sha256(b"delivered").hexdigest()
    assert record["archive"]["response_file"] == str((tmp_path / "response.txt").resolve())
    assert record["response_sha256"] == record["archive"]["response_sha256"] == response_sha
    assert record["archive"]["short_receipt_file"] == str((tmp_path / "receipt.txt").resolve())
    assert record["archive"]["short_receipt_sha256"] == receipt_sha
    assert json.loads(result.stdout)["response_sha256"] == response_sha
    assert record["return_receipt"]["status"] == "BLOCKED"  # No parent routing in fixture.
    assert "delivered_at" not in record["return_receipt"]
    before = registry.read_bytes()
    replay = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert replay.returncode == 0 and json.loads(replay.stdout)["idempotent"]
    assert registry.read_bytes() == before


@pytest.mark.parametrize("status", ["PENDING", "SENT", "UNCERTAIN", "FAILED", "COMPLETE"])
def test_archive_preserves_existing_receipt_evidence_and_historical_key(tmp_path, status):
    registry, args = _fixture(tmp_path)
    data = json.loads(registry.read_text(encoding="utf-8"))
    receipt = {"status": status, "message_key": "historical-receipt-digest-key",
               "attempt_count": 1, "destination_thread_id": "historical-parent",
               "routing_mode": "PARENT_SESSION", "delivery_status": "observed-status",
               "sent_at": "observed-time", "fallback_attempt_count": 1}
    data["bindings"]["em:alpha:convergence"]["return_receipt"] = receipt
    registry.write_text(json.dumps(data), encoding="utf-8")
    result = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    data = json.loads(registry.read_text(encoding="utf-8"))
    assert data["bindings"]["em:alpha:convergence"]["return_receipt"] == receipt
    assert data["directions"]["alpha"]["return_receipt"] == receipt


def test_archive_stages_new_receipt_to_bound_parent_without_delivery_claim(tmp_path):
    registry, args = _fixture(tmp_path)
    data = json.loads(registry.read_text(encoding="utf-8"))
    parent = "11111111-1111-1111-1111-111111111111"
    data["bindings"]["em:alpha:convergence"]["parent_thread_id"] = parent
    registry.write_text(json.dumps(data), encoding="utf-8")
    result = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(registry.read_text(encoding="utf-8"))["bindings"]["em:alpha:convergence"]["return_receipt"]
    assert receipt["status"] == "PENDING"
    assert receipt["destination_thread_id"] == parent
    assert receipt["attempt_count"] == 0
    assert receipt["response_sha256"] == hashlib.sha256(b"full decision").hexdigest()
    assert "delivered_at" not in receipt and "delivery_status" not in receipt


def test_historical_archived_record_replay_does_not_rewrite_evidence(tmp_path):
    registry, args = _fixture(tmp_path)
    data = json.loads(registry.read_text(encoding="utf-8"))
    record = data["bindings"]["em:alpha:convergence"]
    record.update(state="ARCHIVED", response_sha256="historical-receipt-sha",
                  archive={"response_file": "old-receipt-path"},
                  return_receipt={"message_key": "old-key", "status": "COMPLETE"})
    registry.write_text(json.dumps(data), encoding="utf-8")
    before = registry.read_bytes()
    result = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0 and json.loads(result.stdout)["idempotent"]
    assert registry.read_bytes() == before


@pytest.mark.parametrize("blocker", [False, True])
def test_archive_stages_unsent_or_post_blocker_completion(tmp_path, blocker):
    registry, args = _fixture(tmp_path)
    data = json.loads(registry.read_text(encoding="utf-8"))
    record = data["bindings"]["em:alpha:convergence"]
    parent = "11111111-1111-1111-1111-111111111111"
    record["parent_thread_id"] = parent
    record["send_click_count"] = 3
    receipt = {"status": "PENDING", "attempt_count": 0}
    if blocker:
        receipt.update(kind="TERMINAL_BLOCKER", status="UNCERTAIN", attempt_count=1,
                       message_key="prior-blocker-key", parent_thread_id=parent,
                       delivery_status="actual unknown send effect")
    record["return_receipt"] = dict(receipt)
    registry.write_text(json.dumps(data), encoding="utf-8")
    result = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    data = json.loads(registry.read_text(encoding="utf-8"))
    record = data["bindings"]["em:alpha:convergence"]
    assert record["return_receipt"]["status"] == "PENDING"
    assert record["return_receipt"]["attempt_count"] == 0
    assert record["send_click_count"] == 3
    assert record["return_receipt"]["response_sha256"] == hashlib.sha256(b"full decision").hexdigest()
    if blocker:
        assert record["return_receipt_history"] == [receipt]
        assert data["directions"]["alpha"]["return_receipt_history"] == [receipt]


@pytest.mark.parametrize("mismatch", ["request", "prompt", "state"])
def test_refusal_leaves_registry_bytes_unchanged(tmp_path, mismatch):
    registry, args = _fixture(tmp_path)
    data = json.loads(registry.read_text(encoding="utf-8"))
    record = data["bindings"]["em:alpha:convergence"]
    if mismatch == "request":
        record["request_id"] = "different-request"
    elif mismatch == "prompt":
        record["prompt_sha256"] = "0" * 64
    else:
        record["state"] = "SEND_UNCERTAIN"
    registry.write_text(json.dumps(data), encoding="utf-8")
    before = registry.read_bytes()
    result = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode != 0
    assert registry.read_bytes() == before
