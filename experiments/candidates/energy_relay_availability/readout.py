"""World-seed inference for the fixed four-panel ordinary-reference batch."""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import t as student_t

from .events import aggregate_events


def _distribution(values: list[float]) -> dict:
    x = np.asarray(values, dtype=np.float64)
    return {"n": len(x), "mean": float(x.mean()) if len(x) else None,
            "sd": float(x.std(ddof=1)) if len(x) > 1 else None}


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _interval(mean: float, se: float, df: float) -> list[float] | None:
    if not np.isfinite(df) or df <= 0 or not np.isfinite(se):
        return None
    half = float(student_t.ppf(0.975, df) * se)
    return [mean - half, mean + half]


def paired(a: list[float], b: list[float]) -> dict:
    """a-minus-b on matched world seeds, with a t95 interval."""
    if len(a) != len(b) or not a:
        raise ValueError("paired contrast requires equal nonempty lists")
    differences = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    n = len(differences)
    mean = float(differences.mean())
    sd = float(differences.std(ddof=1)) if n > 1 else None
    se = sd / math.sqrt(n) if sd is not None else None
    return {"n": n, "mean": mean, "sd": sd, "se": se, "df": n - 1,
            "t95": _interval(mean, se, n - 1) if se is not None else None}


def welch(a: list[float], b: list[float]) -> dict:
    """a-minus-b for disjoint condition seeds, with Welch SE/df and t95."""
    if not a or not b:
        raise ValueError("Welch contrast requires two nonempty samples")
    xa, xb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    va = float(xa.var(ddof=1)) if len(xa) > 1 else None
    vb = float(xb.var(ddof=1)) if len(xb) > 1 else None
    mean = float(xa.mean() - xb.mean())
    if va is None or vb is None:
        return {"n_a": len(xa), "n_b": len(xb), "mean": mean, "se": None,
                "df": None, "t95": None}
    aa, bb = va / len(xa), vb / len(xb)
    se = math.sqrt(aa + bb)
    denom = aa * aa / (len(xa) - 1) + bb * bb / (len(xb) - 1)
    df = (aa + bb) ** 2 / denom if denom else None
    return {"n_a": len(xa), "n_b": len(xb), "mean": mean, "se": se,
            "df": df, "t95": _interval(mean, se, df) if df is not None else None}


def summarize(worlds: list[dict], expected_keys: list[str]) -> dict:
    by_key = {row["job_key"]: row for row in worlds}
    failed = [key for key in expected_keys if key in by_key and by_key[key]["status"] == "failed"]
    unreconciled = [key for key in expected_keys if key in by_key
                    and by_key[key]["status"] == "unreconciled"]
    cancelled = [key for key in expected_keys if key in by_key
                 and by_key[key]["status"] == "cancelled"]
    missing = [key for key in expected_keys if key not in by_key]
    groups = {f"{condition}/{controller}": []
              for condition in ("fault_off", "fault_on")
              for controller in ("H_local", "H_central")}
    for key in expected_keys:
        row = by_key.get(key)
        if row and row["status"] == "completed":
            groups[f'{row["condition"]}/{row["controller"]}'].append(row)
    numeric_fields = sorted({field for rows in groups.values() for row in rows
                             for field, value in row.items() if _number(value)
                             and field not in {"seed", "worker_peak_rss_kib",
                                               "worker_cpu_seconds", "worker_wall_seconds",
                                               "raw_bytes"}})
    panels = {}
    for name, rows in groups.items():
        metrics = {}
        for field in numeric_fields:
            values = [float(row[field]) for row in rows if _number(row.get(field))]
            metrics[field] = _distribution(values) | {"missing": len(rows) - len(values)}
        panels[name] = {
            "planned_worlds": 32, "completed_worlds": len(rows),
            "metrics": metrics,
            "events": {kind: aggregate_events(rows, kind) for kind in ("onset", "recovery")},
            "expiry_count": sum(row["events"]["expiry_count"] for row in rows),
            "refault_count": sum(row["events"]["refault_count"] for row in rows),
            "terminal_types": {kind: sum(row["terminal_type"] == kind for row in rows)
                               for kind in ("terminated", "truncated", "horizon")},
        }
    complete = (not failed and not unreconciled and not cancelled and not missing
                and all(len(rows) == 32 for rows in groups.values()))
    contrasts = {}
    if complete:
        # Every panel has the same native metric keys. Pair only identical seed identities.
        fields = numeric_fields
        mapped = {key: {row["seed"]: row for row in rows} for key, rows in groups.items()}
        for field in fields:
            missing_by_panel = {name: sum(not _number(row.get(field)) for row in rows)
                                for name, rows in groups.items()}
            if any(missing_by_panel.values()):
                contrasts[field] = {"status": "not_comparable",
                                    "missing_by_panel": missing_by_panel}
                continue
            controller_gaps = {}
            for condition in ("fault_off", "fault_on"):
                local, central = mapped[f"{condition}/H_local"], mapped[f"{condition}/H_central"]
                seeds = sorted(local)
                if seeds != sorted(central):
                    raise ValueError("same-condition controller seeds no longer pair")
                controller_gaps[condition] = [central[s][field] - local[s][field] for s in seeds]
            contrasts[field] = {
                "central_minus_local": {
                    condition: paired(gaps, [0.0] * len(gaps))
                    for condition, gaps in controller_gaps.items()},
                "on_minus_off": {
                    controller: welch(
                        [r[field] for r in groups[f"fault_on/{controller}"]],
                        [r[field] for r in groups[f"fault_off/{controller}"]])
                    for controller in ("H_local", "H_central")},
                "controller_gap_on_minus_off": welch(
                    controller_gaps["fault_on"], controller_gaps["fault_off"]),
            }
    return {"status": "complete" if complete else "incomplete",
            "planned_jobs": len(expected_keys), "completed_jobs": sum(len(v) for v in groups.values()),
            "failed_jobs": failed, "unreconciled_jobs": unreconciled,
            "cancelled_jobs": cancelled, "missing_jobs": missing, "panels": panels,
            "contrasts": contrasts, "inference_unit": "world seed",
            "event_reading": "descriptive within-episode; events and UAVs are not independent samples"}
