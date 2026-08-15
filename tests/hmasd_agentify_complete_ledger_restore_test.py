"""Focused regression coverage for canonical ledger-only Agentify restoration."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / ".agents" / "skills" / "hmasd-agentify-transport" / "scripts" / "restore_complete_agentify_ledger.py"
SPEC = importlib.util.spec_from_file_location("ledger_restore", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CompleteLedgerRestoreTest(unittest.TestCase):
    def test_restores_complete_schema_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            question = root / "question.md"
            question.write_text("frozen request\n", encoding="utf-8")
            sha = hashlib.sha256(question.read_bytes()).hexdigest()
            response = "full exact answer"
            response_sha = hashlib.sha256(response.encode("utf-8")).hexdigest()
            op = {
                "status": "COMPLETE", "terminalState": "NATURAL_COMPLETION_VERIFIED",
                "sendCount": 1, "sendActionCount": 1, "clickCount": 1,
                "operationId": "op-1", "provider": "chatgpt", "model": "Pro",
                "stableKey": "stable", "idempotencyKey": "key-1", "promptSha256": sha,
                "conversationUrl": "https://chatgpt.com/c/example", "conversationId": "example",
                "userMessageId": "user-1", "assistantMessageId": "assistant-1",
                "responseText": response, "responseSha256": response_sha,
                "causalSendReceipt": {"ok": True, "persisted": True, "operationId": "op-1", "sendActionCount": 1, "clickCount": 1, "sourceSha256": sha, "canonicalPromptSha256": sha},
                "snapshots": [{"assistantMessageId": "assistant-1", "textSha256": response_sha}, {"assistantMessageId": "assistant-1", "textSha256": response_sha}],
                "controls": {"stop": False, "continue": False, "retry": False, "answerNow": False},
                "tabId": "tab-1",
            }
            state = root / "state.json"
            state.write_text(json.dumps({"operations": {"key-1": op}}), encoding="utf-8")
            batch = root / "batch.json"
            batch.write_text(json.dumps({"provider": "chatgpt", "question_paths": [str(question)]}), encoding="utf-8")
            target = root / "results.json"
            restored = MODULE.restore(state_path=state, batch_path=batch, idempotency_key="key-1", results_path=target)
            self.assertEqual(restored["schema_version"], 1)
            self.assertEqual(restored["rows"][0]["response"], response)
            self.assertEqual(restored["rows"][0]["receipt"]["responseSha256"], response_sha)
            self.assertIsNone(restored["tab_cleanup"]["closed"])
            with self.assertRaises(MODULE.RestoreError):
                MODULE.restore(state_path=state, batch_path=batch, idempotency_key="key-1", results_path=target)

    def test_rejects_incomplete_or_mutated_ledger_response(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            question = root / "question.md"
            question.write_text("q", encoding="utf-8")
            sha = hashlib.sha256(question.read_bytes()).hexdigest()
            op = {"status": "COMPLETE", "terminalState": "NATURAL_COMPLETION_VERIFIED", "sendCount": 1, "sendActionCount": 1, "clickCount": 1, "operationId": "x", "provider": "chatgpt", "model": "Pro", "stableKey": "s", "promptSha256": sha, "conversationUrl": "https://chatgpt.com/c/x", "conversationId": "x", "userMessageId": "u", "assistantMessageId": "a", "responseText": "full", "responseSha256": "0" * 64, "causalSendReceipt": {"ok": True, "persisted": True, "operationId": "x", "sendActionCount": 1, "clickCount": 1, "sourceSha256": sha, "canonicalPromptSha256": sha}, "snapshots": [{"assistantMessageId": "a", "textSha256": "0" * 64}, {"assistantMessageId": "a", "textSha256": "0" * 64}], "controls": {"stop": False, "continue": False, "retry": False, "answerNow": False}}
            state = root / "state.json"; state.write_text(json.dumps({"operations": {"key": op}}), encoding="utf-8")
            batch = root / "batch.json"; batch.write_text(json.dumps({"provider": "chatgpt", "question_paths": [str(question)]}), encoding="utf-8")
            with self.assertRaises(MODULE.RestoreError):
                MODULE.restore(state_path=state, batch_path=batch, idempotency_key="key", results_path=root / "result.json")


if __name__ == "__main__":
    unittest.main()
