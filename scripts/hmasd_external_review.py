#!/usr/bin/env python3
"""Root-only helpers for deterministic HMASD external-review boundaries.

This module deliberately contains no provider transport, browser, or Agentify
ledger code. Root's current CLI validates one stage prompt, durably registers
its exact bytes, or recovers one exact registration transaction. Historical
read-only helpers have no current CLI route or registration authority.
"""

from __future__ import annotations

import argparse
import copy
import datetime as _datetime
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, NoReturn, Sequence
from urllib.parse import urlsplit


ROUND_ID_HEX_LENGTH = 20
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_OWNED_ARCHIVE_ROOT = PurePosixPath("docs/external-review/directions")
_OWNED_RESPONSE_FILENAME = "response.md"
_OWNED_OPERATION_REF_FILENAME = "operation_ref.json"
_SUPPORTED_REVIEW_STAGES = frozenset({"pro_innovator", "pro_convergence"})
_PROMPT_FILENAMES = {
    "pro_innovator": "PRO_INNOVATOR_PROMPT.md",
    "pro_convergence": "PRO_CONVERGENCE_PROMPT.md",
}
_OWNED_EXTERNAL_INDEX = PurePosixPath(
    "docs/research/candidates/{direction_id}/workflow/external-review/index.json"
)
_REGISTRATION_JOURNAL_ROOT = PurePosixPath(
    ".omp/runtime/external-review-registrations"
)
_REGISTRATION_JOURNAL_SCHEMA = "hmasd_external_prompt_registration_v1"
_REGISTRATION_PHASES = frozenset(
    {
        "PREPARING",
        "STAGED",
        "PROMPT_PUBLISHED",
        "INDEX_PUBLISHED",
        "VERIFIED",
        "CLEANING",
        "COMMITTED",
        "ROLLING_BACK",
        "ROLLED_BACK",
        "UNKNOWN",
    }
)
_REGISTRATION_TERMINAL_PHASES = frozenset({"COMMITTED", "ROLLED_BACK"})
PROMPT_FILES = (
    "PRO_INNOVATOR_PROMPT.md",
    "PRO_CONVERGENCE_PROMPT.md",
)
_REQUIRED_ARCHIVE_RECEIPT_FIELDS = (
    "path",
    "sha256",
    "size_bytes",
    "projection",
    "verified_at",
)
_REQUIRED_OPERATION_FIELDS = (
    "schema_version",
    "direction_id",
    "round_id",
    "workflow_version",
    "review_stage",
    "provider",
    "product_model",
    "reasoning_effort",
    "stable_key",
    "operation_id",
    "idempotency_key",
    "request_fingerprint",
    "prompt_sha256",
    "question_sha256",
    "evidence_sha256",
    "phase",
    "commitment",
    "recoverability",
    "observability",
    "message_capability",
    "failure",
    "provider_user_message_count",
    "send_activation_count",
    "conversation_url",
    "conversation_id",
    "user_message_id",
    "assistant_message_id",
    "archive",
)
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


class RevisionConflict(ExternalReviewError):
    """The external-review index changed before a prompt registration."""


class RegistrationUnknown(ExternalReviewError):
    """Canonical registration state cannot be reconciled without choosing."""


@dataclass(frozen=True)
class ArchiveRecord:
    """Validated archive data and the bytes from which it was read."""

    data: dict[str, Any]
    raw_bytes: bytes
    archive_sha256: str
    response_sha256: str
    source_path: Path | None = None


@dataclass(frozen=True)
class _PromptValidation:
    index: dict[str, Any]
    index_raw: bytes
    index_path: Path
    prompt_path: Path
    prompt_raw: bytes
    prompt_sha256: str
    review_stage: str
    direction_id: str
    round_id: str
    question_sha256: str
    evidence_set_sha256: str
    workflow_version: str
    canonical_relative: PurePosixPath
    canonical_path: Path


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


def _owned_response_path(
    direction_id: str,
    round_id_value: str,
    review_stage: str,
    provider: str,
) -> PurePosixPath:
    return (
        _OWNED_ARCHIVE_ROOT
        / direction_id
        / round_id_value
        / review_stage
        / provider
        / _OWNED_RESPONSE_FILENAME
    )


def _owned_operation_ref_path(response_path: PurePosixPath) -> PurePosixPath:
    return response_path.with_name(_OWNED_OPERATION_REF_FILENAME)


def _validate_archive_target(provider: str, session_id: str, conversation_url: Any) -> str:
    url = _require_text(conversation_url, label="conversation_url")
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
    expected_fields = set(_REQUIRED_OPERATION_FIELDS)
    if set(result) != expected_fields:
        missing = sorted(expected_fields - set(result))
        extra = sorted(set(result) - expected_fields)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        raise ExternalReviewError(
            "operation reference fields do not match current schema: " + "; ".join(details)
        )
    if result["schema_version"] != 3:
        raise ExternalReviewError("operation reference schema_version must be 3")
    if result["commitment"] == "UNRESOLVED":
        raise CommitmentUnknown(
            "Agentify commitment is unresolved; no resend or archive publication is allowed"
        )

    direction_id = result["direction_id"]
    if not isinstance(direction_id, str) or _DIRECTION_ID.fullmatch(direction_id) is None:
        raise ExternalReviewError(
            "operation reference direction_id must match [a-z0-9][a-z0-9_-]{1,63}"
        )
    round_id_value = result["round_id"]
    if not isinstance(round_id_value, str) or _ROUND_ID.fullmatch(round_id_value) is None:
        raise ExternalReviewError(
            f"operation reference round_id must be {ROUND_ID_HEX_LENGTH} lowercase hex characters"
        )
    workflow_version = _require_text(
        result["workflow_version"],
        label="operation reference workflow_version",
    )
    review_stage = _require_text(
        result["review_stage"],
        label="operation reference review_stage",
    )
    if review_stage not in _SUPPORTED_REVIEW_STAGES:
        raise ExternalReviewError(
            "operation reference review_stage must be one of: "
            + ", ".join(sorted(_SUPPORTED_REVIEW_STAGES))
        )
    provider = _require_provider(result["provider"], label="operation reference provider")
    product_model = _require_text(
        result["product_model"],
        label="operation reference product_model",
    )
    if provider == "chatgpt":
        reasoning_effort = _require_text(
            result["reasoning_effort"],
            label="operation reference reasoning_effort",
        )
        if product_model != "GPT-5.6 Sol" or reasoning_effort != "Pro":
            raise ExternalReviewError(
                "current ChatGPT operation requires product_model GPT-5.6 Sol and reasoning_effort Pro"
            )
    elif result["reasoning_effort"] is not None:
        raise ExternalReviewError(
            "current Gemini operation requires reasoning_effort null"
        )
    for key in (
        "stable_key",
        "operation_id",
        "idempotency_key",
        "user_message_id",
        "assistant_message_id",
    ):
        _require_text(result[key], label=f"operation reference {key}")
    for key in (
        "request_fingerprint",
        "prompt_sha256",
        "question_sha256",
        "evidence_sha256",
    ):
        _require_sha(result[key], label=f"operation reference {key}")

    expected_round_id = round_id(
        direction_id,
        result["question_sha256"],
        result["evidence_sha256"],
        workflow_version,
    )
    if round_id_value != expected_round_id:
        raise ExternalReviewError(
            "operation reference round_id does not match its frozen direction, question, evidence, and workflow"
        )
    conversation_id = _require_session_id(
        result["conversation_id"],
        label="operation reference conversation_id",
    )
    _validate_archive_target(provider, conversation_id, result["conversation_url"])

    expected_terminal = {
        "phase": "TERMINAL",
        "commitment": "ONE_EXACT",
        "recoverability": "NONE",
        "observability": "FRESH_COMPLETE",
        "message_capability": "SEALED",
        "provider_user_message_count": 1,
    }
    for key, expected in expected_terminal.items():
        if result[key] != expected:
            raise ExternalReviewError(
                f"operation reference {key} must be {expected!r} for natural completion"
            )
    activation_count = result["send_activation_count"]
    if (
        isinstance(activation_count, bool)
        or not isinstance(activation_count, int)
        or activation_count not in {0, 1}
    ):
        raise ExternalReviewError(
            "operation reference send_activation_count must be 0 or 1"
        )
    failure = result["failure"]
    if not isinstance(failure, Mapping) or set(failure) != {"locus", "code"}:
        raise ExternalReviewError("operation reference failure must contain exactly locus and code")
    if failure["locus"] != "NONE" or failure["code"] != "NONE":
        raise ExternalReviewError("natural completion operation reference failure must be NONE/NONE")

    archive = result["archive"]
    if not isinstance(archive, Mapping) or set(archive) != set(_REQUIRED_ARCHIVE_RECEIPT_FIELDS):
        raise ExternalReviewError(
            "operation reference archive must contain exactly path, sha256, size_bytes, projection, and verified_at"
        )
    archive_path = archive["path"]
    expected_response_path = _owned_response_path(
        direction_id,
        round_id_value,
        review_stage,
        provider,
    ).as_posix()
    if archive_path != expected_response_path:
        raise ExternalReviewError(
            "operation reference archive.path does not match its direction, round, stage, and provider"
        )
    _require_sha(archive["sha256"], label="operation reference archive.sha256")
    size_bytes = archive["size_bytes"]
    if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 1:
        raise ExternalReviewError("operation reference archive.size_bytes must be a positive integer")
    if archive["projection"] != "exact":
        raise ExternalReviewError("operation reference archive.projection must be exact")
    verified_at = archive["verified_at"]
    if isinstance(verified_at, bool) or not isinstance(verified_at, int) or verified_at < 1:
        raise ExternalReviewError(
            "operation reference archive.verified_at must be a positive epoch-millisecond integer"
        )
    return result


def _read_raw_archive(archive: Any) -> tuple[bytes, Path]:
    if not isinstance(archive, (str, os.PathLike)):
        raise ExternalReviewError("archive must be a path to raw UTF-8 assistant response bytes")
    path = Path(archive)
    if path.is_symlink() or not path.is_file():
        raise ExternalReviewError(f"archive is not a regular file: {path}")
    first = _read_regular_bytes(path, label="archive")
    second = _read_regular_bytes(path, label="archive reread")
    if first != second:
        raise ExternalReviewError("archive bytes changed between fingerprint and exact reread")
    try:
        text = first.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExternalReviewError("archive is not UTF-8") from exc
    if not text:
        raise ExternalReviewError("archive assistant response is empty")
    return first, path


def _archive_record(operation_ref: Any, archive: Any) -> ArchiveRecord:
    operation_value, _, _ = _input_value(operation_ref, label="operation reference")
    operation = _validate_operation_ref(operation_value)
    raw, source_path = _read_raw_archive(archive)
    archive_sha256 = hashlib.sha256(raw).hexdigest()
    receipt = operation["archive"]
    if receipt["sha256"] != archive_sha256:
        raise ExternalReviewError(
            "raw archive bytes do not match operation reference archive.sha256"
        )
    if receipt["size_bytes"] != len(raw):
        raise ExternalReviewError(
            "raw archive byte length does not match operation reference archive.size_bytes"
        )
    return ArchiveRecord(
        data=operation,
        raw_bytes=raw,
        archive_sha256=archive_sha256,
        response_sha256=archive_sha256,
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


def _read_prompt(round_dir: Path, filename: str) -> tuple[Path, str]:
    path = round_dir / filename
    if not path.is_file() or path.is_symlink():
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
            raise ExternalReviewError(f"{label} contains a forbidden review reference: {pattern}")


_INNOVATOR_FORBIDDEN_PATTERNS = (
    r"PRO[-_ ]CONVERGENCE(?:[-_ ](?:PROMPT|RESPONSE|ARCHIVE|HANDOFF))?(?:\.md)?",
    r"\bconvergence\s+(?:prompt|stage|review|operation|response|archive|conversation|metadata)\b",
    r"\b(?:em[- ]authored\s+)?local\s+synthesis\b",
    r"\b(?:em[- ]authored|em|local)\s+(?:scientific\s+)?conclusions?\b",
    r"\b(?:our|the|accepted|current|final|preliminary)\s+(?:scientific\s+)?conclusion\s+(?:is|was|that)\b",
    r"(?m)^\s*(?:#{1,6}\s+)?conclusions?\s*:",
    r"\b(?:we|em)\s+conclude[ds]?\b",
    r"(?<!do not )\bassume\b.{0,80}\b(?:correct|true|favou?red|wins?)\b",
    r"\b(?:favou?red|preferred)\s+(?:answer|conclusion|mechanism|outcome)\s*(?:is|:)",
    r"(?:response\.md|operation_ref\.json)",
    r"\b(?:conversation|operation|idempotency|stable)[-_ ]?(?:id|key|url|ref|metadata)\b",
    r"\b(?:response|archive|handoff)[-_ ]?(?:sha256|text|path|ref|id|metadata)\b",
    r"\b(?:response|archive|conversation|operation)\s+(?:metadata|reference|path|url|transcript|text)\b",
    r"\b(?:assistant|user)[-_ ]?message[-_ ]?id\b",
    r"\b(?:provider|model)[-_ ]?(?:identity|metadata|operation|ref)\b",
    r"\bagentify\b",
    r"https?://",
)
_CONVERGENCE_FORBIDDEN_PATTERNS = (
    r"PRO[-_ ]INNOVATOR(?:[-_ ](?:PROMPT|RESPONSE|ARCHIVE|HANDOFF))?(?:\.md)?",
    r"(?:^|[/\\])pro[-_]innovator(?:[/\\])",
    r"(?:response\.md|operation_ref\.json)",
    r"\btranscript\b",
    r"\binnovator\s+(?:response|archive|handoff|conversation|operation)\b",
    r"\b(?:conversation|operation|idempotency|stable)[-_ ]?(?:id|key|url|ref|metadata)\b",
    r"\b(?:response|archive|handoff)[-_ ]?(?:sha256|text|path|ref|id|metadata)\b",
    r"\b(?:response|archive|conversation|operation)\s+(?:metadata|reference|path|url|transcript|text)\b",
    r"\b(?:assistant|user)[-_ ]?message[-_ ]?id\b",
    r"\bagentify\b",
    r"https?://",
)


def validate_prompts(round_dir: os.PathLike[str] | str) -> dict[str, Any]:
    """Validate a historical prompt pair without authoring or registration authority."""

    directory = Path(round_dir)
    if not directory.is_dir() or directory.is_symlink():
        raise ExternalReviewError(f"round directory is not a regular directory: {directory}")
    loaded = {name: _read_prompt(directory, name) for name in PROMPT_FILES}
    innovator = loaded["PRO_INNOVATOR_PROMPT.md"][1]
    convergence = loaded["PRO_CONVERGENCE_PROMPT.md"][1]

    innovator_patterns = _INNOVATOR_FORBIDDEN_PATTERNS
    _reject_prompt_references(
        innovator,
        innovator_patterns,
        label="Pro Innovator prompt",
    )

    convergence_patterns = _CONVERGENCE_FORBIDDEN_PATTERNS
    _reject_prompt_references(
        convergence,
        convergence_patterns,
        label="Pro Convergence prompt",
    )
    if _normalise_prompt(innovator) in _normalise_prompt(convergence):
        raise ExternalReviewError("Pro Convergence prompt embeds the Pro Innovator prompt")
    if not re.search(
        r"(?:em[- ]authored\s+local\s+synthesis|local\s+synthesis\s+(?:authored|written|prepared)\s+by\s+(?:the\s+)?em)",
        convergence,
        re.IGNORECASE,
    ):
        raise ExternalReviewError("Pro Convergence prompt must name the EM-authored local synthesis")
    if not re.search(
        r"\bdeclared\s+(?:repository|repo)[\s_-]+evidence\b",
        convergence,
        re.IGNORECASE,
    ):
        raise ExternalReviewError("Pro Convergence prompt must name declared repository evidence")

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


def _state_module() -> Any:
    if __package__:
        from scripts import hmasd_state
    else:
        import hmasd_state  # type: ignore[reportMissingImports]
    return hmasd_state


def _read_regular_bytes(path: Path, *, label: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise PathRefusal(f"cannot open {label} {path}: {exc}") from exc
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise PathRefusal(f"{label} is not a regular file: {path}")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            return handle.read()
    except OSError as exc:
        raise PathRefusal(f"cannot read {label} {path}: {exc}") from exc
    finally:
        if fd >= 0:
            os.close(fd)


def _owned_relative_path(relative: PurePosixPath, *, label: str) -> Path:
    if relative.is_absolute() or ".." in relative.parts or "\\" in str(relative):
        raise PathRefusal(f"{label} is not a safe project-relative path: {relative}")
    root = _PROJECT_ROOT.resolve()
    target = root.joinpath(*relative.parts)
    current = root
    for component in relative.parts:
        current /= component
        if current.is_symlink():
            raise PathRefusal(f"{label} contains a symlink: {current}")
    try:
        target.resolve(strict=False).relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise PathRefusal(f"{label} escapes the project root: {relative}") from exc
    return target


def _owned_external_index_path(
    direction_id: str,
    supplied: os.PathLike[str] | str,
) -> Path:
    relative = PurePosixPath(
        str(_OWNED_EXTERNAL_INDEX).format(direction_id=direction_id)
    )
    expected = _owned_relative_path(relative, label="external-review index path")
    candidate = Path(supplied)
    if not candidate.is_absolute():
        candidate = _PROJECT_ROOT / candidate
    try:
        if candidate.resolve(strict=False) != expected.resolve(strict=False):
            raise PathRefusal(
                "external-review index path does not match the direction-owned canonical path"
            )
    except (OSError, RuntimeError) as exc:
        raise PathRefusal(f"cannot resolve external-review index path: {candidate}") from exc
    if candidate.is_symlink():
        raise PathRefusal(f"external-review index is symlinked: {candidate}")
    return expected


def _prompt_relative_path(
    direction_id: str,
    round_id_value: str,
    review_stage: str,
) -> PurePosixPath:
    return (
        _OWNED_ARCHIVE_ROOT
        / direction_id
        / round_id_value
        / review_stage
        / _PROMPT_FILENAMES[review_stage]
    )


def _require_ref(value: Any, *, label: str) -> dict[str, str]:
    loaded, _, _ = _input_value(value, label=label)
    if not isinstance(loaded, Mapping) or set(loaded) != {"path", "sha256"}:
        raise ExternalReviewError(f"{label} must contain exactly path and sha256")
    path = _require_text(loaded["path"], label=f"{label}.path")
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts or "\\" in path:
        raise PathRefusal(f"{label}.path is not a safe project-relative path")
    return {
        "path": path,
        "sha256": _require_sha(loaded["sha256"], label=f"{label}.sha256"),
    }


def _verify_durable_ref(
    reference: Mapping[str, str],
    *,
    label: str,
    required_prefix: str | None = None,
) -> None:
    relative = PurePosixPath(reference["path"])
    if required_prefix is not None and not reference["path"].startswith(required_prefix):
        raise PathRefusal(f"{label}.path is outside {required_prefix}")
    target = _owned_relative_path(relative, label=f"{label}.path")
    raw = _read_regular_bytes(target, label=label)
    observed = hashlib.sha256(raw).hexdigest()
    if observed != reference["sha256"]:
        raise ExternalReviewError(
            f"{label}.sha256 does not match exact durable bytes: "
            f"expected={reference['sha256']} observed={observed}"
        )


def _validate_external_index(
    value: Any,
    *,
    direction_id: str,
) -> tuple[dict[str, Any], bytes, Path]:
    index_path = _owned_external_index_path(direction_id, value)
    raw = _read_regular_bytes(index_path, label="external-review index")
    parsed = _parse_json(raw, label="external-review index")
    if not isinstance(parsed, dict):
        raise ExternalReviewError("external-review index must be a JSON object")
    state = _state_module()
    try:
        state.validate_document(
            "external_review_index",
            parsed,
            writer=f"EM-{direction_id}",
        )
    except state.StateError as exc:
        raise ExternalReviewError(f"invalid external-review index: {exc}") from exc
    if parsed["direction_id"] != direction_id:
        raise ExternalReviewError("external-review index direction_id does not match --direction")
    return parsed, raw, index_path


def _find_active_round(
    index: Mapping[str, Any],
    round_id_value: str,
) -> dict[str, Any] | None:
    matches = [
        item
        for item in index["rounds"]
        if isinstance(item, dict) and item.get("round_id") == round_id_value
    ]
    if len(matches) > 1:
        raise ExternalReviewError(f"duplicate external-review round: {round_id_value}")
    return matches[0] if matches else None


def _require_prompt_identity(text: str, value: str, *, label: str) -> None:
    if value not in text:
        raise ExternalReviewError(f"prompt does not contain exact {label}: {value}")


def _validate_stage_text(
    text: str,
    *,
    review_stage: str,
    question_sha256: str,
    evidence_set_sha256: str,
    workflow_version: str,
    innovator_ref: Mapping[str, str] | None,
) -> None:
    for value, label in (
        (review_stage, "review_stage"),
        (question_sha256, "question_sha256"),
        (evidence_set_sha256, "evidence_set_sha256"),
        (workflow_version, "workflow_version"),
    ):
        _require_prompt_identity(text, value, label=label)
    if review_stage == "pro_innovator":
        _reject_prompt_references(
            text,
            _INNOVATOR_FORBIDDEN_PATTERNS,
            label="Pro Innovator prompt",
        )
        return
    _reject_prompt_references(
        text,
        _CONVERGENCE_FORBIDDEN_PATTERNS,
        label="Pro Convergence prompt",
    )
    if innovator_ref is None:
        raise ExternalReviewError("Pro Convergence requires a canonical Innovator prompt ref")
    for value in innovator_ref.values():
        if value in text:
            raise ExternalReviewError(
                "Pro Convergence prompt contains canonical Innovator prompt provenance"
            )
    if not re.search(
        r"(?:em[- ]authored\s+local\s+synthesis|local\s+synthesis\s+(?:authored|written|prepared)\s+by\s+(?:the\s+)?em)",
        text,
        re.IGNORECASE,
    ):
        raise ExternalReviewError("Pro Convergence prompt must name the EM-authored local synthesis")
    if not re.search(
        r"\bdeclared\s+(?:repository|repo)[\s_-]+evidence\b",
        text,
        re.IGNORECASE,
    ):
        raise ExternalReviewError("Pro Convergence prompt must name declared repository evidence")


def _validated_stage_prompt(
    review_stage: str,
    prompt: os.PathLike[str] | str,
    *,
    external_index: os.PathLike[str] | str,
    direction_id: str,
    round_id_value: str,
    question_sha256: str,
    evidence_set_sha256: str,
    workflow_version: str,
    local_synthesis_ref: Any = None,
    innovator_prompt_ref: Any = None,
    expected_prompt_sha256: str | None = None,
) -> _PromptValidation:
    if review_stage not in _SUPPORTED_REVIEW_STAGES:
        raise ExternalReviewError(
            "review_stage must be exactly pro_innovator or pro_convergence"
        )
    if not isinstance(direction_id, str) or _DIRECTION_ID.fullmatch(direction_id) is None:
        raise ExternalReviewError("direction_id must match [a-z0-9][a-z0-9_-]{1,63}")
    question = _require_sha(question_sha256, label="question_sha256")
    evidence = _require_sha(evidence_set_sha256, label="evidence_set_sha256")
    workflow = _require_text(workflow_version, label="workflow_version")
    supplied_round = _require_text(round_id_value, label="round_id")
    canonical_round = round_id(direction_id, question, evidence, workflow)
    if supplied_round != canonical_round:
        raise ExternalReviewError(
            f"round_id does not match frozen identities: "
            f"expected={canonical_round} supplied={supplied_round}"
        )

    index, index_raw, index_path = _validate_external_index(
        external_index,
        direction_id=direction_id,
    )
    if index["schema_version"] != 4:
        raise ExternalReviewError(
            "current stage prompt validation and registration require index schema v4"
        )
    if index["workflow_version"] != workflow:
        raise ExternalReviewError(
            "workflow_version does not match the external-review index"
        )
    active_round = _find_active_round(index, canonical_round)
    if active_round is not None and (
        active_round["question_sha256"] != question
        or active_round["evidence_set_sha256"] != evidence
    ):
        raise ExternalReviewError(
            "active round question/evidence identities do not match the exact inputs"
        )
    canonical_relative = _prompt_relative_path(
        direction_id,
        canonical_round,
        review_stage,
    )
    canonical_path = _owned_relative_path(
        canonical_relative,
        label="canonical prompt path",
    )

    supplied_synthesis: dict[str, str] | None = None
    supplied_innovator: dict[str, str] | None = None
    if review_stage == "pro_innovator":
        if local_synthesis_ref is not None or innovator_prompt_ref is not None:
            raise ExternalReviewError(
                "Pro Innovator does not accept Convergence stage prerequisites"
            )
        if active_round is not None:
            raise ExternalReviewError(
                "Pro Innovator round is already registered and immutable"
            )
    else:
        if active_round is None:
            raise ExternalReviewError(
                "Pro Convergence requires an existing canonical Innovator round"
            )
        if active_round["status"] != "SYNTHESIS_READY":
            raise ExternalReviewError(
                "Pro Convergence requires round status SYNTHESIS_READY"
            )
        indexed_synthesis = active_round.get("local_synthesis_ref")
        indexed_innovator = active_round["prompt_refs"].get("pro_innovator")
        if indexed_synthesis is None:
            raise ExternalReviewError(
                "Pro Convergence requires a durable local synthesis ref"
            )
        if indexed_innovator is None:
            raise ExternalReviewError(
                "Pro Convergence requires a canonical Innovator prompt ref"
            )
        if active_round["prompt_refs"].get("pro_convergence") is not None:
            raise ExternalReviewError(
                "Pro Convergence prompt is already registered and immutable"
            )
        if local_synthesis_ref is None or innovator_prompt_ref is None:
            raise ExternalReviewError(
                "Pro Convergence requires exact synthesis and Innovator prompt refs"
            )
        supplied_synthesis = _require_ref(
            local_synthesis_ref,
            label="local synthesis ref",
        )
        supplied_innovator = _require_ref(
            innovator_prompt_ref,
            label="Innovator prompt ref",
        )
        if supplied_synthesis != indexed_synthesis:
            raise ExternalReviewError(
                "local synthesis ref does not match the external-review index"
            )
        if supplied_innovator != indexed_innovator:
            raise ExternalReviewError(
                "Innovator prompt ref does not match the external-review index"
            )
        expected_innovator_path = str(
            _prompt_relative_path(
                direction_id,
                canonical_round,
                "pro_innovator",
            )
        )
        if supplied_innovator["path"] != expected_innovator_path:
            raise PathRefusal(
                "Innovator prompt ref is not the canonical round/stage path"
            )
        _verify_durable_ref(
            supplied_innovator,
            label="Innovator prompt ref",
        )
        _verify_durable_ref(
            supplied_synthesis,
            label="local synthesis ref",
            required_prefix=f"docs/research/candidates/{direction_id}/",
        )

    prompt_path = Path(prompt)
    prompt_raw = _read_regular_bytes(prompt_path, label="disposable prompt")
    if not prompt_raw:
        raise ExternalReviewError("disposable prompt is empty")
    try:
        text = prompt_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExternalReviewError(f"disposable prompt is not UTF-8: {exc}") from exc
    if not text.strip():
        raise ExternalReviewError("disposable prompt is empty")
    prompt_sha = hashlib.sha256(prompt_raw).hexdigest()
    if expected_prompt_sha256 is not None:
        expected_sha = _require_sha(
            expected_prompt_sha256,
            label="expected_prompt_sha256",
        )
        if prompt_sha != expected_sha:
            raise ExternalReviewError(
                "disposable prompt hash changed after validation: "
                f"expected={expected_sha} observed={prompt_sha}"
            )
    _validate_stage_text(
        text,
        review_stage=review_stage,
        question_sha256=question,
        evidence_set_sha256=evidence,
        workflow_version=workflow,
        innovator_ref=supplied_innovator,
    )
    return _PromptValidation(
        index=index,
        index_raw=index_raw,
        index_path=index_path,
        prompt_path=prompt_path,
        prompt_raw=prompt_raw,
        prompt_sha256=prompt_sha,
        review_stage=review_stage,
        direction_id=direction_id,
        round_id=canonical_round,
        question_sha256=question,
        evidence_set_sha256=evidence,
        workflow_version=workflow,
        canonical_relative=canonical_relative,
        canonical_path=canonical_path,
    )


def _prompt_validation_result(validated: _PromptValidation) -> dict[str, Any]:
    return {
        "status": "VALID",
        "review_stage": validated.review_stage,
        "direction_id": validated.direction_id,
        "round_id": validated.round_id,
        "prompt_path": str(validated.prompt_path),
        "prompt_sha256": validated.prompt_sha256,
        "prompt_size_bytes": len(validated.prompt_raw),
        "canonical_prompt_ref": {
            "path": str(validated.canonical_relative),
            "sha256": validated.prompt_sha256,
        },
        "external_index_revision": validated.index["revision"],
    }


def validate_prompt(
    review_stage: str,
    prompt: os.PathLike[str] | str,
    *,
    external_index: os.PathLike[str] | str,
    direction_id: str,
    round_id_value: str,
    question_sha256: str,
    evidence_set_sha256: str,
    workflow_version: str,
    local_synthesis_ref: Any = None,
    innovator_prompt_ref: Any = None,
) -> dict[str, Any]:
    """Validate one disposable stage prompt without creating durable facts."""

    return _prompt_validation_result(
        _validated_stage_prompt(
            review_stage,
            prompt,
            external_index=external_index,
            direction_id=direction_id,
            round_id_value=round_id_value,
            question_sha256=question_sha256,
            evidence_set_sha256=evidence_set_sha256,
            workflow_version=workflow_version,
            local_synthesis_ref=local_synthesis_ref,
            innovator_prompt_ref=innovator_prompt_ref,
        )
    )


def _registration_timestamp() -> str:
    return (
        _datetime.datetime.now(_datetime.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _next_prompt_index(validated: _PromptValidation) -> dict[str, Any]:
    if validated.index["schema_version"] != 4:
        raise ExternalReviewError(
            "prompt registration requires current external-review index schema v4"
        )
    next_index = copy.deepcopy(validated.index)
    timestamp = _registration_timestamp()
    prompt_ref = {
        "path": str(validated.canonical_relative),
        "sha256": validated.prompt_sha256,
    }
    if validated.review_stage == "pro_innovator":
        next_index["rounds"].append(
            {
                "round_id": validated.round_id,
                "question_sha256": validated.question_sha256,
                "evidence_set_sha256": validated.evidence_set_sha256,
                "status": "INNOVATOR_PENDING",
                "prompt_refs": {
                    "pro_innovator": prompt_ref,
                    "pro_convergence": None,
                },
                "providers": {
                    "pro_innovator": None,
                    "pro_convergence": None,
                },
                "local_synthesis_ref": None,
                "created_at": timestamp,
                "completed_at": None,
            }
        )
    else:
        active_round = _find_active_round(next_index, validated.round_id)
        if active_round is None:
            raise ExternalReviewError("canonical round disappeared before registration")
        active_round["prompt_refs"]["pro_convergence"] = prompt_ref
    next_index["revision"] = validated.index["revision"] + 1
    next_index["updated_at"] = timestamp
    return next_index


def _stage_bytes(parent: Path, prefix: str, raw: bytes, *, mode: int) -> Path:
    fd, name = tempfile.mkstemp(prefix=prefix, dir=str(parent))
    temporary = Path(name)
    try:
        os.fchmod(fd, mode & 0o777)
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short staged write")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        return temporary
    except Exception:
        if fd >= 0:
            os.close(fd)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _prepare_owned_parent(target: Path) -> list[Path]:
    root = _PROJECT_ROOT.resolve()
    missing: list[Path] = []
    current = target.parent
    while current != root and not current.exists():
        missing.append(current)
        current = current.parent
    if current.is_symlink() or not current.is_dir():
        raise PathRefusal(f"canonical prompt parent is unsafe: {current}")
    created: list[Path] = []
    try:
        for directory in reversed(missing):
            try:
                directory.mkdir()
                created.append(directory)
            except FileExistsError:
                if directory.is_symlink() or not directory.is_dir():
                    raise PathRefusal(
                        f"canonical prompt parent is unsafe: {directory}"
                    )
        return created
    except Exception:
        for directory in reversed(created):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise


def _replace_file(source: Path, destination: Path) -> None:
    os.replace(source, destination)


def _unlink_if_present(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _registration_request(
    review_stage: str,
    prompt: os.PathLike[str] | str,
    *,
    external_index: os.PathLike[str] | str,
    direction_id: str,
    round_id_value: str,
    question_sha256: str,
    evidence_set_sha256: str,
    workflow_version: str,
    expected_revision: int,
    prompt_sha256: str,
    local_synthesis_ref: Any,
    innovator_prompt_ref: Any,
) -> tuple[dict[str, Any], Path]:
    if review_stage not in _SUPPORTED_REVIEW_STAGES:
        raise ExternalReviewError(
            "review_stage must be exactly pro_innovator or pro_convergence"
        )
    if not isinstance(direction_id, str) or _DIRECTION_ID.fullmatch(direction_id) is None:
        raise ExternalReviewError("direction_id must match [a-z0-9][a-z0-9_-]{1,63}")
    if (
        not isinstance(expected_revision, int)
        or isinstance(expected_revision, bool)
        or expected_revision < 1
    ):
        raise RevisionConflict("expected_revision must be a positive integer")
    question = _require_sha(question_sha256, label="question_sha256")
    evidence = _require_sha(evidence_set_sha256, label="evidence_set_sha256")
    workflow = _require_text(workflow_version, label="workflow_version")
    supplied_round = _require_text(round_id_value, label="round_id")
    canonical_round = round_id(direction_id, question, evidence, workflow)
    if supplied_round != canonical_round:
        raise ExternalReviewError(
            "round_id does not match the frozen registration identities"
        )
    expected_prompt = _require_sha(prompt_sha256, label="prompt_sha256")
    index_path = _owned_external_index_path(direction_id, external_index)
    canonical_relative = _prompt_relative_path(
        direction_id,
        canonical_round,
        review_stage,
    )
    canonical_path = _owned_relative_path(
        canonical_relative,
        label="canonical prompt path",
    )
    synthesis = (
        None
        if local_synthesis_ref is None
        else _require_ref(local_synthesis_ref, label="local synthesis ref")
    )
    innovator = (
        None
        if innovator_prompt_ref is None
        else _require_ref(innovator_prompt_ref, label="Innovator prompt ref")
    )
    if review_stage == "pro_innovator" and (
        synthesis is not None or innovator is not None
    ):
        raise ExternalReviewError(
            "Pro Innovator does not accept Convergence stage prerequisites"
        )
    if review_stage == "pro_convergence" and (
        synthesis is None or innovator is None
    ):
        raise ExternalReviewError(
            "Pro Convergence requires exact synthesis and Innovator prompt refs"
        )
    source = Path(prompt)
    if not source.is_absolute():
        source = Path.cwd() / source
    root = _PROJECT_ROOT.resolve()
    return (
        {
            "review_stage": review_stage,
            "direction_id": direction_id,
            "round_id": canonical_round,
            "question_sha256": question,
            "evidence_set_sha256": evidence,
            "workflow_version": workflow,
            "expected_revision": expected_revision,
            "writer": f"EM-{direction_id}",
            "prompt_sha256": expected_prompt,
            "disposable_prompt_path": str(source.resolve(strict=False)),
            "external_index_path": index_path.relative_to(root).as_posix(),
            "canonical_prompt_path": canonical_path.relative_to(root).as_posix(),
            "local_synthesis_ref": synthesis,
            "innovator_prompt_ref": innovator,
        },
        index_path,
    )


def _missing_prompt_directories(target: Path) -> list[str]:
    root = _PROJECT_ROOT.resolve()
    missing: list[Path] = []
    current = target.parent
    while current != root and not current.exists():
        missing.append(current)
        current = current.parent
    if current.is_symlink() or not current.is_dir():
        raise PathRefusal(f"canonical prompt parent is unsafe: {current}")
    return [path.relative_to(root).as_posix() for path in reversed(missing)]


def _blob_binding(label: str, raw: bytes, mode: int) -> dict[str, Any]:
    digest = hashlib.sha256(raw).hexdigest()
    return {
        "file": f"{label}-{digest}.blob",
        "sha256": digest,
        "size_bytes": len(raw),
        "mode": stat.S_IMODE(mode),
    }


def _registration_transaction(
    request: Mapping[str, Any],
    validated: _PromptValidation,
    next_index_raw: bytes,
) -> dict[str, Any]:
    return {
        "request": dict(request),
        "old_index": _blob_binding(
            "old-index",
            validated.index_raw,
            validated.index_path.stat().st_mode,
        ),
        "new_index": _blob_binding(
            "new-index",
            next_index_raw,
            validated.index_path.stat().st_mode,
        ),
        "prompt": _blob_binding("prompt", validated.prompt_raw, 0o644),
        "created_directories": _missing_prompt_directories(
            validated.canonical_path
        ),
    }


def _transaction_id(transaction: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(transaction)).hexdigest()


def _registration_journal_path(transaction_id: str) -> Path:
    identifier = _require_sha(transaction_id, label="transaction_id")
    return _owned_relative_path(
        _REGISTRATION_JOURNAL_ROOT / identifier / "journal.json",
        label="registration journal path",
    )


def _registration_transaction_directory(
    transaction_id: str,
    *,
    create: bool,
) -> Path:
    journal_path = _registration_journal_path(transaction_id)
    directory = journal_path.parent
    if create:
        created = _prepare_owned_parent(journal_path)
        for created_directory in created:
            _fsync_directory(created_directory.parent)
    if directory.is_symlink() or not directory.is_dir():
        raise PathRefusal(
            f"registration transaction directory is unsafe: {directory}"
        )
    return directory


def _write_registration_journal(journal: Mapping[str, Any]) -> None:
    transaction_id = _require_sha(
        journal.get("transaction_id"),
        label="journal transaction_id",
    )
    directory = _registration_transaction_directory(transaction_id, create=True)
    temporary = _stage_bytes(
        directory,
        ".journal.",
        _canonical_json(journal),
        mode=0o600,
    )
    try:
        _replace_file(temporary, directory / "journal.json")
        temporary = None
        _fsync_directory(directory)
    finally:
        if temporary is not None:
            _unlink_if_present(temporary)


def _registration_phase(
    journal: Mapping[str, Any],
    phase: str,
    *,
    observation: str | None = None,
) -> dict[str, Any]:
    if phase not in _REGISTRATION_PHASES:
        raise ExternalReviewError(f"unknown registration journal phase: {phase}")
    updated: dict[str, Any] = copy.deepcopy(dict(journal))
    updated["phase"] = phase
    updated["updated_at"] = _registration_timestamp()
    if observation is None:
        updated.pop("observation", None)
    else:
        updated["observation"] = observation
    _write_registration_journal(updated)
    return updated


def _validate_blob_binding(
    transaction_id: str,
    label: str,
    value: Any,
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {
        "file",
        "sha256",
        "size_bytes",
        "mode",
    }:
        raise RegistrationUnknown(
            f"registration {transaction_id} has an invalid {label} binding"
        )
    digest = _require_sha(value["sha256"], label=f"journal {label}.sha256")
    expected_file = f"{label}-{digest}.blob"
    if value["file"] != expected_file:
        raise RegistrationUnknown(
            f"registration {transaction_id} has a non-content-addressed {label} blob"
        )
    size = value["size_bytes"]
    mode = value["mode"]
    if (
        isinstance(size, bool)
        or not isinstance(size, int)
        or size < 0
        or isinstance(mode, bool)
        or not isinstance(mode, int)
        or mode < 0
        or mode > 0o777
    ):
        raise RegistrationUnknown(
            f"registration {transaction_id} has invalid {label} metadata"
        )
    return dict(value)


def _validate_registration_transaction(
    transaction_id: str,
    transaction: Any,
) -> dict[str, Any]:
    if not isinstance(transaction, Mapping) or set(transaction) != {
        "request",
        "old_index",
        "new_index",
        "prompt",
        "created_directories",
    }:
        raise RegistrationUnknown(
            f"registration {transaction_id} has an invalid immutable transaction"
        )
    if _transaction_id(transaction) != transaction_id:
        raise RegistrationUnknown(
            f"registration journal identity/hash collision: {transaction_id}"
        )
    request = transaction["request"]
    if not isinstance(request, Mapping):
        raise RegistrationUnknown(
            f"registration {transaction_id} has an invalid request binding"
        )
    required_request = {
        "review_stage",
        "direction_id",
        "round_id",
        "question_sha256",
        "evidence_set_sha256",
        "workflow_version",
        "expected_revision",
        "writer",
        "prompt_sha256",
        "disposable_prompt_path",
        "external_index_path",
        "canonical_prompt_path",
        "local_synthesis_ref",
        "innovator_prompt_ref",
    }
    if set(request) != required_request:
        raise RegistrationUnknown(
            f"registration {transaction_id} has an incomplete request binding"
        )
    stage = request["review_stage"]
    direction = request["direction_id"]
    if (
        stage not in _SUPPORTED_REVIEW_STAGES
        or not isinstance(direction, str)
        or _DIRECTION_ID.fullmatch(direction) is None
    ):
        raise RegistrationUnknown(
            f"registration {transaction_id} has an invalid stage or direction"
        )
    question = _require_sha(
        request["question_sha256"],
        label="journal question_sha256",
    )
    evidence = _require_sha(
        request["evidence_set_sha256"],
        label="journal evidence_set_sha256",
    )
    workflow = _require_text(
        request["workflow_version"],
        label="journal workflow_version",
    )
    canonical_round = round_id(direction, question, evidence, workflow)
    if request["round_id"] != canonical_round:
        raise RegistrationUnknown(
            f"registration {transaction_id} has a noncanonical round"
        )
    if request["writer"] != f"EM-{direction}":
        raise RegistrationUnknown(
            f"registration {transaction_id} has the wrong writer"
        )
    expected_revision = request["expected_revision"]
    if (
        isinstance(expected_revision, bool)
        or not isinstance(expected_revision, int)
        or expected_revision < 1
    ):
        raise RegistrationUnknown(
            f"registration {transaction_id} has an invalid expected revision"
        )
    prompt_sha = _require_sha(
        request["prompt_sha256"],
        label="journal prompt_sha256",
    )
    expected_index = _owned_external_index_path(
        direction,
        request["external_index_path"],
    )
    expected_prompt_relative = _prompt_relative_path(
        direction,
        canonical_round,
        stage,
    )
    expected_prompt = _owned_relative_path(
        expected_prompt_relative,
        label="journal canonical prompt path",
    )
    root = _PROJECT_ROOT.resolve()
    if request["external_index_path"] != expected_index.relative_to(root).as_posix():
        raise RegistrationUnknown(
            f"registration {transaction_id} has a noncanonical index path"
        )
    if request["canonical_prompt_path"] != expected_prompt.relative_to(root).as_posix():
        raise RegistrationUnknown(
            f"registration {transaction_id} has a noncanonical prompt path"
        )
    prompt_binding = _validate_blob_binding(
        transaction_id,
        "prompt",
        transaction["prompt"],
    )
    if prompt_binding["sha256"] != prompt_sha:
        raise RegistrationUnknown(
            f"registration {transaction_id} prompt identity/hash collision"
        )
    old_binding = _validate_blob_binding(
        transaction_id,
        "old-index",
        transaction["old_index"],
    )
    new_binding = _validate_blob_binding(
        transaction_id,
        "new-index",
        transaction["new_index"],
    )
    created_directories = transaction["created_directories"]
    if not isinstance(created_directories, list) or not all(
        isinstance(value, str) for value in created_directories
    ):
        raise RegistrationUnknown(
            f"registration {transaction_id} has invalid created directories"
        )
    allowed_parents: set[str] = set()
    current = expected_prompt.parent
    while current != root:
        allowed_parents.add(current.relative_to(root).as_posix())
        current = current.parent
    if (
        len(set(created_directories)) != len(created_directories)
        or any(value not in allowed_parents for value in created_directories)
    ):
        raise RegistrationUnknown(
            f"registration {transaction_id} has unsafe created directories"
        )
    return {
        "request": dict(request),
        "old_index": old_binding,
        "new_index": new_binding,
        "prompt": prompt_binding,
        "created_directories": list(created_directories),
    }


def _load_registration_journal(
    transaction_id: str,
) -> dict[str, Any]:
    journal_path = _registration_journal_path(transaction_id)
    try:
        raw = _read_regular_bytes(journal_path, label="registration journal")
        parsed = _parse_json(raw, label="registration journal")
    except ExternalReviewError as exc:
        raise RegistrationUnknown(
            f"registration journal {transaction_id} is UNKNOWN: {exc}"
        ) from exc
    if not isinstance(parsed, Mapping) or set(parsed) - {
        "schema",
        "transaction_id",
        "transaction",
        "phase",
        "updated_at",
        "observation",
    }:
        raise RegistrationUnknown(
            f"registration journal {transaction_id} has an invalid shape"
        )
    if (
        parsed.get("schema") != _REGISTRATION_JOURNAL_SCHEMA
        or parsed.get("transaction_id") != transaction_id
        or parsed.get("phase") not in _REGISTRATION_PHASES
        or not isinstance(parsed.get("updated_at"), str)
    ):
        raise RegistrationUnknown(
            f"registration journal {transaction_id} has invalid metadata"
        )
    try:
        transaction = _validate_registration_transaction(
            transaction_id,
            parsed.get("transaction"),
        )
    except RegistrationUnknown:
        raise
    except ExternalReviewError as exc:
        raise RegistrationUnknown(
            f"registration journal {transaction_id} is UNKNOWN: {exc}"
        ) from exc
    result = dict(parsed)
    result["transaction"] = transaction
    return result


def _registration_journals() -> list[dict[str, Any]]:
    root = _owned_relative_path(
        _REGISTRATION_JOURNAL_ROOT,
        label="registration journal root",
    )
    if not root.exists():
        return []
    if root.is_symlink() or not root.is_dir():
        raise RegistrationUnknown("registration journal root is unsafe")
    journals: list[dict[str, Any]] = []
    for directory in sorted(root.iterdir(), key=lambda value: value.name):
        if directory.name.startswith("."):
            continue
        if directory.is_symlink() or not directory.is_dir():
            raise RegistrationUnknown(
                f"registration journal entry is unsafe: {directory}"
            )
        if _SHA256.fullmatch(directory.name) is None:
            raise RegistrationUnknown(
                f"registration journal entry has an invalid identity: {directory}"
            )
        journal_path = directory / "journal.json"
        if not journal_path.exists():
            continue
        journals.append(_load_registration_journal(directory.name))
    return journals


def _registration_blob_path(
    journal: Mapping[str, Any],
    label: str,
) -> Path:
    binding = journal["transaction"][label]
    directory = _registration_transaction_directory(
        journal["transaction_id"],
        create=False,
    )
    return directory / binding["file"]


def _blob_observation(
    journal: Mapping[str, Any],
    label: str,
) -> tuple[str, bytes | None]:
    path = _registration_blob_path(journal, label)
    if not path.exists() and not path.is_symlink():
        return "MISSING", None
    if path.is_symlink() or not path.is_file():
        return "WRONG", None
    raw = _read_regular_bytes(path, label=f"registration {label} blob")
    binding = journal["transaction"][label]
    if (
        len(raw) != binding["size_bytes"]
        or hashlib.sha256(raw).hexdigest() != binding["sha256"]
    ):
        return "WRONG", raw
    return "EXACT", raw


def _write_registration_blob(
    journal: Mapping[str, Any],
    label: str,
    raw: bytes,
) -> None:
    binding = journal["transaction"][label]
    if (
        len(raw) != binding["size_bytes"]
        or hashlib.sha256(raw).hexdigest() != binding["sha256"]
    ):
        raise RegistrationUnknown(
            f"registration {journal['transaction_id']} {label} bytes changed"
        )
    observed, _ = _blob_observation(journal, label)
    if observed == "EXACT":
        return
    if observed == "WRONG":
        raise RegistrationUnknown(
            f"registration {journal['transaction_id']} {label} blob collision"
        )
    directory = _registration_transaction_directory(
        journal["transaction_id"],
        create=False,
    )
    temporary = _stage_bytes(
        directory,
        f".{label}.",
        raw,
        mode=binding["mode"],
    )
    target = _registration_blob_path(journal, label)
    try:
        try:
            os.link(temporary, target, follow_symlinks=False)
        except FileExistsError:
            observed, _ = _blob_observation(journal, label)
            if observed != "EXACT":
                raise RegistrationUnknown(
                    f"registration {journal['transaction_id']} {label} blob collision"
                )
        _fsync_directory(directory)
    finally:
        _unlink_if_present(temporary)


def _prompt_observation(journal: Mapping[str, Any]) -> str:
    request = journal["transaction"]["request"]
    target = _owned_relative_path(
        PurePosixPath(request["canonical_prompt_path"]),
        label="journal canonical prompt path",
    )
    if not target.exists() and not target.is_symlink():
        return "ABSENT"
    if target.is_symlink() or not target.is_file():
        return "WRONG"
    raw = _read_regular_bytes(target, label="canonical prompt")
    binding = journal["transaction"]["prompt"]
    if (
        len(raw) == binding["size_bytes"]
        and hashlib.sha256(raw).hexdigest() == binding["sha256"]
    ):
        return "EXACT"
    return "WRONG"


def _index_observation(journal: Mapping[str, Any]) -> str:
    transaction = journal["transaction"]
    request = transaction["request"]
    target = _owned_relative_path(
        PurePosixPath(request["external_index_path"]),
        label="journal external-review index path",
    )
    if not target.exists() and not target.is_symlink():
        return "MISSING"
    if target.is_symlink() or not target.is_file():
        return "WRONG"
    raw = _read_regular_bytes(target, label="external-review index")
    digest = hashlib.sha256(raw).hexdigest()
    if (
        len(raw) == transaction["old_index"]["size_bytes"]
        and digest == transaction["old_index"]["sha256"]
    ):
        return "OLD"
    if (
        len(raw) == transaction["new_index"]["size_bytes"]
        and digest == transaction["new_index"]["sha256"]
    ):
        return "NEW"
    try:
        parsed = _parse_json(raw, label="external-review index")
        if not isinstance(parsed, dict):
            return "WRONG"
        state = _state_module()
        state.validate_document(
            "external_review_index",
            parsed,
            writer=request["writer"],
        )
    except Exception:
        return "WRONG"
    if (
        parsed.get("revision", 0) <= request["expected_revision"]
        or parsed.get("direction_id") != request["direction_id"]
        or parsed.get("workflow_version") != request["workflow_version"]
    ):
        return "WRONG"
    review_round = _find_active_round(parsed, request["round_id"])
    expected_ref = {
        "path": request["canonical_prompt_path"],
        "sha256": request["prompt_sha256"],
    }
    if (
        review_round is not None
        and review_round.get("prompt_refs", {}).get(request["review_stage"])
        == expected_ref
    ):
        return "DESCENDANT_NEW"
    return "WRONG"

def _registration_unknown(
    journal: Mapping[str, Any],
    observation: str,
) -> NoReturn:
    try:
        _registration_phase(journal, "UNKNOWN", observation=observation)
    except (ExternalReviewError, OSError):
        pass
    raise RegistrationUnknown(
        f"registration {journal['transaction_id']} is UNKNOWN: {observation}"
    )


def _require_exact_blob(
    journal: Mapping[str, Any],
    label: str,
) -> Path:
    observed, _ = _blob_observation(journal, label)
    if observed != "EXACT":
        _registration_unknown(
            journal,
            f"{label} staged bytes are {observed.lower()}",
        )
    return _registration_blob_path(journal, label)


def _publish_registration_prompt(journal: Mapping[str, Any]) -> None:
    if _prompt_observation(journal) == "EXACT":
        return
    if _prompt_observation(journal) != "ABSENT":
        _registration_unknown(journal, "canonical prompt bytes are irreconcilable")
    blob = _require_exact_blob(journal, "prompt")
    request = journal["transaction"]["request"]
    target = _owned_relative_path(
        PurePosixPath(request["canonical_prompt_path"]),
        label="journal canonical prompt path",
    )
    created = _prepare_owned_parent(target)
    allowed = set(journal["transaction"]["created_directories"])
    root = _PROJECT_ROOT.resolve()
    unexpected = [
        path for path in created if path.relative_to(root).as_posix() not in allowed
    ]
    if unexpected:
        for path in reversed(created):
            try:
                path.rmdir()
            except OSError:
                pass
        _registration_unknown(
            journal,
            "canonical prompt parent observations changed",
        )
    try:
        os.link(blob, target, follow_symlinks=False)
    except FileExistsError:
        if _prompt_observation(journal) != "EXACT":
            _registration_unknown(
                journal,
                "canonical prompt path collided with different bytes",
            )
    _fsync_directory(target.parent)
    if _prompt_observation(journal) != "EXACT":
        _registration_unknown(journal, "canonical prompt publication did not verify")


def _index_publish_path(journal: Mapping[str, Any]) -> Path:
    directory = _registration_transaction_directory(
        journal["transaction_id"],
        create=False,
    )
    return directory / "index.publish"


def _publish_registration_index(journal: Mapping[str, Any]) -> None:
    index_state = _index_observation(journal)
    if index_state in {"NEW", "DESCENDANT_NEW"}:
        return
    if index_state not in {"OLD", "MISSING"}:
        _registration_unknown(journal, "external-review index bytes are irreconcilable")
    blob = _require_exact_blob(journal, "new_index")
    publish = _index_publish_path(journal)
    if publish.exists() or publish.is_symlink():
        if publish.is_symlink() or not publish.is_file():
            _registration_unknown(journal, "index publication stage is unsafe")
        raw = _read_regular_bytes(publish, label="index publication stage")
        binding = journal["transaction"]["new_index"]
        if (
            len(raw) != binding["size_bytes"]
            or hashlib.sha256(raw).hexdigest() != binding["sha256"]
        ):
            _registration_unknown(journal, "index publication stage collided")
    else:
        os.link(blob, publish, follow_symlinks=False)
        _fsync_directory(publish.parent)
    request = journal["transaction"]["request"]
    target = _owned_relative_path(
        PurePosixPath(request["external_index_path"]),
        label="journal external-review index path",
    )
    if _index_observation(journal) not in {"OLD", "MISSING"}:
        _registration_unknown(
            journal,
            "external-review index changed before publication",
        )
    _replace_file(publish, target)
    _fsync_directory(target.parent)
    if _index_observation(journal) not in {"NEW", "DESCENDANT_NEW"}:
        _registration_unknown(journal, "external-review index publication did not verify")


def _check_registration_stages(journal: Mapping[str, Any]) -> None:
    for label in ("old_index", "new_index", "prompt"):
        observed, _ = _blob_observation(journal, label)
        if observed == "WRONG":
            _registration_unknown(journal, f"{label} staged bytes collided")
    publish = _index_publish_path(journal)
    if publish.exists() or publish.is_symlink():
        if publish.is_symlink() or not publish.is_file():
            _registration_unknown(journal, "index publication stage is unsafe")
        raw = _read_regular_bytes(publish, label="index publication stage")
        binding = journal["transaction"]["new_index"]
        if (
            len(raw) != binding["size_bytes"]
            or hashlib.sha256(raw).hexdigest() != binding["sha256"]
        ):
            _registration_unknown(journal, "index publication stage collided")


def _cleanup_registration_stages(journal: Mapping[str, Any]) -> None:
    _check_registration_stages(journal)
    directory = _registration_transaction_directory(
        journal["transaction_id"],
        create=False,
    )
    for path in (
        _index_publish_path(journal),
        _registration_blob_path(journal, "prompt"),
        _registration_blob_path(journal, "new_index"),
        _registration_blob_path(journal, "old_index"),
    ):
        _unlink_if_present(path)
    _fsync_directory(directory)


def _cleanup_rolled_back_directories(journal: Mapping[str, Any]) -> None:
    root = _PROJECT_ROOT.resolve()
    for relative in reversed(journal["transaction"]["created_directories"]):
        path = _owned_relative_path(
            PurePosixPath(relative),
            label="journal-created prompt directory",
        )
        try:
            path.rmdir()
        except OSError:
            continue
        _fsync_directory(path.parent)
        if path == root:
            break


def _registration_result(
    journal: Mapping[str, Any],
    status: str,
) -> dict[str, Any]:
    request = journal["transaction"]["request"]
    result = {
        "status": status,
        "transaction_id": journal["transaction_id"],
        "journal_phase": journal["phase"],
        "review_stage": request["review_stage"],
        "direction_id": request["direction_id"],
        "round_id": request["round_id"],
        "prompt_ref": {
            "path": request["canonical_prompt_path"],
            "sha256": request["prompt_sha256"],
        },
        "previous_external_index_revision": request["expected_revision"],
    }
    if status == "REGISTERED":
        result["external_index_revision"] = request["expected_revision"] + 1
    return result


def _finish_committed_registration(
    journal: Mapping[str, Any],
) -> dict[str, Any]:
    if _prompt_observation(journal) != "EXACT" or _index_observation(journal) not in {
        "NEW",
        "DESCENDANT_NEW",
    }:
        _registration_unknown(journal, "terminal new state did not verify")
    journal = _registration_phase(journal, "VERIFIED")
    journal = _registration_phase(journal, "CLEANING")
    _cleanup_registration_stages(journal)
    journal = _registration_phase(journal, "COMMITTED")
    return _registration_result(journal, "REGISTERED")


def _finish_rolled_back_registration(
    journal: Mapping[str, Any],
) -> dict[str, Any]:
    if _prompt_observation(journal) != "ABSENT" or _index_observation(journal) != "OLD":
        _registration_unknown(journal, "terminal old state did not verify")
    journal = _registration_phase(journal, "ROLLING_BACK")
    _cleanup_registration_stages(journal)
    _cleanup_rolled_back_directories(journal)
    journal = _registration_phase(journal, "ROLLED_BACK")
    return _registration_result(journal, "ROLLED_BACK")


def _recover_registration_locked(
    journal: Mapping[str, Any],
) -> dict[str, Any]:
    journal = _load_registration_journal(journal["transaction_id"])
    _check_registration_stages(journal)
    phase = journal["phase"]
    prompt_state = _prompt_observation(journal)
    index_state = _index_observation(journal)
    if prompt_state == "WRONG" or index_state == "WRONG":
        _registration_unknown(
            journal,
            f"canonical observations are index={index_state}, prompt={prompt_state}",
        )
    if phase == "ROLLED_BACK":
        if index_state == "OLD" and prompt_state == "ABSENT":
            return _registration_result(journal, "ROLLED_BACK")
        _registration_unknown(journal, "rolled-back terminal state changed")
    if phase == "COMMITTED":
        if index_state in {"NEW", "DESCENDANT_NEW"} and prompt_state == "EXACT":
            _cleanup_registration_stages(journal)
            return _registration_result(journal, "REGISTERED")
        _registration_unknown(journal, "committed terminal state changed")
    if index_state == "MISSING" and prompt_state == "ABSENT":
        old_blob = _require_exact_blob(journal, "old_index")
        request = journal["transaction"]["request"]
        target = _owned_relative_path(
            PurePosixPath(request["external_index_path"]),
            label="journal external-review index path",
        )
        publish = _index_publish_path(journal)
        if publish.exists() or publish.is_symlink():
            _unlink_if_present(publish)
        os.link(old_blob, publish, follow_symlinks=False)
        _fsync_directory(publish.parent)
        _replace_file(publish, target)
        _fsync_directory(target.parent)
        index_state = _index_observation(journal)
    if index_state == "OLD" and prompt_state == "ABSENT":
        if phase in {"PREPARING", "STAGED", "ROLLING_BACK", "UNKNOWN"}:
            return _finish_rolled_back_registration(journal)
        _publish_registration_prompt(journal)
        journal = _registration_phase(journal, "PROMPT_PUBLISHED")
        prompt_state = "EXACT"
    if prompt_state == "EXACT" and index_state in {"OLD", "MISSING"}:
        _publish_registration_index(journal)
        journal = _registration_phase(journal, "INDEX_PUBLISHED")
        index_state = _index_observation(journal)
    elif prompt_state == "ABSENT" and index_state in {"NEW", "DESCENDANT_NEW"}:
        _publish_registration_prompt(journal)
        journal = _registration_phase(journal, "PROMPT_PUBLISHED")
        prompt_state = "EXACT"
    if prompt_state == "EXACT" and index_state in {"NEW", "DESCENDANT_NEW"}:
        return _finish_committed_registration(journal)
    _registration_unknown(
        journal,
        f"no deterministic terminal state for index={index_state}, prompt={prompt_state}",
    )


def recover_registration(transaction_id: str) -> dict[str, Any]:
    """Recover one exact durable prompt registration without semantic choice."""

    journal = _load_registration_journal(transaction_id)
    request = journal["transaction"]["request"]
    index_path = _owned_relative_path(
        PurePosixPath(request["external_index_path"]),
        label="journal external-review index path",
    )
    state = _state_module()
    with state.state_lock(index_path):
        return _recover_registration_locked(journal)


def _new_registration_journal(
    request: Mapping[str, Any],
    validated: _PromptValidation,
    next_index_raw: bytes,
) -> dict[str, Any]:
    transaction = _registration_transaction(request, validated, next_index_raw)
    identifier = _transaction_id(transaction)
    journal = {
        "schema": _REGISTRATION_JOURNAL_SCHEMA,
        "transaction_id": identifier,
        "transaction": transaction,
        "phase": "PREPARING",
        "updated_at": _registration_timestamp(),
    }
    _write_registration_journal(journal)
    return journal


def _run_registration(
    journal: Mapping[str, Any],
    *,
    old_index_raw: bytes,
    new_index_raw: bytes,
    prompt_raw: bytes,
) -> dict[str, Any]:
    _write_registration_blob(journal, "old_index", old_index_raw)
    _write_registration_blob(journal, "new_index", new_index_raw)
    _write_registration_blob(journal, "prompt", prompt_raw)
    journal = _registration_phase(journal, "STAGED")
    _publish_registration_prompt(journal)
    journal = _registration_phase(journal, "PROMPT_PUBLISHED")
    _publish_registration_index(journal)
    journal = _registration_phase(journal, "INDEX_PUBLISHED")
    return _finish_committed_registration(journal)


def register_prompt(
    review_stage: str,
    prompt: os.PathLike[str] | str,
    *,
    external_index: os.PathLike[str] | str,
    direction_id: str,
    round_id_value: str,
    question_sha256: str,
    evidence_set_sha256: str,
    workflow_version: str,
    expected_revision: int,
    prompt_sha256: str,
    local_synthesis_ref: Any = None,
    innovator_prompt_ref: Any = None,
) -> dict[str, Any]:
    """Register exact bytes through a crash-recoverable durable transaction."""

    request, index_path = _registration_request(
        review_stage,
        prompt,
        external_index=external_index,
        direction_id=direction_id,
        round_id_value=round_id_value,
        question_sha256=question_sha256,
        evidence_set_sha256=evidence_set_sha256,
        workflow_version=workflow_version,
        expected_revision=expected_revision,
        prompt_sha256=prompt_sha256,
        local_synthesis_ref=local_synthesis_ref,
        innovator_prompt_ref=innovator_prompt_ref,
    )
    state = _state_module()
    with state.state_lock(index_path):
        journals = _registration_journals()
        matches = [
            journal
            for journal in journals
            if journal["transaction"]["request"] == request
        ]
        if len(matches) > 1:
            raise RegistrationUnknown(
                "multiple content-addressed journals bind the exact registration request"
            )
        if matches:
            return _recover_registration_locked(matches[0])
        for journal in journals:
            journal_request = journal["transaction"]["request"]
            if (
                journal_request["external_index_path"]
                == request["external_index_path"]
                and journal["phase"] not in _REGISTRATION_TERMINAL_PHASES
            ):
                _recover_registration_locked(journal)

        validated = _validated_stage_prompt(
            review_stage,
            prompt,
            external_index=external_index,
            direction_id=direction_id,
            round_id_value=round_id_value,
            question_sha256=question_sha256,
            evidence_set_sha256=evidence_set_sha256,
            workflow_version=workflow_version,
            local_synthesis_ref=local_synthesis_ref,
            innovator_prompt_ref=innovator_prompt_ref,
            expected_prompt_sha256=request["prompt_sha256"],
        )
        if validated.index["revision"] != expected_revision:
            raise RevisionConflict(
                f"expected revision {expected_revision}, "
                f"observed {validated.index['revision']}"
            )
        if validated.canonical_path.exists() or validated.canonical_path.is_symlink():
            raise ExternalReviewError(
                "canonical prompt path is already registered and immutable: "
                f"{validated.canonical_path}"
            )
        next_index = _next_prompt_index(validated)
        try:
            state.validate_document(
                "external_review_index",
                next_index,
                writer=request["writer"],
            )
        except state.StateError as exc:
            raise ExternalReviewError(
                f"registered external-review index would be invalid: {exc}"
            ) from exc
        next_index_raw = _canonical_json(next_index)
        journal = _new_registration_journal(
            request,
            validated,
            next_index_raw,
        )
        try:
            return _run_registration(
                journal,
                old_index_raw=validated.index_raw,
                new_index_raw=next_index_raw,
                prompt_raw=validated.prompt_raw,
            )
        except Exception:
            journal_path = _registration_journal_path(journal["transaction_id"])
            if journal_path.exists() and not journal_path.is_symlink():
                return _recover_registration_locked(journal)
            raise


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
    """Validate one current operation receipt against reread raw response bytes."""

    return _archive_record(operation_ref, archive).data.copy()


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _ensure_parent(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _fsync_directory(path.parent)
    except OSError as exc:
        raise PathRefusal(f"cannot prepare archive parent {path.parent}: {exc}") from exc


def _owned_destination(operation: Mapping[str, Any], destination: os.PathLike[str] | str) -> Path:
    root = _PROJECT_ROOT.resolve()
    relative = PurePosixPath(str(operation["archive"]["path"]))
    expected = root.joinpath(*relative.parts)
    supplied = Path(destination)
    target = supplied if supplied.is_absolute() else root / supplied
    try:
        if target.resolve(strict=False) != expected.resolve(strict=False):
            raise PathRefusal(
                "response destination does not match the operation reference's owned response path"
            )
        parent = root
        for component in relative.parts[:-1]:
            parent /= component
            if parent.is_symlink():
                raise PathRefusal(f"owned response path contains a symlinked parent: {parent}")
    except (OSError, RuntimeError) as exc:
        raise PathRefusal(f"cannot resolve owned response destination: {target}: {exc}") from exc
    return expected


def _publish_exact_file(path: Path, raw: bytes, *, label: str) -> str:
    _ensure_parent(path)
    fd: int | None = None
    temporary: Path | None = None
    try:
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
        temporary = Path(temporary_name)
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError(f"short {label} write")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = None
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError:
            if path.is_symlink() or not path.is_file():
                raise PathRefusal(f"{label} destination is not a regular file: {path}")
            first = _read_regular_bytes(path, label=f"existing {label}")
            second = _read_regular_bytes(path, label=f"existing {label} reread")
            if first != second:
                raise ArchiveConflict(f"{label} destination changed during exact reread")
            if first != raw:
                raise ArchiveConflict(f"{label} destination has different exact bytes")
            return "IDEMPOTENT"
        _fsync_directory(path.parent)
        return "CREATED"
    except FileNotFoundError as exc:
        raise PathRefusal(f"{label} destination parent disappeared: {path.parent}") from exc
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


def create_archive_if_absent(
    operation_ref: Any,
    archive: Any,
    destination: os.PathLike[str] | str,
) -> dict[str, Any]:
    """Publish exact raw response bytes and their immutable current operation receipt."""

    operation_value, _, _ = _input_value(operation_ref, label="operation reference")
    operation = _validate_operation_ref(operation_value)
    record = _archive_record(operation, archive)
    target = _owned_destination(operation, destination)
    if target.exists() and target.is_dir():
        raise PathRefusal(f"response destination is a directory: {target}")
    target = _owned_destination(operation, target)
    response_status = _publish_exact_file(target, record.raw_bytes, label="response")

    relative_response = PurePosixPath(operation["archive"]["path"])
    operation_relative = _owned_operation_ref_path(relative_response)
    operation_target = _PROJECT_ROOT.resolve().joinpath(*operation_relative.parts)
    operation_raw = _canonical_json(operation)
    operation_status = _publish_exact_file(
        operation_target,
        operation_raw,
        label="operation reference",
    )
    if response_status == operation_status == "IDEMPOTENT":
        status = "IDEMPOTENT"
    elif response_status == operation_status == "CREATED":
        status = "CREATED"
    else:
        status = "RECOVERED"
    return {
        "status": status,
        "response_ref": {
            "path": relative_response.as_posix(),
            "sha256": record.archive_sha256,
            "size_bytes": len(record.raw_bytes),
        },
        "operation_ref": {
            "path": operation_relative.as_posix(),
            "sha256": hashlib.sha256(operation_raw).hexdigest(),
        },
    }


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
    operation_ref: Any,
    archive: Any,
    out: os.PathLike[str] | str,
) -> dict[str, Any]:
    """Render a mechanical, ignored handoff from one exact current receipt."""

    record = _archive_record(operation_ref, archive)
    rendered = {
        "handoff_kind": "hmasd_external_review_intake_v3",
        "operation_ref": record.data,
        "response_sha256": record.archive_sha256,
        "response_size_bytes": len(record.raw_bytes),
        "response_text": record.raw_bytes.decode("utf-8"),
    }
    _write_json_atomic(Path(out), rendered)
    return rendered


def _add_prompt_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--review-stage",
        choices=tuple(sorted(_SUPPORTED_REVIEW_STAGES)),
        required=True,
    )
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--external-index", required=True)
    parser.add_argument("--direction", required=True)
    parser.add_argument("--round-id", required=True)
    parser.add_argument("--question-sha", required=True)
    parser.add_argument("--evidence-sha", required=True)
    parser.add_argument("--workflow-version", required=True)
    parser.add_argument("--local-synthesis-ref")
    parser.add_argument("--innovator-prompt-ref")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)


    prompt_parser = commands.add_parser(
        "validate-prompt",
        help="validate one disposable stage prompt without durable effects",
    )
    _add_prompt_arguments(prompt_parser)

    register_parser = commands.add_parser(
        "register-prompt",
        help="durably register one validated stage prompt",
    )
    _add_prompt_arguments(register_parser)
    register_parser.add_argument("--prompt-sha", required=True)
    register_parser.add_argument("--expected-revision", required=True, type=int)

    recovery_parser = commands.add_parser(
        "recover-registration",
        help="recover one exact content-addressed registration transaction",
    )
    recovery_parser.add_argument("--transaction-id", required=True)

    return parser


def _command_result(args: argparse.Namespace) -> Any:
    if args.command == "validate-prompt":
        return validate_prompt(
            args.review_stage,
            args.prompt,
            external_index=args.external_index,
            direction_id=args.direction,
            round_id_value=args.round_id,
            question_sha256=args.question_sha,
            evidence_set_sha256=args.evidence_sha,
            workflow_version=args.workflow_version,
            local_synthesis_ref=args.local_synthesis_ref,
            innovator_prompt_ref=args.innovator_prompt_ref,
        )
    if args.command == "register-prompt":
        return register_prompt(
            args.review_stage,
            args.prompt,
            external_index=args.external_index,
            direction_id=args.direction,
            round_id_value=args.round_id,
            question_sha256=args.question_sha,
            evidence_set_sha256=args.evidence_sha,
            workflow_version=args.workflow_version,
            expected_revision=args.expected_revision,
            prompt_sha256=args.prompt_sha,
            local_synthesis_ref=args.local_synthesis_ref,
            innovator_prompt_ref=args.innovator_prompt_ref,
        )
    if args.command == "recover-registration":
        return recover_registration(args.transaction_id)
    raise ExternalReviewError(f"unknown command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = _command_result(args)
    except RegistrationUnknown as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 8
    except CommitmentUnknown as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 7
    except ArchiveConflict as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 6
    except RevisionConflict as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4
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
