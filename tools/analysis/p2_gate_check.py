#!/usr/bin/env python
"""P2-lite Pre-check 2 gate.

Reads a ``p2_recovery_precheck`` run's ``metrics/train_updates.csv`` and decides
whether the recovery-window credit reward variants (h0/h1/l1) may run.

HARD gate (blocks h0/h1/l1) -- the load-bearing "the soft potential MOVES during
disconnect" property, which is robustly measurable:

    delta_phi_soft_nonzero_rate_when_full_disconnect > min_delta_phi
    delta_phi_soft_nonzero_rate_when_near_disconnect  > min_delta_phi

INFORMATIONAL (printed, never blocks by default) -- credit-direction diagnostics.
Full reconnection within one short segment is too sparse for a stable correlation,
so the continuous ``p2_corr_credit_delta_bh_frac`` (does the assigned credit track
the actual backhaul improvement?) is the meaningful one:

    p2_corr_phi_recovery_event            (full-reconnection corr; event-starved)
    p2_corr_credit_delta_bh_frac          (continuous credit<->delta_bh_frac corr)
    p2_partial_recovery_frac              (how often partial recovery fires)
    p2_credit_by_partial_recovery_event   (mean credit on partial-recovery segments)

Pass ``--require-corr`` to additionally HARD-gate on
``p2_corr_credit_delta_bh_frac > --min-corr``.

Exit codes:
    0  gate passed
    1  gate failed (metrics present but below threshold)
    2  no precheck CSV found
    3  CSV present but P2 hard-gate columns missing (stale logging -> re-run precheck)
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import sys

HARD_KEYS = (
    "delta_phi_soft_nonzero_rate_when_full_disconnect",
    "delta_phi_soft_nonzero_rate_when_near_disconnect",
)
INFO_KEYS = (
    "p2_corr_phi_recovery_event",
    "p2_corr_credit_delta_bh_frac",
    "p2_partial_recovery_frac",
    "p2_credit_by_partial_recovery_event",
)
CONTINUOUS_CORR_KEY = "p2_corr_credit_delta_bh_frac"


def _discover_csv(log_root: str) -> str | None:
    pattern = os.path.join(log_root, "*p2_recovery_precheck*", "metrics", "train_updates.csv")
    matches = glob.glob(pattern)
    if not matches:
        return None
    # Newest by mtime so re-running the precheck supersedes an older gate.
    return max(matches, key=os.path.getmtime)


def _tail_mean(rows: list[dict], key: str) -> float | None:
    vals = []
    for r in rows:
        raw = r.get(key, "")
        if raw in (None, ""):
            continue
        try:
            vals.append(float(raw))
        except (TypeError, ValueError):
            continue
    if not vals:
        return None
    # Average over the converged tail (last half) so a few cold-start updates don't
    # sink an otherwise-stable signal.
    tail = vals[max(1, len(vals) // 2) - 1:]
    return sum(tail) / len(tail)


def main() -> int:
    ap = argparse.ArgumentParser(description="P2-lite Pre-check 2 gate")
    ap.add_argument("--log-root", default="logs")
    ap.add_argument("--gate-csv", default="", help="Explicit precheck CSV; overrides discovery")
    ap.add_argument("--min-delta-phi", type=float, default=0.0)
    ap.add_argument("--min-corr", type=float, default=0.0,
                    help="Threshold for the continuous credit<->delta_bh_frac corr (only enforced with --require-corr)")
    ap.add_argument("--require-corr", action="store_true",
                    help="Also HARD-gate on p2_corr_credit_delta_bh_frac > --min-corr")
    args = ap.parse_args()

    csv_path = args.gate_csv or _discover_csv(args.log_root)
    if not csv_path or not os.path.isfile(csv_path):
        print(
            "[p2-gate] FAIL: no p2_recovery_precheck train_updates.csv found under "
            f"'{args.log_root}'.  Run --experiment p2_recovery_precheck first.",
            file=sys.stderr,
        )
        return 2

    with open(csv_path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print(f"[p2-gate] FAIL: precheck CSV '{csv_path}' has no rows.", file=sys.stderr)
        return 2

    missing_cols = [k for k in HARD_KEYS if k not in rows[0]]
    if missing_cols:
        print(
            f"[p2-gate] FAIL: precheck CSV '{csv_path}' is missing hard-gate columns "
            f"{missing_cols} -- it predates the metric logging fix.  Re-run the precheck.",
            file=sys.stderr,
        )
        return 3

    print(f"[p2-gate] reading {csv_path} ({len(rows)} updates; tail-half mean)")

    failed = False
    print("[p2-gate] HARD gate (delta_phi moves during disconnect):")
    for key in HARD_KEYS:
        val = _tail_mean(rows, key)
        if val is None:
            print(f"[p2-gate]   {key}: no numeric values -> FAIL", file=sys.stderr)
            failed = True
            continue
        ok = val > args.min_delta_phi
        print(f"[p2-gate]   {key} = {val:.4f}  (need > {args.min_delta_phi})  {'PASS' if ok else 'FAIL'}")
        failed = failed or not ok

    print("[p2-gate] INFORMATIONAL (credit-direction diagnostics):")
    for key in INFO_KEYS:
        val = _tail_mean(rows, key)
        shown = "n/a" if val is None else f"{val:.4f}"
        print(f"[p2-gate]   {key} = {shown}")

    if args.require_corr:
        val = _tail_mean(rows, CONTINUOUS_CORR_KEY)
        if val is None:
            print(f"[p2-gate]   {CONTINUOUS_CORR_KEY}: no values, but --require-corr set -> FAIL",
                  file=sys.stderr)
            failed = True
        else:
            ok = val > args.min_corr
            print(f"[p2-gate]   REQUIRED {CONTINUOUS_CORR_KEY} = {val:.4f}  "
                  f"(need > {args.min_corr})  {'PASS' if ok else 'FAIL'}")
            failed = failed or not ok

    if failed:
        print(
            "[p2-gate] GATE FAILED: do NOT run h0/h1/l1 yet.  The hard delta_phi "
            "property (or a required corr) is not satisfied.",
            file=sys.stderr,
        )
        return 1
    print("[p2-gate] GATE PASSED: reward variants (h0/h1/l1) are cleared to run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
