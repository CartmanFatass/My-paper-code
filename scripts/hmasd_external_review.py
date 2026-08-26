#!/usr/bin/env python3
"""Root-only helpers for deterministic HMASD external-review boundaries.

This module deliberately contains no provider transport, browser, or Agentify
ledger code.  Transport agents return an operation reference and an immutable
Agentify natural-completion archive; Root uses these local-only helpers to
validate, partition, import, and render those values.
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

try:
    from scripts import hmasd_platform
except ImportError:
    import hmasd_platform


ROUND_ID_HEX_LENGTH = 20
ARCHIVE_SCHEMA = "agentify_review_natural_completion_archive_v1"
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_OWNED_ARCHIVE_ROOT = PurePosixPath("docs/external-review/directions")
_OWNED_ARCHIVE_FILENAME = "NATURAL_COMPLETION_ARCHIVE.json"
PROMPT_FILES = (
    "GEMINI_DIVERGENT_PROMPT.md",
    "PRO_DIVERGENT_PROMPT.md",
    "PRO_CONVERGENCE_PROMPT.md",
)
_REQUIRED_ARCHIVE_FIELDS = (
    "schema",
    "operationId",
    "idempotencyKey",
    "stableKey",
    "provider",
    "model",
    "conversationUrl",
    "conversationId",
    "terminalState",
    "sendCount",
    "sendActionCount",
    "userMessageId",
    "assistantMessageId",
    "responseSha256",
    "responseText",
    "completedAt",
)
_REQUIRED_OPERATION_FIELDS = (
    "direction_id",
    "round_id",
    "provider",
    "stable_key",
    "session_id",
    "operation_id",
    "idempotency_key",
    "request_fingerprint",
    "commitment_state",
    "prompt_sha256",
    "question_sha256",
    "evidence_sha256",
    "archive_path",
    "archive_sha256",
)
_COMMITTED_STATES = frozenset({"COMMITTED", "NATURAL_COMPLETION_VERIFIED"})
_PROVIDER_TARGETS = {
    "chatgpt": ("chatgpt.com", "c"),
    "gemini": ("gemini.google.com", "app"),
}
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_DIRECTION_ID = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
_ROUND_ID = re.compile(rf"[0-9a-f]{{{ROUND_ID_HEX_LENGTH}}}\Z")
_SESSION_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}\Z")


class ExternalReviewError(ValueError):
    """A directly observed external-review contract violation."""


class ArchiveConflict(ExternalReviewError):
    """The immutable destination already contains a different archive."""


class CommitmentUnknown(ExternalReviewError):
    """Agentify did not establish whether a submission committed."""


class PathRefusal(ExternalReviewError):
    """A destination cannot be safely treated as an owned regular file."""


@dataclass(frozen=True)
class ArchiveRecord:
    """Validated archive data and the bytes from which it was read."""

    data: dict[str, Any]
    raw_bytes: bytes
    archive_sha256: str
    response_sha256: str
    source_path: Path | None = None


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            separators=(",", ": "),
        ).encode("utf-8")
        + b"\n"
    )


def _json_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ExternalReviewError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_json(raw: bytes, *, label: str) -> Any:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExternalReviewError(f"{label} is not UTF-8") from exc
    try:
        return json.loads(text, object_pairs_hook=_json_object_pairs)
    except (json.JSONDecodeError, ExternalReviewError) as exc:
        raise ExternalReviewError(f"{label} is not valid JSON: {exc}") from exc


def _input_value(value: Any, *, label: str) -> tuple[Any, bytes | None, Path | None]:
    """Load a path, inline JSON value, or already-decoded value.

    Returning source bytes is important for the foreign archive: Root must
    copy Agentify's exact bytes rather than serializing a modified object.
    """

    if isinstance(value, Mapping):
        return dict(value), None, None
    if isinstance(value, (list, tuple)):
        return list(value), None, None
    if isinstance(value, os.PathLike):
        path = Path(value)
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise ExternalReviewError(f"cannot read {label}: {path}: {exc}") from exc
        return _parse_json(raw, label=label), raw, path
    if not isinstance(value, str):
        raise ExternalReviewError(f"{label} must be a JSON path, JSON text, or object")

    stripped = value.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return _parse_json(value.encode("utf-8"), label=label), None, None
    path = Path(value)
    try:
        is_file = path.is_file()
    except OSError as exc:
        raise ExternalReviewError(f"cannot inspect {label}: {value}: {exc}") from exc
    if not is_file:
        raise ExternalReviewError(f"{label} is not a JSON file: {value}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ExternalReviewError(f"cannot read {label}: {path}: {exc}") from exc
    return _parse_json(raw, label=label), raw, path


def _require_sha(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ExternalReviewError(f"{label} must be a lowercase SHA-256 value")
    return value


def _require_text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExternalReviewError(f"{label} must be a non-empty string")
    if "\x00" in value:
        raise ExternalReviewError(f"{label} contains NUL")
    return value


def _require_count(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 1:
        raise ExternalReviewError(f"{label} must be an integer from 0 through 1")
    return value


def _validate_timestamp(value: Any) -> str:
    text = _require_text(value, label="completedAt")
    if not text.endswith("Z"):
        raise ExternalReviewError("completedAt must be a UTC RFC 3339 timestamp ending in Z")
    try:
        _datetime.datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise ExternalReviewError("completedAt is not a UTC RFC 3339 timestamp") from exc
    return text


def _require_provider(value: Any, *, label: str) -> str:
    provider = _require_text(value, label=label)
    if provider not in _PROVIDER_TARGETS:
        raise ExternalReviewError(f"{label} must be one of: {', '.join(sorted(_PROVIDER_TARGETS))}")
    return provider


def _require_session_id(value: Any, *, label: str) -> str:
    session_id = _require_text(value, label=label)
    if _SESSION_ID.fullmatch(session_id) is None:
        raise ExternalReviewError(f"{label} is not a stable provider session identifier")
    return session_id


def _owned_archive_path(direction_id: str, round_id_value: str, provider: str) -> PurePosixPath:
    return _OWNED_ARCHIVE_ROOT / direction_id / round_id_value / provider / _OWNED_ARCHIVE_FILENAME


def _validate_archive_target(provider: str, session_id: str, conversation_url: Any) -> str:
    url = _require_text(conversation_url, label="conversationUrl")
    host, marker = _PROVIDER_TARGETS[provider]
    expected = f"https://{host}/{marker}/{session_id}"
    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        raise ExternalReviewError("conversationUrl is not a valid provider target") from exc
    if (
        url != expected
        or parsed.scheme != "https"
        or parsed.netloc != host
        or parsed.path != f"/{marker}/{session_id}"
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ExternalReviewError("conversationUrl does not match the provider and stable session identity")
    return url


def _validate_operation_ref(operation_ref: Any) -> dict[str, Any]:
    if not isinstance(operation_ref, Mapping):
        raise ExternalReviewError("operation reference must be a JSON object")
    result = dict(operation_ref)
    missing = [key for key in _REQUIRED_OPERATION_FIELDS if key not in result]
    if missing:
        raise ExternalReviewError("operation reference is missing required fields: " + ", ".join(missing))

    commitment = _require_text(result["commitment_state"], label="commitment_state")
    normalised_commitment = commitment.upper().replace("-", "_")
    if normalised_commitment in {"UNKNOWN", "COMMITMENT_UNKNOWN", "UNKNOWN_COMMITMENT"}:
        raise CommitmentUnknown("Agentify commitment is unknown; no resend or archive import is allowed")
    if commitment not in _COMMITTED_STATES:
        raise ExternalReviewError("commitment_state must be COMMITTED or NATURAL_COMPLETION_VERIFIED")

    direction_id = result["direction_id"]
    if not isinstance(direction_id, str) or _DIRECTION_ID.fullmatch(direction_id) is None:
        raise ExternalReviewError("operation reference direction_id must match [a-z0-9][a-z0-9_-]{1,63}")
    round_id_value = result["round_id"]
    if not isinstance(round_id_value, str) or _ROUND_ID.fullmatch(round_id_value) is None:
        raise ExternalReviewError(f"operation reference round_id must be {ROUND_ID_HEX_LENGTH} lowercase hex characters")
    provider = _require_provider(result["provider"], label="operation reference provider")
    for key in ("stable_key", "operation_id", "idempotency_key"):
        _require_text(result[key], label=f"operation reference {key}")
    _require_session_id(result["session_id"], label="operation reference session_id")
    for key in ("request_fingerprint", "prompt_sha256", "question_sha256", "evidence_sha256", "archive_sha256"):
        _require_sha(result[key], label=f"operation reference {key}")

    expected_archive_path = _owned_archive_path(direction_id, round_id_value, provider).as_posix()
    archive_path = result["archive_path"]
    if not isinstance(archive_path, str) or archive_path != expected_archive_path:
        raise ExternalReviewError(
            "operation reference archive_path does not match its direction, round, and provider ownership"
        )
    return result


def validate_operation_ref(operation_ref: Any) -> dict[str, Any]:
    """Validate and return a detached operation-reference copy without side effects."""

    return dict(_validate_operation_ref(operation_ref))


def _validate_archive_data(archive: Any) -> dict[str, Any]:
    if not isinstance(archive, Mapping):
        raise ExternalReviewError("archive must be a JSON object")
    data = dict(archive)
    missing = [key for key in _REQUIRED_ARCHIVE_FIELDS if key not in data]
    if missing:
        raise ExternalReviewError("archive is missing required fields: " + ", ".join(missing))
    if data.get("schema") != ARCHIVE_SCHEMA:
        raise ExternalReviewError(f"archive schema must be {ARCHIVE_SCHEMA}")
    forbidden = sorted(key for key in ("schema_version", "revision", "writer") if key in data)
    if forbidden:
        raise ExternalReviewError("foreign archive must not contain HMASD fields: " + ", ".join(forbidden))

    for key in (
        "operationId",
        "idempotencyKey",
        "stableKey",
        "model",
        "userMessageId",
        "assistantMessageId",
    ):
        _require_text(data[key], label=key)
    provider = _require_provider(data["provider"], label="provider")
    session_id = _require_session_id(data["conversationId"], label="conversationId")
    _validate_archive_target(provider, session_id, data["conversationUrl"])
    if data["terminalState"] != "NATURAL_COMPLETION_VERIFIED":
        raise ExternalReviewError("archive terminalState is not a verified natural completion")
    _require_count(data["sendCount"], label="sendCount")
    _require_count(data["sendActionCount"], label="sendActionCount")
    response_text = data["responseText"]
    if not isinstance(response_text, str):
        raise ExternalReviewError("responseText must be a string")
    declared_sha = _require_sha(data["responseSha256"], label="responseSha256")
    computed_sha = hashlib.sha256(response_text.encode("utf-8")).hexdigest()
    if declared_sha != computed_sha:
        raise ExternalReviewError("responseSha256 does not match responseText UTF-8 bytes")
    _validate_timestamp(data["completedAt"])
    return data


def _validate_archive_identity(
    operation: Mapping[str, Any],
    archive: Mapping[str, Any],
    archive_sha256: str,
) -> None:
    for operation_key, archive_key in (
        ("provider", "provider"),
        ("stable_key", "stableKey"),
        ("session_id", "conversationId"),
        ("operation_id", "operationId"),
        ("idempotency_key", "idempotencyKey"),
    ):
        if operation[operation_key] != archive[archive_key]:
            raise ExternalReviewError(f"archive {archive_key} does not match operation reference {operation_key}")
    if operation["archive_sha256"] != archive_sha256:
        raise ExternalReviewError("archive bytes do not match operation reference archive_sha256")


def _archive_record(operation_ref: Any | None, archive: Any) -> ArchiveRecord:
    operation: dict[str, Any] | None
    if operation_ref is None:
        operation = None
    else:
        operation_value, _, _ = _input_value(operation_ref, label="operation reference")
        operation = _validate_operation_ref(operation_value)
    data, raw, source_path = _input_value(archive, label="archive")
    validated = _validate_archive_data(data)
    if raw is None:
        raw = _canonical_json(validated)
    archive_sha256 = hashlib.sha256(raw).hexdigest()
    if operation is not None:
        _validate_archive_identity(operation, validated, archive_sha256)
    return ArchiveRecord(
        data=validated,
        raw_bytes=raw,
        archive_sha256=archive_sha256,
        response_sha256=validated["responseSha256"],
        source_path=source_path,
    )


def round_id(
    direction_id: str,
    question_sha256: str,
    evidence_set_sha256: str,
    workflow_version: str,
) -> str:
    """Return the deterministic 20-hex identity for a frozen review round."""

    if not isinstance(direction_id, str) or _DIRECTION_ID.fullmatch(direction_id) is None:
        raise ExternalReviewError("direction_id must match [a-z0-9][a-z0-9_-]{1,63}")
    question = _require_sha(question_sha256, label="question_sha256")
    evidence = _require_sha(evidence_set_sha256, label="evidence_set_sha256")
    workflow = _require_text(workflow_version, label="workflow_version")
    if "\n" in workflow or "\r" in workflow:
        raise ExternalReviewError("workflow_version cannot contain a line break")
    material = f"{direction_id}\n{question}\n{evidence}\n{workflow}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:ROUND_ID_HEX_LENGTH]


def _normalise_prompt(value: str) -> str:
    return " ".join(value.split()).casefold()


def _is_alias(path: Path) -> bool:
    """Recognize POSIX symlinks and Windows junction/reparse aliases."""

    return hmasd_platform.is_reparse_or_symlink(path)


def _read_prompt(round_dir: Path, filename: str) -> tuple[Path, str]:
    path = round_dir / filename
    if not path.is_file() or _is_alias(path):
        raise ExternalReviewError(f"missing prompt file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ExternalReviewError(f"cannot read prompt file {path}: {exc}") from exc
    if not text.strip():
        raise ExternalReviewError(f"prompt file is empty: {path}")
    return path, text


def _reject_prompt_references(text: str, patterns: Sequence[str], *, label: str) -> None:
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            raise ExternalReviewError(f"{label} contains a forbidden provider reference: {pattern}")


def validate_prompts(round_dir: os.PathLike[str] | str) -> dict[str, Any]:
    """Validate provider separation and the Pro convergence isolation boundary."""

    directory = Path(round_dir)
    if not directory.is_dir() or _is_alias(directory):
        raise ExternalReviewError(f"round directory is not a regular directory: {directory}")
    loaded = {name: _read_prompt(directory, name) for name in PROMPT_FILES}
    gemini = loaded["GEMINI_DIVERGENT_PROMPT.md"][1]
    pro = loaded["PRO_DIVERGENT_PROMPT.md"][1]
    convergence = loaded["PRO_CONVERGENCE_PROMPT.md"][1]

    if _normalise_prompt(gemini) == _normalise_prompt(pro):
        raise ExternalReviewError("Gemini and Pro divergent prompts must remain separate")
    _reject_prompt_references(
        gemini,
        (
            r"PRO_DIVERGENT_PROMPT\.md",
            r"pro[-_ ]divergent",
            r"PRO_CONVERGENCE_PROMPT\.md",
            r"pro[-_ ]convergence",
            r"\bchatgpt\b",
        ),
        label="Gemini divergent prompt",
    )
    _reject_prompt_references(
        pro,
        (
            r"GEMINI_DIVERGENT_PROMPT\.md",
            r"gemini[-_ ]divergent",
            r"\bgemini\b",
        ),
        label="Pro divergent prompt",
    )

    convergence_patterns = (
        r"GEMINI_DIVERGENT_PROMPT\.md",
        r"PRO_DIVERGENT_PROMPT\.md",
        r"(?:^|[/\\])gemini(?:[/\\])",
        r"(?:^|[/\\])pro[-_]divergent(?:[/\\])",
        r"NATURAL_COMPLETION_ARCHIVE\.json",
        r"\b(?:conversation(?:id|url)?|operationid|idempotencykey|stablekey)\b",
        r"\b(?:responseSha256|responseText|assistantMessageId|userMessageId)\b",
        r"https?://",
        r"\bgemini\b",
        r"\bchatgpt\b",
    )
    _reject_prompt_references(convergence, convergence_patterns, label="Pro convergence prompt")
    normalised_convergence = _normalise_prompt(convergence)
    for label, text in (("Gemini divergent prompt", gemini), ("Pro divergent prompt", pro)):
        if _normalise_prompt(text) in normalised_convergence:
            raise ExternalReviewError(f"Pro convergence prompt embeds the {label}")
    if not re.search(r"(?:local\s+(?:em[- ]authored\s+)?synthesis|em[- ]authored\s+local\s+synthesis)", convergence, re.IGNORECASE):
        raise ExternalReviewError("Pro convergence prompt must name the EM-authored local synthesis")
    if not re.search(r"(?:repository|repo)[\s_-]+evidence", convergence, re.IGNORECASE):
        raise ExternalReviewError("Pro convergence prompt must name declared repository evidence")

    return {
        "status": "VALID",
        "round_dir": str(directory),
        "prompts": {
            key.removesuffix(".md").lower(): {
                "path": str(path),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
            for key, (path, text) in loaded.items()
        },
    }


def _session_key(value: Any) -> str:
    if isinstance(value, str):
        return _require_text(value, label="session key")
    if not isinstance(value, Mapping):
        raise ExternalReviewError("each monitor session must be a string or object")
    for key in (
        "stableKey",
        "stable_key",
        "sessionKey",
        "session_key",
        "sessionRef",
        "session_ref",
        "sessionId",
        "session_id",
        "id",
    ):
        if key in value:
            return _require_text(value[key], label=f"session {key}")
    raise ExternalReviewError("monitor session has no stable session key")


def partition_monitors(sessions: Any, count: int) -> list[list[Any]]:
    """Sort sessions by stable key and assign them round-robin to monitors."""

    if isinstance(sessions, Mapping):
        if "sessions" not in sessions:
            raise ExternalReviewError("sessions object must contain a sessions list")
        sessions = sessions["sessions"]
    if not isinstance(sessions, (list, tuple)):
        raise ExternalReviewError("sessions must be a JSON list")
    if isinstance(count, bool) or not isinstance(count, int) or count not in {1, 2, 3}:
        raise ExternalReviewError("monitor count must be 1, 2, or 3")

    entries = list(sessions)
    keyed = [(_session_key(entry), index, entry) for index, entry in enumerate(entries)]
    seen: set[str] = set()
    for key, _, _ in keyed:
        if key in seen:
            raise ExternalReviewError(f"duplicate stable session key: {key}")
        seen.add(key)
    keyed.sort(key=lambda item: (item[0], item[1]))
    partitions: list[list[Any]] = [[] for _ in range(count)]
    for index, (_, _, entry) in enumerate(keyed):
        partitions[index % count].append(entry)
    return partitions


def validate_archive(operation_ref: Any, archive: Any) -> dict[str, Any]:
    """Validate an Agentify archive without changing or importing it."""

    return _archive_record(operation_ref, archive).data.copy()


def _fsync_directory(path: Path) -> None:
    hmasd_platform.fsync_directory(path)


def _ensure_parent(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _fsync_directory(path.parent)
    except OSError as exc:
        raise PathRefusal(f"cannot prepare archive parent {path.parent}: {exc}") from exc


def _owned_destination(operation: Mapping[str, Any], destination: os.PathLike[str] | str) -> Path:
    root = _PROJECT_ROOT.resolve()
    relative = PurePosixPath(str(operation["archive_path"]))
    expected = root.joinpath(*relative.parts)
    supplied = Path(destination)
    target = supplied if supplied.is_absolute() else root / supplied
    try:
        if target.resolve(strict=False) != expected.resolve(strict=False):
            raise PathRefusal(
                "archive destination does not match the operation reference's owned tracked archive path"
            )
        parent = root
        for component in relative.parts[:-1]:
            parent /= component
            if _is_alias(parent):
                raise PathRefusal(f"owned archive path contains a symlink or reparse parent: {parent}")
    except (OSError, RuntimeError) as exc:
        raise PathRefusal(f"cannot resolve owned archive destination: {target}: {exc}") from exc
    return expected


def _existing_archive(destination: Path) -> ArchiveRecord:
    if _is_alias(destination) or not destination.is_file():
        raise PathRefusal(f"archive destination is not a regular file: {destination}")
    return _archive_record(None, destination)


def create_archive_if_absent(
    operation_ref: Any,
    archive: Any,
    destination: os.PathLike[str] | str,
) -> dict[str, Any]:
    """Publish one bound foreign archive to its sole owned tracked path.

    The destination is derived from the operation's direction, round, and
    provider binding, then published by linking a fully written/fsynced
    temporary file. A losing writer is idempotent only when the destination's
    complete raw archive bytes have the same SHA-256 as the incoming archive.
    """

    operation_value, _, _ = _input_value(operation_ref, label="operation reference")
    operation = _validate_operation_ref(operation_value)
    record = _archive_record(operation, archive)
    target = _owned_destination(operation, destination)
    if target.exists() and target.is_dir():
        raise PathRefusal(f"archive destination is a directory: {target}")
    _ensure_parent(target)
    target = _owned_destination(operation, target)

    fd: int | None = None
    temporary: Path | None = None
    try:
        fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
        temporary = Path(temporary_name)
        view = memoryview(record.raw_bytes)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short archive write")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = None
        try:
            os.link(temporary, target, follow_symlinks=False)
        except FileExistsError:
            existing = _existing_archive(target)
            if existing.archive_sha256 != record.archive_sha256 or existing.raw_bytes != record.raw_bytes:
                raise ArchiveConflict(
                    "archive destination has different exact archive bytes: "
                    f"existing={existing.archive_sha256} incoming={record.archive_sha256}"
                )
            return {
                "status": "IDEMPOTENT",
                "path": str(target),
                "archive_sha256": existing.archive_sha256,
                "response_sha256": existing.response_sha256,
            }
        _fsync_directory(target.parent)
        return {
            "status": "CREATED",
            "path": str(target),
            "archive_sha256": record.archive_sha256,
            "response_sha256": record.response_sha256,
        }
    except FileNotFoundError as exc:
        raise PathRefusal(f"archive destination parent disappeared: {target.parent}") from exc
    finally:
        if fd is not None:
            os.close(fd)
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    _ensure_parent(path)
    fd: int | None = None
    temporary: Path | None = None
    raw = _canonical_json(value)
    try:
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
        temporary = Path(temporary_name)
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short JSON write")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = None
        os.replace(temporary, path)
        temporary = None
        _fsync_directory(path.parent)
    finally:
        if fd is not None:
            os.close(fd)
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


def render_handoff_input(
    archive: Any,
    out: os.PathLike[str] | str,
) -> dict[str, Any]:
    """Render a mechanical, ignored handoff input without authoring science."""

    record = _archive_record(None, archive)
    rendered = dict(record.data)
    rendered.update(
        {
            "archiveSha256": record.archive_sha256,
            "archiveBytes": len(record.raw_bytes),
            "handoffKind": "agentify_review_natural_completion_intake",
        }
    )
    _write_json_atomic(Path(out), rendered)
    return rendered


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    round_parser = commands.add_parser("round-id", help="compute a deterministic review round id")
    round_parser.add_argument("--direction", required=True)
    round_parser.add_argument("--question-sha", required=True)
    round_parser.add_argument("--evidence-sha", required=True)
    round_parser.add_argument("--workflow-version", required=True)

    prompt_parser = commands.add_parser("validate-prompts", help="validate blind provider prompts")
    prompt_parser.add_argument("--round-dir", required=True)

    partition_parser = commands.add_parser("partition-monitors", help="partition monitor sessions")
    partition_parser.add_argument("--sessions", required=True)
    partition_parser.add_argument("--count", type=int, choices=(1, 2, 3), required=True)

    archive_parser = commands.add_parser("validate-archive", help="validate or import an Agentify archive")
    archive_parser.add_argument("--operation-ref", required=True)
    archive_parser.add_argument("--archive", required=True)
    archive_parser.add_argument(
        "--out",
        help="optional destination; it must equal the operation's owned direction/round/provider archive path",
    )

    handoff_parser = commands.add_parser("render-handoff-input", help="render an ignored handoff input")
    handoff_parser.add_argument("--archive", required=True)
    handoff_parser.add_argument("--out", required=True)
    return parser


def _command_result(args: argparse.Namespace) -> Any:
    if args.command == "round-id":
        return round_id(args.direction, args.question_sha, args.evidence_sha, args.workflow_version)
    if args.command == "validate-prompts":
        return validate_prompts(args.round_dir)
    if args.command == "partition-monitors":
        sessions, _, _ = _input_value(args.sessions, label="sessions")
        return {"count": args.count, "partitions": partition_monitors(sessions, args.count)}
    if args.command == "validate-archive":
        if args.out:
            return create_archive_if_absent(args.operation_ref, args.archive, args.out)
        record = _archive_record(args.operation_ref, args.archive)
        return {
            "status": "VALID",
            "operation_id": record.data["operationId"],
            "response_sha256": record.response_sha256,
            "archive_sha256": record.archive_sha256,
        }
    if args.command == "render-handoff-input":
        rendered = render_handoff_input(args.archive, args.out)
        return {
            "status": "RENDERED",
            "path": str(Path(args.out)),
            "response_sha256": rendered["responseSha256"],
            "archive_sha256": rendered["archiveSha256"],
        }
    raise ExternalReviewError(f"unknown command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = _command_result(args)
    except CommitmentUnknown as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 7
    except ArchiveConflict as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 6
    except PathRefusal as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 5
    except ExternalReviewError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
