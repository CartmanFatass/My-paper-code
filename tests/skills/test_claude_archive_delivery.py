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
    before = registry.read_bytes()
    replay = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert replay.returncode == 0 and json.loads(replay.stdout)["idempotent"]
    assert registry.read_bytes() == before


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
