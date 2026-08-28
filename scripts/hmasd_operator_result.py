#!/usr/bin/env python3
"""Validate the narrow HMASD Experiment Operator terminal observation."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from scripts import hmasd_platform
except ImportError:
    import hmasd_platform


SCHEMA_PATH = Path(__file__).with_name("schemas") / "hmasd_operator_result_v1.schema.json"
SCHEMA_VERSION = 1
RUN_ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
PATH_RE = re.compile(
    r"(?!/)(?![A-Za-z]:)(?!.*\\)(?!.*[\x00-\x1f\x7f-\x9f])"
    r"(?!.*:)(?!\.{1,2}(?:/|$))(?!.*//)(?!.*(?:^|/)\.{1,2}(?:/|$))"
    r"(?![^/]*[. ](?:/|$))(?!.*/[^/]*[. ](?:/|$))[^/]+(?:/[^/]+)*\Z"
)
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "CANCELLED", "UNKNOWN"}
FIELDS = {
    "schema_version", "run_id", "manifest_path", "stdout_path", "stderr_path",
    "terminal_status", "exit_code", "observed_at",
}


class OperatorResultError(Exception):
    pass


class ValidationError(OperatorResultError):
    pass


class PublicationError(OperatorResultError):
    pass


def _validate_path(value: Any, label: str) -> None:
    if not isinstance(value, str) or PATH_RE.fullmatch(value) is None:
        raise ValidationError(f"{label} is invalid")


def _validate_timestamp(value: Any) -> None:
    if not isinstance(value, str):
        raise ValidationError("observed_at is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError("observed_at is invalid") from exc
    if parsed.tzinfo is None:
        raise ValidationError("observed_at must include timezone")


def validate_document(document: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValidationError("operator result must be a JSON object")
    if set(document) != FIELDS:
        missing = sorted(FIELDS - set(document))
        extra = sorted(set(document) - FIELDS)
        raise ValidationError(f"operator result fields are invalid; missing={missing}, extra={extra}")
    if document["schema_version"] != SCHEMA_VERSION:
        raise ValidationError(f"schema_version must be {SCHEMA_VERSION}")
    if not isinstance(document["run_id"], str) or RUN_ID_RE.fullmatch(document["run_id"]) is None:
        raise ValidationError("run_id is invalid")
    for field in ("manifest_path", "stdout_path", "stderr_path"):
        _validate_path(document[field], field)
    if document["terminal_status"] not in TERMINAL_STATUSES:
        raise ValidationError("terminal_status is invalid")
    exit_code = document["exit_code"]
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool) or exit_code < 0
    ):
        raise ValidationError("exit_code must be a non-negative integer or null")
    if document["terminal_status"] == "SUCCEEDED" and exit_code != 0:
        raise ValidationError("SUCCEEDED requires exit_code 0")
    _validate_timestamp(document["observed_at"])
    return dict(document)


def publish_document(path: str | os.PathLike[str], document: Mapping[str, Any]) -> dict[str, Any]:
    validated = validate_document(document)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(validated, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, raw = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".init", dir=target.parent)
        temporary = Path(raw)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
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
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read operator result {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError("operator result must be a JSON object")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--path", required=True)
    args = parser.parse_args(argv)
    try:
        result = validate_document(_load(Path(args.path)))
    except OperatorResultError as exc:
        print(f"hmasd operator result refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
