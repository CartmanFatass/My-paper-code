from __future__ import annotations

import importlib.util
import json
import sys
from argparse import Namespace
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / ".agents" / "skills" / "hmasd-chatgpt-pro-transport" / "scripts"
for path in (ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import transport_contract as contract  # noqa: E402


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TRANSPORT_VALIDATE = _load("transport_validate", SCRIPT_DIR / "validate_request.py")
MATERIALIZE = _load("transport_materialize", SCRIPT_DIR / "materialize_packet.py")
BIND = _load("transport_bind", SCRIPT_DIR / "bind_conversation.py")
TRANSPORT_SKILL = ROOT / ".agents" / "skills" / "hmasd-chatgpt-pro-transport" / "SKILL.md"
OUTSOURCE_SKILL = ROOT / ".agents" / "skills" / "hmasd-workflow-outsource" / "SKILL.md"
SINGLETON_THREAD_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    direction = tmp_path / "docs" / "research" / "candidates" / "demo_direction"
    portfolio = tmp_path / "docs" / "research" / "portfolio"
    direction.mkdir(parents=True)
    portfolio.mkdir(parents=True)
    (direction / "DIRECTION.md").write_text("# Demo\n", encoding="utf-8")
    (portfolio / "PORTFOLIO.md").write_text("| demo_direction | ACTIVE |\n", encoding="utf-8")
    codex = tmp_path / ".codex"
    codex.mkdir()
    (codex / "hmasd-transport.toml").write_text(
        "\n".join(
            (
                "schema_version = 1",
                'mode = "singleton"',
                'status = "active"',
                f'thread_id = "{SINGLETON_THREAD_ID}"',
                'environment = "local"',
                'model = "gpt-5.6-luna"',
                'reasoning_effort = "xhigh"',
                "",
            )
        ),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def upload_request(tmp_path: Path) -> dict[str, object]:
    prompt = tmp_path / "PROMPT_BODY.md"
    reference = tmp_path / "REFERENCE_FILES.md"
    prompt.write_bytes("exact prompt bytes\r\n".encode("utf-8"))
    reference.write_bytes("exact reference bytes\n".encode("utf-8"))
    return {
        "request_id": "req-transport-01",
        "direction_id": "demo_direction",
        "prompt_path": str(prompt.resolve()),
        "reference_paths": [str(reference.resolve())],
        "source_thread_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "parent_thread_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "companion_prompt": "Execute the canonical packet exactly once.",
    }


def test_packet_names_are_stable_and_attempts_are_isolated() -> None:
    first = contract.packet_artifacts("req/unsafe", "direction", ["REFERENCE_FILES.md"], attempt=1)
    retry = contract.packet_artifacts("req/unsafe", "direction", ["REFERENCE_FILES.md"], attempt=2)

    assert first["packet_id"] == "req-unsafe--direction"
    assert first["body_filename"] == "req-unsafe--direction__00_PROMPT.md"
    assert first["reference_filenames"][0]["canonical_filename"].endswith(
        "__01_REF_001_REFERENCE_FILES.md"
    )
    assert first["packet_id"] == retry["packet_id"]
    assert first["archive_id"] != retry["archive_id"]
    assert first["response_filename"] != retry["response_filename"]


def test_materialize_preserves_bytes_and_binds_one_manifest(
    project_root: Path, upload_request: dict[str, object], tmp_path: Path
) -> None:
    out_dir = tmp_path / "packet"
    manifest = MATERIALIZE.materialize(
        upload_request,
        project_root=project_root,
        out_dir=out_dir,
    )

    assert manifest["canonical_form"] == "logical_packet_manifest"
    assert manifest["reference_order_is_authoritative"] is True
    body_path = Path(manifest["body"]["materialized_path"])
    reference_path = Path(manifest["references"][0]["materialized_path"])
    assert body_path.read_bytes() == Path(str(upload_request["prompt_path"])).read_bytes()
    assert reference_path.read_bytes() == Path(str(upload_request["reference_paths"][0])).read_bytes()
    manifest_path = Path(manifest["manifest_path"])
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["packet_id"] == manifest["packet_id"]
    assert manifest["materialized_hashes"]["body"] == contract.materialized_file_sha256(body_path)


def test_materialize_is_idempotent_and_refuses_conflicting_overwrite(
    project_root: Path, upload_request: dict[str, object], tmp_path: Path
) -> None:
    out_dir = tmp_path / "packet"
    MATERIALIZE.materialize(upload_request, project_root=project_root, out_dir=out_dir)
    MATERIALIZE.materialize(upload_request, project_root=project_root, out_dir=out_dir)
    prompt_path = next(out_dir.glob("*__00_PROMPT.md"))
    prompt_path.write_bytes(b"different")

    with pytest.raises(ValueError, match="packet artifact conflict"):
        MATERIALIZE.materialize(upload_request, project_root=project_root, out_dir=out_dir)


def _record() -> dict[str, object]:
    return {
        "request_id": "req-1",
        "direction_id": "demo_direction",
        "conversation_id": "6a95b06d-0104-83e8-9493-f59f26b61c82",
        "provider_url": "https://chatgpt.com/c/6a95b06d-0104-83e8-9493-f59f26b61c82",
        "state": "SEND_CONFIRMED",
        "source_thread_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "parent_thread_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "tab_id": "17",
        "tab_lease": {"handle": "17", "lifecycle": "OPEN", "origin": "agent", "reusable": True},
    }


def test_waiting_state_keeps_tab_active_and_monitor_ignores_tab_identity() -> None:
    record = _record()
    contract.transition_record(record, "WAITING_GENERATION", now="2026-08-31T00:00:00Z")
    contract.observe_monitor(
        record,
        observed_url=record["provider_url"],
        tab_handle="17",
        observed_state="Pro thinking",
        cursor="c1",
        now="2026-08-31T00:15:00Z",
    )

    assert record["tab_lifecycle"] == "OPEN"
    assert record["tab_lease"]["lifecycle"] == "OPEN"
    assert record["monitor"]["identity_key"] == contract.monitor_identity_key(record)
    assert "17" not in record["monitor"]["identity_key"]
    with pytest.raises(ValueError, match="MONITOR_IDENTITY_MISMATCH"):
        contract.observe_monitor(
            record,
            observed_url="https://chatgpt.com/c/wrong",
            tab_handle="17",
            observed_state="unknown",
        )


def test_tab_cannot_close_before_archive_and_receipt_staging() -> None:
    record = _record()
    contract.transition_record(record, "WAITING_GENERATION")
    with pytest.raises(ValueError, match="ARCHIVED"):
        contract.close_tab_lease(record, reason="executor turn ended")

    contract.transition_record(record, "NATURAL_COMPLETION")
    contract.transition_record(record, "ARCHIVE_PENDING")
    contract.transition_record(record, "ARCHIVED")
    with pytest.raises(ValueError, match="staged or explicitly blocked completion receipt"):
        contract.close_tab_lease(record, reason="archive complete")

    contract.stage_receipt(
        record,
        {"response_file": "response.md", "transport_fact_file": "facts.json"},
        "a" * 64,
        now="2026-08-31T00:30:00Z",
    )
    contract.close_tab_lease(record, reason="natural completion", now="2026-08-31T00:31:00Z")
    assert record["tab_id"] is None
    assert record["tab_lifecycle"] == "CLOSED"


def test_receipt_outbox_is_deterministic_and_uncertain_is_not_retryable() -> None:
    record = _record()
    record["state"] = "ARCHIVED"
    contract.stage_receipt(record, {"response_file": "response.md"}, "b" * 64)
    key = record["return_receipt"]["message_key"]
    assert key == contract.receipt_message_key("req-1", "demo_direction", record["conversation_id"], "b" * 64)
    assert record["return_receipt"]["status"] == "PENDING"
    assert record["return_receipt"]["routing_mode"] == "PARENT_SESSION"
    assert record["return_receipt"]["destination_thread_id"] == record["parent_thread_id"]
    assert record["return_receipt"]["fallback_enabled"] is False
    contract.record_receipt_result(record, "UNCERTAIN", delivery_status="timeout", error="unknown")
    assert record["return_receipt"]["status"] == "UNCERTAIN"
    assert record["return_receipt"]["retry_allowed"] is False
    assert record["return_receipt"]["attempt_count"] == 1


def test_missing_parent_blocks_completion_receipt_without_a_destination() -> None:
    record = _record()
    record["state"] = "ARCHIVED"
    record["parent_thread_id"] = None
    record["fallback_enabled"] = True
    record["fallback_thread_id"] = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    record["return_receipt"] = {
        "status": "PENDING",
        "attempt_count": 0,
        "message_key": "legacy-unsent-key",
        "routing_mode": "FIXED_FALLBACK",
        "fallback_enabled": True,
        "fallback_thread_id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
    }
    contract.stage_receipt(record, {"response_file": "response.md"}, "c" * 64)
    receipt = record["return_receipt"]
    assert receipt["required"] is False
    assert receipt["status"] == "BLOCKED"
    assert receipt["receipt_state"] == "RETURN_RECEIPT_BLOCKED"
    assert receipt["routing_mode"] == "PARENT_SESSION"
    assert receipt["fallback_enabled"] is False
    assert receipt["parent_thread_id"] is None
    assert receipt["destination_thread_id"] is None
    assert receipt.get("message_key") is None
    assert "fallback_thread_id" not in receipt
    assert "fallback_thread_id" not in record
    assert record["state"] == "ARCHIVED"
    contract.close_tab_lease(record, reason="archive complete; receipt unavailable")
    assert record["tab_lifecycle"] == "CLOSED"


def test_unattempted_legacy_pending_receipt_migrates_to_parent() -> None:
    record = _record()
    record["state"] = "ARCHIVED"
    response_sha256 = "d" * 64
    key = contract.receipt_message_key(
        str(record["request_id"]),
        str(record["direction_id"]),
        str(record["conversation_id"]),
        response_sha256,
    )
    record["return_receipt"] = {
        "required": True,
        "source_thread_id": record["source_thread_id"],
        "parent_thread_id": record["parent_thread_id"],
        "destination_thread_id": record["source_thread_id"],
        "status": "PENDING",
        "attempt_count": 0,
        "message_key": key,
        "routing_mode": "FIXED_FALLBACK",
        "fallback_enabled": True,
        "fallback_thread_id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
    }

    contract.stage_receipt(record, {"response_file": "response.md"}, response_sha256)

    receipt = record["return_receipt"]
    assert receipt["message_key"] == key
    assert receipt["destination_thread_id"] == record["parent_thread_id"]
    assert receipt["routing_mode"] == "PARENT_SESSION"
    assert receipt["fallback_enabled"] is False
    assert "fallback_thread_id" not in receipt


def test_any_legacy_delivery_evidence_preserves_mixed_fallback_receipt_without_restaging() -> None:
    record = _record()
    record["state"] = "ARCHIVED"
    mixed_receipt = {
        "required": True,
        "destination_thread_id": record["source_thread_id"],
        "status": "BLOCKED",
        "attempt_count": 0,
        "message_key": "legacy-logical-key",
        "delivery_status": "rejected",
        "fallback_enabled": True,
        "fallback_status": "SENT",
        "fallback_used": True,
        "fallback_attempt_count": 1,
        "fallback_delivery_status": "accepted",
        "fallback_sent_at": "2026-09-01T11:26:41Z",
    }
    record["return_receipt"] = dict(mixed_receipt)

    contract.stage_receipt(record, {"response_file": "response.md"}, "e" * 64)

    assert record["return_receipt"] == mixed_receipt
    assert contract.receipt_has_delivery_evidence(record["return_receipt"]) is True


def test_terminal_blocker_receipt_routes_once_to_the_parent() -> None:
    record = _record()
    record["state"] = "BLOCKED"
    contract.stage_blocker_receipt(
        record,
        "BLOCKED",
        "provider URL no longer resolves",
        now="2026-08-31T00:40:00Z",
    )
    receipt = record["return_receipt"]
    message_key = receipt["message_key"]
    assert receipt["status"] == "PENDING"
    assert receipt["kind"] == "TERMINAL_BLOCKER"
    assert receipt["routing_mode"] == "PARENT_SESSION"
    assert receipt["fallback_enabled"] is False
    assert receipt["return_control_after_attempt"] is True
    assert receipt["destination_thread_id"] == record["parent_thread_id"]
    contract.stage_blocker_receipt(record, "BLOCKED", "provider URL no longer resolves")
    assert record["return_receipt"]["message_key"] == message_key


def test_terminal_blocker_without_parent_is_receipt_blocked() -> None:
    record = _record()
    record["state"] = "BLOCKED"
    record["parent_thread_id"] = None
    contract.stage_blocker_receipt(
        record,
        "BLOCKED",
        "provider URL no longer resolves",
        now="2026-08-31T00:40:00Z",
    )
    receipt = record["return_receipt"]
    assert receipt["kind"] == "TERMINAL_BLOCKER"
    assert receipt["status"] == "BLOCKED"
    assert receipt["receipt_state"] == "RETURN_RECEIPT_BLOCKED"
    assert receipt["destination_thread_id"] is None
    assert receipt["fallback_enabled"] is False
    assert receipt.get("message_key") is None
    assert record["state"] == "BLOCKED"


def test_parent_route_receipt_outcome_is_terminal_and_never_rerouted() -> None:
    record = _record()
    record["state"] = "ARCHIVED"
    record["parent_thread_id"] = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    contract.stage_receipt(record, {"response_file": "response.md"}, "e" * 64)
    receipt = record["return_receipt"]
    assert receipt["parent_thread_id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    assert receipt["destination_thread_id"] == record["parent_thread_id"]
    contract.record_receipt_result(record, "FAILED", error="send tool failed")
    receipt = record["return_receipt"]
    assert receipt["status"] == "FAILED"
    assert receipt["attempt_count"] == 1
    assert receipt["retry_allowed"] is False
    with pytest.raises(ValueError, match="one pending, unsent receipt"):
        contract.record_receipt_result(record, "SENT", delivery_status="accepted")
    assert record["return_receipt"]["status"] == "FAILED"

    uncertain = _record()
    uncertain["state"] = "ARCHIVED"
    contract.stage_receipt(uncertain, {"response_file": "response.md"}, "f" * 64)
    contract.record_receipt_result(uncertain, "UNCERTAIN", error="timeout")
    assert uncertain["return_receipt"]["status"] == "UNCERTAIN"
    assert uncertain["return_receipt"]["destination_thread_id"] == uncertain["parent_thread_id"]
    with pytest.raises(ValueError, match="one pending, unsent receipt"):
        contract.record_receipt_result(uncertain, "SENT")


def test_source_thread_validator_accepts_any_uuid_and_no_fallback_api_exists() -> None:
    source = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    assert contract.validate_source_thread_id(source) == source
    assert contract.validate_parent_thread_id(source) == source
    with pytest.raises(ValueError, match="source_thread_id"):
        contract.validate_source_thread_id("not-a-task")
    with pytest.raises(ValueError, match="parent_thread_id"):
        contract.validate_parent_thread_id("not-a-task")
    assert not hasattr(contract, "DEFAULT_FALLBACK_THREAD_ID")
    assert not hasattr(contract, "validate_fallback_thread_id")


def test_uncertain_or_invalid_conversation_states_cannot_stage_receipt() -> None:
    uncertain = _record()
    uncertain["state"] = "SEND_UNCERTAIN"
    uncertain["source_thread_id"] = None
    with pytest.raises(ValueError, match="ARCHIVED"):
        contract.stage_receipt(uncertain, {"response_file": "response.md"}, "1" * 64)
    assert "return_receipt" not in uncertain

    invalid_identity = _record()
    invalid_identity["state"] = "ARCHIVED"
    invalid_identity["conversation_id"] = None
    invalid_identity["source_thread_id"] = None
    with pytest.raises(ValueError, match="monitor identity missing"):
        contract.stage_receipt(invalid_identity, {"response_file": "response.md"}, "2" * 64)
    assert "return_receipt" not in invalid_identity


def test_registry_lock_is_fail_closed_and_releases_after_bounded_mutation(tmp_path: Path) -> None:
    registry = tmp_path / "nested" / "registry.json"
    with contract.registry_lock(registry):
        assert registry.with_name("registry.json.lock").is_file()
        with pytest.raises(RuntimeError, match="REGISTRY_LOCK_BUSY"):
            with contract.registry_lock(registry):
                pass
    assert not registry.with_name("registry.json.lock").exists()


def test_validate_request_exposes_packet_plan_and_return_readiness(
    project_root: Path, upload_request: dict[str, object]
) -> None:
    result = TRANSPORT_VALIDATE.validate(upload_request, project_root)
    assert result["packet"]["packet_id"] == "req-transport-01--demo_direction"
    assert result["packet"]["reference_filenames"][0]["canonical_filename"].startswith(
        "req-transport-01--demo_direction__01_REF_001_"
    )
    assert result["return_receipt_ready"] is True
    assert result["creator_thread_id"] == upload_request["source_thread_id"]
    assert result["parent_thread_id"] == upload_request["parent_thread_id"]
    assert result["return_receipt_thread_id"] == upload_request["parent_thread_id"]
    assert result["return_route"] == "PARENT_SESSION"
    assert "fallback_thread_id" not in result


def test_validate_request_requires_operator_for_every_canonical_workflow(
    project_root: Path, upload_request: dict[str, object]
) -> None:
    canonical = {
        **upload_request,
        "workflow_node": "em_innovator",
        "direction_ids": ["demo_direction"],
        "conversation_binding_key": "em:demo_direction:innovator",
        "decision_authority": "pro_final",
        "dispatch_mode": "REUSE_SINGLETON",
        "operator_reuse_required": True,
        "operator_model": "gpt-5.6-luna",
        "operator_thinking": "xhigh",
    }
    with pytest.raises(ValueError, match="requires the configured Transport singleton operator_thread_id"):
        TRANSPORT_VALIDATE.validate(canonical, project_root)

    accepted = TRANSPORT_VALIDATE.validate(
        {**canonical, "operator_thread_id": SINGLETON_THREAD_ID},
        project_root,
    )
    assert accepted["operator_thread_id"] == SINGLETON_THREAD_ID

    with pytest.raises(ValueError, match="dispatch_mode=REUSE_SINGLETON"):
        TRANSPORT_VALIDATE.validate(
            {
                **canonical,
                "dispatch_mode": "CREATE_ON_DEMAND",
                "operator_thread_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
            },
            project_root,
        )

    with pytest.raises(ValueError, match="does not match the configured project Transport singleton"):
        TRANSPORT_VALIDATE.validate(
            {**canonical, "operator_thread_id": "dddddddd-dddd-dddd-dddd-dddddddddddd"},
            project_root,
        )


def test_validate_request_allows_legacy_transport_without_a_receipt_parent(
    project_root: Path, upload_request: dict[str, object]
) -> None:
    legacy = dict(upload_request)
    legacy.pop("parent_thread_id")
    accepted = TRANSPORT_VALIDATE.validate(legacy, project_root)
    assert accepted["workflow_node"] == "legacy"
    assert accepted["source_thread_id"] == upload_request["source_thread_id"]
    assert accepted["parent_thread_id"] is None
    assert accepted["return_receipt_ready"] is False
    assert accepted["return_receipt_thread_id"] is None


@pytest.mark.parametrize(
    "field",
    ["fallback_enabled", "fallback_thread_id", "fallback_destination_thread_id", "primary_destination_thread_id"],
)
def test_validate_request_rejects_every_legacy_fallback_field(
    project_root: Path, upload_request: dict[str, object], field: str
) -> None:
    with pytest.raises(ValueError, match="legacy fallback routing fields"):
        TRANSPORT_VALIDATE.validate({**upload_request, field: None}, project_root)


def test_validate_request_accepts_only_evidenced_provider_context_reset(
    project_root: Path, upload_request: dict[str, object]
) -> None:
    evidence = {
        "previous_request_id": "req-transport-00",
        "decision_outcome": "BLOCKED",
        "repository_paths_read": 0,
        "provider_context_contamination_acknowledged": True,
        "acknowledged_prompt_defect": "obsolete provider-visible instruction",
    }
    accepted = TRANSPORT_VALIDATE.validate(
        {**upload_request, "reset_invalid_provider_context": True, "provider_context_reset_evidence": evidence},
        project_root,
    )
    assert accepted["reset_invalid_provider_context"] is True
    assert accepted["provider_context_reset_evidence"] == evidence

    with pytest.raises(ValueError, match="requested_conversation_id"):
        TRANSPORT_VALIDATE.validate(
            {
                **upload_request,
                "requested_conversation_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "reset_invalid_provider_context": True,
                "provider_context_reset_evidence": evidence,
            },
            project_root,
        )


def test_validate_request_enforces_canonical_single_body_attachment(
    project_root: Path, upload_request: dict[str, object]
) -> None:
    canonical = {
        **upload_request,
        "source_mode": "single_body_attachment",
        "dispatch_mode": "REUSE_SINGLETON",
        "operator_reuse_required": True,
        "operator_model": "gpt-5.6-luna",
        "operator_thinking": "xhigh",
        "operator_thread_id": SINGLETON_THREAD_ID,
    }
    canonical.pop("reference_paths")
    accepted = TRANSPORT_VALIDATE.validate(canonical, project_root)
    assert accepted["source_mode"] == "single_body_attachment"
    assert accepted["transport_input_mode"] == "upload"
    assert accepted["reference_files"] == []

    with pytest.raises(ValueError, match="must not declare reference_paths"):
        TRANSPORT_VALIDATE.validate(
            {**canonical, "reference_paths": []},
            project_root,
        )
    with pytest.raises(ValueError, match="must not declare reference_paths"):
        TRANSPORT_VALIDATE.validate(
            {**canonical, "reference_file": "REFERENCE_FILES.md"},
            project_root,
        )

    without_source = {**canonical}
    without_source.pop("source_thread_id")
    with pytest.raises(ValueError, match="canonical handoff requires source_thread_id"):
        TRANSPORT_VALIDATE.validate(without_source, project_root)

    without_parent = {**canonical}
    without_parent.pop("parent_thread_id")
    with pytest.raises(ValueError, match="canonical handoff requires parent_thread_id"):
        TRANSPORT_VALIDATE.validate(without_parent, project_root)

    without_operator = {**canonical}
    without_operator.pop("operator_thread_id")
    with pytest.raises(ValueError, match="requires the configured Transport singleton operator_thread_id"):
        TRANSPORT_VALIDATE.validate(without_operator, project_root)


def test_bind_records_v4_parent_route_lease_monitor_and_outbox(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"
    args = Namespace(
        registry=registry,
        direction_id="demo_direction",
        direction_ids_json=json.dumps(["demo_direction"]),
        workflow_node="legacy",
        conversation_binding_key="legacy:demo_direction",
        decision_authority="legacy",
        conversation_id="6a95b06d-0104-83e8-9493-f59f26b61c82",
        provider_url="https://chatgpt.com/c/6a95b06d-0104-83e8-9493-f59f26b61c82",
        tab_id="17",
        request_id="req-1",
        visible_model="Pro",
        underlying_model="GPT-5.6 Sol",
        thinking_effort="5/5",
        source_mode="upload",
        prompt_sha256="a" * 64,
        reference_files_json=json.dumps([{"filename": "REFERENCE_FILES.md", "bytes": 1, "sha256": "b" * 64}]),
        source_thread_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        parent_thread_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        operator_thread_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        packet_id=None,
        packet_manifest=str((tmp_path / "PACKET_MANIFEST.json").resolve()),
        tab_origin="agent",
    )

    assert BIND.bind(args) == 0
    record = json.loads(registry.read_text(encoding="utf-8"))["directions"]["demo_direction"]
    assert record["schema_version"] == 4
    assert record["tab_lease"]["lifecycle"] == "OPEN"
    assert record["monitor"]["identity_key"] == contract.monitor_identity_key(record)
    assert record["creator_thread_id"] == args.source_thread_id
    assert record["parent_thread_id"] == args.parent_thread_id
    assert record["operator_thread_id"] == args.operator_thread_id
    assert record["return_route"] == "PARENT_SESSION"
    assert record["return_receipt"]["destination_thread_id"] == args.parent_thread_id
    assert record["return_receipt"]["routing_mode"] == "PARENT_SESSION"
    assert record["return_receipt"]["fallback_enabled"] is False
    assert record["heartbeat"]["status"] == "PENDING"
    assert record["reference_files"][0]["canonical_filename"].endswith("REFERENCE_FILES.md")


def test_bind_legacy_without_parent_disables_automatic_receipt(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"
    args = Namespace(
        registry=registry,
        direction_id="demo_direction",
        direction_ids_json=json.dumps(["demo_direction"]),
        workflow_node="legacy",
        conversation_binding_key="legacy:demo_direction",
        decision_authority="legacy",
        conversation_id="6a95b06d-0104-83e8-9493-f59f26b61c82",
        provider_url="https://chatgpt.com/c/6a95b06d-0104-83e8-9493-f59f26b61c82",
        tab_id="17",
        request_id="req-no-source",
        visible_model="Pro",
        underlying_model="GPT-5.6 Sol",
        thinking_effort="5/5",
        source_mode="upload",
        prompt_sha256="a" * 64,
        reference_files_json="[]",
        source_thread_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        parent_thread_id=None,
        operator_thread_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        packet_id=None,
        packet_manifest=None,
        tab_origin="agent",
    )

    assert BIND.bind(args) == 0
    record = json.loads(registry.read_text(encoding="utf-8"))["bindings"][args.conversation_binding_key]
    assert "fallback_enabled" not in record
    assert "fallback_thread_id" not in record
    assert record["source_thread_id"] == args.source_thread_id
    assert record["parent_thread_id"] is None
    assert record["return_receipt"]["required"] is False
    assert record["return_receipt"]["status"] == "BLOCKED"
    assert record["return_receipt"]["receipt_state"] == "RETURN_RECEIPT_BLOCKED"
    assert record["return_receipt"]["destination_thread_id"] is None
    assert record["return_receipt"]["fallback_enabled"] is False


def _em_bind_args(tmp_path: Path, request_id: str) -> Namespace:
    conversation_id = "6a95b06d-0104-83e8-9493-f59f26b61c82"
    return Namespace(
        registry=tmp_path / "registry.json",
        direction_id="demo_direction",
        direction_ids_json=json.dumps(["demo_direction"]),
        workflow_node="em_innovator",
        conversation_binding_key="em:demo_direction:innovator",
        decision_authority="pro_final",
        conversation_id=conversation_id,
        provider_url=f"https://chatgpt.com/c/{conversation_id}",
        tab_id="17",
        request_id=request_id,
        visible_model="Pro",
        underlying_model="GPT-5.6 Sol",
        thinking_effort="5/5",
        source_mode="upload",
        prompt_sha256="a" * 64,
        reference_files_json="[]",
        source_thread_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        parent_thread_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        operator_thread_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        packet_id=None,
        packet_manifest=None,
        tab_origin="agent",
    )


def test_bind_rejects_canonical_request_without_runtime_operator(tmp_path: Path) -> None:
    request = _em_bind_args(tmp_path, "req-no-operator")
    request.operator_thread_id = None
    assert BIND.bind(request) == 2
    assert not request.registry.exists()


def test_next_round_preserves_delivered_legacy_receipt_only_in_history(tmp_path: Path) -> None:
    first = _em_bind_args(tmp_path, "req-legacy-delivered")
    assert BIND.bind(first) == 0
    registry = json.loads(first.registry.read_text(encoding="utf-8"))
    key = first.conversation_binding_key
    mixed_receipt = {
        "required": True,
        "destination_thread_id": first.source_thread_id,
        "status": "BLOCKED",
        "attempt_count": 0,
        "message_key": "legacy-logical-key",
        "delivery_status": "rejected",
        "fallback_enabled": True,
        "fallback_status": "SENT",
        "fallback_used": True,
        "fallback_attempt_count": 1,
        "fallback_delivery_status": "accepted",
        "fallback_sent_at": "2026-09-01T11:26:41Z",
    }
    for record in (registry["bindings"][key], registry["directions"][first.direction_id]):
        record.update(
            {
                "state": "ARCHIVED",
                "fallback_enabled": True,
                "fallback_thread_id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
                "fallback_thread_url": "codex://threads/eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
                "return_receipt": dict(mixed_receipt),
                "archive": {"response_file": "response.md"},
                "timestamps": {"archived_at": "2026-09-01T11:26:41Z"},
            }
        )
    first.registry.write_text(json.dumps(registry), encoding="utf-8")

    second = _em_bind_args(tmp_path, "req-current-parent-route")
    second.source_thread_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    second.parent_thread_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    second.operator_thread_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    assert BIND.bind(second) == 0

    current = json.loads(second.registry.read_text(encoding="utf-8"))["bindings"][key]
    historical = current["request_history"][-1]
    assert historical["return_receipt"] == mixed_receipt
    assert historical["fallback_thread_id"] == "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    assert current["source_thread_id"] == second.source_thread_id
    assert current["operator_thread_id"] == second.operator_thread_id
    assert current["parent_thread_id"] == second.parent_thread_id
    assert current["return_receipt"]["routing_mode"] == "PARENT_SESSION"
    assert current["return_receipt"]["fallback_enabled"] is False
    assert "fallback_thread_id" not in current
    assert "fallback_thread_url" not in current


def test_archived_direction_mirror_releases_stale_binding_for_next_serial_round(
    tmp_path: Path,
) -> None:
    first = _em_bind_args(tmp_path, "req-01")
    assert BIND.bind(first) == 0
    registry = json.loads(first.registry.read_text(encoding="utf-8"))
    key = first.conversation_binding_key

    # Model an older completion writer that durably archived the historical
    # direction mirror but failed before replacing the duplicated binding copy.
    archived = registry["directions"][first.direction_id]
    archived.update(
        {
            "state": "ARCHIVED",
            "archive": {"response_file": "response.md", "transport_fact_file": "facts.json"},
            "timestamps": {"archived_at": "2026-09-01T00:00:00Z"},
        }
    )
    registry["bindings"][key]["state"] = "WAITING_GENERATION"
    first.registry.write_text(json.dumps(registry), encoding="utf-8")

    second = _em_bind_args(tmp_path, "req-02")
    assert BIND.bind(second) == 0

    repaired = json.loads(second.registry.read_text(encoding="utf-8"))["bindings"][key]
    assert repaired["conversation_id"] == first.conversation_id
    assert repaired["provider_url"] == first.provider_url
    assert repaired["request_id"] == "req-02"
    assert repaired["state"] == "DIRECTION_VERIFIED"
    assert repaired["send_click_count"] == 0
    assert repaired["request_history"][-1]["request_id"] == "req-01"
    assert repaired["request_history"][-1]["state"] == "ARCHIVED"


def test_nonterminal_binding_still_blocks_distinct_serial_request(tmp_path: Path) -> None:
    first = _em_bind_args(tmp_path, "req-01")
    assert BIND.bind(first) == 0
    before = first.registry.read_bytes()

    second = _em_bind_args(tmp_path, "req-02")
    assert BIND.bind(second) == 4
    assert first.registry.read_bytes() == before


def test_same_request_bind_is_idempotent_after_initial_admission(tmp_path: Path) -> None:
    request = _em_bind_args(tmp_path, "req-01")
    assert BIND.bind(request) == 0
    assert BIND.bind(request) == 0

    record = json.loads(request.registry.read_text(encoding="utf-8"))["bindings"][request.conversation_binding_key]
    assert record["request_id"] == "req-01"
    assert record.get("request_history") is None
    assert record["send_click_count"] == 1


def test_skill_contracts_encode_execution_owner_async_and_tab_boundaries() -> None:
    transport_text = TRANSPORT_SKILL.read_text(encoding="utf-8")
    for reference in ("attachment-compatibility.md", "attachment-send.md"):
        transport_text += (TRANSPORT_SKILL.parent / "references" / reference).read_text(encoding="utf-8")
    outsource_text = OUTSOURCE_SKILL.read_text(encoding="utf-8")

    for phrase in (
        "The transport task is the execution owner",
        "scripts/materialize_packet.py",
        "never use `INTERVAL=1` busy polling",
        "the tab lease remains active while generation is pending",
        "The executor turn ending, a heartbeat wake returning, or a timeout is never",
        "request_id|conversation_binding_key|conversation_id|provider_url",
        "stage_receipt",
        "provider filename suffix or normalization",
        "Acceptance of a\nvalidated handoff authorizes uploading exactly its validated `prompt_path`",
        "Do not request\naction-time confirmation before upload or immediately before Send",
        "does not extend to any other local file, destination, replacement packet, or second",
        "rejected before acceptance and produced no external effect",
        "`parent_thread_id` is the sole completion",
        "`fallback_enabled=false`",
        "a rejection must not cause a second send",
        "`RETURN_RECEIPT_BLOCKED`",
        "Never multiplex a later",
        "stage_blocker_receipt",
    ):
        assert phrase in transport_text
    assert "fallback_enabled=true" not in transport_text
    assert "obtain the required action-time confirmation" not in transport_text
    assert "transport-level confirmation gate" not in transport_text
    assert "01a05860-" not in transport_text
    assert "01a04f5a-" not in transport_text
    assert "owns the complete edit and verification" in outsource_text
    assert "never silently fan out, duplicate, or replace an agent" in outsource_text
    assert "close the temporary tab\nafter recording that state" not in transport_text


def test_skill_contracts_bound_locator_coordinate_offset_recovery() -> None:
    transport_text = (TRANSPORT_SKILL.parent / "references" / "send-hit-point-recovery.md").read_text(encoding="utf-8")

    for phrase in (
        "Locator hit-point mismatch recovery",
        "matchCount=1",
        "visibleCount=1",
        "disabled=false",
        "No element found at point",
        "fresh DOM state using the current browser",
        "exact visible Send prompt node",
        "the URL is unchanged from the\npre-send observation",
        "no visible user-message node exists for the exact prompt",
        "enabled and\nvisible",
        "the exact visible user-message node and\nits exact prompt text",
        "every expected attachment/file group and recorded hash",
        "terminal `SEND_UNCERTAIN`; do not retry",
        "Never perform blind coordinate retries, a second\nDOM-node click, or any retry after `SEND_UNCERTAIN`.",
    ):
        assert phrase in transport_text

    assert "Treat that combination\nas a locator coordinate offset, not as `SEND_FAILED_PRE_SEND`" in transport_text
    assert "This DOM-node click replaces the failed locator click; it is the one Send\nattempt" in transport_text


def test_transport_contracts_require_one_attachment_for_prompt_author_packets() -> None:
    transport_text = "\n".join(
        (TRANSPORT_SKILL.parent / "references" / reference).read_text(encoding="utf-8")
        for reference in ("attachment-compatibility.md", "attachment-send.md")
    )

    assert "`PROMPT_BODY.md` is the sole scientific\nattachment" in transport_text
    assert "must not declare, upload, or synthesize `reference_paths`" in transport_text
    assert "upload only `PROMPT_BODY.md`" in transport_text
    assert "must not be\nsplit back out for upload" in transport_text


@pytest.mark.parametrize("visible,underlying,effort,valid", [
    ("6 Pro", "Latest", "Pro, 5 of 5.", True),
    ("6 Pro", "GPT-6 Astra", "Pro, 5 of 5.", True),
    ("Pro", "GPT-6 Astra", "Pro, 5 of 5.", True),
    ("Pro", "GPT-5.6 Sol", "Pro, 5 of 5.", False),
    ("7 Pro", "Latest", "Pro, 5 of 5.", False),
    ("Pro", "Latest", "Pro, 5 of 5.", False),
    ("6 Pro", "Latest", "Thinking, 4 of 5.", False),
])
def test_provider_model_is_verified_separately_from_executor(visible, underlying, effort, valid) -> None:
    requirement = {"model": "GPT-6 Astra", "mode": "Pro", "label": "6 Pro", "selector_hint": "Latest"}
    args = dict(visible_model=visible, underlying_model=underlying, thinking_effort=effort)
    if valid:
        contract.verify_provider_selection(requirement, **args)
    else:
        with pytest.raises(ValueError):
            contract.verify_provider_selection(requirement, **args)


def test_old_answer_capture_is_not_accepted_as_new_request() -> None:
    binding = {"conversation_id": "conversation", "user_message_id": "question", "assistant_message_id": "answer"}
    answer = "建议继续这一项有界研究。证据支持该选择，但加速效果尚未实测。"
    with pytest.raises(ValueError, match="RESPONSE_IDENTITY_MISMATCH"):
        contract.validate_response_identity(answer, expected_binding=binding, observed_binding={**binding, "assistant_message_id": "earlier-answer"})
    contract.validate_response_identity(answer, expected_binding=binding, observed_binding=dict(binding))


@pytest.mark.parametrize("field", ["conversation_id", "user_message_id", "assistant_message_id"])
def test_response_pairing_requires_complete_matching_provider_evidence(field) -> None:
    binding = {"conversation_id": "conversation", "user_message_id": "question", "assistant_message_id": "answer"}
    with pytest.raises(ValueError, match="RESPONSE_IDENTITY_MISMATCH"):
        contract.validate_response_identity("结论", expected_binding=binding, observed_binding={**binding, field: "other"})
    with pytest.raises(ValueError, match="missing recorded provider binding"):
        contract.validate_response_identity("结论", expected_binding={**binding, field: ""}, observed_binding=binding)


def test_direct_transport_requires_owner_and_exact_caller(project_root, upload_request) -> None:
    request = {**upload_request, "dispatch_mode": "CALLER_DIRECT", "operator_thread_id": upload_request["source_thread_id"]}
    with pytest.raises(ValueError, match="owner's execution instruction"):
        TRANSPORT_VALIDATE.validate(request, project_root)
    request["owner_execution_instruction"] = "Root operates personally."
    assert TRANSPORT_VALIDATE.validate(request, project_root)["return_receipt_ready"] is True
    request["operator_thread_id"] = SINGLETON_THREAD_ID
    with pytest.raises(ValueError, match="exact source caller"):
        TRANSPORT_VALIDATE.validate(request, project_root)
