from __future__ import annotations

import json
from dataclasses import asdict, replace

import pytest

from tools.codex_supervisor.host_state import (
    PROCESS_RECORD_SCHEMA,
    READY_RECORD_SCHEMA,
    HostStateValidationError,
    SupervisorProcessRecord,
    SupervisorReadyRecord,
    atomic_write_json,
    load_process_record,
    load_ready_record,
    validate_ready_record,
)


def process_record(**overrides: object) -> SupervisorProcessRecord:
    values = {
        "schema": PROCESS_RECORD_SCHEMA,
        "pid": 123,
        "process_start_time_utc": "2026-08-23T12:00:00Z",
        "executable": "C:/Program Files/Python/python.exe",
        "repo_root": "C:/Projects/HMASD-app-server-live-runtime",
        "runtime_home": "C:/Users/test/AppData/Local/HMASD/codex-supervisor",
        "profile": "OBSERVER",
        "started_at": "2026-08-23T12:00:01Z",
        "ready_file": "C:/Users/test/AppData/Local/HMASD/codex-supervisor/ready.json",
    }
    values.update(overrides)
    return SupervisorProcessRecord(**values)  # type: ignore[arg-type]


def ready_record(**overrides: object) -> SupervisorReadyRecord:
    values = {
        "schema": READY_RECORD_SCHEMA,
        "run_id": "run-1",
        "process_id": 123,
        "initialized_at": "2026-08-23T12:00:02Z",
        "watcher_active": True,
        "first_reconciliation_completed": True,
        "thread_count": 0,
        "runtime_home": "C:/Users/test/AppData/Local/HMASD/codex-supervisor",
        "profile": "OBSERVER",
    }
    values.update(overrides)
    return SupervisorReadyRecord(**values)  # type: ignore[arg-type]


def test_alive_process_record_without_ready_record_is_not_ready():
    process = process_record(pid=123)
    assert validate_ready_record(process, None) == ("ready record is missing",)


def test_ready_record_requires_watcher_and_reconciliation():
    process = process_record(pid=123)
    ready = ready_record(
        process_id=123,
        watcher_active=False,
        first_reconciliation_completed=False,
    )
    errors = validate_ready_record(process, ready)
    assert "server-request watcher is not active" in errors
    assert "first reconciliation is incomplete" in errors


def test_ready_record_requires_matching_identity_and_nonempty_run_id():
    process = process_record()
    ready = ready_record(
        process_id=456,
        runtime_home="C:/runtime/other",
        profile="MANAGED_MANUAL",
        run_id="  ",
    )
    assert validate_ready_record(process, ready) == (
        "process ID does not match",
        "runtime home does not match",
        "profile does not match",
        "run_id is empty",
    )


def test_valid_ready_record_has_no_errors():
    assert validate_ready_record(process_record(), ready_record()) == ()


def test_atomic_write_json_replaces_complete_record(tmp_path):
    path = tmp_path / "nested" / "process.json"
    atomic_write_json(path, {"old": True})
    atomic_write_json(path, asdict(process_record()))

    assert load_process_record(path) == process_record()
    assert not list(path.parent.glob(f".{path.name}.*.tmp"))


def test_load_ready_record_round_trips_exact_contract(tmp_path):
    path = tmp_path / "ready.json"
    expected = ready_record(thread_count=17)
    atomic_write_json(path, asdict(expected))
    assert load_ready_record(path) == expected


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("pid", True),
        ("pid", "123"),
        ("process_start_time_utc", None),
        ("executable", ""),
        ("runtime_home", []),
    ],
)
def test_load_process_record_rejects_wrong_types_and_empty_facts(
    tmp_path, field, invalid
):
    path = tmp_path / "process.json"
    payload = asdict(process_record())
    payload[field] = invalid
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(HostStateValidationError):
        load_process_record(path)


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("process_id", True),
        ("watcher_active", 1),
        ("first_reconciliation_completed", "true"),
        ("thread_count", -1),
        ("thread_count", False),
        ("run_id", None),
    ],
)
def test_load_ready_record_rejects_wrong_types(tmp_path, field, invalid):
    path = tmp_path / "ready.json"
    payload = asdict(ready_record())
    payload[field] = invalid
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(HostStateValidationError):
        load_ready_record(path)


@pytest.mark.parametrize("record_kind", ["process", "ready"])
def test_load_record_rejects_unknown_and_missing_fields(tmp_path, record_kind):
    path = tmp_path / f"{record_kind}.json"
    record = process_record() if record_kind == "process" else ready_record()
    payload = asdict(record)
    payload.pop("schema")
    payload["unexpected"] = "value"
    path.write_text(json.dumps(payload), encoding="utf-8")

    loader = load_process_record if record_kind == "process" else load_ready_record
    with pytest.raises(HostStateValidationError, match="fields differ"):
        loader(path)


def test_load_records_reject_wrong_schema(tmp_path):
    process_path = tmp_path / "process.json"
    ready_path = tmp_path / "ready.json"
    atomic_write_json(
        process_path,
        asdict(replace(process_record(), schema="HMASD_SUPERVISOR_PROCESS_V0")),
    )
    atomic_write_json(
        ready_path,
        asdict(replace(ready_record(), schema="HMASD_SUPERVISOR_READY_V1")),
    )

    with pytest.raises(HostStateValidationError, match="schema must equal"):
        load_process_record(process_path)
    with pytest.raises(HostStateValidationError, match="schema must equal"):
        load_ready_record(ready_path)


def test_load_record_rejects_non_object_json(tmp_path):
    path = tmp_path / "ready.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(HostStateValidationError, match="must be a JSON object"):
        load_ready_record(path)


def test_host_state_contract_has_no_semantic_state_field():
    assert "semantic_state" not in SupervisorProcessRecord.__dataclass_fields__
    assert "semantic_state" not in SupervisorReadyRecord.__dataclass_fields__
