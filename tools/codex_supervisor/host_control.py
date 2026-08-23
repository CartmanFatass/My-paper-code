"""Typed, external file control channel for one long-lived supervisor host.

The channel is deliberately closed over :class:`CommandKind`.  It never
accepts an App Server method name, and it never retries a managed mutation.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .host_state import atomic_write_json
from .runtime_profiles import CommandKind, RuntimeProfile, require_command_allowed


CONTROL_REQUEST_SCHEMA = "HMASD_SUPERVISOR_CONTROL_REQUEST_V1"
CONTROL_RESPONSE_SCHEMA = "HMASD_SUPERVISOR_CONTROL_RESPONSE_V1"
DEFAULT_MAX_REQUEST_AGE_SECONDS = 300.0
DEFAULT_FUTURE_SKEW_SECONDS = 30.0
_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_REQUEST_FIELDS = frozenset(
    {"schema", "request_id", "created_at", "operator", "command", "arguments"}
)
_RESPONSE_FIELDS = frozenset(
    {"schema", "request_id", "status", "payload", "error", "completed_at"}
)
_RESPONSE_STATUSES = frozenset(
    {"OK", "ERROR", "REJECTED", "NOT_IMPLEMENTED", "SUBMISSION_UNCERTAIN"}
)
_REPLAY_FENCED_COMMANDS = frozenset(
    command
    for command in CommandKind
    if command not in {CommandKind.STATUS, CommandKind.INSPECT, CommandKind.MAILBOX_LIST}
)
_MUTATING_COMMANDS = _REPLAY_FENCED_COMMANDS - {CommandKind.STOP}


class HostControlError(RuntimeError):
    """Base error for the local control protocol."""


class HostControlValidationError(HostControlError, ValueError):
    """A request or response is not exactly valid."""


class HostControlConflictError(HostControlError):
    """A request ID was reused with different content."""


@dataclass(frozen=True)
class HostControlRequest:
    schema: str
    request_id: str
    created_at: str
    operator: str
    command: CommandKind
    arguments: dict[str, object]

    def __post_init__(self) -> None:
        _validate_request(self)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["command"] = self.command.value
        return payload


@dataclass(frozen=True)
class HostControlResponse:
    schema: str
    request_id: str
    status: str
    payload: dict[str, object]
    error: str | None
    completed_at: str

    def __post_init__(self) -> None:
        _validate_response(self)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_request(payload: Mapping[str, object]) -> HostControlRequest:
    _require_exact_mapping(payload, _REQUEST_FIELDS, "control request")
    try:
        command = CommandKind(payload["command"])
    except (TypeError, ValueError) as exc:
        raise HostControlValidationError("control request.command is invalid") from exc
    arguments = payload["arguments"]
    if type(arguments) is not dict:
        raise HostControlValidationError("control request.arguments must be an object")
    return HostControlRequest(
        schema=payload["schema"],  # type: ignore[arg-type]
        request_id=payload["request_id"],  # type: ignore[arg-type]
        created_at=payload["created_at"],  # type: ignore[arg-type]
        operator=payload["operator"],  # type: ignore[arg-type]
        command=command,
        arguments=dict(arguments),
    )


def parse_response(payload: Mapping[str, object]) -> HostControlResponse:
    _require_exact_mapping(payload, _RESPONSE_FIELDS, "control response")
    body = payload["payload"]
    if type(body) is not dict:
        raise HostControlValidationError("control response.payload must be an object")
    return HostControlResponse(
        schema=payload["schema"],  # type: ignore[arg-type]
        request_id=payload["request_id"],  # type: ignore[arg-type]
        status=payload["status"],  # type: ignore[arg-type]
        payload=dict(body),
        error=payload["error"],  # type: ignore[arg-type]
        completed_at=payload["completed_at"],  # type: ignore[arg-type]
    )


def _validate_request(request: HostControlRequest) -> None:
    if request.schema != CONTROL_REQUEST_SCHEMA:
        raise HostControlValidationError(
            f"control request.schema must equal {CONTROL_REQUEST_SCHEMA!r}"
        )
    _require_request_id(request.request_id)
    _parse_timestamp(request.created_at, "control request.created_at")
    _require_nonempty_string(request.operator, "control request.operator")
    if not isinstance(request.command, CommandKind):
        raise HostControlValidationError("control request.command must be a CommandKind")
    if type(request.arguments) is not dict:
        raise HostControlValidationError("control request.arguments must be an object")
    _require_json_value(request.arguments, "control request.arguments")


def _validate_response(response: HostControlResponse) -> None:
    if response.schema != CONTROL_RESPONSE_SCHEMA:
        raise HostControlValidationError(
            f"control response.schema must equal {CONTROL_RESPONSE_SCHEMA!r}"
        )
    _require_request_id(response.request_id)
    if response.status not in _RESPONSE_STATUSES:
        raise HostControlValidationError("control response.status is invalid")
    if type(response.payload) is not dict:
        raise HostControlValidationError("control response.payload must be an object")
    _require_json_value(response.payload, "control response.payload")
    if response.error is not None and type(response.error) is not str:
        raise HostControlValidationError("control response.error must be a string or null")
    if response.status == "OK" and response.error is not None:
        raise HostControlValidationError("an OK response cannot carry an error")
    if response.status != "OK" and not response.error:
        raise HostControlValidationError("a non-OK response requires an error")
    _parse_timestamp(response.completed_at, "control response.completed_at")


def _require_exact_mapping(
    payload: Mapping[str, object], expected: frozenset[str], label: str
) -> None:
    if not isinstance(payload, Mapping):
        raise HostControlValidationError(f"{label} must be an object")
    actual = set(payload)
    if actual != expected:
        raise HostControlValidationError(
            f"{label} fields differ: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _require_request_id(value: object) -> str:
    if type(value) is not str or not _REQUEST_ID.fullmatch(value):
        raise HostControlValidationError("request_id contains unsafe characters")
    return value


def _require_nonempty_string(value: object, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise HostControlValidationError(f"{label} must be a non-empty string")
    return value


def _parse_timestamp(value: object, label: str) -> datetime:
    if type(value) is not str or not value.strip():
        raise HostControlValidationError(f"{label} must be a non-empty string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HostControlValidationError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise HostControlValidationError(f"{label} must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def _require_json_value(value: object, label: str) -> None:
    if value is None or type(value) in {str, bool, int}:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise HostControlValidationError(f"{label} contains a non-finite number")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _require_json_value(item, f"{label}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise HostControlValidationError(f"{label} keys must be strings")
            _require_json_value(item, f"{label}.{key}")
        return
    raise HostControlValidationError(f"{label} contains a non-JSON value")


def _load_json(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HostControlValidationError(f"{label} is not valid UTF-8 JSON") from exc
    if type(value) is not dict:
        raise HostControlValidationError(f"{label} must be a JSON object")
    return value


def _canonical_request(request: HostControlRequest) -> str:
    return json.dumps(
        request.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _require_existing_directory(path: Path, label: str) -> Path:
    try:
        resolved = Path(path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise HostControlValidationError(f"{label} must be an existing directory") from exc
    if not resolved.is_dir():
        raise HostControlValidationError(f"{label} must be an existing directory")
    return resolved


def _require_profile_semantic_state(
    profile: RuntimeProfile,
    repo_root: Path,
    semantic_state_path: Path | None,
) -> Path | None:
    if profile is RuntimeProfile.OBSERVER:
        if semantic_state_path is not None:
            raise HostControlValidationError(
                "OBSERVER profile forbids a semantic state path"
            )
        return None
    if semantic_state_path is None:
        raise HostControlValidationError(
            f"{profile.value} profile requires a launch-bound semantic state path"
        )
    try:
        resolved = Path(semantic_state_path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise HostControlValidationError(
            "semantic state must be an existing regular file"
        ) from exc
    if not resolved.is_file():
        raise HostControlValidationError(
            "semantic state must be an existing regular file"
        )
    try:
        resolved.relative_to(repo_root)
    except ValueError:
        pass
    else:
        raise HostControlValidationError(
            "semantic state must be external to the repository"
        )
    from tools.codex_semantic_mvp.db import (
        SemanticDatabaseValidationError,
        validate_existing_database,
    )

    try:
        return validate_existing_database(resolved)
    except SemanticDatabaseValidationError as exc:
        raise HostControlValidationError(
            f"semantic state is not an initialized compatible HMASD database: {exc}"
        ) from exc


class HostControlChannel:
    """Atomic request inbox, single-host claims, and durable responses."""

    def __init__(
        self,
        control_home: Path,
        *,
        profile: RuntimeProfile,
        repo_root: Path,
        semantic_state_path: Path | None = None,
        max_request_age_seconds: float = DEFAULT_MAX_REQUEST_AGE_SECONDS,
        future_skew_seconds: float = DEFAULT_FUTURE_SKEW_SECONDS,
        poll_interval_seconds: float = 0.05,
    ) -> None:
        if not isinstance(profile, RuntimeProfile):
            raise HostControlValidationError("profile must be a RuntimeProfile")
        self.profile = profile
        self.repo_root = _require_existing_directory(repo_root, "repo root")
        self.semantic_state_path = _require_profile_semantic_state(
            profile,
            self.repo_root,
            semantic_state_path,
        )
        self.control_home = Path(control_home).resolve()
        self.inbox = self.control_home / "inbox"
        self.processing = self.control_home / "processing"
        self.outbox = self.control_home / "outbox"
        self.rejected = self.control_home / "rejected"
        for directory in (self.inbox, self.processing, self.outbox, self.rejected):
            directory.mkdir(parents=True, exist_ok=True)
        if max_request_age_seconds <= 0 or future_skew_seconds < 0 or poll_interval_seconds <= 0:
            raise ValueError("control timing values are invalid")
        self.max_request_age_seconds = float(max_request_age_seconds)
        self.future_skew_seconds = float(future_skew_seconds)
        self.poll_interval_seconds = float(poll_interval_seconds)
        # A request already in processing when this channel object is created
        # may have crossed a mutation boundary in an earlier host process.  It
        # is observable but must never be blindly submitted again.
        self._recovered_processing = {
            path.name for path in self.processing.glob("*.json")
        }
        self._recovered_request_ids: set[str] = set()

    def submit(self, request: HostControlRequest) -> HostControlRequest:
        _validate_request(request)
        existing = self._existing_request(request.request_id)
        if existing is not None:
            if _canonical_request(existing) != _canonical_request(request):
                self._record_conflict(request)
                raise HostControlConflictError(
                    f"request_id {request.request_id!r} conflicts with an existing request"
                )
            return existing
        lock = self.inbox / f".{request.request_id}.submit.lock"
        deadline = time.monotonic() + 5.0
        while True:
            try:
                descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(descriptor)
                break
            except FileExistsError:
                existing = self._existing_request(request.request_id)
                if existing is not None:
                    if _canonical_request(existing) != _canonical_request(request):
                        self._record_conflict(request)
                        raise HostControlConflictError(
                            f"request_id {request.request_id!r} conflicts with an existing request"
                        )
                    return existing
                if time.monotonic() >= deadline:
                    raise HostControlError("timed out waiting for request submission lock")
                time.sleep(0.01)
        try:
            existing = self._existing_request(request.request_id)
            if existing is not None:
                if _canonical_request(existing) != _canonical_request(request):
                    self._record_conflict(request)
                    raise HostControlConflictError(
                        f"request_id {request.request_id!r} conflicts with an existing request"
                    )
                return existing
            atomic_write_json(self._request_path(self.inbox, request.request_id), request.to_dict())
            return request
        finally:
            lock.unlink(missing_ok=True)

    def response(self, request_id: str) -> HostControlResponse | None:
        path = self._request_path(self.outbox, _require_request_id(request_id))
        if not path.exists():
            return None
        return parse_response(_load_json(path, "control response"))

    def write_response(self, response: HostControlResponse) -> HostControlResponse:
        _validate_response(response)
        existing = self.response(response.request_id)
        if existing is not None:
            if existing != response:
                raise HostControlConflictError("response already exists with different content")
            return existing
        if self._existing_request(response.request_id) is None:
            raise HostControlValidationError("response has no durable request")
        atomic_write_json(
            self._request_path(self.outbox, response.request_id), response.to_dict()
        )
        return response

    def claim_next(self) -> HostControlRequest | None:
        while self._recovered_processing:
            name = min(self._recovered_processing)
            self._recovered_processing.remove(name)
            processing_path = self.processing / name
            if not processing_path.exists():
                continue
            try:
                request = parse_request(_load_json(processing_path, "control request"))
                if processing_path.stem != request.request_id:
                    raise HostControlValidationError("request_id does not match its file name")
                if self.response(request.request_id) is not None:
                    continue
                self._recovered_request_ids.add(request.request_id)
                return request
            except HostControlValidationError as exc:
                self._reject_claim(processing_path, str(exc))
                continue
        # A queued STOP is an out-of-band containment command.  Inspect the
        # immutable, atomically-published request files only to establish
        # claim priority, then retain os.replace as the actual claim boundary.
        # Every claimed file is parsed and freshness-checked again below.
        def inbox_priority(path: Path) -> tuple[int, str]:
            try:
                candidate = parse_request(_load_json(path, "control request"))
                if path.stem != candidate.request_id:
                    return (1, path.name)
                self._require_fresh(candidate)
            except HostControlValidationError:
                return (1, path.name)
            return (
                0 if candidate.command is CommandKind.STOP else 1,
                path.name,
            )

        for inbox_path in sorted(self.inbox.glob("*.json"), key=inbox_priority):
            request = self._claim_inbox_path(inbox_path)
            if request is None:
                continue
            if request.command is not CommandKind.STOP:
                stop_request = self._claim_fresh_stop()
                if stop_request is not None:
                    # The STOP was published after the original inbox
                    # enumeration.  Put the mutation back before exposing the
                    # STOP to the dispatcher so it remains wholly unclaimed.
                    os.replace(
                        self.processing / inbox_path.name,
                        self.inbox / inbox_path.name,
                    )
                    return stop_request
            return request
        return None

    def _claim_inbox_path(self, inbox_path: Path) -> HostControlRequest | None:
        """Atomically claim and validate one immutable inbox request."""

        processing_path = self.processing / inbox_path.name
        try:
            os.replace(inbox_path, processing_path)
        except FileNotFoundError:
            return None
        try:
            request = parse_request(_load_json(processing_path, "control request"))
            if processing_path.stem != request.request_id:
                raise HostControlValidationError("request_id does not match its file name")
            self._require_fresh(request)
            return request
        except HostControlValidationError as exc:
            self._reject_claim(processing_path, str(exc))
            return None

    def _claim_fresh_stop(self) -> HostControlRequest | None:
        """Claim a newly published valid STOP without claiming other work."""

        for inbox_path in sorted(self.inbox.glob("*.json")):
            try:
                candidate = parse_request(_load_json(inbox_path, "control request"))
                if inbox_path.stem != candidate.request_id:
                    raise HostControlValidationError(
                        "request_id does not match its file name"
                    )
                self._require_fresh(candidate)
            except HostControlValidationError:
                # Invalid inbox entries are never fences.  Claiming them here
                # preserves the ordinary durable rejection behavior.
                self._claim_inbox_path(inbox_path)
                continue
            if candidate.command is not CommandKind.STOP:
                continue
            request = self._claim_inbox_path(inbox_path)
            if request is None:
                continue
            if request.command is CommandKind.STOP:
                return request
            # Request files are atomically published and immutable by
            # contract.  Still fail safely if a non-conforming writer changed
            # this file between inspection and claim.
            os.replace(
                self.processing / inbox_path.name,
                self.inbox / inbox_path.name,
            )
        return None

    def claim(self) -> HostControlRequest | None:
        """Compatibility spelling for claiming at most one inbox request."""

        return self.claim_next()

    async def dispatch(
        self,
        request: HostControlRequest,
        *,
        profile: RuntimeProfile,
        service: object,
        stop_event: asyncio.Event,
    ) -> HostControlResponse:
        if profile is not self.profile:
            raise HostControlValidationError(
                "dispatch profile does not match the immutable host channel profile"
            )
        require_command_allowed(profile, request.command)
        if stop_event.is_set() and request.command in _MUTATING_COMMANDS:
            raise HostControlValidationError("host is stopping and accepts no new mutation")
        payload, status, error = await _dispatch_allowlisted(
            request,
            profile=profile,
            service=service,
            stop_event=stop_event,
            repo_root=self.repo_root,
            semantic_state_path=self.semantic_state_path,
        )
        return HostControlResponse(
            schema=CONTROL_RESPONSE_SCHEMA,
            request_id=request.request_id,
            status=status,
            payload=_json_object(payload),
            error=error,
            completed_at=_now(),
        )

    async def serve(
        self,
        *,
        profile: RuntimeProfile,
        service: object,
        stop_event: asyncio.Event,
    ) -> None:
        while not stop_event.is_set():
            request = self.claim_next()
            if request is None:
                try:
                    await asyncio.wait_for(
                        stop_event.wait(), timeout=self.poll_interval_seconds
                    )
                except asyncio.TimeoutError:
                    pass
                continue
            existing = self.response(request.request_id)
            if existing is not None:
                continue
            recovered = request.request_id in self._recovered_request_ids
            self._recovered_request_ids.discard(request.request_id)
            try:
                if recovered and request.command in _REPLAY_FENCED_COMMANDS:
                    response = HostControlResponse(
                        schema=CONTROL_RESPONSE_SCHEMA,
                        request_id=request.request_id,
                        status="SUBMISSION_UNCERTAIN",
                        payload={"recovered_processing_request": True},
                        error=(
                            "request was claimed by an earlier host process; durable state "
                            "must be inspected and the mutation will not be resent"
                        ),
                        completed_at=_now(),
                    )
                else:
                    response = await self.dispatch(
                        request,
                        profile=profile,
                        service=service,
                        stop_event=stop_event,
                    )
            except Exception as exc:
                message = str(exc) or type(exc).__name__
                lowered = message.lower()
                status = (
                    "SUBMISSION_UNCERTAIN"
                    if "uncertain" in lowered or "do not retry" in lowered
                    else "REJECTED"
                    if isinstance(exc, (HostControlValidationError, ValueError))
                    else "ERROR"
                )
                response = HostControlResponse(
                    schema=CONTROL_RESPONSE_SCHEMA,
                    request_id=request.request_id,
                    status=status,
                    payload={},
                    error=message,
                    completed_at=_now(),
                )
            self.write_response(response)
            if stop_event.is_set():
                break

    def _existing_request(self, request_id: str) -> HostControlRequest | None:
        request_id = _require_request_id(request_id)
        for directory in (self.processing, self.inbox):
            path = self._request_path(directory, request_id)
            if path.exists():
                return parse_request(_load_json(path, "control request"))
        return None

    def _require_fresh(self, request: HostControlRequest) -> None:
        created = _parse_timestamp(request.created_at, "control request.created_at")
        age = (datetime.now(timezone.utc) - created).total_seconds()
        if age > self.max_request_age_seconds:
            raise HostControlValidationError("control request is stale")
        if age < -self.future_skew_seconds:
            raise HostControlValidationError("control request timestamp is in the future")

    def _reject_claim(self, path: Path, reason: str) -> None:
        destination = self.rejected / path.name
        if destination.exists():
            destination = self.rejected / f"{path.stem}.{uuid.uuid4().hex}.json"
        os.replace(path, destination)
        atomic_write_json(
            destination.with_suffix(destination.suffix + ".reason.json"),
            {"schema": "HMASD_SUPERVISOR_CONTROL_REJECTION_V1", "error": reason},
        )

    def _record_conflict(self, request: HostControlRequest) -> None:
        destination = self.rejected / (
            f"{request.request_id}.conflict.{uuid.uuid4().hex}.json"
        )
        atomic_write_json(destination, request.to_dict())

    @staticmethod
    def _request_path(directory: Path, request_id: str) -> Path:
        return directory / f"{_require_request_id(request_id)}.json"


async def _dispatch_allowlisted(
    request: HostControlRequest,
    *,
    profile: RuntimeProfile,
    service: object,
    stop_event: asyncio.Event,
    repo_root: Path,
    semantic_state_path: Path | None,
) -> tuple[dict[str, object], str, str | None]:
    command = request.command
    arguments = request.arguments
    store = getattr(service, "store", None)
    if store is None:
        raise HostControlValidationError("service has no observer store")

    if command is CommandKind.STATUS:
        _require_arguments(arguments, frozenset())
        return _mechanical_status(service, profile), "OK", None
    if command is CommandKind.STOP:
        _require_arguments(arguments, frozenset())
        stop_event.set()
        return {"stopping": True, "run_id": str(getattr(service, "run_id", "") or "")}, "OK", None
    if command is CommandKind.INSPECT:
        return _inspect(arguments, store), "OK", None
    if command is CommandKind.ARM_SINGLE_WAKE:
        _require_arguments(arguments, frozenset())
        return (
            {"armed": False, "implemented": False},
            "NOT_IMPLEMENTED",
            "ARM_SINGLE_WAKE is reserved for Task 25 and did not arm a wake",
        )

    client = getattr(service, "client", None)
    if client is None:
        raise HostControlValidationError("live App Server client is unavailable")

    if command in {
        CommandKind.MANAGED_CREATE,
        CommandKind.MANAGED_ADOPT,
        CommandKind.MANAGED_VERIFY,
        CommandKind.MANAGED_TURN,
        CommandKind.MANAGED_SUSPEND,
        CommandKind.MANAGED_REVOKE,
        CommandKind.MAILBOX_ENQUEUE,
        CommandKind.MAILBOX_DELIVER_ONCE,
    }:
        from .binding_store import BindingStore
        from .semantic_bridge import SemanticBridge

        semantic_state = _require_profile_semantic_state(
            profile,
            repo_root,
            semantic_state_path,
        )
        if semantic_state is None:  # defensive: mutating commands are never OBSERVER commands
            raise HostControlValidationError(
                "this host profile has no launch-bound semantic state"
            )
        bridge = SemanticBridge(semantic_state, store)
        try:
            bindings = BindingStore(store, bridge)
            if command in {
                CommandKind.MANAGED_CREATE,
                CommandKind.MANAGED_ADOPT,
                CommandKind.MANAGED_VERIFY,
                CommandKind.MANAGED_TURN,
                CommandKind.MANAGED_SUSPEND,
                CommandKind.MANAGED_REVOKE,
            }:
                return await _dispatch_managed(
                    request,
                    bindings=bindings,
                    bridge=bridge,
                    client=client,
                    repo_root=repo_root,
                )
            return await _dispatch_mailbox_mutation(
                request, bindings=bindings, bridge=bridge, client=client
            )
        finally:
            bridge.close()

    if command is CommandKind.MAILBOX_LIST:
        from .mailbox_store import MailboxStore

        _require_arguments(arguments, frozenset(), frozenset({"target_actor_context_id"}))
        target = arguments.get("target_actor_context_id")
        if target is not None:
            target = _require_nonempty_string(target, "arguments.target_actor_context_id")
        rows = MailboxStore(store).list_messages(target_actor_context_id=target)
        return {"messages": [_json_object(asdict(item)) for item in rows]}, "OK", None

    raise HostControlValidationError(f"no dispatcher for command {command.value}")


async def _dispatch_managed(request, *, bindings, bridge, client, repo_root: Path):
    from .command_gateway import CommandGateway
    from .managed_models import ManagedIntentKind
    from .managed_runtime import ManagedRuntime
    from .managed_turns import ManagedTurns
    from .provisioning import ManagedProvisioner

    command = request.command
    args = request.arguments
    turns = ManagedTurns(bindings, client)
    provisioner = ManagedProvisioner(bindings, client)

    if command is CommandKind.MANAGED_CREATE:
        common = frozenset({"actor_context_id"})
        _require_arguments(args, common | {"confirm_global_memory_disabled"})
        snapshot = _snapshot_for_actor(
            bridge, _require_arg_string(args, "actor_context_id")
        )
        _require_true(args, "confirm_global_memory_disabled")
        binding_id = provisioner.prepare(
            snapshot,
            repo_root=repo_root,
            operator=request.operator,
        )
        provisioner.confirm_global_memory_disabled(binding_id, operator=request.operator)
        thread_id = await provisioner.create_fresh_thread(binding_id)
        return {"binding_id": binding_id, "thread_id": thread_id}, "OK", None

    if command is CommandKind.MANAGED_ADOPT:
        common = frozenset({"actor_context_id"})
        _require_arguments(
            args,
            common
            | {
                "thread_id",
                "allow_existing_history",
                "confirm_history_nonauthoritative",
                "confirm_global_memory_disabled",
            },
        )
        snapshot = _snapshot_for_actor(
            bridge, _require_arg_string(args, "actor_context_id")
        )
        _require_true(args, "allow_existing_history")
        _require_true(args, "confirm_history_nonauthoritative")
        _require_true(args, "confirm_global_memory_disabled")
        binding_id = await provisioner.adopt_existing_thread(
            snapshot,
            thread_id=_require_arg_string(args, "thread_id"),
            repo_root=repo_root,
            operator=request.operator,
            allow_existing_history=True,
            confirm_history_nonauthoritative=True,
        )
        provisioner.confirm_global_memory_disabled(binding_id, operator=request.operator)
        return {"binding_id": binding_id, "thread_id": args["thread_id"]}, "OK", None

    binding_id = _require_arg_string(args, "binding_id")
    snapshot = _snapshot_for_binding(bindings, bridge, binding_id)
    common = frozenset({"binding_id"})

    if command is CommandKind.MANAGED_VERIFY:
        _require_arguments(args, common, frozenset({"raw_message_seq"}))
        raw_seq = args.get("raw_message_seq")
        if raw_seq is not None and (type(raw_seq) is not int or raw_seq <= 0):
            raise HostControlValidationError("arguments.raw_message_seq must be a positive integer")
        runtime = ManagedRuntime(
            bindings, turns, CommandGateway(bindings, bridge), bridge
        )
        if raw_seq is None:
            submitted = await runtime.submit_verification(binding_id, snapshot)
            turn_id = str(submitted.get("app_server_turn_id") or "")
            if not turn_id:
                raise HostControlError("verification submission returned no turn id; do not retry")
            raw_seq = await _await_completed_item(runtime, binding_id, turn_id)
        result = runtime.complete_activation(binding_id, raw_message_seq=raw_seq)
        return _json_object(result), "OK", None

    if command is CommandKind.MANAGED_TURN:
        _require_arguments(args, common | {"text"})
        text = _require_arg_string(args, "text")
        intent_id = turns.prepare(
            binding_id,
            intent_kind=ManagedIntentKind.MANUAL_OPERATOR,
            input_ref=f"host-control:{request.request_id}",
            checkpoint_id=snapshot.checkpoint_id,
            expected_state_version=snapshot.state_version,
            expected_epoch_id=snapshot.epoch_id,
            expected_epoch_revision=snapshot.epoch_revision,
        )
        result = await turns.submit(intent_id, text)
        return {"turn_intent_id": intent_id, "submission": _json_object(result)}, "OK", None

    if command is CommandKind.MANAGED_SUSPEND:
        _require_arguments(args, common)
        return {"binding": _json_object(asdict(bindings.suspend(binding_id)))}, "OK", None
    if command is CommandKind.MANAGED_REVOKE:
        _require_arguments(args, common)
        return {"binding": _json_object(asdict(bindings.revoke(binding_id)))}, "OK", None
    raise HostControlValidationError(f"unsupported managed command {command.value}")


async def _dispatch_mailbox_mutation(request, *, bindings, bridge, client):
    from .mailbox_models import MailboxMessageKind, MailboxSourceSystem
    from .mailbox_store import MailboxStore
    from .managed_runtime import ManagedRuntime
    from .managed_turns import ManagedTurns
    from .command_gateway import CommandGateway

    args = request.arguments
    mailbox = MailboxStore(bindings.store)
    if request.command is CommandKind.MAILBOX_ENQUEUE:
        required = frozenset(
            {
                "source_actor_context_id",
                "target_actor_context_id",
                "message_kind",
                "subject_ref",
                "payload_ref",
                "priority",
            }
        )
        _require_arguments(args, required, frozenset({"source_event_key"}))
        source = _snapshot_for_actor(
            bridge, _require_arg_string(args, "source_actor_context_id")
        )
        target = _snapshot_for_actor(
            bridge, _require_arg_string(args, "target_actor_context_id")
        )
        if source.actor_context_id == target.actor_context_id:
            raise HostControlValidationError("mailbox source and target must differ")
        _require_bound_actor(bindings, source)
        _require_bound_actor(bindings, target)
        priority = args["priority"]
        if type(priority) is not int:
            raise HostControlValidationError("arguments.priority must be an integer")
        try:
            kind = MailboxMessageKind(args["message_kind"])
        except (TypeError, ValueError) as exc:
            raise HostControlValidationError("arguments.message_kind is invalid") from exc
        source_key = args.get("source_event_key")
        if source_key is None:
            source_key = f"host-control:{request.request_id}"
        message = mailbox.enqueue(
            source_system=MailboxSourceSystem.MANAGED_ACTOR.value,
            source_event_key=_require_nonempty_string(source_key, "arguments.source_event_key"),
            sender_actor_context_id=source.actor_context_id,
            target_actor_context_id=target.actor_context_id,
            message_kind=kind,
            subject_ref=_require_arg_string(args, "subject_ref"),
            payload_ref=_require_arg_string(args, "payload_ref"),
            direction_id=target.direction_id,
            epoch_id=target.epoch_id,
            priority=priority,
        )
        return {"message": _json_object(asdict(message))}, "OK", None

    _require_arguments(
        args,
        frozenset({"target_actor_context_id"}),
    )
    target = _snapshot_for_actor(
        bridge, _require_arg_string(args, "target_actor_context_id")
    )
    _require_bound_actor(bindings, target)
    runtime = ManagedRuntime(
        bindings,
        ManagedTurns(bindings, client),
        CommandGateway(bindings, bridge, mailbox),
        bridge,
    )
    instance_id = f"host-control:{request.request_id}"
    scheduler = runtime.scheduler(mailbox, instance_id=instance_id)
    await scheduler.recovery.recover()
    scanned = scheduler.scanner.scan()
    target_binding = bindings.binding_for_actor(target.actor_context_id)
    if target_binding is None:
        raise HostControlValidationError("target actor has no managed binding")
    from .scheduler_leases import LeaseError

    try:
        lease = scheduler.leases.acquire(target_binding.binding_id, instance_id)
    except LeaseError:
        result = {"scanned": scanned, "scheduled": None, "lease": "unavailable"}
    else:
        try:
            scheduled = await scheduler.schedule_binding(
                target_binding.binding_id,
                lease_generation=int(lease["generation"]),
            )
            result = {"scanned": scanned, "scheduled": scheduled}
        finally:
            scheduler.leases.release(
                target_binding.binding_id,
                instance_id,
                generation=int(lease["generation"]),
            )
    return _json_object(result), "OK", None


async def _await_completed_item(runtime, binding_id: str, turn_id: str) -> int:
    binding = runtime.bindings.get(binding_id)
    if binding is None or not binding.thread_id:
        raise HostControlValidationError("verification binding has no thread")
    deadline = asyncio.get_running_loop().time() + 1800.0
    while True:
        raw_seq = runtime._latest_completed_seq(binding.thread_id, turn_id)
        if raw_seq is not None:
            completed = runtime.bindings.store.connection.execute(
                "SELECT 1 FROM turn_snapshots WHERE thread_id = ? AND turn_id = ? AND status = 'completed'",
                (binding.thread_id, turn_id),
            ).fetchone()
            if completed is not None:
                return raw_seq
        owner = runtime.turns._owner()
        if owner.terminated:
            raise HostControlError("App Server session terminated during verification")
        if asyncio.get_running_loop().time() >= deadline:
            raise HostControlError("verification completion timed out; do not retry")
        await asyncio.sleep(0.1)


def _snapshot_for_actor(bridge, actor_context_id: str):
    from .managed_models import ManagedActorKind

    try:
        snapshot = bridge.snapshot(actor_context_id)
        ManagedActorKind(snapshot.actor_kind)
    except ValueError as exc:
        raise HostControlValidationError("only OPERATIONAL_ROOT and PORTFOLIO may be managed") from exc
    return snapshot


def _snapshot_for_binding(bindings, bridge, binding_id: str):
    binding = bindings.get(binding_id)
    if binding is None:
        raise HostControlValidationError("unknown binding")
    snapshot = _snapshot_for_actor(bridge, binding.actor_context_id)
    _require_binding_identity(bindings, binding_id, snapshot)
    return snapshot


def _require_binding_identity(bindings, binding_id, snapshot) -> None:
    binding = bindings.get(binding_id)
    if binding is None:
        raise HostControlValidationError("unknown binding")
    if (
        binding.actor_context_id != snapshot.actor_context_id
        or binding.actor_kind.value != snapshot.actor_kind
        or binding.semantic_scope_key != snapshot.scope_key
    ):
        raise HostControlValidationError("binding does not match the exact actor snapshot")


def _require_bound_actor(bindings, snapshot) -> None:
    binding = bindings.binding_for_actor(snapshot.actor_context_id)
    if binding is None:
        raise HostControlValidationError("actor has no managed binding")
    _require_binding_identity(bindings, binding.binding_id, snapshot)


def _mechanical_status(service: object, profile: RuntimeProfile) -> dict[str, object]:
    store = getattr(service, "store")
    return {
        "run_id": str(getattr(service, "run_id", "") or ""),
        "host_process_id": os.getpid(),
        "app_server_child_process_id": getattr(
            getattr(service, "transport", None), "process_id", None
        ),
        "profile": profile.value,
        "stopped": bool(getattr(service, "_stopped", False)),
        "thread_count": _table_count(store, "thread_snapshots"),
        "active_binding_count": _where_count(
            store, "managed_actor_bindings", "binding_state = 'ACTIVE'"
        ),
        "open_wake_batch_count": _where_count(
            store,
            "wake_batches",
            "state IN ('PREPARED','SUBMITTING','SUBMITTED','SUBMISSION_UNCERTAIN','ACTIVE')",
        ),
        "automatic_wake": False,
    }


def _inspect(arguments: Mapping[str, object], store) -> dict[str, object]:
    from .timeline import binding_timeline, mailbox_timeline, thread_timeline, wake_timeline

    selectors = frozenset(
        {"thread_id", "binding_id", "target_actor_context_id", "wake_batch_id"}
    )
    _require_arguments(arguments, frozenset(), selectors)
    supplied = [key for key in selectors if key in arguments]
    if len(supplied) > 1:
        raise HostControlValidationError("INSPECT accepts at most one selector")
    if not supplied:
        return {
            "thread_count": _table_count(store, "thread_snapshots"),
            "reconciliation_count": _table_count(store, "reconciliation_runs"),
            "binding_count": _table_count(store, "managed_actor_bindings"),
            "mailbox_count": _table_count(store, "mailbox_messages"),
            "wake_batch_count": _table_count(store, "wake_batches"),
        }
    key = supplied[0]
    value = _require_nonempty_string(arguments[key], f"arguments.{key}")
    if key == "thread_id":
        return {"thread": _json_object(thread_timeline(store, value))}
    if key == "binding_id":
        return {"binding": _json_value(binding_timeline(store, value))}
    if key == "target_actor_context_id":
        return {"mailbox": _json_value(mailbox_timeline(store, target_actor_context_id=value))}
    return {"wake": _json_value(wake_timeline(store, value))}


def _require_arguments(
    arguments: Mapping[str, object],
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> None:
    actual = set(arguments)
    allowed = required | optional
    if not required.issubset(actual) or not actual.issubset(allowed):
        raise HostControlValidationError(
            f"command arguments differ: missing={sorted(required - actual)}, "
            f"extra={sorted(actual - allowed)}"
        )


def _require_arg_string(arguments: Mapping[str, object], key: str) -> str:
    if key not in arguments:
        raise HostControlValidationError(f"missing arguments.{key}")
    return _require_nonempty_string(arguments[key], f"arguments.{key}")


def _require_true(arguments: Mapping[str, object], key: str) -> None:
    if arguments.get(key) is not True:
        raise HostControlValidationError(f"arguments.{key} must be exactly true")


def _table_count(store, table: str) -> int:
    return int(store.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _where_count(store, table: str, where: str) -> int:
    return int(
        store.connection.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]
    )


def _json_object(value: object) -> dict[str, object]:
    converted = _json_value(value)
    if type(converted) is not dict:
        raise HostControlValidationError("dispatcher payload must be an object")
    return converted


def _json_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if value is None or type(value) in {str, bool, int, float}:
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    raise HostControlValidationError(f"dispatcher returned non-JSON value {type(value).__name__}")


__all__ = (
    "CONTROL_REQUEST_SCHEMA",
    "CONTROL_RESPONSE_SCHEMA",
    "HostControlChannel",
    "HostControlConflictError",
    "HostControlError",
    "HostControlRequest",
    "HostControlResponse",
    "HostControlValidationError",
    "parse_request",
    "parse_response",
)
