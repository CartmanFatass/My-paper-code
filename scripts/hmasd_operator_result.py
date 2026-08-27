#!/usr/bin/env python3
"""Validate the narrow HMASD v2 Experiment Operator terminal result."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from scripts import hmasd_platform
except ImportError:
    import hmasd_platform


SCHEMA_PATH = Path(__file__).with_name("schemas") / "hmasd_operator_result_v2.schema.json"
SCHEMA_VERSION = 2
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
RUN_ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
OPERATOR_IDENTITY_RE = re.compile(r"Operator-[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
PATH_RE = re.compile(
    r"(?!/)(?![A-Za-z]:)(?!.*\\)(?!.*[\x00-\x1f\x7f-\x9f])"
    r"(?!.*:)(?!\.{1,2}(?:/|$))(?!.*//)(?!.*(?:^|/)\.{1,2}(?:/|$))"
    r"(?![^/]*[. ](?:/|$))(?!.*/[^/]*[. ](?:/|$))[^/]+(?:/[^/]+)*\Z"
)
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "CANCELLED", "UNKNOWN"}
FIELDS = {
    "schema_version",
    "assignment_message_id",
    "run_id",
    "operator_identity",
    "manifest_ref",
    "stdout_ref",
    "stderr_ref",
    "terminal_status",
    "exit_code",
}


class OperatorResultError(Exception):
    """Base error for the Operator result seam."""


class ValidationError(OperatorResultError):
    """The document is not a narrow v2 Operator terminal result."""


class PublicationError(OperatorResultError):
    """The immutable Operator result could not be published."""


def _validate_file_ref(value: Any, label: str) -> None:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ValidationError(f"{label} must contain only path and sha256")
    path = value.get("path")
    digest = value.get("sha256")
    if not isinstance(path, str) or PATH_RE.fullmatch(path) is None:
        raise ValidationError(f"{label}.path is invalid")
    if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
        raise ValidationError(f"{label}.sha256 is invalid")


def validate_document(document: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return one narrow Operator terminal result unchanged."""

    if not isinstance(document, dict):
        raise ValidationError("operator result must be a JSON object")
    if set(document) != FIELDS:
        missing = sorted(FIELDS - set(document))
        extra = sorted(set(document) - FIELDS)
        raise ValidationError(
            f"operator result fields are invalid; missing={missing}, extra={extra}"
        )
    if document["schema_version"] != SCHEMA_VERSION:
        raise ValidationError(f"schema_version must be {SCHEMA_VERSION}")
    assignment_message_id = document["assignment_message_id"]
    if (
        not isinstance(assignment_message_id, str)
        or ID_RE.fullmatch(assignment_message_id) is None
    ):
        raise ValidationError("assignment_message_id is invalid")
    run_id = document["run_id"]
    if not isinstance(run_id, str) or RUN_ID_RE.fullmatch(run_id) is None:
        raise ValidationError("run_id is invalid")
    operator_identity = document["operator_identity"]
    if (
        not isinstance(operator_identity, str)
        or OPERATOR_IDENTITY_RE.fullmatch(operator_identity) is None
    ):
        raise ValidationError("operator_identity is invalid")
    for label in ("manifest_ref", "stdout_ref", "stderr_ref"):
        _validate_file_ref(document[label], label)
    terminal_status = document["terminal_status"]
    if terminal_status not in TERMINAL_STATUSES:
        raise ValidationError("terminal_status is invalid")
    exit_code = document["exit_code"]
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool) or exit_code < 0
    ):
        raise ValidationError("exit_code must be a non-negative integer or null")
    if terminal_status == "SUCCEEDED" and exit_code != 0:
        raise ValidationError("SUCCEEDED requires exit_code 0")
    return document


def publish_document(
    path: str | os.PathLike[str], document: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate and create one immutable result without replacing any path."""

    validated = validate_document(document)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(validated, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, raw_temporary = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".init", dir=target.parent
        )
        temporary = Path(raw_temporary)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise PublicationError("short write while staging operator result")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        try:
            os.link(temporary, target)
        except FileExistsError as exc:
            raise PublicationError(f"operator result path already exists: {target}") from exc
        hmasd_platform.fsync_directory(target.parent)
    except PublicationError:
        raise
    except OSError as exc:
        raise PublicationError(f"cannot publish operator result {target}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            with contextlib.suppress(FileNotFoundError):
                temporary.unlink()
    return validated


def _load(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read operator result {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise ValidationError("operator result must be a JSON object")
    return document


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate one Operator result")
    validate.add_argument("--path", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        document = validate_document(_load(Path(args.path)))
    except OperatorResultError as exc:
        print(f"hmasd operator result refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
