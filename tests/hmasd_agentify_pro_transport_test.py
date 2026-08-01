from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / ".agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py"
SPEC = importlib.util.spec_from_file_location("hmasd_agentify_pro_transport", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AgentifyTransportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs/external-review/round").mkdir(parents=True)
        (self.root / "logs/agentify/round").mkdir(parents=True)
        self.prompt = "Assignment: ROUND-ABC\nReply exactly."
        self.prompt_path = self.root / "docs/external-review/round/20_PRO_OPEN_QUESTION.md"
        self.prompt_path.write_bytes(self.prompt.encode("utf-8"))
        self.backend_selection_path = self.root / "logs/agentify/round/TRANSPORT_BACKEND.json"
        self.backend_selection_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "assignment_identity": "ROUND-ABC",
                    "transport_backend": "agentify",
                    "operation_key": "round-abc-stage-1",
                }
            ),
            encoding="utf-8",
        )
        self.request = {
            "schema_version": 1,
            "transport_backend": "agentify",
            "transport_owner": "code_project_manager",
            "stable_key": "hmasd-formal-pro",
            "provider": "chatgpt",
            "model": "Pro",
            "conversation_url": "https://chatgpt.com/c/conversation-1",
            "conversation_id": "conversation-1",
            "idempotency_key": "round-abc-stage-1",
            "assignment_identity": "ROUND-ABC",
            "backend_selection_path": str(self.backend_selection_path),
            "prompt_path": str(self.prompt_path),
            "timeout_ms": 300000,
        }
        self.validated = MODULE.validate_request(self.request, repo_root=self.root)
        response = "STRICT_OK"
        response_hash = sha256(response)
        self.receipt = {
            "operationId": "operation-1",
            "idempotencyKey": self.request["idempotency_key"],
            "requestFingerprint": "a" * 64,
            "stableKey": self.request["stable_key"],
            "provider": "chatgpt",
            "model": "Pro",
            "conversationUrl": self.request["conversation_url"],
            "conversationId": self.request["conversation_id"],
            "promptSha256": sha256(self.prompt),
            "timeoutMs": 300000,
            "deadlineAt": 301000,
            "status": "COMPLETE",
            "terminalState": "NATURAL_COMPLETION_VERIFIED",
            "sendCount": 1,
            "createdAt": 1000,
            "preparedAt": 1100,
            "modelEvidence": "Pro",
            "userMessageId": "user-1",
            "submittedAt": 1200,
            "assistantMessageId": "assistant-1",
            "responseText": response,
            "responseSha256": response_hash,
            "snapshots": [
                {"observedAt": 2000, "assistantMessageId": "assistant-1", "textSha256": response_hash},
                {"observedAt": 5000, "assistantMessageId": "assistant-1", "textSha256": response_hash},
            ],
            "controls": {"stop": False, "continue": False, "retry": False, "answerNow": True},
            "clickedControls": [],
            "completedAt": 5100,
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_complete_receipt_and_visible_answer_now_without_activation_pass(self) -> None:
        result = MODULE.validate_receipt(self.receipt, self.validated)
        self.assertEqual(result["assistantMessageId"], "assistant-1")

    def test_owner_key_prompt_and_conversation_are_bound(self) -> None:
        cases = [
            ("stable_key", "hmasd-independent-research-pro", "stable_key_owner_mismatch"),
            ("conversation_id", "other", "conversation_identity_mismatch"),
            ("assignment_identity", "ROUND-MISSING", "backend_selection_mismatch"),
        ]
        for field, value, error in cases:
            with self.subTest(field=field), self.assertRaisesRegex(MODULE.TransportError, error):
                bad = dict(self.request)
                bad[field] = value
                MODULE.validate_request(bad, repo_root=self.root)
        self.backend_selection_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "assignment_identity": "ROUND-MISSING",
                    "transport_backend": "agentify",
                    "operation_key": "round-abc-stage-1",
                }
            ),
            encoding="utf-8",
        )
        missing = dict(self.request)
        missing["assignment_identity"] = "ROUND-MISSING"
        with self.assertRaisesRegex(MODULE.TransportError, "assignment_identity_not_in_prompt"):
            MODULE.validate_request(missing, repo_root=self.root)
        selection = json.loads(self.backend_selection_path.read_text(encoding="utf-8"))
        selection["assignment_identity"] = "ROUND-ABC"
        self.backend_selection_path.write_text(json.dumps(selection), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.TransportError, "request_field_set_mismatch"):
            MODULE.validate_request({**self.request, "extra": "forbidden"}, repo_root=self.root)

    def test_backend_selection_is_restart_stable_and_agentify_only(self) -> None:
        selection = json.loads(self.backend_selection_path.read_text(encoding="utf-8"))
        selection["transport_backend"] = "browser"
        self.backend_selection_path.write_text(json.dumps(selection), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.TransportError, "backend_selection_mismatch"):
            MODULE.validate_request(self.request, repo_root=self.root)

    def test_prepare_command_computes_hash_and_writes_exact_restart_stable_pair(self) -> None:
        selection = self.root / "logs/agentify/frozen/TRANSPORT_BACKEND.json"
        request_path = self.root / "logs/agentify/frozen/REQUEST.json"
        prompt = self.root / "docs/external-review/round/frozen_question.md"
        prompt.write_text("Assignment: ROUND-FROZEN\nReply exactly.", encoding="utf-8")
        args = SimpleNamespace(
            owner="code_project_manager",
            stable_key="hmasd-formal-pro",
            model="Pro",
            conversation_url="https://chatgpt.com/c/conversation-1",
            conversation_id="conversation-1",
            assignment_identity="ROUND-FROZEN",
            operation_key="round-frozen-operation",
            prompt_path=prompt,
            prompt_source=None,
            timeout_ms=300000,
            selection=selection,
            request=request_path,
        )
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root):
            MODULE.command_prepare(args)
            MODULE.command_prepare(args)
            args.model = "Thinking"
            with self.assertRaisesRegex(MODULE.TransportError, "output_exists_with_different_bytes"):
                MODULE.command_prepare(args)
        expected_hash = hashlib.sha256(prompt.read_bytes()).hexdigest()
        self.assertEqual(
            json.loads(selection.read_text(encoding="utf-8")),
            {
                "schema_version": 1,
                "assignment_identity": "ROUND-FROZEN",
                "transport_backend": "agentify",
                "operation_key": "round-frozen-operation",
            },
        )
        prepared_request = json.loads(request_path.read_text(encoding="utf-8"))
        self.assertEqual(prepared_request["prompt_path"], str(prompt.resolve()))
        self.assertEqual(prepared_request["backend_selection_path"], str(selection.resolve()))
        self.assertEqual(
            MODULE.validate_request(prepared_request, repo_root=self.root)["prompt"],
            prompt.read_bytes().decode("utf-8"),
        )

    def test_direction_provision_copies_exact_explorer_prompt_once(self) -> None:
        source = self.root / "local_research/frozen_direction_prompt.md"
        source.parent.mkdir(parents=True)
        identity = "IR_DIRECTION_REVIEW:direction-1"
        source_bytes = f"{identity}\nReview the frozen candidate.\n".encode("utf-8")
        source.write_bytes(source_bytes)
        item = self.root / "local_research/pro_reviews/direction-1"
        prompt = item / "20_PRO_OPEN_QUESTION.md"
        args = SimpleNamespace(
            assignment_identity=identity,
            prompt_path=prompt,
            prompt_source=source,
        )
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root):
            MODULE.command_provision_direction(args)
            MODULE.command_provision_direction(args)
        self.assertEqual(prompt.read_bytes(), source_bytes)

        bad_source = self.root / "local_research/pro_reviews/source.md"
        bad_source.write_text(identity, encoding="utf-8")
        args.prompt_source = bad_source
        args.prompt_path = self.root / "local_research/pro_reviews/direction-2/20_PRO_OPEN_QUESTION.md"
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root):
            with self.assertRaisesRegex(MODULE.TransportError, "prompt_source_inside_review_archive"):
                MODULE.command_provision_direction(args)

        invalid_prompt = self.root / "local_research/pro_reviews/direction-3/NONCANONICAL.md"
        args.prompt_source = source
        args.prompt_path = invalid_prompt
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root):
            with self.assertRaisesRegex(MODULE.TransportError, "direction_prompt_item_depth_invalid"):
                MODULE.command_provision_direction(args)
        self.assertFalse(invalid_prompt.exists())

    def test_prepare_parser_does_not_accept_operator_supplied_prompt_hash(self) -> None:
        help_text = MODULE.build_parser().format_help()
        self.assertIn("prepare", help_text)
        self.assertIn("provision-direction", help_text)
        prepare = MODULE.build_parser()._subparsers._group_actions[0].choices["prepare"]
        self.assertNotIn("--prompt-sha256", prepare.format_help())
        self.assertNotIn("--prompt-source", prepare.format_help())

    def test_receipt_rejects_wrong_send_identity_completion_and_hash(self) -> None:
        mutations = [
            ("sendCount", 2, "receipt_sendCount_mismatch"),
            ("assistantMessageId", "user-1", "receipt_message_identity_collision"),
            ("responseSha256", "0" * 64, "receipt_response_hash_mismatch"),
            ("clickedControls", ["Answer now"], "receipt_prohibited_control_activated"),
        ]
        for field, value, error in mutations:
            with self.subTest(field=field), self.assertRaisesRegex(MODULE.TransportError, error):
                bad = json.loads(json.dumps(self.receipt))
                bad[field] = value
                MODULE.validate_receipt(bad, self.validated)

    def test_receipt_rejects_short_or_mismatched_stable_snapshots(self) -> None:
        short = json.loads(json.dumps(self.receipt))
        short["snapshots"][1]["observedAt"] = 4999
        with self.assertRaisesRegex(MODULE.TransportError, "receipt_snapshot_stability_too_short"):
            MODULE.validate_receipt(short, self.validated)
        mismatch = json.loads(json.dumps(self.receipt))
        mismatch["snapshots"][1]["assistantMessageId"] = "assistant-2"
        with self.assertRaisesRegex(MODULE.TransportError, "receipt_snapshot_identity_mismatch"):
            MODULE.validate_receipt(mismatch, self.validated)

        outside = json.loads(json.dumps(self.receipt))
        outside["snapshots"][0]["observedAt"] = outside["submittedAt"] - 1
        with self.assertRaisesRegex(MODULE.TransportError, "receipt_snapshot_outside_response_interval"):
            MODULE.validate_receipt(outside, self.validated)

    def test_response_text_preserves_leading_and_trailing_whitespace(self) -> None:
        receipt = json.loads(json.dumps(self.receipt))
        receipt["responseText"] = "\n  STRICT_OK  \n"
        receipt["responseSha256"] = sha256(receipt["responseText"])
        for snapshot in receipt["snapshots"]:
            snapshot["textSha256"] = receipt["responseSha256"]
        self.assertEqual(MODULE.validate_receipt(receipt, self.validated)["responseText"], receipt["responseText"])

    def test_agentify_source_identity_mismatch_fails_before_http(self) -> None:
        state_dir = self.root / "agentify-state"
        state_dir.mkdir()
        (state_dir / "state.json").write_text(
            json.dumps(
                {
                    "port": 43111,
                    "serverId": "server-1",
                    "sourceCommit": "0" * 40,
                    "sourceDirty": False,
                }
            ),
            encoding="utf-8",
        )
        (state_dir / "token.txt").write_text("token", encoding="utf-8")
        with mock.patch.object(MODULE, "_http_json") as http_json:
            with self.assertRaisesRegex(MODULE.TransportError, "agentify_state_source_identity_mismatch"):
                MODULE.call_agentify(self.validated, state_dir=state_dir, verify_existing=False)
            http_json.assert_not_called()

        (state_dir / "state.json").write_text(
            json.dumps(
                {
                    "port": 43111,
                    "serverId": "server-1",
                    "sourceCommit": MODULE.AGENTIFY_REQUIRED_COMMIT,
                    "sourceDirty": False,
                }
            ),
            encoding="utf-8",
        )
        wrong_health = {
            "ok": True,
            "serverId": "server-1",
            "sourceCommit": "0" * 40,
            "sourceDirty": False,
        }
        with mock.patch.object(MODULE, "_http_json", return_value=wrong_health) as http_json:
            with self.assertRaisesRegex(MODULE.TransportError, "agentify_server_identity_mismatch"):
                MODULE.call_agentify(self.validated, state_dir=state_dir, verify_existing=True)
            http_json.assert_called_once()

        with self.assertRaisesRegex(MODULE.TransportError, "agentify_state_dir_not_absolute"):
            MODULE.call_agentify(self.validated, state_dir=Path("relative-state"), verify_existing=True)

    def test_recovery_refuses_resend_when_failed_operation_has_user_message(self) -> None:
        state_dir = self.root / "agentify-state"; state_dir.mkdir()
        (state_dir / "review-transport.json").write_text(json.dumps({"operations": {self.request["idempotency_key"]: {"status": "BLOCKED", "userMessageId": "user-1"}}}), encoding="utf-8")
        request_path = self.root / "logs/agentify/round/request-recovery.json"; receipt_path = self.root / "logs/agentify/round/receipt-recovery.json"; request_path.write_text(json.dumps(self.request), encoding="utf-8")
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), mock.patch.object(MODULE, "call_agentify", return_value=self.receipt) as call_agentify:
            MODULE.command_submit(SimpleNamespace(request=request_path, receipt=receipt_path, state_dir=state_dir, verify_existing=True))
        self.assertTrue(call_agentify.call_args.kwargs["verify_existing"]); self.assertTrue(receipt_path.exists())

    def test_archive_is_exact_and_never_overwrites_different_bytes(self) -> None:
        output = self.root / "docs/external-review/round/21_PRO_OPEN_RAW.md"
        MODULE._atomic_write_new(output, self.receipt["responseText"].encode("utf-8"))
        self.assertEqual(output.read_bytes(), b"STRICT_OK")
        MODULE._atomic_write_new(output, b"STRICT_OK")
        with self.assertRaisesRegex(MODULE.TransportError, "output_exists_with_different_bytes"):
            MODULE._atomic_write_new(output, b"DIFFERENT")

    def test_command_archive_validates_and_rereads_exact_bytes(self) -> None:
        request_path = self.root / "logs/agentify/round/request.json"
        receipt_path = self.root / "logs/agentify/round/receipt.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        raw_output = self.root / "docs/external-review/round/21_PRO_OPEN_RAW.md"
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root):
            MODULE.command_archive(
                SimpleNamespace(request=request_path, receipt=receipt_path, raw_output=raw_output)
            )
        self.assertEqual(raw_output.read_bytes(), self.receipt["responseText"].encode("utf-8"))

    def test_command_verify_returns_stable_operation_identity(self) -> None:
        request_path = self.root / "logs/agentify/round/request-verify.json"
        receipt_path = self.root / "logs/agentify/round/receipt-verify.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        output = io.StringIO()
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root):
            with contextlib.redirect_stdout(output):
                MODULE.command_verify(SimpleNamespace(request=request_path, receipt=receipt_path))
        self.assertIn("operation_id=operation-1", output.getvalue())
        self.assertIn(str(receipt_path.resolve()), output.getvalue())


if __name__ == "__main__":
    unittest.main()
