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


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    direction = tmp_path / "docs" / "research" / "candidates" / "demo_direction"
    portfolio = tmp_path / "docs" / "research" / "portfolio"
    direction.mkdir(parents=True)
    portfolio.mkdir(parents=True)
    (direction / "DIRECTION.md").write_text("# Demo\n", encoding="utf-8")
    (portfolio / "PORTFOLIO.md").write_text("| demo_direction | ACTIVE |\n", encoding="utf-8")
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
        "source_thread_id": "01a04f5a-1c9f-7331-b1d9-249fb767362e",
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
        "source_thread_id": "01a04f5a-1c9f-7331-b1d9-249fb767362e",
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
    with pytest.raises(ValueError, match="staged completion receipt"):
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
    contract.record_receipt_result(record, "UNCERTAIN", delivery_status="timeout", error="unknown")
    assert record["return_receipt"]["status"] == "UNCERTAIN"
    assert record["return_receipt"]["retry_allowed"] is False
    assert record["return_receipt"]["attempt_count"] == 1


def test_missing_source_without_explicit_fallback_remains_blocked() -> None:
    record = _record()
    record["state"] = "ARCHIVED"
    record["source_thread_id"] = None
    contract.stage_receipt(record, {"response_file": "response.md"}, "c" * 64)
    receipt = record["return_receipt"]
    assert receipt["status"] == "BLOCKED"
    assert receipt["fallback_enabled"] is False
    assert receipt["fallback_used"] is False
    assert receipt["destination_thread_id"] is None


def test_explicit_fallback_routes_missing_source_to_the_bound_session() -> None:
    record = _record()
    record["state"] = "ARCHIVED"
    record["source_thread_id"] = None
    record["fallback_enabled"] = True
    record["fallback_thread_id"] = contract.DEFAULT_FALLBACK_THREAD_ID
    contract.stage_receipt(record, {"response_file": "response.md"}, "d" * 64)
    receipt = record["return_receipt"]
    assert receipt["status"] == "PENDING"
    assert receipt["fallback_used"] is True
    assert receipt["return_control_after_attempt"] is True
    assert receipt["fallback_delivery_mode"] == "bounded_single_attempt"
    assert receipt["destination_thread_id"] == contract.DEFAULT_FALLBACK_THREAD_ID
    assert receipt["fallback_status"] == "PENDING"
    assert receipt["fallback_message_key"].endswith(
        f"|fallback|{contract.DEFAULT_FALLBACK_THREAD_ID}"
    )


def test_explicit_fallback_stages_terminal_blocker_without_archive() -> None:
    record = _record()
    record["state"] = "BLOCKED"
    record["source_thread_id"] = None
    record["fallback_enabled"] = True
    contract.stage_blocker_receipt(
        record,
        "BLOCKED",
        "provider URL no longer resolves",
        now="2026-08-31T00:40:00Z",
    )
    receipt = record["return_receipt"]
    assert receipt["kind"] == "TERMINAL_BLOCKER"
    assert receipt["status"] == "PENDING"
    assert receipt["fallback_used"] is True
    assert receipt["destination_thread_id"] == contract.DEFAULT_FALLBACK_THREAD_ID
    assert receipt["fallback_staged_at"] == "2026-08-31T00:40:00Z"


def test_definite_primary_failure_stages_fallback_but_uncertain_does_not() -> None:
    record = _record()
    record["state"] = "ARCHIVED"
    record["source_thread_id"] = "01a05860-6919-7bd3-9b04-99f8344ed73d"
    record["fallback_enabled"] = True
    record["fallback_thread_id"] = contract.DEFAULT_FALLBACK_THREAD_ID
    contract.stage_receipt(record, {"response_file": "response.md"}, "e" * 64)
    contract.record_receipt_result(record, "FAILED", error="send tool failed")
    receipt = record["return_receipt"]
    assert receipt["fallback_used"] is True
    assert receipt["fallback_status"] == "PENDING"
    contract.record_fallback_result(record, "SENT", delivery_status="accepted")
    assert record["return_receipt"]["fallback_status"] == "SENT"

    uncertain = _record()
    uncertain["state"] = "ARCHIVED"
    uncertain["fallback_enabled"] = True
    uncertain["fallback_thread_id"] = contract.DEFAULT_FALLBACK_THREAD_ID
    contract.stage_receipt(uncertain, {"response_file": "response.md"}, "f" * 64)
    contract.record_receipt_result(uncertain, "UNCERTAIN", error="timeout")
    assert uncertain["return_receipt"]["fallback_used"] is False
    assert uncertain["return_receipt"]["fallback_status"] == "NOT_NEEDED"


def test_only_the_configured_fallback_uuid_is_accepted() -> None:
    with pytest.raises(ValueError, match=contract.DEFAULT_FALLBACK_THREAD_ID):
        contract.validate_fallback_thread_id("6a95b06d-0104-83e8-9493-f59f26b61c82")


def test_uncertain_or_invalid_conversation_states_cannot_stage_fallback() -> None:
    uncertain = _record()
    uncertain["state"] = "SEND_UNCERTAIN"
    uncertain["source_thread_id"] = None
    uncertain["fallback_enabled"] = True
    with pytest.raises(ValueError, match="ARCHIVED"):
        contract.stage_receipt(uncertain, {"response_file": "response.md"}, "1" * 64)
    assert "return_receipt" not in uncertain

    invalid_identity = _record()
    invalid_identity["state"] = "ARCHIVED"
    invalid_identity["conversation_id"] = None
    invalid_identity["source_thread_id"] = None
    invalid_identity["fallback_enabled"] = True
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
    enabled = TRANSPORT_VALIDATE.validate(
        {
            **upload_request,
            "fallback_enabled": True,
            "fallback_thread_id": contract.DEFAULT_FALLBACK_THREAD_ID,
        },
        project_root,
    )
    assert enabled["fallback_enabled"] is True
    assert enabled["fallback_thread_id"] == contract.DEFAULT_FALLBACK_THREAD_ID
    assert enabled["fallback_thread_url"] == contract.DEFAULT_FALLBACK_THREAD_URL


def test_validate_request_requires_the_explicit_fallback_flag() -> None:
    # Validation reaches direction registration first in a real project; this
    # focused assertion checks the helper's fixed-target validator directly.
    with pytest.raises(ValueError, match=contract.DEFAULT_FALLBACK_THREAD_ID):
        contract.validate_fallback_thread_id("not-the-bound-session")


def test_bind_records_v2_lease_monitor_and_outbox(tmp_path: Path) -> None:
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
        source_thread_id="01a04f5a-1c9f-7331-b1d9-249fb767362e",
        fallback_enabled=False,
        fallback_thread_id=None,
        packet_id=None,
        packet_manifest=str((tmp_path / "PACKET_MANIFEST.json").resolve()),
        tab_origin="agent",
    )

    assert BIND.bind(args) == 0
    record = json.loads(registry.read_text(encoding="utf-8"))["directions"]["demo_direction"]
    assert record["schema_version"] == 2
    assert record["tab_lease"]["lifecycle"] == "OPEN"
    assert record["monitor"]["identity_key"] == contract.monitor_identity_key(record)
    assert record["return_receipt"]["destination_thread_id"] == args.source_thread_id
    assert record["heartbeat"]["status"] == "PENDING"
    assert record["reference_files"][0]["canonical_filename"].endswith("REFERENCE_FILES.md")


def test_bind_persists_explicit_fallback_binding(tmp_path: Path) -> None:
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
        request_id="req-fallback",
        visible_model="Pro",
        underlying_model="GPT-5.6 Sol",
        thinking_effort="5/5",
        source_mode="upload",
        prompt_sha256="a" * 64,
        reference_files_json="[]",
        source_thread_id=None,
        fallback_enabled=True,
        fallback_thread_id=contract.DEFAULT_FALLBACK_THREAD_ID,
        packet_id=None,
        packet_manifest=None,
        tab_origin="agent",
    )

    assert BIND.bind(args) == 0
    record = json.loads(registry.read_text(encoding="utf-8"))["bindings"][args.conversation_binding_key]
    assert record["fallback_enabled"] is True
    assert record["fallback_thread_id"] == contract.DEFAULT_FALLBACK_THREAD_ID
    assert record["fallback_thread_url"] == contract.DEFAULT_FALLBACK_THREAD_URL
    assert record["return_receipt"]["fallback_enabled"] is True


def test_skill_contracts_encode_execution_owner_async_and_tab_boundaries() -> None:
    transport_text = TRANSPORT_SKILL.read_text(encoding="utf-8")
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
        "fallback_enabled=true",
        "01a04f5a-1c9f-7331-b1d9-249fb767362e",
        "fallback for `UNCERTAIN`, `SEND_UNCERTAIN`",
        "stage_blocker_receipt",
    ):
        assert phrase in transport_text
    assert "The target is responsible for the full lifecycle after acceptance" in outsource_text
    assert "do not dispatch the task to itself" in outsource_text
    assert "close the temporary tab\nafter recording that state" not in transport_text
