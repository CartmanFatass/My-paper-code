from __future__ import annotations

import contextlib
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


class FakeSubmitWorker:
    def __init__(self, polls: list[int | None], *, stderr: str = "") -> None:
        self.pid = 4242
        self._polls = list(polls)
        self._last: int | None = None
        self.returncode: int | None = None
        self.stderr = stderr
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        if self._polls:
            self._last = self._polls.pop(0)
        if self._last is not None:
            self.returncode = self._last
        return self._last

    def communicate(self) -> tuple[str, str]:
        return "", self.stderr

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = -15
        self._last = -15

    def wait(self, timeout: float | None = None) -> int:
        del timeout
        assert self.returncode is not None
        return self.returncode

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9
        self._last = -9


class AgentifyTransportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs/external-review/round").mkdir(parents=True)
        (self.root / "logs/agentify/round").mkdir(parents=True)
        self.prompt = "Assess whether the proposed estimator is identifiable."
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
            "first_binding": False,
            "idempotency_key": "round-abc-stage-1",
            "assignment_identity": "ROUND-ABC",
            "backend_selection_path": str(self.backend_selection_path),
            "prompt_path": str(self.prompt_path),
            "timeout_ms": 300000,
        }
        self.validated = MODULE.validate_request(self.request, repo_root=self.root)
        response = "STRICT_OK"
        self.receipt = {
            "operationId": "operation-1",
            "idempotencyKey": self.request["idempotency_key"],
            "stableKey": self.request["stable_key"],
            "provider": "chatgpt",
            "model": "Pro",
            "conversationUrl": self.request["conversation_url"],
            "conversationId": self.request["conversation_id"],
            "timeoutMs": 300000,
            "deadlineAt": 301000,
            "status": "COMPLETE",
            "terminalState": "NATURAL_COMPLETION_VERIFIED",
            "sendCount": 1,
            "sendActionCount": 1,
            "createdAt": 1000,
            "preparedAt": 1100,
            "modelEvidence": "Pro",
            "userMessageId": "user-1",
            "submittedAt": 1200,
            "assistantMessageId": "assistant-1",
            "responseText": response,
            "snapshots": [
                {"observedAt": 2000, "assistantMessageId": "assistant-1"},
                {"observedAt": 5000, "assistantMessageId": "assistant-1"},
            ],
            "controls": {"stop": False, "continue": False, "retry": False, "answerNow": True},
            "clickedControls": [],
            "completedAt": 5100,
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_live_agentify_state(self) -> Path:
        state_dir = self.root / "agentify-state"
        state_dir.mkdir(exist_ok=True)
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
        (state_dir / "token.txt").write_text("token", encoding="utf-8")
        return state_dir

    def _live_tab(self, **updates: object) -> dict[str, object]:
        tab: dict[str, object] = {
            "id": "tab-1",
            "key": self.request["stable_key"],
            "vendorId": self.request["provider"],
            "url": self.request["conversation_url"],
        }
        tab.update(updates)
        return tab

    def _idle_status(self, **updates: object) -> dict[str, object]:
        status: dict[str, object] = {
            "ok": True,
            "tabId": "tab-1",
            "blocked": False,
            "promptVisible": True,
            "tabs": [self._live_tab()],
            "activeQuery": None,
            "runtime": {"activeQueries": []},
        }
        status.update(updates)
        return status

    def test_complete_receipt_and_visible_answer_now_without_activation_pass(self) -> None:
        result = MODULE.validate_receipt(self.receipt, self.validated)
        self.assertEqual(result["assistantMessageId"], "assistant-1")

    def test_owner_key_prompt_and_conversation_are_bound(self) -> None:
        cases = [
            ("stable_key", "hmasd-independent-research-explorer-pro", "stable_key_owner_mismatch"),
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
        selection = json.loads(self.backend_selection_path.read_text(encoding="utf-8"))
        selection["assignment_identity"] = "ROUND-ABC"
        self.backend_selection_path.write_text(json.dumps(selection), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.TransportError, "request_field_set_mismatch"):
            MODULE.validate_request({**self.request, "extra": "forbidden"}, repo_root=self.root)

    def test_explorer_direct_owner_uses_explorer_stable_key_and_item_root(self) -> None:
        item = self.root / "local_research/pro_reviews/direction-1"
        item.mkdir(parents=True)
        prompt = item / "20_PRO_OPEN_QUESTION.md"
        prompt.write_text("Review the scientific mechanism and its strongest alternative explanation.\n", encoding="utf-8")
        selection = item / "TRANSPORT_BACKEND.json"
        selection.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "assignment_identity": "IR_DIRECTION_REVIEW:direction-1",
                    "transport_backend": "agentify",
                    "operation_key": "direction-1-operation",
                }
            ),
            encoding="utf-8",
        )
        request = {
            **self.request,
            "transport_owner": "independent_research_explorer",
            "stable_key": "hmasd-independent-research-explorer-pro",
            "assignment_identity": "IR_DIRECTION_REVIEW:direction-1",
            "idempotency_key": "direction-1-operation",
            "backend_selection_path": str(selection),
            "prompt_path": str(prompt),
        }
        validated = MODULE.validate_request(request, repo_root=self.root)
        self.assertEqual(validated["transport_owner"], "independent_research_explorer")
        self.assertEqual(validated["stable_key"], "hmasd-independent-research-explorer-pro")

    def test_uav_formal_key_is_cpm_owned(self) -> None:
        uav_request = dict(self.request)
        uav_request["stable_key"] = "hmasd-uav-formal-pro"
        validated = MODULE.validate_request(uav_request, repo_root=self.root)
        self.assertEqual(validated["stable_key"], "hmasd-uav-formal-pro")

        wrong_owner = dict(uav_request)
        wrong_owner["transport_owner"] = "independent_research_explorer"
        with self.assertRaisesRegex(MODULE.TransportError, "stable_key_owner_mismatch"):
            MODULE.validate_request(wrong_owner, repo_root=self.root)

    def test_backend_selection_is_restart_stable_and_agentify_only(self) -> None:
        selection = json.loads(self.backend_selection_path.read_text(encoding="utf-8"))
        selection["transport_backend"] = "browser"
        self.backend_selection_path.write_text(json.dumps(selection), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.TransportError, "backend_selection_mismatch"):
            MODULE.validate_request(self.request, repo_root=self.root)

    def test_prepare_command_writes_exact_restart_stable_pair_without_hash_gate(self) -> None:
        selection = self.root / "logs/agentify/frozen/TRANSPORT_BACKEND.json"
        request_path = self.root / "logs/agentify/frozen/REQUEST.json"
        prompt = self.root / "docs/external-review/round/frozen_question.md"
        prompt.write_text("Evaluate the scientific claim and identify the smallest separating test.", encoding="utf-8")
        args = SimpleNamespace(
            owner="code_project_manager",
            stable_key="hmasd-formal-pro",
            provider="chatgpt",
            model="Pro",
            conversation_url="https://chatgpt.com/c/conversation-1",
            conversation_id="conversation-1",
            first_binding=False,
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
        validated = MODULE.validate_request(prepared_request, repo_root=self.root)
        body = MODULE.agentify_body(validated, verify_existing=False)
        self.assertEqual(body["prompt"], prompt.read_text(encoding="utf-8"))
        self.assertNotIn(prepared_request["assignment_identity"], body["prompt"])

    def test_direction_provision_copies_exact_explorer_prompt_once(self) -> None:
        source = self.root / "local_research/frozen_direction_prompt.md"
        source.parent.mkdir(parents=True)
        identity = "IR_DIRECTION_REVIEW:direction-1"
        source_bytes = b"Review the frozen candidate's causal mechanism and alternatives.\n"
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

    def test_methodology_provision_accepts_only_methodology_review_prefix(self) -> None:
        source = self.root / "local_research/frozen_methodology_prompt.md"
        source.parent.mkdir(parents=True)
        source.write_text(
            "Review the methodology's assumptions, estimand, and strongest counterexample.\n",
            encoding="utf-8",
        )
        prompt = self.root / "local_research/pro_reviews/methodology-1/20_PRO_OPEN_QUESTION.md"
        args = SimpleNamespace(
            assignment_identity="IR_METHODOLOGY_REVIEW:methodology-1",
            prompt_path=prompt,
            prompt_source=source,
        )
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root):
            MODULE.command_provision_direction(args)
        self.assertEqual(prompt.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))

        args.assignment_identity = "IR_METHODOLOGY_REVIEWISH:methodology-1"
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root):
            with self.assertRaisesRegex(MODULE.TransportError, "direction_provision_identity_invalid"):
                MODULE.command_provision_direction(args)

    def test_prepare_parser_does_not_accept_operator_supplied_prompt_hash(self) -> None:
        help_text = MODULE.build_parser().format_help()
        self.assertIn("prepare", help_text)
        self.assertIn("provision-direction", help_text)
        prepare = MODULE.build_parser()._subparsers._group_actions[0].choices["prepare"]
        self.assertNotIn("--prompt-sha256", prepare.format_help())
        self.assertNotIn("--prompt-source", prepare.format_help())

    def test_prepare_first_binding_needs_no_preexisting_conversation_identity(self) -> None:
        item = self.root / "local_research/pro_reviews/first-binding"
        item.mkdir(parents=True)
        prompt = item / "20_PRO_OPEN_QUESTION.md"
        prompt.write_text("Assess the scientific mechanism.", encoding="utf-8")
        selection = item / "TRANSPORT_BACKEND.json"
        request_path = item / "REQUEST.json"
        args = SimpleNamespace(
            owner="independent_research_explorer",
            stable_key="hmasd-independent-research-explorer-pro",
            provider="chatgpt",
            model="Pro",
            conversation_url=None,
            conversation_id=None,
            first_binding=True,
            assignment_identity="IR_DIRECTION_REVIEW:first-binding",
            operation_key="first-binding-operation",
            prompt_path=prompt,
            timeout_ms=300000,
            selection=selection,
            request=request_path,
        )
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root):
            MODULE.command_prepare(args)
        request = json.loads(request_path.read_text(encoding="utf-8"))
        self.assertEqual(request["conversation_url"], "https://chatgpt.com/")
        self.assertEqual(request["conversation_id"], "__new__")
        self.assertTrue(request["first_binding"])

    def test_gemini_uses_same_request_contract_with_its_own_binding(self) -> None:
        item = self.root / "local_research/pro_reviews/gemini"
        item.mkdir(parents=True)
        prompt = item / "20_PRO_OPEN_QUESTION.md"
        prompt.write_text("Assess the scientific mechanism.", encoding="utf-8")
        selection = item / "TRANSPORT_BACKEND.json"
        selection.write_text(json.dumps({
            "schema_version": 1,
            "assignment_identity": "IR_DIRECTION_REVIEW:gemini",
            "transport_backend": "agentify",
            "operation_key": "gemini-operation",
        }), encoding="utf-8")
        request = {
            **self.request,
            "transport_owner": "independent_research_explorer",
            "stable_key": "hmasd-independent-research-explorer-gemini",
            "provider": "gemini",
            "model": "Gemini 2.5 Pro",
            "conversation_url": "https://gemini.google.com/app/gemini-review",
            "conversation_id": "gemini-review",
            "idempotency_key": "gemini-operation",
            "assignment_identity": "IR_DIRECTION_REVIEW:gemini",
            "backend_selection_path": str(selection),
            "prompt_path": str(prompt),
        }
        validated = MODULE.validate_request(request, repo_root=self.root)
        self.assertEqual(validated["provider"], "gemini")
        self.assertFalse(validated["first_binding"])

    def test_receipt_rejects_wrong_send_identity_completion_and_control_state(self) -> None:
        mutations = [
            ("sendCount", 2, "receipt_sendCount_mismatch"),
            ("assistantMessageId", "user-1", "receipt_message_identity_collision"),
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
        self.assertEqual(MODULE.validate_receipt(receipt, self.validated)["responseText"], receipt["responseText"])

    def test_transport_records_have_no_workflow_hash_admission_fields(self) -> None:
        for record in (self.request, self.receipt):
            forbidden = [
                key
                for key in record
                if any(token in key.lower() for token in ("hash", "digest", "fingerprint", "byte"))
            ]
            self.assertEqual(forbidden, [])

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

    def test_call_agentify_reuses_exact_preexisting_idle_tab_without_page_mutation(self) -> None:
        state_dir = self._write_live_agentify_state()
        health = {
            "ok": True,
            "serverId": "server-1",
            "sourceCommit": MODULE.AGENTIFY_REQUIRED_COMMIT,
            "sourceDirty": False,
        }
        calls: list[tuple[str, dict[str, object] | None]] = []

        def fake_http(
            url: str,
            *,
            token: str | None = None,
            body: dict[str, object] | None = None,
            timeout_seconds: float = 10.0,
        ) -> dict[str, object]:
            del timeout_seconds
            calls.append((url, body))
            if url.endswith("/health"):
                self.assertIsNone(token)
                return health
            self.assertEqual(token, "token")
            if url.endswith("/tabs"):
                return {"ok": True, "tabs": [self._live_tab()]}
            if "/status?" in url:
                self.assertIn("tabId=tab-1", url)
                return self._idle_status()
            if url.endswith("/review-query"):
                self.assertEqual(body["stableKey"], self.request["stable_key"])
                return {"ok": True, "receipt": self.receipt}
            self.fail(f"unexpected Agentify endpoint: {url}")

        with mock.patch.object(MODULE, "_http_json", side_effect=fake_http):
            result = MODULE.call_agentify(self.validated, state_dir=state_dir, verify_existing=False)
        self.assertEqual(result, self.receipt)
        urls = [url for url, _ in calls]
        self.assertEqual(len(urls), 4)
        self.assertFalse(any("/tabs/create" in url or "/tabs/close" in url or "/navigate" in url for url in urls))
        self.assertTrue(urls[-1].endswith("/review-query"))

    def test_preexisting_tab_inventory_failures_never_reach_review_query(self) -> None:
        cases = [
            ([], "agentify_preexisting_tab_missing"),
            ([self._live_tab(), self._live_tab(id="tab-2")], "agentify_preexisting_tab_ambiguous"),
            ([self._live_tab(url="https://chatgpt.com/c/other")], "agentify_preexisting_tab_identity_mismatch"),
            ([self._live_tab(vendorId="gemini")], "agentify_preexisting_tab_identity_mismatch"),
        ]
        for tabs, error in cases:
            with self.subTest(error=error), mock.patch.object(
                MODULE, "_http_json", return_value={"ok": True, "tabs": tabs}
            ) as http_json, self.assertRaisesRegex(MODULE.TransportError, error):
                MODULE._require_preexisting_review_tab(
                    "http://127.0.0.1:43111",
                    "token",
                    self.validated,
                    state_dir=self.root / "agentify-state",
                )
            http_json.assert_called_once_with(
                "http://127.0.0.1:43111/tabs", token="token", timeout_seconds=10.0
            )

    def test_tab_creation_is_limited_to_first_binding_or_post_restart_recovery(self) -> None:
        state_dir = self.root / "agentify-state"
        state_dir.mkdir()

        def run_creation(*, restart_binding: bool) -> list[tuple[str, dict[str, object] | None]]:
            if restart_binding:
                (state_dir / "review-transport.json").write_text(
                    json.dumps(
                        {
                            "bindings": {self.request["stable_key"]: {"conversationId": self.request["conversation_id"]}},
                            "operations": {self.request["idempotency_key"]: {"status": "BLOCKED"}},
                        }
                    ),
                    encoding="utf-8",
                )
            calls: list[tuple[str, dict[str, object] | None]] = []

            def fake_http(
                url: str,
                *,
                token: str | None = None,
                body: dict[str, object] | None = None,
                timeout_seconds: float = 10.0,
            ) -> dict[str, object]:
                del token, timeout_seconds
                calls.append((url, body))
                if url.endswith("/tabs") and body is None:
                    return {"ok": True, "tabs": [] if len(calls) == 1 else [self._live_tab()]}
                if url.endswith("/tabs/create"):
                    return {"ok": True, "tab": self._live_tab()}
                if "/status?" in url:
                    return self._idle_status()
                self.fail(f"unexpected Agentify endpoint: {url}")

            with mock.patch.object(MODULE, "_http_json", side_effect=fake_http):
                MODULE._require_preexisting_review_tab(
                    "http://127.0.0.1:43111",
                    "token",
                    self.validated,
                    allow_tab_creation=True,
                    state_dir=state_dir,
                )
            self.assertEqual(sum(url.endswith("/tabs/create") for url, _ in calls), 1)
            return calls

        run_creation(restart_binding=False)
        run_creation(restart_binding=True)

        with mock.patch.object(
            MODULE,
            "_http_json",
            return_value={"ok": True, "tabs": []},
        ) as http_json, self.assertRaisesRegex(MODULE.TransportError, "agentify_preexisting_tab_missing"):
            MODULE._require_preexisting_review_tab(
                "http://127.0.0.1:43111",
                "token",
                self.validated,
                state_dir=state_dir,
            )
        http_json.assert_called_once()

    def test_command_submit_reaches_first_binding_tab_creation_exception(self) -> None:
        state_dir = self.root / "agentify-state"
        state_dir.mkdir()
        request_path = self.root / "logs/agentify/round/request-first-binding.json"
        receipt_path = self.root / "logs/agentify/round/receipt-first-binding.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        worker = FakeSubmitWorker([0])
        args = SimpleNamespace(
            request=request_path,
            receipt=receipt_path,
            state_dir=state_dir,
            verify_existing=False,
            allow_tab_creation=True,
        )
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(
                 MODULE,
                 "_ledger_operation",
                 side_effect=[{}, self._confirmed_operation()],
             ), \
             mock.patch.object(MODULE, "_agentify_session", return_value=("base", "token", "tab-1")) as session, \
             mock.patch.object(MODULE, "_spawn_submit_worker", return_value=worker) as spawn:
            MODULE.command_submit(args)
        session.assert_called_once_with(
            self.validated,
            state_dir,
            allow_tab_creation=True,
        )
        spawn.assert_called_once_with(args, False)

    def test_command_submit_reaches_post_restart_tab_creation_with_existing_identity(self) -> None:
        state_dir = self.root / "agentify-state"
        state_dir.mkdir()
        (state_dir / "review-transport.json").write_text(
            json.dumps(
                {
                    "bindings": {self.request["stable_key"]: {"conversationId": self.request["conversation_id"]}},
                    "operations": {self.request["idempotency_key"]: {"status": "COMPLETE", "userMessageId": "user-1"}},
                }
            ),
            encoding="utf-8",
        )
        request_path = self.root / "logs/agentify/round/request-post-restart.json"
        receipt_path = self.root / "logs/agentify/round/receipt-post-restart.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        operation = self._confirmed_operation(status="COMPLETE")
        args = SimpleNamespace(
            request=request_path,
            receipt=receipt_path,
            state_dir=state_dir,
            verify_existing=False,
            allow_tab_creation=True,
        )
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(MODULE, "_ledger_operation", return_value=operation), \
             mock.patch.object(MODULE, "_agentify_session", return_value=("base", "token", "tab-1")) as session, \
             mock.patch.object(MODULE, "_complete_from_existing", return_value=self.receipt) as complete:
            MODULE.command_submit(args)
        session.assert_called_once_with(
            self.validated,
            state_dir,
            require_send_ready=False,
            allow_tab_creation=True,
        )
        complete.assert_called_once_with(self.validated, state_dir, receipt_path)

    def test_command_submit_denies_ordinary_missing_tab_without_exception_flag(self) -> None:
        state_dir = self.root / "agentify-state"
        state_dir.mkdir()
        request_path = self.root / "logs/agentify/round/request-missing-tab.json"
        receipt_path = self.root / "logs/agentify/round/receipt-missing-tab.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        args = SimpleNamespace(
            request=request_path,
            receipt=receipt_path,
            state_dir=state_dir,
            verify_existing=False,
            allow_tab_creation=False,
        )
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(MODULE, "_ledger_operation", return_value={}), \
             mock.patch.object(
                 MODULE,
                 "_agentify_session",
                 side_effect=MODULE.TransportError("agentify_preexisting_tab_missing"),
             ) as session, \
             mock.patch.object(MODULE, "_spawn_submit_worker") as spawn, \
             self.assertRaisesRegex(MODULE.TransportError, "agentify_preexisting_tab_missing"):
            MODULE.command_submit(args)
        session.assert_called_once_with(
            self.validated,
            state_dir,
            allow_tab_creation=False,
        )
        spawn.assert_not_called()

    def test_preexisting_tab_status_change_or_busy_state_fails_closed(self) -> None:
        stale = self._idle_status(tabs=[self._live_tab(url="https://chatgpt.com/c/other")])
        blocked = self._idle_status(blocked=True)
        busy_direct = self._idle_status(activeQuery={"tabId": "tab-1"})
        busy_runtime = self._idle_status(
            runtime={"activeQueries": [{"tabId": "other", "scope": f"key:{self.request['stable_key']}"}]}
        )
        for status, error in [
            (stale, "agentify_preexisting_tab_status_identity_mismatch"),
            (blocked, "agentify_preexisting_tab_status_invalid"),
            (busy_direct, "agentify_preexisting_tab_busy"),
            (busy_runtime, "agentify_preexisting_tab_busy"),
        ]:
            with self.subTest(error=error), mock.patch.object(
                MODULE,
                "_http_json",
                side_effect=[{"ok": True, "tabs": [self._live_tab()]}, status],
            ) as http_json, self.assertRaisesRegex(MODULE.TransportError, error):
                MODULE._require_preexisting_review_tab(
                    "http://127.0.0.1:43111",
                    "token",
                    self.validated,
                    state_dir=self.root / "agentify-state",
                )
            self.assertEqual(http_json.call_count, 2)

    def test_call_agentify_blocked_tab_fails_before_review_query(self) -> None:
        state_dir = self._write_live_agentify_state()
        health = {
            "ok": True,
            "serverId": "server-1",
            "sourceCommit": MODULE.AGENTIFY_REQUIRED_COMMIT,
            "sourceDirty": False,
        }
        calls: list[str] = []

        def fake_http(
            url: str,
            *,
            token: str | None = None,
            body: dict[str, object] | None = None,
            timeout_seconds: float = 10.0,
        ) -> dict[str, object]:
            del body, timeout_seconds
            calls.append(url)
            if url.endswith("/health"):
                self.assertIsNone(token)
                return health
            self.assertEqual(token, "token")
            if url.endswith("/tabs"):
                return {"ok": True, "tabs": [self._live_tab()]}
            if "/status?" in url:
                return self._idle_status(blocked=True)
            self.fail(f"blocked tab reached forbidden endpoint: {url}")

        with mock.patch.object(MODULE, "_http_json", side_effect=fake_http), self.assertRaisesRegex(
            MODULE.TransportError, "agentify_preexisting_tab_status_invalid"
        ):
            MODULE.call_agentify(self.validated, state_dir=state_dir, verify_existing=False)
        self.assertEqual(len(calls), 3)
        self.assertFalse(any(url.endswith("/review-query") for url in calls))

    def test_prompt_invisible_fails_before_review_query(self) -> None:
        with mock.patch.object(
            MODULE,
            "_http_json",
            side_effect=[
                {"ok": True, "tabs": [self._live_tab()]},
                self._idle_status(promptVisible=False),
            ],
        ) as http_json, self.assertRaisesRegex(
            MODULE.TransportError, "agentify_preexisting_tab_prompt_unavailable"
        ):
            MODULE._require_preexisting_review_tab(
                "http://127.0.0.1:43111",
                "token",
                self.validated,
                state_dir=self.root / "agentify-state",
            )
        self.assertEqual(http_json.call_count, 2)

    def test_verify_existing_present_false_is_observe_only_before_fresh_key(self) -> None:
        request_path = self.root / "logs/agentify/round/request-verify-existing.json"
        receipt_path = self.root / "logs/agentify/round/receipt-verify-existing.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        output = io.StringIO()
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(MODULE, "_spawn_submit_worker") as spawn, \
             contextlib.redirect_stdout(output):
            MODULE.command_submit(
                SimpleNamespace(
                    request=request_path,
                    receipt=receipt_path,
                    state_dir=self.root / "missing-agentify-state",
                    verify_existing=True,
                )
            )
        self.assertIn("HMASD_AGENTIFY_EXISTING_USER_MESSAGE present=false", output.getvalue())
        spawn.assert_not_called()

    def _confirmed_operation(self, **updates: object) -> dict[str, object]:
        operation: dict[str, object] = {
            "status": "RUNNING",
            "sendCount": 1,
            "sendActionCount": 1,
            "userMessageId": "user-1",
            "submittedAt": 1200,
            "stableKey": self.request["stable_key"],
            "provider": self.request["provider"],
            "conversationUrl": self.request["conversation_url"],
            "conversationId": self.request["conversation_id"],
            "tabId": "tab-1",
        }
        operation.update(updates)
        return operation

    def test_submit_stall_without_confirmed_message_terminates_owned_worker(self) -> None:
        state_dir = self.root / "agentify-state"; state_dir.mkdir()
        request_path = self.root / "logs/agentify/round/request-stall.json"
        receipt_path = self.root / "logs/agentify/round/receipt-stall.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        worker = FakeSubmitWorker([None, None, None])
        clock = iter([0.0, 1.0, 62.0])
        output = io.StringIO()
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(MODULE, "_agentify_session", return_value=("base", "token", "tab-1")), \
             mock.patch.object(MODULE, "_spawn_submit_worker", return_value=worker), \
             mock.patch.object(MODULE, "_ledger_operation", return_value={"status": "SEND_INTENT", "sendCount": 0}), \
             mock.patch.object(MODULE.time, "monotonic", side_effect=lambda: next(clock)), \
             mock.patch.object(MODULE.time, "sleep"), \
             contextlib.redirect_stdout(output), \
             self.assertRaisesRegex(MODULE.TransportError, "pre_send_blocked_existing_operation_unconfirmed"):
            MODULE.command_submit(SimpleNamespace(request=request_path, receipt=receipt_path, state_dir=state_dir, verify_existing=False))
        self.assertFalse(worker.terminated)
        self.assertFalse(worker.killed)
        self.assertIn('"phase": "PRE_SEND_BLOCKED"', output.getvalue())
        self.assertFalse(receipt_path.exists())

    def test_unreadable_existing_ledger_blocks_before_worker_spawn(self) -> None:
        state_dir = self.root / "agentify-state"
        state_dir.mkdir()
        (state_dir / "review-transport.json").write_text("{not-json", encoding="utf-8")
        request_path = self.root / "logs/agentify/round/request-unreadable.json"
        receipt_path = self.root / "logs/agentify/round/receipt-unreadable.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(MODULE, "_spawn_submit_worker") as spawn, \
             self.assertRaisesRegex(MODULE.TransportError, "unreadable_json"):
            MODULE.command_submit(
                SimpleNamespace(
                    request=request_path,
                    receipt=receipt_path,
                    state_dir=state_dir,
                    verify_existing=False,
                )
            )
        spawn.assert_not_called()

    def test_deadline_termination_rereads_late_confirmation_without_resend(self) -> None:
        state_dir = self.root / "agentify-state"
        state_dir.mkdir()
        request_path = self.root / "logs/agentify/round/request-race.json"
        receipt_path = self.root / "logs/agentify/round/receipt-race.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        worker = FakeSubmitWorker([None])
        operations = iter(
            [
                {},
                {"status": "SEND_INTENT", "sendCount": 0},
                {"status": "SEND_INTENT", "sendCount": 0},
                self._confirmed_operation(),
                self._confirmed_operation(),
                self._confirmed_operation(status="COMPLETE"),
            ]
        )
        output = io.StringIO()
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(MODULE, "_agentify_session", return_value=("base", "token", "tab-1")), \
             mock.patch.object(MODULE, "_spawn_submit_worker", return_value=worker) as spawn, \
             mock.patch.object(MODULE, "_ledger_operation", side_effect=lambda *_: next(operations)), \
             mock.patch.object(MODULE, "_complete_from_existing", return_value=self.receipt) as complete, \
             mock.patch.object(MODULE.time, "monotonic", side_effect=[0.0, 1.0, 62.0, 63.0]), \
             mock.patch.object(MODULE.time, "sleep"), \
             contextlib.redirect_stdout(output):
            MODULE.command_submit(
                SimpleNamespace(
                    request=request_path,
                    receipt=receipt_path,
                    state_dir=state_dir,
                    verify_existing=False,
                )
            )
        spawn.assert_called_once()
        complete.assert_called_once_with(self.validated, state_dir, receipt_path)
        self.assertTrue(worker.terminated)
        self.assertNotIn('"phase": "PRE_SEND_BLOCKED"', output.getvalue())
        self.assertIn('"phase": "MESSAGE_CONFIRMED"', output.getvalue())

    def test_partial_user_message_is_post_send_and_worker_is_not_terminated(self) -> None:
        state_dir = self.root / "agentify-state"
        state_dir.mkdir()
        request_path = self.root / "logs/agentify/round/request-partial.json"
        receipt_path = self.root / "logs/agentify/round/receipt-partial.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        worker = FakeSubmitWorker([None])
        partial = self._confirmed_operation(conversationId="wrong-conversation")
        operations = iter([{}, partial])
        output = io.StringIO()
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(MODULE, "_agentify_session", return_value=("base", "token", "tab-1")), \
             mock.patch.object(MODULE, "_spawn_submit_worker", return_value=worker), \
             mock.patch.object(MODULE, "_ledger_operation", side_effect=lambda *_: next(operations)), \
             mock.patch.object(MODULE.time, "monotonic", side_effect=[0.0, 1.0, 2.0]), \
             contextlib.redirect_stdout(output), \
             self.assertRaisesRegex(MODULE.TransportError, "post_send_blocked_partial_message_identity"):
            MODULE.command_submit(
                SimpleNamespace(
                    request=request_path,
                    receipt=receipt_path,
                    state_dir=state_dir,
                    verify_existing=False,
                )
            )
        self.assertFalse(worker.terminated)
        self.assertIn('"phase": "POST_SEND_BLOCKED"', output.getvalue())
        self.assertNotIn('"phase": "PRE_SEND_BLOCKED"', output.getvalue())

    def test_early_worker_exit_waits_for_delayed_message_confirmation(self) -> None:
        state_dir = self.root / "agentify-state"
        state_dir.mkdir()
        request_path = self.root / "logs/agentify/round/request-delayed.json"
        receipt_path = self.root / "logs/agentify/round/receipt-delayed.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        worker = FakeSubmitWorker([1], stderr="client exited")
        operations = iter(
            [
                {},
                {},
                self._confirmed_operation(),
                self._confirmed_operation(status="COMPLETE"),
            ]
        )
        output = io.StringIO()
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(MODULE, "_agentify_session", return_value=("base", "token", "tab-1")), \
             mock.patch.object(MODULE, "_spawn_submit_worker", return_value=worker) as spawn, \
             mock.patch.object(MODULE, "_ledger_operation", side_effect=lambda *_: next(operations)), \
             mock.patch.object(MODULE, "_complete_from_existing", return_value=self.receipt) as complete, \
             mock.patch.object(MODULE.time, "monotonic", side_effect=[0.0, 1.0, 2.0, 3.0]), \
             mock.patch.object(MODULE.time, "sleep"), \
             contextlib.redirect_stdout(output):
            MODULE.command_submit(
                SimpleNamespace(
                    request=request_path,
                    receipt=receipt_path,
                    state_dir=state_dir,
                    verify_existing=False,
                )
            )
        spawn.assert_called_once()
        complete.assert_called_once_with(self.validated, state_dir, receipt_path)
        self.assertFalse(worker.terminated)
        self.assertIn('"phase": "MESSAGE_CONFIRMED"', output.getvalue())
        self.assertNotIn('"phase": "PRE_SEND_BLOCKED"', output.getvalue())

    def test_existing_message_uses_independent_live_tab_identity(self) -> None:
        state_dir = self.root / "agentify-state"
        state_dir.mkdir()
        request_path = self.root / "logs/agentify/round/request-tab-mismatch.json"
        receipt_path = self.root / "logs/agentify/round/receipt-tab-mismatch.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        for ledger_tab in (None, "stale-tab"):
            with self.subTest(ledger_tab=ledger_tab):
                operation = self._confirmed_operation(tabId=ledger_tab)
                with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
                     mock.patch.object(MODULE, "_agentify_session", return_value=("base", "token", "live-tab")), \
                     mock.patch.object(MODULE, "_ledger_operation", return_value=operation), \
                     mock.patch.object(MODULE, "_spawn_submit_worker") as spawn, \
                     self.assertRaisesRegex(MODULE.TransportError, "post_send_blocked_ledger_identity_unconfirmed"):
                    MODULE.command_submit(
                        SimpleNamespace(
                            request=request_path,
                            receipt=receipt_path,
                            state_dir=state_dir,
                            verify_existing=True,
                        )
                    )
                spawn.assert_not_called()

    def test_submit_reports_early_confirmation_then_long_generation(self) -> None:
        state_dir = self.root / "agentify-state"; state_dir.mkdir()
        request_path = self.root / "logs/agentify/round/request-success.json"
        receipt_path = self.root / "logs/agentify/round/receipt-success.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        worker = FakeSubmitWorker([None, None, 0])
        clock = iter([0.0, 1.0, 2.0, 303.0])
        output = io.StringIO()
        operations = iter([
            {},
            self._confirmed_operation(),
            self._confirmed_operation(),
            self._confirmed_operation(),
        ])
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(MODULE, "_agentify_session", return_value=("base", "token", "tab-1")), \
             mock.patch.object(MODULE, "_spawn_submit_worker", return_value=worker), \
             mock.patch.object(MODULE, "_ledger_operation", side_effect=lambda *_: next(operations)), \
             mock.patch.object(MODULE.time, "monotonic", side_effect=lambda: next(clock)), \
             mock.patch.object(MODULE.time, "sleep"), \
             contextlib.redirect_stdout(output):
            MODULE.command_submit(SimpleNamespace(request=request_path, receipt=receipt_path, state_dir=state_dir, verify_existing=False))
        phases = output.getvalue()
        self.assertIn('"phase": "MESSAGE_CONFIRMED"', phases)
        self.assertGreaterEqual(phases.count('"phase": "GENERATING"'), 2)
        self.assertIn('"phase": "STABLE_COMPLETE"', phases)
        self.assertFalse(worker.terminated)

    def test_worker_failure_after_message_confirmation_observes_same_operation(self) -> None:
        state_dir = self.root / "agentify-state"; state_dir.mkdir()
        request_path = self.root / "logs/agentify/round/request-interrupted.json"
        receipt_path = self.root / "logs/agentify/round/receipt-interrupted.json"
        request_path.write_text(json.dumps(self.request), encoding="utf-8")
        worker = FakeSubmitWorker([None, 1], stderr="client interrupted")
        operations = iter([
            {},
            self._confirmed_operation(),
            self._confirmed_operation(),
            self._confirmed_operation(status="COMPLETE"),
        ])
        output = io.StringIO()
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(MODULE, "_agentify_session", return_value=("base", "token", "tab-1")), \
             mock.patch.object(MODULE, "_spawn_submit_worker", return_value=worker) as spawn, \
             mock.patch.object(MODULE, "_ledger_operation", side_effect=lambda *_: next(operations)), \
             mock.patch.object(MODULE, "_complete_from_existing", return_value=self.receipt) as complete, \
             mock.patch.object(MODULE.time, "monotonic", side_effect=[0.0, 1.0, 2.0, 3.0]), \
             mock.patch.object(MODULE.time, "sleep"), \
             contextlib.redirect_stdout(output):
            MODULE.command_submit(SimpleNamespace(request=request_path, receipt=receipt_path, state_dir=state_dir, verify_existing=False))
        spawn.assert_called_once()
        complete.assert_called_once_with(self.validated, state_dir, receipt_path)
        self.assertFalse(worker.terminated)
        self.assertIn('"phase": "STABLE_COMPLETE"', output.getvalue())

    def test_recovery_refuses_resend_when_failed_operation_has_user_message(self) -> None:
        state_dir = self.root / "agentify-state"; state_dir.mkdir()
        (state_dir / "review-transport.json").write_text(json.dumps({"operations": {self.request["idempotency_key"]: {"status": "BLOCKED", "userMessageId": "user-1"}}}), encoding="utf-8")
        request_path = self.root / "logs/agentify/round/request-recovery.json"; receipt_path = self.root / "logs/agentify/round/receipt-recovery.json"; request_path.write_text(json.dumps(self.request), encoding="utf-8")
        with mock.patch.object(MODULE, "_repo_root", return_value=self.root), \
             mock.patch.object(MODULE, "_agentify_session", return_value=("base", "token", "tab-1")), \
             mock.patch.object(MODULE, "_spawn_submit_worker") as spawn, \
             mock.patch.object(MODULE, "_ledger_operation", return_value=self._confirmed_operation(status="COMPLETE")), \
             mock.patch.object(MODULE, "_complete_from_existing", return_value=self.receipt) as complete:
            MODULE.command_submit(SimpleNamespace(request=request_path, receipt=receipt_path, state_dir=state_dir, verify_existing=True))
        spawn.assert_not_called()
        complete.assert_called_once_with(self.validated, state_dir, receipt_path)

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
