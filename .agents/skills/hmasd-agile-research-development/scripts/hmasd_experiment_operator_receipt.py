#!/usr/bin/env python3
"""Deterministic receipt writer/checker for the Experiment Operator boundary."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


INPUT_KEYS = (
    "run",
    "source_commit",
    "execution_mode",
    "phase",
    "exit_codes",
    "artifacts",
    "last_progress",
    "process_live",
    "direct_error",
)
OUTPUT_KEYS = INPUT_KEYS + ("terminal",)
EXECUTION_MODES = {"fresh", "retry", "resume", "restart"}
PHASES = ("NONE", "TRAIN", "EVALUATE", "ANALYZE")
EXIT_KEYS = ("train", "evaluate", "analyze")
UPPER_EXIT_KEYS = tuple(key.upper() for key in EXIT_KEYS)
SOURCE_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class ReceiptError(ValueError):
    """A deterministic receipt input or output is invalid."""


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReceiptError(f"cannot read JSON: {path}: {exc}") from exc


def _require_exact_keys(value: dict[str, Any], expected: tuple[str, ...]) -> None:
    if set(value) != set(expected):
        missing = sorted(set(expected) - set(value))
        extra = sorted(set(value) - set(expected))
        details = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if extra:
            details.append(f"extra={','.join(extra)}")
        raise ReceiptError("exact keys required (" + "; ".join(details) + ")")


def _validate_exit_codes(
    value: Any, *, allow_uppercase: bool = True
) -> dict[str, int | None]:
    if not isinstance(value, dict):
        raise ReceiptError("exit_codes must be an object")
    if set(value) == set(EXIT_KEYS):
        input_keys = EXIT_KEYS
    elif allow_uppercase and set(value) == set(UPPER_EXIT_KEYS):
        input_keys = UPPER_EXIT_KEYS
    else:
        _require_exact_keys(value, EXIT_KEYS)
        input_keys = EXIT_KEYS

    normalized: dict[str, int | None] = {}
    for key, input_key in zip(EXIT_KEYS, input_keys):
        code = value[input_key]
        if code is not None and (isinstance(code, bool) or not isinstance(code, int)):
            raise ReceiptError(f"exit_codes.{key} must be an integer or null")
        normalized[key] = code

    # Execution is sequential: a later phase cannot have an exit code after
    # an earlier phase was not attempted, and a failed phase cannot be followed.
    saw_unrun = False
    for key in EXIT_KEYS:
        code = normalized[key]
        if code is None:
            saw_unrun = True
        elif saw_unrun:
            raise ReceiptError("exit_codes contain an out-of-order later phase")
    for index, key in enumerate(EXIT_KEYS[:-1]):
        code = normalized[key]
        if code is not None and code != 0 and any(
            normalized[later] is not None for later in EXIT_KEYS[index + 1 :]
        ):
            raise ReceiptError("a nonzero phase exit cannot be followed by another phase")
    return normalized


def _validate_record(value: Any, *, receipt: bool) -> tuple[dict[str, Any], str]:
    if not isinstance(value, dict):
        raise ReceiptError("record must be a JSON object")
    _require_exact_keys(value, OUTPUT_KEYS if receipt else INPUT_KEYS)

    run = value["run"]
    if not isinstance(run, str) or not run.strip():
        raise ReceiptError("run must be a nonempty string")
    source_commit = value["source_commit"]
    if not isinstance(source_commit, str) or not SOURCE_COMMIT_RE.fullmatch(source_commit):
        raise ReceiptError("source_commit must be exactly 40 lowercase hex characters")
    if value["execution_mode"] not in EXECUTION_MODES:
        raise ReceiptError("execution_mode must be fresh, retry, resume, or restart")

    phase = value["phase"]
    if phase not in PHASES:
        raise ReceiptError("phase must be NONE, TRAIN, EVALUATE, or ANALYZE")
    exit_codes = _validate_exit_codes(
        value["exit_codes"], allow_uppercase=not receipt
    )

    artifacts = value["artifacts"]
    if not isinstance(artifacts, (list, dict)):
        raise ReceiptError("artifacts must be a list or object")
    if not isinstance(value["process_live"], bool):
        raise ReceiptError("process_live must be boolean")
    if value["process_live"]:
        raise ReceiptError("terminal receipt cannot have process_live=true")

    direct_error = value["direct_error"]
    if direct_error is not None and (
        not isinstance(direct_error, str) or not direct_error.strip()
    ):
        raise ReceiptError("direct_error must be null or a nonempty string")

    attempted_count = PHASES.index(phase)
    for index, key in enumerate(EXIT_KEYS):
        attempted = exit_codes[key] is not None
        if attempted != (index < attempted_count):
            if index < attempted_count:
                raise ReceiptError(f"phase {phase} requires {key} to have an exit code")
            raise ReceiptError(f"phase {phase} cannot contain a later phase exit code")

    if direct_error is not None:
        terminal = "ERROR"
    elif phase == "ANALYZE" and all(exit_codes[key] == 0 for key in EXIT_KEYS):
        terminal = "COMPLETE"
    else:
        raise ReceiptError(
            "incomplete or nonzero exits require a nonempty direct_error"
        )

    if terminal == "COMPLETE" and not artifacts:
        raise ReceiptError("COMPLETE requires nonempty artifacts")

    if receipt and value["terminal"] != terminal:
        raise ReceiptError("terminal does not match the derived terminal")
    normalized = {key: value[key] for key in INPUT_KEYS}
    normalized["exit_codes"] = exit_codes
    if receipt:
        normalized["terminal"] = value["terminal"]
    return normalized, terminal


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    parent = path.parent
    if not parent.is_dir():
        raise ReceiptError(f"receipt parent does not exist: {parent}")
    encoded = (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{path.name}.", suffix=".tmp", dir=parent, delete=False
        ) as handle:
            temporary_name = handle.name
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    except OSError as exc:
        raise ReceiptError(f"atomic receipt write failed: {path}: {exc}") from exc
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


def _ascii_terminal_text(value: object) -> str:
    """Keep compact terminal evidence writable on legacy Windows consoles."""
    return str(value).encode("ascii", errors="backslashreplace").decode("ascii")


def _success(command: str, terminal: str, path: Path) -> None:
    safe_path = _ascii_terminal_text(path)
    print(
        "HMASD_EXPERIMENT_OPERATOR_RECEIPT_OK "
        f"command={command} terminal={terminal} receipt_path={safe_path}"
    )


def _run_write(record_path: Path, receipt_path: Path) -> None:
    record = _load_json(record_path)
    normalized, terminal = _validate_record(record, receipt=False)
    normalized["terminal"] = terminal
    _atomic_write(receipt_path, normalized)
    _success("write", terminal, receipt_path)


def _run_check(receipt_path: Path) -> None:
    receipt = _load_json(receipt_path)
    _, terminal = _validate_record(receipt, receipt=True)
    _success("check", terminal, receipt_path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    write = commands.add_parser("write", help="validate and atomically write a receipt")
    write.add_argument("--record", required=True, type=Path)
    write.add_argument("--receipt", required=True, type=Path)
    check = commands.add_parser("check", help="validate an existing receipt")
    check.add_argument("--receipt", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "write":
            _run_write(args.record, args.receipt)
        else:
            _run_check(args.receipt)
    except ReceiptError as exc:
        print(
            "HMASD_EXPERIMENT_OPERATOR_RECEIPT_ERROR: "
            f"{_ascii_terminal_text(exc)}",
            file=os.sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
