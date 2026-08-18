"""Immutable observer types. No semantic authority lives here."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class RpcShape(str, Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    NOTIFICATION = "NOTIFICATION"
    INVALID = "INVALID"


class RequestClass(str, Enum):
    HANDSHAKE = "HANDSHAKE"
    READ_IDEMPOTENT = "READ_IDEMPOTENT"
    MUTATING_NO_RETRY = "MUTATING_NO_RETRY"


class EndKind(str, Enum):
    NORMAL = "NORMAL"
    OPERATOR_INTERRUPT = "OPERATOR_INTERRUPT"
    TRANSPORT_EOF = "TRANSPORT_EOF"
    PROTOCOL_INCIDENT = "PROTOCOL_INCIDENT"
    LINE_TOO_LARGE = "LINE_TOO_LARGE"
    UNEXPECTED_SERVER_REQUEST = "UNEXPECTED_SERVER_REQUEST"
    PROCESS_EXIT = "PROCESS_EXIT"


FORBIDDEN_EVENT_KINDS = frozenset(
    {"BLOCKED", "FAILED", "SUCCESS", "RETIRED", "PAUSED", "PARKED", "RELEASED"}
)


@dataclass(frozen=True)
class ObserverConfig:
    schema_version: int
    client_name: str
    client_title: str
    client_version: str
    experimental_api: bool
    initialize_timeout_seconds: float
    request_timeout_seconds: float
    reconcile_interval_seconds: float
    max_jsonl_line_bytes: int
    read_retry_attempts: int
    read_retry_base_seconds: float
    unexpected_server_request_policy: str
    runtime_home: Path


@dataclass(frozen=True)
class ProtocolIds:
    request_id: str | None
    method: str | None
    thread_id: str | None
    turn_id: str | None
    item_id: str | None


@dataclass(frozen=True)
class SchemaCapture:
    binary: Path
    version: str
    output_root: Path
    schema_files: tuple[str, ...]
    observed_methods: tuple[str, ...]
    manifest_path: Path


@dataclass(frozen=True)
class TransportMessage:
    transport_seq: int
    payload: Mapping[str, Any]
    observed_at: str


@dataclass(frozen=True)
class NormalizedEvent:
    event_kind: str
    raw_message_seq: int
    run_id: str
    thread_id: str | None
    turn_id: str | None
    item_id: str | None
    mechanical_status: str | None
    payload: dict[str, Any]
    observed_at: str


@dataclass(frozen=True)
class ObserverRunResult:
    run_id: str
    end_kind: str
    exit_code: int | None
    initialized: bool
    thread_count: int = 0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanaryResult:
    canary_id: str
    run_id: str
    thread_id: str | None
    turn_id: str | None
    outcome: str
    final_text: str | None = None
    incident: str | None = None
