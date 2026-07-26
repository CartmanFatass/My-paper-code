#!/usr/bin/env python3
"""Measure complete HMASD Project Manager workflows from local Codex usage."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Any


SCHEMA_VERSION = 1
TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
PRICES = {
    "gpt-5.6-sol": {
        "input": Decimal("5.00"),
        "cached_input": Decimal("0.50"),
        "cache_write": Decimal("6.25"),
        "output": Decimal("30.00"),
    },
    "gpt-5.6-terra": {
        "input": Decimal("2.50"),
        "cached_input": Decimal("0.25"),
        "cache_write": Decimal("3.125"),
        "output": Decimal("15.00"),
    },
    "gpt-5.6-luna": {
        "input": Decimal("1.00"),
        "cached_input": Decimal("0.10"),
        "cache_write": Decimal("1.25"),
        "output": Decimal("6.00"),
    },
}
PRICE_EFFECTIVE_DATE = "2026-07-26"
EVENT_PENALTIES = {
    "post_acceptance_defect": (20, 40),
    "downstream_rework": (10, 25),
    "workflow_violation": (20, 20),
    "pm_caused_clarification": (5, 15),
}


class MetricsError(RuntimeError):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status


def _now() -> tuple[str, int]:
    current = datetime.now(timezone.utc)
    return current.isoformat(timespec="milliseconds").replace("+00:00", "Z"), int(
        current.timestamp() * 1000
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _default_state_db() -> Path:
    return Path.home() / ".codex" / "state_5.sqlite"


def _default_ledger() -> Path:
    return _repo_root() / "logs" / "pm-model-performance" / "ledger.jsonl"


def _bool(value: str) -> bool:
    normalized = value.lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def _empty_usage() -> dict[str, int]:
    return {field: 0 for field in TOKEN_FIELDS}


def _normalize_usage(raw: dict[str, Any]) -> dict[str, int]:
    usage = {field: int(raw.get(field, 0) or 0) for field in TOKEN_FIELDS}
    if any(value < 0 for value in usage.values()):
        raise MetricsError("INVALID_TOKEN_USAGE", "token counters must be nonnegative")
    if usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
        raise MetricsError(
            "INVALID_TOKEN_USAGE", "total_tokens must equal input_tokens plus output_tokens"
        )
    if (
        usage["cached_input_tokens"] + usage["cache_write_input_tokens"]
        > usage["input_tokens"]
    ):
        raise MetricsError(
            "INVALID_TOKEN_USAGE", "cached and cache-write input exceed total input"
        )
    if usage["reasoning_output_tokens"] > usage["output_tokens"]:
        raise MetricsError(
            "INVALID_TOKEN_USAGE", "reasoning output exceeds total output"
        )
    return usage


def _thread_row(state_db: Path, thread_id: str) -> dict[str, str]:
    if not state_db.is_file():
        raise MetricsError("STATE_DB_UNAVAILABLE", f"missing state database: {state_db}")
    connection = sqlite3.connect(f"file:{state_db.as_posix()}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT id, model, reasoning_effort, rollout_path FROM threads WHERE id = ?",
            (thread_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise MetricsError("THREAD_NOT_FOUND", f"thread not found: {thread_id}")
    values = dict(zip(("id", "model", "reasoning_effort", "rollout_path"), row))
    if not all(values.values()):
        raise MetricsError("THREAD_STATE_INCOMPLETE", "thread metrics fields are incomplete")
    return {key: str(value) for key, value in values.items()}


def _settings_from_event(obj: dict[str, Any]) -> tuple[str | None, str | None]:
    payload = obj.get("payload")
    if not isinstance(payload, dict):
        return None, None
    if obj.get("type") == "turn_context":
        return payload.get("model"), payload.get("effort")
    if obj.get("type") == "event_msg" and payload.get("type") == "thread_settings_applied":
        settings = payload.get("thread_settings")
        if isinstance(settings, dict):
            return settings.get("model"), settings.get("reasoning_effort")
    return None, None


def _scan_rollout(
    rollout: Path, start_offset: int = 0
) -> tuple[int, dict[str, int] | None, set[str], set[str]]:
    if not rollout.is_file():
        raise MetricsError("ROLLOUT_UNAVAILABLE", f"missing rollout: {rollout}")
    latest: dict[str, int] | None = None
    models: set[str] = set()
    efforts: set[str] = set()
    complete_offset = start_offset
    with rollout.open("rb") as handle:
        handle.seek(start_offset)
        while True:
            line_start = handle.tell()
            raw_line = handle.readline()
            if not raw_line:
                break
            if not raw_line.endswith(b"\n"):
                complete_offset = line_start
                break
            complete_offset = handle.tell()
            try:
                obj = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise MetricsError("ROLLOUT_PARSE_ERROR", f"invalid JSONL at {line_start}: {exc}")
            model, effort = _settings_from_event(obj)
            if model:
                models.add(str(model))
            if effort:
                efforts.add(str(effort))
            payload = obj.get("payload")
            if (
                obj.get("type") == "event_msg"
                and isinstance(payload, dict)
                and payload.get("type") == "token_count"
            ):
                info = payload.get("info")
                if isinstance(info, dict) and isinstance(info.get("total_token_usage"), dict):
                    latest = _normalize_usage(info["total_token_usage"])
    return complete_offset, latest, models, efforts


def _load_events(ledger: Path) -> list[dict[str, Any]]:
    if not ledger.exists():
        return []
    events: list[dict[str, Any]] = []
    with ledger.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise MetricsError(
                    "LEDGER_PARSE_ERROR", f"invalid ledger JSON at line {line_number}: {exc}"
                )
            if event.get("schema_version") != SCHEMA_VERSION:
                raise MetricsError(
                    "LEDGER_SCHEMA_ERROR", f"unsupported schema at line {line_number}"
                )
            events.append(event)
    return events


def _append_event(ledger: Path, event: dict[str, Any]) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _rounds(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rounds: dict[str, dict[str, Any]] = {}
    for event in events:
        round_id = event.get("round_id")
        if not round_id:
            raise MetricsError("LEDGER_SCHEMA_ERROR", "ledger event lacks round_id")
        record = rounds.setdefault(
            str(round_id), {"start": None, "close": None, "quality_events": []}
        )
        event_type = event.get("event")
        if event_type == "round_started":
            if record["start"] is not None:
                raise MetricsError("LEDGER_SCHEMA_ERROR", f"duplicate start: {round_id}")
            record["start"] = event
        elif event_type == "round_closed":
            if record["close"] is not None:
                raise MetricsError("LEDGER_SCHEMA_ERROR", f"duplicate close: {round_id}")
            record["close"] = event
        elif event_type == "quality_event_added":
            record["quality_events"].append(event["quality_event"])
        else:
            raise MetricsError("LEDGER_SCHEMA_ERROR", f"unknown ledger event: {event_type}")
    return rounds


def _quality(events: list[dict[str, Any]]) -> tuple[int, dict[str, int]]:
    counts = {event_type: 0 for event_type in EVENT_PENALTIES}
    for event in events:
        event_type = event.get("event_type")
        if event_type not in counts or event.get("attributed_to_pm") is not True:
            raise MetricsError("INVALID_QUALITY_EVENT", "quality event is invalid")
        counts[event_type] += 1
    deduction = sum(
        min(cap, penalty * counts[event_type])
        for event_type, (penalty, cap) in EVENT_PENALTIES.items()
    )
    return max(0, 100 - deduction), counts


def _usage_delta(end: dict[str, int], start: dict[str, int]) -> dict[str, int]:
    delta = {field: end[field] - start[field] for field in TOKEN_FIELDS}
    if any(value < 0 for value in delta.values()):
        raise MetricsError("TOKEN_COUNTER_REGRESSED", "cumulative token counter regressed")
    return _normalize_usage(delta)


def _cost(model: str, usage: dict[str, int]) -> tuple[str, dict[str, str]]:
    rates = PRICES.get(model)
    if rates is None:
        raise MetricsError("UNSUPPORTED_MODEL", f"no current reference price for {model}")
    uncached = (
        usage["input_tokens"]
        - usage["cached_input_tokens"]
        - usage["cache_write_input_tokens"]
    )
    amount = (
        Decimal(uncached) * rates["input"]
        + Decimal(usage["cached_input_tokens"]) * rates["cached_input"]
        + Decimal(usage["cache_write_input_tokens"]) * rates["cache_write"]
        + Decimal(usage["output_tokens"]) * rates["output"]
    ) / Decimal(1_000_000)
    return format(amount.quantize(Decimal("0.000000001")), "f"), {
        key: format(value, "f") for key, value in rates.items()
    }


def _start(args: argparse.Namespace) -> dict[str, Any]:
    events = _load_events(args.ledger)
    rounds = _rounds(events)
    for record in rounds.values():
        start = record["start"]
        if start and start["thread_id"] == args.thread_id and record["close"] is None:
            raise MetricsError("ACTIVE_ROUND_EXISTS", "this PM task already has an open round")
    thread = _thread_row(args.state_db, args.thread_id)
    if thread["model"] not in PRICES:
        raise MetricsError("UNSUPPORTED_MODEL", f"no current reference price for {thread['model']}")
    rollout = Path(thread["rollout_path"])
    offset, usage, _, _ = _scan_rollout(rollout)
    timestamp, epoch_ms = _now()
    round_id = str(uuid.uuid4())
    event = {
        "schema_version": SCHEMA_VERSION,
        "event": "round_started",
        "round_id": round_id,
        "thread_id": args.thread_id,
        "timestamp": timestamp,
        "timestamp_epoch_ms": epoch_ms,
        "model": thread["model"],
        "reasoning_effort": thread["reasoning_effort"],
        "rollout_path": str(rollout),
        "rollout_offset": offset,
        "token_baseline": usage or _empty_usage(),
    }
    _append_event(args.ledger, event)
    return {
        "status": "ROUND_STARTED",
        "round_id": round_id,
        "model": thread["model"],
        "reasoning_effort": thread["reasoning_effort"],
    }


def _close(args: argparse.Namespace) -> dict[str, Any]:
    events = _load_events(args.ledger)
    rounds = _rounds(events)
    open_records = [
        (round_id, record)
        for round_id, record in rounds.items()
        if record["start"]
        and record["start"]["thread_id"] == args.thread_id
        and record["close"] is None
    ]
    if len(open_records) != 1:
        raise MetricsError("NO_ACTIVE_ROUND", "expected exactly one open round for PM task")
    round_id, record = open_records[0]
    start = record["start"]
    thread = _thread_row(args.state_db, args.thread_id)
    if (
        thread["model"] != start["model"]
        or thread["reasoning_effort"] != start["reasoning_effort"]
        or str(Path(thread["rollout_path"])) != str(Path(start["rollout_path"]))
    ):
        raise MetricsError("CONFIGURATION_CHANGED", "PM model, effort, or rollout changed")
    _, latest, models, efforts = _scan_rollout(
        Path(start["rollout_path"]), int(start["rollout_offset"])
    )
    if any(model != start["model"] for model in models) or any(
        effort != start["reasoning_effort"] for effort in efforts
    ):
        raise MetricsError("CONFIGURATION_CHANGED", "PM model or effort changed inside round")
    end_usage = latest or start["token_baseline"]
    usage = _usage_delta(end_usage, start["token_baseline"])
    cost_usd, rates = _cost(start["model"], usage)
    timestamp, epoch_ms = _now()
    elapsed_seconds = Decimal(epoch_ms - int(start["timestamp_epoch_ms"])) / Decimal(1000)
    event = {
        "schema_version": SCHEMA_VERSION,
        "event": "round_closed",
        "round_id": round_id,
        "thread_id": args.thread_id,
        "timestamp": timestamp,
        "timestamp_epoch_ms": epoch_ms,
        "model": start["model"],
        "reasoning_effort": start["reasoning_effort"],
        "contains_code_work": args.contains_code_work,
        "token_usage": usage,
        "pricing_basis": "user_supplied_reference",
        "pricing_effective_date": PRICE_EFFECTIVE_DATE,
        "price_unit": "USD_per_million_tokens",
        "price_rates": rates,
        "estimated_cost_usd": cost_usd,
        "elapsed_seconds": format(elapsed_seconds, "f"),
        "quality_score_at_close": 100,
    }
    _append_event(args.ledger, event)
    return {
        "status": "ROUND_CLOSED",
        "round_id": round_id,
        "quality_score": 100,
        "estimated_cost_usd": cost_usd,
        "elapsed_seconds": event["elapsed_seconds"],
    }


def _add_event(args: argparse.Namespace) -> dict[str, Any]:
    events = _load_events(args.ledger)
    rounds = _rounds(events)
    record = rounds.get(args.round_id)
    if record is None or record["close"] is None:
        raise MetricsError("ROUND_NOT_CLOSED", "quality events require a closed round")
    if not args.incident_id.strip() or not args.evidence.strip():
        raise MetricsError(
            "INVALID_QUALITY_EVENT", "incident_id and evidence must be nonempty"
        )
    timestamp, _ = _now()
    quality_event = {
        "event_id": str(uuid.uuid4()),
        "incident_id": args.incident_id,
        "event_type": args.event_type,
        "timestamp": timestamp,
        "evidence": args.evidence,
        "attributed_to_pm": True,
        "code_related": args.code_related,
    }
    score, _ = _quality(record["quality_events"] + [quality_event])
    _append_event(
        args.ledger,
        {
            "schema_version": SCHEMA_VERSION,
            "event": "quality_event_added",
            "round_id": args.round_id,
            "timestamp": timestamp,
            "quality_event": quality_event,
            "quality_score_after": score,
        },
    )
    return {
        "status": "QUALITY_EVENT_ADDED",
        "round_id": args.round_id,
        "event_id": quality_event["event_id"],
        "quality_score": score,
    }


def _decimal_median(values: list[Decimal]) -> str:
    return format(median(values), "f")


def _summary(args: argparse.Namespace) -> dict[str, Any]:
    rounds = _rounds(_load_events(args.ledger))
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in rounds.values():
        close = record["close"]
        if close is None:
            continue
        grouped.setdefault((close["model"], close["reasoning_effort"]), []).append(record)
    output = []
    for (model, effort), records in sorted(grouped.items()):
        scores = []
        costs = []
        elapsed = []
        code_rounds = 0
        event_counts = {event_type: 0 for event_type in EVENT_PENALTIES}
        code_event_counts = {event_type: 0 for event_type in EVENT_PENALTIES}
        for record in records:
            score, counts = _quality(record["quality_events"])
            scores.append(Decimal(score))
            close = record["close"]
            costs.append(Decimal(close["estimated_cost_usd"]))
            elapsed.append(Decimal(close["elapsed_seconds"]))
            code_rounds += int(bool(close["contains_code_work"]))
            for event_type, count in counts.items():
                event_counts[event_type] += count
            for quality_event in record["quality_events"]:
                if quality_event["code_related"]:
                    code_event_counts[quality_event["event_type"]] += 1
        output.append(
            {
                "model": model,
                "reasoning_effort": effort,
                "sample_count": len(records),
                "median_quality_score": _decimal_median(scores),
                "median_estimated_cost_usd": _decimal_median(costs),
                "median_elapsed_seconds": _decimal_median(elapsed),
                "code_work_sample_count": code_rounds,
                "quality_event_counts": event_counts,
                "code_related_quality_event_counts": code_event_counts,
            }
        )
    return {"status": "SUMMARY", "groups": output}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-db", type=Path, default=_default_state_db())
    parser.add_argument("--ledger", type=Path, default=_default_ledger())
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start")
    start.add_argument("--thread-id", required=True)
    start.set_defaults(handler=_start)

    close = subparsers.add_parser("close")
    close.add_argument("--thread-id", required=True)
    close.add_argument("--contains-code-work", required=True, type=_bool)
    close.set_defaults(handler=_close)

    add_event = subparsers.add_parser("add-event")
    add_event.add_argument("--round-id", required=True)
    add_event.add_argument("--event-type", choices=tuple(EVENT_PENALTIES), required=True)
    add_event.add_argument("--incident-id", required=True)
    add_event.add_argument("--evidence", required=True)
    add_event.add_argument("--code-related", required=True, type=_bool)
    add_event.set_defaults(handler=_add_event)

    summary = subparsers.add_parser("summary")
    summary.set_defaults(handler=_summary)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = args.handler(args)
    except MetricsError as exc:
        print(json.dumps({"status": exc.status, "message": str(exc)}))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
