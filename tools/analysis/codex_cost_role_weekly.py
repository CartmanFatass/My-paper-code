#!/usr/bin/env python3
"""Generate weekly token/cost breakdown grouped by model+effort and role.

Output format:
- gpt-5.6-sol high
turns=286 total_tokens=... cost=$...
role\t$cost\txx.xx%
- gpt-5.6-sol xhigh
...
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from decimal import Decimal

from typing import Dict, Tuple


def _repo_default_pricing_path() -> Path:
    return Path(__file__).resolve().parents[2] / "references" / "default-pricing.json"


def _normalize_path(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value)
    if text.startswith("\\\\?\\"):
        text = text[4:]
    try:
        return str(Path(text).resolve())
    except Exception:
        return None


def _week_start_end(now: datetime | None = None) -> tuple[float, float]:
    now_dt = now or datetime.now().astimezone()
    # Monday is 0
    monday = now_dt - timedelta(days=now_dt.weekday())
    start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now_dt
    return start.timestamp(), end.timestamp()


def _load_pricing(path: Path) -> dict[str, dict[str, Decimal]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != 1 or raw.get("unit") != "USD_per_million_tokens":
        raise ValueError("unsupported pricing schema")
    models = raw.get("models", {})
    converted: dict[str, dict[str, Decimal]] = {}
    required = ("input", "cached_input", "cache_write_input", "output")
    for model, rates in models.items():
        converted[str(model)] = {name: Decimal(str(rates[name])) for name in required}
    return converted


def _price_usage(rates: dict[str, dict[str, Decimal]], model: str,
                input_tokens: int, cached_input_tokens: int,
                cache_write_input_tokens: int, output_tokens: int) -> float | None:
    model_rates = rates.get(model)
    if model_rates is None:
        return None
    uncached = input_tokens - cached_input_tokens - cache_write_input_tokens
    value = (
        Decimal(uncached) * model_rates["input"]
        + Decimal(cached_input_tokens) * model_rates["cached_input"]
        + Decimal(cache_write_input_tokens) * model_rates["cache_write_input"]
        + Decimal(output_tokens) * model_rates["output"]
    ) / Decimal(1_000_000)
    return float(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-db", type=Path, default=Path.home() / ".codex" / "state_5.sqlite")
    parser.add_argument("--pricing-json", type=Path, default=_repo_default_pricing_path())
    parser.add_argument("--project-cwd", type=str, default=str(Path.cwd()))
    parser.add_argument("--start", type=int, default=None, help="unix ts for start (default: this week Monday 00:00)")
    parser.add_argument("--end", type=int, default=None, help="unix ts for end (default: now)")
    args = parser.parse_args()

    start, end = _week_start_end() if args.start is None or args.end is None else (args.start, args.end)

    rates = _load_pricing(args.pricing_json)
    project_cwd = _normalize_path(args.project_cwd)

    conn = sqlite3.connect(f"file:{args.state_db.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        threads = conn.execute(
            """
            SELECT id, model, reasoning_effort, agent_role, cwd, rollout_path, created_at
            FROM threads
            """
        ).fetchall()
    finally:
        conn.close()

    agg: Dict[Tuple[str, str], dict] = defaultdict(
        lambda: {
            "turns": 0,
            "token": 0,
            "input": 0,
            "output": 0,
            "cached_input": 0,
            "cache_write_input": 0,
            "reasoning": 0,
            "cost": 0.0,
            "roles": defaultdict(float),
        }
    )

    for row in threads:
        created = row["created_at"]
        if not isinstance(created, int):
            continue
        if not (start <= created <= end):
            continue

        if _normalize_path(row["cwd"]) != project_cwd:
            continue

        rp = _normalize_path(row["rollout_path"])
        if not rp:
            continue
        p = Path(rp)
        if not p.exists():
            continue

        model = str(row["model"] or "UNKNOWN")
        effort = str(row["reasoning_effort"] or "UNKNOWN")
        role = str(row["agent_role"] or "unlabeled_root")

        latest = {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "cache_write_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
            "total_tokens": 0,
        }
        prior_total = 0
        current_model = model
        current_effort = effort
        active = None

        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                j = json.loads(line)
                payload = j.get("payload") or {}
                ptype = payload.get("type")

                # thread settings can change model/effort in-stream
                if j.get("type") == "turn_context":
                    if payload.get("model"):
                        current_model = str(payload["model"])
                    if payload.get("effort"):
                        current_effort = str(payload["effort"])
                elif payload.get("type") == "thread_settings_applied":
                    ts = payload.get("thread_settings") or {}
                    if ts.get("model"):
                        current_model = str(ts["model"])
                    if ts.get("reasoning_effort"):
                        current_effort = str(ts["reasoning_effort"])

                if ptype == "token_count":
                    info = payload.get("info") or {}
                    tu = info.get("total_token_usage")
                    if isinstance(tu, dict):
                        input_tokens = int(tu.get("input_tokens", 0))
                        cached_input_tokens = int(tu.get("cached_input_tokens", 0))
                        cache_write_input_tokens = int(tu.get("cache_write_input_tokens", 0))
                        output_tokens = int(tu.get("output_tokens", 0))
                        reasoning_output_tokens = int(tu.get("reasoning_output_tokens", 0))
                        total_tokens = int(tu.get("total_tokens", 0))
                        candidate = {
                            "input_tokens": input_tokens,
                            "cached_input_tokens": cached_input_tokens,
                            "cache_write_input_tokens": cache_write_input_tokens,
                            "output_tokens": output_tokens,
                            "reasoning_output_tokens": reasoning_output_tokens,
                            "total_tokens": total_tokens,
                        }
                        if total_tokens < prior_total:
                            # safety fallback
                            candidate = latest
                        latest = candidate
                        prior_total = latest["total_tokens"]

                elif ptype == "task_started":
                    active = latest.copy()

                elif ptype == "task_complete":
                    if active is None:
                        continue
                    baseline = active
                    diff_input = latest["input_tokens"] - baseline["input_tokens"]
                    diff_cached = latest["cached_input_tokens"] - baseline["cached_input_tokens"]
                    diff_cachew = latest["cache_write_input_tokens"] - baseline["cache_write_input_tokens"]
                    diff_output = latest["output_tokens"] - baseline["output_tokens"]
                    diff_reason = latest["reasoning_output_tokens"] - baseline["reasoning_output_tokens"]
                    diff_total = latest["total_tokens"] - baseline["total_tokens"]

                    cost = _price_usage(
                        rates,
                        current_model,
                        diff_input,
                        diff_cached,
                        diff_cachew,
                        diff_output,
                    )
                    if cost is None:
                        active = None
                        continue

                    key = (current_model, current_effort)
                    bucket = agg[key]
                    bucket["turns"] += 1
                    bucket["input"] += diff_input
                    bucket["cached_input"] += diff_cached
                    bucket["cache_write_input"] += diff_cachew
                    bucket["output"] += diff_output
                    bucket["reasoning"] += diff_reason
                    bucket["token"] += diff_total
                    bucket["cost"] += cost
                    bucket["roles"][role] += cost
                    active = None

    # Keep output in the requested format
    for (model, effort), bucket in sorted(agg.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        if bucket["turns"] == 0:
            continue
        print(f"{model} {effort}")
        print(f"turns={bucket['turns']} total_tokens={bucket['token']} cost=${bucket['cost']:.6f}")
        total_cost = bucket["cost"]
        for role, value in sorted(bucket["roles"].items(), key=lambda kv: kv[1], reverse=True):
            pct = (value / total_cost * 100.0) if total_cost else 0.0
            print(f"{role}\t${value:.6f}\t{pct:.2f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
